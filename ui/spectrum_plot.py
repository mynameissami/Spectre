# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/spectrum_plot.py — Channel Congestion Spectrum
Displays per-channel (1–13) packet counts as a styled bar graph.
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout

import config
from styles.theme import make_plot_widget


class SpectrumPlot(QWidget):
    """
    Bar graph showing 2.4 GHz channel congestion (channels 1–13).
    Bar colours are gradient-mapped from cool→hot based on relative count.
    """

    _CHANNELS = np.arange(
        config.CHANNEL_MIN,
        config.CHANNEL_MAX + 1,
        dtype=np.float32,
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Section header
        hdr = QHBoxLayout()
        hdr.setContentsMargins(8, 4, 8, 0)
        lbl = QLabel("◈  CHANNEL CONGESTION  ·  2.4 GHz SPECTRUM")
        lbl.setObjectName("section_header")
        hdr.addWidget(lbl)
        hdr.addStretch()

        self._lbl_hot_ch = QLabel("HOT: --")
        self._lbl_hot_ch.setStyleSheet(
            f"font-size:10px; color:{config.COLOR_ACCENT_ORANGE}; "
            f"font-weight:bold; letter-spacing:1px;"
        )
        hdr.addWidget(self._lbl_hot_ch)
        layout.addLayout(hdr)

        # Plot
        self._plot = make_plot_widget(
            y_label="Packets",
            x_label="Channel",
        )
        self._plot.setXRange(0.0, 14.0)
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.setMenuEnabled(False)

        # Channel tick labels
        axis = self._plot.getAxis("bottom")
        axis.setTicks([
            [(float(i), str(i)) for i in range(config.CHANNEL_MIN, config.CHANNEL_MAX + 1)]
        ])

        # Build initial bar graph item
        n_ch = config.CHANNEL_MAX - config.CHANNEL_MIN + 1
        zeros = np.zeros(n_ch, dtype=np.float32)

        brushes = self._make_brushes(zeros)
        self._bars = pg.BarGraphItem(
            x=self._CHANNELS,
            height=zeros,
            width=0.7,
            brushes=brushes,
        )
        self._plot.addItem(self._bars)

        # Invisible text items for bar value labels
        self._labels: list[pg.TextItem] = []
        for ch in self._CHANNELS:
            ti = pg.TextItem(text="", color=config.COLOR_TEXT_DIM, anchor=(0.5, 1.0))
            ti.setPos(ch, 0)
            self._plot.addItem(ti)
            self._labels.append(ti)

        layout.addWidget(self._plot)

    # ─── Public API ────────────────────────────────────────────────────────────

    def update_data(self, channels: np.ndarray, counts: np.ndarray) -> None:
        """Update bar heights and colours from channel count arrays."""
        if len(counts) == 0:
            return

        max_count = counts.max() if counts.max() > 0 else 1

        # Rebuild bar graph with updated heights + colours
        brushes = self._make_brushes(counts)
        self._bars.setOpts(
            x=channels,
            height=counts,
            width=0.7,
            brushes=brushes,
        )

        # Update Y-axis range
        self._plot.setYRange(0, max(max_count * 1.2, 10))

        # Update per-bar count labels
        for i, (ch, cnt) in enumerate(zip(channels, counts)):
            if cnt > 0:
                self._labels[i].setText(str(int(cnt)))
                self._labels[i].setPos(ch, cnt)
            else:
                self._labels[i].setText("")

        # Hot channel label
        hot_idx = int(counts.argmax())
        hot_ch  = int(channels[hot_idx])
        if counts[hot_idx] > 0:
            self._lbl_hot_ch.setText(f"HOT: CH {hot_ch}  [{int(counts[hot_idx])} pkts]")

    # ─── Colour Gradient ──────────────────────────────────────────────────────

    @staticmethod
    def _make_brushes(counts: np.ndarray) -> list[pg.QtGui.QColor]:
        """
        Map count values to a colour gradient:
          low  → cyan  (#00D4FF)
          high → orange (#FFA500)
        """
        mx = counts.max() if counts.max() > 0 else 1
        brushes = []
        for c in counts:
            t = float(c) / mx          # 0.0 … 1.0
            # Linear interpolation in RGB space
            r = int(0x00 + t * (0xFF - 0x00))
            g = int(0xD4 + t * (0xA5 - 0xD4))
            b = int(0xFF + t * (0x00 - 0xFF))
            brushes.append(pg.mkBrush(r, g, b, 220))
        return brushes
