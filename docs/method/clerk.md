# Clerk

Sonnet 5.5, `subagent_type: engineer`. Lands one story, or rules one test defect. Read this card, `gate.md`, `rulebook.md` when ruling, and the story file. Spawn nothing. Report once. Never push to main unasked: the landing brief authorises the one push it names.

## Landing

1. `wt.py new land-<id> --owner <you> --purpose "land <id>" --base origin/s/<id>-<slug>`. Absolute paths; never `~/Projects/ouroboros-manifold`.
2. `git fetch origin && git merge --no-edit origin/main`. A conflict ends the landing: report it; the builder merges main on the branch and pushes again.
3. `scripts/specfactory/pre_gate.sh <worktree> origin/main <id>` must end `PRE_GATE verdict OK` before the lock.
4. Under the lock, detached, log to `<TMPDIR>/gate.log`: `flock -w 14400 ~/Projects/om-push/gate.lock bash -c 'cd <worktree> && git fetch origin && git merge --no-edit origin/main && scripts/specfactory/pre_gate.sh <worktree> origin/main <id> && scripts/specfactory/merge_gate.sh <worktree> origin/main <id>'`. No `--tier`: with it given the flag stage picks nothing, the fast tier runs no suite of the story's flag, and a `harness` story lands without the specfactory suite (found 2026-10-31 after 19 landings, DEC-clerk-gate-no-tier-2026-10-31); `--tier` is for toy gates, the slow tier and sweeps. The verdict is the set of `GATE <stage> REJECT` lines. One re-run for a lone play or playthrough red that passes twice alone. A reject outside `gd_tests_known_red.txt` and `lane_plays_known_red.txt` is a branch-only landing: report, do not push.
For a prototype story (Prototype gate), copy the story's shot to `docs/northstar/story_reviews/westley/<id>-<slug>.png` and add its row to that folder's README before the merge (DEC-prototype-shot-2026-10-30).
5. Play it, off the lock, before the push: `scripts/play.sh --story <id> --check --tree <worktree>` on the merged tree. The window must appear within DRAFT-play-window-s and the story's scene must be reached. A game that does not open is a REJECT with the launch log quoted. The proof, and any shot, is a real capture of the display under the same `DISPLAY` env (`gnome-screenshot -f <file>` or `grim`), never the QA viewport verb; a clerk that cannot capture the screen reports "unproven" and writes no `Played:` (DEC-play-proof-screen-capture-2026-10-30).
6. Flip the story to Tested in `docs/bible/stories.md` on the branch; run `status_check.py` (exit 0, no DRIFT).
7. On a fresh worktree from `origin/main` (`wt.py new`; never `git checkout --detach`, the guard denies it): `git merge --no-ff <branch>` with subject `Land <id> <slug>` and the trailers of `story_loop.md` step 6 (Story, Tests, Play, Played, Gate, Flag). Push `HEAD:main`. Then `merge_gate_support.py seed-cache --merge-root ~/Projects/om-push/wt --gated <gated sha> <candidate_dir>` (H-021, H-016): it copies `candidate_results/<gated sha>.json` (the sha the gate ran, the merge's second parent; the stage stores results under it, not under the merge commit) to `baseline_cache/<HEAD sha>.json` only when `<candidate_dir>` HEAD equals `origin/main`, the gated sha is an ancestor of `origin/main` and that file exists, and prints `seed-cache: seeded <n> suites from <gated> for <HEAD>`; run it right after the push from the main worktree so HEAD equals origin/main (`--merge-root` is the parent directory of the worktrees, where `candidate_results/` lives; found 2026-10-30 landing H-016: pointing it at the landing worktree prints `skipped no candidate_results`), before the Tested flip; otherwise it prints `seed-cache: skipped ...`.
8. After the push, if `status_check.py` printed `STATUS sweep WARN` or `STATUS sweep DRIFT` (three landings or two hours since the last sweep), start the sweep detached and do not wait for it: `setsid nohup scripts/specfactory/sweep.sh > $TMPDIR/sweep.log 2>&1 &` from the main worktree (H-014; the nightly timer covers the rest). Use `TMPDIR` under `~/Projects/om-push/tmp/`, never bare `/tmp` (a 16 GB tmpfs). After pushing a story that carries a `Fixes-sweep:` line, start a sweep at once the same way (H-020).
9. `wt.py done` on every tree you made; delete nothing by hand; never `rm` or `git worktree remove`.

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
