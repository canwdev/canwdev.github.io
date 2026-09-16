#!/usr/bin/env python3
"""将 .docx 文件转换为 .md（图片导出到同名目录，相对路径引用）。

用法:
    convert_docx2md.py 文档.docx [更多.docx ...]
输出:
    与源文件同目录、同名的 .md 文件；
    图片位于同目录下 "<文件名>_image" 或 "<文件名>" 目录中。
依赖:
    pandoc (https://pandoc.org/installing.html)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PANDOC_HINT = "下载: https://pandoc.org/installing.html"


def _setup_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass


def find_pandoc() -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print("[错误] 未找到 pandoc，请先安装并加入 PATH", file=sys.stderr)
        print(PANDOC_HINT, file=sys.stderr)
        sys.exit(1)
    return pandoc


def convert_one(pandoc: str, src: Path) -> bool:
    if src.suffix.lower() != ".docx":
        print(f'[跳过] 不支持的格式 "{src.suffix}": {src}')
        return False
    if not src.is_file():
        print(f"[错误] 文件不存在: {src}", file=sys.stderr)
        return False

    dst = src.with_suffix(".md")
    media_dir = src.stem  # 与原 bat 一致：媒体目录名 = 源文件基名
    print(f"\n转换: {src}")
    print(f"  --> {dst}")
    print(f"  图片: {src.parent / media_dir}")

    proc = subprocess.run(
        [
            pandoc,
            src.name,
            "-o",
            dst.name,
            "--wrap=none",
            f"--extract-media={media_dir}",
        ],
        cwd=src.parent,
    )
    if proc.returncode != 0:
        print(f"[失败] {src}", file=sys.stderr)
        return False

    print(f"[完成] {dst}")
    return True


def main(argv: list[str]) -> int:
    files = argv[1:]
    if not files:
        print("用法: convert_docx2md.py 文档.docx [更多.docx ...]")
        print("输出: 与源文件同目录下生成同名 .md")
        print("图片: 同目录下 <文件名> 目录（相对路径引用）")
        return 1

    pandoc = find_pandoc()  # 启动时先检查依赖

    success = failed = 0
    for name in files:
        if convert_one(pandoc, Path(name)):
            success += 1
        else:
            failed += 1

    if failed:
        print("\n" + "=" * 40)
        print(f"成功: {success}  失败: {failed}")
        print("=" * 40)
        return 1
    return 0


if __name__ == "__main__":
    _setup_console()
    sys.exit(main(sys.argv))