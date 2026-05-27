# Wave 3 Pre-Zip Wiring — Parent Assumption-Sweep

**Status:** active. Updated 2026-05-26 14:30 (post-leaf-02 staging).

## Per-leaf ASSUMPTIONS review (Wave 1 leaves)

### leaf-01 (B5-A)
- No `.ASSUMPTIONS.md` file written.
- Sub-agent reported: "No sibling ASSUMPTIONS files present at start. No contract proposals needed — only edited impl_files listed in brief."
- Disposition: CLEAN — no inferences logged.

### leaf-02 (B5-B)
Reviewed `.swarm/briefs/wave_3_pre_zip_wiring/leaf-02.ASSUMPTIONS.md`. Entries:

1. **Test runner bash exec blocked.** RED→GREEN empirical proof unrunnable in sub-agent shell. Static-equivalence pass only.
   - Category: NOT drift — operational gap, not design pick.
   - Damage: zero design risk. /swarm-merge step 5 + 6 will re-run umbrella in parent shell.
   - Disposition: ACCEPT — parent verifies behavior via merge gates.

2. **SceneRouter lookup via `/root/SceneRouter`** (not class-name autoload var).
   - Category: convention pick. Matches Godot autoload access pattern. Existing `tests/test_wave3_blockers_umbrella.gd` uses same `get_root().get_node_or_null(...)` pattern.
   - Disposition: ACCEPT — consistent with project convention.

3. **Label not RichTextLabel** for privacy text.
   - Category: implementation choice. Test accepts either per assertion (4) in brief: "Label/RichTextLabel containing 'PRIVATE PLAYTEST BUILD'".
   - Spec §B5-B says "Label or RichTextLabel".
   - Disposition: ACCEPT — within brief allowance.

4. **Verbatim text per spec lines 63-68** — 4-line form (header + 3-line body).
   - Category: source-faithful copy.
   - Verified: spec lines 60-69 contain exact text leaf staged.
   - Disposition: ACCEPT.

5. **Real-path temp-copies cleaned** during attempted runs.
   - Category: anti-bypass discipline.
   - Disposition: ACCEPT — sub-agent obeyed HARD RULE STAGING ONLY rule.

## Cross-leaf drift check

- leaf-01 + leaf-02 share zero files (project.godot edit by leaf-01 vs scenes/privacy_modal/ + tests/test_privacy_modal.gd by leaf-02).
- No cross-leaf contradictions.
- No fabricated symbols.
- No compounded inferences.

## Parent /swarm UNSTATED carryover

`docs/test_specs/wave_3_pre_zip_wiring.UNSTATED.md` — 10 entries, all confirmed 2026-05-26. No drift.

## Verdict

**Wave 1 assumption-sweep CLEAN.** Proceed to per-leaf /swarm-merge gates.

## Wave plan locked

| Wave | Leaves | Status |
|---|---|---|
| 1 | leaf-01 (B5-A), leaf-02 (B5-B) | sweep clean, gating in progress |
| 2 | leaf-04 (B3-A), leaf-05 (B2-B) | pending |
| 3 | leaf-06 (B3-B) | pending |
| 4 | leaf-07 (B5-C) | pending |
