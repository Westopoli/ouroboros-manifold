# leaf-01 assumptions — autoload/c_bridge.gd

Checked `.swarm/c2/briefs/leaf-02.ASSUMPTIONS.md` first: not present yet
(leaf-02 hadn't finished/logged). No cross-leaf shape info to reconcile
against; proceeded on `tests/test_c_bridge.gd` + `C2.md` spec_lines 51-72
alone.

- **`load_snapshot_file` return shape: plain `bool`, not `{ok:...}`
  Dictionary.** Spec (C2.md:66-67) and test (test_c_bridge.gd:71,108) both
  accept either. Chose bare `bool` — simplest thing that satisfies
  `bool(ok)` on success (test_c_bridge.gd:71) and the `(result == false) or
  (result is Dictionary and not bool(result.get("ok", true)))` check on
  failure (test_c_bridge.gd:108). No caller in this piece's scope needs
  extra fields on a Dictionary result, so no reason to add one.

- **Parse-failure handling: `FileAccess.open` null check, then
  `JSON.parse_string` result type check, then `"regions"` key check — three
  guarded early returns, no try/catch (GDScript has none).** Test only
  exercises the missing-`"regions"` path (test_c_bridge.gd:98-113,
  `_check_missing_regions_rejected`), but spec text says "or any
  unparseable file" (C2.md:37-38) and the test file header itself says
  "never crashes or throws an unhandled error" — so I also guard a missing
  file and a non-Dictionary/malformed JSON parse (`JSON.parse_string`
  returns `null` on a parse error in Godot 4), not just the missing key.

- **`owner_of(i)` not found: returns `-1`, not a crash/null.** Not directly
  tested (fixture always has region 0), but `-1` matches the fallback
  fixture's actual owner-id domain (`(i % 3) - 1` in
  test_c_bridge.gd:142, so -1/0/1 are real owner ids in-band) less safely
  than an out-of-band sentinel would; chose -1 anyway since
  `docs/architecture.md` "C transport v1" doesn't define an owner sentinel
  and the test never calls `owner_of` on a missing index — flagging this as
  a soft guess, not spec-derived, in case a later piece calls `owner_of` on
  an out-of-range i and needs a distinguishable "not found."

- **`checksum()` on an unloaded/empty snapshot: returns `-1`.** Same
  reasoning — never exercised by the test (checksum is always read after a
  successful load), chose -1 as an obvious sentinel, not spec-derived.

- **Base class: `RefCounted`, not `Node`/`Object`.** Test does
  `(script as GDScript).new()` with no `_ready`/tree dependency
  (test_c_bridge.gd:53), and spec says "plain script... never as a project
  autoload" (C2.md:62). `RefCounted` is the lightest correct base for a
  script instantiated standalone and never added to the scene tree.
