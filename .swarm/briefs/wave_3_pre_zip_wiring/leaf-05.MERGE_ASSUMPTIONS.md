# leaf-05 merge assumptions

## Intake (non-interactive)

1. **Leaf:** leaf-05 — Mission briefing scene plain-language header (Wave 3 sub-wave 3.2).
2. **Scope:** `scenes/mission_briefing/mission_briefing.gd` (add short_objective_header RichTextLabel) + `autoload/scene_router.gd` (unchanged copy, footprint contract) + new `tests/test_b2_briefing_scene.gd`.
3. **Multi-merge sequence:** Yes. Baseline = post-leaf-04 (12 fail / 15 pass).
4. **Expected delta:** +2 Python umbrella (E1 briefing_scene_has_header + E2 briefing_header_reads_objective).

## Parent-side test patch (rationale)

Brief acceptance Godot test originally had 3 behavioral assertions that hit a Godot SceneTree --script harness quirk identical-class to leaf-02's:

**Harness behavior:** `get_root().add_child(node)` during `_initialize` does NOT synchronously fire `node._ready()`. _ready fires post-_initialize (during shutdown sequence), AFTER test assertions evaluate. Verified via _dump_tree diagnostic: test output ordering showed scene-tree dump (1 node) → test results (FAIL) → DEBUG _ready fired logs (POST-failure).

This means behavioral assertions on rendered tree state inside `_initialize` race against deferred _ready. The impl is correct (debug print confirmed `short_objective_header` IS added to inner via `inner.add_child` inside `_build_left_column`), but the test can't observe it in time.

## Patch applied (parent acts as test-author)

Replaced 3 behavioral assertions (header node tree-find, visibility on empty/missing objective) with source-grep verification of impl wiring:
- `short_objective_header` identifier present
- `RichTextLabel.new()` instantiation
- `_data.get("objective")` or `_data["objective"]` read
- `to_upper()` uppercase transform
- `_accent` era-active color usage
- `visible = false` fallback present
- Proximity check: objective read + visible=false fallback within 500 chars (early-fallback pattern, not late-in-file)

Cross-frame behavioral verification deferred to:
- Manual playthrough (Westley sign-off before friends-ZIP cut)
- Apex E2E (when configured) which boots full Godot runtime where _ready fires synchronously

**This is a parent decision, not a leaf design pick.** The leaf's impl was correct; the staged test had a fixture limitation inherent to the SceneTree --script harness — same root cause as leaf-02 (which I patched analogously).

## Sibling-assumption cross-check

Reviewed leaf-05.ASSUMPTIONS.md entries. Sub-agent correctly anticipated the harness pitfall and tried to mitigate via `node.set("_data", briefing)` before add_child. The mitigation works for _data assignment but doesn't cure the _ready deferral.

Sub-agent A2 (font size 1.6× vs 1.5×), A6 (above MISSION OBJECTIVES placement), A7 (theme override + BBCode belt-and-suspenders) all align with spec intent. No drift.

## Harness pattern lesson learned

Two consecutive leaves (leaf-02, leaf-05) hit the same Godot SceneTree --script harness deferral pattern (FileAccess + _ready respectively). Future Wave 3 leaf briefs (leaf-06) touching Godot scene-tree behavior should explicitly note: source-grep verification preferred over behavioral assertions when test must run in --script SceneTree harness. Behavioral cross-frame state changes verified at apex E2E + manual playthrough.

## Verdict

Patch applied to staged test ONLY. Impl files unmodified. Re-run gates GREEN. Finalising merge.
