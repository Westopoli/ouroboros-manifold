# PROPOSED RE-CUT, E-05 remaining stubs

File build order (dependency-forced): csrc/agent.c -> csrc/resolve.c -> csrc/collision.c -> csrc/friction.c.
Rule applied: a test reaching stubs in 2+ files is owned by the LATER file's card.

## PREREQUISITE 0 (blocking, parent-owned, not a DeepSeek card)

csrc/om_internal.h currently has NO storage for:
- event queue (om_queued_event array + count) -- needed by om_event_queue (resolve.c) AND om_step_admin_revolts (friction.c)
- damage history (windowed per-region military/economy loss, 150-tick decay) -- needed by om_region_add_damage / om_region_damage_history (resolve.c)
- friction tick log (om_friction array + count) -- needed by om_tick_friction (friction.c)
- admin-roll tick log (om_admin_roll array + count) -- needed by om_tick_admin_rolls (friction.c)

Every existing DONE E-05 card kept allowed_files to a single .c file BECAUSE om_internal.h's struct already had the fields it needed (decisions/telegraphs/attacks/collisions/reinforces/colonizations all pre-declared, see om_internal.h:53-65). That pre-declaration step never happened for event_queue/damage_history/friction/admin_rolls. This is a struct-shape decision ("Sub-agents... may not make architectural or API decisions") -- the parent must add these 4 fields to om_internal.h before cards RESOLVE-3 (event queue), RESOLVE-4 (damage history), FRICTION-1, FRICTION-2 below can be built. Card 206a/206b/204b2 as currently parked have `allowed_files: "csrc/friction.c"` / `"csrc/resolve.c"` only -- missing om_internal.h -- so even without the SPANS_ANOTHER_CARD failures they would fail to compile as scoped.

## CARD SEQUENCE

### CARD 1 -- agent.c: telegraph declare, draw, queue
Replaces: 203b2-e05-intent-telegraph-queue.md.satisfied-by-203b1 (WRONGLY marked satisfied -- its acceptance tests R-035-07/08 pass because 203b1 already built the accumulate fallback; the telegraph logic it was supposed to add was never built and om_pending_telegraphs is still STUB. Re-open with corrected acceptance below.)
snippet_file: csrc/agent.c
snippet_symbol: om_pending_telegraphs, om_step_decisions  (2 symbols; om_step_decisions is NOT stub today but must be re-edited to add ALG-15's RNG draw + telegraph enqueue -- ALLOWED, same pattern as 203b1->203b2 both touching this symbol)
acceptance: test_R_036_01_telegraph_preference_0_7_0, test_R_036_02_preference_0_3_0_2
  (Rule: a bug-inject control belongs to the card whose file makes the detector observable; when the branch and the observation live in different files, the later file owns it. test_control_e05_entrench_current_tick is owned by new card 208+e05-spawn-fault-branches in csrc/agent.c for om_faction_candidates; test_control_e05_agent_reads_live is owned by CARD 2 204a3 in csrc/resolve.c since its observation requires attack resolution to mutate military in step 3f.)
expected_lines: ~45 (pref calc+clamp ~10, RNG draw+mode branch ~10, telegraph append ~8, om_pending_telegraphs reader ~8)
assertions: 8+7 = 15 (within the 15 cap)
ALG/R: ALG-15, R-036-01, R-036-02

### CARD 2 (RESOLVE-1) -- resolve.c: core attack resolution (ALG-20/21)
Replaces: 204a3-e05-battle-damage-bands.md.hold.blocked (fixes its SPANS_ANOTHER_CARD by sequencing after CARD 1)
snippet_file: csrc/resolve.c
snippet_symbol: om_step_resolve, om_tick_attacks  (2 symbols)
acceptance: test_R_037_01, test_R_037_02, test_R_037_03, test_R_037_04, test_R_037_05, test_R_037_06, test_R_037_07, test_R_037_08, test_control_e05_surprise_on_defense
  (bug branch OM_BUG_SURPRISE_ON_DEFENSE = 0.5 applied to defense not attack -- inline in this function)
expected_lines: ~55 (effective attack/defense, stochastic draw, 3-band split, attacker-side no-mutation invariant, bug branch)
assertions: 28+15+25+11+14+7+8+18+3 = 129 -- WAY over cap. SIZING FLAG: split into
  - RESOLVE-1a "attack/defense multipliers + surprise/telegraph efficiency": R_037_01, R_037_06, control_surprise_on_defense (38 asserts, still over but a real algorithm sub-family: "the multiplier stage")
  - RESOLVE-1b "damage bands (breakthrough/contested/repelled + tension cap)": R_037_02, R_037_03, R_037_04, R_037_05 (65 asserts)
  - RESOLVE-1c "attacker-side invariants (budget spent in full, attacker regions untouched)": R_037_07, R_037_08 (26 asserts)
  Root cause noted below (Key Findings): these are legacy mega-tests bundling 2-4 Given/When/Then boundary cases per rule row; no card split gets any of them under 15 without splitting the TEST functions themselves, which is out of a sub-agent's authority (tests are the spec).
ALG/R: ALG-20, ALG-21, R-037-01..08

### CARD 3 (RESOLVE-2) -- resolve.c: reactive reinforce (ALG-18/19)
Replaces: 204a2-e05-reactive-reinforcement.md.hold (already lint-clean; kept, just resequenced after CARD 2 by file-internal ordering, though it has no real dependency on CARD 2)
snippet_file: csrc/resolve.c
snippet_symbol: om_step_reinforce, om_tick_reinforces (2 symbols)
acceptance: test_R_036_05_with_probability_min_1_defend, test_R_036_06_base_10_0_5_60
expected_lines: ~50 (per existing card's own estimate)
assertions: 10+11 = 21 (over cap but close; existing 204a2 card already scoped this way)
ALG/R: ALG-18, ALG-19, R-036-05, R-036-06

### CARD 4 (RESOLVE-3) -- resolve.c: telegraph maturation (ALG-15 tail, 3c dispatch)
Replaces: 204a1-e05-telegraph-maturation.md.hold.blocked (fixes SPANS_ANOTHER_CARD; ALSO fixes the under-scoping bug -- original brief only described list bookkeeping, but must call the SAME resolution logic CARD 2 built, at full efficiency, since R_036_03 asserts `att.effective_attack == 70.0` after maturation)
snippet_file: csrc/resolve.c
snippet_symbol: om_step_telegraphs (1 symbol; reuses CARD 2's internal resolution code, not itself a new symbol)
acceptance: test_R_036_03_it_resolves_in_step_3c
  (needs CARD 1 + CARD 2 + CARD 3 all landed first -- this is effectively the S-036 story gate test, see Story Gate Placement)
expected_lines: ~35 (scan telegraphs[], maturity check, drop-if-attacker-dead, call shared resolve helper, remove entry)
assertions: 22 (single test, near the cap top -- fine)
ALG/R: ALG-15/20/21 combined, R-036-03

### CARD 5 (RESOLVE-4) -- resolve.c: conquest (ALG-22 transfer/garrison)
Replaces: 204b1-e05-conquest-garrison.md.hold.blocked (fixes SPANS_ANOTHER_CARD by sequencing after CARD 1/2)
snippet_file: csrc/resolve.c
snippet_symbol: om_step_resolve (extend, same symbol as CARD 2 -- matches existing 204a3->204b1 precedent of re-editing one symbol across cards), also wire OM_BUG_CONQUEST_ON_BAND and OM_BUG_GARRISON_BEFORE_DAMAGE branches here
acceptance: test_R_038_01, test_R_038_02, test_R_038_03, test_R_038_05, test_R_038_06, test_control_e05_conquest_on_band, test_control_e05_garrison_before_damage
expected_lines: ~40 (conquest condition, owner transfer, garrison add, extra penalties, held-since reset, 2 bug branches)
assertions: 28+13+14+13+11+4+6 = 89 -- over cap. SIZING FLAG: split into
  - RESOLVE-4a "conquest condition + ownership + garrison + extra penalties": R_038_01, R_038_02, R_038_03, control_garrison_before_damage, control_conquest_on_band (58 asserts)
  - RESOLVE-4b "held-since reset + edge update (S-024 R-024-03)": R_038_05, R_038_06 (24 asserts)
ALG/R: ALG-22, R-038-01, R-038-02, R-038-03, R-038-05, R-038-06

### CARD 6 (RESOLVE-5) -- resolve.c: conquest-unrest queue + solo colonize (ALG-22 tail + ALG-24)
Replaces: 204b2-e05-unrest-colonize.md.hold (fixes: needs om_internal.h event-queue field added per PREREQUISITE 0; allowed_files must add csrc/om_internal.h)
snippet_file: csrc/resolve.c
snippet_symbol: om_step_resolve (extend, 3rd touch), om_tick_colonizations, om_event_queue (3 symbols -- at the cap)
acceptance: test_R_038_04_with_probability_0_60_conquest, test_R_040_04_chain_still_completes_nothing_interrupts
  (R_040_04 statically reaches only om_event_queue + om_tick_reinforces -- no om_tick_admin_rolls call at all; it likely seeds the admin-separatist event directly rather than rolling for it, so it is satisfiable here, BEFORE friction.c's admin-revolt card, despite living in the S-040 test file. Flagging as a genuine surprise -- confirm before committing to this placement.)
expected_lines: ~45 (draw+delay+enqueue on conquest; om_tick_colonizations reader; om_event_queue reader)
assertions: 9+22 = 31 (over cap, modest)
NOTE: om_tick_colonizations / the solo (non-collision) colonize-write path has NO test anywhere in tests/csim that exercises it standalone -- it is only exercised transitively later, inside CARD 8 (collision.c) via test_R_039_04. Flag as thin/indirect coverage, not "no test reaches it" (a later card does reach it) -- see Key Findings.
ALG/R: ALG-22 (unrest tail), ALG-24, R-038-04

### CARD 7 -- csrc/sim.c: 3c/3e dispatch-order fault (RENAMES/REPLACES card 207)
Real finding: card 207 as parked is mis-scoped. `om_debug_inject` (csrc/sim.c:380) is already a fully generic `w->inject = (int)bug` setter (works for ANY om_bug/om_bug_e05 value already) -- there is nothing left to "wire" for 8 of the 9 E-05 bug codes; each of those belongs INSIDE the domain file that implements the behavior being faulted (folded into CARDS 1/2/5/8/9/10 above/below as bug branches). The ONE E-05 bug that is genuinely sim.c's job is OM_BUG_TELEGRAPH_AFTER_REINFORCE (101): "3c runs after 3e" is a STEP-ORDER fault in om_world_step's fixed call sequence (csrc/sim.c:116-119), which only sim.c can inject.
snippet_file: csrc/sim.c
snippet_symbol: om_world_step (re-edit, add one conditional branch swapping the om_step_telegraphs/om_step_reinforce call order when w->inject == 101)
acceptance: test_control_e05_telegraph_after_reinforce
  (needs CARD 1 + CARD 3 + CARD 4 landed first: the reorder must produce an observably different result, which requires real telegraph-declare, reinforce, and maturation logic to exist)
expected_lines: ~15
assertions: 2
ALG/R: R-036-03 (ordering), OM_BUG_TELEGRAPH_AFTER_REINFORCE
Empirically confirmed by running it: test_control_e05_agent_reads_live and test_control_e05_entrench_current_tick and test_control_e05_friction_counts_trade FAIL TODAY even though card_lint reports card 207 clean -- lint cannot see functional incompleteness, only STUB tags. This is a real card_lint blind spot worth flagging to the main session (not fixed here, read-only task).

### CARD 8 (COLLISION-1) -- collision.c: lottery + unowned colonize (ALG-23 lottery/retention + ALG-24 dispatch)
Replaces: 205a1-e05-collision-lottery.md.hold (clean) + 205a2-e05-collision-unowned-colonize.md.hold.blocked (fixes SPANS_ANOTHER_CARD by sequencing after CARD 6)
snippet_file: csrc/collision.c
snippet_symbol: om_tick_collisions (1 symbol; also wire OM_BUG_COLLISION_MAX_STRENGTH branch here)
acceptance: test_R_039_01, test_R_039_02, test_R_039_03, test_R_039_04, test_R_039_06, test_control_e05_collision_max_strength
  (depends on CARD 6 for the unowned-colonize write path reused by R_039_04)
expected_lines: ~65 (grouping+strength+lottery+retention/refund ~35, unowned-colonize dispatch+narrow-margin penalty ~20, loser-tension ~8, bug branch ~5) -- OVER the 80 cap is close but the assertion count is the real problem
assertions: 10+7+5+15+12+2 = 51 -- SIZING FLAG: split into
  - COLLISION-1a "grouping, strength, lottery, retention/refund + loser tension": R_039_01, R_039_02, R_039_03, control_collision_max_strength (24 asserts)
  - COLLISION-1b "unowned-target colonize dispatch + narrow-margin penalty + 3-collider generalization": R_039_04, R_039_06 (27 asserts)
ALG/R: ALG-23, ALG-24, R-039-01, R-039-02, R-039-03, R-039-04, R-039-06

### CARD 9 (COLLISION-2) -- collision.c: owned-target multi-collider combat (ALG-20/21/22 reused)
Replaces: 205b-e05-collision-owned-combat.md.hold.blocked (fixes SPANS_ANOTHER_CARD by sequencing after CARD 5)
snippet_file: csrc/collision.c
snippet_symbol: om_tick_collisions (extend, same symbol as CARD 8)
acceptance: test_R_039_05_each_collider_s_strength_applied
  (depends on CARD 2 -- attack resolution reused -- AND CARD 5 -- conquest reused)
expected_lines: ~60 (per-collider stochastic draw against shared defense, summed damage, conquest dispatch to winner)
assertions: 15 (right at cap -- fine)
ALG/R: ALG-20, ALG-21, ALG-22 (multi-collider variant), R-039-05

### CARD 10 (FRICTION-1) -- friction.c: border friction (ALG-25)
Replaces: 206a-e05-border-friction.md.hold (clean; needs no other-file dependency -- can build any time after PREREQUISITE 0's friction-log field exists)
snippet_file: csrc/friction.c
snippet_symbol: om_step_friction, om_tick_friction (2 symbols; also wire OM_BUG_FRICTION_COUNTS_TRADE branch here)
acceptance: test_R_041_01, test_R_041_02, test_R_041_03, test_R_041_04, test_R_041_05, test_control_e05_friction_counts_trade
expected_lines: ~50
assertions: 10+15+20+15+19+1 = 80 -- SIZING FLAG: split into
  - FRICTION-1a "hostile-neighbor counting across border/both, trade-only excluded, empty/same-faction excluded": R_041_02, R_041_03, R_041_05, control_friction_counts_trade (55 asserts, still heavy)
  - FRICTION-1b "delta application + economy floor clamp": R_041_01, R_041_04 (25 asserts)
ALG/R: ALG-25, R-041-01..05

### CARD 11 (FRICTION-2) -- friction.c: admin revolt rolls (ALG-29)
Replaces: 206b-e05-admin-revolts.md.hold.blocked (fixes SPANS_ANOTHER_CARD by sequencing after CARD 6; needs PREREQUISITE 0's admin-roll-log field)
snippet_file: csrc/friction.c
snippet_symbol: om_step_admin_revolts, om_tick_admin_rolls (2 symbols; also wire OM_BUG_ADMIN_ROLL_PER_FACTION branch here)
acceptance: test_R_040_01, test_R_040_02, test_R_040_03, test_control_e05_admin_roll_per_faction
expected_lines: ~50
assertions: 7+7+12+2 = 28 (over cap, modest)
ALG/R: ALG-29, R-040-01, R-040-02, R-040-03

## TESTS OWNED BY NO CARD (need a later epic / a gate card, not this recut)
- test_R_040_05_e_07_creates_new_faction -- stubs={} (0 reach into agent/resolve/collision/friction). Rule text: "the Admin Breakaway event fires... E-07 creates a new faction holding the region." Genuinely E-07's job. Recommend: leave as a `kind: gate`-adjacent xfail/skip-until-E-07 marker, not an E-05 card. (It currently reports "1 xfailed" when run standalone, so it may already be marked xfail -- confirm.)

## STUBS NO TEST REACHES (dead ABI or missing test -- flag)
- om_region_add_damage (resolve.c) -- zero test files under tests/csim call it, directly or via the conftest.py `add_damage()` wrapper (grepped the whole tree, only conftest.py itself defines the wrapper; no caller). ALG-11's opportunist damage-history boost is real bible content (Q-035-01 already flagged this gap once: "the Python code never fed it"). Recommend: either write the missing test as part of CARD 6, or explicitly park this as known-untested with a TODO pointing at Q-035-01.
- om_region_damage_history (resolve.c) -- same, zero callers in test suite (only reached internally by agent.c's om_faction_candidates, which is non-stub and already built reading it as a hardcoded 0.0).

## STUBS REACHED ONLY TRANSITIVELY (thin coverage, not "no test", flag anyway)
- om_tick_colonizations (resolve.c) -- no test calls it for the SOLO (non-collision) colonize-intent path; the only caller in the test suite is test_R_039_04 via the collision.c COLLISION path (CARD 8), which exercises the "collision winner colonizes" branch, not the "single faction colonizes uncontested" branch that om_step_resolve's plain 3f dispatch would also need to hit. Recommend flagging to the main session whether a dedicated solo-colonize test is owed before Tested status.
