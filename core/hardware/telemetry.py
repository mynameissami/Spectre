# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/telemetry.py — TelemetryReceiver QThread
Reads and parses ESP32 serial frames, emits Qt signals to the GUI thread.

Wire Protocol v2 (backward-compatible with v1):
    Frame telemetry:
        MGMT:<RSSI>,<LEN>,<SUBTYPE>[,<BSSID>,<CHANNEL>]
        DAT:<RSSI>,<LEN>,<SUBTYPE>[,<BSSID>,<CHANNEL>]
    Scan results:
        SCAN:<SSID>,<BSSID>,<CHANNEL>,<RSSI>
        SCAN_DONE:<COUNT>
    Target lock:
        TARGET:<SSID>,<BSSID>,<CHANNEL>
    Status:
        STATUS:<CODE>[,<MESSAGE>]
"""

from __future__ import annotations

import re
import threading
import time
import random
from typing import Optional

from PySide6.QtCore import QThread, Signal

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

import config

# Pre-compiled regex patterns for maximum throughput parsing
# v1: MGMT:-45,128,8
# v2: MGMT:-45,128,8,AA:BB:CC:DD:EE:FF,6
_FRAME_RE = re.compile(
    r'^(MGMT|DAT):(-?\d+),(\d+),(\d+)'
    r'(?:,([0-9A-Fa-f:]{17}),(\d+))?\s*$'
)

# SCAN:MyNetwork,AA:BB:CC:DD:EE:FF,6,-45
_SCAN_RE = re.compile(
    r'^SCAN:(.+),([0-9A-Fa-f:]{17}),(\d+),(-?\d+)\s*$'
)

# TARGET:MyNetwork,AA:BB:CC:DD:EE:FF,6
_TARGET_RE = re.compile(
    r'^TARGET:(.+),([0-9A-Fa-f:]{17}),(\d+)\s*$'
)

# STATUS:ONLINE  or  STATUS:BOOT,S.P.E.C.T.R.E. Edge Sensor v2.0
_STATUS_RE = re.compile(
    r'^STATUS:(\w+)(?:,(.+))?\s*$'
)

# SCAN_DONE:5
_SCAN_DONE_RE = re.compile(
    r'^SCAN_DONE:(\d+)\s*$'
)


class TelemetryReceiver(QThread):
    """
    Background QThread that reads serial data from the ESP32 edge sensor,
    parses each frame, and emits typed Qt signals consumed by the main window.

    Signals:
        packet_received(dict)   – one parsed frame  {prefix, rssi, payload_size, subtype, bssid?, channel?}
        scan_result(dict)       – one AP from scan   {ssid, bssid, channel, rssi}
        scan_complete(int)      – scan finished with N results
        target_locked(dict)     – target metadata    {ssid, bssid, channel}
        esp_status(str, str)    – status code + optional message
        status_changed(str)     – human-readable connection status message
        error_occurred(str)     – recoverable or fatal error description
        connected()             – emitted once the port opens successfully
        disconnected()          – emitted when port closes / thread stops
    """

    packet_received: Signal = Signal(dict)
    scan_result:     Signal = Signal(dict)
    scan_complete:   Signal = Signal(int)
    target_locked:   Signal = Signal(dict)
    esp_status:      Signal = Signal(str, str)
    status_changed:  Signal = Signal(str)
    error_occurred:  Signal = Signal(str)
    connected:       Signal = Signal()
    disconnected:    Signal = Signal()

    def __init__(
        self,
        port: str,
        baud: int = config.SERIAL_BAUD,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.port  = port
        self.baud  = baud
        self._stop_event = threading.Event()
        self._ser: Optional["serial.Serial"] = None   # type: ignore[type-arg]

    # ─── Public API ───────────────────────────────────────────────────────────

    def stop(self) -> None:
        """Signal the thread to exit at the next safe checkpoint."""
        self._stop_event.set()
        # Wake a blocked readline() if possible
        if self._ser and self._ser.is_open:
            try:
                self._ser.cancel_read()
            except Exception:
                pass

    def send_command(self, cmd: str) -> None:
        """Send a command string to the ESP32 (e.g. 'CMD:PING')."""
        if self._ser and self._ser.is_open:
            try:
                self._ser.write(f"{cmd}\n".encode("ascii"))
            except Exception:
                pass

    # ─── Thread Body ──────────────────────────────────────────────────────────

    def run(self) -> None:
        self._run_serial()

    # ─── Serial Mode ──────────────────────────────────────────────────────────

    def _run_serial(self) -> None:
        if not SERIAL_AVAILABLE:
            self.error_occurred.emit("pyserial not installed — cannot open port.")
            return

        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=config.SERIAL_TIMEOUT,
            )
            self.status_changed.emit(f"Connected to {self.port} @ {self.baud} baud")
            self.connected.emit()
        except serial.SerialException as exc:
            self.error_occurred.emit(f"Cannot open {self.port}: {exc}")
            return

        while not self._stop_event.is_set():
            try:
                raw_line = self._ser.readline()
                if not raw_line:
                    continue  # timeout → retry
                line = raw_line.decode("ascii", errors="ignore").strip()
                self._dispatch_line(line)
            except serial.SerialException as exc:
                self.error_occurred.emit(f"Serial error: {exc}")
                break
            except Exception as exc:  # noqa: BLE001
                # Log but never crash the thread
                self.error_occurred.emit(f"Parse error: {exc}")

        self._close_port()
        self.status_changed.emit("Disconnected")
        self.disconnected.emit()

    def _close_port(self) -> None:
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass

    # ─── Line Dispatcher ──────────────────────────────────────────────────────

    def _dispatch_line(self, line: str) -> None:
        """Route a raw serial line to the appropriate parser and signal."""
        if not line:
            return

        # Frame telemetry (most frequent — check first)
        if line.startswith(("MGMT:", "DAT:")):
            pkt = self._parse_frame(line)
            if pkt:
                self.packet_received.emit(pkt)
            return

        # Scan result
        if line.startswith("SCAN:"):
            result = self._parse_scan(line)
            if result:
                self.scan_result.emit(result)
            return

        # Scan done
        if line.startswith("SCAN_DONE:"):
            m = _SCAN_DONE_RE.match(line)
            if m:
                self.scan_complete.emit(int(m.group(1)))
            return

        # Target lock
        if line.startswith("TARGET:"):
            target = self._parse_target(line)
            if target:
                self.target_locked.emit(target)
            return

        # Status message
        if line.startswith("STATUS:"):
            m = _STATUS_RE.match(line)
            if m:
                code = m.group(1)
                msg  = m.group(2) or ""
                self.esp_status.emit(code, msg)
            return

    # ─── Parsers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_frame(line: str) -> Optional[dict]:
        """Parse a MGMT/DAT telemetry line (v1 or v2 format)."""
        m = _FRAME_RE.match(line)
        if not m:
            return None
        prefix, rssi_s, size_s, sub_s, bssid, ch_s = m.groups()
        pkt = {
            "prefix":       prefix,
            "rssi":         int(rssi_s),
            "payload_size": int(size_s),
            "subtype":      int(sub_s),
        }
        if bssid:
            pkt["bssid"] = bssid.upper()
        if ch_s:
            pkt["channel"] = int(ch_s)
        return pkt

    @staticmethod
    def _parse_scan(line: str) -> Optional[dict]:
        """Parse a SCAN: AP result line."""
        m = _SCAN_RE.match(line)
        if not m:
            return None
        return {
            "ssid":    m.group(1),
            "bssid":   m.group(2).upper(),
            "channel": int(m.group(3)),
            "rssi":    int(m.group(4)),
        }

    @staticmethod
    def _parse_target(line: str) -> Optional[dict]:
        """Parse a TARGET: lock line."""
        m = _TARGET_RE.match(line)
        if not m:
            return None
        return {
            "ssid":    m.group(1),
            "bssid":   m.group(2).upper(),
            "channel": int(m.group(3)),
        }

    # ─── Pure Hardware Loop ───────────────────────────────────────────────────


# ─── Utility: enumerate available serial ports ────────────────────────────────

def list_serial_ports() -> list[str]:
    """Return a list of available serial port names on this system."""
    if not SERIAL_AVAILABLE:
        return []
    ports = serial.tools.list_ports.comports()
    return sorted(p.device for p in ports)
