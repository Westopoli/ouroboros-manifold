# The story loop

One story, one branch, one landing, one merge commit. Git is the record: there is no lane table, no pieces table, no ledger, no review queue. What a table used to hold is a branch, a commit subject or a trailer, and `scripts/method/status.sh` reads it back.

## 1. Requirement

The story is Ready (`requirements.md`). Ready in `docs/bible/stories.md` is the queue; `git log -- docs/bible/stories.md` is its history. Nothing else is written.

## 2. Spec

The Architect writes one page, `docs/stories/<id>.md`, on the branch `s/<id>-<slug>` from `origin/main`:

- the rules it proves, quoted by id;
- every file it touches, named; every interface two agents share, in full (fields, types, column names);
- every number, or a named `DRAFT-` with its register row;
- the scene: the run line `scripts/play.sh --story <id>` resolves to (scene path, arguments, what the player should be able to do there);
- the tool: a Workflow, or a `/manager-mode` cascade for a sim-side cluster of three or more file-disjoint units under one umbrella test;
- the gate flag: `harness`, `client`, `sim` or `contract`;
- the pre-flight: every precondition checked by reading or running, with the sha read.

Commit subject `<id> spec: <what>`. The branch on origin is "in flight". The Architect names files so that two in-flight stories do not share one; if they do, the merge at step 5 conflicts and the landing returns to the builder, who merges main into the branch and pushes again. Contract files (`csrc/ouroboros_sim.h`, `signatures.toml`, the pipe frames, the save format) are frozen: a story that changes one is a `contract` story and lands before its consumers start.

## 3. Verification

A test writer, never the builder, commits to the same branch: fenced tests, red at the branch base for the stated reason with the failing assertion line pasted in the commit body; one positive control green; for a player-facing story the `qa_state()` element inventory and the story play. Commit subject `<id> tests: <n> red, <m> control`. An audit by a fresh Sonnet happens only when the story touches a contract or writes a new rule.

## 4. Build

One builder, one worktree from `wt.py new`, reads `builder.md` and the story file, builds until the story's tests are green, runs `scripts/specfactory/pre_gate.sh`, pushes, runs `wt.py done`, stops. A test it believes wrong goes in its report as `test-defect:` with the failing line; the clerk rules it by `rulebook.md`. A change to a test is a commit with the trailer `Test-defect: <why> (<ruler>)`, never a silent edit. A reject returns to the same builder; after three rounds the clerk writes a brief under a page for the Architect.

## 5. Verify

The clerk merges `origin/main` into the branch, runs `pre_gate.sh`, takes `~/Projects/om-push/gate.lock`, runs the layered gate (`gate.md`): the flag layer, the story's tests, the selected fast tier, under ten minutes. The full suite runs as the sweep on main off the lock; a red sweep bisects with `git bisect run --first-parent` on the failing test and reverts the culprit landing.

## 6. Land

Before the push counts, the clerk opens the merged game as a player would: `scripts/play.sh --story <id>` on the merged tree builds the pipe, launches Godot on the real display, waits for the window (DRAFT-play-window-s 60) and runs the story's scene. A game that does not open, or a scene that cannot be reached, is a REJECT with the launch log quoted, whatever the tests said (Westley, 2026-10-30, after the game would not open for his friends).

The merge is `git merge --no-ff` with subject `Land <id> <slug>` and trailers:

```
Story: S-042
Tests: tests/csim/test_layer_vision.py tests/test_tactical_view.gd
Scene: scripts/play.sh --story S-042
Played: 2026-11-02 window 11s scene reached
Gate: 412s fast
Flag: sim
```

The same merge flips the story to Tested in `stories.md`. Westley's verdict is a one-line commit `Seen <id>` with trailer `Verdict: approve <his words>`, or `Verdict: reject <his words>`, after which the story returns to Ready with the reason written into its story file.

## Scenes, not screenshots

The review artifact of a player-facing story is a scene Westley runs and interacts with, never a picture. The story file names the scene path under `scenes/` and the launch arguments that put the game in the story's state; the existing `OS.get_cmdline_user_args()` readers in `autoload/c_bridge.gd`, `autoload/era_config.gd` and `autoload/qa_daemon.gd` are the pattern, and a story that needs a new entry state adds its argument in its own build. `scripts/play.sh [--scene <path>] [--seed N] [--story <id>]` is the one run line for every reader: Westley, the clerk at step 6, the 30B nightly. It refreshes `~/Projects/om-push/main` (a plain checkout of `origin/main` kept only for playing), runs `scripts/build_pipe_linux.sh`, launches Godot with the story's arguments and prints the seconds to the window. No shot per piece, no copy to a review folder, no README row, no verdict on a still. The blank-frame detector stays as an automated test on the frame. The 30B's nightly play uses the same script and files what it finds as `H-` rows.

Playing main is the same script with no arguments.

## Other trailers

- `Test-defect: <why> (<ruler>)` on a commit that changes a test.
- `Decision: DEC-<slug>-<date>` on a commit that adds a row to `decisions.md`.
- `Finding: <what broke, which landing>` on the revert a bisect produces, subject `Revert Land <id> <slug>`.
- `Sweep <date> <pass|red n>` as the subject of the sweep's empty commit on main.
- `Base: <sha>` on the first sweep after a gate change.

`scripts/specfactory/status_check.py` checks the schema: every `Land` commit has Story, Tests, Scene, Played, Gate, Flag; every story in Tested has a `Land` commit; every `Seen` has a Verdict. The gate refuses a landing whose merge message lacks a trailer.

## Slots and waits

DRAFT-build-slots: three builds in flight, one landing. Waits are `flock -w`; no chat polls a gate or schedules a wakeup. A builder pushes and stops; a fresh clerk lands. Every agent reports once, at the end, in its card's schema, and stops past 120k context.
