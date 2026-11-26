"""Exercise the actual receiver over loopback without Pi hardware."""
from pathlib import Path
import socket
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EchoTest(unittest.TestCase):
    def test_echo_multiple_nodes_and_reject_oversized(self):
        process = subprocess.Popen(
            [sys.executable, "-u", str(ROOT / "pi/udp_echo.py"),
             "--host", "127.0.0.1", "--port", "0"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            startup = process.stdout.readline().strip()
            self.assertIn("Listening on 127.0.0.1:", startup)
            port = int(startup.split(":")[-1].split()[0])
            for node in ("node-01", "node-02"):
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
                    client.settimeout(1)
                    for payload in (f"kha:{node}:abc:1".encode(), b"\x00\xff\x80", b""):
                        client.sendto(payload, ("127.0.0.1", port))
                        reply, peer = client.recvfrom(4096)
                        self.assertEqual(reply, payload)
                        self.assertEqual(peer, ("127.0.0.1", port))
                    client.sendto(b"x" * 2049, ("127.0.0.1", port))
                    client.settimeout(0.15)
                    with self.assertRaises(socket.timeout):
                        client.recvfrom(4096)
                    client.settimeout(1)
                    client.sendto(b"still alive", ("127.0.0.1", port))
                    self.assertEqual(client.recvfrom(4096)[0], b"still alive")
        finally:
            process.terminate()
            try:
                process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()


if __name__ == "__main__":
    unittest.main()
