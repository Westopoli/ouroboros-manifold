# Worktree reap dry run, 2026-10-24

Westley: this is what the cleanup would do, nothing has been removed. I flagged every old tree (2 pinned, 2 active, 529 finished) and ran `wt.py reap --dry-run`.

- Would remove: 218 trees, 100.8 GB.
- Keeps, by reason: dirty 429, foreign 73, not-on-origin 70, not-worktree 8, pending 4, pinned 2, active 2, open-files 2, young 2 (592 total). Dirty, not-on-origin and open-files trees stay because they may hold work git does not have.
- Slots and disk after the flags (from status): `worktrees 809 slots 3/12 wt 361.5/120 free 80.0/60` (slots in use / cap, wt GB / cap, free GB / floor).
- Not-worktree directories, ruled by hand before any removal: .pytest_cache 1 MB; PC-speed-v 91 MB; _stale 663 MB; baseline_cache 13 MB; baseline_cache_mainpipe 1 MB; logs 1 MB; vg-e1-shot-land-tmp 305 MB; vg-e1c-land-tmp 365 MB. Foreign trees (73): 22564 MB in total (22.0 GB), ruled by hand before any removal.
- Young list (would be removed, age under 2 days, spare any a live chat still uses; age is from the tree's .git file, so it counts from creation): 150 trees: ans-04 (0.7d), arch-e1c-spec (0.7d), batch-rev (0.7d), batch-rev3 (0.7d), chk-main-ref (0.7d), chk-main-ref2 (0.7d), chk-vg-a18cam-base (0.7d), costreport-build (1.7d), costreport-tests (1.7d), ctxguard-tests (0.7d), diag-walk-ke2 (0.7d), dl-build (1.7d), fab-audit (0.7d), fab-audit2 (0.7d), fab-rev (0.7d), fst-build (1.7d), fst-tests (1.7d), ft-tests (1.7d), goc-tests (1.7d), gp-build (1.7d), greentests (0.7d), greentests-lab (0.7d), guard-rule (0.7d), inv-simfacing (0.7d), io-tests (1.7d), kr-build (1.7d), kr-tests (1.7d), lab-placed (0.7d), lab-run1 (0.7d), labrev2-captrace3 (0.7d), labrev2-drift (0.7d), labrev2-drift2 (0.7d), labrev2-e0-tests (0.7d), labrev2-e1-tests (0.7d), labrev2-e2-tests (0.7d), labrev2-e3-tests (0.7d), labrev2-e4-tests (0.7d), labrev2-fix-audit (0.7d), labrev2-fix-audit2 (0.7d), labrev2-fix5-audit (0.7d), labrev2-flipeval (0.7d), labrev2-flipeval2 (0.7d), labrev2-l1-tests (0.7d), labrev2-l2-tests (0.7d), labrev2-l3-tests (0.7d), labrev2-l4-tests (0.7d), labrev2-l6-tests (0.7d), labrev2-l7-tests (0.7d), labrev2-l8m-audit (0.7d), labrev2-l8m2 (0.7d), labrev2-l8m2-tests (0.7d), labrev2-landA (0.7d), labrev2-pins (0.7d), labrev2-vc-ruler (0.7d), labrev2-vc-ruler-old (0.7d), labrev2-vc-tests (0.7d), labrev3-a-ruler (0.7d), labrev3-a-tests (0.7d), labrev3-b (0.7d), labrev3-b-ruler (0.7d), labrev3-b-sbuild (0.7d), labrev3-b-smoke (0.7d), labrev3-b-tests (0.7d), labrev3-c (0.7d), labrev3-c-ruler (0.7d), labrev3-c-tests (0.7d), land-dl (1.7d), landlab-prep (0.7d), lp-build (1.7d), lp-tests (1.7d), lt-build (1.7d), lt-tests (1.7d), merge-ab (0.7d), pcyc-build (1.7d), pcyc-tests (1.7d), rec-audits (1.7d), rec-batch13 (0.7d), rec-credit9pm (1.7d), rec-drift (1.7d), rec-recordslock (1.7d), rec-slots1 (1.7d), rec-slots3 (1.7d), rec-td-l8m2 (0.7d), records-22a (1.7d), records-22b (1.7d), records-23a (1.7d), records-23b (1.7d), records-23c (1.7d), records-24 (1.7d), records-25 (1.7d), records-26 (1.7d), records-27 (1.7d), records-28 (1.7d), records-28b (1.7d), records-29 (1.7d), records-29b (1.7d), records-batch8 (1.7d), rf-build (1.7d), rf-tests (1.7d), roadmap (0.7d), sc-build (1.7d), sc-tests (1.7d), scout-icons (0.7d), scout-k-d1 (0.7d), sdk-audit (0.7d), sdk-audit2 (0.7d), sdk-drift (0.7d), sdk-rev (0.7d), sdkbuf-build (1.7d), sdkbuf-tests (1.7d), seed-main (0.7d), showcase-refs (0.7d), showcase-secrets (0.7d), simlane-d (0.7d), simlane-land (0.7d), sj-build (1.7d), sj-tests (1.7d), sv-spec (0.7d), sv0-row (0.7d), sv4-base (0.7d), ud-build (1.7d), ugf-tests (1.7d), vg-b20-base (0.7d), vg-b24-pg (0.7d), vg-b5 (0.7d), vg-b7-tests (0.7d), vg-d2 (0.7d), vg-d7 (0.7d), vg-dview-pre5 (0.7d), vg-e1g-tests (0.7d), vg-e1i (0.7d), vg-e7r-3-base (0.7d), vg-g1-base (0.7d), vg-harness-c1b (0.7d), vg-ka-bridge-base (0.7d), vg-ka-check-fog (0.7d), vg-ka-mapgen-base (0.7d), vg-kd1-main (0.7d), vg-ke5-rulings (0.7d), vg-parked-3 (0.7d), vg-prodslot-bl (0.7d), vg-w2s-goldens-base (0.7d), vg-w2s-goldens2-orig (0.7d), vgd1-gate (0.7d), vgd1-main (0.7d), vl-build (1.7d), vl-tests (1.7d), wtcap-build (0.7d), wtcap-records (0.7d), wtcap-tests (0.7d).

Bulk removal runs only on Westley's word (wt.py reap without --dry-run, by the clerk).

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
KEEP ans-01 dirty
KEEP ans-03 dirty
REMOVE ans-04 368 MB (dry run)
KEEP ans-06 dirty
KEEP ans-09 dirty
REMOVE arch-audit2 481 MB (dry run)
REMOVE arch-batch2 482 MB (dry run)
REMOVE arch-batchslim 482 MB (dry run)
REMOVE arch-credits 484 MB (dry run)
REMOVE arch-credits-run 481 MB (dry run)
REMOVE arch-e1c-spec 427 MB (dry run)
REMOVE arch-epicdrift 481 MB (dry run)
KEEP arch-fu-obey dirty
KEEP arch-fu-obey-6b dirty
KEEP arch-fu-obey-p1 dirty
REMOVE arch-fu-obey-rec 482 MB (dry run)
KEEP arch-fu-reshot dirty
REMOVE arch-fu-s103 484 MB (dry run)
KEEP arch-fu-simviewer dirty
REMOVE arch-fu-transition 484 MB (dry run)
KEEP arch-fu-transition-run dirty
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
KEEP b-land not-on-origin
KEEP b25-lay-branch dirty
KEEP b25-lay-main dirty
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
KEEP c25patch-land dirty
KEEP c4-land2 dirty
KEEP cand-missionover2 foreign
KEEP chain2-scripts-land dirty
KEEP chk-a17-run dirty
KEEP chk-a17-run-r3 not-on-origin
KEEP chk-a17-run2 not-on-origin
KEEP chk-base-b26r dirty
KEEP chk-base-e1h3 dirty
KEEP chk-build-udir dirty
KEEP chk-clean-udir dirty
KEEP chk-cs004-run dirty
KEEP chk-e1m-build dirty
KEEP chk-e1n-build dirty
KEEP chk-e1n-tests dirty
KEEP chk-e1q-join not-on-origin
KEEP chk-e1r-base dirty
KEEP chk-e1r-build dirty
KEEP chk-e1r-build-r2 dirty
KEEP chk-e1r-main dirty
KEEP chk-e1r-main-r2 dirty
KEEP chk-e1w-build dirty
KEEP chk-e7-b20 dirty
KEEP chk-e7-base dirty
KEEP chk-e7-base-c dirty
KEEP chk-e7-base-r20 dirty
KEEP chk-e7-base-r21 dirty
KEEP chk-e7-base-r22 dirty
KEEP chk-e7-base-r23 dirty
KEEP chk-e7-base-r24 dirty
KEEP chk-e7-base2 dirty
KEEP chk-e7-base3 dirty
KEEP chk-e7-basew dirty
KEEP chk-e7-build dirty
KEEP chk-e7-build-c dirty
KEEP chk-e7-build-main dirty
KEEP chk-e7-build-ref dirty
KEEP chk-e7-goldens dirty
KEEP chk-e7-goldens-2 dirty
KEEP chk-e7-goldens-b dirty
KEEP chk-e7-goldens-c dirty
KEEP chk-e7-goldens-m dirty
KEEP chk-e7-goldens-main dirty
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
KEEP chk-e7-main dirty
KEEP chk-e7-ref dirty
KEEP chk-e7-rev dirty
KEEP chk-e7-tests dirty
KEEP chk-e7-tests-b dirty
KEEP chk-e7-tests-m dirty
KEEP chk-e7-tests-r2 dirty
KEEP chk-e7g-main dirty
KEEP chk-fskel-join not-on-origin
KEEP chk-ke5-gate dirty
KEEP chk-main dirty
REMOVE chk-main-ref 431 MB (dry run)
REMOVE chk-main-ref2 431 MB (dry run)
KEEP chk-main-udir dirty
KEEP chk-protodens3 dirty
KEEP chk-push-vg-b24b dirty
KEEP chk-push-vg-b24b-tests dirty
KEEP chk-push-vg-b26 dirty
KEEP chk-push-vg-b26-tests dirty
KEEP chk-push-vg-b26r dirty
KEEP chk-push-vg-b26r-tests dirty
KEEP chk-push-vg-e1c-tests-fix dirty
KEEP chk-push-vg-e1h-2 dirty
KEEP chk-push-vg-e1h-3 dirty
KEEP chk-push-vg-e1p-a dirty
KEEP chk-push-vg-ka-pipe-2 dirty
KEEP chk-push-vg-ka-support-2 dirty
KEEP chk-push-vg-kd1 dirty
KEEP chk-push-vg-kd1-tests dirty
KEEP chk-push-vg-ke4 dirty
KEEP chk-push-vg-ke5-base dirty
KEEP chk-vg-a16 dirty
KEEP chk-vg-a16-main dirty
KEEP chk-vg-a18cam not-on-origin
REMOVE chk-vg-a18cam-base 447 MB (dry run)
KEEP chk-vg-a18cam-main dirty
KEEP chk-vg-a18cam-r2 dirty
KEEP chk-vg-a18cam-r2-base dirty
KEEP chk-vg-a18cam-r2-comb dirty
KEEP chk-vg-a18cam-r2-mb dirty
KEEP chk-vg-b22 dirty
KEEP chk-vg-b22-comment dirty
KEEP chk-vg-b22-main dirty
KEEP chk-vg-b25 dirty
KEEP chk-vg-b25-main dirty
KEEP chk-vg-dview dirty
KEEP chk-vg-dview-c3 dirty
KEEP chk-vg-dview-c3-main dirty
KEEP chk-vg-dview-c3-pg dirty
KEEP chk-vg-dview-c3-scratch dirty
KEEP chk-vg-dview-main dirty
KEEP chk-vg-dview-pg dirty
KEEP chk-vg-dview-rev dirty
KEEP chk-vg-flobby dirty
KEEP chk-vg-flobby-main dirty
KEEP chk-vg-flobby-pg dirty
KEEP chk-w2-base dirty
KEEP chk-w2-build dirty
KEEP chk-w2-contract dirty
KEEP chk-w2-tests not-on-origin
KEEP clerk-b2b3 not-on-origin
KEEP clerk-clock not-on-origin
KEEP clerk-hdr5 not-on-origin
KEEP core-sim-session foreign
REMOVE costreport-build 449 MB (dry run)
REMOVE costreport-tests 449 MB (dry run)
KEEP ctxguard-build active
REMOVE ctxguard-tests 450 MB (dry run)
REMOVE diag-walk-ke2 428 MB (dry run)
KEEP diag-walk-main dirty
REMOVE dl-build 492 MB (dry run)
KEEP docfix foreign
KEEP e06-verify foreign
KEEP fa-build dirty
KEEP fa-tests dirty
REMOVE fab-audit 449 MB (dry run)
REMOVE fab-audit2 450 MB (dry run)
REMOVE fab-rev 450 MB (dry run)
KEEP flake-cold dirty
KEEP flake-rootcause dirty
KEEP flockfix-land dirty
REMOVE fst-build 456 MB (dry run)
REMOVE fst-tests 450 MB (dry run)
REMOVE ft-tests 497 MB (dry run)
REMOVE g3pc-audit 491 MB (dry run)
REMOVE g3pc-build 491 MB (dry run)
KEEP g3pc-land dirty
KEEP g3pc-tests open-files
KEEP galaxy-before-shrink dirty
KEEP galaxy-look dirty
KEEP gate-kd dirty
KEEP gate-kd-main dirty
KEEP gate-w4 dirty
KEEP gatebase-build foreign
KEEP gatebase-land not-on-origin
KEEP gatebase-land2 dirty
KEEP gatebase-rec dirty
KEEP gatebase-scripts foreign
KEEP gatebase-scripts-land dirty
KEEP goc-build dirty
REMOVE goc-tests 490 MB (dry run)
REMOVE gp-build 492 MB (dry run)
KEEP gp-tests dirty
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
KEEP lab-land2 dirty
REMOVE lab-placed 417 MB (dry run)
KEEP lab-placed-land dirty
KEEP lab-rev2-records not-on-origin
REMOVE lab-run1 457 MB (dry run)
KEEP labdiag dirty
KEEP labrev2-base-audit dirty
KEEP labrev2-captrace2 dirty
REMOVE labrev2-captrace3 493 MB (dry run)
REMOVE labrev2-drift 490 MB (dry run)
REMOVE labrev2-drift2 491 MB (dry run)
KEEP labrev2-e0 dirty
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
KEEP labrev2-landE3 dirty
KEEP labrev2-landE3-base dirty
KEEP labrev2-landLab dirty
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
KEEP lakefill-build dirty
KEEP lakefill-tests dirty
KEEP land-3 not-on-origin
KEEP land-3b dirty
KEEP land-4 dirty
KEEP land-5 dirty
KEEP land-b25 pending
KEEP land-cl pending
KEEP land-ctxguard young
REMOVE land-dl 492 MB (dry run)
KEEP land-lm pending
KEEP land-sd pending
KEEP land-ugfnsm dirty
KEEP land-wtcap dirty
REMOVE landlab-prep 490 MB (dry run)
KEEP lf-count-1 dirty
KEEP lf-lane3-build foreign
KEEP lf-lane3-test foreign
KEEP lm-build dirty
KEEP lm-tests dirty
KEEP lm-tests3 dirty
KEEP logs not-worktree
KEEP look5 foreign
KEEP lop-build dirty
KEEP lop-mainref dirty
KEEP lop-tests dirty
REMOVE lp-build 493 MB (dry run)
REMOVE lp-tests 490 MB (dry run)
KEEP ls-build dirty
KEEP ls-tests dirty
KEEP lst-build foreign
REMOVE lt-build 449 MB (dry run)
REMOVE lt-tests 449 MB (dry run)
REMOVE measure-speed3 493 MB (dry run)
REMOVE merge-ab 498 MB (dry run)
KEEP mvp-play dirty
KEEP nettick-edge dirty
KEEP nsm-build dirty
KEEP nsm-tests dirty
KEEP p2r-rec dirty
KEEP p2r-rec3 not-on-origin
REMOVE p2r-tests2 494 MB (dry run)
REMOVE pcyc-build 463 MB (dry run)
REMOVE pcyc-tests 463 MB (dry run)
KEEP pf-godot dirty
KEEP pf-lab not-on-origin
KEEP pieces-flip dirty
REMOVE pin-ruler 492 MB (dry run)
KEEP play-main dirty
KEEP pre-escr dirty
KEEP prodslot-land2 dirty
KEEP prodslot-rec dirty
KEEP proto-density-pre dirty
KEEP proto-density-pre-b dirty
KEEP proto-galaxy-shot dirty
KEEP proto-highground not-on-origin
KEEP proto-land-iter dirty
KEEP proto-walkers dirty
KEEP protodens3-pre dirty
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
KEEP sd-tests2 dirty
KEEP sd-tests3 dirty
KEEP sd-tests4 dirty
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
KEEP simlane-audit-ab dirty
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
KEEP sweep-gate dirty
KEEP t1-verify foreign
KEEP tests-tick-period-modules foreign
KEEP tmp-vg-a18-testfix not-on-origin
REMOVE ud-build 495 MB (dry run)
KEEP ugf-base dirty
KEEP ugf-build dirty
REMOVE ugf-tests 490 MB (dry run)
REMOVE vc-land-chk 491 MB (dry run)
KEEP vg-a-edgescroll-land dirty
KEEP vg-a-land-10 dirty
KEEP vg-a-land-5 not-on-origin
KEEP vg-a-land-8 not-on-origin
KEEP vg-a-plays dirty
KEEP vg-a-tests dirty
KEEP vg-a1 dirty
KEEP vg-a11 dirty
KEEP vg-a11b not-on-origin
KEEP vg-a12 dirty
KEEP vg-a13 dirty
KEEP vg-a13b dirty
KEEP vg-a14 dirty
KEEP vg-a15b dirty
KEEP vg-a16 not-on-origin
KEEP vg-a16-land not-on-origin
KEEP vg-a16b-base dirty
KEEP vg-a16c-main dirty
KEEP vg-a17-land dirty
KEEP vg-a17-play dirty
KEEP vg-a18cam-fix-scratch foreign
KEEP vg-a18cam-playverify-scratch not-on-origin
KEEP vg-a18cam-pre dirty
KEEP vg-a18cam-pre-s3 dirty
KEEP vg-a18cam-pre2 dirty
KEEP vg-a18cam-testfix2-scratch not-on-origin
KEEP vg-a1b dirty
KEEP vg-a2 dirty
KEEP vg-a3 dirty
KEEP vg-a4 dirty
KEEP vg-a5 dirty
KEEP vg-a5b dirty
KEEP vg-a6 dirty
KEEP vg-a7 dirty
KEEP vg-a8 dirty
KEEP vg-a9 dirty
KEEP vg-b-ctrl dirty
KEEP vg-b-land-10 dirty
KEEP vg-b-land-11 dirty
KEEP vg-b-land-7 not-on-origin
KEEP vg-b-land-8 dirty
KEEP vg-b-look-land dirty
KEEP vg-b-look-land-2 dirty
KEEP vg-b-look-tests dirty
KEEP vg-b-main-chk dirty
KEEP vg-b-plays dirty
KEEP vg-b-plays-2 dirty
KEEP vg-b-tests-fix-5 dirty
KEEP vg-b-tests-fix-6 dirty
KEEP vg-b0 dirty
KEEP vg-b0-main dirty
KEEP vg-b1 dirty
KEEP vg-b1-tests dirty
KEEP vg-b11 dirty
KEEP vg-b12-2 dirty
KEEP vg-b13 dirty
KEEP vg-b13-fix dirty
KEEP vg-b14 dirty
KEEP vg-b14-2 dirty
KEEP vg-b15 dirty
KEEP vg-b16 dirty
KEEP vg-b16-main dirty
KEEP vg-b17 dirty
KEEP vg-b18 dirty
KEEP vg-b19 dirty
KEEP vg-b19-land dirty
KEEP vg-b2 dirty
KEEP vg-b20 dirty
KEEP vg-b20-2 dirty
REMOVE vg-b20-base 427 MB (dry run)
KEEP vg-b20-scratch not-on-origin
KEEP vg-b22-land dirty
KEEP vg-b22-landbase dirty
KEEP vg-b23-base dirty
KEEP vg-b23-land dirty
KEEP vg-b23-px-main dirty
KEEP vg-b23-px-vk dirty
KEEP vg-b23-rulings dirty
KEEP vg-b23-shot dirty
REMOVE vg-b24-pg 457 MB (dry run)
KEEP vg-b24-pre dirty
KEEP vg-b24-pre-b dirty
KEEP vg-b24-pre-c dirty
KEEP vg-b24-pre-d dirty
KEEP vg-b24b-pre dirty
KEEP vg-b24b-pre-2 not-on-origin
KEEP vg-b25-gate not-on-origin
KEEP vg-b25-gpu-tests-b dirty
KEEP vg-b25-land not-on-origin
KEEP vg-b26-land not-on-origin
KEEP vg-b26-land2 dirty
KEEP vg-b26-pre dirty
KEEP vg-b26r-base dirty
KEEP vg-b26r-pre dirty
KEEP vg-b3a dirty
KEEP vg-b3a-tests dirty
KEEP vg-b3b not-on-origin
KEEP vg-b3b-2 dirty
KEEP vg-b3b-fix dirty
KEEP vg-b3b-fix-2 dirty
KEEP vg-b3b-fix-3 dirty
KEEP vg-b4 dirty
REMOVE vg-b5 417 MB (dry run)
KEEP vg-b5-2 dirty
KEEP vg-b5-3 dirty
KEEP vg-b6 dirty
REMOVE vg-b7-tests 417 MB (dry run)
KEEP vg-b9 dirty
KEEP vg-b9-base dirty
KEEP vg-c-plays-3 dirty
KEEP vg-c-tests dirty
KEEP vg-c10b dirty
KEEP vg-c10c dirty
KEEP vg-c10d dirty
KEEP vg-c10e-2 dirty
KEEP vg-c6 dirty
KEEP vg-c6-2 dirty
KEEP vg-c7-2 dirty
KEEP vg-c8 dirty
KEEP vg-ca-land-2 dirty
KEEP vg-cb-land-2 not-on-origin
KEEP vg-d-goldens dirty
KEEP vg-d-goldens-2-base dirty
KEEP vg-d-goldens-base dirty
KEEP vg-d-land dirty
KEEP vg-d-land-3 dirty
REMOVE vg-d2 424 MB (dry run)
KEEP vg-d2-2 dirty
KEEP vg-d3-2 dirty
KEEP vg-d4-2 dirty
KEEP vg-d5-2 dirty
KEEP vg-d5-3 dirty
REMOVE vg-d7 424 MB (dry run)
KEEP vg-d7-tests dirty
KEEP vg-dview-b3-base dirty
KEEP vg-dview-b3-scratch foreign
KEEP vg-dview-base dirty
KEEP vg-dview-land not-on-origin
KEEP vg-dview-pre dirty
KEEP vg-dview-pre2 dirty
KEEP vg-dview-pre4 dirty
REMOVE vg-dview-pre5 452 MB (dry run)
KEEP vg-dview-pre6 dirty
KEEP vg-dview-pre7 dirty
KEEP vg-dview-pre8 dirty
KEEP vg-dview-pre9 dirty
KEEP vg-dview-scratch2 not-on-origin
KEEP vg-dview-tests-run dirty
KEEP vg-e1-shot-land-tmp not-worktree
KEEP vg-e1a2-base dirty
KEEP vg-e1a3-base dirty
KEEP vg-e1a3-land not-on-origin
KEEP vg-e1a3-land-2 not-on-origin
KEEP vg-e1c-3 not-on-origin
KEEP vg-e1c-land-tmp not-worktree
KEEP vg-e1d-2 not-on-origin
KEEP vg-e1e not-on-origin
KEEP vg-e1g-3-base dirty
REMOVE vg-e1g-tests 426 MB (dry run)
KEEP vg-e1h-3-base dirty
REMOVE vg-e1i 426 MB (dry run)
KEEP vg-e1n-fix dirty
KEEP vg-e1q-rulings-verify not-on-origin
KEEP vg-e1r-land dirty
KEEP vg-e1screens-land not-on-origin
KEEP vg-e1screens-pre dirty
KEEP vg-e1w dirty
KEEP vg-e1w-b dirty
KEEP vg-e7 not-on-origin
KEEP vg-e7-pre not-on-origin
KEEP vg-e7-pre-fg not-on-origin
KEEP vg-e7-pre-r2 not-on-origin
KEEP vg-e7-proto dirty
REMOVE vg-e7r-3-base 505 MB (dry run)
KEEP vg-e7r-exp2 dirty
KEEP vg-e7r-gbase2 dirty
KEEP vg-e7r-goldens-stale not-on-origin
KEEP vg-e7r-land dirty
KEEP vg-e7r-pre dirty
KEEP vg-e7r7-build not-on-origin
KEEP vg-e7r7-stub not-on-origin
KEEP vg-f-land dirty
KEEP vg-f-land-2 dirty
KEEP vg-f-s140-click-land dirty
KEEP vg-f-scripts dirty
KEEP vg-f-scripts-fix dirty
KEEP vg-f-tests dirty
KEEP vg-f-tests-fix dirty
KEEP vg-f5 dirty
KEEP vg-f5-land-4 dirty
KEEP vg-f5b dirty
KEEP vg-f6a dirty
KEEP vg-f6b dirty
KEEP vg-flobby-land-r2 not-on-origin
KEEP vg-flobby-pre3 dirty
REMOVE vg-g1-base 420 MB (dry run)
KEEP vg-g2 dirty
KEEP vg-g3 dirty
KEEP vg-gate-mainpipe dirty
KEEP vg-guard-land dirty
KEEP vg-h-renderer dirty
REMOVE vg-harness-c1b 495 MB (dry run)
KEEP vg-harness-c1b-red dirty
KEEP vg-harness-c235-land dirty
KEEP vg-harness-c4-land dirty
REMOVE vg-harness-provscope 494 MB (dry run)
KEEP vg-harness-provscope-land dirty
REMOVE vg-harness-provscope-tests 494 MB (dry run)
KEEP vg-k-tests dirty
KEEP vg-k-tests-2 dirty
KEEP vg-k0 dirty
KEEP vg-k0-land dirty
REMOVE vg-ka-bridge-base 419 MB (dry run)
REMOVE vg-ka-check-fog 416 MB (dry run)
KEEP vg-ka-check-terrain dirty
KEEP vg-ka-check-unit dirty
KEEP vg-ka-land dirty
KEEP vg-ka-main-chk dirty
KEEP vg-ka-mapgen dirty
REMOVE vg-ka-mapgen-base 430 MB (dry run)
KEEP vg-ka-mission dirty
KEEP vg-ka-pipe dirty
KEEP vg-ka-pipe-2 dirty
KEEP vg-ka-support-2 dirty
KEEP vg-ka-terrain dirty
KEEP vg-ka-unit dirty
KEEP vg-ka2-land dirty
KEEP vg-ka2-land-2 dirty
KEEP vg-kd dirty
KEEP vg-kd-land dirty
KEEP vg-kd-tests dirty
REMOVE vg-kd1-main 438 MB (dry run)
KEEP vg-kd1-pre dirty
KEEP vg-kd2 dirty
KEEP vg-ke5-goldens dirty
KEEP vg-ke5-land dirty
REMOVE vg-ke5-rulings 430 MB (dry run)
KEEP vg-kf dirty
KEEP vg-kf-land dirty
KEEP vg-kh-bridge dirty
KEEP vg-kh-land dirty
KEEP vg-kh-pipe dirty
KEEP vg-kh-pipe-2 dirty
KEEP vg-kh-tests dirty
KEEP vg-kh-wire dirty
KEEP vg-nettick-diag dirty
KEEP vg-nettick-pre dirty
KEEP vg-nettick-pre2 dirty
KEEP vg-p1-land2 dirty
KEEP vg-p1-land3 dirty
REMOVE vg-parked-3 416 MB (dry run)
KEEP vg-perf-minof-w2 dirty
KEEP vg-pipe-split dirty
KEEP vg-pipe-split-base dirty
KEEP vg-prodslot-base dirty
REMOVE vg-prodslot-bl 508 MB (dry run)
KEEP vg-prodslot-gbase dirty
KEEP vg-prodslot-land dirty
KEEP vg-prodslot-mv dirty
KEEP vg-rec-sprint6 dirty
KEEP vg-rec-sprint7 dirty
KEEP vg-rec-sprint8 dirty
KEEP vg-records-combo dirty
KEEP vg-script-p2r-land dirty
KEEP vg-split-land-2 dirty
KEEP vg-t-r087-land dirty
KEEP vg-t-reach-land dirty
KEEP vg-u-pipe-fix-land dirty
KEEP vg-u-pipe-tests-land dirty
KEEP vg-udir-land dirty
KEEP vg-udir-land2 not-on-origin
KEEP vg-udir-land3 dirty
KEEP vg-udir-land4 dirty
KEEP vg-udir-pre dirty
KEEP vg-udir-pre-b dirty
REMOVE vg-venvlink 493 MB (dry run)
REMOVE vg-venvlink-tests 493 MB (dry run)
KEEP vg-w1-leftovers dirty
KEEP vg-w1-pre dirty
KEEP vg-w2b dirty
KEEP vg-w2r-pre dirty
KEEP vg-w2s-fix2 foreign
KEEP vg-w2s-fix2-old foreign
REMOVE vg-w2s-goldens-base 448 MB (dry run)
REMOVE vg-w2s-goldens2-orig 449 MB (dry run)
KEEP vg-w2s-pre dirty
KEEP vg-w2s-pre3 dirty
KEEP vg-w2s-pre5 dirty
KEEP vg-w2s-tests3-build dirty
KEEP vg-w4 dirty
REMOVE vgd1-gate 437 MB (dry run)
REMOVE vgd1-main 437 MB (dry run)
REMOVE vl-build 493 MB (dry run)
REMOVE vl-tests 490 MB (dry run)
KEEP wt-cap-spec active
REMOVE wtcap-build 456 MB (dry run)
KEEP wtcap-partb young
REMOVE wtcap-records 450 MB (dry run)
REMOVE wtcap-tests 450 MB (dry run)
```

## Status totals

`worktrees 809 slots 3/12 wt 361.5/120 free 80.0/60`
