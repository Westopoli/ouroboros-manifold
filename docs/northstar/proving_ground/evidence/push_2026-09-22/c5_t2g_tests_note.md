# C5/T2g tests note — minimal tactical view + save slots (push 2026-09-22, wave-2 rows C5, T2g)

Fenced tests wrote, red today, right reason. `scenes/tactical_c/**` (C5, dep
`attach/B10`, `attach/B12`, T1's tactical frame) does not exist at all yet.
`scenes/load_game/**` (T2g, dep `attach/T2c`, `attach/T1`) exists today as the
Python-era slot screen (`UIDataBus.get_save_slots()`); the C-bridge rebind has
not happened.

## Files

- `tests/test_tactical_view.gd` — instantiates `res://scenes/tactical_c/tactical_view.tscn`,
  feeds two hand-written C transport v1 tactical frames, checks via `qa_state()`
  and `issue_command()`.
- `tests/test_load_game.gd` — instantiates `res://scenes/load_game/load_game.tscn`,
  injects a `FakeBridge` test double standing in for `autoload/c_bridge.gd`
  (piece C2, also not built), checks the rendered slot rows and the load path.
- `tests/fixtures/tactical_frame_seed11.json` (tick 0) and
  `tests/fixtures/tactical_frame_seed11_tick10.json` (tick 10) — one scripted
  move, hand-written to the "tactical snapshot" shape in
  `docs/architecture.md` "C transport v1" (no C sim exists yet to generate
  them through ctypes, unlike `tests/transport/fixtures/snapshot_seed1_tick10.json`).

## Fixture design

12 units, two factions (0: ids 1-6, 1: ids 7-12), one of each of the six
`om_tier`-style role slots per side (`type` 0-5, matching R-082-01's row
order: Raider, Interceptor, Vanguard, Warden, Bombard, Bastion), tier 2, one
static `map` (`canvas` 4000, one cover circle, one obstacle, two nodes)
unchanged between the two frames.

- **Moved unit** (id 4, faction 0): tick0 `x=1500 y=2000 facing=1.5708`
  (matches `docs/architecture.md`'s own tactical-snapshot example unit id and
  `type`); tick10 `x=1575 y=2000 facing=0.0` — 75 wu along +x, y unchanged,
  facing turned to face travel (R-100-01). 75 wu over 10 ticks at 20 Hz
  (0.5 s) is 150 wu/s, R-082-01's Raider speed, though id4 is typed as the
  Interceptor slot here; the number is illustrative, not asserted.
- **Dead unit** (id 2, faction 0): present at tick0 (`hp=15`, already low),
  **entirely absent** from tick10's `units` array — R-136 placeholder is "the
  block is removed", not a lingering wreck, so death here is modelled as
  removal, not a visual-duration field.
- **Fog-hidden-but-alive unit** (id 10, faction 1): present in tick10's
  `units` array (alive, unmoved) but dropped from `visible["0"]` at tick10 —
  distinct from id 2's case, so the test can tell "gone from the world" apart
  from "alive but currently outside my faction's sensor range" (R-089-04's
  actual claim: no memory of last-seen positions, not merely "never seen").
- **Never-visible units** (ids 11, 12, faction 1): excluded from
  `visible["0"]` in both frames — the simple "always excluded" case, drawn
  from the task brief's "excluding two enemy units."
- `visible["1"]` (faction 1's own view) also excludes two of faction 0's
  units (5, 6) in both frames, for completeness against a future
  multi-viewpoint client; the test only renders from `local_faction = 0`
  (Round 1, single player), so this half is fixture-only, not asserted.

## Contract each file requires (spec, since impl does not exist yet)

`scenes/tactical_c/tactical_view.tscn` root:
- `load_frame(frame: Dictionary) -> void`
- `qa_state() -> Dictionary`, JSON-safe: `tick`, `canvas`, `units`
  `{id:{faction,type,tier,hp,layer,facing,state,x,y}}` (ground truth, every
  unit the loaded frame carries, regardless of visibility), `units_px`
  `{id:[x,y]}` (screen space, **only** for ids in the local faction's
  `visible` set — an id in `units` but missing from `units_px` has no node,
  proving R-089-04), `local_faction` (fixed 0 in Round 1), `selected`,
  `camera {x,y}`
- `qa_plant(id) -> bool` — PLANTS reused verbatim from the p4 and p8 mockup
  briefs where they still apply to a minimal renderer: `facing-fixed`,
  `camera-unbounded`. `select-all-exists` must return **false always**, never
  true even "planted" — R-105-04 forbids the command outright, so this scene
  must never wire that fault site up at all (the one plant id that is a
  permanent negative, not a togglable positive-control pair)
- `issue_command(cmd: Dictionary) -> Dictionary` — `{"kind":"move"|"attack_move"|
  "attack_target","unit_ids":[...],"x":..,"y":..}` or `{...,"target":id}` in,
  `{"type":"cmd","name":"command_move"|"command_attack_move"|"command_attack_target",
  ...same fields...}` out; never actually sent
- `qa_box_select(x0,y0,x1,y1) -> Array` — screen-space rect select, sets and
  returns the newly selected ids
- `qa_pan(x,y) -> void` — pans/recentres the camera, clamped to the loaded
  frame's `map.canvas` (R-103-02)

`scenes/load_game/load_game.tscn` root:
- `qa_set_bridge(bridge) -> void` — bridge is any object with `list_saves()
  -> Array` and `load(slot_id: String) -> Dictionary`; replaces the rendered
  slot list immediately from `bridge.list_saves()` (this is the literal
  "slot list comes from `c_bridge.list_saves()`" the brief names — a fake
  double stands in for `autoload/c_bridge.gd`, C2's file, not T2g's, so this
  test's red stays pinned on T2g and does not also require C2 to exist)
- `qa_state() -> Dictionary`, JSON-safe: `slot_count`, `current_version`
  (the build's save-format version, for the R-111-03 comparison),
  `has_save_button`, `rows` `[{slot, tick, chapter, version, refused,
  label_text}]` — one row per `list_saves()` entry
- `qa_load_slot(slot_id) -> Dictionary` — drives the same load action a click
  on that slot's card would; calls the bridge's `load(slot_id)` and returns
  its result verbatim

`list_saves()`'s contracted shape is exactly the brief's `{slot, tick,
chapter, version}`; this test's fixtures add an unlisted `checksum` field
for their own bookkeeping only, per the C transport v1 rule "a client
ignores keys it does not know" — R-111-02 needs some way to compare "the
slot's recorded checksum" against the post-load snapshot's checksum without
a second, uncontracted accessor, and this is the minimal way to get there
without inventing one.

## Assertions, per bible rule

`test_tactical_view.gd`, 15 checks (57 assertions once satisfied — see
"Reference-stub proof" below):

- `qa_state()` survives `JSON.stringify`
- `units` carries all 12 units (ground truth) regardless of visibility;
  `units_px` entries fall inside the viewport
- R-089-04: drawn ids at tick0 equal `visible["0"]` exactly (10 of 12); ids
  11, 12 (never visible) have no node
- R-100-01: unit 4's facing changes between tick0 and tick10; its screen
  position moves along one dominant axis (a pure +x, y-unchanged move under a
  fixed, non-rotated top-down camera, R-103-03, should not read as diagonal)
- unit 2 is gone from `units` entirely at tick10 (R-136 placeholder); unit 10
  is still in `units` but has no node at tick10 (R-089-04's actual "no
  memory" case, distinct from unit 2's "no longer exists" case)
- `issue_command` for move (R-096-01), attack-move (R-096-02), attack-target
  (R-096-04): `type`, `name`, `unit_ids`, and `x`/`y` or `target` all correct
- R-105-01: a box drawn tightly around units 1 and 3's `units_px` selects
  exactly `{1, 3}`; a move issued right after carries both ids
- R-103-02: panning to the canvas centre lands there (positive control);
  panning far past the edge clamps inside `[0, canvas]`, not passed through
  raw
- PLANT `camera-unbounded`: the same edge-pan now exceeds the canvas
- PLANT `facing-fixed`: the clean run already proved unit 4's facing differs
  across the two frames; under the plant, reloading both no longer
  reproduces that difference
- R-105-04: `qa_plant("select-all-exists")` is false unconditionally
- `qa_plant("nope")` false, both real ids (`facing-fixed`, `camera-unbounded`)
  true

`test_load_game.gd`, 6 checks:

- `qa_state()` survives `JSON.stringify`
- R-111-04: `has_save_button` is false; a tree-walk finds no button whose
  text contains "save" — with a positive control (the same tree-walk does
  find the BACK button that exists today)
- `current_version` is a non-negative int
- R-111-03: two fixture slots, one matching `current_version` and one
  `current_version + 1`; the matching one is not refused, the mismatched one
  is refused and its `label_text` names both version numbers
- R-111-02: a fixture slot carries a `checksum`; `qa_load_slot` calls the
  bridge's `load` exactly once with that slot id, and the returned
  post-load snapshot's `checksum` equals the slot's recorded one
- R-111-04 (unlimited slots): a 30-entry fixture list renders `slot_count ==
  30` and 30 `rows`

## Reference-stub proof (both files are actually satisfiable, not just red)

Per the "verify satisfiable before trusting a red test" discipline, each
file was proved green against a throwaway reference implementation before
being left red for real — built, run, then fully deleted (never committed;
`git status --short` before and after was compared to confirm nothing of
the throwaway scenes survived).

- `test_tactical_view.gd`: a temporary `scenes/tactical_c/tactical_view.tscn`
  + `.gd` stub implementing the contract above scored **57/57 PASS**. Two
  real bugs in the test file itself were caught and fixed this way, not
  guessed:
  1. GDScript's `Array.has()`/`in` compares element type strictly (`1 in
     [1.0]` is `false`, confirmed with a throwaway probe script), while
     JSON always parses whole numbers as floats and scalar `==` is
     permissive (`1 == 1.0` is `true`, `[1] == [1.0]` is `false`). Every
     id-set comparison in the file (`_same_set`) now normalizes both sides
     to `int` internally rather than trusting the caller; the three
     `issue_command` unit_ids checks moved from raw `==` to a new
     `_ints_eq_ordered` helper for the same reason.
  2. `"%s" % an_array_with_two_elements` in GDScript tries to unpack the
     array as two substitution arguments against one `%s`, which throws
     `not all arguments converted during string formatting`, not a
     GDScript-level type error — three failure-message format strings
     (`unit_ids`) needed `str(...)` around the array first.
  3. (Non-bug, environment fact) `get_root().size` under `--headless` reads
     `(100, 100)` regardless of `project.godot`'s configured 1920x1080; the
     viewport-bounds check's fallback threshold moved from `<= 0` to `<
     200` so it actually engages the 1920x1080 fallback instead of
     asserting units_px against a meaningless 100x100 box. `test_galaxy_view.gd`
     has the same `<= 0` fallback condition and would likely hit the same
     issue once `scenes/galaxy/galaxy_view.tscn` exists to instantiate — not
     mine to fix, flagging for M3/M0.
  A negative control (temporarily making the stub draw every unit regardless
  of `visible`) correctly failed 4 of the R-089-04-related assertions,
  confirming the check is not vacuous.
- `test_load_game.gd`: a temporary `scenes/load_game/_scratch_load_stub.tscn`
  + `.gd` implementing the contract scored **23/23 PASS**. One real bug
  found: `_ready()` on a node added via `add_child()` in this `--script`
  SceneTree harness is **not** synchronous (confirmed with a throwaway probe:
  a child's own children were empty immediately after `add_child`, present
  one `process_frame` later) — `test_load_game.gd` was missing the
  `await process_frame` (twice) that `test_galaxy_view.gd` already has after
  its own `add_child`; added. Three negative controls confirmed the checks
  are not vacuous: an added "SAVE" button was caught by the R-111-04 check;
  a `qa_load_slot` that ignores the bridge and returns a wrong checksum
  failed both the "bridge was called" and "checksum matches" assertions.

## Red proof (real files, live checkout, branch `main`)

```
$ xvfb-run -a scripts/run_godot_tests.sh tests/test_tactical_view.gd tests/test_load_game.gd
=== Running res://tests/test_tactical_view.gd (timeout 300s) ===
...
ERROR: Cannot open file 'res://scenes/tactical_c/tactical_view.tscn'.
ERROR: Failed loading resource: res://scenes/tactical_c/tactical_view.tscn.

=== Tactical View Test Results ===
PASS: 3  FAIL: 1
Failures:
  - cannot load res://scenes/tactical_c/tactical_view.tscn (piece C5 not attached yet)
=== RED ===
FAIL: res://tests/test_tactical_view.gd (exit 1)

=== Running res://tests/test_load_game.gd (timeout 300s) ===
...
=== Load Game Test Results ===
PASS: 3  FAIL: 3
Failures:
  - load_game root missing method (T2g rebind not done): qa_set_bridge
  - load_game root missing method (T2g rebind not done): qa_state
  - load_game root missing method (T2g rebind not done): qa_load_slot
=== RED ===
FAIL: res://tests/test_load_game.gd (exit 1)
```

Combined runner exit code 1. `test_tactical_view.gd`'s 3 passes are the two
fixture files parsing and the tick0 fixture carrying exactly 12 units — both
proven before the scene-load gate, so the failure is pinned on the missing
scene, not a fixture bug. `test_load_game.gd`'s 3 passes are the scene file
existing, loading, and instantiating (today's Python-era scene is real and
parses clean) — the failure is pinned on the three missing rebind methods,
not on the scene being absent or broken. Zero parse errors in either test
file, zero unguarded GDScript exception, every `load()`/`has_method()` call
null-checked before use, matching the C2/T2 tests notes' pattern.

Console noise present in both runs, pre-existing, unrelated to these two
files (same as `c2_tests_note.md` already documents): `TacticalPerfLogger`
mac-path warning on every autoload boot; `SimBridge` spawning the legacy
Python sim autoload with its reader thread exiting clean when nothing
answers; renderer "leaked at exit" / `PagedAllocator` errors from the dummy
headless renderer tearing down on every `--headless` script run in this repo.

## Q- candidates (full text in each rule's citation above)

- Screen-direction convention for a pure single-axis world move: (a) assert
  only "one dominant screen axis changed" (chosen here — camera-orientation
  agnostic, still fails under a genuinely broken or rotated projection); (b)
  assert an exact sign (world +x maps to screen +x); (c) assert against the
  raw world `x`/`y` in `qa_state().units` instead of `units_px` and treat
  screen projection as untested. (a) holds regardless of which axis
  correspondence C5 picks for the fixed top-down camera (R-103-03).
- `current_version`'s source: (a) a scene-local constant (assumed here,
  simplest, matches the test's black-box style); (b) `om_abi_version()`
  (2, from the pipe hello) plumbed through `c_bridge`; (c) a separate
  save-format version distinct from the wire ABI. The test only requires
  *some* non-negative int exposed consistently; R-111-03 holds under any of
  the three.
- Dead-unit modelling: (a) full removal from `units` (assumed here, matches
  the brief's literal "block removed" for the R-136 placeholder); (b) `hp<=0`
  kept in `units` with a wreck flag, closer to the eventual full R-136
  visual. (a) is simpler and is what this file's fixtures encode; a future
  epic-level death-visual piece would need its own fixtures under (b),
  not these.

## Not tested here

R-105-02/03 (control-group bind/recall/Tab cycling) and R-105-06 (layer
narrowing) — S-105's full selection depth is the p8 HUD mockup's job on its
own toy scene; this minimal tactical view only needs box-select-then-move to
prove the selection-to-command pipeline exists (R-105-01), per the task
brief's explicit list. `pass-through`/`instant-fight` (no collision or
damage sim in a pure renderer), `silhouettes-same` (this view draws uniform
blocks, not per-role silhouettes, so the distinction the plant tests does
not exist here), `no-death-visual` (R-136 placeholder for this minimal view
*is* "block removed with no visual," so there is no visual to disable — see
the dead-unit Q- candidate above), `box-one-layer`/`group-shared` (single
layer, no control groups in this minimal view), `clock-wallclock`/
`narrow-moves-focus` (no HUD clock or layer narrowing here) — none of these
p4/p8 plant ids apply to C5's scope; forcing them in would mean inventing
mechanics the task brief does not ask for. R-111-01 (autosave fires at
mission start/end/jump end) — a client-side trigger with no load_game.tscn
surface to assert against; `t2_tests_note.md` already flags this same rule
as "not tested" for the same reason. Live rebind to the real
`autoload/c_bridge.gd` once C2 attaches, and to the real pipe once T1
attaches — both pieces' own job at attach time, per the plan's attach-order
gates (steps 7 and 9).
