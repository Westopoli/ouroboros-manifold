# Legacy

Retired code kept as provenance. Nothing here is built by the game or its gate.

- toys/layerlab (now `legacy/toys/layerlab`): the layer-dynamics toy the skill lab's sample, rows and formations modules were ported from (2026-10-01); last touched by a9fd3105; kept as provenance, not built.

## scenes/debug (now `legacy/scenes/debug`)

Eight hand-run debug scenes that nothing loads (no scene, autoload, test, `project.godot` or script names them; checked by grep 2026-10-23). Only `wave2_visual_check` has a header comment; the other purposes are read from the scene's code. Each is kept as provenance of how the panel it drove was first looked at, not run. `scenes/debug/debug_ws_test.*` stays: `tests/test_tacticalbridge_ratchet.gd` names it.

- test_chronicle_scroll (last commit c4d9441a): drove the chronicle scroll panel with mock entries and a mock time jump, printing the print-finished and expansion signals.
- test_faction_info_panel (last commit 6fb9680c): showed the faction info panel on mock factions.
- test_faction_palette (last commit 300fc699): dumped the FactionPalette swatches and per-region values for several scenarios.
- test_info_panel_host (last commit 6fb9680c): hosted the info panel host over mock regions.
- test_region_info_panel (last commit 6fb9680c): showed the region info panel on mock regions.
- test_time_jump (last commit 5cde9aa5): stepped a time-jump sequencer through a paced panel.
- test_world_view (last commit 0c6a3805): loaded the shared world-view shell for a by-eye check.
- wave2_visual_check (last commit 2e1768bb): "runs the two Wave 2 UI changes through a paced sequence so Westley can read and verify each step before it advances".
