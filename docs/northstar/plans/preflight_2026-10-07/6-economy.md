Superseded 2026-10-09: the E-22 flags listed as open below were closed by Westley's batches 13 to 22; the register is the source.

# Pre-flight scout 6-economy (2026-10-07, Sonnet, read-only)

Scout 6 report. All figures are from origin/main at fetch time, and the worktree is removed. The headline: the brief's premise does not hold. Batches 1 to 12 settled none of the economy numbers.

## 0. Headline

- All 40 E-22 flags, Q-167-01 to Q-181-02 (including Q-177-05), are `open` in `docs/northstar/ambiguity_register.md`.
- The carried flags Q-159-07, -08, -09, -10, -12 and -13 are also open.
- ROADMAP lines 186, 245 and 246 agree.
  - Line 186: "An ordered answer sheet is not yet drafted."
  - Line 245: the economy rules instrument is "needed, none exists".
  - Line 246: the economy look mockup is "needed, none exists".
- E-22's own gate verdict is "not passed" (E-22:14), and CLAUDE.md says an epic with an open flag is not built.
- What Westley decided on 2026-10-01 and 10-02 are the mechanisms, already folded into E-22's 83 rules. The costs, times, caps, yields, lot rule, building set, resources and doctrines are all unset.
- Batches 9 to 12 (commits a3d15377, b928b937, 594952ae/464c2505, 829f2444) covered lockstep, flow, settlements, strongpoints and weather. Only the settlement and strongpoint/weather rows serve lane E.

## 1. The answered record

Rules cited in brackets are what the answer folded into.

**E-22 mechanism decisions (2026-10-01 and 10-02)**
- **Q-159-01**: the economy is "(d), a combination built on a classic base" (Age of Empires Online and Age of Empires 3). It is folded into E-22 S-167 to S-181.
- **Q-159-02** (verbatim): "A3, player can change it on the fly... B3 C2+4 D2+3... E1+3". It gives named doctrines, perfect hands, no foresight, one dial, and a counter shift that can be switched off [R-179-03/05/06, R-180-*, R-181-03].
- **Q-159-03**: "C2+4". The solo commander has the dial and points; he does not place buildings [R-180-04]. In the paired mode the economy player places buildings anywhere [R-168-01].
- **Q-159-04**: "Yes grows during mission" [R-179-02, R-193-07].
- **Q-159-05**: a small APM benefit, "1.1 or 1.2x". It is still unbound, and the exact bound is set under Q-159-01 [no rule].
- **Q-159-06**: "not necessarily" a city, but every side has a base of operations [R-177-01].
- **Q-159-11** (verbatim): "A3+5, but at the point they've lost their original main base it's partial failure at maximum. B1+2" [R-178-01/04/06/07, R-212-01, R-210-02].
- **Q-159-14**: "keep" (supply distance) [R-177-03].
- **Q-210-01**: the archetype-to-base table "looks good, no changes needed" [E-22 S-177 table, R-210-02].
- **Q-192-05**: "build both with a switch" for raid lanes, generator-output and route-grid [E-17 S-192]. How a side sees the lanes (Q-174-01) stays open.
- **Q-238-02**: "your side can't see its own shipment, no vision at all, no indication it was killed" [R-176-02/03, R-238-02].
- **Q-166-01 and Q-166-03**: settlement generation, height bands, and natural paths through dense districts [R-166-01 to -06, R-193-09].
- **Q-207-01**: "(a), a building blocks from placement" [E-13 R-207-*].
- **Q-214-01**: "9: b", enemy force and resources scale in step with the number of pairs [R-214-03/04].

**E-17 settlements (batch 11, 2026-10-06)**
- **Q-193-01**: "b". Wave events are a shipment arriving, an expansion founded, a season turning, a capture and a battle's end [R-193-04].
- **Q-193-02**: "a with your recommendations". There are five stages: empty, staked, scaffold, small, large [R-193-05]. The density thresholds are drafted in the prototype and approved by him (Q-191-05 item 5).
- **Q-193-03**: "b". Openings in rock are cosmetic only [R-193-02].
- **Q-193-06**: "a". The generator leaves open streets along contours and rivers [R-193-09].
- **Q-222-01**: "a for now". Density reads only the region's economy and the mission clock [E-02/E-07].
- **Q-193-04 and Q-193-05**: parked ("park", "park as well, we'll run fights in the simulation"). Density slowdown and cover stay out [R-193-08].

**E-15 strongpoints and weather (batch 12, 2026-10-06)**
- **Q-218-01**: already answered by Q-192-01(b). The count is R-126-01's, capped by the slopes there are [R-218-01].
- **Q-218-02**: "a". Holding gives a position to fight from and production, nothing more [R-218-02].
- **Q-218-03**: "c". A strongpoint falls to rubble and can be refounded [R-218-05, replacing R-127-03].
- **Q-218-04**: "b". The 0.20/0.80 force split is dropped and the situation decides [R-218-06].
- **Q-218-06**: "c". The name is "strongpoint" for the mechanic, with an era-skinned visual [R-218-08].
- **Q-219-01**: "b". The troubles are a small fixed list [R-219-01].
- **Q-219-03**: "c". What "shut down" means differs per trouble [R-219-04].

**E-10 and E-16, closed or merged**
- Q-234-01 and Q-240-01 were closed in batch 10. They are a zoom and screen matter (E-16 S-234), not economy.
- The merge rows Q-210-02, Q-210-05, Q-211-01, Q-212-01/02/03 and Q-213-01 are not answers. They point at E-22 flags that are still open: Q-177-01, Q-191-04, Q-177-02, Q-178-05, Q-178-04, Q-178-02 and Q-173-01.

**E-13 workers and E-07**
- E-13 S-209 has no flags.
- E-07 only picked up the Q-222-01 fold. Nothing else.

**Two inconsistencies**
- The approved settlement mockup has four stages plus rubble (thresholds 0.10, 0.22, 0.38, 0.58). R-193-05 says five stages (empty, staked, scaffold, small, large). The mockup needs a delta, and the thresholds still go to Westley.
- Q-237-01 (how many lot stages) is still `open` in the register, although Q-193-02 effectively answers it. The register row is stale.

## 2. Still-open rows, with candidates and my small/design marking

I read the 5% rule as: small means a tuning number or a name that can be re-set later with no change to what a rule means. Design-level means the answer changes what a rule means, or a pass mark or tolerance.

**Small (Architect liberty, document in the spec's "Liberties taken" table and the register)**
- **Q-167-01** worker time, cost and load: (c) set in the lab.
- **Q-167-02** yield falloff with distance: (c) set in the lab, or (a) a straight fall per distance.
- **Q-167-03** workers outside the roster: (b) a separate list outside the roster.
- **Q-168-03** construction: (a) workers build, with a resource cost. The "who builds" half is borderline.
- **Q-169-01** population weight: (a) one unit, one point, plus a starting cap and a ceiling.
- **Q-170-01/02/03** production timings: (c) set in the lab, flat change time.
- **Q-173-01/02** tech formula and levels: (a) one step, (a) five levels.
- **Q-174-02** wall, gate and tower stats: (a) wall blocks, gate blocks and opens for its owner, tower fires.
- **Q-179-02** habit weights: (a) a short fixed list.
- **Q-180-01** the dial's form: (a) three positions per axis, or (b) a slider. Borderline small.
- **Q-235-01**: (a) only the four named ticker beats.
- **Q-237-01**: superseded by Q-193-02, so close it as a stale row.
- **Q-193-02's** density thresholds, and **Q-191-05 item 5**: the Architect drafts them and Westley approves with the product, which is his own option (a).

**Design-level (needs Westley)**
- **Q-159-08**: the three resources and which role needs which. It blocks every cost and counter, and so S-167, S-170, S-171 and the tests.
- **Q-168-01**: what a lot is, and how limited lots meet free placement (candidates a, b, c).
- **Q-168-02** adjacency yield, **Q-168-04** the building set per era, **Q-159-12** what technology does.
- **Q-159-09, Q-172-01, Q-171-01, Q-238-01**: disguise and reveal.
- **Q-174-01** lane visibility.
- **Q-175-01/02/03**: expansion and forward-works rules.
- **Q-176-01/02**: shipments. A shipment that is a unit would break its blindness against E-12 R-089-05.
- **Q-177-01 to -05** base kinds and supply distance, **Q-178-01 to -05** occupation and fall-back, **Q-211-02/03** and **Q-212-04/05** (mission-side effects).
- **Q-179-01** the doctrine list and first doctrine.
- **Q-180-02/03/04** request kinds, unit mix per archetype, and switch timing.
- **Q-181-01/02**: the enemy economy's fog and foresight.
- **Q-159-07 and Q-159-13**: carry-forward and damage persistence.
- **Q-159-10**: picks among offered pieces.
- **Q-226-01/02**: whether the faction's budget sets the economy.
- **Q-219-02** weather path (to be designed; he prefers the player not see it coming), and **Q-219-04** (parked).
- **Q-193-04/05** (parked).
- **Q-118-03**: whether a strongpoint may drift. It touches R-130-01, so I mark it design-level.
- **Q-210-03/04/06**, **Q-214-02**.
- **E-16 layout Qs**: Q-230-01/02/03, Q-231-01/02/03, Q-233-01.
- **Q-217-01** (E-14): how economy orders enter the command vocabulary and the replay stream. It is a contract-level choice.

## 3. The stories

All E-22 stories read "Design decided ... not scheduled" in `stories.md`, except S-182, which reads "Open". The rule counts below come from the epic files. "Refs Q" is the number of rules that mention a Q tag in their line, not the number of open flags.

| Story | Rules | Refs Q | Status |
|---|---|---|---|
| S-167 | 4 | 4 | not scheduled |
| S-168 | 5 | 4 | not scheduled |
| S-169 | 4 | 1 | not scheduled |
| S-170 | 6 | 3 | not scheduled |
| S-171 | 4 | 2 | not scheduled |
| S-172 | 3 | 2 | not scheduled |
| S-173 | 5 | 3 | decided in part, not scheduled |
| S-174 | 5 | 2 | not scheduled |
| S-175 | 4 | 3 | not scheduled |
| S-176 | 4 | 1 | not scheduled |
| S-177 | 10 | 5 | not scheduled |
| S-178 | 7 | 5 | not scheduled |
| S-179 | 6 | 2 | not scheduled |
| S-180 | 7 | 4 | not scheduled |
| S-181 | 5 | 2 | not scheduled |
| S-182 | 4 | 3 | Open |

- The E-22 total is 83 rules, 46 of which reference a Q tag.
- **S-209** (E-13): 2 rules, 0 Q. Design decided, not scheduled.
- **S-210** (E-10): 4 rules, 3 Q. **S-211**: 4 rules, 3 Q. **S-212**: 7 rules, 5 Q. **S-213**: 3 rules, 1 Q (decided in part). **S-214**: 4 rules, 1 Q.
- **S-230** (E-16): 6 rules, 2 Q. **S-231**: 5 rules, 2 Q. **S-232** (ping, out of lane E): 5 rules, 4 Q, Spec'd and blocked. **S-233**: 3 rules, 1 Q. **S-234** (zoom, out of lane E): 4 rules, 0 Q, Spec'd. **S-235**: 4 rules, 1 Q.
- **S-236** (E-18, land ground, outside this lane's list): 3 rules, 1 Q.
- **S-237** (E-18): 5 rules, 1 Q (Q-237-01, effectively superseded). **S-238**: 4 rules, 1 Q (Q-238-01).
- **S-210 to S-214, S-230, S-231, S-233, S-235 to S-238** are all "Design decided 2026-10-02, not scheduled".
- Strongpoints and weather, for reference: S-218 has 8 rules (1 Q, Q-118-03) and S-219 has 6 rules (2 Q). Both are decided apart from those. S-193 (settlements) has 9 rules (2 Q, parked).

## 4. The sim today

**Structures**
- `csrc/mission.c:2373` `om_mission_place_structures` fills 64 slots at mission setup (`OM_MISSION_STRUCTURE_SLOTS`). It uses R-126-01 count and owner split and lays them along the spine at a fixed lateral fraction. It does not use slopes, so strongpoints (R-218-01) do not exist.
- State lives in `csrc/tactical_support.c`: `om_sup_structure`, `OM_SUP_MAX_STRUCTURES = 64`.
- `om_support_tick` (`tactical_support.c:907`) is called from `unit.c:2261` and `unit.c:2552`, on the tactical tick. It runs the capture census and accrual and `om_sup_structure_tick_production_driver`. Production spawns via `om_unit_spawn` on a 30 s × power/100 timer.
- `om_structure_unit_cost` returns 0 (R-126-06, "units have no cost").
- Capture, damage, the destroy-and-never-rebuild behaviour (R-127-03), owner switching and drift all exist.
- `om_structure_hud` is the only structure output struct: `timer_progress`, `next_unit_type`, `hp`, `max_hp`.

**What does not exist**
- None of these have a symbol in `csrc/`: worker units, gathering, resources, lots, construction stages, population cap, doctrine and dial, shipments, lanes, walls, gates, towers, expansions, base kinds, occupation, technology effects and weather.
- Terrain slopes do exist (`om_terrain_slope_*`, `terrain.c`).
- `om_mapgen_cell_set_density` is obstacle density, not settlement density.
- `om_hazard_spawn_moving_interference` exists, but it has no callers in `mission.c`, `unit.c` or the pipe.
- `om_unit_spawn_non_combat` exists (convoys).
- `enemy_macro.c` budgets are the strategic E-05 faction budgets (`faction_budget`). There is no mission economy.

**The pipe**
- The `tactical` frame (`architecture.md:258`) carries `units`, `visible`, `objectives` and `map.{nodes,cover,obstacles}`. It carries no structures, workers, resources or lots.
- `place_structure` (`architecture.md:251`, `csrc/pipe/om_pipe.c:1922`) is a debug-only verb behind `OM_DEBUG_INJECT`, capped at 64.
- `om_client_snapshot` is `{unit_count, units[256]}` of `{id, faction_id}`.
- The `terrain_*` verbs return bands, walkable cells and slopes.
- There is no economy verb or frame. A pipe contract piece is needed first.

**The client**
- `scenes/` and `autoload/` hits on "economy" are the region field. There is no `scenes/economy*`.
- `scenes/mockups/hud/hud.gd` was matched by the grep but has no economy panel (my grep for econom, worker, resource, doctrine and dial in it found nothing).
- The only economy-adjacent code is `scenes/mockups/settlement/`.

**Tests**
- `tests/csim` has `test_E02_S014_economy.py` (region economy) and `test_E15_S131_reading_hazards_and_structures.py`.
- No test names S-167 to S-182.

## 5. The settlement mockup

- **Size**: 1,111 lines (`settlement_mockup.gd` 466, `settlement_sim.gd` 633, plus a `.tscn`). The brief says 1,099.
- **Record**: `docs/northstar/research/settlement_mockup/README.md`. Westley's verbatim approval on 2026-10-06 was "Settlements mockup approved". It covers the look of pass 1; "every number is a CANDIDATE".
- **Inputs**
  - A 121×121 window of 100 wu cells cut from `FieldMap` (`scenes/mockups/landscape/field_map.gd`, seed 11, read-only, core = `nodes[0]`). The elevation, slope and water per cell feed `setup()` (`settlement_sim.gd:71`).
  - Four lot stages: marked, scaffold, built, dense, plus rubble.
  - A density potential spreading one ring per 3 s tick (decay, climb, steepness and water terms), eased toward P × maturity.
  - An every-fourth-row lane grid with per-cell jitter.
  - Waves: shipment, expansion and season.
  - Placement of a 5×5 building with a 2-cell refill ring.
  - Damage: stages run back to rubble, rebuild after 10 s.
  - Cliff dwellings above slope 0.22, capped at 3 stages.
  - Dijkstra paths to 8 sectors.
- **What it lacks**: workers, resources, buildings with roles and strongpoints. It draws placeholder boxes with no economy input.
- **Port fit**
  - The mockup's density, lots and stages are in GDScript on the mockup's own `FieldMap`.
  - R-193-08 puts the density field in the simulation. The sim has terrain bands, slopes and walkability to read.
  - The stage count differs (4 versus the ruled 5).
  - The five questions in the README are answered by batch 11 in the register.

## 6. The piece list for lane E

The size, in units (one Doer unit is about one file and under about 100 lines), is my estimate.

**Contract pieces first**
1. **Structure and economy frame contract**: structures, workers and lots in the tactical frame, plus a signatures delta. This is a contract change that lands alone, 1 unit. It needs the pipe shape, not the numbers.
2. **Economy command verbs** (place, schedule, focus, request, dial, doctrine): the contract, 1 unit. This is blocked by Q-217-01 (design-level).

**Sim pieces**
3. **Density field and lot stages (R-193-01/05/06)**: a new file reading terrain bands, slopes and water. About 3 units. It can start on liberties (Q-193-02 and thresholds by Q-191-05 option (a)) but the numbers still go to Westley.
4. **Wave events and rubble and rebuild**: 2 units. Q-193-01 is answered.
5. **Placement and footprint clearing (R-193-03, R-168-01)**: 2 units. Blocked by Q-168-01.
6. **Workers as units** (non-combat spawn, gather, return, yield by distance; S-167, S-209): 3 to 4 units. The mechanism is decided, and the numbers are liberties (Q-167-01/02/03). It is blocked by Q-159-08 (resources). A placeholder single-resource model would be a liberty, but it is not what R-167-01 asks for.
7. **Resources, cost and population cap (S-169, S-170 cost)**: 2 units. Blocked by Q-159-08.
8. **Production schedule and focus (S-170)**: 3 units. Timings are liberties. It is blocked by Q-159-08 for costs.
9. **Strongpoints on slopes (S-218)**: 2 units, plus the rubble and refound change to R-127-03. It can run now, since the rows are closed apart from Q-118-03.
10. **Weather troubles (S-219)**: 2 to 3 units. The path and speed are open (Q-219-02), so it is blocked on a design, with a possible interim liberty for a straight-line mover.
11. **Rules economy and doctrine (S-179 to S-181)**: 4 to 5 units. Blocked by Q-179-01, Q-180-02/03/04 and Q-181-01/02.
12. **Bases, expansions, occupation, fall-back (S-175, S-177, S-178, S-210 to S-212)**: 5 to 6 units. Blocked by about 15 design-level flags.
13. **Shipments and lanes (S-174, S-176)**: 3 units. Blocked by Q-176-01/02 and Q-174-01.
14. **Disguise (S-172)**: 2 units. Blocked by Q-159-09.
15. **Tech effects (S-173)**: 2 units. Blocked by Q-159-12.

**Client pieces (after lane A, the battle screen)**
16. **Settlement renderer** (port the mockup onto sim lots; stage rise; cliff dwellings): 3 to 4 units, plus a delta for 5 stages versus 4. Depends on piece 3.
17. **Workers drawn, resource carry, the sources** (S-238): 2 to 3 units. Depends on piece 6.
18. **Placement UI and yield preview (S-230 R-230-02)**: 2 units. Depends on pieces 5 and 1.
19. **Economy screen S-230**: 4 units, and Q-230-01 (layout) is design-level.
20. **Solo dial, doctrine and unit-mix panel S-231, S-233**: 3 units, blocked by Q-231-01/02, Q-233-01 and Q-180-01.
21. **Map markers and ticker (S-235)**: 2 units. Q-235-01 is a small liberty.
22. **Weather and strongpoint drawing (S-238, S-218 R-218-08)**: 2 units.

**Tests per piece** follow the rule that failing, fenced tests come first. Each story needs at least one isolation test and one integration test and a positive control for each detector. That is about one test file per piece, with the sim pieces in `tests/csim/`, the frame in `tests/transport/`, and the client in `tests/qa/`.

**Shape of the lane**
- **Can run now on liberties** (about 15 to 20 units): contract 1, density and lots 3, waves 4, strongpoints 9, the settlement renderer 16, and the smaller client pieces 21 and 22.
- **Blocked until Westley** (about 40 or more units): the three resources (Q-159-08), lots (Q-168-01), shipments, bases and occupation, the doctrine list, the disguise set, what technology does, and the screen layout.
- The programme's estimate of 12 to 16 units (plus 2 contracts) fits only the first group.
