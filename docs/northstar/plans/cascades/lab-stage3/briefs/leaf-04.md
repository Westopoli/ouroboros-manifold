---
leaf_id: leaf-04
spec_file: docs/northstar/plans/cascades/lab-stage3/spec.md
spec_lines: 41-43
test_files:
  - tests/method/test_replay_sh.py
impl_files:
  - scripts/replay.sh
  - README.md
contract_imports:
do_not_edit:
  - docs/northstar/**
  - tests/**
  - csrc/**
  - scripts/specfactory/**
  - .claude-swarm.toml
  - scripts/skilllab/arena/features.py
  - scripts/skilllab/arena/run.py
  - scripts/skilllab/arena/snapshot.py
  - scripts/skilllab/arena/SNAPSHOT.md
  - scenes/proto/fight_replay/fight_replay.gd
  - scripts/skilllab/arena/page.py
  - scripts/skilllab/arena/situations.py
impl_line_budget: 90
test_assertion_budget: 20
test_owned_by: parent
wave: 1
---

## Task

Implement spec criteria 12 and 13: the new executable `scripts/replay.sh` and a "Watch a lab fight" section in `README.md`. The script finds Godot (`$GODOT`, `godot` on `PATH`, `~/.local/bin/godot.real`, `/Applications/Godot.app/Contents/MacOS/Godot`; first match wins), runs `<godot> --headless --import --path <repo>` once per checkout (marker `.godot/replay_imported`), then launches `<godot> --path <repo> --windowed --resolution 1919x1080 res://scenes/proto/fight_replay/fight_replay.tscn` with `OM_FIGHT` set to the fight's absolute path and, with `--shots <dir>`, `OM_SHOT_OUT` to its absolute path. `--dry-run` prints the import line and the launch line and runs nothing; `OM_UNAME` overrides `uname -s`; a missing fight file exits 2 naming the file. It must run under bash 3.2 (macOS): no associative arrays, no `mapfile`, no `${var,,}`, no `timeout`, `flock`, `setsid` or xdotool. Match the argument loop and comment style of `scripts/play.sh`; the Godot search order mirrors `scripts/run_godot_tests.sh` lines 10-25 plus the two entries above.

Test files `tests/method/test_replay_sh.py` are already written and failing. You are working inside your own git worktree, which is your working directory. Never run git. Edit `scripts/replay.sh`, `README.md` in place there until those tests pass. Do not modify test files, do not create files outside `impl_files`, and keep every edit to what the cited spec criteria require (no cosmetic refactoring; a doc claim your change makes wrong is rewritten in the same file). Keep the module's existing comment style and the `# See also:` traceability lines.

## Acceptance

Run `~/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/method/test_replay_sh.py -q -p no:cacheprovider` from the worktree root. Confirm RED. Edit the impl files. Confirm GREEN. Stop.

## Escalation triggers

Stop and report to the parent if a symbol the test imports is not in `contract_imports`, the impl needs a file not listed in `impl_files`, the impl needs a file in `do_not_edit`, two assertions require contradictory behavior, or the impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

Infer nothing silently. Record any inference in `docs/northstar/plans/cascades/lab-stage3/briefs/leaf-04.ASSUMPTIONS.md` (format: `- **<thing>**: <value> - source: <spec line / file / no source>`).
