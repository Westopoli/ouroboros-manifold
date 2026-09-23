# Plan-consistency + invariant-audit notes — t2g

## check_invariants.py known-limitation waiver (same class as prior pieces)

`spec-link` FAILs on `tests/test_load_game.gd` — pre-existing, parent-owned
fenced test. Accepted as-is. Traceability satisfied by the test's own
header comment (cites T2g, the two-day-push brief, pieces.toml attach
step 9, the c5_t2g_tests_note.md contract verbatim).

## Plan-consistency (1.5)

1. AC↔AC: no gap.
2. AC↔contract: no C ABI symbols (pure GDScript, duck-typed bridge).
3. AC↔"umbrella": n/a.
4. Observability: every field asserted is directly readable from
   `qa_state()`/`qa_load_slot()` return values.
5. Named-entity resolution: `current_version`'s source is an explicitly
   open Q-candidate per c5_t2g_tests_note.md — resolved here as a
   scene-local constant (the note's own candidate (a), simplest, matches
   the test's black-box style), not silently guessed.

## Built fixture-first, per M0 (2026-09-22)

`depends_on = ["T2c", "T1"]` gates the ATTACH tag, not this build. T2c
isn't built yet at all — this piece is satisfiable regardless since the
fenced test injects its own `FakeBridge` double, standing in for both
T2c and C2's real bridge; no live dependency exists for the fenced test
itself.
