# Project brief

## What we are building

kha is a local home automation system that accepts a small vocabulary of Mandarin phrases and recognizable whistle patterns. Inexpensive listening nodes placed around the home detect or capture sound. A central Raspberry Pi coordinates actions, beginning with lights on existing TP-Link Kasa smart plugs.

The desired experience is a short command or whistle followed promptly by the intended action, without opening an app or waiting for an internet service. Multiple listening locations should eventually cover multiple rooms.

## End goal

- Always-listening, USB-powered nodes placed wherever coverage is needed.
- Explicit Mandarin commands for lights, fans, and scenes such as movie mode.
- Distinct whistle patterns as an alternative input for the same actions.
- Local operation and predictable mapping from recognized input to action.
- Low perceived latency, reliable recognition, and low false-trigger rates in realistic room noise.
- Room-aware routing and suppression of duplicate detections when several nodes hear the same sound.
- Clear feedback and automatic recovery from temporary network or power interruptions.

## Requirements and preferences

| Area | Requirement or preference |
| --- | --- |
| Processing | Prefer local processing and LAN control |
| Latency | Minimize time from the end of a command/pattern to the actual device response |
| Inputs | Mandarin fixed phrases and whistles |
| Hardware | Inexpensive distributed nodes and one central hub |
| Recognition | A small allowed command vocabulary; avoid accidental sentence triggers |
| Networking | Wi-Fi is the initial transport; patchy coverage must be evaluated at actual placements |
| Power | USB wall power for permanent installations |
| Expansion | Several nodes, then several rooms and scenes |

The earlier 200–500 ms response estimate is a **design target**, not a promise or benchmark. Consistent sub-100 ms speech-to-device operation has not been established. Published model latency is not the same as complete end-to-end latency.

## Candidate command vocabulary

These are examples discussed during planning, not a finalized vocabulary or trained configuration.

| Phrase | Pinyin | Meaning |
| --- | --- | --- |
| 请开灯 | qǐng kāi dēng | Please turn on the lights |
| 请关灯 | qǐng guān dēng | Please turn off the lights |
| 打开风扇 | dǎ kāi fēng shàn | Turn on the fan |
| 关闭风扇 | guān bì fēng shàn | Turn off the fan |
| 观影模式 | guān yǐng mó shì | Movie mode |

Short and long whistles, rising/falling pitch, and two-whistle patterns have been considered. No final pattern-to-action mapping exists. If a single whistle and double whistle are both commands, the single-whistle action must wait long enough to rule out a second whistle. Prefer clearly distinct patterns when fast response is important.

A wake word followed by an allowed command was considered, as was direct fixed-phrase detection. This is still an accuracy/false-trigger/latency decision. A separate conversational assistant is a possible future extension, outside this MVP.

## MVP scope

One listening node, one hub, and one test lamp. Establish reliable transport, capture audio, recognize two explicit actions, then add whistle recognition and measure performance. Do not expand to all rooms until the first room works reliably.

Not currently in scope: general conversation, arbitrary Mandarin transcription, cloud dependency, Bluetooth audio, custom battery hardware, and a full smart-home dashboard.

## Current status

| Item | Status |
| --- | --- |
| Hardware | Pi 5 4GB and three XIAO ESP32-S3 Sense boards selected/purchased |
| Node Wi-Fi | Reported connected during manual setup; no quantitative coverage log committed |
| Node-to-Pi test | Source code prepared; physical results not yet recorded |
| Pi receiver | Automated loopback integration test passes |
| Firmware compilation | Not verified in the preparation environment; toolchain download failed |
| Audio streaming | Planned; not implemented |
| Mandarin / whistle recognition | Planned; not implemented |
| Kasa automation | Planned; not implemented |

Connectivity source is provided now so development can advance independently of the recognition choice. Avoid interpreting this repository as a completed voice assistant.
