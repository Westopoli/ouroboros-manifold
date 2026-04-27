# AI Status Board

Shared status file for parallel Claude sessions working on launch to-do items. Before starting a task, claim it here. Check this file before picking up work to avoid collisions.

## Format

```
- [ ] Task name — **claimed by: [session description]** — status notes
- [x] Task name — **done** — summary of what changed
```

## Active Work

- [ ] Fix unit rotation not working — **claimed by: Opus session (rotation/visuals)** — **ON HOLD**: formula fix done, 5/6 unit types confirmed correct, bombard offset pending verification. Blocked on other session's new_game.gd parser error preventing game launch
- [x] Fix mission briefing empty / Wire mission generator into game loop — **done** — pipe_transport.py: added _generate_and_build_engine(), _mission_setup_to_briefing(), _build_fallback_mission(); game loop uses real missions via --real-missions flag (passed by sim_bridge.gd); time_jump.py: now accumulates faction_actions; sim_bridge.gd: adds --real-missions arg

- [ ] Improve chronicle text output — **claimed by: Opus session (rotation/chronicle)** — implementing 6-step plan: prose event names, region grounding, faction-attributed deltas, word-echo prevention, overlap dedup, fragment trimming

- [ ] Stage 11.5 — World View 3D Territory Visualization — **claimed by: Opus session (world view)** — starting Checkpoint A (main menu / world view file separation). Touches: world_view_structure.gd/.tscn, main_menu.gd, loading_screen.gd, then later settled_reach_renderer.gd, orbital_camera_3d.gd, chronicle_scroll_panel.gd, chronicle_entry.gd, time_jump_sequencer.gd

## Cross-Session Notes

- **SIM_UNITS_PER_SIDE changed from 1 → 10** in `autoload/sim_bridge.gd:35` by rotation session. Needed 10v10 to properly test facing. The mission wiring session should be aware this affects unit counts in briefing data. Revert to desired value when done if needed.
- **Chronicle text improvement plan** (rotation/chronicle session) — purely Python-side text pipeline changes. Does NOT touch any Godot files, scroll UI, or world view rendering. Files being modified:
  - `simulation/events.py` — adding `chronicle_prose` string field to each TEMPLATES entry (no behavioral changes)
  - `simulation/chronicle_assembler.py` — region grounding, word-echo prevention, faction-attributed deltas
  - `simulation/chronicle_distiller.py` — cross-entry overlap dedup
  - `simulation/library/chronicle/fragments.json` — trimming verbose fragments
  - The world view session (implementing `world_view_major_modification.md`) touches the Godot-side scroll panel and faction-colored text — no conflict with these Python text changes. If the world view session needs to change how `ScrollEntry` fields are consumed in GDScript, the chronicle text session is not modifying the `ScrollEntry` dataclass shape.

## Completed

*(none yet)*
