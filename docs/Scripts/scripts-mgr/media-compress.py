#!/usr/bin/env python3
"""媒体压缩：图像走 caesiumclt，视频走 HandBrakeCLI，工具路径自动查找。

用法:
    media-compress <文件或目录...> [-o <输出目录>] [--only image|video]
                   [--image-quality N] [--image-format F] [--image-strip-exif]
                   [--dry-run]

视频参数完全由脚本旁的 media-compress.json 决定（HandBrake 预设导出格式，
直接原样交给 `--preset-import-file`），脚本不提供任何视频参数开关：
要硬件编码就把该文件里的 VideoEncoder 改成 nvenc_h264，要改质量就改
VideoQualitySlider，要改分辨率就改 PictureWidth/PictureHeight，字幕取舍
看 SubtitleTrackSelectionBehavior（"all" 保留全部字幕轨）。

输出到源目录的 _compressed/，镜像源目录结构，原文件始终不动。没有日志文件、
没有台账、没有锁文件，唯一产物就是压缩后的文件本身——图像压不动时原样复制，
保证输出目录不缺图。

工具查找顺序: 环境变量 CAESIUM_CLT / HANDBRAKE_CLI / FFPROBE / FFMPEG -> PATH ->
常见安装目录。缺失的工具只在真正需要处理该类媒体时才会报错。

退出码: 0 成功或跳过；1 存在失败文件或工具/配置缺失；2 参数错误。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import string
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock

SOURCE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SOURCE_DIR / "media-compress.json"
DEFAULT_OUTPUT_DIR = "_compressed"
LOG_SUFFIX = ".log"
# 当前轮次打开着的日志文件；log() 在有它时同步落盘。None 表示不写日志。
_log_file = None
# stdout 被下游提前关闭（例如 `media-compress ... | head`）后置位，之后不再尝试写控制台。
_console_dead = False
# 临时文件名里用的递增序号，配合 pid 保证同一次运行内不重名。
_temp_seq = 0
_temp_lock = Lock()
# 日志开头那行配置信息所需的内容：(配置文件, 实际选中的预设, 容器扩展名, 可用预设)。
# 用模块级变量是因为它要在 Logger.open() 里、第一行 command 之后立刻打印。
_config_note: tuple = (None, "", "", [])
# 是否给控制台输出上色：只在输出到真终端时为真。
_color = False

RESET = "\033[0m"
ORANGE = "\033[38;5;208m"
# 一行一个颜色：按消息里出现的标记词匹配，靠前的先命中（所以具体原因要排在通用的
# [IMAGE]/[VIDEO] 之类之前，否则永远轮不到）。
# 注意这些字符串必须和实际打印出来的字面一致——`WARNING:` 有冒号无方括号，
# 缺口明细行里没有 "WARNING" 字样，所以只能靠原因词本身来识别。
COLOR_RULES = (
    # 缺口明细行带 [MISSING] 前缀——它与正常状态行结构相同（都是 "[IMAGE] 原因"），
    # 靠模式猜会误染，所以让打印方显式标出来。
    ("[MISSING]", ORANGE),
    ("WARNING:", ORANGE),
    ("[FAIL]", "\033[31m"),               # 红
    ("[OK]", "\033[32m"),                 # 绿
    ("[SKIP]", "\033[33m"),               # 黄
    ("[COPY]", "\033[36m"),               # 青
    ("[ERROR]", "\033[31m"),              # 红
    ("exec:", "\033[90m"),                # 灰
    ("command:", "\033[90m"),             # 灰
)


def enable_vt() -> bool:
    """尽力打开 Windows 控制台的 ANSI 转义处理。

    只在确实是控制台句柄时才动手：本工具在管道里跑时 GetConsoleMode 会失败，
    而这正是我们想要的结果——那种情况本来就不该输出颜色。
    失败不报错，返回 False 让调用方退回无颜色。
    """
    if os.name != "nt":
        return True
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.GetStdHandle(-11)                 # STD_OUTPUT_HANDLE
        mode = wintypes.DWORD()
        if not kernel32.GetConsoleMode(wintypes.HANDLE(handle), ctypes.byref(mode)):
            return False
        want = mode.value | 0x0004 | 0x0001                 # VT | PROCESSED_OUTPUT
        return bool(kernel32.SetConsoleMode(wintypes.HANDLE(handle), want))
    except (OSError, AttributeError, ImportError):
        return False


def want_color() -> bool:
    """是否给控制台着色：只在输出到真终端时上色。

    没有开关——重定向到文件或管道时一定无色，所以不会往日志或别人的管道里灌转义码。
    """
    return sys.stdout.isatty() and enable_vt()


def paint(line: str) -> str:
    """给消息上色；时间戳保持原样，方便眼睛直接跳过前缀。"""
    if not _color:
        return line
    body = line[20:] if len(line) > 20 else line      # 跳过 "YYYY-MM-DD HH:MM:SS "
    for marker, code in COLOR_RULES:
        if marker in body:
            return line[:20] + code + body + RESET
    return line


def log(message: str = "", file=None, **_ignored) -> None:
    """带人类可读时间戳的输出。

    时间戳打在**每一行**上，因为多行结果（例如"输出目录完整"那两行）只有每行
    各自带时间才知道那会儿在做什么。注意换行符在时间戳之前，续行才不会被污染。
    并发时也逐行加锁式打印，所以时间戳的顺序与实际写出顺序一致。
    总是 flush：后台运行或管道里被缓冲的话，时间戳就失去意义了。

    同时（若已分配日志文件）以同样格式落盘，所以日志就是屏幕内容的副本。
    颜色只加在控制台上，日志文件始终是纯文本——转义码进了文件就不好读了，
    也会破坏按列解析。
    写失败一律吞掉：日志写不进去、或下游把管道关了（`| head`），都不该让整轮
    任务半路崩掉——那会留下做了一半的输出和临时目录。
    """
    global _console_dead
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{stamp} {message}"
    if not _console_dead:
        try:
            print(paint(line), file=file, flush=True)
        except OSError:
            _console_dead = True          # 管道被下游关闭，之后只写文件
    if _log_file is not None:
        try:
            _log_file.write(line + "\n")
            _log_file.flush()
        except (OSError, ValueError):
            pass

# caesiumclt 1.5.0 读不了这些，实测每次都失败：
#   .avif/.heic/.heif/.jxl -> 报错退出
#   .tif/.tiff/.bmp        -> "Unable to compute the base path for the files."
# 它们本身也不易再压，所以不压缩、但仍是图像类别，这样 --copy-unprocessed yes
# 会把它们原样搬进输出目录，输出目录不会缺文件。
PASSTHROUGH_EXTS = {".avif", ".heic", ".heif", ".jxl", ".tif", ".tiff", ".bmp"}
IMAGE_EXTS = ({".jpg", ".jpeg", ".jfif", ".png", ".webp", ".gif"} | PASSTHROUGH_EXTS)
VIDEO_EXTS = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi",
              ".wmv", ".flv", ".mpg", ".mpeg", ".ts", ".m2ts", ".3gp"}
MODERN_VIDEO_CODECS = {"hevc", "h265", "av1", "vp9", "vp8"}
# 图像最长边上限。0 = 不限制。只在源超出时才缩，永不放大。
# 常见取值（按需自行改这一个数）：
#   1920  1080p 屏全屏
#   2560  1440p
#   3840  4K 原生
#   5120  5K
#   6144  6K
#   7680  8K
#   8192  常见扫描/相机输出的上限
IMAGE_MAX_EDGE_CHOICES = (0, 1920, 2560, 3840, 5120, 6144, 7680, 8192)
DEFAULT_IMAGE_MAX_EDGE = 5120
HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}
JUNK_NAMES = {"desktop.ini", "thumbs.db", "ehthumbs.db", ".ds_store", ".localized"}
# 表示"故意不动它"，不是失败：算 SKIP 而不是 FAIL，也不影响退出码。
#   hdr / modern_codec      —— 视频：HDR 重编会变色，现代编码器重编通常只会更大
#   bitrate_not_worth_it    —— 音频：目标码率不低于源，重编出来只会一样大或更大
INTENTIONAL_SKIPS = {"hdr", "modern_codec", "bitrate_not_worth_it"}
# HandBrake 的 FileFormat 取值 -> 容器扩展名。
CONTAINER_EXTS = {"av_mp4": ".mp4", "av_m4v": ".mp4", "av_mkv": ".mkv",
                  "av_webm": ".webm", "av_avi": ".avi"}
# 图像输出格式 -> 扩展名；original 表示沿用源扩展名。
FORMAT_EXTS = {"original": "", "jpeg": ".jpg", "png": ".png", "gif": ".gif",
               "webp": ".webp", "tiff": ".tiff"}

MIN_SAVINGS_RATIO = 0.05          # 目的地动作: 至少省这么多才认为值得替换
AUDIO_MIN_SAVINGS = 0.10          # 音频收益空间小，门槛比视频高一档
PROBE_TIMEOUT = 60
MAX_PATH_LENGTH = 240            # Windows 上超过这个长度的路径工具容易失败

# ------------------------------ 音频 ------------------------------
# 音频参数只有两个：输出编码器和码率。
AUDIO_CODECS = ("mp3", "flac", "opus", "aac")
AUDIO_BITRATES = ("128k", "192k", "256k", "320k")
DEFAULT_AUDIO_CODEC = "mp3"
DEFAULT_AUDIO_BITRATE = "192k"
# 编码器 -> (输出扩展名, ffmpeg muxer, 编码器参数)。码率只对有损编码器追加。
AUDIO_TARGETS = {
    "mp3": (".mp3", "mp3", ["-c:a", "libmp3lame"]),
    "flac": (".flac", "flac", ["-c:a", "flac"]),
    "opus": (".opus", "opus", ["-c:a", "libopus"]),
    "aac": (".m4a", "ipod", ["-c:a", "aac"]),
}
# 目标格式能否内嵌封面。opus(Ogg) 装不下 attached_pic——实测映射封面会让它产出
# 0 字节无流的文件，所以那几种目标必须去掉封面映射，也不能因为没有封面而判失败。
AUDIO_TARGET_COVER = {"mp3": True, "flac": True, "aac": True, "opus": False}

# 源扩展名 -> 它对应的编码器，用来判断"源已经是目标格式了"。已经是就不转：
# 同编码器重转收益接近零（flac->flac 实测省 0%），有损的同格式重转更是白掉一次音质。
# 转码与否**只看目标格式**：已经是目标格式 -> 原样复制，其余一律转换。这样
# `--audio-codec opus` 对所有 mp3 都会真的转，符合"传了目标格式就是要转"的直觉。
# 至于"转完是不是更省"由 AUDIO_MIN_SAVINGS 把关：省不到 10% 就保留原文件，所以
# 320k→320k 这类无意义重编码不会发生。
AUDIO_SOURCE_CODEC = {
    ".mp3": "mp3", ".flac": "flac", ".opus": "opus", ".oga": "opus", ".ogg": "opus",
    ".m4a": "aac", ".aac": "aac", ".wma": "wma", ".mpc": "mpc",
}
# 低效无损（.wav/.alac/.ape/...）不映射到任何编码器，永远会被转——它们是收益最大的一类。
LOW_EFFICIENCY_LOSSLESS_EXTS = {".wav", ".alac", ".ape", ".wv", ".aiff", ".aif", ".caf"}
# 所有会进音频队列的扩展名。
AUDIO_EXTS = set(AUDIO_SOURCE_CODEC) | LOW_EFFICIENCY_LOSSLESS_EXTS
# 有损编码器：只有它们才受码率影响（无损编码器忽略码率）。
LOSSY_AUDIO_CODECS = {"mp3", "opus", "aac"}
AUDIO_NARROW_TARGETS = {"mp3": "mp3 cannot carry multichannel or >48kHz audio; "
                               "channels will be downmixed and sample rate resampled"}


def audio_action(src: Path, codec: str, bitrate: str = DEFAULT_AUDIO_BITRATE) -> str:
    """返回 "convert"（送去转码）或 "copy"（原样复制）。

    规则：
      * 源扩展名不是音频 -> copy（其他后缀在 classify 里就被分流了）
      * 源已经是目标格式且**没有显式调码率** -> copy（同编码器重转没有收益）
      * 源已经是目标格式但**显式给了非默认码率** -> convert（就是要按这个码率重编，
        例如把 320k 的 mp3 压成 128k）
      * 源是别的格式 -> convert

    "同格式调码率"必须能真的转，否则 `--audio-bitrate 128k` 处理 mp3 库会一声不响地
    全都原样复制——实测踩过。判断依据是"码率是否被显式改过"而不是源码率的绝对值：
    classify 阶段拿不到源码率（要额外探测每个文件），而默认码率下重编没有任何收益。
    """
    suffix = src.suffix.lower()
    if suffix not in AUDIO_EXTS:
        return "copy"
    if AUDIO_SOURCE_CODEC.get(suffix) != codec:
        return "convert"          # 低效无损不在表里，取到 None，与任何目标都不等 -> 必转
    # 到这里源已经是目标格式。"显式调码率"只对**有损格式**有意义：无损编码器（flac）
    # 忽略码率，重编一遍只会白费时间，不会更省。
    if codec in LOSSY_AUDIO_CODECS and bitrate != DEFAULT_AUDIO_BITRATE:
        return "convert"
    return "copy"


def setup_console() -> None:
    """Windows 控制台尽量用 UTF-8，避免中文路径打印成乱码。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError, ValueError):
            pass


class Logger:
    """把整轮运行的输出写成一份日志文件。

    文件名带时间戳，放在输出根（-o 给的目录，或各源目录的 _compressed/），
    方便事后回看"哪个文件当时执行了什么命令"。
    """

    def __init__(self, path: Path, fresh: bool) -> None:
        self.path = path
        self.fresh = fresh

    def open(self) -> None:
        global _log_file
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _log_file = self.path.open("w" if self.fresh else "a", encoding="utf-8")
        # 开头三行：本次调用的原样命令行、日志自身位置、实际生效的配置。
        # 配置是唯一没有持久状态的东西，不回显出来事后就无从复现当时用了哪套视频参数。
        log("command: " + invocation(sys.argv))
        log(f"log file: {self.path}")
        config, preset, container, names = _config_note
        if config is not None:
            others = [n for n in names if n != preset]
            log(f"config: {config}  preset={preset}  container={container}"
                + (f"  others: {', '.join(others)}" if others else ""))

    def close(self) -> None:
        global _log_file
        if _log_file is not None:
            try:
                _log_file.close()
            except OSError:
                pass
            _log_file = None


def human(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size) < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def invocation(argv: list[str]) -> str:
    """把本次调用的命令行还原成可复制粘贴的一行。

    直接用 sys.argv 而不是拿 argparse 的结果重建：重建会丢掉用户实际怎么写
    （--log=no 还是 --log no、路径带不带引号），而日志的第一价值就是"当时到底
    敲了什么"。只有含空格或引号的参数才补引号。
    """
    return " ".join(f'"{a}"' if (" " in a or '"' in a) else a for a in argv)


# ------------------------------ 工具查找 ------------------------------

def find_tool(names: list[str], env_var: str, candidates: list[Path]) -> str:
    """按 环境变量 -> PATH -> 常见安装目录 的顺序查找可执行文件。"""
    override = os.environ.get(env_var, "").strip().strip('"')
    if override and Path(override).is_file():
        return override
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return ""


def tools(needed: list[str], extra_dir: Path | None = None) -> dict[str, str]:
    """只解析 needed 里点名的工具路径；extra_dir 用于和 ffmpeg 同目录兜底。

    只处理视频时连 caesium 的存在性都不会去查，反之亦然——"按需"要是真的按需。
    解析是纯路径查找（无 subprocess、无版本探测），成本只有几次文件存在性判断。

    HandBrake 常被装到非系统盘（本机就在 D:\\Program Files\\HandBrake），
    而 ProgramFiles 只指向 C:，所以要遍历所有盘符的 Program Files 一并找。
    """
    found: dict[str, str] = {}
    if "caesium" in needed:
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "caesiumclt" / "caesiumclt.exe",
            Path.home() / "scoop" / "shims" / "caesiumclt.exe",
            Path("/usr/local/bin/caesiumclt"), Path("/usr/bin/caesiumclt"),
        ]
        if extra_dir:
            candidates.append(extra_dir / "caesiumclt.exe")
        found["caesium"] = find_tool(["caesiumclt", "caesium-clt"], "CAESIUM_CLT", candidates)
    if "handbrake" in needed:
        roots: list[Path] = []
        for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
            if os.environ.get(var):
                roots.append(Path(os.environ[var]))
        if os.name == "nt":
            for letter in string.ascii_uppercase:
                roots.append(Path(f"{letter}:\\Program Files"))
        roots.append(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs")
        candidates = [root / "HandBrake" / "HandBrakeCLI.exe" for root in roots] + [
            Path("/Applications/HandBrakeCLI"), Path("/usr/local/bin/HandBrakeCLI"),
            Path("/usr/bin/HandBrakeCLI"), Path("/opt/homebrew/bin/HandBrakeCLI"),
        ]
        found["handbrake"] = find_tool(["HandBrakeCLI"], "HANDBRAKE_CLI", candidates)
    if "ffprobe" in needed:
        candidates = []
        if extra_dir:
            candidates.append(extra_dir / ("ffprobe.exe" if os.name == "nt" else "ffprobe"))
        found["ffprobe"] = find_tool(["ffprobe"], "FFPROBE", candidates)
    if "ffmpeg" in needed:
        candidates = []
        if extra_dir:
            candidates.append(extra_dir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"))
        found["ffmpeg"] = find_tool(["ffmpeg"], "FFMPEG", candidates)
    return found


def flatten_presets(nodes) -> list[dict]:
    """把 HandBrake 预设文件里的预设摊平。

    导出的文件可以是**多层的**：顶层 PresetList 里可能放的是文件夹
    （Type 0，或带 ChildrenArray 却没有 FileFormat），真正的预设藏在
    ChildrenArray 里。所以不能只取 PresetList[0]——那会拿到文件夹，名字是
    文件夹名、也没有 FileFormat。
    """
    found: list[dict] = []
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        children = node.get("ChildrenArray") or []
        is_folder = node.get("Type") == 0 or (children and not node.get("FileFormat"))
        if is_folder:
            found.extend(flatten_presets(children))
            continue
        found.append(node)
        found.extend(flatten_presets(children))
    return found


def load_preset(path: Path, wanted: str = "") -> tuple[str, str, str, list[str]]:
    """读 HandBrake 预设文件，返回 (预设名, 输出容器扩展名, 全部预设名)。

    wanted 为空时取第一个预设；给了名字就必须精确命中——HandBrake 的预设名
    **区分大小写**（实测 `aaa-480p` 匹配不到 `AAA-480p`），这里用宽松匹配会
    造成"脚本放行、HandBrake 拒绝"。找不到时把可用名字都列出来，否则用户只能
    去翻 JSON。
    """
    if not path.is_file():
        raise SystemExit(f"[ERROR] config file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        raise SystemExit(f"[ERROR] cannot parse config ({exc}): {path}") from None

    presets = flatten_presets(data.get("PresetList") or [])
    named = [p for p in presets if str(p.get("PresetName") or "")]
    if not named:
        raise SystemExit(f"[ERROR] no presets in {path}")

    names = [str(p["PresetName"]) for p in named]
    if wanted:
        preset = next((p for p in named if str(p["PresetName"]) == wanted), None)
        if preset is None:
            raise SystemExit(f"[ERROR] preset \"{wanted}\" not found in {path}\n"
                             f"        available: {', '.join(names)}")
    else:
        preset = named[0]

    name = str(preset["PresetName"])
    # 容器由预设的 FileFormat 决定。未知取值不再静默当 mp4——那会让输出后缀
    # 与实际容器不符，且用户无从察觉。
    raw_format = str(preset.get("FileFormat") or "")
    if raw_format not in CONTAINER_EXTS:
        log(f"[WARNING] unknown FileFormat {raw_format!r} in preset \"{name}\"; "
            f"assuming av_mp4 (.mp4)", file=sys.stderr)
        raw_format = "av_mp4"
    # 两个都返回：扩展名用于拼输出名，av_* 原值用于显式告诉 HandBrake 容器
    # （临时文件是 .mctmp，它没法从后缀推断）。
    return name, CONTAINER_EXTS[raw_format], raw_format, names


# ------------------------------ 工具调用 ------------------------------

def run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, encoding="utf-8",
                          errors="replace", timeout=PROBE_TIMEOUT)


def problem(result: subprocess.CompletedProcess, limit: int = 300) -> str:
    """工具失败时的可读原因：首行（通常是病因）+ 末行（通常是结论）。"""
    lines = [line.strip() for line in (result.stderr or result.stdout or "").splitlines()
             if line.strip()]
    if not lines:
        return f"exit {result.returncode}"
    if len(lines) == 1:
        return lines[0][:limit]
    return f"{lines[0]} | … | {lines[-1]}"[:limit]


def longest_edge(ffprobe: str, path: Path) -> int:
    """源图的最长边（像素）；读不出来返回 0。

    只用来决定"要不要下传 --long-edge"：不加判断直接传也对（caesium 不会放大），
    但显式判断能让 dry-run 打印出真正会执行的参数。
    """
    command = [ffprobe, "-v", "error", "-select_streams", "v",
               "-show_entries", "stream=width,height", "-of", "json", str(path)]
    try:
        result = run(command)
        if result.returncode != 0:
            return 0
        streams = (json.loads(result.stdout or "{}").get("streams") or [{}])
        first = streams[0]
        return max(int(first.get("width") or 0), int(first.get("height") or 0))
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, IndexError, ValueError):
        return 0


def probe(ffprobe: str, path: Path) -> dict:
    """用 ffprobe 读视频流与容器信息；图像路径不走这里。"""
    command = [ffprobe, "-v", "error",
               "-show_entries",
               "stream=codec_type,codec_name,width,height,color_transfer,bit_rate",
               "-show_entries", "format=duration,bit_rate", "-of", "json", str(path)]
    try:
        result = run(command)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(str(exc)) from None
    if result.returncode != 0:
        raise RuntimeError(problem(result))
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise RuntimeError("no video stream found")
    fmt = data.get("format") or {}
    return {
        "codec": str(video.get("codec_name") or ""),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "transfer": str(video.get("color_transfer") or ""),
        "bitrate": int(str(fmt.get("bit_rate") or video.get("bit_rate") or 0) or 0),
        "duration": float(fmt.get("duration") or 0.0),
        "video_streams": sum(1 for s in streams if s.get("codec_type") == "video"),
        "audio_streams": sum(1 for s in streams if s.get("codec_type") == "audio"),
    }


# ------------------------------ 音频 ------------------------------

def probe_audio(ffprobe: str, path: Path) -> dict:
    """读音频文件的时长、编码器、声道数、标签数与是否有内嵌封面。

    封面在多数容器里以 attached_pic 视频流的形式存在，丢掉它几乎无法补救，所以要
    单独识别、映射时一并搬运。

    标签要同时看 format_tags 和 stream_tags：**ogg/opus 把 Vorbis comment 放在
    stream 级**，只查 format_tags 会误判成"标签全丢"（实测踩过）。
    """
    command = [ffprobe, "-v", "error",
               "-show_entries", "stream=codec_type,codec_name,channels,bit_rate:"
                                "stream_disposition=attached_pic:stream_tags",
               "-show_entries", "format=duration:format_tags", "-of", "json", str(path)]
    result = run(command)
    if result.returncode != 0:
        raise RuntimeError(problem(result))
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams") or []
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if audio is None:
        raise RuntimeError("no audio stream found")
    special = {"encoder", "duration", "language", "handler_name", "vendor_id"}
    tags = {k.lower() for k in ((data.get("format") or {}).get("tags") or {})}
    # 只收**音频流**的标签。封面流（attached_pic）会带 comment="Cover (front)" 这类
    # 描述封面自身的标签，收进来会造成误判：转 opus 时封面流被丢弃，于是 comment
    # 消失，校验便谎报"标签丢失"而放弃一次本来成功的转换。实测踩过。
    tags |= {k.lower() for k in (audio.get("tags") or {})}
    return {
        "codec": str(audio.get("codec_name") or ""),
        "channels": int(audio.get("channels") or 0),
        # VBR/ABR 文件报告的是**平均**码率（实测纯音内容 q0 只有 63k），所以拿它做
        # "码率是否已经一样"的判断必须带容差，不能要求精确相等。
        "bit_rate": int(str(audio.get("bit_rate") or 0) or 0),
        "duration": float((data.get("format") or {}).get("duration") or 0.0),
        "has_cover": any((s.get("disposition") or {}).get("attached_pic")
                         for s in streams if s.get("codec_type") == "video"),
        "tags": tags - special,
        "audio_streams": sum(1 for s in streams if s.get("codec_type") == "audio"),
    }


def bitrate_value(bitrate: str) -> int:
    """把 "192k" 这样的目标码率换成 bps；解析不出来返回 0。"""
    text = bitrate.strip().lower().rstrip("b")
    if text.endswith("k"):
        text = text[:-1]
    return int(float(text) * 1000) if text.replace(".", "", 1).isdigit() else 0


def bitrate_wont_shrink(source_bps: int, target: str) -> bool:
    """目标码率没有明显低于源码率 —— 压了也不会省，别压。

    这是"花 67 秒重编完才发现没省到"的提前出口：脚本本来就知道源码率（探测只要
    二十几毫秒），完全可以在启动编码器之前就判断出来。实测踩过——286k 的源码被要求
    转到 320k，整条重编一遍，结果产物和源一样大，只能原样复制，时间全白花。

    判据是"目标是否比源低 MIN_SAVINGS_RATIO 以上"，而不是"是否相等"：
      * 目标高于源（286k -> 320k）        -> 必然变大，跳过
      * 目标只低一点点（300k -> 320k）     -> 省不到门槛，跳过
      * 目标明显更低（286k -> 128k）       -> 该转，放行
    容差比节省门槛再宽一点，因为 VBR 文件报告的只是平均码率，本身就有波动。
    源码率读不到时返回 False（照常转，宁可多花时间也不要漏掉该压的）。
    """
    want = bitrate_value(target)
    if not source_bps or not want:
        return False
    return want > source_bps * (1 - MIN_SAVINGS_RATIO - 0.03)


def compress_audio(ffmpeg: str, ffprobe: str, src: Path, target: Path, codec: str,
                   bitrate: str, dry_run: bool) -> tuple[int, str]:
    """转码单个音频文件，成功返回 (压缩后字节数, "")；失败或省得不够返回 (0, 原因)。

    target 已由调用方通过 resolve_free_name 定好，这里只管写它。

    元数据必须显式搬运：`-map_metadata 0` 保标签，封面要以 attached_pic 单独映射并
    `-c:v copy` 原样搬运（光有 map_metadata 不够，实测封面会丢）。音乐库里标签和封面
    是最难重建的东西，丢了不可逆。

    输出容器靠 `-f` 显式指定：ffmpeg 本来是靠扩展名猜容器的，而临时文件名不一定带
    正确扩展名。
    """
    try:
        info = probe_audio(ffprobe, src)
    except (RuntimeError, json.JSONDecodeError) as exc:
        return 0, f"cannot read metadata: {exc}"

    # 开始编码**之前**先判断值不值得压：脚本已经拿到源码率了，没必要等整条重编完
    # 才发现没省到（长音频一次就是几十秒）。
    # 只在**编码器相同**时判断：跨编码器时源码率没有可比性（opus 128k 的信息量约等于
    # mp3 256k），不能因为数字接近就跳过本该发生的转换。
    if info["codec"] == codec and codec in LOSSY_AUDIO_CODECS \
            and bitrate_wont_shrink(info["bit_rate"], bitrate):
        log(f"    note: source is already {codec} @ {info['bit_rate'] // 1000}k, "
            f"target {bitrate} would not be smaller — skipping re-encode")
        return 0, "bitrate_not_worth_it"

    _, muxer, encoder_args = AUDIO_TARGETS[codec]
    # 码率只对有损编码器有意义；flac 是无损，给了也会被忽略。
    if codec != "flac":
        encoder_args = encoder_args + ["-b:a", bitrate]
    keeps_cover = AUDIO_TARGET_COVER.get(codec, False)
    if codec in AUDIO_NARROW_TARGETS and (info["channels"] > 2 or info["has_cover"]):
        log(f"    note: {AUDIO_NARROW_TARGETS[codec]}")
    prefix = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-nostdin",
              "-i", str(src),
              "-map", "0:a", "-map_metadata", "0"]
    if keeps_cover:
        # 只有目标容器装得下时才映射封面流——opus 映射它会让输出变成 0 字节。
        prefix += ["-map", "0:v?", "-c:v", "copy", "-disposition:v", "attached_pic"]
    prefix += encoder_args
    if dry_run:
        # 显示真正的目标名而不是临时名；-f 已显式给出，容器不靠后缀判定。
        log("    " + " ".join(prefix + ["-f", muxer, str(target)]))
        return 0, "dry_run"
    # 建目录必须放在 dry-run 判断**之后**，否则 dry-run 会凭空造出输出目录。
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = temp_file_for(target)
    command = prefix + ["-f", muxer, str(temp)]
    log("exec: " + " ".join(command))
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding="utf-8", errors="replace")
    except OSError as exc:
        return 0, str(exc)
    try:
        if result.returncode != 0 or not temp.is_file() or temp.stat().st_size == 0:
            return 0, (problem(result) or "tool produced no file")
        if info["duration"] > 1.0:
            check = probe_audio(ffprobe, temp)
            tolerance = max(0.5, info["duration"] * 0.01)
            if abs(check["duration"] - info["duration"]) > tolerance:
                return 0, (f"duration {check['duration']:.1f}s "
                           f"!= source {info['duration']:.1f}s")
            # 标签丢了要当场发现（音乐库里它几乎无法重建）；封面只在目标装得下时
            # 才要求保留。
            missing = info["tags"] - check["tags"]
            if missing:
                return 0, f"metadata lost: {', '.join(sorted(missing)[:4])}"
            if keeps_cover and info["has_cover"] and not check["has_cover"]:
                return 0, "cover art was lost"
        size = temp.stat().st_size
        if size >= src.stat().st_size or size > src.stat().st_size * (1 - AUDIO_MIN_SAVINGS):
            return 0, "not_smaller"
        os.replace(temp, target)                      # 同卷改名，原子
        return size, ""
    finally:
        temp.unlink(missing_ok=True)


# 临时文件名形如 `<目标名>-<pid>-<序号>.mctmp`。
# 用专属后缀 `.mctmp` 而不是 `.tmp`：`.tmp` 太通用，用户完全可能自己有个 `notes.tmp`，
# 而我们的临时文件是"目标名 + 进程号 + 序号"，只靠名字形状去猜就有误删的可能。
# `.mctmp` 是脚本专有的，见到它就能确定是自己造的，判定因此变得简单而可靠。
TEMP_SUFFIX = ".mctmp"
TEMP_STEM_RE = re.compile(r"-\d+-\d+$")      # 名字以 `-<pid>-<序号>` 结尾


def _our_temp_file(path: Path) -> bool:
    """是不是本脚本造的临时文件：`.mctmp` 结尾，且名字以 `-<pid>-<序号>` 收尾。

    专属后缀已经排除了绝大多数误判；再要求尾段形状，是为了连"用户自己也有个
    `.mctmp` 文件"这种极端情况也不会被误删。
    """
    return path.suffix == TEMP_SUFFIX and bool(TEMP_STEM_RE.search(path.stem))


def sweep_temp_files(out_roots: set[Path], whole_run: bool = False) -> int:
    """清掉输出目录里的临时文件残留。

    正常情况下每个文件的临时文件都由 finally 删掉；但**进程被强杀时 finally 不会执行**，
    残留就会一直躺在输出目录里（实测出现过 `<名字>-<pid>-<序号>.mctmp`）。所以除了收尾
    清理，还要在**开始时**扫一遍：那时本次运行还没建过任何临时文件，凡是匹配的必定是
    上一次留下的，删掉一定安全。

    whole_run=True 时不看 pid：开始时用，清掉所有历史残留。False 时只删本进程的，
    避免踩到另一个同时在跑的实例。
    """
    removed = 0
    mine = f"-{os.getpid()}-"
    for out_root in out_roots:
        if not out_root.is_dir():
            continue
        for stale in out_root.rglob(f"*{TEMP_SUFFIX}"):
            if not _our_temp_file(stale) or not stale.is_file():
                continue
            if not whole_run and mine not in stale.name:
                continue
            try:
                stale.unlink()
                removed += 1
            except OSError:
                pass                        # 删不掉就算了，不影响主流程
    return removed


def temp_file_for(target: Path) -> Path:
    """目标同目录下唯一的临时文件名：`<目标名>-<pid>-<序号>.mctmp`。

    容器不再靠后缀判定——ffmpeg 那边本来就有显式 `-f muxer`，HandBrake 那边补上
    `--format`。所以临时文件不必伪装成成品，`.mctmp` 一眼就能认出是中间产物，
    即使进程被强杀残留下来，也不会被误认为正常输出。
    结尾的 pid 与递增计数保证并发时不重名，也让清理能识别出是自己造的。
    """
    global _temp_seq
    with _temp_lock:
        _temp_seq += 1
        seq = _temp_seq
    return target.with_name(f"{target.name}-{os.getpid()}-{seq}{TEMP_SUFFIX}")


# ------------------------------ 压缩 ------------------------------

def make_temp_dir(out_root: Path) -> Path:
    """为一次运行建一个临时目录，放在输出根下。

    caesiumclt 只支持"输出目录"、无法直接指定输出文件名，所以必须有这么个目录。
    它要和目标同卷，否则 os.replace 跨盘会报 WinError 17（退化成复制就失去原子性），
    所以放在输出根而不是系统临时目录。

    放成"输出根下唯一的隐藏目录"而不是"每个文件一个目标同级目录"：后者会在输出
    镜像树的每个子目录里都塞一个临时目录（如 _compressed/P/.x.webp.mc-tmp/），
    翻目录时会看见，也不像正常产物。名字带 pid，两个进程同时跑不会互相踩。

    每次调用还会顺手清掉本卷上过期的同类目录（进程被硬杀时会留下）。
    """
    tmp = out_root / f".media-compress-tmp-{os.getpid()}"
    if tmp.is_dir():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    for stale in out_root.glob(".media-compress-tmp-*"):
        if stale != tmp:
            shutil.rmtree(stale, ignore_errors=True)
    return tmp


def compress_image(caesium: str, src: Path, target: Path, quality: int, image_format: str,
                   strip_exif: bool, max_edge: int, tmp: Path) -> tuple[int, str]:
    """压缩单张图像，成功返回 (压缩后字节数, "")；失败或省得不够返回 (0, 原因)。

    caesiumclt 的 `-e` 是"保留 EXIF"，所以 --image-strip-exif 是省掉该开关而
    不是加上某个开关。
    `--keep-orientation` 始终保留：只留方向标签，否则带 EXIF 旋转的照片会躺倒。

    临时目录由调用方按"输出根"建一个并登记清理；它不是按文件各建一个，所以
    输出镜像树里不会凭空多出目录。并发压缩时各文件用各自不同的文件名写进这个
    目录，再由 os.replace 原子改名到目标，彼此不冲突。

    max_edge > 0 时按最长边缩放，配 --no-upscale：caesium 只在源超限时才缩，
    不会把小图放大。缩放和编码在同一次调用里完成，不会二次有损。
    """
    command = [caesium, "-q", str(quality), "--keep-orientation", "--keep-dates",
               "-O", "all", "--json", "-o", str(tmp)]
    if not strip_exif:
        command.append("-e")
    # 只在输出扩展名与源不同时才传 --format。caesiumclt 对"转成自身格式"会直接
    # 报 "Cannot convert to the same format"（实测 png->png / jpg->jpeg /
    # webp->webp / gif->gif 全失败），而 --format original 的语义本就是保持原样，
    # 传了反而会把本来能压的文件变成"失败后复制"。
    if image_format != "original" and target.suffix.lower() != src.suffix.lower():
        command += ["--format", image_format]
    if max_edge > 0:
        command += ["--long-edge", str(max_edge), "--no-upscale"]
    command.append(str(src))
    log("exec: " + " ".join(command))         # 完整命令，方便事后单独复现
    result = run(command)
    try:
        payload = json.loads(result.stdout or "{}")
        entry = (payload.get("files") or [{}])[0]
    except (json.JSONDecodeError, IndexError):
        return 0, problem(result)
    if result.returncode != 0 or entry.get("status") != "success":
        return 0, (entry.get("message") or problem(result))
    produced = Path(str(entry.get("output_path") or ""))
    if not produced.is_file():
        return 0, "tool produced no file"
    size = produced.stat().st_size
    if not keeps_enough(src.stat().st_size, size):
        return 0, "not_smaller"
    target.parent.mkdir(parents=True, exist_ok=True)   # os.replace 不会建目标目录
    os.replace(produced, target)                  # 同卷改名，原子
    return size, ""


def compress_video(handbrake: str, ffprobe: str, src: Path, target: Path, temp: Path,
                   config_path: Path, preset_name: str, file_format: str,
                   dry_run: bool) -> tuple[int, str]:
    """转码单个视频，成功返回 (压缩后字节数, "")；失败或省得不够返回 (0, 原因)。

    明确传 `--format`：临时文件名是 `.mctmp`，HandBrake 没法从后缀推断容器。取值与
    预设里的 FileFormat 同域（av_mp4 等），所以结果和"让它自己推断"一致。
    """
    try:
        info = probe(ffprobe, src)
    except (RuntimeError, json.JSONDecodeError) as exc:
        return 0, f"cannot read metadata: {exc}"

    if info["codec"] in MODERN_VIDEO_CODECS:
        kbps = info["bitrate"] / 1000
        if kbps and kbps <= 5500 * (info["height"] / 1080 or 1) * 1.2:
            return 0, "modern_codec"
    if info["transfer"].lower() in HDR_TRANSFERS:
        return 0, "hdr"

    command = [handbrake, "-i", str(src), "-o", str(temp),
               "--format", file_format,
               "--preset-import-file", str(config_path), "--preset", preset_name]
    if dry_run:
        log("    " + " ".join(command))
        return 0, "dry_run"

    target.parent.mkdir(parents=True, exist_ok=True)
    log("exec: " + " ".join(command))         # 完整命令，方便事后单独复现
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding="utf-8", errors="replace")
    except OSError as exc:
        return 0, str(exc)
    try:
        if result.returncode != 0 or not temp.is_file():
            return 0, (problem(result) or "tool produced no file")
        broken = verify_video(ffprobe, src, temp, info)
        if broken:
            return 0, broken
        size = temp.stat().st_size
        if not keeps_enough(src.stat().st_size, size):
            return 0, "not_smaller"
        os.replace(temp, target)
        return size, ""
    finally:
        temp.unlink(missing_ok=True)


def keeps_enough(before: int, after: int) -> bool:
    return after > 0 and after < before and after <= before * (1 - MIN_SAVINGS_RATIO)


def verify_video(ffprobe: str, src: Path, out: Path, info: dict) -> str:
    """转码结果必须和源片同长、同音轨数，分辨率只允许缩小；返回 "" 表示通过。"""
    try:
        check = probe(ffprobe, out)
    except (RuntimeError, json.JSONDecodeError) as exc:
        return f"cannot read transcoded output: {exc}"
    if check["audio_streams"] != info["audio_streams"]:
        return f"audio tracks {check['audio_streams']} != source {info['audio_streams']}"
    if check["height"] > info["height"] + 2:
        return f"height {check['height']} exceeds source {info['height']}"
    if info["duration"] > 1.0:
        tolerance = max(0.5, info["duration"] * 0.01)
        if abs(check["duration"] - info["duration"]) > tolerance:
            return f"duration {check['duration']:.1f}s != source {info['duration']:.1f}s"
    return ""


# ------------------------------ 扫描与主流程 ------------------------------

def classify(path: Path, audio_codec: str, audio_bitrate: str) -> str:
    """返回 image / video / audio / audio-copy / passthrough / junk。

    passthrough 表示"不压缩、但会原样搬到输出目录"，包含两类：
      * caesiumclt 读不了的图像格式；
      * 其余一切非媒体文件（.txt/.srt/.nfo/.md ...）。
    两类都必须进队列，否则输出目录会缺文件——而这个脚本的用途是"压完删源目录"，
    缺文件就等于丢数据。只有明确的操作系统垃圾（Thumbs.db 等）才丢下不管。

    audio-copy 与 audio 分开：前者（源已是目标格式且没调码率）只复制，后者才真的送去
    转码。分开是为了让"哪些会被压缩"在输出里一眼可见。
    """
    if path.name.lower() in JUNK_NAMES:
        return "junk"
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        return "passthrough" if suffix in PASSTHROUGH_EXTS else "image"
    if suffix in VIDEO_EXTS:
        return "video"
    if suffix in AUDIO_EXTS:
        return "audio" if audio_action(path, audio_codec, audio_bitrate) == "convert" \
            else "audio-copy"
    return "passthrough"


Item = tuple[Path, Path, Path]               # (源文件, 输入根目录, 输出根目录)


def collect(paths: list[Path], output: str | None, audio_codec: str,
            audio_bitrate: str) \
        -> tuple[list[Item], list[Item], list[Item], list[Item], int, int]:
    """展开输入为 (图像, 视频, 音频, 仅复制, 扫描总数, 垃圾数)，不读取文件内容。

    "仅复制"包括非媒体文件（.txt/.srt/.nfo/...）、caesiumclt 读不了的图像格式，以及
    按当前设置不转码的音频（见 classify）。它们不压缩但会原样搬进输出目录——这个脚本
    的用途是"压完删源目录"，漏一个就是丢数据。返回总数让调用方能交叉校验：凡是扫到
    却没有去处的文件都说明输出目录会缺东西，必须报警而不是宣称"可以删源目录"。

    每个输入各自决定输出根目录：显式 --output 时是所有输入共用的那一个，
    否则是该输入自己的 <目录>/_compressed/。
    """
    images: list[Item] = []
    videos: list[Item] = []
    audios: list[Item] = []
    passthrough: list[Item] = []
    scanned = 0
    junk = 0
    for path in paths:
        # 在这里绝对化，而不是要求调用方保证：下面判"是否位于输出目录之内"必须两边
        # 同为绝对路径。源给了相对路径时 rglob 产出相对路径，与 resolve() 过的输出根
        # 永远不相等，那条跳过会静默失效（上一轮产物被重新压一遍、输出多套一层目录）。
        path = path.resolve()
        if path.is_file():
            root, files, base = path.parent, [path], path.parent
        elif path.is_dir():
            root, files, base = path, sorted(p for p in path.rglob("*") if p.is_file()), path
        else:
            continue
        out_root = Path(output).expanduser().resolve() if output \
            else (base / DEFAULT_OUTPUT_DIR).resolve()
        for item in files:
            # 跳过"位于输出目录之内"的文件，也就是上一轮的产物。
            # 判断方向不能反：out_root 是源目录的**祖先**时（例如 -o 指向源目录的
            # 父目录），`out_root in item.parents` 同样成立，那会把所有源文件误判成
            # "自己的输出"而全部跳过——整轮变成 nothing to process。
            if out_root in item.parents:
                continue
            scanned += 1
            kind = classify(item, audio_codec, audio_bitrate)
            if kind == "image":
                images.append((item, root, out_root))
            elif kind == "video":
                videos.append((item, root, out_root))
            elif kind == "audio":
                audios.append((item, root, out_root))
            elif kind in ("passthrough", "audio-copy"):
                passthrough.append((item, root, out_root))
            else:
                junk += 1                     # 操作系统垃圾，有意不搬
    return images, videos, audios, passthrough, scanned, junk


def destination(src: Path, root: Path, out_root: Path, suffix: str, keep: bool = False,
                qualify: bool = False) -> Path:
    """输出路径：镜像源目录结构，名字按需带上目标扩展名。

    三种形态：
      * `keep=True`      -> 保留名，就是源本名（`a.flac`）。内容与扩展名一致，不说谎。
      * `qualify=False`  -> 最简转换名（`a.png` 转 webp -> `a.webp`）。
      * `qualify=True`   -> 带源扩展名的转换名（`a.png.webp`），用于和别的源撞名时区分。

    扩展名本来就相符时（image-format original、现代编码跳过的视频、非媒体文件）
    目标扩展名与源相同，不加任何后缀，保持 `a.webp`、`a.txt` 的原名。
    """
    source_suffix = src.suffix          # 保留原始大小写，如 .PNG
    if keep or suffix.lower() == source_suffix.lower():
        name = src.name
    elif qualify:
        name = src.name + suffix
    else:
        name = src.with_suffix(suffix).name
    try:
        relative = src.relative_to(root).with_name(name)
    except ValueError:
        relative = Path(name)
    if not relative.parts:
        relative = Path(name)
    return out_root / relative


def main(argv: list[str]) -> int:
    class Parser(argparse.ArgumentParser):
        """让 argparse 自己的报错也走 log()，否则那几行没有时间戳。

        error() 直接用 2 退出，不再经过 exit()，所以不会被当成帮助。
        脚本约定：参数错误 = 2，帮助 = 0。
        """

        def error(self, message: str) -> None:
            self.print_usage(sys.stderr)
            self.exit(2, f"{self.prog}: [ERROR] {message}\n")

        def exit(self, status: int = 0, message: str | None = None) -> None:
            if message:
                text = message.rstrip("\n")
                if text.startswith("usage:"):     # 用法块只有 print_usage 输出，别重复加时间戳
                    sys.stderr.write(text + "\n")
                else:
                    log(text, file=sys.stderr)
            raise SystemExit(status)

    parser = Parser(
        prog="media-compress", add_help=True,
        description="Compress images with caesiumclt and videos with HandBrakeCLI; "
                    "tool paths are auto-detected.",
        epilog="Video options come from media-compress.json next to this script; "
               "the script exposes no video switches.")
    parser.add_argument("paths", nargs="+", help="files or directories to process")
    parser.add_argument("--output", "-o", default=None,
                        help="output directory mirroring the source tree "
                             f"(default: <dir>/{DEFAULT_OUTPUT_DIR}/ per input)")
    parser.add_argument("--only", choices=("image", "video", "audio"),
                        help="compress one media kind only; the others are still handled "
                             "by --copy-unprocessed (copied, not compressed)")
    parser.add_argument("--image-quality", type=int, default=82,
                        help="image quality 0-100 (default: 82)")
    parser.add_argument("--image-format", default="original", choices=tuple(FORMAT_EXTS),
                        help="image output format (default: original, keep source format)")
    parser.add_argument("--image-strip-exif", action="store_true",
                        help="strip image EXIF (including GPS and other private data)")
    parser.add_argument("--image-max-edge", type=int, default=DEFAULT_IMAGE_MAX_EDGE,
                        help="downscale images so the longest edge fits this many pixels "
                             f"(default: {DEFAULT_IMAGE_MAX_EDGE}; 0 = no limit). "
                             "Never upscales. Common values: "
                             + ", ".join(str(v) for v in IMAGE_MAX_EDGE_CHOICES[1:]))
    parser.add_argument("--image-jobs", type=int, default=3,
                        help="parallel image compressions (default: 3; 1 = serial)")
    parser.add_argument("--copy-unprocessed", choices=("yes", "no"), default="yes",
                        help="copy files left uncompressed into the output tree "
                             "(default: yes). 'no' makes the output tree INCOMPLETE, "
                             "so it can no longer replace the source folder.")
    parser.add_argument("--video-config", metavar="FILE", default=None,
                        help="HandBrake preset JSON to use for video "
                             f"(default: {CONFIG_PATH.name} next to this script)")
    parser.add_argument("--video-preset", metavar="NAME", default=None,
                        help="preset to pick from --video-config (default: the first one). "
                             "Names are case-sensitive.")
    parser.add_argument("--audio-codec", choices=AUDIO_CODECS, default=DEFAULT_AUDIO_CODEC,
                        help=f"audio output codec (default: {DEFAULT_AUDIO_CODEC}). Every "
                             "audio file is converted except those already in this format. "
                             "Conversions that save less than 10%% are discarded and the "
                             "original is copied instead.")
    parser.add_argument("--audio-bitrate", choices=AUDIO_BITRATES,
                        default=DEFAULT_AUDIO_BITRATE,
                        help=f"audio bitrate for lossy codecs (default: {DEFAULT_AUDIO_BITRATE}); "
                             "ignored by flac")
    parser.add_argument("--dry-run", action="store_true", help="print commands only, write nothing")
    parser.add_argument("--log", nargs="?", const="auto", default="auto", metavar="no|FILE",
                        help="write a log next to the output (default: auto, i.e. "
                             "<output>/media-compress-<timestamp>.log). 'no' disables it; "
                             "a path writes/appends there instead.")
    args = parser.parse_args(argv[1:])
    # 颜色要在这里就定下来：下面所有校验失败都会打 [ERROR]，放到校验之后就染不上色了。
    global _color
    _color = want_color()
    if not 0 <= args.image_quality <= 100:
        log("[ERROR] --image-quality must be between 0 and 100", file=sys.stderr)
        return 2
    if args.image_jobs < 1:
        log("[ERROR] --image-jobs must be at least 1", file=sys.stderr)
        return 2
    if args.image_max_edge != 0 and args.image_max_edge < 64:
        log("[ERROR] --image-max-edge must be 0 (no limit) or at least 64", file=sys.stderr)
        return 2
    if args.audio_codec not in AUDIO_CODECS:
        log(f"[ERROR] --audio-codec must be one of: {', '.join(AUDIO_CODECS)}",
            file=sys.stderr)
        return 2
    if args.audio_bitrate not in AUDIO_BITRATES:
        log(f"[ERROR] --audio-bitrate must be one of: {', '.join(AUDIO_BITRATES)}",
            file=sys.stderr)
        return 2

    # 配置和预设要在扫描之前定下来并校验：参数写错却先跑，会白做几百个文件
    # （而且它们已经进了输出目录）。--video-config 的相对路径按调用者的当前目录解析，
    # 这才符合命令行直觉。
    global _config_note
    config_path = Path(args.video_config).expanduser() if args.video_config else CONFIG_PATH
    preset_name, container_ext, file_format, preset_names = load_preset(
        config_path, args.video_preset or "")
    _config_note = (config_path, preset_name, container_ext, preset_names)
    # 输入一律绝对化。下游所有比较都是绝对路径对绝对路径：源用相对路径（如 "."）时
    # rglob 产出的是相对路径，而输出根是 resolve() 过的绝对路径，两者永远不相等，
    # 于是"跳过位于输出目录之内的文件"这条会静默失效——上一次的产物被当成输入再压
    # 一遍，输出还会多套一层 _compressed。实测踩过。
    paths = [Path(p).expanduser().resolve() for p in args.paths]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for path in missing:
            log(f"[ERROR] path not found: {path}", file=sys.stderr)
        return 1

    # --output 不能与源目录重叠。三种重叠都直接拒绝：
    #   * 等于源目录      -> 每个文件的输出路径就是它自己，整轮静默什么都不做
    #   * 在源目录之内    -> 下次运行会把上一轮产物当输入再压一遍（有损叠加），
    #                        输出里还会多出套娃目录
    #   * 是源目录的祖先  -> 输出目录把源目录包在里面，扫描时会连自己的产出一起扫
    # 这些都是"跑很久之后才发现结果不对"，所以宁可拒绝也不放行。
    if args.output:
        out_root = Path(args.output).expanduser().resolve()
        for src in paths:
            base = src.resolve() if src.is_dir() else src.resolve().parent
            if out_root == base:
                log(f"[ERROR] --output must not be the source directory itself: {out_root}",
                    file=sys.stderr)
                return 2
            if base in out_root.parents:
                log(f"[ERROR] --output must not be inside a source directory", file=sys.stderr)
                log(f"        output: {out_root}", file=sys.stderr)
                log(f"        source: {base}", file=sys.stderr)
                return 2
            if out_root in base.parents:
                log(f"[ERROR] --output must not contain a source directory", file=sys.stderr)
                log(f"        output: {out_root}", file=sys.stderr)
                log(f"        source: {base}", file=sys.stderr)
                return 2

    # 日志要在规划之前打开，"已存在则跳过"那些行才进得了日志。
    # 显式路径 -> 追加；auto -> 在输出根下新建带时间戳的文件。
    # dry-run 承诺"零写入"，日志也是写入，所以这里就不开日志文件了——否则
    # `--dry-run --log auto` 会凭空在输出根建出一个 _compressed 和一份日志。
    logger: Logger | None = None
    if args.log != "no" and not args.dry_run:
        # 时间戳带微秒：同一秒内连跑两次（脚本很快时很常见）文件名就不会撞，
        # 否则第二次会把第一次的日志截断覆盖。
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        if args.log == "auto":
            # 与 collect 同一套规则：有 -o 就是它，否则各自源目录的 _compressed。
            base = Path(args.output).expanduser().resolve() if args.output else \
                (paths[0] if paths[0].is_dir() else paths[0].parent)
            log_path = (base if args.output else base / DEFAULT_OUTPUT_DIR) / \
                f"media-compress-{stamp}{LOG_SUFFIX}"
            fresh = True
        else:
            log_path = Path(args.log).expanduser()
            fresh = False
        try:
            logger = Logger(log_path, fresh)
            logger.open()
        except OSError as exc:
            log(f"[ERROR] cannot open log file: {exc}", file=sys.stderr)
            return 1

    try:
        return compress_all(args, paths, config_path, preset_name, container_ext, file_format)
    finally:
        if logger is not None:
            logger.close()


def resolve_free_name(wanted: Path, taken: set, lock) -> Path:
    """取 wanted；若已被本次运行占用或磁盘上已存在，就加序号直到空位。

    两个源争同一个输出名时（同目录的 song.mp3 与 song.flac 都想写 song.mp3），
    后到者自动变成 song-2.mp3。宁可名字带序号，也不要覆盖别人、也不要丢文件。

    必须在锁内调用：图像阶段是多线程的，否则两个线程可能拿到同一个名字。
    taken 是本次运行已经答应写出的路径集合（磁盘上还没有，所以只看 is_file 不够）。
    """
    with lock:
        if wanted not in taken and not wanted.is_file():
            taken.add(wanted)
            return wanted
        stem, suffix = wanted.stem, wanted.suffix
        for n in range(2, 10000):
            candidate = wanted.with_name(f"{stem}-{n}{suffix}")
            if candidate not in taken and not candidate.is_file():
                taken.add(candidate)
                return candidate
    raise OSError(f"cannot find a free name near {wanted}")


def deliver(kind: str, tag: str, src: Path, target: Path, size: int) -> tuple | None:
    """把未压缩的文件原样复制到**已经定好**的目标路径；失败返回结果元组。

    名字由调用方定好，这里不再解析一次——多解析一次会让序号无故往后跳。
    """
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    except OSError as exc:
        # 要复制却复制失败 = 输出目录缺口，必须让用户看见。
        return tag, src, target, size, 0, "FAIL", f"copy: {exc}"
    return None


def wanted_pair(src: Path, root: Path, out_root: Path, suffix: str,
                qualify: bool = False) -> tuple[Path, Path]:
    """一个源的两种可能产出：(转换成功的路径, 压不动时保留原件的路径)。

    qualify=True 表示这个名字会和别的源撞上，于是把源扩展名也写进转换产物名
    （`a.png` -> `a.png.webp`）；保留件始终是源本名，不受影响。
    """
    target = destination(src, root, out_root, suffix)
    if qualify and target.suffix.lower() != src.suffix.lower():
        target = destination(src, root, out_root, suffix, qualify=True)
    return target, destination(src, root, out_root, suffix, keep=True)


def compress_all(args, paths: list[Path], config_path: Path, preset_name: str,
                 container_ext: str, file_format: str) -> int:
    """打开日志之后的主体；单独成函数，好让日志在 finally 里可靠关闭。"""
    images, videos, audios, passthrough, scanned, junk = collect(
        paths, args.output, args.audio_codec, args.audio_bitrate)

    # --only 表示"只**压缩**这一类"，不是"只出现在输出目录"。其余类照样按
    # --copy-unprocessed 处理：yes 时原样复制（输出目录因此仍是完整的，可以替换源
    # 目录），no 时才真的丢弃。否则 `--only image` 会悄悄让输出目录缺掉所有视频，
    # 而末尾那句"可以删源目录"就成了谎话。
    ignored = 0
    kinds = {"image": images, "video": videos, "audio": audios}
    if args.only in kinds:
        for name, items in kinds.items():
            if name == args.only:
                continue
            if args.copy_unprocessed == "yes":
                passthrough += items       # 降级为"只复制"，永不压缩
            else:
                ignored += len(items)
            items.clear()

    # 交叉校验：扫到的文件必须都有去处——入队、被 --only 有意丢弃、或被明确判为
    # 系统垃圾。剩下的就是"无处可去"，那会在输出目录里缺席，也就是最后那句
    # "可以删源目录"在说谎。这条断言存在的意义就是让那种情况不可能静默发生。
    accounted = len(images) + len(videos) + len(audios) + len(passthrough) + ignored + junk
    if scanned != accounted:
        log(f"[WARNING] scanned {scanned} file(s) but only {accounted} are accounted for; "
            f"{scanned - accounted} would be missing from the output tree", file=sys.stderr)

    # 先算出真正需要哪些工具，再去解析它们；不压缩的那一类连查找都不做。
    # passthrough 里的文件只会被复制，不需要任何工具——所以 `--only video` 在没有
    # caesiumclt 的机器上也跑得起来。
    # 图像也要 ffprobe：--image-max-edge 要先知道源的最长边才能决定是否下传
    # --long-edge（dry-run 打印的命令要如实反映这一点）。
    # 音频用 ffmpeg 转码、ffprobe 校验，两者都由 ffmpeg 那一项覆盖。
    needed = (["caesium", "ffprobe"] if images else []) \
        + (["ffprobe", "handbrake"] if videos else []) \
        + (["ffmpeg", "ffprobe"] if audios else [])
    found = tools(needed)
    absent = [name for name in needed if not found[name]]
    if absent:
        log(f"[ERROR] missing tool(s): {', '.join(absent)}"
              f" (set CAESIUM_CLT / HANDBRAKE_CLI / FFPROBE / FFMPEG to override the path)",
              file=sys.stderr)
        return 1

    # 按媒体类型给出 (源, 输出, 输出根, 原样复制路径)，并一次性滤掉已有输出与过长的路径。
    # COPY 一类永远不压缩，只在 --copy-unprocessed yes 时原样搬进输出目录。
    plan: list[tuple[str, set, list[tuple[Path, Path, Path, Path]]]] = []
    # 预过滤（已存在/撞名/路径过长）与阶段内跳过分开计数：前者不在 todo 里，
    # 混进 TOTAL 的 SKIP 会得出"共 1 个却跳过 8 个"这种自相矛盾的行。
    prefiltered = 0
    # 输出目录留下的缺口：走完全流程却没有对应文件。删源目录前必须为 0。
    gaps: list[tuple[str, str, Path]] = []    # (kind, 原因, 路径)
    # 图像输出扩展名由 --image-format 决定；original 时沿用源扩展名。
    # 这一步同时决定"已存在则跳过"的比对路径，格式换了才不会被误判成已完成。
    image_ext = FORMAT_EXTS[args.image_format]

    # 名字冲突全部交给运行期的 resolve_free_name 处理，规划期不预定任何名字：
    # 先占住会让 process 把自己想要的名字判成"已被占用"，平白多出一个 -2。
    audio_ext = AUDIO_TARGETS[args.audio_codec][0]
    phases = (("IMAGE", sorted(images, key=lambda i: str(i[0])), image_ext),
              ("VIDEO", sorted(videos, key=lambda i: str(i[0])), container_ext),
              ("AUDIO", sorted(audios, key=lambda i: str(i[0])), audio_ext),
              ("COPY", sorted(passthrough, key=lambda i: str(i[0])), ""))

    # 名字策略：不冲突就用最简名（`a.webp`），只有真的会和**别的源**撞名时才把源扩展名
    # 也写进去（`a.png.webp`）。正常目录里保持简洁，同 stem 多格式时才限定。
    entries: list[tuple[str, Path, Path, Path, str]] = []   # (kind, src, root, out_root, want)
    for kind, items, suffix in phases:
        for src, root, out_root in items:
            entries.append((kind, src, root, out_root, suffix or src.suffix))
    # 每个源都要按**它自己**的目标扩展名来算名字——跨媒体类型时不等于当前源的那个
    # （`.webp` 图像走 passthrough 时扩展名不变，而 `.png` 要转 webp）。
    # 同时要记住各自的 root：镜像结构靠 src.relative_to(root)，传错就会把子目录里的
    # 文件平铺到输出根（实测踩过）。
    # 同一次运行里出现相同的源只可能来自互相重叠的输入参数，去重后再判重名。
    plans_of: dict[Path, tuple[Path, Path, str]] = {}      # src -> (root, out_root, want)
    for kind, src, root, out_root, want in entries:
        plans_of.setdefault(src, (root, out_root, want))

    # 名字要一次性定稳：谁因为撞名而加了限定，和它有牵连的那些源的名字也得跟着重算，
    # 所以用一个工作集反复迭代到不再变化为止。加上限是防御——正常情况一两轮就收敛。
    #
    # 只在**同一套名字空间内**比：目标名之间比、保留名之间比。不做"我的目标 vs 别人的
    # 保留名"这种交叉比较——那是误判：`s.wav`(目标 s.mp3、保留 s.wav) 与
    # `s.flac`(目标 s.flac.mp3、保留 s.flac) 四个名字两两不同，根本没有冲突，交叉比对
    # 却会把 s.wav 判成冲突，让它白白变成 `s.wav.mp3`。实测踩过。
    qualified: set[Path] = set()
    names: dict[Path, tuple[Path, Path]] = {}
    for _ in range(6):
        for src, (root, out_root, want) in plans_of.items():
            names[src] = wanted_pair(src, root, out_root, want, src in qualified)
        changed = False
        for src in plans_of:
            target, kept = names[src]
            for other in plans_of:
                if other == src:
                    continue
                other_target, other_kept = names[other]
                if target == other_target or kept == other_kept:
                    if src not in qualified:
                        qualified.add(src)
                        changed = True
                    if other not in qualified:
                        qualified.add(other)
                        changed = True
                    break
        if not changed:
            break
    for src, (root, out_root, want) in plans_of.items():
        names[src] = wanted_pair(src, root, out_root, want, src in qualified)

    by_phase: dict[str, list[tuple[Path, Path, Path, Path]]] = {}
    for kind, src, root, out_root, want in entries:
        if len(str(src)) > MAX_PATH_LENGTH:
            log(f"[{kind}] [SKIP] path too long (>{MAX_PATH_LENGTH})  {src}")
            prefiltered += 1
            gaps.append((kind, "path too long", src))
            continue
        target, kept = names[src]
        # 两种产物各查一次：转换成功落在 target，压不动保留原件落在 kept（源名）。
        done = next((p for p in (target, kept)
                     if p.is_file() and p.stat().st_size > 0), None)
        if done is not None:
            log(f"[{kind}] [SKIP] output exists  {done}")
            prefiltered += 1
            continue
        by_phase.setdefault(kind, []).append((src, target, kept, out_root))

    # 执行顺序：先原样复制（最快，且复制都是纯 IO），再图像，然后音频，最后视频。
    # 视频放最后是因为它最慢、且 HandBrake 的管线吃 CPU，放在末尾不会拖住别的阶段。
    # 收集与命名的顺序仍走 phases，不随之改变——命名只跟源集合有关，与先后无关。
    for kind in ("COPY", "IMAGE", "AUDIO", "VIDEO"):
        pending = by_phase.get(kind)
        if pending:
            plan.append((kind, set(), pending))

    # 输出根集合：临时文件清理要按输出根来扫，而不是扫整个源目录。
    out_roots = {out_root for _kind, _src, _root, out_root, _want in entries}

    # 开工前先清掉上一次留下的临时文件。此刻本次运行还没建过任何临时文件，所以凡是
    # 符合命名规则的必定是历史残留——进程被强杀时 finally 不执行，就靠这一步兜底。
    leftovers = sweep_temp_files(out_roots, whole_run=True)
    if leftovers:
        log(f"cleaned up {leftovers} leftover temp file(s) from a previous run")

    todo = sum(len(pending) for _, _taken, pending in plan)
    if not todo:
        note = f" ({prefiltered} skipped beforehand)" if prefiltered else ""
        log(f"nothing to process.{note}")
        return 0

    log(f"IMAGE {len(images)} / VIDEO {len(videos)} / AUDIO {len(audios)}"
          f" / COPY {len(passthrough)}"
          f"  (preset {preset_name}, container {container_ext})"
          + (f"  [{prefiltered} skipped beforehand]" if prefiltered else "")
          + ("  [dry-run]" if args.dry_run else "")
          + ("" if args.copy_unprocessed == "yes"
             else "  [--copy-unprocessed no: output tree will be incomplete]"))

    tmp_for: dict[Path, Path] = {}            # 输出根 -> 本次运行在该卷上的临时目录
    tmp_dirs: set[Path] = set()               # 本次运行建出的临时目录，finally 清理
    tmp_lock = Lock()                         # 保护上面两个共享集合

    def temp_dir(out_root: Path) -> Path:
        """取（必要时创建）该输出根的临时目录；并发下只建一次。"""
        with tmp_lock:
            tmp = tmp_for.get(out_root)
            if tmp is None:
                tmp = make_temp_dir(out_root)
                tmp_for[out_root] = tmp
                tmp_dirs.add(tmp)
            return tmp

    # 单个待办文件的完整处理：返回 (tag, 源, 目标, 源大小, 压缩后大小, 结果词, 备注)，
    # 结果词取 OK / SKIP / COPY / FAIL / DRY。记账全部交给主线程的 report 做，
    # 所以并发时不需要给计数器加锁。
    def process(index: int, kind: str, src: Path, target: Path, kept: Path, out_root: Path,
                taken: set, name_lock) -> tuple:
        tag = f"[{index:>{len(str(todo))}}/{todo}] [{kind}]"
        if src.resolve() == target.resolve():
            gaps.append((kind, "output would overwrite the source", src))
            return tag, src, target, 0, 0, "SKIP", "output would overwrite the source"
        try:
            size = src.stat().st_size
        except OSError as exc:
            gaps.append((kind, f"cannot stat source: {exc}", src))
            return tag, src, target, 0, 0, "FAIL", f"cannot stat source: {exc}"
        log(f"{tag} {src}", flush=True)

        # 主路径的名字。保留件（kept）就是源名、已经确定，不需要在这里解析，也就不会
        # 出现"先占了主路径的名字却什么都没写"的情况——那种情况会让重跑永远认不出
        # 已完成，每次多生成一个带序号的副本。
        try:
            real_target = resolve_free_name(target, taken, name_lock)
        except OSError as exc:
            gaps.append((kind, f"no free output name: {exc}", src))
            return tag, src, target, size, 0, "FAIL", f"no free output name: {exc}"
        if real_target != target:
            log(f"    note: {target.name} taken in this run, writing {real_target.name}")

        if kind == "COPY":                    # 不压缩，只看 --copy-unprocessed
            # 措辞按文件性质分开：音频不是"格式不支持"，只是它已经是目标格式、
            # 或没调码率所以不值得重编。一律说"unsupported format"会误导。
            if src.suffix.lower() in AUDIO_EXTS:
                copied_note = "already in the target format, copied as is"
            else:
                copied_note = "unsupported format, copied as is"
            if args.copy_unprocessed == "no":
                gaps.append((kind, copied_note, src))
                return tag, src, target, size, 0, "SKIP", copied_note
            if args.dry_run:
                log(f"    copy -> {real_target}", flush=True)
                return tag, src, target, size, 0, "DRY", ""
            failed_copy = deliver(kind, tag, src, real_target, size)
            return failed_copy or (tag, src, real_target, size, 0, "COPY", copied_note)
        if kind == "IMAGE":
            # 只有源超过上限才缩。caesium 本身不会放大，但先判断能让 dry-run
            # 打印出真正会执行的参数。
            shrink = 0
            if args.image_max_edge > 0:
                edge = longest_edge(found["ffprobe"], src)
                if edge > args.image_max_edge:
                    shrink = args.image_max_edge
            if args.dry_run:
                command = [found["caesium"], "-q", str(args.image_quality),
                           "--keep-orientation", "--keep-dates", "-O", "all", "--json",
                           "-o", str(out_root / f".media-compress-tmp-{os.getpid()}")]
                if not args.image_strip_exif:
                    command.append("-e")
                if args.image_format != "original" \
                        and src.suffix.lower() != real_target.suffix.lower():
                    command += ["--format", args.image_format]
                if shrink:
                    command += ["--long-edge", str(shrink), "--no-upscale"]
                log("    " + " ".join(command + [str(src)]), flush=True)
                return tag, src, target, size, 0, "DRY", ""
            try:
                tmp = temp_dir(out_root)
            except OSError as exc:
                # 临时目录建不出来，压缩没法进行；但输出目录仍要完整。
                gaps.append((kind, f"cannot create temp dir: {exc}", src))
                failed_copy = deliver(kind, tag, src, real_target, size)
                return failed_copy or (tag, src, real_target, size, 0, "COPY",
                                       "cannot create temp dir, copied as is")
            with tmp_lock:
                tmp_dirs.add(tmp)             # 登记后即使中断也会被清理
            new_size, reason = compress_image(found["caesium"], src, real_target,
                                              args.image_quality, args.image_format,
                                              args.image_strip_exif, shrink, tmp)
        if kind == "AUDIO":
            new_size, reason = compress_audio(found["ffmpeg"], found["ffprobe"], src,
                                              real_target, args.audio_codec,
                                              args.audio_bitrate, args.dry_run)
            if reason == "dry_run":
                return tag, src, target, size, 0, "DRY", ""
        elif kind == "VIDEO":
            # 临时文件是 .mctmp，容器由 --format 显式给出；每次调用唯一，便于并发。
            new_size, reason = compress_video(found["handbrake"], found["ffprobe"], src,
                                              real_target, temp_file_for(real_target),
                                              config_path, preset_name, file_format,
                                              args.dry_run)
            if reason == "dry_run":
                return tag, src, target, size, 0, "DRY", ""

        if not reason:                        # 压缩成功
            return tag, src, real_target, size, new_size, "OK", ""

        # 未产出可用结果。压缩出错时永远复制：删源目录前必须保证输出目录完整，
        # 否则会丢文件。故意跳过（省得不够 / 现代编码 / HDR / 码率不划算）则听
        # --copy-unprocessed。
        #
        # 落脚在 kept（= 源名），所以扩展名与内容一致，不会说谎。它在规划阶段已经
        # 查过"是否已存在"，走到这里说明还没写过，直接复制即可。
        def keep_original(note: str) -> tuple:
            failed_copy = deliver(kind, tag, src, kept, size)
            return failed_copy or (tag, src, kept, size, 0, "COPY", note)

        if kind != "COPY" and reason not in INTENTIONAL_SKIPS and reason != "not_smaller":
            return keep_original(f"compression failed ({reason}), copied as is")
        if reason == "not_smaller":
            note = "not worth compressing, copied as is"
        elif reason in INTENTIONAL_SKIPS:
            note = f"{reason}, copied as is"
        if args.copy_unprocessed == "no":
            gaps.append((kind, reason, src))
            return tag, src, target, size, 0, "SKIP", f"{reason} (not copied)"
        return keep_original(note)

    def report(results: list[tuple]) -> None:
        """在主线程里记账并打印，逐条处理以便并发结果一到就显示。"""
        nonlocal done, failed, copied, saved, skipped
        for tag, src, target, size, new_size, word, note in results:
            if word == "DRY":
                continue
            if word == "OK":
                done += 1
                saved += max(0, size - new_size)
                ratio = f"-{100 * (size - new_size) / size:.0f}%" if size else "-0%"
                log(f"{tag} [OK] {ratio}  "
                      f"{human(size)} -> {human(new_size)}  {target}")
            elif word == "COPY":
                copied += 1
                log(f"{tag} [COPY] {note}  {target}")
            elif word == "SKIP":
                skipped += 1
                log(f"{tag} [SKIP] {note}  {src}")
            else:
                failed += 1
                log(f"{tag} [FAIL] {note}  {src}")

    done = failed = copied = skipped = 0
    saved = 0
    # 进出总量按本次实际处理的文件算：被"已存在"过滤掉的不参与，合计才对得上。
    total_in = 0
    for _, _taken, pending in plan:
        for src, _target, _kept, _out_root in pending:
            try:
                total_in += src.stat().st_size
            except OSError:
                pass
    # 输出名消歧用的锁：图像阶段是多线程的，必须让它和 taken 一起受保护。
    name_lock = Lock()
    try:
        for kind, taken, pending in plan:
            if kind != "IMAGE" or args.image_jobs == 1:
                # 逐个处理、逐个上报：绝不能先把整批 process 完再一起 report，
                # 否则完成行要等到这批结束才出现（视频批尤其致命）。
                for i, (src, target, kept, out_root) in enumerate(pending, 1):
                    report([process(i, kind, src, target, kept, out_root,
                                    taken, name_lock)])
                continue
            # 图像之间并发；视频保持串行——HandBrake 的管线本身就吃 CPU，
            # 实测与图像并发只会互相拖慢（视频侧慢 1.8 倍）。
            with ThreadPoolExecutor(max_workers=args.image_jobs) as pool:
                futures = [pool.submit(process, i, kind, src, target, kept, out_root,
                                       taken, name_lock)
                           for i, (src, target, kept, out_root) in enumerate(pending, 1)]
                for future in as_completed(futures):
                    report([future.result()])
    finally:
        for tmp in tmp_dirs:                  # 哪怕 Ctrl+C 也不留临时目录
            shutil.rmtree(tmp, ignore_errors=True)
        # 再兜一遍临时文件：正常路径上各文件都自己删过，这里只处理异常中断漏掉的
        # （只删本进程的，免得踩到另一个同时在跑的实例）。
        sweep_temp_files(out_roots)

    if args.dry_run:
        log(f"TOTAL {todo}  dry-run only, nothing written")
        return 0
    counts = f"TOTAL {todo}  OK {done}  SKIP {skipped}  COPY {copied}  FAIL {failed}"
    final_size = total_in - saved
    if total_in:
        log(f"{counts}  total {human(total_in)} -> {human(final_size)}  "
              f"saved {human(saved)}  ({100 * saved / total_in:.0f}%)")
    else:
        log(f"{counts}  saved 0 B")

    # 输出目录完整性：这个脚本的用途是"压完抽查、无误就删原文件夹"，
    # 所以必须明确回答"现在能不能删"。只要还有文件没进输出目录就拦住。
    if gaps:
        log(f"WARNING: {len(gaps)} file(s) are NOT in the output tree; "
              f"do NOT delete the source folder:", file=sys.stderr)
        for kind, reason, path in gaps:
            log(f"  [MISSING] [{kind}] {reason}  {path}", file=sys.stderr)
    else:
        log(f"output tree complete for {todo} file(s); "
            f"the source folder can be replaced by the output tree")
    return 1 if failed else 0

if __name__ == "__main__":
    setup_console()
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        log("interrupted.", file=sys.stderr)
        sys.exit(130)
