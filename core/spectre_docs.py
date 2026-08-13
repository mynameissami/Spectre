# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/spectre_docs.py — Documentation loader.

The HTML content lives in assets/docs/spectre_docs.html.
This module loads it at import time and provides the same
SPECTRE_DOCUMENTATION constant for backward compatibility.
"""

from __future__ import annotations

from pathlib import Path

_DOCS_PATH = Path(__file__).parent.parent / "assets" / "docs" / "spectre_docs.html"

def load_docs() -> str:
    """Load and return the full HTML documentation string."""
    try:
        return _DOCS_PATH.read_text(encoding="utf-8")
    except OSError:
        return "<html><body><p>Documentation file not found.</p></body></html>"

# Backward-compatible constant — loaded once at import time
SPECTRE_DOCUMENTATION: str = load_docs()
