# Relocating the G-800 stopper heading — checklist

The 450° overlap **cannot be removed** — it's mechanical (see
[`overlap.md`](overlap.md)). What you *can* do is **move where the stopper
heading (the dead zone) sits**, so the overlap sector falls in a direction you
rarely use instead of biting you mid-QSO.

> ⚠️ **Read before starting**
> - This is **physical, shared-rig work.** It affects PSTRotatorAz and every
>   Windows position that shares the rotor. Coordinate first; nobody else should
>   be driving the rotor while you do this.
> - It involves **tower work and AC-powered controller internals.** Don't work
>   alone; kill power before touching connectors; follow the Yaesu manual's own
>   safety notes.
> - The calibration steps below are **adapted from the Yaesu G-800DXA manual** and
>   describe the *factory* alignment (stopper referenced to South/180°). **Verify
>   every value against your own rig** — your current stopper may already be
>   elsewhere. When in doubt, the printed manual is authoritative.
> - After any change, **all clients must be re-checked** — headings and any saved
>   presets in PSTRotator / the Windows clients shift with the calibration.

---

## Part 0 — Diagnose first (safe, no commitment)

Find out where your stopper actually is *before* changing anything. Nothing here
moves hardware permanently.

- [ ] Announce to the other operators that you're taking the rotor for testing.
- [ ] At the controller, use the **manual rotation (seesaw) switch** to drive the
      rotator **fully counter-clockwise** until it hits its automatic stop. Note
      the true compass bearing the antenna points and what the dial reads.
- [ ] Drive **fully clockwise** to the other stop. Note that bearing too.
- [ ] Watch the **OVERLAP LED**: note the bearing at which it lights — that marks
      where the overlap sector begins.
- [ ] From Linux, run `rotor watch` during the sweep and record the reported
      degrees at each end. (Reads are non-intrusive.)
- [ ] Conclusion: the **dead zone / stopper** is the gap between the CW-stop and
      CCW-stop bearings; the **overlap sector** is the ~90° the LED flags. Write
      down where they currently are.

## Part 1 — Decide the target

- [ ] Pick the **desired stopper heading** = your least-used compass direction
      (often due south, or wherever your coax service loop is happiest). The
      overlap sector will sit adjacent to it.
- [ ] Compute the **offset** = desired stopper − current stopper (degrees). This
      is how far the antenna must be re-clamped in Part 3.

## Part 2 — Coordinate the shared rig

- [ ] Tell all operators the rotor is **offline** for reconfiguration.
- [ ] Stop / park PSTRotatorAz and any Windows clients so nothing sends bearing
      commands during the work.
- [ ] Note current PSTRotator calibration (north offset / min-max) so you can
      re-verify it afterward.

## Part 3 — Physical relocation (tower work)

The mechanical end-stops are fixed inside the rotator body; the stopper's
**compass** position is set by how the antenna is clamped to the mast. Moving it
means re-clamping the antenna by the Part-1 offset.

- [ ] Kill controller power. Secure the tower; have a ground crew member.
- [ ] Drive the rotator to a **known mechanical stop** (do this before climbing,
      then power off) so you have a fixed reference.
- [ ] At the antenna: loosen the mast clamps, **rotate the antenna on the mast by
      the offset** so that — with the rotor at its stop — the dead zone now points
      at your desired stopper heading. Re-tighten to spec.
- [ ] **Re-check the coax service loop** for the full 450° sweep (manual step 11:
      "provide sufficient slack… so the antenna can rotate over its full 450°
      range without putting any tension on the coax"). Re-dress and secure.

## Part 4 — Recalibrate the controller

Adapted from the G-800DXA manual "Indoor Performance Check and Alignment"
(steps 5–14). Set the rear-panel **SELECT SWITCH → ADJ MODE** first; return it to
**OPERATION MODE** when done.

- [ ] Drive fully CCW to the stop; set the indicator **needle** to the stop
      reference (factory: 180° S) — reseat the needle/bezel or use **FULL SCALE
      ADJ** as the manual directs.
- [ ] Verify a full 360° CW sweep returns the needle to the same reference
      (calibration marks on the bell/base realign).
- [ ] `PRESET` to 180° → START; adjust **PRESET ADJ A** until it stops exactly at
      180°.
- [ ] `PRESET` to 270° → START; adjust **PRESET ADJ B** until it stops exactly at
      450° (270° W in the overlap).
- [ ] Confirm the **OVERLAP LED** lights at the correct point; trim with the
      **OVERLAP LED ADJ** pot if needed.
- [ ] Install/rotate the **dial heading sheet** so the display reads *true compass
      bearing* for the new orientation (the sheet can place N — or any direction —
      anywhere on the dial).
- [ ] SELECT SWITCH → **OPERATION MODE**, power cycle.

## Part 5 — Recalibrate the ERC-Mini

So the serial bearing (GS-232B `C` → `AZ=ddd`) matches the controller after the shift.

- [ ] Recalibrate the **ERC-Mini** with its own **Service-Tool** (azimuth
      start/end setpoints against the rotator's pot), per the ERC-Mini manual. This
      replaces the old Idiom Press RotorCard `K` calibration-mode procedure, which no
      longer applies now that the ERC-Mini fronts the rotator.
- [ ] Verify: `rotor read` matches the controller dial at several headings
      (N/E/S/W). If they disagree, the ERC-Mini calibration isn't done.

## Part 6 — Verify end-to-end

- [ ] Sweep the full range; confirm the **dead zone is now where you intended**
      and the overlap sector sits in the unused direction.
- [ ] Confirm no "long way" travel when pointing in your commonly-used sectors.
- [ ] Re-check the **coax** has slack across the whole sweep.
- [ ] Bring PSTRotatorAz back online; **re-verify its calibration** and every
      client's headings/presets against `rotor read`.
- [ ] Tell the other operators it's back.

---

## Sources

- [Yaesu G-800DXA / G-1000DXA / G-2800DXA User Manual](https://static.dxengineering.com/global/images/instructions/ysu-g-800dxa_os.pdf) — alignment steps 5–14, dial heading sheet, coax slack (step 11)
- [Idiom Press Rotor-EZ / RotorCard Control Protocol](https://www.hamsupply.com/wp-content/uploads/2015/11/Rotor-EZ-Protocol.pdf) — `K`/`k` calibration mode, jumper-vs-serial persistence
- [Rotor-EZ manual index (Ham Supply)](https://www.hamsupply.com/support/rotor-ez-manual/)
