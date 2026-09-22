# Plan-consistency + invariant-audit notes — c4

## check_invariants.py known-limitation waiver (same class as C7/T1/C2)

`spec-link` FAILs on `tests/test_briefing_debrief.gd` — pre-existing,
parent-owned fenced test authored before this cascade. Cannot add a
`# spec: ...::AC-N` header without editing `tests/**`. Traceability already
satisfied by the test's own header comment (cites C4, the two-day-push
brief, pieces.toml, the frame shapes doc, and bible rules R-079-01..04,
R-077-01/02, R-076). Accepted as-is, consistent with prior waivers.

## Plan-consistency (1.5)

1. AC↔AC: no gap — two independent scene blocks, no shared state.
2. AC↔contract: no C ABI symbols (pure GDScript). Field mappings verified
   directly against the fenced test's literal source.
3. AC↔"umbrella": n/a.
4. Observability: every field asserted is directly readable from
   `qa_state()`.
5. Named-entity resolution: the marker-name table's exact contents beyond
   covering the fixture's node ids (3, 7, 12) are left to the leaf as
   ordinary internal implementation — not a design decision with external
   weight, since nothing else currently consumes this table.

## Built fixture-first, per M0 (2026-09-22)

Both fixtures (`tests/fixtures/mission_frame_seed11.json`,
`tests/fixtures/debrief_frame_seed11.json`) exist on `main` already (part
of the same commit that landed the fenced test). `depends_on = ["B9",
"T1"]` in `pieces.toml` gates the ATTACH tag, not this build — per M0's
explicit instruction, this piece is built now against the fixtures and
will rebind to the live pipe automatically once `attach/T1` lands (the
frame shape is identical either way).
