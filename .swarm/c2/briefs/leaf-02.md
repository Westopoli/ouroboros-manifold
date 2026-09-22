---
leaf_id: leaf-02
spec_file: docs/northstar/plans/push/specs/C2.md
spec_lines: 1-158
test_files:
  - tests/test_galaxy_view.gd
impl_files:
  - scenes/galaxy/galaxy_view.tscn
  - scenes/galaxy/galaxy_view.gd
  - scenes/galaxy/galaxy_gen.gd
  - scenes/galaxy/orbit_camera.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - autoload/c_bridge.gd
  - scenes/mockups/**
  - scenes/shared/**
impl_line_budget: 900
test_assertion_budget: 20
test_owned_by: parent
wave: 1
---

## Task

Build `scenes/galaxy/galaxy_view.tscn` (root scene) plus backing scripts per
spec_lines 1-50 and 73-158 of the spec file above: a root node implementing
`set_snapshot`, `qa_state`, `qa_plant`, `qa_seed`, `qa_camera` exactly as
`tests/test_galaxy_view.gd` calls them (read that file in full — it is the
literal contract: exact key names in `qa_state()`'s returned Dictionary,
exact `PLANTS` ids, exact plant behaviors). Mirror the proven implementation
pattern already built and reviewed at `scenes/mockups/galaxy/{galaxy_gen.gd,
galaxy_view.gd,orbit_camera.gd}` (read-only reference, do not load or import
it) — same seeded-layout approach, same camera-distance band blending, same
filament/point rendering idea — adapted to real snapshot data (region
owners/edges from `set_snapshot`'s argument, not self-generated topology)
and to the six `qa_plant` fault-site ids the spec names. Owner colours come
from `autoload/faction_palette.gd`'s hue function (read-only reference, do
not autoload it — copy the formula).

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c2/worktrees/leaf-02/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or the user's checkout.

Run `scripts/run_godot_tests.sh tests/test_galaxy_view.gd`. Confirm RED
first (scene missing). Edit `impl_files` in place, at their normal paths
inside the worktree. Confirm GREEN (`=== GREEN ===`, exit 0, all 14 checks
pass including the 6 plant checks and `qa_plant("nope")==false`). Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files` (adding a
  small additional helper script under `scenes/galaxy/` alongside the ones
  listed is fine if genuinely needed — just note it in your report; only
  escalate if you need to touch something outside `scenes/galaxy/**`).
- The impl would need to edit any file in `do_not_edit`.
- Impl approaches `impl_line_budget` (900) with checks still red.
- A field the test names (`qa_state()`'s keys, a `PLANTS` id) seems to
  require a design decision with weight beyond this file's internals —
  escalate rather than guess a value another piece would observe (nothing
  else currently consumes this scene's output directly, so this is
  unlikely, but the palette/colour formula is shared visual language other
  pieces may later reuse).

## Assumption log

Log every inference to `.swarm/c2/briefs/leaf-02.ASSUMPTIONS.md` — this
piece has several deliberately-open points per the spec (band distance
thresholds beyond what the test directly forces, exactly how `edges_3d`
toggling should look versus just flipping a reported flag, the
`pick_radius_px` default value, hash formula details). Cite the spec
section, the test line, or the mockup file/line you mirrored.

## Sibling-assumption read

A sibling leaf-01 (`autoload/c_bridge.gd`) builds in parallel in this same
wave, no shared files. Before logging your own assumptions about the
snapshot dict shape, check `.swarm/c2/briefs/leaf-01.ASSUMPTIONS.md` (may
not exist yet) for anything relevant — you consume snapshot dicts directly
via `set_snapshot`, same shape `c_bridge` reads, so a mismatch there would
matter.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c2/questions/leaf-02-Q<n>.md` /
`.swarm/c2/proposals/leaf-02.md` if genuinely blocked with cross-piece
weight (see escalation triggers above).
