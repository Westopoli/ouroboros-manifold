# Gap-fix plan: make the MVP honest in real play

## Context

The MVP build items are on main (bk-46), and the local 30B has started playing the build for QA. Four read-only investigations then found things that pass their tests but are wrong or missing in real play, because tests call functions directly:
- a C4 draft, with an adversarial audit of it
- a runtime audit of the draft's headline gaps
- deep sweeps of the sim/pipe and of the client

A plan review against the code corrected the first draft of this plan. The findings are in `~/Projects/om-push/logs/verified-picture-2026-09-28.md`, with the detail reports beside it.

The goal: what a player sees, and so what the 30B reports, reflects the real simulation. This is also the first work run under the new CLAUDE.md architecture rules (frozen contracts, one owner per file, small build units, wired not just tested), with gate lints that keep this class of gap from coming back.

Westley's decisions (2026-09-28):
- New Game keeps going straight to the galaxy for the MVP, and onboarding (E-08 S-063) stays parked behind Q-063-01/02.
- The in-game bug report is kept and wired into live play.
- The Era Library is kept and its data made real; Replay Tutorial and the access-key hint leave the main menu.
- The commander is a dedicated unit in each mission.
- C4 is retired; its three useful facts move into existing files.
- **Prototype migration.** The approved galaxy and chronicle prototypes (`scenes/mockups/galaxy/`, `scenes/mockups/chronicle/`, including a790cb2 and 037ed26) become the live MVP look.
  - The simulation itself grows to hundreds of regions, so every rendered system is a real region.
  - 60 fps on a GTX 1070 stays the hard bar, and the galaxy falls back to cheaper rendering automatically when it would miss it.

## How the work runs

- **Tiers.** Architect (this chat) writes rules, contract shapes and briefs, and rules on reports. Engineer (`subagent_type: engineer`) writes every piece's tests first, the lints, and does the git and merge work. Doer (`sonnet46-doer` leaves, spawned by the lane chats) builds against a brief. The sim lane chat and the client lane chat each get one batched brief per wave and report once.
- **Rules per piece.**
  - Tests land red first.
  - One owner per file.
  - About one file and under 100 lines per build unit.
  - A contract change lands as its own piece before its consumers.
  - No stacked branches: a piece starts from fresh origin/main after the previous piece on its file lands.
  - Everything reaches main through the queue and the merge clerk.
  - Nothing is launched while plan mode is on.
- **Piece ids.** Each unit takes the next increment id of the attached piece that owns its file (for example `B9-N` for `mission.c`, `T1-N` for `om_pipe.c`, `C4-N` for `debrief.gd`, `T2g-N` for `load_game.gd`). Bare new ids would collide with attached `C1`..`C5` and fail `pieces.py check_unique_ids`. A file with no owning piece gets a row added in Wave 0.

## Wave 0: rails first (Architect and Engineer)

1. **Land the approved CLAUDE.md on main.** Resume the stopped Engineer agent; its branch `push/claude-md-trim` is ready, and it stopped only because plan mode was inherited. Rewrite the stale references it found: `docs/legacy/agora_era/stage1_audit.md:18,803`, the three `docs/legacy/stage_specs/_completed/stage_7*`/`stage_8` spec lines, and `stage_11d_mid_mission_hud_spec.md:28`.
2. **`pieces.toml` hygiene (M0).**
   - Set `Q1` to attached, since its content landed with C3-4b, and drop its one-off `scenes/**/*.gd` glob. That glob would otherwise overlap every client piece.
   - Add rows for files no piece owns: `autoload/ui_data_bus.gd`, `autoload/tactical_bridge.gd`, `autoload/sim_bridge*.gd`, `scenes/error_screen/**`, `scenes/loading_screen/**`, `scenes/settings/**`, `scenes/era_library/**`, `scenes/bug_report/**` and the bug report manager, if unowned (the lint says which).
3. **Three gate lints** in `scripts/specfactory/`, each with M0-owned tests and a positive control, wired into `merge_gate.sh`:
   - **Reachability** (`reach_lint.py`). Every public symbol in `csrc/ouroboros_sim.h` that tests call must be reachable from `om_world_step`, `om_tactical_step`, the jump entry, or a pipe handler, or listed in a test/debug allowlist. Build on `tick_closure.py`'s `ORCHESTRATORS`. `om_world_step`'s `OM_FEAT_TACTICAL` branch (`csrc/sim.c:206,230,547`) is allowlisted as a test-only path, with a note.
   - **Ownership overlap** (`owner_lint.py`). No file may be owned by two in-flight pieces. Reuses `pieces.py` (`check_owns_disjoint`), which today also counts attached pieces and so needs the in-flight filter.
   - **Diff size** (`size_lint.py`). Warns above 100 changed lines or 1 owned file for merge-profile pieces, and rejects above a hard cap Westley sets. It skips docs-profile contract and harness pieces.
4. **Baseline the reachability lint on main.** It must list `om_mission_eval_commander_fate`; if it does not, the lint is wrong. Its output is the checked work list for Wave 2.
5. **Correct `docs/architecture.md` (M0).**
   - Line 288: the `visible{}` mechanism is `om_player_can_see_unit`.
   - Delete the duplicate at 316-320.
   - Add a tick-order section (from the audited `push/c4-mvp` `3-components-sim.md`).
   - Note the two tactical drive paths: the pipe's `tactical_step` is the live path; `om_world_step` with feature 8 is test-only by design.
   - Add a short scene-graph note to the client docs.
6. **E-10 rule for the commander (Architect).** Each mission spawns one commander unit for the player, tied to the lineage character the HUD shows. Its hit points decide the fate that R-077-03 and R-079-03 describe. The commander's unit type and on-screen marker become one register row, with candidates for Westley: an existing durable type such as Warden with a marker ring, or a new Commander profile. S1 waits on that answer.
7. **Housekeeping.** Delete the obsolete m1 escalation notes and the stray `wt/sweep-sim` worktree, and update the in-flight tracker memory.
8. **Region-count rule change (Architect, E-03).** R-021-01 becomes: region count drawn uniformly from [250, 400], taken from the approved prototype's `SYSTEM_COUNT_MIN/MAX`. The faction count stays 15, per the bible; the prototype's 4 to 8 is noted, not adopted.
   - Every scale budget sized to the old range gets re-measured at 400 regions and presented to Westley before it is changed. That covers the E-03 generation budget ("110 regions under 5 ms"), E-02 drift ("60 regions under 50 µs"), and the per-tick budgets in E-04 to E-07.
   - The same goes for the E-16 galaxy budget ("60 fps with 60 systems"). Its restatement at the new count is his call, with the automatic fallback in G-G4 as the mechanism.
   - Rates the rules calibrated at about 100 regions (events per window, friction and revolt probabilities, Knowledge Lost per window) are re-run at the new size. Each rate that moves goes to the register as "scales with regions: retune or keep" rather than being tuned silently.

## Wave 1: contract piece HDR4 (docs profile; Architect approves the shape)

Additions only; ABI stays 3. The plan review found which accessors are really missing:
- **Objective node and radius** (`om_objective_get_node`, `om_objective_get_radius`). `om_objective_spec` (`ouroboros_sim.h:1090-1098`) has neither.
- **Started mission's force composition** (`om_mission_get_force_count`, `om_mission_get_force_unit`). No accessor exists, and `om_mission_spawn_force` (`mission.c:2016-2026`) discards the spawned ids.
- **Chapter number** (`om_chapter_get_number`). `chapter_number` exists and is saved in generational state (`generational.c` about 255 and 1005); only the getter is missing.
- **Commander unit id** (`om_mission_get_commander_unit`), after the rule in Wave 0 item 6.
- **Not needed:** a faction-refs accessor. `om_chronicle_entry` already carries `faction_ref` and `lineage_ref`, and the pipe already reads the entry.

The piece carries the header, `signatures.toml`, `symbol_modules.toml`, conftest bindings, one core test per accessor, and the `docs/architecture.md` frame text.

**HDR5, region scale (contract, docs profile, after the Wave 0 rule).**
- `OM_MAX_REGIONS` goes from 128 to 512 (`csrc/om_internal.h:14`, used in 58 places).
- The dense `region_edge[OM_MAX_REGIONS][OM_MAX_REGIONS]` matrix (1 MB at 512) is measured. If any per-tick loop scans it in O(N²) and misses budget at 400, it becomes an adjacency list.
- The save format version is bumped, and so is the ABI if any public struct embeds a region-sized array (the lane checks).
- Worldgen's feasibility gate and placement are verified at 250 and 400. The E-03 tests move to the new range as a rule change: M0 edits, ledger row, not a loosening.
- The scale suite runs at 400 regions.
- The pipe's snapshot and delta sizes, and the client's parse time, are measured at 400 regions.

**Chronicle frame, ownership timeline (contract, documented in `docs/architecture.md` first).** The chronicle frame gains `ownership: [{tick, region, owner}]`, the ownership changes during the jump, so the galaxy can replay them as the prototype does (fixture key `ownership_timeline`). It is built in the sim lane as a `T1-N` piece after S3.

## Wave 2: sim and pipe (sim lane; tests by Engineer first)

- **S1 (`B9-N`, `mission.c`): the commander is real.**
  - `om_mission_spawn_force` keeps the ids and spawns the commander unit per the new rule.
  - `om_mission_end` calls `om_mission_eval_commander_fate(hp, max_hp)` with the commander's state (`om_unit_get_hp`, `om_unit_profile_max_hp`).
  - Tests: a core test, and a transport test where the commander's death gives a `killed` debrief.
- **`om_pipe.c` chain.** Five pieces, strictly in order: S2, S3, S4, S5, S6.
  - **S2:** the mission frame's `node`, `radius` and `force` come from HDR4. Transport test against the worked example in `docs/architecture.md`.
  - **S3:** `refs.factions` from the `faction_ref` the pipe already reads. Test: no `[faction]` text after a jump. Character names are deferred: no entry links to a character, and `chronicle_names.gd` takes no lineage argument. That becomes a register row, not a build item.
  - **S4:** save honesty. The sidecar's `format_version` comes from `OM_SAVE_FORMAT_VERSION`, `chapter` from `om_chapter_get_number`, and `list_saves` is sorted by slot name.
  - **S5:** remove the stale "STUB" labels on `om_tactical_step` in the header and the pipe comments. The test docstring is M0's.
  - **S6** (latent): tactical frame `tier` and `state`, filled from unit accessors if they exist, otherwise marked reserved in `docs/architecture.md`.

## Wave 2 in parallel: client (client lane)

Order within a shared file is by `depends_on`. `project.godot` gets G1's change first, then G6's. `debrief.gd` gets G1's change first, then G2's.

- **G1: the Python sim leaves the live path.** One unit per file:
  - `load_game.gd`: remove the dead legacy save cards, and remove the Delete button, since no E-16 rule covers deleting a save.
  - `error_screen.gd`: Retry goes through SimSession.
  - `debrief.gd`: drop the `continue_from_debrief` send.
  - `ui_data_bus.gd`: `trigger_autosave` goes through SimSession instead of SimBridge.
  - `loading_screen.gd`: off SimBridge.
  - Last, `project.godot`: remove the SimBridge autoload.

  The parked chain (`new_game`, `onboarding`, `time_jump_sequencer`) gets a one-line "parked until Q-063-01/02, unreachable" header. `tests/test_qa_state_scenes.gd:103-104` instantiates `time_jump_sequencer` and must be adjusted; M0 classifies that change and any other SimBridge-only test. `simulation/` stays as legacy tooling.
- **G2: pipe failures are visible.** A small shared helper on the bridge (`C2-N`), then one unit per scene: galaxy, debrief, chronicle, tactical_c, briefing. Each shows an error panel with the reason, Retry and Main Menu instead of a bare `push_error`. The briefing's silent `mock_001` fallback leaves the live path.
- **G3: main menu per the decision** (`C1-N`). Remove Replay Tutorial and the access-key hint; keep New Campaign, Continue, Settings, Quit and Era Library.
- **G4: debug overlay gated off by default.** It appears only with an explicit debug flag, which is not set in normal or QA launches. Rewire it from the dead TacticalBridge to the tactical frame.
- **G5: stored settings applied at boot.** Resolution, fullscreen, master and music volume, and edge scroll, which the live tactical_c camera reads.
- **G5b: key rebinding**, its own piece. This is new UI, new storage and `InputMap` wiring for the layer modifier and control groups (R-110-02); none of it exists today.
- **G6: TacticalBridge off boot.** Remove the autoload and its perf logger (hard-coded macOS path) once G4 and E2 no longer read it.

## Wave 3: new behaviour behind written rules

- **E1: Era Library with real data.**
  1. The Architect writes the screen's rules from E-20 S-146..S-149: installed packs as validated by `scripts/specfactory/pack_validate.py`, and entitlement from a local ownership store (all installed eras owned in development).
  2. Mastery and tier progress are defined nowhere, so they become register rows and show "not yet tracked" until answered.
  3. The Engineer writes tests.
  4. The client lane replaces the hard-coded values in `sim_bridge_data_source.gd`.
- **E2: bug report in live play**, a rewrite rather than a move. It keeps today's player-facing behaviour: F12 builds a ZIP with a screenshot, logs, state and metrics, saves it to `user://logs/reports/` and the Downloads folder, and copies it to the clipboard for sharing. Two things change:
  - It reads state from the live bridge and tactical frame instead of the dead TacticalBridge (`bug_report_manager.gd:35,86-92`).
  - It is reachable from every live screen, with a "Report a bug" entry in the tactical pause menu.

  The Architect writes the story in E-16 first. The work is two or three units. No network calls.
- **E3: delete the legacy tactical scene** (`scenes/tactical/`) and its legacy-only tests, after E2. M0 classifies each test removed.

## Prototype migration (client lane, from Wave 2; region-dependent parts after HDR5)

**Galaxy** (`scenes/galaxy/`, owner C2; one unit per file, in order).

The live view is coloured points, straight tubes, and a camera that cannot move. The prototype has territory shells, shimmering curved lanes, labels, an ambient rig, a full camera and hover emphasis.

Must survive unchanged:
- every `qa_state()` key: `system_count, owners, edge_counts` (by `om_edge_type`), `systems_px, region_colours, owner_colours, band, distance, pick_radius_px, edges_3d, hash, tick, plants`;
- the six plants and their visible effects;
- conquest recolour on `set_snapshot`, which is what `test_galaxy_view.gd`, `test_galaxy_conquest.py` and `test_galaxy_pixels.py` fence.

Units:
- **G-G1 camera.** Port the prototype's pan, orbit, zoom, click-to-focus tween and idle mood cycle (`scenes/mockups/galaxy/orbit_camera.gd`) onto the live `orbit_camera.gd`, keeping its `set_view`/`qa_camera` API. Add `focus_region(i)` for the chronicle.
- **G-G2 renderers.**
  - Move `legacy_shell_renderer.gd`, `legacy_constellation_renderer.gd`, `legacy_ambient_rig.gd`, `legacy_zoom_disclosure_controller.gd` and the two shaders to live paths.
  - Write one new adapter from the live snapshot (region `i`, `owner`, edge `a`, `b`, `t`) into the renderers' `regions/connections/territories` shape. It replaces `galaxy_adapter.gd`'s fake-galaxy mapping.
  - Recolour happens through the shells.
- **G-G3 labels and hover.** Faction name labels and hover or pin emphasis come from the snapshot's `factions[]`, which the live view receives and ignores today. Names come from the client's existing name derivation (`chronicle_names.gd`), since the wire carries no names.
- **G-G4 frame-time fallback.**
  - The view measures frame time and steps down quality: raymarched shells, then the existing stand-in spheres, then fewer particles.
  - It keeps 60 fps on a GTX 1070 as the bar and reports the current quality tier in `qa_state`.
  - A desktop test asserts the tier drops under a forced slow frame (positive control).
  - The real-hardware number is Westley's to read.
- **G-G5 layout at scale.** The client layout (`scenes/galaxy/galaxy_gen.gd`) takes the prototype's spacing and disc constants, stays deterministic per region ids and seed, and handles 400 regions. `c_bridge.gd`'s `DEFAULT_N_REGIONS` moves into the new range, and the "real boot loads 80 regions" check moves with the rule (a rule change, edited by M0).

**Chronicle** (`scenes/world/chronicle_*`, owner C3).

Today the chronicle is a standalone screen reached from the debrief. Its entries already build clickable `[url=kind:id]` mentions and emit `mention_clicked`, but only the parked `time_jump_sequencer` listens. The prototype prints the chronicle beside an embedded galaxy, as E-16 S-108 says.

Must survive: the chronicle tests (`test_chronicle_scroll.gd`, `test_flow_spine.py`), its `qa_state` keys, and the `entries-dropped` and `refs-unresolved` plants.

Units:
- **G-C1 layout.** The live chronicle scene becomes the composite: the galaxy view with the scroll panel beside it, following the prototype's `chronicle_mockup.tscn` layout.
- **G-C2 mention click.** A region mention calls the galaxy camera's `focus_region(id)`, the same change 037ed26 made in the prototype (`MOUSE_FILTER_PASS` plus a one-shot guard so the row does not also expand). A faction mention focuses that faction's territory centroid; this needs S3's faction refs.
- **G-C3 jump replay.** During the scroll, ownership changes from the new chronicle-frame `ownership` list recolour and flash on the galaxy, as in the prototype's keyframes.

The prototype folders stay as reference until the migrated screens pass their tests and Westley's look. After that they are marked reference-only, not deleted.

## Critical files

- **Sim/pipe:** `csrc/mission.c` (`om_mission_end` about 1361, fate at 1372, spawn at 2016), `csrc/pipe/om_pipe.c` (815-840, `write_chronicle` about 905, `handle_save` about 1578-1594, `list_saves` 1402), `csrc/ouroboros_sim.h`, `csrc/generational.c`, `csrc/sim.c`.
- **Client:** `autoload/{c_bridge,sim_session,sim_bridge,sim_bridge_data_source,ui_data_bus,tactical_bridge}.gd`, `scenes/{load_game,error_screen,debrief,loading_screen,mission_briefing,main_menu,settings,era_library}/`, the bug report manager, `project.godot`, `tests/test_qa_state_scenes.gd`.
- **Migration:**
  - sources: `scenes/mockups/galaxy/{orbit_camera,legacy_shell_renderer,legacy_constellation_renderer,legacy_ambient_rig,legacy_zoom_disclosure_controller,galaxy_adapter,galaxy_gen}.gd`, `shaders/*.gdshader`, `scenes/mockups/chronicle/{chronicle_mockup,entry_view}.gd`
  - targets: `scenes/galaxy/{galaxy_view,orbit_camera,galaxy_gen}.gd`, `scenes/world/chronicle_{scroll_panel,entry,entry_expansion}.gd`
  - region scale: `csrc/om_internal.h` (`OM_MAX_REGIONS`), `csrc/worldgen.c`, `docs/bible/epics/E-03-*.md` (R-021-01)
- **Harness/docs:** `scripts/specfactory/` (new lints beside `tick_closure.py`, `pieces.py`, `merge_gate.sh`), `docs/northstar/plans/push/pieces.toml`, `docs/architecture.md`, `docs/bible/epics/E-10`, `E-16`, `E-20` (rules, M0 only), `docs/northstar/ambiguity_register.md`.

## Verification

- **Per piece:** tests are red on main and green on the branch. The three lints pass in the gate. The known red set is unchanged except for the rows the piece exists to turn green.
- **After Wave 2:**
  - The reachability lint reports no rule-backed behaviour that is tested but unwired.
  - `tests/transport`, `tests/csim/test_core_*`, the E-10 suite, the Godot tests and `tests/qa/desktop` all pass.
  - During a QA session, `ps` shows no `pipe_transport.py` process.
- **End to end (Westley's eyes; QA plays but judges nothing visual):**
  - A briefing shows a named position, a force roster and parity.
  - A mission whose commander dies says "killed in action".
  - Chronicle entries show faction names.
  - Killing the pipe mid-game shows the error panel.
  - The main menu matches the decision.
  - F12 produces a report from a live mission.
  - The galaxy shows 250 to 400 regions with shells, lanes, labels and the free camera. It holds 60 fps on Westley's machine and the min-spec bar through the fallback.
  - The chronicle prints beside the galaxy, and clicking a region mention flies the camera there.
- **Region raise:** the scale suite at 400 regions, with every re-timed budget confirmed by Westley. The rate re-runs are in the register. The E-03 tests pass at the new range.
- **30B QA:** over the next day of sessions, the `qa-backlog` branch shows no new rows about the fixed screens. Any that appear are regressions and go back to the owning lane.
