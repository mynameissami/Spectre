# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
config.py — S.P.E.C.T.R.E. Engine Global Configuration
All tunable constants live here for easy access.
"""

# ─── Application Meta ─────────────────────────────────────────────────────────
APP_NAME = "S.P.E.C.T.R.E. Engine OS"
APP_VERSION = "v1.0"
APP_TITLE = f"{APP_NAME} {APP_VERSION}"

# ─── Window Geometry ──────────────────────────────────────────────────────────
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
WINDOW_MIN_W = 1200
WINDOW_MIN_H = 700

# ── Serial / Wire Protocol ───────────────────────────────────────────────────
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 1.0  # seconds read timeout
SERIAL_RECONNECT_DELAY = 2.0  # seconds between reconnect attempts

# ─── DSP Parameters ───────────────────────────────────────────────────────────
BUFFER_LEN = 200  # Fixed deque length for RSSI history
MA_WINDOW = 20  # Moving average sliding window width (samples)

# ── Plot / Render ────────────────────────────────────────────────────────────
PLOT_UPDATE_INTERVAL_MS = 16  # ~60 FPS target
RSSI_Y_MIN = -100  # dBm axis floor
RSSI_Y_MAX = 0  # dBm axis ceiling
CHANNEL_MIN = 1
CHANNEL_MAX = 13

# ─── Threat Thresholds ────────────────────────────────────────────────────────
DEAUTH_SUBTYPE = 12  # 802.11 Deauthentication frame subtype
DEAUTH_ALERT_THRESH = 15  # frames / second to trigger alert
DEAUTH_WINDOW_SEC = 1.0  # sliding window duration

# ─── Event Log ────────────────────────────────────────────────────────────────
EVENT_LOG_MAX_LINES = 500  # hard cap on log lines in QTextEdit

# ─── Colour Palette ──────────────────────────────────────────────────────────
COLOR_BG = "#0A0A0A"
COLOR_PANEL_BG = "#0F0F0F"
COLOR_BG_PANEL = "#0F0F0F"  # <-- ADDED: Alias for panel background
COLOR_BORDER = "#1A1A2E"
COLOR_ACCENT_GREEN = "#00FF41"  # cyber matrix green
COLOR_ACCENT_RED = "#FF3333"  # critical red
COLOR_ACCENT_ORANGE = "#FFA500"  # warning orange
COLOR_ACCENT_CYAN = "#00D4FF"  # info cyan
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_DIM = "#5A5A6A"
COLOR_PLOT_BG = "#050508"
COLOR_PLOT_GRID = "#1A1A2E"

# Plot Traces
COLOR_RAW_RSSI = "#FF3333"  # red dotted
COLOR_SMOOTH_RSSI = "#00FF41"  # green solid

# Channel Spectrum
COLOR_SPECTRUM_BASE = "#00D4FF"
COLOR_SPECTRUM_HOT = "#FFA500"

# ─── Layout Ratios ────────────────────────────────────────────────────────────
LEFT_PANEL_RATIO = 7  # 70%
RIGHT_PANEL_RATIO = 3  # 30%

# ─── Demo / Simulation Mode ───────────────────────────────────────────────────
DEMO_PACKET_RATE_HZ = 120  # synthetic packets per second in demo mode

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Leave empty in .env to disable AI vendor lookup
