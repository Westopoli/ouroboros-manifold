# Movement: the old side-step on main (2026-11-24)

Decision: `DEC-movement-sidestep-2026-11-24` in `docs/northstar/story_reviews/westley/decisions.md`. Westley approved variant A of the comparison artifact (https://claude.ai/artifact/8YJhVNwQnRo7FCuXYSS6RG, version 3). This spec turns the scratch experiment into the shipped rule. A cascade: one test writer, then one different implementer, both Sonnet; the chat (Architect) drives and writes the docs. Method and Constraints are those of `docs/northstar/plans/engine-rules-2026-11-08/spec.md` (Constraints and Test architecture bind, in particular: per-tick assertions are never replaced by final-state ones).

## The behaviour

All in `csrc/tactical_move.c`; `csrc/ouroboros_sim.h`, `signatures.toml` and the pipe frames are not touched.

1. **No give-up.** `om_move_giveup_pass` and everything that exists only for it are deleted: `giveup_near` (state, its reset at both order-start sites, the `om_tac_move_reissue` reset, the hash word, the save and load words), `OM_GROUP_GIVEUP_RADIUS`, `OM_GROUP_GIVEUP_TICKS`, and `OM_STEERING_DETOUR_MIN_DIST` if nothing else uses it (line ~2552 uses it today: read it, keep the constant only if still needed). An order ends only as before: arrival (R-099-04 radius and slot), a new order, death, or the pursuit and guard rules. No dead code, no disabled code that looks live.
2. **Probe skip.** The probe gather (both the cell scan and the displaced-unit spill list in the function around line 2053) skips a unit `cid` for mover `id` when `ms->units[id].group_id != 0 && ms->units[cid].group_id == ms->units[id].group_id`, or when `ms->idle[cid]` and `om_unit_get_faction(w, cid) == om_unit_get_faction(w, id)`. Enemies, and friends that are moving, holding a target or engaged, still block. The comment above the gather ("group mates and idle friends included") is rewritten.
3. **Committed detour.** In `om_move_steer_step`: if the straight probe is clear, the detour state is cleared; otherwise the sweep tries the six angles +30, -30, +60, -60, +90, -90 degrees in that order, but a unit that already has a detour tries only the angles on the side of its stored detour (`(steer_x * detour_dy - steer_y * detour_dx) > 0` means the first side, as in the experiment); a found angle is stored as the detour and kept until the straight line is clear again (replaces the 60 wu `detour_remaining` hold; the field is renamed or removed to say what it now is); if no angle on its side is clear it keeps its stored heading. Deterministic: fixed angle order, no randomness.

The reference implementation is the scratch experiment and is the acceptance bar, not the code style: `~/Projects/om-wt/engine-rules-baseline/r6-advance/diffs/A.diff` (against `t-a`, which is V1 plus logging) and `~/Projects/om-wt/engine-rules-baseline/r6-giveup/diffs/v1.diff`; the full scratch tree is `~/Projects/om-wt/engine-rules-baseline/r6-advance/t-A`. Strip every `EXPERIMENT` marker, the `adv_*` logging variables, the `1e9` sentinel (use a named flag or a plainly named field), and the `OM_DBG_*` getters.

## Acceptance

1. **Byte-identical fights.** Recorded with the lab engine on the built branch, seed 1, one attack-move per side at tick 0 (the layouts' own orders), the fight files for L-0054 (`docs/northstar/research/layer_dynamics/catalogue/L-0054.toml`) and SIT-0106 (converted layout `L-0106`) equal variant A's files: L-0054 at every 2 ticks, tick count 6408, winner side B, 17 survivors; SIT-0106 at every 2 ticks, tick count 2301, winner B, 13 survivors. The recorded sha256 of A's files are in `~/Projects/om-wt/engine-rules-baseline/r6-compare/out/*-A.facts.json` and the files themselves under `~/Projects/om-wt/engine-rules-baseline/r6-compare/runs/`. Compare the frames (positions, hp, targets, orders), ignoring the document's `layout_path` line and any hash of internal state (the movement state hash changes because `giveup_near` is gone).
2. Determinism: two runs, identical bytes.
3. The lab's carried-through check: no alive unit ends a fight with an active order, no progress for 200 ticks and a free path.
4. csim, transport and QA suites green, with every change to an existing test in a commit carrying `Test-defect:` naming `DEC-movement-sidestep-2026-11-24`.

## Save format and goldens (a known cost)

Removing `giveup_near` removes a word from the movement hash and from the movement save slot (`mv_put_u32` / `mv_get_u32`, `tactical_move.c` ~3823, ~3941, ~4092). That changes golden hashes and the save-blob layout. The test writer lists every test that pins them (search `giveup`, the movement save-slot tests, `baseline hashes` files, A99, F1, F2, F3, S101); the implementer re-pins in `Test-defect:` commits. If the save-blob change needs a format version bump under an existing contract (`docs/architecture.md`), the implementer stops that part and reports; the chat decides.

## Tests (written first, red)

By the test writer, never the implementer. Each names the rule it proves.

- `tests/csim/`: (a) a blocked group attack-mover with a friend in front is never given up: per tick for 3000 ticks its order stays active until arrival; (b) probe skip: a group mate and an idle friend do not deflect a mover, an enemy, a holding friend and a firing friend do; positive control that goes red when the skip is removed; (c) committed side: a unit that deflected left on tick t does not deflect right while the straight line stays blocked, and clears the detour once the line is clear; (d) lone unit: no give-up either.
- Lab whole-run, `tests/skilllab/`: L-0054 and SIT-0106 reproduce variant A's per-tick positions (read A's fight files by path from the scratch folder named above; copy a compact hash per 100-tick block into the test, not the files). The carried-through check as a per-tick invariant.
- Retire or rewrite with `Test-defect:` the tests whose rule is gone: `tests/csim/test_E13_R099_05_*`, `test_PP_unit_giveup.py`, `test_E11_R087_09_blocked_line_gives_up.py` (check what it really pins: R-087-09's own give-up of a target is a different rule and stays), and the give-up assertions inside `test_E13_R097_10_*`, `test_E13_R096_02_order_kept_through_shot_pause.py`, `test_E11_S087_redirect_resumes_original_point.py`, `test_collision_radius.py`, `test_PP_collision_radius_runtime.py`, `test_F1_fog_per_faction_observers.py`.

## Documents the change makes wrong (the chat rewrites them; agents list, not edit)

`docs/bible/algorithms.md` ALG-68 (the "Direction changed 2026-10-02, rewrite pending" paragraph and the give-up sentence); `docs/bible/epics/E-13-movement-and-command.md` R-099-05 (removed), R-099-04 (the lone-walker clause that cites the give-up), R-097-03, R-096-02 (the give-up exception), R-097-10 note and Q-097-04; `docs/bible/references/movement-requirements.md` (row "A blocked unit" and the contradicted-by-ruling rows); `docs/northstar/plans/engine-rules-2026-11-08/round6.md` pieces E2 (superseded); `docs/stories/H-040.md` (the give-up mention if any); the approved fights' expected winners in `docs/northstar/research/layer_dynamics/arena/approved.toml` (move to the new results, decision id in each row).

## Pieces

1. **LS1 tests** (test writer): the red tests above, the list of pinning tests, the byte-comparison helper.
2. **LS2 build** (implementer): the three behaviour changes and the deletions, one commit each, wiring last; re-pin commits with `Test-defect:`.
3. **LS3 regression and report** (a third agent, read-only on source): the standing regression over every `approved.toml` row before and after (winner, survivors, last tick, end kind), written to `docs/reports/2026-11-24-movement-sidestep-landing.md` as a table; csim, transport and QA chunk results.
4. **LS4 beta check**: pipe build, `scripts/play.sh --check`, and a played movement scene; the Mac walk is Westley's.
Open: none for Westley. Every number the spec leaves is named `DRAFT-` in the code and listed in the report.
