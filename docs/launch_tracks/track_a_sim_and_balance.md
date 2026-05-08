# Track A — Sim & Headless Balance Work

**Owner:** one Claude Code session.
**Branch:** `claude/survey-game-implementation-VE8jl` (or split per session, by ai_status.md claim).
**Reads first (in order):** `CLAUDE.md`, this file, `docs/bible/game_bible.md` hub, `docs/bible/bible_combat.md` (engagement targets and stat philosophy), `docs/ai_status.md` (claim before starting).

This track is for work that lives entirely in `simulation/` and is verifiable headlessly via `python3 simulation/test_*.py` or `python3 simulation/sim_tuner.py`. No Godot launching needed.

## Goal

Resolve the open simulation-side launch_todo items that gate the friends-ZIP feeling right. The biggest one is the force-allocation balance pass — missions are currently producing 8–10 units when the design intent is larger, and the temporary 4× debug values used during Stage 11d testing have been reverted, leaving the sim under-scaled.

## Scope (in)

- `simulation/config.py` — balance tuning parameters.
- `simulation/sim_tuner.py` — scenario sweeps and graph generation. Already exists.
- `simulation/test_*.py` — diagnostic harnesses. Two new ones from the Stage 13 starter commit: `test_facing_convergence.py` and `test_facing_snapshot_propagation.py`. Both pass — use as templates if more harnesses are needed.
- `simulation/force_allocator.py`, `simulation/force_composition.py`, `simulation/power_rating.py` — read-only references for understanding allocation. Edit only if the audit demands it.
- `build/pyinstaller_spec.py` — iterate `hiddenimports` if Track C reports missing modules during PyInstaller checkpoint A.

## Scope (out — do NOT touch)

| Off-limits | Why |
|---|---|
| `simulation/socket_server.py` | Protected. Explicit Westley approval required. |
| `simulation/world_view/` | C2 (Stage 11g) owns. Checkpoints D, E, etc. |
| `simulation/chronicle_assembler.py` | C2 will edit at Stage 11g Checkpoint N. Coordinate via ai_status.md if the chronicle-output session is also active. |
| `simulation/tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py` | Protected engine files per `CLAUDE.md`. Approval required. |
| `simulation/tactical_engine.py`, `facing.py`, `damage.py` | Treat as protected. Approval required. |
| `simulation/pipe_transport.py` | Track C may also touch this for `time_jump_emitter` wiring. Coordinate via ai_status.md before editing. |
| Anything outside `simulation/` and `build/` | Other tracks' territory. |

## Items in priority order

### A1. Force allocation scale tuning (priority)

**Symptom (per `docs/launch_todo.md`):** missions consistently produce only 8–10 units; feels too small.

**Background:** `simulation/config.py:705-706` currently has:
```python
BUDGET_TO_POWER_SCALE  = 150.0
MILITARY_TO_POWER_SCALE = 1000.0
```
During Stage 11d testing these were temporarily set to 4× values; that test was reverted. Bible engagement targets in `bible_combat.md`: minimum 45 s brawl, ~2 min tactical, 50v50 mirror 150–200 s.

**Deliverable:**
1. Run a controlled `sim_tuner.py` sweep over `BUDGET_TO_POWER_SCALE` and `MILITARY_TO_POWER_SCALE`. Record:
   - Resulting unit counts (player + enemy) per archetype
   - 50v50 mirror engagement durations
   - Outcome-band distribution
2. Pick values that hit the bible targets without breaking force-composition invariants.
3. Update `config.py` with chosen values + a one-line comment of intent (no multi-paragraph rationale).
4. Update `docs/launch_todo.md` to mark "Tune force allocation scale" complete with date.

**Test strategy:**
- All existing `simulation/test_*.py` stay green.
- 50v50 mirror invariant: median engagement duration in [150, 200] s with current `bible_combat.md` HP and damage values.
- Force-composition tests (`force_allocator` direct invocation) still produce expected category mixes per archetype.

**STOP-and-escalate triggers:**
- Bible targets unattainable with any reasonable scale value (suggests the bug is in `force_allocator.py` or `power_rating.py`, not the scale).
- 50v50 invariant fails after picking a value (do **not** widen the invariant — escalate).

### A2. Per-unit balance follow-on (only if A1 surfaces it)

If A1's mirror sweep shows specific unit types dominating or evaporating, do a targeted stat sweep for the offender(s) via `sim_tuner`. **Do not** touch HP/damage values without confirming the issue with Westley first. Per-unit stat values are config not engine — change is allowed, but only after diagnosis. One unit type at a time.

### A3. Stage 13 PyInstaller hidden_imports follow-on (reactive)

If Track C reports missing imports while running PyInstaller (Stage 13 Checkpoint A iteration), append to the `hiddenimports` list in `build/pyinstaller_spec.py`. This is a reactive item — wait for Track C to ping in `ai_status.md`.

### A4. Library name regen — DEFER

Out of friends-ZIP scope unless playtester feedback specifically calls out bad names. Don't pull this work into the launch push.

### A5. Chronicle output polish — CHECK ai_status.md

There is (or was) an Opus session claiming this work. If still active, leave alone. If stale (no commits in 7+ days), check with Westley before picking up. Touches `simulation/chronicle_assembler.py`, `simulation/chronicle_distiller.py`, `simulation/events.py`, `simulation/library/chronicle/fragments.json`.

## Workflow

1. `git pull` before starting any item.
2. Claim in `docs/ai_status.md` before any code edit. Use existing format.
3. Form hypothesis → measure → change → re-measure (per `CLAUDE.md` debugging discipline).
4. Run all relevant `simulation/test_*.py` after each change.
5. Commit with a clear message. Push.
6. Update `docs/launch_todo.md` to mark items closed with date.
7. After each item lands, stop and report. Do not chain into the next item without Westley's go.

## Guardrails

- **Never widen an invariant or loosen a tolerance** to make a balance value pass. Either find a value that works or escalate.
- **One change at a time.** If A1 needs both scale tuning and force-composition adjustment, do the scale first, confirm, then tackle composition separately.
- **No shotgun debugging.** Form a hypothesis, add logging or instrumentation that confirms or refutes it, then fix.
- **No blind git reverts.** `git checkout/restore/stash` requires confirming with Westley that working tree is clean first.
- **No bible edits** without Westley's sign-off. If a tuning result implies a bible change (e.g., engagement target needs to widen), escalate the design question.

## Definition of done

- A1 complete: force allocation scale values landed, 50v50 mirror invariant passes, launch_todo item marked done.
- All `simulation/test_*.py` green at end of each commit.
- ai_status.md reflects current claim state.
