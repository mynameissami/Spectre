# Wi-Fi Analyzer

The Wi-Fi Analyzer is one of S.P.E.C.T.R.E.'s core defensive modules. It provides real-time wireless environment analysis through four sub-tabs and a dedicated Sonar mode.

---

## Channel Occupancy Graph

Displays a bar chart of how many networks occupy each Wi-Fi channel.

- **2.4 GHz view** — Channels 1–14
- **5 GHz view** — Common non-DFS channels (36, 40, 44, 48, 149, 153, 157, 161, 165)
- Toggle between bands using the **Band** dropdown
- Each BSSID is assigned a unique colour via the `BSSIDColorRegistry`

The graph uses `pyqtgraph` `BarGraphItem` for high-performance rendering.

---

## Rolling Signal Strength History (Time Graph)

A live time-series plot showing RSSI over time for every discovered BSSID:

- Each network gets a unique colour (persistent across refreshes)
- X-axis shows elapsed time in seconds
- Y-axis shows RSSI in dBm
- The graph auto-scrolls and clears old data on each scan cycle

---

## Access Point Table

A sortable table listing all discovered access points:

| Column | Description |
|---|---|
| SSID | Network name (or `<Hidden>` for cloaked networks) |
| BSSID | MAC address of the access point |
| RSSI | Signal strength in dBm (colour-coded: green > -50, yellow > -70, red ≤ -70) |
| Channel | Operating channel |
| Encryption | Security type (WPA2, WPA3, Open, etc.) |

In **Mesh/Roaming** mode, the table highlights entries matching the target SSID.

---

## Channel Rating

Rates each channel's congestion level on a 10-point scale:

- **★★★★★★★★★★ (10.0)** — Empty channel, ideal
- **★★★★★★★☆☆☆ (7.0)** — Light usage
- **★★★★☆☆☆☆☆☆ (4.0)** — Moderate congestion
- **★☆☆☆☆☆☆☆☆☆ (1.0)** — Heavily congested

The scoring algorithm considers:
- **Co-channel penalty** — Networks on the exact same channel (weighted by RSSI)
- **Adjacent channel penalty** — Networks on overlapping channels (lighter weight)

The best channel is marked with a cyan **[RECOMMENDED]** tag.

---

## Sonar Mode

Sonar Mode locks the scanner onto a single SSID for focused analysis:

1. Click the **SONAR** button
2. Select a target SSID from the dropdown (populated from current scan results)
3. The Wi-Fi Analyzer filters all views to show only that SSID's BSSID(s)

This is useful for:
- Tracking a specific network's signal stability over time
- Monitoring mesh/roaming behaviour across multiple APs with the same SSID
- Deep analysis of a suspected rogue AP

Click **SONAR** again to exit and return to the full scan view.

---

## Controls

| Control | Function |
|---|---|
| **Band Dropdown** | Switch between 2.4 GHz and 5 GHz views |
| **SONAR Button** | Toggle Sonar mode on/off |
| **SONAR Dropdown** | Select target SSID (visible when Sonar is active) |
| **Mesh/Roaming Checkbox** | Enable mesh-aware mode for multi-AP SSID tracking |
| **Pause/Resume** | Freeze the display without stopping data collection |

---

**See also:** [[Features Overview]] · [[Architecture]]
