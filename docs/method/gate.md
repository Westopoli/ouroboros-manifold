# The layered gate

Spec of record: `docs/northstar/plans/2026-10-29-layered-gate-spec.md` (Westley approved 2026-10-29; DEC-layered-gate-window, DEC-layered-gate-flags, DEC-landing-noff). This page is the summary.

## Per landing, under `gate.lock`, under ten minutes

0. Base: the candidate contains the current `origin/main`, else reject in seconds.
1. Pre-gate (also run before every push, off the lock): make, every lint, the footprint fence, noise check, the story's own tests; with any `csrc/` change, the pinned csim files. A lint or noise reject never costs a gate.
2. Flag layer: the story's `Flag:` (`harness`, `client`, `sim`, `contract`) is verified by the two determinism traces against the base sha and by the diff footprint. A wrong flag is a finding on the story, not a rule change.
3. Fast tier: the suites the flag selects (a `harness` story runs the harness tests; `client` adds the playthrough and the plays; `sim` adds the csim regression; `contract` adds the pins). `merge_gate.sh --tier fast <candidate> origin/main <id>`.
4. Play: `scripts/play.sh --story <id>`, window within DRAFT-play-window-s, scene reached.

The verdict is the set of `GATE <stage> REJECT` lines. The landing is one `--no-ff` merge whose subject begins `Land `.

## Off the lock

- Sweep: the slow tier (the full suite) runs over main after DRAFT-slow-tier-batch (3) landings, DRAFT-slow-tier-hours (2 h), or nightly at DRAFT-sweep-nightly (23:30), on a worktree at `origin/main`, and records an empty commit `Sweep <date> pass|red n`.
- Bisect: a red sweep runs `git bisect run --first-parent` on the failing test between the last green sweep and head, reverts the culprit landing (`Revert Land <id>`, trailer `Finding:`), and the story returns to Ready. Main is green when the last sweep is green.

## Cache

Suite results are keyed by declared inputs (`suite_inputs.toml`); the clerk seeds the cache from the gated sha after the push so a docs-only merge hits and a code merge misses.
