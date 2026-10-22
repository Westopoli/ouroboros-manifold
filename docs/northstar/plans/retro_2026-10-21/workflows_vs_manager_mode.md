# Workflows versus Manager Mode for the beta programme and the lab (Architect, 2026-10-21)

Question (Westley, 2026-10-21): would an all-Sonnet overlord-and-shards cascade (/manager-mode) be more efficient than the Workflow tool for the beta programme and the simulation lab?

## Evidence

Workflow regime, 2026-10-14 to 10-21 (four active days; run records under the Jarvis project dir, 32 runs):
- 2 of 32 runs completed clean; about 11 pieces landed on main (hand count).
- 15 of 32 runs stopped after one agent (a preflight probe that found a gap).
- Stop causes: 12 spec gaps (unlisted pins 5, missing interface 2, contradiction 4, unmeetable number 1), 3 stale rule-pin hashes, 5 harness rejects (pieces.toml status or merge gate), 1 build red, 9 other (predecessor not landed 4, planned stops 2, usage limit, worktree setup, vacuous control).
- Spend (DEDUP estimate from transcript usage, list rates): $1,763 for the window; Fable chats 35 percent, Sonnet sub-agents 53 percent. About $160 per landed piece.
- Retro window 10-07 to 10-10 for comparison: $1,647, 135 pieces landed ($12 per piece), 62 wrong tests, 0 stories Seen. The quality bar since then (tests first by a separate writer, audits, shots, gates) is what the per-piece cost bought.

Manager Mode regime, the one run on this project (skill-lab harness, 2026-10-02, "manager-mode-lite", all Sonnet):
- 9 leaves, 2 waves, 90 minutes wall clock from wave base to last admission; 0 reverts; 547 tests green at landing.
- Later defects: four ledger rows, three of them wrong premises in the Architect's brief (mirror tolerance, planted control, anchors), one test-author overreach the cascade's own audit caught. No leaf bug.
- Its admission runs the configured umbrella test only. It does not run merge_gate.sh, pre_gate, pieces.toml ownership, the playthrough, the look stage or status_check. Its config fences csrc/**, tests/csim/** and scripts/specfactory/** as parent-owned.
- Working records (briefs, GATES.md, sweeps) did not survive on main; wave-1 leaf commits are 6 seconds apart, which the skill itself names as a sign of a collapsed admission loop.

## Reading

1. The cost of the workflow regime is not the tool. 20 of 32 stops (spec gaps, stale pins, records state) are defects in the spec-and-records layer the Architect writes, surfaced one at a time by a preflight agent, each costing a Dispatcher-Architect-records-relaunch round trip. Manager Mode's cascade showed the same failure class (wrong premises) and only moved it later, to the apex tests after admission.
2. What Manager Mode does better: one context holds spec, contract and umbrella and checks them against each other before any leaf runs (Phase 1.5); per-leaf failing tests are written and audited inside the same run, so a stale pin or an unlisted number is found before a build, not after. Leaves are file-disjoint by construction. Nine leaves in 90 minutes is a throughput no workflow run here has matched.
3. What Manager Mode lacks for this programme: the merge gate and its playthrough, the look stage and the shot for Westley, the ownership table, status drift, the one-landing lock across lanes, and the rule that thresholds are Westley's (its escalation is a file the overlord adjudicates). An all-Sonnet overlord drafting the spec is the weak point: the cascade's own defects came from the spec, and Sonnet writes weaker specs than it executes.
4. The beta's remaining path is mostly not build work: Steam steps 7 and 8 need Westley's accounts and app id; eleven first-look verdicts are queued. Neither tool moves those.

## Recommendation (Westley decides)

Hybrid, with the split by work shape, not by lane:
- Manager Mode (Sonnet overlord, Sonnet leaves, hardcore audit on contract-touching work) for sim-side clusters that are test-expressible, file-disjoint and umbrella-coverable: the places lane P3 wiring, startforce placement, the lab engine pieces E1 to E4, harness pieces. The Architect writes spec, contract and umbrella (as now); the overlord is the Dispatcher chat. The cascade's integration branch then goes through the existing landing clerk and merge gate as one landing, so nothing the gate checks is lost.
- Workflows kept for everything that ends in a frame: client pieces, plays, shots, the look stage, and for landings.
- Preconditions before the first cascade: a programme-specific .claude-swarm.toml (parent_owned rewritten to the frozen header, signatures.toml, goldens and the bible; umbrella = the piece's test file plus the csim regression subset; max_impl_lines 100 to match the build-unit rule); the cascade's briefs and GATES.md committed under docs/northstar/plans/cascades/<slug>/ so the record survives; one trial cascade on a sim piece already specced (P3 is the candidate) measured against the workflow numbers above: stops, wall clock, dollars, defects found by the gate afterwards.
- Independent of the tool: the spec-gap rate is the lever. A pre-launch consistency pass (the cascade's Phase 1.5 shape) run on every workflow spec before its script launches would have caught 15 of the 20 spec-and-records stops at one agent's cost each instead of a relaunch.
