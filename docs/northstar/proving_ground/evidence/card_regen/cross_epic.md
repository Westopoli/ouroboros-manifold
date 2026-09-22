# Cross-epic symbol ownership -- card_regen

- `om_character_create`: E-08, E-09
- `om_chronicle_entry_count`: E-08, E-09
- `om_command_activate_ability`: E-11, E-13
- `om_command_attack_move`: E-11, E-12, E-13
- `om_command_attack_target`: E-11, E-13
- `om_command_move`: E-11, E-12, E-13
- `om_event_fire_manual`: E-08, E-09
- `om_event_get_attached_character`: E-08, E-09
- `om_lineage_create`: E-08, E-09
- `om_lineage_record_history_region`: E-08, E-09
- `om_map_add_cover`: E-11, E-12, E-13
- `om_map_add_obstacle`: E-12, E-13
- `om_mission_compute_parity`: E-10, E-14
- `om_mission_end`: E-10, E-14
- `om_mission_get_objective_completion`: E-10, E-15
- `om_objective_get_center`: E-15, E-17
- `om_tactical_step`: E-08, E-11, E-12
- `om_tactical_tick`: E-10, E-11, E-14, E-15, E-17
- `om_tactical_tick_to`: E-14, E-15, E-17
- `om_tick_friction`: E-03, E-06
- `om_time_jump_run`: E-08, E-10
- `om_unit_attack`: E-12, E-13
- `om_unit_deal_damage`: E-11, E-15
- `om_unit_get_hp`: E-12, E-13
- `om_unit_get_pos`: E-12, E-13
- `om_unit_get_target`: E-12, E-13, E-15
- `om_unit_set_hp`: E-11, E-13
- `om_unit_spawn`: E-11, E-12, E-13
- `om_unit_spawn_combat`: E-15, E-17
- `om_unit_teleport`: E-11, E-12
- `om_visibility_compute`: E-12, E-13
- `om_world_generated`: E-03, E-06
- `om_world_get_state_checksum`: E-12, E-13
- `om_world_set_tick`: E-06, E-10

## Beyond the 12-epic scope: real-queue collisions

`cross_epic_overlap()` above only compares the 12 epics processed in one
invocation. A manual check of every symbol these 12 epics' regenerated
cards claim (via `snippet_symbol`) against every `snippet_symbol` already
named by a real, live (non-`.superseded`/`.retired`) queue card in ANY
epic (including E-04 and E-05, not part of this run) found more
collisions, not decided here:

- `om_tick_friction` (E-03's `213a-e03-worldgen-routes_carry_armies_trad`
  and E-06's `220a-e06-diplomacy-three_ways_to_feel_about`, both above)
  is ALSO already claimed by E-05's live `206a-e05-border-friction.md.hold`
  -- a three-way conflict, not just two.
- `om_tick_events` (E-06's `223a2-e06-diplomacy-a_faction_s_technology_i`)
  is already claimed by E-04's live `208b3-e04-revolts-and-deltas.md.hold`.
- `om_event_queue_external` and `om_tick_pruned` (E-07's
  `230a-e07-lifecycle-a_revolt_can_birth_a_nat`) are already claimed by
  E-04's live `209c-e04-chain-spawns.md.hold` and
  `209b-e04-queue-resolution.md.hold` respectively.
- `om_event_template_count` and `om_events_load_launch` (E-09's
  `256a2-e09-chronicle-the_fragment_library_con`) are already claimed by
  E-04's live `208a-e04-library-load-readback.md.hold`.

`card_lint.py` (run against the real agora queue, see the finishing
report) independently confirms this same conflict as `SPANS_ANOTHER_CARD`
-- but on `256a3`, not `256a2`: `card_lint` only inspects the symbols a
card's own ACCEPTANCE tests reach, not its `snippet_symbol` declaration,
and 256a2's own assigned tests never call `om_event_template_count`/
`om_events_load_launch` directly (some other test needs both of those
PLUS a later symbol, so its acceptance line landed on 256a3 instead, per
this tool's own "spans later cards" rule); 256a3's acceptance does call
them as fixture setup, and since csrc/events.c's real body is still
E-04's STUB (neither 256a2 nor E-04's own card has been built), `card_lint`
correctly flags it there. Both cards are part of the same conflict: 256a2
is the intended builder, 256a3 is the first card whose acceptance would
actually exercise the un-built symbol.

Every one of these is E-04/E-05's event and friction plumbing, reached as
fixture setup by E-06/E-07/E-09's own tests (a revolt or a fragment-library
test drives the tick log through the event queue). The regenerated cards
above still name these symbols, since a story's own test genuinely calls
them and this tool has no cross-epic queue-wide ownership check built in
(only the 12-epic same-invocation check above). Design-lane question, not
decided: either E-04/E-05's own card builds these first and E-06/E-07/E-09's
regenerated cards drop them from `snippet_symbol` (treating them as
already-available, the same sequential-ownership rule this tool already
applies within one epic), or a repair pass re-cuts whichever side is wrong.

