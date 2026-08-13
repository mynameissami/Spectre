# Getting Started

## Launching S.P.E.C.T.R.E.

### Linux (Full Hardware Mode)
```bash
sudo ./.venv/bin/python main.py
```

### macOS (Full Hardware Mode)
```bash
sudo ./.venv/bin/python main.py
```

### Windows (Administrator Command Prompt)
```cmd
.venv\Scripts\python.exe main.py
```

### Demo Mode (Software Simulator)
If you don't have an ESP32 connected, you can run S.P.E.C.T.R.E. in software simulation mode.

Linux / macOS:
```bash
./.venv/bin/python main.py --demo
```

Windows:
```cmd
.venv\Scripts\python.exe main.py --demo
```

> **Why root/admin?** S.P.E.C.T.R.E. needs elevated privileges for raw socket access (Scapy), binding to port 80 (MITM web server), and ESP32 serial port access.

## The Splash Screen

On launch, you'll see a cinematic splash screen with the S.P.E.C.T.R.E. intro video. This plays automatically and transitions to the main interface. If the video can't play (e.g., missing FFmpeg codecs), it's safely skipped.

## Connection Banner

After the splash screen, you'll see the **Connection Banner** at the top of the interface. This is where you choose how to operate:

### Demo Mode (No Hardware Required)

When you run S.P.E.C.T.R.E. with the `--demo` command-line flag, the application automatically bypasses the hardware connection and launches the built-in software simulator. This generates:
- Synthetic RSSI telemetry with realistic signal fluctuations
- Simulated access point discoveries
- Fake deauthentication traffic for IDS testing
- Throughput data for the payload monitor

**Demo mode is the best way to explore the UI** without any hardware or network configuration. Additionally, you can find a **Host Demo AP** toggle inside the Attack Panel to broadcast a synthetic access point within the interface.

### Hardware Mode (ESP32 Required)

1. Flash the firmware from `esp32/spectre_edge_sensor.ino` to your ESP32
2. Connect the ESP32 via USB
3. Select the COM port from the dropdown (e.g., `/dev/ttyUSB0` on Linux, `COM3` on Windows)
4. Click **CONNECT** to begin streaming live serial telemetry

The ESP32 runs in Promiscuous Mode, capturing raw 802.11 frames and transmitting parsed telemetry at 115200 baud.

## Interface Layout

The main window is divided into several key areas:

| Area | Location | Purpose |
|---|---|---|
| **Connection Banner** | Top | COM port selection, CONNECT/DEMO buttons |
| **Left Panel** | Left sidebar | Dual-trace RSSI plot, spectrum waterfall, throughput monitor |
| **Center Tabs** | Center | Wi-Fi Analyzer, MITM, Attack, Recon, Documentation |
| **Right Panel** | Right sidebar | Event log, IDS rules, status indicators, timeline |
| **Menu Bar** | Top bar | Settings, AI Assistant |

## Command-Line Options

```bash
python main.py --help
```

| Flag | Description |
|---|---|
| `--port PORT` | Pre-select a COM port on startup (e.g., `/dev/ttyUSB0` or `COM3`) |

---

**Next:** [[Features Overview]]
