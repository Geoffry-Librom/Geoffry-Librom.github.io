# 微信群收款「按人填金额」自动化（iPhone 镜像 + EasyOCR + PyAutoGUI）
# 修订记录（2026-11-07）：
#   1. 修复整数金额（如 100、20.00）被误判为"仍是 0.00"而重复输入的问题
#   2. 收紧联系人匹配：名字须完全一致，或长度相同且相似（容忍 OCR 误读一个字），
#      "张三" 不会再匹配到 "张三丰"；不确定时不填，进入失败名单人工核对
#   3. 填完后读取同行金额并与名单核对，不一致记入失败名单（不自动补救，避免追加输入）
#   4. 小修：exit -> sys.exit；FAILSAFE 注释更正
import os
import re
import sys
import time
from difflib import SequenceMatcher
import subprocess
import ctypes
import ctypes.util
from datetime import datetime
import mss
import numpy as np
import cv2
import pyautogui
import pyperclip
import easyocr

# ==================== 0. 全局设置与系统底层权限/焦点修复 ====================
pyautogui.FAILSAFE = True   # 安全保护：鼠标快速甩到屏幕任意一个角可紧急中止程序
pyautogui.PAUSE = 0.02      # 基础指令间隔


def suppress_python_dock_rocket():
    """
    通过 ctypes 调用 macOS 原生 Objective-C 运行时，将 Python 进程设为 Accessory 后台模式。
    作用：彻底防止运行脚本时 Dock 栏跳出 Python 小火箭图标抢走『iPhone 镜像』的窗口焦点。
    """
    try:
        appkit = ctypes.cdll.LoadLibrary(ctypes.util.find_library('AppKit'))
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('objc'))
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
        objc.objc_msgSend.restype = ctypes.c_void_p

        cls_NSApp = objc.objc_getClass(b"NSApplication")
        NSApp = objc.objc_msgSend(cls_NSApp, objc.sel_registerName(b"sharedApplication"), 0)
        # 1 = NSApplicationActivationPolicyAccessory (纯后台静默模式)
        objc.objc_msgSend(NSApp, objc.sel_registerName(b"setActivationPolicy:"), ctypes.c_long(1))
        print("✅ [系统内核] 小火箭拦截成功！程序将在后台静默运行。")
    except Exception as e:
        print(f"⚠️ 隐藏小火箭失败 (非 macOS 环境可忽略): {e}")


def check_macos_accessibility():
    """启动自检：检测当前 IDE (PyCharm/VSCode) 或终端是否已获得 macOS『辅助功能』键鼠控制权限"""
    try:
        app_services = ctypes.cdll.LoadLibrary(ctypes.util.find_library('ApplicationServices'))
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        if app_services.AXIsProcessTrusted():
            print("✅ [权限自检] macOS 辅助功能 (Accessibility) 权限已授权。")
        else:
            print("🚨 [严重警告] 当前 IDE/终端 缺少 macOS『辅助功能』权限，鼠标点击将被系统拦截！")
            print("   👉 请前往：系统设置 -> 隐私与安全性 -> 辅助功能，开启对应软件权限。")
    except Exception:
        pass


suppress_python_dock_rocket()
check_macos_accessibility()


def debug_log(msg):
    """带毫秒级时间戳的控制台日志输出"""
    now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{now_str}] {msg}", flush=True)


# ==================== 1. OOP 自动化主控类 ====================
class WeChatSplitBot:
    def __init__(self, debug_mode=True):
        debug_log("🔧 正在初始化 WeChatSplitBot (视觉闭环 + 物理键盘极速版)...")
        # 【🔧 需根据实际情况修改 1】debug_mode=True 会在同级目录生成 debug_logs 文件夹保存每一步的视觉标记图
        self.debug_mode = debug_mode
        self.debug_dir = "debug_logs"
        if self.debug_mode:
            os.makedirs(self.debug_dir, exist_ok=True)

        debug_log("⏳ 正在加载 EasyOCR 中英文识别引擎...")
        self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

        self.sct = mss.mss()
        # 【🔧 需根据实际情况修改 2】monitors[1] 代表主屏幕；若你的 iPhone 镜像放在外接副屏上，请改为 monitors[2]
        self.monitor = self.sct.monitors[1]

        # 使用真实截图矩阵尺寸计算 Retina 缩放比 (解决 macOS 物理像素与逻辑坐标相差 2 倍的问题)
        sample_img = self.grab_screen()
        img_h, img_w = sample_img.shape[:2]
        scr_w, scr_h = pyautogui.size()
        self.scale_x = img_w / scr_w
        self.scale_y = img_h / scr_h
        debug_log(f"🖥️ 屏幕参数: 物理像素={img_w}x{img_h}, 逻辑坐标={scr_w}x{scr_h}, 缩放比=({self.scale_x:.2f}, {self.scale_y:.2f})")

        self.phone_box = None          # 手机投屏窗口的物理像素边界 {'x1', 'y1', 'x2', 'y2'}
        self.search_bar_roi_x = None   # 搜索框『搜索』文字在 ROI 内的 X 坐标
        self.search_bar_roi_y = None   # 搜索框在 ROI 内的 Y 坐标
        self.clear_btn_roi_x = None    # 搜索框最右侧 ⊗ 清除按钮在 ROI 内的 X 坐标

        # 【🔧 需根据实际情况修改 3】待分配的群成员名单与对应金额（建议直接用群昵称或微信备注名，注意不要有错别字）
        self.amount_data = {
            "张三": "54.3",   "李四": "49.05",  "王麻子": "40.05", "赵六": "51.45",
            "孙七": "38.25",  "周八": "40.05",  "吴九": "51.75",   "郑十": "52.8",
            "冯十一": "40.8", "陈十二": "34.65", "褚十三": "46.65", "卫十四": "41.85",
            "蒋十五": "38.25", "沈十六": "59.1", "韩十七": "46.65", "杨十八": "40.8",
            "朱十九": "40.05", "秦二十": "65.55", "尤二一": "40.05", "许二二": "38.25"
        }

    # ==================== 2. 底层视觉抓取与拟真键鼠工具 ====================
    def force_activate_iphone(self):
        """
        调用 AppleScript 将 iPhone 镜像窗口置顶激活。
        【🔧 需根据实际情况修改 4】英文系统应用名为 "iPhone Mirroring"，中文系统若报错可改为 "iPhone镜像"
        """
        script = '''
        try
            tell application "iPhone Mirroring" to activate
        on error
            try
                tell application "iPhone镜像" to activate
            end try
        end try
        '''
        subprocess.run(["osascript", "-e", script], capture_output=True)
        time.sleep(0.25)

    def iphone_tap(self, logic_x, logic_y, desc=""):
        """
        针对 iPhone Mirroring 优化的拟真触控点击：
        平滑移动 -> 悬停 50ms 捕获光标 -> 按下保持 80ms -> 抬起，防止投屏层丢弃瞬时点击事件。
        """
        logic_x, logic_y = float(logic_x), float(logic_y)
        pyautogui.moveTo(logic_x, logic_y, duration=0.10)
        time.sleep(0.05)
        pyautogui.mouseDown(logic_x, logic_y, button='left')
        time.sleep(0.08)
        pyautogui.mouseUp(logic_x, logic_y, button='left')
        debug_log(f"    🖱️ [触控点击] {desc} -> 逻辑坐标: ({logic_x:.1f}, {logic_y:.1f})")

    def physical_keyboard_type_amount(self, amount_str):
        """
        使用 Mac 物理键盘直接向微信数字软键盘输入金额。
        采用 keyDown + 45ms 保持 + keyUp，确保投屏连接稳定接收每一个按键。
        """
        debug_log(f"    ⌨️ [物理键盘输入] 正在键入金额: {amount_str}")
        for ch in str(amount_str):
            pyautogui.keyDown(ch)
            time.sleep(0.045)
            pyautogui.keyUp(ch)
            time.sleep(0.09)

    def grab_screen(self):
        """抓取全屏画面并转为 OpenCV 标准 BGR 格式"""
        return cv2.cvtColor(np.array(self.sct.grab(self.monitor)), cv2.COLOR_BGRA2BGR)

    def grab_phone_roi(self):
        """仅截取手机投屏窗口区域 (ROI)，大幅提升后续 OCR 速度并排除外部代码编辑器文字干扰"""
        if not self.phone_box:
            return self.grab_screen(), 0, 0
        img = self.grab_screen()
        x1, y1, x2, y2 = self.phone_box['x1'], self.phone_box['y1'], self.phone_box['x2'], self.phone_box['y2']
        return img[y1:y2, x1:x2], x1, y1

    def roi_point_to_screen_logic(self, roi_x, roi_y):
        """将手机 ROI 内部物理像素坐标 -> 转换为全局屏幕 PyAutoGUI 逻辑坐标"""
        ox = self.phone_box['x1'] if self.phone_box else 0
        oy = self.phone_box['y1'] if self.phone_box else 0
        return (roi_x + ox) / self.scale_x, (roi_y + oy) / self.scale_y

    @staticmethod
    def bbox_center(bbox):
        """计算 EasyOCR 文本框的中心坐标 (cx, cy)"""
        return (bbox[0][0] + bbox[2][0]) / 2.0, (bbox[0][1] + bbox[2][1]) / 2.0

    def save_debug_img(self, img, step_name, bboxes=None, target_point=None, h_line_y=None):
        """
        保存可视化调试图片到 debug_logs 目录：
        - 绿色多边形：OCR 识别出的文字边界框
        - 黄色水平线：当前锁定的联系人同行对齐基准线
        - 红心黄圈靶点：程序即将执行鼠标点击的精确像素位置
        """
        if not self.debug_mode:
            return
        dbg = img.copy()
        if h_line_y is not None:
            cv2.line(dbg, (0, int(h_line_y)), (dbg.shape[1], int(h_line_y)), (0, 255, 255), 2)
        if bboxes:
            for bbox, text, prob in bboxes:
                pts = np.array(bbox, dtype=np.int32)
                cv2.polylines(dbg, [pts], True, (0, 255, 0), 2)
                cv2.putText(dbg, str(text), (pts[0][0], max(15, pts[0][1] - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        if target_point:
            cv2.circle(dbg, (int(target_point[0]), int(target_point[1])), 10, (0, 0, 255), -1)
            cv2.circle(dbg, (int(target_point[0]), int(target_point[1])), 14, (0, 255, 255), 2)
        path = os.path.join(self.debug_dir, f"{step_name}.jpg")
        cv2.imwrite(path, dbg)

    def find_text_in_results(self, results, target_kws, min_y=None, max_y=None):
        """在指定垂直高度区间 [min_y, max_y] 内模糊匹配关键词列表"""
        if isinstance(target_kws, str):
            target_kws = [target_kws]
        for bbox, text, prob in results:
            _, cy = self.bbox_center(bbox)
            if min_y is not None and cy < min_y:
                continue
            if max_y is not None and cy > max_y:
                continue
            clean_text = text.replace(" ", "").lower()
            for kw in target_kws:
                if kw.lower() in clean_text:
                    return bbox, text, prob
        return None, None, None

    def has_wechat_green_highlight(self, roi_img, bbox):
        """利用 HSV 色彩空间检测文本框内是否包含微信搜索结果特有的绿色高亮字体 (#07C160)"""
        h, w = roi_img.shape[:2]
        x1 = max(0, int(min(p[0] for p in bbox)) - 4)
        y1 = max(0, int(min(p[1] for p in bbox)) - 4)
        x2 = min(w, int(max(p[0] for p in bbox)) + 4)
        y2 = min(h, int(max(p[1] for p in bbox)) + 4)
        if x2 <= x1 or y2 <= y1:
            return False
        patch = roi_img[y1:y2, x1:x2]
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([45, 50, 80]), np.array([85, 255, 255]))
        return cv2.countNonZero(mask) >= 12

    # ==================== 3. 自适应窗口锁定与基准坐标标定 ====================
    def locate_iphone_window(self):
        debug_log("📱 正在动态测算并锁定 iPhone 投屏窗口...")
        self.force_activate_iphone()
        img = self.grab_screen()
        results = self.reader.readtext(img)

        # 【🔧 需根据实际情况修改 5】同时兼容英文版微信 "Specific Amount" 与中文版微信 "指定金额" / "按人填金额"
        title_bbox, title_text, _ = self.find_text_in_results(
            results, ["specificamount", "指定金额", "按人填金额"]
        )
        if not title_bbox:
            debug_log("❌ 找不到群收款标题栏（Specific Amount / 指定金额），请确保手机画面未被遮挡！")
            self.save_debug_img(img, "00_ERROR_FullScreen", results)
            sys.exit(1)

        cx, cy = self.bbox_center(title_bbox)
        title_w = title_bbox[2][0] - title_bbox[0][0]
        title_h = title_bbox[2][1] - title_bbox[0][1]

        # 若为中文四字标题（宽度较窄），左右延展系数自动放大；英文标题则按 1.4 倍延展
        expand_ratio = 1.4 if len(title_text.replace(" ", "")) >= 8 else 2.5
        half_w = int(title_w * expand_ratio)

        self.phone_box = {
            "x1": max(0, int(cx - half_w)),
            "y1": max(0, int(cy - title_h * 2)),
            "x2": min(img.shape[1], int(cx + half_w)),
            "y2": min(img.shape[0], int(cy + half_w * 4.3))
        }
        debug_log(f"✅ 动态锁定成功！手机物理像素边界: {self.phone_box}")

        roi, _, _ = self.grab_phone_roi()
        roi_h, roi_w = roi.shape[:2]
        top_results = self.reader.readtext(roi[:int(roi_h * 0.25), :])

        s_bbox, s_text, _ = self.find_text_in_results(top_results, ["搜索", "Search", "索", "艘索"])
        if s_bbox:
            sx, sy = self.bbox_center(s_bbox)
            self.search_bar_roi_x, self.search_bar_roi_y = sx, sy
            debug_log(f"✅ 搜索框基准坐标标定成功: ROI({sx:.1f}, {sy:.1f}) (依据:'{s_text}')")
        else:
            self.search_bar_roi_x = roi_w * 0.15
            self.search_bar_roi_y = roi_h * 0.11
            debug_log(f"⚠️ 使用几何比例标定搜索框: ROI({self.search_bar_roi_x:.1f}, {self.search_bar_roi_y:.1f})")

        # 搜索框最右侧 ⊗ 清除按钮的固定水平位置 (约 91.5% 宽度处)
        self.clear_btn_roi_x = roi_w * 0.915
        self.save_debug_img(roi, "00_Locked_Phone_Window", top_results,
                            target_point=(self.search_bar_roi_x, self.search_bar_roi_y))

    # ==================== 4. 核心检测器：Paste 气泡与 Allow Paste 弹窗 ====================
    def _detect_paste_bubble(self, roi, top_results):
        """
        检测搜索框正下方的 iOS 黑色『Paste / 粘贴』气泡：
        方式 A：OCR 直接识别到 'Paste' / '粘贴'
        方式 B：图像像素级兜底检测搜索框下方是否出现大面积黑色气泡背景 (灰度 < 55)
        """
        sy = self.search_bar_roi_y
        p_bbox, p_text, _ = self.find_text_in_results(
            top_results, ["paste", "粘贴"], min_y=sy + 25, max_y=sy + 115
        )
        if p_bbox:
            px, py = self.bbox_center(p_bbox)
            return (px, py), f"OCR命中 '{p_text}'"

        roi_h, roi_w = roi.shape[:2]
        y1, y2 = max(0, int(sy + 40)), min(roi_h, int(sy + 90))
        x1, x2 = int(roi_w * 0.03), int(roi_w * 0.22)
        if y2 > y1 and x2 > x1:
            patch = roi[y1:y2, x1:x2]
            gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
            dark_ratio = np.count_nonzero(gray < 55) / float(gray.size)
            if dark_ratio > 0.45:
                return ((x1 + x2) / 2.0, (y1 + y2) / 2.0), f"黑色气泡像素特征(占比{dark_ratio:.0%})"

        return None, None

    def _handle_allow_paste_Popup(self, roi, results, name, attempt):
        """
        检测并处理 iOS 跨设备粘贴权限弹窗：
        注意：弹窗上方按钮是『Don't Allow Paste』，下方按钮才是『Allow Paste』！
        必须严格排除含 don / not / 不 的文本框，精准点击最下方的『Allow Paste / 允许粘贴』。
        """
        roi_h, roi_w = roi.shape[:2]
        allow_candidates = []
        dont_allow_bbox = None
        has_popup_title = False

        for bbox, text, prob in results:
            cx, cy = self.bbox_center(bbox)
            if not (roi_h * 0.30 <= cy <= roi_h * 0.78):
                continue

            clean_t = text.replace(" ", "").lower()
            if "wouldliketopaste" in clean_t or "doyouwanttoallow" in clean_t:
                has_popup_title = True

            if ("don" in clean_t or "not" in clean_t or "不" in clean_t) and (
                "allow" in clean_t or "paste" in clean_t or "允许" in clean_t
            ):
                dont_allow_bbox = bbox
                continue

            if any(k in clean_t for k in ["allowpaste", "allow", "允许粘贴", "允许"]):
                if not any(bad in clean_t for bad in ["don", "not", "不", "would", "want", "from"]):
                    allow_candidates.append((cy, bbox, text))

        target_pt = None
        reason = ""

        if allow_candidates:
            # 按 Y 坐标从大到小排序，选择位置最靠下的按钮（即 Allow Paste）
            allow_candidates.sort(key=lambda x: x[0], reverse=True)
            _, best_bbox, best_text = allow_candidates[0]
            target_pt = self.bbox_center(best_bbox)
            reason = f"OCR命中 '{best_text}'"
        elif dont_allow_bbox is not None or has_popup_title:
            if dont_allow_bbox is not None:
                dx, dy = self.bbox_center(dont_allow_bbox)
                target_pt = (dx, dy + 85.0)
                reason = "根据 Don't Allow 按钮向下偏移 85px 几何锁定"
            else:
                target_pt = (roi_w * 0.50, roi_h * 0.595)
                reason = "根据弹窗标题几何锁定底部 Allow Paste"

        if target_pt is not None:
            debug_log(f"    🛡️ 检测到『Allow Paste』授权弹窗 ({reason}) -> 自动点击允许！")
            self.save_debug_img(roi, f"01c_{name}_allow_paste_try{attempt}", results, target_point=target_pt)
            lx, ly = self.roi_point_to_screen_logic(target_pt[0], target_pt[1])
            self.iphone_tap(lx, ly, desc="点击 Allow Paste (允许粘贴)")
            time.sleep(0.65)
            return True

        return False

    def _find_filtered_contact_row(self, roi, results, name):
        """在搜索框下方的『第一行结果区』查找目标联系人（绿色高亮行），杜绝未过滤列表假阳性"""
        min_row1_y = self.search_bar_roi_y + 40
        max_row1_y = self.search_bar_roi_y + 230

        # 若搜索框内仍残留灰色的“搜索”占位符，说明还未输入成功
        placeholder_bbox, _, _ = self.find_text_in_results(
            results, ["搜索", "Search", "艘索"],
            min_y=self.search_bar_roi_y - 30,
            max_y=self.search_bar_roi_y + 30
        )
        if placeholder_bbox is not None:
            return None, None

        for bbox, text, prob in results:
            cx, cy = self.bbox_center(bbox)
            if not (min_row1_y <= cy <= max_row1_y):
                continue
            if cx > roi.shape[1] * 0.55:
                continue

            clean_text = text.replace(" ", "")
            if clean_text == name:
                return bbox, text                      # 完全一致，最可靠
            similar = SequenceMatcher(None, name, clean_text).ratio()
            if len(clean_text) == len(name) and similar >= 0.5 and self.has_wechat_green_highlight(roi, bbox):
                return bbox, text                      # 长度相同、只差 OCR 误读，且有绿色高亮
            if name in clean_text:
                debug_log(f"    ⚠️ 第一行是『{clean_text}』，与『{name}』不完全一致，不填，交给人工核对")

        return None, None

    # ==================== 5. 单人 5 步业务执行流水线 ====================
    def step1_and_2_search_and_paste(self, name, max_retries=3):
        """
        步骤 1 & 2：预置剪贴板 -> 点击搜索框唤出 Paste 气泡 -> 点击 Paste -> 处理授权弹窗 -> 验证第一行绿色姓名
        """
        debug_log(f"\n▶️ [步骤1&2] 搜索并粘贴【{name}】...")

        for attempt in range(1, max_retries + 1):
            pyperclip.copy(name)
            time.sleep(0.15)

            roi, _, _ = self.grab_phone_roi()
            top_h = int(roi.shape[0] * 0.30)
            top_results = self.reader.readtext(roi[:top_h, :])

            s_bbox, _, _ = self.find_text_in_results(top_results, ["搜索", "Search", "索", "艘索"])
            if s_bbox:
                self.search_bar_roi_x, self.search_bar_roi_y = self.bbox_center(s_bbox)

            paste_pt, paste_reason = self._detect_paste_bubble(roi, top_results)

            if paste_pt is None:
                self.save_debug_img(roi, f"01a_{name}_click_search_try{attempt}", top_results,
                                    target_point=(self.search_bar_roi_x, self.search_bar_roi_y))
                lx, ly = self.roi_point_to_screen_logic(self.search_bar_roi_x, self.search_bar_roi_y)
                self.iphone_tap(lx, ly, desc=f"点击搜索框 (第1下, try={attempt})")
                time.sleep(0.45)

                roi, _, _ = self.grab_phone_roi()
                top_results = self.reader.readtext(roi[:top_h, :])
                paste_pt, paste_reason = self._detect_paste_bubble(roi, top_results)

                if paste_pt is None:
                    # 第一次点击仅聚焦了绿色输入光标 `|`，再点第 2 下即可唤出黑色的 Paste 气泡
                    debug_log("    ℹ️ 搜索框已聚焦光标，再次点击搜索框以唤出『Paste』气泡...")
                    self.iphone_tap(lx, ly, desc=f"点击搜索框唤出 Paste 气泡 (第2下, try={attempt})")
                    time.sleep(0.50)

                    roi, _, _ = self.grab_phone_roi()
                    top_results = self.reader.readtext(roi[:top_h, :])
                    paste_pt, paste_reason = self._detect_paste_bubble(roi, top_results)

            if paste_pt is not None:
                debug_log(f"    🎯 发现『Paste』气泡 ({paste_reason}) -> ROI({paste_pt[0]:.1f}, {paste_pt[1]:.1f})")
            else:
                paste_pt = (max(35.0, self.search_bar_roi_x - 25.0), self.search_bar_roi_y + 61.0)
                debug_log(f"    ⚠️ 未检测到气泡文字，使用几何位置兜底点击 -> ROI({paste_pt[0]:.1f}, {paste_pt[1]:.1f})")

            self.save_debug_img(roi, f"01b_{name}_click_paste_bubble_try{attempt}", top_results, target_point=paste_pt)
            plx, ply = self.roi_point_to_screen_logic(paste_pt[0], paste_pt[1])
            self.iphone_tap(plx, ply, desc="点击黑色 Paste 气泡")
            time.sleep(0.65)

            roi, _, _ = self.grab_phone_roi()
            full_results = self.reader.readtext(roi)
            if self._handle_allow_paste_Popup(roi, full_results, name, attempt):
                roi, _, _ = self.grab_phone_roi()
                full_results = self.reader.readtext(roi)

            contact_bbox, matched_text = self._find_filtered_contact_row(roi, full_results, name)
            if contact_bbox:
                cx, cy = self.bbox_center(contact_bbox)
                debug_log(f"    ✅ [搜索验证成功] 第一行已锁定绿色目标: '{matched_text}' (ROI_Y={cy:.1f})")
                self.save_debug_img(roi, f"02_{name}_verified", full_results, target_point=(cx, cy), h_line_y=cy)
                return contact_bbox
            else:
                debug_log(f"    ❌ [第 {attempt} 次验证未通过] 未刷出【{name}】，点击右侧 ⊗ 重置后重试...")
                self.save_debug_img(roi, f"02_{name}_failed_try{attempt}", full_results)
                self.step5_clear_search(name, silent=True)

        debug_log(f"🚨 【{name}】搜索粘贴重试超限（请检查名单是否有错别字或该成员不在群内），跳过该人员。")
        return None

    def step3_click_amount_box(self, name, contact_bbox):
        """步骤 3：严格按照步骤 2 锁定的绿色联系人同行 Y 坐标，点击右侧对应的 0.00 输入框"""
        debug_log(f"\n▶️ [步骤3] 寻找与【{name}】同行的 0.00 输入框...")
        roi, _, _ = self.grab_phone_roi()
        roi_h, roi_w = roi.shape[:2]

        _, contact_cy = self.bbox_center(contact_bbox)
        expected_row_y = contact_cy + 12.0

        # 仅截取联系人所在行的条带区域进行 OCR，速度提升 5 倍且绝不串行
        strip_y1 = max(0, int(expected_row_y - 55))
        strip_y2 = min(roi_h, int(expected_row_y + 55))
        strip_results = self.reader.readtext(roi[strip_y1:strip_y2, :])
        shifted_results = [
            ([[p[0], p[1] + strip_y1] for p in bbox], text, prob)
            for bbox, text, prob in strip_results
        ]

        best_click_pt = None
        best_text = ""

        # 【🔧 需根据实际情况修改 6】同时兼容英文版 "CNY" 与中文版 "元"
        for bbox, text, prob in shifted_results:
            bx, by = self.bbox_center(bbox)
            if bx < roi_w * 0.55:
                continue
            clean_t = text.replace(" ", "").upper()
            if any(k in clean_t for k in ["0.00", "0.0", "CNY", "元", "00"]):
                box_w = bbox[2][0] - bbox[0][0]
                if "0" in clean_t and ("CNY" in clean_t or "元" in clean_t):
                    target_rx = bbox[0][0] + box_w * 0.30
                elif "CNY" in clean_t or "元" in clean_t:
                    target_rx = bbox[0][0] - box_w * 0.85
                else:
                    target_rx = bx
                best_click_pt = (target_rx, by)
                best_text = text
                break

        if best_click_pt is None:
            best_click_pt = (roi_w * 0.74, expected_row_y)
            best_text = "同行几何坐标兜底"
            debug_log(f"    ⚠️ 启用同行几何坐标点击: ROI({best_click_pt[0]:.1f}, {best_click_pt[1]:.1f})")
        else:
            debug_log(f"    🎯 同行金额框锁定成功 (依据:'{best_text}') -> ROI({best_click_pt[0]:.1f}, {best_click_pt[1]:.1f})")

        self.save_debug_img(roi, f"03_{name}_amount_box", shifted_results,
                            target_point=best_click_pt, h_line_y=expected_row_y)

        lx, ly = self.roi_point_to_screen_logic(best_click_pt[0], best_click_pt[1])
        self.iphone_tap(lx, ly, desc=f"点击【{name}】同行 0.00")
        time.sleep(0.55)
        return best_click_pt, expected_row_y

    def _fallback_tap_screen_keypad(self, full_roi, amount_str):
        """备用兜底：若物理键盘输入被中文输入法拦截，自动在屏幕底部 4×3 数字软键盘网格上点击"""
        roi_h, roi_w = full_roi.shape[:2]
        col_x = [roi_w * (1.0 / 6.0), roi_w * (3.0 / 6.0), roi_w * (5.0 / 6.0)]
        row0_y = roi_h * 0.723
        step_y = roi_h * 0.066
        key_grid = {
            '1': (0, 0), '2': (0, 1), '3': (0, 2),
            '4': (1, 0), '5': (1, 1), '6': (1, 2),
            '7': (2, 0), '8': (2, 1), '9': (2, 2),
            '.': (3, 0), '0': (3, 1)
        }
        for ch in str(amount_str):
            if ch in key_grid:
                r, c = key_grid[ch]
                kx, ky = col_x[c], row0_y + r * step_y
                lx, ly = self.roi_point_to_screen_logic(kx, ky)
                self.iphone_tap(lx, ly, desc=f"软键盘兜底按键 '{ch}'")
                time.sleep(0.10)

    def step4_input_amount(self, name, amount, amount_click_pt, expected_row_y):
        """步骤 4：使用物理键盘直接输入金额，并二次校验同行金额是否已脱离 0.00"""
        debug_log(f"\n▶️ [步骤4] 使用物理键盘输入金额: {amount} ...")

        self.physical_keyboard_type_amount(amount)
        time.sleep(0.35)

        roi, _, _ = self.grab_phone_roi()
        roi_h, roi_w = roi.shape[:2]
        strip_y1 = max(0, int(expected_row_y - 45))
        strip_y2 = min(roi_h, int(expected_row_y + 45))
        right_strip = roi[strip_y1:strip_y2, int(roi_w * 0.55):]
        strip_results = self.reader.readtext(right_strip)

        # 只认"单独的 0.00"：100.00、20.00 这类前面紧挨数字的不算（否则会被重复追加输入）
        still_zero = any(re.search(r'(?<![\d.])0\.00(?!\d)', t.replace(" ", "")) for _, t, _ in strip_results)
        if still_zero:
            debug_log("    ⚠️ 检测到同行金额仍为 0.00，重新点击 0.00 并启用屏幕软键盘兜底输入...")
            lx, ly = self.roi_point_to_screen_logic(amount_click_pt[0], amount_click_pt[1])
            self.iphone_tap(lx, ly, desc="重申点击 0.00")
            time.sleep(0.55)
            self._fallback_tap_screen_keypad(roi, amount)
            time.sleep(0.30)
            roi, _, _ = self.grab_phone_roi()

        # 核对：读出同行金额，与名单比较（读 2 次，避免 OCR 偶发误读造成误报）
        ok, shown = False, []
        for _ in range(2):
            roi, shown = self._read_row_amount(expected_row_y)
            if any(abs(float(n) - float(amount)) < 0.001 for n in shown):
                ok = True
                break
            time.sleep(0.3)

        self.save_debug_img(roi, f"04_{name}_after_amount_input", h_line_y=expected_row_y)
        if ok:
            debug_log(f"    ✅ 【{name}】金额 {amount} 输入并核对一致！")
        else:
            debug_log(f"    ❌ 【{name}】金额核对不一致：应为 {amount}，屏幕读到 {shown or '无'}，请手动检查")
        return ok, shown

    def _read_row_amount(self, expected_row_y):
        """读取联系人同行右半边显示的金额数字，返回 (截图, 数字字符串列表)"""
        roi, _, _ = self.grab_phone_roi()
        roi_h, roi_w = roi.shape[:2]
        y1 = max(0, int(expected_row_y - 45))
        y2 = min(roi_h, int(expected_row_y + 45))
        results = self.reader.readtext(roi[y1:y2, int(roi_w * 0.55):])
        nums = []
        for _, t, _ in results:
            t = t.replace(" ", "").replace("，", ".").replace(",", ".")
            nums += re.findall(r'\d+(?:\.\d+)?', t)
        return roi, nums

    def step5_clear_search(self, name, silent=False):
        """步骤 5：点击搜索框右侧的 ⊗ 按钮，一键清空文字并返回初始列表界面"""
        if not silent:
            debug_log(f"\n▶️ [步骤5] 点击搜索框右侧 ⊗ 清除按钮返回初始列表...")

        roi, _, _ = self.grab_phone_roi()
        roi_h, roi_w = roi.shape[:2]
        sy = int(self.search_bar_roi_y)

        # 利用灰度阈值寻找搜索框最右侧灰色的 ⊗ 图标中心；若未找到则用 91.5% 几何位置兜底
        cx, cy = self.clear_btn_roi_x, self.search_bar_roi_y
        x1, x2 = int(roi_w * 0.84), int(roi_w * 0.96)
        y1, y2 = max(0, sy - 22), min(roi_h, sy + 22)
        patch = roi[y1:y2, x1:x2]
        if patch.size > 0:
            gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
            mask = cv2.inRange(gray, 140, 215)
            if cv2.countNonZero(mask) >= 12:
                ys, xs = np.where(mask > 0)
                cx = x1 + float(np.mean(xs))
                cy = y1 + float(np.mean(ys))

        if not silent:
            self.save_debug_img(roi, f"05_{name}_clear_btn", target_point=(cx, cy))

        lx, ly = self.roi_point_to_screen_logic(cx, cy)
        self.iphone_tap(lx, ly, desc="点击清除按钮 ⊗")
        time.sleep(0.45)

    # ==================== 6. 主流程批量调度 ====================
    def run(self):
        print("\n" + "=" * 65)
        self.locate_iphone_window()

        targets = list(self.amount_data.items())
        success_list = []
        failed_list = []

        for idx, (name, amount) in enumerate(targets, 1):
            print("\n" + "-" * 55)
            debug_log(f"🟢 [进度 {idx}/{len(targets)}] 开始处理: {name} -> {amount} 元")

            contact_bbox = self.step1_and_2_search_and_paste(name)
            if not contact_bbox:
                failed_list.append((name, amount, "搜索或粘贴未匹配到联系人"))
                continue

            amount_click_pt, expected_row_y = self.step3_click_amount_box(name, contact_bbox)
            ok, shown = self.step4_input_amount(name, amount, amount_click_pt, expected_row_y)
            self.step5_clear_search(name)
            if ok:
                success_list.append((name, amount))
            else:
                failed_list.append((name, amount, f"金额核对不一致（屏幕读到 {shown or '无'}）"))

        print("\n" + "=" * 65)
        debug_log(f"🎉 批量分配执行完毕！成功: {len(success_list)} 人，失败: {len(failed_list)} 人。")
        if failed_list:
            debug_log("⚠️ 失败名单汇总如下（未匹配的请检查错别字后手动补录；金额不一致的请到微信里手动改正）：")
            for n, a, reason in failed_list:
                debug_log(f"   - {n} ({a} 元): {reason}")


if __name__ == '__main__':
    # 启动自动化机器人（默认开启 debug_mode 保存每一步视觉校验图）
    bot = WeChatSplitBot(debug_mode=True)
    bot.run()
