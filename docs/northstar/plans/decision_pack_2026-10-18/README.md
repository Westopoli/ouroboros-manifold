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

## B. The Architect's rulings of this week (context, candidates, lean)

### B1. SIM-LOGS W1, the window
`docs/northstar/plans/2026-10-15-sim-logs-spec.md`, "Rulings needed". The bible says "this window" (E-10 R-073-01); the reference never windowed. (a) the bible's window: entries since the previous mission ended or was refused; (b) everything the ring holds; (c) a fixed tick count of yours. Lean (a).

### B2. SIM-LOGS W2, the Defensive Stand trigger
Today the C sim admits a Defensive Stand on "any hostile neighbour", which composes an empty mission 14 times in 100 and swaps it silently. (a) an attack must be logged as resolved in the window or pending as a telegraph against the region; the hostile-neighbour shortcut goes and the test that pins it is retired under TD-SIM-1; (b) keep the shortcut, size the unattacked stand as an insurgency. Lean (a).

### B3. SIM-LOGS W4, the Containment arm
The bible says "two or more colonizations"; the reference counted attack conquests; the C port invented a revolt-or-archetype gate. (a) the bible's colonisation count, the gate goes; (b) the reference's conquest count; (c) keep the gate as an extra AND. Lean (a).

### B4. CHRON-CONTEXT W3, chain length
Moved out of SIM-LOGS. (a) stays 0 as the reference's effective behaviour; (b) the jump's count of events sharing the chain tag, as ALG-50 and R-066-02 say. Lean (b).

### B5. Second-Fable audit of SIM-LOGS' contract paragraph
The rules say the Dispatcher chat spawns it. (a) you open the Dispatcher for that one brief this week; (b) waive it for this piece, the three Sonnet rounds stand. Lean (a); the piece changes the save and the ABI.

### B6. Ripple entries (ledger row 10)
The reference had no ripple cluster; adjacent-region events competed as regional entries. The C port added ripples, uncapped, before scored clusters; 9 of 25 jumps carried 3 or 4. (a) drop ripples, match the reference; (b) keep, capped at 2 as E-09 R-065-05 reads. Lean (a).

### B7. Repeats (ledger row 13)
147 verbatim sentence repeats in 5 campaigns; the reference deduped within one scroll only (40 percent overlap). R-071 says never in a campaign. (a) campaign-level dedup with a fallback fragment; (b) relax R-071 to per scroll, as the reference did; (c) grow the library (E-21 pipeline). Lean (a) now, (c) later.

### B8. Fix order after SIM-LOGS
(a) chronicle.c rows 7 to 9 as one batch (family entry dropped past the 256-candidate cap, chain clusters at score 0, blank shells on the pipe); (b) the three as a skeleton you see in the sim viewer first, then the rest. Lean (b).

### B9. Q-069-03, the chronicle map and the printing entry
Entries print one at a time (your 10-13 call). When the galaxy replay reaches the next keyframe while an entry is still printing: (a) the map holds until the entry finishes, book with pictures; (b) the map runs at 2 ticks per second and the scroll catches up. Unblocks the chronicle map piece and shapes the transition's galaxy moment. Lean (a).

### B10. Q-B23b-01, the galaxy renderer
Under Forward+ the translucent faction shells wash the system dots (pixel test 6 of 18); under opengl3, the gate's renderer, they read. (a) ship Forward+, the pixel test gains a Forward+ run; (b) the wash is the approved look; (c) a lane B piece lowers shell alpha over dots. Lean (c) and ship Forward+ (the 3D ground wants it).

### B11. Branch delete
`branch_triage_2026-10-15/delete_list.txt`: 250 branches proven landed (97 ancestors of main, 153 byte-identical on every file). (a) delete the 250; (b) keep, list only. The 127 unproven and 2 provisional stay either way. Lean (a).

### B12. Q-NET-05, Linux and Mac lockstep
Measured 2026-10-18 (`2026-10-18-macos-pipe-probe.md`): the Mac's full checksums equal the Linux pins at ticks 100, 500, 1000, 2000; the release tick path calls no libm transcendental. (a) close as matching, Windows row from the wine result beside it; (b) also run under Rosetta to cover the SSE branch; (c) extend the probe to a second seed, a longer run and a tactical fight before closing. Lean (c) then (a).

### B13. A99 tactical hashes (test-defect candidate)
`tests/csim/test_E13_A99_tactical_equivalence.py` reds on Linux and Mac alike at step 0 for the three gap fights; the harness builds the fight with Python `math.hypot`, so the recorded hash depends on the Python version. (a) test-defect: the harness uses the sim's own distance and the hashes are re-recorded under a TD row; (b) a real finding to diagnose first. Lean (a).

### B14. Transition mockup pass 1b (S-108)
Shots `P-S108-*` in your folder. (a) approved: an integration lane row for S-108 (guard 4, approved means scheduled) with the star-blob note as its first fix; (b) pass 2 first: name what to change (blobs, haze, timing, the dot's scale).

### B15. Terrain-obeys mockup pass 1 (S-191, S-189)
Shots `P-S191-*`. The pads, the choke and the vantage are produced and measured; routes are not, the ground has none to spare. (a) pass 2 with route carving (a corridor of the rolled width along a found path, graded under 35 degrees) as the fourth edit, plus the objective off the base line and canvas-scaled insets; then lane P rev 6 from its facts; (b) stop prototyping, write the C spec from pass 1's numbers; (c) a different direction (say which). Lean (a).

### B16. The 92 control stubs and the 37 untested ALG rows
`sim_lane_2026-10-12/coverage_algorithms.md`. Every detector must ship a positive control; 92 generated stubs raise NotImplementedError. (a) a test-writer batch fills them epic by epic, E-08, E-09, E-10 first (the sim's core); (b) retire the stubs whose bug ids no code names, fill the rest; (c) later. Lean (b). The 37 uncovered ALG rows: same order, E-08/E-09/E-10 first, your thresholds per row as the writer reaches them.

### B17. Unused constants (ledger row 16)
`om_constants.h` defines `OM_BUDGET_PRESSURE_THRESHOLD`, `OM_REINFORCE_*`, `OM_ATTACK_CONFIDENCE_*`; `agent.c` and `resolve.c` use the literals 0.8, 0.5, 1.5 instead. (a) a CONST-2 piece makes the code read the constants (byte-identical behaviour, a test proves it); (b) leave. Lean (a).

### B18. Row 4, the opening jump seats no lineage
The first mission of every campaign scores relevance 0 because the generator runs before the selector seats the lineage; SIM-LOGS papers over it with `om_seated_lineage`. (a) the selector-order fix as its own piece after SIM-LOGS; (b) accept the paper-over. Lean (a).

### B19. Lab run on the Mac during the offline window
`scripts/simviewer/probes/offline_run.sh` (landing today) runs the mission-choice sweep at 50 seeds, the chronicle twin at 20, the csim suite, and a skill-lab layout-search batch at 8 workers as a Mac-vs-Linux parity run. Nothing to rule; the results are read when you are back.

### B20. The camera among five stacked sheets, and the layer read from the map (T3; Q-103-06)
`docs/northstar/research/options/space-camera/options.md`. The vision tube is ruled; what is open is the camera beyond it. T3-1: the lane D shot shows first (A) peel to the focus layer, (B) camera stays above the stack, or (C) the gap grows with pitch. T3-2: which two of (a) pins, (b) stacked slices, (c) colour bands, (d) sheet silhouettes to mock up beside pins for Q-103-06. T3-3: is C's exploded view worth its picking cost (yes keeps it, no retires it). Lean: A first, mock up (b) and (d), C yes.

### B21. Layout library pairing (T19, section 4 row 1)
`docs/northstar/research/layout_engine/library_audit_2026-10-18.md` (landing today): per-layout keep/reference/retire and a proposed archetype pairing; its questions for you are listed at its end.

### B22. Website refresh draft (T8)
Branch `refresh-2026-10-18` in `~/Projects/ouroboros-site` (local only, never pushed, `npm run build` green, 21 pages): `/galaxy/`, `/landscapes/`, `/walkers/`, `/method/` plus nav links. Read it with `cd ~/Projects/ouroboros-site && git switch refresh-2026-10-18 && npm run dev`. Thirteen claims the writer flagged for checking are in its report (the Architect holds them); two are yours: (a) does `/method/` publish internal programme figures (83 percent of pieces landed, 0 of 240 stories Seen, 62 test-defect rulings, three quarters of cost in two planning sessions) or keep them in the repo; (b) are your name and verbatim quotes on the site. The site is still `noindex` behind the private-playtest banner. Publish is a separate yes.

### B23. ALG-49 and ALG-77 (sim lane ledger rows 18, 19; `push/alg-cover-e08-e10`)
ALG-49 says a supreme commander's successor is created "in the faction's first region"; the C creates it in the dead commander's region. (a) the dead commander's region, rewrite the row (the successor takes the post where it fell); (b) the faction's lowest-index owned region as the row reads; (c) the faction's home region (the capital). Lean (a). ALG-77 says history weight in the commander pools decays 0.75 per generation; the C applies that decay only to the rotation probability (your Q-057-01 (a)) and pool scoring has none. (a) the row follows the ruling, decay stays on rotation only; (b) add the decay to pool scoring as the row reads. Lean (a).
