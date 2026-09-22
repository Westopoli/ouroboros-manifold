# leaf-01 assumptions

Piece C4, mission_briefing.gd rebind (`load_frame`/`qa_state`/`qa_plant`).

- **Node->marker name table contents.** Spec (spec_lines 60-72 of C4.md)
  and brief say table must cover node ids 3, 7, 12 (fixture ids) and must
  not be `str(node)` or `"Node %d" % node`. Exact strings not specified
  anywhere. Picked `{3: "Ridge Point", 7: "Forward Camp", 12: "Hollow
  Crossing"}` plus a `_FALLBACK_MARKER_NAME := "Unmarked Position"` for
  any node id outside the table (never exercised by the fenced test, but
  needed so `.get()` has a safe default instead of null propagating into
  JSON.stringify). Test line 202-203
  (`_check_marker_name_from_table_not_frame`) only asserts non-echo and
  stability, not specific content, so any readable set satisfies it.

- **`load_frame` does not trigger `_build_ui()`.** Test calls
  `root.load_frame(...)` then only reads `root.qa_state()` — never
  touches the rendered Control tree after `load_frame`. Spec_lines 62-67
  describe `load_frame` as "the rebind entry point, independent of
  setup()" and say it stores fields; it says nothing about re-rendering.
  Implemented `load_frame` as pure state storage (no call into
  `_build_ui()` or any node-tree mutation), consistent with "independent
  of setup()" and with keeping the diff purely additive per the brief's
  "do not remove or restructure setup()/_ready()/_build_ui()" instruction.
  If a later piece wants `load_frame` to also drive the legacy visual
  tree, that's a separate, explicitly-scoped change.

- **Objective ordering.** Spec/test don't require a specific order;
  `qa_state()`'s `objectives` list is built by iterating
  `_frame_objectives` in the order the frame provided them (frame order
  preserved, no re-sort). Test only checks size==3 and primary count==1,
  and separately finds "the" primary via `_primary_objective()` (first
  match), so order is not load-bearing.

- **`force` field.** Spec_lines 62-64 list `force` among stored fields;
  `qa_state()` per spec_lines 68-72 (and test) only ever reads
  `archetype`, `deadline_ticks`, `objectives`. Stored `_frame_force` for
  completeness/fidelity to "stores archetype, region, deadline_ticks,
  objectives[], force from the frame" but it is not surfaced in
  `qa_state()` since nothing in the test or the read spec section calls
  for it there. Same for `region` — stored as `_frame_region` but not
  read back anywhere (not in qa_state's field list at spec_lines 68-72).

- **`qa_plant("marker-from-frame")` is sticky across `load_frame` calls.**
  Test line 218-226 calls `qa_plant("marker-from-frame")` once, then
  calls `load_frame` again afterward and expects the plant still active.
  Implemented as a persistent `_plant_marker_from_frame` bool that
  `load_frame` never resets — only set, never cleared (no "undo plant"
  path exists in the test, so none was built).
