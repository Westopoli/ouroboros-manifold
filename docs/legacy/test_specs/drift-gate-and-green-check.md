# drift-gate-and-green-check

## Summary

Two independent fixes decided in the 2026-09-17 harness defect investigation (`docs/northstar/research/harness_defects_2026-09-17/`), bundled into one cascade because the second fix's targeted verification (S-021/S-033 style budget test) depends on the first fix landing.

1. **Drift gate** — `csrc/sim.c` runs the passive-drift loop unconditionally, ignoring `OM_FEAT_DRIFT`, and runs it *before* the faction/friction/admin-revolt block instead of after (`docs/bible/algorithms.md`'s tick sequence puts drift at step 5, after faction agents at step 3). This is card 202b2's actual blocker: the card cannot be built because the harness that would grade it is itself broken. The fix gates the loop on `OM_FEAT_DRIFT`, moves it to run last (after factions/friction/admin-revolts), and sets `OM_FEAT_DRIFT = 1` in `om_world_new` (every other feature switch stays off — that default is a separate open flag, A4).
2. **green_check** — the spec factory pipeline (`docs/northstar/spec_factory.md`) has `red_check.py` (confirms a card's stub fails its acceptance test) but nothing that confirms a *reference* implementation of a card actually passes — so a detector that can never fail was possible to ship undetected. `scripts/specfactory/green_check.py` closes that gap for future cards; it is infrastructure, not itself gameplay behavior.

## Acceptance criteria

1. `OM_FEAT_DRIFT` switched off skips the drift step entirely; a region's four fields are byte-identical across a tick.
2. `om_world_new` returns a world with `OM_FEAT_DRIFT` on and every other feature switch off.
3. With `OM_FEAT_FACTIONS` and `OM_FEAT_DRIFT` both on, the same-tick faction budget step (ALG-17) reads each region's economy as it stood *before* that tick's drift — drift runs after factions in the tick, not before.
4. The existing `csrc/faction.c` budget body (`om_faction_step_budget`, committed `d641ea2`) produces the exact ALG-17 answer — `budget_after == pytest.approx(2.275)` in `tests/csim/test_E05_S033_territory_pays_or_costs.py::test_R_033_01_budget_66_8_40_8` — once (3) holds; it does not today, because drift-before-factions perturbs the economy values the budget step reads. That test's later, unrelated assertion (`len(decisions) >= 1`, line 70) stays failing regardless: it depends on `om_step_decisions` in `csrc/agent.c`, a separate unimplemented stub this cascade never touches. AC4 is about the budget assertions specifically, not the whole test going green.
5. `green_check.py`, given a card file path and a reference implementation file, applies the reference in a scratch git worktree and runs the card's acceptance command; exits 0 only if it passes, and refuses (non-zero, explicit reason) a reference that also passes against the untouched stub — a detector that cannot fail is rejected, not silently accepted.
6. `docs/northstar/spec_factory.md`'s pipeline table gains a row for `green_check.py` describing what it checks and where its reference bodies live.

## Inputs / Outputs / Constraints / Out of scope

Inputs: `OM_FEAT_DRIFT` and other feature-switch state on `om_world`; tick sequence position; for green_check, a card file path, its acceptance command, and a reference body file.

Outputs: whether the drift step executed on a given tick; which economy value the same-tick budget step observed; green_check's exit code and stderr reason.

Constraints: the drift math itself (`ALG-01` through `ALG-10`) is unchanged — this is a gating and ordering fix only, never a formula change. Trace and checksum emission (currently inside the per-region drift loop) move with the loop, so a checksum keeps capturing end-of-tick state (matches `tick.py`, which logs after drift, its step 7).

Out of scope: A4 (feature defaults for EVENTS/FACTIONS/FRICTION/ADMIN_REVOLTS/DIPLOMACY/TECHNOLOGY beyond DRIFT), the "earlier suites stay green" clause, card 202b2 itself (retired, not rebuilt — its only content was the budget body, already committed by hand), bulk `## Header slice` authoring for the other 135 spec-factory cards, GDScript whole-file mode.

## Scale & Boundary Profile

- **N typical / N peak:** drift gate: 1 region (unit) to 60 regions (E-02's confirmed scale gate, `docs/bible/epics/E-02-region-fields-and-drift.md` "Scale requirements"). green_check: one card per invocation, no batch mode in this wave.
- **Growth claim per hot path:** `unbounded-unknown — assert growth only, no absolutes`. Neither change touches a loop's asymptotic shape; the drift loop's existing O(n_regions) walk is unchanged, only gated and relocated. green_check runs one worktree + one acceptance command per call — O(1) in card count.
- **Memory posture:** bounded-buffer (no new allocation shape; green_check's scratch worktree is disk, not memory, and is a fixed-size checkout).
- **External call budget:** green_check shells out to `git worktree add` once per invocation; the acceptance list runs at most twice per invocation (once against the untouched worktree, once against the applied reference — the whole point of the detector) — never per-file, never in a loop.

## Bible Compliance

- **Bible path:** `docs/bible/epics/E-02-region-fields-and-drift.md` (story S-160), plus `docs/bible/algorithms.md` (tick sequence, unchanged text, cited for order) and `docs/northstar/spec_factory.md` (pipeline table, not a bible file but the doc of record for the spec-factory tooling green_check extends).
- **Sections referenced:** E-02 epic "Stories" (new S-160), "Ways this could be wrong" (new bullet); `algorithms.md` "Tick sequence" lines 9-29.
- **Deliberate divergences:** none. This spec implements decided fixes; it does not change any retained equation or any bible claim beyond correcting the stale feature-switch-defaults sentence in `csrc/ouroboros_sim.h`'s header comment (a code comment, not a bible file, but the same stale-doc-tripwire discipline applies).
