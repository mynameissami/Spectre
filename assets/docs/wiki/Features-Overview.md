# Features Overview

S.P.E.C.T.R.E. provides a comprehensive suite of wireless security tools. Here's every feature organized by category.

---

## 🛡️ Defensive & Analytics

### Live Telemetry & DSP
Real-time signal processing with dual-trace RSSI visualization:
- **Raw RSSI trace** — Unfiltered signal strength from the ESP32
- **Smoothed RSSI trace** — Exponentially weighted moving average for trend analysis
- **Channel spectrum waterfall** — Heatmap of signal activity across Wi-Fi channels
- **Payload throughput monitor** — Bytes/second sliding window

### Wi-Fi Analyzer
Full-featured wireless analysis suite (see [[Wi‐Fi Analyzer]] for details):
- **Channel Occupancy Graph** — Bar chart showing networks per channel (2.4 GHz / 5 GHz)
- **Rolling Signal Strength History** — Time-series plot of RSSI per BSSID
- **Access Point Table** — Sortable list of discovered networks with SSID, BSSID, RSSI, channel, encryption
- **Channel Rating** — Congestion scoring with star ratings and "RECOMMENDED" markers
- **Sonar Mode** — Lock onto a single SSID for deep signal tracking

### Reconnaissance Engine
Automated network discovery using ARP and ICMP probes:
- Live host discovery on any subnet
- Port scanning (top ports) per host
- OUI-based vendor identification via IEEE MAC database
- Rogue/honeypot AP detection and hidden SSID identification

### Intrusion Detection System (IDS)
Rule-based IDS with real-time traffic rate calculation:
- **Deauth Flood Detection** — Triggers on excessive deauthentication frame rates
- **Beacon Spam Detection** — Flags anomalous beacon frame counts
- **Probe Storm Detection** — Detects excessive probe request activity
- Visual `MONITORING` / `TRIGGERED` states per rule
- Configurable thresholds per rule

### Threat Monitor
Intelligent sliding-window attack detection:
- Deauthentication rate analysis with source concentration tracking
- Persistence measurement (distinguishes brief bursts from sustained attacks)
- Multi-source congestion vs. single-source attack differentiation
- Automatic "THREAT CLEARED" notifications

### PMKID Capture Simulation
Educational demonstration of WPA2 PMKID/EAPOL key exchange:
- Simulated 4-way handshake capture
- HMAC-SHA1 PMKID computation display
- Shows the vulnerability in key exchange protocols

### Timeline Event Logging
Persistent timeline that records:
- Attack start/stop events with timestamps
- IDS trigger events
- Threat level changes (ALERT → OK)
- Reconnection events

---

## ⚔️ Offensive Operations

### 802.11 RF Attacks (via ESP32)
Requires the ESP32 hardware interface:
- **Deauthentication Flood** — Mass deauth frames to disconnect clients
- **Beacon Spam** — Flood the airspace with fake SSIDs
- **Probe Request Storm** — Generate excessive probe requests

### L2/L3 Network Attacks (via Scapy)
Software-based attacks using raw sockets:
- **ARP Flood** — Device crash / DoS via ARP cache overflow
- **DHCP Starvation** — Exhaust DHCP pool to deny new connections
- **DNS Flood** — Overwhelm DNS servers
- **ICMP Ping Storm** — ICMP-based DoS
- Configurable intensity slider

### Network Topology Map
Interactive visualization of discovered network devices and their relationships on the local network.

---

## 🕵️‍♂️ Man-In-The-Middle (MITM)

See [[MITM Guide]] for detailed usage.

- **ARP Spoofing** — Active ARP cache poisoning
- **DNS Spoofing** — Forge DNS responses for traffic redirection
- **Credential Harvester** — Passive HTTP credential capture
- **Payload Injector** — Inject JavaScript into intercepted HTTP responses
- **Session Hijacking Test** — Cookie theft demonstration
- **Dynamic Web Server** — Auto-hosted HTTP server on port 80

---

## 🎨 UI & Customization

### Multi-Theme Engine
Four built-in themes with instant switching (see [[Theming]]):
- **Dark Hacker** — Green-on-black matrix aesthetic
- **Deep Blue** — Naval radar, navy with cyan accents
- **Blood Red** — Aggressive dark crimson palette
- **Monochrome** — Clean silver/white on near-black

### Configurable Font Sizes
Per-region font scaling with live preview:
- Global UI, Menu Bar, Labels & Headers, Buttons, Event Log, Tables & Lists, Plot Axis Labels

### AI Assistant
Groq-powered (LLaMA 3.3 70B) contextual AI:
- MAC address vendor lookups (OUI database)
- Network diagnostics assistance
- Contextual security explanations

### Settings Panel
Full settings dialog:
- **Appearance Tab** — Theme selection, font sizes
- **Performance Tab** — FPS target, antialiasing toggle, OpenGL toggle
- **About Tab** — Version info, license, disclaimer

### Splash Screen
Cinematic intro video with audio playback on application startup.

---

**See also:** [[Wi‐Fi Analyzer]] · [[MITM Guide]] · [[Attack Vectors]] · [[Theming]]
