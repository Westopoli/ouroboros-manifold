# Apex E2E Ship Test Spec

> Authoritative spec for the end-to-end ship-readiness test. The eventual Steam submission is the long-term ship goal — no near-term deadline; this test exists so that whenever the build *is* ready, there's a single integration test that gates the call.

> **Framing note (2026-06-02):** the original Phase 1 master plan was retired. The substrate (one E2E test that exercises the full user journey on a fresh checkout) is still the right shape. Per-system tests cover their individual mechanics; this is the integration guarantee. "Friends-ZIP" framing below was the original delivery mode — the same test substrate covers a Steam build too.

## Purpose

One test that exercises the full user journey end-to-end. If this passes on a fresh checkout, the build is ship-ready. If it regresses, ship is blocked. Per-system tests cover individual mechanics; this is the integration guarantee.

## Test files

- **Python sim side:** `simulation/test_phase1_apex_ship.py`
- **Godot side:** `tests/test_phase1_apex_ship.gd` — runs headless via `scripts/run_godot_tests.sh`

## Runner

```
scripts/run_godot_tests.sh tests/test_phase1_apex_ship.gd
python3 simulation/test_phase1_apex_ship.py
```

Each test returns exit code 0 on pass, non-zero on fail. Apex test asserts both halves pass within a 5-minute budget on a fresh checkout.

## Fixture preconditions

- Fresh `saves/` directory (no autosave slot).
- Deterministic RNG seed (config TBD; reuse `DUMP_SEED=3` convention from `test_j_duration.py`).
- No leftover `~/.local/share/godot/...` or `~/Library/Application Support/Godot/...` state.
- Sim entrypoint = `simulation/pipe_transport.py` (no `--load` flag for first run).
- Godot exec = `godot --headless --path . --script res://tests/test_phase1_apex_ship.gd --quit-after 300`.

## 10-step scenario walk

### Step 1 — Cold boot
- **Action:** Launch Godot. Main menu loads.
- **Assertions:**
  - Main menu scene resolves (no crash).
  - CONTINUE button is hidden or disabled (no autosave slot exists).
  - NEW GAME button is visible + enabled.
- **Fail-look-fors:** crash on boot, CONTINUE button visible without autosave, sim subprocess started before NEW GAME pressed.

### Step 2 — Onboarding picker
- **Action:** Click NEW GAME. Onboarding scene loads. Pick difficulty + archetype. Confirm.
- **Assertions:**
  - `scenes/onboarding/onboarding.gd` instantiates.
  - On confirm, `saves/<slot>/onboarding.json` written with chosen difficulty + archetype.
  - Schema matches `simulation/onboarding_store.py` shape.
- **Fail-look-fors:** missing keys in onboarding.json, default difficulty written when player picked something else, scene fails to transition.

### Step 3 — Tutorial fires
- **Action:** First mission loads. Tutorial overlay fires.
- **Assertions:**
  - Tutorial beats fire in sequence: movement, selection, control groups, mission objective intro, chronicle voice intro.
  - Each beat sourced from `simulation/library/tutorial/` library entry (cache hit on second read).
  - Tutorial overlay dismissible after final beat.
- **Fail-look-fors:** beats fire out of order, content hardcoded instead of library-sourced, dismiss button non-functional, tutorial fires on second-mission entry.

### Step 4 — World view + first time-jump autosave
- **Action:** Sim boots, first time-jump fires.
- **Assertions:**
  - `saves/<slot>/sim.json` written post-time-jump.
  - Top-level keys present: `sim_state`, `chapter_number`, `year`, `rng_state`, `last_time_jump_messages`.
  - `sim_state` payload matches `serialize_world()` schema v3 (per `simulation/save/world_serializer.py`).
  - Chronicle entries, factions, stances, naming_system all serialized.
- **Fail-look-fors:** schema_version drift, missing `stances` key, RNG state un-restorable, `last_time_jump_messages` empty.

### Step 5 — Mission briefing (B2)
- **Action:** Click region → mission entry.
- **Assertions:**
  - `scenes/mission_briefing/mission_briefing.gd` opens before tactical scene loads.
  - Briefing text names objective in plain language (matches archetype string from `UIDataBus.get_mission_briefing()`).
  - All 6 archetype objective strings render without "[OBJECTIVE_TYPE_UNKNOWN]" or empty fallback.
- **Fail-look-fors:** briefing skipped, placeholder text rendered, archetype string mismatch with HUD.

### Step 6 — Tactical scene populated
- **Action:** Dismiss briefing. Tactical scene loads.
- **Assertions:**
  - Mission marker beacons populated under `_mission_markers` Node3D (per `scenes/tactical/tactical.gd:68-70`).
  - HUD objectives list populated with same archetype objective from Step 5.
  - HUD progress bars present and at 0%.
- **Fail-look-fors:** empty markers, objective text mismatch, HUD list shows wrong count.

### Step 7 — Mid-mission save (B6)
- **Action:** Advance ~30 sim seconds. Open pause menu. Click SAVE & QUIT.
- **Assertions:**
  - Pause menu scene opens (B6 surface).
  - `saves/<slot>/tactical.json` written via `write_tactical_state()`.
  - `TacticalEngine.export_full_state()` payload includes: tick, rng_state, store, objectives, command_queue, reinforcement_structures.
  - Quit returns to main menu cleanly.
- **Fail-look-fors:** pause menu missing, tactical.json absent or short, RNG state not encoded, sim subprocess still running after quit.

### Step 8 — Resume
- **Action:** From main menu, click CONTINUE.
- **Assertions:**
  - Sim relaunched with `--load <slot>`.
  - `_load_sim_env()` restores world, factions, stances, ledger, naming, gen_state, pending_queue, trigger_state, noise_offsets.
  - Persisted time-jump messages replayed verbatim after `ready_for_time_jump` signal.
  - Tactical scene re-enters at saved tick (engine tick == saved tick).
  - Unit positions, HP, command queue, objective progress all identical to pre-save snapshot.
- **Fail-look-fors:** state divergence (mismatched tick, lost units, wrong objective progress), narration paints different than pre-save, RNG drift.

### Step 9 — Mission resolution
- **Action:** Drive mission to win (or scripted loss). Debrief screen loads.
- **Assertions:**
  - Win/lose detected by tactical engine, debrief scene loads.
  - `scenes/debrief/debrief.gd` populated from `simulation/debrief_data.py`.
  - Post-debrief autosave fires (next time-jump triggers autosave).
  - Control returns to world view.
- **Fail-look-fors:** debrief blank, autosave missed post-debrief, world view fails to resume.

### Step 10 — Clean exit
- **Action:** Quit from main menu.
- **Assertions:**
  - Godot process exits with code 0.
  - Sim subprocess terminated (no `pipe_transport.py` orphan).
  - No `Application crashed` dialog.
- **Fail-look-fors:** hung subprocess (Ctrl-C hang exception is documented — Stage 10 dead code), Godot exits non-zero, lockfile leftover.

## Reusable harness

- `simulation/setup_sim_env()` — sim env builder.
- `simulation/sim_tuner.py` `run_scenario()` — drives sim ticks deterministically.
- `simulation/test_pipe_load_resume.py` — load-resume integration template.
- `tests/test_world_view_*.gd` — Godot scene-test pattern (instantiate, signal record, assert, `get_tree().quit()`).

## Schema drift policy

Any change to `sim.json` or `tactical.json` shape goes through `docs/architecture.md` first (per CLAUDE.md tick-delta-shape rule, generalized).

## Out of scope for apex test

- Balance tuning (covered by `test_j_duration.py` + sim_tuner).
- Visual polish (Westley confirms manually).
- Steam-side launch tasks (S#1-S#7 in priority queue).
- Multi-seed determinism stress (one seed only; multi-seed is POST-BETA).
