"""Shared state: shield `[[...]]` inside fenced/inline code from roamlinks."""

from __future__ import annotations

import re
from typing import Callable

_FENCE_RE = re.compile(r"(^```.*?^```)|(^~~~.*?^~~~)", re.MULTILINE | re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`+[^`]+`+")

# page.src_uri → list of original code snippets
_store: dict[str, list[str]] = {}

_TOKEN = "FAKESECRET_c2d3e4f5g6h7i8j9k0l1"


def protect(markdown: str, key: str) -> str:
    chunks: list[str] = []

    def stash(text: str) -> str:
        idx = len(chunks)
        chunks.append(text)
        # Whole fence replaced by token — roamlinks never sees `[[` inside
        return f"{_TOKEN}{idx}<<<"

    def repl_fence(m: re.Match[str]) -> str:
        return stash(m.group(0))

    out = _FENCE_RE.sub(repl_fence, markdown)

    def repl_inline(m: re.Match[str]) -> str:
        return stash(m.group(0))

    out = _INLINE_CODE_RE.sub(repl_inline, out)
    _store[key] = chunks
    return out


def restore(markdown: str, key: str) -> str:
    chunks = _store.pop(key, None)
    if not chunks:
        return markdown

    def repl(m: re.Match[str]) -> str:
        idx = int(m.group(1))
        return chunks[idx]

    return re.sub(
        re.escape(_TOKEN) + r"(\d+)<<<",
        repl,
        markdown,
    )


def make_handlers(
    priority_before: int,
    priority_after: int,
) -> tuple[Callable, Callable]:
    from mkdocs.plugins import event_priority

    @event_priority(priority_before)
    def before(markdown, *, page, **kwargs):
        return protect(markdown, page.file.src_uri)

    @event_priority(priority_after)
    def after(markdown, *, page, **kwargs):
        return restore(markdown, page.file.src_uri)

    return before, after
