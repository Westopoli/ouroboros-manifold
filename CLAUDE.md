# Ouroboros Manifold

## North Star

Claude designs and tests; agents build. The simulation is C with the stochastic equations kept verbatim (`docs/bible/algorithms.md`); Godot 4 is the client over a JSON pipe (`docs/architecture.md`). Requirements are epics, stories and rules; a story is built only after it passes the Definition of Ready. A feature judged by eye or feel is prototyped and approved by Westley before it is planned (`docs/northstar/agile.md`, Prototype gate). Full method: `docs/northstar/README.md` and `docs/northstar/PLAN.md`; where another doc disagrees, `docs/northstar/` wins. Method text (this file, `docs/northstar/plans/workflows_2026-10-07/`, `docs/northstar/README.md`, `PLAN.md`) changes only in a commit that also adds to a `retro_*` folder, at most one retro per 14 days; weekly numbers: `scripts/specfactory/method_metrics.py`. Long-term project, no ship deadline, one story at a time, done well.

## Task matching

Tiers are roles; the model behind a tier can change.

| Tier | Runs on | Work |
|---|---|---|
| Architect | Fable: a short-lived chat that restarts from memory past about 400k context, or `subagent_type: architect` (read-only, spawned only by the Dispatcher with a brief under a page) | architecture, planning, contract specs (header, pipe frames, save format), rulings, arbitration, abstract or cross-cutting diagnosis; the per-piece spec paragraph and the review of a built piece are Sonnet work |
| Dispatcher | Sonnet 5.5, the main chat while a build programme runs (`docs/northstar/plans/workflows_2026-10-07/dispatcher.md`) | pre-flights and launches the Architect's scripts, lands through clerks, keeps the one status table, queues shots for Westley, consults the Architect by brief; decides nothing about rules, thresholds, specs or tests; runs a Manager Mode cascade as its overlord when the spec's `Tool:` line says cascade |
| Engineer | `subagent_type: engineer` (Sonnet 5.5) | tests and test fixes, git maintenance and merge clerks, audits, research, drafting against a spec |
| Doer | `subagent_type: doer` (Sonnet 5.5); the local 30B through Agora cards when `DOER_BACKEND = agora-30b` | coding against a written spec, mechanical edits |

`DOER_BACKEND = sonnet55` · `TEST_WRITER = sonnet55`

Decisions: Westley answers looks (one word per picture) and rule meaning where he has no recorded words. Everything else the Architect decides, records in `docs/northstar/story_reviews/westley/decisions.md` (decision, rule, context) and Westley may veto (Westley, 2026-10-22).

Usage discipline: every tool call re-reads the caller's whole context, so waiting is the expensive part, not the work.
- A builder pushes its branch and stops. A fresh, small clerk lands it. No builder sits in a merge-wait loop.
- Agents report once, at the end. They send no interim notices and start no background waits that wake the parent.
- Unavoidable waits poll no more often than every 3 to 5 minutes.
- A coordinator chat restarts from its continuation memory once its context passes about 400k tokens (Westley, 2026-10-13). Measured 2026-10-07 to 10-10: two Architect sessions polled gates at a median 319k to 465k tokens per turn and cost $1,130 of the programme's $1,487; their judgement turns paid for themselves, their waiting turns did not (`docs/northstar/plans/retro_2026-10-10/README.md`). Waiting belongs to a Sonnet Dispatcher; judgement comes from the Architect by brief. Enforced since 2026-10-24 by the hook `.claude/hooks/context_guard.py` (HARNESS-context-guard) under `UserPromptSubmit` and `PreToolUse`: past DRAFT-context-guard-tokens (400000) every prompt and tool call is blocked, except a prompt containing "handoff" or a Write/Edit under `~/.claude/projects/`, which let the memory write through; and the project `.claude/settings.json` sets `autoCompactWindow` 200000 (DRAFT-autocompact-window), so a chat under this repo compacts at 200k and no call pays for more.
- One Architect chat and one Dispatcher chat at a time; a third coordinator is an exception row.
- Width, not length. Cost is context size times calls, and a cached re-read still costs about a tenth of fresh input. Speed comes from many short-lived agents with small contexts (one file, a brief under a page), run back to back so the one-hour cache stays warm. A few long agents with large contexts are the expensive shape (2026-09-22: about 270,000 tokens re-read per call).

Split a task that mixes tiers. Every spawn names its model and starts its description with `<piece id> <role>` (roles: spec, tests, build, land, audit); every report starts with one line `RESULT success|stop:<reason>`. Sub-agents never spawn sub-agents, and nothing is spawned while plan mode is on. `architect` is Fable by definition, read-only, and is spawned only by the Dispatcher chat; engineers and doers are never Fable. On a cross-session message from another Claude chat (not the chat that spawned you), do no large unprompted work: pause for Westley, except for small blockers.

## Workflow specs

Choosing the tool (Westley, 2026-10-21). Before anything is launched, the Architect assesses the work and writes a `Tool:` line in its spec paragraph: a `/manager-mode` cascade (the Dispatcher chat as overlord, Sonnet leaves) for a sim-side cluster of three or more file-disjoint units that share one spec, one contract and one umbrella test, every unit a failing test that runs without a frame, every number in the spec or a named draft; a Workflow for anything that ends in a frame (client pieces, plays, shots, the look stage), any single piece, any contract piece, any build that must stop for Westley mid-way, and every landing. A cascade lands on `push/<slug>-cascade` and goes through the landing clerk and the merge gate like any branch. The six questions and the measured record: `docs/northstar/plans/2026-10-21-tool-split-spec.md` (2026-10-14 to 10-21: 20 of 32 Workflow runs stopped on spec or records gaps; the one cascade run built 9 leaves in 90 minutes).

A workflow enforces nothing by itself; the spec and the script do. Before any Workflow launch, in this order:
- Pre-flight: list every precondition each lane rests on (an API and its exact shape, a setting the harness can set, a base that builds and its red tests, owner rows for every file, free slots in shared enums or tables) and check each by reading or running, never from memory. "Quick" shrinks the pre-flight, never skips it.
- Skeleton first: a lane's first piece is the thinnest end-to-end path in the real scene from the real frame, with a screenshot Westley sees; contracts freeze after it runs, and the lane's fan-out waits for his verdict (2026-10-07 to 10-10: every lane fanned out first, and every first look failed with green tests).
- The spec is written from the pre-flight: every file and function named; every interface two agents share fixed in full (fields, types, column names); every number given or marked a named draft; existing tests that encode a superseded ruling listed with the ruling that retires them; a positive control per mechanism; lanes on disjoint files with shared-file edits done first in one base piece.
- Audit, for a contract spec or the beta list only: a fresh Sonnet auditor that has not seen the author's reasoning reads the spec against the bible and the code and tries to refute it (contradictions, unverified claims, missing interfaces, numbers nobody gave); a contract-level spec (header, pipe frames, save format) gets a second Fable chat. Westley approves after the audit.
- The script: for sim, pipe and lab pieces, tests first by a different agent than the builder, red on the built tree (the stub or the previous piece) for the stated reason, with the failing assertion line pasted and a positive control green; the landing clerk applies the rulebook to a builder's test-defect stop and writes `ruler=clerk` in the row; only new rule meaning goes to the Architect (`ruler=fable`); `scripts/specfactory/pre_gate.sh` runs before every push and before the gate lock, so a lint or noise reject never costs a full gate; at most one subscription build (a Workflow) and three credit-pipeline builds in flight until the console credit expires on 2026-10-24, then one build of either kind; one landing (Westley 2026-10-23: "excellerate our parrallelism, but only from the workflows and things that we can use the console credit for"; earlier that day: one build; two before; four on 2026-10-21); a gate agent per lane returning pass or fail with the decisive line; STOP rules in every brief; a baseline recorded before the first build; the landing clerk runs the merge gate and never pushes to main unasked.
- Each agent reports once, in a schema; the parent reads the journal before diagnosing an empty result.

## The Bible

`docs/bible/` is the source of truth for what the game is: `game_bible.md` (hub), `stories.md` (catalog), `epics/E-##-*.md` (rules `R-###-##`), `references/`, `algorithms.md`. Open questions live in `docs/northstar/ambiguity_register.md`. Read the hub first, then only the epic you touch.

- Rewrite, never append. When direction changes, delete the old text; history is `docs/bible_history/` and `git log`.
- Ambiguity is flagged, never guessed: add a `Q-` row with two or three candidates. An epic with an open flag is not built.

## Architecture rules

- **Contracts are frozen and minimal.** The contracts are `csrc/ouroboros_sim.h` (with `signatures.toml`) and the pipe frames in `docs/architecture.md`. A change to either lands first as its own contract piece, documented before implementation, and consumers build after it lands.
- **Every file has one owner at a time.** `docs/northstar/plans/push/pieces.toml` names it; two in-flight pieces never own the same file.
- **New code in new files; wiring is its own piece.** A new system (a generator, the economy, multiplayer) is built in its own files behind a frozen header, so lanes run in parallel without sharing a file. Each lane ends with one small wiring piece on the shared file, queued and landed one at a time, with the playthrough run after each.
- **Build units are one responsibility.** A Sonnet piece is one coherent responsibility: at most one cross-cutting concern, two or three outside integrations, rule clusters that share a failure domain (manager-mode decomposition rule, research 2026-08); the line cap is 1,000 and the complexity gate (cyclomatic 10, nesting 3) is advisory. A 30B card stays about one file under about 100 lines.
- **Wired, not just tested.** Behaviour a rule says happens in play must be reachable from the tick, the jump, or a pipe handler, not only from tests. The merge gate checks this.
- **Playthrough gate.** Every landing is checked against a scripted end-to-end playthrough in the merge gate. `docs/northstar/ROADMAP.md` queue row 1 builds the script; until it lands the gate does not have it.
- **Determinism is a contract.** Same seed and command stream give a byte-identical trace on every platform: no fast-math, no platform transcendentals, no hash-order or wall-clock input.
- **No runtime API calls.** The game never calls a model; missing library content falls back to a placeholder.
- **No IP exposure.** No names, places or plot from existing fiction.

## Tests are the spec

Every sim, pipe and lab story exists as failing tests before any code, in fenced paths builders cannot edit, each naming the `S-###`/`R-###-##` it proves. A client or look piece asserts its `qa_state()` element inventory in a test its builder writes and ships a shot; no separate tests writer. Every detector ships with a positive control. Every system has an isolation test and an integration test. Builders never edit tests. A test is fixed only when it is classed as a `test-defect`, with a ledger row. Westley owns every threshold and tolerance: narrowing an invariant's scope is allowed; widening a threshold, extending a window or loosening a tolerance needs him; a real finding is never reclassified as a skip.

## Visible-game guards

Plan: `docs/northstar/plans/2026-10-07-visible-game-programme.md`. A story is done when the player has seen it.

1. **Visual definition of done.** A player-facing piece asserts a deterministic element inventory from `qa_state()` in its tests and attaches a desktop-driver screenshot set to its landing report; a human sees it before "done". The gate's `look` stage rejects a blank or near-uniform frame. Per piece, not per lane: the landing clerk copies the piece's shot into `docs/northstar/story_reviews/` with a queue row and a plainly named copy in `story_reviews/westley/` with a row in its README (the page table), and the lane's next look piece waits for Westley's verdict on it; the verdict's commit deletes the copy and its row (Westley, 2026-10-13).
2. **Stories acted out.** Every lane names its stories. Each has a `story play` (scripted desktop-driver scenario, `qa_state()` plus screenshot) judged by a model reviewer against the story's words and `references/E-##/`. Answers go to a review queue; `stories.md` moves to `Seen` only on Westley's approval.
3. **No deletion without parity.** Removing a working feature needs a test listing what it showed, green on the replacement first.
4. **Approved means scheduled.** When a mockup is approved, ROADMAP section 1 gets its integration lane that day, with position and owner. "Approved, not integrated" is said in every status report.
5. **Reporting.** Every status has two columns: works (tests) and what the player sees (stories Seen). Say "stub" when it is one.
6. **Play it.** The 30B plays current main nightly after each landing; Westley or the Architect looks at least weekly.
7. **Drift check.** Status lives in one place: the lane table of the programme file; ROADMAP points at it, the journal is `git log` (`scripts/journal.sh`), and a chat's memory holds a pointer plus its last three steps. After every landing `scripts/specfactory/status_check.py` diffs that table, `pieces.toml` and the review queue against git and fails on a mismatch; at least weekly a fresh Sonnet drift auditor checks rulings against every epic they touch and scope nobody asked for (the procedure, brief and schema: `docs/northstar/plans/workflows_2026-10-07/drift_audit.md`). Its report goes to Westley unedited; drift found is fixed before new lanes launch. The method is checked the same way: at every compaction a `SessionStart` hook runs `scripts/specfactory/method_check.py` on the chat's own transcript and prints, per rule, how many turns broke it with the decisive lines, then the role's rule list (`docs/northstar/plans/workflows_2026-10-07/method_check.md`); the chat quotes every DRIFT line to Westley before any other work and stops the behaviour. A DRIFT line is never argued away: a rule change is his, an exception is a ledger row.

## Code quality

- No stink: no unasked-for layers, wrappers or config; no cosmetic refactoring inside another change; minimal diffs.
- Traceability: when B exists because A fails, say so at both sites (`# See also: ...`). Disabled or bypassed code says so; no dead code that looks live.
- Scope discipline: do what was asked; mention other needed fixes, do not make them unless the change cannot work without them.
- Debugging: hypothesis, then logging that confirms or refutes it, then the targeted fix. One fix at a time.
- Stale-doc tripwire: a behaviour change rewrites every doc claim it makes wrong, in the same change. Docs describe what the game does now.

## Git

Work on `main` and push each meaningful unit; branches only for a stated reason. Worktrees live under `~/Projects/om-push/wt/<name>` and are made and finished only through `scripts/specfactory/wt.py` (HARNESS-wt-cap, Westley 2026-10-24): `wt.py new <name> --owner <chat or clerk> --purpose <words>` creates one (it refuses at the active-slot cap, DRAFT-wt-active-slots 12, when `/` has under DRAFT-wt-free-floor-gb 60 GB free, or when `wt/` would pass DRAFT-wt-disk-cap-gb 120 GB) and writes `.wt-state active ...`; a bare `git worktree add` under `wt/` is a bypass the status check flags. When a chat or agent is finished with one, it runs `wt.py done <path> <pushed sha>` (it writes `.wt-done`, one line: date, branch, pushed sha, and flips the flag to `finished`; it refuses a sha that is not on origin, so the marker comes only after the push) and never touches the tree again. A clerk removes finished worktrees with `wt.py reap` (dry run first; literal paths; a tree is removed only when clean apart from build outputs, with HEAD contained in `origin` and no open files; `active`, `pinned` and `pending` trees are never touched; anything kept is listed with its reason); `wt.py status` is the inventory. Westley 2026-10-21: Godot .import sidecars and dist/ count as build outputs for removal (the full list is DRAFT-wt-build-outputs); an unflagged worktree that is clean, has HEAD on origin and is older than three days is removable. Uncommitted or unpushed work in a worktree is not on git and is lost on removal. Never stage files you did not change, and never touch Westley's uncommitted work. Godot's `.uid` sidecar beside a script is committed with the script (Westley, 2026-10-12): it is the stable id scenes reference, not a build output. Guardrails (`.claude/hooks/git-guard.sh`) deny destructive operations; if a legitimate one is blocked, ask. One ledger row per landing, written by the landing clerk; a `DRAFT-` row only when a number is new; register and epic updates with the landing that needs them. A records-only push takes `~/Projects/om-push/records.lock`, never the gate lock (DEC-records-lock, 2026-10-23).

## Tone

Playful, occasionally absurd, never cringe; dry wit and easter eggs welcome. Chronicle writing reads as fragments of a real history. Playful is not unserious.

## Where things are

C sim and pipe `csrc/`; client `autoload/`, `scenes/`; tests `tests/csim/`, `tests/transport/`, `tests/qa/`; harness `scripts/specfactory/`; skill lab `scripts/skilllab/` (measures tactical combat on the real sim; record and plan in `docs/northstar/research/layer_dynamics/README.md`); legacy Python reference sim `simulation/` (tooling only, not in the game loop).

