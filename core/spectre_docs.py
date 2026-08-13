# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/spectre_docs.py — Documentation loader.

Loads all offline Wiki markdown files from assets/docs/wiki/.
Provides `get_wiki_pages()` for UI rendering and `get_full_documentation()`
for the AI context.
"""

from __future__ import annotations
import os
from pathlib import Path

WIKI_DIR = Path(__file__).parent.parent / "assets" / "docs" / "wiki"

def get_wiki_pages() -> dict[str, str]:
    """Returns a dictionary mapping filename (without .md) to markdown content."""
    pages = {}
    if WIKI_DIR.exists():
        # Sort files so they appear in a consistent order in the UI
        for file in sorted(WIKI_DIR.glob("*.md")):
            try:
                pages[file.stem] = file.read_text(encoding="utf-8")
            except OSError:
                pass
    return pages

def get_full_documentation() -> str:
    """Concatenates all wiki pages for the AI RAG context."""
    pages = get_wiki_pages()
    if not pages:
        return "No offline documentation found."
        
    content = []
    for title, text in pages.items():
        content.append(f"--- [WIKI PAGE: {title}] ---")
        content.append(text)
        content.append("\n")
        
    return "\n".join(content)

# Backward-compatible constant for direct import if needed
SPECTRE_DOCUMENTATION: str = get_full_documentation()
