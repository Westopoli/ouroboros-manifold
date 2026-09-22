# Plan-consistency + invariant-audit notes — c2

## check_invariants.py known-limitation waiver (same class as C7/T1)

`spec-link` FAILs on both `tests/test_c_bridge.gd` and
`tests/test_galaxy_view.gd` — both are pre-existing, parent-owned fenced
tests (authored before this cascade, already committed on `main`) that
this cascade cannot add a `# spec: ...::AC-N` header to without editing a
`tests/**` file. Traceability is already satisfied: both files carry their
own header comments naming the piece, the brief, and the bible rules they
prove (`tests/test_c_bridge.gd`'s header cites T1/C2 and
`docs/architecture.md`; `tests/test_galaxy_view.gd`'s cites C2, S-106/S-107,
R-106-01..05, R-107-01..05). Accepted as-is, consistent with the C7 and T1
waivers.

## Plan-consistency (1.5)

1. AC↔AC: no gap. `tests/test_c_bridge.gd` and `tests/test_galaxy_view.gd`
   are independent (galaxy_view degrades gracefully when the bridge is
   missing, per its own `_load_snapshot_via_bridge` fallback), so the two
   leaves genuinely have no ordering dependency despite the production
   wiring later consuming the bridge's output.
2. AC↔contract: no formal `contract_imports` — same C-header regex
   limitation as T1 (n/a here anyway, these are pure GDScript with no C ABI
   symbols). Field mappings (`qa_state()` keys, `PLANTS` ids) verified
   directly against both fenced test files' literal source, not paraphrased
   from any brief.
3. AC↔"umbrella": n/a, no shared umbrella test for this cascade.
4. Observability: every field the tests assert on is directly observable
   (`qa_state()` dict keys, `qa_plant` booleans, method presence).
5. Named-entity resolution: `edges_3d`/`pick_radius_px`/`owner_colours` are
   flagged in `c2_tests_note.md` itself as added for the plants to have
   something to flip — self-consistency only, no external formula pinned.
   Not a blocking external-unverified item; the spec already carries this
   note forward verbatim.

## pieces.toml loose end (not this piece's to fix)

`pieces.toml`'s C2 row acceptance list omits `tests/test_c_bridge.gd`
despite C2 owning `autoload/c_bridge.gd` directly (flagged already in
`c2_tests_note.md`'s own "Loose end" section, and in the M3 brief item 3).
Both tests are treated as fenced acceptance for this cascade regardless.
`docs/**` including `pieces.toml` is parent-owned; flagging again here for
M0, not editing it.
