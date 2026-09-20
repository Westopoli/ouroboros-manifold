# PX-05 — Metamorphic desync detector (proving the factory)

Run 2026-09-19 (ouroboros `5d4bc67`: `tests/qa/t1/desync.py`, `test_desync_detector.py`, `tests/qa/README.md`; the first files in the fenced `tests/qa/` tree PLAN.md named). Claim (Factory section; A7 memo): desync detection is a T1 detector from rung P0: two `om_world` instances, same seed and commands, checksums compared every cadence; a bit flip in instance two trips within ten ticks and the detector names tick, region and field; a clean pair never trips over 5,000 ticks.

Result: **pass**.

- RED first (`file or directory not found`), then 4/4 green: clean pair never diverges (checksums and full trace rows byte-identical over 5,000 ticks); a bit flip at tick 100 trips by tick 110 with the region and field named; the named field matches the corruption; out-of-order peer input trips.
- Timings: 5,000 ticks, 7 regions, checksum plus trace memcmp: 0.07 s; 60 regions, checksum only: 0.39 s; 60 regions with trace memcmp: 0.56 s. Fits every C card's acceptance, not only the epic gate.
- Field naming needs DRIFT on beside FACTIONS: the trace rows are written inside the drift step, so a FACTIONS-only pair has an empty trace and can name only the tick. Documented in the detector.
- Out-of-order test: swapping the order of two `om_intent_inject` calls changed nothing, so the test uses two `om_rng_force` queues in reversed order, which flips faction 0's telegraph/surprise draw and diverges the peers on tick 1 (positive control confirmed).

Side finding, verified (DECISIONS.md R8): `om_intent_inject` appends to `w->decisions[]`, and `om_step_decisions` (3d) begins with `decisions_n = 0` and recomputes every faction, so an injected decision looks erased before 3f resolves it; injection is a full no-op under FACTIONS; all 15 tests that use it fail at HEAD; the code, not the contract, is wrong (the contract never had a positive control).

Design consequence: the desync detector joins every C card's acceptance from rung P0 (cost under a second); the multiplayer rung adds the peer-command injection hook, which this side finding shows must be designed against the actual 3d behaviour.
