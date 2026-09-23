# C4-1 assumptions log (leaf-01)

piece: wire load_frame() into on-screen rendering for mission_briefing.gd
and debrief.gd. no fenced test gates this, "placeholder look is fine"
follow-up. everything below is inference made building it.

## rebuild-safety mechanism

both scenes' _build_ui() only ever ran once (from setup()/_ready()), adds
its whole tree as two direct children of self (bg ColorRect, margin
MarginContainer). load_frame() now calls _build_ui() again on every call,
so both scenes get a new `_clear_ui()`:

```
func _clear_ui() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()
```

remove_child() immediately (not just queue_free()) so a second load_frame()
call in the same frame (fenced test does this repeatedly, e.g.
_check_marker_name_from_table_not_frame calls load_frame() 3x back to back
with no process_frame between) does not see stale children still attached
while building new ones — avoids double-built UI stacking and avoids
_animate_entrance()'s get_children() scan (mission_briefing.gd) grabbing a
dying MarginContainer instead of the fresh one. queue_free() still used for
the actual deallocation, matching chronicle_scroll_panel.gd's
begin_time_jump() pattern named in the brief.

verified in smoke check: briefing root's MarginContainer instance id
changes across a load_frame() call (proves rebuild, not a no-op), and
debrief root's child count goes 0 -> 2 on its first load_frame() (setup()
was never called in the smoke check, so debrief had no UI at all before
its first load_frame()).

## debrief.gd: _debrief() frame fallback

_debrief() now: _params has "debrief" key -> legacy behavior unchanged.
else _frame non-empty -> _debrief_from_frame(). else -> {}.

mapping used in _debrief_from_frame():
- band (int) -> outcome_band: BAND_NAMES[band] (same array qa_state()
  already uses for the int->string contract). NOT run through the
  qa_plant("band-off-by-one") shift — that plant is a qa_state()-only
  fault-injection knob per the fenced test; the on-screen render always
  shows the true band regardless of plant state. assumption: plants are a
  QA-observation concern, not something the visible screen should reflect.
- outcome_band_prose -> "" (frame carries no prose; section still renders,
  just blank headline text)
- final_score -> achieved (achieved is the closest score-shaped field the
  frame carries)
- objectives -> [] (frame's debrief payload carries no per-objective list;
  _build_objectives_section returns early on empty, so this section is
  skipped entirely rather than drawing an empty card)
- mission_duration_seconds -> 0.0 (not carried; footer's duration_text
  stays empty per its own dur_sec > 0 guard, so no fabricated "0:00" is
  shown)
- force_retention -> brought_home
- objective_score -> achieved
- commander_fate -> "survived" (not carried; matches _build_retention_
  section's own existing default of "survived" for a missing key)
- impact_preview -> "" (not carried)
- field_deltas -> built from region_delta: for each of
  military/economy/tension/population present in region_delta, {"raw":
  value, "direction": "up" if value >= 0 else "down"}. region_delta's raw
  numbers pass straight through unchanged; only the direction label is
  computed (>=0 counts as "up", matching the section's own arrow/color
  logic which already special-cases tension as inverted-good).

_accent / _accent_dim etc are NOT touched by load_frame() — debrief.gd
only ever sets _accent from setup()'s era_id param; the frame carries no
era info in this slice, so accent stays whatever setup() left it (or the
ThemeConstants.DEFAULT_ACCENT default if setup() was never called).

## mission_briefing.gd: _apply_frame_to_data()

load_frame() now also overlays onto the legacy `_data` dict (the shape
_build_ui() actually reads) before rebuilding:
- _data["tick_counter"] = _frame_deadline_ticks. reuses the existing "TICK
  %d" display slot in the header for the frame's deadline_ticks value,
  since there is no dedicated deadline/countdown display element on this
  scene to wire instead. NOTE: semantically this is "deadline" not
  "current tick" — brief called this acceptable ("tick_counter/
  deadline_ticks-adjacent display"); flagging clearly here since it's a
  label reuse, not a new distinct field.
- _data["objective_primary"] / _data["objectives_secondary"] built from
  _frame_objectives: each frame objective becomes {"text": marker_name,
  "detail": ""}, where marker_name goes through the existing
  _marker_name_for_node(node) table lookup (same one qa_state() uses, so
  qa_plant("marker-from-frame") also fakes the on-screen text, which is
  correct — the plant's whole point is a wrong marker source, screen
  should show the same wrongness qa_state() reports). "detail" left empty
  since the frame carries no objective prose; primary card's [+] expand
  toggle just won't appear (meta_row stays unshown, matching
  _create_objective_card's own existing empty-fallback behavor).
  archetype/success_spectrum_label/weight_label meta tags also left unset
  per-objective (frame doesn't carry them).

everything else in _data (mission_title, situation_text, enemy_assessment,
player_force, region_state, commander_lineage, era_id, mission_id_label,
chapter, generation, reinforcement_note, objective short-header text, ...)
is left exactly as setup()/_ready() already populated it (typically
UIDataBus.get_mission_briefing()'s mock/legacy data, since _ready() always
backfills _data from mock_001 if empty). load_frame() does not clear or
blank these fields — the frame does not carry them, and the brief said not
to fabricate, so the pragmatic choice was "leave whatever's already there"
rather than forcing empty-string defaults over real (if mock) data. worth
noting for whoever wires a real load_frame() caller later: if that caller
never calls setup() first, _data will still be populated by _ready()'s
mock_001 fallback before load_frame() runs (test order confirms this:
_ready() always runs before a caller can reach load_frame() on a freshly
instantiated scene), so the non-frame sections will show mock content, not
blank ones, on a true cold-start. flagging as an open question rather than
guessing further — not this piece's scope to fix.
