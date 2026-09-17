# leaf-01 gate evidence — wave 1

Written by `run_gates.py`. Every row below is the result of a check
that actually executed; a gate that did not run has no row.

| gate | result | evidence | timestamp |
|------|--------|----------|-----------|
| 6.0 bypass | PASS | first leaf of the wave | 2026-09-17T22:47:04+00:00 |
| A1 wave-baseline snapshot | PASS | .swarm/drift-gate-and-green-check/wave-1.base.json | 2026-09-17T22:47:04+00:00 |
| A2 assumption-sweep (G7) | PASS | wave-1.SWEEP.md newer than every ASSUMPTIONS | 2026-09-17T22:47:04+00:00 |
| A3 pre-impl test audit | PASS | .swarm/drift-gate-and-green-check/audits/wave-1/default/TEST-AUDIT.md | 2026-09-17T22:47:04+00:00 |
| A4 boundary sweep | PASS | .swarm/drift-gate-and-green-check/audits/wave-1/default/BOUNDARIES.md | 2026-09-17T22:47:04+00:00 |
| 6.3 file-match | PASS | 2 changed path(s) ⊆ 4 declared; all 2 impl file(s) present (commit 5b0eaaac6e0d) | 2026-09-17T22:47:04+00:00 |
| G1 parent-owned | PASS | 2 leaf-owned path(s) vs 37 parent_owned glob(s) (2 parent-authored test path(s) exempt) | 2026-09-17T22:47:04+00:00 |
| G2 ASSUMPTIONS | PASS | leaf-01.ASSUMPTIONS.md present | 2026-09-17T22:47:04+00:00 |
| G3 open-question | PASS | no question ledger | 2026-09-17T22:47:04+00:00 |
| G4 contract-proposal | PASS | no proposal filed | 2026-09-17T22:47:04+00:00 |
| G5 footprint | PASS | every commit difference is declared; leaf never ran git | 2026-09-17T22:47:04+00:00 |
| G6 escalation-trigger | SKIP | no triggers declared | 2026-09-17T22:47:04+00:00 |
| G8 | PASS | leaf-01: PASS (reachability + lite mutation) | 2026-09-17T22:47:04+00:00 |
| G9 | PASS | leaf-01: PASS (complexity + nesting) | 2026-09-17T22:47:04+00:00 |
| G10 | PASS | leaf-01: PASS (scale antipatterns + growth assertions) | 2026-09-17T22:47:04+00:00 |

**Verdict: clear to admit** — 0 blocking, 0 advisory, 14 pass.

Admission itself (merge into integration, umbrella pre/post, log row)
is `worktree_ops.py admit` and is deliberately not done here — this
runner never mutates the project.
