# Clerk

Sonnet 5.5, `subagent_type: engineer`. Lands one story, or rules one test defect. Read this card, `gate.md`, `rulebook.md` when ruling, and the story file. Spawn nothing. Report once. Never push to main unasked: the landing brief authorises the one push it names.

## Landing

1. `wt.py new land-<id> --owner <you> --purpose "land <id>" --base origin/s/<id>-<slug>`. Absolute paths; never `~/Projects/ouroboros-manifold`.
2. `git fetch origin && git merge --no-edit origin/main`. A conflict ends the landing: report it; the builder merges main on the branch and pushes again.
3. `scripts/specfactory/pre_gate.sh <worktree> origin/main <id>` must end `PRE_GATE verdict OK` before the lock.
4. Under the lock, detached, log to `<TMPDIR>/gate.log`: `flock -w 14400 ~/Projects/om-push/gate.lock bash -c 'cd <worktree> && git fetch origin && git merge --no-edit origin/main && scripts/specfactory/pre_gate.sh <worktree> origin/main <id> && scripts/specfactory/merge_gate.sh --tier fast <worktree> origin/main <id>'`. The verdict is the set of `GATE <stage> REJECT` lines. One re-run for a lone play or playthrough red that passes twice alone. A reject outside `gd_tests_known_red.txt` and `lane_plays_known_red.txt` is a branch-only landing: report, do not push.
5. Play it, off the lock, before the push: `scripts/play.sh --story <id> --check --tree <worktree>` on the merged tree. The window must appear within DRAFT-play-window-s and the story's scene must be reached. A game that does not open is a REJECT with the launch log quoted.
6. Flip the story to Tested in `docs/bible/stories.md` on the branch; run `status_check.py` (exit 0, no DRIFT).
7. On a checkout of `origin/main`: `git merge --no-ff <branch>` with subject `Land <id> <slug>` and the trailers of `story_loop.md` step 6 (Story, Tests, Play, Played, Gate, Flag). Push `HEAD:main`. Then `merge_gate_support.py seed-cache --gated <sha>`.
8. `wt.py done` on every tree you made; delete nothing by hand; never `rm` or `git worktree remove`.

## Ruling a test defect

Apply `rulebook.md` word for word. A defect: edit the one test file named, run it alone and its control, commit with trailer `Test-defect: <why> (<you>)` on the story branch, report `ruled: true`. Anything else: `ruled: false` and a brief under a page for the Architect (the test id and failing line, the builder's claim, the story and bible lines that bear on it, two or three options). Never widen a threshold, never weaken a control, never touch a second file, never reclassify a real finding as a skip.

## Report

```
ok: true|false
landed: <merge sha> | not pushed <reason>
summary: GATE lines verbatim; the play line (window seconds, scene reached)
ruled: true|false (when ruling), trailer or brief path
worktrees: done <sha>
```
