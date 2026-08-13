# Attack Vectors

S.P.E.C.T.R.E. supports two categories of offensive operations: **802.11 RF Attacks** (via the ESP32 hardware interface) and **L2/L3 Network Attacks** (via Scapy on the host machine).

> ⚠️ **Only use these on networks you own or have explicit authorization to test.**

---

## 802.11 RF Attacks (ESP32 Required)

These attacks require a connected ESP32 microcontroller running the S.P.E.C.T.R.E. Edge Sensor firmware. The ESP32 handles all raw 802.11 frame injection.

### Deauthentication Flood

Sends mass deauthentication frames to disconnect clients from a target access point.

- **Target:** Selected via the ESP32's on-device menu (lock onto a BSSID)
- **Effect:** All clients associated with the target AP are forcibly disconnected
- **Intensity:** Configurable via the slider

### Beacon Spam

Floods the 2.4 GHz airspace with fake beacon frames advertising non-existent SSIDs.

- **Effect:** Nearby devices see dozens of fake networks in their Wi-Fi list
- **Use case:** Testing client behaviour when encountering many SSIDs

### Probe Request Storm

Generates excessive probe request frames to overwhelm access points.

- **Effect:** APs waste resources responding to fake probe requests
- **Use case:** Testing AP resilience under probe load

---

## L2/L3 Network Attacks (Scapy)

These attacks run on the host machine using Scapy for raw packet crafting. They require root/administrator privileges.

### ARP Flood (DoS / Device Crash)

Sends a massive volume of ARP packets to overwhelm a target device's ARP cache.

- **Target:** IP address of the victim device
- **Effect:** Can cause device crashes, network disconnects, or severe performance degradation
- **Intensity:** Controls packets per second

### DHCP Starvation (DoS)

Exhausts the DHCP server's available IP address pool by sending numerous DHCP Discover packets with randomized MAC addresses.

- **Target:** The local DHCP server (typically the router)
- **Effect:** New devices cannot obtain IP addresses and join the network

### DNS Flood (DoS / Server Crash)

Sends a high volume of DNS query packets to a target DNS server.

- **Target:** IP address of the DNS server
- **Effect:** Server becomes unresponsive, denying DNS resolution to legitimate clients

### ICMP Ping Storm (DoS)

Floods a target with ICMP Echo Request packets.

- **Target:** IP address of the victim
- **Effect:** Bandwidth saturation and potential device/network unresponsiveness

---

## Attack Configuration

All attacks share common configuration options in the Attack Panel:

| Control | Description |
|---|---|
| **Target IP** | The victim's IP address (L2/L3 attacks) |
| **Attack Vector** | Dropdown to select the specific attack type |
| **Intensity Slider** | Controls the rate/aggressiveness of the attack |
| **FIRE / CEASEFIRE** | Start or stop the attack |

---

## Safety & Ethics

- **Never** use these tools on public or unauthorized networks
- **Always** obtain written permission before testing
- These features exist for **education** and **authorized penetration testing** only
- The ESP32 attacks are particularly dangerous as they operate at the physical radio layer

---

**See also:** [[MITM Guide]] · [[ESP32 Hardware]] · [[Features Overview]]
