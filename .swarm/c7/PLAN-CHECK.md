# Plan-consistency — c7

| # | check | finding | artifact + line | resolution |
|---|-------|---------|------------------|------------|
| 1 | AC ↔ AC | no gap | spec C7.md | clean |
| 2 | AC ↔ contract | qa_daemon.gd is pure GDScript, no C symbols from csrc/ouroboros_sim.h; leaf brief sets contract_imports: [] | C7.md | clean (no contract dependency for this piece) |
| 3 | AC ↔ "umbrella" | no shared umbrella test exists yet (tests/push/ is new); this piece's adapter test is the umbrella seed | C7.md | clean |
| 4 | Observability | state() Dictionary keys scene/tick are directly assertable | tests/test_qa_daemon.gd | clean |
| 5 | Named-entity resolution | `--qa-port` wire protocol (TCP, line-delimited JSON) is under-defined by the brief; not required by the fenced acceptance test, left as build-simplest-thing per M3 brief's "under-defined -> simplest thing + report candidates" rule | 2026-09-22-manager-M3.md item 1 | external-unverified (no fenced test forces a shape; leaf reports candidates) |

## Checks with no finding
All clean except #5, waived as external-unverified per manager-common ground rule "when something here is under-defined, build the simplest thing that works" (mockup-harness brief line 20, same convention M3 brief inherits).
