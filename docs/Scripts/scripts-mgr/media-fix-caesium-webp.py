#!/usr/bin/env python3
"""修复 caesiumclt 生成的"浏览器打不开"的 webp：把 ICCP chunk 挪到 ALPH 之前。

用法:
    media-fix-caesium-webp <文件或目录>

目录会递归扫描全部 *.webp。命中的文件**原地**修复（同目录临时文件 + os.replace 原子
替换，路径不变，mtime/atime 沿用原值），其余文件一个字节都不动。不写日志、不留备份、
不生成副本。

本模块同时是"修复逻辑"的唯一实现：media-compress.py 按路径导入它、在每次压缩成功
之后调用 repair_file() 自检自己刚写出的产物。修法只在这里有一份，改规则只改这里。

------------------------------------------------------------------------------
技术细节（README 里不展开，只留在这里，免得用户被 WebP 容器格式缠住）
------------------------------------------------------------------------------
病灶（**实测版本 caesiumclt 1.5.0**，更高版本未验证）：caesiumclt 处理"带 ICC 色彩
配置、且带非不透明 alpha"的源图时，写出的 chunk 顺序是

    VP8X -> ALPH -> ICCP -> VP8

而 WebP 容器规范要求 `VP8X -> ICCP -> ALPH -> VP8`。libwebp 在**解析头部**阶段就拒绝
这种顺序（`WebPGetFeatures` 失败），于是 Chrome / Edge / Safari / Pillow 一律打不开
（Pillow 报 "could not create decoder object"），而 ffmpeg 用自己的解码器、不校验
chunk 顺序，照样能解——坏文件因此极难被发现。带 ICC 但没有 alpha 的源顺序是对的，
所以只有扫描件、透明 PNG 这类会中招。caesiumclt 也没有对应开关（`--strip-icc` 只对
JPG 生效）。

修复只做两件事：把 ICCP 插到 VP8X 之后、ALPH 之前；补上 VP8X 的 ICC 标志位（0x20，
caesium 在带 alpha 时把它漏掉了）。chunk 重排不改变总字节数，像素数据不动。顺序本来
就对、或根本没有 ICCP/ALPH 的文件原样放过，所以可以反复跑（幂等）。若上游哪天真把
bug 修好了，这一步对正确文件就是空操作。

结构上真有问题的文件（RIFF 长度不符、chunk 越界、没有 VP8/VP8L、VP8X 不是 10 字节、
尾部有垃圾）只报告、不猜着改——那种文件里没有任何依据能判断"应该"是什么样。

退出码: 0 全部正常或已修复；1 存在无法修复/写入失败的文件；2 参数错误。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

WEBP_ICC_FLAG = 0x20          # VP8X 的 ICC 标志位
IMAGE_CHUNKS = (b"VP8 ", b"VP8L")


def setup_console() -> None:
    """Windows 控制台尽量用 UTF-8，避免中文路径打印成乱码。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError, ValueError):
            pass


def read_chunks(data: bytes) -> tuple[list[list] | None, str]:
    """拆出 (chunks, 错误说明)。错误说明非空 = 结构上不可处理，调用方只管报告。"""
    if len(data) < 12:
        return None, "file is shorter than a RIFF header"
    if data[:4] != b"RIFF":
        return None, "not a RIFF container"
    if data[8:12] != b"WEBP":
        return None, f"RIFF form type is {data[8:12]!r}, not 'WEBP'"
    declared = int.from_bytes(data[4:8], "little")
    actual = len(data) - 8
    if declared != actual:
        # 截断（declared > actual）或尾巴上有垃圾（declared < actual）都不猜，直接报告。
        return None, f"RIFF size field says {declared} bytes, file contains {actual}"
    chunks: list[list] = []
    offset = 12
    while offset + 8 <= len(data):
        fourcc = data[offset:offset + 4]
        size = int.from_bytes(data[offset + 4:offset + 8], "little")
        if offset + 8 + size > len(data):
            return None, (f"chunk {fourcc!r} declares {size} bytes but only "
                          f"{len(data) - offset - 8} remain")
        chunks.append([fourcc, data[offset + 8:offset + 8 + size]])
        offset += 8 + size + (size & 1)       # 奇数长度的 chunk 后面有一个对齐字节
    if offset != len(data):
        return None, f"{len(data) - offset} unexpected trailing byte(s)"
    if not any(fourcc in IMAGE_CHUNKS for fourcc, _ in chunks):
        return None, "no VP8/VP8L image chunk"
    vp8x = next((c for c in chunks if c[0] == b"VP8X"), None)
    if vp8x is not None and len(vp8x[1]) != 10:
        return None, f"VP8X payload is {len(vp8x[1])} bytes, expected 10"
    return chunks, ""


def rebuild(chunks: list[list]) -> bytes:
    """按当前顺序拼回 RIFF；偶数化填充一并重算，总长度与重排前相同。"""
    body = b""
    for fourcc, payload in chunks:
        body += fourcc + len(payload).to_bytes(4, "little") + payload
        if len(payload) & 1:
            body += b"\x00"
    return b"RIFF" + (4 + len(body)).to_bytes(4, "little") + b"WEBP" + body


def chunk_order(chunks: list[list]) -> str:
    return " ".join(fourcc.decode("latin1").strip() or "?" for fourcc, _ in chunks)


def repair_bytes(data: bytes) -> tuple[str, str, bytes | None]:
    """返回 (状态, 说明, 新字节)。状态: fixed / clean / bad。

    只有"ICCP 排在 ALPH 之后"这一种情况会被改写（外加顺手置 ICC 标志位）。其余一律
    clean——包括顺序本来就对的文件，所以重复运行不会产生任何写入。
    """
    chunks, error = read_chunks(data)
    if chunks is None:
        return "bad", error, None
    names = [fourcc for fourcc, _ in chunks]
    if b"ICCP" not in names or b"ALPH" not in names:
        return "clean", "", None
    if names.index(b"ICCP") < names.index(b"ALPH"):
        return "clean", "", None
    before = chunk_order(chunks)
    iccp = chunks.pop(names.index(b"ICCP"))
    vp8x = next((c for c in chunks if c[0] == b"VP8X"), None)
    if vp8x is not None:                     # 规范: 有 ICCP 就该置 ICC 标志位
        vp8x[1] = bytes([vp8x[1][0] | WEBP_ICC_FLAG]) + vp8x[1][1:]
    chunks.insert(chunks.index(vp8x) + 1 if vp8x is not None else 0, iccp)
    out = rebuild(chunks)
    if out == data:                          # 理论上不会走到，留着当护栏
        return "clean", "", None
    return "fixed", f"{before} -> {chunk_order(chunks)}", out


def write_in_place(path: Path, data: bytes) -> str:
    """同目录写临时文件再原子替换；顺便把 mtime/atime 还原成改之前的值。

    直接 write_bytes 到原文件的话，半路崩掉就是一个截断的 webp——比坏 chunk 顺序更糟。
    临时名带 pid，两个实例同时跑不会互相踩；它不以 .webp 结尾，扫描时也不会被当成输入。
    """
    stat = path.stat()
    temp = path.with_name(f"{path.name}.{os.getpid()}.fixing")
    try:
        temp.write_bytes(data)
        os.utime(temp, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        os.replace(temp, path)
    except OSError as exc:
        return str(exc)
    finally:
        temp.unlink(missing_ok=True)
    return ""


def repair_file(path: Path) -> tuple[str, str]:
    """读入、判断、必要时原地写回。返回 (状态, 说明)。

    状态: fixed / clean / bad / failed。这是唯一的文件级入口——CLI 和 media-compress.py
    都调它，所以"什么算坏、怎么修、怎么判定"不会出现两套说法。
    非 .webp 后缀直接 clean，连读都不读（主脚本的 png/jpeg 产物走的就是这条快速路）。
    """
    if path.suffix.lower() != ".webp":
        return "clean", ""
    try:
        data = path.read_bytes()
    except OSError as exc:
        return "failed", f"cannot read: {exc}"
    status, note, out = repair_bytes(data)
    if status != "fixed":
        return status, note
    error = write_in_place(path, out)
    return ("fixed", note) if not error else ("failed", f"cannot write: {error}")


def collect(paths: list[Path]) -> list[Path]:
    """展开输入为待检查的 *.webp 列表；后缀大小写不敏感（Windows 上很常见 .WEBP）。"""
    found: list[Path] = []
    for path in paths:
        if path.is_file():
            found.append(path)
        elif path.is_dir():
            found.extend(p for p in path.rglob("*")
                         if p.is_file() and p.suffix.lower() == ".webp")
        else:
            continue
    return sorted(found)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="media-fix-caesium-webp", add_help=True,
        description="Repair the ICCP/ALPH chunk order that makes caesiumclt's webp "
                    "unreadable in browsers; files are fixed in place, nothing else "
                    "is touched.")
    parser.add_argument("path", help="a .webp file, or a directory scanned recursively")
    args = parser.parse_args(argv[1:])

    target = Path(args.path).expanduser()
    if not target.exists():
        print(f"[ERROR] path not found: {target}", file=sys.stderr, flush=True)
        return 2
    target = target.resolve()
    if target.is_file() and target.suffix.lower() != ".webp":
        print(f"[ERROR] not a .webp file: {target}", file=sys.stderr, flush=True)
        return 2

    files = collect([target])
    print(f"media-fix-caesium-webp: scanning {target}  ({len(files)} webp file(s))",
          flush=True)

    fixed = clean = bad = failed = 0
    for path in files:
        status, note = repair_file(path)
        if status == "clean":
            clean += 1
        elif status == "fixed":
            fixed += 1
            print(f"[FIXED] {path}  {note}", flush=True)
        elif status == "bad":
            bad += 1
            print(f"[BAD]   {path}  {note}", file=sys.stderr, flush=True)
        else:
            failed += 1
            print(f"[FAIL]  {path}  {note}", file=sys.stderr, flush=True)

    print(f"done: {len(files)} scanned  {fixed} fixed  {clean} already fine  "
          f"{bad} structurally bad  {failed} failed", flush=True)
    return 1 if (bad or failed) else 0


if __name__ == "__main__":
    setup_console()
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print("interrupted.", file=sys.stderr)
        sys.exit(130)
