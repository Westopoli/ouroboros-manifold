# Lab inventory, 2026-10-30

Read-only inventory by a Sonnet engineer for Westley's resume plan under `docs/method/`; delivered unedited. Brief: what is built, what is unlanded, what is planned, which bible rules and numbers back each piece, the last result he saw.

LAB INVENTORY (Sonnet engineer, read-only, origin/main 80105fdf, 2026-10-30)

I took every figure below from the files and git history, and did not run any test. All paths are inside the worktree `/home/westopoli/Projects/om-push/wt/lab-inventory`, which is now marked finished. Paths starting `docs/` are under `docs/northstar/` unless I wrote the full path.

**PURPOSE:**
- The lab is a simulator that varies what an RTS varies (position, orientation, damage, health, vision, landscape, layers) and finds where "the lines cross". That means the settings at which a smaller force played with skill beats a larger force played without it, for five skills: landscape, formation, layers, enemy position and unit-type matchup.
- Westley, 2026-10-01: "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force". Also: "The goal is to create a game with significant strategic depth. We get to this goal by tuning all the variables we laid out such that that sentence becomes a reality." (`research/layer_dynamics/README.md` section 1.)
- Method, 2026-09-30: "iteratively try small things, check the output, and tune repetatively."
- More than one answer is allowed, 2026-10-01: "The lines can cross in multiple locations."
- On 2026-10-15 he added that "the whole point of the simulation lab is to find multiple points where the lines cross" (E-20 R-151-02).
- It measures on the real C sim, not a model. It counts "can your unit get shots off" (README section 2). Break-even is in whole units: "16 units beat 17 enemies and lose to 18".
- Finished means (Westley 2026-10-27, decision DEC-lab-finished-lines-cross-2026-10-27, `story_reviews/westley/decisions.md:76`): "where the lines cross should be documented quite extensively, we know the lab is finished when that happens."
- Priority (Westley 2026-10-26, decisions.md:67): "The lab is more important than the beta. Honestly, the beta should come after the lab, because the beta is going to use the information from the lab."

**LANDED:**

Everything below is under `scripts/skilllab/` (about 8,100 lines in 44 modules). It has 144 test files in `tests/skilllab/` plus `ground/` and `integration/`. Roughly 217 test files in the repo mention skilllab. Every row has tests, with a positive control for each detector.

| Capability | Files | Landing sha, date | Test |
|---|---|---|---|
| Harness: runs one fight on the real C library through ctypes, with deterministic position shifts as replicates; reads the winner, margin, ticks and units firing | `contract.py`, `engine.py`, `fight.py`, `firing.py`, `formations.py` | `61a201e6`, 2026-10-02 | Yes, `tests/skilllab/`, plus three real-engine controls (mirror, numbers, planted 20% damage) |
| Break-even scans in whole units, 8 to 48 enemies against 16, bisection and full scan; a play that beats 48 is a "ceiling hit" | `scan.py`, `breakeven.py`, `pool.py` | rev 2 landing `43bf9462`, 2026-10-22 | Yes |
| Fourteen scripted plays (skilled and naive), roster mixes M0 to M4 and M3b, naive baselines (blob, line, attacker, defender) | `plays.py`, `plays_space.py`, `skills.py`, `scenes.py` | `43bf9462`, 2026-10-22 | Yes |
| Knob sweeps (vision, range-up, damage-up, emitting, sign-flip, arc and cone), coarse grid in a 0.25x to 4x band, refined at a crossing, with controls | `sweep.py`, `batches.py`, `asym.py` | `43bf9462` | Yes. The arc and cone families skip because the engine lacked them until E0 |
| Pre-flight that refuses cells it cannot run (`no_fit`, `unroutable`, `no_reach`, `blind_post`) | `scenes.py` | `43bf9462` | Yes |
| Re-engage stand-in rule (idle units attack-move to the visible enemy centroid) and its refinements | `fight.py` | `43bf9462`, then `1938aefd`, 2026-10-22 | Yes |
| Predictions per fight (count-only and type-weighted, opening window of 40 ticks) and an agreement column | `firing.py`, `rows.py` | `43bf9462` | Yes |
| Artifact page: findings, top-down SVG diagram for every crossing, ceiling hit and both-wrong fight, condition verdicts only if given a thresholds file | `report.py`, `diagram.py`, `conditions.py`, `evidence.py`, `charts.py` | `43bf9462` | Yes |
| Ground scene `s1_slope_top` on seed 11, canvas 12000 | `ground/scenes_ground.py` | `43bf9462` | Yes. Its knobs are inert in the natural scene (README section 7) |
| Speed work: firing cache, epoch counter and memo levers | `engine.py`, `fight.py` | `3ee183d7` and `384108e9`, 2026-10-22 | Yes. Two speed tests are known red under `FINDING-speed-marks-unmet` |
| Vision positive control (play `s3_vision_control`) | `plays_space.py` | `e93d31ba`, 2026-10-22 | Yes |
| Rev 3 A: built-in unit types instead of copies (fixes the lost Warden aura and Bastion cap), naive attacker fields the play's mix, dark striker emits, category family marked unavailable, inert-knob probe, coverage test | `coverage.py`, `probe.py`, `contract.py`, `sweep.py` | `7b91383c`, 2026-10-22 | Yes. Coverage test T1 was a strict expected failure until B |
| Rev 3 B: mixes M5 to M9, plays on all five layers, layer-symmetry control, 30-fight mirror pre-check, Warden cap of 4 per 16 | `plays_space.py`, `scenes.py`, `sweep.py` | `7dd4d8fc`, 2026-10-23 | Yes. `pieces.toml` still says queued and has no landing row |
| E0 contract piece: `OM_TP_FIRING_ARC_DEG`, `om_roster_set_cone` and `om_combat_can_engage` declared in the C header. ABI version 9, save format 13 | `csrc/ouroboros_sim.h:1079-1093` | main, 2026-10-29. Records at `301b68e5`; the pieces.toml attach flip says `3ee3faaf`, which is the SPEED stage-one commit, so check that sha | Yes (`tests/specfactory/test_pp_contract_lab_rev2.py`) |
| Engine behaviour that the lab depends on: attack-move resumes after engagement (E1, E1b), runtime collision radius (E3) | `csrc/unit.c`, `csrc/tactical_move.c` | `43bf9462` (E1, E1b), `b517d01a` (E3) | Yes |
| Port-parity engine pieces (the `PP-*` rows) and the layer engine: ping, going dark, reach by type, targeting by sight | `csrc/` | README section 8 steps 3 and 5 | Yes |
| Layout run 1: 200 layouts, 12 scans each, 244,800 fights | `scripts/skilllab/depth.py`, `maps.py`, run folder `docs/northstar/research/layer_dynamics/runs/2026-10-08_layout_run1/` | `a9ee5897`, 2026-10-08 | Yes |
| Earlier landscape, formation and layers batches, and a ping search | `runs/` (24 folders), `search*.py` | 2026-10-02 to 10-08 | Yes |

**UNLANDED:**

I found 137 lab-named remote branches. Most have 0 commits ahead of main. Those with commits not on main are below.

| Branch | Holds | Tip date | Stopped why |
|---|---|---|---|
| `push/labrev3-c` (22 commits ahead; sub-branches `-tests`, `-mbuild`, `-mirror-tests`, `-float`, `-golden`, `-tests-wip`) | Rev 3 C built: reach table as a swept input, paper prediction, `no_reach_stall`, `decided_one_way_reach`, verdict-aware mirror pre-check, a re-recorded golden. Tip `e0c2c01e` | 2026-10-20 | Not landed. The plan of record says "not started", which is wrong. The `-tests-wip` branches were saved after the overseer chat was out-of-memory-killed on 10-20. Everything on the branch predates the E0 landing and the 10-22 rev 2 landing, so it needs a merge, re-gating and probably new goldens. I did not check how it merges. |
| `push/labrev2-e2` (4 ahead) | E2 firing arc gate, cone damage and the `can_engage` body. Tip `3c35accb` | 2026-10-14 | Waits for E0 to land. Decision DEC-lab-E0-rebase-2026-10-29 says re-pin it onto ABI 9 / save 13. |
| `push/labrev2-e4` (8 ahead, includes E2) | E4 radius guard step-and-return, 200 wu. Tip `f9e4a436`. Tests branch `push/labrev2-e4-tests` (`55b532df`) needs a re-audit. | 2026-10-14 | Same as E2. |
| `push/archive-lab-e0g-e0`, `-e0audit-e0`, `-e0push-e0`, `-e0red-merged-e0` | Archived E0 working branches | 2026-10-29 | E0 has landed; these are leftovers. |
| `push/labrev2-e0-lo` and `-lob` | Arc lower bound 10 to 5 (decision 48) | 2026-10-19 | Superseded by DEC-arc-lo-10-2026-10-29, which keeps 10. |
| `push/labrev2-flip` and `-flip-tests` (5 and 2 ahead) | Default for `orders_per_unit` flipped to False (group attack-move) | 2026-10-20 | Never landed. The README says the flip rides the landing only if every cap is a blind-post finding. |
| `push/labrev2-layoutfit` (1 ahead) | Which draw layouts fit the vision plays; information only | 2026-10-19 | Informational. |
| `push/labrev2-speed2-tests` (2 ahead) and `-speed-tests` (1 ahead) | Frozen reference and tests for a second speed piece | 2026-10-22 | "Tests withheld, pre-piece ratio below 0.7 (stop rule)." |
| `push/labrev2-capability-tests` (1 ahead) | Holding branch for six E0/E2 capability tests | 2026-10-21 | Waits on E2. |
| `push/lab-decisions-page` (1 ahead) | Decisions page for run 1: three owner questions drawn as SVG | 2026-10-08 | Not landed. |
| `push/lab-runs-1006b` (3 ahead) | Old formation, layers and landscape batch run files | 2026-10-06 | Old instrument, superseded. |

**PLANNED:**

The plan of record (`plans/2026-10-27-lab-plan-of-record.md` section 3; status head says resumed 2026-10-29) and the rev 3 plan (`plans/2026-10-19-skill-lab-rev3-plan.md`) list the following.

1. Records fix: flip LAB-REV3-B in `pieces.toml`, add its landing row and the ROADMAP row, add the positioning-decides sentence to README sections 2 and 4, add the ten coverage defects to README section 12. Depends on nothing.
2. E2 (firing arc, cone) plus E4 (guard radius) plus FU-warden-no-stack (Wardens do not stack, R-083-03). They build stacked on one branch and land once, because they share `csrc/unit.c`. Depend on E0, which has landed. About 35 M tokens.
3. Vision-asymmetry plays (ping, going-dark, decoy). The Architect first checks which are registered in `plays_space.py` and specs the missing ones. About 15 M.
4. Rev 3 C: reach and vision as swept knobs, the paper prediction ("positioning decides" made operational), `no_reach_stall`, per-reach crossings. The branch exists (see UNLANDED). It depends on E0. About 15 M, ceiling 50 M.
5. R9 sight-engagement engine rule (Starcraft rule set, approved), then retire the re-engage stand-in. About 15 M.
6. Batch one, the first night after steps 2 to 5 are on main. Plays: layer-above, types-by-reach, the five mix plays, and the ping and dark plays. It covers every layer pair the reach table allows and the arc, cone and guard families, on smoke layouts 81, 78 and 192. Compute, then about 10 M to review. Westley sees the first page and diagrams.
7. Batch two and the ground scene, with ALG rows written for Q-008-03. Waits on batch one's analysis.
8. Speed-up piece (marks kept, queued after rev 3 C).
9. The search for every region where the conditions hold, run two ways (all settings at once; step by step). Not specced. `LAB-SEARCH` is only an attached row, and `search.py` is the ping-search scene, not this.
10. The crossings document, read by Westley. This is the stated end.
11. Not in the numbered plan but open: the layout run 1 chart that Westley has not seen; the weekly "definition of lab finished" still unconfirmed (see REQUIREMENTS).

**REQUIREMENTS:**

No story or rule states the lab itself. Several stories name it as the source of their numbers, and the lab's own definition lives only in `research/layer_dynamics/README.md` and decisions.md.

| Capability or plan item | Bible home |
|---|---|
| The lab as a whole, its five skills and conditions | No story. Closest: E-01 S-008 "I know whether my unit can shoot an enemy one layer up", "spec'd, blocked on Q-008-02, Q-008-03" (`docs/bible/stories.md:14`), and E-01 acceptance bar line 161 ("strategic depth holds in the skill lab before any cross-layer number is fixed"). Hub principle 4. |
| Balance harness and pass marks | E-21 S-156 (`stories.md:162`), R-156-01 and R-156-02, blocked on Q-156-02 (`epics/E-21-offline-ai-pipeline.md:89-95`). Does not describe the five skills, plays, sweeps or the artifact. |
| Search, many crossing regions | E-20 S-151 (`stories.md:157`), R-151-02 (`epics/E-20-multi-era-and-monetization.md:116`) |
| Ping, going dark, reach by type | S-162, S-163, S-164 (spec'd; the lab measures them) |
| Firing arc (E2) | S-100 R-100-04 draft. Open row Q-100-01 in the register; decision 46 gave 30 degrees. |
| Cone (E2) | E-11 R-082-10 (shape ruled 2026-10-15, numbers DRAFT) |
| Radius guard (E4) | S-208, R-096-08 (ruled 2026-10-13); Q-208-01 open |
| Warden no-stack | E-11 R-083-03 |
| Attack-move resumes, return-fire redirect | R-096-02, R-087-06 (rewritten 2026-10-13) |
| Cross-layer vision and ground flyers | R-005-05, R-005-09; Q-005-05 and Q-005-06 are parked for the beta |
| Positioning decides, paper prediction | Memory note `feedback-positioning-decides` and rev 3 plan R4 only. Not in the bible. The README does not yet state it. |
| Naive baselines, plays and counters, artifact, scans, speed marks | No story. These are lab internals (rev 2 spec, rulings 1 to 13). |

**Open Q rows** (status as the register shows it):
- Q-008-02 (the research programme, open; E-01 names the lab as its answer).
- Q-008-06 (how refusing a fight is checked, open).
- Q-156-02 (pass marks, open; Westley 2026-10-21 said "not enough context", and decision DEC-Q156-2026-10-22 has the lab report without verdicts until he confirms).
- Q-166-04 (does a layer step scale with height; open; "3: scales with height and let's measure it with the lab").
- Q-LS-02 (sweep the enemy mix per layout, open) and Q-LS-03 (likely-places ping policy, open).
- Q-165-01 (open, no text recorded).
- Q-008-03 is closed in the register ("decided by the skill lab") but README section 12 says it closes when the ALG rows exist. The two disagree.
- Q-LAB-01 (stalemates) is superseded. Q-LAB-02, Q-LAB-03, Q-008-05, Q-008-07, Q-096-01, Q-005-07 and Q-001-05 are closed (Q-001-05 as provisional).

**Numbers the lab relies on:**

| Name | Value | Source |
|---|---|---|
| Fight ends by elimination; tick cap 12000 as bug detector | Westley | Q-LAB-03, 2026-10-13 |
| Enemy headcount scan, against a force of 16 | 8 to 48 | Westley, "#2: A", 2026-10-13 |
| Same units, same values on both sides | rule | Westley 2026-10-13 |
| Sweep band | 0.25x to 4x of base; firing up is a penalty, grid 1.0 down to 0.25 | Westley 2026-10-13 (rulings in README section 4) |
| Emitting pair | sight x2.0, seen x3.0 | Westley 2026-10-13: "let's make that a knob, let the sweep find the crossing" |
| Skill worth | singles about 30%, full mastery 3x or more; rough sizes only, not pass marks | Westley 2026-10-01 ("I like C") |
| Larger force wins when everything is identical | control | Westley 2026-10-01 |
| Mirror control tolerance 0.10, 20 fights | Westley | 2026-10-02, harness check |
| Firing arc 30 degrees, grid 7.5 to 120 | Westley decision 46 and 47, 2026-10-19; the header name stays DRAFT | decisions.md |
| Arc lower bound 10 degrees | Architect, DRAFT-arc-lo | DEC-arc-lo-10-2026-10-29 |
| Reach rulings (ground fire goes cross-layer; vision symmetric in space, asymmetric in ground) | Westley | 2026-10-13 |
| Mixes M5 to M9 | Westley accepted | 2026-10-19 (rev 3 plan R1) |
| Warden cap 4 per 16 | Interim until FU-warden-no-stack | rev 3 plan D9 |
| Pass marks C0 to C9 (for example C1 at least 80% of maps, C2 rank agreement at least 0.8, C3 5%, C4 60%, C5 10%, C6 half the advantage on 60% of maps) | "Answered 2026-10-27: pass marks as drafted" per the plan of record section 5. The register and DEC-Q156-2026-10-22 still call them unconfirmed. I found no recorded quote of that answer. | Treat as unconfirmed |
| Speed marks (16 v 48 fight under 1.5 s; 8 to 48 scan at 3 replicates under 90 s; first batch under 4 h wall; rows byte-identical at 1 and 12 workers) | Westley "Keep speed marks", 2026-10-27 | DEC-speed-marks-kept |
| Opening window 40 ticks | Draft | DRAFT-opening-window-ticks |
| Guard radius 200 wu | Draft | DRAFT-guard-radius |
| Cone range 300, half-angle 45, share 1.0 | Draft | R-082-10 |
| Mixes M1 to M4, M3b and layer stacks of the five mix plays | Architect drafts | README section 12 |
| Re-engage silence 40 ticks; moved threshold 1 wu | Draft | README section 12 |
| Behind cover 150 wu; ambush behind 200 wu | Draft | README section 12 |
| Coarse step 8; control tick cap 600 | Draft | README section 12 |
| Ground geometry (holder radius 30+3*sqrt(n), five coordinate pairs) | Draft, measured | README section 12 |
| 30-fight naive mirror pre-check | Architect | rev 3 plan |
| Layout run 1 grid: 6 features, 648 layouts, 200 sampled, 12 scans per layout, G=2 gain threshold, WIN_MARGIN 0.05 | Drafts, Q-LS-01 says "draft stands until the first chart" | `lab-drift.md` section 4 |
| Daily token allotment 300 M (60 Dispatcher, 180 pieces, 60 reserve) | Westley approved 2026-10-27 | DEC-daily-allotment |

The `lab-drift.md` constants list is dated 2026-10-07. I did not re-check it line by line against the code, so many constants in it may have been retired by rev 2.

**LAST RESULT:**
- The last lab batch was layout run 1 (landed `a9ee5897`, 2026-10-08, files in `runs/2026-10-08_layout_run1/`).
  - It ran 244,800 fights over 200 layouts.
  - 37.2% were decided, 6.9% capped, and 294 of 2,400 groups had a cap.
  - The naive line scored 0 or 1 on 184 of 200 layouts.
  - Six layouts scored 5 (81, 78, 68, 151, 169, 192).
  - Start distance 1400 scored 2.08 against 1.19 for 2800.
- This result is stale. It was taken on the old instrument, and the 10-13 ruling says run 1's 143 always-capped groups had no contact at all.
- Rev 2 and rev 3 rebuilt the instrument after it, so run 1 is not comparable to anything built since.
- After the rev 2 landing, only smoke checks have run, with no analysis. Batch one has never run (plan of record section 2).
- The last time Westley saw a lab chart was the Formation Read page on 2026-10-04 (`ROADMAP.md:60`, private artifact).
  - His earlier "much better" came on 2026-10-01, about the sample chart form (README section 5).
  - Run 1's chart is recorded as "waits for Westley" and I found no reaction to it.
- His last recorded words on the lab are policy, not a result. On 2026-10-26 and 10-27 he said the lab comes before the beta, the lab is finished when the crossings are documented, build the combat behaviours first, and keep the speed marks.

**RESUME FIRST (engineer's reading):**
1. Correct the plan of record. E0 is on main (so step 2 no longer waits on E0), and rev 3 C is built and unlanded on `push/labrev3-c`, not "not started".
2. Convert the lab's pieces to stories. The lab itself has no story, so the Architect needs to write one: the five-skills goal, the measure, the conditions and the "finished" definition (DEC-lab-finished-lines-cross-2026-10-27). Pass marks in the register and the plan of record disagree, so settle that first.
3. First buildable story: E2 plus E4 plus FU-warden-no-stack, re-pinned onto ABI 9 (branches `labrev2-e2` and `labrev2-e4` are 16 days old). Rev 3 C follows, merged over E0 and rev 2.
4. Two bible gaps block clean stories: the positioning-decides rule is in no epic or README principle, and Q-156-02 and Q-008-06 are still open. Q-008-03 closes in the register but not in the README.
5. The search and the crossings document have no spec at all, and batch one waits on all of the above. That is where most of the unwritten requirements sit.

**NOT VERIFIED:**
- I ran no tests and built nothing. The test counts come from the 10-13 baseline file (2,543 passed, 2 failed, 80 skipped), not from a fresh run.
- I did not check how `push/labrev3-c` merges with current main.
- I did not verify the E0 attach sha (`3ee3faaf` looks like the SPEED commit, not E0).
- I did not confirm that "pass marks as drafted" was said by Westley on 2026-10-27, only that the plan of record states it.
- I did not read the rev 2 decisions file (271 lines) or the rev 2 spec in full. I used only the baseline, the quoted decision lines, and the plan of record.
- I did not check which vision-asymmetry plays are in `plays_space.py` (plan step 3).
- I did not read the programme-spec audits or the 2026-10-02 parity files beyond what is quoted.

**WORKTREE:** done 80105fdffa351450e6701ffb667c69b728035594
