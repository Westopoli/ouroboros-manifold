# SHOWCASE first look: the first ten minutes

A cold read by a Sonnet reader who had not seen the repository. The showcase plan pages were read last.

## 1. What the game is

A multi-era real-time strategy game on a generated land or space map, set in a galaxy that a stochastic simulation keeps running between missions. The sentence that told me: "A multi-era real-time strategy game set in a living, stochastic galaxy. A simulation written in C drives factions, regions and history; between missions decades pass and the galaxy moves on without you, and the chronicle writes down what happened" (`README.md:3`). The same paragraph carries the design bet, that a smaller force holding the high ground and the right layer beats a larger one that does not. Two screenshots follow, a star map and a multiplayer lobby, and both files exist.

## 2. How it is built, and where the proof is

- **Sim:** C in `csrc/` (about 45 files). The frozen contract is `csrc/ouroboros_sim.h`. The stochastic equations are kept verbatim from `docs/bible/algorithms.md`.
- **Client:** Godot 4 (`scenes/`, `autoload/`, `project.godot`). It draws and the sim decides.
- **Pipe:** a JSON pipe server (`make pipe/ouroboros_pipe`). The frames are in `docs/architecture.md`.
- **Determinism:** one seed plus one command stream gives a byte-identical trace. The gate compares `-O0` against `-O2` (`README.md:15`). The Makefile compile line shows the discipline: `-fno-fast-math -ffp-contract=off -mfpmath=sse`.
- **Proof, tests:** `tests/csim` holds 320 entries, with 311 `test_*` files. Filenames carry story ids (`test_E17_S190_spawn_on_ground.py`). There are also `tests/transport`, `tests/qa/desktop` (a desktop driver with story plays), Godot `test_*.gd` files and `tests/specfactory`.
- **Proof, gate:** `scripts/specfactory/merge_gate.sh` (stages listed in its header and in `docs/METHOD.md`), `pre_gate.sh` and `status_check.py`. Known-red lists sit beside them.

## 3. The method as I understood it

Claude designs specs and tests, and cheaper agents build. Tests are written first in paths builders may not edit, and each names the `S-###` or `R-###-##` it proves. `docs/northstar/plans/push/pieces.toml` (296 piece tables) names one owner per file, and `owner_lint.py` checks it. Everything reaches main through the gate. The ledger and the ambiguity register record what landed and what is open. A human owner, Westley, approves pictures and rule meaning. Every other decision goes into `docs/northstar/story_reviews/westley/decisions.md`, which he may veto. `CLAUDE.md` is the rule sheet for the agents.

Is the evidence where the README says it is? Mostly yes. These were present and matched: `merge_gate.sh`, `pre_gate.sh`, `status_check.py`, `method_check.py`, `pieces.toml`, `decisions.md` (44 lines, dated rows with rule and context), the screenshot shots, and the three known-red lists. The README says "8 of 240 stories are Seen"; `docs/bible/stories.md` has 240 rows and 8 of them start with `Seen`, so that claim checks out. The README is also honest about stubs (the layout engine's `om_layout_places`, the lobby team size) and about `look` only warning.

## 4. What I could not find or did not understand

- `make test` failed at once: `No module named pytest`. I looked in the system Python. The README lists pytest as a prerequisite, but there is no requirements file or venv hint.
- `merge_gate.sh` hard-codes `PYTHON=/home/westopoli/Projects/agora/.venv/bin/python` (line 22). That is a machine-specific path to a sibling project, so a stranger cannot run the gate. I looked in `scripts/specfactory/merge_gate.sh` and the README.
- "Agora" and "the 30B" appear in `CLAUDE.md` and `docs/README.md` with no explanation. I looked in the README and METHOD.md. The reader has to dig into `docs/northstar/` to learn that it is a separate, local-model task queue.
- I found no CI definition and no record of the last gate run. I looked at the repo root and `.claude/`. The proof is therefore "the gate exists", not "the gate is green on this commit".
- The test counts for the whole repo and the gate pass rate are not stated anywhere I read.
- I could not tell how much is real versus stubbed. `docs/northstar/plans/2026-10-07-visible-game-programme.md` holds the only lane table, and I did not open it in the ten minutes.
- `scripts/journal.sh` is named in `CLAUDE.md` as the journal. I did not run it.

## 5. Impressed and put off

Impressed:
1. The README is honest. It states what is stub, approved but not integrated, and warning-only (`README.md:36-37`, `README.md:26`).
2. Determinism is treated as a contract and enforced: build flags in the `Makefile`, `scripts/specfactory/libm_lint.py`, and an `-O0` versus `-O2` trace comparison in the gate.
3. The decisions page and `docs/METHOD.md`. The page records the decision, the rule and the context (`docs/northstar/story_reviews/westley/decisions.md`). The method page includes the author's own measured failure record: "2 of 32 runs completed clean… about $1,763" (`docs/METHOD.md`, "Workflow or manager-mode"). Few authors publish that.

Put off:
1. Nothing runs for a stranger. `make` built in 31 seconds, but `make test` needed pytest, which was not installed, and the gate's interpreter path points at `/home/westopoli/Projects/agora/.venv` (`scripts/specfactory/merge_gate.sh:22`).
2. The repository is heavy with process material. There are 5,507 tracked files and 78 entries under `docs/northstar/plans/`. `docs/README.md` admits stale folders (`claude_exchange`, `random`, `stage_specs`) and says "Nothing has moved yet". Tracked `build/` and `.swarm/` output still sit in the tree (144 files together).
3. The method leans on an unexplained cast: Fable, Dispatcher, Architect, Doer, Agora, "the 30B", and a Westley who is both owner and rule source. `CLAUDE.md` (`@RTK.md` import, dated quotes, "Westley, 2026-10-22") reads as a private working file. It is linked as the rules for the agents and a visitor will take it for the project's voice.

## 6. Verdict

Yes, I would interview this author. The C sim, the pipe, the determinism discipline and a gate that cites its own failures show an engineer who builds and measures, though a stranger cannot yet reproduce the proof (missing pytest note, hard-coded venv path), and the interview would start there.

## Do the plan pages match?

I read `docs/northstar/plans/showcase/README.md` (and skimmed `inventory.md`) last. They match what I found: `README.md`, `METHOD.md`, `docs/README.md`, `CONTRIBUTING.md` and the MIT `LICENSE` exist as step 2 describes, and the stale folders and tracked build output are the ones the plan lists as step 3, not yet moved. The plan does not mention the two gaps I hit hardest, which are a first-run path for a stranger (dependencies, the gate's interpreter) and an explanation of Agora and the 30B.
