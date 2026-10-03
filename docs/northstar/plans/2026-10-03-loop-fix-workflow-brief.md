# Workflow brief: make the MVP loop play (2026-10-03)

Paste this whole file into a fresh Sonnet 5.5 chat. Westley's instruction to that chat: **run this brief as a workflow** (the Workflow tool, Sonnet agents only), then report once.

## Your role

You run one small workflow and report numbers. You do not design, rule, or widen scope. The Architect (Fable chat `Agora-Fable-Planner`) wrote this brief and reads your report. All other lanes are paused, so nothing else is landing on main.

Read before you start, and point your agents at these instead of pasting them: `CLAUDE.md`, `docs/northstar/plans/briefs/leaf-mechanics.md`, `tests/qa/README.md`.

## Goal

The loop new campaign, galaxy, briefing, deploy, mission, debrief, chronicle with entries, next chapter runs end to end on a fresh checkout of origin/main, and the 30B QA model can play it. Three lanes fix the three known breaks. Source of the evidence below: the stage 0 audit of origin/main `1c2d4494`.

## Rules for every agent

- Sonnet only. Every spawn names its model. No agent spawns agents.
- Small contexts: one lane step per agent, a brief under a page, one report under 30 lines. Agents report once, at the end.
- Each agent works in its own new worktree from `origin/main` under `~/Projects/om-push/wt/lf-<lane>-<step>`. Never read or touch the live checkout `/home/westopoli/Projects/ouroboros-manifold`. Never remove worktrees. Put no repo copies in `/tmp` (16 GB RAM disk).
- No `git stash`, no rebase, no amend, no force, no blind "take theirs". Push a branch and stop.
- Debugging order: hypothesis, then logging that confirms or refutes it, then one targeted fix.
- Tests first. A test-writer agent writes the failing test; a different agent builds. Builders never edit tests. If an existing test looks wrong, stop that lane and report it; do not change it.
- Do not edit the bible, the ambiguity register, `pieces.toml`, `ROADMAP.md`, `CLAUDE.md`, or any memory file. Do not invent constants or thresholds.
- Python: `/home/westopoli/Projects/agora/.venv/bin/python`. Godot 4.6.3 is installed; the desktop flow runs under `xvfb-run`.

## Lanes (run the three in parallel; steps inside a lane in order)

### Lane 1: chronicle and jump

- **Evidence.** `tests/qa/desktop` `test_s_c8_05` fails: `C3-6: chronicle screen has 0 entries after end-mission jump; expected >= 1 (qa_state().entries = [])`. `tests/test_sim_session.gd` has 2 failures: after the chronicle's 50-tick jump the shared world's tick is 220, expected 250 or more. Transport tests prove the pipe returns chronicle entries (`test_pipe_chronicle_*`, green), so the fault is on the client side of the pipe or in the end-mission path.
- **Step 1, diagnose** (one agent): find why the jump does not advance the shared world and why the chronicle screen loads no entries. Output: the cause with file and line, proven by a log line, and the smallest fix. No code change.
- **Step 2, build** (one agent): make that fix. Files: only those the diagnosis names, expected under `autoload/` and `scenes/world/chronicle_*` or `scenes/debrief/`. If the cause is in `csrc/` or the pipe contract, stop and report.
- **Done when:** `test_s_c8_05` and both `test_sim_session` cases pass, transport stays 251 of 251, and the Godot flow reaches the next chapter after the chronicle.

### Lane 2: fresh checkout boots

- **Evidence.** `project.godot` line 31 autoloads `SimBridge` (`autoload/sim_bridge.gd`), which starts the legacy Python sim (`simulation/pipe_transport.py`) and needs numpy and a `logs/` folder. With neither, a fresh checkout boots to `error_screen` and every desktop flow test fails. Line 29 autoloads `TacticalBridge`.
- **Step 1, test** (one agent): a test that boots a fresh checkout with a Python that has no numpy and no `logs/` folder and expects the main menu, not `error_screen`. It must fail today.
- **Step 2, diagnose and build** (one agent): the smallest change that passes it. Prefer stopping the legacy sim from being started over deleting files. If the change needs edits in more than three files, stop and report the list instead of building.
- **Done when:** the new test passes and the desktop flow passes on a worktree with no `.venv` link and no `logs/` folder.

### Lane 3: the 30B QA reaches the galaxy (Agora repo, `~/Projects/agora`)

- **Evidence.** Newest sessions (`qa-20261002-0047` and the four before it) never leave the main menu: turn 2 clicks NEW GAME, logs `stuck: IndexError`, then loops on ERA LIBRARY. Full loops: 0. The QA clone `~/Projects/om-push/qa` is at `35794bfd` (2026-10-01), so the pre-session refresh to origin/main is not happening.
- **Step 1, diagnose** (one agent): the `IndexError` on NEW GAME with its traceback, and why the clone is not refreshing. The refresh may be skipping because the build or boot fails (see lane 2); say whether that is so. No code change.
- **Step 2, test then build** (two agents): a failing test in the Agora repo for the `IndexError`, then the fix. Follow the Agora repo's own rules file.
- **Done when:** the test passes and, after lanes 1 and 2 land, one live 30B session on current origin/main reaches the galaxy. If you cannot start a live session, say exactly what stopped you.

## Landing

One fresh, small clerk agent per branch lands it through `scripts/specfactory/merge_gate.sh` (see `leaf-mechanics.md` for piece ids; look the owner up in `docs/northstar/plans/push/pieces.toml`, never edit it). Land lane 2 first, then lane 1, one at a time. After each landing, run the desktop flow (`tests/qa/desktop`) on the new main. A red that was green before means revert that landing and report. Lane 3 lands in the Agora repo by that repo's rules.

## Stop and report instead of deciding

A cause in a contract file (`csrc/ouroboros_sim.h`, the pipe frames); a file with no owner row; a test that looks wrong; a fix larger than about 100 lines; anything that needs a number or a rule nobody has given.

## Report (one file, then one message)

Write `docs/northstar/plans/runs/2026-10-03-loop-fix-report.md` on a branch `push/lf-report`, push it, and send one message to the session `Agora-Fable-Planner` naming the branch. Under 60 lines:

1. Per lane: cause (file and line), fix commit, test that proves it, landed or not.
2. The loop table: each step from new campaign to next chapter, passing test named, on the final main.
3. Counts before and after: transport, desktop, QA t1, Godot scripts.
4. Numbers: agents spawned, tokens per agent and in total, wall-clock time, lines changed per lane.
5. Anything you stopped on, with the evidence.
