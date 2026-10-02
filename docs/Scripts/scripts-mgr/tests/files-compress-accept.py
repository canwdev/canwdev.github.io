"""Acceptance runner for files-compress.py (implementation doc, section 11).

Generate the fixtures first, with a Python that has Pillow:

    python tests/files-compress-fixtures.py %TEMP%/fc-accept
    python tests/files-compress-accept.py

The runner starts the CLI itself with the system Python, so the tested
interpreter matches the real one.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

TMP = Path(tempfile.gettempdir())
FIX = TMP / "fc-accept"
WORK = TMP / "fc-work"
CLI = Path(__file__).resolve().parent.parent / "files-compress.py"
PY = shutil.which("python") or sys.executable

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  -- ' + detail) if detail else ''}", flush=True)
    return bool(ok)


def cli(*args: str, timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(CLI), *args], capture_output=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def report(directory: Path, name: str) -> dict:
    return json.loads((directory / name).read_text(encoding="utf-8"))


def reasons(items: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        out[item["reason"]] = out.get(item["reason"], 0) + 1
    return out


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fresh_work(name: str) -> Path:
    target = WORK / name
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(FIX, target)
    ahead = time.time() + 3600              # keep the in-progress gate valid all run
    os.utime(target / "fresh.jpg", (ahead, ahead))
    link = target / "small_link.png"          # copytree breaks hard links, restore one
    link.unlink(missing_ok=True)
    os.link(target / "small.png", link)
    os.utime(link, (time.time() - 7200, time.time() - 7200))
    return target


def ledgers(directory: Path) -> list[dict]:
    for path in (directory / ".compress-state" / "state.jsonl", directory / "state.jsonl"):
        if path.exists():
            return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()]
    return []


def slow_video(path: Path, seconds: int) -> None:
    """A high-bitrate, compressible source: pass the threshold and take a while
    to re-encode, so the mid-run and kill tests have a usable window."""
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", "testsrc=size=1920x1080:rate=30", "-t", str(seconds),
                    "-c:v", "libx264", "-b:v", "12M", "-minrate", "12M", "-maxrate", "12M",
                    "-bufsize", "6M", "-x264-params", "nal-hrd=cbr", "-pix_fmt", "yuv420p",
                    str(path)], check=True)


def main() -> int:
    if not FIX.exists():
        print(f"fixtures not found: {FIX}\nrun tests/files-compress-fixtures.py first",
              file=sys.stderr)
        return 2
    if not CLI.exists():
        print(f"cli not found: {CLI}", file=sys.stderr)
        return 2
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)

    # ---------------- copy-out mode ----------------
    tree = fresh_work("copyout")
    original_big = sha(tree / "big.png")
    plan = cli(str(tree), "--dry-run")
    success = report(tree / "_compressed", "success.json")
    dry_failed = report(tree / "_compressed", "failed.json")
    check("A1 dry-run reports the 2 corrupt files and exits 1",
          plan.returncode == 1 and dry_failed["count"] == 2
          and all(i["reason"] == "failed_probe" for i in dry_failed["items"]),
          f"rc={plan.returncode} failed={dry_failed['count']}")
    check("A1 dry-run plans 7 encodes", success["count"] == 7, f"count={success['count']}")
    check("A1 dry-run marks items planned",
          all(item.get("planned") for item in success["items"]))
    check("A1 dry-run writes no media output",
          not any(p.is_file() for p in (tree / "_compressed").glob("**/*")
                  if p.suffix.lower() in {".png", ".jpg", ".mp4"}))
    check("A1 dry-run leaves no temp dir", not (tree / "_compressed" / ".compress-tmp").exists())
    check("A1 dry-run writes no ledger", not (tree / "_compressed" / "state.jsonl").exists())

    result = cli(str(tree))
    success = report(tree / "_compressed", "success.json")
    failed = report(tree / "_compressed", "failed.json")
    skipped = report(tree / "_compressed", "skipped.json")
    skip_reasons = reasons(skipped["items"])
    check("A2 real run fails only the 2 corrupt files",
          result.returncode == 1 and failed["count"] == 2
          and all(i["reason"] == "failed_probe" for i in failed["items"]),
          f"rc={result.returncode} failed={failed['count']}")
    check("A2 exits 1 when a file failed", result.returncode == 1)
    check("A2 encodes 6 files (the 7th, notsmall_noise.mp4, is discarded)", success["count"] == 6,
          f"count={success['count']}")
    for reason in ("animated", "hdr", "modern_codec", "archive", "unsupported", "junk",
                   "empty", "in_progress", "duplicate_inode", "below_threshold",
                   "too_long_path"):
        check(f"A2 skip reason {reason}", skip_reasons.get(reason, 0) >= 1,
              f"reasons={sorted(skip_reasons)}")
    check("A2 压不动的视频被丢弃（not_smaller 或 no_size_gain）",
          skip_reasons.get("not_smaller", 0) + skip_reasons.get("no_size_gain", 0) >= 1,
          f"reasons={sorted(skip_reasons)}")
    check("A2 lowq noise video was not kept",
          any(i["source"].endswith("notsmall_noise.mp4")
              and i["reason"] in ("not_smaller", "no_size_gain")
              for i in skipped["items"]))
    check("A2 originals untouched", sha(tree / "big.png") == original_big)
    check("A2 reports use relative paths",
          all(not i["source"].startswith(":") and ":" not in i["source"] for i in success["items"]))
    check("A2 output mirrors the tree", (tree / "_compressed" / "sub" / "huge.jpg").exists())

    huge = tree / "_compressed" / "sub" / "huge.jpg"
    dims = Image.open(huge).size
    check("A3 6000x4000 image was capped to 4096",
          max(dims) == 4096 and abs(dims[0] / dims[1] - 1.5) < 0.02, f"dims={dims}")
    four_k = tree / "_compressed" / "big4k.mp4"
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(four_k)], capture_output=True,
                           encoding="utf-8", errors="replace")
    check("A3 4K video was downscaled to 1440p", probe.stdout.strip() == "2560,1440",
          f"dims={probe.stdout.strip()}")
    check("A3 4K video is meaningfully smaller",
          four_k.stat().st_size < (tree / "big4k.mp4").stat().st_size * 0.95)
    log_text = (tree / "_compressed" / "run.log").read_text(encoding="utf-8")
    check("A4 run.log records the executed command lines",
          "exec caesiumclt" in log_text and "exec ffmpeg" in log_text)
    check("A4 run.log records tool versions",
          '工具版本 ffmpeg="' in log_text and "libx264" in log_text)

    encoded = {i["source"] for i in success["items"]}
    check("A4 copy-out mode keeps a ledger", (tree / "_compressed" / "state.jsonl").exists())
    check("A4 ledger records the uncompressible video as no_change",
          any(e["key"] == "notsmall_noise.mp4" and e["status"] == "no_change"
              for e in ledgers(tree / "_compressed")))

    again = cli(str(tree))
    success2 = report(tree / "_compressed", "success.json")
    skip2 = {i["source"]: i["reason"]
             for i in report(tree / "_compressed", "skipped.json")["items"]}
    check("A5 re-run does not re-encode anything",
          success2["count"] == 0
          and all(skip2.get(source) in ("already_processed", "already_compressed")
                  for source in encoded)
          and skip2.get("notsmall_noise.mp4") in ("already_processed", "already_compressed"),
          f"success={success2['count']} noise={skip2.get('notsmall_noise.mp4')}")

    # ---------------- in-place mode ----------------
    tree = fresh_work("inplace")
    originals = {rel: sha(tree / rel) for rel in
                 ("big.png", "sub/huge.jpg", "big4k.mp4", "exif.jpg", "two_audio.mp4", "subbed.mp4")}
    mtimes = {rel: (tree / rel).stat().st_mtime_ns for rel in originals}
    result = cli(str(tree), "--in-place", "--keep-originals")
    check("B1 in-place run completes", result.returncode in (0, 1), result.stderr.strip()[:200])
    success = report(tree / ".compress-state", "success.json")
    replaced_first = {item["source"] for item in success["items"]}
    check("B1 in-place replaced at least the 6 clear candidates",
          len(replaced_first) >= 6, f"count={len(replaced_first)} {sorted(replaced_first)}")
    check("B1 keeps a verified original of every replaced file",
          all((tree / "_originals" / rel).exists() and sha(tree / "_originals" / rel) == digest
              for rel, digest in originals.items()))
    check("B1 replaced files are smaller",
          all((tree / rel).stat().st_size < (tree / "_originals" / rel).stat().st_size
              for rel in originals))
    check("B1 original mtimes preserved",
          all((tree / rel).stat().st_mtime_ns == mtimes[rel] for rel in originals))
    exif = Image.open(tree / "exif.jpg").getexif()
    check("B1 EXIF DateTimeOriginal survives the swap", exif.get(36867) == "2021:07:04 12:34:56",
          f"got {exif.get(36867)}")
    check("B1 EXIF Make survives", exif.get(271) == "TestMake")
    entries = ledgers(tree)
    check("B1 ledger has a replaced entry per success",
          sum(1 for e in entries if e["status"] == "replaced") == len(replaced_first),
          f"entries={len(entries)} replaced={len(replaced_first)}")
    check("B1 no temp directory survives", not (tree / ".compress-tmp").exists())

    rerun = cli(str(tree), "--in-place", "--keep-originals")
    success = report(tree / ".compress-state", "success.json")
    skipped = report(tree / ".compress-state", "skipped.json")
    rerun_reasons = reasons(skipped["items"])
    check("B2 re-run does no work", success["count"] == 0, f"success={success['count']}")
    check("B2 已压缩文件是终态（already_compressed）",
          rerun_reasons.get("already_compressed", 0) == len(replaced_first),
          f"reasons={rerun_reasons} expected={len(replaced_first)}")
    check("B2 re-run does not touch originals",
          all(sha(tree / "_originals" / rel) == digest for rel, digest in originals.items()))

    audited = cli(str(tree), "--audit", "--in-place")
    audit = json.loads((tree / ".compress-state" / "audit.json").read_text(encoding="utf-8"))
    check("B3 audit confirms convergence", audit["counts"].get("would_compress", 0) == 0,
          f"would_compress={audit['counts'].get('would_compress')}")
    check("B3 audit exits 0", audited.returncode == 0)

    ledger_path = tree / ".compress-state" / "state.jsonl"
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write('{"key": "truncated-line"\n')
    cli(str(tree), "--audit", "--in-place")
    after = ledgers(tree)
    backups = list((tree / ".compress-state").glob("state.jsonl.bak-*"))
    check("B4 truncated ledger line is dropped and backed up",
          len(after) == len(entries) and bool(backups), f"entries={len(after)} backups={len(backups)}")

    saved_lines = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()
                   if line.strip()]
    for line in saved_lines:
        line["rules_version"] = 999
    ledger_path.write_text("\n".join(json.dumps(line) for line in saved_lines) + "\n",
                           encoding="utf-8")
    cli(str(tree), "--audit", "--in-place")
    audit = json.loads((tree / ".compress-state" / "audit.json").read_text(encoding="utf-8"))
    check("B5 stale rules_version invalidates the no_change entries",
          audit["ledger"]["stale"] >= 6 and audit["counts"].get("would_compress", 0) >= 1,
          f"stale={audit['ledger']['stale']} would={audit['counts'].get('would_compress')} "
          "(files that stayed above their threshold are reported again)")
    check("B5 版本变更不重压已压缩文件（终态）",
          audit["counts"].get("already_compressed", 0) == len(replaced_first),
          f"already_compressed={audit['counts'].get('already_compressed')} "
          f"expected={len(replaced_first)}")
    for line in saved_lines:
        line["rules_version"] = 2
    ledger_path.write_text("\n".join(json.dumps(line) for line in saved_lines) + "\n",
                           encoding="utf-8")

    # ---------------- locks, interruption, optimistic re-check ----------------
    lock_tree = fresh_work("lock")
    background = subprocess.Popen([PY, str(CLI), str(lock_tree), "--in-place", "--keep-originals"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  encoding="utf-8", errors="replace")
    time.sleep(2.0)
    second = cli(str(lock_tree), "--in-place", "--keep-originals", "--lock-timeout", "0", timeout=120)
    lock_path = lock_tree / ".compress-state" / "state.lock"
    locked_message = str(lock_path) in second.stderr      # language independent
    background.wait(timeout=1800)
    check("C1 a second concurrent run is refused", second.returncode == 2 and locked_message,
          f"rc={second.returncode} err={second.stderr.strip()[:120]}")
    check("C1 the lock file is released afterwards",
          not (lock_tree / ".compress-state" / "state.lock").exists())

    change_tree = WORK / "change"
    change_tree.mkdir()
    slow_video(change_tree / "slow.mp4", 20)
    os.utime(change_tree / "slow.mp4", (time.time() - 7200, time.time() - 7200))
    before_hash = sha(change_tree / "slow.mp4")
    worker = subprocess.Popen([PY, str(CLI), str(change_tree), "--in-place"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              encoding="utf-8", errors="replace")
    # Wait for the encode to actually start: the startup probes take a few
    # seconds, and touching the file before the scan would just look like an
    # in-progress download instead of a concurrent edit.
    change_log = change_tree / ".compress-state" / "run.log"
    deadline = time.time() + 120
    while time.time() < deadline:
        if change_log.exists() and "exec ffmpeg" in change_log.read_text(encoding="utf-8"):
            break
        time.sleep(0.2)
    os.utime(change_tree / "slow.mp4", None)          # simulate a concurrent edit
    worker.communicate(timeout=1800)
    skipped = report(change_tree / ".compress-state", "skipped.json")
    check("C2 a file changed mid-run is left alone",
          reasons(skipped["items"]).get("changed_during_run", 0) == 1
          and sha(change_tree / "slow.mp4") == before_hash,
          f"reasons={reasons(skipped['items'])}")
    check("C2 no bogus ledger entry for the changed file", not ledgers(change_tree))

    kill_tree = WORK / "kill"
    kill_tree.mkdir()
    slow_video(kill_tree / "slow.mp4", 20)
    os.utime(kill_tree / "slow.mp4", (time.time() - 7200, time.time() - 7200))
    before_hash = sha(kill_tree / "slow.mp4")
    victim = subprocess.Popen([PY, str(CLI), str(kill_tree), "--in-place"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              encoding="utf-8", errors="replace")
    time.sleep(3.0)
    victim.kill()
    victim.wait(timeout=60)
    check("D1 a hard kill leaves the original intact", sha(kill_tree / "slow.mp4") == before_hash)
    check("D1 no ledger entry claims the killed file was replaced",
          all(e.get("status") != "replaced" for e in ledgers(kill_tree)))
    stale = WORK / "stale"
    stale.mkdir()
    shutil.copy2(FIX / "small.png", stale / "small.png")
    (stale / ".compress-tmp").mkdir()
    (stale / ".compress-tmp" / "leftover.bin").write_bytes(b"x" * 32)
    cli(str(stale), "--in-place")
    check("D2 a stale temp directory is cleaned up", not (stale / ".compress-tmp").exists())

    # ---------------- E: profiles (implementation doc section 16) ----------------
    tier_sources = {"huge.jpg": FIX / "sub" / "huge.jpg", "big.png": FIX / "big.png",
                    "big4k.mp4": FIX / "big4k.mp4", "noise.mp4": FIX / "notsmall_noise.mp4"}
    tier_tree = WORK / "profiles"
    tier_tree.mkdir()
    for name, source in tier_sources.items():
        shutil.copy2(source, tier_tree / name)
        os.utime(tier_tree / name, (time.time() - 7200, time.time() - 7200))

    stats: dict[str, tuple[dict, str, Path]] = {}
    for profile in ("balanced", "small", "tiny"):
        out = WORK / f"profiles-{profile}"
        cli(str(tier_tree), "-o", str(out), "--profile", profile)
        stats[profile] = (report(out, "success.json"),
                          (out / "run.log").read_text(encoding="utf-8"), out)

    saved = {name: sum(item["saved"] for item in data["items"]) for name, (data, _, _) in stats.items()}
    check("E1 三档节省额单调递增",
          saved["balanced"] < saved["small"] < saved["tiny"],
          " / ".join(f"{k}={v / 1048576:.1f}MB" for k, v in saved.items()))

    edges = {name: max(Image.open(out / "huge.jpg").size) for name, (_, _, out) in stats.items()}
    check("E1 图片长边随档位递减（4096 / 2560 / 1920）",
          (edges["balanced"], edges["small"], edges["tiny"]) == (4096, 2560, 1920), f"{edges}")

    heights = {}
    for name, (_, _, out) in stats.items():
        probe_out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=height",
                                    "-of", "csv=p=0", str(out / "big4k.mp4")],
                                   capture_output=True, encoding="utf-8", errors="replace")
        heights[name] = probe_out.stdout.strip()
    check("E1 视频高度随档位递减（1440 / 1080 / 720）",
          (heights["balanced"], heights["small"], heights["tiny"]) == ("1440", "1080", "720"),
          f"{heights}")

    tiny_log = stats["tiny"][1]
    balanced_log = stats["balanced"][1]
    check("E1 tiny 档使用极端参数（-q 58 / -crf 30 -preset slow / zopfli / 4:2:0）",
          "-q 58" in tiny_log and "-crf 30 -preset slow" in tiny_log
          and "--zopfli" in tiny_log and "4:2:0" in tiny_log)
    check("E1 balanced 档保持原参数（-q 82 / -crf 23 -preset medium，无额外开关）",
          "-q 82" in balanced_log and "-crf 23 -preset medium" in balanced_log
          and "--zopfli" not in balanced_log)
    policies = {name: data["policy"] for name, (data, _, _) in stats.items()}
    check("E1 三档 policy 指纹互不相同，且与报告一致",
          len(set(policies.values())) == 3
          and all(data["profile"] == name for name, (data, _, _) in stats.items()),
          f"{policies}")

    # terminal state across profile switches, in place
    switch = WORK / "switch"
    switch.mkdir()
    for name, source in tier_sources.items():
        shutil.copy2(source, switch / name)
        os.utime(switch / name, (time.time() - 7200, time.time() - 7200))
    cli(str(switch), "--in-place")
    first = report(switch / ".compress-state", "success.json")
    replaced = [item["source"] for item in first["items"]]
    hashes = {rel: sha(switch / rel) for rel in replaced}
    check("E2 首次运行替换了预期文件", len(replaced) == 3 and "noise.mp4" not in replaced,
          f"replaced={replaced}")

    cli(str(switch), "--in-place", "--profile", "tiny")
    tiny_items = report(switch / ".compress-state", "skipped.json")["items"]
    tiny_skip = reasons(tiny_items)
    tiny_by_source = {item["source"]: item["reason"] for item in tiny_items}
    check("E2 换到 tiny 档不重压已压缩文件",
          tiny_skip.get("already_compressed", 0) == 3
          and all(sha(switch / rel) == hashes[rel] for rel in replaced),
          f"reasons={tiny_skip}")
    check("E2 未压缩的 no_change 文件被重新评估（走 A）",
          tiny_by_source.get("noise.mp4") not in (None, "already_processed", "in_progress"),
          f"noise.mp4 -> {tiny_by_source.get('noise.mp4')}（重新做了决策即可，丢弃或压缩都算）")

    cli(str(switch), "--in-place", "--profile", "balanced")
    back_skip = reasons(report(switch / ".compress-state", "skipped.json")["items"])
    check("E3 换回 balanced 档同样不重压、也不产生新的替换",
          report(switch / ".compress-state", "success.json")["count"] == 0
          and back_skip.get("already_compressed", 0) == 3
          and all(sha(switch / rel) == hashes[rel] for rel in replaced),
          f"reasons={back_skip}")

    touched = switch / "huge.jpg"
    older = time.time() - 7000                  # old enough for the in-progress gate, but != recorded
    os.utime(touched, (older, older))           # sync client changed only the mtime
    cli(str(switch), "--in-place")
    touch_skip = reasons(report(switch / ".compress-state", "skipped.json")["items"])
    check("E4 只改 mtime 不改内容时仍按已压缩跳过（首尾哈希兜底）",
          touch_skip.get("already_compressed", 0) == 3
          and sha(touched) == hashes["huge.jpg"], f"reasons={touch_skip}")

    # ---------------- F: hardware decode (implementation doc section 5.6) ----------------
    for name, extra in (("hwaccel-on", []), ("hwaccel-off", ["--no-hwaccel"])):
        tree = WORK / name
        tree.mkdir()
        shutil.copy2(FIX / "big4k.mp4", tree / "clip.mp4")
        os.utime(tree / "clip.mp4", (time.time() - 7200, time.time() - 7200))
        cli(str(tree), "-o", str(WORK / f"{name}-out"), *extra)

    on_item = report(WORK / "hwaccel-on-out", "success.json")["items"][0]
    off_item = report(WORK / "hwaccel-off-out", "success.json")["items"][0]
    on_log = (WORK / "hwaccel-on-out" / "run.log").read_text(encoding="utf-8")
    off_log = (WORK / "hwaccel-off-out" / "run.log").read_text(encoding="utf-8")

    check("F1 硬解探针可跑通且命令行带 -hwaccel",
          "硬件探针" in on_log and "d3d11va=True" in on_log and "-hwaccel " in on_log)
    if os.name == "nt":
        check("F1 报告记录实际使用的硬解", on_item["hwaccel"] == "d3d11va",
              f"hwaccel={on_item['hwaccel']}")
    check("F2 --no-hwaccel 不探测、不加参数、报告为空",
          off_item["hwaccel"] is None and "-hwaccel" not in off_log
          and "hwaccel=off" in off_log)
    check("F3 硬解与软解输出逐字节一致（零画质变化）",
          sha(WORK / "hwaccel-on-out" / "clip.mp4") == sha(WORK / "hwaccel-off-out" / "clip.mp4"))

    spec = importlib.util.spec_from_file_location("files_compress", CLI)
    module = importlib.util.module_from_spec(spec)
    sys.modules["files_compress"] = module      # dataclasses resolves the module by name
    spec.loader.exec_module(module)
    f4_sample = module.make_probe_sample(WORK)
    check("F4 无效硬解名被探针拒绝（回退路径的判据）",
          module.probe_hwdec("definitely-not-a-hwaccel", f4_sample, module.Logger(None))[0] is False)
    if os.name == "nt":
        check("F4 d3d11va 探针通过",
              module.probe_hwdec("d3d11va", f4_sample, module.Logger(None))[0] is True)
    sample = module.MediaInfo(width=1920, height=1080, codec="h264", format_name="mov,mp4")
    decision = module.Decision("encode")
    hardware = module.video_command(Path("in.mp4"), Path("out.mp4"), decision, sample,
                                    module.PROFILES["balanced"], "d3d11va")
    software = module.video_command(Path("in.mp4"), Path("out.mp4"), decision, sample,
                                    module.PROFILES["balanced"], "")
    check("F4 -hwaccel 是输入选项（在 -i 之前）",
          hardware.index("-hwaccel") < hardware.index("-i")
          and hardware[hardware.index("-hwaccel") + 1] == "d3d11va")
    check("F4 软解命令不含 -hwaccel", "-hwaccel" not in software)

    # ---------------- G: hardware encoding, opt-in (implementation doc section 5.7) ----------------
    for encoder in ("x264", "qsv", "qsv-hevc"):
        tree = WORK / f"enc-{encoder}"
        tree.mkdir()
        shutil.copy2(FIX / "big4k.mp4", tree / "clip.mp4")
        os.utime(tree / "clip.mp4", (time.time() - 7200, time.time() - 7200))
        cli(str(tree), "-o", str(WORK / f"enc-{encoder}-out"), "--encoder", encoder)

    enc_report = {name: report(WORK / f"enc-{name}-out", "success.json")
                  for name in ("x264", "qsv", "qsv-hevc")}
    enc_items = {name: data["items"][0] for name, data in enc_report.items()}
    enc_logs = {name: (WORK / f"enc-{name}-out" / "run.log").read_text(encoding="utf-8")
                for name in ("x264", "qsv", "qsv-hevc")}

    check("G1 三个编码器都产出了更小的文件",
          all(item["size_after"] < item["size_before"] for item in enc_items.values()),
          " / ".join(f"{n}={i['size_after']}" for n, i in enc_items.items()))
    if os.name == "nt":
        check("G1 --encoder qsv 用 h264_qsv 并按码率驱动",
              enc_items["qsv"]["encoder"] == "qsv" and "-c:v h264_qsv" in enc_logs["qsv"]
              and "-b:v " in enc_logs["qsv"] and "-pix_fmt nv12" in enc_logs["qsv"])
        check("G1 --encoder qsv-hevc 用 hevc_qsv 并加 hvc1 标签",
              enc_items["qsv-hevc"]["encoder"] == "qsv-hevc"
              and "-c:v hevc_qsv" in enc_logs["qsv-hevc"]
              and "-tag:v hvc1" in enc_logs["qsv-hevc"])
    check("G1 x264 档不出现硬件编码参数",
          "-crf 23" in enc_logs["x264"] and "-c:v h264_qsv" not in enc_logs["x264"]
          and "-c:v hevc_qsv" not in enc_logs["x264"])
    check("G2 编码器进入 policy 指纹（三者互不相同）",
          len({data["policy"] for data in enc_report.values()}) == 3
          and all(data["encoder"] == name for name, data in enc_report.items()),
          f"{ {n: d['policy'] for n, d in enc_report.items()} }")

    qsv_available = module.probe_encoder("qsv", WORK, module.Logger(None))[0]
    switch = WORK / "enc-switch"
    switch.mkdir()
    for name, source in (("compressible.mp4", FIX / "big4k.mp4"),
                         ("uncompressible.mp4", FIX / "notsmall_noise.mp4")):
        shutil.copy2(source, switch / name)
        os.utime(switch / name, (time.time() - 7200, time.time() - 7200))
    cli(str(switch), "--in-place")
    first_skip = reasons(report(switch / ".compress-state", "skipped.json")["items"])
    kept = sha(switch / "compressible.mp4")
    check("G3 x264 下压不动的文件被丢弃（not_smaller/no_size_gain）",
          first_skip.get("not_smaller", 0) + first_skip.get("no_size_gain", 0) >= 1,
          f"skipped={first_skip}")

    cli(str(switch), "--in-place", "--encoder", "qsv")
    second = {item["source"]: item
              for item in report(switch / ".compress-state", "success.json")["items"]}
    second_skip = reasons(report(switch / ".compress-state", "skipped.json")["items"])
    check("G3 换编码器不会重压已压缩文件（终态）",
          second_skip.get("already_compressed", 0) == 1
          and sha(switch / "compressible.mp4") == kept, f"reasons={second_skip}")
    if qsv_available:
        check("G3 换编码器后 no_change 文件被重新评估并按码率压小",
              "uncompressible.mp4" in second, f"success={sorted(second)} skipped={second_skip}")
    else:
        check("G3 无 QSV 时按 x264 回退且不误报",
              "uncompressible.mp4" not in second, f"skipped={second_skip}")

    # ---------------- H: no total time limit, stall watchdog, log format ----------------
    long_tree = WORK / "long-video"
    long_tree.mkdir()
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", "testsrc2=size=1920x1080:rate=30", "-t", "120", "-c:v", "libx264",
                    "-b:v", "6M", "-minrate", "6M", "-maxrate", "6M", "-bufsize", "3M",
                    "-x264-params", "nal-hrd=cbr", "-pix_fmt", "yuv420p",
                    str(long_tree / "long.mp4")], check=True)
    os.utime(long_tree / "long.mp4", (time.time() - 7200, time.time() - 7200))
    old_limit = 60 + 0.25 * 120          # what the removed formula would have allowed
    started = time.time()
    cli(str(long_tree), "-o", str(WORK / "long-out"))
    elapsed = time.time() - started
    long_report = report(WORK / "long-out", "success.json")
    # No assertion on the elapsed time: it depends on CPU load, so a slow machine
    # would fail the *test* while the product is fine.  It is reported instead.
    check("H1 3 分钟视频正常压完（不再有任何总时长上限）", long_report["count"] == 1,
          f"用时 {elapsed:.0f}s；被删掉的公式只允许 {old_limit:.0f}s")

    smoke_log = WORK / "smoke.log"
    smoke_run = module.Run(
        in_root=WORK, state_dir=WORK, temp_dir=WORK, out_root=WORK, originals_dir=None,
        profile=module.PROFILES["balanced"], policy="smoke", in_place=False, dry_run=False,
        ledger=module.Ledger(WORK / "smoke.jsonl", module.Logger(None), False, "smoke"),
        log=module.Logger(smoke_log))
    hung = [sys.executable, "-c",
            "import time,sys; print('frame=1'); sys.stdout.flush(); time.sleep(30)"]
    ticking = [sys.executable, "-c",
               "import time,sys\nfor i in range(10):\n    print('out_time_ms=%d' % (i*500000))"
               "; sys.stdout.flush(); time.sleep(0.4)"]
    quiet = [sys.executable, "-c", "import time; time.sleep(3)"]

    smoke_run.stall_timeout = 2
    started = time.time()
    stalled = False
    try:
        module.exec_ffmpeg(smoke_run, hung, "卡死用例")
    except module.ToolStalled:
        stalled = True
    check("H2 无进度的卡死进程在 N 秒后被中止",
          stalled and time.time() - started < 15, f"用时 {time.time() - started:.1f}s")

    module.exec_ffmpeg(smoke_run, ticking, "有进度用例")
    check("H3 一直在输出的慢任务不被误杀，且进度被解析",
          "完成 有进度用例" in smoke_log.read_text(encoding="utf-8")
          and "已编码" in smoke_log.read_text(encoding="utf-8"))

    smoke_run.stall_timeout = 1
    stalled = False
    try:
        module.exec_ffmpeg(smoke_run, quiet, "静默用例")
    except module.ToolStalled:
        stalled = True
    check("H4 静默进程在看门狗阈值内被中止", stalled)

    smoke_run.stall_timeout = 0
    started = time.time()
    module.exec_ffmpeg(smoke_run, quiet, "关闭看门狗用例")
    check("H4 --stall-timeout 0 完全不设时限（静默 3 秒也放行）",
          time.time() - started >= 2.9)

    spaced = WORK / "with space & paren (test)"
    spaced.mkdir()
    shutil.copy2(FIX / "big4k.mp4", spaced / "clip.mp4")
    os.utime(spaced / "clip.mp4", (time.time() - 7200, time.time() - 7200))
    cli(str(spaced), "-o", str(WORK / "spaced-out"))
    spaced_log = (WORK / "spaced-out" / "run.log").read_text(encoding="utf-8")
    check("H5 命令行日志可复制粘贴（含空格与特殊字符的路径被引号包住）",
          '"' in spaced_log and "with space & paren (test)" in spaced_log)
    check("H5 编码结束行带用时与进度", "用时" in spaced_log and "已编码" in spaced_log)
    check("H5 运行头不再出现 Python 字典字面量",
          "versions={" not in spaced_log and '工具版本 ffmpeg="' in spaced_log)

    # ---------------- I: hardware failure budget and probe diagnostics ----------------
    probe_sample = module.make_probe_sample(WORK)
    bogus_ok, bogus_reason = module.probe_hwdec("definitely-not-real", probe_sample,
                                                module.Logger(None))
    check("I1 探针失败会带回原始错误（不再只是 ok=False）",
          bogus_ok is False and len(bogus_reason) > 5, f"reason={bogus_reason!r}")

    probe_log = WORK / "probe.log"
    module.probe_hardware(WORK, module.Logger(probe_log))
    probe_text = probe_log.read_text(encoding="utf-8")
    check("I2 硬件探针一次列出四条路径",
          all(key in probe_text for key in ("d3d11va=", " qsv=", "encoder_qsv=",
                                            "encoder_qsv-hevc=")),
          next((line for line in probe_text.splitlines() if "硬件探针 " in line), "")[:150])

    hw_log = WORK / "hw.log"
    hw_run = module.Run(
        in_root=FIX, state_dir=WORK, temp_dir=WORK / "hw-tmp", out_root=WORK / "hw-out",
        originals_dir=None, profile=module.PROFILES["balanced"], policy="hw", in_place=False,
        dry_run=False, encoder="x264", hwaccel="definitely-not-real", stall_timeout=600,
        ledger=module.Ledger(WORK / "hw.jsonl", module.Logger(None), False, "hw"),
        log=module.Logger(hw_log))
    clip = FIX / "big4k.mp4"
    clip_size = clip.stat().st_size
    clip_info = module.probe(clip)
    clip_decision = module.decide_video(clip, clip_info, clip_size, False, hw_run.profile)
    states: list[tuple[int, str]] = []
    produced: list[int | None] = []
    for _ in range(module.HARDWARE_MAX_FAILURES):
        module.prepare_temp_dir(hw_run)
        produced.append(module.encode(hw_run, clip, "video", clip_info, clip_decision, clip_size))
        states.append((hw_run.hwdec_failures, hw_run.hwaccel))
    hw_text = hw_log.read_text(encoding="utf-8")
    check("I3 单个文件的硬解失败不再关闭整轮硬解",
          states[0][1] == "definitely-not-real" and states[1][1] == "definitely-not-real"
          and "第 1/3 次" in hw_text,
          f"states={states}")
    check("I3 达到失败预算后才切换，且失败文件本身仍成功（改用软解）",
          hw_run.hwdec_failures == module.HARDWARE_MAX_FAILURES and hw_run.hwaccel == ""
          and all(size and size > 0 for size in produced),
          f"failures={hw_run.hwdec_failures} hwaccel={hw_run.hwaccel!r}")

    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("failed: " + "; ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
