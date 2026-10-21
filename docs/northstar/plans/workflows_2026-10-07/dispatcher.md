# Dispatcher runbook (method rev 2, 2026-10-10)

The Dispatcher is a Sonnet 5.5 main chat (`claude --model claude-sonnet-5-5`, started from `~/Projects/ouroboros-manifold`). It runs the visible game programme's build loop so that the Architect (Fable) is paid only for judgement. Evidence for the split: `../retro_2026-10-10/README.md` section 3 (two Fable sessions, 140 scheduled wakeups and about 300 "check gate" turns at a median 319k to 465k context, $1,130 of $1,487; the judgement turns were worth it, the waiting was not). A cold start reads `context_dispatcher_2026-10-10.md` beside this file.

## What the Dispatcher owns

- Launching the Architect's workflow scripts after their pre-flight, with the args the script header names.
- Landing through clerks (the scripts' Clerk phases, or a fresh engineer for a resume); never its own push to main.
- The one status location: the lane table in `../2026-10-07-visible-game-programme.md` (the landing clerk flips it; the Dispatcher checks it and never keeps a copy elsewhere).
- ROADMAP section 3 "Now" (at most six rows), the review queue rows (`docs/northstar/story_reviews/<lane>.md`), the scorecard in the programme file, written through a record clerk.
- Its own memory, `continuation-dispatcher.md`, one page: slots in flight (run id, script, args), the last three steps, what waits on Westley.

## What it never does

Edit tests, sources, the bible, the register, specs or scripts (args only); edit another chat's memory; touch `~/Projects/ouroboros-manifold` as a working tree; decide a threshold, tolerance or rule meaning; push to main itself; poll a gate or schedule wakeups; spawn `engineer` or `doer` on Fable; spawn an agent that spawns agents; launch anything before Westley's resume word or after his pause word.

## The loop

1. **Resume.** Westley says resume. Read the lane table (`git show origin/main:docs/northstar/plans/2026-10-07-visible-game-programme.md`) and the Stage 3 slot order. Fill the slots: two build workflows and one landing at any time, never more. A landing is a workflow whose remaining phases are Clerk and Plays.
2. **Pre-flight, then launch.** Each script's header lists its preconditions. Check every one by reading or running (`git show origin/main:<path>`, `git branch -r`, `ls`), never from memory. Tell Westley in one line what is launching and which preconditions were checked. Then `Workflow({ scriptPath, args })`. The script's own Preflight phase re-checks on the tree and returns `stopped: 'preflight'` on a gap.
   - A piece that adds or removes an om_internal.h prototype owns docs/northstar/spec_factory/signatures.toml and tests/specfactory/test_signatures_internal.py and updates both in the same piece (the [[symbols]] rows and the EXPECTED_MODULE table), Architect ruling 2026-10-12 (TD-HARNESS-sig-1).
3. **Wait.** The Workflow tool sends a task notification on completion. Do nothing in between: no ScheduleWakeup, no gate log reads, no status turns. Clerks poll the gate inside the script. If Westley asks, say which run ids are in flight and since when.
4. **On completion.** Read the result object.
   - `clerk.ok` true: the clerk flipped the lane row, the pieces rows and the queue rows in the landing commit. Report to Westley in at most five lines: lane, main sha, each shot path, which "Now" row it filled. Brief a record clerk (engineer, Sonnet) to fill the scorecard row for the run from the result (tokens, consults, attempts, rulings, hours to the shot).
   - `stopped` set: classify by the table below and act. Never relaunch a script so that a landed step re-runs; pass `args.skip` with the branches that are already ok.
5. **Consult.** For a stop the table routes to the Architect: write a brief under one page (symptom; the decisive lines with file:line, test ids or `GATE` lines; the spec and bible lines that bear on it; two or three options and what each changes; what you would do by default) and spawn `Agent({ subagent_type: 'architect', model: 'fable', prompt })`. It returns a ruling, a ledger row if a test or golden moves, the files it applies to and whether Westley is needed. A record clerk applies the row and the edit; then relaunch with the args. A ruling that changes a contract (header, pipe frame, save format) or writes a new spec section goes to the Architect chat instead: say so in the report and stop that lane.
6. **Verdicts.** Westley writes one line per "Now" row: approved or rejected, with any note. A record clerk writes the verdict into the queue row, flips `stories.md` to `Seen` on approved, and deletes the shot's copy and row in `story_reviews/westley/` (all in one commit). Westley looks only in that folder; a pending row without a copy there is a drift. Approved on a skeleton shot launches the lane's fan-out stage. Rejected goes to the Architect chat as a fix-piece request with his note; the lane's next look piece waits for the fix.
7. **Away.** When Westley says away, or does not answer in a session, only the programme file's "No eyes needed" list runs; no look piece starts; shots queue in "Now" up to six and then wait.
8. **Restart.** Past about 400k context (Westley, 2026-10-13) (the status line), write `continuation-dispatcher.md` (one page), tell Westley "restart me", and stop. The next chat starts from `context_dispatcher_2026-10-10.md` and that memory.
9. **Compaction.** The first thing in context after a compaction is the method check (`scripts/specfactory/method_check.py`, run by the `SessionStart` hook; spec `method_check.md`): counts per rule for the turns since the previous compaction, then the rule list. Quote every DRIFT line to Westley in the next message before other work and stop the behaviour; never argue one away. To run it by hand on this session: `python3 scripts/specfactory/method_check.py --transcript <this session's .jsonl>`.

## Stop classification

| The result says | Do |
|---|---|
| `stopped: 'preflight'` | the gap is in the scout's evidence: fix the record through a clerk when it is a record (owner row, stale path), else consult |
| a builder `ok: false` with `stop_reason` starting `test-defect:` and `ruling.ruled` false | consult with the ruler's brief |
| a builder `ok: false` with "file outside my list" | check `pieces.toml` owns it for the piece; a record clerk adds `owns` or `depends_on`; relaunch with `skip` |
| a builder `ok: false` with "a number nobody gave" or a contradiction | consult |
| a checker `pass: false` | relaunch that piece with `skip` for the others; a second failure: consult |
| a clerk `ok: false` with `GATE <stage> REJECT` lines that are footprint, owner_lint, noise or a lint | the pre-gate was skipped or stale: one engineer fixes the candidate and re-lands (a resume, not a new workflow) |
| a clerk `ok: false` with a regression or playthrough REJECT | consult with the REJECT lines and the diff summary |
| a timeout, a hung Godot run, a lost worktree, a killed run (power) | one engineer (rules.md section (b) or (a)) resumes that step on its branch; nothing landed re-runs |
| needs Westley | a "Now" row if one is free, else the waiting list in ROADMAP section 3; tell him in one line |

## Measures (the scorecard, per lane run)

Hours from launch to Westley's verdict on the first shot; landing attempts per landing; full-gate rejects that were non-semantic (footprint, owner rows, noise, lints); ledger rows added (rulings); pieces built before the first human look; Fable consults (count and their tokens); the most workflows in flight at once; `status_check.py` DRIFT lines after the landing; tokens and dollars from the workflow result. The record clerk appends the column to the scorecard table in the programme file.

## Briefs the Dispatcher writes

Engineer briefs for the record clerk, the cleanup clerk, the branch triage clerk and a resume: one page, a single deliverable, the exact file list, the verification command, the report shape, the rules.md section that applies, "model Sonnet 5.5, never spawn sub-agents, think tersely, report once". Never hand an engineer a plan; hand it a role.

Consult briefs for the Architect: the shape in step 5. Never pad with history the ruling does not need.

Reports to Westley: lane, sha, shots, what he must do now, one line each. No narration of what was checked.

## Cascades and the consistency pass (2026-10-21)

From `docs/northstar/plans/2026-10-21-tool-split-spec.md`:

The Dispatcher chat (Sonnet) is the cascade's overlord: it runs `/manager-mode` (hardcore when the cascade touches a save, pipe or checksum path) in a worktree under `~/Projects/om-push/wt/<slug>` on branch `push/<slug>-cascade`, never in the live checkout and never on `main`. The Architect writes the spec, the contract and the umbrella test's assertions (the shard-test-writer writes the per-leaf tests inside the cascade). Leaves are Sonnet 5.5 doers (`DOER_BACKEND`); the test writers and auditors are Sonnet 5.5 (`TEST_WRITER`). No Fable agent is spawned by the cascade. The overlord's own context is the long-lived one; it restarts from its continuation memory past about 400k tokens like any coordinator chat, with the cascade's on-disk records as its state.

For Workflow pieces, the one-agent preflight stop moves out of the script: before a launch, the Dispatcher spawns one Sonnet engineer with the spec paragraph, the pieces row, the ledger rows it names, the rule pins of the tests it names and the script's own preflight list, and that engineer reports every gap in one message. The Architect answers them in one ruling. The script then launches with the gaps closed. Fifteen of the twenty spec-and-records stops of 2026-10-14 to 10-21 would have been one message each instead of a relaunch.
