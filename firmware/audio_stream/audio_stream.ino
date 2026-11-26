// Section 3B: raw 16 kHz mono PCM, 20 ms per UDP packet.
// Uploading starts continuous LAN audio transmission when Wi-Fi is connected.
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP_I2S.h>
#include <esp_system.h>
#include "secrets.h"

constexpr uint16_t PI_PORT = 5007;
constexpr size_t SAMPLES = 320;
constexpr size_t HEADER_BYTES = 20;
constexpr uint32_t SAMPLE_RATE = 16000;
I2SClass microphone;
WiFiUDP udp;
IPAddress pi;
int16_t pcm[SAMPLES];
uint8_t packet[HEADER_BYTES + sizeof(pcm)];
uint32_t sessionId, sequence = 0, sent = 0, failed = 0;
uint32_t lastReconnect = 0, lastReport = 0;
bool socketReady = false;

void put32(size_t offset, uint32_t value) {
  for (size_t i = 0; i < 4; ++i) packet[offset + i] = (value >> (8 * i)) & 0xff;
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  if (!pi.fromString(PI_IP) || NODE_NUMBER == 0) {
    Serial.println("ERROR: check PI_IP and positive NODE_NUMBER in secrets.h");
    while (true) delay(1000);
  }
  microphone.setPinsPdmRx(42, 41);
  if (!microphone.begin(I2S_MODE_PDM_RX, SAMPLE_RATE,
                        I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO)) {
    Serial.println("ERROR: microphone initialization failed");
    while (true) delay(1000);
  }
  microphone.setTimeout(250);
  sessionId = esp_random();
  memcpy(packet, "KHA1", 4);
  put32(12, NODE_NUMBER);
  put32(16, SAMPLE_RATE);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setSleep(false);
  lastReconnect = millis();
  Serial.println("Streaming raw audio to the Pi on UDP 5007. Unplug to stop.");
}

void loop() {
  // Read continuously even while offline, avoiding a backlog of stale audio.
  size_t bytes = microphone.readBytes(reinterpret_cast<char*>(pcm), sizeof(pcm));
  if (bytes != sizeof(pcm)) {
    // A capture discontinuity starts a new session; never silently join timelines.
    sessionId = esp_random();
    sequence = 0;
    Serial.println("ERROR: incomplete capture; new session, restart Pi recording");
    delay(10);
    return;
  }
  uint32_t currentSequence = sequence++;
  if (WiFi.status() != WL_CONNECTED) {
    if (socketReady) { udp.stop(); socketReady = false; }
    if (millis() - lastReconnect >= 15000) {
      WiFi.reconnect();
      lastReconnect = millis();
    }
  } else {
    if (!socketReady) socketReady = udp.begin(5008) == 1;
    if (socketReady) {
      put32(4, sessionId);
      put32(8, currentSequence);
      // ESP32-S3 stores signed int16 PCM in little-endian order.
      memcpy(packet + HEADER_BYTES, pcm, sizeof(pcm));
      bool ok = false;
      if (udp.beginPacket(pi, PI_PORT)) {
        size_t written = udp.write(packet, sizeof(packet));
        ok = udp.endPacket() == 1 && written == sizeof(packet);
      }
      if (ok) ++sent; else ++failed;
    }
  }
  if (millis() - lastReport >= 2000) {
    lastReport = millis();
    if (Serial) Serial.printf("WiFi:%s | sent:%lu | send_failed:%lu | RSSI:%d dBm\n",
                             WiFi.status() == WL_CONNECTED ? "connected" : "offline",
                             (unsigned long)sent, (unsigned long)failed, WiFi.RSSI());
  }
}
