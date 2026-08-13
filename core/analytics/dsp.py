# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/dsp.py — DSP Engine
Maintains RSSI history buffers and provides real-time signal processing.

Operations:
    - Raw RSSI accumulation (fixed deque)
    - Moving average via NumPy convolution
    - Per-channel packet count tracking (for spectrum plot)
"""

from __future__ import annotations

from collections import deque, defaultdict
from typing import Tuple

import numpy as np

import config


class DSPEngine:
    """
    Stateful DSP processor for incoming Wi-Fi telemetry.

    Thread Safety:
        All methods are called from the *main* (GUI) thread via Qt signals,
        so no locks are required here.
    """

    def __init__(
        self,
        buffer_len: int = config.BUFFER_LEN,
        ma_window:  int = config.MA_WINDOW,
    ) -> None:
        self._buffer_len = buffer_len
        self._ma_window  = ma_window

        # Fixed-size RSSI history
        self._raw_buf: deque[float] = deque(maxlen=buffer_len)

        # Channel packet counts  {channel_num: count}
        self._channel_counts: defaultdict[int, int] = defaultdict(int)

        # Pre-allocated smoothing kernel (updated when window changes)
        self._kernel = np.ones(ma_window) / ma_window

        # Running packet counter
        self.total_packets: int = 0

    # ─── Core Update ──────────────────────────────────────────────────────────

    def push(self, rssi: float, channel: int | None = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Ingest a new RSSI sample and optional channel tag.

        Returns:
            (raw_array, smoothed_array)  — both length == current buffer occupancy
        """
        self._raw_buf.append(float(rssi))
        self.total_packets += 1

        if channel is not None:
            ch = max(config.CHANNEL_MIN, min(config.CHANNEL_MAX, channel))
            self._channel_counts[ch] += 1

        raw = np.array(self._raw_buf, dtype=np.float32)
        smoothed = self._moving_average(raw)
        return raw, smoothed

    # ─── DSP Computations ─────────────────────────────────────────────────────

    def _moving_average(self, signal: np.ndarray) -> np.ndarray:
        """
        Sliding window moving average using mode='same' convolution.
        Edge artefacts are suppressed by normalising against actual window coverage.
        """
        if len(signal) < 2:
            return signal.copy()
        n = min(self._ma_window, len(signal))
        kernel = np.ones(n, dtype=np.float32) / n
        return np.convolve(signal, kernel, mode="same")

    # ─── Channel Spectrum ─────────────────────────────────────────────────────

    def get_channel_counts(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return (channels_array, counts_array) for channels 1–13.
        Suitable for direct use in a PyQtGraph BarGraphItem.
        """
        channels = np.arange(config.CHANNEL_MIN, config.CHANNEL_MAX + 1, dtype=np.float32)
        counts   = np.array(
            [self._channel_counts[ch] for ch in range(config.CHANNEL_MIN, config.CHANNEL_MAX + 1)],
            dtype=np.float32,
        )
        return channels, counts

    def reset_channel_counts(self) -> None:
        """Reset channel packet counts (e.g., on reconnect)."""
        self._channel_counts.clear()

    # ─── Configuration ────────────────────────────────────────────────────────

    def set_ma_window(self, window: int) -> None:
        """Update the moving average window size at runtime."""
        self._ma_window = max(1, int(window))
        self._kernel = np.ones(self._ma_window) / self._ma_window

    @property
    def ma_window(self) -> int:
        return self._ma_window

    def reset(self) -> None:
        """Clear all buffers (e.g., on new connection)."""
        self._raw_buf.clear()
        self._channel_counts.clear()
        self.total_packets = 0

    # ─── Stats ────────────────────────────────────────────────────────────────

    def current_rssi(self) -> float | None:
        """Most recent raw RSSI, or None if buffer is empty."""
        return self._raw_buf[-1] if self._raw_buf else None

    def peak_rssi(self) -> float | None:
        """Maximum (least negative) RSSI in the current buffer."""
        return max(self._raw_buf) if self._raw_buf else None

    def mean_rssi(self) -> float | None:
        """Mean of buffered RSSI values."""
        return float(np.mean(list(self._raw_buf))) if self._raw_buf else None
