# Theming

S.P.E.C.T.R.E. features a runtime theme engine that applies colour palettes instantly — no application restart required.

---

## Built-in Themes

### Dark Hacker (Default)
The classic green-on-black matrix aesthetic.

| Property | Colour |
|---|---|
| Background | `#0A0A0A` |
| Accent Primary | `#00FF41` (Neon Green) |
| Accent Secondary | `#00D4FF` (Cyan) |
| Text | `#E0E0E0` |
| Alert | `#FF3333` (Red) |

### Deep Blue
Naval radar inspired, navy base with cyan accents.

| Property | Colour |
|---|---|
| Background | `#030712` |
| Accent Primary | `#00BFFF` (Deep Sky Blue) |
| Accent Secondary | `#4488FF` (Royal Blue) |
| Text | `#C0D8FF` |
| Alert | `#FF4455` |

### Blood Red
Aggressive dark crimson palette.

| Property | Colour |
|---|---|
| Background | `#080005` |
| Accent Primary | `#FF2244` (Crimson) |
| Accent Secondary | `#FF6688` (Rose) |
| Text | `#F0C0C8` |
| Alert | `#FF0000` |

### Monochrome
Clean silver/white on near-black.

| Property | Colour |
|---|---|
| Background | `#0D0D0D` |
| Accent Primary | `#E0E0E0` (Silver) |
| Accent Secondary | `#AAAAAA` (Grey) |
| Text | `#D0D0D0` |
| Alert | `#CC3333` |

---

## How the Theme Engine Works

The theme system follows a three-step pipeline:

### 1. `ThemePalette` (Data)
Each theme is a frozen dataclass (`core/theme_manager.py`) containing all colour values:
- Backgrounds (main, panel, plot, banner)
- Accents (primary, secondary, red, orange)
- Text (primary, dim)
- Plot traces (raw RSSI, smooth RSSI)
- Spectrum (base, hot)

### 2. `config.py` Mutation
When a theme is applied, `ThemeManager._mutate_config()` writes the palette values directly into the `config` module's global constants (e.g., `config.COLOR_ACCENT_GREEN = palette.accent_primary`).

### 3. QSS Rebuild
The `styles/qss.py` module reads from `config` to build a complete Qt stylesheet string. After mutation, the stylesheet is regenerated and applied via `QApplication.setStyleSheet()`.

### 4. Widget Refresh
After the global stylesheet is applied, the `theme_changed` signal triggers `refresh_theme()` on every panel that uses inline styles (settings sliders, plot axis colours, AP table headers, etc.).

---

## Switching Themes

1. Open **Settings** (menu bar or shortcut)
2. Go to the **Appearance** tab
3. Click a theme card — the preview applies instantly
4. Click **Apply** or **OK** to save

The selected theme persists across sessions via `.spectre_settings.json`.

---

## Architecture Reference

```
ThemePalette (dataclass)
    ↓
ThemeManager.apply()
    ├── _mutate_config()     → Updates config.COLOR_* constants
    ├── QPixmapCache.clear() → Invalidates cached SVG icons
    ├── build_qss()          → Regenerates QSS from config values
    ├── app.setStyleSheet()  → Applies to all Qt widgets
    └── theme_changed.emit() → Triggers refresh_theme() on panels
```

**Key files:**
- `core/theme_manager.py` — Palette definitions, theme application
- `styles/qss.py` — QSS stylesheet builder
- `styles/pyqtgraph_theme.py` — PyQtGraph-specific theming
- `config.py` — Global colour constants

---

**See also:** [[Features Overview]] · [[Architecture]]
