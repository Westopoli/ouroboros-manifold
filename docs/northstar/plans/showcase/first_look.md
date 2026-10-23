# First look: the first ten minutes (SHOWCASE-first-look)

A cold read of branch `push/showcase-fl2` on 2026-10-23, by a Sonnet reader who had not seen the repo. I read `README.md`, `docs/METHOD.md`, `docs/README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, the top of `docs/bible/game_bible.md`, and the `pieces.toml` header. I looked at the test and decisions pages and ran `make`, `make test` and `status_check.py`. I opened the plan pages under `docs/northstar/plans/showcase/` last.

## 1. What the game is

A multi-era real-time strategy game set in a simulated galaxy. A C simulation moves factions and history along while you are away between missions. In a mission you command a task force, and positioning (high ground, the right layer) beats numbers. The sentence that told me: "A multi-era real-time strategy game set in a living, stochastic galaxy... a smaller force that holds the high ground and the right layer beats a larger one that does not" (`README.md:3`). The bible hub (`docs/bible/game_bible.md`) says the same at more length and adds multiplayer and a 2.5D layer-and-vision system. The README is honest that this is not shipped: 8 of 240 stories are "Seen" and some lanes are stubs (`README.md:36-37`).

## 2. How it is built, and where the proof is

- **Sim.** About 50 C files under `csrc/` (roughly 33k lines in the top-level `.c` files). The contract is `csrc/ouroboros_sim.h`. The equations are said to be verbatim from `docs/bible/algorithms.md`. Determinism is a stated contract, checked by comparing an `-O0` build with an `-O2` build (`README.md:15`).
- **Client.** Godot 4 under `autoload/` and `scenes/`, talking to the sim over a JSON pipe. The frames are in `docs/architecture.md`, and the pipe server is under `csrc/pipe/`.
- **Proof.** Fenced tests: 311 `tests/csim/test_*.py` files plus Godot `.gd` tests at `tests/` top level, `tests/transport`, `tests/qa/desktop` (a real-client driver) and `tests/skilllab`. The gate is `scripts/specfactory/merge_gate.sh` (708 lines), with its lint and harness code under `scripts/specfactory/` (60 entries at top level). The csim test I opened (`tests/csim/test_E04_S027_one_thing_leads_to_another.py`) names its story and rule ids in the docstring and test names, as claimed.
- **What I ran.** `make` built the shared library and the debug library in about 29 seconds (`/tmp/fl_make.txt`). `make test` failed at once with `No module named pytest`. The README does list pytest as a prerequisite, so that is my machine, but the failure is abrupt and I could not see a test pass. `python3 scripts/specfactory/status_check.py` ran with no FAIL lines (26 OK or WARN lines, including three WARNs about review verdict cells missing `legend=, unit=, band=`).

## 3. The method as I understood it

Claude designs and writes tests; cheaper agents build; tests are written first and builders cannot edit them. Every file has one owner at a time (`docs/northstar/plans/push/pieces.toml`, `owner_lint.py`). Nothing reaches `main` except through the merge gate. One status table (the lane table in `docs/northstar/plans/2026-10-07-visible-game-programme.md`) is diffed against git by `status_check.py`. `method_check.py` audits the chat's own behaviour at each compaction. Ambiguity goes in a register, not into a guess. Decisions are logged in `docs/northstar/story_reviews/westley/decisions.md`, with the owner's veto. Roles are Architect (Fable), Dispatcher (Sonnet), and engineers or doers (Sonnet). There is a Workflow versus manager-mode split, with a measured retro (`docs/northstar/plans/retro_2026-10-21/workflows_vs_manager_mode.md`), including a candid record that 2 of 32 workflow runs completed clean.

The evidence is mostly where the README says. The gate script, the lane table, `pieces.toml`, the decisions page and the shots the README embeds all exist. I did not run the gate or confirm that the known-red lists are short (they are 25, 4 and 4 lines). The proof that the method works is mostly the method's own records, which the author wrote. I could not check them independently in ten minutes.

## 4. What I could not find or did not understand

- A way to see the game run without Godot and a desktop session: README "Run it" gives no download, video or play-by-play. Looked in `README.md` and `docs/README.md`.
- Which tests are green on `main` today: no CI badge or recent gate result. Looked in `README.md`, `docs/METHOD.md`.
- What `make test` covers beyond the csim: it only runs `pytest tests/csim` (`Makefile:100`). The Godot, transport and playthrough suites need other commands.
- Why the dev build still spawns the legacy Python sim (`autoload/sim_bridge.gd:35`, `SIM_SCRIPT_PATH := "simulation/pipe_transport.py"`) when `CLAUDE.md` calls it "tooling only". The plan pages name it as a finding.
- Who the "Westley" in the docs is relative to the author. The README never introduces them or names the author. `LICENSE` presumably does.
- The meaning of many internal ids (`VG-C2-5-glowkey`, `TD-HARNESS-...`, `DEC-...`) in `CLAUDE.md` and the decisions page. There is no glossary.
- How "8 of 240 Seen" counts: `docs/bible/stories.md` has about 8 rows marked Seen plus a few "Seen; ..." variants.
- The size of the "Architect" and "Dispatcher" cost: the retro quotes $1,763 for one week, but I did not find a page tying spend to what shipped beyond that retro.

## 5. Three that impressed, three that put me off

Impressed:
1. The honest status in `README.md:34-37` and `docs/METHOD.md`'s measured retro: stubs are labelled, "approved, not integrated" is a defined phrase, and failures (20 of 32 runs stopped on spec gaps) are published.
2. Every story as a failing test first, with ids in the file names (`tests/csim/test_E04_S027_*`), plus "every detector ships with a positive control" (`CONTRIBUTING.md`). That is a discipline I rarely see.
3. A real determinism contract with a mechanical check (`-O0` versus `-O2` checksums in `scripts/specfactory/merge_gate.sh`), and the equations kept in one page (`docs/bible/algorithms.md`).

Put off:
1. The repo is dominated by process records. `docs/northstar/plans/` has about 67 entries, `docs/northstar/` is huge, and `CLAUDE.md` is 97 lines of dense, dated rule text. It is hard to tell the product from the paperwork. See `docs/README.md`'s own "Still to move" list.
2. Leftovers the README does not mention: `simulation/` (246 files at the root) is a legacy sim the dev client still launches, and `legacy/README.md` says `scenes/debug` moved while `scenes/debug/debug_ws_test.gd` is still there.
3. Very little shown in motion: two stills in the README, 8 stories seen. `reach_lint.py` reportedly fails on 250 of 779 tested public symbols (`docs/northstar/plans/showcase/code_quality.md`), which I read last. A reader would want that said up front.

## 6. Verdict

Yes, I would interview this author: the discipline around tests, ownership, determinism and honest measurement is unusual and well documented, though I would ask them what a human shipped here beyond the agent process, and for a demo.

## Do the plan pages match?

I read `showcase/README.md`, the top of `code_quality.md` and `inventory.md` last. They match what I found: the README, METHOD, `docs/README.md`, CONTRIBUTING and LICENSE the plan promised exist, and the junk and legacy moves are partly done (`toys/` is gone, `legacy/toys` exists). The plan's open items (the dev-build Python spawn, `simulation/` still at root, `reach_lint` failures) are the same gaps I listed. Two differences: `code_quality.md` gives 39,821 `csrc` lines where I counted about 33k (it includes headers and `csrc/pipe/`), and the plan's Step 5 asks for a reader to "find the game, the architecture and the method within the README's links", which I did, apart from running the tests.
