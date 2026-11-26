# Section 3B: stream audio to the Pi and listen

Goal: hear the actual microphone signal at useful distances, and check continuous Wi-Fi delivery. This step does not recognize words or whistles. Section 3A's changing RMS readings establish sound response, not intelligible across-room speech.

## 1. Update both copies of kha

On the Pi and on the computer used for Arduino uploads, run `git pull --ff-only` inside the repository, or download the current ZIP. The Pi needs only Python 3; no pip packages or node SD card are required.

The old UDP echo receiver is not used. Stop it with Ctrl+C if it is still running; its port 5005 is separate from the audio port 5007.

## 2. Configure and upload the node

1. Copy `firmware/audio_stream/secrets.example.h` to `firmware/audio_stream/secrets.h`.
2. Set your Wi-Fi credentials, Pi LAN IPv4 address, and `NODE_NUMBER = 1` for the first node. This numeric field differs from the text ID in the echo test. Use a different positive integer per additional node.
3. Open `firmware/audio_stream/audio_stream.ino` in Arduino IDE.
4. Use **Tools → Board → esp32 → XIAO_ESP32S3**, the USB port, **USB CDC On Boot → Enabled**, and Espressif's **3.x** Arduino board package. The microphone interface matches the Section 3A PDM test (clock 42, data 41).
5. Upload and open Serial Monitor at 115200 baud if you want status. On successful Wi-Fi/send operation, `sent` should rise by roughly 100 every two seconds. Successful local sending is not proof the Pi receives the packets.

**Uploading this sketch starts continuous raw microphone transmission to the configured Pi over the LAN while Wi-Fi is connected.** It has no speech gate, authentication, or encryption. The Pi only saves audio during an explicitly run recording command. Unplug the node or replace its firmware to stop transmission. Test on a trusted LAN; no port forwarding is needed.

## 3. Record 15 seconds on the Pi

```bash
cd ~/kha
mkdir -p recordings
python3 pi/record_audio.py --node 1 --seconds 15 --output recordings/mic-test.wav
```

Wait for `Recording node 1 ... Speak now.` It waits up to 30 seconds for the first matching packet, then records for 15 wall-clock seconds. During the recording:

- Start with a few seconds of silence.
- Say the same short Mandarin command several times at about 1 metre.
- Say it at the intended across-room position.
- Whistle, then end with silence.

Use normal speech and avoid handling the board while recording. Repeat in realistic TV/fan noise after the quiet-room baseline. For comparisons, use separate filenames for each distance/noise condition. Existing output files are never overwritten.

Expected terminal summary includes `received_packets`, `missing_sample_percent`, signal level, and `near_clip_percent`. A continuously received 15-second recording contains about 750 packets of 320 samples each. Missing sample slots are filled with zero-valued silence, not removed from the timeline; out-of-order packets arriving before the recording closes can fill their slots.

## 4. Listen

On a Pi with desktop audio, open the WAV in an audio player. On a headless Pi, copy it to your Mac. Run the following in **Mac Terminal**, replacing both placeholders:

```bash
scp YOUR_PI_USER@YOUR_PI_IP:~/kha/recordings/mic-test.wav ~/Downloads/
open ~/Downloads/mic-test.wav
```

Use ordinary comfortable playback volume first. The recording is raw and unnormalized: quiet speech is a measurement result, not automatically a failure. Increasing playback volume does not recover speech buried in noise. An all-zero or constant capture is not a pass.

## Interpret results

- **Missing sample percent:** percentage of the fixed-duration WAV's samples not received for the selected stream, including the trailing gap if it stops. This is not a count of only router-dropped packets: local sending failures, disconnected nodes, and session changes can contribute.
- **Reordered:** packets that arrived behind an already received sequence but were recovered into the recording. There is no real-time playout buffer in this diagnostic.
- **Ignored:** other nodes/sources/sessions, packets outside the recording sequence range, and older data. The recorder locks to the first valid source/session for the selected node number. Restart it if the node restarts or reports a new capture session.
- **RMS dBFS:** digital signal level relative to full-scale sample amplitude, not acoustic sound pressure. Missing silence is included. The measurement is DC-corrected; `null` means zero AC RMS.
- **Near clip percent:** fraction of samples within a small threshold of the digital rails. Listen for distortion as well; this metric alone does not identify every analog/acoustic fault.
- A clear recording establishes capture quality and transport behavior, not recognition accuracy or real-time latency.

If packet delivery is poor, repeat near the access point, check antenna/power, and compare before adding model inference. If delivery is good but words are unclear, focus on placement, microphone noise, and acoustics. Higher audio gain alone cannot solve poor signal-to-noise ratio.

## Protocol and implementation limits

UDP destination 5007, node source port 5008. Every packet is 660 bytes:

| Byte offset | Field | Encoding |
| --- | --- | --- |
| 0 | `KHA1` | 4-byte magic/protocol version |
| 4 | Boot/capture session | uint32 little-endian |
| 8 | Sequence | uint32 little-endian; incremented for every complete captured block, including offline blocks |
| 12 | Node number | uint32 little-endian, positive |
| 16 | Sample rate | uint32 little-endian, fixed 16000 |
| 20 | Audio | 320 signed int16 little-endian mono samples (20 ms) |

Capture errors start a new session. There is no retransmission or compression. The capture loop can still fall behind during slow sends/scheduling; sample/packet counts alone cannot prove continuity inside the microphone DMA buffers. A sustained-load test and eventual separate capture/send tasks may be needed.

The receiver allocates at most 120 seconds of PCM (3.84 MB), bounds packet sequence placement, filters other streams, and writes a standard PCM WAV. It uses wall time to bound recording and sample indices for placement. It has no synchronized capture timestamps and does not measure one-way audio delay. Out-of-order recovery into a saved file is not a final live jitter-buffer design.

Recordings are ignored by Git (`*.wav`). Do not publish recordings, Wi-Fi credentials, or identifying network diagnostics without reviewing them. Each run explicitly enables saving; nothing is retained by a cloud service by this receiver.

## Validation status

Automated tests cover protocol validation, silence insertion for missing packets, reordered/duplicate/session handling, uint32 sequence wrap, UDP-to-WAV output, no-packet timeout, duration bounds, and overwrite protection. Firmware API use matches the microphone sketch that was reported working; the combined streaming firmware has not been compiled or tested on physical hardware in the preparation environment.

Next: use the recordings to choose microphone placement and test Mandarin phrase detection, then whistle recognition. Keep evaluating latency and false triggers before connecting automations.
