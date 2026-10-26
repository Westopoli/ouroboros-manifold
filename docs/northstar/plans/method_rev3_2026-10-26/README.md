# Method rev 3 (2026-10-26): the 23 gaps, their fixes, and the weekly numbers

- `spec.md`: the gaps (G01 to G23), each with its fix, how the fix is verified to be in force, the effect metric with its exact procedure, the FAIL condition, the positive control and the W43 baseline; the rule-text diffs; the pieces and owners.
- `briefs/`: one brief per agent (tests writer, builders, records clerk, landing clerk, auditors A and B).
- `metrics/<ISO week>.json`: one file per week written by `scripts/specfactory/method_metrics.py --write` (the timer from Phase 4 on); `2026-W43.json` is the frozen bad week, the standing positive control.
- `audit_findings.md`: Phase 3, every auditor finding with both sides' evidence and Westley's ruling.

## Weekly table (one row per `--write`)

| Week | FAIL | DRAFT | PASS | NA | Decisive lines |
|---|---|---|---|---|---|
