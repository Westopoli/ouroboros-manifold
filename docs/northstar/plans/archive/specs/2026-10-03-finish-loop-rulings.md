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

Units on one file queue in the order listed. Each has a failing test first.

## Onto the reach allowlist (behaviour is live another way; reversible)

- **Superseded by live code:** `om_macro_enemy_leaves_trigger` (no-op by design, R-120-02), `om_chapter_advance_phase`, `om_chapter_end_reason_for_collapse`, `om_character_selector_confirm_commander`, `om_player_faction_collapsed`, `om_selector_resolve_fallback_pool`, `om_breakaway_create`, `om_faction_create_breakaway`, `om_outcome_apply_consequences`, `om_mission_setup_tactical`, `om_force_set_surviving_units`, `om_force_allocator_run`.
- **Public wrappers and test accessors over live state:** `om_event_breached`, `om_event_last_fired`, `om_chain_counter`, `om_campaign_opening_jump_length`, `om_character_selector_input_region`.
- **Unused flag:** `om_chapter_transition_start`, `om_chapter_transition_complete` (nothing reads `in_transition`; R-064-01's persistence is live because the jump does not reset state).

Deleting these and their tests is Westley's call (tests are the spec); allowlisting has precedent (rulings-2, Addendum 9).

## Deferred (the feature is not in the MVP loop)

`om_tick_revolts`, `om_tick_reversions`, `om_tick_absorptions` (a faction-history view); `om_mission_setup_survive`, `om_mission_eval_survive` (no archetype uses it); `om_mission_compute_starting_force`, `om_mission_compute_reinforcement_capacity` (Q-218-04 open); `om_objective_setup_drifting`, `om_hazard_spawn_moving_interference`, `om_hazard_sample_interference`, `om_zone_sample_interference` (arrive with map generation reaching mission setup).

## Results (2026-10-03, evening)

- **Landed** (`0d4006fd`): B1-U1, B1-U2, B1-U4, B7-1, RET-1, and 16 of the 19 allowlist entries.
- **Refused for the allowlist, with evidence** (F11 below): `om_selector_resolve_fallback_pool` is not the same job as the live resolver; `om_player_faction_collapsed` contradicts R-062-01 for a faction that no longer exists. `om_force_set_surviving_units` is not superseded: it writes state nothing reads.
- **OBJ-1 held** (F12 below): the rules give only fractions; nothing defines the targets, the escorted units or the extraction point. Red tests wait on `push/obj-tests`.
- **ABIL-1 deferred.** The sim half of R-086-09 is done and tested (the event record). No live client code reads a per-tick event list, the tactical frame has no events array, and E-18 S-135 (how an ability looks) is "Spec'd, needs reference" and is judged by eye, so it needs a prototype first (`agile.md`, Prototype gate). The pipe contract lands together with the S-135 render piece. Scout's draft for then: an `events` array on every tactical frame, at most 256, drained on write; open points are whether a mid-play `snapshot` should consume events and whether events are filtered by what the player's side sees. `docs/northstar/spec_factory/transport/tactical.schema.json` has no owner row and `docs/architecture.md` has two (DOCS-arch, PP-contract); both need settling before that contract piece.
- **Known limits of what landed:** a force's starting hit-point sum is captured once, so later reinforcements raise its share; the retreat also calls `om_unit_order_move` per unit because `om_command_move` does not write the destination record the getter reads (the clean fix is in `csrc/tactical_move.c`, owned by the movement and layers lane); retention counts only the force as deployed (F13).

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
| F11 | `om_player_faction_collapsed` and `om_selector_resolve_fallback_pool` disagree with their rule or the live path: fix, or remove with their tests? | Tests are the spec |
| F12 | Objectives (R-075-03, R-075-04): what a designated target is and how many, who is escorted and how many, where the extraction point is, where Interception's enemy force comes from | Rule content |
| F13 | Retention (R-077-01): do the commander's unit, units made mid-mission and structures count; is a unit that leaves the map alive? | Rule content |
