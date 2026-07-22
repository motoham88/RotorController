#!/usr/bin/env python3
"""Poll the ERC-Mini (Yaesu G-800) over raw GS-232B on the terminal server.

Sends `C` (read bearing) once per second and prints anything that comes
back, with timestamp / raw hex / parsed digits. Auto-reconnects on drop.
"""
import socket
import time
import sys

HOST, PORT = "192.168.115.99", 4001
DURATION = 120          # seconds total
POLL_EVERY = 1.0        # seconds between C polls
READ_CMD = b"C\r"

def parse(data: bytes) -> str:
    digits = "".join(chr(b) for b in data if 0x30 <= b <= 0x39)
    return digits or "(no digits)"

def main():
    start = time.time()
    got_any = False
    while time.time() - start < DURATION:
        try:
            with socket.create_connection((HOST, PORT), timeout=5) as s:
                s.settimeout(1.5)
                print(f"[{time.strftime('%H:%M:%S')}] connected {HOST}:{PORT}", flush=True)
                last_poll = 0.0
                while time.time() - start < DURATION:
                    now = time.time()
                    if now - last_poll >= POLL_EVERY:
                        s.sendall(READ_CMD)
                        last_poll = now
                    try:
                        data = s.recv(256)
                        if not data:
                            print(f"[{time.strftime('%H:%M:%S')}] peer closed", flush=True)
                            break
                        got_any = True
                        print(f"[{time.strftime('%H:%M:%S')}] RX {len(data)}B "
                              f"hex={data.hex()} parsed={parse(data)}", flush=True)
                    except socket.timeout:
                        pass
        except (ConnectionRefusedError, OSError) as e:
            print(f"[{time.strftime('%H:%M:%S')}] conn error: {e}; retry in 2s", flush=True)
            time.sleep(2)
    print(f"\nDONE after {DURATION}s. "
          + ("Received bearing data ✅" if got_any else "NO data received ❌ (readback still dark)"),
          flush=True)
    sys.exit(0 if got_any else 1)

if __name__ == "__main__":
    main()
