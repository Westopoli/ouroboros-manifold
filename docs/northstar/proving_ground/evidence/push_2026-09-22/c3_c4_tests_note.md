# C3/C4 tests note — chronicle scroll + briefing/debrief rebind (push 2026-09-22, wave-2 rows C3, C4)

Fenced tests wrote, red today, right reason. Impl (`load_frame`/`qa_state`/`qa_plant` on
`scenes/world/chronicle_scroll_panel.gd`, `scenes/mission_briefing/mission_briefing.gd`,
`scenes/debrief/debrief.gd`) is M3 job (pieces C3/C4, `docs/northstar/plans/push/pieces.toml`,
dep B8+T1 / B9+T1), not exist yet. Both scenes already exist and instantiate clean today
(confirmed live, autoloads DO load under `--script` SceneTree mode with `--path .` — checked
by hand before writing these, contra the mockup brief's "no autoloads under --script" note,
which is true only for whatever narrower invocation `scripts/mockup_verify.sh` uses). Red is
pinned on missing methods, zero parse error, zero crash.

## Files

- `tests/test_chronicle_scroll.gd` — instantiate `scenes/world/chronicle_scroll_panel.tscn`,
  feed it a snapshot plus a C transport v1 chronicle frame, check via `qa_state()`.
- `tests/test_briefing_debrief.gd` — instantiate `scenes/mission_briefing/mission_briefing.tscn`
  then `scenes/debrief/debrief.tscn` (two independent blocks, one scene's missing methods
  never blocks the other scene's checks), feed each a C frame, check via `qa_state()`.
- `tests/fixtures/chronicle_frame_seed11.json` — jump 100→150, 6 entries, refs into
  `tests/transport/fixtures/snapshot_seed1_tick10.json`'s regions/factions.
- `tests/fixtures/mission_frame_seed11.json` — archetype 2, region 7, deadline_ticks 380,
  1 primary + 2 secondary objectives (node ids 3, 7, 12).
- `tests/fixtures/debrief_frame_seed11.json` — band 2, achieved 0.8, brought_home 0.6,
  region_delta 4 fields.

Every fixture also embedded verbatim as a fallback builder inside its test file (house
pattern from `test_c_bridge.gd`/`test_galaxy_view.gd`): a missing/corrupt fixture file
degrades to the same shape instead of a second failure mode, real fixture edits need zero
test edit.

## Contract each scene must add (spec, since impl not exist yet)

### `scenes/world/chronicle_scroll_panel.gd` (piece C3)

- `set_snapshot(snapshot: Dictionary) -> void` — same raw C transport v1 snapshot shape
  `c_bridge.gd`/`galaxy_view.gd` take (docs/architecture.md "C transport v1"); gives the
  panel region existence + owner lookup so refs can be validated and "held by" rendered
  (R-068-04, not fenced here, but this is the hook it needs).
- `load_frame(frame: Dictionary) -> void` — the rebind entry point. Takes a C transport v1
  chronicle frame (`{"type":"chronicle","jump":{from_tick,to_tick},"entries":[{id,
  start_tick,end_tick,category,cluster_type,refs:{regions,factions},fragment,
  significance}]}`). No prose in the frame (C5 rule): `fragment` is a
  `simulation/library/chronicle/fragments.json` id the panel resolves to text, or renders
  `"[fragment <id>]"` when absent. Replaces `begin_time_jump()`/`queue_entry()`'s legacy
  `{entry_id, base_form, expanded_form, mentions[]}` input for the C-fed path; calling
  `load_frame` again on the same node must reset and re-render from scratch (idempotent,
  same frame in ⇒ same `hash` out, R-068-08).
- `qa_state() -> Dictionary`, JSON-safe, canonical from data never HUD labels: `hash`,
  `timing_ms {load}`, `regen_count`, `entries` (list of `{entry_id, fragment_id, text}`,
  one per surviving entry), `expanded_id` (empty/-1 when nothing expanded), `owners`
  (`{region_i: owner}` for exactly the regions referenced by the loaded frame's entries),
  `pace {word_interval_s, fade_s}` (R-069-02: must read 0.08 / 0.20 — the legacy
  `chronicle_entry.gd` cadence, 0.125 s cadence timer / ~8 s fade tween, does **not**
  match the bible; flagging, not fixing, per scope discipline — C3 must reconcile this),
  `dropped_entries` (count of entries dropped because every one of their refs was
  unresolved), `unresolved_refs` (count of individual bad region/faction ids across all
  entries, dropped or not).
- `qa_plant(id) -> bool`, `qa_click_entry(entry_id: int) -> void` (opens the expansion
  headless, since no mouse event fires under `--script`), `qa_dismiss() -> void` (closes
  it, resumes from state).
- `PLANTS := ["entries-dropped", "refs-unresolved"]` — new to this piece, not verbatim
  from the p7 mockup brief (its `PLANTS` are about the mockup's own printing/pause/morph
  concerns, a different scene entirely; these two are this rebind's own fault sites).
  Fault sites: `refs-unresolved` disables ref-existence checking (`unresolved_refs` reads
  0 even with a bad ref present); `entries-dropped` disables the drop-if-wholly-unresolved
  rule (`dropped_entries` reads 0, the broken entry shows up in `entries[]` instead).

`owners`, `unresolved_refs`, `entries[].fragment_id`/`.text` are not verbatim from any
brief — added here so the ref-validity and prose-source checks (both explicitly asked
for) have fields to read. `entries[]` deliberately does NOT carry the p7 mockup's
printing-progress fields (`printed_words`/`total_words`/`printed`/`expanded`) — this pass
is data plumbing (frame → resolved prose/refs), not the print-cadence animation; a later
visual pass can extend `entries[]` to match p7 exactly if the two panels are meant to
share one `qa_state()` shape.

Note: the task line asking for "every entry's refs name an existing region or faction
... (R-068-07)" — R-068-07 in the bible is actually the 40%-content-word dedup rule, not
a referential-integrity rule; keeping the citation as given (not mine to relabel), but
flagging the mismatch here for whoever reads this next. The dedup rule itself is
server-side text-similarity math that cannot run client-side once the frame carries no
prose, so it is out of scope for this rebind regardless.

### `scenes/mission_briefing/mission_briefing.gd` (piece C4)

- `load_frame(mission: Dictionary) -> void` — takes a C transport v1 mission frame
  (`{"type":"mission","archetype","region","deadline_ticks","objectives":[{i,kind,node,
  primary,radius,progress}],"force"}`). Replaces `setup(params)`'s
  `UIDataBus.get_mission_briefing(mission_id)` name-and-prose lookup for the C-fed path.
- `qa_state() -> Dictionary`: `hash`, `timing_ms {load}`, `regen_count`, `archetype` (int,
  straight from the frame), `deadline_ticks` (int, straight from the frame — R-076/R-079:
  qa_state is data, the no-digits-in-prose reading of R-079-04 is about rendered text, not
  this canonical field), `objectives` (list of `{i, kind, node, primary, marker_name}`).
  `marker_name` must come from a client-side node→name table keyed on `node` alone (a
  const Dictionary is enough for now), never be derived from the frame's own fields —
  proven by loading two frames that share a node id but differ in region/archetype/
  deadline and requiring the same `marker_name` both times.
- `qa_plant(id) -> bool`, `PLANTS := ["marker-from-frame"]` — fault site: marker_name
  becomes the literal `"Node %d" % node` (the frame-echoing bug the table exists to
  prevent) instead of the table lookup.

### `scenes/debrief/debrief.gd` (piece C4)

- `load_frame(debrief: Dictionary) -> void` — takes a C transport v1 debrief frame
  (`{"type":"debrief","band","achieved","brought_home","region_delta":{military,economy,
  tension,population}}`). Replaces `setup({"debrief": {...}})`'s
  `outcome_band`/`objective_score`/`force_retention`-named dict for the C-fed path.
- `qa_state() -> Dictionary`: `hash`, `timing_ms {load}`, `regen_count`, `band` (String,
  one of `total_failure/partial_failure/partial_success/strong_success/total_success`,
  mapped from the frame's int by index — that ordering is R-077-02's own, worst to best),
  `achieved_pct`/`brought_home_pct` (the frame's 0–1 floats ×100), `region_delta` (exactly
  the frame's 4 fields, unchanged). The band **threshold math** (R-077-01/02) already ran
  server-side (B9/`csrc/mission.c`, proven by `tests/csim`); this piece only owns the
  int→string display mapping, so that is all this test checks.
- `qa_plant(id) -> bool`, `PLANTS := ["band-off-by-one"]` — fault site: the int→string
  index shifts by +1 (clamped to `total_success`), so band 2 reads `strong_success`
  instead of `partial_success`.

## Assertions, per bible rule

`test_chronicle_scroll.gd`, 11 checks (`docs/bible/epics/E-09-chronicle.md`):
R-065-01 (6 entries), dropped_entries 0 clean, R-068-07-as-cited (refs resolve + `owners`
matches the snapshot fixture), prose-from-fragment-not-frame (frame has no text-like key;
every entry's placeholder is `"[fragment <id>]"` since all six fixture ids are
deliberately unassigned), R-069-02 (`pace` == 0.08/0.20), R-068-08 (`load_frame` twice ⇒
same hash), R-069-04 (`qa_click_entry`/`qa_dismiss` on `expanded_id`), 2 plants each
positive-control-then-plant (`refs-unresolved`, `entries-dropped`), `qa_plant("nope")`
false + both real ids true.

`test_briefing_debrief.gd`, 15 checks across two scenes
(`docs/bible/epics/E-10-missions.md`): archetype + deadline_ticks straight from frame
(R-076 referenced by R-079), objectives.size()==3 with exactly 1 primary (R-079-01..04,
cross-ref R-075-01), marker_name stable across two frames sharing a node id and not a raw
echo of it (positive control), 1 plant (`marker-from-frame`); band string per R-077-02's
ordering, achieved/brought_home as percentages, region_delta exactly 4 fields matching the
frame, 1 plant (`band-off-by-one`); `qa_plant("nope")` false + real id true on each scene.

## Logic check (mock, not committed)

Neither scene has the contract yet, so nothing here can go green against real code. Built
throwaway mock scripts outside the repo (`/tmp/.../scratchpad/mock_c3/`,
`.../mock_c4/`, never touched anything tracked) implementing the contract above, pointed
each test file's scene-loading line at a mock instead of the `.tscn`, ran both: 58/58 and
35/35 pass against a conformant mock. Deliberately broke the mock's ref/faction existence
check first (missed 2 of 58, a real mock bug, fixed) and separately broke marker-name to
literally echo `"Node %d" % node` (missed 1 of 35 — the exact regression the check exists
to catch) — confirms the checks are live detectors, not rubber stamps. Real test files in
`tests/` were never edited by this experiment; verified `SCENE_PATH`/`BRIEFING_SCENE_PATH`/
`DEBRIEF_SCENE_PATH` in the committed files still point at the real `.tscn` paths.

## Red proof

Ran `xvfb-run -a scripts/run_godot_tests.sh tests/test_chronicle_scroll.gd
tests/test_briefing_debrief.gd` on branch `main`, live checkout. Output:

```
=== Chronicle Scroll Test Results ===
PASS: 4  FAIL: 6
Failures:
  - chronicle_scroll_panel root missing method (piece C3 not attached yet): set_snapshot
  - chronicle_scroll_panel root missing method (piece C3 not attached yet): load_frame
  - chronicle_scroll_panel root missing method (piece C3 not attached yet): qa_state
  - chronicle_scroll_panel root missing method (piece C3 not attached yet): qa_plant
  - chronicle_scroll_panel root missing method (piece C3 not attached yet): qa_click_entry
  - chronicle_scroll_panel root missing method (piece C3 not attached yet): qa_dismiss
=== RED ===
FAIL: res://tests/test_chronicle_scroll.gd (exit 1)

=== Briefing/Debrief Test Results ===
PASS: 6  FAIL: 6
Failures:
  - mission_briefing root missing method (piece C4 not attached yet): load_frame
  - mission_briefing root missing method (piece C4 not attached yet): qa_state
  - mission_briefing root missing method (piece C4 not attached yet): qa_plant
  - debrief root missing method (piece C4 not attached yet): load_frame
  - debrief root missing method (piece C4 not attached yet): qa_state
  - debrief root missing method (piece C4 not attached yet): qa_plant
=== RED ===
FAIL: res://tests/test_briefing_debrief.gd (exit 1)
```

Both red on Godot's own `has_method()` returning false, zero parse error, zero unguarded
GDScript exception. Chronicle run shows 4 PASS (both fixtures loaded/built, scene
`load()`+`instantiate()`+2 frames succeeded) before hitting the missing methods.
Briefing/debrief shows 6 PASS (2 fixtures, then briefing scene load+instantiate,
then debrief scene load+instantiate) before hitting its 6 missing methods (3 per scene).
Confirmed by hand, before writing either test, that both scenes already instantiate clean
under `--headless --path . --script` (autoloads present, `_ready()` runs, no error) — so
today's red is purely "the contract method doesn't exist yet," never a scene that fails to
load. Both exit 1, both print the full PASS/FAIL block, no hang, no crash.

Console noise present in both runs, pre-existing, unrelated to these files:
`TacticalPerfLogger` mac-path warning, `SimBridge` spawns the legacy Python sim autoload
and its reader thread exits clean when nothing answers, renderer "leaked at exit" errors
from the dummy headless renderer tearing down — same as `c2_tests_note.md` already
recorded, every `--headless` script run in this repo prints these regardless of what the
script tests.

## Not tested here

Live pipe rebind (`attach/T1`) — M3 job once T1 lands; fallback builders here stay as the
pre-T1 stand-in, same as C2's note. The chronicle's map-side keyframe/border-morph
animation (R-069-01, R-069-03, R-069-05) — that lives in a different scene (the world
view's map viewport, not `chronicle_scroll_panel.tscn` itself) and is not this piece's
`owns_glob`. Full Situation/Objective/Assets three-section prose content (R-079-01's
"each from authored fragments") — the briefing's actual prose-assembly pass is a further
step past this rebind; this test only proves `objectives[]`/`archetype`/`deadline_ticks`
plumbing and the marker-name table. Visual/screenshot correctness — held for Westley's
day-2 briefing/tactical look per the plan, never a gate here.
