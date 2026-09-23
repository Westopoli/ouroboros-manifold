# T2g — save slots rebind

Manager: M3. Piece id `T2g`, `depends_on = ["T2c", "T1"]` — built fixture-first
now (T2c isn't built yet, no live bridge exists — the test injects a fake
bridge double, so this piece is genuinely satisfiable without T2c or T1
being real). Owns `scenes/load_game/**` (existing scene, additive rebind —
same pattern as C4, not a fresh scene like C5).

Single leaf.

## Source of truth (read every one of these before writing code)

- **Fenced acceptance test, read in full — the literal contract**:
  `tests/test_load_game.gd` (238 lines, 6 checks). Every field name, every
  threshold in this spec is taken directly from that file, including its
  own `FakeBridge` inner class (a `RefCounted` with `list_saves() -> Array`
  and `load(slot_id: String) -> Dictionary`) that stands in for
  `autoload/c_bridge.gd` (piece C2 — not what this test exercises; the
  wiring shape is what's tested, C2's real bridge rebinds later at
  attach). If this spec and the test ever disagree, the test wins.
- `docs/northstar/proving_ground/evidence/push_2026-09-22/c5_t2g_tests_note.md`
  — the "### `scenes/load_game/load_game.tscn` root" section is this
  spec's direct source. Its Q-candidates section flags `current_version`'s
  source as genuinely open (a scene-local constant is the simplest valid
  choice and is what this spec directs — see below).
- `scenes/load_game/load_game.gd` (232 lines, read in full before editing
  — additive change only). Today it renders slots from the legacy
  `UIDataBus.get_save_slots()` path (`_refresh_slots()`,
  `_add_slot_card()`) with a different field shape (`name`,
  `era_accent_color`, `playtime_seconds`, `era_name`, `chapter`,
  `generation`, `id`) than this rebind's contract. Do not remove the
  legacy path (`_ready()` still calls `_build_ui()` → `_refresh_slots()`
  on its own at scene load, unrelated to this rebind) — this is additive,
  a second, independent rendering path triggered by `qa_set_bridge`.
  Already has a working BACK button and no SAVE button (matches R-111-04
  naturally, nothing to change there) and a delete-confirm overlay
  (untouched, legacy-path-only, this rebind adds no delete flow).

## What to build

- `qa_set_bridge(bridge) -> void` — stores the injected bridge (duck-typed:
  anything with `list_saves()` and `load(slot_id)`), immediately calls
  `bridge.list_saves()` and rebuilds the rendered row list from it,
  replacing whatever was shown before (independent of the legacy
  `UIDataBus`-driven cards — this is a second, parallel render path the
  test's own `_root` instance uses, triggered only when `qa_set_bridge` is
  called).
- `qa_state() -> Dictionary`, JSON-safe: `slot_count` (int, = the bridge's
  row count), `current_version` (int, non-negative — **a simple
  scene-local constant is correct here**, e.g. `const CURRENT_SAVE_VERSION
  := 1`; the test only requires *some* consistent non-negative int, not a
  specific value or source), `has_save_button` (bool, always `false` — this
  screen never offers a manual save, R-111-04), `rows` (list of
  `{slot, tick, chapter, version, refused, label_text}`, one per
  `bridge.list_saves()` entry — `refused` is `true` when that row's
  `version` doesn't equal `current_version`; `label_text` is the actual
  rendered row text and, when `refused`, **must contain both version
  numbers** as their plain int string forms, e.g. `"...build v1, save
  v2..."`).
- `qa_load_slot(slot_id: String) -> Dictionary` — calls the injected
  bridge's `load(slot_id)` exactly once and returns its result verbatim
  (the test's own `FakeBridge.load()` returns a canned snapshot-shaped
  dict with a `checksum` field; this method must not transform, wrap, or
  re-key that return value).

`list_saves()`'s contracted shape is `{slot, tick, chapter, version}`; a
row may also carry an unlisted `checksum` field (only in the fenced
test's own fixtures, for its own R-111-02 bookkeeping) — per the C
transport v1 rule "a client ignores keys it does not know," don't assume
every row has `checksum`, just pass through whatever `load()` returns for
`qa_load_slot`.

## Acceptance

`scripts/run_godot_tests.sh tests/test_load_game.gd` — prints
`=== GREEN ===`, exit 0, all 6 checks pass (JSON-safety, no-save-button
positive-controlled via the BACK button, current_version presence,
version-mismatch refusal with a two-version label, load-calls-bridge +
checksum match, unlimited 30-slot rendering).

## Ownership

`scenes/load_game/load_game.gd` only (no new files needed — additive to
the existing script). Does not touch `scenes/load_game/load_game.tscn`,
`csrc/**`, `docs/**`, `tests/**`, `Makefile`, `project.godot`, or any
other scene.
