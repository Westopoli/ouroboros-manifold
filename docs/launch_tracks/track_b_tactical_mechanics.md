# Track B — Tactical Mechanics & Combat Polish

**Owner:** one Claude Code session.
**Branch:** `claude/survey-game-implementation-VE8jl` (or split per session, by ai_status.md claim).
**Reads first (in order):** `CLAUDE.md`, this file, `docs/bible/bible_combat.md` (combat visuals, command vocabulary, unit behavior), `docs/ai_status.md` (claim before starting).

This track is the tactical scene polish layer: in-mission rendering, input, selection, command, and unit-feel work. Westley is in the loop for visual confirmation on most items — code the change, ask him to launch the game, mark "ready for confirm" in `ai_status.md` until he confirms.

## Goal

Drain the open tactical-side launch_todo items so the friends-ZIP playthrough feels right at the unit level: rotation visible, impacts where they should be, selection and control groups behaving correctly, hotkeys ergonomic.

## Scope (in)

- `scenes/tactical/**` — input router, unit renderer, HUD, attack/impact/destruction visuals.
- `scripts/tactical/**` — visibility, etc.
- `autoload/tactical_bridge.gd` — only if a new field needs to surface at the bridge layer; coordinate via ai_status.md before editing autoloads.

## Scope (out — do NOT touch)

| Off-limits | Why |
|---|---|
| `simulation/**` | Track A (or protected). Sim-side rotation pipeline is already verified clean — see `simulation/test_facing_convergence.py` and `simulation/test_facing_snapshot_propagation.py`. |
| `scenes/world/**`, `scenes/shared/world_view/**` | C2 (Stage 11g) is editing extensively. Hands off until Stage 11g lands. |
| `scenes/privacy_modal/**`, `autoload/debug_overlay.gd`, `autoload/sim_bridge.gd`, `autoload/theme_constants.gd`, `project.godot` | Track C (Stage 13 packaging). |
| `autoload/faction_palette.gd` | New, owned by C2 (Stage 11g). |
| `autoload/era_theme_resolver.gd` | Stable contract; do not edit without Westley's approval. |

## Items in priority order

### B1. Unit rotation (renderer-side) — priority

**Symptom (per `docs/launch_todo.md`):** units don't visually rotate.

**Pre-diagnosis (already done):** Track A's two harnesses prove the sim is correct end to end:
- `simulation/test_facing_convergence.py` — 4 assertions, all pass. `update_facing()` rotates toward the target bearing, respects rotation speed caps, holds steady when stationary.
- `simulation/test_facing_snapshot_propagation.py` — 9 assertions, all pass. `full_snapshot()` includes `facing_rad`, `delta()` emits it on change, `apply_delta()` round-trips it.

Run them yourself first to confirm they still pass:
```
cd simulation && python3 test_facing_convergence.py && python3 test_facing_snapshot_propagation.py
```

**Where the bug must live:** `scenes/tactical/unit_renderer.gd`, the squad mesh transform loop around lines 140–146:

```gdscript
var squad_count: int = EraThemeResolver.get_squad_count(unit_type)
...
for i in squad_count:
    batch.entries.append({"uid": uid, "squad_idx": i, "offset": offset, "vscale": vscale, "facing_offset": foff})
```

Likely failure modes:
- The per-frame transform application doesn't read `facing_rad` from the latest snapshot/delta dict.
- The mesh `Transform3D.basis` is being constructed without the rotation, or with the wrong axis.
- The `facing_offset` per squad mesh is being applied in place of (rather than added to) the unit's rotation.

**Deliverable:** rotation visible in playthrough. Westley confirms by running the game and watching units face their targets and movement direction.

**Test strategy:**
- Sim-side tests stay green.
- Westley confirms visually. Mark "ready for confirm" in ai_status.md until confirmed.
- Optional: a Godot-side test scene (`tests/test_unit_rotation_visual.tscn` or similar) that loads a fixed snapshot and screenshot-checks the unit orientation. Only worth building if the bug recurs after fix.

### B2. Squad-member impact origins

**Symptom:** projectiles and impact effects fire from / hit a single point even when a unit's `squad_count > 1`.

**Cause:** the sim has no squad concept — squads are renderer-only via `EraThemeResolver.get_squad_count`. `scenes/tactical/visuals/projectile_renderer.gd` and `scenes/tactical/visuals/impact_feedback_manager.gd` both use the logical unit position as the origin/target. They need to read the squad mesh positions instead.

**Deliverable:**
- Projectiles spawn from a randomized (or round-robin) squad mesh on the firing unit.
- Impacts spawn at a randomized squad mesh position on the target unit.
- Visual density is preserved; per-shot positions feel like multiple firing/landing points across the squad footprint.

**Test strategy:** visual confirmation. Westley confirms after fix.

### B3. Control groups swapping bug

**Symptom (per `docs/launch_todo.md`):** control group assignments are broken; units swap between groups unexpectedly.

**Likely site:** `scenes/tactical/input_router.gd` — recently touched in C1's Stage 11d work. Read the full file before editing.

**Deliverable:**
- `Ctrl+1..0` assigns selected units to a group, replacing prior membership.
- `1..0` selects the named group.
- Once a unit is in group N, it stays there until reassigned. No cross-group swapping.

**Test strategy:**
- Headless input-router test (synthesize input events, assert selection state). Worth writing — input handling is regression-prone.
- Westley spot-check.

### B4. Selection upgrades (cluster — input_router.gd)

Three small items, batch them:

- **Shift-click / shift-drag adds to selection.** Holding `Shift` while clicking or box-dragging adds to the current selection rather than replacing.
- **Double-click selects all visible of that unit type on screen.** Read camera frustum from the existing minimap viewport-box code (Stage 11d Checkpoint G) for screen visibility.
- **Auto-assigned unit-type hotkeys.** `1`/`2`/`3`/`4` automatically select all friendly units of category army/strike/line/siege respectively. Automatic, not user-configured.

**Deliverable:** all three behaviors work, no conflict with control-group `Ctrl+N` assignment. Note: this can conflict with B3 if both touch the `1..0` keybind — coordinate within the same session (do B3 first, then B4 hotkeys).

**Test strategy:** input-router tests where the value justifies. Westley spot-check.

### B5. Command queueing

**Symptom (feature, not bug):** no way to shift-queue commands.

**Deliverable:**
- Holding `Shift` while issuing a `move` or `attack-move` adds the command to the unit's queue.
- Units execute queued commands in sequence.
- A queue-state HUD indicator (small marker per queued command, optional first pass) — Westley confirms visual.

**Implementation notes:** the command queue is unit-side data. Existing `Command` and `CommandQueue` structures live in `simulation/command.py` — do **not** change those (Track A territory). Queueing is a renderer-side intent buffer that emits commands one at a time when the unit completes the current order. Wire through `input_router.gd` and a new per-uid queue dictionary in `tactical.gd` or similar.

**Test strategy:** queue-state assertions in headless. Westley confirms visual indicator.

### B6. Camera pan/zoom tuning

**Symptom:** main tactical camera pan/zoom feels off.

**Deliverable:** Westley says it feels good.

**Implementation:** pure feel. Iterate on speed/acceleration/zoom curves with Westley in the loop. No automated test possible.

### B7. Unit sizing pass

**Symptom:** unit visual scales feel off.

**Deliverable:** Westley confirms sizes look right.

**Implementation:** scales are likely in `EraThemeResolver` per-era manifest or a per-unit-type config. Investigate the scale source first; read-only audit before any change. **Do not touch the manifest schema** without Westley's approval.

### B8. Fog of war terrain darkening

**Symptom (per `docs/launch_todo.md`):** fog hides enemy units correctly but gives no spatial feedback. Need StarCraft 2-style ground darkening outside player vision.

**Implementation:** vision-radius overlay (transparent within sensor range, darkened outside). Likely a screen-space shader pass over the terrain layer, or a projector decal that follows the player force.

**Deliverable:** Westley sees clearly which areas are visible and which aren't.

## Workflow

1. `git pull` before starting any item.
2. Claim in `docs/ai_status.md` before editing.
3. **Confirm sim-side is clean before touching the renderer for B1.** Run the two facing tests.
4. Form hypothesis → instrument → measure → fix. No shotgun changes.
5. Visual items: do not mark "done" — mark "ready for confirm" in ai_status.md until Westley confirms.
6. One item at a time. After each, stop and report before picking up the next.

## Guardrails

- **Visual confirmation gate.** Anything that affects appearance, feel, or input timing must be confirmed by Westley before being marked done.
- **One fix at a time.** Multiple bugs in flight at once breaks bisection if a regression appears.
- **No protected-file edits.** Even where a tactical scene reads a sim field, the fix lives in the scene — not in the sim.
- **No blind git reverts.** Multiple sessions are likely writing files concurrently.
- **No shotgun debugging.** Form a hypothesis, add logging, ask Westley to run, then fix targeted to the confirmed cause.

## Definition of done

- B1 (rotation) and B2 (squad impact origins) both confirmed by Westley in playthrough.
- B3, B4, B5 behave correctly in playthrough; control-group and selection edge cases tested.
- B6, B7, B8 confirmed by Westley.
- `docs/launch_todo.md` updated with each completed item.
- All `simulation/test_*.py` green (this track shouldn't break sim tests, but verify after any cross-cutting change).
