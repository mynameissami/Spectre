# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/pmkid_sim.py — PMKID Capture Educational Simulator
Demonstrates WPA2 handshake vulnerability for academic purposes.
Shows how PMKID can be captured and used for offline cracking.
"""

from __future__ import annotations
import hashlib
import hmac
from dataclasses import dataclass
from typing import Optional


@dataclass
class PMKIDCapture:
    """Represents a captured PMKID handshake."""

    ssid: str
    bssid: str
    pmkid: str  # Hex string
    mac_ap: str
    mac_client: str
    timestamp: float


class PMKIDSimulator:
    """
    Educational PMKID capture simulator.
    Shows the structure of WPA2 handshake without actual exploitation.
    """

    def __init__(self):
        self._captures: list[PMKIDCapture] = []

    def simulate_capture(self, ssid: str, bssid: str, client_mac: str) -> PMKIDCapture:
        """
        Simulate capturing a PMKID from a handshake.
        This is for EDUCATIONAL DEMONSTRATION only.
        """
        import time

        # Simulate PMKID calculation (simplified for demo)
        # Real PMKID = HMAC-SHA1-128(PMK, "PMK Name" || MAC_AP || MAC_STA)
        pmk_placeholder = b"DEMO_PMK_FOR_EDUCATIONAL_PURPOSES"
        mac_ap_bytes = bytes.fromhex(bssid.replace(":", ""))
        mac_client_bytes = bytes.fromhex(client_mac.replace(":", ""))

        pmkid = (
            hmac.new(
                pmk_placeholder,
                b"PMK Name" + mac_ap_bytes + mac_client_bytes,
                hashlib.sha1,
            )
            .hexdigest()[:32]
            .upper()
        )

        capture = PMKIDCapture(
            ssid=ssid,
            bssid=bssid,
            pmkid=pmkid,
            mac_ap=bssid,
            mac_client=client_mac,
            timestamp=time.time(),
        )

        self._captures.append(capture)
        return capture

    def get_captures(self) -> list[PMKIDCapture]:
        return self._captures.copy()

    def format_hashcat(self, capture: PMKIDCapture) -> str:
        """
        Format PMKID for hashcat (educational display only).
        Format: PMKID*MAC_AP*MAC_STA*SSID
        """
        return (
            f"{capture.pmkid}*"
            f"{capture.mac_ap.replace(':', '').upper()}*"
            f"{capture.mac_client.replace(':', '').upper()}*"
            f"{capture.ssid}"
        )

    def reset(self):
        self._captures.clear()
