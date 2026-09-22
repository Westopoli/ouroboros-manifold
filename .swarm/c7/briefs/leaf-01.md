---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/C7.md
spec_lines: 1-95
test_files:
  - tests/push/test_leaf_c7.py
impl_files:
  - autoload/qa_daemon.gd
  - scenes/harness/harness.tscn
  - scenes/harness/harness.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
impl_line_budget: 400
test_assertion_budget: 5
test_owned_by: parent
---

## Task

Build `autoload/qa_daemon.gd` (extends Node) and `scenes/harness/harness.tscn` +
`scenes/harness/harness.gd` per spec_lines 1-95 of the spec file above. The
daemon exposes `state() -> Dictionary` returning at minimum `{"scene": <String,
current scene name or path>, "tick": <int>}`, and must not throw when
`get_tree()` is null (the fenced test instantiates it outside a running
SceneTree via `Script.new()` — guard every `get_tree()` call). In `_ready()`,
check `OS.get_cmdline_user_args()` for `--qa-port` or `--qa-script`; if
neither is present, do nothing beyond existing (no socket, no polling). When
`--qa-port N` is present, open a 127.0.0.1-only TCP listener speaking
line-delimited JSON, one verb per line, for the verb set named in the spec
(`state`, `tree`, `seed`, `fixture`, `pause`, `step <n>`, `screenshot`,
`inject <bug-id>`, `input`). When `--qa-script PATH` is present, replay a JSON
action array the same way `scenes/mockups/_shared/qa_driver.gd` does
(`preload` its verb implementations for `move`/`click`/`key`/`wait_frames`
etc. rather than duplicating that code; only `state`, `tree`, `seed`,
`fixture`, `pause`, `step`, `inject` are new here). `scenes/harness/harness.gd`
sets `DisplayServer.window_set_title("QA:" + name)` on ready so
`scripts/qa_harness.sh liveness`'s `xdotool search --name '^QA:'` finds the
window, matching `qa_driver.gd`'s existing title convention.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c7/worktrees/leaf-01/`, which is your working directory and which the
parent manages. Never run git. Nothing you do there is visible to the user's
checkout.

Run `~/Projects/agora/.venv/bin/python -m pytest tests/push/test_leaf_c7.py -q`
for this test_file. Confirm RED. Edit `impl_files` in place, at their normal
paths inside the worktree. Confirm GREEN. Also run
`scripts/run_godot_tests.sh tests/test_qa_daemon.gd` directly and confirm it
prints `=== GREEN ===` and exits 0 — that is the fenced acceptance test the
adapter wraps. Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit `project.godot`, anything under `scripts/**`,
  `tests/**`, `docs/**`, or `csrc/**`.
- Impl approaches `impl_line_budget` with `tests/test_qa_daemon.gd` still red.

## Assumption log

If you had to infer anything the brief did not specify (the `--qa-port`
wire-protocol exact framing, whether `harness.tscn` is the main menu itself
or a thin wrapper around it, the `inject <bug-id>` return shape), write it to
`.swarm/c7/briefs/leaf-01.ASSUMPTIONS.md` before you finish, one line per
inference, citing source or "no source — pure guess".

## Sibling-assumption read

No sibling leaves in this wave (single-leaf piece). Skip.

## Question ledger

If genuinely blocked on an ambiguity with weight beyond this file (would a
sibling leaf or a later piece observe it from outside your files?), write
`.swarm/c7/questions/leaf-01-Q<n>.md` per the standard shape, proceed under
best-guess, and tag your ASSUMPTIONS entry `unanswered: true`.

## Contract-proposal protocol

Not applicable — this leaf touches no parent-owned file.
