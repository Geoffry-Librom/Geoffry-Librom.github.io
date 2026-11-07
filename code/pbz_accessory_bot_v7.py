# -*- coding: utf-8 -*-
"""
影之刃零 (Phantom Blade Zero) 饰品属性叠加脚本 —— v7（后台模式 + 虚拟屏）
VERSION = v7（2026-11-06）。历史版本在 history/。

v7 相对 v6 的改动（11/06 14:30~15:55 日志：v6 连跑 110 轮叠 110 层，然后 □ 又失灵 3 轮 → 停止）：
  · v6 的"按之前补发松开 + 失败时松开所有键"都做了（日志 6 次 🔓），□ 还是没反应 → 不是 Mac 这边卡键。
    同一轮里 ○、✕、OPTIONS、方向键都正常；之前两次重启脚本（隔了 3 分钟左右）后 □ 就恢复了。
    原因还不确定（可能是 PS5 / Chiaki 串流那边 □ 的状态卡住，也可能是游戏的冷却），v7 先做到"不停机、能自愈"，并收集证据：
  · □ 失灵时不再算普通失败：退回野外，依次停 60 / 120 / 240 / 480 秒不发任何键再试（共 15 分钟），
    哪次恢复了会在日志里写"✅ 失灵的键已恢复（等了多少秒）"；15 分钟都不行才停止。

v6 相对 v5 的改动（11/06 12:32~14:22 三份日志：121 + 8 + 7 层）：
  · 现象：跑一阵后【某一个键】彻底失灵，其它键正常：14:02 起 ○ 连按十几次都没反应（停在装备页退不出去），
    14:11 和 14:21 两次都是跑了 7~8 轮后 □ 再也按不出"重置确认框"（✕、○、OPTIONS 照常），连续 3 轮失败停止；
    重启脚本后又能跑 7~8 轮。截图里没有 Chiaki 菜单。
  · 判断：Chiaki 收到了这个键的"按下"、丢了"松开"，以为它一直按着，之后的按下都无效；
    重启脚本会给所有键发"松开"，所以重启就好了。v5 把发键的事件源改成了私有源（为了清修饰键），之后才出现这种连续失灵。
  · 改：事件源换回 v4 的 HIDSystemState（修饰键照样清零）；每次按键前先补发一次"松开"；
    任何按键没反应要重试时（○ 打不开铃铛、□ 没弹框、OPTIONS 没开菜单、退不出界面、方向键光标不动），
    先把所有键松开一遍再按；□ 和 OPTIONS 重试次数 2 → 3。

v5 相对 v4 的改动（11/06 09:27~10:39 日志：99 轮叠加 96 层；尘埃 294,220 → 304,220 读对了）：
  · 10:39 起所有按键都没反应（OPTIONS ×2、○ ×3）→ "不在铃铛旁" 停止。截图底部出现 Chiaki-ng 自己的串流菜单
    （✕ / 音量 / Mic / Zoom / Stretch / Default / High Quality / Custom / Display，右下 Mbps / dropped frames）。
    这个菜单的快捷键是 ⌘O（Ctrl+O）/ 手柄 L1+R1+L3+R3；弹出期间键盘输入被菜单接走，PS5 收不到。
    根因：10:39:05.608 脚本正好发了 'o'（OPTIONS），而发键用的事件源会带上你当时实际按着的修饰键，
    你那一刻按着 ⌘ → Chiaki 收到 ⌘O → 打开了串流菜单。
    改①：发键改用私有事件源，并把修饰键标志清零（CGEventSetFlags(ev, 0)），脚本发的永远是"裸键"。
    改②（v5.1 补充：用户实测 ⌘O 能关掉菜单，检测到菜单后脚本自己发 ⌘O，最多 3 次，不行再等）：
    chiaki_overlay() 识别这个菜单（万一用户自己按出来）；每轮开头、每次失败、"打不开铃铛"停止前都检查一次。
    检测到 → 不发任何键；鼠标如果停在 Chiaki 窗口上就移回主屏中央；等菜单消失（最多 10 分钟）后继续，
    这一轮不计入连续失败；10 分钟还在 → 停止并提示。诊断模式也会打印"Chiaki 串流菜单：有/无"。

v4 相对 v3 的改动（11/06 09:22 日志，当时跑的还是 v2）：
  · 尘埃从 8 万多刷到 29 万后，数字变长、往左长，固定的读数框切掉了开头："304,220" 读成 4220
    → 误判"尘埃不够学海纳百川"→ 停止。
    改：读数框按画面里实际的数字位置自动找（从右往左合并字符，遇到 ✦ 图标前的大空隙停止）；每次读 3 次取多数；
    重置后尘埃比重置前还少 = 读错，不据此判断；"尘埃不够"要再读 5 次确认才停。

v3 相对 v2 的改动（11/05 23:55 ~ 11/06 08:58 三份日志：约 520 轮，成功 481 层，失败 65 轮）：
  · 【主要问题，62 轮】按了【能力修行】却进了【装备升级】。铃铛菜单从下往上淡入，v2 在菜单刚出现、
    只认出 ['买卖货物','能力修行','保存记忆','离开'] 时就开始操作，把第一个认出的行当成光标所在行，
    高亮又看不清 → 按推断按了 ✕，实际光标在【装备升级】。
    改：等 6 行都认出来（最多 3 秒，超时按行距补齐）；只有亲眼看到高亮在【能力修行】、隔 0.15 秒再确认一次
    才按 ✕，看不清就等，绝不按推断按 ✕。
  · 【1 轮】海纳百川其实学会了，但 OCR 把"已修行"读成"己修行"→ 按了 3 次后整轮作废。
    改：learned_text() 认 已/己/巳修行，或含"修行"但没有"按住/消耗/收集/完成"。
  · 【2 次】菜单刚打开时按键被吃掉，光标没动 → v2 误判"饰品区没有空格"/"列表里找不到聚宝盆"，后者直接停止了程序。
    改：格子移动连续 3 次没动才放弃、每次多等 0.3 秒；方向键按住 0.12 秒；进装备页后先等 0.6 秒；
    找不到饰品先算本轮失败，连续 2 轮找不到才停止。

v2 相对 v1 的改动（11/05 23:45 日志：连续 3 轮在铃铛菜单"高亮看不清"，没敢按 ✕ → 停止）：
  · 根因：这次的铃铛在暗室里（远眺龙柱处），菜单每一行背后都很暗，高亮行墨迹亮度 2、其它行 11~52，
    差值不到 v1 要求的 15。其实光标就在【能力修行】上（截图里 ✕ 图标在那一行）。
  · 高亮判断加"✕ 图标"判据：高亮行文字左边有白色 ✕ 圆圈（实拍 253 vs 其它 ≤70），和场景明暗无关；
    墨迹判据放宽为"差 ≥15，或最暗一行 ≤ 第二暗的 60%"。两个判据矛盾时才算看不清。
  · 看不清时存截图 debug/bell_unsure_*.jpg；屏蔽 EasyOCR 的 pin_memory 警告。

原理（玩家实测的游戏 BUG）：在铃铛【能力修行】里重置所有修行，会把【海纳百川·一式】多出来的饰品槽连同里面的饰品
强制卸下；重学节点、再把同一件饰品装回去，这件饰品的效果就多叠一层。没有界面显示叠了几层，没有上限。

一轮流程（对照 reference/README.md 的 00~15 号截图）：
  ① 野外铃铛旁按 ○ → 铃铛菜单 → 光标移到【能力修行】→ ✕
  ② 能力修行：□ 重置 →【将重置所有修行…】✕确定 →【饰品槽被重置，以上饰品已卸下】✕确定（尘埃 +10000）
  ③ 按 RELEARN_NODES 依次移到节点、按住 ✕ 修行（收放自如 0 尘埃 → 海纳百川·一式 10000 尘埃），确认"已修行"
  ④ ○ 回铃铛菜单 → ○ 回野外（还在菜单就选【离开】）
  ⑤ OPTIONS 打开暂停菜单【角色】→ 饰品行找到空格（标题"装备饰品"）→ ✕ → 列表里找到 TARGET_ACCESSORY → ✕
     → 确认这一格的标题就是目标饰品 → ○ 回野外
每一步都要"看到结果"再走下一步；看不清就不按 ✕；任何一步失败 → 退回野外、这一轮作废重来；
连续 3 轮失败 / 找不到饰品 / 尘埃不够 10000 / 不在铃铛旁 → 安全停止。

底层（后台截图、发键、冻结看门狗、内存保险丝、STOP 急停、日志）原样沿用 DD2 v28。
换饰品：只改下面的 TARGET_ACCESSORY。
"""
import os
import re
import sys
import ssl
import atexit
import time
import difflib
from datetime import datetime

import cv2
import numpy as np
import gc
import contextlib
try:
    import Quartz
    import objc
    from AppKit import NSWorkspace
    _pool = objc.autorelease_pool          # 用完立刻释放 Cocoa/Quartz 对象（防内存泄漏，DD2 v15 教训）
except ImportError:   # 离线测试环境没有 pyobjc；在 Mac 上运行时必须有
    Quartz = None
    NSWorkspace = None
    _pool = contextlib.nullcontext
import warnings
warnings.filterwarnings("ignore", message=".*pin_memory.*")   # v2：EasyOCR 在 MPS 上的无害警告
import easyocr

ssl._create_default_https_context = ssl._create_unverified_context

VERSION = "v7"

# =============================================================================
# ★ 最常改的设置
# =============================================================================
TARGET_ACCESSORY = "聚宝盆"          # ← 要叠加的饰品名字（和游戏里显示的一样）。换饰品只改这里
# 重置后要重学的节点（按顺序）：(节点名, OCR 可接受的片段)。光标从【黑石】开始，每个节点都是往右（→）找
RELEARN_NODES = [
    ("收放自如", ["收放", "放自", "自如"]),
    ("海纳百川", ["海纳", "纳百", "百川"]),     # 增加 1 个饰品槽位，消耗 10000 意识尘埃
]
SLOT_COST = 10000                   # 海纳百川·一式 的尘埃消耗；尘埃少于这个数 → 停止
HOLD_LEARN_SEC = 2.5                # 修行时按住 ✕ 的时长（视频约 1 秒，留余量）
FAIL_STREAK_STOP = 3                # 连续几轮失败 → 停止
KEY_DEAD_WAITS = [60, 120, 240, 480]  # v7：某个键失灵时，依次等这么多秒再试（共 15 分钟），还不行才停止
LOOP_TIMEOUT_SEC = 240              # 单轮最长时间（正常约 50~70 秒）

# ---------- 按键（与 Chiaki-ng → Settings → Keys 一致，沿用 DD2 那套）----------
K_CROSS, K_CIRCLE, K_SQUARE, K_OPTIONS = "/", "'", ";", "o"
K_UP, K_DOWN, K_LEFT, K_RIGHT = "i", "k", "j", "l"          # 十字键
K_L1, K_R1 = "q", "e"

# ---------- 路径 ----------
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()
DEBUG_DIR = os.path.join(BASE_DIR, "debug")
# OCR 模型：优先用本项目 assets/easyocr，其次直接用 DD2 项目里已有的那份，都没有才联网下载到 ~/.EasyOCR
OCR_MODEL_DIRS = [os.path.join(BASE_DIR, "assets", "easyocr"),
                  os.path.join(os.path.dirname(BASE_DIR), "DragonsDogma2", "assets", "easyocr")]
MEM_WARN_GB, MEM_STOP_GB = 6.0, 12.0
STOP_FILE = os.path.join(BASE_DIR, "STOP")   # 双击 stop_bot.command 会在这里新建 STOP 文件 → 安全停止

ALL_KEYS = ['/', "'", ';', 'o', 'i', 'k', 'j', 'l', 'q', 'e', 'w', 'a', 's', 'd']
MAC_KEYCODES = {
    'a': 0, 's': 1, 'd': 2, 'q': 12, 'w': 13, 'e': 14, 'r': 15, 't': 17, 'o': 31, '[': 33, 'i': 34,
    'l': 37, 'j': 38, "'": 39, 'k': 40, ';': 41, '/': 44, 'tab': 48, 'left': 123, 'right': 124,
    'down': 125, 'up': 126,
}
CANON_W, CANON_H = 2880, 1800          # 沿用 DD2：视频 2880x1620，上下各 90 像素黑边
CANON_VID_H, CANON_VID_Y = 1620, 90

# =============================================================================
# 界面区域（视频画面的比例坐标 x1, y1, x2, y2；按 11/05 录屏 1920x1080 实测）
# =============================================================================
ROI_TABS = (0.25, 0.02, 0.76, 0.08)          # 暂停菜单顶部 地图/任务/角色/道具/读物/系统
ROI_LEFT_HEADER = (0.13, 0.19, 0.30, 0.24)   # 暂停菜单左侧小标题：装备页="装备"，饰品列表="全部"
ROI_EQ_TITLE = (0.655, 0.185, 0.95, 0.25)    # 装备页/列表 右侧物品标题（"装备饰品" / "聚宝盆"）
ROI_TREE_TITLE = (0.70, 0.17, 0.98, 0.24)    # 能力修行 右侧节点标题（"黑石" / "收放自如" / "海纳百川·一式"）
ROI_TREE_BAR = (0.72, 0.82, 0.96, 0.87)      # 能力修行 右下按钮条（"按住✕消耗✦10000 完成修行" / "已修行"）
ROI_TREE_HINT = (0.80, 0.92, 0.98, 0.98)     # 能力修行 右下角 "□重置 ○返回"
ROI_DUST = (0.912, 0.025, 0.975, 0.07)       # 右上角意识尘埃数（不含左边的 ✦ 图标）（修行页和暂停菜单都在这里）
ROI_DIALOG = (0.25, 0.28, 0.75, 0.50)        # 两种确认框的正文
ROI_BELL = (0.30, 0.55, 0.80, 0.97)          # 铃铛菜单（6 行）
ROI_CHIAKI_MENU_L = (0.0, 0.91, 0.42, 0.99)   # v5：Chiaki-ng 串流菜单 左下（Mic / Zoom / Stretch / Display）
ROI_CHIAKI_MENU_R = (0.80, 0.92, 1.0, 0.995)  # v5：Chiaki-ng 串流菜单 右下（Mbps / Connected to / dropped frames）
CHIAKI_MENU_WAIT_SEC = 600                    # v5：Chiaki 菜单最多等它消失多久
BELL_LABELS = ["穿行", "装备升级", "买卖货物", "能力修行", "保存记忆", "离开"]
BELL_FALLBACK_YS = [0.657, 0.703, 0.748, 0.794, 0.840, 0.886]   # OCR 找不到行时用的固定位置
BELL_FALLBACK_X = 0.482
# 装备页格子中心：列 x，行 y（行 0/1 = 武器区，行 2/3 = 饰品区；第 4 行目前是锁住的格子）
EQ_XS = [0.107, 0.182, 0.258]
EQ_YS = [0.375, 0.497, 0.683, 0.805]
ACC_ROWS = [2, 3]
# 饰品列表格子中心
LIST_XS = [0.120, 0.183, 0.247]
LIST_YS = [0.300, 0.415, 0.530, 0.645, 0.760]
CELL_HALF = (0.02, 0.035)

# =============================================================================
# 异常 / 通用工具
# =============================================================================
class StopRequested(Exception):
    pass


class ChiakiNotReady(Exception):
    pass


class MemoryGuardException(Exception):
    pass


class StreamResumed(Exception):
    """画面冻结后又恢复了：冻结期间的操作都是盲操作 → 这一轮作废重来"""


class LoopFailed(Exception):
    """这一轮某一步没成功 → 退回野外，这一轮作废"""


class KeyDead(LoopFailed):
    """v7：某个键连按好几次（中间松开所有键）都没反应。不是画面识别的问题 → 退回野外、等一段时间再试"""


class FatalStop(Exception):
    """继续跑没有意义的情况（不在铃铛旁 / 找不到饰品 / 尘埃不够 / 连续失败）→ 停止程序"""


def debug_log(msg):
    now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{now_str}] {msg}", flush=True)


def sep(ch="-", n=70):
    print("\n" + ch * n, flush=True)


def current_rss_gb():
    try:
        import subprocess
        kb = float(subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())], text=True).strip())
        return kb / 1024 / 1024
    except Exception:
        return -1.0


def zh_hit(text, frags, min_ratio=0.67):
    """中文模糊匹配：text 里含任一片段即命中；否则和每个片段做相似度（OCR 错一个字也能命中）"""
    t = re.sub(r"\s+", "", str(text or ""))
    if not t:
        return False
    if isinstance(frags, str):
        frags = [frags]
    for f in frags:
        if f in t:
            return True
    for f in frags:
        n = len(f)
        if n < 2:
            continue
        for i in range(0, max(1, len(t) - n + 1)):
            if difflib.SequenceMatcher(None, t[i:i + n], f).ratio() >= min_ratio and n >= 3:
                return True
    return False


def target_frags(name):
    """饰品名 → OCR 片段：整名 + 每两个相邻字（3 个字以上的名字错一个字也能认出）"""
    name = re.sub(r"\s+", "", name)
    frags = [name]
    if len(name) >= 3:
        frags += [name[i:i + 2] for i in range(len(name) - 1)]
    return frags


def learned_text(bar):
    """v3：按钮条是不是"已修行"。OCR 常把 已 读成 己 / 巳（11/06 04:56 日志："己修行" 被当成没学会，按了 3 次后整轮作废）。
    判据：X修行（X = 已/己/巳/e），或含"修行"但没有"按住"/"消耗"/"收集"（没学时的按钮条一定有这些字）"""
    t = re.sub(r"\s+", "", str(bar or ""))
    if re.search(r"[已己巳]修行", t):
        return True
    return "修行" in t and not any(k in t for k in ("按住", "消耗", "收集", "完成"))


def roi_px(shape, roi):
    H, W = shape[:2]
    x1, y1, x2, y2 = roi
    return int(x1 * W), int(y1 * H), int(x2 * W), int(y2 * H)


class Frame:
    """一帧视频画面（2880x1620，已去掉 DD2 那套统一坐标里的上下黑边）"""

    def __init__(self, bgr):
        self.bgr = bgr
        self.gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        self.H, self.W = bgr.shape[:2]

    def crop(self, roi, gray=False):
        x1, y1, x2, y2 = roi_px(self.bgr.shape, roi)
        return (self.gray if gray else self.bgr)[y1:y2, x1:x2]

    def region_median(self, x1, y1, x2, y2):
        a = self.gray[max(0, int(y1 * self.H)):int(y2 * self.H), max(0, int(x1 * self.W)):int(x2 * self.W)]
        return float(np.median(a)) if a.size else 0.0


def grid_cursor(fr, xs, ys, min_val=95.0, margin=30.0):
    """格子光标：选中的格子是白底，中位亮度明显高于其它格子（实测 123~142 vs ≤92）。
    返回 ((行, 列) 或 None, 亮度表)"""
    vals = {}
    for r, y in enumerate(ys):
        for c, x in enumerate(xs):
            vals[(r, c)] = fr.region_median(x - CELL_HALF[0], y - CELL_HALF[1], x + CELL_HALF[0], y + CELL_HALF[1])
    order = sorted(vals, key=vals.get, reverse=True)
    best, second = vals[order[0]], vals[order[1]]
    if best >= min_val and best - second >= margin:
        return order[0], vals
    return None, vals


# =============================================================================
# 后台截图 + 发键（原样沿用 DD2 v28）
# =============================================================================
class ChiakiBackend:
    """找到 Chiaki 窗口；截图时去掉标题栏、按 16:9 找出视频区域，再还原成全屏时的 2880x1800 画面"""
    TITLEBAR_PT = 28

    def __init__(self):
        if Quartz is None:
            raise ChiakiNotReady("缺少 pyobjc：pip install pyobjc-framework-Quartz pyobjc-framework-Cocoa")
        self.pid, self.wid, self.bounds, self.app = None, None, None, None
        # ---- 画面冻结看门狗 ----
        self.freeze_sec = 8.0          # 发了按键后画面 8 秒完全不变 → 冻结
        self.freeze_min_keys = 2
        self.last_thumb = None
        self.last_change_t = time.time()
        self.keys_since_change = 0
        self.in_freeze_handler = False
        self.activate_on_freeze = False   # True = 冻结 20s 后把 Chiaki 调到前台（旧行为，会抢焦点）
        self.freeze_wait_max = 600.0      # 不调前台时最多原地等 10 分钟
        self.refresh()

    def refresh(self):
        with _pool():
            self._refresh()

    def _refresh(self):
        self.pid = None
        for app in NSWorkspace.sharedWorkspace().runningApplications():
            if "chiaki" in (app.localizedName() or "").lower():
                self.pid = app.processIdentifier()
                self.app = app
                break
        if self.pid is None:
            raise ChiakiNotReady("没找到运行中的 Chiaki")
        wins = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionAll, Quartz.kCGNullWindowID) or []
        best, area = None, 0
        for w in wins:
            if w.get(Quartz.kCGWindowOwnerPID) != self.pid or w.get(Quartz.kCGWindowLayer, 0) != 0:
                continue
            b = w.get(Quartz.kCGWindowBounds) or {}
            ar = float(b.get("Width", 0)) * float(b.get("Height", 0))
            if ar > area:
                best, area = w, ar
        if best is None or area < 200 * 120:
            raise ChiakiNotReady("找到 Chiaki 进程，但没有串流窗口（还没开始串流，或窗口被最小化了）")
        self.wid = best[Quartz.kCGWindowNumber]
        self.bounds = dict(best[Quartz.kCGWindowBounds])

    def capture_raw(self):
        with _pool():   # v15：截图对象在这里用完立即释放（之前没有释放池 → 每张 18MB 一直不归还）
            img = Quartz.CGWindowListCreateImage(
                Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow, self.wid,
                Quartz.kCGWindowImageBoundsIgnoreFraming | Quartz.kCGWindowImageBestResolution)
            if img is None:
                return None
            w, h = Quartz.CGImageGetWidth(img), Quartz.CGImageGetHeight(img)
            if w < 50 or h < 50:
                return None
            bpr = Quartz.CGImageGetBytesPerRow(img)
            data = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(img))
            try:
                buf = np.frombuffer(data, np.uint8)
            except TypeError:   # 个别 pyobjc 版本 NSData 不支持缓冲区协议 → 退回复制一次
                buf = np.frombuffer(bytes(data), np.uint8)
            arr = buf.reshape((h, bpr // 4, 4))[:, :w, :3]
            out = np.ascontiguousarray(arr)   # 只复制需要的 BGR 部分，之后 data / img 随释放池一起释放
            del arr, buf, data, img
            return out

    def video_rect(self, raw):
        """返回 (x, y, w, h)：窗口截图里视频所在的矩形"""
        H, W = raw.shape[:2]
        scale = W / max(1.0, float(self.bounds.get("Width", W)))
        tb = int(round(self.TITLEBAR_PT * scale))
        strip = raw[:tb] if tb > 0 else None
        if (tb >= H // 3 or strip is None or float(strip.mean()) < 150 or float(strip.std()) > 12
                or abs(W / H - 16 / 9) < 0.001):   # 不是"又亮又均匀"的标题栏，或画面本身就是 16:9（全屏）→ 不裁
            tb = 0
        ch = H - tb
        if W / ch > 16 / 9:   # 窗口比视频宽 → 左右黑边
            vh, vw = ch, int(round(ch * 16 / 9))
            return (W - vw) // 2, tb, vw, vh
        vw, vh = W, int(round(W * 9 / 16))
        return 0, tb + (ch - vh) // 2, vw, vh

    def grab_canonical(self):
        raw = self.capture_raw()
        if raw is None:
            self.refresh()
            raw = self.capture_raw()
            if raw is None:
                raise ChiakiNotReady("截不到 Chiaki 窗口（屏幕录制权限？窗口被最小化？）")
        x, y, w, h = self.video_rect(raw)
        vid = raw[y:y + h, x:x + w]
        if not self.in_freeze_handler:
            self.watch_freeze(vid)
        out = np.zeros((CANON_H, CANON_W, 3), np.uint8)
        out[CANON_VID_Y:CANON_VID_Y + CANON_VID_H] = cv2.resize(
            vid, (CANON_W, CANON_VID_H), interpolation=cv2.INTER_AREA if w > CANON_W else cv2.INTER_LINEAR)
        return out, (raw.shape[1], raw.shape[0], x, y, w, h)

    # ------------------------------------------------------------------
    # 画面冻结看门狗
    # ------------------------------------------------------------------
    @staticmethod
    def _thumb(vid):
        return cv2.resize(cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY), (160, 90),
                          interpolation=cv2.INTER_AREA).astype(np.float32)

    def frame_changed(self, vid):
        """和上一帧比较：真实串流（风、雾、人物呼吸、视频压缩噪点）几乎不可能连续 8 秒像素级不变"""
        th = self._thumb(vid)
        prev, self.last_thumb = self.last_thumb, th
        if prev is None or prev.shape != th.shape:
            return True
        return float(np.mean(np.abs(th - prev))) > 0.05

    def watch_freeze(self, vid):
        now = time.time()
        if self.frame_changed(vid):
            self.last_change_t, self.keys_since_change = now, 0
            return
        if now - self.last_change_t >= self.freeze_sec and self.keys_since_change >= self.freeze_min_keys:
            self.handle_freeze(vid, reason=f"发出 {self.keys_since_change} 次按键后画面 "
                                           f"{now - self.last_change_t:.0f}s 完全没变")

    def window_diagnosis(self):
        with _pool():
            return self._window_diagnosis()

    def _window_diagnosis(self):
        parts = []
        try:
            info = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionIncludingWindow, self.wid) or []
            if not info:
                parts.append("窗口已不存在（Chiaki 断开串流了？）")
            else:
                w = info[0]
                onscreen = bool(w.get(Quartz.kCGWindowIsOnscreen, False))
                parts.append("窗口在当前桌面上" if onscreen else "❗窗口不在当前桌面（被最小化 / 全屏到单独桌面 / 在别的桌面）")
            if self.app is not None and self.app.isHidden():
                parts.append("❗Chiaki 被隐藏了（⌘H）")
            front = NSWorkspace.sharedWorkspace().frontmostApplication()
            parts.append(f"当前前台程序={front.localizedName() if front else '?'}")
            # 看 Chiaki 窗口有没有被别的窗口整个盖住
            above = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenAboveWindow, self.wid) or []
            b = self.bounds or {}
            bx, by = float(b.get("X", 0)), float(b.get("Y", 0))
            bw, bh = float(b.get("Width", 0)), float(b.get("Height", 0))
            for o in above:
                if o.get(Quartz.kCGWindowLayer, 0) != 0:
                    continue
                ob = o.get(Quartz.kCGWindowBounds) or {}
                ox, oy = float(ob.get("X", 0)), float(ob.get("Y", 0))
                ow, oh = float(ob.get("Width", 0)), float(ob.get("Height", 0))
                if ox <= bx + 2 and oy <= by + 2 and ox + ow >= bx + bw - 2 and oy + oh >= by + bh - 2:
                    parts.append(f"❗Chiaki 窗口被【{o.get(Quartz.kCGWindowOwnerName, '?')}】整个盖住了")
                    break
        except Exception as e:
            parts.append(f"诊断出错: {e}")
        return "；".join(parts)

    def _wait_unfreeze(self, seconds):
        """等画面重新动起来；期间检查 STOP 文件"""
        t0 = time.time()
        while time.time() - t0 < seconds:
            if os.path.exists(STOP_FILE):
                raise StopRequested("检测到 STOP 文件")
            time.sleep(1.0)
            raw = self.capture_raw()
            if raw is None:
                try:
                    self.refresh()
                except ChiakiNotReady:
                    continue
                continue
            x, y, w, h = self.video_rect(raw)
            if self.frame_changed(raw[y:y + h, x:x + w]):
                return True
        return False

    def handle_freeze(self, vid, reason=""):
        self.in_freeze_handler = True
        try:
            release_everything()
            debug_log(f"🧊 [画面冻结] {reason}")
            debug_log(f"🧊 [画面冻结] 窗口诊断：{self.window_diagnosis()}")
            # [调试用，已停用] 保存冻结画面到 debug/frozen_*.jpg —— 需要排查时去掉下面几行的 #
            # try:
            #     path = out_path(f"frozen_{datetime.now().strftime('%H%M%S')}.jpg", DEBUG_DIR)
            #     cv2.imwrite(path, cv2.resize(vid, None, fx=0.5, fy=0.5))
            #     debug_log(f"🧊 [画面冻结] 冻结画面已保存: {path}")
            # except Exception:
            #     pass
            debug_log("🧊 [画面冻结] 常见原因：Chiaki 窗口被其它窗口【完全】挡住 / 被最小化或隐藏 / 全屏到单独桌面 / "
                      "显示器睡眠或锁屏 / 串流断开。根治：把 Chiaki 放到 BetterDisplay 虚拟屏上。")
            if not self.activate_on_freeze:
                debug_log(f"🧊 [画面冻结] 原地暂停等待画面恢复（不会把 Chiaki 调到前台；最多 {self.freeze_wait_max / 60:.0f} 分钟）...")
                t0, ok = time.time(), False
                while time.time() - t0 < self.freeze_wait_max:
                    if self._wait_unfreeze(30):
                        ok = True
                        break
                    debug_log(f"🧊 [画面冻结] 已等 {time.time() - t0:.0f}s 仍冻结 | {self.window_diagnosis()}")
                if not ok:
                    raise ChiakiNotReady(f"Chiaki 画面冻结超过 {self.freeze_wait_max / 60:.0f} 分钟，停止运行")
                debug_log("✅ [画面冻结] 画面已恢复刷新 → 冻结期间的操作作废，从本轮开头重新开始")
                self.last_change_t, self.keys_since_change = time.time(), 0
                raise StreamResumed("画面冻结后恢复")
            debug_log("🧊 [画面冻结] 等 20 秒看能否自己恢复...")
            ok = self._wait_unfreeze(20)
            if not ok:
                debug_log("🧊 [画面冻结] 仍未恢复 → 把 Chiaki 窗口调到前台（只在冻结时这样做）")
                try:
                    self.refresh()
                    if self.app is not None:
                        if self.app.isHidden():
                            self.app.unhide()
                        self.app.activateWithOptions_(2)   # NSApplicationActivateIgnoringOtherApps
                except Exception as e:
                    debug_log(f"🧊 [画面冻结] 调到前台失败: {e}")
                ok = self._wait_unfreeze(40)
            if not ok:
                raise ChiakiNotReady("Chiaki 画面持续冻结超过 60 秒（串流断开 / 窗口最小化 / 锁屏？），停止运行，"
                                     "冻结期间不能盲操作")
            debug_log("✅ [画面冻结] 画面已恢复刷新 → 冻结期间的操作作废，从本轮开头重新开始")
            self.last_change_t, self.keys_since_change = time.time(), 0
            raise StreamResumed("画面冻结后恢复")
        finally:
            self.in_freeze_handler = False

    def display_info(self):
        """Chiaki 窗口所在的屏幕：名字、是否内建、像素分辨率"""
        try:
            b = self.bounds
            rect = Quartz.CGRectMake(float(b["X"]), float(b["Y"]), float(b["Width"]), float(b["Height"]))
            err, ids, cnt = Quartz.CGGetDisplaysWithRect(rect, 4, None, None)
            if not cnt:
                return "未知屏幕"
            did = ids[0]
            name = ""
            try:
                from AppKit import NSScreen
                for sc in NSScreen.screens():
                    if int(sc.deviceDescription()["NSScreenNumber"]) == int(did):
                        name = str(sc.localizedName())
            except Exception:
                pass
            mode = Quartz.CGDisplayCopyDisplayMode(did)
            px = f"{Quartz.CGDisplayModeGetPixelWidth(mode)}x{Quartz.CGDisplayModeGetPixelHeight(mode)}px" if mode else "?"
            pt = f"{int(Quartz.CGDisplayPixelsWide(did))}x{int(Quartz.CGDisplayPixelsHigh(did))}pt"
            kind = "内建屏" if Quartz.CGDisplayIsBuiltin(did) else "外接/虚拟屏"
            main = "（主屏）" if Quartz.CGDisplayIsMain(did) else ""
            return f"{name or '屏幕'} #{did} {kind}{main} {pt} / {px}" + (f" | 窗口跨 {cnt} 块屏" if cnt > 1 else "")
        except Exception as e:
            return f"无法获取屏幕信息: {e}"

    def startup_freeze_check(self):
        """启动时先确认画面在刷新（不发任何按键，看 3 秒）；冻结则走冻结处理流程"""
        for _ in range(12):
            raw = self.capture_raw()
            if raw is not None:
                x, y, w, h = self.video_rect(raw)
                if self.frame_changed(raw[y:y + h, x:x + w]) and self.last_thumb is not None and _ > 0:
                    debug_log("✅ [启动检查] Chiaki 画面正在刷新")
                    self.last_change_t, self.keys_since_change = time.time(), 0
                    return
            time.sleep(0.25)
        try:
            self.handle_freeze(raw[y:y + h, x:x + w] if raw is not None else np.zeros((90, 160, 3), np.uint8),
                               reason="启动时 3 秒内画面完全没变")
        except StreamResumed:
            pass

    def key(self, name, down):
        if down:
            self.keys_since_change += 1
        code = MAC_KEYCODES[name]
        with _pool():
            # v5：用"私有"事件源并把修饰键清零。原来用 HIDSystemState，发出的按键会带上你当时实际按着的修饰键：
            # 你正好按着 ⌘ 时脚本发 'o' → Chiaki 收到 ⌘O = 打开串流菜单（11/06 10:39），⌘Q 甚至会退出 Chiaki。
            # v6：事件源换回 v4 及以前用的 HIDSystemState（v4 之前连跑 600+ 轮没出现"某个键一直失灵"），
            # 修饰键仍然清零（v5 的修复保留）
            src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
            ev = Quartz.CGEventCreateKeyboardEvent(src, code, bool(down))
            Quartz.CGEventSetFlags(ev, 0)
            Quartz.CGEventPostToPid(self.pid, ev)


class _KB:
    """替代 pyautogui 的 keyDown/keyUp：按键只发给 Chiaki；每次按键前检查 STOP 文件"""
    backend = None

    @classmethod
    def keyDown(cls, k):
        if os.path.exists(STOP_FILE):
            raise StopRequested("检测到 STOP 文件")
        cls.backend.key(k, True)

    @classmethod
    def keyUp(cls, k):
        cls.backend.key(k, False)


KB = _KB


# =============================================================================

# =============================================================================
# 运行日志：终端输出同时另存到 debug/logs/（原样沿用 DD2 v28）
# =============================================================================
LOG_DIR = os.path.join(DEBUG_DIR, "logs")
LOG_KEEP = 30


class _Tee:
    """把写到终端的内容同时写进日志文件（每次写入都 flush，脚本被强行停掉也不丢）"""

    def __init__(self, stream, fh):
        self.stream, self.fh = stream, fh

    def write(self, data):
        try:
            self.stream.write(data)
        except Exception:
            pass
        try:
            self.fh.write(data)
            self.fh.flush()
        except Exception:
            pass
        return len(data)

    def flush(self):
        for x in (self.stream, self.fh):
            try:
                x.flush()
            except Exception:
                pass

    def __getattr__(self, name):   # isatty / encoding 等交给原始终端
        return getattr(self.stream, name)


class RunLog:
    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        self.path = os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.fh = open(self.path, "w", encoding="utf-8")
        self._out, self._err = sys.stdout, sys.stderr
        sys.stdout = _Tee(self._out, self.fh)
        sys.stderr = _Tee(self._err, self.fh)   # 报错的 Traceback 也会记进去
        atexit.register(self.close)
        self._prune()

    def note(self, text):
        """记录用户在 input() 里输入的内容（PyCharm 控制台的输入不经过 stdout）"""
        self.fh.write(f"[输入] {text}\n")
        self.fh.flush()

    def tag(self, label):
        """按运行模式给日志改名，如 run_20261019_120501_mode7.log，方便找"""
        new = self.path.replace(".log", f"_{label}.log")
        try:
            os.rename(self.path, new)   # macOS 下文件打开着也能改名，写入不受影响
            self.path = new
        except OSError:
            pass

    def close(self):
        if sys.stdout is not self._out:
            sys.stdout, sys.stderr = self._out, self._err
        try:
            self.fh.close()
        except Exception:
            pass

    @staticmethod
    def _prune():
        logs = sorted(f for f in os.listdir(LOG_DIR) if f.startswith("run_") and f.endswith(".log"))
        for f in logs[:-LOG_KEEP]:
            try:
                os.remove(os.path.join(LOG_DIR, f))
            except OSError:
                pass


def release_everything():
    """停止/异常后，给 Chiaki 发送所有按键的松开事件，避免角色一直走或一直转"""
    if KB.backend is None:
        return
    for k in ALL_KEYS:
        try:
            KB.keyUp(k)
        except Exception:
            pass



# =============================================================================
# 主体
# =============================================================================
class PBZAccessoryBot:
    def __init__(self):
        debug_log(f"🔧 正在初始化 影之刃零 饰品叠加脚本 {VERSION}（后台模式）...")
        debug_log(f"🎯 目标饰品：【{TARGET_ACCESSORY}】 | 重学节点：{' → '.join(n for n, _ in RELEARN_NODES)}")
        self.target_frags = target_frags(TARGET_ACCESSORY)
        debug_log("⏳ 正在初始化 EasyOCR 引擎...")
        model_dir = next((d for d in OCR_MODEL_DIRS
                          if all(os.path.exists(os.path.join(d, f)) for f in ("craft_mlt_25k.pth", "zh_sim_g2.pth"))), None)
        if model_dir:
            self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=True, model_storage_directory=model_dir,
                                         download_enabled=False)
            debug_log(f"✅ EasyOCR 加载完毕（模型：{model_dir}）")
        else:
            self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
            debug_log("✅ EasyOCR 加载完毕（模型：~/.EasyOCR）")
        self.backend = ChiakiBackend()
        # 菜单画面大多是静止的：放宽冻结判定，避免把"静止的菜单"当成冻结（25s 内按了 6 次键画面都没变才算）
        self.backend.freeze_sec = 25.0
        self.backend.freeze_min_keys = 6
        KB.backend = self.backend
        _, info = self.backend.grab_canonical()
        rw, rh, vx, vy, vw, vh = info
        debug_log(f"🖥️ [后台模式] Chiaki PID={self.backend.pid} 窗口ID={self.backend.wid} | 截图 {rw}x{rh}px | "
                  f"视频区域 x={vx} y={vy} {vw}x{vh}")
        debug_log(f"🖥️ [后台模式] Chiaki 窗口所在屏幕: {self.backend.display_info()}")
        self.backend.startup_freeze_check()
        if vw < 1600:
            debug_log("⚠️ Chiaki 窗口偏小，文字识别可能变差")
        self.loops_ok = 0
        self.fail_streak = 0
        self.not_found_streak = 0
        self.key_dead_streak = 0

    # =========================================================================
    # 截图 / OCR / 按键
    # =========================================================================
    def grab(self):
        if os.path.exists(STOP_FILE):
            raise StopRequested("检测到 STOP 文件")
        canon, _ = self.backend.grab_canonical()
        return Frame(np.ascontiguousarray(canon[CANON_VID_Y:CANON_VID_Y + CANON_VID_H, :, :3]))

    def ocr_boxes(self, fr, roi, scale=0.6, allowlist=None):
        """带文字检测的 OCR。返回 [(文字, (x1,y1,x2,y2) 视频比例坐标)]"""
        img = fr.crop(roi)
        if img.size == 0:
            return []
        if scale != 1.0:
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        try:
            res = self.reader.readtext(img, detail=1, paragraph=False, allowlist=allowlist)
        except Exception as e:
            debug_log(f"    ⚠️ OCR 异常: {e}")
            return []
        rx1, ry1, rx2, ry2 = roi
        out = []
        for box, text, conf in res:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            sx, sy = (rx2 - rx1) / img.shape[1], (ry2 - ry1) / img.shape[0]
            out.append((str(text).replace(" ", ""),
                        (rx1 + min(xs) * sx, ry1 + min(ys) * sy, rx1 + max(xs) * sx, ry1 + max(ys) * sy)))
        return out

    def ocr_text(self, fr, roi, scale=0.6, allowlist=None):
        return "".join(t for t, _ in self.ocr_boxes(fr, roi, scale=scale, allowlist=allowlist))

    @staticmethod
    def dust_roi(fr):
        """v4：右上角尘埃数是右对齐的（右边缘固定在 x≈0.949），位数变多会往左长，v3 的固定框会切掉开头的数字
        （11/06 09:22：304,220 被切成 "04,220" → 读成 4220 → 误判尘埃不够、停止）。
        做法：在 0.84~0.975 里按列找文字块，从最右边往左合并（字间距 ≤12px），遇到大空隙（✦ 图标前约 26px）就停。"""
        x1, y1, x2, y2 = 0.84, 0.025, 0.975, 0.07
        a = fr.crop((x1, y1, x2, y2), gray=True).astype(np.float32)
        if a.size == 0:
            return ROI_DUST
        bg = float(np.median(a))
        cols = (np.abs(a - bg) > 45).sum(0) >= 2
        segs, inside, s0 = [], False, 0
        for i, c in enumerate(cols):
            if c and not inside:
                s0, inside = i, True
            elif not c and inside:
                segs.append((s0, i))
                inside = False
        if inside:
            segs.append((s0, len(cols)))
        if not segs:
            return ROI_DUST
        max_gap = 12 * fr.W / 2880.0
        left, right = segs[-1]
        for s, e in reversed(segs[:-1]):
            if left - e > max_gap:
                break
            left = s
        pad = 8
        w = a.shape[1]
        return (x1 + max(0, left - pad) / w * (x2 - x1), y1, x1 + min(w, right + pad) / w * (x2 - x1), y2)

    def read_dust_once(self, fr):
        t = self.ocr_text(fr, self.dust_roi(fr), scale=1.0, allowlist="0123456789,.")
        digits = re.sub(r"[^0-9]", "", t)
        return int(digits) if 3 <= len(digits) <= 9 else None

    def read_dust(self, fr=None, tries=3):
        """v4：读 3 次（每次重新截图），取出现最多的值；读不出返回 None"""
        vals = []
        for i in range(tries):
            f = fr if (fr is not None and i == 0) else self.grab()
            v = self.read_dust_once(f)
            if v is not None:
                vals.append(v)
            if len(vals) >= 2 and vals[-1] == vals[-2]:
                return vals[-1]
            time.sleep(0.15)
        if not vals:
            return None
        return max(set(vals), key=vals.count)

    @staticmethod
    def tap(key, hold=0.08, wait=0.45, quiet=False):
        if not quiet:
            debug_log(f"    ⌨️ [{key}]")
        # v6：按下前先补发一次"松开"。如果 Chiaki 以为这个键还按着（松开事件丢了），
        # 新的按下会被当成"一直按着"而无效 → 这个键从此失灵，直到重启脚本（11/06 14:11、14:21 的 □）
        KB.keyUp(key)
        time.sleep(0.03)
        KB.keyDown(key)
        time.sleep(hold)
        KB.keyUp(key)
        time.sleep(wait)

    def unstick(self, why=""):
        """v6：按键没反应时，先把所有键松开一遍再重试（清掉 Chiaki 里"卡住"的键）"""
        debug_log(f"    🔓 按键没反应{('（' + why + '）') if why else ''} → 松开所有键后重试")
        release_everything()
        time.sleep(0.3)

    @staticmethod
    def hold(key, sec, wait=0.6):
        debug_log(f"    ⌨️ [长按 {key}] {sec:.1f}s")
        KB.keyDown(key)
        try:
            t0 = time.time()
            while time.time() - t0 < sec:
                if os.path.exists(STOP_FILE):
                    raise StopRequested("检测到 STOP 文件")
                time.sleep(0.05)
        finally:
            KB.keyUp(key)
        time.sleep(wait)

    def wait_for(self, pred, timeout=5.0, interval=0.3, desc=""):
        """每 interval 秒看一次画面，pred(fr) 为真就返回那一帧；超时返回 None"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            fr = self.grab()
            if pred(fr):
                return fr
            time.sleep(interval)
        if desc:
            debug_log(f"    ⏱️ 等待【{desc}】超时 {timeout:.0f}s")
        return None

    def save_debug_frame(self, tag, fr=None):
        try:
            fr = fr or self.grab()
            path = os.path.join(DEBUG_DIR, f"{tag}_{datetime.now().strftime('%m%d_%H%M%S')}.jpg")
            os.makedirs(DEBUG_DIR, exist_ok=True)
            cv2.imwrite(path, cv2.resize(fr.bgr, None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 85])
            debug_log(f"    📸 截图已保存: {path}")
        except Exception as e:
            debug_log(f"    ⚠️ 保存截图失败: {e}")

    # =========================================================================
    # 界面识别（只看固定位置的 UI 文字 / 背景，不看 3D 场景）
    # =========================================================================
    def is_pause(self, fr):
        t = self.ocr_text(fr, ROI_TABS)
        return sum(k in t for k in ("地图", "任务", "角色", "道具", "读物", "系统")) >= 2

    def pause_page(self, fr):
        """'equip' 装备页 / 'list' 饰品列表 / 'other' 别的页"""
        t = self.ocr_text(fr, ROI_LEFT_HEADER, scale=1.0)
        if "全部" in t:
            return "list"
        if "装备" in t:
            return "equip"
        return "other"

    @staticmethod
    def parchment(fr):
        """能力修行是一张亮色宣纸：左侧（0.03~0.15）中位亮度 92~110；野外/暂停菜单实测 41~53"""
        return fr.region_median(0.03, 0.30, 0.15, 0.70) >= 85

    def is_tree(self, fr):
        if not self.parchment(fr):
            return False
        return "返回" in self.ocr_text(fr, ROI_TREE_HINT, scale=1.0)

    def dialog_kind(self, fr):
        """'reset' 将重置所有修行 / 'slot' 饰品槽被重置 / None"""
        t = self.ocr_text(fr, ROI_DIALOG)
        if zh_hit(t, ["重置所有", "所有修行", "返还全部", "是否继续"]):
            return "reset"
        if zh_hit(t, ["饰品槽", "槽被重置", "已卸下", "以上饰品"]):
            return "slot"
        return None

    def bell_rows(self, fr):
        """铃铛菜单：OCR 找出各行文字的位置。返回 {行名: (x1, y中心)}（视频比例）"""
        rows = {}
        for text, (x1, y1, x2, y2) in self.ocr_boxes(fr, ROI_BELL):
            for lab in BELL_LABELS:
                if lab not in rows and zh_hit(text, [lab] + ([lab[:2], lab[2:]] if len(lab) == 4 else [])):
                    rows[lab] = (x1, (y1 + y2) / 2)
        return rows

    def is_bell(self, fr, rows=None):
        rows = rows if rows is not None else self.bell_rows(fr)
        return len(rows) >= 3 and ("能力修行" in rows or "离开" in rows)

    @staticmethod
    def bell_highlight(fr, rows):
        """v2：两个判据。
          ① ✕ 图标：高亮行文字左边有一个白色 ✕ 圆圈 —— 每行取文字左侧小框的 97% 分位亮度，
             最亮的一行比第二亮高 ≥30 就是它（11/05 23:45 实拍：253 vs ≤70；录屏：151 vs ≤116）。
          ② 墨迹：高亮行背后的墨迹最暗。暗场景里各行都很暗（11/05 日志：2 vs 11~52），所以除了
             差值 ≥15，"最暗一行 ≤ 第二暗的 60% 且差 ≥5" 也算。
        两个判据都给出答案但不一致 → 看不清。返回 (行名 或 None, {行名: (图标亮度, 墨迹亮度)})"""
        icon, band = {}, {}
        for lab, (x1, yc) in rows.items():
            a = fr.gray[max(0, int((yc - 0.014) * fr.H)):int((yc + 0.014) * fr.H),
                        max(0, int((x1 - 0.034) * fr.W)):int((x1 - 0.010) * fr.W)]
            icon[lab] = float(np.percentile(a, 97)) if a.size else 0.0
            band[lab] = fr.region_median(x1 - 0.005, yc - 0.012, x1 + 0.07, yc + 0.012)
        vals = {lab: (int(icon[lab]), int(band[lab])) for lab in rows}
        if len(rows) < 2:
            return None, vals
        hi = sorted(icon, key=icon.get, reverse=True)
        by_icon = hi[0] if icon[hi[0]] - icon[hi[1]] >= 30 else None
        lo = sorted(band, key=band.get)
        b0, b1 = band[lo[0]], band[lo[1]]
        by_band = lo[0] if (b1 - b0 >= 15 or (b0 <= 0.6 * b1 and b1 - b0 >= 5)) else None
        if by_icon and by_band and by_icon != by_band:
            return None, vals
        return (by_icon or by_band), vals

    def send_cmd_o(self):
        """给 Chiaki 发 ⌘O（Chiaki-ng 串流菜单的开关）。按下 ⌘ → 按 O（带 ⌘ 标志）→ 松 O → 松 ⌘"""
        debug_log("    ⌨️ [⌘O] 关闭 Chiaki 串流菜单")
        release_everything()
        cmd_flag = Quartz.kCGEventFlagMaskCommand
        with _pool():
            src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStatePrivate)
            seq = [(55, True, cmd_flag), (MAC_KEYCODES['o'], True, cmd_flag),
                   (MAC_KEYCODES['o'], False, cmd_flag), (55, False, 0)]
            for code, down, flags in seq:
                ev = Quartz.CGEventCreateKeyboardEvent(src, code, down)
                Quartz.CGEventSetFlags(ev, flags)
                Quartz.CGEventPostToPid(self.backend.pid, ev)
                time.sleep(0.06)

    def chiaki_overlay(self, fr=None):
        """v5：Chiaki-ng 自己的串流菜单（不是游戏的 UI）：左下角 ✕ / 音量 / Mic / Zoom / Stretch / Default /
        High Quality / Custom / Display，右下角 "xx Mbps / Connected to 192.168.x.x / xx dropped frames"。
        它一出来，键盘输入就被这个菜单接走，PS5 收不到任何按键（11/06 10:39 日志：OPTIONS、○ 全部没反应）。"""
        fr = fr or self.grab()
        left = self.ocr_text(fr, ROI_CHIAKI_MENU_L, scale=0.8).lower()
        right = self.ocr_text(fr, ROI_CHIAKI_MENU_R, scale=0.8).lower()
        hits = sum(k in left for k in ("mic", "zoom", "stretch", "volume", "default", "custom", "display", "quality"))
        hits += sum(k in right for k in ("mbps", "connected", "dropped", "frames"))
        return hits >= 3

    def mouse_on_chiaki(self):
        """鼠标是不是停在 Chiaki 窗口上（全局坐标，单位 pt）"""
        try:
            loc = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
            b = self.backend.bounds or {}
            x, y, w, h = float(b["X"]), float(b["Y"]), float(b["Width"]), float(b["Height"])
            return x <= loc.x <= x + w and y <= loc.y <= y + h, (int(loc.x), int(loc.y))
        except Exception:
            return False, None

    def handle_chiaki_overlay(self, where=""):
        """检测到 Chiaki 菜单：先发 ⌘O 关掉（最多 3 次）；还在就把鼠标从 Chiaki 窗口上挪回主屏，再等菜单消失。
        消失了 → 返回 True（这一轮作废、继续跑）；等 CHIAKI_MENU_WAIT_SEC 还在 → 停止并提示手动处理。"""
        if not self.chiaki_overlay():
            return False
        debug_log(f"🧭 [{where}] 检测到 Chiaki-ng 串流菜单（Mic/Zoom/Stretch…），按键会被它接走 → 暂停发键")
        self.save_debug_frame("chiaki_menu")
        # v5.1：用户实测 ⌘O 可以关掉这个菜单 → 脚本自己发 ⌘O（只在亲眼看到菜单时才发，否则反而会打开它）
        for attempt in range(1, 4):
            self.send_cmd_o()
            time.sleep(1.2)
            if not self.chiaki_overlay():
                debug_log(f"    ✅ 已发 ⌘O 关掉 Chiaki 菜单（第 {attempt} 次）→ 继续")
                return True
            debug_log(f"    🔁 发了 ⌘O 菜单还在（第 {attempt} 次）")
        on, loc = self.mouse_on_chiaki()
        if on:
            try:
                mb = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
                cx, cy = mb.origin.x + mb.size.width / 2, mb.origin.y + mb.size.height / 2
                Quartz.CGWarpMouseCursorPosition(Quartz.CGPointMake(cx, cy))
                debug_log(f"    🖱️ 鼠标停在 Chiaki 窗口上 {loc} → 已移回主屏中央 ({int(cx)}, {int(cy)})")
            except Exception as e:
                debug_log(f"    ⚠️ 移动鼠标失败: {e}")
        t0 = time.time()
        while time.time() - t0 < CHIAKI_MENU_WAIT_SEC:
            time.sleep(2.0)
            if not self.chiaki_overlay():
                debug_log(f"    ✅ Chiaki 菜单已消失（等了 {time.time() - t0:.0f}s）→ 继续")
                return True
            if int(time.time() - t0) % 30 < 2:
                debug_log(f"    ⏳ Chiaki 菜单还在…（{time.time() - t0:.0f}s）请把鼠标移出虚拟屏 / Chiaki 窗口")
        self.save_debug_frame("chiaki_menu_stuck")
        raise FatalStop(f"Chiaki-ng 的串流菜单 {CHIAKI_MENU_WAIT_SEC}s 都没消失 —— 请把鼠标移出 Chiaki 窗口，"
                        f"确认菜单关掉后重新运行")

    def screen_kind(self, fr=None):
        fr = fr or self.grab()
        if self.is_pause(fr):
            return "pause_" + self.pause_page(fr)
        if self.parchment(fr):
            dk = self.dialog_kind(fr)
            if dk:
                return "dialog_" + dk
            if self.is_tree(fr):
                return "tree"
        if self.is_bell(fr):
            return "bell"
        dk = self.dialog_kind(fr)
        if dk:
            return "dialog_" + dk
        return "world"

    def escape_to_world(self, tag=""):
        """不管停在哪个界面，都退回野外（每种界面都有回家的路）"""
        last_k = None
        for i in range(10):
            fr = self.grab()
            k = self.screen_kind(fr)
            if k != "world" and k == last_k and i >= 2:
                self.unstick(f"{k} 退不出去")
            last_k = k
            if k == "world":
                if i:
                    debug_log(f"    🏠 [{tag}] 已退回野外")
                return True
            debug_log(f"    🏠 [{tag}] 当前界面 {k} → 退出")
            if k == "dialog_slot":
                self.tap(K_CROSS, wait=0.8)          # 这个框只有【确定】
            elif k == "bell":
                self.tap(K_CIRCLE, wait=0.9)
                fr2 = self.grab()
                rows = self.bell_rows(fr2)
                if self.is_bell(fr2, rows):
                    fr2, rows = self.read_bell_menu(timeout=1.5)
                    if fr2 is not None:
                        self.bell_select(fr2, rows, "离开")
            else:
                self.tap(K_CIRCLE, wait=0.9)         # 重置确认框按 ○ = 取消；修行页 / 暂停菜单按 ○ = 返回
        self.save_debug_frame("escape_fail")
        return False

    # =========================================================================
    # ① 野外 → 铃铛菜单 → 能力修行
    # =========================================================================
    @staticmethod
    def complete_bell_rows(rows):
        """v3：OCR 漏掉的行按行距补上（菜单 6 行等间距，行距约 0.046）。认出的行少于 2 行就原样返回"""
        idx = {lab: BELL_LABELS.index(lab) for lab in rows}
        if len(rows) < 2 or len(rows) == len(BELL_LABELS):
            return dict(rows)
        labs = sorted(rows, key=idx.get)
        pitches = [(rows[b][1] - rows[a][1]) / (idx[b] - idx[a]) for a, b in zip(labs, labs[1:])]
        pitch = float(np.median(pitches))
        x1 = float(np.median([v[0] for v in rows.values()]))
        base = labs[0]
        out = dict(rows)
        for i, lab in enumerate(BELL_LABELS):
            if lab not in out:
                out[lab] = (x1, rows[base][1] + (i - idx[base]) * pitch)
        return out

    def read_bell_menu(self, timeout=3.0):
        """v3：菜单是从下往上淡入的，刚出现时只认得出下面几行（11/06 日志：['买卖货物','能力修行','保存记忆','离开']）。
        等到 6 行都认出来再开始操作；超时就按行距补齐。返回 (frame, rows) 或 (None, {})"""
        t0 = time.time()
        fr, rows = None, {}
        while time.time() - t0 < timeout:
            f = self.grab()
            r = self.bell_rows(f)
            if len(r) >= len(rows):
                fr, rows = f, r
            if len(r) == len(BELL_LABELS):
                return f, r
            time.sleep(0.25)
        if fr is None or len(rows) < 2:
            return None, {}
        full = self.complete_bell_rows(rows)
        debug_log(f"    🔧 铃铛菜单只认出 {list(rows)}，其余行按行距补齐")
        return fr, full

    def bell_select(self, fr, rows, label, press=True):
        """把铃铛菜单的高亮移到 label 那一行。v3：只在亲眼看到高亮时才移动 / 按 ✕，绝不按推断按 ✕
        （v2 按推断按 ✕，菜单还没淡入完时把【装备升级】当成【能力修行】，11/05~06 共 62 轮因此失败）"""
        rows = self.complete_bell_rows(rows)
        if label not in rows:
            debug_log(f"    ⚠️ 铃铛菜单里没认出【{label}】（认出：{list(rows)}）")
            return False
        names = [lab for lab in BELL_LABELS if lab in rows]
        unsure, moves = 0, 0
        while moves <= 10:
            cur, vals = self.bell_highlight(fr, rows)
            if cur is None:
                unsure += 1
                if unsure in (1, 4):
                    debug_log(f"    🔎 铃铛菜单高亮看不清（图标/墨迹 {vals}），等一下再看")
                if unsure >= 10:
                    self.save_debug_frame("bell_unsure", fr)
                    debug_log("    ⚠️ 约 3 秒都看不清高亮，不敢按 ✕")
                    return False
                time.sleep(0.3)
                fr = self.grab()
                continue
            unsure = 0
            if cur == label:
                time.sleep(0.15)        # 再看一眼，确认高亮停在这一行
                fr2 = self.grab()
                if self.bell_highlight(fr2, rows)[0] != label:
                    fr = fr2
                    continue
                if press:
                    self.tap(K_CROSS, wait=0.8)
                return True
            idx, tgt = names.index(cur), names.index(label)
            self.tap(K_DOWN if tgt > idx else K_UP, hold=0.12, wait=0.4, quiet=True)
            moves += 1
            fr = self.grab()
        return False

    def open_ability_tree(self):
        fr = self.grab()
        if self.is_tree(fr):
            return True
        for attempt in range(1, 4):
            debug_log(f"🔔 [①] 按 ○ 打开铃铛菜单（第 {attempt} 次）")
            if attempt > 1:
                self.unstick("○")
            self.tap(K_CIRCLE, wait=0.6)
            fr = self.wait_for(lambda f: self.is_bell(f), timeout=4.0, desc="铃铛菜单")
            if fr is not None:
                break
        else:
            if self.handle_chiaki_overlay("打不开铃铛"):
                raise LoopFailed("Chiaki 菜单挡住了按键（已消失），本轮重来")
            self.save_debug_frame("no_bell")
            raise FatalStop("按 ○ 三次都没打开铃铛菜单 —— 请把角色停在铃铛旁边（能看到白色交互提示）再运行")
        fr, rows = self.read_bell_menu()
        if fr is None:
            raise LoopFailed("铃铛菜单认不出几行")
        debug_log(f"    ✅ 铃铛菜单：{list(rows)}")
        if not self.bell_select(fr, rows, "能力修行"):
            raise LoopFailed("没能选中【能力修行】")
        if self.wait_for(self.is_tree, timeout=6.0, desc="能力修行") is None:
            raise LoopFailed("按了【能力修行】但没进修行页")
        debug_log("    ✅ 已进入【能力修行】")
        return True

    # =========================================================================
    # ② 重置 ③ 重学节点
    # =========================================================================
    def reset_tree(self):
        d0 = self.read_dust()
        debug_log(f"♻️ [②] 重置前尘埃 = {d0}")
        fr = None
        for attempt in range(3):
            if attempt:
                self.unstick("□")
            self.tap(K_SQUARE, wait=0.6)
            fr = self.wait_for(lambda f: self.dialog_kind(f) == "reset", timeout=4.0, desc="重置确认框")
            if fr is not None:
                break
        if fr is None:
            raise KeyDead("按 □ 没弹出【将重置所有修行】确认框")
        debug_log("    ✅ 确认框：将重置所有修行 → ✕ 确定（光标默认在【确定】）")
        got_slot = False
        for attempt in range(3):
            self.tap(K_CROSS, wait=0.8)
            k = None
            t0 = time.time()
            while time.time() - t0 < 5.0:
                f = self.grab()
                k = self.dialog_kind(f)
                if k == "slot":
                    break
                if k is None and self.is_tree(f):
                    break
                time.sleep(0.3)
            if k == "slot":
                got_slot = True
                debug_log("    ✅ 【饰品槽被重置，以上饰品已卸下】→ ✕ 确定")
                self.tap(K_CROSS, wait=0.8)
                if self.wait_for(lambda f: self.dialog_kind(f) is None and self.is_tree(f), timeout=5.0,
                                 desc="回到修行页") is None:
                    self.tap(K_CROSS, wait=0.8)
                break
            if k is None:
                break
            debug_log("    🔁 确认框还在 → 再按一次 ✕")
        f = self.grab()
        if not self.is_tree(f) or self.dialog_kind(f) is not None:
            self.save_debug_frame("reset_fail", f)
            raise LoopFailed("重置后没回到修行页（或确认框还开着）")
        d1 = self.read_dust()
        debug_log(f"    尘埃 {d0} → {d1}" + ("" if got_slot else "  ⚠️ 没看到【饰品槽被重置】框（上一轮饰品可能没装上）"))
        if d0 is not None and d1 is not None and d1 < d0 + SLOT_COST - 1:
            debug_log("    ⚠️ 重置后尘埃没有增加 1 万（重置前海纳百川可能没学）")
        if d0 is not None and d1 is not None and d1 < d0:
            # v4：重置只会返还尘埃，不可能变少 → 一定是读错了，不据此停止
            debug_log(f"    ⚠️ 尘埃读数 {d0} → {d1} 不合理（重置不会让尘埃变少），按读错处理，继续")
            d1 = None
        if d1 is not None and d1 < SLOT_COST:
            d1b = self.read_dust(tries=5)
            if d1b is not None and d1b < SLOT_COST:
                raise FatalStop(f"意识尘埃只有 {d1b}，不够学【海纳百川】({SLOT_COST})")
            debug_log(f"    ⚠️ 尘埃第一次读成 {d1}，复读是 {d1b}，继续")
        return d0, d1, got_slot

    def tree_title(self, fr=None):
        return self.ocr_text(fr or self.grab(), ROI_TREE_TITLE)

    def tree_bar(self, fr=None):
        return self.ocr_text(fr or self.grab(), ROI_TREE_BAR)

    def learn_node(self, name, frags):
        title = self.tree_title()
        # 光标从【黑石】开始，每个节点都在当前位置的右边；往右最多 5 下，还不行再试上 / 下
        for key in [K_RIGHT] * 5 + [K_UP, K_DOWN, K_DOWN]:
            if zh_hit(title, frags):
                break
            self.tap(key, wait=0.45, quiet=True)
            title = self.tree_title()
            debug_log(f"    [{key}] → 光标标题：{title}")
        if not zh_hit(title, frags):
            raise LoopFailed(f"修行树里找不到【{name}】（最后看到：{title}）")
        bar = self.tree_bar()
        debug_log(f"    🎯 光标在【{title}】 | 按钮条：{bar}")
        if learned_text(bar):
            debug_log(f"    ✅ 【{name}】已经是已修行")
            return True
        for attempt in range(3):
            self.hold(K_CROSS, HOLD_LEARN_SEC, wait=0.6)
            fr = self.wait_for(lambda f: learned_text(self.tree_bar(f)), timeout=3.0)
            if fr is not None:
                debug_log(f"    ✅ 【{name}】修行完成")
                return True
            debug_log(f"    🔁 按钮条：{self.tree_bar()} → 再按住一次")
        raise LoopFailed(f"【{name}】按住 ✕ 三次都没变成已修行")

    def relearn_nodes(self):
        for name, frags in RELEARN_NODES:
            debug_log(f"📚 [③] 重学【{name}】")
            self.learn_node(name, frags)
        d2 = self.read_dust()
        debug_log(f"    尘埃 = {d2}")
        return d2

    # =========================================================================
    # ④ 退回野外
    # =========================================================================
    def leave_bell(self):
        debug_log("🚪 [④] ○ 返回 → 离开铃铛")
        self.tap(K_CIRCLE, wait=0.9)
        fr = self.wait_for(lambda f: not self.is_tree(f), timeout=3.0, desc="离开修行页")
        if fr is None:
            raise LoopFailed("按 ○ 没退出修行页")
        if not self.escape_to_world("离开铃铛"):
            raise LoopFailed("没能回到野外")

    # =========================================================================
    # ⑤ 装回饰品
    # =========================================================================
    def eq_title(self, fr=None):
        return self.ocr_text(fr or self.grab(), ROI_EQ_TITLE)

    def move_cursor(self, xs, ys, target, max_steps=12):
        """格子光标移到 target=(行, 列)；看得到光标才走。
        v3：连续 3 次按键光标都没动才算"那个格子不存在"，每次没动就多等一会儿
        （11/06 两次：菜单刚打开时按键被吃掉，光标没动 → v2 只等 2 次就放弃 → 误判"没有空格"/"找不到饰品"）"""
        last, stuck = None, 0
        for _ in range(max_steps):
            fr = self.grab()
            cur, vals = grid_cursor(fr, xs, ys)
            if cur is None:
                time.sleep(0.4)
                cur, vals = grid_cursor(self.grab(), xs, ys)
                if cur is None:
                    debug_log("    ⚠️ 看不清格子光标在哪")
                    return False
            if cur == target:
                return True
            stuck = stuck + 1 if cur == last else 0
            if stuck == 2:
                self.unstick("方向键")
            if stuck >= 3:
                return False
            last = cur
            if cur[0] != target[0]:
                key = K_DOWN if target[0] > cur[0] else K_UP
            else:
                key = K_RIGHT if target[1] > cur[1] else K_LEFT
            self.tap(key, hold=0.12, wait=0.35 + 0.3 * stuck, quiet=True)
        return False

    def open_equip_page(self):
        debug_log("🎒 [⑤] OPTIONS 打开暂停菜单")
        fr = None
        for attempt in range(3):
            if attempt:
                self.unstick("OPTIONS")
            self.tap(K_OPTIONS, wait=0.8)
            fr = self.wait_for(self.is_pause, timeout=4.0, desc="暂停菜单")
            if fr is not None:
                break
        if fr is None:
            raise LoopFailed("按 OPTIONS 没打开暂停菜单")
        for i in range(7):
            page = self.pause_page(fr)
            if page == "equip":
                debug_log("    ✅ 在【角色 → 装备】页")
                time.sleep(0.6)      # v3：等菜单动画结束，刚打开时按键会被吃掉
                return True
            if page == "list":
                self.tap(K_CIRCLE, wait=0.6)
            else:
                self.tap(K_R1, wait=0.7)   # 切到下一个页签，直到【角色】的装备页
            fr = self.grab()
        raise LoopFailed("暂停菜单里没找到【角色 → 装备】页")

    def find_empty_slot(self):
        """饰品格逐个看标题："装备饰品" = 空格。目标饰品已经在某格 → 返回 ('already', 格子)"""
        for r in ACC_ROWS:
            for c in range(len(EQ_XS)):
                if not self.move_cursor(EQ_XS, EQ_YS, (r, c)):
                    continue
                title = self.eq_title()
                debug_log(f"    饰品格 ({r},{c})：{title}")
                if zh_hit(title, ["装备饰品"]):
                    return "empty", (r, c)
                if zh_hit(title, self.target_frags):
                    return "already", (r, c)
        return None, None

    def pick_from_list(self):
        """在饰品列表里逐格找目标饰品，找到就按 ✕"""
        for r in range(len(LIST_YS)):
            for c in range(len(LIST_XS)):
                if not self.move_cursor(LIST_XS, LIST_YS, (r, c)):
                    if c == 0:
                        return False          # 这一行第一个格子都没有 = 列表到底了
                    break
                title = self.eq_title()
                debug_log(f"    列表 ({r},{c})：{title}")
                if zh_hit(title, self.target_frags):
                    debug_log(f"    🎯 找到【{TARGET_ACCESSORY}】→ ✕")
                    self.tap(K_CROSS, wait=0.9)
                    return True
        return False

    def equip_target(self):
        self.open_equip_page()
        state, cell = self.find_empty_slot()
        if state == "already":
            debug_log(f"    ⚠️ 【{TARGET_ACCESSORY}】已经装在 {cell}（重置没把它卸下？）→ 本轮不算叠加")
            self.escape_to_world("装备")
            raise LoopFailed("目标饰品没被卸下")
        if state is None:
            self.save_debug_frame("no_empty_slot")
            raise LoopFailed("饰品区没有空格（海纳百川没学上？）")
        debug_log(f"    ✅ 空饰品格 {cell} → ✕ 打开饰品列表")
        self.tap(K_CROSS, wait=0.9)
        if self.wait_for(lambda f: self.pause_page(f) == "list", timeout=4.0, desc="饰品列表") is None:
            raise LoopFailed("按 ✕ 没打开饰品列表")
        if not self.pick_from_list():
            self.save_debug_frame("target_not_found")
            # v3：偶尔是按键被吃掉、没走到那一格（11/06 08:58），先算本轮失败；连续 2 轮都找不到才停止
            self.not_found_streak += 1
            if self.not_found_streak >= 2:
                raise FatalStop(f"连续 2 轮在饰品列表里找不到【{TARGET_ACCESSORY}】（名字写对了吗？）")
            raise LoopFailed(f"饰品列表里没找到【{TARGET_ACCESSORY}】")
        self.not_found_streak = 0
        fr = self.wait_for(lambda f: self.pause_page(f) == "equip", timeout=4.0, desc="回到装备页")
        if fr is None:
            raise LoopFailed("选了饰品但没回到装备页")
        cur, _ = grid_cursor(fr, EQ_XS, EQ_YS)
        title = self.eq_title(fr)
        if not zh_hit(title, self.target_frags):
            self.save_debug_frame("equip_verify_fail", fr)
            raise LoopFailed(f"装备后这一格的标题是【{title}】，不是目标饰品")
        debug_log(f"    ✅ 【{TARGET_ACCESSORY}】已装进 {cur}")
        if not self.escape_to_world("关闭暂停菜单"):
            raise LoopFailed("没能关掉暂停菜单")

    # =========================================================================
    # 主循环
    # =========================================================================
    def one_loop(self):
        self.handle_chiaki_overlay("轮开头")
        if not self.escape_to_world("轮开头"):
            raise LoopFailed("轮开头退不回野外")
        self.open_ability_tree()
        self.reset_tree()
        self.relearn_nodes()
        self.leave_bell()
        self.equip_target()

    def run_loop(self, max_loops=0):
        n = 0
        while max_loops <= 0 or n < max_loops:
            n += 1
            sep("=")
            gc.collect()
            try:
                import torch
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
            except Exception:
                pass
            mem = current_rss_gb()
            debug_log(f"🔁 第 {n} 轮 | 已成功叠加 {self.loops_ok} 层 | 🧠 内存 {mem:.2f} GB")
            if mem > MEM_STOP_GB:
                raise MemoryGuardException(f"脚本占用 {mem:.1f}GB > {MEM_STOP_GB}GB")
            if mem > MEM_WARN_GB:
                debug_log(f"⚠️ 内存偏高 {mem:.1f}GB")
            t0 = time.time()
            try:
                self.one_loop()
                self.loops_ok += 1
                self.fail_streak = 0
                if self.key_dead_streak:
                    debug_log(f"    ✅ 失灵的键已恢复（之前连续 {self.key_dead_streak} 次没反应，共等了 "
                              f"{sum(KEY_DEAD_WAITS[:self.key_dead_streak])}s）")
                    self.key_dead_streak = 0
                debug_log(f"🏆 第 {n} 轮完成，共叠加 {self.loops_ok} 层（本轮 {time.time() - t0:.0f}s）")
            except KeyDead as e:
                debug_log(f"❌ 第 {n} 轮失败：{e}")
                self.save_debug_frame("key_dead")
                if self.handle_chiaki_overlay("失败检查"):
                    self.escape_to_world("Chiaki 菜单消失后")
                    continue
                self.escape_to_world("按键失灵")
                if self.key_dead_streak >= len(KEY_DEAD_WAITS):
                    raise FatalStop(f"按键失灵，等了 {sum(KEY_DEAD_WAITS)}s 都没恢复 —— 请在 Chiaki 窗口里手动按一下 □"
                                    f"（键盘 {K_SQUARE}）看有没有反应，再把结果告诉 AI")
                wait = KEY_DEAD_WAITS[self.key_dead_streak]
                self.key_dead_streak += 1
                debug_log(f"    ⏸️ 按键失灵第 {self.key_dead_streak} 次 → 在野外停 {wait}s 不发任何键，再试")
                t_w = time.time()
                while time.time() - t_w < wait:
                    if os.path.exists(STOP_FILE):
                        raise StopRequested("检测到 STOP 文件")
                    time.sleep(1.0)
                release_everything()
            except LoopFailed as e:
                debug_log(f"❌ 第 {n} 轮失败：{e}")
                self.save_debug_frame("loop_fail")
                if self.handle_chiaki_overlay("失败检查"):
                    # 是 Chiaki 菜单挡住了按键，不是脚本/游戏的问题 → 不计入连续失败
                    self.escape_to_world("Chiaki 菜单消失后")
                    continue
                self.fail_streak += 1
                debug_log(f"    （连续失败 {self.fail_streak} 次）")
                self.escape_to_world("失败恢复")
                if self.fail_streak >= FAIL_STREAK_STOP:
                    raise FatalStop(f"连续 {self.fail_streak} 轮失败")
            except StreamResumed:
                debug_log("🔁 画面冻结后恢复 → 本轮作废")
                self.escape_to_world("冻结恢复")
            if time.time() - t0 > LOOP_TIMEOUT_SEC:
                debug_log(f"⚠️ 这一轮用了 {time.time() - t0:.0f}s，超过 {LOOP_TIMEOUT_SEC}s")

    # =========================================================================
    # 诊断：截一帧打印所有检测结果
    # =========================================================================
    def diagnose(self):
        fr = self.grab()
        path = os.path.join(DEBUG_DIR, "debug_snapshot.jpg")
        os.makedirs(DEBUG_DIR, exist_ok=True)
        cv2.imwrite(path, fr.bgr)
        debug_log(f"📸 已保存 {path}（{fr.W}x{fr.H}）")
        debug_log(f"界面判断：{self.screen_kind(fr)} | Chiaki 串流菜单：{'有' if self.chiaki_overlay(fr) else '无'} | 鼠标在 Chiaki 上：{self.mouse_on_chiaki()}")
        debug_log(f"  宣纸亮度(左侧)={fr.region_median(0.03, 0.30, 0.15, 0.70):.0f}（≥85 = 修行页）")
        for name, roi in [("暂停页签", ROI_TABS), ("左侧小标题", ROI_LEFT_HEADER), ("装备标题", ROI_EQ_TITLE),
                          ("修行标题", ROI_TREE_TITLE), ("修行按钮条", ROI_TREE_BAR), ("修行右下提示", ROI_TREE_HINT),
                          ("确认框", ROI_DIALOG)]:
            debug_log(f"  OCR {name}: {self.ocr_text(fr, roi)}")
        debug_log(f"  尘埃: {self.read_dust(fr)} | 读数框 {tuple(round(v, 3) for v in self.dust_roi(fr))}")
        rows = self.bell_rows(fr)
        debug_log(f"  铃铛菜单行: { {k: (round(v[0], 3), round(v[1], 3)) for k, v in rows.items()} }")
        if rows:
            hl, vals = self.bell_highlight(fr, rows)
            debug_log(f"  铃铛高亮: {hl} | 图标/墨迹亮度 {vals}")
        for nm, xs, ys in [("装备页格子", EQ_XS, EQ_YS), ("列表格子", LIST_XS, LIST_YS)]:
            cur, vals = grid_cursor(fr, xs, ys)
            debug_log(f"  {nm}光标: {cur} | 亮度 { {k: int(v) for k, v in vals.items()} }")
        # 在截图上画出所有区域，方便核对位置
        vis = fr.bgr.copy()
        for roi in [ROI_CHIAKI_MENU_L, ROI_CHIAKI_MENU_R, ROI_TABS, ROI_LEFT_HEADER, ROI_EQ_TITLE, ROI_TREE_TITLE, ROI_TREE_BAR, ROI_TREE_HINT,
                    ROI_DUST, ROI_DIALOG, ROI_BELL]:
            x1, y1, x2, y2 = roi_px(vis.shape, roi)
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 3)
        for xs, ys, col in [(EQ_XS, EQ_YS, (0, 255, 0)), (LIST_XS, LIST_YS, (255, 0, 255))]:
            for y in ys:
                for x in xs:
                    p1 = (int((x - CELL_HALF[0]) * fr.W), int((y - CELL_HALF[1]) * fr.H))
                    p2 = (int((x + CELL_HALF[0]) * fr.W), int((y + CELL_HALF[1]) * fr.H))
                    cv2.rectangle(vis, p1, p2, col, 2)
        p2 = os.path.join(DEBUG_DIR, "debug_rois.jpg")
        cv2.imwrite(p2, cv2.resize(vis, None, fx=0.5, fy=0.5))
        debug_log(f"📸 区域标注图: {p2}")


MODE_MENU = """  [回车 / 0] 🚀 完整自动循环（手动停止：双击 stop_bot.command）
  [1]  🔔 单步测试 ①：野外按 ○ 打开铃铛 → 进入【能力修行】
  [2]  ♻️ 单步测试 ②③：（已在能力修行页）重置 + 重学节点
  [3]  🚪 单步测试 ④：退回野外
  [4]  🎒 单步测试 ⑤：（在野外）OPTIONS → 把目标饰品装进空格
  [5]  🔁 只跑 1 轮完整流程
  [9]  🩺 诊断：截一帧打印所有检测结果，保存 debug_snapshot.jpg / debug_rois.jpg"""


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=f"影之刃零 饰品叠加 {VERSION}（后台模式）")
    ap.add_argument("--mode", help="运行模式（不填则询问）")
    ap.add_argument("--loops", type=int, default=0, help="循环次数，0 = 一直跑到手动停止（默认）")
    args = ap.parse_args()

    run_log = RunLog()
    print("=" * 65)
    print(f"🗡️ 影之刃零 饰品属性叠加脚本 - {VERSION}（后台模式）  目标饰品：{TARGET_ACCESSORY}")
    print("   开始前：角色站在铃铛旁边（能看到白色交互提示），不要打开任何菜单")
    print("   要停止：双击 stop_bot.command（或在 PhantomBladeZero 文件夹里新建名为 STOP 的文件）")
    print("=" * 65)
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)
        print("🧹 已清除上次留下的 STOP 文件")
    if args.mode is not None:
        mode = args.mode.strip()
    else:
        print("🛠️ 请选择运行模式 (输入数字后回车):")
        print(MODE_MENU)
        mode = input("请输入运行模式 (默认 0): ").strip()
    mode = mode or "0"
    run_log.note(f"运行模式 = '{mode}'")
    run_log.tag(f"mode{mode}")
    try:
        bot = PBZAccessoryBot()
    except ChiakiNotReady as e:
        debug_log(f"❌ {e}")
        run_log.close()
        sys.exit(1)
    debug_log(f"📝 本次日志: {run_log.path}")
    try:
        if mode == "0":
            bot.run_loop(max_loops=args.loops)
        elif mode == "1":
            bot.open_ability_tree()
        elif mode == "2":
            bot.reset_tree()
            bot.relearn_nodes()
        elif mode == "3":
            bot.escape_to_world("测试")
        elif mode == "4":
            bot.equip_target()
        elif mode == "5":
            bot.run_loop(max_loops=1)
        elif mode == "9":
            bot.diagnose()
        else:
            debug_log(f"❌ 未知模式 '{mode}'")
    except FatalStop as e:
        debug_log(f"🛑 [安全停止] {e}")
    except LoopFailed as e:
        debug_log(f"❌ [单步失败] {e}")
    except StreamResumed:
        debug_log("🔁 画面冻结后已恢复；请重新运行")
    except MemoryGuardException as e:
        debug_log(f"🛑 [内存保险丝] {e}")
    except StopRequested:
        debug_log("🛑 检测到 STOP 文件，安全停止")
        try:
            os.remove(STOP_FILE)
        except OSError:
            pass
    except ChiakiNotReady as e:
        debug_log(f"🛑 Chiaki 窗口不可用：{e}")
    except KeyboardInterrupt:
        debug_log("🛑 手动中断")
    except Exception:
        import traceback
        debug_log("💥 未捕获的异常：")
        traceback.print_exc()
    finally:
        release_everything()
        try:
            debug_log(f"📊 本次共叠加 {bot.loops_ok} 层")
        except Exception:
            pass
        debug_log(f"📝 日志已保存: {run_log.path}")
        run_log.close()
