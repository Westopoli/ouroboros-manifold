# Stage 5 Checkpoint K — Continuation Notes

Paused 2026-04-08 to fix upstream bugs. Pick up from here when returning to Checkpoint K.

## Checkpoints A-J: Complete

All approved by Westley across multiple sessions. Key fixes applied during I/J:

- Fragment article cleanup (~116 edits in fragments.json): identity slots own their articles, fragments never prepend articles
- Faction display names from naming system pools (not hardcoded theme names)
- Breakaway faction naming: parent_faction_id passed through assign_faction_leader for pool inheritance
- Chronicle assembler: field_delta_summary rewritten with dynamic clause builder, duration_prose lowercase, category cap of 2, chain cluster merging
- Library validator: ARTICLE_BEFORE_SLOT_RE structural check added
- Schism cultural drift: derive_schism_subset wired into tick.py revolt path
- tick.py (authorized changes): breakaway leader assignment, faction naming, schism drift

## Checkpoint K Status: In Progress

### What's Done

**Invariant functions K1-K12** — all written and registered in `ALL_INVARIANTS` and `GROUP_MAP["K"]` in `invariants.py`:
- K1 `chronicle_entry_count`: 5-10 entries per jump
- K2 `chronicle_lineage_present`: lineage in every jump
- K3 `chronicle_consequence_first`: consequence first when present
- K4 `chronicle_word_limits`: base<90, expanded<140
- K5 `chronicle_slots_resolved`: no unresolved {slot} patterns in expanded_text
- K6 `fragment_library_no_dupes`: loads fragments.json, runs validate_dedup
- K7 `every_faction_has_leader`: factions with regions have active supreme_commander
- K8 `lineage_grows_during_jumps`: >= 1 new member for jumps >50 ticks
- K9 `dead_names_become_available`: dead names available after cooldown
- K10 `no_duplicate_active_names`: unique names per faction among active characters
- K11 `schism_subsets_differ`: breakaway subsets differ from parent by exactly 1 category
- K12 `stage5_regression`: runs all A-J critical invariants

**Scenarios** added to `sim_tuner.py`:
- `11_chronicle_4faction`: full_game_50, 2000 ticks, chronicle_reviews at [500, 1000, 1500, 2000], 100-tick jump duration
- `12_naming_stress`: full_game_50, 3000 ticks, coherence_ledger + real_naming_pools (no chronicle reviews)

Note: the spec says scenarios 09, 10, 11 but implementation used 11 and 12 because 09 and 10 were already taken. The `11_chronicle_4faction` scenario is functionally equivalent to the spec's "10_chronicle_4faction".

**sim_validator.py** extended:
- TrajectoryLog has `naming_system`, `time_jump_results`, `coherence_ledger` fields
- `_load_real_naming_pools(ns)`: loads from library/naming/names.json and prompts/variable_subsets.json
- Coherence ledger setup: creates leaders for initial factions, assigns faction display names
- Time jump execution block: finds player lineage, iterates chronicle_reviews, calls run_time_jump(), stores results

**Fixes applied during K work:**

1. **Succession on natural death** (`coherence_ledger.py`): `kill_character` now accepts optional `world` and `rng` params. When a supreme_commander or regional_commander dies and their faction still has regions, `_succeed()` creates a replacement via `create_character`. `process_natural_deaths` passes `world` through. This implements the bible's "Succession" spec.

2. **Lineage_quiet cluster region_id** (`chronicle_distiller.py`): When building a lineage_quiet cluster with no events, the region_id fallback chain is: active member with region -> lineage history (last known region) -> last_mission_region -> any inhabited region in world. Prevents None region_id that caused slot resolution crashes.

3. **Post-jump snapshots** (`time_jump.py`): Each `run_time_jump()` return dict now includes `"post_jump_snapshot"` with faction region counts and region ownership as they exist after the time jump's tick loop, lineage generation, and natural death processing. K-group invariants use these instead of main-loop snapshots, which diverge because time jumps mutate the world.

4. **K7 temporal checking** (`invariants.py`): K7 checks leader existence at each time jump's `end_tick` using born_tick/death_tick comparison (not status field, which reflects final state). Skips factions created after the jump's timeline.

5. **K9 reuse vs active** (`invariants.py`): K9 skips names currently held by an active character — legitimate reuse after cooldown is a pass, not a fail. Uses last time jump's end_tick as final_tick instead of log.total_ticks.

### Last Test Run (seed 1)

```
 + K1_entry_count
 + K2_lineage_present
 + K3_consequence_first
 + K4_word_limits
 + K5_slots_resolved
 + K6_no_fragment_dupes
 + K7_faction_leaders
 + K8_lineage_growth
 X K9_name_reuse [CRITICAL]       — 22/279 dead names still unavailable after cooldown
 + K10_unique_names
 X K11_schism_drift [WARNING]     — 216 breakaway(s) with invalid subset drift
 X K12_stage5_regression [CRITICAL] — E2, J15 fail
```

### Remaining Failures to Investigate

**K9 (name reuse)** — 18 names (after the active-name fix) still show as unavailable despite cooldown expiring. Initial diagnosis started but was interrupted. The 11 overlap names (in both `_in_use` and `_cooldowns`) are correctly handled by the active-name skip. The remaining ~18 are historical characters whose names are NOT in use by any active character but `is_available()` still returns False. Suspect: the name is in `_in_use` from a `get_name` call that created a character who was later killed, but `release_name` wasn't called (or was called with a different string). Start by checking whether those 18 names are in `_in_use` and if so, which faction_id they map to and whether any character with that name is actually active.

**K11 (schism drift)** — 216 breakaways with invalid subset drift. Diagnosis was just starting when paused. The issue: `derive_schism_subset` in tick.py only runs when `coherence_ledger is not None` AND `parent_fid` exists. It requires the parent faction to have a variable subset registered in the naming system. Likely causes to investigate:
- Parent factions (original 4) may not have subsets loaded — check whether `_load_real_naming_pools` in sim_validator.py loads variable_subsets.json for the faction IDs used in the scenario
- Breakaway-of-breakaway factions: a breakaway's child won't find a parent subset if the intermediate breakaway never got one
- The invariant checks ALL breakaways against non-breakaway parents. But some breakaways are children of other breakaways, so the parent-finding logic (iterate non-breakaway factions looking for 1-category diff) fails

**K12 (stage5 regression)** — E2 (conquest_ownership) and J15 fail. This is expected: time jumps mutate the world in place, corrupting the relationship between main-loop snapshots and actual world state. The A-J invariants were designed for main-loop-only runs. Two options:
1. Run K12 against a separate trajectory that doesn't include time jumps (use a scenario without chronicle_reviews)
2. Accept that K12 will fail on chronicle scenarios and only run it on non-chronicle scenarios

Westley should decide the approach. The E2/J15 failures are not real bugs — they're artifacts of the time jump world mutation.

### Architecture Notes for Next Session

**World mutation problem**: The sim_validator runs the main tick loop (ticks 1-2000) capturing snapshots, then runs time jumps which mutate the same world object. This means:
- Main-loop snapshots at ticks 500-2000 were captured during the main loop
- Time jumps starting at ticks 500, 1000, 1500, 2000 re-run those ticks on the already-evolved world
- Post-jump snapshots reflect the world after BOTH the main loop and time jump mutations

This is fine for K-group invariants (they use post_jump_snapshot), but it means A-J invariants checking the final world state will see post-time-jump corruption. K12 needs to account for this.

**Ledger is cumulative**: The coherence ledger accumulates state across all time jumps. K7 handles this by checking born_tick/death_tick against each jump's end_tick rather than checking status=="active". Any new K invariant that checks ledger state at intermediate time points needs the same temporal approach.

### Files Modified During Checkpoint K

- `invariants.py` — K1-K12 functions + registration in ALL_INVARIANTS and GROUP_MAP["K"]
- `sim_validator.py` — TrajectoryLog extensions, time jump wiring, real naming pool loading
- `sim_tuner.py` — scenarios 11_chronicle_4faction and 12_naming_stress
- `time_jump.py` — post_jump_snapshot capture, world param to process_natural_deaths
- `coherence_ledger.py` — succession in kill_character/_succeed, world param on process_natural_deaths
- `chronicle_distiller.py` — lineage_quiet region_id fallback chain
- `chronicle_assembler.py` — no pending changes (reverted the None-skipping)

### Command to Re-run

```bash
cd simulation
python3 test_validate.py 11_chronicle_4faction --groups=K
```

Seed is controlled by the scenario definition (seed=1). For multi-seed testing, the scenario would need to be run 3 times with seed overrides — this isn't wired up yet. The spec says seeds 1-3.
