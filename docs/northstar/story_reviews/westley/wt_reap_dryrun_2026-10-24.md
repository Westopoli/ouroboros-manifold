# Worktree reap dry run, second run, 2026-10-24

Westley: this is what the cleanup would do after the fix to the tool; nothing has been removed. First run before HARNESS-wt-cap-2: remove 218 trees, 100.8 GB; it kept 366 trees dirty on build noise the tool did not recognise. This second run is `wt.py reap --dry-run` on the fixed tool.

- Would remove: 558 trees, 258.3 GB.
- Keeps, by reason (260 trees): dirty 95 (44.1 GB), not-on-origin 69 (32.5 GB), foreign 73 (22.0 GB), pending 4 (2.3 GB), open-files 4 (2.0 GB), active 3 (1.3 GB), pinned 2 (1.0 GB), young 2 (0.9 GB), not-worktree 8 (1.4 GB). Dirty, not-on-origin and open-files trees stay because they may hold work git does not have.
- Slots and disk (from status): `worktrees 818 slots 5/12 wt 365.7/120 free 75.2/60` (slots in use / cap, wt GB / cap, free GB / floor).
- Not-worktree directories, ruled by hand before any removal: .pytest_cache 1 MB; PC-speed-v 91 MB; _stale 663 MB; baseline_cache 13 MB; baseline_cache_mainpipe 1 MB; logs 1 MB; vg-e1-shot-land-tmp 305 MB; vg-e1c-land-tmp 365 MB. Foreign trees (73): 22.0 GB in total (unchanged), ruled by hand before any removal.
- Young list (would be removed, age under 2 days, spare any a live chat still uses; age is from the tree's .git file, so it counts from creation): 462 trees: ans-01 (0.8d), ans-03 (0.8d), ans-04 (0.8d), ans-06 (0.8d), arch-e1c-spec (0.8d), b25-lay-branch (0.8d), b25-lay-main (0.8d), batch-rev (0.8d), batch-rev3 (0.8d), chk-a17-run (0.8d), chk-base-b26r (0.8d), chk-base-e1h3 (0.8d), chk-clean-udir (0.8d), chk-cs004-run (0.8d), chk-e1m-build (0.8d), chk-e1n-build (0.8d), chk-e1n-tests (0.8d), chk-e1r-build (0.8d), chk-e1r-build-r2 (0.8d), chk-e7-b20 (0.8d), chk-e7-base (0.8d), chk-e7-base-r20 (0.8d), chk-e7-base-r21 (0.8d), chk-e7-base-r22 (0.8d), chk-e7-base-r23 (0.8d), chk-e7-base-r24 (0.8d), chk-e7-base2 (0.8d), chk-e7-base3 (0.8d), chk-e7-basew (0.8d), chk-e7-build (0.8d), chk-e7-build-c (0.8d), chk-e7-build-main (0.8d), chk-e7-goldens (0.8d), chk-e7-goldens-2 (0.8d), chk-e7-goldens-b (0.8d), chk-e7-goldens-c (0.8d), chk-e7-goldens-m (0.8d), chk-e7-goldens-main (0.8d), chk-e7-main (0.8d), chk-e7-ref (0.8d), chk-e7-tests-m (0.8d), chk-e7-tests-r2 (0.8d), chk-e7g-main (0.8d), chk-ke5-gate (0.8d), chk-main-ref (0.8d), chk-main-ref2 (0.8d), chk-main-udir (0.8d), chk-protodens3 (0.8d), chk-push-vg-b26 (0.8d), chk-push-vg-b26-tests (0.8d), chk-push-vg-b26r-tests (0.8d), chk-push-vg-e1c-tests-fix (0.8d), chk-push-vg-e1h-2 (0.8d), chk-push-vg-e1h-3 (0.8d), chk-push-vg-e1p-a (0.8d), chk-push-vg-ka-pipe-2 (0.8d), chk-push-vg-ka-support-2 (0.8d), chk-push-vg-kd1 (0.8d), chk-push-vg-kd1-tests (0.8d), chk-push-vg-ke4 (0.8d), chk-push-vg-ke5-base (0.8d), chk-vg-a16 (0.8d), chk-vg-a16-main (0.8d), chk-vg-a18cam-base (0.8d), chk-vg-a18cam-r2 (0.8d), chk-vg-a18cam-r2-base (0.8d), chk-vg-b22 (0.8d), chk-vg-b22-comment (0.8d), chk-vg-b22-main (0.8d), chk-vg-b25 (0.8d), chk-vg-b25-main (0.8d), chk-vg-dview-c3-pg (0.8d), chk-vg-dview-pg (0.8d), chk-vg-flobby (0.8d), chk-vg-flobby-main (0.8d), chk-vg-flobby-pg (0.8d), chk-w2-base (0.8d), chk-w2-build (0.8d), chk-w2-contract (0.8d), costreport-build (1.8d), costreport-tests (1.8d), ctxguard-records (0.8d), ctxguard-tests (0.8d), ctxguard2-tests (0.8d), diag-walk-ke2 (0.8d), dl-build (1.8d), fa-build (1.8d), fa-tests (1.8d), fab-audit (0.8d), fab-audit2 (0.8d), fab-rev (0.8d), fst-build (1.8d), fst-tests (1.8d), ft-tests (1.8d), galaxy-look (0.8d), gate-kd (0.8d), gate-kd-main (0.8d), goc-build (1.8d), goc-tests (1.8d), gp-build (1.8d), gp-tests (1.8d), greentests (0.8d), greentests-lab (0.8d), guard-rule (0.8d), inv-simfacing (0.8d), io-tests (1.8d), kr-build (1.8d), kr-tests (1.8d), lab-placed (0.8d), lab-placed-land (0.8d), lab-run1 (0.8d), labrev2-captrace3 (0.8d), labrev2-drift (0.8d), labrev2-drift2 (0.8d), labrev2-e0 (0.8d), labrev2-e0-tests (0.8d), labrev2-e1-tests (0.8d), labrev2-e2-tests (0.8d), labrev2-e3-tests (0.8d), labrev2-e4-tests (0.8d), labrev2-fix-audit (0.8d), labrev2-fix-audit2 (0.8d), labrev2-fix5-audit (0.8d), labrev2-flipeval (0.8d), labrev2-flipeval2 (0.8d), labrev2-l1-tests (0.8d), labrev2-l2-tests (0.8d), labrev2-l3-tests (0.8d), labrev2-l4-tests (0.8d), labrev2-l6-tests (0.8d), labrev2-l7-tests (0.8d), labrev2-l8m-audit (0.8d), labrev2-l8m2 (0.8d), labrev2-l8m2-tests (0.8d), labrev2-landA (0.8d), labrev2-landE3 (0.8d), labrev2-landLab (0.8d), labrev2-pins (0.8d), labrev2-vc-ruler (0.8d), labrev2-vc-ruler-old (0.8d), labrev2-vc-tests (0.8d), labrev3-a-ruler (0.8d), labrev3-a-tests (0.8d), labrev3-b (0.8d), labrev3-b-ruler (0.8d), labrev3-b-sbuild (0.8d), labrev3-b-smoke (0.8d), labrev3-b-tests (0.8d), labrev3-c (0.8d), labrev3-c-ruler (0.8d), labrev3-c-tests (0.8d), lakefill-build (1.8d), lakefill-tests (1.8d), land-4 (1.8d), land-5 (1.8d), land-dl (1.8d), land-wtcap (0.8d), land-wtcap2 (0.8d), landlab-prep (0.8d), lm-build (1.8d), lm-tests (1.8d), lm-tests3 (1.8d), lop-mainref (0.8d), lop-tests (1.8d), lp-build (1.8d), lp-tests (1.8d), ls-build (1.8d), ls-tests (1.8d), lt-build (1.8d), lt-tests (1.8d), merge-ab (0.8d), mvp-play (0.8d), nsm-tests (1.8d), pcyc-build (1.8d), pcyc-tests (1.8d), pieces-flip (0.8d), play-main (0.8d), proto-density-pre (0.8d), proto-density-pre-b (0.8d), proto-galaxy-shot (0.8d), proto-walkers (0.8d), protodens3-pre (0.8d), rec-audits (1.8d), rec-batch13 (0.8d), rec-credit9pm (1.8d), rec-drift (1.8d), rec-recordslock (1.8d), rec-slots1 (1.8d), rec-slots3 (1.8d), rec-td-l8m2 (0.8d), records-22a (1.8d), records-22b (1.8d), records-23a (1.8d), records-23b (1.8d), records-23c (1.8d), records-24 (1.8d), records-25 (1.8d), records-26 (1.8d), records-27 (1.8d), records-28 (1.8d), records-28b (1.8d), records-29 (1.8d), records-29b (1.8d), records-batch8 (1.8d), rf-build (1.8d), rf-tests (1.8d), roadmap (0.8d), sc-build (1.8d), sc-tests (1.8d), scout-icons (0.8d), scout-k-d1 (0.8d), sd-tests2 (1.8d), sd-tests3 (1.8d), sd-tests4 (1.8d), sdk-audit (0.8d), sdk-audit2 (0.8d), sdk-drift (0.8d), sdk-rev (0.8d), sdkbuf-build (1.8d), sdkbuf-tests (1.8d), seed-main (0.8d), showcase-refs (0.8d), showcase-secrets (0.8d), simlane-audit-ab (0.8d), simlane-d (0.8d), simlane-land (0.8d), sj-build (1.8d), sj-tests (1.8d), sv-spec (0.8d), sv0-row (0.8d), sv4-base (0.8d), ud-build (1.8d), ugf-base (0.8d), ugf-build (1.8d), ugf-tests (1.8d), vg-a-edgescroll-land (0.8d), vg-a-plays (0.8d), vg-a-tests (0.8d), vg-a1 (0.8d), vg-a11 (0.8d), vg-a12 (0.8d), vg-a13 (0.8d), vg-a13b (0.8d), vg-a14 (0.8d), vg-a15b (0.8d), vg-a16b-base (0.8d), vg-a16c-main (0.8d), vg-a17-land (0.8d), vg-a18cam-pre (0.8d), vg-a18cam-pre-s3 (0.8d), vg-a18cam-pre2 (0.8d), vg-a1b (0.8d), vg-a2 (0.8d), vg-a3 (0.8d), vg-a4 (0.8d), vg-a5 (0.8d), vg-a5b (0.8d), vg-a6 (0.8d), vg-a7 (0.8d), vg-a8 (0.8d), vg-a9 (0.8d), vg-b-ctrl (0.8d), vg-b-land-10 (0.8d), vg-b-land-11 (0.8d), vg-b-land-8 (0.8d), vg-b-look-land (0.8d), vg-b-look-land-2 (0.8d), vg-b-look-tests (0.8d), vg-b-main-chk (0.8d), vg-b-plays (0.8d), vg-b-plays-2 (0.8d), vg-b-tests-fix-5 (0.8d), vg-b0 (0.8d), vg-b0-main (0.8d), vg-b1 (0.8d), vg-b1-tests (0.8d), vg-b11 (0.8d), vg-b12-2 (0.8d), vg-b13 (0.8d), vg-b13-fix (0.8d), vg-b14 (0.8d), vg-b14-2 (0.8d), vg-b15 (0.8d), vg-b16 (0.8d), vg-b16-main (0.8d), vg-b17 (0.8d), vg-b18 (0.8d), vg-b19 (0.8d), vg-b2 (0.8d), vg-b20-2 (0.8d), vg-b20-base (0.8d), vg-b22-land (0.8d), vg-b23-base (0.8d), vg-b23-px-main (0.8d), vg-b23-px-vk (0.8d), vg-b23-rulings (0.8d), vg-b23-shot (0.8d), vg-b24-pg (0.8d), vg-b24-pre (0.8d), vg-b24-pre-b (0.8d), vg-b24-pre-c (0.8d), vg-b24-pre-d (0.8d), vg-b24b-pre (0.8d), vg-b26-land2 (0.8d), vg-b26r-base (0.8d), vg-b3a (0.8d), vg-b3a-tests (0.8d), vg-b3b-2 (0.8d), vg-b3b-fix (0.8d), vg-b3b-fix-2 (0.8d), vg-b3b-fix-3 (0.8d), vg-b4 (0.8d), vg-b5 (0.8d), vg-b5-2 (0.8d), vg-b5-3 (0.8d), vg-b6 (0.8d), vg-b7-tests (0.8d), vg-b9 (0.8d), vg-b9-base (0.8d), vg-c-plays-3 (0.8d), vg-c-tests (0.8d), vg-c10b (0.8d), vg-c10c (0.8d), vg-c10d (0.8d), vg-c10e-2 (0.8d), vg-c6 (0.8d), vg-c6-2 (0.8d), vg-c7-2 (0.8d), vg-c8 (0.8d), vg-ca-land-2 (0.8d), vg-d-goldens (0.8d), vg-d-goldens-2-base (0.8d), vg-d-goldens-base (0.8d), vg-d-land (0.8d), vg-d-land-3 (0.8d), vg-d2 (0.8d), vg-d2-2 (0.8d), vg-d3-2 (0.8d), vg-d4-2 (0.8d), vg-d5-2 (0.8d), vg-d5-3 (0.8d), vg-d7 (0.8d), vg-d7-tests (0.8d), vg-dview-base (0.8d), vg-dview-pre (0.8d), vg-dview-pre2 (0.8d), vg-dview-pre4 (0.8d), vg-dview-pre5 (0.8d), vg-dview-pre6 (0.8d), vg-dview-pre7 (0.8d), vg-dview-pre8 (0.8d), vg-dview-pre9 (0.8d), vg-e1a2-base (0.8d), vg-e1a3-base (0.8d), vg-e1g-3-base (0.8d), vg-e1g-tests (0.8d), vg-e1h-3-base (0.8d), vg-e1i (0.8d), vg-e1screens-pre (0.8d), vg-e7r-3-base (0.8d), vg-e7r-gbase2 (0.8d), vg-e7r-land (0.8d), vg-e7r-pre (0.8d), vg-f-land (0.8d), vg-f-land-2 (0.8d), vg-f-scripts (0.8d), vg-f-scripts-fix (0.8d), vg-f-tests (0.8d), vg-f-tests-fix (0.8d), vg-f5 (0.8d), vg-f5b (0.8d), vg-f6a (0.8d), vg-f6b (0.8d), vg-flobby-pre3 (0.8d), vg-g1-base (0.8d), vg-g2 (0.8d), vg-g3 (0.8d), vg-gate-mainpipe (0.8d), vg-guard-land (0.8d), vg-h-renderer (0.8d), vg-harness-c1b (0.8d), vg-k-tests (0.8d), vg-k-tests-2 (0.8d), vg-k0 (0.8d), vg-ka-bridge-base (0.8d), vg-ka-check-fog (0.8d), vg-ka-check-terrain (0.8d), vg-ka-check-unit (0.8d), vg-ka-land (0.8d), vg-ka-main-chk (0.8d), vg-ka-mapgen (0.8d), vg-ka-mapgen-base (0.8d), vg-ka-mission (0.8d), vg-ka-pipe (0.8d), vg-ka-pipe-2 (0.8d), vg-ka-support-2 (0.8d), vg-ka-terrain (0.8d), vg-ka-unit (0.8d), vg-ka2-land (0.8d), vg-ka2-land-2 (0.8d), vg-kd (0.8d), vg-kd-land (0.8d), vg-kd-tests (0.8d), vg-kd1-main (0.8d), vg-kd1-pre (0.8d), vg-kd2 (0.8d), vg-ke5-goldens (0.8d), vg-ke5-land (0.8d), vg-ke5-rulings (0.8d), vg-kf (0.8d), vg-kf-land (0.8d), vg-kh-bridge (0.8d), vg-kh-land (0.8d), vg-kh-pipe (0.8d), vg-kh-pipe-2 (0.8d), vg-kh-tests (0.8d), vg-kh-wire (0.8d), vg-nettick-pre (0.8d), vg-nettick-pre2 (0.8d), vg-p1-land2 (0.8d), vg-p1-land3 (0.8d), vg-parked-3 (0.8d), vg-perf-minof-w2 (0.8d), vg-pipe-split (0.8d), vg-pipe-split-base (0.8d), vg-prodslot-base (0.8d), vg-prodslot-bl (0.8d), vg-prodslot-gbase (0.8d), vg-prodslot-land (0.8d), vg-rec-sprint6 (0.8d), vg-rec-sprint7 (0.8d), vg-rec-sprint8 (0.8d), vg-script-p2r-land (0.8d), vg-split-land-2 (0.8d), vg-t-r087-land (0.8d), vg-t-reach-land (0.8d), vg-u-pipe-tests-land (0.8d), vg-udir-land (0.8d), vg-udir-land3 (0.8d), vg-udir-land4 (0.8d), vg-udir-pre (0.8d), vg-udir-pre-b (0.8d), vg-w1-leftovers (0.8d), vg-w1-pre (0.8d), vg-w2b (0.8d), vg-w2r-pre (0.8d), vg-w2s-goldens-base (0.8d), vg-w2s-goldens2-orig (0.8d), vg-w2s-pre (0.8d), vg-w2s-pre3 (0.8d), vg-w2s-pre5 (0.8d), vg-w4 (0.8d), vgd1-gate (0.8d), vgd1-main (0.8d), vl-build (1.8d), vl-tests (1.8d), wtcap-build (0.8d), wtcap-partb (0.8d), wtcap-records (0.8d), wtcap-tests (0.8d), wtcap2-build (0.8d), wtcap2-tests (0.8d)

Bulk removal runs only on Westley's word (wt.py reap without --dry-run, by the clerk).

## Kept trees with real changes (164 rows)

The trees kept `dirty` or `not-on-origin`. Columns: name, branch (HEAD is detached), last commit subject, age in days, the top three top-level paths changed (count of files; `build` and `.wt-state` are build output and the flag, counted here only because the listing is raw). Westley rules on these rows; the tool never removes them.

| name | branch | last commit subject | age days | changed paths (top 3) | kept |
|---|---|---|---|---|---|
| A23-bis | HEAD | U1 P2: first shot ready on tick target first in range (R-084-01), gated PURSUE_BY_STEERING | 0.8 | build (326), csrc (1), .wt-state (1) dirty |
| A3-u | HEAD | U7: cohort (id-1)%N, float backswing, post-move fire pass, same-tick return fire (parity,  | 0.8 | .wt-state (1) not-on-origin |
| A5-opt-base | HEAD | PP-move A5 opt: collision passes 2..N revisit only units a displacement touched; positions | 0.8 | .wt-state (1), tests (1) dirty |
| PC-survey | push/pc-survey | Merge remote-tracking branch 'origin/push/pc-g67' into push/pc-survey | 0.8 | .wt-state (1), tests (1) not-on-origin |
| PD-focus | push/pd-focus | Merge remote-tracking branch 'origin/push/pd-formation' into push/pp-build | 0.8 | docs (3), .wt-state (1) dirty |
| PP-land2 | push/pp-a-land2 | Merge remote-tracking branch 'origin/main' into push/pp-a-land2 | 0.8 | tests (1), .wt-state (1), pipe (1) not-on-origin |
| U-guard | HEAD | PP guard tests: rule id R-096-08, step-in-flight tolerance in the lost-target test | 0.8 | .wt-state (1) not-on-origin |
| ans-09 | push/ans-9-simviewer-run | EXC-sprint-2026-10-13 extended: four build workflows stay until Westley says two (Westley  | 0.8 | .shots (2), .wt-state (1), pipe (1) dirty |
| audit-cov | HEAD | Merge origin/main into push/vg-script-e7r3-land | 4.8 | tests (122), assets (47), scenes (41) dirty |
| c25-records | push/vg-c25-records | Merge remote-tracking branch 'origin/main' into push/vg-c25-records | 0.8 | docs (36), CLAUDE.md (1), .wt-state (1) dirty |
| chk-a17-run-r3 | chk-a17-run-r3 | Merge remote-tracking branch 'origin/push/vg-a17s-play' into chk-a17-run-r3 | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| chk-a17-run2 | chk-a17-run2 | Merge remote-tracking branch 'origin/push/vg-a17s-play' into chk-a17-run2 | 0.8 | assets (47), .wt-state (1), pipe (1) not-on-origin |
| chk-build-udir | HEAD | HARNESS-userdir: client.screenshot makes user_dir/qa (fresh user dir has none) | 0.8 | tests (122), assets (47), scenes (41) dirty |
| chk-e1q-join | HEAD | Merge remote-tracking branch 'origin/push/vg-e1q-rulings' into HEAD | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| chk-e1r-base | HEAD | Harness: HARNESS-lab-slow-tier built (row note and ledger row) | 0.8 | .wt-state (1), pipe (1), tests (1) dirty |
| chk-e1r-main | HEAD | Merge origin/main into push/vg-e1r-rec (ledger: both sides kept; E1r finding row on day37) | 0.8 | .wt-state (1), pipe (1), tests (1) dirty |
| chk-e1r-main-r2 | HEAD | Merge origin/main into push/vg-e1r-rec (ledger: both sides kept; E1r finding row on day37) | 0.8 | .wt-state (1), pipe (1), tests (1) dirty |
| chk-e1w-build | HEAD | Rule pins lines on the E1 screens tests (HARNESS-C1b) | 0.8 | tests (122), assets (47), scenes (41) dirty |
| chk-e7-base-c | HEAD | Merge remote-tracking branch 'origin/main' into push/vg-harness-c1b-land | 0.8 | tests (29), .wt-state (1), pipe (1) dirty |
| chk-e7-build-ref | HEAD | Records: FINDING-lab-d11 one-way reach decided fight, verdict decided_one_way_reach in LAB | 0.8 | tests (22), .wt-state (1), pipe (1) dirty |
| chk-e7-join | HEAD | Merge remote-tracking branch 'origin/push/vg-e7r-docs2' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-join-r20 | HEAD | Merge vg-e7r-goldens (pieces theirs, ledger both) | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-join-r21 | HEAD | Merge remote-tracking branch 'origin/push/vg-e7r-goldens' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-join-r22b | HEAD | Merge remote-tracking branch 'origin/push/vg-e7r-goldens' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-join-r23 | HEAD | join: goldens (ledger both) | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-join-r24 | HEAD | Merge remote-tracking branch 'origin/push/vg-e7r-goldens' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-join2 | HEAD | Merge remote-tracking branch 'origin/push/vg-e7r-goldens' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-join3 | HEAD | join check: merge vg-e7r-goldens (ledger both sides) | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-joinw | HEAD | Merge remote-tracking branch 'origin/push/vg-e7r-goldens' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-e7-m20 | HEAD | Records: TD-VG-E-27 row and VG-CONTRACT-E7 owns brought to the E7 branch text; FU-E7-reinf | 0.8 | tests (23), .wt-state (1), pipe (1) dirty |
| chk-e7-rev | HEAD | Merge origin/main into push/vg-e7r-3m (ledger, pieces, spec take main's side; TD-VG-E-33 k | 0.8 | csrc (7), .wt-state (1), pipe (1) dirty |
| chk-e7-tests | HEAD | Merge remote-tracking branch 'origin/main' into push/vg-e7r-tests | 0.8 | tests (122), assets (47), scenes (41) dirty |
| chk-e7-tests-b | HEAD | Merge remote-tracking branch 'origin/main' into push/vg-e7r-tests | 0.8 | tests (122), assets (47), scenes (41) dirty |
| chk-fskel-join | HEAD | Merge remote-tracking branch 'origin/push/vg-fskel-b2' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-main | HEAD | Sprint file: HARNESS-gate-parallel-stages paragraph (parallel stages inside one gate; desi | 0.8 | tests (123), assets (47), scenes (41) dirty |
| chk-push-vg-b24b | HEAD | VG-B24b: galaxy quality row in Settings DISPLAY card, qa_state keys, drop known-red line | 0.8 | tests (122), assets (47), scenes (41) dirty |
| chk-push-vg-b24b-tests | HEAD | VG-B24b tests: story play S-110, galaxy quality choice in Settings (R-110-02, A54/A60) | 0.8 | tests (122), assets (47), scenes (41) dirty |
| chk-push-vg-b26r | HEAD | Merge remote-tracking branch 'origin/push/vg-b26r-rulings2' into push/vg-b26r | 0.8 | tests (122), scenes (41), autoload (8) dirty |
| chk-vg-a18cam | HEAD | Merge remote-tracking branch 'origin/push/vg-a18cam-play-tests' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| chk-vg-a18cam-main | HEAD | Records 2026-10-13: A18 test fixes (TD-VG-A-15, FINDING-edge-scroll-restore-overshoot, FU- | 0.8 | tests (124), assets (47), scenes (41) dirty |
| chk-vg-a18cam-r2-comb | HEAD | a18 ground-era set_terrain centre = own-unit box, anchors param (FU-A18-3d) | 0.8 | tests (128), assets (47), scenes (41) dirty |
| chk-vg-a18cam-r2-mb | HEAD | VG-B24 owns tests/test_vg_b_b22.gd (row 6 :189 and header :27-30 only, TD-VG-B-18) | 0.8 | tests (123), assets (47), scenes (41) dirty |
| chk-vg-dview | HEAD | space view pans to own-unit centroid at ground height, kind-7 anchor only as fallback | 0.8 | tests (122), assets (47), scenes (42) dirty |
| chk-vg-dview-c3 | HEAD | Merge newer VG-D-VIEW test and play branches (b3ace679, 37bfc970) | 0.8 | tests (122), assets (47), scenes (42) dirty |
| chk-vg-dview-c3-main | HEAD | Skill lab rev 2 spec rev 2: both audits folded in (contract fixed, E4 radius guard, seams  | 0.8 | tests (122), assets (47), scenes (41) dirty |
| chk-vg-dview-c3-scratch | HEAD | Merge newer VG-D-VIEW test and play branches (b3ace679, 37bfc970) | 0.8 | scenes (2), .wt-state (1), pipe (1) dirty |
| chk-vg-dview-main | HEAD | Skill lab rev 2: workflow spec (2026-10-14) and the LAB-REV2 umbrella owner row | 0.8 | tests (122), assets (47), scenes (41) dirty |
| chk-vg-dview-rev | HEAD | space view pans to own-unit centroid at ground height, kind-7 anchor only as fallback | 0.8 | tests (122), scenes (49), assets (47) dirty |
| chk-w2-tests | HEAD | Merge remote-tracking branch 'origin/push/vg-w2s-docs' into HEAD | 0.8 | tests (122), scenes (41), autoload (8) not-on-origin |
| clerk-b2b3 | clerk/b2b3 | merge push/B2B3 (B2 hold zone 12000 ticks, B3 rivals) | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| clerk-clock | clerk/clock | merge relay/04-clock-code (Q-076-02 clock table) | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| clerk-hdr5 | clerk/hdr5 | Merge push/HDR5-ver-td (HDR5 C2 region scale 512) | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| diag-walk-main | HEAD | Journal: E1f landing 2 | 0.8 | csrc (1), .wt-state (1) dirty |
| flake-cold | HEAD | ROADMAP.md: loop fix and playthrough gate landed; next is B1, B6, B7, C6; W6 to W8 for Wes | 0.8 | assets (47), tests (42), scenes (6) dirty |
| flake-rootcause | push/flake-rootcause | Record Westley's batch 12: strongpoints and weather (Q-218-01..04, -06, Q-219-01, -03 clos | 0.8 | autoload (2), scenes (2), .wt-state (1) dirty |
| galaxy-before-shrink | push/galaxy-field | galaxy field: delete the legacy shell renderer and shader, add new look pictures | 0.8 | scenes (249), assets (47), tests (27) dirty |
| gate-w4 | HEAD | W4 lobby: host/join, MatchRecord, ready/go, menu row, route | 0.8 | scenes (3), autoload (1), .wt-state (1) dirty |
| gatebase-land | push/vg-gatebase-land | Merge remote-tracking branch 'origin/main' into push/vg-gatebase-land | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| inv-landview | inv/landview | Westley page: the live S-140 command needs OM_GODOT_GUI=1 (the PATH godot is a headless wr | 0.8 | tests (122), assets (47), scenes (42) dirty |
| l8m-verify | push/labrev2-l8m-land | Merge origin/main into L8M verification | 2.8 | - not-on-origin |
| l8m-verify-main | HEAD | Lab: DEC-lab-post-gate-records-merge, DEC-SPEED-2-ratio (DRAFT-lab-speed-ratio-2 0.60) | 2.8 | tests (4) dirty |
| lab-land | clerk/lab-land | Merge remote-tracking branch 'origin/main' into clerk/lab-land | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| lab-rev2-records | HEAD | LAB-REV2 umbrella owns the baseline file | 11.8 | - not-on-origin |
| labdiag | HEAD | Merge origin/main (VG-CONTRACT-E7 landing, records) into push/labrev2-landLab | 3.9 | scripts (31), docs (1), tests (1) dirty |
| labrev2-base-audit | HEAD | L6 preflight: route every mover by 50 wu BFS with per-kind mask, drop straight-line flyer  | 0.8 | tests (4), scripts (3), .wt-state (1) dirty |
| labrev2-captrace2 | HEAD | LAB-REV2 flip tests: orders_per_unit default False (TD-LAB-REV2-flip, decisions 13/21/23/4 | 0.8 | scripts (1), .wt-state (1) dirty |
| labrev2-e2-audit | HEAD | LAB-REV2-E2 tests: firing arc (R-100-04 draft), cone area damage (R-082-06 draft), om_comb | 0.8 | csrc (2), .wt-state (1) dirty |
| labrev2-e2-scratch | HEAD | Merge remote-tracking branch 'origin/main' into push/labrev2-e2-tests | 0.8 | tests (3), csrc (2), .wt-state (1) dirty |
| labrev2-l2-audit-scratch | HEAD | Merge origin/main into push/labrev2-l2-tests | 0.8 | scripts (12), docs (1), .wt-state (1) dirty |
| labrev2-l3-audit-ref | HEAD | LAB-REV2-L3 tests: roster mixes M0 to M4, same mix both sides, no vision factor, s3 plays  | 0.8 | docs (1), scripts (1), .wt-state (1) dirty |
| labrev2-l4-ref | scratch/labrev2-l4-ref | Merge remote-tracking branch 'origin/main' into push/labrev2-lab | 0.8 | tests (32), scripts (7), .wt-state (1) dirty |
| labrev2-l4-ref2 | HEAD | scratch: merge main | 0.8 | tests (16), scripts (3), .wt-state (1) not-on-origin |
| labrev2-l4-ref3 | HEAD | scratch: merge main | 0.8 | tests (16), scripts (3), .wt-state (1) not-on-origin |
| labrev2-l6-scratch | HEAD | LAB-REV2-L6 tests: s1_slope_top (scene, grid, knobs, controls), highground tests retired,  | 0.8 | scripts (5), .wt-state (1) dirty |
| labrev2-l8-e1bcheck | HEAD | E1b ruler: return-fire out-of-range scenes put the attack-moving attacker inside the senso | 0.8 | scripts (4), .wt-state (1), tests (1) dirty |
| labrev2-l8-ref | HEAD | Merge origin/main into push/labrev2-l8-tests | 0.8 | scripts (4), tests (2), .wt-state (1) dirty |
| labrev2-landE3-base | HEAD | Skill lab rev 2 spec: E1 excluded from the engine-only golden proof by design; lands with  | 0.8 | .wt-state (1), tests (1) dirty |
| labrev2-roles-check | HEAD | LAB-REV2-FIX-2: roles from Setup, per-type naive anchors, walkers-only no_fit, blind post  | 5.8 | tests (1) dirty |
| land-3 | push/vg-c-land3 | Merge remote-tracking branch 'origin/main' into push/vg-c-land3 | 0.8 | .sdk_engineer_report.md (1), .wt-state (1), landing-template.md (1) not-on-origin |
| land-3b | push/vg-c-land3b | Shots for Westley, lane C landing 3b: land march order (28 wardens selected, move ok, tick | 1.8 | tests (125), docs (60), assets (47) dirty |
| land-ugfnsm | push/vg-c-land-ugfnsm | playthrough_known_red: remove test_fresh_checkout_boots_to_main_menu_without_numpy_or_logs | 1.8 | tests (123), assets (47), scenes (41) dirty |
| lf-count-1 | HEAD | Record Westley's batch 4: Q-192-01, -02, -05, Q-197-01 closed; Q-191-04 amended (layout en | 0.8 | .wt-state (1), desktop_counts.txt (1), godot_counts.txt (1) dirty |
| lop-build | push/vg-c-landone | TD-pin-refresh-2026-10-23: refresh R-009-01 and R-104-10 pins after the space-only layer r | 1.8 | tests (123), assets (47), scenes (41) dirty |
| nsm-build | push/vg-c-noslope | VG-C-no-slope-markers: drop the per-slope midline bars and the midlines qa key | 1.8 | tests (122), assets (47), scenes (41) dirty |
| p2r-rec3 | push/vg-p2r-rec3 | Merge remote-tracking branch 'origin/main' into push/vg-p2r-rec3 | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| pf-godot | HEAD | Layout engine: methods page for arranging puzzle pieces, Q-191-12 candidates, Q-191-13 | 0.8 | assets (47), tests (42), scenes (6) dirty |
| pf-lab | HEAD | Merge remote-tracking branch 'origin/push/lab-bind-tfix' into HEAD | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| pre-escr | HEAD | Records: Warden aura does not stack, visible 300 wu radius (R-083-03 rewritten, Q-084-01 c | 0.8 | tests (129), assets (47), scenes (46) dirty |
| proto-highground | HEAD | highground: full batch run 2026-10-05 | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| proto-land-iter | push/proto-land-iter | land mockup pass 6b: cliff pieces removed, impassable ground shaded, canvas up to 128,000  | 0.8 | assets (47), tests (41), scenes (7) dirty |
| records-batch3 | push/vg-records-batch3 | Merge remote-tracking branch 'origin/main' into push/vg-records-batch3 | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| s132-scout | HEAD | Shots for Westley, lane C landing 3b: land march order (28 wardens selected, move ok, tick | 0.8 | docs (4), .sdk_engineer_report.md (1), .wt-state (1) dirty |
| s246-proof | HEAD | Merge remote-tracking branch 'origin/main' into push/vg-d-s246-import | 0.8 | docs (2), .sdk_engineer_report.md (1), .wt-state (1) dirty |
| sc-fl2 | push/showcase-fl2 | Records batch 22b: audit4 highs applied (test-edit-row, size-lint-fail, red-evidence, csim | 0.8 | docs (1), .sdk_engineer_report.md (1), .wt-state (1) dirty |
| sc-qa2 | push/showcase-qa2 | Records batch 22b: audit4 highs applied (test-edit-row, size-lint-fail, red-evidence, csim | 0.8 | docs (1), .sdk_engineer_report.md (1), .wt-state (1) dirty |
| scout-edgescroll | HEAD | Records 2026-10-13: A18 check (TD-VG-A-16, FINDING-a18-ground-centre, FU-A18-3d amended);  | 0.8 | tests (124), assets (47), scenes (42) dirty |
| scout-westley-owner | HEAD | pieces.toml: VG-A18 owns the story_reviews/westley README row and the S-103 copy (footprin | 0.8 | scripts (2), tests (2), .wt-state (1) dirty |
| sd-build | push/vg-a-sightdisc | VG-A-sightdisc: clip each sight disc at the camera near plane before projection; skip mask | 1.8 | tests (127), assets (47), scenes (41) dirty |
| sdk-scripts | push/vg-d-s246-import | Merge remote-tracking branch 'origin/main' into push/vg-d-s246-import | 1.8 | tests (122), assets (47), scenes (41) dirty |
| sdk-scripts2 | HEAD | Merge remote-tracking branch 'origin/main' into records-venvlink | 0.8 | drafts (5), .sdk_engineer_report.md (1), .wt-state (1) dirty |
| sdk-trial-standins | HEAD | Records 2026-10-21 (batch 6): twelve rule violations from the sim-viewer run recorded as f | 3.8 | .sdk_engineer_report.md (1), standins_batch_1.md (1) dirty |
| sf-records | push/vg-sf-records | Merge remote-tracking branch 'origin/main' into push/vg-sf-records | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| showcase-fl | HEAD | Westley 2026-10-23: exhaust the credit by 21:00 EDT, checkpoint 16:00 (DEC-credit-9pm) | 0.8 | .sdk_engineer_report.md (1), .wt-state (1), docs (1) dirty |
| showcase-qa | HEAD | Westley 2026-10-23: exhaust the credit by 21:00 EDT, checkpoint 16:00 (DEC-credit-9pm) | 0.8 | .sdk_engineer_report.md (1), .wt-state (1), docs (1) dirty |
| simlane-audit-c | HEAD | Sim lane 2026-10-13: findings ledger (61 rows), mission-choice and chronicle-source runner | 0.8 | tests (15), .wt-state (1) dirty |
| site-captures | HEAD | Record Westley's batch 12: strongpoints and weather (Q-218-01..04, -06, Q-219-01, -03 clos | 0.8 | assets (47), tests (43), scenes (16) dirty |
| sl-memory-base | HEAD | Merge push/pa-land: A199, attack-move holds formation until an enemy is in attack range (R | 0.8 | .wt-state (1), tests (1) dirty |
| sv4-land | push/sv4-land | SV-4 lands: pieces row attached at 4e4b2ae1, programme lane row | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| tmp-vg-a18-testfix | HEAD | Merge commit 'a54e1d5e4a9b806040f09d5bbee4de24b8c52f4e' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-a-land-10 | push/vg-a-land-10 | lane_plays_known_red: drop S-134 and S-136 ground entries (pass with 9g) | 0.8 | tests (119), docs (64), scenes (41) dirty |
| vg-a-land-5 | push/vg-a-land-5 | Merge remote-tracking branch 'origin/push/vg-a-plays-fix-2' into push/vg-a-land-5 | 0.8 | tests (118), assets (47), scenes (45) not-on-origin |
| vg-a-land-8 | push/vg-a-land-8 | TD-VG-A-10: c5_3 drag box from units_px | 0.8 | tests (120), assets (47), scenes (41) not-on-origin |
| vg-a11b | push/vg-a11b | Merge remote-tracking branch 'origin/push/vg-aa-land' into push/vg-a11b | 0.8 | .wt-state (1) not-on-origin |
| vg-a16 | push/vg-a16 | Merge remote-tracking branch 'origin/push/vg-aa-land' into push/vg-a16 | 0.8 | .wt-state (1) not-on-origin |
| vg-a16-land | push/vg-a16-land | Merge remote-tracking branch 'origin/push/vg-a16b' into push/vg-a16-land | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| vg-a17-play | push/vg-a17-play | Land F-SKEL-A and F-SKEL-B: Steam-less lobby skeleton (UDP transport, local lobby backend, | 0.8 | tests (123), assets (47), scenes (41) dirty |
| vg-a18cam-playverify-scratch | HEAD | Merge branch 'push/vg-a18cam-play-tests' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-a18cam-testfix2-scratch | HEAD | Merge commit '3c1285c9' into HEAD | 11.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-b-land-7 | push/vg-b-land-7 | Merge remote-tracking branch 'origin/push/vg-b-tests-fix-4' into push/vg-b-land-7 | 0.8 | .wt-state (1) not-on-origin |
| vg-b-tests-fix-6 | push/vg-b-tests-fix-6 | TD-VG-B-9: B17 expects chronicle names; S-108 play reaches the chronicle scroll | 15.9 | tests (118), scenes (45), autoload (7) dirty |
| vg-b19-land | push/vg-b19-land | Merge origin/push/vg-b19 into push/vg-b19-land | 0.8 | tests (118), assets (47), scenes (45) dirty |
| vg-b20 | push/vg-b20 | Merge origin/push/vg-b19 into push/vg-b19-land | 0.8 | tests (118), scenes (48), assets (47) dirty |
| vg-b20-scratch | HEAD | Merge remote-tracking branch 'origin/push/vg-b-tests-fix-6' into HEAD | 0.8 | .wt-state (1) not-on-origin |
| vg-b22-landbase | HEAD | Scripts fix 1: B22 records keeps the existing VG-B22 row and the builder owns the shell_la | 0.8 | tests (122), assets (47), scenes (41) dirty |
| vg-b23-land | push/vg-b23-land | Merge origin/main into the B23 landing (K-d1 landing 3125ee77; ledger appends keep both si | 0.8 | tests (122), assets (47), scenes (41) dirty |
| vg-b24b-pre-2 | HEAD | Merge origin/push/vg-rec-sprint8 (local preflight; ledger conflict kept both sides) | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-b25-gate | push/vg-b25-gate | Merge remote-tracking branch 'origin/main' into push/vg-b25-gate | 0.8 | tests (122), assets (47), scenes (44) not-on-origin |
| vg-b25-land | push/vg-b25-land | VG-B25 lands: dim wash, four real-depth star layers, camera-following dust (DRAFT-b25-*);  | 0.8 | tests (122), assets (47), scenes (44) not-on-origin |
| vg-b26-land | push/vg-b26-land | Merge remote-tracking branch 'origin/main' into push/vg-b26-land | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-b26-pre | HEAD | VG-D-VIEW spec paragraph rev 1: the first space look (sheets, asteroid slabs, units with l | 0.8 | tests (122), assets (47), scenes (41) dirty |
| vg-b26r-pre | HEAD | Readings recorded for Westley's go on asks 2 and 3: E7 starting-force floor (at least half | 0.8 | tests (122), assets (47), scenes (41) dirty |
| vg-b3b | push/vg-b3b | merge b3b tests | 0.8 | .wt-state (1) not-on-origin |
| vg-cb-land-2 | push/vg-cb-land-2 | Merge remote-tracking branch 'origin/push/vg-a-plays-era' into push/vg-cb-land-2 | 0.8 | tests (119), assets (47), scenes (40) not-on-origin |
| vg-dview-b3-base | HEAD | Merge origin/main into rec/altkeys-2026-10-13 | 0.8 | tests (122), assets (47), scenes (42) dirty |
| vg-dview-land | push/vg-dview-land | Merge remote-tracking branch 'origin/main' into push/vg-dview-land | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| vg-dview-scratch2 | HEAD | Merge commit '4674fefacfe96c583485182ee66744e5642f0c9a' into HEAD | 0.8 | tests (123), assets (47), scenes (43) not-on-origin |
| vg-dview-tests-run | HEAD | Merge origin/main into rec/altkeys-2026-10-13 | 0.8 | tests (125), assets (47), scenes (41) dirty |
| vg-e1a3-land | push/vg-e1a3-land | Merge remote-tracking branch 'origin/push/vg-ke3-docs-3' into push/vg-e1a3-land | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| vg-e1a3-land-2 | push/vg-e1a3-land-2 | Merge remote-tracking branch 'origin/push/vg-ke3-docs-3' into push/vg-e1a3-land-2 | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-e1c-3 | push/vg-e1c-3 | Merge remote-tracking branch 'origin/push/vg-e1c-2' into push/vg-e1c-3 | 0.8 | csrc (1), .wt-state (1), pipe (1) not-on-origin |
| vg-e1d-2 | push/vg-e1d-2 | Merge remote-tracking branch 'origin/push/vg-e1c-2' into push/vg-e1d-2 | 0.8 | .wt-state (1) not-on-origin |
| vg-e1e | push/vg-e1e | merge e1e tests | 0.8 | .wt-state (1) not-on-origin |
| vg-e1q-rulings-verify | HEAD | Merge remote-tracking branches 'origin/push/vg-e1q-field' and 'origin/push/vg-e1q-lots' in | 0.8 | tests (2), .wt-state (1) not-on-origin |
| vg-e1screens-land | push/vg-e1screens-land | Merge remote-tracking branch 'origin/main' into push/vg-e1screens-land | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-e1w | push/vg-e1w | E1w: wire TickerBeats and MapMarkers into the tactical view (PIECES, shell, frame path, qa | 4.8 | assets (47), docs (2), pipe (1) dirty |
| vg-e1w-b | push/vg-e1w-b | Merge origin/push/vg-e1n-fix into e1w-b | 4.8 | tests (122), assets (47), scenes (41) dirty |
| vg-e7 | push/vg-e7 | merge vg-e7-tests | 0.8 | csrc (7), docs (1), scenes (1) not-on-origin |
| vg-e7-pre | HEAD | Merge remote-tracking branch 'origin/push/vg-rec-sprint8' into HEAD | 0.8 | tests (122), scenes (41), autoload (8) not-on-origin |
| vg-e7-pre-fg | HEAD | scratch dry run GAP 13 (never pushed) | 0.8 | .wt-state (1), pipe (1) not-on-origin |
| vg-e7-pre-r2 | HEAD | Merge remote-tracking branch 'origin/push/vg-rec-sprint8' into HEAD | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-e7-proto | HEAD | Merge remote-tracking branch 'origin/push/vg-rec-sprint8' into push/vg-e7-base | 0.8 | tests (123), assets (47), scenes (41) dirty |
| vg-e7r-exp2 | HEAD | Records: decision 49 (L8 moved semantics), damage_up cap findings, cap-trace evidence, lay | 0.8 | tests (122), assets (47), scenes (41) dirty |
| vg-e7r-goldens-stale | push/vg-e7r-goldens-stale | Merge origin/push/vg-e7r-3 into push/vg-e7r-goldens (ledger: both sides kept) | 0.8 | tests (122), assets (47), scenes (41) not-on-origin |
| vg-e7r7-build | HEAD | Merge remote-tracking branch 'origin/push/vg-e7r-rulings6' into HEAD | 0.8 | .wt-state (1) not-on-origin |
| vg-e7r7-stub | HEAD | Merge remote-tracking branch 'origin/push/vg-e7r-rulings6' into HEAD | 0.8 | .wt-state (1) not-on-origin |
| vg-f-s140-click-land | push/vg-f-s140-click-land | Merge origin/main into push/vg-f-s140-click-land (programme: main's lobby row, S-140 row k | 0.8 | docs (4), .wt-state (1) dirty |
| vg-f5-land-4 | push/vg-f5-land-4 | TD-VG-A-7: play_support sends bare bool to set_fog_filter | 0.8 | tests (118), assets (47), scenes (47) dirty |
| vg-flobby-land-r2 | push/vg-flobby-land-r2 | Merge origin/main into push/vg-flobby-land-r2 (known-red: keep S-140, S-143 and S-241 remo | 0.8 | .wt-state (1) not-on-origin |
| vg-harness-c1b-red | HEAD | HARNESS-C1b: rule_pins_tests.py, empty sidecar, pre_gate pins and provenance steps, merge_ | 0.8 | tests (2), .wt-state (1) dirty |
| vg-k0-land | push/vg-k0-land | Park the dead-slot cost test (Westley bound 3.0, red at 4.5x): kept on push/vg-parked, off | 17.8 | tests (52), assets (47), autoload (7) dirty |
| vg-nettick-diag | HEAD | net view loads match last_frame, no extra step in _load_live (VG-F-NETTICK) | 12.8 | tests (124), assets (47), scenes (41) dirty |
| vg-prodslot-mv | HEAD | Merge origin/main into push/vg-chain1-scripts | 0.8 | tests (122), assets (47), scenes (41) dirty |
| vg-udir-land2 | push/vg-udir-land2 | HARNESS-userdir: gate builds pipe/ouroboros_pipe before the first regression stage; test_7 | 0.8 | .wt-state (1) not-on-origin |
| vg-w2s-tests3-build | HEAD | VG-W2: rename the static point helper (the exported om_move_route_point name is withdrawn) | 0.8 | tests (1), .wt-state (1), pipe (1) dirty |

## Dry-run table (verbatim)

```
KEEP .pytest_cache not-worktree
KEEP A23-bis dirty
KEEP A3-u not-on-origin
KEEP A5-opt-base dirty
KEEP B10c-10-r foreign
KEEP B10c-4-scale foreign
KEEP B10c-7-base foreign
KEEP B10c-7-scale foreign
KEEP B10c-8-tp foreign
KEEP B10c-base foreign
KEEP B11-6-base foreign
KEEP B11-6-scale foreign
KEEP B12-3-try foreign
KEEP B12-7-scale foreign
KEEP B12-9-scale-after foreign
KEEP B12-9-scale-before foreign
KEEP B14-7-base foreign
KEEP B14-7-mine foreign
KEEP B3-chr-land foreign
KEEP B5-tt-main foreign
KEEP B8-8-throwaway foreign
KEEP C3-G5 foreign
KEEP C3-r097 foreign
KEEP C7-2 foreign
KEEP F2r foreign
KEEP G-simbridge-1 foreign
KEEP HDR4-2-r foreign
KEEP PA-base foreign
KEEP PC-g3-base foreign
KEEP PC-speed-v not-worktree
KEEP PC-survey not-on-origin
KEEP PD-focus dirty
KEEP PP-land2 not-on-origin
KEEP T1-2 foreign
KEEP T1-b7-diag foreign
KEEP T2c foreign
KEEP TD-tacview-main foreign
KEEP U-guard not-on-origin
KEEP _stale not-worktree
REMOVE ans-01 456 MB (dry run)
REMOVE ans-03 377 MB (dry run)
REMOVE ans-04 368 MB (dry run)
REMOVE ans-06 498 MB (dry run)
KEEP ans-09 dirty
REMOVE arch-audit2 481 MB (dry run)
REMOVE arch-batch2 482 MB (dry run)
REMOVE arch-batchslim 482 MB (dry run)
REMOVE arch-credits 484 MB (dry run)
REMOVE arch-credits-run 481 MB (dry run)
REMOVE arch-e1c-spec 427 MB (dry run)
REMOVE arch-epicdrift 481 MB (dry run)
REMOVE arch-fu-obey 377 MB (dry run)
REMOVE arch-fu-obey-6b 377 MB (dry run)
REMOVE arch-fu-obey-p1 377 MB (dry run)
REMOVE arch-fu-obey-rec 482 MB (dry run)
REMOVE arch-fu-reshot 498 MB (dry run)
REMOVE arch-fu-s103 484 MB (dry run)
REMOVE arch-fu-simviewer 484 MB (dry run)
REMOVE arch-fu-transition 484 MB (dry run)
REMOVE arch-fu-transition-run 456 MB (dry run)
REMOVE arch-implrec 482 MB (dry run)
KEEP arch-read pinned
REMOVE arch-rec-evening 493 MB (dry run)
REMOVE arch-rec-night 494 MB (dry run)
REMOVE arch-rec3 495 MB (dry run)
REMOVE arch-rec4 498 MB (dry run)
REMOVE arch-rec5 483 MB (dry run)
REMOVE arch-rec6 486 MB (dry run)
REMOVE arch-shots 482 MB (dry run)
REMOVE arch-statusfix 482 MB (dry run)
REMOVE arch-toolsplit 504 MB (dry run)
REMOVE arch-verdict-qs 482 MB (dry run)
REMOVE arch-verdict-qs2 482 MB (dry run)
REMOVE arch-verdict1 481 MB (dry run)
REMOVE arch-verdict2 481 MB (dry run)
REMOVE arch-verdict3 482 MB (dry run)
KEEP audit-cov dirty
KEEP b-land open-files
REMOVE b25-lay-branch 503 MB (dry run)
REMOVE b25-lay-main 503 MB (dry run)
KEEP baseline_cache not-worktree
KEEP baseline_cache_mainpipe not-worktree
REMOVE batch-rev 450 MB (dry run)
REMOVE batch-rev3 450 MB (dry run)
KEEP bk-1 foreign
KEEP bk-13 foreign
KEEP bk-14 foreign
KEEP bk-16 foreign
KEEP bk-17 foreign
KEEP bk-18 foreign
KEEP bk-19 foreign
KEEP bk-2 foreign
KEEP bk-26 foreign
KEEP bk-28 foreign
KEEP bk-3 foreign
KEEP bk-32 foreign
KEEP bk-34 foreign
KEEP bk-6 foreign
KEEP bk-8 foreign
KEEP boot-proof foreign
REMOVE c25-fix 502 MB (dry run)
KEEP c25-records dirty
REMOVE c25patch-land 615 MB (dry run)
REMOVE c4-land2 614 MB (dry run)
KEEP cand-missionover2 foreign
REMOVE chain2-scripts-land 619 MB (dry run)
REMOVE chk-a17-run 447 MB (dry run)
KEEP chk-a17-run-r3 not-on-origin
KEEP chk-a17-run2 not-on-origin
REMOVE chk-base-b26r 501 MB (dry run)
REMOVE chk-base-e1h3 441 MB (dry run)
KEEP chk-build-udir dirty
REMOVE chk-clean-udir 458 MB (dry run)
REMOVE chk-cs004-run 447 MB (dry run)
REMOVE chk-e1m-build 499 MB (dry run)
REMOVE chk-e1n-build 500 MB (dry run)
REMOVE chk-e1n-tests 499 MB (dry run)
KEEP chk-e1q-join not-on-origin
KEEP chk-e1r-base dirty
REMOVE chk-e1r-build 495 MB (dry run)
REMOVE chk-e1r-build-r2 495 MB (dry run)
KEEP chk-e1r-main dirty
KEEP chk-e1r-main-r2 dirty
KEEP chk-e1w-build dirty
REMOVE chk-e7-b20 603 MB (dry run)
REMOVE chk-e7-base 616 MB (dry run)
KEEP chk-e7-base-c dirty
REMOVE chk-e7-base-r20 613 MB (dry run)
REMOVE chk-e7-base-r21 615 MB (dry run)
REMOVE chk-e7-base-r22 615 MB (dry run)
REMOVE chk-e7-base-r23 616 MB (dry run)
REMOVE chk-e7-base-r24 616 MB (dry run)
REMOVE chk-e7-base2 613 MB (dry run)
REMOVE chk-e7-base3 613 MB (dry run)
REMOVE chk-e7-basew 613 MB (dry run)
REMOVE chk-e7-build 499 MB (dry run)
REMOVE chk-e7-build-c 494 MB (dry run)
REMOVE chk-e7-build-main 494 MB (dry run)
KEEP chk-e7-build-ref dirty
REMOVE chk-e7-goldens 496 MB (dry run)
REMOVE chk-e7-goldens-2 612 MB (dry run)
REMOVE chk-e7-goldens-b 614 MB (dry run)
REMOVE chk-e7-goldens-c 616 MB (dry run)
REMOVE chk-e7-goldens-m 616 MB (dry run)
REMOVE chk-e7-goldens-main 612 MB (dry run)
KEEP chk-e7-join not-on-origin
KEEP chk-e7-join-r20 not-on-origin
KEEP chk-e7-join-r21 not-on-origin
KEEP chk-e7-join-r22b not-on-origin
KEEP chk-e7-join-r23 not-on-origin
KEEP chk-e7-join-r24 not-on-origin
KEEP chk-e7-join2 not-on-origin
KEEP chk-e7-join3 not-on-origin
KEEP chk-e7-joinw not-on-origin
KEEP chk-e7-m20 dirty
REMOVE chk-e7-main 496 MB (dry run)
REMOVE chk-e7-ref 492 MB (dry run)
KEEP chk-e7-rev dirty
KEEP chk-e7-tests dirty
KEEP chk-e7-tests-b dirty
REMOVE chk-e7-tests-m 497 MB (dry run)
REMOVE chk-e7-tests-r2 494 MB (dry run)
REMOVE chk-e7g-main 495 MB (dry run)
KEEP chk-fskel-join not-on-origin
REMOVE chk-ke5-gate 435 MB (dry run)
KEEP chk-main dirty
REMOVE chk-main-ref 431 MB (dry run)
REMOVE chk-main-ref2 431 MB (dry run)
REMOVE chk-main-udir 462 MB (dry run)
REMOVE chk-protodens3 447 MB (dry run)
KEEP chk-push-vg-b24b dirty
KEEP chk-push-vg-b24b-tests dirty
REMOVE chk-push-vg-b26 457 MB (dry run)
REMOVE chk-push-vg-b26-tests 455 MB (dry run)
KEEP chk-push-vg-b26r dirty
REMOVE chk-push-vg-b26r-tests 500 MB (dry run)
REMOVE chk-push-vg-e1c-tests-fix 439 MB (dry run)
REMOVE chk-push-vg-e1h-2 439 MB (dry run)
REMOVE chk-push-vg-e1h-3 441 MB (dry run)
REMOVE chk-push-vg-e1p-a 436 MB (dry run)
REMOVE chk-push-vg-ka-pipe-2 538 MB (dry run)
REMOVE chk-push-vg-ka-support-2 431 MB (dry run)
REMOVE chk-push-vg-kd1 447 MB (dry run)
REMOVE chk-push-vg-kd1-tests 447 MB (dry run)
REMOVE chk-push-vg-ke4 436 MB (dry run)
REMOVE chk-push-vg-ke5-base 435 MB (dry run)
REMOVE chk-vg-a16 448 MB (dry run)
REMOVE chk-vg-a16-main 448 MB (dry run)
KEEP chk-vg-a18cam not-on-origin
REMOVE chk-vg-a18cam-base 447 MB (dry run)
KEEP chk-vg-a18cam-main dirty
REMOVE chk-vg-a18cam-r2 458 MB (dry run)
REMOVE chk-vg-a18cam-r2-base 458 MB (dry run)
KEEP chk-vg-a18cam-r2-comb dirty
KEEP chk-vg-a18cam-r2-mb dirty
REMOVE chk-vg-b22 439 MB (dry run)
REMOVE chk-vg-b22-comment 438 MB (dry run)
REMOVE chk-vg-b22-main 439 MB (dry run)
REMOVE chk-vg-b25 503 MB (dry run)
REMOVE chk-vg-b25-main 502 MB (dry run)
KEEP chk-vg-dview dirty
KEEP chk-vg-dview-c3 dirty
KEEP chk-vg-dview-c3-main dirty
REMOVE chk-vg-dview-c3-pg 458 MB (dry run)
KEEP chk-vg-dview-c3-scratch dirty
KEEP chk-vg-dview-main dirty
REMOVE chk-vg-dview-pg 458 MB (dry run)
KEEP chk-vg-dview-rev dirty
REMOVE chk-vg-flobby 501 MB (dry run)
REMOVE chk-vg-flobby-main 501 MB (dry run)
REMOVE chk-vg-flobby-pg 492 MB (dry run)
REMOVE chk-w2-base 459 MB (dry run)
REMOVE chk-w2-build 570 MB (dry run)
REMOVE chk-w2-contract 460 MB (dry run)
KEEP chk-w2-tests not-on-origin
KEEP clerk-b2b3 not-on-origin
KEEP clerk-clock not-on-origin
KEEP clerk-hdr5 not-on-origin
KEEP core-sim-session foreign
REMOVE costreport-build 449 MB (dry run)
REMOVE costreport-tests 449 MB (dry run)
KEEP ctxguard-build active
REMOVE ctxguard-records 450 MB (dry run)
REMOVE ctxguard-tests 450 MB (dry run)
KEEP ctxguard2-build active
REMOVE ctxguard2-tests 450 MB (dry run)
REMOVE diag-walk-ke2 428 MB (dry run)
KEEP diag-walk-main dirty
REMOVE dl-build 492 MB (dry run)
KEEP docfix foreign
KEEP e06-verify foreign
REMOVE fa-build 500 MB (dry run)
REMOVE fa-tests 499 MB (dry run)
REMOVE fab-audit 449 MB (dry run)
REMOVE fab-audit2 450 MB (dry run)
REMOVE fab-rev 450 MB (dry run)
KEEP flake-cold dirty
KEEP flake-rootcause dirty
REMOVE flockfix-land 619 MB (dry run)
REMOVE fst-build 456 MB (dry run)
REMOVE fst-tests 450 MB (dry run)
REMOVE ft-tests 497 MB (dry run)
REMOVE g3pc-audit 491 MB (dry run)
REMOVE g3pc-build 491 MB (dry run)
REMOVE g3pc-land 616 MB (dry run)
KEEP g3pc-tests open-files
KEEP galaxy-before-shrink dirty
REMOVE galaxy-look 330 MB (dry run)
REMOVE gate-kd 438 MB (dry run)
REMOVE gate-kd-main 438 MB (dry run)
KEEP gate-w4 dirty
KEEP gatebase-build foreign
KEEP gatebase-land not-on-origin
REMOVE gatebase-land2 615 MB (dry run)
REMOVE gatebase-rec 620 MB (dry run)
KEEP gatebase-scripts foreign
REMOVE gatebase-scripts-land 620 MB (dry run)
REMOVE goc-build 500 MB (dry run)
REMOVE goc-tests 490 MB (dry run)
REMOVE gp-build 492 MB (dry run)
REMOVE gp-tests 499 MB (dry run)
REMOVE greentests 505 MB (dry run)
REMOVE greentests-lab 491 MB (dry run)
REMOVE guard-rule 499 MB (dry run)
KEEP inv-landview dirty
REMOVE inv-simfacing 490 MB (dry run)
REMOVE io-tests 454 MB (dry run)
REMOVE kr-build 504 MB (dry run)
REMOVE kr-tests 490 MB (dry run)
KEEP l8m-verify not-on-origin
KEEP l8m-verify-main dirty
REMOVE lab-fixer 491 MB (dry run)
REMOVE lab-fixer-main 489 MB (dry run)
KEEP lab-land not-on-origin
REMOVE lab-land2 621 MB (dry run)
REMOVE lab-placed 417 MB (dry run)
REMOVE lab-placed-land 545 MB (dry run)
KEEP lab-rev2-records not-on-origin
REMOVE lab-run1 457 MB (dry run)
KEEP labdiag dirty
KEEP labrev2-base-audit dirty
KEEP labrev2-captrace2 dirty
REMOVE labrev2-captrace3 493 MB (dry run)
REMOVE labrev2-drift 490 MB (dry run)
REMOVE labrev2-drift2 491 MB (dry run)
REMOVE labrev2-e0 560 MB (dry run)
REMOVE labrev2-e0-tests 449 MB (dry run)
REMOVE labrev2-e1-tests 449 MB (dry run)
KEEP labrev2-e2-audit dirty
KEEP labrev2-e2-scratch dirty
REMOVE labrev2-e2-tests 450 MB (dry run)
REMOVE labrev2-e3-tests 449 MB (dry run)
REMOVE labrev2-e4-tests 449 MB (dry run)
REMOVE labrev2-fix-audit 490 MB (dry run)
REMOVE labrev2-fix-audit2 490 MB (dry run)
REMOVE labrev2-fix5-audit 491 MB (dry run)
REMOVE labrev2-flipeval 491 MB (dry run)
REMOVE labrev2-flipeval2 494 MB (dry run)
REMOVE labrev2-l1-tests 449 MB (dry run)
KEEP labrev2-l2-audit-scratch dirty
REMOVE labrev2-l2-tests 457 MB (dry run)
KEEP labrev2-l3-audit-ref dirty
REMOVE labrev2-l3-tests 450 MB (dry run)
KEEP labrev2-l4-ref dirty
KEEP labrev2-l4-ref2 not-on-origin
KEEP labrev2-l4-ref3 not-on-origin
REMOVE labrev2-l4-tests 496 MB (dry run)
KEEP labrev2-l6-scratch dirty
REMOVE labrev2-l6-tests 491 MB (dry run)
REMOVE labrev2-l7-tests 449 MB (dry run)
KEEP labrev2-l8-e1bcheck dirty
KEEP labrev2-l8-ref dirty
REMOVE labrev2-l8m-audit 494 MB (dry run)
REMOVE labrev2-l8m2 495 MB (dry run)
REMOVE labrev2-l8m2-tests 495 MB (dry run)
KEEP labrev2-lab foreign
REMOVE labrev2-landA 452 MB (dry run)
REMOVE labrev2-landE3 518 MB (dry run)
KEEP labrev2-landE3-base dirty
REMOVE labrev2-landLab 624 MB (dry run)
REMOVE labrev2-pins 498 MB (dry run)
KEEP labrev2-roles-check dirty
KEEP labrev2-vc foreign
REMOVE labrev2-vc-ruler 497 MB (dry run)
REMOVE labrev2-vc-ruler-old 494 MB (dry run)
REMOVE labrev2-vc-tests 496 MB (dry run)
KEEP labrev3-a foreign
KEEP labrev3-a-pbuild foreign
REMOVE labrev3-a-ruler 498 MB (dry run)
REMOVE labrev3-a-tests 496 MB (dry run)
REMOVE labrev3-b 501 MB (dry run)
REMOVE labrev3-b-ruler 497 MB (dry run)
REMOVE labrev3-b-sbuild 498 MB (dry run)
REMOVE labrev3-b-smoke 496 MB (dry run)
REMOVE labrev3-b-tests 495 MB (dry run)
REMOVE labrev3-c 503 MB (dry run)
KEEP labrev3-c-mbuild foreign
REMOVE labrev3-c-ruler 504 MB (dry run)
REMOVE labrev3-c-tests 505 MB (dry run)
REMOVE lakefill-build 458 MB (dry run)
REMOVE lakefill-tests 458 MB (dry run)
KEEP land-3 not-on-origin
KEEP land-3b dirty
REMOVE land-4 578 MB (dry run)
REMOVE land-5 579 MB (dry run)
KEEP land-b25 pending
KEEP land-cl pending
KEEP land-ctxguard open-files
KEEP land-ctxguard2 young
REMOVE land-dl 492 MB (dry run)
KEEP land-lm pending
KEEP land-sd pending
KEEP land-ugfnsm dirty
REMOVE land-wtcap 579 MB (dry run)
REMOVE land-wtcap2 579 MB (dry run)
REMOVE landlab-prep 490 MB (dry run)
KEEP lf-count-1 dirty
KEEP lf-lane3-build foreign
KEEP lf-lane3-test foreign
REMOVE lm-build 461 MB (dry run)
REMOVE lm-tests 500 MB (dry run)
REMOVE lm-tests3 499 MB (dry run)
KEEP logs not-worktree
KEEP look5 foreign
KEEP lop-build dirty
REMOVE lop-mainref 500 MB (dry run)
REMOVE lop-tests 500 MB (dry run)
REMOVE lp-build 493 MB (dry run)
REMOVE lp-tests 490 MB (dry run)
REMOVE ls-build 458 MB (dry run)
REMOVE ls-tests 458 MB (dry run)
KEEP lst-build foreign
REMOVE lt-build 449 MB (dry run)
REMOVE lt-tests 449 MB (dry run)
REMOVE measure-speed3 493 MB (dry run)
REMOVE merge-ab 498 MB (dry run)
REMOVE mvp-play 428 MB (dry run)
REMOVE nettick-edge 619 MB (dry run)
KEEP nsm-build dirty
REMOVE nsm-tests 500 MB (dry run)
REMOVE p2r-rec 619 MB (dry run)
KEEP p2r-rec3 not-on-origin
REMOVE p2r-tests2 494 MB (dry run)
REMOVE pcyc-build 463 MB (dry run)
REMOVE pcyc-tests 463 MB (dry run)
KEEP pf-godot dirty
KEEP pf-lab not-on-origin
REMOVE pieces-flip 416 MB (dry run)
REMOVE pin-ruler 492 MB (dry run)
REMOVE play-main 447 MB (dry run)
KEEP pre-escr dirty
REMOVE prodslot-land2 606 MB (dry run)
REMOVE prodslot-rec 619 MB (dry run)
REMOVE proto-density-pre 465 MB (dry run)
REMOVE proto-density-pre-b 465 MB (dry run)
REMOVE proto-galaxy-shot 330 MB (dry run)
KEEP proto-highground not-on-origin
KEEP proto-land-iter dirty
REMOVE proto-walkers 378 MB (dry run)
REMOVE protodens3-pre 465 MB (dry run)
KEEP rb2-B10c-7-tw foreign
KEEP rb2-B10c-9-tw foreign
KEEP rb5-B9-11 foreign
REMOVE rec-audits 490 MB (dry run)
REMOVE rec-batch13 416 MB (dry run)
REMOVE rec-credit9pm 490 MB (dry run)
REMOVE rec-drift 490 MB (dry run)
REMOVE rec-frontdoor 488 MB (dry run)
REMOVE rec-greek 487 MB (dry run)
REMOVE rec-lab3 489 MB (dry run)
REMOVE rec-landview 488 MB (dry run)
REMOVE rec-landview2 488 MB (dry run)
REMOVE rec-lanec 487 MB (dry run)
REMOVE rec-ool-1 487 MB (dry run)
REMOVE rec-ool-2 487 MB (dry run)
REMOVE rec-prov 489 MB (dry run)
REMOVE rec-recordslock 490 MB (dry run)
REMOVE rec-s001 487 MB (dry run)
REMOVE rec-s004 488 MB (dry run)
REMOVE rec-s005 488 MB (dry run)
REMOVE rec-s005b 488 MB (dry run)
REMOVE rec-s132 487 MB (dry run)
REMOVE rec-scrub 492 MB (dry run)
REMOVE rec-showcase0 488 MB (dry run)
REMOVE rec-showcase1 488 MB (dry run)
REMOVE rec-slopes 487 MB (dry run)
REMOVE rec-slots 490 MB (dry run)
REMOVE rec-slots1 490 MB (dry run)
REMOVE rec-slots3 490 MB (dry run)
REMOVE rec-td-l8m2 490 MB (dry run)
REMOVE records-22a 463 MB (dry run)
REMOVE records-22b 463 MB (dry run)
REMOVE records-23a 463 MB (dry run)
REMOVE records-23b 463 MB (dry run)
REMOVE records-23c 463 MB (dry run)
REMOVE records-24 463 MB (dry run)
REMOVE records-25 463 MB (dry run)
REMOVE records-26 463 MB (dry run)
REMOVE records-27 463 MB (dry run)
REMOVE records-28 463 MB (dry run)
REMOVE records-28b 463 MB (dry run)
REMOVE records-29 463 MB (dry run)
REMOVE records-29b 463 MB (dry run)
KEEP records-batch3 not-on-origin
KEEP records-batch7 pinned
REMOVE records-batch8 462 MB (dry run)
REMOVE records-combined 499 MB (dry run)
REMOVE records-gatespeed 499 MB (dry run)
REMOVE records-l7 490 MB (dry run)
REMOVE records-modelreview 488 MB (dry run)
REMOVE rf-build 493 MB (dry run)
REMOVE rf-tests 493 MB (dry run)
REMOVE roadmap 427 MB (dry run)
KEEP runner-savedir foreign
KEEP s132-scout dirty
KEEP s246-proof dirty
REMOVE sc-build 493 MB (dry run)
KEEP sc-fl2 dirty
KEEP sc-qa2 dirty
REMOVE sc-tests 490 MB (dry run)
KEEP scale foreign
KEEP scout-edgescroll dirty
REMOVE scout-icons 487 MB (dry run)
REMOVE scout-k-d1 435 MB (dry run)
KEEP scout-westley-owner dirty
KEEP sd-build dirty
KEEP sd-tests open-files
REMOVE sd-tests2 459 MB (dry run)
REMOVE sd-tests3 459 MB (dry run)
REMOVE sd-tests4 459 MB (dry run)
REMOVE sdk-audit 489 MB (dry run)
REMOVE sdk-audit2 450 MB (dry run)
REMOVE sdk-drift 490 MB (dry run)
REMOVE sdk-rev 450 MB (dry run)
KEEP sdk-scripts dirty
KEEP sdk-scripts2 dirty
KEEP sdk-trial-standins dirty
REMOVE sdkbuf-build 456 MB (dry run)
REMOVE sdkbuf-tests 450 MB (dry run)
REMOVE seed-main 471 MB (dry run)
KEEP sf-records not-on-origin
KEEP showcase-fl dirty
REMOVE showcase-inv 488 MB (dry run)
KEEP showcase-qa dirty
REMOVE showcase-refs 488 MB (dry run)
REMOVE showcase-secrets 488 MB (dry run)
REMOVE simlane-audit-ab 448 MB (dry run)
KEEP simlane-audit-c dirty
REMOVE simlane-d 446 MB (dry run)
REMOVE simlane-land 448 MB (dry run)
KEEP site-captures dirty
KEEP site-refresh foreign
REMOVE sj-build 452 MB (dry run)
REMOVE sj-tests 493 MB (dry run)
KEEP sl-memory-base dirty
REMOVE speed-audit 494 MB (dry run)
REMOVE speed-build 498 MB (dry run)
REMOVE speed-tests 495 MB (dry run)
REMOVE speed1b-audit 493 MB (dry run)
REMOVE speed1b-build 498 MB (dry run)
REMOVE speed1b-tests 494 MB (dry run)
REMOVE speed2-tests 490 MB (dry run)
REMOVE sv-spec 446 MB (dry run)
REMOVE sv0-row 446 MB (dry run)
REMOVE sv4-base 456 MB (dry run)
KEEP sv4-land not-on-origin
KEEP sweep-b3 foreign
REMOVE sweep-gate 615 MB (dry run)
KEEP t1-verify foreign
KEEP tests-tick-period-modules foreign
KEEP tmp-vg-a18-testfix not-on-origin
REMOVE ud-build 495 MB (dry run)
REMOVE ugf-base 501 MB (dry run)
REMOVE ugf-build 501 MB (dry run)
REMOVE ugf-tests 490 MB (dry run)
REMOVE vc-land-chk 491 MB (dry run)
REMOVE vg-a-edgescroll-land 573 MB (dry run)
KEEP vg-a-land-10 dirty
KEEP vg-a-land-5 not-on-origin
KEEP vg-a-land-8 not-on-origin
REMOVE vg-a-plays 429 MB (dry run)
REMOVE vg-a-tests 416 MB (dry run)
REMOVE vg-a1 423 MB (dry run)
REMOVE vg-a11 424 MB (dry run)
KEEP vg-a11b not-on-origin
REMOVE vg-a12 424 MB (dry run)
REMOVE vg-a13 424 MB (dry run)
REMOVE vg-a13b 424 MB (dry run)
REMOVE vg-a14 424 MB (dry run)
REMOVE vg-a15b 424 MB (dry run)
KEEP vg-a16 not-on-origin
KEEP vg-a16-land not-on-origin
REMOVE vg-a16b-base 448 MB (dry run)
REMOVE vg-a16c-main 448 MB (dry run)
REMOVE vg-a17-land 447 MB (dry run)
KEEP vg-a17-play dirty
KEEP vg-a18cam-fix-scratch foreign
KEEP vg-a18cam-playverify-scratch not-on-origin
REMOVE vg-a18cam-pre 463 MB (dry run)
REMOVE vg-a18cam-pre-s3 467 MB (dry run)
REMOVE vg-a18cam-pre2 466 MB (dry run)
KEEP vg-a18cam-testfix2-scratch not-on-origin
REMOVE vg-a1b 423 MB (dry run)
REMOVE vg-a2 423 MB (dry run)
REMOVE vg-a3 423 MB (dry run)
REMOVE vg-a4 423 MB (dry run)
REMOVE vg-a5 423 MB (dry run)
REMOVE vg-a5b 423 MB (dry run)
REMOVE vg-a6 423 MB (dry run)
REMOVE vg-a7 423 MB (dry run)
REMOVE vg-a8 423 MB (dry run)
REMOVE vg-a9 424 MB (dry run)
REMOVE vg-b-ctrl 436 MB (dry run)
REMOVE vg-b-land-10 426 MB (dry run)
REMOVE vg-b-land-11 427 MB (dry run)
KEEP vg-b-land-7 not-on-origin
REMOVE vg-b-land-8 426 MB (dry run)
REMOVE vg-b-look-land 428 MB (dry run)
REMOVE vg-b-look-land-2 428 MB (dry run)
REMOVE vg-b-look-tests 424 MB (dry run)
REMOVE vg-b-main-chk 433 MB (dry run)
REMOVE vg-b-plays 425 MB (dry run)
REMOVE vg-b-plays-2 427 MB (dry run)
REMOVE vg-b-tests-fix-5 424 MB (dry run)
KEEP vg-b-tests-fix-6 dirty
REMOVE vg-b0 416 MB (dry run)
REMOVE vg-b0-main 418 MB (dry run)
REMOVE vg-b1 418 MB (dry run)
REMOVE vg-b1-tests 418 MB (dry run)
REMOVE vg-b11 418 MB (dry run)
REMOVE vg-b12-2 424 MB (dry run)
REMOVE vg-b13 426 MB (dry run)
REMOVE vg-b13-fix 418 MB (dry run)
REMOVE vg-b14 418 MB (dry run)
REMOVE vg-b14-2 418 MB (dry run)
REMOVE vg-b15 424 MB (dry run)
REMOVE vg-b16 424 MB (dry run)
REMOVE vg-b16-main 433 MB (dry run)
REMOVE vg-b17 424 MB (dry run)
REMOVE vg-b18 424 MB (dry run)
REMOVE vg-b19 424 MB (dry run)
KEEP vg-b19-land dirty
REMOVE vg-b2 418 MB (dry run)
KEEP vg-b20 dirty
REMOVE vg-b20-2 426 MB (dry run)
REMOVE vg-b20-base 427 MB (dry run)
KEEP vg-b20-scratch not-on-origin
REMOVE vg-b22-land 556 MB (dry run)
KEEP vg-b22-landbase dirty
REMOVE vg-b23-base 447 MB (dry run)
KEEP vg-b23-land dirty
REMOVE vg-b23-px-main 438 MB (dry run)
REMOVE vg-b23-px-vk 438 MB (dry run)
REMOVE vg-b23-rulings 447 MB (dry run)
REMOVE vg-b23-shot 447 MB (dry run)
REMOVE vg-b24-pg 457 MB (dry run)
REMOVE vg-b24-pre 463 MB (dry run)
REMOVE vg-b24-pre-b 463 MB (dry run)
REMOVE vg-b24-pre-c 466 MB (dry run)
REMOVE vg-b24-pre-d 466 MB (dry run)
REMOVE vg-b24b-pre 467 MB (dry run)
KEEP vg-b24b-pre-2 not-on-origin
KEEP vg-b25-gate not-on-origin
REMOVE vg-b25-gpu-tests-b 501 MB (dry run)
KEEP vg-b25-land not-on-origin
KEEP vg-b26-land not-on-origin
REMOVE vg-b26-land2 509 MB (dry run)
KEEP vg-b26-pre dirty
REMOVE vg-b26r-base 501 MB (dry run)
KEEP vg-b26r-pre dirty
REMOVE vg-b3a 418 MB (dry run)
REMOVE vg-b3a-tests 418 MB (dry run)
KEEP vg-b3b not-on-origin
REMOVE vg-b3b-2 418 MB (dry run)
REMOVE vg-b3b-fix 418 MB (dry run)
REMOVE vg-b3b-fix-2 418 MB (dry run)
REMOVE vg-b3b-fix-3 418 MB (dry run)
REMOVE vg-b4 418 MB (dry run)
REMOVE vg-b5 417 MB (dry run)
REMOVE vg-b5-2 418 MB (dry run)
REMOVE vg-b5-3 418 MB (dry run)
REMOVE vg-b6 418 MB (dry run)
REMOVE vg-b7-tests 417 MB (dry run)
REMOVE vg-b9 418 MB (dry run)
REMOVE vg-b9-base 426 MB (dry run)
REMOVE vg-c-plays-3 439 MB (dry run)
REMOVE vg-c-tests 416 MB (dry run)
REMOVE vg-c10b 425 MB (dry run)
REMOVE vg-c10c 425 MB (dry run)
REMOVE vg-c10d 425 MB (dry run)
REMOVE vg-c10e-2 426 MB (dry run)
REMOVE vg-c6 425 MB (dry run)
REMOVE vg-c6-2 426 MB (dry run)
REMOVE vg-c7-2 426 MB (dry run)
REMOVE vg-c8 425 MB (dry run)
REMOVE vg-ca-land-2 426 MB (dry run)
KEEP vg-cb-land-2 not-on-origin
REMOVE vg-d-goldens 439 MB (dry run)
REMOVE vg-d-goldens-2-base 439 MB (dry run)
REMOVE vg-d-goldens-base 427 MB (dry run)
REMOVE vg-d-land 427 MB (dry run)
REMOVE vg-d-land-3 547 MB (dry run)
REMOVE vg-d2 424 MB (dry run)
REMOVE vg-d2-2 424 MB (dry run)
REMOVE vg-d3-2 424 MB (dry run)
REMOVE vg-d4-2 424 MB (dry run)
REMOVE vg-d5-2 424 MB (dry run)
REMOVE vg-d5-3 424 MB (dry run)
REMOVE vg-d7 424 MB (dry run)
REMOVE vg-d7-tests 424 MB (dry run)
KEEP vg-dview-b3-base dirty
KEEP vg-dview-b3-scratch foreign
REMOVE vg-dview-base 458 MB (dry run)
KEEP vg-dview-land not-on-origin
REMOVE vg-dview-pre 466 MB (dry run)
REMOVE vg-dview-pre2 467 MB (dry run)
REMOVE vg-dview-pre4 467 MB (dry run)
REMOVE vg-dview-pre5 452 MB (dry run)
REMOVE vg-dview-pre6 467 MB (dry run)
REMOVE vg-dview-pre7 467 MB (dry run)
REMOVE vg-dview-pre8 467 MB (dry run)
REMOVE vg-dview-pre9 467 MB (dry run)
KEEP vg-dview-scratch2 not-on-origin
KEEP vg-dview-tests-run dirty
KEEP vg-e1-shot-land-tmp not-worktree
REMOVE vg-e1a2-base 431 MB (dry run)
REMOVE vg-e1a3-base 547 MB (dry run)
KEEP vg-e1a3-land not-on-origin
KEEP vg-e1a3-land-2 not-on-origin
KEEP vg-e1c-3 not-on-origin
KEEP vg-e1c-land-tmp not-worktree
KEEP vg-e1d-2 not-on-origin
KEEP vg-e1e not-on-origin
REMOVE vg-e1g-3-base 441 MB (dry run)
REMOVE vg-e1g-tests 426 MB (dry run)
REMOVE vg-e1h-3-base 441 MB (dry run)
REMOVE vg-e1i 426 MB (dry run)
REMOVE vg-e1n-fix 502 MB (dry run)
KEEP vg-e1q-rulings-verify not-on-origin
REMOVE vg-e1r-land 623 MB (dry run)
KEEP vg-e1screens-land not-on-origin
REMOVE vg-e1screens-pre 516 MB (dry run)
KEEP vg-e1w dirty
KEEP vg-e1w-b dirty
KEEP vg-e7 not-on-origin
KEEP vg-e7-pre not-on-origin
KEEP vg-e7-pre-fg not-on-origin
KEEP vg-e7-pre-r2 not-on-origin
KEEP vg-e7-proto dirty
REMOVE vg-e7r-3-base 505 MB (dry run)
KEEP vg-e7r-exp2 dirty
REMOVE vg-e7r-gbase2 616 MB (dry run)
KEEP vg-e7r-goldens-stale not-on-origin
REMOVE vg-e7r-land 504 MB (dry run)
REMOVE vg-e7r-pre 512 MB (dry run)
KEEP vg-e7r7-build not-on-origin
KEEP vg-e7r7-stub not-on-origin
REMOVE vg-f-land 426 MB (dry run)
REMOVE vg-f-land-2 427 MB (dry run)
KEEP vg-f-s140-click-land dirty
REMOVE vg-f-scripts 419 MB (dry run)
REMOVE vg-f-scripts-fix 419 MB (dry run)
REMOVE vg-f-tests 416 MB (dry run)
REMOVE vg-f-tests-fix 424 MB (dry run)
REMOVE vg-f5 425 MB (dry run)
KEEP vg-f5-land-4 dirty
REMOVE vg-f5b 426 MB (dry run)
REMOVE vg-f6a 425 MB (dry run)
REMOVE vg-f6b 425 MB (dry run)
KEEP vg-flobby-land-r2 not-on-origin
REMOVE vg-flobby-pre3 510 MB (dry run)
REMOVE vg-g1-base 420 MB (dry run)
REMOVE vg-g2 416 MB (dry run)
REMOVE vg-g3 416 MB (dry run)
REMOVE vg-gate-mainpipe 427 MB (dry run)
REMOVE vg-guard-land 416 MB (dry run)
REMOVE vg-h-renderer 425 MB (dry run)
REMOVE vg-harness-c1b 495 MB (dry run)
KEEP vg-harness-c1b-red dirty
REMOVE vg-harness-c235-land 620 MB (dry run)
REMOVE vg-harness-c4-land 622 MB (dry run)
REMOVE vg-harness-provscope 494 MB (dry run)
REMOVE vg-harness-provscope-land 620 MB (dry run)
REMOVE vg-harness-provscope-tests 494 MB (dry run)
REMOVE vg-k-tests 416 MB (dry run)
REMOVE vg-k-tests-2 417 MB (dry run)
REMOVE vg-k0 416 MB (dry run)
KEEP vg-k0-land dirty
REMOVE vg-ka-bridge-base 419 MB (dry run)
REMOVE vg-ka-check-fog 416 MB (dry run)
REMOVE vg-ka-check-terrain 430 MB (dry run)
REMOVE vg-ka-check-unit 430 MB (dry run)
REMOVE vg-ka-land 420 MB (dry run)
REMOVE vg-ka-main-chk 419 MB (dry run)
REMOVE vg-ka-mapgen 416 MB (dry run)
REMOVE vg-ka-mapgen-base 430 MB (dry run)
REMOVE vg-ka-mission 416 MB (dry run)
REMOVE vg-ka-pipe 416 MB (dry run)
REMOVE vg-ka-pipe-2 420 MB (dry run)
REMOVE vg-ka-support-2 417 MB (dry run)
REMOVE vg-ka-terrain 416 MB (dry run)
REMOVE vg-ka-unit 416 MB (dry run)
REMOVE vg-ka2-land 420 MB (dry run)
REMOVE vg-ka2-land-2 426 MB (dry run)
REMOVE vg-kd 427 MB (dry run)
REMOVE vg-kd-land 427 MB (dry run)
REMOVE vg-kd-tests 424 MB (dry run)
REMOVE vg-kd1-main 438 MB (dry run)
REMOVE vg-kd1-pre 457 MB (dry run)
REMOVE vg-kd2 424 MB (dry run)
REMOVE vg-ke5-goldens 433 MB (dry run)
REMOVE vg-ke5-land 557 MB (dry run)
REMOVE vg-ke5-rulings 430 MB (dry run)
REMOVE vg-kf 420 MB (dry run)
REMOVE vg-kf-land 420 MB (dry run)
REMOVE vg-kh-bridge 424 MB (dry run)
REMOVE vg-kh-land 427 MB (dry run)
REMOVE vg-kh-pipe 427 MB (dry run)
REMOVE vg-kh-pipe-2 427 MB (dry run)
REMOVE vg-kh-tests 426 MB (dry run)
REMOVE vg-kh-wire 425 MB (dry run)
KEEP vg-nettick-diag dirty
REMOVE vg-nettick-pre 456 MB (dry run)
REMOVE vg-nettick-pre2 456 MB (dry run)
REMOVE vg-p1-land2 572 MB (dry run)
REMOVE vg-p1-land3 617 MB (dry run)
REMOVE vg-parked-3 416 MB (dry run)
REMOVE vg-perf-minof-w2 468 MB (dry run)
REMOVE vg-pipe-split 426 MB (dry run)
REMOVE vg-pipe-split-base 434 MB (dry run)
REMOVE vg-prodslot-base 618 MB (dry run)
REMOVE vg-prodslot-bl 508 MB (dry run)
REMOVE vg-prodslot-gbase 497 MB (dry run)
REMOVE vg-prodslot-land 622 MB (dry run)
KEEP vg-prodslot-mv dirty
REMOVE vg-rec-sprint6 574 MB (dry run)
REMOVE vg-rec-sprint7 573 MB (dry run)
REMOVE vg-rec-sprint8 574 MB (dry run)
REMOVE vg-records-combo 619 MB (dry run)
REMOVE vg-script-p2r-land 620 MB (dry run)
REMOVE vg-split-land-2 426 MB (dry run)
REMOVE vg-t-r087-land 618 MB (dry run)
REMOVE vg-t-reach-land 618 MB (dry run)
REMOVE vg-u-pipe-fix-land 619 MB (dry run)
REMOVE vg-u-pipe-tests-land 619 MB (dry run)
REMOVE vg-udir-land 574 MB (dry run)
KEEP vg-udir-land2 not-on-origin
REMOVE vg-udir-land3 478 MB (dry run)
REMOVE vg-udir-land4 615 MB (dry run)
REMOVE vg-udir-pre 560 MB (dry run)
REMOVE vg-udir-pre-b 560 MB (dry run)
REMOVE vg-venvlink 493 MB (dry run)
REMOVE vg-venvlink-tests 493 MB (dry run)
REMOVE vg-w1-leftovers 419 MB (dry run)
REMOVE vg-w1-pre 447 MB (dry run)
REMOVE vg-w2b 424 MB (dry run)
REMOVE vg-w2r-pre 458 MB (dry run)
KEEP vg-w2s-fix2 foreign
KEEP vg-w2s-fix2-old foreign
REMOVE vg-w2s-goldens-base 448 MB (dry run)
REMOVE vg-w2s-goldens2-orig 449 MB (dry run)
REMOVE vg-w2s-pre 468 MB (dry run)
REMOVE vg-w2s-pre3 468 MB (dry run)
REMOVE vg-w2s-pre5 469 MB (dry run)
KEEP vg-w2s-tests3-build dirty
REMOVE vg-w4 423 MB (dry run)
REMOVE vgd1-gate 437 MB (dry run)
REMOVE vgd1-main 437 MB (dry run)
REMOVE vl-build 493 MB (dry run)
REMOVE vl-tests 490 MB (dry run)
KEEP wt-cap-spec active
REMOVE wtcap-build 456 MB (dry run)
REMOVE wtcap-partb 450 MB (dry run)
KEEP wtcap-partc young
REMOVE wtcap-records 450 MB (dry run)
REMOVE wtcap-tests 450 MB (dry run)
REMOVE wtcap2-build 452 MB (dry run)
REMOVE wtcap2-tests 450 MB (dry run)
```

## Status totals

`worktrees 818 slots 5/12 wt 365.7/120 free 75.2/60`
