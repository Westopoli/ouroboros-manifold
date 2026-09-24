# M-client: manager brief (open in a Sonnet chat, cwd `~/Projects/om-push/m3`)

You manage the transport and Godot client queue of the push. Method: `docs/northstar/plans/briefs/2026-09-22-two-day-push.md` (read "Day-3 corrections" first), specs under `docs/northstar/plans/push/specs/` (T1.md, C8.md), pieces in `docs/northstar/plans/push/pieces.toml`, history in the tail of `docs/northstar/plans/push_ledger_2026-09-22.md`, evidence format in `docs/northstar/proving_ground/evidence/push_2026-09-22/first_look/README.md`. Every leaf gets `docs/northstar/plans/briefs/leaf-mechanics.md` verbatim plus a five-line delta. M0 (Claude session `parallel-backend-client-mvp`) rules, merges, tags and writes the ledger; you never push to main and never message M0 to start.

First action in the chat: when the rate-limit prompt ever appears, choose "wait here, then continue automatically". Then `git fetch -q origin && git merge --ff-only origin/main` in the clone.

## Queue rule

A dependency counts as met when its branch is on origin (`git ls-remote --heads origin 'push/*'`), not only when it is tagged or merged: the leaf bases on or merges that branch (see leaf-mechanics.md). Only a dependency that has not been pushed at all blocks a piece. Landing on main is M0's serialized step and never gates starting work.

Same as M-sim: next piece whose dependencies are met, one direct Sonnet leaf per piece in its own worktree, forward each report to M0 in one message, never two leaves on one file. Client leaves verify with `scripts/run_godot_tests.sh` and, for desktop pieces, `scripts/qa_harness.sh liveness` plus `tests/qa/desktop/test_flow_spine.py`; every visual claim is filed as held with a screenshot path, never as pass.

## Queue on 2026-09-24 (in order)

Waiting for M0's merge: C2-3 and C7-2 (galaxy over the live pipe, daemon `state` carrying the scene's `qa_state()`, harness creating `logs/` and `.venv`) — a leaf may still be running from M0; check origin before touching.

1. C8-look-4: after C2-3/C7-2 merge, the look-3 procedure again (galaxy live: 80 systems drawn, owners coloured, six plants each differ from clean by pixel count) into `first_look/look4/`.
2. C4-2: briefing and debrief screens read the live mission frame (B9-2/B9-3 on main) instead of the fixture; test first (`tests/test_briefing_debrief.gd` live case), then the scene.
3. C3-3: chronicle scroll reads the live chronicle frame once B8 is merged.
4. C5-2: tactical view reads the live tactical snapshot once B12 is merged (units move; plants for stuck and rubber-band).
5. T2g-2: save slots bound to T2c-2's `om_save_state_*` through the pipe (`save`/`load` commands per `docs/architecture.md`).
6. C2-4: galaxy plant `conquest-no-recolour` exercised over a scripted 200-tick run (a region changes owner and recolours).
7. Anything M0 adds by message.

## Never

Edit tests, `csrc/**` except `csrc/pipe/**`, docs, or another manager's files; run `worktree_ops.py`; merge main into a leaf branch (rebuild by copy instead); stage Westley's files; run Godot with the live checkout as cwd.
