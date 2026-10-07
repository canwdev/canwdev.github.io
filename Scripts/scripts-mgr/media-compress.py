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


def log(message: str = "", file=None, **_ignored) -> None:
    """带人类可读时间戳的输出。

    时间戳打在**每一行**上，因为多行结果（例如"输出目录完整"那两行）只有每行
    各自带时间才知道那会儿在做什么。注意换行符在时间戳之前，续行才不会被污染。
    并发时也逐行加锁式打印，所以时间戳的顺序与实际写出顺序一致。
    总是 flush：后台运行或管道里被缓冲的话，时间戳就失去意义了。
    """
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{stamp} {message}", file=file, flush=True)


def human(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size) < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


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


def load_preset(path: Path) -> tuple[str, str]:
    """读 HandBrake 预设文件，返回 (预设名, 输出容器扩展名)。"""
    if not path.is_file():
        raise SystemExit(f"[ERROR] config file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        preset = (data.get("PresetList") or [])[0]
        name = str(preset["PresetName"])
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise SystemExit(f"[ERROR] cannot parse config ({exc}): {path}") from None
    return name, CONTAINER_EXTS.get(str(preset.get("FileFormat", "")), ".mp4")


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

def temp_dir_for(target: Path) -> Path:
    """caesiumclt 的输出目录，按目标文件独立命名，避免一个共享目录。

    caesiumclt 只支持"输出目录"、无法指定输出文件名，所以必须先落一个目录。
    它必须和 target 同卷，否则 os.replace 跨盘会报 WinError 17（退化成复制则
    失去原子性）。因此宁可留一个隐藏目录，也不要放到系统临时目录去。
    """
    return target.parent / f".{target.name}.mc-tmp"


def compress_image(caesium: str, src: Path, target: Path, quality: int, image_format: str,
                   strip_exif: bool, dry_run: bool, tmp: Path) -> tuple[int, str]:
    """压缩单张图像，成功返回 (压缩后字节数, "")；失败或省得不够返回 (0, 原因)。

    caesiumclt 的 `-e` 是"保留 EXIF"，所以 --image-strip-exif 是省掉该开关而
    不是加上某个开关。
    `--keep-orientation` 始终保留：只留方向标签，否则带 EXIF 旋转的照片会躺倒。

    临时目录由调用方按文件独立命名并登记清理；创建推迟到真正要压缩之时，
    所以 dry-run 和"输出会覆盖源文件"这类提前跳过的路径不留任何东西。
    每次调用用独立目录，多个并发任务才不会写进同一个目录互相覆盖。
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
    command.append(str(src))
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
    os.replace(produced, target)                  # 同卷改名，原子
    return size, ""


def compress_video(handbrake: str, ffprobe: str, src: Path, target: Path,
                   preset_name: str, dry_run: bool) -> tuple[int, str]:
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
               "--preset-import-file", str(CONFIG_PATH), "--preset", preset_name]
    if dry_run:
        log("    " + " ".join(command))
        return 0, "dry_run"

    target.parent.mkdir(parents=True, exist_ok=True)
    try:        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
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
    """返回 image / video / passthrough / junk / other。

    passthrough 表示"不压缩、但可以原样搬过去"：caesiumclt 读不了的格式。
    这类文件必须进队列，否则 --copy-unprocessed 管不到它，输出目录会缺文件。
    """
    if path.name.lower() in JUNK_NAMES:
        return "junk"
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        return "passthrough" if suffix in PASSTHROUGH_EXTS else "image"
    if suffix in VIDEO_EXTS:
        return "video"
    return "other"


Item = tuple[Path, Path, Path]               # (源文件, 输入根目录, 输出根目录)


def collect(paths: list[Path], output: str | None) -> tuple[list[Item], list[Item], list[Item]]:
    """展开输入为 (图像, 视频, 仅复制) 三个列表，过程不读取任何文件内容。

    每个输入各自决定输出根目录：显式 --output 时是所有输入共用的那一个，
    否则是该输入自己的 <目录>/_compressed/。
    """
    images: list[Item] = []
    videos: list[Item] = []
    passthrough: list[Item] = []
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
            if out_root in item.parents:
                continue                      # 不处理自己的输出
            kind = classify(item)
            if kind == "image":
                images.append((item, root, out_root))
            elif kind == "video":
                videos.append((item, root, out_root))
            elif kind == "passthrough":
                passthrough.append((item, root, out_root))
    return images, videos, passthrough


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
    parser.add_argument("--only", choices=("image", "video"), help="process one media kind only")
    parser.add_argument("--image-quality", type=int, default=82,
                        help="image quality 0-100 (default: 82)")
    parser.add_argument("--image-format", default="original", choices=tuple(FORMAT_EXTS),
                        help="image output format (default: original, keep source format)")
    parser.add_argument("--image-strip-exif", action="store_true",
                        help="strip image EXIF (including GPS and other private data)")
    parser.add_argument("--image-jobs", type=int, default=3,
                        help="parallel image compressions (default: 3; 1 = serial)")
    parser.add_argument("--copy-unprocessed", choices=("yes", "no"), default="yes",
                        help="copy files left uncompressed into the output tree "
                             "(default: yes). 'no' makes the output tree INCOMPLETE, "
                             "so it can no longer replace the source folder.")
    parser.add_argument("--dry-run", action="store_true", help="print commands only, write nothing")
    args = parser.parse_args(argv[1:])
    if not 0 <= args.image_quality <= 100:
        log("[ERROR] --image-quality must be between 0 and 100", file=sys.stderr)
        return 2
    if args.image_jobs < 1:
        log("[ERROR] --image-jobs must be at least 1", file=sys.stderr)
        return 2

    preset_name, container_ext = load_preset(CONFIG_PATH)
    paths = [Path(p).expanduser() for p in args.paths]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for path in missing:
            log(f"[ERROR] path not found: {path}", file=sys.stderr)
        return 1

    images, videos, passthrough = collect(paths, args.output)
    if args.only == "image":
        videos = []
    elif args.only == "video":
        images = []
        passthrough = []

    # 先算出真正需要哪些工具，再去解析它们；不处理的那一类连查找都不做。
    needed = (["caesium"] if images else []) + (["ffprobe", "handbrake"] if videos else [])
    found = tools(needed)
    absent = [name for name in needed if not found[name]]
    if absent:
        log(f"[ERROR] missing tool(s): {', '.join(absent)}"
              f" (set CAESIUM_CLT / HANDBRAKE_CLI / FFPROBE to override the path)",
              file=sys.stderr)
        return 1

    # 按媒体类型给出 (源, 输出)，并一次性滤掉已有输出与过长的路径。
    # COPY 一类永远不压缩，只在 --copy-unprocessed yes 时原样搬进输出目录。
    plan: list[tuple[str, list[tuple[Path, Path]]]] = []
    taken: dict[Path, Path] = {}              # 输出路径 -> 已占用它的源文件
    # 预过滤（已存在/撞名/路径过长）与阶段内跳过分开计数：前者不在 todo 里，
    # 混进 TOTAL 的 SKIP 会得出"共 1 个却跳过 8 个"这种自相矛盾的行。
    prefiltered = 0
    # 输出目录留下的缺口：走完全流程却没有对应文件。删源目录前必须为 0。
    gaps: list[tuple[str, str, Path]] = []    # (kind, 原因, 路径)
    # 图像输出扩展名由 --image-format 决定；original 时沿用源扩展名。
    # 这一步同时决定"已存在则跳过"的比对路径，格式换了才不会被误判成已完成。
    image_ext = FORMAT_EXTS[args.image_format]
    for kind, items, suffix in (("IMAGE", images, image_ext),
                                ("VIDEO", videos, container_ext),
                                ("COPY", passthrough, "")):
        pending: list[tuple[Path, Path]] = []
        for src, root, out_root in items:
            if len(str(src)) > MAX_PATH_LENGTH:
                log(f"[{kind}] [SKIP] path too long (>{MAX_PATH_LENGTH})  {src}")
                prefiltered += 1
                gaps.append((kind, "path too long", src))
                continue
            target = destination(src, root, out_root, suffix or src.suffix)
            if target in taken and taken[target] != src:
                log(f"[{kind}] [SKIP] output name taken by {taken[target]}  {target}")
                prefiltered += 1
                gaps.append((kind, "output name taken", target))
                continue
            if target.is_file() and target.stat().st_size > 0:
                log(f"[{kind}] [SKIP] output exists  {target}")
                prefiltered += 1
                continue
            taken[target] = src
            pending.append((src, target))
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

    # 单个待办文件的完整处理：返回 (tag, 源, 目标, 源大小, 压缩后大小, 结果词, 备注)，
    # 结果词取 OK / SKIP / COPY / FAIL / DRY。记账全部交给主线程的 report 做，
    # 所以并发时不需要给计数器加锁。
    def process(index: int, kind: str, src: Path, target: Path) -> tuple:
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
                log(f"    copy -> {target}", flush=True)
                return tag, src, target, size, 0, "DRY", ""
            failed_copy = deliver(kind, tag, src, target, size)
            return failed_copy or (tag, src, target, size, 0, "COPY",
                                   "unsupported format, copied as is")
        if kind == "IMAGE":
            tmp = temp_dir_for(target)
            if args.dry_run:
                command = [found["caesium"], "-q", str(args.image_quality),
                           "--keep-orientation", "--keep-dates", "-O", "all", "--json",
                           "-o", str(tmp)]
                if not args.image_strip_exif:
                    command.append("-e")
                if args.image_format != "original" \
                        and src.suffix.lower() != target.suffix.lower():
                    command += ["--format", args.image_format]
                log("    " + " ".join(command + [str(src)]), flush=True)
                return tag, src, target, size, 0, "DRY", ""
            try:
                tmp.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                # 临时目录建不出来，压缩没法进行；但输出目录仍要完整。
                gaps.append((kind, f"cannot create temp dir: {exc}", src))
                failed_copy = deliver(kind, tag, src, target, size)
                return failed_copy or (tag, src, target, size, 0, "COPY",
                                       "cannot create temp dir, copied as is")
            with tmp_lock:
                tmp_dirs.add(tmp)             # 登记后即使中断也会被清理
            new_size, reason = compress_image(found["caesium"], src, target,
                                              args.image_quality, args.image_format,
                                              args.image_strip_exif, False, tmp)
        else:
            new_size, reason = compress_video(found["handbrake"], found["ffprobe"], src,
                                              target, preset_name, args.dry_run)
            if reason == "dry_run":
                return tag, src, target, size, 0, "DRY", ""

        if not reason:                        # 压缩成功
            return tag, src, target, size, new_size, "OK", ""

        # 未产出可用结果。压缩出错时永远复制：删源目录前必须保证输出目录完整，
        # 否则会丢文件。故意跳过（省得不够 / 现代编码 / HDR）则听 --copy-unprocessed。
        if kind != "COPY" and reason not in INTENTIONAL_SKIPS and reason != "not_smaller":
            note = f"compression failed ({reason}), copied as is"
            failed_copy = deliver(kind, tag, src, target, size)
            return failed_copy or (tag, src, target, size, 0, "COPY", note)
        if reason == "not_smaller":
            note = "not worth compressing, copied as is"
        elif reason in INTENTIONAL_SKIPS:
            note = f"{reason}, copied as is"
        if args.copy_unprocessed == "no":
            gaps.append((kind, reason, src))
            return tag, src, target, size, 0, "SKIP", f"{reason} (not copied)"
        failed_copy = deliver(kind, tag, src, target, size)
        return failed_copy or (tag, src, target, size, 0, "COPY", note)

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
    tmp_dirs: set[Path] = set()
    tmp_lock = Lock()                         # 只保护 tmp_dirs 这一个共享集合
    # 进出总量按本次实际处理的文件算：被"已存在"过滤掉的不参与，合计才对得上。
    total_in = 0
    for _, pending in plan:
        for src, _target in pending:
            try:
                total_in += src.stat().st_size
            except OSError:
                pass
    try:
        for kind, pending in plan:
            if kind != "IMAGE" or args.image_jobs == 1:
                report([process(i, kind, src, target)
                        for i, (src, target) in enumerate(pending, 1)])
                continue
            # 图像之间并发；视频保持串行——HandBrake 的管线本身就吃 CPU，
            # 实测与图像并发只会互相拖慢（视频侧慢 1.8 倍）。
            with ThreadPoolExecutor(max_workers=args.image_jobs) as pool:
                futures = [pool.submit(process, i, kind, src, target)
                           for i, (src, target) in enumerate(pending, 1)]
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
            log(f"  [{kind}] {reason}  {path}", file=sys.stderr)
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
