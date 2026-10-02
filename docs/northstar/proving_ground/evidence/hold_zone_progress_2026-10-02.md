# Hold-zone progress in play, diagnosis for A115 (2026-10-02, origin/main 9ccc565a)

Read-only trace. No code changed.

## Answer: (a) another path already stops progress for an enemy in the zone

Tick chain: `om_tactical_step` (csrc/unit.c:1666) calls `om_support_tick` (unit.c:1682) then `om_mission_tactical_tick` (unit.c:1683, defined csrc/mission.c:1283).

`om_mission_tactical_tick` (mission.c:1283-1325), hold-zone kind:
- Zone centre: `om_objective_get_center(w, 0)` (mission.c:1294; impl mission.c:2608). A centre pushed by `om_objective_set_center` wins, else the spine node position read live.
- Radius: `OM_MISSION_OBJECTIVE_COVER_RADIUS` = 400.0 (om_constants.h:611), mission.c:1295. NOT the 300 wu `OM_REINFORCEMENT_CAPTURE_RADIUS` that `om_objective_is_contested` uses.
- Faction filter: `om_unit_get_faction(id) == enemy` where `enemy = om_mission_enemy_faction(...)` (mission.c:1290; impl 2366: region owner if not player, else the hostile neighbour owner with most military, else the other of faction 0/1). One enemy faction only. A third hostile faction would not count. Friendly (== player) units only set `player_alive`; they never count.
- Unit state: `om_unit_alive` only (mission.c:1301). No stance or order check.
- Effect: `om_mission_eval_hold_zone(w, 0, enemies_inside)` (mission.c:1316; impl 1636-1644): `hold_elapsed_ticks += tick_period` only when `enemies_inside == 0`; completion = elapsed/required (12000 base ticks, `OM_MISSION_HOLD_ZONE_REQUIRED_TICKS`, mission.c:565). Elapsed is recomputed from live positions every step with no latch, so progress resumes the step the enemy leaves (elapsed is kept, not reset). Wired: `om_pipe.c:1549` calls `om_mission_build_objectives`, which calls `om_mission_setup_hold_zone` (mission.c:1213) for hold-zone archetypes. Gate: mission_set, not ended, n_objectives > 0.

No separate "contested" state field exists; "contested" for the mission path is just `enemies_inside > 0` for that step.

## `om_objective_is_contested`

Defined tactical_support.c:876; declared ouroboros_sim.h:1770; bound only in tests/csim/conftest.py:2455. Nothing in csrc calls it. It counts ANY living unit (no faction) within 300 wu of the refreshed centre, so the unit-faction filter in flight would only repair a function nothing in play uses.

## Drifted zone

The mission path uses the moved centre IF the centre was pushed: `om_support_tick` runs before the mission tick and (tactical_support.c:~858) refreshes each drifting objective via `om_sup_objective_refresh_center`, which calls `om_objective_set_center` (tactical_support.c:817). BUT `om_objective_setup_drifting` (tactical_support.c:799) has no caller in csrc/ (only tests); `om_pipe.c` never makes an objective drift. So in play today the hold centre never drifts through this API, and the R-130-02 drift fixture is test-only reachable. The spine-node route (`om_map_setup_drifting_node`, ouroboros_sim.h:1706, read live by `om_objective_get_center`) is the only other drift source; I did not trace whether it is wired.

## Recommendation (one paragraph)

Choose (a): the mission-path rule already is R-130-02 in play (enemy-faction filter, alive units, live centre via `om_objective_get_center`, resumes on leave, friendly ignored), so move R-130-02's tests to drive `om_tactical_step` with a built hold-zone mission (`om_mission_build_objectives` + `om_mission_setup_tactical`, enemy and friendly units placed with `om_unit_spawn_combat`, assertions on `om_mission_get_objectives` completion and `hold_elapsed`), and delete `om_objective_is_contested`, its header declaration, the conftest binding, `OM_SUP_CONTEST_SCAN_CAP` (tactical_support.c:166) and its comment at :811, and the in-flight faction-filter fix. Two things must change in those tests: the contest radius is 400 wu not 300 (the fixture's inside-old-zone/outside-moved-zone geometry, drift 150 wu, must be re-derived against 400, where an enemy at the old centre is inside both zones unless placed more than 400 wu from the moved one, which a 150 wu drift cannot produce, so that specific "outside the moved zone" assertion cannot be built at span 150; Architect ruling needed on moving the radius or the drift span), and the drift itself is not wired, so the drifted-zone case needs either `om_objective_setup_drifting` called from a pipe or mission setup path (a B14 insertion after `om_mission_build_objectives` at om_pipe.c:1549 or inside `om_mission_setup_hold_zone`, mission.c:2560) or an explicit decision that drift is a later piece. If the Architect prefers (b) instead, the exact insertion point is `om_mission_tactical_tick` mission.c:1301-1306, which already is the stop; there is nothing further to wire.
