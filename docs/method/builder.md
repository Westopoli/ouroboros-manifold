# Builder

Sonnet 5.5, `subagent_type: doer`. Read this card, then the story file the brief names, then nothing else unless the story sends you there. Spawn nothing. Think tersely. Report once, at the end.

## Setup

- A cascade leaf works in the worktree the skill made and never runs git. A lone builder works on a worktree cut from the repository: `git -C ~/Projects/ouroboros-manifold worktree add ~/Projects/om-wt/<name> -b <branch> origin/main`. Every command names the absolute path; never edit `~/Projects/ouroboros-manifold` itself.
- Build: `make && make pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg`; `godot.real --headless --import` once first. Python `.venv/bin/python`; Godot `~/.local/bin/godot.real`.
- Godot tests: `timeout 1800 scripts/run_godot_tests.sh <file>`; display-needing files under `xvfb-run -a -s '-screen 0 1920x1080x24'`. Every Godot or xvfb run under `timeout 1800`.
- Long runs: `systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 -- nice -n 10 <cmd>`.

## Rules

- Touch only the files the story file names. A file outside the list, a number nobody gave, a new public C symbol not in the frozen header: stop and report.
- Never edit a test. A test that looks wrong stops you: `stop_reason` begins `test-defect:` with the test id, the failing assertion line and the story or bible line it contradicts.
- Determinism: integer or plain double arithmetic, no libm transcendentals, no wall clock, no hash-order iteration; new world state is hashed and saved.
- New code in new files; wiring is its own commit. Behaviour a rule says happens in play is reachable from the tick, the jump or a pipe handler, not only from tests.
- No stash, rebase, amend, force, `make clean`; never push to main; never stage `*.import` or `*.uid` noise (a `.uid` beside a new script of yours is committed).
- No stink: no unasked layers, wrappers or config; no cosmetic refactoring inside the change; a doc claim the change makes wrong is rewritten in the same commit.
- Before the push, `story_loop.md` step 5: `make`, the story's tests, `godot.real --headless --import`, console clean of `SCRIPT ERROR`, `ERROR:`, `Parser Error`.
- Push the branch, stop. Stop past 120k context.

## Report

```
ok: true|false
branch, sha
summary: the story's test lines verbatim, the import and console lines
red_ids: []
stop_reason: none | test-defect: ... | file outside list: ... | number nobody gave: ...
```
