#!/usr/bin/env python3
# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.
from __future__ import annotations
import sys
import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
import config
from styles.theme import QSS, apply_pyqtgraph_theme
from ui.main_window import MainWindow
from ui.splash_screen import SplashScreen
import warnings

warnings.filterwarnings(
    "ignore", message="overflow encountered in cast", category=RuntimeWarning
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="S.P.E.C.T.R.E. — Signal Processing & Electronic Cyber Security "
        "Reconnaissance Engine",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with synthetic telemetry (no hardware required)",
    )
    p.add_argument(
        "--port",
        default="",
        help="Pre-select a COM port on startup (e.g. /dev/ttyUSB0 or COM3)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName("SPECTRE Systems")

    # ─ CRITICAL FIX: Prevent app from quitting when splash closes ──────────
    app.setQuitOnLastWindowClosed(False)

    # Font setup
    font = QFont("Lexend", 12)
    font.setStyleHint(QFont.StyleHint.Monospace)
    app.setFont(font)

    # ── Theme ──────────────────────────────────────────────────────────────
    app.setStyleSheet(QSS)
    apply_pyqtgraph_theme()

    # ── 1. SHOW SPLASH SCREEN FIRST ──────────────────────────────────────────
    splash = SplashScreen(duration_ms=21000, video_path="assets/intro.mp4")
    splash.show()
    app.processEvents()  # Force splash to render immediately

    # ── 2. LOAD MAIN WINDOW IN BACKGROUND (Hidden) ───────────────────────────
    window = MainWindow()

    # ─ 3. SEQUENCE: Switch to Main Window after 20 seconds ──────────────────
    def transition_to_main():
        # Show main window FIRST to keep the app alive
        window.show()
        window.raise_()
        window.activateWindow()

        # Then close splash
        splash.close()

        # Re-enable normal quit behavior
        app.setQuitOnLastWindowClosed(True)

    # Wait for the splash video to finish naturally instead of a hardcoded timer
    splash.finished.connect(transition_to_main)

    # Auto-connect in demo mode (delayed slightly to ensure UI is ready)
    if args.demo:
        QTimer.singleShot(
            21000,
            lambda: window._banner.connect_requested.emit("DEMO", True),
        )

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())