# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/sonar_engine.py — Signal Mapper (Sonar Beep Generator)

This engine generates radar-like ping sounds. The interval between pings
is dynamically calculated based on the RSSI of the target BSSID.
Runs seamlessly in the Qt event loop using QTimer.
"""

from __future__ import annotations
import os
from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtMultimedia import QSoundEffect

class SonarEngine(QObject):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._target_rssi = -100.0
        self._active = False
        
        # Load the beep sound
        self._beep = QSoundEffect(self)
        
        # Resolve absolute path for QUrl
        beep_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'beep.wav'))
        if os.path.exists(beep_path):
            self._beep.setSource(QUrl.fromLocalFile(beep_path))
            self._beep.setVolume(0.8)
            
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timeout)

    def set_rssi(self, rssi: float) -> None:
        """Update the current target RSSI. (-100 to -20)"""
        self._target_rssi = max(-100.0, min(-20.0, float(rssi)))

    def start(self) -> None:
        if self._active:
            return
        self._active = True
        self._timer.start(100) # Start immediately to do first check

    def stop(self) -> None:
        self._active = False
        self._timer.stop()
        self._target_rssi = -100.0

    def is_active(self) -> bool:
        return self._active

    def _on_timeout(self) -> None:
        if not self._active:
            self._timer.stop()
            return
            
        if self._target_rssi <= -95.0:
            self._timer.setInterval(500)
            return

        # Map RSSI [-90, -30] to Interval [1.5s, 0.15s]
        clamped_rssi = max(-90.0, min(-30.0, self._target_rssi))
        normalized = (clamped_rssi - (-90.0)) / (-30.0 - (-90.0))
        interval_sec = 1.5 - (1.35 * normalized)
        interval_ms = int(interval_sec * 1000)
        
        self._timer.setInterval(interval_ms)
        
        # Play sound
        if self._beep.status() == QSoundEffect.Status.Ready:
            self._beep.play()
