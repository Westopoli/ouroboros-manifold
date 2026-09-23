# leaf-01 assumptions

- `CURRENT_SAVE_VERSION := 1`. Spec T2g.md and brief both say "a simple
  scene-local constant is correct here... not a specific value or
  source"; test only asserts `current_version >= 0` (test_load_game.gd
  line 149). Picked 1 as the first real save-format version.

- `label_text` exact wording on refusal: `"Chapter %d — build v%d, save
  v%d — incompatible"` (build = CURRENT_SAVE_VERSION, save = row's
  version). Test only requires the string contain both version numbers'
  plain int forms (test_load_game.gd lines 180-182); spec T2g.md gives
  `"...build v1, save v2..."` as an example. Non-refused rows get a
  plain `"Chapter %d"` label — test doesn't check non-refused label
  content, only that `refused == false` for the matching-version row.

- Row storage/rendering approach: `qa_set_bridge` calls
  `bridge.list_saves()` immediately and materializes a plain `Array` of
  `Dictionary` rows (`_bridge_rows`) computed once at call time, stored
  on the node, returned by `qa_state()`. No live Control nodes are built
  for this path (spec/test never inspect a rendered node tree for these
  rows, only `qa_state()`'s dict and `qa_load_slot()` — see
  `_check_version_mismatch_refused_R111_03` and
  `_check_unlimited_slots_thirty_rows_R111_04`, both read only from
  `qa_state()`). Kept fully independent of `_slot_list` /
  `_add_slot_card` (legacy UIDataBus path untouched).

- `qa_load_slot` stores no bridge reference beyond what `qa_set_bridge`
  already set; calls `_bridge.load(slot_id)` and returns it verbatim,
  per spec ("must not transform, wrap, or re-key that return value").
