# Plan-consistency + invariant-audit notes — t1

## check_invariants.py known-limitation waivers (not fixed, documented instead)

1. **contract_imports left empty.** `check_invariants.py`'s `_load_contract_symbols`
   only parses Python (`class`/`def`) and TypeScript (`export ...`) declaration
   shapes; it has no C function-declaration regex, so every real symbol from
   `csrc/ouroboros_sim.h` (a C header) registers as "not in locked contract"
   even though it genuinely is. Verified manually via `grep` against the header
   for all ~27 symbols this piece needs (see spec T1.md's per-section citations).
   Left `contract_imports:` empty rather than fight a tool built for a different
   contract-file language; the symbols are cited in the brief's Task prose and
   the spec's per-section header-line references instead.

2. **spec-link FAIL on `tests/transport/test_pipe_shapes.py`, accepted as-is.**
   The Spec Link Rule (`# spec: <path>::<section>::AC-<N>` in the test file's
   first 5 lines) is designed for tests the shard-test-writer authors fresh in
   Phase 2.6. `tests/transport/test_pipe_shapes.py` is a pre-existing,
   parent-owned fenced test written by M0's F4 step before this cascade
   started (its own header comment already names its source: `docs/architecture.md`,
   "C transport v1"); this M3 cascade cannot add a header to it without editing
   a `tests/**` file, which is forbidden. Same class of gap as C7's
   documented adapter-test deviation (ground rules line 9) — a structural
   mismatch between the generic skill tooling and this repo's fenced-test
   convention, not a defect in the brief or the test. Traceability is already
   satisfied by the spec's own "Source of truth" section naming the exact
   test file and function.

## Plan-consistency (1.5)

1. AC↔AC: no gap — spec has one acceptance path (tests/transport green + clean build).
2. AC↔contract: contract is `csrc/ouroboros_sim.h`; every field the spec's hello/
   snapshot/delta/command sections cite resolves to a real header symbol
   (manually verified, see above).
3. AC↔fenced-test: **one real, called-out contradiction** — `docs/architecture.md`
   says `snapshot` is sent "on request and after set_seed/load"; the fenced
   test's own script requires `set_seed` to emit nothing (see spec T1.md's
   "Documented deviation" section for the full reasoning). Resolution: the
   fenced test wins (project rule: tests are the spec); spec built around
   that; doc correction flagged for M0, not made unilaterally (`docs/**` is
   parent-owned).
4. Observability: every acceptance criterion (hello fields, delta count/type,
   snapshot tick/checksum) is directly assertable and is in fact asserted by
   the fenced test.
5. Named-entity resolution: `om_save_state_read`/load-back symbol name is not
   confirmed by line number in the spec (spec says "grep the header near line
   1419-1420" rather than naming it exactly) — left as a leaf-time grep task
   since `load`/`save` aren't exercised by the fenced test at all; not a
   blocking external-unverified item, just an internal implementation detail
   the leaf resolves itself.
