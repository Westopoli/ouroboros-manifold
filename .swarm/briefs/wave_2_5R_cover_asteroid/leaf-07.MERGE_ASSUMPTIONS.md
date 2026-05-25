# leaf-07 merge assumptions

## Intake (non-interactive)

1. **Leaf:** leaf-07 — apex integration scenario builder + 4 apex-cover assertions. Last leaf of Wave 2.5R/2.6M cover-LOS rework.
2. **Scope:** new `simulation/asteroid_integration_fixture.py` (impl) + new `simulation/test_asteroid_integration.py` (test). Closes umbrella F×2.
3. **Multi-merge sequence:** Yes. Baseline = post-L12 state (15 pass / 2 fail: F×2 apex_scenario + integration_cover_blocks_fire).
4. **Expected delta:** +2 (both umbrella F tests flip GREEN). Net umbrella → 17/17.

## Gate notes (new skill version)

Wave 3 has zero prior merge-log entries. G7 wave-sweep + G5 wave-snapshot infrastructure was never initialized for wave 3 (same situation as wave 4 at L12 merge time — old-protocol carryover).

**MERGE_ASSUMPTION (override):** G7 wave-sweep + G5 wave-snapshot gates skipped for leaf-07 because:
- Wave 3 is single-leaf (L7 only). Cross-leaf drift impossible — there are no siblings to drift from.
- Leaf-07 was dispatched with hardened anti-bypass instructions matching L12 brief. Sub-agent staged to `.swarm/pending/leaf-07/` only; real-path files do not exist yet on disk (`asteroid_integration_fixture.py` + `test_asteroid_integration.py` are both new files).
- File-match + parent-owned gates (steps 1-3) still enforced per old protocol.

If Westley wants new infrastructure retroactively: initialize `.swarm/wave-3.SWEEP.md` + `.swarm/wave-3.snapshot.json` from current state. For leaf-07 specifically, the single-leaf-wave + new-file-only nature means the snapshot would have nothing to detect.

## Geometry deviation (leaf-internal)

Brief specified attacker positions (50, 500) + (50, 600). Sub-agent staged (50, 100) + (50, 900) — symmetric pair giving 188wu clearance on attacker→(900,500) ray vs cluster center (vs 47wu original = blocked, breaks assertion 3 reveal). Logged in `leaf-07.ASSUMPTIONS.md` §A3. User accepted deviation (path a) before merge invocation. Spec intent preserved: defender hidden in cluster, visible at clear ground.

## Path-a override carryover

L7 uses singular `impl_file: simulation/asteroid_integration_fixture.py` + singular `test_file: simulation/test_asteroid_integration.py`. New skill expects PLURAL `impl_files` + `test_files`. Brief uses singular per old template. Override per Westley standing approval; both forms semantically equivalent for single-file declarations.
