# Regression: three tiers

What "nothing broke" means, and when each check runs.

## Tier 1: landing

Every merge goes through the merge gate, `scripts/specfactory/merge_gate.sh`. Passing means no stage rejects.

## Tier 2: integration check

When: after each prototype is integrated, after multiplayer is wired, and before a plan is marked finished in `docs/northstar/ROADMAP.md`.

Command: `scripts/integration_check.sh <name>` (options: `--only <suite,...>`, `--no-compare`, `--declare <file>`). It runs every suite below one after another, each under `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0` and a `timeout`. It writes `docs/northstar/baselines/<date>_<name>.json` and `.md`, compares against the newest earlier `.json` there, prints PASS or REGRESSION, and exits 0 or 1.

| suite | what runs |
|---|---|
| csim | pytest `tests/csim` |
| scale | pytest `tests/csim/scale` with `OM_SCALE=1` |
| transport | pytest `tests/transport` |
| t1 | pytest `tests/qa/t1` (its own run: conftest collision with csim) |
| specfactory | pytest `tests/specfactory` |
| desktop | pytest `tests/qa/desktop` under `xvfb-run` |
| long | pytest `tests/long`; one row per seed (archetype, end, ticks, alive, wall seconds) |
| godot | `scripts/run_godot_tests.sh` on each `tests/*.gd`; pass, fail or aborted per script |
| mockups | `scripts/mockup_verify.sh` for each `scenes/mockups/*/verify.gd` |
| net | pytest `tests/net`; recorded `absent` until that directory exists |
| tactical_trace | `scripts/specfactory/tactical_trace.py`, O0 build against O2 build; `absent` until the file exists |

Regression (verdict REGRESSION) is any of:
- a test id, Godot script or mockup that passed in the previous baseline and fails or aborts now;
- fewer total tests in a suite;
- a long-suite seed whose `end` or `ticks` differs;
- `net` or `tactical_trace` passing before and failing or absent now.

Reported but not counted: all timings, scale budget failures, and mockup failures whose first failure line is a time budget (`took Nms, expected <`).

Declared changes: each integration plan lists up front what it expects to change (test ids, Godot script names, long-suite seeds as `seed:N`). That list goes in a text file, one per line, passed with `--declare`. Declared items are reported, not counted. Anything else that moves is a regression.

Who runs it: a Sonnet clerk, memory-scoped by the script. The clerk commits the two baseline files and reports the verdict; it does not chase failures.

Baselines live in `docs/northstar/baselines/`. The first, `main-pre-lockstep`, is the reference for the multiplayer work.

## Tier 3: play check

When: the same moments as tier 2. Three 30B QA sessions on the new main, read from Agora's run logs. Each plays at least one mission to its own end. The campaign ledger shows no new error fingerprint.

This tier is run by hand today; there is no command for it.
