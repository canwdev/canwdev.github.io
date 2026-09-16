#!/usr/bin/env python3
"""脚本管理工具：为同目录脚本生成 .cmd 包装、列出可用命令、打开所在文件夹。

命令:
    scripts-mgr.shim   生成 .cmd 包装（仅 Windows；已存在默认跳过，加 -f 强制覆盖）
    scripts-mgr.ls     列出当前可用的命令
    scripts-mgr.open   在文件管理器中打开脚本所在目录
    scripts-mgr.help   显示帮助

支持的脚本类型: .py  .mjs  .js  .cjs  .ps1
生成物与源脚本同目录，命名规则为 "<脚本名>.cmd"（例: convert-docx2md.py -> convert-docx2md.cmd）。
本脚本也会为自己生成包装（scripts-mgr.cmd）。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent

INTERP = {
    ".py":  'python "%~dp0{rel}" %*',
    ".mjs": 'node "%~dp0{rel}" %*',
    ".js":  'node "%~dp0{rel}" %*',
    ".cjs": 'node "%~dp0{rel}" %*',
    ".ps1": 'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0{rel}" %*',
}

NATIVE_EXEC = {".bat", ".cmd"}  # Windows 原生可执行，无需生成 shim

USAGE = """脚本管理工具

用法: scripts-mgr <命令>

命令:
  shim [-f]  为同目录下的脚本生成 .cmd 包装（仅 Windows；已存在默认跳过，-f 强制覆盖）
  ls         列出当前可用的命令
  open       在文件管理器中打开脚本所在目录
  help       显示本帮助

支持的脚本类型: .py  .mjs  .js  .cjs  .ps1
包装命名: <脚本名>.cmd（例: convert-docx2md.py -> convert-docx2md.cmd）
注意: .bat/.cmd 为 Windows 原生可执行，无需生成包装。
"""


def _setup_console() -> None:
    """Windows 控制台尽量使用 UTF-8，避免中文乱码。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass


def iter_scripts() -> list[Path]:
    """返回目录下受支持的源脚本（已排序）。"""
    scripts = [
        p
        for p in DIR.iterdir()
        if p.is_file() and p.suffix.lower() in INTERP
    ]
    return sorted(scripts, key=lambda p: p.stem.lower())


def iter_native() -> list[Path]:
    """返回目录下的 Windows 原生可执行文件（.bat/.cmd），已排序。"""
    natives = [
        p
        for p in DIR.iterdir()
        if p.is_file() and p.suffix.lower() in NATIVE_EXEC
    ]
    return sorted(natives, key=lambda p: p.stem.lower())


def find_conflicts(scripts: list[Path]) -> dict[str, list[Path]]:
    """找出包装名互相冲突的脚本（同名不同扩展，如 foo.js 与 foo.cjs）。"""
    by_stem: dict[str, list[Path]] = {}
    for script in scripts:
        by_stem.setdefault(script.stem.lower(), []).append(script)
    return {stem: group for stem, group in by_stem.items() if len(group) > 1}


def shim_path(script: Path) -> Path:
    """源脚本对应的包装路径：同目录、同名、.cmd 后缀。"""
    return DIR / f"{script.stem}.cmd"


def shim_content(script: Path) -> str:
    """包装应有的内容。用默认编码写入: cmd.exe 读到 UTF-8 BOM 会在首行留乱码。"""
    return "@echo off\n" + INTERP[script.suffix.lower()].format(rel=script.name) + "\n"


def cmd_shim(force: bool = False) -> int:
    """为每个受支持的脚本生成 .cmd 包装；已存在且未指定 -f 时直接跳过。"""
    scripts = iter_scripts()
    if not scripts:
        print(f"[提示] 没有可生成包装的脚本: {DIR}")
        return 0

    conflicts = find_conflicts(scripts)
    conflicted = {p for group in conflicts.values() for p in group}

    for stem, group in sorted(conflicts.items()):
        names = ", ".join(p.name for p in group)
        print(f"[跳过] 包装名冲突 {{{stem}.cmd}}: {names}", file=sys.stderr)

    generated: list[Path] = []
    overwritten: list[Path] = []
    skipped: list[Path] = []
    conflict_skipped = len(conflicted)

    for script in scripts:
        if script in conflicted:
            continue

        shim = shim_path(script)
        existed = shim.exists()

        if existed and not force:
            skipped.append(shim)
            continue

        # 检查是否有同名 .bat 可能遮蔽 .cmd
        bat = DIR / f"{script.stem}.bat"
        if bat.exists():
            print(f"[警告] 存在同名 {bat.name}，生成的 {shim.name} 可能被其遮蔽", file=sys.stderr)

        shim.write_text(shim_content(script))
        if existed:
            overwritten.append(shim)
        else:
            generated.append(shim)

    for shim in generated:
        print(f"生成: {shim}")
    for shim in overwritten:
        print(f"覆盖: {shim}")
    for shim in skipped:
        print(f"跳过: {shim} (已存在)")

    print(
        f"\n完成: 生成 {len(generated)} 个, 覆盖 {len(overwritten)} 个, "
        f"跳过 {len(skipped) + conflict_skipped} 个 ({DIR})"
    )
    return 0


def cmd_ls() -> int:
    """列出当前可用的命令及其源脚本。"""
    scripts = iter_scripts()
    natives = iter_native() if os.name == "nt" else []

    if not scripts and not natives:
        print(f"[提示] 没有可用的脚本: {DIR}")
        return 0

    conflicts = find_conflicts(scripts)
    rows = []

    # 处理需要 shim 的脚本
    for script in scripts:
        name = script.stem
        if name.lower() in conflicts:
            status = "冲突"
        elif shim_path(script).exists():
            status = "已存在"
        else:
            status = "未生成"
        rows.append((name, script.name, status))

    # 处理原生可执行
    for native in natives:
        rows.append((native.stem, native.name, "原生可执行"))

    # 排序：按名称
    rows.sort(key=lambda r: r[0].lower())

    w_name = max(len(r[0]) for r in rows)
    w_file = max(len(r[1]) for r in rows)
    w_status = max(len(r[2]) for r in rows)

    print(f"可用命令 ({len(rows)} 个) — {DIR}\n")
    for name, filename, status in rows:
        print(f"  {name.ljust(w_name)}  {filename.ljust(w_file)}  {status.ljust(w_status)}")

    for stem, group in sorted(conflicts.items()):
        names = ", ".join(p.name for p in group)
        print(f"\n[注意] {{{stem}.cmd}} 名冲突: {names}", file=sys.stderr)
    return 0


def cmd_open() -> int:
    """在系统文件管理器中打开脚本所在目录。"""
    if not DIR.is_dir():
        print(f"[错误] 目录不存在: {DIR}", file=sys.stderr)
        return 1

    try:
        if os.name == "nt":
            os.startfile(DIR)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(DIR)], check=True)
        else:
            subprocess.run(["xdg-open", str(DIR)], check=True)
    except OSError as exc:
        print(f"[错误] 无法打开目录: {exc}", file=sys.stderr)
        return 1

    print(f"已打开: {DIR}")
    return 0


def cmd_help() -> int:
    print(USAGE, end="")
    return 0


COMMANDS = {
    "shim": cmd_shim,
    "ls": cmd_ls,
    "open": cmd_open,
    "help": cmd_help,
    "-h": cmd_help,
    "--help": cmd_help,
}


def main(argv: list[str]) -> int:
    args = argv[1:]

    if not args:
        print(USAGE, end="")
        return 1

    command = args[0]
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"[错误] 未知命令: {command}\n", file=sys.stderr)
        print(USAGE, end="", file=sys.stderr)
        return 1

    rest = args[1:]
    if command == "shim":
        if os.name != "nt":
            print("[错误] 生成 .cmd 包装仅支持 Windows", file=sys.stderr)
            return 1
        unknown = [a for a in rest if a not in ("-f", "--force")]
        if unknown:
            print(f"[错误] shim 不支持参数: {' '.join(unknown)}", file=sys.stderr)
            return 1
        return cmd_shim(force=any(a in ("-f", "--force") for a in rest))

    if rest:
        print(f"[错误] {command} 不接受参数: {' '.join(rest)}", file=sys.stderr)
        return 1

    return handler()


if __name__ == "__main__":
    _setup_console()
    sys.exit(main(sys.argv))