# Working on kha

- Read README.md and docs/project.md before extending the project. docs/implementation.md defines the stages; do not imply later stages are implemented merely because they are documented.
- Preserve a raw-audio path for whistle detection. Avoid adding speech-only gates that silently discard non-speech inputs.
- Optimize and measure end-to-end responsiveness, reliability, and false triggers. Distinguish RTT, model delay, frame compute time, and actual actuator response.
- Keep secrets.h, Wi-Fi/device credentials, recordings, private network logs, receipts, and account information out of commits. Use example configuration files.
- Keep the diagnostic UDP listener on a trusted LAN. Do not add public exposure or disable network protections to make tests pass.
- Prefer explicit device actions and plan for duplicate detections from multiple nodes.
- Run python3 -m unittest discover -s tests -v for receiver changes. Compile firmware for XIAO_ESP32S3 when a toolchain is available; report unverified hardware behavior clearly.
