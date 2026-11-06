# Stage 4, L-0061 (vantage) investigation, 2026-11-06

Investigator: Sonnet 5.5 sub-agent, read-only. Method: hooked `Engine.step` and logged every tick of the real engine, seed 10, on `run.fight`. Westley's reports: (A) in the control, red never shoots back at blue; (B) red is supposed to see blue when blue walks up the ramp past the halfway threshold defined in the bible; the lab has diverged from his rules.

## (B) Regular fight: red never sees blue (PROVEN)

Rules:
- E-01 R-005-09: in a ground era a lower layer never sees up. A unit on a slope counts as the band on its side of the midline.
- R-004-06 and R-004-08: below the midline you are on layer L, at or above it on layer L+1. R-004-02: from the midline the unit attacks as a unit of the layer it is moving to.
- R-001-06: a slope has a midline halfway along its length. R-001-07: a walker changes layer only by walking a slope.
- S-004 title (`docs/bible/stories.md:10`): the halfway line is a place the player "can see and hold".

Cause:
- `scripts/skilllab/arena/features.py:3-6` builds only planar blocks and the `slope` kind. The `vantage` kind is drawn only, so L-0061 gets no terrain.
- With no terrain the engine skips its walker slope logic (`csrc/tactical_move.c:3458-3478`); `csrc/unit.c` keeps the spawn layer. Blue is layer 1 and red layer 0 from tick 0, and red never changes layer in either fight.
- The ramp Westley sees is `layout_shot.gd` drawing it (`RAMP_WU` 200: foot at radius 900, rim at 700, midline at 800). A red unit first passes the drawn midline at tick 101 and the rim at tick 125. At tick 200 all 23 living red are past the midline, still layer 0, seeing 0 blue.
- If red were set to layer 1, both sides see each other at tick 1 and red targets 5 at once. With a real slope built (4v4 test) the engine flips red to layer 1, red sees blue and fires. The rule works in C when the lab supplies terrain.

Divergences:
- D1: no slope or height band for a vantage layout. H-088 marks it out of scope for stage 4 (height bands as terrain are stage 5). The stage 4 README line "red walks in blind until it is on the band" is false for this fight.
- D2: layer comes from the layout's `layer` column, not from ground. Conflicts with R-200-01/02.
- D3: the lab sets reach (0 up, 1 down) for every role (`run.py:48,149`) against R-164-01. With the table as written: sight on, nobody ever fires; control, red Raiders and Interceptors fire up from tick 94 and blue never fires, the opposite of what the lab shows. The game itself never sets reach, so it is 0/0 today.
- Side finding: on a built slope the cross-over (`csrc/terrain.c:948`) sits at x about 2200, not the geometric halfway at 2000. Cause UNPROVEN.

## (A) Control: why red does not return fire (PROVEN)

- The control removes only sight targeting; reach stays 0 up 1 down.
- Red on layer 0 against blue on layer 1 is offset 1 against up 0, so `om_tac_in_reach` (`csrc/unit.c:573`) rejects it. The same check gates acquisition, return fire and fire (lines 1734, 2164, 2216).
- Red targets are 0 at every tick of both fights and blue loses no hp. Blue first targets at tick 57.
- Range is not the cause: red is within its attack range of blue (515 of 552 pairs at tick 200) and stops at tick 193 in blue's arc, 16.7 wu from the nearest blue.
- With reach up forced to 1 (monkeypatch only) the control has red targeting from tick 58 and a different fight (2979 ticks). With sight on and reach up 1, red still cannot see up, as R-005-09 says.

## Shared with L-0080 and L-0083

Each carries two `vantage` features and has 8 and 15 units written `layer = 1`. D1 to D3 apply to both.

## Smallest candidate fix

Build the vantage as real terrain (a rise of one band with a ramp, using the `slope` machinery, unit layer taken from the ground). That is stage 5 height-band work. The control cannot show red returning fire while reach up is 0. Whether red may fire up and Line may fire down is Westley's R-164-01 ruling.

## Open questions

Is "halfway" the drawn ramp midline or the engine's band boundary? Red stays on layer 0 under either. Guard radius and the flinch rule (R-087-01) were not re-measured (UNPROVEN).
