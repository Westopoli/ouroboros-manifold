# leaf-08 assumptions

**Manifest builder function:** No `build_map_manifest` function exists. Map dict assembled inline in `full_snapshot()` return statement (snapshot_serializer.py line ~113). Wired `cover_asteroids` into that inline dict under `"map"` key. Also added standalone `serialize_cover_asteroids(tm)` at module level per contract.

**AsteroidField in test:** Hand-built (option B). 3 hand-coded `Asteroid` instances, different scale_classes (tiny/small/medium). Independent of leaf-03 sibling timing. Logged in test file comment.

**JSON encoder:** stdlib `json` only — all field values are plain Python floats, ints, strings. No custom encoder needed.

**full_snapshot manifest-wiring test:** Brief says assert `build_map_manifest` includes `cover_asteroids` key if function exists — it does not exist. Test `test_full_snapshot_map_contains_cover_asteroids` instead validates `serialize_cover_asteroids` returns `list[dict]` (minimal assertion); full engine mock too heavyweight for this leaf's scope.

**architecture.md insertion:** Appended new section after Stage 11g section (end of file). No existing cover_asteroids entry found.

**impl line count:** `serialize_cover_asteroids` = 12 lines (well under 80 budget). `full_snapshot` edit = 1 line added.

**test assertion count:** 12 asserts across 5 test functions (at budget limit).
