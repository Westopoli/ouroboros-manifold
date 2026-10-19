# Branch triage, second audit (T18; 2026-10-15)

Westley chose (c) on 2026-10-15: delete only what a second audit proves landed by another route. A read-only Sonnet audit (`proof.py`) checked 379 `origin/push/*` branches of the 2026-09-22 to 09-24 families (B*, C*, T1-*, T2g*, F2*, HDR*, INV-*, SAVE-1, W-1*, CONST-1, HARNESS-consplit-*).

Proof per branch: for every file changed against its merge-base with main, (i) the branch tip's blob equals a blob in that path's history on `origin/main`, or (ii) the file is absent on main and the ledger or `pieces.toml` shows the piece landed. A deleted file that still exists on main fails.

| Class | Count | File |
|---|---|---|
| proven landed: tip is an ancestor of main | 97 | `proven_list.txt` |
| proven landed: every file byte-identical on main | 153 | `proven_list.txt` |
| provisional (proof ii only via ledger "OK merged" lines, no sha): C2-6-tests, C8-10-revert | 2 | kept |
| not proven | 127 | `proof_all_379.txt` (first failing file per branch) |

`delete_list.txt` is the 250 names (no `origin/` prefix). **Nothing is deleted until Westley says so**; the command would be `git push origin --delete push/<name>` per line. Caveat: proof (i) shows the content reached main at some commit, not that main still carries it.

The 127 not proven, by first failing file: csrc intermediate states 82 (chronicle.c, events.c, fog.c, om_internal.h, ouroboros_sim.h, om_pipe.c, mission.c, tactical_*.c, diplomacy.c, generational.c), autoload 9, scenes 7, `.swarm`/`.claude-swarm` tooling artefacts 16, docs 6 (the INV-* investigation notes of 2026-10-01/02 are unique content: keep), tests 7. These wait for an Architect look or a third audit that diffs each tip against main's current file.
