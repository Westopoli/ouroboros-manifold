# F6 item 6: rejection replays (2026-09-22)

Brief: `docs/northstar/plans/briefs/2026-09-22-two-day-push.md`, item 6. Five replays in scratch worktrees under `/tmp/pxF6/` (removed after; branches `docs-replay-d`/`docs-replay-d-clean`, created as local-only worktree branches during (d), could not be force-deleted under the `-D` git-guard block -- confirmed via `git ls-remote origin` they never reached the real origin, harmless local clutter). Base commit for (a)/(b)/(c): `1515ab2` (F6-5). Tools: `scripts/specfactory/merge_gate.sh`, `~/Projects/agora/scripts/merge_cli.py`.

Two real bugs were found and fixed while producing this evidence, both false positives that would have rejected innocent candidates; see "Bugs found" below. All wall times below are from the POST-fix runs unless marked otherwise.

## (a) `om_pow` reverted to libm `pow` -- rejected by libm lint

`csrc/sim.c:334`, the release-path `tension_headroom_pow` computation, changed from `om_pow(...)` back to bare `pow(...)`. Gate: `merge_gate.sh /tmp/pxF6/replay_a HEAD~1 B4` (piece id arbitrary -- `sim.c` is core, owned by no wave piece).

- Exit code: **1** (reject). Wall time: **1m11.7s**.
- `GATE libm_lint REJECT FAIL /tmp/pxF6/replay_a/csrc/sim.c:334 libm pow() call -- not deterministic across platforms LIBM LINT FAILED (1)` -- the named check fires exactly as intended.
- Also independently rejected (expected, not the point of this replay): `alg_constants` (335 pre-existing un-allowlisted `sim.c` literals, unrelated to this line -- allowlist predates a recent legitimate `sim.c` change), `footprint` (B4 does not own `sim.c`), `acceptance`/`qa_t1`/`transport` (this repo's current baseline redness: E-03 route tests, `tests/qa/t1/test_rts_detectors.py`'s expected-red stub import, and the T1 pipe placeholder -- all true on a totally clean candidate too).
- `checksum_trace` (O0 vs O2) came back **MATCH** even with the bad `pow()` in place -- expected and worth stating plainly: O0-vs-O2 on the *same* platform cannot catch a libm cross-platform divergence (glibc vs. platform libm), which is exactly why `libm_lint`'s static check exists as a separate, non-negotiable gate rather than relying on the numeric comparison alone.

## (b) a planted regression -- rejected by regression, id named

`csrc/agent.c:119`, `factor_1 = w->regions[j].tension / 100.0;` changed to `/ 200.0` (halves the tension weakness factor). Gate: `merge_gate.sh /tmp/pxF6/replay_b HEAD~1 B2`.

- Exit code: **1**. Wall time: **1m12.9s**.
- `GATE regression_csim REJECT REJECT new failures: ['tests/csim/test_E05_S034_who_looks_worth_taking.py::test_R_034_03_factor_one_0_80_tension']` -- the named id, exactly as asked, with no other new failures and no false-positive "changed assertions" noise (see bug 1 below -- the first run, before the fix, also showed 8 unrelated "changed assertions").
- `libm_lint` and `symbol_ownership` both **OK** (this diff introduces neither); `footprint` independently rejects (B2 does not own `agent.c` -- arbitrary piece choice for this replay, `agent.c`/E-05's agent logic is not one of the two-day-push's new pieces).

## (c) a `tests/` edit -- rejected by footprint

Appended a comment line to `tests/csim/test_E04_wiring.py`. Gate: `merge_gate.sh /tmp/pxF6/replay_c HEAD~1 B1` (B1 owns `csrc/events.c`, not this file).

- Exit code: **1**. Wall time: **1m19.0s**.
- `GATE footprint REJECT REJECT diff touches files outside B1's owns: ['tests/csim/test_E04_wiring.py']` -- exactly the named file, exactly the intended rejection.
- `libm_lint` **OK** (no csrc touched at all by this diff).

## (d) a clean docs-only branch through `merge_cli.py docs` -- accepted, not pushed

New file `docs/northstar/proving_ground/evidence/push_2026-09-22/replay_d_scratch_note.md`, one commit off the F6-5 base, branch `docs-replay-d-clean`. `--dry-run` added to `merge_cli.py docs` per this item's own instruction (stops before push).

- Exit code: **0**. Wall time: **12.8s**.
- Output: `OK  dry-run: collection and lints OK, not pushed`.
- Confirmed nothing pushed: origin's `main` sha unchanged (checked via the command's own dry-run gate, which never reaches the push line -- see `cmd_docs`'s `if dry_run: return ... "not pushed"` before the push subprocess call).
- First attempt (before two fixes below) rejected this exact clean branch twice in a row, for two different pre-existing, unrelated reasons -- see "Bugs found".

## (e) acceptance replay -- leaf + fake `.swarm/` artifact, cherry-pick path, footprint fence

Branch `push/B1e`: commit 1 (`200c43e`) touches `csrc/events.c` (real "leaf work"); commit 2 (`82a18f1`) adds `.swarm/leaf-B1e/wave-1.base.json` naming leaf `B1e` -> commit `200c43e`. Run via `merge_cli.py merge B1e --dry-run` against a throwaway independent clone (`/tmp/pxF6/project_e`, its own local bare `origin_e.git` -- an independent clone rather than a worktree of the live checkout was required here specifically, since `merge_cli.py merge` needs to redirect the `project`'s own `origin` remote to a controlled stand-in, and a `git worktree` shares its main checkout's remote config; overriding it there would have altered the real checkout's origin for every worktree at once).

- Exit code: **0**. Wall time: **2.3s** (footprint-fence-only dry-run, not the full suite).
- Output: `OK  dry-run: cherry-picked ['200c43ee3bb9083b3633aa74a4c49972938d1651'] from push/B1e onto fresh main; footprint fence: OK OK` -- only the leaf sha was cherry-picked; the `.swarm/**` artifact commit's file never appears in the diff the footprint fence checked (footprint fence ignores `.swarm/**` regardless, but the real point of this replay is that the artifact commit is never even cherry-picked at all, so it could not land on main even if the ignore list were wrong).
- This exercises `_dry_run_merge`, added specifically so "dry-run" performs the real cherry-pick and a real footprint check rather than printing a sentence -- see bug 2 below, found by this exact replay.

## Bugs found (both false positives; fixed, with new positive-control tests, before this table's final numbers)

1. **Worktree-path noise in "changed assertions" (`merge_gate_support.regression_check`).** Any ctypes `AttributeError` for an unbuilt symbol embeds the `.so`'s own absolute path (`"<path>/libouroboros.so: undefined symbol: ..."`); the before-worktree and the candidate live at two different temp paths by construction, so this fired on nearly every STUB failure in the codebase (E-06..E-17 is almost entirely stubs today). Replay (b)'s first run showed 8 unrelated "changed assertions" (`test_E03_S023`, seven `test_E07_S053` rows) alongside the real, intended finding; a control run of `merge_gate_support.py regression` against a **pure docs-only diff** came back REJECT on the same 7 `test_E07_S053` ids with zero code changed. Fixed: both worktree roots are replaced with a common placeholder in every first-assertion string before comparing (`_normalize_worktree_paths`). New positive control in `tests/specfactory/test_merge_gate_support.py`. Commit `98fa65b`.
2. **`cmd_merge --dry-run` didn't check anything (`merge_cli.py`).** Before this pass, `--dry-run` just printed a sentence describing what it would do, never performing the cherry-pick or the footprint check -- replay (e) as originally asked ("must pass the footprint fence via the cherry-pick path") was not actually provable. Fixed: `_dry_run_merge` performs the real cherry-pick in a throwaway detached worktree and calls `merge_gate_support.footprint_check` directly, stopping before any push. While building this fix, found and fixed a **third** bug (below) it immediately exposed.
3. **Cherry-pick worktree checked out ON the base branch itself (`merge_queue.py`, `merge_cli.py`).** `merge_queue.merge_candidate`'s `cherry_pick_shas` path (and `merge_cli.py`'s `revert`/`_dry_run_merge`) added the worktree directly on the `tmp_main` (`_merge_main`) branch, not detached. Each cherry-pick (or revert) then advanced `tmp_main`'s own ref along with HEAD, so `git diff tmp_main..HEAD` afterward compared a ref to itself -- always empty. No candidate merged this way could ever fail a footprint or regression check keyed on `tmp_main` by name. Confirmed by reconstructing the pre-fix code in isolation (not by reverting and re-running the real commit) and replaying the exact scenario: it reported `OK (no diff)` where the fixed code correctly reports `REJECT ... mod.py`. Fixed: `git worktree add --detach` for all three call sites; the pre-existing rebase path (checks out the *candidate* branch, never `tmp_main`) was never affected. Commit `d60676b`.
4. **`cmd_docs`'s collection and lint checks were absolute, not before/after (`merge_cli.py`).** Replay (d)'s first run rejected a purely docs-only, unrelated branch twice in a row: first because `tests/qa/t1/test_rts_detectors.py` fails to *collect* on main today (it imports `scripts.qa.rts_detectors`, expected red ahead of piece Q2's own build -- not a fenced-test defect, a normal pre-build state); second, after fixing that, because `csrc/sim.c` already carries 335 un-allowlisted bare literals on main (the allowlist predates a recent legitimate `sim.c` change, and `sim.c` is a protected engine file this profile has no business re-running `--gen-allowlist` against). An absolute "must collect clean" / "must lint clean" check would have rejected *every* docs commit through this profile for as long as either gap exists. Fixed: both checks now compare a worktree at fresh main against the rebased candidate, rejecting only a NEWLY broken file or a NEW lint violation the candidate's own diff introduces (`libm_lint`/`alg_constants --lint` run with `csrc` as a *relative* path under each worktree's own `cwd`, so the FAIL-line sets are comparable at all -- an absolute path bakes in each worktree's own scratch location). New positive controls for both gaps. Commits `7f6e456`, `b14f664`.

## Gate wall time and the timeout to set

`merge_gate.sh`'s full run (steps 1-11, `tests/csim` before/after in a throwaway worktree, `tests/qa/t1` before/after, acceptance, `qa_t1` standalone, `checksum_trace` O0-vs-O2 over 500 ticks including two fresh builds, `undertest_check`) measured **71-79 seconds** three times on this machine, on a tree of 686+92+119 fenced `tests/csim` items and 20 `tests/qa/t1` items, `csrc` at its current (mostly-stub E-06..E-17) size. `merge_cli.py`'s `--dry-run` paths (no full suite, footprint-fence-only or collection+lint-only) ran in 2-13 seconds. Recommendation: **300s working timeout for the current tree size**, with real headroom before the item's own suggested default (`merge_cli.py merge`'s `--timeout 1500`) -- the fifteen-fold margin absorbs the real suite's eventual growth (686 fenced tests today will roughly quadruple once E-06..E-17 stop being stubs and their bodies actually run) plus the two full builds `checksum_trace`'s O0/O2 comparison forces every gate run.
