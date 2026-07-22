"""
Obsidian-style global attachment lookup for MkDocs.

Resolves bare / wrong-relative image paths by filename anywhere under docs/
(unique basename match), similar to Obsidian's attachment resolution.

Handles:
  ![alt](disk2vhd.webp)     → ![alt](assets/.../disk2vhd.webp)
  ![[netconfig.webp]]       → ![netconfig.webp](../assets/netconfig.webp)
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from mkdocs.plugins import event_priority
from mkdocs.utils import get_relative_url

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import File, Files
    from mkdocs.structure.pages import Page

log = logging.getLogger("mkdocs.hooks.obsidian_attachments")

_IMAGE_SUFFIXES = {
    ".webp",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".bmp",
    ".ico",
    ".avif",
}

# ![alt](path) or ![alt](path "title") / ![alt](<path>)
_MD_IMG_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\("
    r"(?P<lt><)?"
    r"(?P<path>[^)\s>]+)"
    r"(?P<gt>>)?"
    r"(?P<title>\s+(?:\"[^\"]*\"|'[^']*'))?"
    r"\)"
)

# ![[file|alias|WxH]] / ![[file|300]] — Obsidian image embed
_WIKI_EMBED_RE = re.compile(
    r"!\[\[(?P<target>[^\]|#]+?)(?P<title>#[^\]|]+)?(?P<meta>(?:\|[^\]]*)?)\]\]"
)

# basename(lower) → list[File]
_index: dict[str, list[File]] = {}


def on_files(files: Files, config: MkDocsConfig) -> Files:
    global _index
    by_name: dict[str, list[File]] = defaultdict(list)
    for f in files:
        suffix = Path(f.src_uri).suffix.lower()
        if suffix not in _IMAGE_SUFFIXES:
            continue
        by_name[Path(f.src_uri).name.lower()].append(f)
    _index = dict(by_name)
    return files


def _is_remote(path: str) -> bool:
    return path.startswith(("http://", "https://", "data:", "//"))


def _path_exists_for_page(page: Page, path: str, docs_dir: Path) -> bool:
    raw = path.split("#", 1)[0]
    candidate = (Path(page.file.abs_src_path).parent / raw).resolve()
    try:
        candidate.relative_to(docs_dir.resolve())
    except ValueError:
        return False
    return candidate.is_file()


def _pick_file(name: str, page: Page) -> File | None:
    cands = _index.get(name.lower())
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]

    # Prefer attachment closest to the page (fewest path parts after common prefix)
    page_parts = PurePosixPath(page.file.src_uri).parts[:-1]

    def score(f: File) -> tuple[int, int, str]:
        parts = PurePosixPath(f.src_uri).parts[:-1]
        common = 0
        for a, b in zip(page_parts, parts):
            if a != b:
                break
            common += 1
        distance = (len(page_parts) - common) + (len(parts) - common)
        return (distance, len(parts), f.src_uri)

    cands_sorted = sorted(cands, key=score)
    chosen = cands_sorted[0]
    others = ", ".join(c.src_uri for c in cands_sorted[1:3])
    log.warning(
        "Ambiguous attachment %r on %s; using %s (also: %s)",
        name,
        page.file.src_uri,
        chosen.src_uri,
        others,
    )
    return chosen


def _href_for(page: Page, target: File) -> str:
    return get_relative_url(target.src_uri, page.file.src_uri)


def _resolve_name(page: Page, path: str) -> str | None:
    name = Path(path.split("#", 1)[0]).name
    if not name or Path(name).suffix.lower() not in _IMAGE_SUFFIXES:
        return None
    found = _pick_file(name, page)
    if found is None:
        return None
    return _href_for(page, found)


def _rewrite_md_image(match: re.Match[str], page: Page, docs_dir: Path) -> str:
    path = match.group("path")
    if _is_remote(path):
        return match.group(0)
    if _path_exists_for_page(page, path, docs_dir):
        return match.group(0)

    resolved = _resolve_name(page, path)
    if resolved is None:
        return match.group(0)

    alt = match.group("alt")
    title = match.group("title") or ""
    # Quote paths with spaces for Markdown
    if re.search(r"[\s()]", resolved):
        return f"![{alt}](<{resolved}>{title})"
    return f"![{alt}]({resolved}{title})"


def _rewrite_wiki_embed(match: re.Match[str], page: Page) -> str:
    target = match.group("target").strip()
    if not target or _is_remote(target):
        return match.group(0)

    name = Path(target).name
    if Path(name).suffix.lower() not in _IMAGE_SUFFIXES:
        # Not an image embed — leave for roamlinks / wikilinks
        return match.group(0)

    # Prefer exact path if given and exists relative to page
    page_dir = Path(page.file.abs_src_path).parent
    if "/" in target.replace("\\", "/"):
        direct = (page_dir / target).resolve()
        if direct.is_file():
            href = Path(direct.relative_to(page_dir)).as_posix()
            return f"![{name}]({href})" if " " not in href else f"![{name}](<{href}>)"

    resolved = _resolve_name(page, name)
    if resolved is None:
        log.warning(
            "Obsidian embed not found: ![[%s]] on %s",
            target,
            page.file.src_uri,
        )
        return match.group(0)

    alt = Path(name).stem
    if re.search(r"[\s()]", resolved):
        return f"![{alt}](<{resolved}>)"
    return f"![{alt}]({resolved})"


@event_priority(100)
def on_page_markdown(
    markdown: str,
    *,
    page: Page,
    config: MkDocsConfig,
    files: Files,
) -> str:
    docs_dir = Path(config.docs_dir)

    def md_repl(m: re.Match[str]) -> str:
        return _rewrite_md_image(m, page, docs_dir)

    def wiki_repl(m: re.Match[str]) -> str:
        return _rewrite_wiki_embed(m, page)

    # Wiki embeds first so roamlinks won't turn ![[img]] into a text link
    markdown = _WIKI_EMBED_RE.sub(wiki_repl, markdown)
    markdown = _MD_IMG_RE.sub(md_repl, markdown)
    return markdown
