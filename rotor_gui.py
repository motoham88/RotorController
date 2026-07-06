#!/usr/bin/env python3
"""rotor_gui — Tkinter compass desktop UI for the Yaesu G-800 rotator.

A live compass dial: the orange needle is the antenna's current heading, the
green marker is your target. Click the dial (or type a heading, or hit a
preset) to aim, then Turn. All rotor I/O runs on a background thread so the
window stays responsive; reads share the line with PSTRotator.

Run via `rotor gui`, or directly: `python3 rotor_gui.py`.
"""
import math
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from rotorlib import RotorClient, host_port  # noqa: E402

POLL_INTERVAL = 1.0     # seconds between bearing reads
TOLERANCE = 2           # arrival tolerance (deg) for the "on target" cue

# palette
BG = "#0f1216"
DIAL = "#1b222b"
RING = "#3a4757"
TICK = "#5a6b7e"
TICK_MAJOR = "#8ea3b8"
CARD = "#e8eef5"
NEEDLE = "#ff7a3d"
TARGET = "#37d67a"
TEXT = "#e8eef5"
MUTED = "#7f8c9b"


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


class RotorWorker(threading.Thread):
    """Owns the socket. Reads bearing ~1 Hz, executes queued set commands."""

    def __init__(self, evt_q):
        super().__init__(daemon=True)
        self.evt_q = evt_q
        self.cmd_q = queue.Queue()
        self._stop = threading.Event()
        self.client = RotorClient()

    def set_azimuth(self, deg):
        self.cmd_q.put(("set", deg))

    def stop(self):
        self._stop.set()
        self.cmd_q.put(("quit", None))

    def run(self):
        while not self._stop.is_set():
            # drain pending commands first (set is more urgent than a read)
            try:
                while True:
                    kind, val = self.cmd_q.get_nowait()
                    if kind == "quit":
                        self.client.close()
                        return
                    if kind == "set":
                        try:
                            cmd = self.client.set_azimuth(val)
                            self.evt_q.put(("sent", val, cmd.decode()))
                        except (OSError, ValueError) as e:
                            self.evt_q.put(("error", str(e)))
                            self.client.close()
            except queue.Empty:
                pass

            start = time.monotonic()
            try:
                b = self.client.read_bearing()
                self.evt_q.put(("bearing", b))
            except OSError as e:
                self.evt_q.put(("error", str(e)))
                self.client.close()
                time.sleep(1.0)

            # pace the loop but stay responsive to stop/commands
            while (time.monotonic() - start) < POLL_INTERVAL:
                if self._stop.is_set() or not self.cmd_q.empty():
                    break
                time.sleep(0.05)


class RotorApp:
    def __init__(self, root):
        self.root = root
        self.evt_q = queue.Queue()
        self.worker = RotorWorker(self.evt_q)

        self.heading = None      # current, from the rotor
        self.target = None       # committed target we told it to turn to
        self.preview = None      # click/typed heading not yet sent

        host, port = host_port()
        root.title(f"rotor — Yaesu G-800  ({host}:{port})")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.size = 340
        self.canvas = tk.Canvas(root, width=self.size, height=self.size,
                                bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=4, padx=16, pady=(16, 4))
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        self.big_font = tkfont.Font(family="DejaVu Sans", size=30, weight="bold")
        self.readout = tk.Label(root, text="---°", font=self.big_font,
                                fg=TEXT, bg=BG)
        self.readout.grid(row=1, column=0, columnspan=4)

        # target entry + Turn
        entry_font = tkfont.Font(family="DejaVu Sans", size=13)
        tk.Label(root, text="Go to:", fg=MUTED, bg=BG, font=entry_font)\
            .grid(row=2, column=0, sticky="e", padx=(16, 2), pady=6)
        self.target_var = tk.StringVar()
        self.entry = tk.Entry(root, textvariable=self.target_var, width=6,
                              font=entry_font, justify="center",
                              bg=DIAL, fg=TEXT, insertbackground=TEXT,
                              relief="flat")
        self.entry.grid(row=2, column=1, sticky="w", pady=6)
        self.entry.bind("<Return>", lambda e: self.commit_from_entry())
        self.turn_btn = tk.Button(root, text="Turn", command=self.commit_from_entry,
                                  font=entry_font, bg=NEEDLE, fg="#111",
                                  activebackground="#ffa06b", relief="flat",
                                  padx=14)
        self.turn_btn.grid(row=2, column=2, columnspan=2, sticky="w", padx=(4, 16))

        # presets
        presets = tk.Frame(root, bg=BG)
        presets.grid(row=3, column=0, columnspan=4, pady=(0, 6))
        for i, (name, deg) in enumerate([("N", 0), ("NE", 45), ("E", 90),
                                         ("SE", 135), ("S", 180), ("SW", 225),
                                         ("W", 270), ("NW", 315)]):
            tk.Button(presets, text=name, width=3,
                      command=lambda d=deg: self.aim(d, commit=False),
                      font=entry_font, bg=DIAL, fg=TEXT,
                      activebackground=RING, relief="flat")\
                .grid(row=0, column=i, padx=2)

        self.status = tk.Label(root, text="connecting…", fg=MUTED, bg=BG,
                               anchor="w", font=entry_font)
        self.status.grid(row=4, column=0, columnspan=4, sticky="we",
                         padx=16, pady=(0, 12))

        self.worker.start()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.draw()
        self.pump()

    # ---- interaction -----------------------------------------------------
    def deg_from_xy(self, x, y):
        cx = cy = self.size / 2
        return int(round(math.degrees(math.atan2(x - cx, cy - y)))) % 360

    def on_click(self, ev):
        self.aim(self.deg_from_xy(ev.x, ev.y), commit=False)

    def on_double_click(self, ev):
        self.aim(self.deg_from_xy(ev.x, ev.y), commit=True)

    def aim(self, deg, commit):
        deg %= 360
        self.preview = deg
        self.target_var.set(str(deg))
        if commit:
            self.commit(deg)
        self.draw()

    def commit_from_entry(self):
        raw = self.target_var.get().strip()
        try:
            deg = int(raw) % 360
        except ValueError:
            self.set_status(f"'{raw}' is not a heading", err=True)
            return
        self.commit(deg)

    def commit(self, deg):
        self.target = deg
        self.preview = None
        self.worker.set_azimuth(deg)
        self.set_status(f"turning to {deg}°…")
        self.draw()

    # ---- event pump ------------------------------------------------------
    def pump(self):
        try:
            while True:
                evt = self.evt_q.get_nowait()
                kind = evt[0]
                if kind == "bearing":
                    self.heading = evt[1]
                    self.on_bearing()
                elif kind == "sent":
                    self.set_status(f"sent {evt[2]} → {evt[1]}°")
                elif kind == "error":
                    self.set_status(f"link error: {evt[1]}", err=True)
        except queue.Empty:
            pass
        self.draw()
        self.root.after(120, self.pump)

    def on_bearing(self):
        if self.heading is None:
            self.set_status("no reply — readback down?", err=True)
            return
        if self.target is not None:
            err = abs(((self.heading - self.target + 180) % 360) - 180)
            if err <= TOLERANCE:
                self.set_status(f"on target ({self.target}°)")
            else:
                self.set_status(f"turning to {self.target}°  (Δ{err}°)")
        else:
            self.set_status(f"heading {self.heading}°")

    def set_status(self, msg, err=False):
        self.status.config(text=msg, fg="#ff6b6b" if err else MUTED)

    # ---- drawing ---------------------------------------------------------
    def draw(self):
        c = self.canvas
        c.delete("all")
        cx = cy = self.size / 2
        r = self.size / 2 - 14

        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=DIAL, outline=RING, width=2)

        for deg in range(0, 360, 10):
            major = (deg % 30 == 0)
            inner = r - (14 if major else 8)
            x1, y1 = polar(cx, cy, inner, deg)
            x2, y2 = polar(cx, cy, r - 2, deg)
            c.create_line(x1, y1, x2, y2,
                          fill=TICK_MAJOR if major else TICK,
                          width=2 if major else 1)

        for name, deg in [("N", 0), ("E", 90), ("S", 180), ("W", 270)]:
            tx, ty = polar(cx, cy, r - 30, deg)
            c.create_text(tx, ty, text=name, fill=CARD,
                          font=("DejaVu Sans", 13, "bold"))

        # target / preview marker
        for val, col, dash in [(self.target, TARGET, ()),
                               (self.preview, "#9aa7b5", (4, 3))]:
            if val is not None:
                mx, my = polar(cx, cy, r - 2, val)
                ix, iy = polar(cx, cy, r - 22, val)
                c.create_line(ix, iy, mx, my, fill=col, width=3, dash=dash or None)
                c.create_oval(mx - 5, my - 5, mx + 5, my + 5, fill=col, outline="")

        # current-heading needle
        if self.heading is not None:
            hx, hy = polar(cx, cy, r - 26, self.heading)
            tailx, taily = polar(cx, cy, 18, (self.heading + 180) % 360)
            c.create_line(tailx, taily, hx, hy, fill=NEEDLE, width=4,
                          capstyle="round", arrow="last", arrowshape=(16, 20, 7))

        c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=RING, outline="")

        self.readout.config(
            text=("---°" if self.heading is None else f"{self.heading}°"))

    def on_close(self):
        self.worker.stop()
        self.root.after(150, self.root.destroy)


def main():
    root = tk.Tk()
    RotorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
