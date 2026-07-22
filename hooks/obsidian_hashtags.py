"""
Obsidian-style hashtags for MkDocs Material.

1. ATX headings require a space after `#` (`# Heading`), so `#tag` is not an H1.
2. Inline `#hashtag` outside code/links are merged into page meta `tags`
   for the Material tags plugin (runs earlier than tags' on_page_markdown).
3. Inline hashtags are rendered as Material `.md-tag` chips linking to the tags index.
"""

from __future__ import annotations

import html
import re
from typing import TYPE_CHECKING

from markdown.blockprocessors import HashHeaderProcessor
from markdown.extensions import Extension
from mkdocs.plugins import event_priority
from mkdocs.utils import get_relative_url
from pymdownx.slugs import slugify as pymdownx_slugify

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

# Obsidian tag: #name, #name/sub — no space after #; start with a letter (incl. CJK)
_TAG_RE = re.compile(
    r"(?<![`\w/])#(?P<tag>[^\W\d_](?:[\w\u4e00-\u9fff]|/(?=[^\W\d_]))*)",
    re.UNICODE,
)

_FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
_TILDE_FENCE_RE = re.compile(r"^~~~.*?^~~~", re.MULTILINE | re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]+`")
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_URL_RE = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)
_FRONTMATTER_RE = re.compile(r"^---\r?\n.*?\r?\n---\r?\n", re.DOTALL)

# Regions that must not be rewritten when styling hashtags
_PROTECTED_RE = re.compile(
    r"(?P<fence>^```.*?^```)"
    r"|(?P<tilde>^~~~.*?^~~~)"
    r"|(?P<inline>`[^`]+`)"
    r"|(?P<link>\[[^\]]*\]\([^)]*\))"
    r"|(?P<wiki>\[\[[^\]]+\]])"
    r"|(?P<url>https?://[^\s)>\]]+)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)

_SLUGIFY = pymdownx_slugify(case="lower")
_ATX_HEADING_RE = re.compile(r"(?m)^#{1,6} ")


class StrictHashHeaderProcessor(HashHeaderProcessor):
    """CommonMark / Obsidian: `# Heading` is a heading; `#tag` is not."""

    RE = re.compile(
        r"(?:^|\n)(?P<level>#{1,6}) (?P<header>(?:\\.|[^\\])*?)#*(?:\n|$)"
    )


class StrictHashHeaderExtension(Extension):
    def extendMarkdown(self, md) -> None:  # noqa: N802
        md.parser.blockprocessors.deregister("hashheader")
        md.parser.blockprocessors.register(
            StrictHashHeaderProcessor(md.parser),
            "hashheader",
            70,
        )


def _strip_non_tag_regions(markdown: str) -> str:
    text = _FRONTMATTER_RE.sub("", markdown)
    text = _FENCE_RE.sub("", text)
    text = _TILDE_FENCE_RE.sub("", text)
    text = _INLINE_CODE_RE.sub("", text)
    text = _MD_LINK_RE.sub(r"\1", text)
    text = _WIKILINK_RE.sub(r"\1", text)
    text = _URL_RE.sub("", text)
    return text


def extract_hashtags(markdown: str) -> list[str]:
    text = _strip_non_tag_regions(markdown)
    tags: list[str] = []
    seen: set[str] = set()
    for match in _TAG_RE.finditer(text):
        tag = match.group("tag").rstrip("/")
        if not tag or tag.endswith("/"):
            continue
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        tags.append(tag)
    return tags


def _tag_anchor(tag: str) -> str:
    """Match Material tags plugin default: tags_slugify_format = tag:{slug}."""
    return f"tag:{_SLUGIFY(tag, '-')}"


def _style_tag_html(tag: str, tags_href: str | None) -> str:
    label = html.escape(tag)
    if tags_href is None:
        return f'<span class="md-tag">{label}</span>'
    href = html.escape(f"{tags_href}#{_tag_anchor(tag)}", quote=True)
    return f'<a href="{href}" class="md-tag">{label}</a>'


def style_hashtags(markdown: str, tags_href: str | None) -> str:
    """Replace inline #tags with Material md-tag chips (skip code/links)."""
    fm = _FRONTMATTER_RE.match(markdown)
    if fm:
        prefix = fm.group(0)
        body = markdown[fm.end() :]
    else:
        prefix = ""
        body = markdown

    def replace_text(text: str) -> str:
        def repl(match: re.Match[str]) -> str:
            tag = match.group("tag").rstrip("/")
            if not tag:
                return match.group(0)
            return _style_tag_html(tag, tags_href)

        return _TAG_RE.sub(repl, text)

    parts: list[str] = []
    last = 0
    for match in _PROTECTED_RE.finditer(body):
        parts.append(replace_text(body[last : match.start()]))
        parts.append(match.group(0))
        last = match.end()
    parts.append(replace_text(body[last:]))
    return prefix + "".join(parts)


def _tags_index_href(page: Page, files: Files, config: MkDocsConfig) -> str | None:
    tags_path = "tags.md"
    tags_plugin = config.plugins.get("tags")
    if tags_plugin is not None:
        configured = getattr(tags_plugin.config, "tags_file", None)
        if configured:
            tags_path = configured

    tags_file = files.get_file_from_path(tags_path)
    if tags_file is None:
        return None
    return get_relative_url(tags_file.url, page.url)


def _merge_tags(page: Page, hashtags: list[str]) -> None:
    if not hashtags:
        return

    existing = page.meta.get("tags")
    if existing is None:
        merged: list[str] = []
    elif isinstance(existing, str):
        merged = [existing]
    else:
        merged = list(existing)

    seen = {str(t).casefold() for t in merged}
    for tag in hashtags:
        key = tag.casefold()
        if key not in seen:
            merged.append(tag)
            seen.add(key)

    page.meta["tags"] = merged


def on_config(config: MkDocsConfig) -> MkDocsConfig:
    config.markdown_extensions.append(StrictHashHeaderExtension())
    return config


def _ensure_filename_title(page: Page, markdown: str) -> None:
    """Use the file stem as title when there is no meta title and no ATX heading."""
    if "title" in page.meta:
        return
    # Ignore fenced/inline code — shell comments like `# apt install` are not titles
    body = _strip_non_tag_regions(markdown)
    if _ATX_HEADING_RE.search(body):
        return
    page.meta["title"] = page.file.name


@event_priority(50)
def on_page_markdown(
    markdown: str,
    *,
    page: Page,
    config: MkDocsConfig,
    files: Files,
) -> str:
    _merge_tags(page, extract_hashtags(markdown))
    _ensure_filename_title(page, markdown)
    return style_hashtags(markdown, _tags_index_href(page, files, config))
