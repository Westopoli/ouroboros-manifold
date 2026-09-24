# Leaf mechanics (standing brief for every push leaf)

Read once per leaf. The manager's assignment adds only: piece id, owned files, acceptance ids, known leftovers, the state slot name.

## Where you work

- Clones: `~/Projects/om-push/m1` (sim modules), `~/Projects/om-push/m3` (client and pipe), `~/Projects/om-push/m0` (M0 only). Never touch `~/Projects/ouroboros-manifold` (Westley's live checkout) and never run Godot with it as cwd.
- Worktree per piece: `cd <clone> && git fetch -q origin && git worktree add ~/Projects/om-push/wt/<piece> -b push/<piece> origin/main`. When your assignment depends on a piece whose branch is pushed but not yet on main, base on that branch instead (`... -b push/<piece> origin/push/<dep>`), or merge it in (`git merge origin/push/<dep>`, never rebase): the merge harness recognises commits that later land on main and skips them, so waiting for the merge queue is never required to start. Work only there. Increments continue on the same branch (`push/<piece>`) or start a new one from the previous tip (`push/<piece>-N`); the merge harness skips commits already on main.
- Build: `make -j8` in the worktree (`make pipe/ouroboros_pipe` for the transport). Python: `~/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider <ids>`. `tests/csim` and `tests/qa/t1` run in separate invocations (their conftest names collide). Godot 4.6.3 is `~/.local/bin/godot`; in a fresh worktree run `~/.local/bin/godot --headless --import --path . --quit` once, `mkdir -p logs`, and `ln -s ~/Projects/agora/.venv .venv` before any desktop run; `scripts/run_godot_tests.sh <files>` is headless; desktop runs use Xvfb the way `scripts/qa_harness.sh` does, never `:0`.

## What you may change

- Only the files your assignment names. Never `tests/**`, `docs/bible/**`, `docs/northstar/**`, `CLAUDE.md`, headers, the Makefile, or another module's file. A test-fix assignment names its test files and the one evidence file explicitly.
- Tests are the spec. A test you believe is wrong is reported (id, first assertion line, the confound, the proposed change), never edited. A behavior another module must provide is reported as a closure leftover naming the symbol and the owning module, never stubbed across files.
- Constants by name from `csrc/om_constants.h`. A value the bible pins in prose but the header lacks: a local `#define` citing the ALG id and the `simulation/config.py` name, and a line in your report. Never an invented number, never a fixture answer hard-coded.
- No file-static per-world state: per-world state lives in your module's `om_world` slot (`w-><module>_state` with its `_free` hook; mirror `csrc/mission.c`). No wall clock, no hash order, no libm outside the deterministic set; `scripts/specfactory/libm_lint.py csrc` and `scripts/specfactory/alg_constants.py --lint csrc` stay clean. Ties break by `OM_TIE_EPSILON`. No new public symbols: the header already declares yours.
- No stink: no docstrings, comments or wrappers beyond what is genuinely non-obvious.

## Git rules

- git-guard denies rebase, reset --hard, clean, -D, --amend, force push, and any command text containing both "push" and "-f" (so never `pgrep -f` or `pkill -f` in a command that also has "push"; a pkill pattern must not appear literally in your own command, use `B9-[2]`-style brackets). Merge, never rebase. If your branch falls behind main and conflicts, do not merge main in; rebuild by copy on a fresh branch from origin/main (`push/<piece>-N`).
- Commit only your files with caveman messages; push `push/<piece>` after each green story so partial progress is on origin. After the final push, `git switch --detach -q` in your worktree so the harness can fetch your branch.
- Never push to main. Never remove worktrees you did not create.

## What you verify (and nothing more)

- Your acceptance ids, green or red with the first assertion line for each red, each red classified: module gap, blocked on `<piece>` (name the stub symbol), cross-module leftover, suspected test defect.
- The two lints. A clean `make -j8`.
- Not the whole-suite before/after: the merge gate computes the failing-id diff on your candidate and rejects any new red id, so a leaf never builds a baseline worktree.
- For anything under `tests/qa/desktop`: kill your Xvfb and Godot processes when done.

## Report back

Caveman prose: branch and final sha; per story or per id results as above; leftovers with symbols; missing constants; suspected test defects (propose, never fix). Time box: a story that stays red with a nameable cause is reported, never forced.

Report-back caveman mode (drop articles/filler/hedging, fragments OK). Markdown docs/briefs you write: caveman. Commit messages: caveman. Code, tests, config: normal prose.
