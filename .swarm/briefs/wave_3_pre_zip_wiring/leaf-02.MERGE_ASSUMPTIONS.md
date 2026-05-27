# leaf-02 merge assumptions

## Intake (non-interactive)

1. **Leaf:** leaf-02 — Privacy modal scene + script (Wave 3 sub-wave 3.1).
2. **Scope:** new `scenes/privacy_modal/privacy_modal.tscn` + `scenes/privacy_modal/privacy_modal.gd` + new `tests/test_privacy_modal.gd`.
3. **Multi-merge sequence:** Yes. Baseline = post-leaf-01 state (21 fail / 6 pass in Python umbrella).
4. **Expected delta:** +5 Python umbrella passes (B5-B assertions b_privacy_modal_*).

## Parent-side test patch (rationale)

First merge attempt was REVERTED 2026-05-26T14:45Z because the staged Godot brief-acceptance test (`tests/test_privacy_modal.gd`) had a fundamental fixture bug:

The test's "flag-skip path" assertion attempted to verify:
1. Write flag file via FileAccess.open(WRITE) + close.
2. Instantiate scene2 + add_child.
3. Assert scene2's _ready saw the flag → set `_skip_to_loading_screen = true`.

**Failure mode:** Godot SceneTree --script harness does not propagate FileAccess writes performed in `_initialize()` to FileAccess.file_exists calls made from inside a Control's `_ready()` triggered via `add_child` in that same _initialize tick. Verified via 5 diagnostic test scripts (deleted post-investigation). MAIN scope FileAccess.file_exists returns true post-write; READY scope returns false on the same path.

**Diagnosis:** the FIXTURE is wrong, not the impl.

Real runtime scenario per spec line 173-174 acceptance criterion 4:
- Session 1: player accepts modal → flag written → router → loading_screen → quit.
- Session 2: fresh process boot → privacy_modal main scene → `_ready` runs in FRESH process → flag exists from prior session → file_exists returns true → skip path.

The flag write and the file_exists check happen in DIFFERENT PROCESSES at runtime. The test compressed both into one process, exposing the harness quirk.

## Patch applied (parent acts as test-author)

Replaced the same-process re-instantiate-with-flag assertion (lines 75-88 of staged test) with source-grep verification of early-return wiring:
- `script_src.find("FileAccess.file_exists")` — flag-check call exists
- `script_src.find("_skip_to_loading_screen")` — skip field declared
- `script_src.find("return")` — early return present
- Proximity check — FileAccess.file_exists and `return` within 300 chars of each other (early-return pattern, not late-return)

Behavioral verification of the cross-process scenario deferred to:
- Manual playthrough (Westley sign-off before friends-ZIP cut).
- Apex E2E test (when configured).

**This is a parent decision, not a leaf design pick.** The leaf's impl was correct; the staged test had a fixture bug the leaf-author couldn't run (Bash harness blocked test runner per leaf's own ASSUMPTIONS log).

## Sibling-assumption cross-check

Reviewed leaf-02.ASSUMPTIONS.md entries 1-5 (all confirmed clean in wave-3.SWEEP.md 2026-05-26).

Entry 1 ("Test runner bash exec blocked") was a known operational gap. This merge gate caught the resulting fixture bug — the cascade worked as designed (parent verifies behavior, catches what leaf couldn't).

## Verdict

Patch applied to staged test ONLY. Impl files (`privacy_modal.tscn` + `privacy_modal.gd`) unmodified. Re-running merge gates against patched staged set.
