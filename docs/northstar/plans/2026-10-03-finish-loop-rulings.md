# Finishing the MVP loop: scout findings and rulings (2026-10-03)

Planner chat, under Westley's 2026-10-03 leave to keep implementation moving. Source: three read-only scouts on origin/main `24df128c` (B1, B6, B7 and the C6 sweep) and the reach lint (280 of 728 tested symbols unreachable). Companion to `2026-09-30-mission-plays-plan.md` and `2026-09-30-work-list.md`. Rulings here are the planner's; anything marked "Westley" is not built until he answers.

## Build now (a rule says it happens in play and nothing live does it)

| Unit | File | Rule | What |
|---|---|---|---|
| B1-U1 | `csrc/enemy_macro.c` | R-120-02, R-122-02, ALG-76 (Q-120-03: 35 percent) | Live hit-point share per force; below 35 percent the force routs, retreats to its fallback point, and the runner sets `force_<i>_routed` |
| B1-U2 | `csrc/enemy_macro.c` (detector may sit in `csrc/mission.c`) | R-122-02, Q-122-01 (a) | A player unit in the objective zone sets `objective_<i>_contested` |
| B1-U4 | `csrc/enemy_macro.c` | R-120-04, R-123-02 | The tick calls `om_macro_execute_behavior` in place of its inline duplicate |
| B7-1 | `csrc/generational.c` | R-061-04 | On commander death the selector marks the character dead (`om_character_kill`) and writes the death ledger (`om_outcome_record_commander_death`) |
| OBJ-1 | `csrc/mission.c` | R-075-03, R-075-04, R-129-02 | Destroy-targets and escort-to-extraction objectives are set up and evaluated in play; today four of ten archetypes can never score |
| RET-1 | `csrc/mission.c`, `csrc/unit.c` | R-077-01 | Retention computed from deployed and surviving unit power; today it is hardcoded to 1.0 |
| ABIL-1 | `docs/architecture.md` first, then `csrc/om_pipe.c` | R-086-09 | Ability events reach the client in the tactical frame (contract piece first) |

Units on one file queue in the order listed. Each has a failing test first.

## Onto the reach allowlist (behaviour is live another way; reversible)

- **Superseded by live code:** `om_macro_enemy_leaves_trigger` (no-op by design, R-120-02), `om_chapter_advance_phase`, `om_chapter_end_reason_for_collapse`, `om_character_selector_confirm_commander`, `om_player_faction_collapsed`, `om_selector_resolve_fallback_pool`, `om_breakaway_create`, `om_faction_create_breakaway`, `om_outcome_apply_consequences`, `om_mission_setup_tactical`, `om_force_set_surviving_units`, `om_force_allocator_run`.
- **Public wrappers and test accessors over live state:** `om_event_breached`, `om_event_last_fired`, `om_chain_counter`, `om_campaign_opening_jump_length`, `om_character_selector_input_region`.
- **Unused flag:** `om_chapter_transition_start`, `om_chapter_transition_complete` (nothing reads `in_transition`; R-064-01's persistence is live because the jump does not reset state).

Deleting these and their tests is Westley's call (tests are the spec); allowlisting has precedent (rulings-2, Addendum 9).

## Deferred (the feature is not in the MVP loop)

`om_tick_revolts`, `om_tick_reversions`, `om_tick_absorptions` (a faction-history view); `om_mission_setup_survive`, `om_mission_eval_survive` (no archetype uses it); `om_mission_compute_starting_force`, `om_mission_compute_reinforcement_capacity` (Q-218-04 open); `om_objective_setup_drifting`, `om_hazard_spawn_moving_interference`, `om_hazard_sample_interference`, `om_zone_sample_interference` (arrive with map generation reaching mission setup).

## Westley

| # | Question | Why it is his |
|---|---|---|
| F1 | R-026-04: event thresholds are meant to be noised at each jump start; live noise is always 0. Wiring it changes every campaign's history and every recorded golden. Wire now, or with the balance simulation? | Effect well over 5 percent; balance items are held for him |
| F2 | R-062-02 collapse successor: the register has Q-062-01 closed as (b) (normal pools restricted to surviving factions, fall back to most regions); the code and ruling A15 use most regions only and say the question is open. Which is right? | Two records disagree on his answer |
| F3 | Chronicle entries for a fallen faction (R-062-04) and a dead commander (R-061-04 "the chronicle frames it"): category and wording | New chronicle content |
| F4 | Campaign end (R-062-03): how the client is told no faction survives | New pipe field |
| F5 | Enemy hooks (R-121-04, R-122-01): no mission registers a second force and no hook scripts exist. Default hook at mission setup, or wait for the script pipeline? | Feature scope |
| F6 | Timed transitions (R-121-02): the duration per force | A number |
| F7 | Cautious break-off (R-120-03): the "contact threshold" | A number |
| F8 | `om_faction_phase` (R-053): who consumes a faction's phase, the chronicle or the mission generator? | Rule meaning |
| F9 | Jump length (R-056-01, Q-056-01): the client sends raw ticks with no clamp to 20 to 100 | Open flag |
| F10 | Regional commander on conquest (R-060-01): never created in play; where it hooks is unclear | Needs a scout first |
