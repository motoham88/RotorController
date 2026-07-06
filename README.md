# rotor

Read and set a **Yaesu G-800** antenna rotator from Linux, over the network — no
Wine, no Windows.

The rotor is driven by an **Idiom Press RotorEZ** serial card, which speaks the
**Hy-Gain DCU-1** protocol. A terminal server exposes that serial port as a raw
TCP socket. `PSTRotatorAz` runs on a Windows PC and shares the rotor among
several operating positions; this tool reads and sets **alongside** it without
stealing the line.

## Install

`rotor` is a single self-contained Python 3 script (stdlib only). Put it on your
PATH:

```sh
ln -s "$PWD/rotor" ~/.local/bin/rotor
```

## Usage

```sh
rotor read                 # print current bearing once (e.g. 269)
rotor watch                # live bearing, timestamped; --interval S (default 1s)
rotor set 270              # turn to 270° — prompts, then watches it arrive
rotor set 270 --yes        # skip the confirmation prompt
rotor set 270 --wait 0     # fire-and-forget (don't poll for arrival)
rotor gui                  # desktop compass UI (Tkinter)
```

### Desktop GUI

`rotor gui` opens a compass dial (`rotor_gui.py`, Tkinter — stdlib only):

- **orange needle** = live antenna heading (updates ~1 Hz)
- **click** the dial to preview a heading (fills "Go to"); **double-click** to turn
- **green marker** = committed target; status shows the delta and "on target"
- **presets** N/NE/E/SE/S/SW/W/NW for one-click aiming
- all rotor I/O runs on a background thread, so the window never freezes

`set` shares the serial line with PSTRotator's polling and physically moves the
antenna, so it confirms by default. `--tolerance` (default 2°) sets the arrival
window.

### Configuration

Target defaults to `192.168.115.99:4001`. Override with environment variables:

```sh
ROTOR_HOST=192.168.1.50 ROTOR_PORT=4001 rotor read
```

## Protocol (Hy-Gain DCU-1, as spoken by RotorEZ)

ASCII, `;`-terminated, over raw TCP. Reverse-engineered from a packet capture
and confirmed live 2026-07-05.

| Action | Send | Reply |
|---|---|---|
| Read bearing | `AI1;` | `;ddd` — leading `;` then 3 ASCII digits, e.g. `;188` = 188° |
| Set azimuth | `AP1ddd;` | (none) — e.g. `AP1270;` turns to 270° |

Degrees are zero-padded to 3 digits (`AP1005;` = 5°). Valid range 0–359.

The terminal server broadcasts the serial RX to every connected TCP client, so
`rotor read`/`watch` see the same bearing stream PSTRotator does — reading is
non-intrusive. Writing (`set`) does contend with PSTRotator's ~1 Hz polling on
the shared line, so avoid hammering it.

## tools/

- `poller.py` — the original diagnostic poller (sends `AI1;` every second, prints
  raw hex + parsed digits, auto-reconnects). Handy for confirming the readback
  path is alive at the hardware level.
