# C2 tests note — galaxy view over C snapshot + bridge (push 2026-09-22, wave-1 row C2)

Fenced tests wrote, red today, right reason. Impl `autoload/c_bridge.gd` +
`scenes/galaxy/galaxy_view.tscn` is M3 job (piece C2, `docs/northstar/plans/push/pieces.toml`,
dep `freeze`), not exist yet.

## Files

- `tests/test_c_bridge.gd` — loads `res://autoload/c_bridge.gd` plain script
  (not project autoload), instantiate direct, exercise contract.
- `tests/test_galaxy_view.gd` — instantiate `res://scenes/galaxy/galaxy_view.tscn`,
  feed C transport v1 snapshot, check via `qa_state()`.

## Fixture status

`tests/transport/fixtures/snapshot_seed1_tick10.json` not landed yet (F4/T1
job, per `docs/architecture.md` "C transport v1"). Both files fall back:
build minimal valid snapshot matching
`docs/northstar/spec_factory/transport/snapshot.schema.json` (60 regions, 59
edges a<b, 3 factions), write to a `user://` temp path, run same assertions
against it. Expected values (owner_of(0), checksum, edge count) come from
whatever file actually loaded, never hardcoded — real fixture drops in
later, zero test edit needed. `test_galaxy_view.gd` tries the fixture
through `c_bridge.gd` first (regions()/edges()/checksum()) so "feeds it the
bridge's snapshot" is literal once the bridge exists; degrades to a direct
JSON parse while the bridge is still missing, so this file's red stays
pinned on the galaxy scene, not doubled up on the bridge too.

## Contract each file requires (spec, since impl not exist yet)

`autoload/c_bridge.gd` (loaded plain, never as the project autoload):
- `load_snapshot_file(path: String) -> bool` — false (or `{ok:false,...}`) on
  a bad snapshot, never crash
- `regions() -> Array`
- `owner_of(i: int) -> int`
- `checksum() -> int`
- `edges() -> Array`

`scenes/galaxy/galaxy_view.tscn` root:
- `set_snapshot(snapshot: Dictionary) -> void` — raw snapshot dict
  (regions/edges/checksum), same shape `c_bridge` hands back
- `qa_state() -> Dictionary`, JSON-safe: `system_count`, `owners`
  `{region_i:owner}`, `edge_counts` `{om_edge_type_int:count}`, `systems_px`
  `{region_i:[x,y]}`, `region_colours` `{region_i:[r,g,b,a]}`,
  `owner_colours` `{owner_id:[r,g,b,a]}`, `band`, `distance`,
  `pick_radius_px`, `edges_3d`, `hash`, `seed`
- `qa_plant(id) -> bool`, `qa_seed(n)`, `qa_camera(distance,
  target_system_id)` — the mockup contract, `2026-09-22-mockup-qa-harness.md`
- `PLANTS` reused verbatim from `2026-09-22-p1-galaxy-mockup.md` (lines
  ~82-84): `seed-ignored`, `owner-colour-flat`, `edges-2d-overlay`,
  `pick-radius-zero`, `bands-frozen`, `conquest-no-recolour`

`edges_3d`, `pick_radius_px`, `owner_colours` are not verbatim from any
brief — added here so the last three plants have a field to flip. Flagging
for M3, not guessing a real formula: colour formula itself untested, only
self-consistency (region colour equals its own owner's palette entry).

## Assertions, per bible rule (`docs/bible/epics/E-16-client-camera-hud-and-world-view.md`)

`test_galaxy_view.gd`, 14 checks:
- qa_state() survives JSON.stringify (mockup contract)
- S-106/R-106-01: `system_count == 60`
- S-106/R-106-02: `owners` 60 entries match the snapshot
- S-106/R-106-02: `edge_counts` (Dictionary) sums to the snapshot's edge count
- S-106/R-106-01: `systems_px` 60 entries, inside the viewport (one drawn
  point per region)
- S-106/R-106-01,02: region colour equals its owner's palette colour
  (self-consistency, not a fixed formula)
- S-107/C5: `qa_seed(11)` twice gives an equal hash, `qa_seed(12)` differs
  (positions are client-side per the C5 no-positions rule, still must be
  deterministic per the determinism contract)
- 6 plant checks, each positive-control-then-plant: `seed-ignored` (hash
  stops changing with seed), `owner-colour-flat` (region_colours collapse to
  one), `edges-2d-overlay` (`edges_3d` flips false), `pick-radius-zero` /
  R-107-01 (`pick_radius_px` to 0), `bands-frozen` / R-106-03 (`band` frozen
  at distance 20), `conquest-no-recolour` / R-106-02,04 (region colour stops
  following an owner change on a re-fed snapshot)
- `qa_plant("nope")` false, all 6 real ids true

`test_c_bridge.gd`, checks: method presence x5, `regions().size()==60`,
`owner_of(0)` matches, `checksum()` matches, `edges().size()` matches,
missing-`regions` snapshot rejected, not crashed.

## Red proof

Ran `xvfb-run -a scripts/run_godot_tests.sh tests/test_c_bridge.gd
tests/test_galaxy_view.gd` on branch `main`, live checkout. Output:

```
=== C Bridge Test Results ===
PASS: 0  FAIL: 1
Failures:
  - c_bridge script failed to load (missing or parse error): res://autoload/c_bridge.gd
=== RED ===
FAIL: res://tests/test_c_bridge.gd (exit 1)

=== Galaxy View Test Results ===
PASS: 1  FAIL: 1
Failures:
  - cannot load res://scenes/galaxy/galaxy_view.tscn (piece C2 not attached yet)
=== RED ===
FAIL: res://tests/test_galaxy_view.gd (exit 1)
```

Both red on Godot's own `load()` failure (`ERROR: Failed loading resource:
res://autoload/c_bridge.gd`, `... res://scenes/galaxy/galaxy_view.tscn`),
zero parse error in either test file, zero unguarded GDScript exception —
every `load()`/`has_method()` call is null-checked before use. Galaxy view
run shows PASS 1 (the fallback-snapshot build succeeded) before hitting the
missing scene at the next line. Both exit 1, both print the full PASS/FAIL
block, no hang, no crash.

Console noise present in both runs, pre-existing, unrelated to these two
files: `TacticalPerfLogger` mac-path warning
(`autoload/tactical_bridge.gd:57` via `scenes/tactical/perf_logger.gd:23`,
fires on every autoload boot); `SimBridge` spawns the legacy Python sim
autoload and its reader thread exits clean when nothing answers; renderer
"leaked at exit" / `PagedAllocator` errors from the dummy headless renderer
tearing down, which every `--headless` script run in this repo prints
regardless of what the script tests.

## Loose end

`docs/northstar/plans/push/pieces.toml`'s C2 row lists only
`tests/test_galaxy_view.gd` under `acceptance`, not `tests/test_c_bridge.gd`,
even though C2 `owns` `autoload/c_bridge.gd` directly. Not mine to edit
(`pieces.toml` is outside my three-file scope); flagging for M0/M3 so the
gate actually runs both.

## Not tested here

Live pipe rebind (`attach/T1`) — M3 job once T1 lands; the fallback path
here stays as the pre-T1 stand-in per the plan's "fixture is the client
pieces' stand-in until T1 attaches." Visual band/colour correctness beyond
self-consistency is held for Westley's day-1-evening look per the plan's
"Visual claims are filed held" rule, never a gate.
