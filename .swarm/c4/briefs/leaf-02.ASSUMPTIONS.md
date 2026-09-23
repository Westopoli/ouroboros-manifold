# leaf-02 assumptions

- `load_frame()` updates queryable state only, does NOT call `_build_ui()`
  / trigger a re-render. Basis: spec_lines 97-99 (C4.md) describe
  `load_frame` as "the rebind entry point, independent of `setup()`" and
  list only the four stored fields; `qa_state()` (spec_lines 100-105) is
  the only read contract given. Test file `_run_debrief_tests()`
  (tests/test_briefing_debrief.gd:108-139) never inspects rendered nodes
  after `load_frame` — only `root.qa_state()` output — so nothing forces a
  UI rebuild. Existing `_build_ui()` reads legacy `_params`/`_debrief()`
  shape (`outcome_band`, `objective_score`, etc.), which `load_frame`'s
  frame shape does not populate; wiring `load_frame` into `_build_ui()`
  would need a second translation layer not specced here (out of scope,
  additive-only, do not restructure `_build_ui()`/`setup()` per the
  brief). Left `_build_ui()`/`setup()` untouched; `load_frame` only writes
  `_frame`.

- `qa_state()` band lookup and the `band-off-by-one` plant read a `_frame`
  instance var populated by `load_frame`, not the raw `_params` dict —
  matches "independent of `setup()`" (C4.md line 97) and keeps the two
  entry points (legacy `setup()` vs. rebind `load_frame`) from sharing
  mutable state.

- `qa_plant("band-off-by-one")` sets a persistent flag (`_plant_band_off_by_one`)
  rather than mutating stored data once, so it stays active across
  subsequent `load_frame()` calls — test line 278 calls
  `root.load_frame(_debrief.duplicate(true))` again after activating the
  plant and still expects the shifted band (tests/test_briefing_debrief.gd:277-283).
