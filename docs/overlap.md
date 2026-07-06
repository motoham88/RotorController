# The G-800 overlap is hardware — no client can control it

**Bottom line:** the 90° overlap (450° total rotation) is a mechanical feature of
the Yaesu G-800 rotator itself. No network client — this `rotor` tool,
PSTRotatorAz, or any Windows operating position — can enable, disable, or prevent
it. It is **not software-addressable**.

> Terminology: this is the **overlap** feature. Don't confuse it with the Rotor-EZ
> protocol's separate, unrelated **"overshoot option"** (`O`/`o` commands).

## Why software can't touch it

Everything that talks to the rig speaks the Idiom Press Rotor-EZ/RotorCard
protocol (a superset of Hy-Gain DCU-1). Per Idiom Press's own protocol document:

- The set command **`AP1xxx` accepts only `000`–`360`.** You physically cannot
  command a bearing in the 360–450 overlap zone.
- The read **`AI1;` returns only `000`–`360`.** The overlap zone is never even
  reported back over the wire.
- There is **no overlap enable/disable command anywhere** in the command set —
  only endpoint, overshoot, unstick, jam-protection toggles, and calibration
  (`K`/`k`).

So no host — ours or PSTRotator — can command into, read, or block the overlap.
They are all bounded by the same wire protocol.

## The overlap belongs to the rotator, not the controller or the software

From the Yaesu G-800DXA manual:

> *"The operator may select the stopper heading (the bearing through which the
> rotator cannot be turned) most convenient for his location and operation,
> allowing full rotation through north, south or both, if desired. In any case,
> 90° overlapping rotation allows rotation through the selected stopper heading
> (450° total rotation)."*

The rotator mechanically turns **450°**. The **stopper heading** — the compass
bearing you cannot turn *through* (the dead zone) — is fixed by how the rotator
and antenna are physically installed, not by any setting a host can send.

## The path into the overlap is the board's decision, not the host's

The behaviour is **path-based** (confirmed on this rig): from 350°, commanding 10°
drives the antenna *forward* through the overlap (350→370) rather than back
through north (350→10). The RotorCard/controller chooses that direction from the
current position and its calibration. The host only ever sends a bare 0–360
target — it has no say in the path.

That is why a software limit is **theater**: since every client can only send
0–360 and the board picks the path, none of them can prevent the long-way travel.

## What actually controls it

Only two levers, both physical and both shared-rig (they affect every operator —
PSTRotator and all Windows positions — so they require coordination and access at
the equipment):

1. **Stopper-heading placement** — where the mechanical dead zone sits. Put it in
   your least-used direction so the overlap sector falls out of the way. See
   [`stopper-heading-checklist.md`](stopper-heading-checklist.md).
2. **RotorCard calibration** — how the pot-to-bearing mapping is set across the
   450° span.

## Sources

- [Idiom Press Rotor-EZ / RotorCard Control Protocol](https://www.hamsupply.com/wp-content/uploads/2015/11/Rotor-EZ-Protocol.pdf)
- [Yaesu G-800DXA / G-1000DXA / G-2800DXA User Manual](https://static.dxengineering.com/global/images/instructions/ysu-g-800dxa_os.pdf)
- [Rotor-EZ manual index (Ham Supply)](https://www.hamsupply.com/support/rotor-ez-manual/)
