<!-- Round-2 fresh Sonnet audit of Lane U rev 2 (REJECT, 10 must-fixes) and HARNESS-coverage rev 2 (accept with nits); all applied in rev 3. -->

# Audit round 2: Lane U rev 2, Lane M, HARNESS-coverage rev 2 (fresh Sonnet auditor, 2026-10-20)

Base: origin/main dae31954 (read-only worktree ~/Projects/om-push/wt/audit-laneu2). Specs: scratchpad/lane_u_spec_rev2.md, harness_coverage_spec_rev2.md.
Note: main now holds the rev 1 records (20 pieces.toml rows, 3 evidence reports, ledger rows); rev 2 changes must be re-recorded.

## VERDICT: REJECT rev 2 of Lane U/M (10 must-fix). HARNESS-coverage rev 2: ACCEPT with 2 nits (provenance exit 0, build verified).
Round 1 tally: 8 CLOSED, 10 PARTLY, 0 OPEN. Two of rev 2's own new claims are false (U7 "seven archetypes", Lane M paths/qa_state) and one round-1 item (14) was itself wrong.

## The 18 items
| # | Status | Evidence |
|---|---|---|
| 1 | PARTLY | Evidence reports now on main (drift_audits/ holds pipe-gaps.md, client-untested-by-lane.md). spec_provenance on lane_u rev 2: 7 findings, all reason (8) "[B R-..] has no pin" (lines 5,9,11,13,15,17,19), because the tags carry the literal `@PIN`. Reasons 3, 10, 11 clean. Coverage spec: exit 0. |
| 2 | PARTLY | Full R-042-05 quote, Q-042-01 contradiction, "table pair hostile, any other neutral" (diplomacy.c:420-421 confirmed), algorithms.md:160 ("the live game never initializes the table" confirmed) all in. But R-032-04 lives in E-05-faction-agents-and-conflict.md:35, not E-06 (wire owner names E-06 only); algorithms.md:160 also says "A missing pair reads hostile", stale under (a); Q-042-01 is already closed (a) "live at launch" (register row 92), no register row Q-042-02 exists yet. |
| 3 | CLOSED | Recipe now `set_seed` features [0..7] (OM_FEAT_DIPLOMACY=4, ouroboros_sim.h:276; sim.c:311), new_campaign false, `qa_dump_state`; B5 edge stated (B5 still owns diplomacy.c, pieces.toml:79); "210 of 210" gone. |
| 4 | CLOSED | U2 stopped on R-215-05 (E-14 line 123 confirmed). Rows VG-U2-* and U6's depends_on VG-U2-PROD-WIRE are still on main (pieces.toml ~3010-3030, 3124): records step must delete. |
| 5 | PARTLY | R-066-02 weights now right (+0.5/+0.3/+0.1*min(L,5)/+0.8, E-09 line 49). Full-context function exists: om_chronicle_calculate_score (chronicle.c:2096, public, header :1408, flags in, so no signature change). But the data the call sites need is not there: fired[] (om_fired_event, header :684) carries no attached character; chain length is only final after the loop (generational.c:2017-2026); no last-mission-region read in the loop. Spec lists chronicle.c:1669-1673 as edited while the wire goes through :2096; pick one. |
| 6 | PARTLY | R-070-02 now quoted right; diplomacy.c:658 acknowledged. Premise is provably red (see below). Observation is not: attached ids live only in manual-fire records keyed by event id (events.c:39-40, :1107), om_fired_event has no id or attachment field, and U0's `events` key (noise, breaches, last_fired) cannot show a character. |
| 7 | PARTLY | Owner moved off lifecycle.c; R-051-04 quoted exactly (E-07 line 67). But collision.c:172 is not a conquest: it is guarded by `regions[target].faction_id < 0` (collision.c:~165) and sets COLONY_START values: a colonisation of an unowned region. Only resolve.c:479 (ALG-22 conquest, `target->military < 5.0`) is a conquest. checksum_full.c:439 hashes the flag, so the wire moves the trace. |
| 8 | PARTLY | "capture" gone; evaluators :1555/:1575/:1599 and :1252-1259 (hold_zone, eliminate_force only, objectives[0] only) confirmed; `objectives[].progress`, `done` confirmed (pipe_tactical.c:326-343). But "seven archetypes map to destroy/escort" is FALSE: mission.c:421-432 gives four (Siege Breaking, Assault, Interception = destroy; Evacuation = escort); survive is primary for none. architecture.md:285 says so and adds that no live mission marks a designated-target subset or places an extraction point. |
| 9 | CLOSED | U6 stopped with Q-218-08; unit.c has 0 references to "structure"; om_structure_apply_damage only in tactical_support.c. Nit: option (b) "captured only, never shot" sits against R-218-05 "when destroyed it falls to rubble ... refounds" (E-18 line 127). |
| 10 | PARTLY | (a) place not repeated, (b) hold: decision made (remove verb; matches R-096-06 rejecting hold, E-13 line 172), (c) ping om_pipe.c:1594 and net verbs 5,6 cmd_stream.c:252-253, header :293 confirmed, (d) alert dropped. (e) emission cites a header contract, not a rule. (f) 11 mechanisms listed + ping + emission; pipe-gaps.md:195-211 has 16: macro save-state field helpers, per-unit support row and move order, fog save-state helpers are neither listed nor set aside. |
| 11 | PARTLY | Field list now in the spec; owns now include header, signatures.toml, pipe_internal.h, Makefile (:80 PIPE_SRC confirmed; PIPE_DBG_OBJ derives from it); edges stated. But the accessor list is deferred to a scout file (`2026-10-20-u0-accessors.md`) that does not exist, and the table below shows 9 keys with no or mismatched source. `EXPECTED_MODULE` (tests/specfactory/test_signatures_internal.py:33) covers om_internal.h only, not public accessors. |
| 12 | CLOSED | depends_on chain U1>U4>U3>U5>U7>U8 is total and stated as enforced by depends_on; TD-VG-U-n per piece. Side effect: Q-042-02 (Westley) now blocks U4, U3, U5, U7, U8 transitively. |
| 13 | CLOSED | Carve-outs listed with owners. Ledger row FU-U-not-scheduled and TD-VG-U-* do not exist yet (grep of ledger and pieces.toml: none). |
| 14 | PARTLY | world_view fixed: 9 .gd files, 2,881 lines, glob `**`. But scenes/shared/loading_screen.gd and scenes/shared/new_game.gd do not exist: the files are scenes/loading_screen/loading_screen.gd and scenes/new_game/new_game.gd, and BOTH already define qa_state() (:186, :209), as do main_menu, onboarding, debrief, time_jump_sequencer, tactical_view. The "doer adds qa_state()" step is moot (round 1 was wrong here). lane_plays.toml has no lane M, so the gate's lane_plays stage never runs plays/M; pieces.toml VG-M-SKEL still has the top-level glob `world_view/*.gd`. |
| 15 | CLOSED | Copy-the-tree route: no env var exists (conftest.py:22-23 LIB_PATH, :41 make; tests/transport has no conftest). After my build, `make -n` on the copy is a no-op, so conftest's make will not rebuild without coverage. |
| 16 | CLOSED | `make all pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg OPT="-O0 --coverage"` builds in a copy in ~5 s (-j8), 86 .gcno, pipe run wrote .gcda, `gcov -f -j` works. Cites Makefile:19/:36 are really :20/:47 (see cites). |
| 17 | CLOSED | Baseline = first real run on landing sha; audit numbers cross-check only; no -x. |
| 18 | PARTLY | status_check shape OK (reads only; --accept separate), depends_on C4 matches pieces.toml:3196, docstring :4 "Seven checks" confirmed, drift_audit.md in owns. reach_lint IS importable: `build_callgraph(Path("csrc"))` returned 1882 nodes; `resolve_roots(graph, dispatch_names, pipe_rel)`, `reachable_from(graph, roots)`, `dispatch_call_names(pipe_c_text)` (reach_lint.py:219,241,282,302). The spec still leaves the name to the writer and keeps a dead `--json` fallback: name them and drop it. |

## Refutation of rev 2 on its own
Cites (all confirmed unless noted): collision.c:172 exists but is colonisation; resolve.c:479, faction.c:206 (om_region_set_owner definition), chronicle.c:2099-2133 (om_chronicle_calculate_score/context_multiplier), generational.c:2028/:2049 (jump call sites)/:1606-1626 (onboarding load/save/update/validate), mission.c:1252-1259/:1555/:1575/:1599/:422-431/:2177, pipe_tactical.c:337, diplomacy.c:420-421/:658, events.c:1077, sim.c:311, c_bridge.gd:27, Makefile:80/:82-97, conftest.py:41 hold. WRONG: Makefile:19 (is :20, OPT ?= -O2), Makefile:36 (is :47, `all:`), conftest.py:24-25 (is :22-23), faction.c:128 (is the self-cooperative line; the hostile line is :130).
(3) U1 red under (a): worldgen.c:263 sets every pair HOSTILE (self COOPERATIVE); run on the built lib, seeds 1-3 at 80 and 200 regions give 15 factions and stances {0,2} only, no neutral. After om_diplomacy_init: 16 of 105 pairs neutral, none involving the player (Player is hostile to Conqueror, Fortifier, Opportunist by diplomacy.c:62-66; neutral only F-F and O-O). Test is red for the stated reason once U0 exists. After init + 2000 steps one pair changed (8-14 neutral to hostile). Design note for Westley: under (a) the player has no peace partner at launch.
(4) U4: yes. TID_REGIONAL_REVOLT (3, trigger OM_TRIG_PROBABILITY, tier 4, OM_EVENT_TIER_EVT_REGIONAL_REVOLT, om_constants.h:376) and TID_GARRISON_COLLAPSE (0, OM_TRIG_BELOW military, tier 4, :368) fire from the trigger pipeline and attach nothing (events.c attach code only in the manual-fire path :1088-1094). See item 6 for the observation gap. Positive control (Knowledge Lost at diplomacy.c:658) is also unobservable through U0 as specced.
(5) U7: false for "seven" (four) and survive; the frame is right.
(6) U8: om_pipe.c has no onboarding/preference/difficulty key in set_seed (:1062) or mission_start (:1210). Spec's `onboarding {difficulty, rare_archetypes: bool}` is not the struct: om_onboarding_config = {uint32 difficulty; double weights[10]; uint32 rare_marks[10]} (header :1271). Nothing in mission.c reads the onboarding slot; difficulty enters only as an argument to om_mission_compute_difficulty_parity (mission.c:1336). om_mission_set_preference takes (archetype, weight) (mission.c:2177); the spec's `preference` has no weight. mission_start draws the archetype before pool scoring (om_pipe.c ~1258).
(7) Lane M: see item 14. qa_state() defined in 7 non-mockup scenes (list above) and the mockups.
(8) coverage: building works; reach_lint importable (item 18).

## MUST-FIX for rev 3
1. U5: drop collision.c (:172 is colonisation); wire only at resolve.c:479 (or om_region_set_owner when cause is conquest); note checksum_full.c:439 / trace move; owner rows for the true site.
2. U7: say four archetypes; survive has none (drop its test or find a live archetype); designated targets and extraction point do not exist (architecture.md:285), so the wire is a design, not "call the evaluators": add a Q- row or restrict to what state supplies.
3. U8: match om_onboarding_config (weights[10], rare_marks[10]) or change the contract on purpose; define how an onboarding slot reaches the pool (nothing reads it); add the preference weight; say where in mission_start the key is applied.
4. U4/U3 data path: where attached ids are stored and read for pipeline events (no event id in om_fired_event); a header change makes it a contract piece. U3 needs attached ids, chain length, mission region at the jump call sites.
5. U0: put the per-key accessor table in the spec (below); resolve the 9 keys with no source or a mismatched shape (waves, rivals, jump.interrupted, force.progression_level, macro.script_state/ambush_hold, structures.refound, betrayal flag, consequence_target, revolt_flag, fog counts); drop the EXPECTED_MODULE claim.
6. Lane M: correct paths to scenes/loading_screen/ and scenes/new_game/, delete the qa_state doer step; add lane M to scripts/specfactory/lane_plays.toml (owner row) and fix the VG-M-SKEL glob to `world_view/**`.
7. U1: R-032-04 edit target is E-05-faction-agents-and-conflict.md:35 (owner row); add algorithms.md to the wire row (pieces.toml row lacks it); decide whether Q-042-02 is really new given Q-042-01 closed (a).
8. Provenance: replace `@PIN` by real pins (run rule_pins) so reason 8 stops firing on 7 tags.
9. U-PIPE-TESTS: list or set aside the 3 missing mechanisms; emission cites a rule or goes to a Q- row.
10. Fix cites: Makefile:20 and :47, conftest.py:22-23, faction.c:130 (hostile line).

## SHOULD-FIX
- Chain order makes the Westley question gate five pieces; put U1 last or break the edge from U4.
- Remove stale rev 1 rows (VG-U2-*, VG-U6 edge to U2, VG-M-SKEL glob) in the records step; write FU-U-not-scheduled and TD-VG-U-n ledger rows before citing.
- Q-218-08 option (b) vs R-218-05 wording.
- `inject`-forced scenarios (U4, U5) need the dbg pipe binary (OM_DEBUG_INJECT).
- 22 unobservable mechanisms vs dump keys: lineage-event classification, absorption/reversion/revolt records, event template library, macro timers/thresholds, structure capture have no key.

## U0 accessor table (public csrc/ouroboros_sim.h today)
| Key | Accessor that exists today | Gap |
|---|---|---|
| diplomacy.stances | om_faction_count (:314), om_faction_stance(w, from, toward) (:319) | enum-name map in pipe code only |
| diplomacy.counters (peace counter) | om_faction_stance_counter(w, a, b) (:1488) | betrayal flag: no state or accessor (betrayal fires instantly, diplomacy.c:213); add one or drop |
| characters | om_character_count (:1644), om_character_id_at (:1653), om_character_get_record (:1650: id, name[32], faction, rank, status, lineage_id) | none |
| lineages.members | om_lineage_count (:1680), om_lineage_id_at (:1686), om_character_lineage_id (:1656) | derive by scan |
| lineages.descendants | record parent_id, generation, n_children | derive by scan |
| rivals {faction, nemesis_faction} | om_character_has_rival_tag (:1652), n_rival_tags, om_selector_get_nemesis_candidate (:1718) | rivals are character-level; no faction-to-faction accessor; define the key from characters or add one |
| player.collapsed | om_player_faction_collapsed (:1745) | none |
| player.terminal_state | om_world_is_terminal (:1751) | none |
| player.faction | om_player_faction (:135) | none |
| jump.length_ticks, deaths | om_time_jump_report (header :1351) is returned by om_time_jump_run only; om_campaign_opening_jump_length (:1630); om_time_jump_death_pass_count (:1724) | no stored last report; pipe must cache it or add a getter |
| jump.interrupted | om_time_jump_interrupt (:1727) is a mutator | add getter |
| force.allocated | om_force_allocated_unit_count(w, mission_id) (:1674) | none |
| force.progression_level | om_progression_has_player_level (:1707) is a bool | add level getter |
| macro.behaviour, modifier, speed | om_macro_get_behavior (:1530), om_macro_get_modifier (:1533), om_macro_get_speed_multiplier(int) (:1535) | per-force enumeration and force count: none |
| macro.script_state | only om_macro_set_state (:1551) | add getter |
| macro.ambush_hold | none (enemy_macro.c:483 internal) | add getter |
| waves {at_tick, size, faction} | om_wave_get_since (:1509) yields om_wave {tick, kind, x, y} from a stub (economy_doctrine.c:1, "E1 later pieces fill them") | shape mismatch (no size, no faction), source is a stub |
| structures id/owner/hp | om_structure_count (:2059), om_structure_get_at (:2060), om_structure_get_owner (:2029), om_structure_get_hp (:2025) | none |
| structures.production_timer, cost | om_structure_get_timer (:2031), om_structure_get_unit_type (:2032) + om_structure_unit_cost (:2049) | none |
| structures.refound | none | add (R-218-05 refound) |
| mission.candidate_pool | om_mission_candidates (:1769) | none |
| mission.preference | om_mission_compute_preference (:1777) | none |
| mission.fallback_archetype | om_mission_fallback_archetype (:1789) | none |
| mission.parity | om_mission_get_player_parity (:1811) | none |
| mission.shortfall | om_mission_get_shortfall_text (:1814) | none |
| mission.consequence_target | om_chronicle_has_mission_consequence_flag (:1669) only | add getter |
| mission.revolt_flag | om_mission_set_revolt_events (:1834) is a setter | add getter |
| events.noise_offsets | om_event_noise(w, region, template) (:641) | none |
| events.breaches | om_event_breached(w, region, template) (:642) | none |
| events.last_fired | om_tick_events (:695) | no attached-character field (item 6) |
| fog.visible_counts | om_player_can_see(w, faction, unit) (:1597), om_recon_is_enemy_visible (:1601) | per-unit only; counts by scan; tactical-only (zero outside a mission) |

## Provenance findings (spec_provenance.py, run on temp copies, deleted; worktree clean)
lane_u_spec_rev2: lines 5, 9, 11, 13, 15, 17, 19: (8) [B R-162-03 | R-042-05 | R-215-05 | R-066-02 | R-070-02 | R-051-04 | R-218-05] has no pin. Exit 1. No other reason fires. Caveat: backticked `DRAFT-...` names sit in code spans, which the lint strips, so reason 6 never checks them: u-audit-counts, u1-ticks, u7-seed, coverage-slack, coverage-stale-days need register or ledger rows by hand.
harness_coverage_spec_rev2: no findings, exit 0.
