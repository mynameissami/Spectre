# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/ids_engine.py — Intrusion Detection System Rules Engine
Configurable rule-based anomaly detection for 802.11 networks.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional
import time


class RuleSeverity(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class IDSRule:
    """A detection rule with threshold and action."""

    rule_id: str
    name: str
    description: str
    severity: RuleSeverity
    threshold: float
    window_sec: float
    enabled: bool = True
    trigger_count: int = 0
    last_triggered: float = 0.0


class IDSEngine:
    """
    Rule-based intrusion detection engine.
    Monitors packet streams and triggers alerts when rules are violated.
    """

    def __init__(self):
        self._rules: dict[str, IDSRule] = {}
        self._packet_buffer: list[dict] = []
        self._alert_callback: Optional[Callable] = None

        # Initialize default rules
        self._init_default_rules()

    def _init_default_rules(self):
        """Set up standard 802.11 IDS rules."""
        self.add_rule(
            IDSRule(
                rule_id="DEAUTH_FLOOD",
                name="Deauthentication Flood",
                description="Excessive deauth frames indicating DoS attack",
                severity=RuleSeverity.HIGH,
                threshold=15.0,  # frames/sec
                window_sec=1.0,
                enabled=True,
            )
        )

        self.add_rule(
            IDSRule(
                rule_id="BEACON_SPAM",
                name="Beacon Flood",
                description="Abnormal beacon rate indicating rogue APs",
                severity=RuleSeverity.MEDIUM,
                threshold=50.0,  # beacons/sec
                window_sec=2.0,
                enabled=True,
            )
        )

        self.add_rule(
            IDSRule(
                rule_id="PROBE_STORM",
                name="Probe Request Storm",
                description="Excessive probe requests (reconnaissance)",
                severity=RuleSeverity.LOW,
                threshold=30.0,  # probes/sec
                window_sec=1.0,
                enabled=True,
            )
        )

        self.add_rule(
            IDSRule(
                rule_id="AUTH_FLOOD",
                name="Authentication Flood",
                description="Auth frame flood (DoS attempt)",
                severity=RuleSeverity.HIGH,
                threshold=20.0,  # auth frames/sec
                window_sec=1.0,
                enabled=True,
            )
        )

    def add_rule(self, rule: IDSRule):
        """Add or update a detection rule."""
        self._rules[rule.rule_id] = rule

    def set_alert_callback(self, callback: Callable):
        """Set function to call when rule triggers."""
        self._alert_callback = callback

    def process_packet(self, packet: dict) -> list[str]:
        """
        Process a packet and check all enabled rules.
        Returns list of triggered rule IDs.
        """
        now = time.monotonic()
        self._packet_buffer.append({**packet, "timestamp": now})

        # Clean old packets (keep last 10 seconds)
        cutoff = now - 10.0
        self._packet_buffer = [
            p for p in self._packet_buffer if p["timestamp"] > cutoff
        ]

        triggered = []

        # Check each enabled rule
        for rule in self._rules.values():
            if not rule.enabled:
                continue

            # Calculate rate for this rule's packet type
            rate = self._calculate_rate(rule, now)

            # Check if threshold exceeded
            if rate >= rule.threshold:
                rule.trigger_count += 1
                rule.last_triggered = now

                triggered.append(rule.rule_id)

                # Call alert callback if set
                if self._alert_callback:
                    self._alert_callback(rule, rate)

        return triggered

    def _calculate_rate(self, rule: IDSRule, now: float) -> float:
        """Calculate packet rate for a specific rule."""
        cutoff = now - rule.window_sec

        # Filter packets by subtype based on rule
        matching_packets = []
        for pkt in self._packet_buffer:
            if pkt["timestamp"] < cutoff:
                continue

            subtype = pkt.get("subtype", 0)

            if rule.rule_id == "DEAUTH_FLOOD" and subtype == 12:
                matching_packets.append(pkt)
            elif rule.rule_id == "BEACON_SPAM" and subtype == 8:
                matching_packets.append(pkt)
            elif rule.rule_id == "PROBE_STORM" and subtype == 4:
                matching_packets.append(pkt)
            elif rule.rule_id == "AUTH_FLOOD" and subtype == 11:
                matching_packets.append(pkt)

        return len(matching_packets) / rule.window_sec

    def get_rule_status(self) -> list[dict]:
        """Get status of all rules."""
        now = time.monotonic()
        
        # Clean old packets first to ensure accurate rate calculation
        cutoff = now - 10.0
        self._packet_buffer = [
            p for p in self._packet_buffer if p["timestamp"] > cutoff
        ]
        
        status_list = []
        for rule in self._rules.values():
            rate = self._calculate_rate(rule, now) if rule.enabled else 0.0
            is_triggered = rule.enabled and (rate >= rule.threshold)
            
            status_list.append({
                "id": rule.rule_id,
                "name": rule.name,
                "severity": rule.severity.name,
                "enabled": rule.enabled,
                "threshold": rule.threshold,
                "trigger_count": rule.trigger_count,
                "is_triggered": is_triggered,
                "current_rate": rate
            })
        return status_list

    def reset(self):
        """Reset all rule counters."""
        for rule in self._rules.values():
            rule.trigger_count = 0
            rule.last_triggered = 0.0
        self._packet_buffer.clear()
