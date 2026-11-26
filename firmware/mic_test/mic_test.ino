// XIAO ESP32-S3 Sense: microphone health check for Arduino ESP32 3.x.
// Raw PDM input; no Wi-Fi, speech gate, noise suppression, or recording.
#include <ESP_I2S.h>
#include <math.h>
#include <stdint.h>

I2SClass microphone;
constexpr uint32_t SAMPLE_RATE = 16000;
constexpr size_t BLOCK_SAMPLES = 320;  // 20 ms
int16_t samples[BLOCK_SAMPLES];
int64_t sum = 0;
uint64_t sumSquares = 0;
uint32_t count = 0;
int32_t minimum = 32767, maximum = -32768;

void setup() {
  Serial.begin(115200);
  delay(2000);
  microphone.setPinsPdmRx(42, 41);  // clock, data; documented Sense PDM mic
  if (!microphone.begin(I2S_MODE_PDM_RX, SAMPLE_RATE,
                        I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO)) {
    Serial.println("ERROR: microphone initialization failed");
    while (true) delay(1000);
  }
  microphone.setTimeout(250);
}

void loop() {
  size_t bytes = microphone.readBytes(reinterpret_cast<char*>(samples), sizeof(samples));
  if (bytes == 0 || bytes % sizeof(int16_t) != 0) {
    Serial.println("ERROR: incomplete microphone read; check the Sense expansion board");
    delay(100);
    return;
  }
  for (size_t i = 0; i < bytes / sizeof(int16_t); ++i) {
    int32_t sample = samples[i];
    sum += sample;
    sumSquares += static_cast<int64_t>(sample) * sample;
    if (sample < minimum) minimum = sample;
    if (sample > maximum) maximum = sample;
    ++count;
  }
  if (count >= SAMPLE_RATE / 10) {  // roughly 10 updates per second
    double mean = static_cast<double>(sum) / count;
    double variance = static_cast<double>(sumSquares) / count - mean * mean;
    if (variance < 0) variance = 0;
    Serial.printf("RMS:%.1f\tPeakToPeak:%ld\n", sqrt(variance),
                  static_cast<long>(maximum - minimum));
    sum = 0;
    sumSquares = 0;
    count = 0;
    minimum = 32767;
    maximum = -32768;
  }
}
