# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm/_scapy.py — Scapy import guard shared across all MITM sub-modules.
"""

from __future__ import annotations

import logging

try:
    from scapy.all import ARP, Ether, IP, UDP, TCP, DNS, DNSQR, DNSRR, Raw, send, sendp, sniff, conf, get_if_hwaddr  # type: ignore[import-not-found, import-untyped]
    import logging as _logging
    _logging.getLogger("scapy").setLevel(logging.ERROR)
    conf.verb = 0
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    # Create stub objects so sub-modules can still import without crashing
    ARP = Ether = IP = UDP = TCP = DNS = DNSQR = DNSRR = Raw = None  # type: ignore
    send = sendp = sniff = conf = get_if_hwaddr = None  # type: ignore
