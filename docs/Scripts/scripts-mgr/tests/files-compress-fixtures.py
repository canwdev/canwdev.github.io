"""Generate the acceptance fixtures for files-compress.py (implementation doc, section 11.1).

Usage: <python-with-Pillow> files-compress-fixtures.py <target-dir>
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(sys.argv[1])
NOISE = "nullsrc=s={w}x{h}:rate={r},geq=lum='random(1)*255':cb=128:cr=128"


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def main() -> None:
    shutil.rmtree(ROOT, ignore_errors=True)
    ROOT.mkdir(parents=True)
    sub = ROOT / "sub"
    sub.mkdir()

    # oversized PNG and a below-threshold one
    ff("-f", "lavfi", "-i", NOISE.format(w=3000, h=2000, r=25), "-frames:v", "1", str(ROOT / "big.png"))
    ff("-f", "lavfi", "-i", "testsrc=size=220x180", "-frames:v", "1", str(ROOT / "small.png"))
    # 6000x4000 photo -> exercises the long-edge cap
    ff("-f", "lavfi", "-i", NOISE.format(w=6000, h=4000, r=25), "-frames:v", "1", "-q:v", "2",
       str(sub / "huge.jpg"))
    # corrupt files with image/video extensions
    (ROOT / "broken.png").write_bytes(os.urandom(4 * 1024 * 1024))
    (ROOT / "broken.mp4").write_bytes(os.urandom(3 * 1024 * 1024))
    # video that grows when re-encoded at CRF 23 -> not_smaller
    # A source our own settings cannot meaningfully beat -> the not_smaller path.
    # 640x360 keeps it small (4.8 MB) and fast; pure 1080p noise would be ~43 MB
    # at CRF 30 and would slow every phase down for no extra coverage.  Measured
    # re-encode/source ratio: 1.12 (same at any resolution, it only depends on the
    # CRF gap and the content).
    ff("-f", "lavfi", "-i", NOISE.format(w=640, h=360, r=30), "-t", "3", "-c:v", "libx264",
       "-crf", "30", "-pix_fmt", "yuv420p", str(ROOT / "notsmall_noise.mp4"))
    # 4K high-bitrate video -> downscale to 1440
    ff("-f", "lavfi", "-i", "testsrc=size=3840x2160:rate=30", "-t", "2", "-c:v", "libx264",
       "-b:v", "60M", "-minrate", "60M", "-maxrate", "60M", "-bufsize", "30M",
       "-x264-params", "nal-hrd=cbr", "-pix_fmt", "yuv420p", str(ROOT / "big4k.mp4"))
    # already-efficient HEVC below its tier -> modern_codec
    ff("-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=25", "-t", "2", "-c:v", "libx265",
       "-x265-params", "log-level=none", "-crf", "30", str(ROOT / "modern_hevc.mp4"))
    # HDR -> hdr
    ff("-f", "lavfi", "-i", "testsrc=size=1280x720:rate=25", "-t", "2", "-c:v", "libx265",
       "-pix_fmt", "yuv420p10le", "-color_primaries", "bt2020", "-color_trc", "smpte2084",
       "-colorspace", "bt2020nc",
       "-x265-params", "colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc:log-level=none",
       str(ROOT / "hdr.mp4"))
    # 1080p high-bitrate with two audio tracks + a text subtitle (stream mapping)
    (ROOT / "subs.srt").write_text("1\n00:00:00,000 --> 00:00:01,500\nhello\n", encoding="utf-8")
    ff("-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=30", "-f", "lavfi", "-i", "sine=frequency=440",
       "-f", "lavfi", "-i", "sine=frequency=880", "-t", "3", "-map", "0:v", "-map", "1:a", "-map", "2:a",
       "-c:v", "libx264", "-b:v", "40M", "-minrate", "40M", "-maxrate", "40M", "-bufsize", "20M",
       "-x264-params", "nal-hrd=cbr", "-pix_fmt", "yuv420p", "-c:a", "aac",
       str(ROOT / "two_audio.mp4"))
    ff("-i", str(ROOT / "two_audio.mp4"), "-i", str(ROOT / "subs.srt"), "-map", "0", "-map", "1",
       "-c", "copy", "-c:s", "mov_text", str(ROOT / "subbed.mp4"))

    # animated gif, archive, junk, empty, in-progress, extension-less still
    ff("-f", "lavfi", "-i", "testsrc=size=240x180:rate=5", "-t", "2", str(ROOT / "anim.gif"))
    with zipfile.ZipFile(ROOT / "pack.zip", "w") as archive:
        archive.writestr("a.txt", "hello")
    (ROOT / "note.txt").write_text("plain text\n", encoding="utf-8")
    (ROOT / ".DS_Store").write_bytes(b"\x00\x01junk")
    (ROOT / "empty.mp4").write_bytes(b"")
    (ROOT / "download.part").write_bytes(b"partial")
    shutil.copy2(ROOT / "small.png", ROOT / "no_extension")
    os.link(ROOT / "small.png", ROOT / "small_link.png")        # duplicate inode

    # EXIF fixture (needs Pillow)
    exif_src = ROOT / "exif.jpg"
    exif = Image.Exif()
    exif[271], exif[272] = "TestMake", "TestModel"
    exif[306] = exif[36867] = "2021:07:04 12:34:56"
    Image.open(ROOT / "big.png").convert("RGB").resize((1600, 1200)).save(exif_src, quality=95, exif=exif)

    # long path (>240 chars) - may fail on some systems, that is fine
    deep = ROOT
    try:
        for index in range(6):
            deep = deep / f"deep-directory-level-{index}-aaaaaaaaaaaaaaaaaaaa"
            deep.mkdir()
        ff("-f", "lavfi", "-i", "testsrc=size=320x240", "-frames:v", "1", str(deep / "deep.png"))
    except OSError as exc:
        print(f"note: deep path fixture skipped ({exc})")

    # everything is old except fresh.jpg, which drives the in-progress mtime gate.
    # Its timestamp is put in the *future* so the gate still holds when a run takes
    # longer than the 300 s window (a slow machine would otherwise turn it into a
    # perfectly ordinary candidate halfway through the run).
    old = time.time() - 7200
    fresh = ROOT / "fresh.jpg"
    shutil.copy2(exif_src, fresh)
    for path in ROOT.rglob("*"):
        if path.is_file() and path != fresh:
            os.utime(path, (old, old))
    os.utime(fresh, None)
    ahead = time.time() + 3600
    os.utime(fresh, (ahead, ahead))

    for path in sorted(ROOT.rglob("*")):
        if path.is_file():
            print(f"{path.stat().st_size:>12}  {path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
