#!/usr/bin/env python3
"""将 .docx 文件转换为 .html。

用法:
    convert_docx2html.py 文档.docx [更多.docx ...]
输出:
    与源文件同目录、同名的 .html 文件。
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
    """Windows 控制台尽量使用 UTF-8，避免中文乱码（等价于 chcp 65001）。"""
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

    dst = src.with_suffix(".html")
    print(f"\n转换: {src}")
    print(f"  --> {dst}")

    # 在源文件所在目录执行，保持与原 bat 相同的相对路径语义
    proc = subprocess.run(
        [pandoc, src.name, "-o", dst.name],
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
        print("用法: convert_docx2html.py 文档.docx [更多.docx ...]")
        print("输出: 与源文件同目录下生成同名 .html")
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