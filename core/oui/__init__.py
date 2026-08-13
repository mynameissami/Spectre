# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/oui — OUI vendor identification deep module.

Public interface (the only import callers need):
    from core.oui import lookup
"""

from core.oui.lookup import lookup

__all__ = ["lookup"]
