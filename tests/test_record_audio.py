import importlib.util
import math
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("record_audio", ROOT / "pi/record_audio.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)


def packet(sequence, value=100, session=42, node=1, rate=16000):
    return rec.HEADER.pack(b"KHA1", session, sequence, node, rate) + struct.pack("<320h", *([value] * 320))


class RecordingTests(unittest.TestCase):
    def test_gaps_reorder_duplicates_and_other_sessions(self):
        recording = rec.Recording(.08, 1)
        source = ("127.0.0.1", 5008)
        self.assertTrue(recording.accept(packet(100, 10), source))
        self.assertTrue(recording.accept(packet(102, 30), source))
        self.assertTrue(recording.accept(packet(101, 20), source))
        self.assertFalse(recording.accept(packet(101, 99), source))
        self.assertFalse(recording.accept(packet(103, 40, session=99), source))
        self.assertFalse(recording.accept(packet(103, 40, node=2), source))
        self.assertFalse(recording.accept(packet(103, 40), ("127.0.0.2", 5008)))
        values = struct.unpack("<1280h", recording.audio)
        self.assertEqual(values, (10,) * 320 + (20,) * 320 + (30,) * 320 + (0,) * 320)
        stats = recording.statistics()
        self.assertEqual(stats["missing_sample_percent"], 25)
        self.assertEqual(stats["duplicates"], 1)
        self.assertEqual(stats["reordered"], 1)

    def test_validation_and_wraparound(self):
        recording = rec.Recording(.03, 1)
        source = ("127.0.0.1", 123)
        for data in [b"", b"x" * rec.PACKET_BYTES, packet(0, rate=8000), packet(0) + b"x"]:
            self.assertFalse(recording.accept(data, source))
        self.assertTrue(recording.accept(packet(0xffffffff, 1), source))
        self.assertTrue(recording.accept(packet(0, 2), source))
        self.assertEqual(recording.received_frames, 480)
        self.assertEqual(len(recording.audio), 960)
        for seconds in [0, -1, 121, float("nan"), float("inf")]:
            with self.assertRaises(ValueError): rec.Recording(seconds, 1)

    def test_no_packets_times_out(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("127.0.0.1", 0))
            with self.assertRaises(TimeoutError):
                rec.capture(sock, rec.Recording(.02, 1), .02, .02)

    def test_udp_to_wav_integration_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "test.wav"
            command = [sys.executable, "-u", str(ROOT / "pi/record_audio.py"), "--host", "127.0.0.1",
                       "--port", "0", "--seconds", ".12", "--wait-timeout", "2", "--output", str(output)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                line = process.stdout.readline()
                self.assertIn("Listening on", line)
                port = int(line.split(":")[1].split()[0])
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
                    for sequence in range(6):
                        samples = [int(1000 * math.sin(2 * math.pi * 440 * (sequence * 320 + i) / 16000)) for i in range(320)]
                        data = rec.HEADER.pack(b"KHA1", 42, sequence, 1, 16000) + struct.pack("<320h", *samples)
                        sender.sendto(data, ("127.0.0.1", port))
                        time.sleep(.02)
                stdout, stderr = process.communicate(timeout=3)
                self.assertEqual(process.returncode, 0, stderr)
                self.assertIn('"missing_sample_percent": 0.0', stdout)
                with wave.open(str(output), "rb") as wav:
                    self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()),
                                     (1, 2, 16000, 1920))
                original = output.read_bytes()
                repeated = subprocess.run(command, capture_output=True, text=True, timeout=3)
                self.assertNotEqual(repeated.returncode, 0)
                self.assertEqual(output.read_bytes(), original)
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate()


if __name__ == "__main__":
    unittest.main()
