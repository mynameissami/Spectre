# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm/engine.py — MITMEngine: orchestrates MITM attack sub-modules.

Public interface:
    MITMEngine(target_ip, gateway_ip, attack_type, intensity, block_target)
    .start() / .stop()
    Signals: log_signal, passive_log_signal, packet_generated, harvester_status_changed
"""

from __future__ import annotations

import socket
from PySide6.QtCore import QThread, Signal

from core.mitm._scapy import SCAPY_AVAILABLE, conf, get_if_hwaddr
from core.mitm import arp, dns, harvester, injector, sniffer


class MITMEngine(QThread):
    """Thin QThread orchestrator that routes to MITM sub-module implementations."""

    log_signal = Signal(str, str)
    passive_log_signal = Signal(str, str)
    packet_generated = Signal(dict)
    harvester_status_changed = Signal(bool)

    def __init__(
        self,
        target_ip: str,
        gateway_ip: str,
        attack_type: str,
        intensity: int,
        block_target: str = "",
        parent: object = None,
    ) -> None:
        super().__init__(parent)  # type: ignore[call-arg]
        self.target_ip = target_ip
        self.gateway_ip = gateway_ip
        self.attack_type = attack_type
        self.intensity = intensity
        self.block_target = block_target.lower()
        self._running = False
        self._running_flag: list[bool] = [False]

        self.attacker_ip = self._get_local_ip()
        self.attacker_mac = "00:00:00:00:00:00"
        if SCAPY_AVAILABLE and get_if_hwaddr is not None and conf is not None:
            try:
                self.attacker_mac = get_if_hwaddr(conf.iface)
            except Exception:
                pass

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip: str = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def run(self) -> None:
        if not SCAPY_AVAILABLE:
            self.log_signal.emit("CRITICAL: Scapy not installed.", "CRIT")
            return

        self._running = True
        self._running_flag = [True]
        self.log_signal.emit(f"Engine started: {self.attack_type}", "INFO")
        interval = max(0.01, 0.5 - (self.intensity / 200.0))
        atype = self.attack_type

        try:
            if "ARP" in atype:
                arp.run_arp_mitm(
                    self.target_ip, self.gateway_ip, self.attacker_mac, interval,
                    self._running_flag, self.log_signal, self.packet_generated,
                )
            elif "DNS" in atype:
                dns.run_dns_spoof(self.attacker_ip, self._running_flag, self.log_signal)
            elif "CREDENTIAL" in atype or "HARVEST" in atype or "PASSIVE" in atype:
                harvester.run_credential_harvester(
                    self._running_flag, self.log_signal,
                    self.passive_log_signal, self.harvester_status_changed,
                )
            elif "RST" in atype or "BLOCK" in atype:
                injector.run_tcp_rst_injector(
                    self.block_target, self._running_flag, self.passive_log_signal
                )
            elif "INJECT" in atype or "HTTP" in atype:
                injector.run_http_injector(self._running_flag, self.passive_log_signal)
            elif "COOKIE" in atype or "SESSION" in atype:
                sniffer.run_cookie_sniffer(self._running_flag, self.passive_log_signal)
            elif "JWT" in atype:
                sniffer.run_session_jwt_sniffer(self._running_flag, self.passive_log_signal)
        except Exception as e:
            self.log_signal.emit(f"Engine Error: {str(e)}", "CRIT")
        finally:
            if "CREDENTIAL" in atype or "HARVEST" in atype:
                self.harvester_status_changed.emit(False)
            self.log_signal.emit("Engine stopped.", "INFO")

    def stop(self) -> None:
        self._running = False
        self._running_flag[0] = False
        self.wait(2000)
