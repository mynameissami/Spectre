# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm — Man-In-The-Middle engine package.

Public interface:
    from core.mitm import MITMEngine

Sub-modules (package-private — do not import directly):
    _scapy      — Scapy import guard
    arp         — ARP poisoning
    dns         — DNS spoofing
    harvester   — Credential harvesting
    injector    — HTTP injection + TCP RST injection
    sniffer     — Cookie & JWT sniffing
    engine      — MITMEngine QThread orchestrator
"""

from core.mitm.engine import MITMEngine

__all__ = ["MITMEngine"]
