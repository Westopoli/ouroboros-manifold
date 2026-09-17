# Wave 1 assumption-sweep

## Summary
- Total assumptions logged: 8 (3 leaf-01, 5 leaf-02)
- Flagged: 0

## Review

Checked each entry against the five categories (contradicts spec, contradicts
bible, cross-leaf contradiction, fabricated symbol/path, compounded inference).

- **leaf-01**'s `om_world_set_feature` call was independently verified: the
  symbol is real, declared in `csrc/ouroboros_sim.h`, defined in
  `csrc/faction.c:7` (an unusual home for a generic world-feature setter, but
  it exists and is exactly what the brief asked for — not a fabrication).
  The `drift_gate_ignored` override matches the brief's admission note and
  BOUNDARIES.md's own stated requirement for the positive control to keep
  working post-fix.
- **leaf-01**'s note about other E-02 story tests (S-012..S-020) "previously
  passing only vacuously because OM_FEAT_DRIFT defaulted off" is consistent
  with the known pre-fix bug shape (drift ran unconditionally regardless of
  any feature flag) — not a new regression, and will be checked directly by
  `apex_test_cmd` at admission (must reproduce the pre-established baseline:
  42 passed, 4 failed, 4 skipped, same four failing ids).
- **leaf-02**'s five assumptions (parser shape, `target_file` fallback
  ordering, short-circuit-on-first-acceptance-failure, always-print output,
  scratch-worktree path scheme) are all narrow implementation choices inside
  leaf-02's own two files, none observed by leaf-01 or by any other test.
  None compound on an unverified prior assumption; each cites the brief text
  it reads from.

Assumption-sweep clean. 8 assumptions reviewed, none flagged.
