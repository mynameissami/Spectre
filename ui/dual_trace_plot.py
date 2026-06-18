# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/dual_trace_plot.py — Real-time Dual-Trace Time Domain Scope
Renders Raw RSSI (red dotted) and Moving Average (green solid) traces.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout

import config
from styles.theme import make_plot_widget


class DualTracePlot(QWidget):
    """
    PyQtGraph PlotWidget wrapped in a QWidget, displaying two live traces:
      - Raw RSSI       (red, dotted/dashed pen, higher weight)
      - Smoothed MA    (green, solid pen)

    Data is pushed externally by calling update_data().
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── Header row with legend ─────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setContentsMargins(8, 4, 8, 0)

        section_lbl = QLabel("◈  TIME DOMAIN  ·  RSSI ANALYSIS")
        section_lbl.setObjectName("section_header")
        hdr.addWidget(section_lbl)
        hdr.addStretch()

        # Legend pills
        for color, text in [
            (config.COLOR_RAW_RSSI,    "─ ─  RAW"),
            (config.COLOR_SMOOTH_RSSI, "──  SMOOTHED"),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"font-size:10px; color:{color}; font-weight:bold; "
                f"letter-spacing:1px;"
            )
            hdr.addWidget(lbl)

        layout.addLayout(hdr)

        # ── Plot ───────────────────────────────────────────────────────────
        self._plot = make_plot_widget(
            y_label="RSSI (dBm)",
            x_label="Sample",
        )
        self._plot.setYRange(config.RSSI_Y_MIN, config.RSSI_Y_MAX)
        self._plot.setXRange(0, config.BUFFER_LEN)

        # Disable mouse panning/zoom for locked display
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.setMenuEnabled(False)

        # ── Raw trace — red dashed ──────────────────────────────────────
        raw_pen = pg.mkPen(
            color=config.COLOR_RAW_RSSI,
            width=1,
            style=Qt.PenStyle.DashLine,
        )
        self._raw_curve = self._plot.plot(
            pen=raw_pen,
            name="Raw RSSI",
        )

        # ── Smoothed trace — green solid ────────────────────────────────
        smooth_pen = pg.mkPen(
            color=config.COLOR_SMOOTH_RSSI,
            width=2,
        )
        self._smooth_curve = self._plot.plot(
            pen=smooth_pen,
            name="Moving Average",
        )

        # Horizontal reference lines
        for y_val, label_text in [(-30, "-30 dBm"), (-60, "-60 dBm"), (-80, "-80 dBm")]:
            ref = pg.InfiniteLine(
                pos=y_val,
                angle=0,
                pen=pg.mkPen(config.COLOR_BORDER, width=1, style=Qt.PenStyle.DotLine),
                label=label_text,
                labelOpts={
                    "color": config.COLOR_TEXT_DIM,
                    "position": 0.02,
                    "rotateAxis": None,
                },
            )
            self._plot.addItem(ref)

        layout.addWidget(self._plot)

        # ── Stats bar ──────────────────────────────────────────────────────
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(8, 2, 8, 4)
        stats_layout.setSpacing(24)

        self._lbl_current = self._make_stat("CURRENT", "-- dBm")
        self._lbl_peak    = self._make_stat("PEAK",    "-- dBm")
        self._lbl_mean    = self._make_stat("MEAN",    "-- dBm")
        self._lbl_samples = self._make_stat("SAMPLES", "0")

        for lbl_pair in [self._lbl_current, self._lbl_peak, self._lbl_mean, self._lbl_samples]:
            stats_layout.addWidget(lbl_pair[0])
            stats_layout.addWidget(lbl_pair[1])

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

    def _make_stat(self, key: str, value: str) -> tuple[QLabel, QLabel]:
        key_lbl = QLabel(key + ":")
        key_lbl.setObjectName("status_key")
        val_lbl = QLabel(value)
        val_lbl.setObjectName("status_value")
        return key_lbl, val_lbl

    # ─── Public API ────────────────────────────────────────────────────────────

    def update_data(self, raw: np.ndarray, smoothed: np.ndarray) -> None:
        """Push new raw + smoothed arrays to both plot curves."""
        n = len(raw)
        x = np.arange(n, dtype=np.float32)

        self._raw_curve.setData(x=x, y=raw)
        self._smooth_curve.setData(x=x, y=smoothed)

        # Update stat labels
        if n > 0:
            self._lbl_current[1].setText(f"{raw[-1]:.0f} dBm")
            self._lbl_peak[1].setText(f"{raw.max():.0f} dBm")
            self._lbl_mean[1].setText(f"{raw.mean():.1f} dBm")
            self._lbl_samples[1].setText(str(n))
