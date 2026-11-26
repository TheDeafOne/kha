# kha

Local home automation with Mandarin phrases and whistle patterns, using XIAO ESP32-S3 Sense microphone nodes and a Raspberry Pi hub.

The immediate goal is to establish reliable Wi-Fi and node-to-Pi communication before introducing audio. Low latency is a design goal, not a measured guarantee.

## Project documentation

- [Project brief](docs/project.md): what the system should do, goals, scope, and current status.
- [Architecture](docs/architecture.md): audio/event paths, networking, recognition, and multiple rooms.
- [Hardware](docs/hardware.md): components, assembly, power, and placement.
- [Implementation stages and validation](docs/implementation.md): staged work, acceptance checks, and latency measurement.
- [Decisions and research](docs/decisions.md): selected starting points, alternatives, caveats, and primary sources.

**Current milestone:** Wi-Fi connectivity has been reported working on the end nodes. Node-to-Pi round-trip testing is the next step; no physical audio or recognition results are recorded yet.

## Build sections

| Section | Included now | Pass condition |
| --- | --- | --- |
| 1. Node Wi-Fi | `firmware/wifi_test` | Node gets an IP and stays connected at its intended location |
| 2. Node-to-Pi communication | `firmware/node_link_test` and `pi/udp_echo.py` | Matching replies, stable round-trip time, few missed/late responses |
| 3. Microphone capture and streaming | Planned | Clear audio arrives without gaps; measure packet loss and buffering |
| 4. Mandarin and whistle recognition | Planned | Accurate triggers in realistic room noise, with measured delay |
| 5. Kasa device control | Planned | Explicit on/off commands operate a test lamp |
| 6. Multiple rooms | Planned | Unique node IDs, duplicate suppression, room routing, recovery after disconnections |

Recognition, audio streaming, BLE transport, and Kasa control are **not implemented** in this initial version. Central recognition versus on-node ESP-SR remains a choice to benchmark.

## Hardware

- One XIAO ESP32-S3 **Sense**, with its included antenna attached.
- USB data cable and a computer for programming. After programming, USB wall power is sufficient.
- Raspberry Pi running Raspberry Pi OS with Python 3. Connect by Ethernet if possible.
- A router providing 2.4 GHz Wi-Fi for the node. Internet access is not required during these tests.

The node joins your router; it does not connect directly to the Pi's Wi-Fi radio. The Pi may use Ethernet while the node uses Wi-Fi, as long as they can communicate on the same LAN. Guest-network/client isolation can block this connection.

## Get the code

Clone this repository or download its ZIP from GitHub. Commands below assume your terminal is in the repository root. On the Pi:

```bash
git clone https://github.com/TheDeafOne/kha.git
cd kha
```

## 1. Test Wi-Fi

1. With USB disconnected, attach the supplied antenna to its tiny round connector. Follow the [Seeed hardware guide](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/#installation-of-antenna). Put the board on a nonconductive surface.
2. Connect the node to your computer with a USB **data** cable.
3. Install [Arduino IDE](https://www.arduino.cc/en/software/).
4. Install **esp32 by Espressif Systems** in Boards Manager. If needed, add this URL in Preferences → Additional Boards Manager URLs:

   ```text
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```

5. Select board **XIAO_ESP32S3** and the USB port that appears when you connect it. Enable **USB CDC On Boot** if available.
6. Copy `firmware/wifi_test/secrets.example.h` to `firmware/wifi_test/secrets.h`. Enter your Wi-Fi name and password **locally**. The file is ignored by Git.
7. Open `firmware/wifi_test/wifi_test.ino` in Arduino IDE and upload it.
8. Open Tools → Serial Monitor, select **115200 baud**, and press RESET once.

Expected output (addresses and signal strength will differ):

```text
CONNECTED | IP: 192.168.1.123 | RSSI: -58 dBm
```

RSSI is received signal strength: a less-negative number is stronger. Aim initially for roughly -60 dBm or better, but use actual packet results to judge placement. Run for ten minutes in the intended location. Connectivity alone does not establish that audio streaming will work well.

## 2. Test node → Pi → node

### On the Pi

Find the Pi's LAN IPv4 address:

```bash
hostname -I
```

Use the address for Ethernet or Wi-Fi on your home LAN, not a Docker, VPN, or IPv6 address. Consider a router DHCP reservation to keep this address stable.

Start the receiver and leave it running:

```bash
python3 pi/udp_echo.py
```

No pip dependencies are required. By default, it listens on all IPv4 interfaces at UDP port 5005. To listen only on the Pi's LAN address:

```bash
python3 pi/udp_echo.py --host 192.168.1.50
```

Press Ctrl+C to stop. This is an unauthenticated diagnostic echo service, not a production command API. Use it on a trusted LAN; do not expose/forward its port to the internet. It echoes packets up to 2048 bytes and rejects larger packets.

### On the node

1. Copy `firmware/node_link_test/secrets.example.h` to `firmware/node_link_test/secrets.h`.
2. Enter Wi-Fi credentials and the Pi's IPv4 address. Use a unique `NODE_ID` (`node-01`, `node-02`, etc.) for each board.
3. Open `firmware/node_link_test/node_link_test.ino` and upload with the same Arduino board settings.
4. Open Serial Monitor at 115200 baud.

Expected node output:

```text
Reply OK | RTT: 8 ms | mean: 8.0 ms | max: 8 ms | RSSI: -55 dBm
Replies: 1/1 | missed/late: 0.0%
```

The Pi prints the sender address and received message. The node verifies the response's source and exact contents, including a boot session ID and sequence number, to avoid counting stale or other-node replies.

Run for at least five minutes at each intended node location. Record typical and maximum RTT and missed/late percentage. A 500 ms timeout counts a missing or late reply; it is **not** the delay we intentionally add to successful replies. Wi-Fi-disconnected periods and local send failures are logged separately and are not included in the reply percentage. Power-cycle the node to check reconnection.

RTT is the time from sending a probe until its reply arrives. It includes both network directions and scheduling. It is not one-way latency, recognition latency, or time to switch a light. One small probe per second is not a sustained audio load test.

## Troubleshooting

- **No USB port:** use a data-capable cable; try a different port. Hold BOOT while connecting USB, release it, select the new port, and upload again.
- **Blank Serial Monitor:** verify 115200 baud and the selected port. Enable USB CDC On Boot, re-upload, reopen the monitor, and press RESET.
- **No Wi-Fi connection:** verify the SSID/password, antenna attachment, and 2.4 GHz availability. Test near the router first.
- **Every probe times out:** verify the Pi IP, running receiver, and guest/client isolation. If you use a firewall, allow UDP 5005 from the trusted LAN rather than disabling the firewall. No router port forwarding is needed.
- **Intermittent replies:** test near the router and compare RSSI and RTT at the final location. Check USB power and interference before changing hardware.

## Checks and current validation

Run the receiver integration test on any computer with Python 3:

```bash
python3 -m unittest discover -s tests -v
```

It exercises actual UDP sockets, multiple simulated node endpoints, binary and empty packets, oversized-packet rejection, and recovery after rejection. It cannot validate the ESP32 radio, physical audio, or Pi/room performance. Firmware compilation and physical hardware testing must be reported separately from Python checks.

## Next implementation choices

- Audio: raw microphone samples with small buffers; preserve a raw path for whistles.
- Central Mandarin recognition candidate: [sherpa-onnx keyword spotting](https://k2-fsa.github.io/sherpa/onnx/kws/index.html). Benchmark the appropriate low-latency model with the user's chosen phrases.
- On-node Mandarin candidate: [ESP-SR MultiNet](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_command_recognition/README.html). Verify model/flash fit and actual recognition latency before adopting it.
- Whistles: distinguish pitch and duration patterns; avoid one-whistle/two-whistle ambiguity if fast response matters.
- Device control candidate: [python-kasa](https://python-kasa.readthedocs.io/en/latest/tutorial.html), with explicit on/off actions and duplicate suppression.
- BLE is a possible later command-event transport; no Bluetooth audio or BLE firmware is included.

## References

- [XIAO getting started and hardware](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)
- [XIAO Wi-Fi examples](https://wiki.seeedstudio.com/xiao_esp32s3_wifi_usage/)
- [XIAO Sense microphone](https://wiki.seeedstudio.com/xiao_esp32s3_sense_mic/)
- [Arduino ESP32 Wi-Fi API](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html)
- [Python socket API](https://docs.python.org/3/library/socket.html)

Do not commit Wi-Fi credentials, device credentials, recordings, or private network logs. Example IP addresses are placeholders. Before publishing changes, check `git diff --cached` and `git status`.
