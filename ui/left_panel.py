# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/left_panel.py — Analytics & DSP Rendering Stack
Displays real-time signal processing visualizations:
- RSSI Time-Domain Scope (Raw vs Smoothed)
- Channel Congestion Spectrum (1-13)
- Throughput Degradation Monitor (KB/s)
"""

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from collections import deque
import config


class LeftPanel(QWidget):
    """Main analytical graphics stack for the S.P.E.C.T.R.E. desktop."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buffer_len = config.BUFFER_LEN
        self._sample_count: int = 0  # Monotonically increasing index for scrolling X

        # Fixed-size history buffers for throughput & RSSI
        self._rssi_raw_buf = deque(maxlen=self._buffer_len)
        self._rssi_smooth_buf = deque(maxlen=self._buffer_len)
        self._throughput_buf = deque(maxlen=self._buffer_len)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── 1. RSSI Time-Domain Scope ──────────────────────────────────
        self._plot_rssi = pg.PlotWidget()
        self._plot_rssi.setTitle("◈ RSSI TIME-DOMAIN SCOPE")
        self._plot_rssi.setLabel("left", "RSSI", units="dBm")
        self._plot_rssi.setLabel("bottom", "Samples")
        self._plot_rssi.showGrid(x=True, y=True, alpha=0.2)
        self._plot_rssi.setYRange(-100, 0, padding=0)
        self._plot_rssi.setBackground(config.COLOR_BG)
        self._plot_rssi.getPlotItem().getViewBox().setBorder(
            pg.mkPen(config.COLOR_ACCENT_GREEN, width=1)
        )

        self._curve_raw = self._plot_rssi.plot(
            pen=pg.mkPen("#FF3333", width=1.5, style=Qt.PenStyle.DashLine), name="Raw"
        )
        self._curve_smooth = self._plot_rssi.plot(
            pen=pg.mkPen("#00FF00", width=2), name="Smoothed"
        )
        self._plot_rssi.addLegend()
        layout.addWidget(self._plot_rssi, stretch=2)

        # ── 2. Channel Congestion Spectrum ─────────────────────────────
        self._plot_spectrum = pg.PlotWidget()
        self._plot_spectrum.setTitle("◈ CHANNEL CONGESTION SPECTRUM (2.4GHz)")
        self._plot_spectrum.setLabel("left", "Packet Count")
        self._plot_spectrum.setLabel("bottom", "Channel")
        self._plot_spectrum.showGrid(y=True, alpha=0.2)
        self._plot_spectrum.setXRange(0.5, 13.5, padding=0)
        self._plot_spectrum.setBackground(config.COLOR_BG)
        self._plot_spectrum.getPlotItem().getViewBox().setBorder(
            pg.mkPen(config.COLOR_ACCENT_CYAN, width=1)
        )

        self._bar_spectrum = pg.BarGraphItem(
            x=list(range(1, 14)),
            height=[0] * 13,
            width=0.6,
            brush=config.COLOR_ACCENT_CYAN,
        )
        self._plot_spectrum.addItem(self._bar_spectrum)
        layout.addWidget(self._plot_spectrum, stretch=1)

        # ── 3. Throughput Degradation Monitor ──────────────────────────
        # FIX 1: Create the widget FIRST
        self._plot_throughput = pg.PlotWidget()
        self._plot_throughput.setTitle("◈ NETWORK THROUGHPUT DEGRADATION")
        self._plot_throughput.setLabel("left", "Throughput", units="KB/s")
        self._plot_throughput.setLabel("bottom", "Time (s)")
        self._plot_throughput.showGrid(x=True, y=True, alpha=0.2)

        # FIX 2: Auto-scale the Y-axis so small values (like 1.14 KB/s) are visible
        self._plot_throughput.enableAutoRange(axis="y")

        self._plot_throughput.setBackground(config.COLOR_BG)
        self._plot_throughput.getPlotItem().getViewBox().setBorder(
            pg.mkPen(config.COLOR_ACCENT_ORANGE, width=1)
        )

        # FIX 3: Store the plot line as _curve_throughput
        self._curve_throughput = self._plot_throughput.plot(
            pen=pg.mkPen(config.COLOR_ACCENT_ORANGE, width=2), name="KB/s"
        )
        layout.addWidget(self._plot_throughput, stretch=1)

    # ─── Public Update API (Called from Main Thread) ─────────────────────

    def update_rssi(self, raw: np.ndarray, smoothed: np.ndarray) -> None:
        """Update dual-trace RSSI scope with a scrolling X-axis."""
        n = len(raw)
        if n == 0:
            return
        self._sample_count += 1
        # x-axis counts from (current_count - n) to current_count so the
        # graph scrolls rightward like an oscilloscope.
        x = np.arange(self._sample_count - n, self._sample_count, dtype=np.float32)
        self._curve_raw.setData(x, raw)
        self._curve_smooth.setData(x, smoothed)
        # Let pyqtgraph auto-scroll
        self._plot_rssi.setXRange(x[0], x[-1], padding=0.02)

    def update_spectrum(self, channels: np.ndarray, counts: np.ndarray) -> None:
        """Update channel congestion bar graph."""
        if len(counts) == 13:
            self._bar_spectrum.setOpts(height=counts)

    def update_throughput(self, throughput_samples: list[float]) -> None:
        """Update the network throughput degradation graph."""
        if not hasattr(self, "_curve_throughput"):
            return
        if not throughput_samples:
            return

        # Take at most the last 120 timer ticks (~2 min at 1 Hz)
        samples = list(throughput_samples)[-120:]
        n = len(samples)

        # X-axis: real elapsed seconds, newest sample = 0 s ago
        # e.g. for 60 samples: [-59, -58, …, -1, 0]
        time_axis = np.arange(-(n - 1), 1, dtype=np.float32)

        self._curve_throughput.setData(time_axis, samples)
        # Always show the latest point at x=0 on the right edge
        self._plot_throughput.setXRange(time_axis[0], 0, padding=0.02)
