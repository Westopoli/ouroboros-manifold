# Plan-consistency + invariant-audit notes — c5

## check_invariants.py known-limitation waiver (same class as C7/T1/C2/C4/C3)

`spec-link` FAILs on `tests/test_tactical_view.gd` — pre-existing,
parent-owned fenced test. Accepted as-is, consistent with prior waivers.
Traceability satisfied by the test's own header comment (cites C5, the
two-day-push brief, pieces.toml attach step 7, the architecture doc, the
full contract verbatim).

## Plan-consistency (1.5)

1. AC↔AC: no gap.
2. AC↔contract: no C ABI symbols (pure GDScript).
3. AC↔"umbrella": n/a.
4. Observability: every field asserted is directly readable from
   `qa_state()`/`issue_command()`/`qa_box_select()` return values.
5. Named-entity resolution: the "Reference-stub proof" section in
   c5_t2g_tests_note.md already lists three under-defined points as
   named Q-candidates with multiple valid answers (screen-direction sign
   convention, current_version's source — not applicable to C5, that's
   T2g — dead-unit modelling) — this spec carries forward only the ones
   relevant to C5 (screen-direction convention), already resolved by the
   test's own tolerance (one dominant axis, not an exact sign), so no
   open external-unverified item remains for this piece.

## Built fixture-first, per M0 (2026-09-22)

Both `tests/fixtures/tactical_frame_seed11.json` and
`tests/fixtures/tactical_frame_seed11_tick10.json` exist on `main`
already. `depends_on = ["B10", "B12", "T1"]` gates the ATTACH tag, not
this build.
