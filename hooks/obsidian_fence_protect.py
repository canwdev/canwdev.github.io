"""Before roamlinks: stash fenced/inline code so `[[` in shell is not a wikilink."""

from __future__ import annotations

import sys
from pathlib import Path

from mkdocs.plugins import event_priority

_HOOKS = Path(__file__).resolve().parent
if str(_HOOKS) not in sys.path:
    sys.path.insert(0, str(_HOOKS))

from _fence_protect import protect  # noqa: E402


@event_priority(110)
def on_page_markdown(markdown, *, page, **kwargs):
    return protect(markdown, page.file.src_uri)
