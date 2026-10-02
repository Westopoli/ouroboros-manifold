# Port gap audit: Python tactical sim vs C tactical sim

Read-only. Repo `/Users/westley/ouroboros`. Note: checkout moved under me mid-audit (branch now `main`, `csrc/unit.c` grew ~104 lines, grid perf only, behaviour-neutral; E-11 R-087-04 rewritten to pin pursuit as Python does). C line numbers below are the current ones. Python line numbers are from `simulation/`.

Status: CONFIRMED = read both sides. SUSPECTED = one side not found or not run.
Bible = `docs/bible/epics/E-11/E-12/E-13`. I do not judge which side is right.

## Summary table (largest fight effect first)

| # | Difference | Status |
|---|---|---|
| G01 | Fire gate: Python shooter needs target in OWN sensor set; C never checks sensor (Bombard/Bastion shoot full range in C, only 300 in Python) | CONFIRMED |
| G02 | Damage timing: Python simultaneous; C sequential by unit id, dead units skip their shot, player spawned first | CONFIRMED |
| G03 | Attack-move leash runs BEFORE damage in Python: attack-moving units with range >200 never fire at targets >200 from anchor; C fires on cohort ticks | CONFIRMED |
| G04 | Intercept: Python buff lasts 1 tick; C buff never expires in the tick loop | CONFIRMED |
| G05 | Ability auto-trigger (Surge, Brace, Rally, Barrage, Fortify, Intercept) exists in C only; cooldown start points differ | CONFIRMED (Python AI side SUSPECTED, behavior_runner not read) |
| G06 | C: any cover disc on the line blocks fire, even for units standing inside it; Python: cover never blocks fire | CONFIRMED |
| G07 | Live C battle map = empty field + ONE objective cover disc; Python maps carry gradients, obstacles, interference, vantage, asteroids | CONFIRMED |
| G08 | Routing and terrain: Python A* navmesh + waypoints + map clamp; C straight-line steering, no routing, no clamp, terrain slow built but fed nothing | CONFIRMED |
| G09 | First volley: C units start with cooldown 0 and wait a full interval; Python fires on first tick in range | CONFIRMED |
| G10 | Pursuit side-differences (beyond the known direct-write gap): not visibility-gated, every tick not cohort, pursuers overlap | CONFIRMED |
| G11 | Group orders: Python attack-move gets formation slots, no speed cap, group dies when all engaged; C attack-move single point, move capped at slowest | CONFIRMED |
| G12 | Return fire: Python also hijacks attack-moving units, picks lowest-id attacker; C only idle units, highest-id attacker | CONFIRMED |
| G13 | Steering sweep: 30deg x6 (Python) vs 15deg x12 (C); fully blocked = walk straight (Python) vs wait (C); layer filter; group-mate exemption | CONFIRMED |
| G14 | Collision and arrival: layer filter, map clamp, navmesh slide (Python only); stationary-stationary pairs, snap-to-slot (C); Python exact-overlap push is x1000 (flings units) | CONFIRMED |
| G15 | Warden aura: Python single 0.10, single heal; C diminishing reduction, stacking heal | CONFIRMED |
| G16 | Bastion never takes >1.0 category multiplier in C; Python Strike hits Bastion x1.5 | CONFIRMED |
| G17 | Barrage: Python no AoE cap, no Bastion rule, cooldown from activation, needs engaged target; C capped, cooldown from impact, any point | CONFIRMED |
| G18 | attack-target command: Python only sets target (no chase, no validation, no fog memory); C chases, kites in place, last-seen memory | CONFIRMED |
| G19 | C drops to 10 steps/s above 1,000 live units; Python has no such rule (store cap 1,024) | CONFIRMED |
| G20 | Fog minor: vantage extra-layer factor, elevation bonus, pulse, asteroid height LOS | CONFIRMED |
| G21 | Reinforcement capture census: wired in Python, no caller in C | CONFIRMED (csrc incl. pipe) |
| G22 | Facing: Python turns toward engaged target; C only turns with heading | CONFIRMED |
| G23 | C fixed-size caps with no Python equivalent | CONFIRMED |
| G24 | Low-impact: cohort phase, tie-breaks, stale targets, stealth/noncombat, command timing, missing verbs | CONFIRMED |

Constants: all roster, matrix, ability, fog, backswing, leash, flee, collision-radius, probe, detour values match. Four differ (section at bottom).

Tick order, Python `tactical_engine.py:39-74`: behavior runners, commands, targeting, movement (+leash +collision), facing, damage (+return fire), abilities (+barrage), fog timers, drift, reinforcement, objectives.
Tick order, C `unit.c:1770-1789 om_tactical_step`: period update, refresh positions (this also replays tactical_move.c movement+collision for the previous tick, `tactical_move.c:1408`), per-unit AI loop (target, hold, pursue, fire, damage applied at once), Warden regen, backswing countdown, ability cooldown/autotrigger/expiry, macro, support, mission.
Net: C moves units at the START of the next step, before AI; Python moves after targeting inside the same step. Effects are one-tick offsets, not listed separately.

---

## G01. Fire needs shooter's own sensor set (Python) vs none (C)

Python: `damage.py:17,38-39` builds `visibility = compute_visibility(...)` and skips the shot if `target not in visibility[uid]`. `fog_of_war.py:59-121`: set is built from THAT unit's own sensor radius x (1 - interference), cross-layer cone factor, asteroid LOS. Never shared across a faction. Acquisition (`damage.py:236-247`) uses attack range only, so Python units pick targets they then cannot shoot.
C: fire gate is `om_combat_can_shoot` (`unit.c:1738`, `tactical_move.c:1451-1479`) = terrain/cover samples only. Acquisition `om_tac_nearest_hostile` (`unit.c:1478`) uses attack range only, skips stealth only. `om_unit_can_see` (`fog.c:571`) is not consulted for firing. `om_unit_acquire_target` (`fog.c:542`) has no caller in the tick.
Fight effect: sensor is below range for Bombard (range 1200, sensor 300) and Bastion (800, 300). Python: they deal damage only at <=300 wu (less in interference). C: full 1200 / 800. Every other type has sensor >= range, so unaffected. Python also loses shots to interference and asteroid-blocked sight; C does neither (no zones live, see G07).
Bible: R-093-02 ("enemy uses its own visible set with the same rules as the player's units") and R-089-01 favour the Python gate. E-11 "Obviously working": "10 Bombards at 1,000 wu: the Bombards kill the Vanguards before they close" only works with the C behaviour. E-12 Purpose says "engine resolves combat identically whatever the player can see" (about the player's view, not unit sets). Neither side matches all three.

## G02. Damage is simultaneous in Python, sequential in C

Python: `damage.py:20-68` every unit fires into a `pending` dict; HP is subtracted and `kill` runs after the loop. A unit that dies this tick still fired this tick. Mutual kills happen.
C: `unit.c:1757-1766 om_tactical_ai_tick` walks rows in id order and `unit.c:811 om_tactical_apply_hit` writes target HP at once; loop skips `hp <= 0` rows. A unit killed earlier in the pass by a lower id never fires that tick. Lower ids get a first-strike edge every tick. `om_mission_instantiate_map` (`mission.c` ~2457-2458) spawns the player force before the enemy, so player ids are lower.
Fight effect: C favours lower id in every last-hit tick; systematic player edge in mirror fights; no mutual kills. Python is symmetric.
Bible: E-11 Invariants "a unit at 0 HP is dead on that tick and never acts again" reads as C. Nothing about same-tick fire.

## G03. Leash vs damage ordering, and effective attack-move range

Python: `movement.py:282-299 _update_attack_move_state` runs at the top of `update_movement`, which runs after `update_targeting` and BEFORE `resolve_damage` (`tactical_engine.py:45-48`). On first engagement anchor = unit position. If the target is >200 from the anchor, `auto_engage_target = -1`. A target acquired at 200 < d <= range is therefore dropped in the same step, before it can be shot, and the unit (no target, so no hold at `movement.py:348`) keeps walking. Re-acquired and re-dropped every cohort turn.
C: `unit.c:1693` same 200 leash, but the drop is checked at the NEXT tick's validation. On the acquisition tick `unit.c:1734-1739` holds and fires (if cooldown ready). Next tick target dropped, unit stays held (`unit.c:1744 hostile_within`), next cohort tick re-acquire and fire again.
Fight effect: attack-moving Interceptor (250), Vanguard (300), Warden (350), Bastion (800), Bombard (1200) in Python only fire at targets within 200 wu of where they acquired and walk on otherwise. In C they hold and fire at full range, shots landing only on cohort ticks (up to 3 ticks late). Raider (200) unaffected. Python plain idle units are unaffected (leash needs `attack_moving`).
Bible: R-087-05 and R-096-03 say the same 200 leash; both sides implement the literal text. Neither text says whether the drop precedes the shot.

## G04. Intercept buff duration

Python: `ability.py:187-213 _check_intercept` sets ACTIVE with duration 1, cooldown 600, retargets to the Strike unit. `ability.py:177-180` expires it next tick. Buff (x1.8 speed, x1.5 damage) lasts about one tick per 30 s.
C: `unit.c:1263-1267` autotrigger sets `ability_phase = ACTIVE`, `ability_bonus_on = 1`; no duration, no cooldown set. `unit.c:1352-1372 om_ability_advance_all` has no Interceptor case, so nothing ends it. `unit.c:2153 effective_speed` and `unit.c:2248 output_multiplier` keep returning x1.8 / x1.5. Only `om_tactical_run_until_engagement_ends` (a run helper, `unit.c` ~1958) resets it. In the live pipe tick it never ends.
Fight effect: C Interceptors that ever see a Strike unit within 350 wu on their layer keep x1.5 damage and x1.8 speed for the rest of the fight. Python Interceptors are nearly unbuffed.
Bible: R-086-02 "for the first engagement, then cooldown 600". Matches neither side in the tick.

## G05. Ability auto-trigger and cooldown start

Python: only Intercept self-triggers (`ability.py:145,187`). Surge/Brace/Rally/Barrage/Fortify fire only from an `activate_ability` command (`command.py:69-72`).
C: `unit.c:1253-1296 om_ability_autotrigger_scan` runs every step for every unit of every faction: Surge when an enemy is in range, Brace same (marks `brace_auto`), Barrage on nearest enemy in range, Rally when a friendly is under 50% HP in 400 wu, Fortify with 2+ friendlies in 350 wu (`fortify_auto`, no x0.4 speed). Suppressed while the unit has an order (`suppress_auto`).
Cooldown start also differs. Surge: Python `ability.py:63-68` cooldown 1,500 from activation; C `unit.c:1299-1310` sets cooldown 1,500 when the 60 ticks END (cycle 1,560). Barrage: Python from activation (`ability.py:117`); C from impact (`unit.c:1333`). Brace Python needs cooldown 0 to cancel (`ability.py:28`); C toggles any time (`unit.c:1224`).
Fight effect: C fights have Surge (x2 damage, x2.5 speed), Brace (x0.5 damage taken), Fortify, Rally, Barrage firing unprompted from tick 1. Python fights without a commanding script have none of them.
SUSPECTED gap-closer: `behavior_runner.py` (not in my list, not read) may issue `activate_ability` for Python enemies.
Bible: R-086-08 says enemy units auto-activate on threshold; "regardless of faction" is C's reading. Q-086-02 (Rally threshold) open.

## G06. Cover disc blocks fire in C

Python: no cover blocking of fire. `damage.py:41-43` blocks only through navmesh cells (obstacle density >= 0.7, `movement.py:661-664`). Asteroids block only through the visibility gate (G01). `get_damage_reduction` has no cover term.
C: `tactical_move.c:1470-1477` samples every 1 wu strictly between shooter and target; any `cover_density > 0` returns "cannot shoot". `tactical_mapgen.c:586-591` returns density 1.0 inside any recorded disc. Unlike vision (`fog.c:272` exempts a disc that contains an endpoint), this has no endpoint exemption.
Fight effect: no shot passes through, into, or out of a cover disc. `mission.c:2455` adds a 400 wu radius disc at map centre for every mission, which is where the objective is. Fights inside or across it produce no damage.
Bible: R-098-02 "blocked exactly as vision is" (C's fire rule is stricter than C's own vision rule). Q-098-01 (open) names this: "a unit inside a cover disc is unshootable". R-084-05 "target behind cover, hit by attacker who can see it: damage unmodified".

## G07. Map content

Python: `tactical_map.py` gradients (obstacle, cover, interference with linear/quadratic/constant falloff), spine nodes, vantage nodes, drifting nodes, asteroid field with 3D cylinders, layer masks, layouts from `map_generator.py`.
C: `tactical_mapgen.c:412-424` `om_map_generate`, `om_map_generate_gradients`, `om_map_generate_spine` are STUB. `tactical_mapgen.c:566-571` gradient sample is binary discs ("the intensity-and-falloff gradient model (ALG-71) belongs to the E-17 map generator, held"). Only caller of any map-feature adder in csrc: `mission.c:2455` (one cover disc) plus spine node and two spawn points (`mission.c` 2453-2457). No caller of `om_map_add_obstacle`, `om_map_add_interference_zone`, `om_map_add_vantage_node`, `om_map_set_obstacle_density`. `om_pipe.c` ~1198 sends `obstacles: []`.
Fight effect: live C battle is an open plane with one cover disc: no interference, no vantage, no obstacles, no asteroids. Everything in G08, G01 (interference), G20 has nothing to act on.
Bible: E-12 S-090/S-091 and E-13 S-097 specify these; E-17 owns generation.

## G08. Routing, terrain, bounds

Python: `movement.py:360-365` A* route on a 100 wu navmesh built from obstacle density (>= 0.7 blocked, asteroids >= 8 radius blocked), cached, LOS-straightened (`movement.py:105-210`); waypoint arrival radius 30 (`:370`). `movement.py:433-443` obstacle repulsion (math: `-steer * density` then normalise is a direction no-op, and at density 1.0 the steer vector is zero so the unit stalls). `:457-459` clamps to map bounds. No terrain speed penalty.
C: `tactical_move.c:1246-1348 om_move_tick_unit` heads straight at destination; no route. `om_navmesh_find_path` (`:1673`) returns a BFS length only, never used by movement (comment `:927` "Never exercised"). `om_steering_get_obstacle_repulsion` (`:1750`) is a readout, not applied in the tick. `om_move_terrain_multiplier` (`:322,1330`) slows by (1 - 0.5 d) in [0.3, 0.7], zero speed above 0.7, from `density_cells` that nothing fills (G07). No bounds clamp anywhere in `tactical_move.c` or `unit.c` (no canvas size known to movement).
Fight effect: C units walk through where Python units would route around, and can walk off the map. If density cells were ever fed, a unit entering a >0.7 cell gets speed 0 and has no route out.
Bible: R-097-01 (route grid + straighten), R-097-06 (terrain slow), R-097-09 (repulsion) describe features C has built but not wired. R-095-04 slot walkability: C checks `om_move_slot_blocked` (`:888`) against empty tables.

## G09. First volley delay

Python: `unit.py:98` attack timer starts 0.0; `damage.py:21-24` fires on the first tick with a valid in-range visible target.
C: `unit.c:778` cooldown 0.0; `unit.c:1605` adds one tick per step; `unit.c:1738` needs `cooldown >= interval`. First shot after one full interval from spawn (16 ticks Raider, 60 ticks Bombard). Cooldown charges while idle or moving, so only matters when the fight starts within one interval of spawn (spawn-in-range fixtures, skill lab).
Also tiny: Bombard repeat cadence is 61 ticks in Python (float countdown, I ran it) vs 60 in C. All other intervals match tick for tick.
Bible: R-084-01 "When its attack timer elapses" silent on initial value.

## G10. Pursuit side-differences (known gap not repeated)

Known gap (direct position write, hold on any enemy in range): `unit.c:1525 om_tac_step_toward`, `unit.c:1741-1754`. E-11 R-087-04 now pins the Python behaviour. Further differences in the same block:
- Gate: Python `damage.py:262-266` requires the enemy in the unit's own visible set. C `unit.c:1747` `om_tac_nearest_hostile(sensor_radius)` has no visibility test (R-087-04 says "visible").
- Cadence: Python picks the pursuit target only on the unit's cohort turn (`damage.py:227-228,256-277`). C every tick.
- Persistence: Python after arrival keeps `attack_moving` set (`movement.py:395-399`), so an idle ex-attack-mover keeps chasing visible enemies in sensor range forever. C `unit.c:1752` drops the order on arrival when nothing is near, then it is just idle.
- Collision: C pursuing units are marked `engaged` (stationary) in the collision pass (`tactical_move.c:848`), so two pursuers, or a pursuer and a holder, are never pushed apart (`:1096-1103`) and can stack. Python treats them as non-moving too (`movement.py:600-614`) but pushes 50/50 if either moved.
- Stale targets: Python keeps an out-of-range alive target in `auto_engage_target` between cohort turns (`damage.py:220-228`), C clears it every tick (`unit.c` drop block ~1690-1706).

## G11. Group orders

Python: `command.py:50-61` attack-move goes through `apply_group_move` (formation offsets from centroid, scatter fallback >450, slot walkability), same as move (`movement.py:667-732`). No speed cap: each unit at own speed. Group ends when the moving set empties (`movement.py:512-513`: engaged units are removed from `moving` permanently) or centroid within 30 (`config.py:601`). On end, EVERY member's move target is cleared (`:528-536`) so an attack-moving group that all engaged does not resume its path after the fight (flags stay set).
C: pipe `om_pipe.c:1738-1746`: `move` -> `om_command_group_move` (`tactical_move.c:1522`: slots, scatter, speed cap = slowest member fixed at order time); `attack_move` -> `om_command_attack_move` (`unit.c`) -> per-unit `om_command_move` to one shared point, no slots, no cap. Group arrival tolerance 22.5 (`tactical_move.c:1351`); group end only flags the group inactive (`:1368`), units keep walking to their own slot. Attack-movers resume their point after a fight (`om_tac_release`, `unit.c:~1550`).
Fight effect: Python attack-move columns keep formation and stop marching after one full engagement; C attack-move units all converge on one point and always resume. Python move groups are not slowed to the slowest; C move groups are.
Bible: R-095-01 (cap, Q-095-01 closed (a): a movement ability detaches the unit; C keeps the fixed cap, SUSPECTED unwired), R-095-02..04 slots (Python and C both slot move; only Python slots attack-move), R-095-05 (1.5 x radius, matches C), R-096-02 (resumes toward the point, matches C).

## G12. Return fire

Python: `damage.py:78-130`. Applies to any non-plain-moving unit with no target, including attack-moving ones. Picks the FIRST same-layer attacker in hit order (lowest id). If out of range: sets `attack_moving`, anchors, overwrites its move target with the attacker position (destination lost). Cross-layer only attackers: flee 200 wu by ordinary movement.
C: `unit.c:1653-1669` only when `order == NONE` and no target. `last_attacker` is the last writer (`unit.c:811-816`, highest id in the pass). In range: target. Out of range: attack-move to attacker. Different layer, stealthed, or non-combat unit: flinch 200 wu by direct write (`unit.c:1574-1581`, `1642-1651`): no steering, no firing, ignores everything until arrival.
Fight effect: Python attack-movers hit by long-range fire turn on the shooter and abandon their march; C ones keep marching. Which attacker is chosen differs with several shooters. C flinchers cannot fire while fleeing; Python fleers can.
Bible: R-087-06 "idle unit with no target and no order" (matches C). R-087-01 flinch. Q-088-01 (b) closed: also flinch when visible but unreachable; neither side implements that branch.

## G13. Steering details

- Sweep: Python `movement.py:421` tries +30,-30,+60,-60,+90,-90 only after the straight probe is blocked. C `tactical_move.c:330-338`, `om_constants.h:592-593` tries 13 angles at 15 deg steps: 0,+15,-15,...,+90,-90 (R-097-03 "fixed order"). Python never takes 15/45/75.
- Nothing clear: Python `movement.py:419` steers straight at the blockers. C `tactical_move.c:1325` waits that tick. R-097-03 "if none, it waits" matches C.
- Layer: Python `movement.py:248` only same-layer units block. C `om_move_probe_gather` (`:975-1027`) has no layer field; every unit blocks.
- Group mates: C `:989,1017` excludes same-group units from probe blockers; Python has no group exemption.
- Snapshot: Python probes against start-of-tick positions (`movement.py:311-325`); C probes live slots, so lower ids move first and higher ids see their new spots.
- Detour: Python decrements 60 by distance moved (`:463`); C by straight distance from origin (`:1281-1288`). Python commits only if straight was blocked (same as C).
- Facing during detour: C snaps facing (R-097-04); Python no snap (cosmetic).
- Ally-only: both treat enemies as blockers; R-097-03 says "ally". C header `:36-42` documents this approximation.

## G14. Collision and arrival

- Layer: Python `movement.py:576` skips other-layer pairs. C `tactical_move.c:1073-1119 om_move_collide_pair` has no layer test.
- Bounds and walls: Python clamps pushed positions to the map and slides along navmesh blocks (`movement.py:621-651`). C does neither.
- Driver set: Python only units that moved start pair checks (`:473-477`). C every unit, ascending id (`:1137-1163`); results match for pairs where one side moved.
- Stationary vs stationary: Python splits 50/50 when either member moved (`:613-614`). C does nothing (`:1096-1103`), so a unit that arrives onto an occupied slot stays overlapped.
- Both moving: 50/50 both. One stationary: mover takes all both sides. Exact overlap: lower id +x (R-097-07) C; Python `dx=-1` for lower id (`:590`), i.e. opposite sign convention.
- Arrival: Python stops within 22.5 (formation) or 30 (waypoint) of target without snapping (`movement.py:372-408`). C steps exactly onto the slot and clears the destination (`tactical_move.c:1333-1336`, R-099-04).
- Iterations: both 3.

## G15. Warden aura

Python `ability.py:297-309` reduction: first Warden within 300 gives 0.10, `break`. `:216-233` healing: first Warden gives 0.075/tick, `break`. No stacking.
C `unit.c:852-873` reduction 1-(0.9)^n; healing `unit.c:876-898` sums per Warden. Bible R-083-03 / Q-084-01: 0.10, then 0.05 (two Wardens = 0.15). C's comment says its form is "equivalently" that, but 1-(0.9)^2 = 0.19, so C's second Warden adds 0.09 not 0.05. Python gives 0.10 for any number. Neither equals the bible for n >= 2; surfacing for Westley, not deciding.
Fight effect: Warden clumps are stronger in C.

## G16. Bastion category rule

Python `damage.py:135` straight matrix. Strike hits Bastion x1.5.
C `unit.c:805-809 om_resolve_hit_multiplier` clamps any multiplier above 1.0 to 1.0 when the TARGET is a Bastion (Strike->Bastion 1.5 becomes 1.0). Also applies to Barrage and Bombard AoE.
Bible: R-081-03 (Bastion survives 4 Raiders >= 20 s) is the rule C implements.

## G17. Barrage

Python `ability.py:107-123,236-271`: needs a live engaged target; hits all same-layer enemies within 100, NO 4x cap, no Bastion rule, no reduction terms. Cooldown 1,800 from activation.
C `unit.c:1174-1196`: any point from the command (`om_ability_manual_activate`, no range check) or auto on nearest in-range enemy; cap 4 x (base x 3.0); Bastion rule; cooldown 1,800 from impact.
Bible: R-086-05 cap matches C.

## G18. attack-target

Python `command.py:63-67`: sets `auto_engage_target` only. No chase, no range or faction check, does not clear `plain_moving` or `attack_moving`. Next cohort turn replaces an out-of-range target with the nearest in range (`damage.py:220-247`).
C `unit.c` `om_command_attack_target` + `unit.c:1678-1690`: moves toward target, holds and fires in range with `om_command_attack_target_kiting` (a "kite" to its own spot), tracks target visibility through faction-shared `om_fog_faction_sees`, goes to last seen on loss (S-093).
Bible: R-096-04, Q-097-01 (a) match C. C keeps faction-shared vision here only; fire (G01) ignores it.

## G19. Tick rate above 1,000 units

C `unit.c:140-141,399-405`: above 1,000 live units each step spans 2 base ticks; every per-second quantity scales. Python: none; `unit.py:5 MAX_UNITS = 1024`. Bible R-099-03.

## G20. Fog minor

- Vantage extra layer: Python `fog_of_war.py:35-44` gives layer diff 3 a factor min(0.2 x 2, 1) = 0.4. C `fog.c:597` returns 0.2.
- Elevation sensor bonus 0.15/tier: C `fog.c:340-355` applies in `om_unit_can_see`; Python has none. Only matters for units spawned via `om_unit_spawn_with_elevation` (`fog.c:610`), which nothing in csrc calls, so tier is 0 in play. SUSPECTED inert.
- Pulse: Python has the state and timers (`fog_of_war.py:19-32`) but I found no caller outside tests; C has only constants (`om_constants.h:563-565`), no code.
- Asteroid LOS: Python 3D cylinder with z (`tactical_map.py:213-277`). C 2D disc, any height (Q-098-01).
- Interference: both linear falloff, sum, clamp, observer position only (R-090-01..03 match). C zones: none created in play.
- Faction sharing: neither shares vision for fire; C shares it for attack-target tracking.

## G21. Reinforcement structures

Python `reinforcement.py:23-81` does its own census (units in 300 wu, any layer), captures after 10 s when exactly one non-owner faction and no owner, produces by power, spawns on the structure's layer, spawn offset from the global unseeded `random`.
C `tactical_support.c:633-669` advances capture only from `capturing_faction` and `contested`, "the orchestrator's job". Callers of `om_structure_set_capturing_faction` / `om_structure_set_contested` in csrc and pipe: none. Capture never advances in play. Production spawns on layer 0 only (`:845`), deterministic RNG (`om_rng_draw`, a C improvement). `om_structure_apply_damage` has no caller; Python has an hp field and no damage code either.
Bible: R-127-01/02 census; E-15.

## G22. Facing

Python `facing.py:59-77`: faces engaged target within 1.5 x range, else move target, else velocity. C `tactical_move.c:1274`: stationary units return before any facing update, so a firing, stationary unit never turns to its target. Moving units face heading, kiting faces the target. Facing has no damage or flank effect in either sim.
Bible: R-100-01 says it faces the target (Python). R-100-03 retreater faces pursuer (C kiting).

## G23. C fixed caps with no Python limit

`tactical_move.c:62-69,88`: 64 groups (65th overwrites the last), 64 group members tracked for arrival, 1,024 density cells, 256 route cache entries, 1,024 queued orders, discovery loop ids 1..255 (`:841`). `tactical_mapgen.c:109-113`: 256 cover, 256 obstacles. `fog.c:105-108`: 64 zones, 32 vantage, 512 elevation-tracked units. `tactical_support.c`: 64 structures. Python navmesh for a 24,000 wu canvas has 57,600 cells.

## G24. Low impact

- Cohort phase: Python `damage.py:12,189-191` module-global counter, never reset between battles, ids from 0. C `unit.c:1710` `unit_id % 4 == (current_tick+1) % 4`, ids from 1.
- Nearest tie-break: Python first in hash cell order (strict `<`, `damage.py:242`); C lowest id (`unit.c:1478` with a tie window, `OM_TIE_EPSILON`).
- Python stale target (G10) and no stealth; C stealth flag (`unit.c`, `om_unit_set_stealth`) and non-combat units (supply, evacuation: never fire, flinch).
- Hold semantics: C halts on ANY hostile in range even between cohort ticks (the known gap); Python needs its own target.
- Commands: Python applies at tick start from a queue (R-096-07). C applies on arrival, replaying movement to the current tick first (`tactical_move.c:1408`).
- Verbs: Python `command_ingest.py` has `layer_hard_transfer` (instant), `layer_preference_set` (stored, unused), control groups. C pipe (`om_pipe.c:1738-1760`) has move, attack_move, attack_target, activate_ability, and rejects `hold`. `om_unit_teleport` ignores its layer argument (`tactical_move.c:1955`); no layer change exists in C. No layer-transition time is simulated in either sim.
- Recon: C freezes all movement in recon (`tactical_move.c:1386`, R-092-02); Python has no phase.
- Python backswing counts down at the start of movement (`movement.py:330-331`), C after the AI pass (`unit.c:1383`); lock lengths differ by about one tick.

---

## Constants

Equal (Python `config.py` vs `om_constants.h` / local defines): all six roster rows (hp, damage, interval, range, speed, sensor, AoE), the 3x3 category matrix, AoE cap 4.0, Surge/Intercept/Brace/Rally/Warden/Barrage/Fortify values, cone 0.5/0.2, vantage x2 + 1 layer, pulse 500/40/400, backswing 0.5, cohort 4, leash 200, flee 200, collision radius 15, probe 40, detour 60, avoidance 50, collision iterations 3, arrival mult 1.5, magic box 450, navmesh cell 100, facing 6.0/4.0/2.5, tick rate 20, structure radius 300 / 10 s / HP 3,000 / production 30 s / power norm 100, reduction cap 0.9.

Different:
1. Steering sweep: Python 6 angles at 30 deg (`movement.py:421`); C 13 at 15 deg (`om_constants.h:592-593`).
2. Group arrival: Python `config.py:601` 30 wu (2 x radius) centroid; C 22.5 (`tactical_move.c:1351`).
3. Navmesh block test: Python `>= 0.7` (`movement.py:28`); C `> 0.7` (`om_constants.h:584`, `tactical_move.c:323,889`).
4. Unit store: Python `unit.py:5` 1,024; C `OM_MAX_UNITS` 10,100.

Present in one side only: C: terrain slow coeff 0.5 and low threshold 0.3 (`om_constants.h:585-586`; Python uses 0.3 only inside repulsion `movement.py:439`), LOS step 1.0, high-load 1000 / period 2 (`unit.c:140-141`), Rally auto 0.5 HP (`unit.c:149`), tie epsilon. Python: asteroid block radius 8, LAYER_Z tables, spatial hash sizes.

## STUB / approximation / unwired list from C comments, and whether Python had the real thing

| C site | Note | Python had it? |
|---|---|---|
| `tactical_mapgen.c:412-424` | map/gradient/spine generate STUB | yes (`map_generator.py`, out of my scope) |
| `tactical_mapgen.c:566-571` | binary gradient, falloff "held" | yes, linear/quadratic/constant (`tactical_map.py:161-182`) |
| `tactical_mapgen.c:595,621,626,631` | layer accessibility, simulation coupling, drifting node, flank checks STUB | accessibility yes (`tactical_map.py:196`) |
| `tactical_move.c:927` | BFS path "never exercised" | yes, real A* |
| `tactical_move.c:36-42` | ally-only probe and turn-rate bucket approximated (no faction/category accessor) | Python probes by layer, uses category |
| `tactical_move.c:22-31` header | says attack-move / attack-target never call into this module: stale, `unit.c` now does | n/a |
| `tactical_move.c:1750` | repulsion is a readout only | yes, applied (direction no-op, G08) |
| `unit.c:1745-1749, 2265-2268` | elevation damage bonus, `set_elevation_tier` STUB | no (flag off, `config.py:535`) |
| `tactical_support.c:870-875` | contested scan "best-effort", cannot tell enemy from friend | n/a |
| `tactical_support.c:638-640` | capture census left to caller, no caller | yes, wired |
| `fog.c:335-339` | era-flag gate ignored, elevation bonus always on | no |
| `fog.c:542` | `om_unit_acquire_target` never called by the tick | n/a |
| `om_pipe.c` ~1198 | obstacles list always empty | n/a |
| `om_pipe.c:1751-1757` | `hold` verb unsupported | no hold in Python either |

## Bible alignment, quick index

C matches: R-081-03 (G16), R-083-03 intent (G15), R-084-04/R-096-02/R-095-05/R-099-04 (G14), R-086-05 cap (G17), R-095-01 (G11), R-096-04 (G18), R-097-03 wait (G13), R-097-06 / R-097-01 / R-097-09 are built in C but fed nothing (G08), R-099-03 (G19), R-092-02 (G24).
Python matches: R-087-04 as rewritten (visible gate, cohort pursue; G10), R-097-05 layer filter (G14), R-097-01 (G08), R-100-01 (G22), R-087-06 only partly (G12), R-093-02 (G01).
Neither: R-086-02 (G04), R-087-01 / Q-088-01 (b) (G12), R-083-03 numbers for n>=2 (G15), R-098-02 as written (G06), R-086-03 cooldown gating.
