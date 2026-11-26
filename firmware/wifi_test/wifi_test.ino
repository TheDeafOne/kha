#include <WiFi.h>
#include "secrets.h"

uint32_t lastAttempt = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setSleep(false);
  lastAttempt = millis();
  Serial.println("kha: Wi-Fi test started");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("CONNECTED | IP: ");
    Serial.print(WiFi.localIP());
    Serial.printf(" | RSSI: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.printf("NOT CONNECTED | status: %d\n", (int)WiFi.status());
    if (millis() - lastAttempt >= 15000) {
      WiFi.reconnect();
      lastAttempt = millis();
    }
  }
  delay(2000);
}
