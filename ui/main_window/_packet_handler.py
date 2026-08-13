# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window._window import MainWindow

from PySide6.QtCore import Qt, Slot, QTimer, QPoint
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QMessageBox, QLabel
import numpy as np
import time
import config
from core.settings_manager import SettingsManager
from core.network.recon import ReconEventType
from core.analytics.threat import ThreatLevel

class PacketHandlerMixin:
    # This is a mixin for MainWindow
        @Slot(dict)
        def _on_packet(self, pkt: dict) -> None:
            now = time.monotonic()
            self._pkt_timestamps.append(now)
            payload_size = pkt.get("payload_size", 0)
            if isinstance(payload_size, (int, float)) and payload_size > 0:
                self._packet_bytes_window.append((now, payload_size))
            cutoff = now - 1.0
            while self._packet_bytes_window and self._packet_bytes_window[0][0] < cutoff:
                self._packet_bytes_window.popleft()
    
            channel = pkt.get("channel")
            if channel is not None:
                channel = int(channel)
            raw, smoothed = self._dsp.push(pkt["rssi"], channel=channel)
            self._pending_raw = raw
            self._pending_smooth = smoothed
            self._data_dirty = True
    
            self._spectrum.add_packet(pkt)
            threat = self._threat.update(pkt)
            events = self._recon.process(pkt)
            triggered_ids = self._ids.process_packet(pkt)
    
            if pkt.get("subtype") == 11 and pkt.get("bssid") and pkt.get("ssid"):
                self._pmkid.simulate_capture(pkt["ssid"], pkt["bssid"], "AA:BB:CC:DD:EE:FF")
    
            if not hasattr(self, "_last_ui_update"):
                self._last_ui_update = 0.0
            if now - self._last_ui_update < 0.066:
                return
            self._last_ui_update = now
    
            if pkt.get("subtype") == 12:
                # Throttle the RX log: max once per 0.5s per source MAC
                src = pkt.get("bssid", "UNKNOWN")
                if not hasattr(self, "_deauth_rx_times"):
                    self._deauth_rx_times: dict = {}
                last_rx = self._deauth_rx_times.get(src, 0.0)
                if now - last_rx >= 0.5:
                    self._log.log(f"DEAUTH FRAME DETECTED | SRC: {src}", "RX")
                    self._deauth_rx_times[src] = now
    
            if not hasattr(self, "_last_deauth_alert_log"):
                self._last_deauth_alert_log = 0.0
            if not hasattr(self, "_was_under_attack"):
                self._was_under_attack = False
    
            if threat.deauth_level == ThreatLevel.ALERT:
                self._was_under_attack = True
                # Throttle: log the ALERT message at most once per second
                if now - self._last_deauth_alert_log >= 1.0:
                    conc_pct = int(threat.src_concentration * 100)
                    persist_s = threat.persistence
                    # Label based on persistence — call it what it is
                    if persist_s >= 5:
                        label = "CONFIRMED DEAUTH FLOOD ATTACK"
                    elif persist_s >= 2:
                        label = "SUSTAINED DEAUTH ATTACK"
                    else:
                        label = "DEAUTH ATTACK DETECTED"
                    self._log.log(
                        f"{label} | {threat.deauth_rate:.1f} f/s | "
                        f"SRC: {threat.top_src} ({conc_pct}% of frames) | "
                        f"Duration: {persist_s}s",
                        "ALERT",
                    )
                    self._last_deauth_alert_log = now
                    self._timeline.add_event(
                        "ALERT",
                        f"{label}: {threat.deauth_rate:.1f}/s from {threat.top_src}"
                    )
            elif threat.deauth_level == ThreatLevel.WARNING:
                # High-ish rate but spread across many sources → likely congestion
                if now - self._last_deauth_alert_log >= 2.0:
                    self._log.log(
                        f"ELEVATED DEAUTH RATE — {threat.deauth_rate:.1f} f/s "
                        f"(multi-source, likely congestion, not an attack)",
                        "WARN",
                    )
                    self._last_deauth_alert_log = now
            else:
                # Attack has ended — notify once
                if self._was_under_attack:
                    self._log.log("DEAUTH THREAT CLEARED — network traffic returned to normal.", "OK")
                    self._timeline.add_event("OK", "Deauth attack ended")
                    self._was_under_attack = False
    
            for ev in events:
                level = "ALERT" if ev.event_type == ReconEventType.ROGUE_AP else "RECON"
                self._log.log(ev.message, level)
                if ev.event_type == ReconEventType.ROGUE_AP:
                    self._timeline.add_event(level, ev.message)
    
            for rule_id in triggered_ids:
                rule_status = next(
                    (r for r in self._ids.get_rule_status() if r["id"] == rule_id), None
                )
                if rule_status:
                    # Throttle IDS alerts: once per 2 seconds per rule
                    if not hasattr(self, "_last_ids_alert_times"):
                        self._last_ids_alert_times: dict = {}
                    last_ids = self._last_ids_alert_times.get(rule_id, 0.0)
                    if now - last_ids >= 2.0:
                        self._log.log(
                            f"IDS TRIGGER: {rule_status['name']} (Rate exceeded threshold)",
                            "ALERT",
                        )
                        self._timeline.add_event(
                            "ALERT", f"IDS: {rule_status['name']} triggered"
                        )
                        self._last_ids_alert_times[rule_id] = now

        @Slot()
        def _on_timer(self) -> None:
            now = time.monotonic()
            cutoff = now - 1.0
            recent_bytes = sum(
                size for ts, size in self._packet_bytes_window if ts > cutoff
            )
            throughput_kbs = (recent_bytes / 1024.0) / 1.0
            self._throughput_samples.append(throughput_kbs)
            self._status.set_throughput(throughput_kbs)
            self._left.update_throughput(self._throughput_samples)
    
            if self._data_dirty and self._pending_raw is not None:
                self._left.update_rssi(self._pending_raw, self._pending_smooth)
                self._data_dirty = False
    
            try:
                result = self._dsp.get_channel_counts()
                if result is not None and len(result) == 2:
                    channels, counts = result
                    self._left.update_spectrum(channels, counts)
                else:
                    self._left.update_spectrum(np.array([]), np.array([]))
            except Exception as e:
                self._log.log(f"DSP spectrum update skipped: {e}", "DEBUG")
    
            fake = {"prefix": "MGT", "rssi": 0, "payload_size": 0, "subtype": 0}
            threat = self._threat.update(fake)
            self._status.set_threat(
                threat.deauth_level, threat.deauth_rate, self._threat.total_deauths
            )
            self._status.set_throughput(threat.throughput_kbs)
    
            recent_pkts = sum(1 for t in self._pkt_timestamps if t > cutoff)
            self._status.set_packet_stats(self._dsp.total_packets, recent_pkts)
            self._status.set_recon_stats(
                self._recon.known_ap_count + self._recon.hidden_net_count,
                self._recon.rogue_ap_count,
            )
    
            ap_count = self._recon.known_ap_count
            if self._data_dirty or (
                self._timer.isActive() and getattr(self, "_last_ap_count", -1) != ap_count
            ):
                targets = []
                for bssid in self._recon._known_aps:
                    ssids = self._recon._bssid_to_ssids.get(bssid, set())
                    display = f"{sorted(ssids)[0]} ({bssid})" if ssids else bssid
                    targets.append((display, bssid))
                self._attack_panel.update_targets(targets)
                self._last_ap_count = ap_count
    
            if hasattr(self, "_ids_rules_widget"):
                self._ids_rules_widget.update_rules(self._ids.get_rule_status())
    
            if int(now) % 2 == 0 and self._connected:
                occ = self._spectrum.calculate_occupancy(6)
                self._timeline.add_event(
                    "INFO",
                    f"Ch6 Occ: Mgmt {occ.management_pct:.0f}% | Data {occ.data_pct:.0f}% | Beacons: {occ.beacon_count}",
                )

        def _refresh_all_theme(self) -> None:
            """Refresh inline styles on every panel after a theme change."""
            # Refresh the placeholder label
            if hasattr(self, '_placeholder'):
                import PySide6.QtWidgets as QtWidgets
                for lbl in self._placeholder.findChildren(QtWidgets.QLabel):
                    lbl.setStyleSheet(
                        f"color: {config.COLOR_ACCENT_GREEN}; font-size: 24px; font-weight: bold;"
                    )
    
            # Notify each panel
            for panel in (
                self._left,
                self._banner,
                self._right,
                self._wifi_panel,
                self._attack_panel,
                self._mitm_panel,
                self._recon_panel,
                self._doc_panel,
            ):
                if hasattr(panel, "refresh_theme"):
                    panel.refresh_theme()
                    
            # Force repolish of main tabs to ensure stylesheet applies immediately
            self._tabs.style().unpolish(self._tabs)
            self._tabs.style().polish(self._tabs)
            self._tabs.tabBar().style().unpolish(self._tabs.tabBar())
            self._tabs.tabBar().style().polish(self._tabs.tabBar())
            self._tabs.update()

        def _refresh_all_graphs(self) -> None:
            """Clear and reset all graph data in the Defensive / Analytics left panel."""
            import numpy as np
    
            # Reset DSP engine history
            self._dsp.reset()
    
            # Clear left panel buffers and curves
            self._left._rssi_raw_buf.clear()
            self._left._rssi_smooth_buf.clear()
            self._left._throughput_buf.clear()
    
            # Reset RSSI scope
            self._left._curve_raw.setData([], [])
            self._left._curve_smooth.setData([], [])
    
            # Reset channel spectrum
            self._left._bar_spectrum.setOpts(height=[0] * 13)
    
            # Reset throughput graph
            self._left._curve_throughput.setData([], [])
    
            # Clear throughput window data
            self._throughput_samples.clear()
            self._packet_bytes_window.clear()
    
            # Reset spectrum engine
            self._spectrum.reset()
    
            self._log.log("All graphs refreshed and reset.", "OK")
