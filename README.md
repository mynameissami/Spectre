# S.P.E.C.T.R.E. Engine OS

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-red.svg)](https://doc.qt.io/qtforpython/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#)

> [!WARNING]  
> **LEGAL DISCLAIMER:** This project is a dual-use security tool provided exclusively for **educational purposes, academic research, and authorized network security auditing**. Intercepting network traffic, performing Denial-of-Service (DoS) attacks, or creating rogue access points on unauthorized networks is strictly illegal. The maintainers are **NOT** responsible for any misuse of this framework. Please read the full [DISCLAIMER.md](DISCLAIMER.md) before proceeding.

**Signal Processing & Electronic Cyber Security Threat Reconnaissance Engine**

S.P.E.C.T.R.E. Engine OS is an advanced, real-time telemetry processing, spectrum visualization, and wireless diagnostics platform. It provides a comprehensive suite of defensive analytics, offensive operations, and man-in-the-middle (MITM) tools wrapped in a high-performance PySide6 graphical user interface.

## 🚀 Features

### 🛡️ Defensive & Analytics
*   **Live Telemetry & DSP:** Real-time signal processing, RSSI visualization, and channel spectrum analysis using `numpy` and `pyqtgraph`.
*   **Reconnaissance Engine:** Automated discovery of access points, rogue/honeypot networks, and hidden SSIDs.
*   **Intrusion Detection System (IDS):** Rule-based IDS that dynamically calculates live traffic rates to detect anomalies like Deauth Floods, Beacon Spam, and Probe Storms, offering visual `MONITORING` and `TRIGGERED` states.
*   **Threat Monitor:** Sliding-window attack detection and payload throughput tracking.

### ⚔️ Offensive Operations
*   **802.11 RF Attacks:** Deauthentication floods, Beacon spamming, and Probe request storms.
*   **L2/L3 Network Attacks:** ARP floods, DHCP starvation, DNS floods, and ICMP Ping storms.
*   **Hardware Integration:** **IMPORTANT:** An ESP32 microcontroller is *required* as the hardware interface to perform physical L1/L2 and 802.11 wireless pentesting attacks (such as RF transmission, spoofing, and signal injection).

### 🕵️‍♂️ Man-In-The-Middle (MITM)
*   **Active Vectors:** ARP Spoofing (Poisoning) and DNS Spoofing (Redirection).
*   **Passive Operations:** Credential Harvester with dual-pane real-time logging (separating active alerts from harvested data).
*   **Dynamic Web Server:** Built-in HTTP server (`core/web_server.py`) that dynamically hosts the `mitm_demo_site` on your local machine (Port 80). When DNS Spoofing is engaged, the L2 Engine intercepts UDP Port 53 queries and forges DNS responses to redirect the victim's traffic directly to this local web server, allowing for seamless credential harvesting or payload injection.

---

### 💻 Hardware Architecture: The Edge Sensor Node

S.P.E.C.T.R.E. utilizes an ESP32 microcontroller as a dedicated physical layer interceptor. By isolating the hardware radio from the host PC, the ESP32 can run its 2.4 GHz antenna in pure Promiscuous Mode, catching raw 802.11 frames and filtering them before transmitting telemetry via USB.

#### Pinout Matrix

The physical navigation cluster relies on the ESP32's internal pull-up resistors (`INPUT_PULLUP`). Wire the tactile buttons directly to Ground (GND)—no external resistors are required.

| Component | ESP32 GPIO | Interface Type | Function Description |
| --- | --- | --- | --- |
| **ST7735 TFT Screen** | `GPIO 18` | SPI (SCK) | Clock Signal (SCL/SCK) |
| **ST7735 TFT Screen** | `GPIO 23` | SPI (MOSI) | Data Transmission (SDA/MOSI) |
| **ST7735 TFT Screen** | `GPIO 4` | Digital Out | Hardware Reset (RES/RST) |
| **ST7735 TFT Screen** | `GPIO 2` | Digital Out | Data/Command Toggle (DC/A0) |
| **ST7735 TFT Screen** | `GPIO 5` | SPI (CS0) | Chip Select (CS/CE) |
| **ST7735 TFT Screen** | `3V3` | Power | Backlight (BLK/LED) - *Always on* |
| **Navigation: UP** | `GPIO 13` | Digital In | Menu Up / Disengage Link |
| **Navigation: SELECT** | `GPIO 12` | Digital In | Menu Select / Arm Stream |
| **Navigation: DOWN** | `GPIO 14` | Digital In | Menu Down |
| **PC Bridge** | `USB TX/RX` | UART | 115200 Baud Telemetry Link |

#### Power & Routing Notes

* **Logic Levels:** The ST7735 logic requires **3.3V**. Do not bridge the `VCC` or `LED` pins to the 5V/VIN rail, as this will damage the display controller.
* **Common Ground:** Ensure all tactile buttons and the TFT display share a common ground (`GND`) with the ESP32.
* **Capacitive Filtering:** The ESP32's RF amplifier draws high transient currents during active packet injection or dense promiscuous sniffing. It is recommended to place a `10µF` capacitor across the `3V3` and `GND` rails to prevent brown-out resets.


## 📂 Directory Structure

The repository is structured to be modular and open-source friendly:

```text
Spectre/
├── core/                  # Backend engines (DSP, IDS, Recon, MITM, Local Web Server)
├── esp32/                 # C++ Firmware for the ESP32 hardware sniffer/injector
├── mitm_demo_site/        # HTML/JS assets served dynamically during DNS Spoofing
├── styles/                # PySide6 Qt Stylesheets (QSS) and UI Themes
├── ui/                    # PySide6 Frontend panels and GUI components
├── assets/                # Media, logos, and the intro video
├── main.py                # Main application entry point
├── config.py              # Global configuration, tuning, and threshold settings
├── .env                   # Environment variables (API Keys) - Ignored in Git
└── requirements.txt       # Python dependencies
```

## 🛠️ Installation

**1. Prerequisites**
Ensure you have Python 3.10+ installed.

**2. Clone and Setup Environment**
```bash
git clone https://github.com/yourusername/spectre-os.git
cd spectre-os
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configuration (Optional)**
If you are using the AI Assistant module, create a `.env` file in the root directory and add your API key:
```env
GROQ_API_KEY="your_api_key_here"
```

## 💻 Usage

To launch the S.P.E.C.T.R.E. Engine interface, ensure you have root/administrator privileges (required for raw socket access and local port 80 hosting), then run:

```bash
sudo ./.venv/bin/python main.py
```

### Modes of Operation
*   **Hardware Mode:** Flash the firmware located in `esp32/` to an ESP32 microcontroller. Select the appropriate COM port mapped to your external hardware and click `CONNECT` to stream live serial telemetry.
*   **Demo Mode:** Click `DEMO` on the connection banner to launch the built-in software simulator, which generates synthetic telemetry and network traffic to demonstrate the UI capabilities without hardware.

### How DNS Spoofing & Credential Harvesting Works
1. Navigate to the **MAN-IN-THE-MIDDLE** tab.
2. Select **DNS SPOOFING (Redirection)** or **CREDENTIAL HARVESTER**.
3. Once engaged, S.P.E.C.T.R.E. starts the background `DynamicWebServer` on `0.0.0.0:80`.
4. The `MITMEngine` begins listening for UDP traffic on Port 53.
5. When a device on the network requests a website (e.g., `http://example.com`), S.P.E.C.T.R.E. intercepts the DNS request and responds with the IP address of your machine.
6. The victim's browser is transparently routed to the `mitm_demo_site` hosted by S.P.E.C.T.R.E., simulating an interception or credential gathering scenario.

---

**Disclaimer:** *This software is designed exclusively for educational purposes and authorized network security auditing. Users are responsible for adhering to all applicable local, state, and federal laws.*