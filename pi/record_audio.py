#!/usr/bin/env python3
"""Record a bounded, opt-in WAV from one kha audio node (standard library only)."""
import argparse
from array import array
import json
import math
from pathlib import Path
import socket
import struct
import sys
import time
import wave

HEADER = struct.Struct("<4sIIII")
RATE = 16000
SAMPLES = 320
PAYLOAD_BYTES = SAMPLES * 2
PACKET_BYTES = HEADER.size + PAYLOAD_BYTES


class Recording:
    """Place sequenced packets into a fixed-size recording, with silence for gaps."""

    def __init__(self, seconds: float, node: int):
        if not math.isfinite(seconds) or not 0 < seconds <= 120:
            raise ValueError("seconds must be greater than 0 and at most 120")
        if not 1 <= node <= 0xffffffff:
            raise ValueError("node must be a positive uint32")
        self.frames = max(1, round(seconds * RATE))
        self.node = node
        self.audio = bytearray(self.frames * 2)
        self.slots = set()
        self.source = None
        self.base_sequence = 0
        self.max_slot = -1
        self.received_frames = 0
        self.invalid = self.ignored = self.duplicates = self.reordered = 0

    def accept(self, data: bytes, address) -> bool:
        if len(data) != PACKET_BYTES:
            self.invalid += 1
            return False
        magic, session, sequence, node, rate = HEADER.unpack_from(data)
        if magic != b"KHA1" or rate != RATE or node == 0:
            self.invalid += 1
            return False
        if node != self.node:
            self.ignored += 1
            return False
        source = (address, session, node)
        if self.source is None:
            self.source = source
            self.base_sequence = sequence
        if source != self.source:
            self.ignored += 1
            return False
        slot = (sequence - self.base_sequence) & 0xffffffff
        if slot * SAMPLES >= self.frames:
            self.ignored += 1
            return False
        if slot in self.slots:
            self.duplicates += 1
            return False
        if slot < self.max_slot:
            self.reordered += 1
        self.max_slot = max(self.max_slot, slot)
        self.slots.add(slot)
        first = slot * SAMPLES
        frames = min(SAMPLES, self.frames - first)
        self.audio[first * 2:(first + frames) * 2] = data[HEADER.size:HEADER.size + frames * 2]
        self.received_frames += frames
        return True

    def statistics(self) -> dict:
        samples = array("h")
        samples.frombytes(self.audio)
        if sys.byteorder != "little":
            samples.byteswap()
        mean = sum(samples) / self.frames
        variance = max(0, sum(x * x for x in samples) / self.frames - mean * mean)
        rms = math.sqrt(variance)
        return {
            "node": self.node, "seconds": self.frames / RATE,
            "received_packets": len(self.slots),
            "expected_packet_slots": math.ceil(self.frames / SAMPLES),
            "missing_sample_percent": round(100 * (self.frames - self.received_frames) / self.frames, 2),
            "duplicates": self.duplicates, "reordered": self.reordered,
            "invalid_packets": self.invalid, "ignored_packets": self.ignored,
            "rms_sample_units": round(rms, 2),
            "rms_dbfs": round(20 * math.log10(rms / 32768), 2) if rms else None,
            "peak_sample_units": max(abs(x) for x in samples),
            "near_clip_percent": round(100 * sum(abs(x) >= 32760 for x in samples) / self.frames, 3),
        }


def capture(sock, recording: Recording, seconds: float, wait_timeout: float) -> None:
    waiting_until = time.monotonic() + wait_timeout
    started = None
    last_report = 0.0
    while True:
        now = time.monotonic()
        deadline = waiting_until if started is None else started + seconds
        remaining = deadline - now
        if remaining <= 0:
            if started is None:
                raise TimeoutError("No matching audio node arrived; check firmware, node number, Pi IP, and UDP 5007")
            return
        sock.settimeout(min(0.2, remaining))
        try:
            data, address = sock.recvfrom(PACKET_BYTES + 1)
        except socket.timeout:
            continue
        accepted = recording.accept(data, address)
        if accepted and started is None:
            started = time.monotonic()
            print(f"Recording node {recording.node} for {seconds:g} seconds. Speak now.", flush=True)
        if started is not None and time.monotonic() - last_report >= 1:
            last_report = time.monotonic()
            print(f"Received {len(recording.slots)} packets...", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5007)
    parser.add_argument("--node", type=int, default=1)
    parser.add_argument("--seconds", type=float, default=15)
    parser.add_argument("--wait-timeout", type=float, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        recording = Recording(args.seconds, args.node)
        if not 0 <= args.port <= 65535:
            raise ValueError("port must be between 0 and 65535")
        if not math.isfinite(args.wait_timeout) or not 0 < args.wait_timeout <= 300:
            raise ValueError("wait-timeout must be greater than 0 and at most 300")
        if args.output.exists():
            raise ValueError("output already exists; choose a new filename")
        if not args.output.parent.is_dir():
            raise ValueError("output directory does not exist; create it first")
    except ValueError as exc:
        parser.error(str(exc))
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((args.host, args.port))
            print(f"Listening on {args.host}:{sock.getsockname()[1]} (UDP); waiting for node {args.node}...", flush=True)
            capture(sock, recording, args.seconds, args.wait_timeout)
        # Exclusive create avoids overwriting a recording even if it appeared during capture.
        with args.output.open("xb") as output:
            with wave.open(output, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(RATE)
                wav.writeframes(recording.audio)
        print(f"Saved {args.output}", flush=True)
        print(json.dumps(recording.statistics(), indent=2), flush=True)
        if recording.received_frames < recording.frames:
            print("Missing sample slots were filled with silence. Inspect the missing percentage.", flush=True)
        return 0
    except (OSError, TimeoutError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Cancelled; no WAV saved.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
