# Ouroboros Manifold

## North Star

Claude designs and tests; agents build. The simulation is C with the stochastic equations kept verbatim (`docs/bible/algorithms.md`); Godot 4 is the client over a JSON pipe (`docs/architecture.md`). Requirements are epics, stories and rules; a story is built only after it passes the Definition of Ready. A feature judged by eye or feel is prototyped and approved by Westley before it is planned (`docs/northstar/agile.md`, Prototype gate). Full method: `docs/northstar/README.md` and `docs/northstar/PLAN.md`; where another doc disagrees, `docs/northstar/` wins. Long-term project, no ship deadline, one story at a time, done well.

## Task matching

Tiers are roles; the model behind a tier can change.

| Tier | Runs on | Work |
|---|---|---|
| Architect | Fable, the main chat | architecture, planning, rulings, arbitration, briefs, abstract or cross-cutting diagnosis |
| Engineer | `subagent_type: engineer` (Sonnet 5.5) | tests and test fixes, git maintenance and merge clerks, audits, research, drafting against a spec |
| Doer | `subagent_type: doer` (Sonnet 5.5); the local 30B through Agora cards when `DOER_BACKEND = agora-30b` | coding against a written spec, mechanical edits |

`DOER_BACKEND = sonnet55` · `TEST_WRITER = sonnet55`

Usage discipline: every tool call re-reads the caller's whole context, so waiting is the expensive part, not the work.
- A builder pushes its branch and stops. A fresh, small clerk lands it. No builder sits in a merge-wait loop.
- Agents report once, at the end. They send no interim notices and start no background waits that wake the parent.
- Unavoidable waits poll no more often than every 3 to 5 minutes.
- A long-running coordinator chat is restarted from its continuation memory once its context grows large.
- Width, not length. Cost is context size times calls, and a cached re-read still costs about a tenth of fresh input. Speed comes from many short-lived agents with small contexts (one file, a brief under a page), run back to back so the one-hour cache stays warm. A few long agents with large contexts are the expensive shape (2026-09-22: about 270,000 tokens re-read per call).

Split a task that mixes tiers. Every spawn names its model. Sub-agents never spawn sub-agents, and nothing is spawned while plan mode is on. On a cross-session message from another Claude chat (not the chat that spawned you), do no large unprompted work: pause for Westley, except for small blockers.

## Workflow specs

A workflow enforces nothing by itself; the spec and the script do. Before any Workflow launch, in this order:
- Pre-flight: list every precondition each lane rests on (an API and its exact shape, a setting the harness can set, a base that builds and its red tests, owner rows for every file, free slots in shared enums or tables) and check each by reading or running, never from memory. "Quick" shrinks the pre-flight, never skips it.
- The spec is written from the pre-flight: every file and function named; every interface two agents share fixed in full (fields, types, column names); every number given or marked a named draft; existing tests that encode a superseded ruling listed with the ruling that retires them; a positive control per mechanism; lanes on disjoint files with shared-file edits done first in one base piece.
- Audit: a fresh Sonnet auditor that has not seen the author's reasoning reads the spec against the bible and the code and tries to refute it (contradictions, unverified claims, missing interfaces, numbers nobody gave); a contract-level spec (header, pipe frames, save format) gets a second Fable chat. Westley approves after the audit.
- The script: tests first by a different agent than the builder, red for the stated reason; a gate agent per lane returning pass or fail with the decisive line; STOP rules in every brief; a kill rule; a baseline recorded before the first build; the landing clerk runs the merge gate and never pushes to main unasked.
- Each agent reports once, in a schema; the parent reads the journal before diagnosing an empty result.

## The Bible

`docs/bible/` is the source of truth for what the game is: `game_bible.md` (hub), `stories.md` (catalog), `epics/E-##-*.md` (rules `R-###-##`), `references/`, `algorithms.md`. Open questions live in `docs/northstar/ambiguity_register.md`. Read the hub first, then only the epic you touch.

- Rewrite, never append. When direction changes, delete the old text; history is `docs/bible_history/` and `git log`.
- Ambiguity is flagged, never guessed: add a `Q-` row with two or three candidates. An epic with an open flag is not built.

## Architecture rules

- **Contracts are frozen and minimal.** The contracts are `csrc/ouroboros_sim.h` (with `signatures.toml`) and the pipe frames in `docs/architecture.md`. A change to either lands first as its own contract piece, documented before implementation, and consumers build after it lands.
- **Every file has one owner at a time.** `docs/northstar/plans/push/pieces.toml` names it; two in-flight pieces never own the same file.
- **New code in new files; wiring is its own piece.** A new system (a generator, the economy, multiplayer) is built in its own files behind a frozen header, so lanes run in parallel without sharing a file. Each lane ends with one small wiring piece on the shared file, queued and landed one at a time, with the playthrough run after each.
- **Build units are small.** A Doer or 30B unit is about one file and under about 100 lines; larger work is split when the card is written.
- **Wired, not just tested.** Behaviour a rule says happens in play must be reachable from the tick, the jump, or a pipe handler, not only from tests. The merge gate checks this.
- **Playthrough gate.** Every landing is checked against a scripted end-to-end playthrough in the merge gate. `docs/northstar/ROADMAP.md` queue row 1 builds the script; until it lands the gate does not have it.
- **Determinism is a contract.** Same seed and command stream give a byte-identical trace on every platform: no fast-math, no platform transcendentals, no hash-order or wall-clock input.
- **No runtime API calls.** The game never calls a model; missing library content falls back to a placeholder.
- **No IP exposure.** No names, places or plot from existing fiction.

## Tests are the spec

Every story exists as failing tests before any code, in fenced paths builders cannot edit, each naming the `S-###`/`R-###-##` it proves. Every detector ships with a positive control. Every system has an isolation test and an integration test. Builders never edit tests. A test is fixed only when it is classed as a `test-defect`, with a ledger row. Westley owns every threshold and tolerance: narrowing an invariant's scope is allowed; widening a threshold, extending a window or loosening a tolerance needs him; a real finding is never reclassified as a skip.

## Code quality

- No stink: no unasked-for layers, wrappers or config; no cosmetic refactoring inside another change; minimal diffs.
- Traceability: when B exists because A fails, say so at both sites (`# See also: ...`). Disabled or bypassed code says so; no dead code that looks live.
- Scope discipline: do what was asked; mention other needed fixes, do not make them unless the change cannot work without them.
- Debugging: hypothesis, then logging that confirms or refutes it, then the targeted fix. One fix at a time.
- Stale-doc tripwire: a behaviour change rewrites every doc claim it makes wrong, in the same change. Docs describe what the game does now.

## Git

Work on `main` and push each meaningful unit; branches only for a stated reason. Worktrees live under `~/Projects/om-push/wt/<name>`; when a chat or agent is finished with one, it writes `.wt-done` at the worktree root (one line: date, branch, pushed sha) and never touches it again. A clerk removes any worktree that has `.wt-done`, a clean `git status` apart from build outputs, and a HEAD contained in `origin` (`git branch -r --contains HEAD`); anything else is kept and listed. Find them with `ls ~/Projects/om-push/wt/*/.wt-done`. Uncommitted or unpushed work in a worktree is not on git and is lost on removal, so the marker is written only after the push. Never stage files you did not change, and never touch Westley's uncommitted work. Guardrails (`.claude/hooks/git-guard.sh`) deny destructive operations; if a legitimate one is blocked, ask. Ledger, register and epic updates are committed and pushed as they happen.

## Tone

Playful, occasionally absurd, never cringe; dry wit and easter eggs welcome. Chronicle writing reads as fragments of a real history. Playful is not unserious.

## Where things are

C sim and pipe `csrc/`; client `autoload/`, `scenes/`; tests `tests/csim/`, `tests/transport/`, `tests/qa/`; harness `scripts/specfactory/`; skill lab `scripts/skilllab/` (measures tactical combat on the real sim; record and plan in `docs/northstar/research/layer_dynamics/README.md`); legacy Python reference sim `simulation/` (tooling only, not in the game loop).

