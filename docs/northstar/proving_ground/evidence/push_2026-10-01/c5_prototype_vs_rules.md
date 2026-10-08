# C5 galaxy: where the approved prototype differs from the rule text (A56)

Source: A56 (`docs/northstar/plans/2026-10-01-architect-rulings-2.md`, Addendum 23): the build matches the prototype (`scenes/mockups/galaxy/`) until Westley has compared it with the game; the rule text is then rewritten to the look he confirms. Line numbers are on `push/C5-G3-impl` (`4302f0a`) / origin/main at the time of writing. "Game" means `scenes/galaxy/` as built on G3-impl.

## Differences that A48 would have overridden (suspended by A56)

| # | Topic | Rule text | Prototype | Game as built (G3-impl) |
|---|---|---|---|---|
| 1 | Band distances, `qa_state` / HUD band | R-106-03: Overview d >= 75, Regional 40 <= d < 65, Local d < 25 (A48-3: rule wins) | `scenes/mockups/galaxy/orbit_camera.gd:27-28` `BAND_SPLIT_LOW := 32.5`, `BAND_SPLIT_HIGH := 70.0`; `get_band()` at 333-340 splits there | `scenes/galaxy/galaxy_view.gd:30-31` same 32.5 / 70.0; `_band_for()` at 299-304 |
| 2 | Band distances inside the prototype are not consistent with each other | (n/a) | The disclosure controller `scenes/mockups/galaxy/legacy_zoom_disclosure_controller.gd:14-17` uses 75 / 65 / 40 / 25 and sets `current_band` "overview" from 65 and "local" below 25, so for d in [65,70) it says overview while `get_band()` says Regional, and for d in [25,32.5) it says regional while `get_band()` says Local. `galaxy_view.gd:_band_weights()` (mockup, 188-205) also blends on 25/40/65/75 | same two sets of numbers coexist: `scenes/galaxy/legacy_zoom_disclosure_controller.gd:14-17` (visuals) and `galaxy_view.gd:30-31` (HUD band, name labels visible from 70, `galaxy_view.gd:142,189`). The A48-3 consistency check (HUD band == controller band) is therefore not satisfiable without changing one side; A56 leaves both |
| 3 | Which edges are drawn | R-106-02: adjacent same-faction systems only (A48-4: cross-faction and neutral edges not drawn) | `scenes/mockups/galaxy/galaxy_adapter.gd:25-28` adds a connection for every galaxy edge; border edges take the owner colour, all others `TRADE_DIM` (`mockups/galaxy/galaxy_view.gd:7`, `Color(0.42, 0.44, 0.5, 0.5)`); `sync_system` (39-47) re-adds every touching edge | `scenes/galaxy/galaxy_adapter.gd:34-42` (comment lines 8-10 say the same) draws every edge with both ends in the snapshot; same-faction non-trade edges take the owner colour, everything else `TRADE_DIM` (line 15) |
| 4 | Drag direction (vertical) | R-107-01 says left-drag pans; A48-2 said vertical drag is grab-style (map follows pointer) | `scenes/mockups/galaxy/orbit_camera.gd:256-264` `_pan_by`: `_target -= right * rel.x * speed; _target += fwd * rel.y * speed` with `fwd` the camera's backward ground vector (`basis.z`). Horizontal is grab-style (drag right moves the map right). Vertical is inverted: drag down moves the target toward the camera, so the map moves UP on screen (not following the pointer) | `scenes/galaxy/orbit_camera.gd:102-112` `_pan` uses the camera's forward ground vector: drag down moves the map down, i.e. grab-style on both axes, ground-plane scaled by `1/sin(PITCH_DEG)`. THE GAME DOES NOT MATCH THE PROTOTYPE HERE (see Ambiguities) |
| 5 | Pan speed | R-103-09 (constant on-screen speed) was withdrawn for the galaxy by A48-2 | `orbit_camera.gd:13,262` `PAN_SPEED 0.09 * distance / 50`: proportional to distance, not an exact on-screen constant | `orbit_camera.gd:104-106` exact on-screen constant (`2 * d * tan(fov/2) / viewport height`) |

## Other differences noticed (no A48 item covers them; not tested)

| # | Topic | Rule text | Prototype | Game |
|---|---|---|---|---|
| 6 | Right-drag | R-107-01: orbits | yaw and pitch (`orbit_camera.gd:267-271`, pitch clamped 20-85, `PITCH_DEFAULT_DEG` 55) | yaw only (`scenes/galaxy/orbit_camera.gd:82-84`), pitch fixed at 55 |
| 7 | Click-to-focus | R-107-01: centres on the system and zooms to Local | distance 28 over 1.5 s (`orbit_camera.gd:24-25`) | distance 25 over 0.6 s (`scenes/galaxy/orbit_camera.gd:12,17`) |
| 8 | Zoom range and step | (not specified) | distance 15 to 120, step 10 percent (`orbit_camera.gd:7-9`) | distance 10 to 220, step x0.9 (`scenes/galaxy/orbit_camera.gd:9-10,13`) |
| 9 | Idle camera | R-107-02: outside a jump the camera is fully the player's | auto-camera moods drift the camera until the first input (`orbit_camera.gd:113-120`, mood table 41-52) | none; only an eased focus, never drifts |
| 10 | Edge dimming by faction hover/pin | R-107-05: only the hovered system's own filaments brighten | emphasis per faction (`mockups/galaxy/galaxy_view.gd:208-212,252-266`, hover_faction / pin_faction) | not present on G3-impl (faction list and data panels are a separate unit, A48 item 7) |

## Pinned in tests (prototype parity, only where cheap and unambiguous)

- Band splits 70 and 32.5: `tests/test_galaxy_view.gd` `_check_bands_match_prototype_A56`.
- Every edge drawn, non-same-faction ones dim (`TRADE_DIM`): `tests/test_galaxy_renderers.gd` `_check_every_edge_drawn_dim_when_not_same_faction_A56`.
- Vertical drag direction: NOT pinned (prototype and game disagree, difference 4).
