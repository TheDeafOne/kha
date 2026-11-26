#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_system.h>
#include "secrets.h"

constexpr uint16_t PI_PORT = 5005;
constexpr uint16_t NODE_PORT = 5006;
constexpr uint32_t TIMEOUT_MS = 500;
WiFiUDP udp;
IPAddress pi;
bool socketReady = false;
uint32_t sessionId, sequence = 0, sent = 0, acknowledged = 0;
uint32_t lastAttempt = 0, maxRtt = 0;
uint64_t totalRtt = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);
  if (!pi.fromString(PI_IP)) {
    Serial.println("Invalid PI_IP: enter the Pi's IPv4 address in secrets.h");
    while (true) delay(1000);
  }
  sessionId = esp_random();
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setSleep(false);
  lastAttempt = millis();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    if (socketReady) { udp.stop(); socketReady = false; }
    Serial.println("Wi-Fi disconnected; waiting to reconnect");
    if (millis() - lastAttempt >= 15000) {
      WiFi.reconnect();
      lastAttempt = millis();
    }
    delay(1000);
    return;
  }
  if (!socketReady) {
    socketReady = udp.begin(NODE_PORT);
    if (!socketReady) { Serial.println("UDP bind failed"); delay(1000); return; }
    Serial.print("Node IP: "); Serial.println(WiFi.localIP());
  }
  // Drain delayed responses so they cannot satisfy a later probe.
  while (udp.parsePacket()) while (udp.available()) udp.read();
  char message[160];
  snprintf(message, sizeof(message), "kha:%s:%08lx:%lu", NODE_ID,
           (unsigned long)sessionId, (unsigned long)++sequence);
  const size_t length = strlen(message);
  uint32_t started = millis();
  bool queued = false;
  if (udp.beginPacket(pi, PI_PORT)) {
    size_t written = udp.write((const uint8_t*)message, length);
    queued = udp.endPacket() == 1 && written == length;
  }
  if (!queued) { Serial.println("Local UDP send failed"); delay(1000); return; }
  ++sent;
  bool replied = false;
  while (millis() - started < TIMEOUT_MS) {
    int size = udp.parsePacket();
    if (size) {
      bool sourceMatches = udp.remoteIP() == pi && udp.remotePort() == PI_PORT;
      char reply[160];
      int count = udp.read(reply, sizeof(reply));
      if (sourceMatches && size == (int)length && count == (int)length &&
          memcmp(message, reply, length) == 0) {
        uint32_t rtt = millis() - started;
        ++acknowledged;
        totalRtt += rtt;
        if (rtt > maxRtt) maxRtt = rtt;
        Serial.printf("Reply OK | RTT: %lu ms | mean: %.1f ms | max: %lu ms | RSSI: %d dBm\n",
                      (unsigned long)rtt, (double)totalRtt / acknowledged,
                      (unsigned long)maxRtt, WiFi.RSSI());
        replied = true;
        break;
      }
    }
    delay(1);
  }
  if (!replied) Serial.println("TIMEOUT: no matching Pi reply within 500 ms");
  Serial.printf("Replies: %lu/%lu | missed/late: %.1f%%\n",
                (unsigned long)acknowledged, (unsigned long)sent,
                100.0 * (sent - acknowledged) / sent);
  delay(1000);
}
