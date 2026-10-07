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

工具查找顺序: 环境变量 CAESIUM_CLT / HANDBRAKE_CLI / FFPROBE -> PATH ->
常见安装目录。缺失的工具只在真正需要处理该类媒体时才会报错。

退出码: 0 成功或跳过；1 存在失败文件或工具/配置缺失；2 参数错误。
"""
from __future__ import annotations

import argparse
import json
import os
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
# compress_video 返回这些原因表示"故意不动它"，不是失败：算 SKIP 而不是 FAIL，
# 也不影响退出码。HDR 重编会变色，现代编码器重编通常只会更大。
INTENTIONAL_SKIPS = {"hdr", "modern_codec"}
# HandBrake 的 FileFormat 取值 -> 容器扩展名。
CONTAINER_EXTS = {"av_mp4": ".mp4", "av_m4v": ".mp4", "av_mkv": ".mkv",
                  "av_webm": ".webm", "av_avi": ".avi"}
# 图像输出格式 -> 扩展名；original 表示沿用源扩展名。
FORMAT_EXTS = {"original": "", "jpeg": ".jpg", "png": ".png", "gif": ".gif",
               "webp": ".webp", "tiff": ".tiff"}

MIN_SAVINGS_RATIO = 0.05          # 目的地动作: 至少省这么多才认为值得替换
PROBE_TIMEOUT = 60
MAX_PATH_LENGTH = 240            # Windows 上超过这个长度的路径工具容易失败


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


def load_preset(path: Path, wanted: str = "") -> tuple[str, str, list[str]]:
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
    return name, CONTAINER_EXTS.get(raw_format, ".mp4"), names


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


def compress_video(handbrake: str, ffprobe: str, src: Path, target: Path,
                   config_path: Path, preset_name: str, dry_run: bool) -> tuple[int, str]:
    """转码单个视频，成功返回 (压缩后字节数, "")；失败或省得不够返回 (0, 原因)。"""
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

    temp = target.with_name(target.name + ".tmp")
    command = [handbrake, "-i", str(src), "-o", str(temp),
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

def classify(path: Path) -> str:
    """返回 image / video / passthrough / junk。

    passthrough 表示"不压缩、但会原样搬到输出目录"，包含两类：
      * caesiumclt 读不了的图像格式；
      * 所有非媒体文件（.txt/.srt/.nfo/.md ...）。
    两类都必须进队列，否则输出目录会缺文件——而这个脚本的用途是"压完删源目录"，
    缺文件就等于丢数据。只有明确的操作系统垃圾（Thumbs.db 等）才丢下不管。
    """
    if path.name.lower() in JUNK_NAMES:
        return "junk"
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        return "passthrough" if suffix in PASSTHROUGH_EXTS else "image"
    if suffix in VIDEO_EXTS:
        return "video"
    return "passthrough"


Item = tuple[Path, Path, Path]               # (源文件, 输入根目录, 输出根目录)


def collect(paths: list[Path], output: str | None) \
        -> tuple[list[Item], list[Item], list[Item], int, int]:
    """展开输入为 (图像, 视频, 仅复制, 扫描总数, 丢弃的垃圾数)，不读取文件内容。

    "仅复制"包括非媒体文件（.txt/.srt/.nfo/...）和 caesiumclt 读不了的图像格式，
    它们不压缩但会原样搬进输出目录——这个脚本的用途是"压完删源目录"，漏一个就是
    丢数据。返回总数让调用方能交叉校验：凡是扫到却没有去处的文件都说明输出目录会
    缺东西，必须报警而不是宣称"可以删源目录"。

    每个输入各自决定输出根目录：显式 --output 时是所有输入共用的那一个，
    否则是该输入自己的 <目录>/_compressed/。
    """
    images: list[Item] = []
    videos: list[Item] = []
    passthrough: list[Item] = []
    scanned = 0
    junk = 0
    for path in paths:
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
            kind = classify(item)
            if kind == "image":
                images.append((item, root, out_root))
            elif kind == "video":
                videos.append((item, root, out_root))
            elif kind == "passthrough":
                passthrough.append((item, root, out_root))
            else:
                junk += 1                     # 操作系统垃圾，有意不搬
    return images, videos, passthrough, scanned, junk


def destination(src: Path, root: Path, out_root: Path, suffix: str) -> Path:
    """输出路径: 在输出根目录下镜像源目录结构，只把扩展名换成目标容器。"""
    try:
        relative = src.relative_to(root).with_suffix(suffix)
    except ValueError:
        relative = Path(src.with_suffix(suffix).name)
    if not relative.parts:
        relative = Path(src.with_suffix(suffix).name)
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
    parser.add_argument("--only", choices=("image", "video"),
                        help="compress one media kind only; the other kind is still handled "
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
    parser.add_argument("--config", metavar="FILE", default=None,
                        help="HandBrake preset JSON to use for video "
                             f"(default: {CONFIG_PATH.name} next to this script)")
    parser.add_argument("--preset", metavar="NAME", default=None,
                        help="preset to pick from --config (default: the first one). "
                             "Names are case-sensitive.")
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

    # 配置和预设要在扫描之前定下来并校验：参数写错却先跑，会白做几百个文件
    # （而且它们已经进了输出目录）。--config 的相对路径按调用者的当前目录解析，
    # 这才符合命令行直觉。
    global _config_note
    config_path = Path(args.config).expanduser() if args.config else CONFIG_PATH
    preset_name, container_ext, preset_names = load_preset(config_path, args.preset or "")
    _config_note = (config_path, preset_name, container_ext, preset_names)
    paths = [Path(p).expanduser() for p in args.paths]
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
    logger: Logger | None = None
    if args.log != "no":
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
        return compress_all(args, paths, config_path, preset_name, container_ext)
    finally:
        if logger is not None:
            logger.close()


def compress_all(args, paths: list[Path], config_path: Path, preset_name: str,
                 container_ext: str) -> int:
    """打开日志之后的主体；单独成函数，好让日志在 finally 里可靠关闭。"""
    images, videos, passthrough, scanned, junk = collect(paths, args.output)

    # --only 表示"只**压缩**这一类"，不是"只出现在输出目录"。另一类照样按
    # --copy-unprocessed 处理：yes 时原样复制（输出目录因此仍是完整的，可以替换源
    # 目录），no 时才真的丢弃。否则 `--only image` 会悄悄让输出目录缺掉所有视频，
    # 而末尾那句"可以删源目录"就成了谎话。
    ignored = 0
    if args.only == "image":
        if args.copy_unprocessed == "yes":
            passthrough += videos          # 视频降级为"只复制"，永不压缩
        else:
            ignored = len(videos)
        videos = []
    elif args.only == "video":
        if args.copy_unprocessed == "yes":
            passthrough += images
        else:
            ignored = len(images)
        images = []

    # 交叉校验：扫到的文件必须都有去处——入队、被 --only 有意丢弃、或被明确判为
    # 系统垃圾。剩下的就是"无处可去"，那会在输出目录里缺席，也就是最后那句
    # "可以删源目录"在说谎。这条断言存在的意义就是让那种情况不可能静默发生。
    accounted = len(images) + len(videos) + len(passthrough) + ignored + junk
    if scanned != accounted:
        log(f"[WARNING] scanned {scanned} file(s) but only {accounted} are accounted for; "
            f"{scanned - accounted} would be missing from the output tree", file=sys.stderr)

    # 先算出真正需要哪些工具，再去解析它们；不压缩的那一类连查找都不做。
    # passthrough 里的文件只会被复制，不需要任何工具——所以 `--only video` 在没有
    # caesiumclt 的机器上也跑得起来。
    # 图像也要 ffprobe：--image-max-edge 要先知道源的最长边才能决定是否下传
    # --long-edge（dry-run 打印的命令要如实反映这一点）。
    needed = (["caesium", "ffprobe"] if images else []) \
        + (["ffprobe", "handbrake"] if videos else [])
    found = tools(needed)
    absent = [name for name in needed if not found[name]]
    if absent:
        log(f"[ERROR] missing tool(s): {', '.join(absent)}"
              f" (set CAESIUM_CLT / HANDBRAKE_CLI / FFPROBE to override the path)",
              file=sys.stderr)
        return 1

    # 按媒体类型给出 (源, 输出, 输出根, 原样复制路径)，并一次性滤掉已有输出与过长的路径。
    # COPY 一类永远不压缩，只在 --copy-unprocessed yes 时原样搬进输出目录。
    plan: list[tuple[str, list[tuple[Path, Path, Path, Path]]]] = []
    # 预过滤（已存在/撞名/路径过长）与阶段内跳过分开计数：前者不在 todo 里，
    # 混进 TOTAL 的 SKIP 会得出"共 1 个却跳过 8 个"这种自相矛盾的行。
    prefiltered = 0
    # 输出目录留下的缺口：走完全流程却没有对应文件。删源目录前必须为 0。
    gaps: list[tuple[str, str, Path]] = []    # (kind, 原因, 路径)
    # 图像输出扩展名由 --image-format 决定；original 时沿用源扩展名。
    # 这一步同时决定"已存在则跳过"的比对路径，格式换了才不会被误判成已完成。
    image_ext = FORMAT_EXTS[args.image_format]

    def keep_name(src: Path, target: Path) -> Path:
        """省不到时原样复制的落脚路径：保留**源**扩展名。

        转 webp 没省到时复制的是原始 jpg 字节，若仍叫 .webp 就是扩展名说谎
        （内容真的是 JPEG）。所以这种情况下退回源文件名；真正转换成功才用新扩展名。
        """
        return target if target.suffix == src.suffix \
            else target.with_name(src.stem + src.suffix)

    # 同目录下同名不同扩展名（poster.jpg + poster.png）在格式转换后会争同一个输出名。
    # 同目录同 stem 超过一个文件就算"有争议"：这类只能保一个，让先到的那个既占
    # target 又占 fallback，另一个记缺口跳过——牺牲一个文件也好过两个源往同一路径
    # 写、互相覆盖。按源路径排序，所以同一份输入每次得到同样的结果。
    stems: dict[tuple[Path, str], set[str]] = {}
    for entries in (images, videos, passthrough):
        for src, _root, out_root in entries:
            stems.setdefault((out_root, src.stem.lower()), set()).add(src.suffix.lower())

    for kind, items, suffix in (("IMAGE", sorted(images, key=lambda i: str(i[0])), image_ext),
                                ("VIDEO", sorted(videos, key=lambda i: str(i[0])), container_ext),
                                ("COPY", sorted(passthrough, key=lambda i: str(i[0])), "")):
        # 每阶段单独占用输出名：跨阶段共表会误判。
        taken: dict[Path, Path] = {}
        pending: list[tuple[Path, Path, Path, Path]] = []
        for src, root, out_root in items:
            if len(str(src)) > MAX_PATH_LENGTH:
                log(f"[{kind}] [SKIP] path too long (>{MAX_PATH_LENGTH})  {src}")
                prefiltered += 1
                gaps.append((kind, "path too long", src))
                continue
            target = destination(src, root, out_root, suffix or src.suffix)
            # 有争议时退回 target：输出目录必须完整，此时宁可让扩展名说谎。
            disputed = len(stems.get((out_root, src.stem.lower()), ())) > 1
            fallback = target if disputed else keep_name(src, target)
            # 两条可能的落脚路径都要防撞名、都要判"已存在"：转换成功落在 target，
            # 省不到则原样落在 fallback，只查其中一条会漏。
            clash = next((p for p in (fallback, target)
                          if p in taken and taken[p] != src), None)
            if clash is not None:
                log(f"[{kind}] [SKIP] output name taken by {taken[clash]}  {clash}")
                prefiltered += 1
                gaps.append((kind, "output name taken", clash))
                continue
            existing = next((p for p in (fallback, target)
                             if p.is_file() and p.stat().st_size > 0), None)
            if existing is not None:
                log(f"[{kind}] [SKIP] output exists  {existing}")
                prefiltered += 1
                continue
            taken[fallback] = src
            taken[target] = src
            pending.append((src, target, out_root, fallback))
        if pending:
            plan.append((kind, pending))

    todo = sum(len(pending) for _, pending in plan)
    if not todo:
        note = f" ({prefiltered} skipped beforehand)" if prefiltered else ""
        log(f"nothing to process.{note}")
        return 0

    log(f"IMAGE {len(images)} / VIDEO {len(videos)} / COPY {len(passthrough)}"
          f"  (preset {preset_name}, container {container_ext})"
          + (f"  [{prefiltered} skipped beforehand]" if prefiltered else "")
          + ("  [dry-run]" if args.dry_run else "")
          + ("" if args.copy_unprocessed == "yes"
             else "  [--copy-unprocessed no: output tree will be incomplete]"))

    def deliver(kind: str, tag: str, src: Path, target: Path, size: int) -> tuple | None:
        """把未压缩的文件原样搬进输出目录；失败返回结果元组，成功返回 None。"""
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
        except OSError as exc:
            # 要复制却复制失败 = 输出目录缺口，必须让用户看见。
            gaps.append((kind, f"copy failed: {exc}", src))
            return tag, src, target, size, 0, "FAIL", f"copy: {exc}"
        return None

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
    def process(index: int, kind: str, src: Path, target: Path, out_root: Path,
                fallback: Path) -> tuple:
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

        if kind == "COPY":                    # 不压缩，只看 --copy-unprocessed
            if args.copy_unprocessed == "no":
                gaps.append((kind, "unsupported format, not copied", src))
                return tag, src, target, size, 0, "SKIP", "unsupported format, not copied"
            if args.dry_run:
                log(f"    copy -> {fallback}", flush=True)
                return tag, src, target, size, 0, "DRY", ""
            failed_copy = deliver(kind, tag, src, fallback, size)
            return failed_copy or (tag, src, fallback, size, 0, "COPY",
                                   "unsupported format, copied as is")
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
                        and src.suffix.lower() != target.suffix.lower():
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
                failed_copy = deliver(kind, tag, src, fallback, size)
                return failed_copy or (tag, src, fallback, size, 0, "COPY",
                                       "cannot create temp dir, copied as is")
            with tmp_lock:
                tmp_dirs.add(tmp)             # 登记后即使中断也会被清理
            new_size, reason = compress_image(found["caesium"], src, target,
                                              args.image_quality, args.image_format,
                                              args.image_strip_exif, shrink, tmp)
        else:
            new_size, reason = compress_video(found["handbrake"], found["ffprobe"], src,
                                              target, config_path, preset_name, args.dry_run)
            if reason == "dry_run":
                return tag, src, target, size, 0, "DRY", ""

        if not reason:                        # 压缩成功
            return tag, src, target, size, new_size, "OK", ""

        # 未产出可用结果。压缩出错时永远复制：删源目录前必须保证输出目录完整，
        # 否则会丢文件。故意跳过（省得不够 / 现代编码 / HDR）则听 --copy-unprocessed。
        # 这些都复制**源文件本身**，所以落脚在 fallback（保留源扩展名）而不是 target。
        if kind != "COPY" and reason not in INTENTIONAL_SKIPS and reason != "not_smaller":
            note = f"compression failed ({reason}), copied as is"
            failed_copy = deliver(kind, tag, src, fallback, size)
            return failed_copy or (tag, src, fallback, size, 0, "COPY", note)
        if reason == "not_smaller":
            note = "not worth compressing, copied as is"
        elif reason in INTENTIONAL_SKIPS:
            note = f"{reason}, copied as is"
        if args.copy_unprocessed == "no":
            gaps.append((kind, reason, src))
            return tag, src, target, size, 0, "SKIP", f"{reason} (not copied)"
        failed_copy = deliver(kind, tag, src, fallback, size)
        return failed_copy or (tag, src, fallback, size, 0, "COPY", note)

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
    for _, pending in plan:
        for src, _target, _out_root, _fallback in pending:
            try:
                total_in += src.stat().st_size
            except OSError:
                pass
    try:
        for kind, pending in plan:
            if kind != "IMAGE" or args.image_jobs == 1:
                # 逐个处理、逐个上报：绝不能先把整批 process 完再一起 report，
                # 否则完成行要等到这批结束才出现（视频批尤其致命）。
                for i, (src, target, out_root, fallback) in enumerate(pending, 1):
                    report([process(i, kind, src, target, out_root, fallback)])
                continue
            # 图像之间并发；视频保持串行——HandBrake 的管线本身就吃 CPU，
            # 实测与图像并发只会互相拖慢（视频侧慢 1.8 倍）。
            with ThreadPoolExecutor(max_workers=args.image_jobs) as pool:
                futures = [pool.submit(process, i, kind, src, target, out_root, fallback)
                           for i, (src, target, out_root, fallback) in enumerate(pending, 1)]
                for future in as_completed(futures):
                    report([future.result()])
    finally:
        for tmp in tmp_dirs:                  # 哪怕 Ctrl+C 也不留临时目录
            shutil.rmtree(tmp, ignore_errors=True)

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
