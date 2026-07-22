# Node-RED & Home Assistant integration

Read and set the **Yaesu G-800** from Node-RED and Home Assistant using the same
**ERC approach** the `rotor` tool uses: raw **Yaesu GS-232B** over TCP to the
terminal server, sitting *alongside* `PSTRotatorAz` as one more peer on the shared
line.

## The protocol you're speaking

Everything below is just the two commands from [`rotorlib.py`](../rotorlib.py),
spoken over a raw TCP socket to the terminal server (default
`192.168.115.99:4001`):

| Action | Send | Reply |
|---|---|---|
| Read bearing | `C` + CR | `AZ=ddd` + CR/LF (e.g. `AZ=269`) |
| Set azimuth | `Mddd` + CR | (none) — zero-padded, 0–359 (e.g. `M270`) |

Three things carry over from the CLI and matter for both platforms:

- **Reads are non-intrusive.** The terminal server broadcasts the serial RX to
  every connected client, so you see the same `AZ=` stream PSTRotator's ~1 Hz
  polling produces. Polling with your own `C` is fine too.
- **Writes contend** with PSTRotator's polling on the shared line — poll gently and
  don't hammer `set`.
- **Parse `AZ=(\d+)`**, not exactly three digits. In the G-800's 360–450° overlap
  zone the controller can report values above 359 (see [`overlap.md`](overlap.md)).

## Recommended shape

```
ERC-Mini (GS-232B) --serial--> Terminal server :4001 (raw TCP, broadcast)
                                     ^   ^
                       +-------------+   +------------ PSTRotatorAz (Windows)
                       |
                  Node-RED  --MQTT-->  Home Assistant
```

Let Node-RED talk GS-232B to the terminal server and bridge to Home Assistant over
MQTT. HA then gets clean entities without any rotor code on the HA box.

## Node-RED

A ready-to-import flow lives in [`../tools/nodered-rotor-flow.json`](../tools/nodered-rotor-flow.json)
(Node-RED → **Import** → paste the file). It contains:

- **Poll** — an inject node (every 5 s) → a `tcp request` node that sends `C\r` and
  returns after a fixed 600 ms timeout (long enough for a fresh `AZ=` line to flush
  from the broadcast stream) → a function node that parses `AZ=(\d+)` and publishes
  the integer bearing to MQTT `rotor/azimuth/state`.
- **Set** — an `mqtt in` on `rotor/azimuth/set` → a function node that range-checks
  0–359 and formats `Mddd\r` → a `tcp request` node to `:4001`.

Before deploying, edit the two `tcp request` nodes' **host/port** and the `mqtt`
broker config to match your setup.

The parse and format function bodies, for reference:

```js
// parse (poll) — tcp reply -> bearing
const m = msg.payload.toString().match(/AZ=(\d+)/);
if (!m) return null;                 // no bearing this cycle, drop it
msg.payload = parseInt(m[1], 10);    // e.g. 269
msg.topic = "rotor/azimuth/state";
return msg;
```

```js
// format (set) — heading -> Mddd
let d = Math.round(Number(msg.payload));
if (!(d >= 0 && d <= 359)) return null;                   // guard the range
msg.payload = "M" + String(d).padStart(3, "0") + "\r";    // "M270\r"
return msg;
```

> **Passive alternative:** because PSTRotator already polls, you can skip sending
> `C` and instead use a `tcp in` node ("connect to" `:4001`, split on `\n`) and
> parse the `AZ=` lines that stream by — zero contention. The active poll in the
> flow is more robust if PSTRotator might be off.

## Home Assistant

### Option A — via Node-RED/MQTT (recommended)

With the flow above running, add a read sensor and a write `number`:

```yaml
mqtt:
  sensor:
    - name: "Rotor Azimuth"
      state_topic: "rotor/azimuth/state"
      unit_of_measurement: "°"
      icon: mdi:antenna
  number:
    - name: "Rotor Setpoint"
      command_topic: "rotor/azimuth/set"
      min: 0
      max: 359
      step: 1
      mode: box
```

You get `sensor.rotor_azimuth` (live bearing) and `number.rotor_setpoint` (turn
the antenna) for dashboards and automations.

### Option B — HA-only, no Node-RED

Talk to the terminal server directly from HA (needs `nc` on the HA host):

```yaml
command_line:
  - sensor:
      name: "Rotor Azimuth"
      command: "printf 'C\r' | nc -w1 192.168.115.99 4001 | grep -aoP 'AZ=\\K\\d+' | head -1"
      unit_of_measurement: "°"
      scan_interval: 5

shell_command:
  rotor_set: "printf 'M%03d\r' {{ (heading | int) }} | nc -w1 192.168.115.99 4001"
```

Call `shell_command.rotor_set` from an automation/script with `data: {heading: 270}`.
Or, since the repo is pure-stdlib, drop the code on the HA box and run
`python3 rotorcli.py set {{ heading }} --yes --wait 0` with `ROTOR_HOST`/`ROTOR_PORT`
set.

## Direct-to-terminal-server vs through PSTRotator

Everything here talks to the **ERC terminal server directly**, which is the
approach the `rotor` tool uses and keeps reads non-intrusive. The alternative is
pointing Node-RED/HA at **PSTRotator's own network interface** (it can expose a
GS-232/TCP or UDP server), making PSTRotator the single master and removing write
contention — at the cost of PSTRotator having to be running. For a home-automation
setup where the antenna should track even when the Windows box is off, the
direct path is usually what you want.
