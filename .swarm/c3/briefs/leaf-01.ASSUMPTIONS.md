# leaf-01 (C3) assumptions

## Fragment library key shape
`simulation/library/chronicle/fragments.json` is a JSON **Array** of
`{id: String, text: String, ...}` (e.g. `"LT_O_001"`), not a dict keyed by
id. Lookup: build `{str(id): text}` once, then key by `str(fragment_id)`.
Fixture fragment ids (910201..910206, ints) never match any library id
(all library ids are non-numeric strings like `LT_O_001`/`CM_C_001`),
confirmed by direct read (no id in the 380-entry library is a digit
string) — so the `"[fragment <id>]"` fallback fires for all 6 fixture
entries, per spec's own claim (C3.md lines 34-36) and test
`_check_prose_from_fragment_not_frame`.

## refs-unresolved plant vs. the drop decision (the one non-obvious call)
Spec/brief say `refs-unresolved` "disables ref-existence checking
entirely (unresolved_refs reads 0)" and separately that
`entries-dropped` "disables the drop-if-wholly-unresolved rule". Taken
literally as one shared checking mechanism, these two plants interact
across the test sequence: `_check_plant_refs_unresolved()` runs BEFORE
`_check_plant_entries_dropped()` and does **not** un-plant itself
afterward (test file has no unplant method). `_check_plant_entries_dropped()`
starts with a "clean" positive control (before touching the
entries-dropped plant) that still expects `dropped_entries == 1` for
`_bad_entry_frame()`'s wholly-bad 7th entry — but by that point
`refs-unresolved` is already active from the previous check.

If a single "ref checking enabled" flag gated both the reported
`unresolved_refs` counter AND the wholly-unresolved drop test, that
positive control would fail (bad refs would look valid, nothing would be
"wholly unresolved", so nothing would drop). So I split it: ref
*validity* (real_bad_refs, used only to decide wholly_unresolved / the
drop) is always computed for real, unaffected by `refs-unresolved`; only
the *reported* `unresolved_refs` total is zeroed when that plant is
active. This is the only way both `_check_plant_refs_unresolved` (tests
the reported counter only, against `_bad_ref_frame()` where the entry is
never wholly bad so drop never triggers either way) and
`_check_plant_entries_dropped`'s positive control (tests the drop only,
run with refs-unresolved already active) pass together. Cited:
tests/test_chronicle_scroll.gd lines 220-270 (test execution order in
`_run_tests()`, lines 90-100, is what makes this order-dependent).

## Hash formula
Used Godot's built-in global `hash(Variant) -> int` directly on the
`frame` Dictionary passed into `load_frame`. Verified empirically
(scratch script) that `hash()` on two separately-constructed Dictionaries
with identical structure/values returns the same int, and that
`JSON.stringify` on a Dictionary with non-string (int) keys auto-converts
them to string keys without erroring — both load-bearing for
`_check_hash_determinism_R068_08` and `_check_qa_state_json_safe`. No
stated formula in spec/test beyond "deterministic... equal, non-null"
(test line 181-186), so any stable content hash satisfies the contract.

## `entries[]` ordering
Not specified by the test (`_check_entries_count_R065_01` only checks
`.size()`; `_check_prose_from_fragment_not_frame` looks each entry up by
`entry_id` via a dict, order-independent). Built in frame `entries[]`
source order — simplest, no reason to reorder.

## `owners` scope on dropped entries
Per spec text and `_distinct_region_refs(frame)` (test lines 279-286),
which iterates ALL entries in the frame including ones that get dropped.
Implemented by populating `_qa_owners` for every region ref encountered
in the per-entry ref-validation loop, before the wholly-unresolved/drop
decision short-circuits (`continue`) — so a dropped entry's region refs
still land in `owners`. Only exercised by the clean fixture in the
fenced test (no fixture entry is ever wholly dropped in the base run), but
implemented to match the documented rule regardless.

## `expanded_id` "empty" representation
Used `int -1` as the empty state (both the default column value and what
`qa_dismiss()` resets to), since the test's own accepted-forms check
(`_check_expanded_id_contract_R069_04`, lines 189-203) explicitly allows
`int(before) == -1` as one of three valid empty encodings.
