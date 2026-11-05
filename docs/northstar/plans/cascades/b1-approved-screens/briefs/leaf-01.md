---
leaf_id: leaf-01
spec_file: docs/northstar/plans/cascades/b1-approved-screens/spec.md
spec_lines: 7-30
test_file: tests/method/test_setup_editor_darwin_edges.py
impl_file: scripts/setup_editor.sh
test_files:
  - tests/method/test_setup_editor_darwin_edges.py
impl_files:
  - scripts/setup_editor.sh
  - scripts/fetch_godotsteam.sh
  - README.md
contract_imports:
  - OM_GODOT_APP
  - ARCH
do_not_edit:
  - tests/**
  - autoload/**
  - scenes/**
  - project.godot
  - scripts/build_pipe_macos.sh
  - scripts/specfactory/**
  - docs/**
impl_line_budget: 90
test_assertion_budget: 40
test_owned_by: parent
---

## Task

Make the Darwin route of `scripts/setup_editor.sh` and the `shasum` route of `scripts/fetch_godotsteam.sh` real, and add the Mac sentence to the README "Open in the editor" paragraph, exactly as `spec.md` lines 7-30 and `contract.md` pin them (R-087-01 to R-087-05). Keep the Linux route byte for byte as it is. The printed `--check` lines, the `OM_GODOT_APP` seam and the Godot discovery order are in `contract.md`; mirror the structure and the `fail()` convention already in `scripts/setup_editor.sh`, and the discovery order of `scripts/run_godot_tests.sh`. The scripts must run under bash 3.2 and BSD `find`, `cp`, `mktemp` (no `find -quit`, no `mapfile`, no associative arrays).

## Acceptance

You are working inside your own git worktree; never run git. Run `python3 -m pytest tests/method/test_setup_editor.py tests/method/test_setup_editor_darwin_edges.py -q -p no:cacheprovider` (run it as `PATH="$PWD/.venv/bin:$PATH" python3 -m pytest ...`: the system python3 has no pytest, `.venv` is linked into your worktree). Confirm RED. Edit `scripts/setup_editor.sh`, `scripts/fetch_godotsteam.sh` and `README.md` in place. Confirm GREEN. Stop. Do not edit any test.

## Escalation triggers

Stop and report to the parent if:
- A test needs behaviour `contract.md` does not state.
- The change would need a file outside `impl_files`.
- Impl approaches impl_line_budget with assertions still failing.
