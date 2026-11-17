# Engine rule fixes, Round 5 (2026-11-17)

Continues `spec.md` in this directory; its sections Constraints and Test architecture bind this round unchanged. Round 5 builds Westley's rulings of 2026-11-17 and leaves the stage 4 rules it touches with a qualifying proof, so that stage 4 can be judged on an engine that obeys its rules.

Pre-flight (2026-11-17, `origin/main` `ade315c0b`): the rules below read as quoted in `docs/bible/epics/E-11-units-and-combat.md` (R-087-01, R-087-03, R-087-04, R-087-10) and `E-13-movement-and-command.md` (R-096-02, R-096-08, R-097-03, R-097-05, R-208-01) on this branch's first commit; no `Q-` row is open on S-087, S-096, S-097 or S-208; `csrc/ouroboros_sim.h`, `signatures.toml` and the pipe frames are not touched by any piece; the work list (engine sites, tests that go red, checker predicates) is `docs/reports/2026-11-17-targeting-rulings-check.md`, read against the engine at `2f2faa223`, which is the engine on this tip; the near-proof candidates are `docs/reports/2026-11-17-requirement-audit.md`. Not checked by running: that every candidate test is green today (the verifier's first step).

Run: one workflow from the Architect chat (DEC-round5-workflow-2026-11-17). Worktree `~/Projects/om-wt/er5`, branch `s/engine-rules-r5`. Every agent reads `~/Projects/om-wt/engine-rules-baseline/AGENT_RULES_R5.md` first.

## Pieces

Each piece names its rule, what is built, the kind of proof and the configuration the proof runs in. "Lab configuration" is what `scripts/skilllab/arena` launches for stage 4: walking units, obstacles, sight on.

### G1. Notice distance (E-11 R-087-04, E-13 R-096-02)
An idle or attack-moving unit with no target acquires the nearest enemy its side sees within its notice distance, and no enemy beyond it. The notice distance is the weapon's reach to that enemy (attack range with the reach table's multiplier for the target's layer, slant as R-087-10 has it) times `1 + OM_NOTICE_MARGIN`, `OM_NOTICE_MARGIN = 0.1` (`DRAFT-notice-margin`): one named constant, new, in an internal header; no public header changes. The leash (`om_tac_leash`) is not changed: it stays the larger of sensor radius and attack range and is no longer the acquisition radius.
Proof: scenario in `tests/csim/` (a Vanguard, range 300: an enemy standing at 340 is never acquired over 200 ticks; at 320 it is acquired at the next cohort turn, walked to 300 and fired on; a plain mover never acquires; an attack-mover passing an enemy at 340 walks on); whole-run in the lab configuration through the checker predicate of G7 on a catalogue layout.

### G2. The lock ends at the notice distance (E-11 R-087-03)
A lock ends when the target dies, leaves the side's sight, leaves the unit's notice distance, or the player orders the unit; the leash and the give-up of R-087-09 end it as before. A target taken by return fire (R-087-06) is exempt from the distance break until that lock ends some other way. After a drop for distance an idle unit holds where it stands and an attack-mover resumes toward its point (R-087-04, R-096-02); the leash return of DEC-leash-anchor-return-2026-11-01 applies to leash drops only. Threat first is not built.
Proof: scenario (a locked target walks away faster than the unit: the lock drops on the tick the target is beyond the notice distance and the unit does not follow; a slower target is followed until the leash; a unit shot from 500 wu by an enemy it sees pursues it past its notice distance, bounded by the leash); whole-run through G7.

### G3. Guard (E-13 R-096-08, R-208-01)
A guard acquires within its notice distance as every unit does, no longer anything its side sees; it follows no farther than `GUARD_RADIUS` from its post; its lock ends as G2; it returns to its post when the lock ends or the chase would pass the radius. Return fire and the readings of DEC-engine-rules-round2-2026-11-11 are unchanged.
Proof: scenario (an enemy seen at 450 from a guard of range 300 leaves the guard at its post for 200 ticks; an enemy at 320 is engaged; a retreating target is followed to 200 wu from the post and no farther, per tick); whole-run through the existing guard predicate, adjusted.

### G4. Unseen fire (E-11 R-087-01)
An attack-mover still on its way to its point is neither moved nor stopped by a hit it cannot see or reach: no move away, no halt, its destination unchanged. An idle unit and an attack-mover that has arrived move 200 wu away and hold there; while holding they acquire and return fire as an idle unit; a repeat hit they cannot answer moves them again. Plain movers, guards and units holding a target are unchanged.
Proof: scenario (an attack-mover hit from a hill it cannot see up keeps closing on its point every tick; an arrived one moves away about 200 wu and is still there 400 ticks later with no hits; an idle one the same); whole-run in the lab configuration on L-0061 or L-0080: no walker with an attack-move destination stands still under unseen fire, and no unit moves away more than once without a new hit.

### G5. Slope collision and the probe (E-13 R-097-05, R-097-03)
Two units within 30 wu that both stand on the same slope collide whichever side of its midline each is on; the steering probe treats such a unit as a unit on its layer. Units on different layers that are not on one slope still do not collide.
Proof: scenario on a slope (two walkers meeting across the midline are pushed to 30 wu apart; a walker on flat ground under a flyer is not pushed); whole-run on the six hill layouts of the Round 3 trial: no two units on one slope closer than 30 wu after the pass except at the iteration cap, and no unit flips layer back and forth across a midline (three or more changes within 20 ticks).

### G6. Hill layouts (`lab-staircase.md` stage 4, DEC-hill-order-points-2026-11-17)
In a catalogue layout where one side must climb a slope to reach the other, that side's attack-move point lies at least `DRAFT-hill-order-margin` = 30 wu past the slope's midline, on the high side.
Proof: a lint test over `docs/northstar/research/layer_dynamics/catalogue/L-*.toml` that computes, from the layout's own geometry and orders, each climbing side's point against the midline. Layouts that fail are corrected by moving the point up the slope and nothing else; each correction is listed in the report with the old and new point, for Westley's veto.

### G7. The lab checker (`scripts/skilllab/invariants.py`, `tests/skilllab/arena/engine_rules_oracle.py`)
- acquire: a pick is legal only if the target was the nearest enemy the side saw within the picker's notice distance at the pick.
- lock: a lock that ends because the target left the notice distance is a legal end, not a swap; a lock kept on a target beyond the notice distance for more than one cohort period is reported, except a return-fire lock.
- unseen fire (new, R-087-01): as G4's whole-run statement.
- slope collision (new, R-097-05): as G5's whole-run statement.
- guard: a guard's pick obeys the notice distance.
Each predicate has a planted case that it reports and a legal case it does not, on fights it was not designed around (the lesson of Round 2: a check that agrees with its own description can still be wrong).

### G8. Seven near-proofs (`docs/reports/2026-11-17-requirement-audit.md`, the table "What is closest")
R-093-02, R-008-04, R-084-04, R-083-03, R-097-10, R-007-01, R-096-08: each candidate is brought to all seven qualifications of `docs/method/requirements.md` Proof, or the report says which qualification cannot be met and why. One named function per rule that quotes the rule's text as it reads on this branch; the Then asserted, not a neighbour of it; the lab configuration; a recorded break that turns it red. A per-tick check is never replaced by a final-state check.

## Order

1. Tests, three writers at once on disjoint files: G1 to G3; G4 and G5; G6 and G7. Each writes its new tests red, and rewrites the existing tests that assert the old rule (list: the check report, section B) in `Test-defect:` commits naming the ruling.
2. Lab builder: G7, then G6's layout corrections.
3. Engine builder one: G1, G2, G3 (`csrc/unit.c`).
4. Engine builder two: G4, G5 (`csrc/unit.c`, `csrc/tactical_move.c`).
5. Near-proofs: G8.
6. Verify: every suite against the baselines; recorded hashes and pinned fight lengths that moved are re-pinned in `Test-defect:` commits after the checker passes the new run; one deliberate break per piece, each turning its test red.
7. Sweep of 199 fights, the four stage 4 fights with controls and their pictures, the stand-off count on the hill and trap fights.

A builder that finds a test wrong reports it and builds the rest. A piece that needs a public header change stops and is reported.

## Acceptance (the Architect, before the merge)

- New tests green; no red outside the baselines except re-pins, each in its own commit.
- Sweep: the checker reports nothing under the new predicates, or each count is explained; end reasons (wipe, cap, stand-off) set beside Round 4's.
- Stage 4 fights re-made into `docs/northstar/story_reviews/westley/arena_stage4/`; outcome of each beside Round 4's; no fight invalid.
- `docs/bible/algorithms.md` ALG-62 and ALG-68 rewritten by the Architect to what the engine now does; Proof lines written for every rule whose test qualifies; the "not built" notes removed from E-11 S-087 and R-097-05; report `docs/reports/2026-11-17-engine-rules-round-5.md`.
