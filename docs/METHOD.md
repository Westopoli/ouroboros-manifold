# How this repo is run

For a reader with ten minutes. Everything here is a pointer; the linked file is the source of truth, and where this page and it disagree, it wins. The short rule list the agents work under is [`CLAUDE.md`](../CLAUDE.md).

## The roles

Claude designs and tests; agents build. The tiers are roles, and the model behind a tier can change.

- **Architect** (a Fable chat, or a read-only `architect` agent): architecture, specs, rulings, briefs. Short-lived; restarts from memory past about 400k tokens of context.
- **Dispatcher** (a Sonnet chat): launches the Architect's scripts, lands work through clerks, keeps the one status table. Decides nothing about rules, thresholds, specs or tests. See [`workflows_2026-10-07/dispatcher.md`](northstar/plans/workflows_2026-10-07/dispatcher.md).
- **Engineers and doers** (Sonnet agents): tests, audits, clerks, and code written against a spec. They spawn nothing.
- **Westley** (the owner): answers what a picture looks like and what a rule means where no one has recorded his words, and may veto any other decision. Decisions are logged in [`story_reviews/westley/decisions.md`](northstar/story_reviews/westley/decisions.md).

Task matching and the usage rules (builders push and stop, a clerk lands, no waiting in a chat): [`CLAUDE.md`](../CLAUDE.md) "Task matching". Shared agent rules: [`workflows_2026-10-07/rules.md`](northstar/plans/workflows_2026-10-07/rules.md).

## Tests are the spec

Every story exists as failing tests before any code, in fenced paths builders cannot edit, each naming the `S-###` or `R-###-##` it proves. Every detector ships with a positive control. A test is fixed only when it is classed as a `test-defect` with a ledger row. Thresholds and tolerances are Westley's: narrowing an invariant is allowed, loosening one needs him. Source: [`CLAUDE.md`](../CLAUDE.md) "Tests are the spec"; the Definition of Ready is in [`northstar/agile.md`](northstar/agile.md).

Since 2026-11-09 a rule that code implements carries a Proof line naming the one test that enforces it, and a weekly audit checks each rule against the bible and each proof against the current lab and beta: [`method/requirements.md`](method/requirements.md) "Proof" and [`method/requirement_audit.md`](method/requirement_audit.md).

## One owner per file

[`northstar/plans/push/pieces.toml`](northstar/plans/push/pieces.toml) names every file's owner. Two in-flight pieces never own the same file. New code goes in new files behind a frozen header; wiring is its own small piece. `scripts/specfactory/owner_lint.py` checks the table.

## The gate

`scripts/specfactory/merge_gate.sh` is the only way to main. Its stages, in order, run base, build, libm lint, algorithm-constants lint, footprint fence, class-name uniqueness, symbol ownership, signature table, reachability lint (C and GDScript), single-owner lint, rule pins, the csim, t1 and transport suites, piece acceptance ids, the Godot import, the playthrough, lane plays, `-O0` versus `-O2` checksum and tactical traces, and a status check. `undertest`, `size_lint` and `look` only warn.

- **Playthrough.** A scripted end-to-end run of the real client under xvfb, checked on every landing.
- **`pre_gate.sh`.** The cheap tier a builder runs before it pushes, so a lint or noise reject never costs a full gate.
- **Known-red lists.** Failures that exist on main and are tracked by a finding are listed with their ledger row in [`gd_tests_known_red.txt`](../scripts/specfactory/gd_tests_known_red.txt), [`lane_plays_known_red.txt`](../scripts/specfactory/lane_plays_known_red.txt) and [`playthrough_known_red.txt`](../scripts/specfactory/playthrough_known_red.txt). A reject naming a listed test does not stop a push; any other reject does. The entry leaves when its row closes.

## Drift and method checks

- **`status_check.py`** runs after every landing and fails on a mismatch between the lane table of [the programme file](northstar/plans/2026-10-07-visible-game-programme.md), `pieces.toml`, the review queue and git. Status lives in that one table.
- **`method_check.py`** runs on a chat's own transcript at every compaction and prints, per rule, how many turns broke it, as `OK`, `REVIEW` or `DRIFT` lines. A `DRIFT` line is quoted to Westley before any other work and the behaviour stops. It is never argued away: a rule change is his, an exception is a ledger row. See [`workflows_2026-10-07/method_check.md`](northstar/plans/workflows_2026-10-07/method_check.md).
- **Weekly drift audit.** A fresh Sonnet auditor checks rulings against every epic they touch. Procedure: [`workflows_2026-10-07/drift_audit.md`](northstar/plans/workflows_2026-10-07/drift_audit.md).

## The ledger and the register

The push ledger ([`push_ledger_2026-09-22.md`](northstar/plans/push_ledger_2026-09-22.md)) records what landed and why. The [ambiguity register](northstar/ambiguity_register.md) holds every open question with two or three candidate answers. Docs are rewritten, never appended: when direction changes the old text goes, and history is `git log` and [`bible_history/`](bible_history/). Ambiguity is flagged, never guessed, and an epic with an open flag is not built. The bible is [`bible/game_bible.md`](bible/game_bible.md).

## Prototypes, then plans

A feature judged by eye or feel is prototyped and approved by Westley before it is planned (the Prototype gate in [`northstar/agile.md`](northstar/agile.md)). An approved mockup gets an integration lane the same day, and every status report says "approved, not integrated" until it is.

## The story-review flow

A player-facing piece ships with a deterministic element inventory from `qa_state()` in its tests and a desktop-driver screenshot. The landing clerk files the picture in [`northstar/story_reviews/`](northstar/story_reviews/) with a queue row, and a copy waits in [`story_reviews/westley/`](northstar/story_reviews/westley/README.md) for one word: approve, reject, or a note. A story moves to `Seen` in [`bible/stories.md`](bible/stories.md) only on his approval, and the lane's next look piece waits for the verdict. Rules: [`CLAUDE.md`](../CLAUDE.md) "Visible-game guards".

## Workflow or manager-mode

Before any build the Architect writes a `Tool:` line in the spec, decided by six questions: one spec, contract and umbrella test? Units that run without a frame? Three or more file-disjoint units? Must it stop for Westley? Does it need live verification? Does it touch the frozen contracts? A sim-side cluster of three or more test-expressible, file-disjoint units is a `/manager-mode` cascade; anything that ends in a frame, any single piece and every landing is a Workflow. The spec: [`2026-10-21-tool-split-spec.md`](northstar/plans/2026-10-21-tool-split-spec.md).

The measured record, from [`retro_2026-10-21/workflows_vs_manager_mode.md`](northstar/plans/retro_2026-10-21/workflows_vs_manager_mode.md): in the Workflow regime (2026-10-14 to 10-21), 2 of 32 runs completed clean, 15 stopped after one agent, 20 stopped on spec or records gaps, and the window cost about $1,763 (about $160 per landed piece). The one Manager Mode run built 9 leaves in 90 minutes with no reverts, but its admission ran only the umbrella test, not the gate. Hence the hybrid.

## The console-credit tools

`scripts/specfactory/sdk_engineer.py` (a Claude Code agent for read-heavy clerk work, one brief in, one report out) and `batch_review.py` (half-price batch reviews of story shots and per-epic drift audits) spend Console credits instead of the subscription. Both dry-run without a key. Setup and caps: [`scripts/specfactory/README_credits.md`](../scripts/specfactory/README_credits.md).
