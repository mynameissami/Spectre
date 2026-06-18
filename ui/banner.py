# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/banner.py — Top Banner Widget
Contains: App title/subtitle, COM port selector, Connect/Disconnect button,
and overall running status indicator.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QSpinBox,
)

import config
from core.telemetry import list_serial_ports


class Banner(QWidget):
    """
    Top banner bar.

    Signals:
        connect_requested(port: str, demo: bool)  — user clicked Connect
        disconnect_requested()                      — user clicked Disconnect
        ma_window_changed(int)                      — MA window spinbox changed
    """

    connect_requested:    Signal = Signal(str, bool)
    disconnect_requested: Signal = Signal()
    ma_window_changed:    Signal = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("banner")
        self.setFixedHeight(70)
        self._connected = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 8, 16, 8)
        root.setSpacing(0)

        # ── Left: Branding ────────────────────────────────────────────────
        branding = QVBoxLayout()
        branding.setSpacing(2)

        title = QLabel("S.P.E.C.T.R.E. ENGINE OS v1.0")
        title.setObjectName("title")
        branding.addWidget(title)

        subtitle = QLabel(
            "SIGNAL PROCESSING & ELECTRONIC CYBER SECURITY RECONNAISSANCE ENGINE"
        )
        subtitle.setObjectName("subtitle")
        branding.addWidget(subtitle)

        root.addLayout(branding)
        root.addStretch()

        # ── Centre: Controls ──────────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setSpacing(10)

        # MA Window spinbox
        ma_lbl = QLabel("MA WIN:")
        ma_lbl.setObjectName("status_key")
        ctrl.addWidget(ma_lbl)

        self._ma_spin = QSpinBox()
        self._ma_spin.setRange(2, 100)
        self._ma_spin.setValue(config.MA_WINDOW)
        self._ma_spin.setToolTip("Moving average window size (samples)")
        self._ma_spin.valueChanged.connect(self.ma_window_changed)
        ctrl.addWidget(self._ma_spin)

        # Separator
        sep = _VSep()
        ctrl.addWidget(sep)

        # COM port selector
        port_lbl = QLabel("PORT:")
        port_lbl.setObjectName("status_key")
        ctrl.addWidget(port_lbl)

        self._port_combo = QComboBox()
        self._port_combo.setEditable(True)
        self._port_combo.setToolTip("Select or type serial port (e.g., /dev/ttyUSB0 or /dev/ttyACM0)")
        self._refresh_ports()
        ctrl.addWidget(self._port_combo)

        # Refresh button
        ref_btn = QPushButton("⟳")
        ref_btn.setFixedSize(28, 28)
        ref_btn.setToolTip("Refresh port list")
        ref_btn.setStyleSheet(
            f"font-size:14px; border:1px solid {config.COLOR_BORDER};"
            f" color:{config.COLOR_TEXT_DIM}; background:transparent;"
            f" border-radius:3px; padding:0;"
        )
        ref_btn.clicked.connect(self._refresh_ports)
        ctrl.addWidget(ref_btn)

        # Connect / Disconnect button
        self._conn_btn = QPushButton("CONNECT")
        self._conn_btn.setMinimumWidth(110)
        self._conn_btn.clicked.connect(self._on_conn_click)
        ctrl.addWidget(self._conn_btn)

        root.addLayout(ctrl)
        root.addStretch()

        # ── Right: Status indicator ────────────────────────────────────────
        self._status_lbl = QLabel("STANDBY")
        self._status_lbl.setObjectName("big_status_paused")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setMinimumWidth(110)
        root.addWidget(self._status_lbl)

    # ─── Slots ─────────────────────────────────────────────────────────────────

    def _on_conn_click(self) -> None:
        if self._connected:
            self.disconnect_requested.emit()
        else:
            port = self._port_combo.currentText()
            self.connect_requested.emit(port, False)

    def _refresh_ports(self) -> None:
        current = self._port_combo.currentText()
        self._port_combo.blockSignals(True)
        self._port_combo.clear()

        ports = list_serial_ports()
        if ports:
            self._port_combo.addItems(ports)

        idx = self._port_combo.findText(current)
        if idx >= 0:
            self._port_combo.setCurrentIndex(idx)

        self._port_combo.blockSignals(False)

    # ─── State Updates ─────────────────────────────────────────────────────────

    def set_connected(self, connected: bool, port: str = "") -> None:
        self._connected = connected
        if connected:
            self._conn_btn.setText("DISCONNECT")
            self._conn_btn.setObjectName("disconnect_btn")
            self._conn_btn.setStyleSheet("")          # force QSS restyle
            self._status_lbl.setText("RUNNING")
            self._status_lbl.setObjectName("big_status_running")
            self._status_lbl.setStyleSheet("")
            self._port_combo.setEnabled(False)
        else:
            self._conn_btn.setText("CONNECT")
            self._conn_btn.setObjectName("")
            self._conn_btn.setStyleSheet("")
            self._status_lbl.setText("STANDBY")
            self._status_lbl.setObjectName("big_status_paused")
            self._status_lbl.setStyleSheet("")
            self._port_combo.setEnabled(True)


class _VSep(QFrame):
    """Thin vertical separator line."""
    def __init__(self) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFixedWidth(1)
        self.setStyleSheet(f"color:{config.COLOR_BORDER};")
