# Stage 11b — Per-Mission Map Variety Wiring

## Goal

Wire the per-mission map seed contract that Stage 7 specified but never implemented, so that the existing map generator pipeline actually produces varied maps across missions instead of repeating the same layout. The variety machinery — authored layouts, archetype filters, jitter, canvas scaling, simulation flavoring, fairness retry — is fully built and works correctly when given a unique seed. The bug is purely in the input: every mission generated at the same simulation tick currently receives `seed=current_tick`, which collapses all variety axes to a deterministic single output. This spec closes that wiring gap.

**Not in scope:** Library hints system (bible §"What Makes Each Mission Unique" item 3 — dozens of per-archetype flavor modifiers, never implemented; not blocking core variety, deferred); the pre-mission map preview UI (separate future spec, blocked on this one landing); layer visuals, fog of war, and mid-mission HUD work (see `stage_11c_layer_visuals_and_fog_spec.md` and `stage_11d_mid_mission_hud_spec.md`); fairness evaluator behavior changes (it works as-is and benefits automatically once seeds vary).

**Architecture.** This is a contract wiring fix entirely on the simulation side. The map generator (`map_generator.py`) is a pure function `(archetype, region_state, canvas_size, seed) → MapGenerationResult` and remains unchanged. Stage 5.5's mission generator (`mission_generator.py`) gains responsibility for producing a unique random seed per mission and embedding it in `MissionSetup.map_params`. Stage 7's pipe transport (`pipe_transport.py`) gains responsibility for reading that seed out of `MissionSetup.map_params` instead of synthesizing one from `current_tick`. The `MissionSetup.map_params` field already exists as a plain `dict` — this spec gives it an enforced schema. No Godot-side changes. No tick delta shape changes.

## Bible References

- **`docs/bible_history/bible_2_00_world.md`** §"Generation Pipeline" (lines 174–211) — confirms the four-axis variety design (layout × canvas scale × library hint × simulation state × gradient texture). Confirms that the seed is the controlling input.
- **`docs/bible_history/bible_2_00_world.md`** line 178 — *"…and a **random seed** (ensures reproducibility for replays and bug reports)."* The bible explicitly specifies "random seed," which resolves the derivation question (see Design Decisions below).
- **`docs/bible_history/bible_2_00_world.md`** line 196 — *"the map is regenerated with a **new random seed**"* on fairness failure. Confirms that retries draw a fresh random seed, not a derived one.
- **`game_bible.md` (hub)** lines 534 — sim runs at 20 ticks/sec, Godot at 60fps. Establishes the relevant performance budgets.
- **`docs/bible_history/bible_2_00_combat.md`** line 313 — same: *"simulation at 20 ticks/sec, Godot at 60fps = 3 render frames per tick."*

Do NOT read `docs/bible_history/bible_2_00_missions.md`, `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_antagonist.md`, `docs/bible_history/bible_2_00_ai_pipeline.md`, or `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) — not relevant to map seed wiring.

## Cross-Stage References

- **Stage 5.5 (mission generation)** — `mission_generator.py` constructs `MissionSetup`. This spec extends what it puts in `MissionSetup.map_params`. No other Stage 5.5 logic changes.
- **Stage 7 (map generation)** — `map_generator.py` and `map_gen_contracts.py` unchanged. Stage 7 spec line 122 specified that `MissionSetup.map_params` must carry the seed. That requirement was never wired through. This spec finishes that wiring.
- **Stage 8 (Godot bridge + persistence)** — the seed must persist into save state per bible reproducibility requirement. `MissionSetup` is already part of persisted mid-mission state per Stage 8's persistence design. Verification only — no new persistence logic needed (see Checkpoint E).
- **Stage 11 (world view + chronicle + transition)** — Checkpoint F of Stage 11 assumes varied missions. This spec is a prerequisite for Stage 11 closure.
- **Stage 11c / 11d** — independent of this spec; can proceed in parallel after this lands.

## Design Decisions

### D1 — Seed source: random per mission, persisted with save

**Decision:** Each mission generates its own seed via `rng.randint(0, 2**31 - 1)` at mission generation time (Stage 5.5), drawn from the mission generator's existing RNG. The seed is stored in `MissionSetup.map_params["seed"]` and persists with the save file as part of normal `MissionSetup` serialization.

**Bible authority:** `docs/bible_history/bible_2_00_world.md:178` and `:196` both say *"random seed."* The reproducibility clause in `:178` (*"ensures reproducibility for replays and bug reports"*) is satisfied by **storing** the seed at generation time, not by **deriving** it deterministically from a tuple. So long as the seed lives in the save file, the same map can be regenerated on demand — that's the bible's reproducibility contract.

**Alternatives rejected:**
- *Deterministic seed derived from `(current_tick, region_id, mission_index)`*: would also work, and was the implementer's first instinct. Rejected because the bible uses the explicit phrase "random seed" twice, and deterministic derivation creates implicit cross-mission coupling (changing how one input is computed retroactively changes all maps). Random + persisted is simpler and matches the bible literal.
- *Seed = `current_tick`* (the current bug): rejected because it collapses the seed space across all missions generated within the same tick.

### D2 — Schema enforcement: typed contract on `MissionSetup.map_params`

**Decision:** Replace the bare `map_params: dict` field on `MissionSetup` with a typed schema. The Stage 7 spec listed required keys (`archetype`, `region_id`, `canvas_size`, `seed`, `generated`) but the dataclass was never updated. This spec lands the schema as a `MapParams` `TypedDict` (or frozen dataclass — implementer's choice, see "What to Build"). The required key for this spec is `seed: int`. Other keys may be present but are advisory; the only consumer that strictly requires `seed` is `pipe_transport.py`.

**Why a schema rather than continuing with bare dict:** the bug we're fixing is exactly the kind of bug a schema prevents — a contract field silently empty. Making the schema explicit at the dataclass boundary means the next consumer that adds a key gets a clear contract change rather than a silent dict mutation.

### D3 — Compatibility with existing saves: graceful fallback at the consumer

**Decision:** `pipe_transport.py` reads the seed via `setup.map_params.get("seed", current_tick)`. The `current_tick` fallback exists exclusively for old saves (pre-this-spec) that have empty `map_params`. After one mission generated post-spec, all subsequent reads hit the explicit seed.

**Why fallback rather than migration:** migration would require touching the save loader to backfill seeds, which is more risk than the fallback. The fallback path produces the same buggy behavior the player has today, so old saves don't get worse.

**Removal:** the fallback is technical debt. A `# See also: simulation/mission_generator.py — seed required to be present in new missions` comment marks it. Once we're past the launch ZIP, the fallback can be removed and a missing seed should raise.

## What to Build

### Files to modify

**`simulation/mission_contracts.py`** — `MissionSetup` dataclass.
- Add a `MapParams` TypedDict (preferred; keep it near `MissionSetup`):
  ```python
  class MapParams(TypedDict, total=False):
      seed: int
      archetype: str
      region_id: str
      canvas_size: int
      generated: bool
  ```
  `total=False` lets Stage 7's optional keys remain optional. Only `seed` is required by current consumers; we don't enforce required-ness in the type to avoid breaking old saves at load time (see D3).
- Change `map_params: dict` → `map_params: MapParams` on `MissionSetup`. Default factory remains `dict` since `TypedDict` is a `dict` subtype at runtime.
- Add a one-line module comment above `MapParams` pointing to this spec doc and to `pipe_transport.py:~375` (the consumer).

**`simulation/mission_generator.py`** — line ~621 (where `MissionSetup` is constructed with `map_params={}`).
- Generate the seed from the mission generator's existing RNG: `seed = self._rng.randint(0, 2**31 - 1)` (use whatever the existing RNG attribute name is — confirm at implementation time).
- Construct: `map_params={"seed": seed}`.
- Add a `# See also: simulation/pipe_transport.py — consumes this seed` comment.
- The seed is generated **after** archetype selection but **before** any logging/serialization of the mission setup, so logs for that mission carry the seed for debugging.

**`simulation/pipe_transport.py`** — line ~375 (where `GeneratorInput` is built).
- Replace `seed=current_tick` with `seed=setup.map_params.get("seed", current_tick)`.
- Add a `# See also: simulation/mission_generator.py — seed source; current_tick fallback only for pre-Stage-11b saves` comment at the call site.
- Log the seed source on each call (e.g., `log.debug("map gen seed=%d source=%s", seed, "map_params" if "seed" in setup.map_params else "current_tick_fallback")`). This log line is part of the baseline-and-verification pattern (see Checkpoints).

**`docs/architecture.md`** — add a `MissionSetup.map_params` schema section.
- Document the `MapParams` TypedDict shape.
- Document the `seed` field's lifecycle: generated by Stage 5.5, consumed by Stage 7, persisted with `MissionSetup` per Stage 8.
- Note the `current_tick` fallback in `pipe_transport.py` and that it's a temporary compatibility shim. Per CLAUDE.md, contract-shape docs live here. (CLAUDE.md's specific rule names tick delta shape; the same discipline is applied to mission contracts because they're equally cross-stage.)

### Files to create

**`tests/diag_map_variety.py`** — variety self-test harness, lives alongside other `diag_*` tools per simulation file map. Generates N missions per archetype using a stub Stage 5.5 driver, runs them through the existing map generator, and reports:
- Per-archetype: count of unique `chosen_layout_id`s out of N missions.
- Per-archetype: per-layout selection count (histogram).
- Per-archetype: ratio of unique layouts hit / size of archetype's compatible-layout pool.
- Aggregate: pass/fail against a `LAYOUT_DIVERSITY_MIN_RATIO` threshold (default 0.8, i.e., 80% of compatible pool must appear over 30 missions).

This is run by checkpoint scripts; it is also useful as a permanent regression check. Keep it simple — no graph generation, just printed metrics.

## Checkpoints

> **Escalation rule — read this before running any checkpoint.**
>
> When a checkpoint's after-state measurement does **not** match this spec's expected outcome — whether a test fails, a baseline doesn't reproduce, a perf number regresses outside the stated tolerance, a schema check rejects something it shouldn't, or any output is unexpected enough that the implementer would be guessing at the cause — **STOP**. Do not modify the implementation, the test, or the spec to make it pass. Do not iterate on a fix.
>
> **FLAG the discrepancy and bring it to Westley.** Include: which checkpoint, what was measured, what was expected, what was observed, and the implementer's hypothesis if any. Wait for guidance.
>
> The cost of a wrong silent fix is a debugging session three weeks from now without context; the cost of a five-minute escalation is five minutes. Default to escalation.
>
> This rule exists per CLAUDE.md ("No shotgun fixes" and "One confirmed diagnosis is worth ten guesses") and applies uniformly to every checkpoint below.

Each checkpoint follows the **measure → change → re-measure** pattern: log the relevant baseline state before the change, make the change, log the new state, confirm the delta matches the expected outcome. A checkpoint is not "passed" until the after-state has been logged and reviewed — making the change without re-measuring leaves a blind spot.

### Checkpoint A — Baseline confirmation: the bug exists and is shaped as expected

**Purpose:** Confirm the gap report's diagnosis with measurement before touching code. If the bug doesn't reproduce as described, the spec is wrong and should be re-investigated rather than implemented around.

**Baseline measurement:**
1. Run `python -m tests.diag_map_variety` with N=10 missions per archetype, all generated at a fixed `current_tick=1000`. (Build the harness as a first step of this checkpoint — it's a Stage 11b deliverable, so writing it here is correct.)
2. Expected baseline output: every archetype reports exactly **1 unique layout** out of 10 missions. Layout diversity ratio: 1 / pool_size for every archetype.
3. Save the printed output to `tuning_output/stage11b/baseline_variety.txt` for the after-comparison.

**Pass condition:** baseline output matches expectation (1 unique layout per archetype). If diversity is already > 1, the bug doesn't reproduce — stop and re-investigate before changing code.

**No code change in this checkpoint.** Only the diag harness (`tests/diag_map_variety.py`) is created. Run it, save the baseline.

### Checkpoint B — Contract schema: `MapParams` lands on `MissionSetup`

**Purpose:** Make the contract change in isolation, before either producer or consumer is touched. Verifies that the schema itself doesn't break anything — existing constructions of `MissionSetup` (with `map_params={}`) must remain valid.

**Baseline measurement:**
- Run the existing test suite: `python -m pytest simulation/` (or whatever the project's test invocation is — confirm at implementation). Log pass/fail counts.
- Confirm `MissionSetup` is currently constructed with `map_params={}` in at least one test or harness.

**Change:**
- Add `MapParams` TypedDict to `mission_contracts.py`.
- Change `MissionSetup.map_params: dict` → `map_params: MapParams`.
- Add the spec-pointing comment.

**After-state measurement:**
- Re-run the test suite. Pass count must equal baseline pass count. Any new failure indicates the type change broke an unintended consumer.
- Construct `MissionSetup(map_params={})` in a one-line REPL check: should still type-check (TypedDict with `total=False` accepts empty dict).
- Construct `MissionSetup(map_params={"seed": 42})`: should also accept.

**Pass condition:** test suite is at parity with baseline; both empty and seeded `map_params` constructions accept.

### Checkpoint C — Producer: mission generator emits unique seeds

**Purpose:** Mission generator now produces non-empty `map_params` with a unique seed. Verify the seed is actually unique across missions, that it's reproducible from the mission generator's RNG seed (so debug runs replay), and that nothing downstream choked on the new content.

**Baseline measurement:**
- Add a one-shot logging hook (or use an existing log line in `mission_generator.py`) that records `MissionSetup.map_params` for every mission generated. Run a 30-mission test (mix of archetypes). Save log: every entry should show `map_params={}`.

**Change:**
- Modify `mission_generator.py` line ~621 to set `map_params={"seed": self._rng.randint(0, 2**31 - 1)}`.
- Add the `# See also: pipe_transport.py` comment.

**After-state measurement:**
- Re-run the 30-mission test. Save log: every entry should now show `map_params={"seed": <int>}` with a distinct integer per mission.
- Assert: `len(set(seeds)) == 30`. (Trivially true unless the RNG is broken; logging it explicitly prevents silent regressions.)
- Verify reproducibility: re-run the same test with the same mission generator seed. The 30 emitted map seeds should match the previous run exactly.

**Pass condition:** all 30 missions emit distinct seeds; rerun with same generator seed produces identical sequence.

**Important:** `pipe_transport.py` is **not yet** changed. The map generator is still using `seed=current_tick`. Maps will still all be the same — this checkpoint verifies producer output only, not end-to-end variety.

### Checkpoint D — Consumer: pipe transport reads from `map_params`

**Purpose:** Wire the consumer end. After this checkpoint, missions actually produce varied maps — this is the user-visible win.

**Baseline measurement:**
- Re-run `tests.diag_map_variety` (the harness from Checkpoint A, now with Checkpoint C's producer change live). It will generate missions with unique seeds in `map_params`, but `pipe_transport.py` is still ignoring them and using `current_tick`. Result: still 1 unique layout per archetype (same as Checkpoint A baseline). Save: `tuning_output/stage11b/post_c_pre_d_variety.txt`.

**Change:**
- Modify `pipe_transport.py` line ~375: `seed=setup.map_params.get("seed", current_tick)`.
- Add the seed-source debug log line.
- Add the `# See also: mission_generator.py` comment with the fallback explanation.

**After-state measurement:**
- Re-run `tests.diag_map_variety`, N=30 per archetype with `--random` flag.
- Save: `tuning_output/stage11b/post_d_variety.txt`.
- Verify three properties:
  1. **Distinct seeds produce distinct maps.** Confirmed by Checkpoint C (every mission has a unique seed in `map_params`).
  2. **Same seed produces the same map.** Re-run the diag harness twice with a fixed `--seed` value and confirm layout selection is identical across runs.
  3. **Layout selection is no longer pinned to one layout per archetype.** Any archetype must hit ≥ 2 unique layouts over 30 random-seed missions. (Counterinsurgency is exempt if its compatible pool is ≤ 2 and fairness rejection pins it — that's a downstream issue, not a wiring issue.)

**Pass condition:** All three properties hold. Zero `current_tick_fallback` log lines for post-Checkpoint-C missions.

> **Note (2026-04-29):** The original pass condition required layout diversity ratio ≥ 0.8 per archetype. During implementation, fairness-rejection instrumentation revealed that **every (layout, archetype) pair fails the fairness evaluator 100% of the time** — the evaluator never finds an acceptable layout, and the map generator always falls back to "best of N retries." Layout selection variety comes from `rng.choice(compatible)` within the retry loop, biased by which layout scores least-bad. This is a layout authoring + FairnessTargetProfile calibration gap, not a seed-wiring gap. The 0.8 threshold was based on an assumption of uniform random selection that doesn't hold under fairness retry tiebreaking. The fairness reconciliation work is tracked separately in `stage_11e_fairness_reconciliation_spec.md`.

### Checkpoint E — Persistence: seed survives save/load

**Purpose:** Confirm Stage 8's mid-mission persistence machinery already carries `MissionSetup.map_params` correctly. This is verification only — no new persistence code expected. If this fails, file an escalation rather than fixing here (would mean Stage 8 has an unrelated bug).

**Baseline measurement:**
- Identify Stage 8's save serializer for mid-mission state (likely in `tactical_engine.py` or a `persistence.py`). Read it. Confirm it serializes `MissionSetup` whole (i.e., includes `map_params`).
- Static check: grep the save loader path. Confirm it reconstructs `MissionSetup` from the saved blob without dropping fields.

**Change:** None expected. If the static check shows `map_params` is not serialized, **stop and escalate** — that's a Stage 8 bug, not Stage 11b's to fix.

**After-state measurement:**
- Functional test: generate a mission, write the save, kill the process, reload, read `setup.map_params["seed"]`. Should equal the seed produced at generation time.
- Functional test: regenerate the map from the loaded seed. Should produce byte-identical (or layout-identical, depending on how the test scopes equivalence) `MapGenerationResult` to the first run.

**Pass condition:** loaded seed equals generated seed; map regenerates identically.

### Checkpoint F — End-to-end stage close: sign-off measurement

**Purpose:** A single-shot run that demonstrates the stage's full behavior change in one place, useful as evidence for closing the spec and as a regression baseline for future work.

**Measurement:**
- Generate 100 missions across all archetypes. Log: per-archetype layout histogram, average generation time per mission.
- Confirm every archetype hits ≥ 2 unique layouts (counterinsurgency exempt per Checkpoint D note).
- Compare average generation time. Expected: unchanged — fairness retries with random seeds are the existing behavior, not a new cost. Any > 10% time regression is a flag for investigation.

**Pass condition:** every archetype (except counterinsurgency if pool ≤ 2) hits ≥ 2 unique layouts over 100 missions; generation time within 10% of baseline. Save the report as `tuning_output/stage11b/stage_close_report.txt`.

## Performance Notes

This spec adds **zero per-frame cost on the Godot side**. Map generation runs once per mission start, on the simulation side, in a separate Python process. The Godot frame budget (16.7 ms at 60 fps target, per `docs/bible_history/bible_2_00_combat.md:313`) is unaffected.

The simulation-side cost of map generation already exists today. With the seed varying per mission, the fairness evaluator may retry slightly more often (varied layouts and gradients hit different fairness profiles), but the bible's design assumes this: *"Map seeds are tiny (~400–500 bytes) and layout instantiation is fast, so regenerating a few times is cheap"* (`docs/bible_history/bible_2_00_world.md:196`). Checkpoint F watches generation time to confirm.

If Checkpoint F shows a > 10% regression in generation time, the likely cause is fairness retries spiking on certain archetypes due to less-tested layout/sim-state combinations now becoming reachable. The fix in that case is to widen the per-archetype `FairnessTargetProfile` tolerances — but that's a Stage 7 escalation, not a Stage 11b change. Per CLAUDE.md, fairness invariant tolerances may not be widened without approval.

## Forward References

- **Pre-mission map preview UI** (future spec, deferred): will consume `MissionSetup.map_params["seed"]` to render a preview of the same map the mission will deliver. Per the design discussion that produced this spec, the preview should display **archetype-dependent spawn-location indicators** (chokepoints, staging zones, vantage points) rather than actual unit positions — the player learns the strategic shape of the map without learning enemy unit composition or precise placement, preserving the fog-of-war information asymmetry that Stage 11c lands.
- **Library hint system** (bible §"What Makes Each Mission Unique" item 3): the bible promises *"dozens of per-archetype flavor modifiers from a large AI-generated pool [that] bias layout selection and add gradient-level detail."* No `library_hints.py` exists. This is a future content-pipeline spec — it would live alongside or after the AI library builder runs are extended to produce hint packets. Not blocking variety; the four other variety axes (layout, jitter, canvas, sim-flavoring) produce sufficient unique-feeling maps at current layout count.

## Out of Scope (reaffirmed)

The following are explicitly NOT addressed in this spec, even where adjacent:

- **Layer visuals, fog of war, layer preference indicator** — `stage_11c_layer_visuals_and_fog_spec.md`.
- **Mission objectives rendering, mission markers, command location indicators, enemy clickability, minimap viewport box** — `stage_11d_mid_mission_hud_spec.md`.
- **Library hint system** — separate future content spec (see Forward References).
- **Pre-mission map preview UI** — separate future spec, blocked on this one.
- **Fairness evaluator changes** — none required. Existing fairness logic works correctly with varied seeds; that's the entire reason this spec is small.
- **Save migration for old saves** — handled by the `current_tick` fallback in `pipe_transport.py` (see D3); old saves keep their pre-spec behavior.
- **Save schema changes** — none expected. `MissionSetup` is already part of mid-mission persistence per Stage 8. Checkpoint E verifies this without changing it.
- **Godot-side changes** — none. This is sim-side wiring only.

## File Map (summary)

**Modify:**
- `simulation/mission_contracts.py` — add `MapParams` TypedDict, change `MissionSetup.map_params` type.
- `simulation/mission_generator.py` (~line 621) — emit `{"seed": rng.randint(...)}`.
- `simulation/pipe_transport.py` (~line 375) — read `setup.map_params.get("seed", current_tick)`, log seed source.
- `docs/architecture.md` — document `MapParams` schema.

**Create:**
- `tests/diag_map_variety.py` — variety self-test harness.
- `tuning_output/stage11b/` (gitignored) — checkpoint output directory.

**Bible:** no changes required. Both the seed semantics (`docs/bible_history/bible_2_00_world.md:178`, `:196`) and the perf budget framing (`docs/bible_history/bible_2_00_combat.md:313`) are already documented.

**Estimated size:** ~30 lines of contract code + ~15 lines per producer/consumer site + ~80 lines of diag harness + architecture.md section. Total active code change is small; the spec is long because the rationale and checkpoint pattern matter more than the diff.

