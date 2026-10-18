# Decision pack, 2026-10-18 (Westley's offline batch)

One sitting, offline, as many as you can. Everything here is a decision only you can make or a shot only you can judge; each says what it unblocks on the Linux box this week. Answer in one file (`answers.md` beside this one, or a message): shots as `<file>: approved | rejected — <note>`, questions as `<id>: <letter> — <words if any>`. The Architect folds every answer into the register, the epics and the queue, and the Dispatcher orders the week from them.

The four appendices: **A** the shots (`../../story_reviews/westley/README.md`, one row per file, plain names); **B** the Architect's rulings of this week (below, with context); **C** the register extract (`register_extract.md`, every open flag with its full question and candidates, grouped); **D** the five doc branches waiting on your reading (`doc_branches_digest.md`).

## What the week on Linux can be, by your answers

| If you answer | Linux queues |
|---|---|
| The lane shots (A) | A, B, C, E fix pieces one per verdict; lane E fan-out (E1l, E1o, E1p-b) on S-237; lane B B25/B26 |
| SIM-LOGS W1, W2, W4 | SIM-LOGS tests and build; then the five call sites; then chronicle.c rows 7 to 9; both sweeps re-run |
| Terrain-obeys pass 2 go | the route-carving mockup pass on the Mac or Linux; lane P rev 6 from its facts; P1 and P2 build meanwhile |
| Transition 1b verdict | integration lane row for S-108 (guard 4) or pass 2 |
| Q-069-03, Q-B23b-01 | chronicle map piece; lane B pixel test |
| Branch delete | a clerk deletes 250 branches |
| Lab pass marks (C §10) | lab rev 2 runs with real marks instead of drafts |
| Combat framework (C §2) | the roster spec for 20 to 40 types; the cone and arc sweeps get their final rule |
| Era roster (C §3) | the era pack form lands; the land era gets its name and brief |

## B. What still needs you (everything else in the old B list was an implementation decision and is taken; see C below)

### B9. Q-069-03, the chronicle map and the printing entry (feel)
Entries print one at a time (your 10-13 call). When the galaxy replay reaches the next keyframe while an entry is still printing: (a) the map holds until the entry finishes, book with pictures; (b) the map runs at 2 ticks per second and the scroll catches up. Lean (a).

### B10. Q-B23b-01, the galaxy renderer (look)
Under Forward+ the translucent faction shells wash the system dots (pixel test 6 of 18); under opengl3, the gate's renderer, they read. (a) ship Forward+, the pixel test gains a Forward+ run; (b) the wash is the approved look; (c) a lane B piece lowers shell alpha over dots. Lean (c) and ship Forward+.

### B14. Transition mockup (look): the shots `P-S108-*`
Pass 1b scale and path; pass 1c (the star blobs) is being built now as a render fix below the gate. (a) approved, S-108 gets its integration lane row; (b) pass 2 with your notes; (c) rejected with a note.

### B15. Terrain-obeys mockup (look): the shots `P-S191-*`
Pass 2 with route carving is being built now (implementation). What is yours: do a pad, a choke bar and a wall read as places on the land, and is the carved-route look (pass 2's shots, next batch) acceptable, or should routes come from the landforms themselves (a design direction, not a fix)?

### B20. The camera among five stacked sheets (look): T3-1 A/B/C, T3-2 two of (a)-(d), T3-3 yes/no
`research/options/space-camera/options.md`. Lean A, (b)+(d), yes.

### B21. Layout library pairing: the three design questions from `research/layout_engine/library_audit_2026-10-18.md`
Q-191-06 engine shape A/B/C (assumed C); may a layout demand a landform (coast, high ground): yes / no / short list; new layouts for the four archetypes with no survivor: draw now / compose from kit situations later / terrain-found places only. The other five of its eight are implementation and taken (retag by geometry; rerun run 1 after the end-rule fix; delete the hand-drawn towns in 04 and 07; a plays field in the file; slope-top and tall-cover node kinds).

### B22. Website (publishing): does `/method/` publish the internal programme figures, and are your name and quotes on the site; and the publish itself.

### B23. ALG-49 (rule meaning): where a supreme commander's successor appears. (a) the dead commander's region, rewrite the row; (b) the faction's lowest-index region as the row reads; (c) the faction's home region. Lean (a). (ALG-77 is taken: the decay stays on rotation per your Q-057-01 (a); the row is rewritten.)

### B5. Process: the second-Fable audit of SIM-LOGS' contract paragraph. (a) you open the Dispatcher chat for that one brief; (b) waive it for this piece. Lean (a).

Plus **A** (the 22 shots), **C** `register_extract.md` (design flags; the Architect sweeps it for implementation-type rows and closes those himself before you read it, marking them "taken"), **D** the five doc branches (a/b/c each).

## C. Taken by the Architect 2026-10-18 (implementation; veto in one line if wrong)

| Was | Taken as | Recorded in |
|---|---|---|
| B1 W1 window | (a) the bible's "this window" = since the last mission ended | `2026-10-15-sim-logs-spec.md` |
| B2 W2 trigger | (a) logged or pending attack; hostile-neighbour shortcut goes; TD-SIM-1 | same |
| B3 W4 Containment | (a) colonisations >= 2, the C gate goes | same |
| B4 W3 chain length | (b) per jump from the chain table | `2026-10-18-chron-context-spec.md` |
| B6 ripple | kept, capped at 2 per R-065-05, flagged consequences only (CH-4) | sim lane ledger |
| B7 repeats | campaign-level dedup with fallback per R-071 (CH-7); library later | ledger |
| B8 fix order | skeleton (CH-1, CH-2, CH-3, mission swap) seen in the viewer, then the rest | ledger |
| B11 branch delete | executed per your (c) ruling (250 proven landed) | `branch_triage_2026-10-15/` |
| B12 Q-NET-05 | closed (a) after PROBE-2 (second seed, long run, a fight) | register |
| B13 A99 harness | test-defect TD-SIM-5 | ledger |
| B16 control stubs | retire-or-fill triage, E-08/E-09/E-10 first | `controls_triage.md` |
| B17 unused constants | CONST-2 launched, byte-identical | `push/const-2` |
| B18 opening seating | SEL-ORDER piece after SIM-LOGS | ledger |
| B19 | nothing to rule | |
| B21 (five of eight) | as listed above | library audit |
| B23 ALG-77 | decay on rotation only, per Q-057-01 (a); row rewritten | ledger |

