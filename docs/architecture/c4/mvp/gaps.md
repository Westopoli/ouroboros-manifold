# Gaps — where the model and the running code disagree, or a boundary is unclear

Every item cites file:line. Nothing here is a design decision; where a real choice is needed, it
is phrased as a question for Westley, not answered.

## 1. `docs/architecture.md` documents a fog function that is never called

`docs/architecture.md:288` states the tactical frame's `visible[faction]` field is
`"om_visibility_compute's set for that faction"`. The actual code building that field,
`csrc/pipe/om_pipe.c:1094-1129`, calls `om_player_can_see_unit` (`csrc/fog.c:470`) per unit
instead. `om_visibility_compute` (`csrc/fog.c:615`) has no caller anywhere in `csrc/` except its
own definition (`grep -rn "om_visibility_compute" csrc/` returns exactly one line). Both
functions do real fog work (`om_player_can_see_unit` calls `om_fog_faction_sees`,
`csrc/fog.c:474`), so this is not a stub standing in for the documented function — it is a second,
working implementation that the doc doesn't mention, while the one the doc names sits unused.
**Question for Westley**: should `docs/architecture.md` be corrected to name
`om_player_can_see_unit`, or should the pipe be rewired to call `om_visibility_compute` (unclear
which is the intended long-term API)?

## 2. `csrc/pipe/om_pipe.c`'s own file-header comment is stale against its body

The comment block at `csrc/pipe/om_pipe.c:1-65` (dated to the "T1-2" wiring pass, 2026-09-24)
states flatly: `"map.nodes" reflects the stub (always empty), "map.cover" and "map.obstacles" are
always empty, and "units"/"visible" are always empty"` (`:50-52`) because "there is also no
enumerator for live tactical unit ids at all" (`:47-48`). Checked against the current body, all
three parts of this claim are now stale, not just the units/visible part:

- **units/visible**: `csrc/pipe/om_pipe.c:1043-1048` enumerates real unit ids via
  `om_unit_count`/`om_unit_id_at` and builds populated `units[]` and `visible{}` entries, using
  `om_unit_get_faction`/`om_player_can_see_unit` (`csrc/fog.c:470`). `om_unit_count`/`om_unit_id_at`
  are real, non-stub E-11 accessors (piece B10, attached per `pieces.toml:196-210`).
- **map.nodes**: `om_map_get_node_count`/`om_map_get_node_pos`/`om_map_get_node_type`
  (`csrc/tactical_mapgen.c:454-476`) are real, non-stub accessors reading a live `om_mapgen_state`
  struct, not hardcoded returns. Every mission populates three real nodes: `om_mission_setup`
  (`csrc/mission.c:2054-2065`) calls `om_mission_instantiate_map`, which calls
  `om_map_add_spine_node` and `om_map_add_spawn_point` twice (`mission.c:2046,2048-2049`), both
  real functions (`tactical_mapgen.c:288-295`, backed by the same `om_mgs_add_node` helper `cover`
  uses). `"map.nodes"` is not always empty; it is always (at least) 3 after `mission_start`.
- **map.cover**: also real and populated — `om_map_add_cover` (`mission.c:2047`) places the
  objective's cover circle, read back by `om_map_cover_count`/`om_map_cover_at`
  (`csrc/pipe/om_pipe.c:1012-1015`), both real (see gap 7's correction).
- **map.obstacles**: this part of the original claim is still accurate.
  `om_map_add_obstacle` (`tactical_mapgen.c:306`) is real and not a stub, but no production code
  was found to call it (`grep -rn "om_map_add_obstacle(" csrc/*.c` outside `tactical_mapgen.c`
  itself returns nothing), and separately `csrc/pipe/om_pipe.c:1033-1036` has its own comment
  confirming no accessor enumerates obstacles at all, so the field is hardcoded `[]` regardless.

A comment that is right about one field, wrong about two, and half-right about the reason (a real
unit enumerator now exists) is worse than a comment that is simply outdated; it should be re-split
or re-dated at the next touch of this file.

## 3. Two live simulation transports, both spawned by the running client

`autoload/sim_bridge.gd:58-61` (`SimBridge._ready()`) unconditionally spawns
`simulation/pipe_transport.py` (the legacy Python sim) on every boot, because `USE_LIVE_SIM`
(`sim_bridge.gd:29`) is a hardcoded `true` with no code path that sets it `false` in this
checkout. Independently, `autoload/sim_session.gd`'s `SimSession.bridge()` lazily spawns
`pipe/ouroboros_pipe` (the C sim) the first time any live-flow scene calls it
(`scenes/galaxy/galaxy_view.gd:97`, etc.). Both subprocesses can be running at once during
ordinary play, one of them (the Python one) doing real, non-trivial work
(`autoload/tactical_bridge.gd`, `autoload/ui_data_bus.gd` via `autoload/sim_bridge_data_source.gd`)
that has nothing to do with the scenes the player actually sees in the live flow, except for
save-slot listing, era library, and settings, which genuinely do read from it. See `gap 4` for the
concrete visible consequence.

## 4. `scenes/load_game/load_game.gd` renders two independent save-slot lists in one screen

`load_game.gd:74` calls `_refresh_slots()` (`:101-109`), which reads `UIDataBus.get_save_slots()`
(the legacy `SimBridge`-backed source) and builds `tm_card` UI rows. Separately, `_render_bridge_rows()`
(`:272-297`, called after a `list_saves` round-trip through the C-bridge) builds a second set of
plain `HBoxContainer` rows from `_bridge.load(slot_id)` (the new C-transport save format). Both
write into the same `_slot_list` container. Only the C-bridge rows' Load button actually navigates
to `"galaxy"` (`load_game.gd:294`, inside `_render_bridge_rows`); the legacy cards' click handler
was not traced as reaching the live galaxy scene. **Question for Westley**: is the legacy
`UIDataBus` save-slot card meant to be removed now that the C-bridge path (piece `T2g`, attached)
covers real loading, or is it still load-bearing for something the C-bridge path doesn't yet do
(e.g. showing era/name/playtime metadata `UIDataBus`'s mock schema carries and the sidecar JSON
does not)?

## 5. `new_game` / `onboarding` / `time_jump_sequencer` are a three-scene chain, all orphaned from the live boot path

`scenes/main_menu/main_menu.gd:71` binds the `"NEW GAME"` label directly to `action: "galaxy"`, and
`_on_menu_action`'s `"galaxy"` arm (`main_menu.gd:314-320`) calls `SceneRouter.go_to("galaxy")` with
no intermediate scene. A repo-wide search finds **no** `go_to("new_game"` call site anywhere in
`scenes/`, so `scenes/new_game/new_game.tscn` is unreachable from the confirmed live flow, even
though it is registered in `SceneRouter.SCENES` (`scene_router.gd:7`) and is a complete, working
scene (creates a save slot via `UIDataBus.create_save_slot`, `new_game.gd:205`, then calls
`go_to("onboarding", ...)`, `new_game.gd:206`). Since that caller never fires,
`scenes/onboarding/onboarding.tscn` is unreachable too, and since `onboarding.gd:386` is the only
caller of `go_to("time_jump", ...)`, `scenes/world/time_jump_sequencer.tscn` — the scene driven by
`SimBridge`'s `time_jump_started`/`time_jump_keyframe`/`chronicle_entry`/`time_jump_ended` signals,
relayed through `UIDataBus` (`autoload/ui_data_bus.gd:5-8`), i.e. the **legacy Python transport** —
is unreachable as well. This is the client-side equivalent of gap 9's orphaned `scenes/tactical/`, except it is three
scenes deep; like `scenes/tactical/`, it is still exercised directly by `tests/test_qa_state_scenes.gd`
(`grep -rln "new_game\|onboarding\|time_jump_sequencer" tests/*.gd`), so it is tested-unreachable
rather than untested. Agora's QA profile (`~/Projects/agora/projects/ouroboros/qa.toml`) corroborates this
independently: its main-menu screen description names only the five menu buttons and describes
NEW GAME leading straight to the galaxy, with no era-select or difficulty step mentioned.

Every jump a player can actually trigger today goes through
`scenes/world/chronicle_scroll_panel.gd`'s `load_chronicle_live` (`autoload/c_bridge.gd:491-503`),
the **C transport**, which hardcodes a 50-tick jump (`c_bridge.gd:496`) regardless of how much time
has actually passed since the last one. The bible describes onboarding as asking the player
difficulty and mission-type preferences before the first chapter (`docs/bible/game_bible.md`, "The
Player's Toolkit"); none of that reaches the player in this checkout — not because the scene is
missing, but because nothing routes to it. **Question for Westley**: is `main_menu.gd:71`'s direct
`"galaxy"` binding a deliberate short-circuit for this stage of development, or a wiring regression
that should call `"new_game"` instead? Agora's QA profile documents **QA-003**: the chronicle list
is empty after a multi-tick game (`qa.toml`, screen description for `chronicle_scroll_panel`) —
unrelated to this orphaning (QA-003 is filed against the live `chronicle_scroll_panel` path, not the
unreached legacy one), not investigated further here.

## 6. `om_mission_begin`/`om_mission_is_started`/`om_mission_get_clock`/`om_mission_get_phase` are defined in `csrc/fog.c`, not `csrc/mission.c`

`csrc/fog.c:429-459` defines four mission-lifecycle functions that `symbol_modules.toml` and the
epic banners assign conceptually to E-10 (missions, `mission.c`), not E-12 (fog, `fog.c`). The pipe
calls them correctly (`om_mission_begin` from `handle_mission_begin`, `csrc/pipe/om_pipe.c:1272`;
`om_mission_is_started` from `in_recon()`, `:1260`), so nothing is broken — this is a code-location
gap, not a wiring gap, but it means a reader looking for mission lifecycle logic in `mission.c`
will not find where recon/begin state is actually stored (`om_fog_state`).

## 7. `csrc/tactical_mapgen.c`: the mission-setup primitives are real; the procedural generator is not

The file's header comment is boilerplate carried over from the skeleton-generation template
(`"has a file to read; every body below is a STUB the build card replaces"`, `tactical_mapgen.c:5`)
and, read literally, overstates how much of the file is still stub — the same pattern found in
every other `sig_table.py`-generated module that has since landed real code (`agent.c`, `resolve.c`,
`collision.c`, `friction.c`, `diplomacy.c`, `lifecycle.c` all carry the identical boilerplate and are
fully built; see `3-components-sim.md`). Checked function by function, `tactical_mapgen.c` splits
into two groups:

- **Real and called from production code**: `om_map_add_cover` (`:260`), `om_map_add_spine_node`
  (`:288`), `om_map_add_spawn_point` (`:292`), `om_map_add_structure` (`:297`), `om_map_add_obstacle`
  (`:306`, real but no caller found — see gap 2), `om_map_cover_count`/`om_map_cover_at`,
  `om_map_clear`, and the read-back accessors `om_map_get_node_count`/`_pos`/`_type`/
  `_nth_node_of_type` (`:454-483`) and `om_map_get_canvas_base_dimension` (`:434`). All of these are
  called from `csrc/mission.c`'s `om_mission_instantiate_map`/`om_mission_setup`
  (`mission.c:2033-2065`) and read back by `csrc/pipe/om_pipe.c`'s `write_tactical` — see the
  corrected gap 2.
- **Still `/* STUB */`**: `om_map_add_layer_restriction_zone` (`:271`), `om_map_get_active_seed`
  (`:428`), `om_map_get_compatible_layout_count`/`_layouts` (`:443,449`), `om_map_get_simulation_coupling`
  (`:491`) — layout-selection and seed/coupling accessors, not the node/cover/obstacle primitives a
  single hand-placed mission map needs.

What genuinely does not exist is the **procedural generator** — the piece that would call these
primitives many times over to lay out cover fields, obstacle clusters, and multiple spine nodes into
a real tactical map, instead of the one spine node, two spawn points, and one cover circle
`om_mission_instantiate_map` places by hand for every mission regardless of archetype. Piece `B15m`
(`pieces.toml:308-323`) is scoped explicitly to "fixture functions only... not the full
1575-line/29-test E-17 generator (held)" — that generator, not the primitives it would call, is
what is missing. The bible's E-17 map-generation epic (archetype-driven, varied layouts) describes
a system that does not exist yet; a single fixed three-node micro-map does.

## 8. `csrc/fog.c`'s `om_visibility_compute` — real code, exercised only by tests

Independent of gap 1's doc mismatch: `om_visibility_compute` itself is a real, non-trivial function
covered by `tests/csim/test_E12_S089_i_see_what_my_units_see.py` through
`test_E12_S094_how_fog_looks.py` (six files), reached only via ctypes in tests, never from the
tick or the pipe. This is a clean instance of the model's **tested-unwired** status: a piece of the
sim that is provably correct in isolation but provably never runs during play.

## 9. Legacy `scenes/tactical/` is a full, built, unreached scene stack

`scenes/tactical/` contains a complete tactical presentation
(`tactical.gd` 13.1K, `hud.gd` 26.4K, `terrain_renderer.gd` 12.3K, `unit_renderer.gd` 16.7K,
`input_router.gd` 11.2K, plus `visuals/*`), wired to `SimBridge`/`TacticalBridge`/the client-side
`Visibility` autoload (`scripts/tactical/visibility.gd`). It is registered in
`autoload/scene_router.gd`'s `SCENES` dict as `"tactical"` (`scene_router.gd:13`) but no
`go_to("tactical")` call site exists anywhere under `scenes/` — the live flow always uses
`"tactical_c"` instead (`scenes/mission_briefing/mission_briefing.gd:668`). It is exercised by
`tests/test_b3_tutorial_integration.gd` and `tests/test_qa_state_scenes.gd`. This is the client-side
equivalent of a tested-unwired component: real, tested, unreachable from the player's actual path
through the game. Given `scenes/tactical_c/` is comparatively minimal (11.8K, one file), the two
stacks are not equivalent in feature completeness — `scenes/tactical/`'s HUD, terrain renderer, and
visual-effects managers (`combat_heatmap.gd`, `ability_overlay_manager.gd`,
`destruction_manager.gd`, `attack_visual_manager.gd`, `ambient_density_manager.gd`, all under
`scenes/tactical/visuals/`) have no equivalent under `scenes/tactical_c/` yet. Agora's QA profile's
**QA-001** ("tactical view renders completely blank (flat grey) after Deploy... The frame IS loaded
(daemon state tick > 0) but nothing renders on screen",
`~/Projects/agora/projects/ouroboros/qa.toml`) is filed against `tactical_c`, the thinner of the
two stacks — consistent with, but not proven caused by, its comparative thinness.

## 10. Client-side fog-of-war logic exists in two more places than `csrc/fog.c`

`scripts/tactical/visibility.gd` (the `Visibility` autoload) is described as "single source of
truth for fog of war" (`visibility.gd:1`) for `scenes/tactical/`'s renderer, HUD, and input router
— a client-side predicate, independent of `csrc/fog.c`'s server-side computation, and applying only
to the unreached legacy tactical scene (gap 9). `scenes/tactical_c/` reads visibility from the
pipe's `visible{}` map instead (gap 1/2). No shared fog implementation exists between the two
tactical stacks.

## 11. The bible's E-19 multiplayer epic has no corresponding container

`docs/bible/epics/E-19-multiplayer.md` exists and describes lockstep two-client play (rung P9 in
`docs/northstar/PLAN.md:174`, "Two clients, lockstep... Checksums agree per tick; desync detector
silent; two-window QA session"). No networking code, no second-client launch path, and no lockstep
message format exist anywhere in this checkout. Every container and flow in this model assumes
exactly one player, one client process, one pipe process, one world. The single-player assumptions
most likely to need revisiting for multiplayer: `autoload/c_bridge.gd`'s one shared
`SimSession.bridge()` singleton per process (`sim_session.gd:14`, "the one pipe session of the
run"); the pipe's `player_faction` being a single scalar on the `hello`/`snapshot` frames
(`docs/architecture.md:238,244`) rather than per-client; and `QADaemon`'s single-port,
single-connection `TCPServer` (`autoload/qa_daemon.gd:33-34,87-94`), which has no notion of a
second player's session at all. **Planned, not built** — status per this model's legend.

## 12. The documented offline library builder does not match the one that exists

`CLAUDE.md:9` names `claude-sonnet-4-20250514` as the offline content-generation model (library
builder). The only concrete builder script in this checkout,
`scripts/library/emit_chronicle_fragments.py`, makes no model API call at all — it regex-parses
hardcoded C string literals out of `csrc/chronicle.c`'s `CHRON_FRAGMENTS[]` array
(`emit_chronicle_fragments.py:1-13,25-38`) and writes them to
`library/chronicle/fragments.json`. This is consistent with (does not violate) the "No runtime API
calls during play" rule, since it makes no call at all, runtime or otherwise, but it means the
actual chronicle prose in the running game today is hand-written placeholder text embedded in C
source, not model-generated content. If real content generation is expected before ship, no code
path for it exists yet in this checkout.

## 13. `csrc/om_internal.h`'s hook hint says B4's freeze dependency

`csrc/worldgen.c` (piece `B4`) is marked `depends_on = ["freeze"]` in `pieces.toml:74` with the
size-estimate note "needs F2's weak `om_world_generate` attribute" — the weak/strong override
pattern (`csrc/region.c:321`'s `__attribute__((weak))` `om_world_step`, similarly `region.c:217`'s
weak `om_world_generate`) is a real, load-bearing mechanism for how these pieces attach
independently without editing a shared dispatch table. It is unverified whether this pattern is
documented anywhere outside the C source comments themselves (`worldgen.c:4-8`) — a reader of
`docs/architecture.md` alone would not learn that world generation is wired this way. Noted here
as a documentation gap, not a code defect.

## 14. Cloudflare R2 and the GDExtension path are named only in `CLAUDE.md`/research notes

Both are stated intentions with zero corresponding code: R2 (`CLAUDE.md:9`, no other reference
anywhere in the checkout) and GDExtension (`CLAUDE.md:9`; `docs/northstar/research/c_rewrite.md:9`,
"Phase 2 adds a thin GDExtension binding and deletes the pipe"). Neither is a defect — both are
explicitly forward-looking — but both are listed here so a reader of this model does not mistake
"named in the tech stack" for "exists."

## 15. The Factory's documented QA verb vocabulary does not match the shipped daemon

`docs/northstar/PLAN.md:143` ("QA architecture") lists an intended actor vocabulary including
`goto`. The shipped `autoload/qa_daemon.gd:183-212` (`_dispatch`) has no `goto`/`nav` case at all,
and the project's own QA profile documents this explicitly and prominently:
`~/Projects/agora/projects/ouroboros/qa.toml` ("IMPORTANT navigation rule: there is NO 'goto' or
'nav' verb in this game. This is not a web browser."). This is the one place in the model where
the general Factory design doc (which is intentionally project-agnostic, `PLAN.md:98`: "it must
serve a second project... not a fork") and this specific project's implementation are already known
and documented (by the project's own profile) to diverge — included here for completeness, not as
a new finding.
