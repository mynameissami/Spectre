# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/threat.py — Threat Monitor
Real-time vulnerability monitoring and alerting.

Detectors:
    1. Deauth Attack  — Sliding-window rate of 802.11 Subtype 12 frames
    2. Throughput     — Rolling KB/s based on payload sizes
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

import config


class ThreatLevel(Enum):
    SECURE  = auto()
    WARNING = auto()
    ALERT   = auto()


@dataclass
class ThreatStatus:
    deauth_level:      ThreatLevel
    deauth_rate:       float          # frames/second in current window
    throughput_kbs:    float          # kilobytes per second
    total_deauths:     int
    top_src:           str = ""       # MAC responsible for most deauths
    src_concentration: float = 0.0   # 0.0–1.0 fraction from top_src
    persistence:       int = 0        # consecutive windows above threshold


class ThreatMonitor:
    """
    Stateful real-time threat monitor.

    Designed to be called from the GUI thread (no internal locking).
    Uses timestamp-based sliding windows for accurate rate computation
    without any external timer dependency.
    """

    def __init__(
        self,
        deauth_thresh:  int   = config.DEAUTH_ALERT_THRESH,
        window_sec:     float = config.DEAUTH_WINDOW_SEC,
    ) -> None:
        self._deauth_thresh = deauth_thresh
        self._window_sec    = window_sec

        # Timestamps of recent deauth frames (sliding window)
        # Each entry: (timestamp, src_mac)
        self._deauth_events: deque[tuple[float, str]] = deque()

        # Payload size accumulator for throughput  (timestamp, bytes)
        self._payload_log: deque[tuple[float, int]] = deque()

        # Cumulative counters
        self._total_deauths: int = 0

        # Persistence tracking (how many consecutive 1-s windows triggered)
        self._consecutive_triggers: int = 0
        self._last_window_check: float = 0.0

    # ─── Main Update ──────────────────────────────────────────────────────────

    def update(self, packet: dict) -> ThreatStatus:
        """
        Ingest a parsed packet and return the current threat status snapshot.
        Call this once per packet in the GUI thread.
        """
        now = time.monotonic()
        subtype      = packet.get("subtype", 0)
        payload_size = packet.get("payload_size", 0)
        src_mac      = packet.get("bssid", "UNKNOWN")

        # Track deauth frames with their source MAC
        if subtype == config.DEAUTH_SUBTYPE:
            self._deauth_events.append((now, src_mac))
            self._total_deauths += 1

        # Track payload for throughput
        self._payload_log.append((now, payload_size))

        # Evict stale entries from both sliding windows
        cutoff = now - self._window_sec
        while self._deauth_events and self._deauth_events[0][0] < cutoff:
            self._deauth_events.popleft()
        while self._payload_log and self._payload_log[0][0] < cutoff:
            self._payload_log.popleft()

        deauth_rate    = len(self._deauth_events) / self._window_sec
        throughput_kbs = sum(b for _, b in self._payload_log) / 1024.0 / self._window_sec

        # ── Source Concentration Analysis ─────────────────────────────────────
        # Count per-source MAC within window
        src_counts: dict[str, int] = {}
        for _, mac in self._deauth_events:
            src_counts[mac] = src_counts.get(mac, 0) + 1

        total_in_window = len(self._deauth_events)
        if total_in_window > 0:
            top_src = max(src_counts, key=lambda m: src_counts[m])
            src_concentration = src_counts[top_src] / total_in_window
        else:
            top_src = ""
            src_concentration = 0.0

        # ── Persistence Tracking ───────────────────────────────────────────────
        # Increment consecutive-trigger counter once per second
        if now - self._last_window_check >= 1.0:
            self._last_window_check = now
            if deauth_rate >= self._deauth_thresh:
                self._consecutive_triggers += 1
            else:
                self._consecutive_triggers = 0

        # ── Threat Classification ──────────────────────────────────────────────
        # A true attack requires BOTH a high rate AND high source concentration
        # (one attacker MAC responsible for ≥70% of frames).
        # Pure high traffic from many sources stays at WARNING.
        is_concentrated = src_concentration >= 0.70

        if deauth_rate >= self._deauth_thresh and is_concentrated:
            level = ThreatLevel.ALERT
        elif deauth_rate >= self._deauth_thresh * 0.5:
            level = ThreatLevel.WARNING
        else:
            level = ThreatLevel.SECURE

        return ThreatStatus(
            deauth_level=level,
            deauth_rate=deauth_rate,
            throughput_kbs=throughput_kbs,
            total_deauths=self._total_deauths,
            top_src=top_src,
            src_concentration=src_concentration,
            persistence=self._consecutive_triggers,
        )

    # ─── Accessors ────────────────────────────────────────────────────────────

    @property
    def total_deauths(self) -> int:
        return self._total_deauths

    def set_deauth_threshold(self, thresh: int) -> None:
        self._deauth_thresh = max(1, thresh)

    def reset(self) -> None:
        self._deauth_events.clear()
        self._payload_log.clear()
        self._total_deauths = 0
        self._consecutive_triggers = 0
        self._last_window_check = 0.0
