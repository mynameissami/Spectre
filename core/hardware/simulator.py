# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/simulator.py — Software-Led Offensive Engine
"""

from PySide6.QtCore import QObject, Signal, QTimer
import random


class AttackSimulator(QObject):
    packet_generated = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._generate_packet)
        self._active = False
        self._vector = ""
        self._target_bssid = "AA:BB:CC:DD:EE:FF"
        self._intensity = 50
        self._counter = 0

    def start(self, target_bssid: str, vector: str, intensity: int) -> None:
        self._active = True
        self._target_bssid = target_bssid if target_bssid else "AA:BB:CC:DD:EE:FF"
        self._vector = vector
        self._intensity = intensity
        self._counter = 0
        interval = max(5, int(505 - (intensity * 5)))
        self._timer.start(interval)

    def stop(self) -> None:
        self._active = False
        self._timer.stop()

    def _generate_packet(self) -> None:
        if not self._active:
            return
        self._counter += 1
        pkt = {}

        # ── RF Attacks (ESP32) ───────────────────────────────────────
        if "DEAUTH" in self._vector:
            pkt = {
                "prefix": "MGMT",
                "subtype": 12,
                "rssi": random.randint(-60, -30),
                "payload_size": 26,
                "bssid": self._target_bssid,
                "channel": 6,
            }
        elif "BEACON" in self._vector:
            fake_bssid = (
                f"DE:AD:BE:EF:{self._counter % 256:02X}:{random.randint(0, 255):02X}"
            )
            pkt = {
                "prefix": "MGMT",
                "subtype": 8,
                "rssi": random.randint(-85, -50),
                "payload_size": 100,
                "bssid": fake_bssid,
                "ssid": "FREE_PUBLIC_WIFI",
                "channel": random.randint(1, 13),
            }
        elif "CAPTIVE" in self._vector or "PORTAL" in self._vector:
            pkt = {
                "prefix": "MGMT",
                "subtype": 8,
                "rssi": random.randint(-40, -20),
                "payload_size": 100,
                "bssid": "DE:AD:BE:EF:00:01",
                "ssid": self._target_bssid,
                "channel": 6,
            }
        elif "PROBE" in self._vector:
            pkt = {
                "prefix": "MGMT",
                "subtype": 4,
                "rssi": random.randint(-85, -45),
                "payload_size": 40,
                "bssid": "FF:FF:FF:FF:FF:FF",
                "channel": random.randint(1, 13),
            }
        elif "AUTH" in self._vector:
            pkt = {
                "prefix": "MGMT",
                "subtype": 11,
                "rssi": random.randint(-80, -50),
                "payload_size": 30,
                "bssid": self._target_bssid,
                "channel": 6,
            }
        elif "RTS" in self._vector:
            pkt = {
                "prefix": "MGMT",
                "subtype": 11,
                "rssi": random.randint(-90, -60),
                "payload_size": 20,
                "bssid": self._target_bssid,
                "channel": 6,
            }

        # ── L2/L3 Network Attacks (DoS) ──────────────────────────────
        elif "ARP" in self._vector:
            pkt = {
                "prefix": "L2",
                "subtype": 6,
                "rssi": random.randint(-30, -10),
                "payload_size": 42,
                "bssid": "FF:FF:FF:FF:FF:FF",
                "channel": 0,
                "ip_target": self._target_bssid,
            }
        elif "DHCP" in self._vector:
            fake_mac = f"FA:KE:{self._counter % 256:02X}:{random.randint(0, 255):02X}:{random.randint(0, 255):02X}:{random.randint(0, 255):02X}"
            pkt = {
                "prefix": "L2",
                "subtype": 7,
                "rssi": random.randint(-30, -10),
                "payload_size": 300,
                "bssid": fake_mac,
                "channel": 0,
            }
        elif "DNS" in self._vector:
            pkt = {
                "prefix": "L3",
                "subtype": 9,
                "rssi": random.randint(-30, -10),
                "payload_size": 64,
                "bssid": self._target_bssid,
                "channel": 0,
            }
        elif "ICMP" in self._vector:
            pkt = {
                "prefix": "L3",
                "subtype": 10,
                "rssi": random.randint(-30, -10),
                "payload_size": 1024,
                "bssid": self._target_bssid,
                "channel": 0,
            }

        # ── Fallback ─────────────────────────────────────────────────
        else:
            pkt = {
                "prefix": "MGMT",
                "subtype": 8,
                "rssi": random.randint(-90, -40),
                "payload_size": 100,
                "bssid": self._target_bssid,
                "ssid": "Baseline_AP",
                "channel": 6,
            }

        self.packet_generated.emit(pkt)
