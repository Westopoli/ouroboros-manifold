# M-sim: manager brief (open in a Sonnet chat, cwd `~/Projects/om-push/m1`)

You manage the C simulation queue of the push. Method: `docs/northstar/plans/briefs/2026-09-22-two-day-push.md` (read "Day-3 corrections" first, then "Waves 1 to 3"), pieces and statuses in `docs/northstar/plans/push/pieces.toml`, history in the tail of `docs/northstar/plans/push_ledger_2026-09-22.md`. Every leaf you spawn gets `docs/northstar/plans/briefs/leaf-mechanics.md` verbatim plus a five-line delta. M0 (Claude session `parallel-backend-client-mvp`) rules, merges, tags and writes the ledger; you never push to main and never message M0 to start.

First action in the chat: when the rate-limit prompt ever appears, choose "wait here, then continue automatically". Then `git fetch -q origin && git merge --ff-only origin/main` in the clone.

## Queue rule

A dependency counts as met when its branch is on origin (`git ls-remote --heads origin 'push/*'`), not only when it is tagged or merged: the leaf bases on or merges that branch (see leaf-mechanics.md). Only a dependency that has not been pushed at all blocks a piece. Landing on main is M0's serialized step and never gates starting work.

Take the next piece in the list below whose dependencies are tagged (`git fetch --tags; git tag -l 'attach/*'`) or merged as increments (ledger). One leaf per piece, in its own worktree, direct (no overlord, no shard testers), spawned with `subagent_type: sonnet46-doer` (Sonnet 4.6, pinned by the agent definition) — never the bare `sonnet` alias, which resolves to Sonnet 5. Never two live leaves on one file. When a leaf reports, forward the report to M0 in one message (`SendMessage` to `parallel-backend-client-mvp`: branch, sha, green/red counts, leftovers, test defects, missing constants) and take the next piece. Do not spawn for a piece whose branch already exists on origin unless M0 asked for an increment.

## Queue on 2026-09-24 (in order)

Branches already pushed and waiting for M0's merge: B5b, B15m, B14, B11, B13, B4-2 (+test), F2j-2, B7-6, T2c-2, B8 and B12 (leaves may still be running from M0; check `git ls-remote --heads origin 'push/*'` and the ledger before touching them), B9-3, B10b.

1. B1-7: events.c save hooks (`events_state_size/_write/_read` on the slot, F2j-2 defines them; E-16 chain-counter round trip). Depends on F2j-2 merged.
2. B7-4: generational.c save hooks (ledger and characters round trip). Depends on F2j-2.
3. B12b: tactical_move.c leftovers once B11 and B15m are merged (S-096 fog call, S-098).
4. B11-2: fog.c leftovers once M0 lands the unit accessors header commit (unit faction, unit type, enumeration) — wait for the ledger row naming it.
5. B13-2, B14-2: enemy_macro.c and tactical_support.c leftovers once B10b and B9-3 are merged (clock advance, objective centre, parity).
6. Q2 impl: `scripts/qa/rts_detectors.py` against `tests/qa/t1/test_rts_detectors.py` (M0 owns the tests).
7. Anything M0 adds by message.

## Never

Edit tests, headers, docs, or another manager's files; run `worktree_ops.py`; merge main into a leaf branch (rebuild by copy instead); stage Westley's files; start the Agora dispatcher.
