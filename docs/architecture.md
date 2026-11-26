# Architecture

## Initial design: central recognition

Each XIAO joins the home's 2.4 GHz Wi-Fi. The router connects it to the Pi, preferably over Ethernet on the Pi side. Nodes need power and Wi-Fi coverage, not a USB data cable back to the hub.

The connectivity test sends text probes; the separate Section 3B firmware now streams raw audio to a bounded WAV recorder. Recognition and actions below remain planned. The intended full path is:

1. Capture microphone samples on the node.
2. Send small, sequenced audio packets across the LAN.
3. Receive them on the Pi with bounded buffering and explicit gap handling.
4. Feed a speech path into a Mandarin keyword spotter and a raw-audio path into a whistle detector.
5. Map a detection to an explicit room/device/action.
6. Suppress duplicates and invoke a local device command.

Central recognition makes models and command mappings easier to update and compare. Its costs are continuous network traffic, sensitivity to Wi-Fi quality, and hub dependence. Multiple microphone streams also increase processing load and need separate detector state.

## Current diagnostic protocol

| Property | Value |
| --- | --- |
| Transport | IPv4 UDP over the local network |
| Pi receiver | Port 5005, configurable with `--port` |
| Node socket | Port 5006 on each node; distinct device IPs allow the same port |
| Payload | `kha:<node-id>:<boot-session>:<sequence>` |
| Pi response | Exact payload echoed to the source IP and source port |
| Response matching | Node checks source IP, source port, length, and exact payload |
| Timeout | 500 ms; replies arriving later count as missed/late |
| Probe pacing | One-second delay after each completed/timed-out probe |
| Statistics | Latest/mean/max RTT, RSSI, and missed/late percentage |

This is a diagnostic echo service, not a production device-command protocol. It has no authentication or encryption. Keep it on a trusted LAN and do not expose it with port forwarding. Future command transport needs sender authentication, replay/duplicate handling, and defined retry behavior.

Wi-Fi disconnections and local send failures are logged separately. The missed/late percentage covers only probes successfully queued locally; it is not total system availability. UDP reordering, duplication, loss, and delayed packets must be handled explicitly in the future streaming implementation.

## Planned audio transport

The Section 3B test implements 16 kHz, mono, signed 16-bit PCM in 20 ms packets. These settings have not been benchmarked on the physical network. Uncompressed payload at these settings is 32,000 bytes/second per node before headers; three nodes produce 96,000 bytes/second before overhead. Bandwidth alone is not proof of reliable low-latency delivery. See the [audio protocol and test guide](audio-streaming.md) for the implemented packet format and limits.

Audio packets carry a version/magic, numeric node identity, boot/capture session, sequence, sample rate, and raw PCM. Capture timestamps and a live jitter buffer are not implemented. The recording receiver uses fixed-size storage and fills missing sample slots with silence; this is not yet a live detector gap policy. Define detector resets/gap markers and stale-audio handling before using UDP audio in production.

The microphone hardware must be checked against the actual board revision. Seeed documents different microphone interfaces across revisions; verify the board and current vendor examples instead of assuming every Sense variant uses the same pins/API.

## Alternative: recognition on the node

An ESP32-S3 can potentially run ESP-SR MultiNet for fixed Mandarin commands and a separate lightweight whistle detector. The node then sends only a command event to the Pi. This avoids continuous audio transport and may reduce network-related variability, but does not prove a faster complete system: recognition latency, memory, accuracy, and task scheduling still need testing.

Whistles need access to raw samples before speech-specific noise suppression or voice-activity gating. Do not assume a speech-oriented front end preserves whistle patterns.

## Wi-Fi, BLE, and coverage

- XIAO ESP32-S3 supports 2.4 GHz Wi-Fi and Bluetooth Low Energy; Bluetooth Classic is not supported.
- BLE event messages are an alternative if recognition runs locally. BLE audio is not a drop-in replacement for the current streaming design.
- Bluetooth and Wi-Fi both use 2.4 GHz; changing to BLE does not automatically solve interference or walls.
- Poor internet service does not prevent local operation if the router and LAN remain operational.
- Test the included antenna, placement, USB power, and actual packet delivery before changing radios.
- A dedicated access point closer to the nodes is an option if testing establishes a coverage problem. No access-point purchase is selected yet.

## Multiple nodes and room routing

The room that hears a sound is not necessarily the room the user intended. A microphone-to-room mapping is a useful default, not acoustic proof of location. Future logic should support explicit room commands, a deliberate node-selection policy, and one action per utterance/pattern.

Prefer explicit on/off operations over toggle so duplicate events do not reverse the intended result. Deduplicate within a bounded time window using command type, session/event identity, and an appropriate room policy. Consider competing commands, stale retries, and node restarts. This logic is not implemented yet.

## Failure and privacy behavior

Keep Wi-Fi/device credentials outside source control. Recognition should reject uncertain input rather than guessing an action. Audio retention should be off by default, with explicitly enabled short recordings only for debugging. Physical microphone mute and visible listening/connectivity indication are future design items.

Document recovery after router outages, node reboot, hub reboot, and device unavailability. The final implementation should report unavailable state and reconnect without issuing stale commands.
