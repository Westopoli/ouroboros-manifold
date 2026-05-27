# Wave 4 (leaf-07 sequential) — Parent Assumption-Sweep

**Status:** active. Created 2026-05-27 (post-leaf-06 merge, pre-leaf-07 merge).

## Wave 4 context

Wave 4 = single-leaf wave (leaf-07 only). Created to serialize project.godot ownership after wave 3 leaves (leaf-06 touched [autoload] section; leaf-07 touches [application] section). Sub-wave numbering: wave-3 + wave-4 together form Wave 3 cascade (Pre-Zip BLOCKERs B2/B3/B5).

## leaf-07 ASSUMPTIONS review

Reviewed `.swarm/briefs/wave_3_pre_zip_wiring/leaf-07.ASSUMPTIONS.md` entries A1-A10:

- A1: Bash blocked — operational gap, not drift. Parent runs merge gates.
- A2: `game_root` resolution via `OS.get_executable_path().get_base_dir()` — matches U-8 (UNSTATED log).
- A3: Windows binary suffix via `OS.has_feature("windows")` — standard Godot platform detection. Matches U-8.
- A4: Mac suffix = none (binary name `ouroboros_sim`). PyInstaller convention.
- A5: sim/ subdir for release binary (`<game_root>/sim/ouroboros_sim`) — matches U-8 + leaf-01 PyInstaller spec COLLECT name.
- A6: project.godot preserves leaf-01 DebugOverlay + leaf-06 TutorialStateMachine. All 19 autoload entries confirmed present.
- A7: source-grep over behavioral per sibling MERGE_ASSUMPTIONS — same lesson as leaf-02/05/06.
- A8: `_spawn_sim(extra_args)` signature unchanged.
- A9: Other methods byte-identical to HEAD.
- A10: Traceability comments added (per CLAUDE.md convention).

## Cross-leaf drift check

- leaf-07 + leaf-06: both edit `project.godot`. Sequential waves (3 vs 4). leaf-06 owns autoload-section edit; leaf-07 owns application-section edit. Section-disjoint. Verified preserve list in leaf-07 ASSUMPTIONS A6.
- No fabricated symbols.
- No compounded inferences.

## Verdict

Wave 4 assumption-sweep CLEAN. Proceed to /swarm-merge leaf-07.
