# Ouroboros Manifold

## North Star

Claude designs and tests; agents build. The simulation is C with the stochastic equations kept verbatim (`docs/bible/algorithms.md`); Godot 4 is the client over a JSON pipe (`docs/architecture.md`). Requirements are epics, stories and rules; a story is built only after it passes the Definition of Ready. Full method: `docs/northstar/README.md` and `docs/northstar/PLAN.md`; where another doc disagrees, `docs/northstar/` wins. Long-term project, no ship deadline, one story at a time, done well.

## Task matching

Tiers are roles; the model behind a tier can change.

| Tier | Runs on | Work |
|---|---|---|
| Architect | Fable, the main chat | architecture, planning, rulings, arbitration, briefs, abstract or cross-cutting diagnosis |
| Engineer | `subagent_type: engineer` (Sonnet 5) | tests and test fixes, git maintenance and merge clerks, audits, research, drafting against a spec |
| Doer | `subagent_type: sonnet46-doer` today; the local 30B through Agora cards when `DOER_BACKEND = agora-30b` | coding against a written spec, mechanical edits |

`DOER_BACKEND = sonnet46` · `TEST_WRITER = sonnet5`

Split a task that mixes tiers. Every spawn names its model. Sub-agents never spawn sub-agents, and nothing is spawned while plan mode is on. On a message from another chat, do no large unprompted work: pause for Westley, except for small blockers.

## The Bible

`docs/bible/` is the source of truth for what the game is: `game_bible.md` (hub), `stories.md` (catalog), `epics/E-##-*.md` (rules `R-###-##`), `references/`, `algorithms.md`. Open questions live in `docs/northstar/ambiguity_register.md`. Read the hub first, then only the epic you touch.

- Rewrite, never append. When direction changes, delete the old text; history is `docs/bible_history/` and `git log`.
- Ambiguity is flagged, never guessed: add a `Q-` row with two or three candidates. An epic with an open flag is not built.

## Architecture rules

- **Contracts are frozen and minimal.** The contracts are `csrc/ouroboros_sim.h` (with `signatures.toml`) and the pipe frames in `docs/architecture.md`. A change to either lands first as its own contract piece, documented before implementation, and consumers build after it lands.
- **Every file has one owner at a time.** `docs/northstar/plans/push/pieces.toml` names it; two in-flight pieces never own the same file.
- **Build units are small.** A Doer or 30B unit is about one file and under about 100 lines; larger work is split when the card is written.
- **Wired, not just tested.** Behaviour a rule says happens in play must be reachable from the tick, the jump, or a pipe handler, not only from tests. The merge gate checks this.
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

Work on `main` and push each meaningful unit; branches only for a stated reason. Never stage files you did not change, and never touch Westley's uncommitted work. Guardrails (`.claude/hooks/git-guard.sh`) deny destructive operations; if a legitimate one is blocked, ask. Ledger, register and epic updates are committed and pushed as they happen.

## Tone

Playful, occasionally absurd, never cringe; dry wit and easter eggs welcome. Chronicle writing reads as fragments of a real history. Playful is not unserious.

## Where things are

C sim and pipe `csrc/`; client `autoload/`, `scenes/`; tests `tests/csim/`, `tests/transport/`, `tests/qa/`; harness `scripts/specfactory/`; legacy Python reference sim `simulation/` (tooling only, not in the game loop).

