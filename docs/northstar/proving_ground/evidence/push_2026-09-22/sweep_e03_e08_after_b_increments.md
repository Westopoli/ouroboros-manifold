# sweep scorecard — 2026-09-22

worktree: /tmp/sweep @ origin/main ec8b705. verify only, no code touch, no commit.

## E02
72 passed / 4 skipped / 0 failed. matches expect (72/4). green.

## E03
32 passed / 2 failed / 0 skip (34 total).
red:
- `test_R_024_01_every_edge_between_their_regions` — assert out.value == BOTH, got 0
- `test_R_024_02_every_edge_between_their_regions` — assert out.value == BORDER, got 2 (BOTH)
diag: diplomacy edge redraw not happening at all when DIPLOMACY feature on + stance flips. `om_region_edge` never changes for the pair — cooperative→BOTH and hostile→BORDER redraw logic (S-024) not wired to `om_world_step`. R-024-03/05 not in fail list — they pass now (B4 fix for those landed as expected).

## E04
31 passed / 0 failed (test_E04_*.py glob, incl S030 launch-library file). matches expect (31/31), green.
`test_E04_S030_external_templates.py` — **file does not exist** in this worktree. no test to run, no 5-failed to report. B1-5 not landed here yet or file lives under a different name; nothing else under `tests/csim` or `tests/specfactory` mentions `external_templates` or `om_event_register_external` (that symbol only shows up in the pushed-repo commit log, not this tree's source).

## E05
62 passed / 2 skipped / 1 xfailed / 0 failed. matches expect (green except Q-039-01/Q-040-02 skips + 1 xfail).

## E06
39 passed / 7 failed (46 total; expect doc said ~38+/42, tree has grown to 46).
red:
- `test_R_045_07_one_uniform_draw_made_if` — assert len(kl_events) >= 1, got 0
- `test_R_045_09_mean_over_all_windows_between` — assert 1.0<=mean<=2.0, got 0.0
  diag: both point at `csrc/diplomacy.c` ~line 636. Knowledge Lost tech-penalty and cooldown-tick DO fire correctly, but the fired record goes through `om_event_fire_manual` into events.c's own manual-fire table, not the `om_tick_events`/trigger-pipeline log `read_events()` queries. code comment at diplomacy.c:636-645 says this straight out — no public way today to make a KL firing show up in that log. observable-gap, not a math bug.
- `test_R_046_04_effective_attack_multiplied_by_it` — assert len(attacks) == 1, got 2
  diag: repro shows attack #2 is an uninvited autonomous attack from the DEFENDER faction (fortifier, budget 100, hostile) back at the attacker — `isolate_agents()` helper turns off EVENTS/DIPLOMACY/TECHNOLOGY/DRIFT/LIFECYCLE but leaves FACTIONS (the agent AI step, csrc/agent.c) ON by design ("leave only the faction step on"). test injects one attack and expects exactly one, but the live agent step for the other faction fires its own. fixture/test interaction, points at csrc/agent.c's autonomous decision loop colliding with an injected intent in the same tick.
- `test_R_048_01_it_1_in_34_67` / `_02_units_use_tier_2_profile` / `_03_units_use_tier_2_profile` / `_04_tier_transition_entry_candidate_e` — all assert tier/candidate values, all get 0
  diag: `om_faction_tech_tier`, `om_tech_tier`, `om_faction_next_mission_unit_tier`, `om_faction_unit_tier`, `om_mission_start`, `om_mission_unit_tier`, `om_chronicle_distill_candidates`, `om_faction_tier_transition_candidate`, `om_tier_transition_candidate_exists` are ALL explicit stubs in `csrc/diplomacy.c` (~line 693), comment says outright: "Left as the original stubs; not this card's scope." S-048 not built yet, not a regression.

## E07
combined 7-file run: 27 passed / 3 failed (30 total). matches expect (27/30).
standalone S-049 file: 6 passed / 1 failed — same failure as combined.
standalone S-051 file: 6 passed / 0 failed — clean, matches combined.
combined now equals standalone sums per-file, confirms events.c slot-table removal fixed the old divergence.
red:
- `test_R_049_06_nothing_happens_chain_pruned` — assert any(pruned matches template), got False
  diag: `csrc/events.c` only prunes a queued event for two reasons: queue-cap overflow (~line 424) or a `cond_kind` condition miss (~line 660). there is no "region changed owner since chain queued" check anywhere in the prune path. rule R-049-06 behavior (ownership-change kills a chain) is simply not implemented.
- `test_R_052_01_it_has_zero_regions_its` — assert budget == 0.0, got 1.05
  diag: repro trace shows budget0 jumps 0.0→1.05 on the SAME tick the region is conquered, then holds flat. `csrc/faction.c` `om_faction_step_budget` sums `(economy-8)*0.025` over regions still tagged to the faction — it runs before `csrc/resolve.c`'s conquest/ownership-transfer step in the tick order, so the region about to be lost this tick still pays out its economy to the old owner one last time. tick-sequencing bug, not the budget formula.
- `test_R_052_02_no_rule_anywhere_checks_whether` — assert damage_player == damage_npc, got 8.0 vs 8.02
  diag: repro math says the 2nd attack resolves as if stochastic draw was 0.99 not the freshly-forced 1.0. `om_rng_force` appends to a FIFO forced-draw queue (csrc/faction.c); the 1st attack (tick 1) only consumes one of its two forced draws (no conquest/unrest roll needed on CONTESTED outcome), leaving the unused 0.99 sitting in the queue. test then calls `force_draws(w, [1.0, 0.99])` again before the 2nd step, which appends rather than resets, so the 2nd attack drains the stale leftover 0.99 first. could be a test-fixture gap (residual forced draw not drained) as much as a sim issue — flagging both, not calling it either way.

## E08
46 passed / 4 failed (50 total; expect doc said 44/45, tree has grown to 50).
red:
- `test_R_055_02_no_strategic_tick_runs_strategic` — assert strategic_tick unchanged after om_world_step during MISSION phase, got advanced (0→1)
  diag: `om_world_strategic_tick`/`om_world_set_strategic_tick` (csrc/generational.c ~1464) are a bare alias for `w->tick` — no separate counter, no phase check. `om_world_step` (csrc/sim.c:194) advances `w->tick` unconditionally, doesn't look at chapter_phase==MISSION at all. gate never built.
- `test_R_055_04_character_selector_runs_after_it` — assert chosen_region != 0, got 0
  diag: `om_mission_generator_run` (csrc/generational.c ~1126) is a labeled placeholder pending E-10/csrc/mission.c: picks "highest-index region with faction_id >= 0" across ALL factions, not a real mission-target selection. fixture in this test owns no regions, so the loop never updates `chosen` off its 0 default. known placeholder, not this card's job.
- `test_R_055_05_opening_time_jump_runs_before` — assert 3<=chronicle_entries<=5, got 0
  diag: `om_campaign_start` just calls `om_chapter_start` — no opening time-jump-then-chronicle pass. `om_chronicle_entry_count` and `om_chronicle_distill_and_assemble` (csrc/chronicle.c ~233) are hard `/* STUB */` returning 0 / no-op.
- `test_R_064_04_next_time_jump_produces_same` — assert save_size > 0, got 0
  diag: `om_save_state_size`/`om_save_state_write` (csrc/generational.c ~1285) are explicit stubs, comment: "save.c (T2c) owns save/load; out of closure for this piece." load side (`om_load_state_read`) same story.

## controls (E-04/E-05, control_liveness.py)
LIVE=18 DEAD=2 ERROR=0 total=20. matches expect (18/20 LIVE) exactly.
dead:
- `test_control_e04_chain_counter_unsaved` (OMBugE04.CHAIN_COUNTER_UNSAVED) — both as-written and neutralized runs passed
- `test_control_e04_triggers_read_live` (OMBugE04.TRIGGERS_READ_LIVE) — both as-written and neutralized runs failed
these two detectors don't discriminate bug-present vs bug-fixed; flag as test-defect candidates, did not touch them.

## checksum_trace (seed 1, 60 regions, 500 ticks, 6 features)
build/O2 and build/O0 both built clean, zero compiler warnings either opt level.
O2 final: 12966767929705903382
O0 final: 12966767929705903382
match. (note: seed-1 world now generated per B4, so this value is not directly comparable to pre-B4 runs, but O2==O0 internal consistency holds.)

## snapshot fixture
`tests/specfactory/test_snapshot_fixture.py`: 7 passed / 0 failed. checked-in transport fixture still matches the generator after B4's populated-world change. no drift.

## piece verdicts
- B4 (E-03 diplomacy wiring): **not tag-ready**: R-024-01, R-024-02 (edge redraw dead)
- B5 (E-06 technology): **not tag-ready**: R-045-07, R-045-09, R-046-04, R-048-01, R-048-02, R-048-03, R-048-04 (R-048-* are stub-scoped, not regressions; R-045-*/R-046-04 are real gaps)
- B6 (E-07 revolt/lineage): **not tag-ready**: R-049-06, R-052-01, R-052-02
- B7 (E-08 generational): **not tag-ready**: R-055-02, R-055-04, R-055-05, R-064-04 (R-055-04/R-055-05/R-064-04 are labeled stubs pending other cards; R-055-02 is a real missing gate)
