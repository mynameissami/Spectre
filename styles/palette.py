# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
styles/palette.py — Color and theme helpers.
"""

def rgba(hex_str: str, alpha: float) -> str:
    """Convert hex color string to CSS rgba format."""
    h = hex_str.lstrip('#')
    if len(h) == 6:
        return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {alpha})"
    return hex_str
