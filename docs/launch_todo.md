# Launch To-Do

Tracked bugs and tasks that must be resolved before launch. Mark items `[x]` when complete.

## Bugs

- [ ] **Fix unit rotation not working** — facing.py + renderer integration exists (Stage 12.5) but units aren't visually rotating. Investigate facing_rad pipeline.
- [ ] **Fix impact/fire visuals hitting single point in squad** — when a unit has multiple squad members (squad_count > 1), projectiles and impact effects only target/originate from the root position, not individual squad meshes.
- [ ] **Fix unit sizing** — unit visual scales feel off.
- [ ] **Fix main camera** — pan/zoom feels off, needs tuning.
- [ ] **Fix unit balance** — combat balance pass needed.
- [ ] **Tune force allocation scale** — missions consistently produce only 8-10 units; feels too small. `MILITARY_TO_POWER_SCALE` and `BUDGET_TO_POWER_SCALE` in `config.py` need a balance pass. Currently set to 4x temp values for testing (revert markers in code).
- [x] **Layer visual system** — Stage 11c landed: layer focus visuals (active-layer emphasis, HUD readout) + fog of war (visibility predicate in renderer, minimap, selection). *(2026-05-03)*
- [ ] **Fix control groups unit swapping** — control group assignments are broken; units swap between groups unexpectedly.
- [x] **Fix mission briefing empty** — wired mission generator into game loop; briefing now shows real archetype, region, enemy, force composition, objectives, and commander lineage. *(2026-04-24)*

## Features

- [ ] **Remove static flyby ship animations** — current ambient flyby ships are placeholder. Remove now, replace with something better later.
- [ ] **Create production building assets** — reinforcement structures need real art.
- [ ] **Auto-assign unit type hotkeys** — 1 = all army, 2 = all strike, 3 = all line, 4 = all siege. Automatic, not manual.
- [ ] **Shift-click/drag to add to selection** — hold SHIFT and click or drag a box to add more units to the current selection instead of replacing it.
- [x] **Allow enemy units to be clickable** — clicking enemy units should select/inspect them (show HP, type, etc). *(Stage 11d sub-goal 4)*
- [ ] **Double-click to select all of that unit type on screen** — double-clicking a unit selects all visible units of the same type.
- [ ] **Add new version of map view** — redesign the Settled Reach world/map view.
- [ ] **Improve chronicle output** — current chronicle entries are too wordy. Tighten prose generation.
- [ ] **Regenerate library names** — current AI-generated names need a quality pass with better prompting/curation.
- [x] **Minimap viewport box** — draw a rectangle on the minimap showing the camera's current viewport bounds (like StarCraft 2). *(Stage 11d sub-goal 5)*
- [ ] **Fog of war terrain darkening** — StarCraft 2-style ground darkening outside player vision range. Currently fog hides enemy units correctly but gives no spatial feedback about where the player can/can't see. Render a vision-radius overlay (transparent within sensor range, darkened outside).
- [ ] **Command queuing** — allow shift-queuing multiple commands so the player can set waypoints/orders and forget. Units execute queued commands in sequence.
- [ ] **Color legend for world view** — show which color maps to which faction on the world view.
- [ ] **Pan/drag invert option in settings** — settings UI toggle for inverting pan/drag direction.
- [ ] **"Center view" / "zoom out" button on world view** — quick navigation control to reset camera.
- [x] **Command location indicators** — transient command decals via `command_indicator.gd`. *(Stage 11d)*
- [ ] **In-game tutorial** — effective explanation of the game and what to do, written in the same artistic style as the chronicle (lore-flavored, not generic UI tooltips).
- [ ] **Skip button for chronicle entries** — add skip controls for the chronicle scroll: a per-entry skip (advance past the current entry) and a skip-all (jump past the entire chronicle sequence).

## Stage 11 Progress

### Done
- [x] **11 A/B** — Keyframe selector, transport plumbing, UIDataBus signals
- [x] **11 C3** — Camera `move_to_position()` for sequencer choreography
- [x] **11 D** — Chronicle scroll panel (word-by-word fade-in, click-to-expand, pause/resume)
- [x] **11 E** — Time jump sequencer (6-phase orchestrator)
- [x] **11b** — Per-mission map seed wiring
- [x] **11c** — Layer focus visuals + fog of war rendering
- [x] **11d** — Objectives, minimap markers, command indicators, enemy clickability, minimap viewport box *(signed off 2026-05-03)*
- [x] **11e** — Fairness pivot: simple random picker + structured JSONL logging (fairness redesign deferred to 11f)

### Remaining (carried to launch_todo features/bugs)
- [x] **Stage 11 signed off** — core loop works. Gaps noted below carried forward.
- [ ] **Smooth territory transitions** — needs shader-uniform animation approach (see spec known limitations)
- [ ] **Border vs trade connection visual distinction** — solid vs dashed lines
- [ ] **Pause menu** — in-mission exit path untested
- [ ] **Performance budget** — no formal profiler measurement yet
- [ ] **11f** — Fairness redesign (blocked on playtest data corpus)

## Completed

- [x] **Fix stuck firing animation** — impact effects triggered by floating point HP noise on snapshot boundaries. Fixed with 0.5 damage threshold in `impact_feedback_manager.gd`. *(2026-04-22)*
- [x] **Fix target loyalty** — units were swapping targets on cohort re-acquisition turns. Fixed by removing cohort override in `damage.py` `update_targeting`. *(2026-04-22)*
