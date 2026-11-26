# Hardware and assembly

## Selected components

| Component | Quantity selected/purchased | Purpose / connection |
| --- | --- | --- |
| Raspberry Pi 5, 4GB | 1 | Central hub; Ethernet to router preferred |
| Official Pi 5 case with fan | 1 | Enclosure and temperature-controlled cooling |
| Official Pi 27W USB-C power supply | 1 | Dedicated power for the Pi |
| XIAO ESP32-S3 Sense | 3 | Wi-Fi listening nodes with microphone expansion boards |
| USB-A to USB-C data cable | 1 initially | Flashing and powering a node |
| Existing Kasa smart plugs and a lamp | Reuse | First controlled device |

An RP2040 KB2040 board was included as a promotional extra in the original hardware order. It has no assigned role in this architecture and is not required for the MVP.

Other required accessories: a microSD card for the Pi (32GB is sufficient for the initial OS/code), a way to write it, an Ethernet cable if using wired networking, and USB cables/adapters for each independently placed node. Their current ownership/availability is not fully recorded here; check before ordering. No microSD card is needed in a node for the current network tests.

## End-node assembly

With USB disconnected:

1. Attach the included antenna to the tiny round Wi-Fi/Bluetooth connector. Gently align the cap, seat one side, then press the opposite side. Never force a misaligned connector or pull on the thin cable.
2. Keep the antenna away from metal and avoid folding it against the board. Secure it mechanically when choosing an enclosure.
3. For microphone work, fit the Sense expansion board using its intended board-to-board connector. Wi-Fi-only testing does not require microphone initialization.
4. If fitting a heatsink, use the correct kit and the vendor's placement for that board revision. Keep connectors, buttons, microphone opening, and camera clear; verify the thermal-pad location rather than sticking a loose heatsink across components.
5. Use a USB data cable to flash the firmware. Afterward, a suitable USB wall adapter can power the node remotely.

Follow [Seeed's assembly guide](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) for the exact board and heatsink variant. Do not confuse the RF connector with the camera/expansion connectors. Soldering GPIO headers is unnecessary for these two connectivity sketches.

## Pi assembly

The official case fan plugs into the Pi 5's dedicated four-pin **FAN** socket, not arbitrary GPIO pins. Disconnect power before plugging it in and align the keyed connector. Follow the [official case product documentation](https://www.raspberrypi.com/products/raspberry-pi-5-case/) for case/heatsink installation. The case includes cooling; do not buy a second cooler solely because the standalone Active Cooler exists.

The Pi should run Raspberry Pi OS with Python 3. A monitor/keyboard is optional if SSH was configured during OS imaging. The node uses Arduino firmware and does not boot Raspberry Pi OS.

## Power

USB wall power is the default for permanent listening nodes. The Pi's 27W supply rating is its maximum capacity, not constant consumption. Likewise, a node connected to a 10W adapter does not necessarily consume 10W.

Earlier planning estimates of roughly 0.5–1W per node at the wall and hours-to-days battery runtime are **unmeasured estimates**. Continuous radio/microphone processing, firmware, adapter efficiency, and power-bank cutoff behavior change the result. Measure the assembled firmware with a USB meter and, for wall consumption, a suitable AC meter before using those estimates for battery sizing or operating cost.

Rechargeable battery pads exist on the XIAO, but custom battery wiring is outside the MVP. Sleep modes that stop sampling cannot simultaneously provide continuous listening.

## Placement and microphone quality

The selected Sense node is an inexpensive development board, not a validated far-field room microphone. Test speech at the intended distance with TV/music/fan noise. A better microphone array can improve intelligibility without proving lower processing latency.

Alternatives considered:

- [ESP32-S3-Korvo-2](https://www.espressif.com/en/dev-board/esp32-s3-korvo-2-en): two-microphone development board recommended by Espressif for ESP-SR work.
- [Home Assistant Voice Preview Edition](https://www.home-assistant.io/voice-pe/): packaged voice satellite with dedicated audio processing; raw-whistle preservation must be verified.
- [ReSpeaker Lite](https://wiki.seeedstudio.com/reSpeaker_usb_v3/): USB/I2S microphone array; firmware/channel selection and whistle handling need validation.
- USB microphone directly on the Pi: removes wireless audio transport but limits physical placement.

None is selected as a mandatory upgrade. Compare measured recognition quality and end-to-end delay before replacing the current hardware.

## Purchase links

These identify the selected products, not guaranteed current prices or stock:

- [Pi 5 4GB](https://www.pishop.us/product/raspberry-pi-5-4gb/)
- [Official Pi supply](https://www.adafruit.com/product/5814)
- [Official case/fan](https://www.adafruit.com/product/5816)
- [XIAO ESP32-S3 Sense](https://www.seeedstudio.com/XIAO-ESP32S3-Sense-p-5639.html)
- [USB data cable](https://www.adafruit.com/product/4474)
- [USB wall adapter](https://www.adafruit.com/product/1994)
- [32GB microSD](https://www.pishop.us/product/microsd-card-32-gb-class-10-blank/)
- [Ethernet cable](https://www.monoprice.com/product?p_id=49071)

Receipts, shipping addresses, account information, and actual Wi-Fi credentials do not belong in this public repository.
