#!/usr/bin/env python3
"""Compress oversized images and videos inside a folder of downloaded resources.

Usage:
    files-compress.py <input-dir> [-o <output-dir>] [--dry-run]
    files-compress.py <input-dir> --in-place [--keep-originals] [--dry-run]
    files-compress.py <input-dir> --audit
    files-compress.py <input-dir> --only image|video

The input directory is scanned recursively, every file is classified as image,
video, archive or unsupported, and images and videos are probed with ffprobe so
a per-file decision can be derived from hardcoded rules: a resolution cap first,
the byte threshold second, then codec/HDR/animation gates.  Only files that pass
are encoded -- images with caesiumclt (https://github.com/Lymphatus/caesium-clt),
videos with ffmpeg.

``--only`` narrows the run to one media kind before anything else happens: files
of the other kind are not scanned, not probed, not encoded and not reported, so
the ledger, the reports and the audit all describe exactly the requested subset.

Two modes:

* copy-out (default): results go to a separate directory that mirrors the input
  tree, originals are never touched, and an existing output marks a file done.
* in-place (``--in-place``): the encoded file atomically replaces the original
  (same-volume temp file, then ReplaceFileW/os.replace), and only after the temp
  file was verified and saves enough space to be worth the change.
  ``--keep-originals`` mirrors originals into ``_originals/`` first, which makes
  a run reversible.

Both modes keep a ledger (JSONL) of every decision next to the reports, so a
re-run does no work: files that were replaced, that could not be compressed
(not_smaller, already efficient, HDR, animated, ...) or that are below their
threshold are skipped without probing or encoding them again.

An encoded file that is not meaningfully smaller is always discarded and the
original kept, in both modes.  Requires ffmpeg, ffprobe and caesiumclt in PATH.
Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat as stat_module
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

__version__ = "0.8.0"

# ------------------------------ detection ------------------------------

IMAGE_EXTS = {
    ".jpg", ".jpeg", ".jfif", ".png", ".webp", ".gif",
    ".bmp", ".tif", ".tiff", ".avif", ".heic", ".heif",
}

VIDEO_EXTS = {
    ".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi",
    ".wmv", ".flv", ".mpg", ".mpeg", ".ts", ".m2ts", ".3gp",
}

# Longest suffixes first, so ".tar.gz" wins over ".gz".
ARCHIVE_EXTS = (
    ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz2", ".txz",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".zst",
)

# OS/editor junk; must never reach the reports as "unsupported".
JUNK_FILES = {
    ".ds_store", "thumbs.db", "ehthumbs.db", "desktop.ini",
    ".localized", "icon\r", ".spotlight-v100", ".trashes",
}

# Suffixes used by download managers while a file is still incomplete.
IN_PROGRESS_SUFFIXES = (".part", ".crdownload", ".!ut", ".aria2", ".partial", ".download")

# caesiumclt 1.5.0 cannot read these (verified: exit -1, "Unable to compute the
# base path for the files."); they are already efficient anyway, so skipping them
# is both safer and more useful than one failure per file.
TOOL_UNSUPPORTED_EXTS = {".avif", ".heic", ".heif", ".jxl"}

# Magic bytes for extension-less downloads (imghdr was removed in Python 3.13).
MAGIC_SIGNATURES = (
    (b"\xff\xd8\xff", "image"),
    (b"\x89PNG\r\n\x1a\n", "image"),
    (b"GIF87a", "image"),
    (b"GIF89a", "image"),
    (b"BM", "image"),
    (b"II*\x00", "image"),
    (b"MM\x00*", "image"),
    (b"\x1aE\xdf\xa3", "video"),           # Matroska / WebM
    (b"FLV\x01", "video"),
    (b"0&\xb2u", "video"),                 # ASF / WMV
)

# ------------------------------ thresholds ------------------------------
# Hardcoded rules, intentionally not exposed as CLI options: edit them here.
# RULES_VERSION invalidates every ledger entry whenever any of them changes.

RULES_VERSION = 2

# Images: allowed bytes per pixel, by container format.
IMAGE_BYTES_PER_PIXEL = {
    ".png": 0.65, ".bmp": 0.90, ".tif": 0.80, ".tiff": 0.80, ".gif": 0.35,
    ".jpg": 0.28, ".jpeg": 0.28, ".jfif": 0.28, ".webp": 0.20,
    ".heic": 0.22, ".heif": 0.22, ".avif": 0.15,
}
IMAGE_DEFAULT_BYTES_PER_PIXEL = 0.50

# Halving the pixel count saves ~50% before the encoder is involved, so the
# resolution cap is evaluated first and applies even to a file that is already
# below its byte threshold.  Rescaling for a <5% gain is never worth it.
IMAGE_DOWNSCALE_TOLERANCE = 1.05
VIDEO_DOWNSCALE_TOLERANCE = 1.05

# Videos: allowed bitrate (kbit/s) per vertical resolution tier.
VIDEO_KBPS_TIERS = (
    (240, 400), (360, 800), (480, 1400), (720, 2800),
    (1080, 5500), (1440, 9000), (2160, 18000),
)

# Already-efficient codecs: re-encoding them with x264 is usually a downgrade.
MODERN_VIDEO_CODECS = {"hevc", "h265", "av1", "vp9", "vp8"}

# HDR must not be fed to a plain x264 pass, it comes out washed out.
HDR_COLOR_TRANSFERS = {"smpte2084", "arib-std-b67"}

# Operational guards.
IN_PROGRESS_MTIME_SECONDS = 300
MAX_PATH_LENGTH = 240
PROBE_TIMEOUT = 60
FREE_SPACE_MARGIN = 64 * 1024 * 1024
# There is deliberately no total time limit for encoding.  Any limit derived from
# the video duration assumes an encoding speed, so it fails valid work on slower
# machines and on longer videos (measured: 0.7x realtime for x264 medium on easy
# 1080p content, 2.8x on hard content - a 15 minute file needed 25+ minutes while
# the old formula allowed 4).  ffmpeg reports progress continuously instead, so a
# *stall* detector is used: it only fires when nothing is happening at all.
STALL_TIMEOUT_SECONDS = 600             # seconds without any progress; 0 disables it
PROGRESS_LOG_SECONDS = 60               # run.log heartbeat while encoding
PROGRESS_TTY_SECONDS = 15               # console heartbeat on a TTY
REPLACE_RETRIES = 3
REPLACE_RETRY_DELAY = 0.5
HASH_CHUNK = 64 * 1024

# Hardware decode: decode the input on the GPU, keep encoding on the CPU.  This
# is a pure speed optimisation - measured byte-identical output on an Intel Iris
# Xe - so it carries no quality risk, unlike hardware *encoding*.  `-hwaccel qsv`
# fails into a CPU pipeline on this machine, hence d3d11va on Windows; other
# platforms let ffmpeg pick.  Every attempt falls back to software decoding.
HWACCEL_DECODE = "d3d11va" if os.name == "nt" else "auto"

# Hardware encoding (opt-in, --encoder).  QSV exposes no working quality mode on
# this machine - `-global_quality`/`-q:v` are ignored and `-look_ahead` fails -
# so it is driven by a bitrate target instead, and the result is measured against
# the same saving gate as always.  It is faster but less efficient per byte than
# x264, which is why it is not the default.
ENCODERS = ("x264", "qsv", "qsv-hevc")
ENCODER_CODECS = {"x264": "libx264", "qsv": "h264_qsv", "qsv-hevc": "hevc_qsv"}
QSV_MAX_SOURCE_RATIO = 0.80             # never ask for more than 80% of the source bitrate
QSV_MIN_BITRATE_KBPS = 150              # ... nor for something unusably small
# A hardware path that fails on one file is usually that file's fault, not the
# machine's: allow this many failures before switching the rest of the run to
# software, instead of giving up on the whole batch after the first one.
HARDWARE_MAX_FAILURES = 3

# ------------------------------ profiles ------------------------------
# Three fixed strengths, selected with --profile.  `balanced` is byte-for-byte
# the behaviour of the pre-profile script, so the default changes nothing.
#
# A profile only scales the quality/size trade-off (how wide the entry gate is,
# how hard the encoder is pushed, how much saving justifies touching a file).
# Safety and capability gates - HDR, animated images, AVIF/HEIC, bitmap
# subtitles, container compatibility - apply to every profile, because
# "as small as possible" never means "allowed to lose content or break playback".


@dataclass(frozen=True)
class Profile:
    name: str
    threshold_factor: float             # multiplies every entry threshold
    image_min_bytes: int                # never compress a smaller image
    image_max_bytes: int                # always compress a bigger one
    image_max_long_edge: int            # resolution cap: the biggest lever
    image_quality: int                  # -q for an over-threshold image
    image_scale_quality: int            # -q when only the resolution is at fault
    image_modern_quality: int           # -q for already-modern containers
    png_opt_level: int
    zopfli: bool
    jpeg_chroma: str
    video_min_bytes: int
    video_max_bytes: int
    video_max_height: int
    video_crf: int
    video_preset: str
    video_audio_bitrate: str
    modern_codec_factor: float          # skip modern codecs below tier x factor
    min_savings_ratio: float            # a replacement must save this much ...
    min_savings_bytes: int              # ... or this many bytes
    timeout_per_second: float           # legacy, no longer used for timeouts; kept
                                        # because it is part of the policy fingerprint


PROFILES = {
    "balanced": Profile(
        name="balanced", threshold_factor=1.0,
        image_min_bytes=200 * 1024, image_max_bytes=12 * 1024 * 1024,
        image_max_long_edge=4096,
        image_quality=82, image_scale_quality=95, image_modern_quality=100,
        png_opt_level=3, zopfli=False, jpeg_chroma="auto",
        video_min_bytes=2 * 1024 * 1024, video_max_bytes=8 * 1024 * 1024 * 1024,
        video_max_height=1440, video_crf=23, video_preset="medium",
        video_audio_bitrate="128k", modern_codec_factor=1.2,
        min_savings_ratio=0.05, min_savings_bytes=64 * 1024,
        timeout_per_second=0.25,
    ),
    "small": Profile(
        name="small", threshold_factor=0.7,
        image_min_bytes=128 * 1024, image_max_bytes=12 * 1024 * 1024,
        image_max_long_edge=2560,
        image_quality=72, image_scale_quality=85, image_modern_quality=90,
        png_opt_level=6, zopfli=False, jpeg_chroma="auto",
        video_min_bytes=1 * 1024 * 1024, video_max_bytes=8 * 1024 * 1024 * 1024,
        video_max_height=1080, video_crf=26, video_preset="medium",
        video_audio_bitrate="112k", modern_codec_factor=1.5,
        min_savings_ratio=0.03, min_savings_bytes=32 * 1024,
        timeout_per_second=0.25,
    ),
    "tiny": Profile(
        name="tiny", threshold_factor=0.4,
        image_min_bytes=64 * 1024, image_max_bytes=12 * 1024 * 1024,
        image_max_long_edge=1920,
        image_quality=58, image_scale_quality=65, image_modern_quality=70,
        png_opt_level=6, zopfli=True, jpeg_chroma="4:2:0",
        video_min_bytes=512 * 1024, video_max_bytes=8 * 1024 * 1024 * 1024,
        video_max_height=720, video_crf=30, video_preset="slow",
        video_audio_bitrate="96k", modern_codec_factor=3.0,
        min_savings_ratio=0.02, min_savings_bytes=16 * 1024,
        timeout_per_second=0.5,          # -preset slow needs a longer leash
    ),
}
DEFAULT_PROFILE = "balanced"


def policy_fingerprint(profile: Profile, encoder: str) -> str:
    """Short hash of the effective policy, stored on `no_change` ledger entries.

    The encoder is part of it because it changes the outcome: a file judged "not
    worth compressing" under x264 deserves a fresh look under QSV.  Hardware
    *decode* is deliberately excluded, since it is byte-identical.

    A file that was skipped under one policy is safe to re-evaluate because
    nothing was written; a file that was replaced is terminal either way.
    """
    payload = json.dumps({"profile": asdict(profile), "encoder": encoder}, sort_keys=True)
    return hashlib.blake2b(payload.encode("utf-8"), digest_size=8).hexdigest()


# Entries written before profiles and encoders existed came from the balanced
# knobs and libx264, so they stay valid for exactly that combination.
LEGACY_POLICY = policy_fingerprint(PROFILES[DEFAULT_PROFILE], "x264")

# ------------------------------ encoders ------------------------------

MODERN_IMAGE_EXTS = {".webp", ".jxl"}
VIDEO_OUTPUT_EXT = ".mp4"               # copy-out container
MP4_SAFE_AUDIO_CODECS = {"aac", "mp3", "ac3", "eac3", "alac"}
TEXT_SUBTITLE_CODECS = {"subrip", "ass", "ssa", "mov_text", "webvtt", "text"}
# Containers an H.264/AAC re-encode can be muxed into under the original name.
# Anything else keeps its name only in copy-out mode, as a ".mp4" sibling.
INPLACE_VIDEO_SUFFIXES = {".mp4", ".m4v", ".mov", ".3gp", ".mkv", ".avi", ".flv", ".ts", ".m2ts"}
# Only these muxers understand -movflags.
MP4_FAMILY_SUFFIXES = {".mp4", ".m4v", ".mov", ".3gp"}

# ------------------------------ layout ------------------------------

OUTPUT_DIR_NAME = "_compressed"
ORIGINALS_DIR_NAME = "_originals"
STATE_DIR_NAME = ".compress-state"
TEMP_DIR_NAME = ".compress-tmp"
LEDGER_NAME = "state.jsonl"
LOCK_NAME = "state.lock"
LOCK_STALE_SECONDS = 6 * 3600
ARTIFACT_DIR_NAMES = {OUTPUT_DIR_NAME, ORIGINALS_DIR_NAME, STATE_DIR_NAME, TEMP_DIR_NAME}

TOOLS = ("ffmpeg", "ffprobe", "caesiumclt")
REQUIRED_ENCODERS = ("libx264", "aac")

# Every skip/failure reason that can appear in a report or a ledger entry.
REASONS = (
    "junk", "in_progress", "cloud_placeholder", "too_long_path", "duplicate_inode",
    "empty", "archive", "unsupported", "unsupported_by_tool", "container_incompatible",
    "animated", "hdr", "modern_codec", "below_threshold", "already_processed",
    "already_compressed", "not_smaller", "no_size_gain", "changed_during_run", "locked",
    "failed_probe", "failed_encode", "failed_verify", "timeout", "no_disk_space", "interrupted",
)
RETRYABLE_REASONS = {"failed_encode", "failed_verify", "timeout", "no_disk_space", "locked"}
# Gates that are transient by nature and must never enter the ledger.
NEVER_LEDGER_REASONS = {"in_progress", "cloud_placeholder", "duplicate_inode", "locked"}

FILE_ATTRIBUTE_READONLY = getattr(stat_module, "FILE_ATTRIBUTE_READONLY", 0x1)
FILE_ATTRIBUTE_OFFLINE = getattr(stat_module, "FILE_ATTRIBUTE_OFFLINE", 0x1000)
FILE_ATTRIBUTE_RECALL_ON_OPEN = getattr(stat_module, "FILE_ATTRIBUTE_RECALL_ON_OPEN", 0x40000)
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x400000
CLOUD_ATTRIBUTES = (FILE_ATTRIBUTE_OFFLINE | FILE_ATTRIBUTE_RECALL_ON_OPEN
                    | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS)


# ------------------------------ helpers ------------------------------

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def setup_console() -> None:
    """Use UTF-8 on the console.

    Two separate problems make this necessary on a non-English Windows: tools are
    captured as UTF-8 (see the `encoding="utf-8", errors="replace"` on every
    subprocess call) while the console defaults to the ANSI code page, and printing
    a path that the code page cannot represent would otherwise raise
    UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")        # type: ignore[attr-defined]
        except (AttributeError, OSError, ValueError):
            pass


def human(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size) < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def last_line(result: subprocess.CompletedProcess) -> str:
    lines = (result.stderr or result.stdout or "").strip().splitlines()
    return lines[-1][:300] if lines else ""


def head_tail_hash(path: Path) -> str:
    """Cheap content fingerprint: first and last 64 KiB (audit/debug only)."""
    digest = hashlib.blake2b(digest_size=16)
    size = path.stat().st_size
    with path.open("rb") as handle:
        digest.update(handle.read(HASH_CHUNK))
        if size > HASH_CHUNK:
            handle.seek(max(0, size - HASH_CHUNK))
            digest.update(handle.read(HASH_CHUNK))
    return digest.hexdigest()


def safe_hash(path: Path) -> str:
    try:
        return head_tail_hash(path)
    except OSError:
        return ""


def is_meaningful_saving(size_before: int, size_after: int, profile: Profile) -> bool:
    """A replacement must be clearly smaller for the active profile: over the
    profile's ratio or its byte floor, and smaller at all."""
    if size_after <= 0 or size_after >= size_before:
        return False
    if size_before - size_after >= profile.min_savings_bytes:
        return True
    return size_after <= size_before * (1 - profile.min_savings_ratio)


def magic_kind(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
    except OSError:
        return None
    for signature, kind in MAGIC_SIGNATURES:
        if head.startswith(signature):
            return kind
    if head[:4] == b"RIFF" and head[8:12] in (b"WEBP", b"AVI "):
        return "image" if head[8:12] == b"WEBP" else "video"
    if head[4:8] == b"ftyp" and len(head) >= 12:
        return "image" if head[8:12] in (b"avif", b"heic", b"heix", b"mif1") else "video"
    return None


def classify(path: Path) -> str:
    """Return "image", "video", "archive" or "unsupported"."""
    name = path.name.lower()
    if name.endswith(ARCHIVE_EXTS):
        return "archive"
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        return "image"
    if suffix in VIDEO_EXTS:
        return "video"
    return magic_kind(path) or "unsupported"


# ------------------------------ probing ------------------------------

PROBE_ENTRIES = (
    "stream=index,codec_type,codec_name,width,height,nb_frames,pix_fmt,color_transfer,bit_rate",
    "format=duration,bit_rate,format_name",
)


@dataclass
class MediaInfo:
    kind: str = ""
    width: int = 0
    height: int = 0
    duration: float = 0.0
    codec: str = ""
    pix_fmt: str = ""
    color_transfer: str = ""
    nb_frames: int = 0
    bit_rate: int = 0
    format_name: str = ""
    audio_codecs: list[str] = field(default_factory=list)
    text_subtitle_indices: list[int] = field(default_factory=list)
    bitmap_subtitles: int = 0
    chapters: int = 0

    @property
    def long_edge(self) -> int:
        return max(self.width, self.height)

    @property
    def animated(self) -> bool:
        name = f"{self.format_name},{self.codec}".lower()
        if "webp_anim" in name or "apng" in name:
            return True
        return self.codec == "gif" and self.nb_frames > 1

    @property
    def hdr(self) -> bool:
        return self.color_transfer.lower() in HDR_COLOR_TRANSFERS


def probe(path: Path) -> MediaInfo:
    """Read geometry and stream metadata with ffprobe; raises RuntimeError on failure."""
    cmd = ["ffprobe", "-v", "error"]
    for entry in PROBE_ENTRIES:
        cmd += ["-show_entries", entry]
    cmd += ["-show_chapters", "-of", "json", str(path)]
    try:
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                                timeout=PROBE_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise RuntimeError("ffprobe timed out") from None
    except OSError as exc:
        raise RuntimeError(str(exc)) from None
    if result.returncode != 0:
        raise RuntimeError(last_line(result) or f"ffprobe exit {result.returncode}")
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"unreadable ffprobe output: {exc}") from None

    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    subtitles = [s for s in streams if s.get("codec_type") == "subtitle"]
    if video is None and not audio:
        raise RuntimeError("no audio/video stream found")

    info = MediaInfo(
        width=int(video.get("width") or 0) if video else 0,
        height=int(video.get("height") or 0) if video else 0,
        duration=float(fmt.get("duration") or 0.0),
        codec=str((video or {}).get("codec_name") or ""),
        pix_fmt=str((video or {}).get("pix_fmt") or ""),
        color_transfer=str((video or {}).get("color_transfer") or ""),
        nb_frames=int(str((video or {}).get("nb_frames") or 0) or 0),
        bit_rate=int(str(fmt.get("bit_rate") or (video or {}).get("bit_rate") or 0) or 0),
        format_name=str(fmt.get("format_name") or ""),
        audio_codecs=[str(s.get("codec_name") or "") for s in audio],
        bitmap_subtitles=sum(1 for s in subtitles if str(s.get("codec_name")) not in TEXT_SUBTITLE_CODECS),
        chapters=len(data.get("chapters") or []),
    )
    info.text_subtitle_indices = [int(s["index"]) for s in subtitles
                                  if str(s.get("codec_name")) in TEXT_SUBTITLE_CODECS and "index" in s]
    if info.width <= 0 or info.height <= 0:
        raise RuntimeError("ffprobe reported no resolution")
    return info


# ------------------------------ policy ------------------------------

@dataclass
class Decision:
    action: str                     # "encode" | "skip"
    reason: str = ""
    quality: int = 82
    long_edge: int | None = None
    target_height: int | None = None
    threshold: int = 0

    @property
    def scaled(self) -> bool:
        return self.long_edge is not None or self.target_height is not None


def image_threshold(path: Path, width: int, height: int, profile: Profile) -> int:
    per_pixel = IMAGE_BYTES_PER_PIXEL.get(path.suffix.lower(), IMAGE_DEFAULT_BYTES_PER_PIXEL)
    allowed = int(width * height * per_pixel * profile.threshold_factor)
    return clamp(allowed, profile.image_min_bytes, profile.image_max_bytes)


def tier_kbps(height: int) -> int:
    for tier_height, kbps in VIDEO_KBPS_TIERS:
        if height <= tier_height:
            return kbps
    return VIDEO_KBPS_TIERS[-1][1]


def video_threshold(width: int, height: int, duration: float, profile: Profile) -> int:
    seconds = duration if duration > 0 else 1.0
    allowed = int(seconds * tier_kbps(height) * 1000 / 8 * profile.threshold_factor)
    return clamp(allowed, profile.video_min_bytes, profile.video_max_bytes)


def decide_image(path: Path, info: MediaInfo, size: int, profile: Profile) -> Decision:
    suffix = path.suffix.lower()
    if info.animated:
        return Decision("skip", "animated")
    if suffix in TOOL_UNSUPPORTED_EXTS:
        return Decision("skip", "unsupported_by_tool")

    threshold = image_threshold(path, info.width, info.height, profile)
    over_threshold = size > threshold
    oversized = info.long_edge > profile.image_max_long_edge * IMAGE_DOWNSCALE_TOLERANCE
    if not over_threshold and not oversized:
        return Decision("skip", "below_threshold", threshold=threshold)

    if suffix in MODERN_IMAGE_EXTS:
        quality = profile.image_modern_quality
    elif over_threshold:
        quality = profile.image_quality
    else:
        quality = profile.image_scale_quality   # only the resolution is at fault
    return Decision("encode", quality=quality, threshold=threshold,
                    long_edge=profile.image_max_long_edge if oversized else None)


def decide_video(path: Path, info: MediaInfo, size: int, in_place: bool,
                 profile: Profile) -> Decision:
    if info.hdr:
        return Decision("skip", "hdr")
    if in_place and path.suffix.lower() not in INPLACE_VIDEO_SUFFIXES:
        return Decision("skip", "container_incompatible")
    if info.codec in MODERN_VIDEO_CODECS:
        kbps = info.bit_rate / 1000 if info.bit_rate else 0.0
        if kbps and kbps <= tier_kbps(info.height) * profile.modern_codec_factor:
            return Decision("skip", "modern_codec")

    threshold = video_threshold(info.width, info.height, info.duration, profile)
    over_threshold = size > threshold
    oversized = info.height > profile.video_max_height * VIDEO_DOWNSCALE_TOLERANCE
    if not over_threshold and not oversized:
        return Decision("skip", "below_threshold", threshold=threshold)
    return Decision("encode", threshold=threshold,
                    target_height=profile.video_max_height if oversized else None)


# ------------------------------ tool calls ------------------------------

class ToolError(RuntimeError):
    """A compression tool failed; the message is user-facing."""


class ToolStalled(ToolError):
    """A tool stopped making progress and was killed by the watchdog."""


# Characters that need no quoting when a command line is written to the log.
SAFE_ARG_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                     "_@%+=:,./-\\")


def quote_arg(part: str) -> str:
    if part and all(char in SAFE_ARG_CHARS for char in part):
        return part
    return '"' + part.replace('"', '\\"') + '"'


def format_command(command: list[str]) -> str:
    """Render a command line so the log entry can be pasted into a shell."""
    return " ".join(quote_arg(part) for part in command)


class ProgressReader(threading.Thread):
    """Reads ffmpeg's `-progress` stream: liveness, position, heartbeat logging.

    `self.owner`/`self.progress` are deliberately not called `run`/`state`:
    `Thread.run` would be shadowed by an attribute of that name and the thread
    would then die with "not callable" without anyone noticing.
    """

    def __init__(self, stream, owner: "Run", label: str) -> None:
        super().__init__(daemon=True)
        self.stream = stream
        self.owner = owner
        self.label = label
        self.last = time.monotonic()
        self.progress: dict[str, str] = {}
        self.lines: list[str] = []
        self.error = ""
        self._logged = time.monotonic()
        self._printed = time.monotonic()

    def run(self) -> None:
        try:
            for raw in self.stream:
                self.last = time.monotonic()
                line = raw.strip()
                if not line:
                    continue
                self.lines.append(line)
                key, _, value = line.partition("=")
                if key in ("frame", "fps", "out_time_ms", "speed", "progress"):
                    self.progress[key] = value
                self._heartbeat()
        except Exception as exc:            # a watchdog thread must not die silently
            self.error = str(exc)

    def _heartbeat(self) -> None:
        now = time.monotonic()
        if now - self._logged >= PROGRESS_LOG_SECONDS:
            self._logged = now
            self.owner.log.log(f"进度 {self.label} {self.describe()}")
        if sys.stdout.isatty() and now - self._printed >= PROGRESS_TTY_SECONDS:
            self._printed = now
            print(f"  ... {self.label} {self.describe()}", flush=True)

    def describe(self) -> str:
        parts: list[str] = []
        position = self.progress.get("out_time_ms", "")
        if position.isdigit():
            parts.append(f"已编码 {int(position) / 1_000_000:.0f}s")
        if self.progress.get("speed"):
            parts.append(f"速度 {self.progress['speed']}")
        if self.progress.get("frame"):
            parts.append(f"帧 {self.progress['frame']}")
        return " ".join(parts)

    def stalled_for(self) -> float:
        return time.monotonic() - self.last

    def watching(self) -> bool:
        """True while the reader can still tell "working" from "stuck"."""
        return self.is_alive()


def exec_tool(run: "Run", command: list[str], label: str) -> None:
    """Run a helper that has no progress output (caesiumclt).

    No time limit: the work is bounded by the source image itself (measured:
    2.6 s for a 70 Mpx source at `tiny` settings, 4.5 s at `balanced`), so a
    limit here could only ever be a false failure.
    """
    run.log.log("exec " + format_command(command))
    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ToolError(str(exc)) from None
    elapsed = time.monotonic() - started
    if result.stdout.strip():
        run.log.log("工具输出：" + " | ".join(result.stdout.strip().splitlines())[:500])
    if result.returncode != 0:
        raise ToolError(error_summary(
            (result.stderr or result.stdout or "").splitlines()) or f"exit {result.returncode}")
    run.log.log(f"完成 {label} 用时 {elapsed:.1f}s")


def exec_ffmpeg(run: "Run", command: list[str], label: str) -> None:
    """Run ffmpeg under a stall watchdog instead of a total time limit.

    A slow machine, a long video or an expensive preset therefore never fails;
    only a genuine hang (no progress at all for `run.stall_timeout` seconds) is
    aborted, and that is reported as a retryable failure.
    """
    run.log.log("exec " + format_command(command))
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               encoding="utf-8", errors="replace")
    reader = ProgressReader(process.stdout, run, label)
    reader.start()
    errors: list[str] = []

    def drain() -> None:
        if process.stderr is not None:
            for line in process.stderr:
                line = line.strip()
                if line:
                    errors.append(line)

    drainer = threading.Thread(target=drain, daemon=True)
    drainer.start()

    killed = False
    while process.poll() is None:
        if (run.stall_timeout and reader.watching()
                and reader.stalled_for() > run.stall_timeout):
            killed = True
            process.kill()
            break
        time.sleep(0.5)
    process.wait()
    reader.join(timeout=5)
    drainer.join(timeout=5)
    elapsed = time.monotonic() - started

    if killed:
        raise ToolStalled(
            f"连续 {run.stall_timeout} 秒无进度输出，已中止（用时 {elapsed:.0f}s，未产生输出）"
            + (f"；最后 {reader.describe()}" if reader.progress else ""))
    if process.returncode != 0:
        raise ToolError(error_summary(errors) or f"exit {process.returncode}")
    note = reader.describe() or "无进度信息"
    if reader.error:
        note += f"；进度读取异常 {reader.error}"
    run.log.log(f"完成 {label} 用时 {elapsed:.1f}s（{note}）")


def qsv_target_kbps(info: MediaInfo, decision: Decision, profile: Profile, size: int) -> int:
    """Bitrate to ask a hardware encoder for.

    QSV cannot be told a quality here, so the target is the profile's acceptable
    bitrate for the *output* resolution, capped at 80% of the source's own
    bitrate so that a replacement is always a real win by construction.
    """
    height = decision.target_height or info.height
    policy_kbps = tier_kbps(height) * profile.threshold_factor
    seconds = info.duration if info.duration > 0 else 1.0
    source_kbps = size * 8 / seconds / 1000
    return int(max(QSV_MIN_BITRATE_KBPS, min(policy_kbps, source_kbps * QSV_MAX_SOURCE_RATIO)))


def first_error_line(result: subprocess.CompletedProcess) -> str:
    """The *cause* of a failed probe.

    ffmpeg reports the reason first and then a cascade of consequences, so the
    last line is usually the useless one ("Nothing was written into output
    file" instead of "Impossible to convert between the formats ...").
    """
    lines = [line.strip() for line in (result.stderr or result.stdout or "").splitlines()
             if line.strip()]
    return lines[0][:200] if lines else f"exit {result.returncode}"


def error_summary(lines: list[str], limit: int = 300) -> str:
    """Cause first, verdict last: both ends of a tool's error output matter."""
    cleaned = [line.strip() for line in lines if line.strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0][:limit]
    return f"{cleaned[0]} | … | {cleaned[-1]}"[:limit]


def make_probe_sample(state_dir: Path) -> Path:
    """A tiny H.264 clip: ffmpeg only uses a hardware *decoder* on a real stream."""
    sample = state_dir / "probe-sample.mp4"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
         "-i", "testsrc2=size=320x240:rate=5", "-t", "1", "-c:v", "libx264",
         "-crf", "30", str(sample)],
        capture_output=True, encoding="utf-8", errors="replace", timeout=PROBE_TIMEOUT)
    return sample


def probe_hwdec(name: str, sample: Path, log: "Logger") -> tuple[bool, str]:
    """Can `-hwaccel name` decode into our CPU filter pipeline?"""
    if not name or not sample.exists():
        return False, "没有可用的探测样例"
    try:
        tested = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-hwaccel", name,
             "-i", str(sample), "-vf", "scale=-2:120", "-c:v", "libx264",
             "-crf", "30", "-f", "null", "-"],
            capture_output=True, encoding="utf-8", errors="replace", timeout=PROBE_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if tested.returncode == 0:
        return True, ""
    return False, first_error_line(tested)


def probe_encoder(encoder: str, state_dir: Path, log: "Logger") -> tuple[bool, str]:
    """Can this encoder produce a file here?  Returns (ok, reason-if-not)."""
    if encoder == "x264":
        return True, ""
    sample = state_dir / "encoder-probe.mp4"
    ok, reason = False, ""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
             "-i", "testsrc2=size=320x240:rate=5", "-t", "1",
             "-c:v", ENCODER_CODECS[encoder], "-b:v", "300k", "-pix_fmt", "nv12", str(sample)],
            capture_output=True, encoding="utf-8", errors="replace", timeout=PROBE_TIMEOUT)
        ok = result.returncode == 0 and sample.exists() and sample.stat().st_size > 0
        if not ok:
            reason = first_error_line(result)
    except (OSError, subprocess.TimeoutExpired) as exc:
        reason = str(exc)
    finally:
        try:
            sample.unlink()
        except OSError:
            pass
    log.log(f"编码器探针 encoder={encoder}（{ENCODER_CODECS[encoder]}）ok={ok}"
            + (f"（原因：{reason}）" if reason else ""))
    return ok, reason


def probe_hardware(state_dir: Path, log: "Logger") -> dict[str, bool]:
    """Probe every hardware path once and report them on a single log line.

    The point is diagnosability: when something silently falls back to software,
    the log has to say which path failed and why.  Costs about two seconds.
    """
    results: dict[str, bool] = {}
    notes: list[str] = []
    sample = make_probe_sample(state_dir)
    try:
        decoders = [HWACCEL_DECODE] + (["qsv"] if HWACCEL_DECODE != "qsv" else [])
        for name in decoders:
            ok, reason = probe_hwdec(name, sample, log)
            results[name] = ok
            if not ok:
                notes.append(f"{name}: {reason}")
    finally:
        try:
            sample.unlink()
        except OSError:
            pass
    for encoder in ("qsv", "qsv-hevc"):
        ok, reason = probe_encoder(encoder, state_dir, log)
        results[f"encoder_{encoder}"] = ok
        if not ok:
            notes.append(f"encoder_{encoder}: {reason}")
    log.log("硬件探针 " + " ".join(f"{key}={value}" for key, value in results.items()))
    for note in notes:
        log.log(f"硬件探针原因 {note}")
    return results


def image_command(src: Path, out_dir: Path, decision: Decision, profile: Profile) -> list[str]:
    cmd = [
        "caesiumclt", "-q", str(decision.quality), "-e", "--keep-orientation", "--keep-dates",
        "--min-savings", str(profile.min_savings_bytes), "-O", "all", "--verbose", "2",
    ]
    if profile.png_opt_level != 3:                  # 3 is the caesiumclt default
        cmd += ["--png-opt-level", str(profile.png_opt_level)]
    if profile.zopfli:
        cmd += ["--zopfli"]
    if profile.jpeg_chroma != "auto":               # auto is the caesiumclt default
        cmd += ["--jpeg-chroma-subsampling", profile.jpeg_chroma]
    cmd += ["-o", str(out_dir)]
    if decision.long_edge:
        cmd += ["--long-edge", str(decision.long_edge), "--no-upscale"]
    cmd.append(str(src))
    return cmd


def video_command(src: Path, dest: Path, decision: Decision, info: MediaInfo,
                  profile: Profile, hwaccel: str = "", encoder: str = "x264",
                  target_kbps: int = 0) -> list[str]:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
           "-nostats", "-progress", "pipe:1"]   # progress drives the stall watchdog
    if hwaccel:
        cmd += ["-hwaccel", hwaccel]            # input option: decode on the GPU
    cmd += ["-i", str(src)]
    cmd += ["-map", "0:v:0"]
    if info.audio_codecs:
        cmd += ["-map", "0:a?"]
    for index in info.text_subtitle_indices:
        cmd += ["-map", f"0:{index}?"]
    cmd += ["-map_metadata", "0", "-map_chapters", "0"]
    if encoder == "x264":
        cmd += ["-c:v", "libx264", "-crf", str(profile.video_crf), "-preset", profile.video_preset]
    else:
        # Every QSV encoder wants nv12 surfaces and is driven by the target bitrate.
        cmd += ["-c:v", ENCODER_CODECS[encoder], "-b:v", f"{target_kbps}k",
                "-preset", profile.video_preset, "-pix_fmt", "nv12"]
    if decision.target_height:
        cmd += ["-vf", f"scale=-2:{decision.target_height}"]
    if encoder == "x264" and (decision.target_height or info.pix_fmt not in ("yuv420p", "yuvj420p")):
        cmd += ["-pix_fmt", "yuv420p"]
    cmd += ["-fps_mode", "passthrough"]
    if not info.audio_codecs:
        cmd += ["-an"]
    elif all(codec in MP4_SAFE_AUDIO_CODECS for codec in info.audio_codecs):
        cmd += ["-c:a", "copy"]
    else:
        cmd += ["-c:a", "aac", "-b:a", profile.video_audio_bitrate]
    if info.text_subtitle_indices:
        cmd += ["-c:s", "mov_text"]
    elif info.bitmap_subtitles:
        cmd += ["-sn"]                          # bitmap subtitles cannot live in MP4
    if encoder == "qsv-hevc" and dest.suffix.lower() in MP4_FAMILY_SUFFIXES:
        cmd += ["-tag:v", "hvc1"]               # otherwise many players refuse HEVC in MP4
    if dest.suffix.lower() in MP4_FAMILY_SUFFIXES:
        cmd += ["-movflags", "+faststart"]
    cmd.append(str(dest))
    return cmd


# ------------------------------ verification ------------------------------

def verify_image(temp: Path, info: MediaInfo, decision: Decision) -> str:
    out = probe(temp)
    if out.long_edge > info.long_edge:
        return "output is larger than the input"
    if decision.long_edge:
        if out.long_edge > decision.long_edge:
            return f"long edge {out.long_edge} exceeds the cap {decision.long_edge}"
        before = info.width / info.height
        after = out.width / out.height
        if abs(before - after) > 0.02:
            return f"aspect ratio changed from {before:.3f} to {after:.3f}"
    elif out.width != info.width or out.height != info.height:
        return f"dimensions changed from {info.width}x{info.height} to {out.width}x{out.height}"
    return ""


def verify_video(temp: Path, info: MediaInfo, decision: Decision) -> str:
    out = probe(temp)
    expected_height = decision.target_height or info.height
    if abs(out.height - expected_height) > 2:
        return f"height {out.height} does not match the expected {expected_height}"
    if info.duration > 1.0:
        tolerance = max(0.5, info.duration * 0.01)
        if abs(out.duration - info.duration) > tolerance:
            return f"duration {out.duration:.2f}s does not match {info.duration:.2f}s"
    if len(out.audio_codecs) != len(info.audio_codecs):
        return f"audio streams {len(out.audio_codecs)} != {len(info.audio_codecs)}"
    return ""


# ------------------------------ atomic swap ------------------------------

def replace_file_windows(temp: Path, target: Path) -> bool:
    """ReplaceFileW with REPLACEFILE_IGNORE_MERGE_ERRORS.

    Verified on this machine: without that flag the call fails with
    ERROR_ACCESS_DENIED (5); with it the swap succeeds.  Returns False when the
    API is unavailable or refused, and the caller falls back to os.replace.
    """
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:                                  # pragma: no cover
        return False
    try:
        api = ctypes.WinDLL("kernel32", use_last_error=True).ReplaceFileW
        api.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                        wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID]
        api.restype = wintypes.BOOL
        return bool(api(str(target), str(temp), None, 0x2, None, None))
    except (AttributeError, OSError):
        return False


def swap_into_place(temp: Path, target: Path, log: "Logger") -> None:
    """Atomically put temp in place of target, retrying on sharing violations."""
    last_error = ""
    for attempt in range(REPLACE_RETRIES):
        method = "ReplaceFileW" if replace_file_windows(temp, target) else ""
        if not method:
            try:
                os.replace(temp, target)
                method = "os.replace"
            except OSError as exc:
                last_error = str(exc)
                time.sleep(REPLACE_RETRY_DELAY * (attempt + 1))
                continue
        log.log(f"替换方式 {method} {temp.name} -> {target.name}")
        return
    raise ToolError(f"could not replace the original: {last_error}")


# ------------------------------ ledger ------------------------------

class Ledger:
    """Append-only JSONL record of every decision, so re-runs do no work.

    Kept in both modes: copy-out already uses "output exists" as its marker, but
    only the ledger stops a file that could not be compressed (not_smaller,
    modern_codec, ...) from being probed and re-encoded on every single run.
    """

    def __init__(self, path: Path, log: "Logger", in_place: bool, policy: str) -> None:
        self.path = path
        self.log = log
        self.in_place = in_place
        self.policy = policy
        self.entries: dict[str, dict] = {}
        self.stale = 0
        self.recovered = ""

    def load(self) -> None:
        if not self.path.exists():
            return
        good: list[str] = []
        bad = 0
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            key = record.get("key")
            if not key:
                bad += 1
                continue
            if record.get("status") != "replaced":
                # Entries written before profiles existed were produced by exactly
                # the balanced knobs, so they remain valid under balanced.
                record.setdefault("policy", LEGACY_POLICY)
                if (record.get("rules_version") != RULES_VERSION
                        or record.get("policy") != self.policy):
                    self.stale += 1
            good.append(line)
            self.entries[key] = record
        if bad:
            backup = self.path.with_name(f"{self.path.name}.bak-{int(time.time())}")
            try:
                shutil.copy2(self.path, backup)
            except OSError:
                pass
            self.path.write_text("\n".join(good) + ("\n" if good else ""), encoding="utf-8")
            self.recovered = f"丢弃 {bad} 行无法解析的记录，备份为 {backup.name}"
            self.log.log(f"台账 {self.recovered}")
        self.log.log(f"台账载入 entries={len(self.entries)} stale={self.stale}")

    def match(self, path: Path, key: str, size: int, mtime_ns: int) -> str:
        """Return the reason to skip this file with, or "" to reconsider it.

        `replaced` is terminal: a file we already compressed is never compressed
        again - not for a different profile, not after a RULES_VERSION bump.
        `no_change` only holds while the same policy produced it, because such a
        file was left untouched and re-evaluating it costs nothing but a probe.
        """
        entry = self.entries.get(key)
        if not entry:
            return ""
        if entry.get("status") == "replaced":
            if not self.in_place:
                # copy-out: the source file is untouched, so "output exists" is the
                # marker (checked by the caller).  Matching here would keep skipping
                # the source even after the user deleted the output.
                return ""
            if entry.get("output_size") != size:
                return ""
            if entry.get("mtime_ns") == mtime_ns:
                return "already_compressed"
            # A sync client or backup tool may have touched the file only.
            recorded_hash = entry.get("head_tail_hash")
            if recorded_hash and recorded_hash == safe_hash(path):
                return "already_compressed"
            return ""
        if entry.get("mtime_ns") != mtime_ns or entry.get("source_size") != size:
            return ""
        if entry.get("rules_version") != RULES_VERSION:
            return ""
        if entry.get("policy") != self.policy:
            return ""
        return "already_processed"

    def record(self, key: str, entry: dict) -> None:
        record = {"key": key, "rules_version": RULES_VERSION, "time": now_iso(), **entry}
        self.entries[key] = record
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def rewrite(self) -> None:
        """Atomically rewrite the ledger from memory (used by --prune)."""
        tmp = self.path.with_name(self.path.name + ".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            for entry in self.entries.values():
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, self.path)

    def prune(self, existing: set[str]) -> int:
        gone = [key for key in self.entries if key not in existing]
        for key in gone:
            self.entries.pop(key, None)
        if gone:
            self.rewrite()
        return len(gone)

    def total_saved(self) -> int:
        return sum(max(0, e.get("saved", 0)) for e in self.entries.values())


class Lock:
    """Single-writer guard: an exclusively created file holding pid and start time."""

    def __init__(self, path: Path, log: "Logger") -> None:
        self.path = path
        self.log = log
        self.held = False

    def acquire(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            try:
                handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if self._stale():
                    self.log.log(f"移除过期锁文件 {self.path}")
                    try:
                        self.path.unlink()
                    except OSError:
                        pass
                    continue
                if time.monotonic() >= deadline:
                    return False
                time.sleep(0.5)
                continue
            except OSError:
                return False
            with os.fdopen(handle, "w", encoding="utf-8") as file:
                file.write(json.dumps({"pid": os.getpid(), "start": now_iso()}))
            self.held = True
            return True

    def _stale(self) -> bool:
        try:
            return time.time() - self.path.stat().st_mtime > LOCK_STALE_SECONDS
        except OSError:
            return True

    def release(self) -> None:
        if not self.held:
            return
        try:
            self.path.unlink()
        except OSError:
            pass
        self.held = False


# ------------------------------ logging & reports ------------------------------

class Logger:
    """Appends to run.log; only the final summary ever reaches the console."""

    def __init__(self, path: Path | None) -> None:
        self.path = path

    def log(self, message: str) -> None:
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(f"{now_iso()} {message}\n")
        except OSError:
            pass


def write_report(path: Path, root: Path, items: list[dict], extra: dict | None = None) -> None:
    payload = {
        "root": str(root),
        "rules_version": RULES_VERSION,
        "generated": now_iso(),
        "count": len(items),
        **(extra or {}),
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ------------------------------ run context ------------------------------

@dataclass
class Run:
    in_root: Path
    state_dir: Path
    temp_dir: Path
    out_root: Path
    originals_dir: Path | None
    profile: Profile
    policy: str
    in_place: bool
    dry_run: bool
    only: str                           # "all" | "image" | "video"
    ledger: Ledger
    log: Logger
    success: list[dict] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    scanned: int = 0
    interrupted: bool = False
    hwaccel: str = ""                   # hardware decoder to try, "" = software
    hwaccel_used: str = ""              # what the last encode actually used
    hwdec_failures: int = 0             # hardware decode failures so far this run
    hwenc_failures: int = 0             # hardware encode failures so far this run
    encoder: str = "x264"               # requested video encoder
    encoder_used: str = ""              # what the last encode actually used
    stall_timeout: int = STALL_TIMEOUT_SECONDS   # 0 = no limit at all

    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.in_root).as_posix()
        except ValueError:
            return path.as_posix()

    def record_skip(self, path: Path, kind: str, reason: str, **extra) -> None:
        self.skipped.append({"source": self.rel(path), "type": kind,
                             "reason": reason, **{k: v for k, v in extra.items() if v is not None}})
        self.log.log(f"跳过 {reason} {self.rel(path)}")

    def record_fail(self, path: Path, kind: str, reason: str, error: str = "", **extra) -> None:
        self.failed.append({"source": self.rel(path), "type": kind, "reason": reason,
                            "error": error[:2000], "retryable": reason in RETRYABLE_REASONS,
                            **extra})
        self.log.log(f"失败 {reason} {self.rel(path)}：{error[:300]}")

    def record_success(self, path: Path, kind: str, dest: Path | None, size_before: int,
                       size_after: int, **extra) -> None:
        self.success.append({
            "source": self.rel(path),
            "output": self.rel(dest) if dest else None,
            "type": kind,
            "size_before": size_before,
            "size_after": size_after,
            "saved": max(0, size_before - size_after),
            **extra,
        })

    def ledger_note(self, path: Path, status: str, reason: str, source_size: int,
                    output_size: int | None, mtime_ns: int, extra: dict | None = None) -> None:
        if self.dry_run or reason in NEVER_LEDGER_REASONS:
            return                          # a dry run never touches the ledger
        record = {
            "status": status, "reason": reason,
            "source_size": source_size, "output_size": output_size,
            "saved": max(0, source_size - (output_size if output_size is not None else source_size)),
            "mtime_ns": mtime_ns,
            **(extra or {}),
        }
        if status == "no_change":
            # `no_change` is only valid while the same policy is in force, because
            # the file itself was never written to.  `replaced` needs no policy: it
            # is terminal.
            record["policy"] = self.policy
        self.ledger.record(self.rel(path), record)


# ------------------------------ scanning & gates ------------------------------

def scan_files(run: Run, only: str = "all") -> list[Path]:
    """Every file worth considering, optionally narrowed to one media kind.

    ``only`` overrides ``run.only`` for the one caller that needs the full tree
    regardless of the filter (``--prune``), because pruning the ledger from a
    filtered scan would silently drop every record of the other kind.
    """
    files: list[Path] = []
    for path in run.in_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel_parts = path.relative_to(run.in_root).parts[:-1]
        if any(part in ARTIFACT_DIR_NAMES for part in rel_parts):
            continue
        if not run.in_place and path.is_relative_to(run.out_root):
            continue
        if only != "all" and classify(path) != only:
            continue
        files.append(path)
    return files


def cheap_gate(path: Path, seen_inodes: set) -> str:
    """Gates that need no probing.  Returns a reason, or "" to continue."""
    name = path.name.lower()
    if name in JUNK_FILES:
        return "junk"
    if name.endswith(IN_PROGRESS_SUFFIXES):
        return "in_progress"
    try:
        info = path.stat()
    except OSError:
        return ""                      # let the probe report the real error
    if info.st_size == 0:
        return "empty"
    if os.name == "nt" and getattr(info, "st_file_attributes", 0) & CLOUD_ATTRIBUTES:
        return "cloud_placeholder"
    if os.name == "nt" and len(str(path)) > MAX_PATH_LENGTH:
        return "too_long_path"
    if time.time() - info.st_mtime < IN_PROGRESS_MTIME_SECONDS:
        return "in_progress"
    inode = (info.st_dev, info.st_ino)
    if info.st_ino and inode in seen_inodes:
        return "duplicate_inode"
    if info.st_ino:
        seen_inodes.add(inode)
    return ""


# ------------------------------ per-file processing ------------------------------

def output_path(run: Run, path: Path, kind: str) -> Path:
    """Final destination: same name in-place, mirrored tree in copy-out."""
    if run.in_place:
        return path
    dest = run.out_root / path.relative_to(run.in_root)
    return dest.with_suffix(VIDEO_OUTPUT_EXT) if kind == "video" else dest


def temp_path(run: Run, path: Path, kind: str) -> Path:
    """Temp file in the same volume; its suffix picks the ffmpeg muxer."""
    if kind == "video":
        suffix = path.suffix if run.in_place else VIDEO_OUTPUT_EXT
        return run.temp_dir / f"{path.stem}-{abs(hash(path.name)) % 10 ** 8}{suffix}"
    return run.temp_dir / path.name


def prepare_temp_dir(run: Run) -> None:
    shutil.rmtree(run.temp_dir, ignore_errors=True)
    run.temp_dir.mkdir(parents=True, exist_ok=True)


def cleanup_temp_dir(run: Run) -> None:
    shutil.rmtree(run.temp_dir, ignore_errors=True)


def free_space(path: Path) -> int:
    """Free bytes on the volume that will hold the temp file."""
    existing = path
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    try:
        return shutil.disk_usage(existing).free
    except OSError:
        return sys.maxsize


def process_file(run: Run, path: Path, seen_inodes: set) -> None:
    kind = classify(path)
    gate = cheap_gate(path, seen_inodes)
    if gate:
        run.record_skip(path, kind, gate)
        return
    if kind == "archive":
        run.record_skip(path, kind, "archive")
        return
    if kind == "unsupported":
        run.record_skip(path, kind, "unsupported")
        return

    key = run.rel(path)
    status = path.stat()
    already = run.ledger.match(path, key, status.st_size, status.st_mtime_ns)
    if already:
        run.record_skip(path, kind, already)
        return
    dest = output_path(run, path, kind)
    if not run.in_place and dest.exists():
        # copy-out mode: an existing output is the processed marker (spec).
        run.record_skip(path, kind, "already_processed", output=run.rel(dest))
        return

    try:
        info = probe(path)
    except (RuntimeError, OSError) as exc:
        run.record_fail(path, kind, "failed_probe", str(exc))
        return
    info.kind = kind

    if kind == "image":
        decision = decide_image(path, info, status.st_size, run.profile)
    else:
        decision = decide_video(path, info, status.st_size, run.in_place, run.profile)
    if decision.action == "skip":
        run.record_skip(path, kind, decision.reason, size=status.st_size, threshold=decision.threshold)
        run.ledger_note(path, "no_change", decision.reason, status.st_size, None, status.st_mtime_ns)
        return

    geometry = {
        "width_before": info.width, "height_before": info.height,
        "long_edge_before": info.long_edge, "duration": round(info.duration, 3),
        "codec": info.codec, "quality": decision.quality,
        "target_height": decision.target_height, "target_long_edge": decision.long_edge,
        "dropped_bitmap_subtitles": info.bitmap_subtitles or None,
    }

    if run.dry_run:
        run.record_success(path, kind, output_path(run, path, kind), status.st_size, status.st_size,
                           planned=True, threshold=decision.threshold, **geometry)
        run.log.log(f"预演压缩 {key} quality={decision.quality} "
                    f"cap={decision.long_edge or decision.target_height}")
        return

    copies = 2 if run.originals_dir is not None else 1      # temp file (+ backup copy)
    needed = status.st_size * copies + FREE_SPACE_MARGIN
    free = free_space(run.temp_dir)
    if free < needed:
        run.record_fail(path, kind, "no_disk_space",
                        f"free {human(free)} < needed {human(needed)}", **geometry)
        return

    prepare_temp_dir(run)
    try:
        size_after = encode(run, path, kind, info, decision, status.st_size)
    except ToolStalled as exc:
        run.record_fail(path, kind, "timeout", str(exc), **geometry)
        return
    except ToolError as exc:
        run.record_fail(path, kind, "failed_encode", str(exc), **geometry)
        return

    if size_after is None:
        run.record_skip(path, kind, "no_size_gain", size=status.st_size, **geometry)
        run.ledger_note(path, "no_change", "no_size_gain", status.st_size, None, status.st_mtime_ns)
        return

    temp = temp_path(run, path, kind)
    problem = verify_image(temp, info, decision) if kind == "image" else verify_video(temp, info, decision)
    if problem:
        run.record_fail(path, kind, "failed_verify", problem, **geometry)
        return

    if not is_meaningful_saving(status.st_size, size_after, run.profile):
        reason = "not_smaller" if size_after >= status.st_size else "no_size_gain"
        run.record_skip(path, kind, reason, size=status.st_size, size_after=size_after, **geometry)
        run.ledger_note(path, "no_change", reason, status.st_size, None, status.st_mtime_ns)
        return

    current = path.stat()
    if (current.st_size, current.st_mtime_ns) != (status.st_size, status.st_mtime_ns):
        run.record_skip(path, kind, "changed_during_run", size=status.st_size, **geometry)
        return

    try:
        dest = finish(run, path, kind, temp, status)
    except ToolError as exc:
        run.record_fail(path, kind, "locked", str(exc), **geometry)
        return

    run.record_success(path, kind, dest, status.st_size, size_after, scaled=decision.scaled,
                       threshold=decision.threshold, hwaccel=run.hwaccel_used or None,
                       encoder=run.encoder_used or None, **geometry)
    run.ledger_note(path, "replaced", "", status.st_size, size_after,
                    dest.stat().st_mtime_ns if run.in_place else status.st_mtime_ns,
                    extra={"geometry": geometry, "head_tail_hash": safe_hash(dest)})
    run.log.log(f"压缩完成 {key}（{human(status.st_size)} -> {human(size_after)}）")


def encode(run: Run, path: Path, kind: str, info: MediaInfo, decision: Decision,
           size: int) -> int | None:
    """Encode into the temp path.  Returns the encoded size, or None when the
    encoder deliberately produced nothing (caesiumclt below --min-savings)."""
    temp = temp_path(run, path, kind)
    run.hwaccel_used = ""
    run.encoder_used = ""
    if kind == "image":
        label = f"{run.rel(path)} 图片"
        exec_tool(run, image_command(path, run.temp_dir, decision, run.profile), label)
    else:
        remaining = list(encoder_attempts(run))
        total = len(remaining)
        attempt = 0
        while remaining:
            hwaccel, encoder = remaining.pop(0)
            attempt += 1
            target = qsv_target_kbps(info, decision, run.profile, size) if encoder != "x264" else 0
            command = video_command(path, temp, decision, info, run.profile, hwaccel,
                                    encoder, target)
            output_height = decision.target_height or info.height
            label = (f"{run.rel(path)} {info.width}x{info.height}->{output_height}p "
                     f"{info.duration:.0f}s {encoder}/{hwaccel or '软解'} "
                     f"[尝试 {attempt}/{total}]")
            try:
                exec_ffmpeg(run, command, label)
            except ToolError as exc:
                if not remaining:
                    raise
                # Hardware decode/encode are optimisations, so a file is never failed
                # over them - but a single unlucky file must not switch the whole run
                # to software either, hence the failure budget.
                if encoder != "x264":
                    run.hwenc_failures += 1
                    if run.hwenc_failures >= HARDWARE_MAX_FAILURES:
                        run.log.log(f"硬件编码已失败 {run.hwenc_failures} 次，"
                                    "本次运行后续文件改用 x264")
                        run.encoder = "x264"
                    else:
                        run.log.log(f"硬件编码失败（第 {run.hwenc_failures}/"
                                    f"{HARDWARE_MAX_FAILURES} 次），本文件改用 x264 重试：{exc}")
                if hwaccel:
                    run.hwdec_failures += 1
                    if run.hwdec_failures >= HARDWARE_MAX_FAILURES:
                        run.log.log(f"硬解已失败 {run.hwdec_failures} 次，"
                                    "本次运行后续文件改用软解")
                        run.hwaccel = ""
                    else:
                        run.log.log(f"硬解失败（第 {run.hwdec_failures}/"
                                    f"{HARDWARE_MAX_FAILURES} 次），本文件改用软解重试：{exc}")
                if isinstance(exc, ToolStalled):
                    # A stall on the hardware path can be a hardware deadlock, so one
                    # software attempt is worth it - but never a third ten-minute wait.
                    remaining = [pair for pair in remaining if pair == ("", "x264")][:1]
                prepare_temp_dir(run)
                continue
            run.hwaccel_used = hwaccel
            run.encoder_used = encoder
            break

    if kind == "image":
        produced = temp
        if not produced.exists():
            candidates = sorted(p for p in run.temp_dir.glob(path.stem + ".*")
                                if p.suffix.lower() in IMAGE_EXTS)
            produced = candidates[0] if candidates else None
        if produced is None:
            return None                     # below --min-savings: not worth replacing
        if produced != temp:
            produced.replace(temp)
    if not temp.exists():
        raise ToolError("the encoder reported success but produced no file")
    return temp.stat().st_size


def encoder_attempts(run: Run) -> list[tuple[str, str]]:
    """(decoder, encoder) pairs to try, best first, ending in the safe fallback."""
    pairs = [(run.hwaccel, run.encoder)]
    if run.encoder != "x264":
        pairs.append((run.hwaccel, "x264"))
    if run.hwaccel:
        pairs.append(("", "x264"))
    unique: list[tuple[str, str]] = []
    for pair in pairs:
        if pair not in unique:
            unique.append(pair)
    return unique


def finish(run: Run, path: Path, kind: str, temp: Path, status: os.stat_result) -> Path:
    """Move the verified temp file into its final place, atomically."""
    dest = output_path(run, path, kind)
    if run.originals_dir is not None:
        backup = run.originals_dir / path.relative_to(run.in_root)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        if backup.stat().st_size != status.st_size:
            raise ToolError("original backup copy is incomplete")
    try:
        os.utime(temp, ns=(status.st_atime_ns, status.st_mtime_ns))
    except OSError:
        pass
    dest.parent.mkdir(parents=True, exist_ok=True)
    readonly = bool(os.name == "nt" and getattr(status, "st_file_attributes", 0) & FILE_ATTRIBUTE_READONLY)
    if readonly:
        try:
            os.chmod(dest, stat_module.S_IWRITE)
        except OSError:
            pass
    swap_into_place(temp, dest, run.log)
    if readonly:
        try:
            os.chmod(dest, stat_module.S_IREAD)
        except OSError:
            pass
    try:
        os.utime(dest, ns=(status.st_atime_ns, status.st_mtime_ns))
    except OSError:
        pass
    return dest


# ------------------------------ audit ------------------------------

def audit(run: Run, files: list[Path], seen_inodes: set, limit: int = 1000) -> int:
    counts: dict[str, int] = {}
    would: list[dict] = []
    stale_hashes = 0
    for path in files:
        gate = cheap_gate(path, seen_inodes)
        if gate:
            counts[gate] = counts.get(gate, 0) + 1
            continue
        kind = classify(path)
        if kind in ("archive", "unsupported"):
            counts[kind] = counts.get(kind, 0) + 1
            continue
        status = path.stat()
        key = run.rel(path)
        skip_reason = run.ledger.match(path, key, status.st_size, status.st_mtime_ns)
        if skip_reason:
            counts[skip_reason] = counts.get(skip_reason, 0) + 1
            entry = run.ledger.entries.get(key) or {}
            recorded_hash = entry.get("head_tail_hash")
            if recorded_hash and recorded_hash != safe_hash(path):
                stale_hashes += 1
            continue
        try:
            info = probe(path)
        except (RuntimeError, OSError):
            counts["failed_probe"] = counts.get("failed_probe", 0) + 1
            continue
        decision = (decide_image(path, info, status.st_size, run.profile) if kind == "image"
                    else decide_video(path, info, status.st_size, run.in_place, run.profile))
        if decision.action == "encode":
            counts["would_compress"] = counts.get("would_compress", 0) + 1
            if len(would) < limit:
                would.append({"source": key, "type": kind, "size": status.st_size,
                              "threshold": decision.threshold, "quality": decision.quality,
                              "target_long_edge": decision.long_edge,
                              "target_height": decision.target_height})
        else:
            counts[decision.reason] = counts.get(decision.reason, 0) + 1

    undecodable: list[str] = []
    if not run.in_place and run.out_root.exists():
        for existing in run.out_root.rglob("*"):
            if existing.is_file() and not existing.is_symlink() and existing.name not in ("run.log",):
                try:
                    probe(existing)
                except (RuntimeError, OSError):
                    if len(undecodable) < 50:
                        undecodable.append(run.rel(existing))

    report = {
        "root": str(run.in_root),
        "mode": "in-place" if run.in_place else "copy-out",
        "profile": run.profile.name,
        "policy": run.policy,
        "only": run.only,
        "encoder": run.encoder,
        "rules_version": RULES_VERSION,
        "generated": now_iso(),
        "scanned": len(files),
        "counts": counts,
        "ledger": {"entries": len(run.ledger.entries), "stale": run.ledger.stale,
                   "recovered": run.ledger.recovered, "hash_mismatch": stale_hashes},
        "would_compress": would,
        "undecodable_outputs": undecodable,
    }
    target = run.state_dir / "audit.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"巡检报告 {target}")
    print(f"档位 {run.profile.name}（policy {run.policy}） | 编码器 {run.encoder}"
          + (f" | 只处理 {run.only}" if run.only != "all" else ""))
    print(f"已扫描 {len(files)} | 待压缩 {counts.get('would_compress', 0)} | "
          f"已压缩 {counts.get('already_compressed', 0)} | "
          f"已处理 {counts.get('already_processed', 0)} | "
          f"台账 {len(run.ledger.entries)} 条（过期 {run.ledger.stale}） | "
          f"无法解码的产物 {len(undecodable)}")
    run.log.log(f"巡检 profile={run.profile.name} policy={run.policy} only={run.only} "
                f"scanned={len(files)} counts={json.dumps(counts, sort_keys=True)}")
    return 0


# ------------------------------ preflight ------------------------------

def preflight() -> list[str]:
    problems: list[str] = []
    missing = [tool for tool in TOOLS if shutil.which(tool) is None]
    if missing:
        problems.append("缺少必需命令：" + "、".join(missing))
        problems.append("请先安装，并确认它们在 PATH 中")
        problems.append("caesiumclt 下载地址：https://github.com/Lymphatus/caesium-clt")
        return problems
    try:
        encoders = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True,
                                  encoding="utf-8", errors="replace", timeout=PROBE_TIMEOUT).stdout
    except (OSError, subprocess.TimeoutExpired):
        encoders = ""
    absent = [name for name in REQUIRED_ENCODERS if name not in encoders]
    if absent:
        problems.append("ffmpeg 缺少编码器：" + "、".join(absent))
    try:
        if subprocess.run(["caesiumclt", "--version"], capture_output=True, encoding="utf-8",
                          errors="replace", timeout=PROBE_TIMEOUT).returncode != 0:
            problems.append("caesiumclt --version 执行失败")
    except (OSError, subprocess.TimeoutExpired):
        problems.append("无法启动 caesiumclt")
    return problems


def tool_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for tool, args in (("ffmpeg", ["-version"]), ("caesiumclt", ["--version"])):
        try:
            result = subprocess.run([tool] + args, capture_output=True, encoding="utf-8",
                                    errors="replace", timeout=PROBE_TIMEOUT)
            line = (result.stdout or result.stderr).strip().splitlines()
            versions[tool] = line[0][:120] if line else "unknown"
        except (OSError, subprocess.TimeoutExpired):
            versions[tool] = "unknown"
    return versions


# ------------------------------ main ------------------------------

def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="files-compress",
        description="递归压缩一个目录里的超大图片和视频。",
        add_help=False,
    )
    # argparse ships English section titles; there is no public API for them, but
    # these two attributes have been stable across every supported CPython.
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示本帮助并退出")
    parser.add_argument("input", type=Path, help="要递归扫描的目录")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help=f"输出目录（默认 <输入目录>/{OUTPUT_DIR_NAME}）")
    parser.add_argument("--dry-run", action="store_true", help="只生成计划，不做任何实际改动")
    parser.add_argument("--in-place", action="store_true",
                        help="原子替换原文件（原地压缩），而不是另存副本")
    parser.add_argument("--keep-originals", nargs="?", const=ORIGINALS_DIR_NAME, default=None,
                        metavar="DIR",
                        help=f"替换前把原文件镜像到 DIR（默认 {ORIGINALS_DIR_NAME}），便于回滚")
    parser.add_argument("--audit", action="store_true", help="只读巡检：确认是否已经收敛")
    parser.add_argument("--profile", choices=tuple(PROFILES), default=DEFAULT_PROFILE,
                        help="压缩档位：balanced 均衡（默认）、small 更小、"
                             "tiny 极端小（不考虑质量，尽可能小）")
    parser.add_argument("--only", choices=("all", "image", "video"), default="all",
                        help="只处理某一类文件：all 全部（默认）、image 只处理图片"
                             "（用 caesiumclt）、video 只处理视频（用 ffmpeg）；"
                             "另一类文件完全不会被扫描、探测或写入报告")
    parser.add_argument("--no-hwaccel", action="store_true",
                        help="关闭硬件解码加速（默认开启；仅在排查问题或需要"
                             "与纯软件解码逐字节一致时使用）")
    parser.add_argument("--encoder", choices=ENCODERS, default="x264",
                        help="视频编码器：x264 CPU（默认，同体积画质最好）、"
                             "qsv Intel 核显 H.264（快约 6 倍，按码率驱动）、"
                             "qsv-hevc 核显 HEVC（更快且更省）")
    parser.add_argument("--prune", action="store_true", help="清理台账中已不存在的文件记录")
    parser.add_argument("--limit", type=int, default=None, help="最多处理 N 个文件")
    parser.add_argument("--order", choices=("size", "name"), default="size",
                        help="处理顺序（默认 size：从大到小）")
    parser.add_argument("--lock-timeout", type=float, default=30.0,
                        help="等待并发运行结束的秒数（默认 30）")
    parser.add_argument("--stall-timeout", type=int, default=STALL_TIMEOUT_SECONDS, metavar="N",
                        help=f"编码连续 N 秒没有任何进度就判定卡死并中止（默认 "
                             f"{STALL_TIMEOUT_SECONDS}；0 = 关闭看门狗，完全不设时限）。"
                             "注意：没有总时长上限，慢机器与长视频不会被误杀")
    parser.add_argument("--version", action="version",
                        help="显示版本号并退出",
                        version=f"files-compress {__version__}（规则版本 {RULES_VERSION}）")
    return parser.parse_args(sys.argv[1:] if argv is None else argv)


def main(argv: list[str] | None = None) -> int:
    setup_console()
    args = parse_args(argv)

    in_root = args.input.expanduser().resolve()
    if not in_root.is_dir():
        print(f"不是目录：{in_root}", file=sys.stderr)
        return 2

    problems = preflight()
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 2

    if args.in_place and args.output:
        print("提示：--in-place 模式下 -o/--output 会被忽略", file=sys.stderr)
    out_root = (args.output.expanduser() if args.output else in_root / OUTPUT_DIR_NAME).resolve()
    if not args.in_place and (out_root == in_root or in_root.is_relative_to(out_root)):
        print(f"输出目录不能包含输入目录：{out_root}", file=sys.stderr)
        return 2

    state_dir = (in_root / STATE_DIR_NAME) if args.in_place else out_root
    temp_dir = (in_root if args.in_place else out_root) / TEMP_DIR_NAME
    originals_dir = None
    if args.keep_originals is not None:
        if not args.in_place:
            print("提示：--keep-originals 只对 --in-place 生效", file=sys.stderr)
        else:
            candidate = Path(args.keep_originals)
            originals_dir = (candidate if candidate.is_absolute() else in_root / candidate).resolve()

    state_dir.mkdir(parents=True, exist_ok=True)
    profile = PROFILES[args.profile]
    policy = policy_fingerprint(profile, args.encoder)
    log = Logger(state_dir / "run.log")
    run = Run(
        in_root=in_root,
        state_dir=state_dir,
        temp_dir=temp_dir,
        out_root=out_root,
        originals_dir=originals_dir,
        profile=profile,
        policy=policy,
        encoder=args.encoder,
        stall_timeout=args.stall_timeout,
        in_place=args.in_place,
        dry_run=args.dry_run,
        only=args.only,
        ledger=Ledger(state_dir / LEDGER_NAME, log, args.in_place, policy),
        log=log,
    )

    lock = Lock(state_dir / LOCK_NAME, log)
    if not args.audit and not lock.acquire(args.lock_timeout):
        print(f"另一个实例正持有 {state_dir / LOCK_NAME}；请等它结束，或直接删除该文件",
              file=sys.stderr)
        return 2

    exit_code = 0
    if run.only == "image":
        # No video will be encoded, so the hardware probes would only cost seconds.
        log.log("仅处理图片：跳过硬件探测，编码全部由 caesiumclt 完成")
    elif not args.dry_run and not args.audit:
        probes = probe_hardware(state_dir, log)
        if not args.no_hwaccel:
            if probes.get(HWACCEL_DECODE):
                run.hwaccel = HWACCEL_DECODE
            else:
                log.log(f"硬解不可用（{HWACCEL_DECODE} 探针失败），本次运行解码走 CPU")
        if run.encoder != "x264" and not probes.get(f"encoder_{run.encoder}"):
            log.log(f"硬件编码不可用（{run.encoder} 探针失败），本次运行回退 x264")
            run.encoder = "x264"
            run.policy = policy_fingerprint(profile, run.encoder)
    try:
        versions = tool_versions()
        log.log(f"运行开始 mode={'in-place' if args.in_place else 'copy-out'} root={in_root} "
                f"output={out_root} profile={profile.name} policy={run.policy} "
                f"encoder={run.encoder} hwaccel={run.hwaccel or 'off'} "
                f"stall={str(run.stall_timeout) + 's' if run.stall_timeout else 'off'} "
                f"only={run.only} dry_run={args.dry_run} audit={args.audit} rules={RULES_VERSION}")
        log.log(f'工具版本 ffmpeg="{versions["ffmpeg"]}" caesiumclt="{versions["caesiumclt"]}"')
        run.ledger.load()
        files = scan_files(run, run.only)
        files = (sorted(files, key=lambda p: p.stat().st_size, reverse=True)
                 if args.order == "size" else sorted(files))
        if args.limit is not None:
            files = files[:max(0, args.limit)]
        run.scanned = len(files)
        log.log(f"扫描 {in_root} -> {run.scanned} 个文件"
                + (f"（仅 {run.only}）" if run.only != "all" else ""))

        seen_inodes: set = set()
        if args.audit:
            return audit(run, files, seen_inodes)

        if not run.dry_run:
            prepare_temp_dir(run)
        for index, path in enumerate(files, start=1):
            try:
                process_file(run, path, seen_inodes)
            except KeyboardInterrupt:
                raise
            except Exception as exc:               # never abort the run because of one file
                run.record_fail(path, classify(path), "failed_encode", f"意外错误：{exc}")
            if sys.stdout.isatty() and index % 25 == 0:
                print(f"  ... 进度 {index}/{run.scanned}", flush=True)

        if args.prune and not run.dry_run:
            # Deliberately unfiltered: --prune drops records whose file is gone,
            # and a narrowed scan would make every other kind look gone.
            dropped = run.ledger.prune({run.rel(path) for path in scan_files(run, "all")})
            log.log(f"清理台账 {dropped} 条记录")
        exit_code = 1 if run.failed else 0
    except KeyboardInterrupt:
        run.interrupted = True
        log.log(f"运行被中断：已扫描 {run.scanned}，成功 {len(run.success)}，"
                f"失败 {len(run.failed)}，跳过 {len(run.skipped)}；"
                "未完成的部分下次运行会继续（已压缩的文件不会被重压）")
        exit_code = 1
        print("已中断：原文件完好，重新运行即可继续", file=sys.stderr)
    finally:
        if not run.dry_run:
            cleanup_temp_dir(run)
        try:
            if not args.audit:                  # audit must not clobber a real run's reports
                write_report(state_dir / "success.json", in_root, run.success,
                             {"mode": "dry-run" if run.dry_run
                              else ("in-place" if run.in_place else "copy-out"),
                              "profile": profile.name, "policy": run.policy,
                              "only": run.only,
                              "encoder": run.encoder})
                write_report(state_dir / "failed.json", in_root, run.failed,
                             {"profile": profile.name, "policy": run.policy,
                              "only": run.only,
                              "encoder": run.encoder})
                write_report(state_dir / "skipped.json", in_root, run.skipped,
                             {"profile": profile.name, "policy": run.policy,
                              "only": run.only,
                              "encoder": run.encoder})
        except OSError as exc:
            print(f"无法写入报告文件：{exc}", file=sys.stderr)
            exit_code = exit_code or 1
        saved = sum(item["saved"] for item in run.success if "saved" in item)
        cumulative = run.ledger.total_saved()
        log.log(f"汇总 profile={profile.name} policy={run.policy} encoder={run.encoder} "
                f"only={run.only} scanned={run.scanned} "
                f"success={len(run.success)} failed={len(run.failed)} "
                f"skipped={len(run.skipped)} saved={saved}")
        if not args.audit:
            print(f"输出目录 {state_dir}")
            print(f"档位 {profile.name}（policy {run.policy}） | 编码器 {run.encoder}"
                  + (f" | 只处理 {run.only}" if run.only != "all" else ""))
            print(f"已扫描 {run.scanned} | 成功 {len(run.success)} | 失败 {len(run.failed)} | "
                  f"跳过 {len(run.skipped)} | 节省 {human(saved)}（累计 {human(cumulative)}）")
            if run.dry_run:
                print("dry-run：未做任何压缩，计划见 success.json")
        lock.release()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
