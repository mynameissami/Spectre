# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/recon.py — Passive Wireless Reconnaissance Engine
Detects anomalies from parsed 802.11 frame metadata without active probing.

Detection capabilities:
    1. Rogue AP / Honeypot   — Same SSID advertised from multiple BSSIDs
    2. Hidden Network        — Probe response with null/empty SSID
    3. Client Tracking       — Associates client MACs with BSSIDs
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ReconEventType(Enum):
    ROGUE_AP = auto()
    HIDDEN_SSID = auto()
    NEW_CLIENT = auto()
    NEW_AP = auto()


@dataclass(frozen=True)
class ReconEvent:
    """Immutable event record produced by the recon engine."""

    event_type: ReconEventType
    message: str
    bssid: Optional[str] = None
    ssid: Optional[str] = None
    client: Optional[str] = None


class ReconEngine:
    """
    Stateful passive recon processor.

    All methods are called from the GUI thread — no locks needed.
    The engine accumulates state across packets and emits events
    only when a novel condition is detected (to avoid log spam).
    """

    def __init__(self) -> None:
        # BSSID → set of SSIDs seen from that AP
        self._bssid_to_ssids: defaultdict[str, set] = defaultdict(set)
        # SSID  → set of BSSIDs advertising it
        self._ssid_to_bssids: defaultdict[str, set] = defaultdict(set)
        # BSSID → set of associated client MACs
        self._bssid_to_clients: defaultdict[str, set] = defaultdict(set)
        # Already-reported rogue SSID pairs (avoid duplicate alerts)
        self._reported_rogues: set[frozenset] = set()
        # Known hidden-network BSSIDs (avoid repeating)
        self._reported_hidden: set[str] = set()
        # Known APs (avoid repeating NEW_AP events)
        self._known_aps: set[str] = set()

        self._client_mac_patterns: defaultdict[str, list] = defaultdict(list)
        self._randomized_macs: set[str] = set()

    # ─── Main Entry ───────────────────────────────────────────────────────────

    def process(self, packet: dict) -> list[ReconEvent]:
        """
        Ingest a parsed packet dict and return a (possibly empty) list of events.

        Expected optional packet fields (real serial data won't have MAC/SSID,
        but the demo mode or a richer ESP32 firmware may include them):
            bssid   str  — AP MAC address
            ssid    str  — advertised network name
            client  str  — associated client MAC
            channel int  — 802.11 channel
        """
        events: list[ReconEvent] = []

        bssid = packet.get("bssid")
        ssid = packet.get("ssid")
        client = packet.get("client")

        if bssid:
            events.extend(self._check_ap(bssid, ssid))
        if bssid and client:
            events.extend(self._check_client(bssid, client))

        return events

    # ─── Detection Sub-routines ───────────────────────────────────────────────
    def get_ap_ssid_map(self) -> dict[str, str]:
        """Returns {BSSID: SSID} for all known APs. Falls back to 'UNKNOWN' or '[HIDDEN]'."""
        mapping = {}
        for bssid in self._known_aps:
            ssids = self._bssid_to_ssids.get(bssid, set())
            if not ssids:
                mapping[bssid] = (
                    "[HIDDEN]" if bssid in self._reported_hidden else "UNKNOWN"
                )
            else:
                # APs typically advertise one SSID. Pick the first alphabetically for stability.
                mapping[bssid] = sorted(ssids)[0]
        return mapping

    def _check_ap(self, bssid: str, ssid: Optional[str]) -> list[ReconEvent]:
        events: list[ReconEvent] = []

        # New AP seen
        if bssid not in self._known_aps:
            self._known_aps.add(bssid)
            events.append(
                ReconEvent(
                    event_type=ReconEventType.NEW_AP,
                    message=f"New AP detected: {bssid}"
                    + (f" [{ssid}]" if ssid else ""),
                    bssid=bssid,
                    ssid=ssid,
                )
            )

        # Hidden network: SSID is null, empty, or all \x00
        if ssid is not None:
            normalised = ssid.replace("\x00", "").strip()
            if not normalised:
                if bssid not in self._reported_hidden:
                    self._reported_hidden.add(bssid)
                    events.append(
                        ReconEvent(
                            event_type=ReconEventType.HIDDEN_SSID,
                            message=f"⚠ Hidden network detected from {bssid}",
                            bssid=bssid,
                        )
                    )
            else:
                # Track SSID↔BSSID mapping for rogue AP detection
                self._bssid_to_ssids[bssid].add(normalised)
                self._ssid_to_bssids[normalised].add(bssid)

                # Rogue AP: same SSID from multiple BSSIDs
                bssids_for_ssid = self._ssid_to_bssids[normalised]
                if len(bssids_for_ssid) > 1:
                    pair = frozenset(bssids_for_ssid)
                    if pair not in self._reported_rogues:
                        self._reported_rogues.add(pair)
                        bssid_list = ", ".join(sorted(bssids_for_ssid))
                        events.append(
                            ReconEvent(
                                event_type=ReconEventType.ROGUE_AP,
                                message=(
                                    f"🚨 ROGUE AP — SSID '{normalised}' seen from "
                                    f"{len(bssids_for_ssid)} BSSIDs: {bssid_list}"
                                ),
                                bssid=bssid,
                                ssid=normalised,
                            )
                        )

        return events

    def get_target_list(self) -> list[tuple[str, str]]:
        """Returns list of (display_name, bssid) tuples. Shows SSID if known, else BSSID."""
        targets = []
        for bssid in self._known_aps:
            ssids = self._bssid_to_ssids.get(bssid, set())
            if ssids:
                # Show SSID + BSSID for clarity
                display = f"{sorted(ssids)[0]} ({bssid})"
            else:
                # Fallback to raw BSSID instead of "UNKNOWN"
                display = bssid
            targets.append((display, bssid))
        return targets

    def detect_mac_randomization(self, client_mac: str, bssid: str) -> bool:
        """
        Detect if a client is using MAC randomization.
        Returns True if randomization detected.
        """
        # Check for locally administered bit (second hex digit is 2, 6, A, or E)
        if len(client_mac) > 1:
            second_char = client_mac[1].upper()
            if second_char in ["2", "6", "A", "E"]:
                self._randomized_macs.add(client_mac)
                return True

        # Track MAC patterns per BSSID
        self._client_mac_patterns[bssid].append(client_mac)

        # If same BSSID sees many different MACs in short time, likely randomization
        if len(set(self._client_mac_patterns[bssid][-20:])) > 15:
            return True

        return False

    def _check_client(self, bssid: str, client: str) -> list[ReconEvent]:
        events: list[ReconEvent] = []
        if client not in self._bssid_to_clients[bssid]:
            self._bssid_to_clients[bssid].add(client)
            events.append(
                ReconEvent(
                    event_type=ReconEventType.NEW_CLIENT,
                    message=f"New client {client} → {bssid}",
                    bssid=bssid,
                    client=client,
                )
            )
        return events

    # ─── Stats ────────────────────────────────────────────────────────────────

    @property
    def known_ap_count(self) -> int:
        return len(self._known_aps)

    @property
    def rogue_ap_count(self) -> int:
        return len(self._reported_rogues)

    @property
    def randomized_mac_count(self) -> int:
        return len(self._randomized_macs)

    @property
    def hidden_net_count(self) -> int:
        return len(self._reported_hidden)

    def client_count(self, bssid: str) -> int:
        return len(self._bssid_to_clients.get(bssid, set()))

    def reset(self) -> None:
        self._bssid_to_ssids.clear()
        self._ssid_to_bssids.clear()
        self._bssid_to_clients.clear()
        self._reported_rogues.clear()
        self._reported_hidden.clear()
        self._known_aps.clear()
