# Mesh report, Mac week against the Linux branches (Architect, 2026-10-19)

Westley asked (2026-10-19): examine what the Mac chat did while the Linux box was off (2026-10-14 night to 2026-10-19), say how well it meshes with what Linux left behind, and what the Dispatcher skips or redoes to get back up and running. This page is that report. Part 1 is for Westley; part 2 is the Dispatcher's checklist; part 3 is what still needs Westley.

## 1. For Westley

**Short answer: it meshes.** The Mac week was records only: 40 commits, every one a document (specs, the decision pack, the drift audits, the register dedupe, the lane P respec, two mockup branches). No code moved on main, so nothing the Linux side built is invalidated. Every branch Linux left waiting still has its tests and its shots. What the two sides both touched is the bookkeeping: the piece ledger, the owner table and the programme page. Those merge with conflicts on four of the waiting branches, and a records clerk resolves each by keeping both sides' rows. That is routine and costs no builds.

**What the player gets from it, in order.** Nothing is lost and the order is unchanged from the 2026-10-14 plan: the owner-table batches first (they unblock everything), then the starting-force contract and the galaxy quality-control piece that were stacked on them, then the layout engine (P1, then P2), the space view, the chronicle one-entry-at-a-time fix, edge scrolling, and the harness fix that keeps test runs out of the machine's home folder. The Mac added a week of sim-lane work behind those (the jump logs, the chronicle context, the control stubs) and two mockups that you judge by eye, which never land.

**What changed under the Linux branches.** Three things, none of them breaking:
- Lane P beyond P2 was respecced to layout-first after you closed the terrain question on 2026-10-15, and its later pieces wait on the terrain-obeys mockup verdict (in, 2026-10-21). P1 and P2, which are built and waiting, stand as they were.
- Nine open-question ids were renumbered in the register dedupe. None of the waiting branches cites an old id, so nothing needs re-pointing.
- The one-shot-per-lane rule for your review folder is suspended for the 2026-10-18 batch, so the folder holds every pending shot at once (19 of them) until you rule; then the rule resumes.

**What you do, in player terms.** Three things only: answer what is left of the decision pack (part 3 lists it), run the branch delete that the guard refused, and say which running chat is the Dispatcher so the checklist below reaches it. Once you say go, the eleven answers you already wrote get processed exactly by your protocol (one agent per three points, kept alive through any back-and-forth), and the two audits you asked for run beside them.

## 2. For the Dispatcher (implementation detail)

Read origin/main `d469152e`, never the live checkout (it is 40 commits behind and carries Westley's files).

**Test merges against origin/main, run 2026-10-19 with `git merge-tree --write-tree`:**

| Branch | Merge | Conflict files | Note |
|---|---|---|---|
| `push/vg-rec-sprint7` 45f4d637 | clean | | land first |
| `push/vg-rec-sprint8` 49a06881 | conflicts | `push_ledger_2026-09-22.md`, `push/pieces.toml` | records clerk resolves keeping both sides' rows; carries the LAB-REV2-E0 edges, TD-VG-E-26, startforce rev 13, TD-VG-E-32 |
| `push/vg-e7-base`, `-tests`, `-docs` | conflicts (same two files) | stacked on records 8 | after records 8 lands: re-merge main, then relaunch the E7 workflow with `baseRef ''` and `args.skip` for base, tests, build (your 2026-10-14 memory already says this); its clerk needs VG-A-edgescroll and VG-B24b attached first |
| `push/vg-b24b-land` d0f883c5 | conflicts (same two files) | stacked on records 8 | same treatment as E7 |
| `push/vg-p1-land2` 08c700ea | clean | | gate as it stands |
| `push/vg-p2-fin` 9c3d85ac | conflicts | `push_ledger_2026-09-22.md` | after P1: resume the P2 script with the skip set in your memory |
| `push/vg-dview-b3` a3495155 | clean | | S-246 green; the shot `D-S246-space-sheets-rings-tube.png` is still owed to `story_reviews/westley/` with a README row |
| `push/vg-b26` f263d4e5 | clean | | |
| `push/vg-a-edgescroll-land` fb63e2af | clean | | |
| `push/vg-udir-land2` | conflicts | `push_ledger_2026-09-22.md` | gate this one, not `vg-udir-final`: land2 contains final plus the pipe-build-first gate change (940291d3, approved 2026-10-14) and the records |
| `push/alg-cover-e08-e10`, `push/const-2`, `push/simlogs-tests`, `push/simlogs-tests-2`, `push/chron-context-tests` | clean | | the Mac's branches; see the handoff page for what each is |
| `push/proto-transition`, `push/proto-terrain-obeys-2` | clean | | mockups, never land; judged by eye |

**Steps, in order.**
1. Baseline on Linux (handoff step 1): the full csim suite. Diff against two records, the Linux one from 2026-10-14 (`2026-10-14-skill-lab-rev2-baseline.md`, lines 28 to 38 list the known reds) and the Mac one (`sim_lane_2026-10-12/runs/2026-10-18_mac/csim_top.summary.txt`: 2,838 passed, 31 failed, 8 errors). Expected on Linux and not a finding: A99 hashes times three (TD-SIM-5), the E-17 S112 to S119 backlog, R-045-09, R-085-04, the 92 control stubs in the controls suite. Mac-only, must be green here: the eight `-msse2` probe-build errors and `test_W7_library_imports_no_sin`. Anything else red is new and stops the queue.
2. Records 7, then records 8 through a records clerk (engineer, Sonnet, literal paths, merge on non-fast-forward, never rebase); `status_check.py --repo .` and `owner_lint.py` OK before each push. Expect the programme header to still say "sprint under EXC-sprint-2026-10-13": that exception expired 2026-10-15 evening, so the cap is two build workflows and one landing again unless Westley renews it. The clerk rewrites the header line in the same change.
3. E7 and B24b re-merged on the new main and relaunched with skip sets; nothing landed re-runs.
4. P1 gate, then the P2 resume. D-VIEW, B26, edgescroll, userdir-land2 through the gate in your queue order; the D-VIEW clerk copies the S-246 shot to Westley's folder.
5. The TD-VG-W-6 twin (W2 timing test, min of 7): no branch carries it on origin (`push/nw-w6*` are unrelated); check the clerk's journal before assuming it was pushed.
6. The answers.md protocol and the two audits are the Architect chat's spawns, not yours; they start on Westley's go.
7. The Mac's sim-lane pieces (SIM-LOGS and onward) wait on their `depends_on` (LAB-REV2-E0, CONTRACT-cone-state, VG-CONTRACT-E7, VG-E-prodslot, VG-E-startforce, B5) and on Westley's B5 answer (the second-Fable audit of the SIM-LOGS contract paragraph, or his waiver).
8. The 250-branch delete list (`branch_triage_2026-10-15/delete_list.txt`) is Westley's to run; do not retry it.

**Records facts to carry.** `pieces.toml` on origin/main still has VG-P1 and VG-P2 as queued and no VG-P3 row (the lane table says "VG-P1 building"; P3 onward live in the places spec rev 5 only). Register re-ids from 0f0c6b4b: Q-002-01 to Q-002-03, Q-065-01 to Q-065-03, Q-085-01 to Q-085-03, Q-085-02 to Q-085-04, Q-111-01 to Q-111-03, Q-118-02 to Q-118-04, Q-120-02 to Q-120-04; Q-124-02 and Q-130-01 merged into the older rows. Records 7 and 8 cite none of the old ids. The Architect owes you the E7 preflight text (`args.released`, `args.audit`, `args.gaps`) before the E7 relaunch; ask by message when records 8 is on main.

## 3. What still needs Westley

Not settled by the handoff, the decision pack's answered part (Batch A, which this chat has not read past its heading, per the instruction at its top) or the pack's part C:
- The workflow cap: two build workflows (the rule) or renew the four of the expired sprint exception.
- Records-only landings: may they skip the merge gate, yes or no.
- Pack B9 (the chronicle map waits or runs on, Q-069-03), B10 (the galaxy renderer, Q-B23b-01), B5 (second-Fable audit of SIM-LOGS or waiver), B23 (where a supreme commander's successor appears, ALG-49), B20, B21, B22.
- Shift for layer preference or drop it (Q-003-02) and the move-cancels-walking-transfer reading of R-002-04, unless a Batch A answer already covers them.
- The shots in `story_reviews/westley/` (the B24 galaxy layout rows and the rest of the 2026-10-18 batch), and the D-S246 shot once the D-VIEW clerk lands it there.
- Which running chat is the Dispatcher (its session name), so part 2 reaches it by message.
