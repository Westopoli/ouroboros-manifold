# Does a unit that sees an enemy attack it? Facts as of 2026-10-19

Read from origin/main a13ad73c; lab from origin/push/labrev2-lab 4c638fc0 and origin/push/labrev2-l8 cb831aab (L8) and -l8-tests 33600785; guard step from origin/push/labrev2-e4 f9e4a436.
Paths below are repo paths; line numbers are those blobs. Nothing in the repo was edited.

Short answer: no rule says "sees it, attacks it" for an enemy outside weapon range. Every rule that names the trigger says "in range" or "enters attack range". The engine matches those rules. One rule line (A199, Westley 2026-10-03) says the opposite for an attack-moving unit marching to its point. The engine's acquisition radius is the weapon range, not the sensor radius.

---------------------------------------------------------------------------------------
## (A) The bible

### A.1 Rules that bear on "sees it, attacks it" (verbatim)

docs/bible/epics/E-11-units-and-combat.md
- l.138 (S-087 story): "As a commander, I want every unit on both sides to flinch from what it cannot fight, obey my orders, and otherwise shoot the nearest enemy in range, so that my skill is direction, not babysitting."
- l.140: "Direction changed 2026-10-02, rewrite pending: an idle or attack-moving unit engages the nearest enemy within its type's reach that its side can see, on its own layer or another (E-01 S-164, R-008-04; E-12 R-093-02). The rules below are what the game does today."
  (No Westley quote is attached. "Reach" is defined in E-01 S-164 as layer offsets, R-164-01: "it names the layer offsets it can fire at", not a distance. The sentence does not say "moves into range".)
- l.143 R-087-01: "Given a unit taking damage from an attacker it cannot see or cannot reach, When the loop runs, Then it moves 200 wu directly away from the damage direction and stops; once the attacker is visible and in range it stands and fights."
- l.144 R-087-02: "Given a unit with an active player order, When the loop runs, Then the order wins over auto-engagement; a plain move never acquires or returns fire."
- l.145 R-087-03: "Given an idle or attack-moving unit with an enemy within attack range on its layer, When targets are evaluated, Then it attacks the nearest such enemy; an engaged target still alive and in range is kept."
- l.146 R-087-04: "Given an attack-moving unit with no target within its attack range, When evaluated, Then it keeps marching on its slot and route (R-095-02, R-097-03), steering around units in its way, and does not walk toward an enemy it merely sees in sensor range; the formation holds until shooting, not until sight (Westley, 2026-10-03, A199; marked for review in playtesting). It halts and fires when an enemy is within its attack range and it can shoot it (...), and pursues an acquired target that leaves that range under the leash (R-087-05)."
- l.147 R-087-05: "Given an attack-moving unit that acquires a target, When it does, Then it anchors at its position, and if the unit itself pursues more than 200 wu from the anchor it drops the target and resumes its attack-move (R-096-03). ..."
- l.148 R-087-06 (return fire): "Given an idle or attack-moving unit with no target taking damage, When hit, Then it targets the attacker (return fire); if the attacker is out of range it pursues the attacker as an engagement (the R-096-03 leash applies). For an attack-moving unit the pursuit is one engagement of its order: when the attacker dies or leaves, it resumes toward its original ordered point (R-096-02, Westley 2026-10-13: ...; the Architect extended it to the redirect 2026-10-19 ...). An idle unit has no point and holds where the pursuit ends. A plain-moving unit and an already-engaged unit ignore incoming damage for targeting. The engine today overwrites the ordered point with the attacker's position (unit.c last_attacker branch); the fix is in the lab rev 2 piece E1."
- l.150 R-087-08: "each unit re-acquires on every 4th tick (cohort stagger) and validates its current target every tick."
- l.151 R-087-09 (blocked line, give-up of a target): "...if it finds none within 1 s (20 ticks) it drops the target and acquires another (Westley, 2026-10-07: ...'a unit gives up to pick another target if it can't find a firing spot within 1 second')."
- l.156: "The flinch also fires when the attacker is visible but out of range with no path to it on the unit's layer; that branch is not built, and the code flinches only when return fire fails to find the attacker."
- l.189 R-202-01 (workers): "it never acquires a target and never returns fire, it flinches from damage".
- l.219 R-204-03: "Given an idle or attack-moving unit with an enemy structure within its reach and visible to its side, When targets are evaluated, Then it attacks an enemy unit in reach first, and an enemy structure only when no enemy unit is in reach (Westley, 2026-10-07: "#5: B")."
- l.24 (60-second check): "the Bombards fire on the Vanguards as they close; without the Raider the Bombards hold fire until the Vanguards are within their 300 wu sensor (E-12 R-093-02)."

docs/bible/epics/E-01-layer-system.md
- l.156 R-008-01: "Given an attacker on layer 3 and a visible enemy on layer 3 in range, When the attacker is idle or attack-moving, Then it engages."
- l.157 R-008-02: "Given an attacker on layer 3 and a visible enemy on layer 4 in range, When the attacker is idle or attack-moving, Then it engages only if its unit type's reach includes one layer up (S-164); ..."
- l.159 R-008-04: "Given an attacker whose side cannot see a target (S-005, E-12 R-093-02), When it would attack that target, Then it does not: a unit never fires at a target its side cannot see, on its own layer or another; a target seen by any friendly unit or revealed by a ping may be fired at."
- l.244 R-164-02: "Given a target at a layer offset outside the attacker's reach, When the attacker would fire, Then it does not, whatever the distance."
- l.113 (Westley, 2026-10-05, verbatim): "Space eras and Ground eras are different in terms of vision. Ground eras are just like Starcraft 2, high ground can see down, low ground can't see up. ..." (vision model only, nothing on engaging.)

docs/bible/epics/E-12-fog-and-sensors.md
- l.18 (Purpose): "Fog binds every side by the same rule: a unit acquires, pursues and fires only at what its own side can see, so a spotter or a ping lets a long-range unit fire and losing sight stops it."
- l.91 R-093-02: "Given any unit of any side, When it acquires, pursues or fires at a target, Then the target is in its side's visible set: ... the rule is the same for the player's units and the enemy's (Westley, 2026-10-02). A unit whose sensor is shorter than its range (Bombard, Bastion: sensor 300) fires beyond its sensor only at what another friendly unit or a ping sees."
  (This makes sight a necessary condition for acquire, pursue and fire. It is not a sufficient one.)
- l.185 (Ways this could be wrong): "A unit fires at a target that no unit of its side sees."

docs/bible/epics/E-13-movement-and-command.md
- l.45: "The guard stance joined the commands 2026-10-13 (S-208, R-096-08). An attack-moving unit engages what is within its type's reach and visible to its side, on its own layer or another (E-01 S-164, R-008-04; E-12 R-093-02). The rules below are what the game does today."
- l.49 R-096-02: "Given an attack-move, When an enemy enters attack range on the unit's layer, Then the unit halts and fires; when the target dies or leaves range it resumes toward the point. ... (Westley, 2026-10-13, option (a): an attack-move is not finished until the unit reaches its point; his 2026-10-02 words for the lone unit, "It should resume its prior goal after the fight is completed", now hold for a group too). ..."
- l.50 R-096-03: "Given an attack-move engagement, When the unit itself has pursued more than 200 wu from its anchor ..., Then it drops the target and resumes; ..."
- l.48 R-096-01: "Given a plain move, When the unit travels, Then it acquires no target, returns no fire, and does not stop when hit."
- l.51 R-096-04 (attack-target): "...the unit moves toward E if out of range and attacks E in range until E dies or a new order arrives; if E becomes invisible the unit moves to E's last known position and idles there."
- l.53 R-096-06: "Given any other command name (patrol, hold, stop, follow), When received, Then it is rejected with a reason and no state changes."
- l.55 R-096-08 (guard): "...each unit takes its position as its post and engages any target its side can see (E-12 R-093-02), stepping toward it no farther than `GUARD_RADIUS` = 200 wu from the post ... firing whenever the target is in range, returning to the post when the target dies or when engaging it would take the guard past the radius; it never crosses the radius and never marches; as built 2026-10-14 the walk is toward same-layer targets only ... return fire (R-087-06) is untouched."
- l.172 R-208-01: "the units hold the post and engage what their side can see (E-12 R-093-02) within `GUARD_RADIUS` of it, returning to the post when the target dies or leaves the radius, never chasing past it (R-096-08)."
- l.100 R-099-04: "...it has arrived where it stands, without snapping to the point: its destination is cleared and it is stationary from that tick onward, and any later displacement by collision or direct position change leaves it at the new position with no re-approach."
- l.101 R-099-05: "Given a unit under a group move whose own slot it cannot reach (a stopped neighbour holds it), When it has been within 75 wu ... for 40 consecutive ticks (2 s) without arriving, Then it ends its order where it stands, the same state as an arrival (destination cleared, stationary from that tick onward); ..."
- l.217 (invariant): "Under a plain move, no target is ever acquired."

docs/bible/game_bible.md: no line on engaging, acquiring or idle units (hub l.84 lists the order set only). docs/bible/algorithms.md:
- l.266 ALG-62: "...on its cohort tick (...) it acquires the nearest same-layer enemy within attack range; failing that, an attack-moving unit with sensor radius > attack range acquires the nearest visible same-layer enemy within sensor radius and moves toward it. Return fire: an idle unit with no target and no order that takes damage targets the attacker. Flinch: ..." followed by "Direction changed 2026-10-02, rewrite pending: pursuit goes through ordinary movement and holds only while the unit's own target is in range, return fire also turns attack-moving units, a unit acts only on what its side can see, ... The text above is what the game does today."
  (Stale in the "failing that" clause: A199 deleted pursuit on sight; ALG-62 still describes it.)

### A.2 Westley's own words (file:line, date)

- docs/northstar/plans/2026-10-01-architect-rulings-2.md:638 (A125, 2026-10-02): "A lone unit on attack-move: "It should resume its prior goal after the fight is completed.""
- same file :635 (A125): "Sight: a unit fires at what its side sees ("Side's shared sight"). Siege units, whose sensor is 300, fire beyond it only with a spotter or a ping; accepted."
- same file :640 (A125): "Target choice: "I had imagined that units would only... just fire at the closest unit and we wouldn't have any other way. And I want to retain that, but ...""
- same file :853 (A199, 2026-10-03): "Attack move should hold formation until shooting, yes, rather than sight. But this is something we might change when it comes to play testing." (The question put to him in A198 :849 was: "Whether attack-move should hold slots until a unit is in attack range (or until the group's front is), rather than at first sight". He answered about FORMATION during the march. He was not asked about idle or arrived units.)
- docs/northstar/ambiguity_register.md:35 (Q-005-03, 2026-10-01): "...both units can just fire back at each other as soon as they see each other if they have the same range." (This is the design worry that the layers need an action; it takes "fire at each other as soon as they see each other" as the baseline between equal-range units.)
- docs/northstar/ambiguity_register.md:128 (Q-088-01, 2026-09-12): "(b), also flinch when visible but unreachable. Flinch if attacker is not visible OR if visible but out of range with no path to it on current layer."
- docs/northstar/ambiguity_register.md:278 (Q-096-01): 2026-10-01 "Yes a guard stance is fine"; 2026-10-13 "B, record this as a decision in the whole repo for the whole game, not just the simulator" (radius guard).
- docs/northstar/plans/2026-10-01-architect-rulings-2.md:824 (A188, provisional): Architect text, no Westley words.
- docs/northstar/plans/decision_pack_2026-10-18/*.md and the other rulings files (2026-10-01-architect-rulings.md, 2026-10-03-finish-loop-rulings.md): grepped for auto-attack, chase, "sees", "on sight", "within vision": no Westley sentence on idle units engaging what they see.
- docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md:88 (decision 28 point 2, Architect, 2026-10-19): "...an arrived unit does not close on a visible enemy outside its range (no rule in the bible makes an idle unit chase; R-096-02 engages what enters range). The engine is per rules here; not a defect."

### A.3 Reading

No rule says a unit that merely sees an enemy outside weapon range attacks it. The trigger words in every rule that sets one are "in range" (R-087-03, R-008-01, R-008-02, R-096-02) or "enters attack range"; R-087-04 states the opposite for the march ("does not walk toward an enemy it merely sees"), with Westley's A199 words behind it, scoped to formation and marked for playtest review. Sight appears as a necessary condition (R-093-02, R-008-04), never as a trigger to move. Two lines lean Westley's way and are not rules: E-11 l.140 and E-13 l.45 ("Direction changed 2026-10-02, rewrite pending: an idle or attack-moving unit engages the nearest enemy within its type's reach that its side can see"), which can be read as "engages what it sees", but "reach" is defined as layer offsets and the rule bodies below them say "in range", so they do not settle it. R-087-06 is the one rule where a unit moves toward an enemy it did not choose to approach, and only after being hit. Decision 28's claim "no rule in the bible makes an idle unit chase" is correct as to rule text. Q-005-03 (Westley, 2026-10-01) and R-208-01 (the guard "engages what their side can see ... within GUARD_RADIUS") show the intent that a unit engages what it sees at least for the guard; the guard is the only stance whose rule says "engages any target its side can see" and lets it step.

---------------------------------------------------------------------------------------
## (B) The engine (csrc/unit.c unless named; origin/main a13ad73c)

Default settings (tactical_move.c l.379-382, enum in ouroboros_sim.h l.1008-1014): OM_TP_PURSUE_BY_STEERING 1, OM_TP_TARGET_BY_SIGHT 1, OM_TP_LEASH_BEFORE_DAMAGE 0. The switch-0 arms are PP baselines, not live.

### B.1 Acquisition and fire
- om_tac_unit_ai (l.2034-2242) is the whole per-unit decision, run once per unit per tick from om_tactical_ai_tick (l.2271).
- Acquire, l.2164-2175: on the unit's cohort tick (`om_unit_cohort_slot == tick % OM_TARGETING_COHORT_COUNT`, l.1710, 2165), when it has no target (or a more damaged enemy exists, or its target left range), and the order is not attack-target, it calls `om_tac_nearest_actable(w, st, u, u->attack_range)` (l.2006) then `om_tac_pick_across` (l.1731). THE SEARCH RADIUS IS `u->attack_range`. Sensor radius is not an argument anywhere in the live acquisition path.
- Sight check: `om_tac_nearest_actable` -> `om_tac_may_act_on` (l.1178) -> `om_tac_faction_sees` (l.1165: not stealthed, and `om_unit_can_see` or `om_fog_faction_sees`, fog.c l.486). So visible-to-the-side is a filter on candidates already inside weapon range.
- Reach/range: `om_tac_in_reach` (l.572), `om_tac_in_range` (l.1716: in reach and within attack_range times the layer-offset range multiplier).
- Fire: not at acquisition. `fire_pending` set at l.2219; `om_tac_fire_pass` (l.2246) fires if `om_tac_in_range` and cooldown ready and `om_combat_can_shoot` (tactical_move.c l.2707, terrain and cover only; units never block fire).
- There is no `om_combat_can_engage` in the source.

### B.2 What can set a destination from another unit's position (the complete list)
1. unit.c l.2109-2114, return fire out of range: `u->order = OM_ORDER_ATTACK_MOVE; u->order_x = atk->x; ... om_command_move(w, &u->unit_id, 1, atk->x, atk->y)`. Fires for an idle or attack-moving unit with no target that is hit by an attacker it can reach (R-087-06). This is the only live "close on an enemy" for idle and attack-moving units. It overwrites the ordered point (E1/E1b fix pending, not on main).
2. unit.c l.2127-2137 and l.2194-2203, attack-target order: moves to the target (`om_command_move(... t->x, t->y)`); if the target leaves the side's sight, `om_command_attack_move` to the last seen point (R-096-04 / S-093).
3. unit.c l.2231-2236, switch-0 baseline arm only (`else if (u->order == OM_ORDER_ATTACK_MOVE)` when pursue is 0): `om_tac_step_toward` a seen enemy. Dead in the default build. Comment l.2176-2178: "A199 (R-087-04): no pursuit on sight ... The old pursue-on-sight call (om_tac_pursue_goal) is deleted".
4. fog.c l.687-714 `om_unit_acquire_target`: nearest enemy the unit `om_unit_can_see`s inside the observer bound -> `om_command_attack_target(w, &unit, 1, best)`, which walks the unit to it. This is exactly the behaviour Westley's sentence describes. It is declared in ouroboros_sim.h l.1608 and has no caller in csrc: not called by the tick or a pipe handler (docs/northstar/research/layer_dynamics/port_gap_audit_2026-10-02.md:246 lists it "never called by the tick"; only tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py:83 calls it). Unwired.
5. enemy_macro.c l.504/514/523/554: the enemy faction's macro behaviour issues attack-move (attack), plain move (DEFEND "move to the objective and stay there", RETREAT). Orders to a point, not to a unit.
6. E4 (origin/push/labrev2-e4 f9e4a436, not on main): `om_tac_guard_pick`, `om_tac_guard_can_engage`, `om_tac_guard_walk` step a guard toward a seen target within OM_GUARD_RADIUS 200 of the post.

### B.3 Return fire and give-up
- R-087-06 return fire: `om_tac_note_attacker` l.1005 records the lowest-id same-layer attacker on each hit; consumed at l.2096-2117. In range: `target_id = attacker`. Out of range: l.2109-2114 as B.2 item 1 (becomes an attack-move toward the attacker's position, `halted = 0`). Guard: only if it can shoot the attacker, never walks (l.2102-2104). Cannot reach or stealthed or noncombat: `om_tac_start_flinch` (l.1974) runs 200 wu away (OM_RETURN_FIRE_FLEE_DIST) for an unordered unit.
- R-099-05 give-up: tactical_move.c `om_move_giveup_pass` (l.2558-2579), constants OM_GROUP_GIVEUP_RADIUS 75, OM_GROUP_GIVEUP_TICKS 40 (om_constants.h l.591-592). Effect: `mu->has_dest = 0; om_move_route_drop(mu)`. It touches movement only. unit.c is not told; the unit keeps `order == OM_ORDER_ATTACK_MOVE` and now has no destination. It does not set a target or a destination toward any enemy.
- R-087-09 "give up and pick another target" (blocked line of fire) is not the same thing: it is the 20-tick firing-spot search, a target drop.

### B.4 Per state: enemy visible, outside weapon range
- Idle (order none, no destination): does nothing. No target is acquired because acquisition radius is attack_range (l.2168); no destination is set; it fires only when the enemy comes into range. Hit by that enemy: return fire then closes on the attacker (l.2109-2114). Pinned by test_R_087_04_A199_an_idle_unit_never_walks_toward_a_seen_enemy.
- Attack-moving with a destination (marching): ignores the enemy and keeps marching its slot and route (A199); halts (`om_tac_hold`, l.2211 -> `om_unit_engage`) and fires only when an enemy is in attack range and it can shoot it. A target already acquired that leaves range is kept (l.2143 under pursue) and the unit `om_tac_release`s (l.2205-2209) onto its route to the point, i.e. the "pursuit" in R-087-04/05 is the march continuing, not a goal set to the target.
- Attack-moving after arrival or after R-099-05 give-up (`has_dest` 0, `order` still ATTACK_MOVE, `chase_idle` l.2044, comment l.2043 "P1: an attack-move that has arrived stays an attack-move"): behaves as idle. Acquires only inside attack range; `om_tac_release` (l.2224-2225) re-issues a move to the order point it is already at. It never closes. This is the state the 2026-10-19 cap trace found (decision 28 point 2).
- Guarding (`u->guard`; om_command_guard tactical_move.c l.3428 -> om_tac_unit_set_guard unit.c l.2023): on main it holds. It acquires only in range, drops a target that leaves range (l.2143: `u->guard` counts with `!pursue`), answers return fire only if it can shoot (l.2104), and never walks. R-096-08's step-and-return is E4, on a branch.
- Holding: there is no hold stance. R-096-06 rejects hold, stop, patrol and follow (tactical_move/pipe). The stances in the engine are: none (idle), move, attack-move, attack-target, guard.

---------------------------------------------------------------------------------------
## (C) The lab

On origin/main (scripts/skilllab):
- plays.py: `_group` gives every group `order="attack_move"` toward Setup.point (the midpoint); the start gap is `sensor_radius + 1 + depths` (plays.py l.44 on L8), i.e. the sides start just outside each other's sensor range and walk to a meeting point. Orders are issued once per unit (or per chunk) by fight.py `_issue_orders` (l.102-126): attack_move / move / group_move / guard / idle.
- plays.py l.9-12 on main: `MOPUP = True  # lab rule, provisional (mopup.py): a stopped side re-issues its attack-move at what it sees`, MOPUP_INTERVAL_TICKS 200. mopup.py `mopup_goal`: when no unit of a side has an enemy in range and it sees one, send the side at the nearest seen enemy to its centroid. fight.py l.263-358 applies it every 200 ticks, counted as `mopup_orders`. So since A199 the lab has already been moving stopped units onto visible enemies on its own.
- asym.py l.11: also uses MOPUP; APPROACH default 0.0 (off).

On origin/push/labrev2-lab 4c638fc0: mopup.py is gone and there is no re-engage yet (grep: none).

On origin/push/labrev2-l8 cb831aab (L8, not yet in labrev2-lab):
- contract.py l.159: `REENGAGE_SILENCE_TICKS = 40   # DRAFT-reengage-silence-ticks (Westley's number, the R-099-05 window)`.
- fight.py l.235-284 class `_Reengage`: each tick, per eligible side, if no unit fired and no unit moved for 40 ticks, `_engage` (l.270): idle units of the side holding an attack-move role (`engine.unit_destination(w, u) is None`) are sent by `engine.order_attack_move(w, idle, x, y)` to the centroid of enemies the side sees (`engine.visible_enemies`). Once per silence (`armed`), guard holders excluded, both sides. Counted in CSV columns reengage_0/1 (contract.py l.121, rows.py l.10/35).
- timeline.py: orders available to plays: attack_move, move, group_move, idle, guard, ping, set_layer, set_emission; no order moves a unit onto a specific unit other than attack_move to a point.
- search_policies.py (labrev2-l8) CHASE_UNITS 4: ping search chases the last picture, a search-policy order, not an engagement rule.

Verdict: the lab moves a unit toward a visible enemy in exactly one place per branch: mop-up on main, re-engage on L8. Both exist to compensate for the engine rule that an idle or arrived attack-mover does not close. Nothing else in the lab does.

---------------------------------------------------------------------------------------
## (D) If the rule became: "a unit with a visible enemy and no order engages it: moves into range and fires; an attack-moving unit does the same on the way and after arrival"

### D.1 Bible lines that change
- E-11 l.140 and E-13 l.45 (the "Direction changed 2026-10-02, rewrite pending" paragraphs) become the rule text, the "rules below are what the game does today" sentence goes.
- E-11 R-087-03 ("within attack range"): trigger widens from range to sight.
- E-11 R-087-04: reversed. Its A199 clause ("does not walk toward an enemy it merely sees"; "the formation holds until shooting, not until sight") is Westley's own ruling of 2026-10-03, marked for playtest review. The "on the way" half of the new sentence contradicts it directly. The "no order" and "after arrival" halves do not: A199 concerned formation during the march, and he was not asked about idle units. A decision for Westley is whether the "on the way" half supersedes A199 (rulings-2 A199, :853).
- E-11 R-087-05 (leash 200 wu from anchor, "pursues"): the leash bound and what happens when a chase passes it need restating for a sight-triggered chase (with no leash an idle unit could be drawn arbitrarily far).
- E-11 R-087-06: its "An idle unit has no point and holds where the pursuit ends" and the engine-today sentence; return fire becomes a special case of acquisition.
- E-11 R-087-08 (cohort re-acquire), R-087-09, l.156 (flinch note), R-204-03, R-202-01/02 (worker and structure targeting by sight).
- E-01 R-008-01, R-008-02 ("in range" -> "visible"), R-164-02 (reach: unchanged).
- E-13 R-096-02 ("When an enemy enters attack range"), R-096-01 (plain move stays blind per R-087-02), R-099-04 ("any later displacement ... leaves it at the new position with no re-approach", and the invariant l.217), R-099-05 ("same state as an arrival"), R-096-08/R-208-01 (guard; the guard rule already is this rule with a radius), R-096-04 (attack-target last-known-position idle).
- E-12 R-093-02 and l.18: "acquires, pursues or fires" already assumes pursuit; unchanged.
- docs/bible/algorithms.md ALG-62 (also stale today, still describes pursuit on sight).
- Register: Q-096-01 text, Q-087-01 (leash), and a new Q row for the A199 reversal.
- docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 28 point 2 ("not a defect") and decision 23.

### D.2 Engine functions that change (csrc/unit.c unless named)
- `om_tac_unit_ai` acquisition block l.2164-2179: radius `u->attack_range` -> a sensor-based radius for a unit with no order; plus a place that sets a destination from the target position for idle and arrived units.
- `om_tac_nearest_actable` l.2006, `om_tac_nearest_visible` l.1985 (already sight-filtered at sensor radius, today used only as the fallback inside nearest_actable), `om_tac_pick_across` l.1731.
- The target-validation drop l.2143 (`!om_tac_in_range` for non-pursue and guards) and the pursuit/release branch l.2205-2209 and l.2224-2225 (`om_tac_release` re-issues the move to the order point).
- `chase_idle`/`ordered` l.2044-2045 and the order-state reconcile l.2054-2065 (an arrived attack-move stays ATTACK_MOVE with no destination).
- tactical_move.c `om_move_giveup_pass` l.2561 and `om_command_*` interplay (R-099-05 ends the move; a new chase must not be undone by the 40-tick pass or the `has_dest == 0` branch).
- `om_tac_leash_broken` l.997 (leash for idle chasers; anchor set at l.2172-2174 only for ATTACK_MOVE).
- fog.c `om_unit_acquire_target` l.687-714 already does "nearest visible -> attack_target" but is unwired; whether to wire it or reuse its choice is a builder decision, not made here.
- Return fire branch l.2096-2117 (merges with the new acquisition); flinch.
- Guard: E4 `om_tac_guard_pick/_can_engage/_walk` (branch labrev2-e4) is the existing radius form of the same rule; a general rule would sit next to it.
- Saved fields: unit rows `anchor_*`, `halted`, `am_*`, `guard` are in the save and checksum (l.3127, 3258); any new field means a save-format and hash change (contract).
- Determinism: A99 hash goldens move.
- Python reference simulation/ (movement.py, tick.py) is parity tooling; its P1 text (tactical-port-parity-requirements.md:19) pursued on sight until A199 and was changed to match.

### D.3 Tests that pin the old behaviour (would go RED if an idle or arrived unit started closing on a visible enemy)
Engine, direct pins:
- tests/csim/test_PP_attack_move_no_sight_pursuit.py::test_R_087_04_A199_an_idle_unit_never_walks_toward_a_seen_enemy (l.231: "a unit with no order stays where it is with an enemy in sensor range, out of attack range, and takes no target"; asserts position within 0.5 wu after 60 ticks and target in (-1, 0)). Idle-unit pin.
- same file ::test_R_087_04_A199_a_lone_attack_mover_keeps_its_goal_and_takes_no_target_for_an_enemy_it_only_sees (l.147), ::..._a_32_unit_line_reaches_its_slots_with_the_shape_intact_past_a_seen_enemy (l.94), ::..._an_acquired_target_that_walks_out_of_range_stays_held_under_the_leash (l.184): attack-moving "on the way" pins (reverse A199).
- tests/csim/test_PP_unit_pursuit.py: test_R_087_04_move_goal_becomes_the_nearest_visible_enemy (l.53; goal stays the march point, distance to both seen enemies grows, target -1), test_R_087_04_pursuit_is_ordinary_movement (l.79; distance to the seen enemy grows every tick), test_R_087_04_chase_persists_after_arrival (l.127; "an arrived unit does not go after it", position unchanged for 16 ticks, target -1) is the arrived-unit pin, test_R_087_04_visible_means_the_sides_set and _only_a_visible_enemy_is_pursued (stealth and blinded cases, may need re-pinning).
- tests/csim/test_PP_C_g3_pursuit_by_sight.py: test_R_093_02_a_visible_enemy_is_pursued_control (a seen enemy 700 wu away "is not chased, distance grows") and test_R_089_02_a_friend_that_sees_the_enemy_lets_it_be_pursued (a friend's sight "does not make it chase"), both re-pinned by TD-PP-A199-repin. test_R_093_02_beyond_sensor_radius_nothing_reacts probably holds.
- tests/csim/test_PP_unit_guard.py::test_R_096_05_guard_holds_while_an_enemy_stands_beyond_range (l.94) and ::..._guard_does_not_step_toward_an_enemy_that_stays_out_of_range (l.118): pin the built guard's "never steps"; already scheduled to change under E4 (labrev2-e4-tests).
- tests/csim/test_PP_unit_return_fire.py (13 hits): R-087-06 return fire. Out-of-range attacker "becomes the new goal" test (l.79) holds either way; "Out-of-range attackers stand beyond its 700 wu sensor so pursuit (R-087-04) cannot also claim it" (header): the fixture assumes sensor-range enemies are the only way to claim, would need distance changes if sight became the trigger.
- tests/csim/test_core_arrival_hold.py (R-099-04: arrived unit "does not re-approach if subsequently displaced"; those use no enemy, so likely still green) and tests/csim/test_PP_unit_giveup.py (R-099-05: destination ends at 40 ticks; likely green because no enemy is present in the constructed scenes, but the S101 scene (20 Raiders, group move) needs a check).
- tests/csim/test_PP_move_group.py ::test_R_096_02_group_ends_when_every_member_has_engaged_and_does_not_resume and tests/csim/test_PP_unit_attack_move_group.py ::..._group_ends_when_every_member_has_engaged: old group-end rule; already contradicted by the 2026-10-13 ruling (R-096-02 text), independent of this question.
- Python mirror: simulation/test_attack_move_no_sight_pursuit.py and tests/csim/parity/test_attack_move_no_sight_pursuit_parity.py (A199 parity), tests/csim/parity/parity_scenes.py.
Golden hashes (re-recorded at A199, ledger TD-PP-A199-rerecord, push_ledger_2026-09-22.md:868; any behaviour change in a fight where a unit sits idle or arrives with an enemy in sight moves them again; "re-record once with a ledger row" is the precedent):
- tests/csim/data/a99_tactical_hashes.json and a99_tactical_hashes_pre_g3.json via tests/csim/test_E13_A99_tactical_equivalence.py (fight_502_gap100, fight_990_gap300/1500/3000), tests/csim/scale/test_scale_A99_tactical_equivalence.py (fight_2501_gap600 ...), F1/F2/F3 goldens (tests/csim/test_F1_fog_per_faction_observers.py:299 "Re-recorded day23 on push/pa-land (A199)", test_F2_nearest_hostile_search.py, test_F3_macro_contact_skip.py), test_PP_target_policy_per_side.py, test_PP_C_g3_hash_invariant, tests/skilllab/golden_hashes.json (test_cross_machine x3, test_trace_real mirror-16-16 and numbers-16-8). Whether each moves is only known by running them.
Lab (these describe lab behaviour, and become obsolete rather than red if the engine chased):
- tests/skilllab/test_mopup.py, tests/skilllab/integration/test_mopup_real.py (main; the mop-up).
- On origin/push/labrev2-l8-tests: tests/skilllab/test_reengage.py, test_reengage_rows.py, integration/test_reengage_real.py (the two capped fights must end by elimination "through a reengage"; ::test_the_elimination_came_through_a_reengage would go red if the engine closed first, since reengage count would be 0), fakes_reengage.py.
- tests/skilllab/integration/test_approach_real.py::test_the_shape_is_held_until_contact (A199 shape control: chunked default ratio 1.21 at first contact, which depends on no chase on sight).
- tests/skilllab/test_timeline*.py (40 hits on "idle", a timeline order name) are unrelated.
Not related (hits on "idle" in another sense): tests/specfactory/*, tests/simviewer/*, tests/*.gd, tests/qa/desktop/*, tests/transport/*, tests/csim/test_core_group_pace.py, test_VG_W_w2_routes.py, test_VG_contract.py, scale tests, the remaining skilllab files; test_E11_S087 ::test_R_087_04_it_moves_toward_nearest_visible asserts only x > init_x with the march goal in the same direction, so it stays green.

### D.4 Does the lab's L8 re-engage become unnecessary?
Yes for its stated purpose. L8 exists only because an idle or arrived attack-mover with a visible out-of-range enemy never closes (decision 28 point 2, FINDING-attackmove-idle-cap). If the engine closed on sight, no unit would sit idle holding an attack-move with a visible enemy, so the "silent side" trigger would fire only when no enemy is visible, where L8 already does nothing (`if not points: return`, fight.py l.278-280). The re-engage columns reengage_0/1 would read 0, and the L8 tests that require "the elimination came through a reengage" would have to change. Two things L8 keeps doing that an engine change would not: it re-orders onto the centroid of visible enemies (a point), and it exempts guard holders; the engine rule as worded would not exempt guards. The mop-up on main (MOPUP = True, 200-tick interval) is the same compensation and is retired by the same change. The 2026-10-19 cap trace's first cause (R-087-06 overwriting the ordered point, E1/E1b) is separate and is not affected by the new rule.

### D.5 Open points the brief leaves to others (not decided here)
- Whether "within vision" means the unit's own sensor, the side's visible set (R-093-02 says the side's), or a ping.
- Whether the new rule applies to enemy-macro forces issued a plain move (DEFEND "Hold", enemy_macro.c l.514), which are blind under R-087-02 / R-096-01.
- The leash and how far an idle chaser may go (D.1, R-087-05).
- A199 reversal for the march (D.1).
