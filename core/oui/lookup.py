# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/oui/lookup.py — OUI vendor lookup with a 3-tier fallback strategy.

Interface (the only thing callers need to know):
    lookup(mac: str) -> str

Internally uses:
  Tier 1 — local OUI_DATABASE dict (zero I/O, instant)
  Tier 2 — mac_vendor_lookup library (comprehensive offline DB)
  Tier 3 — Returns "Unknown Device" if both fail
"""

from __future__ import annotations

import logging

from core.oui.data import OUI_DATABASE

try:
    from mac_vendor_lookup import MacLookup as _MacLookup
    _mac_lookup = _MacLookup()
    _MAC_VENDOR_AVAILABLE = True
except Exception:
    _mac_lookup = None
    _MAC_VENDOR_AVAILABLE = False

logger = logging.getLogger(__name__)


def lookup(mac: str) -> str:
    """Return a vendor name for the given MAC address or OUI prefix.

    Args:
        mac: Full MAC address or 8-char OUI prefix (e.g. "AA:BB:CC" or
             "AA:BB:CC:DD:EE:FF").

    Returns:
        Vendor name string. Falls back to "Unknown Device" when
        no match is found across all tiers.
    """
    prefix = mac.upper()[:8]

    # Tier 1: local static dict — zero I/O, sub-microsecond
    local = OUI_DATABASE.get(prefix)
    if local:
        return local

    # Tier 2: mac_vendor_lookup offline library
    if _MAC_VENDOR_AVAILABLE and _mac_lookup is not None:
        try:
            return _mac_lookup.lookup(mac)
        except Exception:
            pass

    return "Unknown Device"
