# Duplicate flags audit, 2026-10-02

Scope: the open rows of `docs/northstar/ambiguity_register.md` in the id ranges named in the brief (177 open rows found by id filter; the brief said about 173). Read-only: nothing in the register or the epics was changed. "Duplicate" means one answer from Westley would close both flags. A flag that asks two things and overlaps another on only one of them is not folded; it is listed under "related, keep both" with the overlap named.

Keep rule used: the flag in the epic that owns the mechanism (E-22 economy rules, E-17 terrain and placement, E-01 layers, E-11 unit statistics, E-16 controls and screens, E-18 drawing, E-19 wire, E-10 mission setup). Where none of those apply the reason is stated.

## 1. Duplicate groups

| Group | Keep (id, epic/story) | Fold into it (ids, epic/story each) | The one question, in a sentence | Why they are the same |
|---|---|---|---|---|
| D1 | Q-178-05, E-22 / S-178 (E-22 owns base-loss rules) | Q-212-01, E-10 / S-212 | If a side retakes its original main base, does the partial-failure cap lift? | Word-for-word the same question; candidates are the same three-way (stays / lifts on holding at end / lifts on retaking). |
| D2 | Q-178-04, E-22 / S-178 (E-22 owns base-loss rules) | Q-212-02, E-10 / S-212 (also tagged E-14 S-216) | A side with no base and no expansion or forward base to fall back to: does the mission end at once, or go on cut off? | Same question, same candidates (end and score / go on cut off / by archetype). |
| D3 | Q-178-02, E-22 / S-178 (E-22 owns base-loss rules) | Q-212-03, E-10 / S-212 (S-078) | Does the holder of the base at mission end decide the region transfer, replacing the "Region transfers to player on" column of E-10 R-073-01/R-078-04, or does the column stay? | Same collision between the base holder and the transfer column; the three candidates match one for one. |
| D4 | Q-173-01, E-22 / S-173 (E-22 owns the economy and technology rule) | Q-213-01, E-10 / S-213; Q-227-01, E-06 / S-227 | By what formula is a mission's starting technology derived "only slightly" from the faction's technology level? | All three quote the same decision (2026-10-02, "only slightly") and ask for the same formula; Q-227-01's own candidate (c) defers to Q-159-12. Q-213-01 also mentions mapping to era levels, but that is the output side of the same formula. |
| D5 | Q-118-03, E-17 / S-118 (E-17 owns placement and drift of map nodes) | Q-218-05, E-15 / S-218 (S-130) | May a strongpoint drift as an objective does? | Same yes/no on drift; "no" closes both, and "yes" leaves only the path rule, which R-118-01 already carries. |
| D6 | Q-192-01, E-17 / S-192 (E-17 owns placement) | Q-218-01, E-15 / S-218 (E-15 S-126) | How many strongpoints does a map have, on which slopes, when the fitted relief gives few or many band slopes, and does R-126-01's count still apply? | Both ask for the strongpoint count and placement against the relief; both offer "the E-15 count, capped or placed on the slopes there are". The "starting owners" in Q-218-01 is the R-126-01 archetype split, which Q-218-04 also asks about; see related table. |
| D7 | Q-177-01, E-22 / S-177 (E-22 owns the base rule) | Q-210-02, E-10 / S-210 | How do the archetype and the supply distance together decide a side's base kind? | Identical question; candidates (a) match (archetype gives the kind, supply distance gives the supply). |
| D8 | Q-177-04, E-22 / S-177 (E-22 owns the rule; the flag also carries the "what a pair shares" half, see related table) | Q-241-01, E-19 / S-241; Q-214-01, E-10 / S-214 | How much more resource, and how many more enemies, does a 4 to 6 player match bring (in proportion to players, in steps, or set by the simulation)? | All three ask the scaling of resources and enemy force by player count; the candidate sets are the same (in step with players or pairs / fixed steps / set by the situation). |
| D9 | Q-177-02, E-22 / S-177 (E-22 owns the economy situation) | Q-211-01, E-10 / S-211 | Which simulation values decide a mission's limited or abundant resources and its slant to the defender, and how big is the slant? | Both ask for the derivation of the same three numbers (richness, limited or abundant, defender slant) from the region; candidates are new region fields vs derived from existing fields vs per archetype. |
| D10 | Q-191-04, E-17 / S-191 (E-17 owns terrain-first generation) | Q-210-05, E-10 / S-073, S-210 | With no skeleton library, what does the archetype decide on a terrain-first map and what does the terrain decide? | Same question after Q-119-02 closes; both cite R-073-03. Candidates are the same three (objective, base kinds and roles only / adds conditions the generator must meet / biases landform or site weights). E-10 R-073 text itself points at Q-191-04. |
| D11 | Q-174-02, E-22 / S-174 (also E-11) | Q-207-02, E-13 / S-207 (R-207-04) | What do a wall, a gate and a tower do, and in particular how does a gate pass units? | R-207-04 asks only how a gate treats own and enemy units and whether it opens; Q-174-02 asks what each of wall, gate and tower does. Q-207-02's own candidate (c) is "set with Q-174-02", and any answer to Q-174-02 settles it. |
| D12 | Q-240-01, E-18 / S-240 (E-18 owns the draw budget; the E-16 flag is the screen-side restatement) | Q-234-02, E-16 | What are the client budgets (fps and counts) for thousands of units, workers and buildings, given E-16 says 60 fps at 1,000 and E-18 says a 30 fps floor at 1,000? | Both ask Westley for the same client budget numbers; Q-234-02's candidate (c) points to Q-240-01. The "do workers count among the 1,000" part is one of the numbers Q-240-01 asks for. |
| D13 | Q-193-02, E-17 / S-193 (E-17 owns the growth and placement rule) | Q-237-01, E-18 / S-237 | How many stages does a lot rise through? | Same count question (three vs five vs per kit/era pack). What each stage looks like follows from the stage names Q-193-02 will fix. Caveat: Q-237-01 also says "and what does each look like"; if Westley wants a look per stage decided now, keep Q-237-01 as a drawing flag only. |
| D14 | Q-193-01, E-17 / S-193 (E-17 owns growth waves) | Q-225-02, E-04 / S-225 | Which events start a growth wave: shipment, expansion, season, capture, or other? | Q-225-02 asks only whether "events" in R-166-03 means E-04 strategic events or in-mission events. Any answer to Q-193-01 (a list of in-mission events, or "per era") settles that. Judgement call: if Westley meant E-04 events too, Q-193-01 (c) "set per era" does not give that, so recheck if he answers with a mixed list. |

## 2. Related, keep both

| Ids | What differs |
|---|---|
| Q-210-06, Q-215-01, Q-233-01, Q-181-01, Q-180-04 | All touch where and when the economy settings (doctrine, dial, mix toggles, enemy foresight) are chosen. Not duplicates because each adds a part the others lack: Q-215-01 asks the foresight default, Q-181-01 asks one switch or three and whether difficulty sets it, Q-233-01 asks the screen (Settings, onboarding, mission setup) and whether the starting doctrine is the player's pick, Q-180-04 asks who picks the mix when the rules do not, Q-210-06 asks where E-10 receives them. Answer Q-210-06 first; it would close the "when" half of the rest. |
| Q-241-02, Q-177-04, Q-228-02, Q-214-02 | Pair and team structure. Q-177-04 second half (what a pair shares) and Q-241-02 (is a pair its own sub-civilization with its own economy) overlap on "own economy or shared"; Q-241-02 also asks what a sub-commander is. Q-228-02 asks how a pair maps onto a simulation with one faction. Q-214-02 asks whether a pair has its own objective. Four different mechanisms. |
| Q-174-01, Q-192-05 | Both ask whether the generator outputs raid lanes or they are found from the route grid. Q-174-01 also asks how a side sees its own and the enemy's lanes (a display question). Recommend trimming Q-174-01 to the display half once Q-192-05 is answered. Close to a duplicate. |
| Q-070-02, Q-228-01 | Both ask whether the economy seat and teammates have a place in the lineage and character record. Q-070-02 is the chronicle and the military-rank framing of R-070-03; Q-228-01 is the chapter record, ledger and character selector. Answering Q-228-01 (a) makes Q-070-02 (a) very likely but does not state it. |
| Q-191-03, Q-211-03 | "Opposite the objective" measure (E-17) vs where the objective sits against each side's base per archetype (E-10). Q-211-03 candidate (a) may carry the measure; check when answering. |
| Q-159-12, Q-173-02, Q-227-03, Q-226-01 | Technology: what it does; how many levels and their cost; how the three tiers relate to the levels; whether the faction's budget or tier sets a mission's economy. Different questions. |
| Q-220-01, Q-068-03, Q-159-07, Q-159-13 | What a mission leaves behind (region record, time-jump log, carried-forward items, base damage). Q-220-01 answer (a) or (c) would largely force Q-068-03, but each asks about a different record. |
| Q-220-02, Q-177-03 | Where a contested populace ends up in the simulation vs what winning it means in the mission. |
| Q-166-02 with Q-236-01, Q-150-02, Q-219-01 | Q-166-02 (space landscape, "to be designed") is a dependency of the others; its answer does not settle them. |
| Q-146-02, Q-243-01, Q-244-01 | Names and mechanics per era; whether doctrine name and parameters are pack or config; whether names are generated or hand-authored. Three different axes. |
| Q-168-04, Q-133-01, Q-244-01 | Which building kinds an era has (rules) vs how many building pieces the pack draws vs who authors the names. |
| Q-167-01, Q-167-03, Q-154-01, Q-236-02, Q-201-01, Q-170-03 | Worker and unit numbers: training time and cost; statistics and roster membership; names; polygon budget; land-era roster; build time per unit. Same subject, different facets. |
| Q-231-02, Q-180-02, Q-180-04 | Overlap on "what the screen or ticker shows when the rules cannot carry out a request", but one is the rule (E-22) and one is the display (E-16). |
| Q-230-03, Q-171-01 | Line on enemy-composition readouts vs what shows heavy gathering. |
| Q-007-01, Q-162-01, Q-091-01, Q-163-01, Q-166-04 | Cross-layer sight and fire: cover between layers, ping vs cover, elevation tiers vs layers, the emitter's own layer, scaling with step height. Each a separate rule. |
| Q-159-09, Q-172-01, Q-238-01 | How a building is hidden and at what cost; what a seen building reveals; how a hidden building is drawn (E-18 depends on Q-159-09). |
| Q-215-02, Q-179-01, Q-226-02, Q-180-03 | Which doctrine and unit mix: enemy doctrine and ratio; first doctrine of the player; link from the faction's archetype; mix per mission archetype. |
| Q-181-02, Q-215-03, Q-216-03 | Fog limits on enemy economy scouting; foresight vs multi-layer intelligence; raids needing foresight. |
| Q-215-04, Q-242-03 | Macro evaluation budget with an enemy economy vs per-tick and checksum cost of a 6-player team. Different budgets. |
| Q-218-01, Q-218-04 | Strongpoint count (folded into Q-192-01, D6) vs whether the R-126-04 split (one fifth at start) survives. |
| Q-192-03, Q-189-01 | Vantage reachable by walking vs walking routes between bases, objective and bands. |
| Q-188-01, Q-189-02, Q-188-02, Q-195-01, Q-195-02 | Meadow-slope threshold; steepness limit; relief on small canvases; largest canvas; modifier at 64,000 wu. |
| Q-204-01, Q-190-01, Q-193-03 | Layers a structure occupies; height of generated cover; building inside a cliff in the mask. |
| Q-216-01, Q-216-02 | Enemy economy behaviours vs who decides expansion site and time. |
| Q-153-02, Q-180-03 | Where an archetype's base kind and mix are stored (E-21 library vs config) vs what the mix is. |
| Q-221-02, Q-219-01 | Empty regions' climate vs which troubles exist. |
| Q-235-01, Q-231-02, Q-193-01 | Ticker events vs mix acknowledgement vs growth-wave events. |
| Q-193-04, Q-193-05, Q-193-06, Q-222-01 | Dense-district slow, cover and paths vs the density target inputs. Four separate numbers or rules. |
| Q-176-01, Q-176-02, Q-216-03 | Shipment contents and call-in; whether a shipment is a unit; raiding on shipments. |
| Q-168-01, Q-193-02 | What a lot is and where buildings may stand vs how many stages it rises through. |
| Q-210-04, Q-210-06 | Both end at S-079's controls; one is what the briefing states, the other is where settings are chosen. |
| Q-186-01, Q-224-01 | Generation budgets for the map generator vs for world generation at 400 regions. |
| Q-234-01, Q-103-05 | Sand Table as the same drawing or separate; decided by the prototype. |

## 3. Count

- Open flags examined: 177 (id filter on the brief's ranges; the brief estimated about 173).
- Duplicate groups found: 14 (D1 to D14).
- Flags that would be folded: 16 (D1 1, D2 1, D3 1, D4 2, D5 1, D6 1, D7 1, D8 2, D9 1, D10 1, D11 1, D12 1, D13 1, D14 1).
- Net open flags after folding: 161.

## 4. Could not judge

- D13 and D14 rest on a reading of the flag text, not on the rule text in E-18 R-237 or E-04 R-225; both carry a stated caveat.
- D6: whether "starting owners" in Q-218-01 is fully the R-126-01 archetype split was inferred from the flag; if it is a separate ask, Q-218-01 should stay and be trimmed.
- D8 keeper is compound (scaling plus what a pair shares); if the second half is split off, it joins the pair group in the related table.
- Q-231-03 (hub principle 6 fit) is already marked by the auditor as unjudgeable; it has no sibling and is untouched.
- Q-177-05 was read from the register; the E-22 epic says the sidecar holds it until the register takes it, so sidecar candidates may differ. The sidecars (`sidecar_e17.md`, `sidecar_answers2.md`) were not read.
- Candidate lists were truncated by tooling for none of the rows; epics were read only for R-070-03, R-228-01, R-207-04, R-174, R-191, R-211, R-180, R-172.
