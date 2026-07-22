# The G-800 overlap is hardware — no client can control it

**Bottom line:** the 90° overlap (450° total rotation) is a mechanical feature of
the Yaesu G-800 rotator itself. No network client — this `rotor` tool,
PSTRotatorAz, or any Windows operating position — can enable, disable, or prevent
it. It is **not software-addressable**.

> Terminology: this is the **overlap** feature — the mechanical 90° over-travel of
> the rotator. Don't confuse it with any controller-side reporting mode.

## Why software can't touch it

The rig is now driven by an **ERC-Mini** controller in **Yaesu GS-232B** emulation
(it replaced an Idiom Press RotorEZ/RotorCard on the DCU-1 protocol). The argument
below is protocol-agnostic — it holds regardless of which controller/emulation
fronts the rotator:

- **The host only ever sends a bare target azimuth** (`Mddd` under GS-232B, `AP1ddd`
  under DCU-1). It never specifies a *path*, so it cannot ask for the long way
  round through the overlap versus the short way through north.
- **The controller, not the host, chooses the travel path** from the current
  position and its calibration (see below). Every client — this tool, PSTRotator,
  any Windows position — sends the same bare target and gets the same board-chosen
  behaviour.
- **The stopper heading is a mechanical/installation setting**, not a wire command.

So no host can command into, read-around, or block the overlap: they are all bounded
by the same "send a bare target, let the board pick the path" contract.

> ⚠️ **Not re-verified after the ERC-Mini swap:** GS-232B exposes 360°/450° reporting
> modes (`P36`/`P45`) and the controller *may* report a bearing in the 360–450 zone
> (e.g. `AZ=380`) where DCU-1's `AI1;` only ever returned 000–360. That changes what
> the wire can *report*, not the core claim above (the host still sends only a bare
> target). If you need the exact ERC-Mini reporting behaviour on this rig, confirm it
> live rather than trusting the old DCU-1-specific bullets this section replaced.

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
through north (350→10). The ERC-Mini/controller chooses that direction from the
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
2. **Controller calibration** — how the ERC-Mini's pot-to-bearing mapping is set
   across the 450° span.

## Sources

- [Idiom Press Rotor-EZ / RotorCard Control Protocol](https://www.hamsupply.com/wp-content/uploads/2015/11/Rotor-EZ-Protocol.pdf)
- [Yaesu G-800DXA / G-1000DXA / G-2800DXA User Manual](https://static.dxengineering.com/global/images/instructions/ysu-g-800dxa_os.pdf)
- [Rotor-EZ manual index (Ham Supply)](https://www.hamsupply.com/support/rotor-ez-manual/)
