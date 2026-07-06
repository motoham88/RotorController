"""rotorlib — talk Hy-Gain DCU-1 (RotorEZ) to the Yaesu G-800 over TCP.

Shared by the `rotor` CLI and the `rotor-gui` desktop app.

Protocol (confirmed 2026-07-05):
  read : send b"AI1;"    -> reply b";ddd"   (leading ';' + 3-digit degrees)
  set  : send b"AP1ddd;" -> turn to ddd     (zero-padded, 0-359)
"""
import os
import re
import socket
import time

READ_CMD = b"AI1;"
BEARING_RE = re.compile(rb";(\d{3})")

DEFAULT_HOST = "192.168.115.99"
DEFAULT_PORT = 4001


def host_port():
    return (os.environ.get("ROTOR_HOST", DEFAULT_HOST),
            int(os.environ.get("ROTOR_PORT", str(DEFAULT_PORT))))


def format_set(deg: int) -> bytes:
    if not (0 <= deg <= 359):
        raise ValueError(f"degrees must be 0-359 (got {deg})")
    return f"AP1{deg:03d};".encode("ascii")


class RotorClient:
    """A persistent connection to the rotor's raw DCU-1 TCP port.

    Reads share the terminal server's RX broadcast with PSTRotator (non-
    intrusive); writes contend with its ~1 Hz polling, so don't hammer set().
    """

    def __init__(self, host=None, port=None, timeout=5.0):
        h, p = host_port()
        self.host = host or h
        self.port = port or p
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.close()
        self.sock = socket.create_connection((self.host, self.port),
                                             timeout=self.timeout)
        self.sock.settimeout(2.0)
        return self

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _ensure(self):
        if self.sock is None:
            self.connect()

    def read_bearing(self, poll_deadline=4.0):
        """Send one AI1; and return the bearing (int) or None on timeout."""
        self._ensure()
        self.sock.sendall(READ_CMD)
        deadline = time.monotonic() + poll_deadline
        buf = b""
        while time.monotonic() < deadline:
            try:
                data = self.sock.recv(64)
            except socket.timeout:
                continue
            if not data:
                self.close()
                return None
            buf += data
            m = BEARING_RE.search(buf)
            if m:
                return int(m.group(1))
        return None

    def set_azimuth(self, deg: int):
        """Send AP1ddd; to turn to deg. Raises ValueError if out of range."""
        cmd = format_set(deg)
        self._ensure()
        self.sock.sendall(cmd)
        return cmd

    def __enter__(self):
        return self.connect()

    def __exit__(self, *exc):
        self.close()
