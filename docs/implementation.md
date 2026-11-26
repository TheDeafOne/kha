# Implementation stages and validation

Work in small sections with a measured pass condition. The [README](../README.md) contains runnable instructions for sections 1 and 2.

## Section 1 — Wi-Fi

**Code:** `firmware/wifi_test/wifi_test.ino`.

Attach the antenna, configure local `secrets.h`, flash with Arduino IDE, and read Serial Monitor at 115200 baud. Test near the router and at the final location. Verify an IP address, RSSI, and ten minutes without unexplained disconnections. RSSI is context, not a packet reliability guarantee.

**Status:** reported working during setup. No measured reliability results are committed.

## Section 2 — Node-to-Pi communication

**Code:** `firmware/node_link_test/node_link_test.ino` and `pi/udp_echo.py`.

Run the receiver, configure the Pi IP in the node's local `secrets.h`, and compare received messages with matching replies. Run at least five minutes per placement. Record latest/mean/max RTT, missed/late probes, and separately observed Wi-Fi disconnections.

Repeat after a node power cycle and a brief receiver restart. A DHCP reservation avoids editing firmware each time the Pi address changes. Do not disable a firewall as a first troubleshooting step; permit the specific local diagnostic port if needed.

**Status:** code supplied; receiver integration test passes on loopback. Physical node/Pi results and firmware compilation remain unverified.

## Section 3 — Audio acquisition and transport

**Section 3A code:** `firmware/mic_test/mic_test.ino`. Follow the [microphone test guide](microphone-test.md) to compare signal levels in silence versus speech/whistling. Reported working during manual setup.

**Section 3B code:** `firmware/audio_stream/audio_stream.ino` and `pi/record_audio.py`. Follow the [streaming/recording guide](audio-streaming.md). Receiver logic passes automated tests; physical streaming results are pending.

First validate the microphone alone: capture a short explicitly enabled sample, confirm sample rate/channel/format, and listen for clipping, noise, or missing samples. Verify microphone hardware against board revision.

Then add sequenced audio transport and bounded receiver queues. Candidate: mono 16-bit PCM at 16 kHz in roughly 20 ms chunks. Measure sustained packet loss, gaps, arrival jitter, and accumulated buffering. Run the full expected number of nodes, not just one probe per second.

**Pass condition:** intelligible audio at the intended distance, bounded latency without queue growth, and documented gap handling. Choose numeric loss/jitter limits based on detector performance rather than inventing a guarantee in advance.

## Section 4 — Recognition

Start with two explicit light commands. Compare central sherpa-onnx with on-node ESP-SR where practical. Keep models initialized while listening; do not reload them for every command.

Run a separate whistle detector on raw samples. Test distinct pitch/duration patterns. Avoid treating speech VAD as the only trigger for a whistle path.

Create a small evaluation set with target commands, near-matches, ordinary conversation, TV/music, and silence. Include the actual user's pronunciation and intended microphone distances. Record:

- Correct detections and missed commands per phrase/pattern.
- False activations per hour of non-command audio.
- Median, 95th percentile, and worst observed recognition delay.
- CPU/memory use with concurrent nodes.

**Pass condition:** chosen commands work reliably in the target room with an explicitly accepted false-trigger/latency tradeoff. No numerical success threshold has been agreed yet.

## Section 5 — Device actions

Integrate an existing Kasa plug via `python-kasa`. Discover/initialize devices outside the time-critical command path and use explicit on/off actions. Confirm credentials and protocol compatibility for the exact plug model; newer plugs may require TP-Link credentials even for local communication.

Exercise commands with a lamp and record actual visible switching, not only API completion. Handle unavailable devices and retries without accumulating stale actions. Home Assistant can later supply scenes and broader integrations; it is optional for the first plug.

**Pass condition:** correct action, no uncommanded toggles, measured time to visible response, and safe recovery after a failed command.

## Section 6 — Multiple rooms and resilience

Assign unique node IDs and room mappings. Implement cross-node duplicate suppression, a deliberate node-selection policy, and explicit room overrides. Add connectivity indication, a mute strategy, clean restart behavior, and stale-event rejection.

Exercise router/hub/node restarts and representative background noise. Keep debug audio retention opt-in. Compare BLE command-event delivery only if the local-recognition approach is validated and Wi-Fi remains unsuitable.

**Pass condition:** one intended action per command/pattern with documented recovery behavior across the intended rooms.

## Measuring latency correctly

Break the total into capture buffering, transport, recognition/confirmation, action dispatch, and physical actuator response. Some stages overlap; do not blindly sum advertised model numbers.

The current UDP probe measures network **round-trip** time only. Dividing by two is at best an assumption about symmetry. Audio packet timestamps on different clocks cannot establish one-way delay without synchronization or a controlled measurement method.

For user-facing end-to-end measurements, a single synchronized recording of the command and lamp response can provide a practical baseline. Mark the end of the spoken phrase/whistle pattern and the visible response. Account for video frame resolution and report sample count, distance, noise, and missed trials. Repeated trials should include slow responses rather than reporting only the best one.

## Result template

Keep credentials and identifying network details out of public results. For each run record:

```text
Firmware/receiver revision:
Board and microphone revision:
Number of active nodes:
Placement/distance and background noise:
Transport and buffer settings:
Recognition model/settings (when applicable):
Duration/trial count:
RSSI range:
RTT median/p95/max (if measured):
Missed/late probes and disconnected periods:
End-to-end latency median/p95/max (when measured):
Detection accuracy / false triggers:
Observations and next change:
```
