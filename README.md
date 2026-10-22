# Ouroboros Manifold

A multi-era real-time strategy game set in a living, stochastic galaxy. A simulation written in C drives factions, regions and history; between missions decades pass and the galaxy moves on without you, and the chronicle writes down what happened. In a mission you command a task force on a generated land or space map, and a smaller force that holds the high ground and the right layer beats a larger one that does not. You are a commander, not a god, and the world does not wait. No names, places or plot come from existing fiction.

| The galaxy between missions (B-S106, approved) | The multiplayer lobby (F-S143, approved) |
|---|---|
| ![The star map: owner-coloured systems, translucent faction shells and filaments](docs/northstar/story_reviews/shots/20261013-1406-59a24b4/S-106.png) | ![The lobby showing the one era two players share](docs/northstar/story_reviews/shots/run-20261020T144745Z/S-143_common_eras_pair.png) |

*Left: 80 systems in faction colours, seen from inside the ball. Right: two players with different era packs are shown the one era they share. Plain placeholder lobby, and proud of it.*

## Architecture

- **A C simulation.** The stochastic equations are kept verbatim from the bible's `algorithms.md`. The frozen contract is `csrc/ouroboros_sim.h`.
- **A Godot 4 client over a JSON pipe.** The client draws; the sim decides. The pipe frames are documented in [`docs/architecture.md`](docs/architecture.md).
- **Determinism.** The same seed and command stream give a byte-identical trace on every platform: no fast-math, no platform transcendentals, no hash-order or wall-clock input. The gate compares an `-O0` build against an `-O2` build to keep it honest.
- **No runtime model calls.** The game never asks a model anything. Missing library content falls back to a placeholder.

What the game is lives in the bible: start at [`docs/bible/game_bible.md`](docs/bible/game_bible.md).

## How it is built

Requirements are epics, stories and rules in the bible. A story is built only after it passes a Definition of Ready, and every story exists as failing tests first.

- **Tests are the spec.** Tests sit in fenced paths builders cannot edit, and each names the `S-###` or `R-###-##` it proves. Every detector ships with a positive control.
- **One owner per file.** `docs/northstar/plans/push/pieces.toml` names the owner of every file; two in-flight pieces never own the same one.
- **The merge gate** (`scripts/specfactory/merge_gate.sh`) runs, among others: build, libm lint, algorithm-constants lint, footprint fence, symbol-ownership and reachability lints, single-owner lint, rule pins, the csim, t1 and transport suites, the Godot import, the playthrough, lane plays, `-O0` versus `-O2` checksum and tactical traces, and a status check. `look` (a blank or near-uniform frame check) currently only warns.
- **The playthrough gate.** Every landing is run through a scripted end-to-end playthrough of the real client under xvfb.
- **Drift check and method check.** `status_check.py` diffs the programme's lane table, `pieces.toml` and the review queue against git after every landing. `method_check.py` reads a chat's own transcript at each compaction and prints `DRIFT` lines for rules it broke; a DRIFT line is quoted, never argued away.
- **The ledger and the ambiguity register.** Decisions and rulings are recorded as they happen. Ambiguity is flagged in the register, never guessed, and an epic with an open flag is not built.
- **Workflow or manager-mode.** Which tool builds a piece is chosen by six questions, written into its spec.

The ten-minute version, with links to every source of truth, is [`docs/METHOD.md`](docs/METHOD.md).

## Status

- **Beta engineering:** in flight since 2026-10-07 under the programme's lane table ([`docs/northstar/plans/2026-10-07-visible-game-programme.md`](docs/northstar/plans/2026-10-07-visible-game-programme.md)), which is the only status location. Some lanes are stubs: the layout engine's `om_layout_places` is on main but not yet called by the game, and the lobby's team-size choice is a stub until team scaling.
- **Player acceptance:** 8 of 240 stories are `Seen` (a human looked at the picture and said yes). The terrain-obeys prototype was approved on 2026-10-21 and is approved, not integrated.

## Run it

Needs a C compiler, Python 3, pytest, and Godot 4 on `PATH` (the project's tests use 4.6.3).

```
make                                  # build libouroboros.so and the debug library
make test                             # build, then the fenced C-sim suite (pytest tests/csim)
make pipe/ouroboros_pipe              # the JSON pipe server the client talks to
scripts/run_godot_tests.sh tests/test_c_bridge.gd   # one headless Godot test
python3 -m pytest tests/transport     # pipe tests (build the pipe first)
python3 -m pytest tests/qa/desktop    # desktop driver: the real client, run under xvfb-run
python3 scripts/specfactory/status_check.py         # the drift check
```

The desktop driver is `tests/qa/desktop/daemon_client.py`; story plays live in `tests/qa/desktop/plays/`. The skill lab, which measures tactical combat on the real sim, is `scripts/skilllab/` (see its `README.md`).

## Read next

- [`docs/METHOD.md`](docs/METHOD.md): how this repo is run
- [`docs/README.md`](docs/README.md): a map of `docs/`
- [`docs/bible/game_bible.md`](docs/bible/game_bible.md): what the game is
- [`docs/architecture.md`](docs/architecture.md): the pipe and the contracts
- [`docs/northstar/README.md`](docs/northstar/README.md): the development method in full
- [`CLAUDE.md`](CLAUDE.md): the rules the agents work under
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Licence

MIT. See [`LICENSE`](LICENSE).
