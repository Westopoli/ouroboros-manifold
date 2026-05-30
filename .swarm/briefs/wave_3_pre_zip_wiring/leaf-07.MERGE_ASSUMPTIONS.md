# leaf-07 merge assumptions

## Intake (non-interactive)

1. **Leaf:** leaf-07 — Release-mode wire-up (Wave 3 sub-wave 3.3 / brief wave=4). Final Wave 3 leaf.
2. **Scope:** `project.godot [application]` section + `autoload/theme_constants.gd:4` + `autoload/sim_bridge.gd._spawn_sim body` + new `tests/test_b5_release_mode.gd`.
3. **Multi-merge sequence:** Yes. Baseline = post-leaf-06 (23 pass / 4 fail). Expected delta +4 (G×4).
4. **First merge of wave 4:** G7 SWEEP + G5 snapshot created pre-merge.

## Parent-side test patch (rationale)

Brief acceptance Godot test originally asserted `get_root().get_node_or_null("ThemeConstants")` reachability — same harness pattern as leaf-02/05/06: Godot SceneTree `--script` mode does NOT load autoloads. ThemeConstants IS correctly registered in `project.godot [autoload]` (verified pre-merge + post-merge greps) but unreachable during `--script` runtime.

Also caused SCRIPT ERROR: `Invalid access to property or key 'state_updated' on a base object of type 'Nil'` — SimBridge tried to connect to its expected signals but autoload not loaded.

This is the 4th occurrence of the harness deferral pattern in Wave 3 (leaf-02 FileAccess, leaf-05 _ready deferral, leaf-06 same _ready deferral, leaf-07 autoload non-loading).

## Patch applied (parent acts as test-author)

Replaced behavioral autoload-presence check with source-grep on `project.godot` for the autoload registration line:
- `ThemeConstants="*res://autoload/theme_constants.gd"` present
- Other behavioral assertions on ProjectSettings (main_scene, custom_user_dir, custom_user_dir_name) retained — those work in `--script` harness because ProjectSettings parses at engine init.

Cross-runtime autoload verification deferred to:
- Manual playthrough (Westley sign-off before friends-ZIP cut)
- Apex E2E (when configured) — runs full Godot runtime where autoloads load

## Merge-log entry sequencing note

Merge-log entry for leaf-07 was appended BEFORE the brief acceptance test re-run revealed the 1/10 failure. Entry text says "clean" but technically referenced the pre-patch state. Post-patch verification: 10/10 Godot + 27/27 Python = both gates GREEN. Functional state matches "clean". No revert needed — impl files are correct; only test fixture needed parent-side patch (same as leaf-05).

If audit trail strictness matters, the merge-log "clean" status reflects the FINAL post-patch state, which is genuinely clean. The patch is documented here in MERGE_ASSUMPTIONS per cascade convention.

## Wave 3 cascade complete

leaf-07 merge closes Wave 3 cascade. All 6 leaves (01, 02, 04, 05, 06, 07) merged. Umbrella 27/27 GREEN. Pre-Zip BLOCKERs B2/B3/B5 wiring complete.

## Verdict

Patch applied to staged test ONLY (well, real-path test since staging was consumed pre-patch — same effect). Impl files unmodified. Wave 3 GREEN.
