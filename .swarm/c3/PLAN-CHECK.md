# Plan-consistency + invariant-audit notes — c3

## check_invariants.py known-limitation waiver (same class as C7/T1/C2/C4)

`spec-link` FAILs on `tests/test_chronicle_scroll.gd` — pre-existing,
parent-owned fenced test authored before this cascade. Accepted as-is,
consistent with prior waivers. Traceability satisfied by the test's own
header comment (cites C3, the two-day-push brief, pieces.toml, the frame
shapes doc, bible R-065-01, R-068-02/07/08, R-069-01..06).

## Plan-consistency (1.5)

1. AC↔AC: no gap.
2. AC↔contract: no C ABI symbols (pure GDScript).
3. AC↔"umbrella": n/a.
4. Observability: every field asserted is directly readable from
   `qa_state()`.
5. Named-entity resolution: two flagged mismatches carried forward from
   `c3_c4_tests_note.md` rather than silently resolved — the R-068-07
   citation mismatch (it's actually the dedup rule, not referential
   integrity) and the pace-constants mismatch (bible says 0.08/0.20,
   existing animation code uses 0.125/~8s) — both are data the test
   author already flagged; this cascade carries the flag forward, does
   not fix the underlying animation timer (out of scope per the note).

## Built fixture-first, per M0 (2026-09-22)

`tests/fixtures/chronicle_frame_seed11.json` exists on `main` already.
`depends_on = ["B8", "T1"]` gates the ATTACH tag, not this build.
