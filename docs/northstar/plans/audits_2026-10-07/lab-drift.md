# Lab drift audit (2026-10-07, Sonnet)

**Lab drift audit, read against origin/main as of 2026-10-07.** All of it is read-only on a detached worktree, which is now removed.

Three limits on the evidence. I found no repo text for "I'm only ok unpausing the lab if there's information we can glean". I did not run any tests. I did not check unmerged branches.

## 1. Quotes (source in brackets)

- Goal: "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force" (2026-10-01, README §1).
- "The goal is to create a game with significant strategic depth. We get to this goal by tuning all the variables we laid out such that that sentence becomes a reality" (2026-10-01, README §1).
- Method: "iteratively try small things, check the output, and tune repetatively" (2026-09-30, README §1).
- Multiple answers: "The *lines* can cross in multiple locations…" (2026-10-01, README §1).
- Measure: "the differentiator is **can your unit get shots off**" (README §2). Break-even is in whole units: "16 units beat 17 enemies and lose to 18" (README §4).
- Skill worth: "it depends on the number of units that can get shots, not a basic ratio" (README §2). He chose "I like C": singles of about 30 percent, full mastery 3x or more, "rough sizes only, not pass marks" (README §2).
- Naive play: "a blob if they're mediocre players, or a spread out line if they're skilled players" (2026-10-02, README §11).
- Two labs: one per era kind, space and ground, "a clean separation" (2026-10-05, README "Two labs").
- Layout search: "yes on B" (2026-10-06, layout spec L3). The lab "runs on guided-random layouts now, record which induce strategic depth, and find where the composition lines cross, while the ground lab waits" (layout spec L3, the spec's gloss). "go on all, we're pushing for our 2 week deadline" (layout spec L3).
- Stalemates: "matches were flagged as 'ties' when in reality just not all the units had engaged… This is something we want to avoid" (2026-10-06, Q-LAB-01). 2026-10-07: "#7 doesn't pertain to beta."
- Unit size: "we'll want to find lines crossing with unit sizes included" (2026-10-06, Q-LAB-02, closed (a)).
- Placement (Rev 3, 2026-10-07): "why can't we position the units ourselves instead of making them walk… we're placing units in specific patterns to detect strategic depth… A skilled player… will micro them into specific formations." His correction: placement replaces the walking, not the start-distance feature. Rev 4: "a, that sounds good, that accounts for the whole situation."
- Ping: Q-162-05 is "an area of investigation" (2026-10-05). 2026-10-07: "#6: This was already been decided… pertains to simulation lab."
- Priority: "strategic depth (the simulation lab) stays the priority and keeps moving" (visible-game-programme.md:19). "Lab reports are answered first" (:100).
- Not found in the repo: "I'm only ok unpausing the lab if there's information we can glean" and "induce a guided randomness in the layouts". The nearest text is the spec's gloss.

## 2. Requested items

| Item | Source | State | Evidence | Measures what was asked? |
|---|---|---|---|---|
| Skill-vs-naive break-even in whole units | README §4 | Delivered | `scan.py`, `breakeven.py`; golden controls (8 red, awaiting his re-record) | Yes, on contact-distance setups |
| Five skills, plays and counters | README §3 | Partly: 7 skilled plays and 3 counters registered as drafts | `plays_space.py`, `skills.py:63-82`; `plays_drafts.md` | No counter for S3, S5, concave or screen. Westley has not confirmed the plays page. |
| Naive play measured as blob and as line | README §3 | Partly | Layout search uses one shared blob (`depth.py:30`) | The line-abreast baseline is not in run 1. |
| Space lab | README "Two labs" | Delivered | `scripts/skilllab/README.md`; batches in `runs/2026-10-05` to `-06d` | Yes |
| Ground lab on real terrain | 2026-10-05 split | Not started. Terrain stage 2 landed (ROADMAP:67), but `ground/` is still parked with no spec. | `ground/README.md` | No |
| Ping measurement | Q-162-05 | Partly: stage A search batch and run | `runs/2026-10-05_ping_search`, `search_batch.py` | The five readings and pass values are not built. "Likely places" policy (Q-LS-03) is not in the search. |
| Layout generator (guided-random layouts) | layout spec P1 | Delivered (`layout_map`) | `maps.py:40-45`; commit 373dee3b | Yes |
| Depth score and pillars table | layout spec §2-4 | Delivered as a draft | `depth.py:17,136-205` | Smoke only, see below |
| First chart (200 layouts) | layout spec §3, DAG | Not run. Only 3-layout smoke runs exist (`runs/2026-10-06e,f`, `07a`). | `2026-10-07a_layout_smoke/depth_summary.json` | Not applicable yet |
| Unit-size sweep | Q-LAB-02, D1 spec | Not started. `csrc/tactical_move.c` has 0 hits for `ms->rad`, and `test_E13_R097_05_runtime_radius.py` does not exist. | grep on main | The old body cells in `batches.py:259` do not vary with size (the finding of 2026-10-06). |
| Composition crossings (Strike/Line/Siege) | layout spec §2, run 2 | Not started. Needs his category-to-type table. | `compose.py` is the old five-slot rule | No |
| Placed formations, decided by survivors, hold condition | Rev 3, Rev 4 | Not delivered. Only the red test `test_decided_by_survivors.py` exists. `placed_scene`, `decided_by_survivors`, `held` and `hold_ticks` are absent from `scripts/`. | grep on main | No |
| Throughput | throughput_2026-10-06.md | Measured. B9 to B11 deferred. | `throughput_2026-10-06.md` | Run 1 estimate is about 68 min. |

**Does run 1's score answer "which layouts induce strategic depth"?**
- The smoke gains are negative or null for most skills. Layout 0 scores 1 with S1, S3, S4 and S5 gains of -1, -1, -3 and -2. Layout 1 scores 0 with every gain null.
- Today's score is measured on walking fights with mop-up, so a stalled approach or a walk can decide the result. That is the thing he objected to on 2026-10-07.
- The score counts skills with gain >= 2 and a working counter. It never measures whether the layout affected the skills.

**Does whole-unit break-even survive placed formations?** The Rev 3/4 spec does not say. It keeps `cell_result` and the 5% margin, and adds "draw within 5%". How "held" counts toward a break-even is stated only as "like a wipe for the defender".

**Does the hold condition change what "skill pays" means?** Yes.
- Only the defender can win by holding, and the attacker plays the naive blob.
- Gain is then a defender-only quantity.
- Counter plays have the roles swapped, so they cannot be compared with the skilled-play gains.

## 3. Drift, ranked

1. **The layout search was built on the mop-up rule**, not on his "place them, don't walk them". The mop-up rule, the enemy-anchor fallback (`a061ce5a`), the quiet window from first damage (`quiet_from_first_damage`, `contract.py:100`) and the objective scene are all lab inventions. Rev 3 supersedes them on paper, but main still runs them.
2. **Rev 3 and Rev 4 are specified and tests are red, but nothing is built.** The roadmap row still says "spec, not approved" and "first run after B9 to B11". ROADMAP:70 and :89 ("run 1 tonight") disagree.
3. **Q-LS-01 to Q-LS-03 are not in the register.** They exist only in the spec. `depth.py:17` comments "Q-LS-01, Westley's", but the value 2 is the Architect's draft.
4. **Q-LAB-01 is marked "open, parked"**, yet the mop-up rule it offers as option (a) is in production. The 2026-10-07 answer only parks it as not for the beta. It does not approve the rule.
5. **The first chart he was promised has not been delivered.** The 2026-10-04 Formation Read was the only chart he saw. The 200-layout charts do not exist.
6. **The composition axis, size sweep and ground lab have quietly fallen out of the near term.** All three were requested, and all three sit behind unscheduled prerequisites.
7. **Quoted rules that do not match what is built:** Rev 3 gives "start distance stays", but the code does not use it as a placed feature. The mop-up note appears on every batch page.
8. **The old A145 "no skilled plays until its batch" ruling was superseded** by the Architect (2026-10-06), not by Westley.

## 4. Constants not set by Westley (main, `scripts/skilllab/`)

| Constant | Value | File:line | Recorded as his? |
|---|---|---|---|
| G (gain threshold) | 2 units | depth.py:17 | Spec says "draft"; Q-LS-01 not in register |
| Enemy headcount range | 8 to 24 | depth.py:18 | Draft |
| WIN_MARGIN | 0.05 | contract.py:156 | No record found |
| max_ticks | 12000 | contract.py:86 | Q-LAB-01 "provisional" |
| stalemate_ticks | 400 | contract.py:87 | No |
| SHIFT_MAX | 10 wu | contract.py:158 | No |
| MOPUP_INTERVAL_TICKS | 200 | plays.py:12 | "Provisional (A199)" |
| mopup MOVED_WU / WINDOW_TICKS | 30 / 200 | mopup.py:8-9 | Provisional |
| START_GAP | 700 | plays_space.py:20 | Draft |
| BAIT_FALLBACK_TICK / CLOSE_TICK | 100 / 150 | plays_space.py:44,46 | Draft |
| BAIT_COUNT / DETACH_COUNT / FRAIL_COUNT / SCREEN_COUNT / HIGH_COUNT | 4 / 2 / 6 / 8 / 8 | plays_space.py:33-49 | Draft |
| CONCAVE_ARC_DEG / SPREAD_SPACING / SCREEN_HP_FACTOR / SCREEN_RANGE_FACTOR / FRAIL_HP_FACTOR / OUTRANGE_FACTOR | 120 / 60 / 2.0 / 1.2 / 0.5 / 1.2 | plays_space.py | Draft |
| FRAIL_BACK | 400 | plays_space.py:51 | Draft |
| Layout feature grid | w 0/2/4/8; r 0/1.5/3; lanes 0/1/2; k 0/2/4; c 0/0.1/0.3; d 1400/2800 | depth.py:21 | Spec says "drafts" |
| CORRIDOR_WIDTH | 600 | maps.py:38 | Provisional |
| UNIT_RADIUS_WU / LAYOUT_BODY_WU | 15 / 30 | maps.py:39-40 | Provisional |
| LAYOUT_WALL_THICK / WALL_HALF / LANE_HALF / LANE_PAST | 90 / 600 / 140 / 400 | maps.py:41-44 | Provisional |
| CORRIDOR_SLICES | 256 | maps.py:45 | Provisional |
| Ping search draft set | REVEAL_MEMORY 200, SWEEP_BEARINGS (-60,-30,0,30,60), SWEEP_RINGS (0.5,1.0), SWEEP_LAYERS 5, CHASE_UNITS 4, SHIFT_EVERY 400, DRIFT_LEG 12000 | search_policies.py:8-14 | Provisional |
| Ping search batch | REACH_TIMES_SIGHT (1.5,2,3), RADII (250,500,1000), COOLDOWNS (100,200,400,800), REVEAL_TICKS 100, FORCE 16, N_PLACEMENTS 60 | search_batch.py:21-27 | Provisional. He gave 5 s reveal and 20 s cooldown. |
| Search scene | CANVAS 12000x12000, SEEKER_START (-3000,0), HIDER_FORCE 16, CAP_TICKS 2400, AHEAD_HALF_ANGLE 75, PLACEMENT_EXTRA 2000 | search.py:14-24 | Provisional |
| Rev 3/4 numbers | 400 blind ticks, 5% draw band, 1200 hold ticks, 300 wu hold radius | spec only | Spec says "Westley's number" |
| Passive cross-layer sight | 0.50 / 0.20 / 0 | Q-005-07 | His answer: "A, architect decision. Should be close to what it was for the python version." |

## 5. Waiting on

- The Rev 3/4 build is not scheduled: `placed_scene`, the `decided` and `held` outcomes, and the five-feature `lhs_draw`. The red test is the only artifact.
- B1 and B2 are in main, and B9 to B11 are deferred. Run 1 is pinned to a night slot (throughput note, 2026-10-07).
- Westley's decisions on the 400-tick blind window, the 5% draw band, G, the 1,200-tick hold, and the Q-LS-01 to Q-LS-03 rows.
- The category-to-type table for Strike, Line and Siege, which run 2 needs. Q-081-01 is closed and covers a different matter.
- D1, the unit-size runtime piece, is a spec only.
- The ground lab has no spec.
- No programme item blocks the lab directly. Lab run and gate use compete for CPU (8 workers by day, 12 at night), and the lab shares `csrc/tactical_move.c` with the D1 piece.
