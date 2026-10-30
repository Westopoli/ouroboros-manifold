# The layered gate

Spec of record: `docs/northstar/plans/2026-10-29-layered-gate-spec.md` (Westley approved 2026-10-29; DEC-layered-gate-window, DEC-layered-gate-flags, DEC-landing-noff). This page is the summary.

## Per landing, under ten minutes

Stages 0 to 3 run under `gate.lock`; stage 4 runs after it, off the lock, before the push.

0. Base: the candidate contains the current `origin/main`, else reject in seconds.
1. Pre-gate (also run before every push, off the lock): make, every lint, the footprint fence, noise check, the story's own tests; with any `csrc/` change, the pinned csim files. A lint or noise reject never costs a gate.
2. Flag layer: the story's `Flag:` (`harness`, `client`, `sim`, `contract`) is verified by the two determinism traces against the base sha and by the diff footprint. A wrong flag is a finding on the story, not a rule change.
3. Fast tier: the suites the flag selects (a `harness` story runs the harness tests; `client` adds the scripted end-to-end playthrough and the plays; `sim` adds the csim regression; `contract` adds the pins). The playthrough runs for every landing in the sweep, so no flag escapes it for longer than one sweep window. `merge_gate.sh --tier fast <candidate> origin/main <id>`.
4. Play: `scripts/play.sh --story <id> --check --tree <worktree>`, window within DRAFT-play-window-s, scene reached after DRAFT-play-settle-s.

The verdict is the set of `GATE <stage> REJECT` lines. The landing is one `--no-ff` merge whose subject begins `Land `.

## Off the lock

- Sweep: the slow tier (the full suite) runs over main after DRAFT-slow-tier-batch (3) landings, DRAFT-slow-tier-hours (2 h), or nightly at DRAFT-sweep-nightly (23:30), on a worktree at `origin/main`, and records an empty commit `Sweep <date> pass|red n`.
- Baseline: before the first build after the method lands, and after every change to the gate, a sweep on `origin/main` records `Base: <sha>`; every later sweep and bisect measures from it.
- Bisect: a red sweep runs `git bisect run --first-parent` on the failing test between the last green sweep and head, reverts the culprit landing (`Revert Land <id>`, trailer `Finding:`), and the story returns to Ready. Main is green when the last sweep is green.

## Flag source

The flag is the `Flag:` line of the story file and the `Flag:` trailer of the merge message; the gate reads neither pieces.toml nor an owner table (H-006).

## Cache

Suite results are keyed by declared inputs (`suite_inputs.toml`); the clerk seeds the cache from the gated sha after the push so a docs-only merge hits and a code merge misses.
