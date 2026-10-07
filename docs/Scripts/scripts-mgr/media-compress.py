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
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SOURCE_DIR / "media-compress.json"
DEFAULT_OUTPUT_DIR = "_compressed"

IMAGE_EXTS = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi",
              ".wmv", ".flv", ".mpg", ".mpeg", ".ts", ".m2ts", ".3gp"}
# caesiumclt 1.5.0 读不了这些（实测报错），且本身已足够高效，直接跳过。
TOOL_UNSUPPORTED_EXTS = {".avif", ".heic", ".heif", ".jxl"}
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
                   strip_exif: bool, dry_run: bool,
                   made_tmp: set[Path]) -> tuple[int, str]:
    """压缩单张图像，成功返回 (压缩后字节数, "")；失败或省得不够返回 (0, 原因)。

    caesiumclt 的 `-e` 是"保留 EXIF"，所以 --image-strip-exif 是省掉该开关而
    不是加上某个开关。
    `--keep-orientation` 始终保留：只留方向标签，否则带 EXIF 旋转的照片会躺倒。

    目录在真正要压缩时才创建，并登记进 made_tmp 由调用方兜底清理——dry-run
    和"输出会覆盖源文件"这类提前跳过的路径因此不会留下任何东西。
    """
    tmp = temp_dir_for(target)
    command = [caesium, "-q", str(quality), "--keep-orientation", "--keep-dates",
               "-O", "all", "--json", "-o", str(tmp)]
    if not strip_exif:
        command.append("-e")
    if image_format != "original":
        command += ["--format", image_format]
    command.append(str(src))
    if dry_run:
        print("    " + " ".join(command))
        return 0, "dry_run"
    try:
        tmp.mkdir(parents=True, exist_ok=True)
        made_tmp.add(tmp)
    except OSError as exc:
        return 0, f"cannot create temp dir: {exc}"
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
        print("    " + " ".join(command))
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
    if path.name.lower() in JUNK_NAMES:
        return "junk"
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        return "skip" if suffix in TOOL_UNSUPPORTED_EXTS else "image"
    if suffix in VIDEO_EXTS:
        return "video"
    return "other"


Item = tuple[Path, Path, Path]               # (源文件, 输入根目录, 输出根目录)


def collect(paths: list[Path], output: str | None) -> tuple[list[Item], list[Item]]:
    """展开输入为 (图像列表, 视频列表)，过程不读取任何文件内容。

    每个输入各自决定输出根目录：显式 --output 时是所有输入共用的那一个，
    否则是该输入自己的 <目录>/_compressed/。
    """
    images: list[Item] = []
    videos: list[Item] = []
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
    return images, videos


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
    parser = argparse.ArgumentParser(
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
    parser.add_argument("--dry-run", action="store_true", help="print commands only, write nothing")
    args = parser.parse_args(argv[1:])
    if not 0 <= args.image_quality <= 100:
        print("[ERROR] --image-quality must be between 0 and 100", file=sys.stderr)
        return 2

    preset_name, container_ext = load_preset(CONFIG_PATH)
    paths = [Path(p).expanduser() for p in args.paths]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for path in missing:
            print(f"[ERROR] path not found: {path}", file=sys.stderr)
        return 1

    images, videos = collect(paths, args.output)
    if args.only == "image":
        videos = []
    elif args.only == "video":
        images = []

    # 先算出真正需要哪些工具，再去解析它们；不处理的那一类连查找都不做。
    needed = (["caesium"] if images else []) + (["ffprobe", "handbrake"] if videos else [])
    found = tools(needed)
    absent = [name for name in needed if not found[name]]
    if absent:
        print(f"[ERROR] missing tool(s): {', '.join(absent)}"
              f" (set CAESIUM_CLT / HANDBRAKE_CLI / FFPROBE to override the path)",
              file=sys.stderr)
        return 1

    # 按媒体类型给出 (源, 输出)，并一次性滤掉已有输出与过长的路径。
    # 下面三轮的 kind 一律用 IMAGE / VIDEO，和处理阶段保持一致，方便直接比对。
    plan: list[tuple[str, list[tuple[Path, Path]]]] = []
    taken: dict[Path, Path] = {}              # 输出路径 -> 已占用它的源文件
    skipped = 0
    # 图像输出扩展名由 --image-format 决定；original 时沿用源扩展名。
    # 这一步同时决定"已存在则跳过"的比对路径，格式换了才不会被误判成已完成。
    image_ext = FORMAT_EXTS[args.image_format]
    for kind, items, suffix in (("IMAGE", images, image_ext),
                                ("VIDEO", videos, container_ext)):
        pending: list[tuple[Path, Path]] = []
        for src, root, out_root in items:
            if len(str(src)) > MAX_PATH_LENGTH:
                print(f"[{kind}] [SKIP] path too long (>{MAX_PATH_LENGTH})  {src}")
                skipped += 1
                continue
            target = destination(src, root, out_root, suffix or src.suffix)
            if target in taken and taken[target] != src:
                print(f"[{kind}] [SKIP] output name taken by {taken[target]}  {target}")
                skipped += 1
                continue
            if target.is_file() and target.stat().st_size > 0:
                print(f"[{kind}] [SKIP] output exists  {target}")
                skipped += 1
                continue
            taken[target] = src
            pending.append((src, target))
        if pending:
            plan.append((kind, pending))

    todo = sum(len(pending) for _, pending in plan)
    if not todo:
        print("nothing to process.")
        return 0

    print(f"IMAGE {len(images)} / VIDEO {len(videos)}"
          f"  (preset {preset_name}, container {container_ext})"
          + ("  [dry-run]" if args.dry_run else ""))

    done = failed = copied = 0
    saved = 0
    index = 0
    width = len(str(todo))                    # 序号右对齐，位数跟着总数走
    tmp_dirs: set[Path] = set()
    try:
        for kind, pending in plan:
            for src, target in pending:
                index += 1
                tag = f"[{index:>{width}}/{todo}] [{kind}]"
                if src.resolve() == target.resolve():
                    print(f"{tag} [SKIP] output would overwrite the source  {src}")
                    skipped += 1
                    continue
                size = src.stat().st_size
                print(f"{tag} {src}")
                if kind == "IMAGE":
                    new_size, reason = compress_image(found["caesium"], src, target,
                                                      args.image_quality, args.image_format,
                                                      args.image_strip_exif, args.dry_run,
                                                      tmp_dirs)
                else:
                    new_size, reason = compress_video(found["handbrake"], found["ffprobe"], src,
                                                      target, preset_name, args.dry_run)
                if reason == "dry_run":
                    continue
                if reason:
                    if reason in INTENTIONAL_SKIPS:
                        print(f"{tag} [SKIP] {reason}  {src}")
                        skipped += 1
                        continue
                    if reason == "not_smaller":
                        skipped += 1
                        # 图像原样复制到目的地，保证输出目录图像齐全、不缺图。
                        if kind == "IMAGE":
                            try:
                                target.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src, target)
                                copied += 1
                                print(f"{tag} [COPY] not worth compressing, copied as is  "
                                      f"{target}")
                            except OSError as exc:
                                print(f"{tag} [FAIL] copy  {exc}  {src}")
                                failed += 1
                        else:
                            print(f"{tag} [SKIP] not enough savings, source kept  {src}")
                    else:
                        print(f"{tag} [FAIL] {reason}  {src}")
                        failed += 1
                    continue
                saved += max(0, size - new_size)
                done += 1
                print(f"{tag} [OK] -{100 * (size - new_size) / size:.0f}%  "
                      f"{human(size)} -> {human(new_size)}  {target}")
    finally:
        for tmp in tmp_dirs:                      # 哪怕 Ctrl+C 也不留临时目录
            shutil.rmtree(tmp, ignore_errors=True)

    if args.dry_run:
        print(f"TOTAL {todo}  dry-run only, nothing written")
        return 0
    print(f"TOTAL {todo}  OK {done}  SKIP {skipped}  COPY {copied}  FAIL {failed}  "
          f"saved {human(saved)}")
    return 1 if failed else 0


if __name__ == "__main__":
    setup_console()
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print("\ninterrupted.", file=sys.stderr)
        sys.exit(130)
