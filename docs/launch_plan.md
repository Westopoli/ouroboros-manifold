# Launch Plan — Stage 13 ZIP

Coordinated multi-session push to ship the friends-ZIP build. Closes the remaining open work, drains the launch_todo, and packages everything per `docs/stage_specs/stage_13_spec.md`.

This doc is the **index**. Each session reads the per-track spec under `docs/launch_tracks/`, claims items in `docs/ai_status.md`, and works the checkpoints in order.

## Status snapshot (2026-05-08)

- **Done:** Stages 1–12.5, Stage 11b/c/d/e. Stage 11 main spec signed off (carried gaps tracked in launch_todo).
- **In flight:**
  - **Stage 11g (world view inspection)** — at Checkpoint G. Spec: `docs/stage_specs/stage_11g_world_view_inspection_spec.md`. Owner: an existing local Claude Code session ("C2"). Don't dispatch a second window onto Stage 11g.
- **Not started, ready to dispatch:**
  - **Track A** (sim & balance) — `docs/launch_tracks/track_a_sim_and_balance.md`
  - **Track B** (tactical mechanics & polish) — `docs/launch_tracks/track_b_tactical_mechanics.md`
  - **Track C** (Stage 13 packaging) — `docs/launch_tracks/track_c_stage_13_packaging.md`
- **Stage 13:** spec at `docs/stage_specs/stage_13_spec.md`, eight checkpoints A–H, no implementation yet. Build skeletons in `build/` already in tree.

## Carried-forward gaps from Stage 11 close

These are open and listed inside the track specs that pick them up:

- **Smooth territory transitions** (shader-uniform animation) — out of friends-ZIP scope; logged.
- **Border vs trade connection visual distinction** (solid vs dashed) — Track C, held until Stage 11g lands.
- **Pause menu** (Resume / Settings / Exit to Main Menu) — Track C, held until Stage 11g lands.
- **Performance budget verification** — Track C, after Stage 13 D debug overlay lands.

## Track briefs (one paragraph each)

**Track A — Sim & headless.** Owns `simulation/config.py` balance, `sim_tuner.py` sweeps, headless test harnesses, reactive Stage 13 PyInstaller hidden_imports support. Priority item is the force-allocation scale tuning (missions producing 8–10 units; bible target is 50v50 mirror @ 150–200s). Avoid `simulation/world_view/` and `simulation/chronicle_assembler.py` (C2 territory).

**Track B — Tactical mechanics & polish.** Owns `scenes/tactical/**` and `scripts/tactical/**`. Priority item is the unit-rotation renderer fix — Track A has already proven the sim is clean (`test_facing_convergence.py` and `test_facing_snapshot_propagation.py` both pass). Bug is in `unit_renderer.gd` squad mesh transforms. Then squad-impact origins, control-group swap, selection upgrades, command queueing, camera/sizing feel. Westley confirms visual items.

**Track C — Stage 13 packaging.** Owns `build/`, `scenes/privacy_modal/` (new), `autoload/debug_overlay.gd` (new), `autoload/sim_bridge.gd`, `autoload/theme_constants.gd`, `project.godot [application]` block (NOT `[autoload]` — C2 owns that), `scenes/settings/settings.gd`. Drives the eight Stage 13 checkpoints A → H. Two carried Stage 11 items (pause menu, line styling) held until Stage 11g lands.

## File ownership map

Live cross-reference. If you need to touch a file owned by another track, post a heads-up in `docs/ai_status.md` first.

| File / area | Track | Notes |
|---|---|---|
| `simulation/socket_server.py` | hard-protected | Explicit Westley approval, always. |
| `simulation/tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py` | protected | Westley approval before edits. |
| `simulation/tactical_engine.py`, `facing.py`, `damage.py` | treat as protected | Westley approval before logic changes. |
| `simulation/snapshot_serializer.py` | A primarily; C2 extended for 11g | Tick-delta shape changes go to `docs/architecture.md` first. |
| `simulation/config.py` | A | Balance lives here. C2 added Stage 11g feature flags (off by default) — leave those alone. |
| `simulation/pipe_transport.py` | A | `--root` argparse already landed. |
| `simulation/world_view/**` | C2 (Stage 11g) | Hands off. |
| `simulation/chronicle_assembler.py` | C2 from Checkpoint N | Coordinate via ai_status.md. |
| `simulation/sim_tuner.py`, `force_allocator.py`, `force_composition.py`, `power_rating.py` | A | Balance work. |
| `simulation/test_*.py` | A | Diagnostic harnesses. |
| `scenes/tactical/**`, `scripts/tactical/**` | B | All tactical mechanics. |
| `scenes/world/**`, `scenes/shared/world_view/**` | C2 (Stage 11g, while in flight) | Hands off until Stage 11g lands. After that, Track C inherits 11C1 line styling and pause menu. |
| `autoload/faction_palette.gd` | C2 | New, owned by Stage 11g. |
| `autoload/sim_bridge.gd`, `autoload/theme_constants.gd` | C | Stage 13. |
| `autoload/debug_overlay.gd` (new) | C | Stage 13 D. |
| `autoload/era_theme_resolver.gd` | stable | Don't edit without approval. |
| `scenes/privacy_modal/**` (new) | C | Stage 13 C. |
| `scenes/settings/settings.gd` | C | Version label. |
| `project.godot [application]` | C | Custom user dir, main scene. |
| `project.godot [autoload]` | C2 | C2 added FactionPalette. Coordinate via ai_status.md before any addition. |
| `build/**` | C | Stage 13 packaging. Track A appends to `pyinstaller_spec.py` `hiddenimports` if asked. |
| `docs/launch_todo.md` | shared | Mark items closed with date. |
| `docs/ai_status.md` | shared | Claim before starting. |
| `docs/architecture.md` | gated | Tick-delta shape changes here *before* implementation. |
| `docs/bible/**` | gated | Append-only; bible edits need Westley sign-off. |

## Order of operations

1. **Active right now:** C2 finishes Stage 11g (Checkpoints H–Q).
2. **Safe to dispatch concurrently with C2:**
   - **Track A** — start with A1 (force allocation scale tuning).
   - **Track B** — start with B1 (rotation renderer fix), then B2 (squad impact origins). C1's Stage 11d work is complete and `unit_renderer.gd` is clean.
   - **Track C** — start with C1 (Stage 13 Checkpoint A — PyInstaller bundle), then C2 (Checkpoint D — debug overlay).
3. **Once Stage 11g lands** (C2 done):
   - Track C unblocks 11G pause menu and 11C1 line styling, slots them in before Stage 13 Checkpoint F.
   - Coordinate any chronicle output polish work that needs `chronicle_assembler.py` (Track A or another claimed session).
4. **Final:** Stage 13 Checkpoints F (clean install, Westley runs the 20-item checklist) and H (three full sessions, fresh build).

## Guardrails (apply to every track)

- **Protected files** require Westley approval. See ownership map above.
- **Tick delta shape changes** go to `docs/architecture.md` *before* implementation.
- **Invariants** — never widen thresholds, loosen tolerances, or weaken a test to make implementation pass. Scope-narrowing only, with the case explicitly out of the invariant's intent.
- **No blind git reverts** — `git checkout/restore/stash` requires confirming with Westley that working tree is clean.
- **One fix at a time** — batched fixes break bisection.
- **No shotgun debugging** — hypothesis → instrument → measure → fix.
- **Stage 13 ⛔ STOP gates** are absolute. Wait for Westley between checkpoints.
- **Visual-confirm items** stay "ready for confirm" in ai_status.md until Westley confirms.

## How to dispatch a session

For each track, paste this into a fresh Claude Code window:

```
Read in order: CLAUDE.md, docs/launch_tracks/<track_file>.md, docs/ai_status.md.
That track spec is your brief. Follow it strictly. Do not pick up items from
other tracks. Claim items in ai_status.md before editing. Report your first
move and wait for my "go" before any code change.
```

Replace `<track_file>` with `track_a_sim_and_balance`, `track_b_tactical_mechanics`, or `track_c_stage_13_packaging`. One window per track. Do not run two windows on the same track simultaneously — they will race on ai_status.md claims and the same files.
