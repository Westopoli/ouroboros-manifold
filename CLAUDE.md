# Ouroboros Manifold

## North Star

Claude designs and tests; agents build. The simulation is C with the stochastic equations kept verbatim (`docs/bible/algorithms.md`); Godot 4 is the client over a JSON pipe (`docs/architecture.md`). Stories are the requirements; a story is built only after it is Ready, and judged by Westley in a scene he plays. Long-term project, no ship deadline, one story at a time, done well.

## Method

`docs/method/README.md`. Each role reads its own card there and the story it is given. Where another document disagrees, `docs/method/` wins. Decisions: Westley answers looks and rule meaning where he has no recorded words; everything else the Architect decides, records in `docs/northstar/story_reviews/westley/decisions.md`, and Westley may veto.

## The Bible

`docs/bible/` is the source of truth for what the game is: `game_bible.md` (hub), `stories.md` (catalog), `epics/E-##-*.md` (rules `R-###-##`), `references/`, `algorithms.md`. Open questions live in `docs/northstar/ambiguity_register.md`. Read the hub first, then only the epic you touch.

- Rewrite, never append. When direction changes, delete the old text; history is `docs/bible_history/` and `git log`.
- Ambiguity is flagged, never guessed: add a `Q-` row with two or three candidates. An epic with an open flag is not built.

## Architecture rules

- **Contracts are frozen and minimal.** The contracts are `csrc/ouroboros_sim.h` (with `signatures.toml`) and the pipe frames in `docs/architecture.md`. A change to either lands first as its own contract story, documented before implementation, and consumers build after it lands.
- **New code in new files; wiring is its own commit.** A new system is built in its own files behind a frozen header; the wiring commit on the shared file comes last.
- **Wired, not just tested.** Behaviour a rule says happens in play must be reachable from the tick, the jump, or a pipe handler, not only from tests.
- **Played, not just green.** Every landing opens the merged game and reaches the story's scene before the push counts, and the scripted end-to-end playthrough runs in every sweep of main.
- **Determinism is a contract.** Same seed and command stream give a byte-identical trace on every platform: no fast-math, no platform transcendentals, no hash-order or wall-clock input.
- **No runtime API calls.** The game never calls a model; missing library content falls back to a placeholder.
- **No IP exposure.** No names, places or plot from existing fiction.

## Tests are the spec

Every story exists as failing tests before any code, in fenced paths builders cannot edit, each naming the `S-###`/`R-###-##` it proves. Every detector ships with a positive control. Every system has an isolation test and an integration test. Builders never edit tests; a test changes only under `docs/method/rulebook.md`, with a `Test-defect:` trailer. Westley owns every threshold and tolerance: narrowing an invariant's scope is allowed; widening a threshold, extending a window or loosening a tolerance needs him; a real finding is never reclassified as a skip. No deletion without parity.

## Code quality

- No stink: no unasked-for layers, wrappers or config; no cosmetic refactoring inside another change; minimal diffs.
- Traceability: when B exists because A fails, say so at both sites (`# See also: ...`). Disabled or bypassed code says so; no dead code that looks live.
- Scope discipline: do what was asked; mention other needed fixes, do not make them unless the change cannot work without them.
- Debugging: hypothesis, then logging that confirms or refutes it, then the targeted fix. One fix at a time.
- Stale-doc tripwire: a behaviour change rewrites every doc claim it makes wrong, in the same change.

## Git

One story, one branch `s/<id>-<slug>`, one `--no-ff` merge on main (`docs/method/story_loop.md`). Never touch `~/Projects/ouroboros-manifold` as a working tree. Worktrees live under `~/Projects/om-push/wt/<name>` and are made and finished only through `scripts/specfactory/wt.py new` and `wt.py done <path> <pushed sha>`; `wt.py reap` removes finished trees (dry run first, literal paths); `wt.py status` is the inventory. Never stage files you did not change, and never touch Westley's uncommitted work. Godot's `.uid` sidecar beside a script is committed with the script. Guardrails (`.claude/hooks/git-guard.sh`) deny rebase, force and other destructive operations; if a legitimate one is blocked, ask. A records-only push takes `~/Projects/om-push/records.lock`; a landing takes `gate.lock`. Commit trailers are the record: `Story:`, `Tests:`, `Play:`, `Played:`, `Gate:`, `Flag:`, `Base:`, `Test-defect:`, `Decision:`, `Finding:`, `Verdict:`.

## Usage

Every tool call re-reads the caller's whole context, so waiting is the expensive part. A builder pushes and stops; a fresh clerk lands. Agents report once, at the end. Waits are `flock -w`, never a polling chat. Small context per call: one card and one story per agent, briefs by file path, a mixed-role task split into one brief per role. Every spawn names its model; sub-agents never spawn; nothing is spawned in plan mode; engineers and doers are never Fable. Chats compact at 400k; there is no hard stop. Build plus tests is at least half of weekly model spend.

## Tone

Playful, occasionally absurd, never cringe; dry wit and easter eggs welcome. Chronicle writing reads as fragments of a real history. Playful is not unserious.

## Where things are

C sim and pipe `csrc/`; client `autoload/`, `scenes/`; tests `tests/csim/`, `tests/transport/`, `tests/qa/`, `tests/method/`; harness `scripts/specfactory/`, `scripts/method/`, `scripts/play.sh`; skill lab `scripts/skilllab/`; legacy Python reference sim `simulation/` (tooling only, not in the game loop).
