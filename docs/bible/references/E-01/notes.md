# E-01 Layer System — Look and behavior references

**Not external screenshots — a design phase.** The layer system is Ouroboros's most important, distinctive mechanic and is hard to change once built, so it earns a serious design phase instead of a reference pull from other games. Westley does not yet know exactly what it should look like; he will decide by interacting with real options.

## The plan (Westley, 2026-09-13)

1. **Build basic unit movement on a single layer first.** The earliest epics ship a plain one-layer movement prototype in Godot — no layer mechanic yet. This exists specifically to be the sandbox for step 2.
2. **Claude develops a plan to build several layer-system options in Godot** on top of that prototype — different looks and interactions for the stack, height changes, the layer ring/strip, and pulses — that Westley can play with and choose between.
3. Westley picks; the chosen option becomes the E-01 visual end-state and these references are filled with Godot renders of it.

Until step 3, the "references" for E-01 are Godot mockups we produce, not images Westley supplies. Flag Q-E01-08 stays open, but its resolution path is this design phase, not a screenshot hunt.

## Westley's recorded layer ideas

Westley's layer decisions from this planning round are captured as closed rows in `docs/northstar/ambiguity_register.md` (Q-001-xx, Q-002-xx, Q-008-01): always 5 layers engine-wide; layer 1 is the bottom; no auto layer-change (the player owns it); one transition of 1–2 s regardless of distance; cross-layer combat is an intended strategic tuning lever (range/damage vary by layer offset), still under research. The Godot options in step 2 must honor these.

## Slots to fill once the Godot options exist

| # | Story | Shot subject | Aspect — the example | Proves / contrast |
|---|---|---|---|---|
| 01 | S-009, S-010 | Layer stack (5 layers) at normal camera distance | how depth reads at once without clutter | — |
| 02 | S-002, S-004 | Unit changing height (clip) | the 1–2 s transition reads as a height change | — |
| 03 | S-009 | Layer-color ring under a unit + HUD layer strip | current layer legible per-unit and globally | — |
| 04 | S-006 | Sensor pulse reveal and fade (clip) | the reveal sweep and its decay | — |
