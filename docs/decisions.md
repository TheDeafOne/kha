# Decisions, alternatives, and research

This page separates established project choices from candidates and unverified estimates. Links are primary vendor/project references used during planning; consult current documentation when implementing.

## Starting choices

| Choice | Rationale | Limit / revisit trigger |
| --- | --- | --- |
| Fixed Mandarin phrases plus whistles | Matches predictable hands-free home control | Vocabulary and wake-word policy are not finalized |
| XIAO ESP32-S3 Sense nodes | Inexpensive integrated microphone/Wi-Fi development hardware | Room-scale audio quality and board revisions need testing |
| Pi 5 4GB hub | Dedicated local service host with wired networking | Concurrent recognition capacity remains unmeasured |
| USB wall power | Continuous listening without battery-runtime constraints | Measure draw after real firmware exists |
| Wi-Fi first | Supports continuous audio and uses existing infrastructure | Actual placements may have poor coverage |
| Arduino for the first tests | Quick upload/serial workflow | ESP-IDF remains a candidate for production firmware |
| UDP echo for section 2 | Reveals connectivity, missing replies, and RTT | Not the final authenticated command/audio protocol |
| Direct Kasa API initially | Small one-device integration | Add Home Assistant for scenes/broader device support as needed |

## Recognition candidates

### Central sherpa-onnx

[sherpa-onnx keyword spotting](https://k2-fsa.github.io/sherpa/onnx/kws/index.html) provides Chinese and Chinese/English models and customizable keywords. The [Chinese/English 3M model documentation](https://k2-fsa.github.io/sherpa/onnx/kws/pretrained_models/index.html) describes `chunk-8` and `chunk-16` variants, with 160 ms and 320 ms model latency respectively, and notes the lower-latency/accuracy tradeoff. Matching model files must be used together; a chunk setting is not interchangeable with a differently exported model.

These are model figures, not measured command-to-light times on this setup. Benchmark the selected model, confidence settings, and phrase vocabulary. The runtime and pretrained weights can have different licensing conditions; inspect the selected model's license before redistributing weights. No models are bundled in this repo.

### ESP-SR MultiNet on the node

[Espressif's command recognition documentation](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_command_recognition/README.html) describes offline Chinese/English command recognition, user-defined commands, and continuous recognition on ESP32-S3. The vendor advertises delay within 500 ms, but its measurement boundary is not established as identical to sherpa's model figure or the end-to-end target here.

The [ESP-SR benchmark](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/benchmark/README.html) reports per-frame processing times and memory consumption. Processing a frame in roughly 11–12 ms does not mean an entire phrase is recognized that quickly. Validate model partition size, PSRAM, front-end settings, and concurrent tasks on the XIAO before adopting this path.

[Espressif's getting-started guide](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/getting_started/readme.html) recommends Korvo boards and demonstrates wake-word-plus-command recognition. Direct always-listening command behavior needs deliberate implementation and testing; do not assume the example enables it out of the box.

### Porcupine

[Porcupine](https://picovoice.ai/docs/faq/porcupine/) supports Mandarin custom wake words and was considered for fixed phrases. It is an alternative to evaluate, not part of the selected baseline. Account/access-key requirements, target-specific binaries, platform support, and current license terms must be checked before choosing it. Generic microcontroller support is not proof of ESP32-S3 support.

### General transcription / conversational assistants

Whisper and an LLM are not required for a small fixed command vocabulary. Home Assistant's [local voice guide](https://www.home-assistant.io/voice_control/voice_remote_local_assistant/) distinguishes closed-vocabulary Speech-to-Phrase from open-ended Whisper and reports substantially different performance by host. Neither an English demo nor another model's sub-second benchmark establishes Mandarin performance on this hardware.

## Audio and transport decisions

- Section 3B implements small audio packets and a fixed-size diagnostic recording buffer. A live jitter buffer and detector integration are still planned; physical latency is unmeasured.
- Keep raw microphone data available for the whistle detector. Speech enhancement can alter non-speech sounds; its effect must be tested.
- [ESP32-S3 Wi-Fi power-saving documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/wifi-driver/wifi-performance-and-power-save.html) explains the latency/power tradeoff. Initial sketches disable Wi-Fi sleep; this is not a complete interference or jitter solution.
- [ESP32-S3 Bluetooth documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/ble/overview.html) confirms BLE-only support, without Bluetooth Classic. BLE command events are plausible; audio-over-Bluetooth is not provided here.
- A USB microphone directly on the Pi eliminates the radio audio hop but changes placement flexibility. A more expensive microphone improves neither network conditions nor model delay by itself.

## Device integration

[python-kasa](https://python-kasa.readthedocs.io/en/latest/tutorial.html) provides asynchronous controls and documents device credential requirements. Keep credentials local and validate exact plug compatibility. If Home Assistant is introduced, use its [TP-Link integration](https://www.home-assistant.io/integrations/tplink/) and call explicit actions. Home Assistant is not presumed to be a major latency bottleneck without measurements.

## Open questions before expansion

1. Does the actual Sense microphone work reliably at the required distance?
2. How much loss/jitter occurs at each placement under sustained audio load?
3. Does central recognition or on-node ESP-SR give the best accuracy/latency balance for the chosen phrases?
4. What false-trigger rate is acceptable without a wake word?
5. Which whistle patterns remain distinguishable under TV/music/background noise?
6. How should the system resolve the same sound heard by multiple nodes?
7. What recovery, mute, and visible-feedback behavior is needed for everyday use?
8. Does Wi-Fi coverage need improvement, or would locally detected BLE events suffice?

## Claims to avoid

- Do not present the 200–500 ms design target as a measured guarantee.
- Do not equate RTT, per-frame compute, model latency, and physical device latency.
- Do not infer battery runtime from capacity alone or treat adapter ratings as measured draw.
- Do not assume BLE automatically fixes weak Wi-Fi coverage.
- Do not label proposed components or code as physically validated before testing.
