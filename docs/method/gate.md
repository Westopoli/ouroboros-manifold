# The layered gate

Spec of record: `docs/northstar/plans/2026-10-29-layered-gate-spec.md` (Westley approved 2026-10-29; DEC-layered-gate-window, DEC-layered-gate-flags, DEC-landing-noff). This page is the summary.

## Per landing, under ten minutes

Stages 0 to 3 run under the story's channel lock, `gate-lab.lock` or `gate-beta.lock` (the story's `Channel:` Machine line, `lab` when absent; H-059): one landing in flight per channel, and the two channels gate at the same time. Stage 4 runs after it, off the gate lock, before the push. What stays shared between channels: `play.lock` (every real-display `play.sh` run and capture), `push.lock` (fetch, merge, `pre_gate` re-check and `git push HEAD:main`, in `land_push.sh`), `records.lock`, the worktree disk cap, and the sweep. `gate_runs.csv` rows are appended under `flock`, cache and candidate-result files are written to a `mktemp` name and renamed. `status_check.py --story <id> --lock <lock>` reports `STATUS channel DRIFT <id>` when the clerk took the other channel's lock.

0. Base: the candidate contains the current `origin/main`, else reject in seconds.
1. Pre-gate (also run before every push, off the lock): make, every lint, the footprint fence, noise check, the story's own tests; with any `csrc/` change, the pinned csim files. A lint or noise reject never costs a gate.
2. Flag layer: the story's `Flag:` (`harness`, `client`, `sim`, `contract`) is verified by the two determinism traces against the base sha and by the diff footprint. A wrong flag is a finding on the story, not a rule change. When `--tier` is given the stage prints `GATE flag SKIP tier given` and compares nothing (DEC-gate-tier-given-skips-flag-2026-10-30).
3. Fast tier: the suites the flag selects (a `harness` story runs the harness tests; `client` adds the scripted end-to-end playthrough and the plays; `sim` adds the csim regression; `contract` adds the pins). The playthrough runs for every landing in the sweep, so no flag escapes it for longer than one sweep window. The playthrough and lane_plays stages first wait for 3000 MiB of free graphics memory (`gpu_preflight.py`; draft numbers, Westley's); a `GPU-LOW` or `GPU-MEMORY` result is retried after the memory is freed and is never a known-red entry (H-073). `merge_gate.sh <candidate> origin/main <id>`: the flag picks the tier and its suites; a given `--tier fast` skips the flag and runs the bare fast tier (csim selection and transport only), which is never a story landing (DEC-clerk-gate-no-tier-2026-10-31).
4. Play: `scripts/play.sh --story <id> --check --tree <worktree>`, window within DRAFT-play-window-s, scene reached after DRAFT-play-settle-s.

The gd_reach lint (stage 1) rejects a `.gd` under `scenes/` or `autoload/` that no scene reaches; prototype scenes under `scenes/proto/` are declared in `scripts/specfactory/gd_reach_stubs.txt` by their builder (DEC-proto-scenes-reach-2026-10-30).

The verdict is the set of `GATE <stage> REJECT` lines. The landing is one `--no-ff` merge whose subject begins `Land `.

Stacked stories (2026-11-02, DEC-stack-gating-2026-11-02): when finished stories are stacked (each branch contains the one below it), `merge_gate.sh` may gate the top of the stack once with every id in its comma list, widest flag first, because tier and flag come from the first id only (footprint and pre-gate read the first id only too; story-check and story-acceptance loop over every id). The landing is still one `--no-ff` merge per story, in stack order, each with its own `Land <id>` subject and its own Story, Tests, Play, Played, Gate and Flag trailers (`status_check.py` reads one id from each `Land` subject); one merge for several stories is never allowed. The sweep counts each merge.

## Off the lock

- Sweep: the slow tier (the full suite) runs over main after DRAFT-slow-tier-batch (3) landings, DRAFT-slow-tier-hours (2 h), or nightly at DRAFT-sweep-nightly (23:30), on a worktree at `origin/main`, and records the `sweeps.md` row and an empty commit `Sweep <date> pass|red n` (`scripts/specfactory/sweep.sh`, H-014; the timer runs the nightly one, the landing clerk starts the other two when the status line says a sweep is due). A due sweep is a warning in the landing gate; a REJECT sweep row blocks landings until the bisect (DEC-sweep-drift-warn-2026-10-30). The one exception is the story that fixes it: a Machine line `Fixes-sweep: <swept sha>` passes the check as WARN, and the clerk sweeps right after its push (DEC-sweep-fix-exemption-2026-10-30). The slow tier itself never rejects on a red row: it prints `GATE status WARN sweep red <n> at <sha> slow tier` and runs, since the sweep is the only thing that replaces the row (DEC-slow-tier-ignores-red-row-2026-10-30). A red whose ids encode a superseded ruling is re-pinned by a test-defect story, not reverted (DEC-sweep-red-test-defect-2026-10-30).
- Baseline: before the first build after the method lands, and after every change to the gate, a sweep on `origin/main` records `Base: <sha>`; every later sweep and bisect measures from it.
- Bisect: a red sweep runs `git bisect run --first-parent` on the failing test between the last green sweep and head, reverts the culprit landing (`Revert Land <id>`, trailer `Finding:`), and the story returns to Ready. Main is green when the last sweep is green.

## Records pushes

A records-only push (docs, the ledger, the register, decisions, story review pages, a `Seen <id>` commit; no code, no tests) takes `~/Projects/om-push/records.lock` and never waits behind a gate (DEC-records-lock-2026-10-23). It merges the branch into main's tip, never main into the branch (DEC-records-push-first-parent-2026-11-02): `status_check.py` reads the first-parent subjects of main (`Land`, `Seen`), and a branch built by merging `origin/main` into it and then pushed puts first-parent main on the branch, so the commits pushed just before drop off the line it reads (a `Seen H-023` did, and showed `seen_without_commit DRIFT`).

Under the lock, from a detached HEAD so first-parent stays main's own history:

1. `git fetch -q origin`, then `git switch -q --detach origin/main`.
2. `git merge --no-ff --no-edit <the records branch>`. When origin/main's tip is on the branch's own first-parent line (cut from it, nothing landed since), skip the merge and push the branch tip: a fast-forward is fine.
3. `python3 scripts/specfactory/status_check.py --base HEAD | tail -4`. Without `--base` it reads `origin/main`, which does not hold the push yet. Any DRIFT stops the push.
4. `git push -q origin HEAD:main`. Rejected as non-fast-forward means another records push landed: fetch and redo from step 1.

A `Seen <id>` commit is made empty (`git commit --allow-empty`, subject exactly `Seen <id>`, `Verdict:` trailer) directly on the then-current origin/main tip in the same way, under the lock, and pushed at once; it is never made inside a branch that is merged later.

## Flag source

The flag is the `Flag:` line of the story file and the `Flag:` trailer of the merge message; the gate reads neither pieces.toml nor an owner table (H-006).

## Cache

Suite results are keyed by declared inputs (`suite_inputs.toml`); the clerk seeds the cache from the gated sha after the push so a docs-only merge hits and a code merge misses.
