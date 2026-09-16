#!/usr/bin/env python3
"""将 .md 文件转换为 .html。

用法:
    convert_md2html.py 文档.md [更多.md ...]
    convert_md2html.py --standalone 文档.md      # 生成完整 HTML（含 <head>、内嵌样式）
    convert_md2html.py --toc 文档.md             # 生成带目录的 HTML
    convert_md2html.py --css style.css 文档.md   # 使用外部样式表
输出:
    与源文件同目录、同名的 .html 文件。
依赖:
    pandoc (https://pandoc.org/installing.html)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PANDOC_HINT = "下载: https://pandoc.org/installing.html"

# 默认内嵌样式：让 --standalone 输出的 HTML 开箱即用、排版可读
DEFAULT_CSS = """
body {
  max-width: 820px;
  margin: 2em auto;
  padding: 0 1em;
  font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
  line-height: 1.7;
  color: #24292f;
}
h1, h2, h3 { line-height: 1.3; margin-top: 1.6em; }
h1 { border-bottom: 1px solid #d0d7de; padding-bottom: .3em; }
h2 { border-bottom: 1px solid #eaecef; padding-bottom: .2em; }
code {
  background: #f6f8fa; padding: .15em .35em; border-radius: 4px;
  font-family: ui-monospace, Consolas, monospace; font-size: .9em;
}
pre {
  background: #f6f8fa; padding: 1em; border-radius: 6px;
  overflow-x: auto; line-height: 1.45;
}
pre code { background: none; padding: 0; }
blockquote {
  margin: 0; padding: 0 1em; color: #57606a;
  border-left: .25em solid #d0d7de;
}
table { border-collapse: collapse; margin: 1em 0; }
th, td { border: 1px solid #d0d7de; padding: .4em .8em; }
th { background: #f6f8fa; }
img { max-width: 100%; height: auto; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
"""


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


def build_pandoc_args(src: Path, dst: Path, opts: argparse.Namespace) -> list[str]:
    args = [src.name, "-o", dst.name]

    # 默认自动识别；可用 --from / --to 覆盖
    if opts.from_fmt:
        args += ["-f", opts.from_fmt]
    if opts.to_fmt:
        args += ["-t", opts.to_fmt]

    # 是否生成完整 HTML 文档
    if opts.standalone or opts.css or opts.toc or opts.highlight:
        args.append("--standalone")
    if opts.embed_css and not opts.css:
        # 用 pandoc 内置的 --embed-resources 让样式/图片内联进单文件
        pass
    if opts.toc:
        args += ["--toc", "--toc-depth", str(opts.toc_depth)]
    if opts.number_sections:
        args.append("--number-sections")
    if opts.css:
        args += ["--css", opts.css]
    if opts.highlight:
        args += ["--highlight-style", opts.highlight]
    if opts.math:
        args += ["--mathjax"] if opts.math == "mathjax" else ["--katex"]
    if opts.metadata:
        for kv in opts.metadata:
            args += ["-M", kv]
    if opts.extra:
        args += opts.extra

    return args


def convert_one(
    pandoc: str, src: Path, opts: argparse.Namespace
) -> bool:
    if src.suffix.lower() not in (".md", ".markdown"):
        print(f'[跳过] 不支持的格式 "{src.suffix}": {src}')
        return False
    if not src.is_file():
        print(f"[错误] 文件不存在: {src}", file=sys.stderr)
        return False

    dst = src.with_suffix(".html")
    args = build_pandoc_args(src, dst, opts)

    print(f"\n转换: {src}")
    print(f"  --> {dst}")

    # 若用了 --css 且未指定内嵌样式，生成一个临时 style.css 在源目录
    css_file: Path | None = None
    if opts.standalone and not opts.css:
        css_file = src.parent / f".{src.stem}.style.css"
        css_file.write_text(DEFAULT_CSS, encoding="utf-8")
        args += ["--css", css_file.name]

    try:
        proc = subprocess.run([pandoc, *args], cwd=src.parent)
    finally:
        if css_file and css_file.exists():
            css_file.unlink()

    if proc.returncode != 0:
        print(f"[失败] {src}", file=sys.stderr)
        return False

    print(f"[完成] {dst}")
    return True


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(
        prog="convert_md2html.py",
        description="将 .md 转换为 .html（基于 pandoc）",
        add_help=True,
    )
    p.add_argument("files", nargs="*", help="要转换的 .md 文件（可多个）")
    p.add_argument(
        "-s", "--standalone", action="store_true",
        help="生成完整 HTML 文档（含 <head> 和默认内嵌样式）",
    )
    p.add_argument(
        "--embed-css", action="store_true",
        help="将样式内联到 <style> 标签（配合 --standalone）",
    )
    p.add_argument(
        "--css", metavar="FILE",
        help="使用外部样式表（相对源文件目录；自动启用 --standalone）",
    )
    p.add_argument(
        "--toc", action="store_true", help="生成目录（自动启用 --standalone）",
    )
    p.add_argument(
        "--toc-depth", type=int, default=3, metavar="N",
        help="目录深度，默认 3",
    )
    p.add_argument(
        "--number-sections", action="store_true", help="章节自动编号",
    )
    p.add_argument(
        "--highlight", nargs="?", const="tango", metavar="STYLE",
        help="代码高亮主题（默认 tango；可选 pygments、kate、zenburn 等）",
    )
    p.add_argument(
        "--math", choices=["mathjax", "katex"],
        help="数学公式渲染方式（mathjax 或 katex）",
    )
    p.add_argument(
        "--from", dest="from_fmt", metavar="FMT",
        help="输入格式（默认由扩展名推断，通常 gfm）",
    )
    p.add_argument(
        "--to", dest="to_fmt", metavar="FMT",
        help="输出格式（默认 html5）",
    )
    p.add_argument(
        "-M", "--metadata", action="append", default=[], metavar="KEY=VAL",
        help="设置元数据，可多次使用，例如 -M title=报告",
    )
    p.add_argument(
        "extra", nargs=argparse.REMAINDER,
        help="传递给 pandoc 的额外参数（放在 -- 之后）",
    )
    return p.parse_known_args(argv)


def main(argv: list[str]) -> int:
    opts, _ = parse_args(argv[1:])
    files = opts.files

    if not files:
        print("用法: convert_md2html.py [选项] 文档.md [更多.md ...]")
        print("常用: --standalone 生成完整 HTML；--toc 生成目录；--css style.css 使用外部样式")
        return 1

    pandoc = find_pandoc()  # 启动时先检查依赖

    success = failed = 0
    for name in files:
        if convert_one(pandoc, Path(name), opts):
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