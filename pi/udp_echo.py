#!/usr/bin/env python3
"""Local-network UDP echo service for kha node connectivity tests."""
import argparse
import json
import socket

MAX_PACKET = 2048


def run(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        print(f"Listening on {host}:{sock.getsockname()[1]} (UDP)", flush=True)
        try:
            while True:
                data, address = sock.recvfrom(MAX_PACKET + 1)
                # Reject oversized packets instead of echoing truncated payloads.
                if len(data) > MAX_PACKET:
                    continue
                try:
                    sock.sendto(data, address)
                except OSError as exc:
                    print(f"Reply failed: {exc}", flush=True)
                    continue
                # JSON escaping prevents terminal control characters in test data.
                print(json.dumps({"node_ip": address[0], "node_port": address[1],
                                  "bytes": len(data),
                                  "message": data.decode("utf-8", errors="replace")}),
                      flush=True)
        except KeyboardInterrupt:
            print("Stopped.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0", help="IPv4 bind address")
    parser.add_argument("--port", type=int, default=5005)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    run(args.host, args.port)


if __name__ == "__main__":
    main()
