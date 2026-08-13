# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/spectrum_analysis.py — Spectrum Occupancy Calculator
Calculates percentage of airtime consumed by different frame types.
"""

from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
import time


@dataclass
class SpectrumStats:
    """Spectrum occupancy statistics."""

    channel: int
    total_airtime_us: int
    management_pct: float
    data_pct: float
    control_pct: float
    beacon_count: int
    deauth_count: int
    sample_duration_sec: float


class SpectrumAnalyzer:
    """
    Calculates spectrum occupancy and airtime usage.
    Demonstrates how attacks consume wireless medium.
    """

    def __init__(self, sample_window_sec: float = 5.0):
        self._sample_window = sample_window_sec
        self._packets: list[dict] = []
        self._channel_stats: dict[int, SpectrumStats] = {}

    def add_packet(self, packet: dict):
        """Add a packet to the analysis buffer."""
        now = time.monotonic()
        pkt = {**packet, "timestamp": now}
        self._packets.append(pkt)

        # Clean old packets
        cutoff = now - self._sample_window
        self._packets = [p for p in self._packets if p["timestamp"] > cutoff]

    def calculate_occupancy(self, channel: int) -> SpectrumStats:
        """
        Calculate spectrum occupancy for a specific channel.
        Returns percentage breakdown by frame type.
        """
        now = time.monotonic()
        cutoff = now - self._sample_window

        # Filter packets for this channel
        channel_packets = [
            p
            for p in self._packets
            if p.get("channel") == channel and p["timestamp"] > cutoff
        ]

        # Count by type
        mgmt_count = sum(1 for p in channel_packets if p.get("prefix") == "MGMT")
        data_count = sum(1 for p in channel_packets if p.get("prefix") == "DAT")
        beacon_count = sum(1 for p in channel_packets if p.get("subtype") == 8)
        deauth_count = sum(1 for p in channel_packets if p.get("subtype") == 12)

        total = len(channel_packets)

        # Estimate airtime (simplified: assume 1ms per packet)
        total_airtime_us = total * 1000  # microseconds

        mgmt_pct = (mgmt_count / total * 100) if total > 0 else 0
        data_pct = (data_count / total * 100) if total > 0 else 0
        control_pct = 100 - mgmt_pct - data_pct

        return SpectrumStats(
            channel=channel,
            total_airtime_us=total_airtime_us,
            management_pct=mgmt_pct,
            data_pct=data_pct,
            control_pct=control_pct,
            beacon_count=beacon_count,
            deauth_count=deauth_count,
            sample_duration_sec=self._sample_window,
        )

    def get_all_channels(self) -> list[int]:
        """Get list of channels with traffic."""
        return list(set(p.get("channel", 1) for p in self._packets))

    def reset(self):
        self._packets.clear()
        self._channel_stats.clear()
