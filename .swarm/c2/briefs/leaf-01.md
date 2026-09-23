---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/C2.md
spec_lines: 1-72
test_files:
  - tests/test_c_bridge.gd
impl_files:
  - autoload/c_bridge.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - scenes/galaxy/**
  - scenes/galaxy/galaxy_view.tscn
  - scenes/galaxy/galaxy_view.gd
  - scenes/galaxy/galaxy_gen.gd
  - scenes/galaxy/orbit_camera.gd
  - scenes/mockups/**
  - scenes/shared/**
impl_line_budget: 200
test_assertion_budget: 12
test_owned_by: parent
wave: 1
---

## Task

Build `autoload/c_bridge.gd` per spec_lines 51-72 of the spec file above: a
plain GDScript (loaded and instantiated directly, never as a project
autoload) that reads a C transport v1 snapshot JSON file and exposes
`load_snapshot_file(path) -> bool`, `regions() -> Array`,
`owner_of(i: int) -> int`, `checksum() -> int`, `edges() -> Array`.
`load_snapshot_file` must return falsy (not crash, not throw) on a snapshot
missing the `"regions"` key or any unparseable file.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c2/worktrees/leaf-01/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or the user's checkout.

Run `scripts/run_godot_tests.sh tests/test_c_bridge.gd`. Confirm RED first
(script missing). Edit `impl_files` in place, at their normal path inside
the worktree. Confirm GREEN (`=== GREEN ===`, exit 0). Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit any file in `do_not_edit`.
- Impl approaches `impl_line_budget` with the test still red.

## Assumption log

Log any inference (exact JSON-parse-failure handling shape, whether
`load_snapshot_file` returns `bool` or a `{ok:...}` Dictionary — the test
accepts either) to `.swarm/c2/briefs/leaf-01.ASSUMPTIONS.md`, citing the
spec section or test line you based it on.

## Sibling-assumption read

A sibling leaf-02 (`scenes/galaxy/galaxy_view.tscn`) builds in parallel in
this same wave, no shared files. Before logging your own assumptions,
check `.swarm/c2/briefs/leaf-02.ASSUMPTIONS.md` (it may not exist yet if
leaf-02 hasn't finished) for anything about the snapshot dict shape you
should match.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c2/questions/leaf-01-Q<n>.md` /
`.swarm/c2/proposals/leaf-01.md` if genuinely blocked with cross-piece
weight. Unlikely for this leaf — it's small and self-contained.
