# Architecture

This page documents the high-level architecture of S.P.E.C.T.R.E., including the module layout, data flow, and design decisions.

---

## Module Map

```
Spectre/
├── core/                           # Backend — zero GUI dependencies
│   ├── ai/                         # AI integrations
│   │   ├── ai_assistant.py         #   Groq LLM chat interface
│   │   └── groq_vendor_lookup.py   #   MAC → Vendor OUI lookup via AI
│   ├── analytics/                  # Signal processing & detection
│   │   ├── dsp.py                  #   Digital Signal Processing (EMA, channel tracking)
│   │   ├── ids_engine.py           #   Intrusion Detection System (rule-based)
│   │   ├── pmkid_sim.py            #   PMKID capture simulation
│   │   ├── spectrum_analysis.py    #   Spectrum waterfall data
│   │   └── threat.py               #   Threat level assessment (deauth detection)
│   ├── hardware/                   # Physical layer interfaces
│   │   ├── simulator.py            #   Demo mode synthetic telemetry generator
│   │   ├── sonar_engine.py         #   Single-SSID focused scanning
│   │   └── telemetry.py            #   ESP32 serial communication (QThread)
│   ├── mitm/                       # Man-in-the-middle engines
│   │   ├── _scapy.py               #   Scapy import guard (shared across modules)
│   │   ├── arp.py                   #   ARP spoofing thread
│   │   ├── dns.py                   #   DNS spoofing thread
│   │   ├── engine.py                #   MITM orchestrator (QThread)
│   │   ├── harvester.py             #   HTTP credential harvester
│   │   ├── injector.py              #   HTTP payload injector
│   │   └── sniffer.py               #   Passive packet sniffer
│   ├── network/                    # Network operations
│   │   ├── l2_engine.py            #   L2/L3 attack engine (Scapy)
│   │   ├── network_scanner.py      #   ARP/ICMP host discovery
│   │   ├── port_scanner.py         #   TCP port scanning
│   │   ├── recon.py                #   Reconnaissance event detection
│   │   └── wifi_scanner.py         #   Wi-Fi scan result management
│   ├── oui/                        # IEEE OUI database
│   │   ├── data.py                 #   Full OUI → Vendor mapping
│   │   └── lookup.py               #   Lookup functions
│   ├── settings_manager.py         # Persistent settings (JSON file)
│   ├── theme_manager.py            # Runtime theme engine
│   └── web_server.py               # Dynamic HTTP server for MITM
│
├── styles/                         # Presentation layer
│   ├── __init__.py                 #   build_qss() entry point
│   ├── qss.py                      #   Full QSS stylesheet builder
│   ├── palette.py                  #   Colour parsing utilities
│   └── pyqtgraph_theme.py         #   PyQtGraph-specific theming
│
├── ui/                             # GUI layer (PySide6)
│   ├── attack/                     #   802.11 + L2/L3 attack panel
│   │   └── _panel.py
│   ├── main_window/                #   Main window (split into mixins)
│   │   ├── _window.py              #     Core window setup & layout
│   │   ├── _connection_handler.py  #     COM port / demo mode logic
│   │   ├── _menu_builder.py        #     Menu bar construction
│   │   ├── _mitm_handler.py        #     MITM signal wiring
│   │   └── _packet_handler.py      #     Telemetry processing & timer
│   ├── mitm/                       #   MITM control panel
│   │   ├── _config_pane.py         #     Target/gateway inputs
│   │   ├── _controls_pane.py       #     Engage/disengage buttons
│   │   ├── _log_pane.py            #     Dual-pane event log
│   │   ├── _panel.py               #     Main MITM panel container
│   │   └── _payload_pane.py        #     Payload type selector
│   ├── right_panel/                #   Right sidebar
│   │   ├── _event_log.py           #     Scrolling event log widget
│   │   ├── _ids_rules.py           #     IDS rule status display
│   │   ├── _panel.py               #     Right panel container
│   │   ├── _status.py              #     Status indicators
│   │   └── _timeline.py            #     Event timeline
│   ├── settings/                   #   Settings dialog
│   │   ├── about_tab.py            #     About / license / version
│   │   ├── appearance_tab.py       #     Theme selection + font sizes
│   │   ├── performance_tab.py      #     FPS, AA, OpenGL toggles
│   │   ├── settings_panel.py       #     Dialog container
│   │   └── widgets.py              #     Reusable widgets (ComboBox, LabelledSlider)
│   ├── wifi_analyzer/              #   Wi-Fi analysis suite
│   │   ├── _ap_table.py            #     Access point table
│   │   ├── _channel_graph.py       #     Channel occupancy graph
│   │   ├── _channel_rating.py      #     Channel congestion rating
│   │   ├── _color.py               #     BSSID colour registry
│   │   ├── _panel.py               #     Wi-Fi analyzer container
│   │   └── _time_graph.py          #     Rolling signal strength plot
│   ├── banner.py                   #   Connection banner
│   ├── doc_panel.py                #   Built-in documentation viewer
│   ├── left_panel.py               #   Left sidebar (RSSI, spectrum, throughput)
│   ├── recon_panel.py              #   Network reconnaissance panel
│   ├── splash_screen.py            #   Splash screen with video
│   └── topology_map.py             #   Network topology visualization
│
├── esp32/                          # ESP32 firmware (C++/Arduino)
│   └── spectre_edge_sensor.ino
├── mitm_demo_site/                 # Static HTML served during MITM
├── assets/                         # Media, screenshots, SVG icons
├── main.py                         # Entry point
├── config.py                       # Global constants & thresholds
└── requirements.txt                # Python dependencies
```

---

## Data Flow

### Telemetry Pipeline

```
ESP32 (Promiscuous Mode)
    → USB Serial (115200 baud, JSON frames)
    → TelemetryThread (core/hardware/telemetry.py)
    → Qt Signal: packet_received(dict)
    → PacketHandlerMixin._on_packet()
        ├── DSP.push() → raw/smooth RSSI
        ├── SpectrumAnalysis.add_packet()
        ├── ThreatEngine.update()
        ├── ReconEngine.process()
        └── IDSEngine.process_packet()
    → Timer (60 FPS) → _on_timer()
        ├── Update left panel plots
        ├── Update right panel status
        └── Update Wi-Fi analyzer
```

### Theme Pipeline

```
User selects theme in Settings
    → ThemeManager.apply(theme_name, app)
        ├── _mutate_config(palette) → config.COLOR_* updated
        ├── QPixmapCache.clear()
        ├── build_qss() → Full QSS string regenerated
        ├── app.setStyleSheet(qss)
        └── theme_changed.emit()
            → Every panel.refresh_theme()
                ├── Reapply inline stylesheets
                ├── Update pyqtgraph plot colours
                └── Repolish Qt widgets
```

---

## Design Principles

### Mixin-Based Main Window
The `MainWindow` is split into focused handler mixins to keep each file under ~250 lines:
- `_window.py` — Layout and widget creation
- `_packet_handler.py` — Telemetry processing
- `_connection_handler.py` — Serial/demo connections
- `_mitm_handler.py` — MITM signal wiring
- `_menu_builder.py` — Menu bar

### Scapy Import Guard
All Scapy imports are wrapped in try/except blocks with `SCAPY_AVAILABLE` flags. The GUI launches and Demo mode works even if Scapy is not installed.

### Config Mutation Pattern
Themes work by mutating `config.py` globals in-place, then rebuilding the QSS. This means any code that reads `config.COLOR_*` automatically gets the current theme's colours.

---

**See also:** [[Theming]] · [[Features Overview]]
