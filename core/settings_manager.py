# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/settings_manager.py — Persistent Application Settings

Manages reading and writing of user preferences to a local JSON file.
Provides typed accessors and a simple observer pattern for change notification.

Settings file location: <project_root>/.spectre_settings.json
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable


# ─── Default Font Configuration ──────────────────────────────────────────────

@dataclass
class FontSettings:
    """Granular font size settings for each UI region."""
    global_ui: int = 12        # All widgets default
    menu_bar: int = 12         # Menu bar and menus
    labels: int = 12           # Section headers, status labels
    buttons: int = 11          # Button text
    event_log: int = 10        # Event log / terminal output
    tables: int = 11           # QTreeWidget / QTableWidget cells
    plots: int = 9             # PyQtGraph axis tick labels


# ─── Default App Settings ─────────────────────────────────────────────────────

@dataclass
class AppSettings:
    """All configurable application settings with sensible defaults."""
    theme: str = "dark_hacker"
    font: FontSettings = field(default_factory=FontSettings)
    plot_fps: int = 60
    antialiasing: bool = True
    use_opengl: bool = False


# ─── Settings Manager Singleton ───────────────────────────────────────────────

class SettingsManager:
    """
    Singleton that loads/saves AppSettings to a local JSON file.

    Usage:
        mgr = SettingsManager.instance()
        mgr.settings.theme = "monochrome"
        mgr.save()
    """

    _instance: SettingsManager | None = None

    _SETTINGS_FILE = Path(__file__).parent.parent / ".spectre_settings.json"

    def __init__(self) -> None:
        self._settings: AppSettings = AppSettings()
        self._observers: list[Callable[[AppSettings], None]] = []
        self.load()

    @classmethod
    def instance(cls) -> "SettingsManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def settings(self) -> AppSettings:
        return self._settings

    # ── Persistence ───────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load settings from JSON file. Falls back to defaults on any error."""
        if not self._SETTINGS_FILE.exists():
            return
        try:
            with open(self._SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            font_data = data.pop("font", {})
            font = FontSettings(**{k: v for k, v in font_data.items() if k in FontSettings.__dataclass_fields__})
            self._settings = AppSettings(font=font, **{k: v for k, v in data.items() if k in AppSettings.__dataclass_fields__ and k != "font"})
        except Exception:
            self._settings = AppSettings()

    def save(self) -> None:
        """Persist current settings to JSON file."""
        data = asdict(self._settings)
        try:
            with open(self._SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SettingsManager] Could not save settings: {e}")

    # ── Observer Pattern ──────────────────────────────────────────────────────

    def subscribe(self, callback: Callable[[AppSettings], None]) -> None:
        """Register a callback that fires when settings are applied."""
        if callback not in self._observers:
            self._observers.append(callback)

    def notify(self) -> None:
        """Notify all observers (called after settings are applied)."""
        for cb in self._observers:
            try:
                cb(self._settings)
            except Exception as e:
                print(f"[SettingsManager] Observer error: {e}")
