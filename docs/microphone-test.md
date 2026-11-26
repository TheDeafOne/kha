# Section 3A: microphone health check

First verify raw sound capture on one node. This test does not use the Pi, Wi-Fi, credentials, an SD card, or audio files. Uploading it replaces the running UDP test; that sketch can be restored later.

## Hardware

Unplug USB and verify the **Sense expansion board** (the board carrying the camera, microphone, and SD slot) is fitted securely to the XIAO. The microphone is on that expansion board, not the bare controller. Keep its opening uncovered. Reconnect USB using the data cable.

This sketch targets the PDM microphone wiring documented by Seeed: clock GPIO42, data GPIO41. If the board is a different hardware revision, verify its microphone and wiring before changing pins. An initialization success alone is not proof that a physical microphone is connected.

## Upload

1. Update the repository on your programming computer: `git pull --ff-only`, or download a fresh ZIP.
2. Open `firmware/mic_test/mic_test.ino` in Arduino IDE.
3. Select **Tools → Board → esp32 → XIAO_ESP32S3** and the node's USB port. If the toolbar board selector says no boards found, use the Tools menu directly; this is a known IDE dialog issue, not proof of broken USB hardware.
4. Enable **USB CDC On Boot**. Keep **esp32 by Espressif Systems 3.x** installed; the sketch uses its bundled `ESP_I2S.h`. Do not install a separate I2S library or use the old 2.x `I2S.h` example.
5. Upload, then open Serial Monitor at **115200 baud**. Press RESET once if needed.

## Observe

Expect lines resembling the following (illustrative values only):

```text
RMS:25.3    PeakToPeak:160
RMS:310.7   PeakToPeak:1850
```

- Stay quiet for a few seconds and note the baseline.
- Speak close to the microphone, then clap and whistle gently. Values should change noticeably with sound.
- Stop making sound and verify they settle back toward baseline.
- Repeat at the intended speaking distance; room noise and orientation affect results.

RMS is a DC-corrected signal-level measurement in sample units. PeakToPeak is the sample range in the same roughly 100 ms window. Neither is calibrated sound pressure in dB. Whistles should produce a response, but this code does not classify them or recognize phrases.

For a graph, close Serial Monitor and open **Tools → Serial Plotter**, also at 115200 baud. Each line provides labeled RMS and PeakToPeak series. Flat zero or an unchanging signal is not a pass; a changing signal can still be noise, so intentionally compare silence versus speech/whistling.

## Troubleshoot

- `ESP_I2S.h` not found: confirm Espressif's 3.x board package and the selected board. Do not substitute an unrelated library.
- No serial output: check USB CDC On Boot, upload again after changing it, and reopen the correct port.
- Initialization/read errors or flat readings: disconnect power, check the expansion-board connection and microphone opening, then verify hardware revision/pins against vendor documentation.
- Big levels in silence: check handling noise, airflow/fan noise, USB power, and microphone placement. Do not judge audio quality from level alone.

## Pass and next step

Pass when repeated sound/silence tests produce sensible corresponding level changes. Then follow [Section 3B](audio-streaming.md): send raw audio to the Pi, save a short opt-in WAV, and listen for intelligibility, clipping, and gaps. Neither Wi-Fi streaming nor recognition is included in this microphone-only sketch.

**Validation:** the API signature was checked against Espressif's Arduino ESP32 3.3.12 header and the wiring against Seeed's 3.x example. Firmware compilation and physical microphone behavior have not been verified in the preparation environment.

References:

- [Seeed Sense microphone guide (3.x example)](https://wiki.seeedstudio.com/xiao_esp32s3_sense_mic/)
- [Espressif ESP_I2S API](https://github.com/espressif/arduino-esp32/blob/3.3.12/libraries/ESP_I2S/src/ESP_I2S.h)
- [Arduino board-selector issue](https://github.com/arduino/arduino-ide/issues/2235)
