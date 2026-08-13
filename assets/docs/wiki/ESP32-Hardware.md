# ESP32 Hardware

S.P.E.C.T.R.E. uses an ESP32 microcontroller as a dedicated physical layer interceptor — the **Edge Sensor Node**. By isolating the hardware radio from the host PC, the ESP32 runs its 2.4 GHz antenna in pure Promiscuous Mode, catching raw 802.11 frames and transmitting parsed telemetry over USB serial.

---

## Requirements

| Component | Specification |
|---|---|
| **Microcontroller** | ESP32 (any variant with Wi-Fi) |
| **Display** | ST7735 1.8" TFT (128×160 or 160×128) |
| **Buttons** | 3× tactile push buttons (UP, SELECT, DOWN) |
| **Connection** | USB cable (data-capable, not charge-only) |
| **IDE** | Arduino IDE 2.x or PlatformIO |

### Required Arduino Libraries

- `Adafruit_GFX` — Graphics primitives
- `Adafruit_ST7735` — ST7735 TFT driver
- `WiFi` — Built-in ESP32 Wi-Fi
- `esp_wifi` — Low-level Wi-Fi API for promiscuous mode
- `DNSServer` — Captive portal DNS
- `WebServer` — Built-in HTTP server

---

## Pinout Matrix

The physical navigation cluster uses the ESP32's internal pull-up resistors (`INPUT_PULLUP`). Wire tactile buttons directly to Ground — no external resistors needed.

| Component | ESP32 GPIO | Interface | Function |
|---|---|---|---|
| **ST7735 TFT** | `GPIO 18` | SPI (SCK) | Clock signal |
| **ST7735 TFT** | `GPIO 23` | SPI (MOSI) | Data transmission |
| **ST7735 TFT** | `GPIO 4` | Digital Out | Hardware reset |
| **ST7735 TFT** | `GPIO 2` | Digital Out | Data/Command toggle |
| **ST7735 TFT** | `GPIO 5` | SPI (CS0) | Chip select |
| **ST7735 TFT** | `3V3` | Power | Backlight (always on) |
| **Button: UP** | `GPIO 13` | Digital In | Menu up / Disengage link |
| **Button: SELECT** | `GPIO 12` | Digital In | Menu select / Arm stream |
| **Button: DOWN** | `GPIO 14` | Digital In | Menu down |
| **PC Bridge** | `USB TX/RX` | UART | 115200 baud telemetry link |

---

## Power & Routing Notes

### Logic Levels
The ST7735 requires **3.3V** logic. **Do not** connect `VCC` or `LED` pins to the 5V/VIN rail — this will permanently damage the display controller.

### Common Ground
All buttons and the TFT display must share a common ground (`GND`) with the ESP32.

### Capacitive Filtering
The ESP32's RF amplifier draws high transient currents during:
- Active packet injection (deauth/beacon attacks)
- Dense promiscuous sniffing

Place a **10µF capacitor** across the `3V3` and `GND` rails to prevent brown-out resets.

---

## Flashing the Firmware

### Using Arduino IDE

1. Install the **ESP32 board package** via Board Manager
2. Open `esp32/spectre_edge_sensor.ino`
3. Install required libraries via Library Manager
4. Select your board (e.g., "ESP32 Dev Module")
5. Select the correct COM port
6. Click **Upload**

### Serial Monitor Settings

| Setting | Value |
|---|---|
| Baud Rate | 115200 |
| Line Ending | Newline |

---

## ESP32 Operating Modes

The firmware has five states:

| State | Description |
|---|---|
| `SCANNING` | Discovering nearby Wi-Fi networks, displaying on TFT |
| `DETAILS` | Viewing detailed info about a selected network |
| `IDLE` | Low-power idle after timeout (60 seconds of inactivity) |
| `STREAMING` | Actively transmitting telemetry to the PC via USB serial |
| `ATTACKING` | Executing an RF attack (deauth, beacon, probe) |

### Navigation

| Button | Action |
|---|---|
| **UP** | Move cursor up / Disengage serial link |
| **SELECT** | View details / Lock target / Arm serial stream |
| **DOWN** | Move cursor down |

---

## Serial Telemetry Format

The ESP32 transmits JSON-formatted telemetry frames over serial:

```json
{"rssi": -42, "channel": 6, "bssid": "AA:BB:CC:DD:EE:FF", "ssid": "MyNetwork", "subtype": 8}
```

| Field | Type | Description |
|---|---|---|
| `rssi` | int | Signal strength in dBm |
| `channel` | int | Wi-Fi channel (1-14 for 2.4 GHz) |
| `bssid` | string | Access point MAC address |
| `ssid` | string | Network name |
| `subtype` | int | 802.11 frame subtype (8=beacon, 4=probe, 12=deauth) |

---

**See also:** [[Getting Started]] · [[Attack Vectors]]
