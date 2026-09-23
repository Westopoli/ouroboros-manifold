---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/C8-M3.md
spec_lines: 1-90
test_files:
  - tests/qa/desktop/test_flow_spine.py
impl_files:
  - autoload/scene_router.gd
  - autoload/c_bridge.gd
  - scenes/loading_screen/loading_screen.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - scenes/main_menu/**
  - scenes/galaxy/**
  - scenes/mission_briefing/**
  - scenes/debrief/**
  - scenes/tactical_c/**
  - scenes/world/chronicle_*
  - scenes/main_menu/main_menu.gd
  - scenes/galaxy/galaxy_view.gd
  - scenes/galaxy/galaxy_view.tscn
  - scenes/mission_briefing/mission_briefing.gd
  - scenes/tactical_c/tactical_view.gd
  - scenes/tactical_c/tactical_view.tscn
  - scenes/debrief/debrief.gd
  - scenes/world/chronicle_scroll_panel.gd
  - scenes/world/chronicle_scroll_panel.tscn
impl_line_budget: 150
test_assertion_budget: 20
test_owned_by: parent
wave: 1
shard: c8
---

## Task

Leg 1 of piece C8 (foundational plumbing) per spec_lines 1-90 of the spec
file above (`docs/northstar/plans/push/specs/C8-M3.md` — read the piece
spec `docs/northstar/plans/push/specs/C8.md` it cites too, in full, for
the full seven-step flow and button-name contract). Three changes:

1. `autoload/scene_router.gd`'s `SCENES` dict gains exactly three new
   keys: `"galaxy"` → `res://scenes/galaxy/galaxy_view.tscn`,
   `"tactical_c"` → `res://scenes/tactical_c/tactical_view.tscn`,
   `"chronicle"` → `res://scenes/world/chronicle_scroll_panel.tscn`. The
   existing `"tactical"` key stays exactly as is.
2. `autoload/c_bridge.gd` gains one new accessor: `func snapshot() ->
   Dictionary: return _snapshot` — matches the existing
   `regions()`/`edges()`/`checksum()` accessor pattern exactly.
3. `scenes/loading_screen/loading_screen.gd`'s `_on_sim_ready(_metadata)`
   currently calls `SceneRouter.go_to(_target_scene)` directly. Change it
   to `_skip_to_main = true` instead — this reuses the file's own
   existing self-healing `_process()` retry loop (which already calls
   `go_to(_target_scene)` every frame until it succeeds, for the other
   branch where the sim was already ready at `_ready()` time) instead of
   a one-shot call that gets silently dropped by `SceneRouter.go_to`'s
   `if _transitioning: return` guard when the privacy_modal → loading_screen
   fade tween is still running. Read the spec's own analysis of this bug
   (S-C8-07 in `docs/northstar/plans/push/specs/C8.md` "Findings") before
   touching this — it's a real, previously-confirmed race, not a guess.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c8/worktrees/leaf-01/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or the user's checkout.

This leaf's own changes are not independently testable against the full
`test_flow_spine.py` (the other three legs' buttons don't exist yet in
your worktree) — confirm instead:
- `scripts/run_godot_tests.sh tests/test_boot_scripts_parse.gd
  tests/test_privacy_modal.gd` stay green (unaffected by your changes,
  pure regression check).
- Write a small temporary headless script (delete before finishing) that
  launches the real game under Xvfb the way `daemon_client.py`'s
  `GodotGame` does (mirror its `start()`/`wait_for_port()` shell
  invocation shape, or just reuse the actual harness by writing a
  throwaway pytest file that imports `tests/qa/desktop/daemon_client.py`
  directly), with `user://privacy_accepted` pre-written
  (`write_privacy_flag()`), and confirms `state.scene` reaches
  `res://scenes/main_menu/main_menu.tscn` within 15 seconds — this is the
  S-C8-07 fix, and it's racy by nature (per the spec: "fails most runs as
  of this writing, passes when the sim happens to become ready outside
  the transition window" before the fix). Run this check **at least 3
  times** before trusting a pass — a single green run proves nothing
  given the bug's own documented flakiness; report how many times you
  ran it and the result of each run.
- Confirm `snapshot()` returns the last-loaded `_snapshot` dict by a
  quick headless check calling `load_snapshot_file` on
  `tests/transport/fixtures/snapshot_seed1_tick10.json` then `snapshot()`
  and checking it has a `"regions"` key.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit any file in `do_not_edit`.
- The S-C8-07 fix doesn't reliably pass after 3+ runs — report exactly
  what you tried and the failure pattern, don't keep guessing at
  alternative fixes beyond one or two reasonable variations.

## Assumption log

Log any inference (exact chronicle SCENES key name if you pick something
other than `"chronicle"`, anything about the loading_screen fix's
interaction with other timing paths you notice) to
`.swarm/c8/briefs/leaf-01.ASSUMPTIONS.md`, citing the spec section.

## Sibling-assumption read

Three sibling leaves (leaf-02 galaxy/main_menu, leaf-03 mission/tactical,
leaf-04 debrief/chronicle) build in parallel, no shared files, but they
all depend on your `SCENES` dict keys existing for the full flow to work
at combined-verification time. Check `.swarm/c8/briefs/leaf-02.ASSUMPTIONS.md`,
`-03`, `-04` (may not exist yet) if you want to confirm your chosen
chronicle key name matches what they assume — not required, since your
brief already names it explicitly.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c8/questions/leaf-01-Q<n>.md` /
`.swarm/c8/proposals/leaf-01.md` if genuinely blocked with cross-piece
weight.
