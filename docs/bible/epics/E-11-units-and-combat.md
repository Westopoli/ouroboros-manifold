# E-11 — Units, Abilities, and Damage

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 12 stories, 61 rules, numbers from `algorithms.md` ALG-60 through ALG-64 and the unit table. The rules of S-201 to S-204 leave their numbers to open flags. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | Yes; the 15 flags still open are listed at the foot of this file. |
| Every visible-surface story has a reference | **No.** S-088 (how units read on screen, squads, ability cues) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on the open flags listed at the foot and one missing reference (S-088). S-081, S-084, S-085 and S-086 have no open flags; gate to be rerun. The roster flags Q-082-03 to Q-082-05 (how a 20 to 40 type roster is shaped, balanced, and sized per era) are the load-bearing ones. The stories added on 2026-10-02 (S-201 to S-204) are design decided, not scheduled for building, and each carries open flags.

## Purpose

A roster of 20 to 40 unit types per era, in the register of Age of Empires 3 and Age of Empires Online, on three categories and a soft rock-paper-scissors: Strike flanks Siege, Siege crushes Line, Line absorbs Strike. The three categories are the unit families that counter each other (E-22 S-171). The six Settled Reach types below are the first of them and the tuning baseline. Every unit has stats and exactly one ability; how roles and the roster invariants extend past six types is open (Q-082-03), the roster is balanced by a scoring mechanism still to be designed (Q-082-04), and an era built around a named conflict may weight its roster toward that conflict's sides (Q-082-05). Damage is flat: base damage times a category multiplier, no falloff, no cover reduction. Fights last long enough to read and retreat from; HP, not damage, sets the tempo, so flanks resolve first, the center grinds, and Siege duels last longest. Every unit on both sides runs the same three-check decision loop: flinch from what you cannot fight, obey the player, shoot the nearest thing in range. Abilities are the mastery layer: ignorable by a new player, decisive in skilled hands, every one a commitment with a tradeoff. The land era has walking unit types beside the space era's flyers (S-201). Workers are units that cannot fight, and they count in the one population cap and in the unit budgets (S-202). Walls, gates, towers and production buildings are things on the map that block, are seen and can be attacked (S-204). Every unit type has a cost in the three resources by its category (S-203).

The numbers below are the Tier 2 Settled Reach baseline; they are tuned by headless simulation, not by hand (Stage 1 A-261).

## Obviously working in 60 seconds

Spawn 10 Vanguards versus 10 Raiders at 250 wu apart on layer 3 and attack-move both. The Vanguards win with 5 or more survivors; the fight lasts at least 45 s. Swap the Raiders for 10 Bombards at 1,000 wu with one Raider forward as their eyes: the Bombards fire on the Vanguards as they close; without the Raider the Bombards hold fire until the Vanguards are within their 300 wu sensor (E-12 R-093-02). Send 4 Raiders around the flank into 4 Bombards: the Bombards die. Pop Surge on a Raider: it moves at 375 wu/s and hits for 18 for 3 s, then cannot Surge again for 75 s. Same seed, same fight, tick for tick.

## Stories

### S-081 — Three categories, a soft triangle
Flag closed, rule text pending: Q-081-01, Siege to Strike is 0.20 at launch, to be tuned in playtest. The rule below is what the tests read today.
As a commander, I want Strike to beat Siege, Siege to beat Line, and Line to beat Strike, with none of it a death sentence, so that composition matters and positioning can still overturn it.

Rules
- R-081-01  Given an attacker of category A and a target of category B, When damage is dealt, Then damage = base damage × M[A][B] with M: Strike→Strike 1.0, Strike→Line 0.75, Strike→Siege 1.5; Line→Strike 1.5, Line→Line 1.0, Line→Siege 0.75; Siege→Strike [Q-081-01: 0.20 in code, 0.75 in the bible], Siege→Line 1.5, Siege→Siege 1.0.
- R-081-02  Given equal power of Line versus Strike in a straight fight, When resolved, Then Line wins with at least 30 percent of its HP remaining; the same for Siege versus Line and Strike versus Siege from the flank.
- R-081-03  Given a Bastion attacked by 4 Raiders from the flank, When resolved, Then the Bastion survives at least 20 s (the Siege exception to Strike-beats-Siege).
- R-081-04  Given any matchup, When resolved, Then time to kill at a 1.5× advantage is 30 to 40 percent shorter than at 1.0×.

Inputs: unit categories; base damage.
Outputs: damage events in the tick delta; HP.
Open flags: none.

### S-082 — The roster
As a commander, I want a roster of 20 to 40 unit types per era, each with a job I can learn, so that a force offers many options and still reads at a glance.

Rules
- R-082-01  Given the Settled Reach baseline, When loaded, Then it contains at least these six types with this table, checked by a contract test; the rest of each era's roster is set by Q-082-05:

| Unit | Category | Role | HP | Damage | Interval s | Range wu | Speed wu/s | Sensor wu | Layer transition s | AoE wu |
|---|---|---|---|---|---|---|---|---|---|---|
| Raider | Strike | flanker | 250 | 9 | 0.8 | 200 | 150 | 800 | 1.0 | 0 |
| Interceptor | Strike | screen | 325 | 6 | 1.0 | 250 | 130 | 1000 | 1.2 | 0 |
| Vanguard | Line | frontliner | 500 | 7.5 | 1.2 | 300 | 80 | 700 | 2.5 | 0 |
| Warden | Line | support | 375 | 4 | 1.5 | 350 | 70 | 800 | 2.0 | 0 |
| Bombard | Siege | artillery | 400 | 17.5 | 3.0 | 1200 | 50 | 300 | 4.0 | 150 |
| Bastion | Siege | anchor | 1050 | 7 | 1.8 | 800 | 40 | 300 | 5.0 | 0 |

- R-082-02  Given the roster, When ordered by speed, Then every Strike unit is faster than every Line unit, and every Line unit faster than every Siege unit.
- R-082-03  Given the roster, When ordered by HP, Then the Bastion has the most by at least 2× the next, and the Raider the least.
- R-082-04  Given the roster, When sensor radius is read, Then both Strike units see farther than both Siege units.
- R-082-05  Given the roster, When AoE is read, Then only the Bombard has an area attack. Direction changed 2026-10-13, rewrite pending: area damage becomes a knob with its own range and shape, attachable to any role or a single unit (Westley, 2026-10-13; Q-082-06); the rule above is what the game does today.
- R-082-06  DRAFT (Westley, 2026-10-13: "AOE damage (with it's own range), like a cone shaped attack, something that can be added to any unit role or specific individual unit"; Q-082-06): Given a type with a cone set (range above 0; DRAFT-aoe-cone-range 300, DRAFT-aoe-cone-deg 45, DRAFT-aoe-cone-share 1.0), When it attacks, Then its target takes the direct hit and every other enemy inside the circular sector of that range and half-angle about the attacker's facing, within the type's reach offsets, takes base damage times the share, in unit-id order until the ALG-61 cap; a cone replaces the type's disc; range 0 restores it. Shape, numbers and which launch types carry a cone are Westley's after the skill lab shows the effect.
- R-082-06  Given an expansion pack adds a unit type, When loaded, Then it declares category, role, the stats above, and one ability, and no engine code changes.
- R-082-07  Given an era pack, When its roster is validated, Then it declares between 20 and 40 unit types, each with category, role, the stats above, the declarations of R-082-09, and one ability, and the roster passes the balance scoring mechanism [Q-082-04]; an era built around a named conflict may weight its roster toward that conflict's sides [Q-082-05]; whether worker types count toward the 20 to 40 is Q-167-03.
- R-082-08  Given Tier 1 and Tier 3, When profiles are read, Then HP and damage are 0.8× and 1.2× the Tier 2 values and all other ratios scale uniformly.
- R-082-09  Given a unit type added by an era pack or an expansion, When it is loaded, Then it also declares its movement kind (walking, or flying or swimming; E-01 R-001-07), its reach (E-01 S-164), whether it can ping (E-01 S-162), its cost (S-203) and its population weight (E-22 S-169), and no engine code changes.

Inputs: unit profile table (per tier, per era pack).
Outputs: loaded roster; contract test.
Open flags: Q-082-03 (categories, roles, and the roster invariants past six types), Q-082-04 (the balance scoring mechanism), Q-082-05 (launch roster size per era and the conflict swing), workers sit outside the roster for the beta (Westley, 2026-10-07).

### S-083 — Stats, trait cards, ability
As a commander, I want to unlock trait cards and build a force that plays my way, so that units differ in kind, and never in a way that beats positioning.

Rules
- R-083-01  Given a unit type, When its profile is read, Then it has the stats of S-082, zero to two trait cards the player has chosen, and exactly one ability.
- R-083-02  Given a trait card, When applied, Then it changes a stat or a rule; no card or ability ever outweighs positioning: layer position and cross-layer geometry weigh more than any trait or ability, and cards granting vision across layers are kept to a minimum [Q-083-03: the weighting test].
- R-083-04  Given a player, When they play, Then trait cards are unlocked through play, in the register of Dead by Daylight and Age of Empires 3, and abused cards are nerfed after launch [Q-083-03: what earns a card, where it persists, whether the enemy fields cards].
- R-083-03  Given a Warden, When any friendly unit is within 300 wu, Then that unit takes 10 percent less damage and regains 0.075 HP per tick (the Warden's passive aura); a second Warden in range adds 0.05 reduction, not 0.10, and healing stacks per Warden.

Inputs: profile table.
Outputs: effective stats.
Open flags: Q-083-03 (unlock mechanism and the positioning-over-cards weighting test).
Cards ship after launch; launch units are stats plus one ability. The trait option was chosen through the options pass, `docs/northstar/research/options/unit-traits/`.

### S-084 — Flat damage
As a commander, I want damage to be simple and legible: base times matchup, full damage at any range within reach, area damage capped, so that I can predict a fight.

Direction changed 2026-10-02, rewrite pending: an area attack reaches enemies on the layer offsets its type's reach includes, not only the attacker's own layer (E-01 S-164, R-008-03). The rules below are what the game does today.

Rules
- R-084-01  Given an attacker in range of its target every tick, When its attack timer elapses (interval × 20 ticks; a unit's first attack is ready on the tick its target is first in range), Then one attack lands for base × matchup × output multiplier × (1 − reduction), with reduction the sum of Brace 0.50, Fortify 0.20, and Warden aura 0.10 where they apply, capped at 0.9.
- R-084-02  Given a target at 10 wu or at the full range, When hit, Then damage is identical (no falloff).
- R-084-03  Given a Bombard attack centered on a target, When resolved, Then every enemy on the Bombard's layer within 150 wu of the target takes full per-target damage, and the total across all targets is capped at 4 × base damage (70), applied in target order until the cap.
- R-084-04  Given a unit fires, When the attack lands, Then the unit pauses movement for 0.5 s (backswing).
- R-084-05  Given a target behind cover, When hit by an attacker who can see it, Then damage is unmodified (E-01 R-007-04).
- R-084-06  Given elevation, When damage is computed in the Settled Reach, Then no elevation bonus applies; the engine computes the tier difference and the era flag is off.
- R-084-07  Given DPS, When read for the HUD or tuning, Then it is base damage / interval.

Inputs: attacker and target stats, states, positions.
Outputs: damage events; HP in the tick delta.
Open flags: none.

### S-085 — Long enough to think
As a commander, I want fights to last long enough to read, reposition, and retreat, with flanks resolving first and Siege duels last, so that attention management is the skill.

Rules
- R-085-01  Given a 10v10 mirror of any single type at attack range with no abilities, When resolved, Then the fight lasts at least 45 s.
- R-085-02  Given a 50v50 mirror with the default balanced composition, When resolved, Then the fight lasts 150 to 200 s.
- R-085-03  Given a 100v100 balanced battle, When resolved, Then it lasts more than 120 s.
- R-085-04  Given a mixed battle, When per-category engagements are timed, Then Strike-vs-Strike resolves before Line-vs-Line, which resolves before Siege-vs-Siege.
- R-085-05  Given a fight the player is losing, When they issue a move away at the 45 s mark, Then at least 30 percent of the force escapes alive.

Inputs: roster; battle setups.
Outputs: trajectory invariants (T1).
Open flags: none. These are the launch pacing targets (A-340); per-era tempo is deferred (A-321, A-339, A-344).

### S-086 — One ability each
As a commander, I want each unit to have exactly one ability that amplifies its role and costs something, so that mastery is timing and not menus.

Direction changed 2026-10-02, rewrite pending: the Bombard's Barrage reaches enemies on the layer offsets its type's reach includes, not only its own layer (E-01 S-164, R-008-03). The rules below are what the game does today.

Rules
- R-086-01  Given a Raider with Surge ready, When activated, Then for 60 ticks (3 s) speed × 2.5 and damage × 2.0, then cooldown 1,500 ticks (75 s).
- R-086-02  Given an Interceptor with Intercept ready and an enemy Strike unit within 350 wu on its layer, When the check runs, Then it triggers automatically: speed × 1.8 and damage × 1.5 for the first engagement, then cooldown 600 ticks (30 s); the player never activates it.
- R-086-03  Given a Vanguard with Brace ready, When activated, Then it is immobile at once, has no bonus for 40 ticks (2 s windup), then takes 50 percent less damage and deals 1.3× while braced; activating again cancels with the same 40-tick windup; cooldown 700 ticks (35 s) starts at activation.
- R-086-04  Given a Warden with Rally ready, When activated, Then every friendly unit within 400 wu regains 112 HP at once, capped at max HP; cooldown 1,500 ticks (75 s).
- R-086-05  Given a Bombard with Barrage ready and a target position, When activated, Then after a 30-tick (1.5 s) telegraph visible to both sides, every enemy within 100 wu of the position on the Bombard's layer takes base × 3.0, subject to the AoE cap at 4 × (base × 3.0); cooldown 1,800 ticks (90 s).
- R-086-06  Given a Bastion with Fortify ready, When activated, Then for 400 ticks (20 s) every friendly unit within 350 wu of the Bastion takes 20 percent less damage, the zone moves with the Bastion at speed × 0.4, and the zone is visible to the enemy; cooldown 1,400 ticks (70 s). (An auto-started Fortify does not apply the speed x 0.4 penalty in om_unit_effective_speed; it yields to a player order per R-087-02 and is cancelled without cooldown.)
- R-086-07  Given an ability on cooldown, When activated, Then the command is rejected and nothing changes.
- R-086-08  Given an enemy unit, When its ability is ready and the threshold condition holds (an enemy in range for Surge, Brace, Barrage; a damaged friendly in radius for Rally; two or more friendlies in radius for Fortify), Then it activates; no other enemy timing logic exists.
- R-086-09  Given any ability activation, When it fires, Then an explicit ability event with tick, unit, ability, target, duration, and radius is emitted for the renderer (E-18).

Inputs: activate command; unit states; positions.
Outputs: ability state, cooldown, duration in the tick delta; ability events; HUD cooldown ring.
Open flags: none.

### S-087 — Every unit thinks the same way
As a commander, I want every unit on both sides to flinch from what it cannot fight, obey my orders, and otherwise shoot the nearest enemy in range, so that my skill is direction, not babysitting.

Direction changed 2026-10-02, rewrite pending: an idle or attack-moving unit engages the nearest enemy within its type's reach that its side can see, on its own layer or another (E-01 S-164, R-008-04; E-12 R-093-02). The rules below are what the game does today.

Rules
- R-087-01  Given a unit taking damage from an attacker it cannot see or cannot reach, When the loop runs, Then it moves 200 wu directly away from the damage direction and stops; once the attacker is visible and in range it stands and fights.
- R-087-02  Given a unit with an active player order, When the loop runs, Then the order wins over auto-engagement; a plain move never acquires or returns fire.
- R-087-03  Given an idle or attack-moving unit with an enemy within attack range on its layer, When targets are evaluated, Then it attacks the nearest such enemy; an engaged target still alive and in range is kept.
- R-087-04  Given an attack-moving unit with no target within its attack range, When evaluated, Then it keeps marching on its slot and route (R-095-02, R-097-03), steering around units in its way, and does not walk toward an enemy it merely sees in sensor range; the formation holds until shooting, not until sight (Westley, 2026-10-03, A199; marked for review in playtesting). It halts and fires when an enemy is within its attack range and it can shoot it (a target behind cover, a wall or a blocked cell does not stop the march: it keeps walking its route and fires when the line clears, or seeks a firing spot under R-087-09), and pursues an acquired target that leaves that range under the leash (R-087-05).
- R-087-05  Given an attack-moving unit that acquires a target, When it does, Then it anchors at its position, and if the unit itself pursues more than 200 wu from the anchor it drops the target and resumes its attack-move (R-096-03). The leash measures the pursuer's own distance from its anchor, never the target's, so a unit holding and firing from its anchor keeps its target at any weapon range (A188, 2026-10-03).
- R-087-06  Given an idle or attack-moving unit with no target taking damage, When hit, Then it targets the attacker (return fire); if the attacker is out of range it attack-moves to the attacker, dropping its earlier destination; a plain-moving unit and an already-engaged unit ignore incoming damage for targeting.
- R-087-07  Given a supply or evacuation unit, When the loop runs, Then it never attacks; it flinches and otherwise holds.
- R-087-08  Given target acquisition, When it runs, Then each unit re-acquires on every 4th tick (cohort stagger) and validates its current target every tick.
- R-087-09  Given an idle or attack-moving unit with a target within its attack range whose line of fire is blocked by units, cover or ground, When evaluated, Then it steers around the blockers by the probe of blocked movement (R-097-03) until it reaches a spot with a clear line, and if it finds none within 1 s (20 ticks) it drops the target and acquires another (Westley, 2026-10-07: blocked fire is handled like blocked movement; "a unit gives up to pick another target if it can't find a firing spot within 1 second"). An obstacle is a detour, never a full stop (E-17 R-190-07).

Inputs: unit states; visibility (E-12); orders (E-13).
Outputs: target ids and attack events in the tick delta.
Open flags: Q-087-01 (whether the 200 wu leash of R-087-05 is tested before or after damage; the skill lab runs both and Westley picks). Q-008-05 (the nearest enemy stays the game's target rule; a lab-only setting measures focus fire).
The flinch also fires when the attacker is visible but out of range with no path to it on the unit's layer; that branch is not built, and the code flinches only when return fire fails to find the attacker.

### S-088 — Reading units on screen
As a commander, I want a Strike squad to read as a small group, a Siege unit as a single heavy asset, and every ability to have an unmistakable cue, so that I never misjudge what I am looking at.

Rules
- R-088-01  Given a Raider, When drawn, Then one unit is a squad of 5 to 10 small craft in formation sharing one HP bar and one position, much smaller than the other types and passing gaps they cannot (E-17 R-188-05, S-246); the sim tracks one entity, and its collision radius is DRAFT-raider-radius, set with the roster (Q-166-05; Westley 2026-10-13: "Raider T2 specifically, each "unit" will be a group of them, 5-10 and they'll be much smaller than the other units. (like halo wars marines)"). An Interceptor is drawn as 3 to 5 small craft in formation sharing one HP bar and one position.
- R-088-02  Given an ability event, When received by the renderer, Then a cue plays at that tick for the event's duration (Barrage shows its telegraph ring at the target for 1.5 s before impact; Fortify shows its zone; Brace shows a planted state).
- R-088-03  Given a T2 screenshot of a mixed force, When inspected, Then category is distinguishable by silhouette size: Strike smallest, Siege largest.

Inputs: unit types; ability events.
Outputs: screen.
Open flags: none beyond the missing reference. Reference required: `references/E-11/notes.md`, missing.

### S-201 — Units that walk
As a commander in the land era, I want unit types that walk, so that slopes, steep ground and strongpoints at slopes decide where an army can go.

Design decided 2026-10-02, not scheduled for building. This story is for the land era. The space era's types fly.

Rules
- R-201-01  Given the land era pack, When its roster is read, Then it contains unit types whose movement kind is walking (E-01 R-001-07), in the same three categories and under the same roster checks as the space era's roster, because "the units and rules for them will be essentially the same" (Westley, 2026-10-02); the six space types re-skinned with the space era's table (Westley, 2026-10-03), plus the vision units a ground era needs because it has no ping (E-01 R-005-12): seer-type units, and a simple placeholder scout for now (Westley, 2026-10-05: "correct not the same six"; "a simple placeholder unit that's a scout is sufficient for now") [Q-201-02: the seer type's stats and cost].
- R-201-02  Given a walking unit, When it changes layer, Then it does so only by walking a slope (E-01 R-001-07), the time the slope takes is its length over the unit's speed, and the unit type's layer transition time plays no part (E-01 R-004-07).

Inputs: the land era pack's unit profile table.
Outputs: loaded land roster; contract test.
Open flags: none.

### S-202 — Workers are units that cannot fight
As a commander, I want workers to be real units that cannot fight and can be killed, so that a base full of workers is something to protect and the unit budgets are honest about them.

Design decided 2026-10-02, not scheduled for building. What workers gather and carry is E-22 S-167.

Rules
- R-202-01  Given a worker, When the decision loop of S-087 runs, Then it never acquires a target and never returns fire, it flinches from damage, and otherwise holds, follows its move order or does its work (R-087-07, E-15 R-129-01).
- R-202-02  Given a worker that an enemy's side can see within that enemy's reach, When targets are evaluated, Then it is a target as any enemy unit is (R-087-03), and at 0 HP it is dead (Invariants below) (worker statistics, including hit points and the category it is hit as, are placeholders for the beta; workers are outside the roster for the beta, Westley, 2026-10-07).
- R-202-03  Given a side's units, When the population is counted, Then every worker counts in the one population cap with the soldiers (E-22 S-169, S-167).
- R-202-04  Given the unit budgets (the scale requirements of this epic, E-12 and E-13), When workers are counted, Then they count as units with the soldiers, and each figure covers both together.

Inputs: worker type profile (era pack); unit states.
Outputs: worker hit points and position in the tick delta; kills.
Open flags: none on workers; workers under raid (a later idea, Westley, 2026-10-07).

### S-203 — What a unit costs
As an economy player, I want each unit type to cost the three resources by its category, so that what a side builds and what it gathers match.

Design decided 2026-10-02, not scheduled for building.

Rules
- R-203-01  Given a unit type, workers included, When its profile is read, Then it carries a cost in two of the three resources, by its role, in the fixed pattern of E-22 R-171-03; Strike, Line and Siege are the unit families (E-22 S-171) [Q-159-08: the amounts; roles inside a category are Q-082-03].
- R-203-02  Given a unit type, When it counts against the population cap, Then it counts by its population weight (E-22 S-169) [Q-169-01: the weight per type].

Inputs: era pack cost table; population weights.
Outputs: cost and weight in the loaded profile, read by E-22 S-170 and the economy screen.
Open flags: Q-159-08, Q-169-01, Q-167-01 (what a worker costs).

### S-204 — Buildings are things on the map
As a commander, I want walls, gates, towers and production buildings to be things on the map that block, are seen and can be attacked, so that an assault has something to break and a defense has something to stand behind.

Design decided 2026-10-02, not scheduled for building. Walls, gates and towers are written for land maps (E-22 S-174). That they block is E-13 S-097, and that they are seen is E-12 S-205.

Rules
- R-204-01  Given a wall, a gate, a tower or a production building (E-22 S-168, S-170, S-174), When it is placed, Then it is a structure on the map with an owner, a position, a footprint, a layer and hit points; it occupies and blocks its own layer and some layers above it, up to a height, as cover does (E-01 R-007-01; Westley, 2026-10-07: "#4: B") [Q-174-02: its statistics].
- R-204-02  Given an enemy that can see a structure and has it within reach, When it attacks the structure, Then the structure takes damage, and at 0 HP it falls: it stops blocking (E-13 S-097) and stops being seen (E-12 S-205) [Q-174-02: the damage a structure takes from each category].
- R-204-03  Given an idle or attack-moving unit with an enemy structure within its reach and visible to its side, When targets are evaluated, Then it attacks an enemy unit in reach first, and an enemy structure only when no enemy unit is in reach (Westley, 2026-10-07: "#5: B").
- R-204-04  Given a tower with an enemy within its range that its side sees, When its turn comes, Then [Q-174-02: whether a tower fires, and its damage, range and interval].

Inputs: structure records (E-22 S-168, S-170, S-174); unit states; visibility (E-12).
Outputs: structure hit points and destroyed events in the tick delta.
Open flags: Q-174-02.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Unit profile table | Era pack, per tier | 20 to 40 types per era, stats as S-082, the declarations of R-082-09 | missing field fails load |
| Structures | E-22 (S-168, S-170, S-174) | Position, footprint, layer, hit points | |
| Ability activation | Player (E-13 command) or enemy macro | unit ids | on cooldown or dead: rejected |
| Positions, layers, visibility | E-01, E-12, E-13 | | |
| Elevation flag | Era pack | bool, false for the Settled Reach | |

## Outputs

| Output | Observable where |
|---|---|
| HP, target, ability state, cooldown | Tick delta per unit; HUD portrait panel; unit HP bars |
| Damage and ability events | Tick delta events; renderer cues; T1 trace |
| Structure hit points; structure destroyed | Tick delta; screen |
| Pacing invariants | T1 trace |

## Invariants

- HP in [0, max]; a unit at 0 HP is dead on that tick and never acts again.
- Exactly one ability per type; at most one active per unit.
- No fire across layers outside the attacker type's reach (E-01 S-164); a type with reach 0 fires only on its own layer.
- A worker never attacks and never returns fire.
- Total AoE per attack ≤ 4 × base.
- Same seed and commands, same fight, all platforms.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): targeting and damage for 1,000 units in under 2 ms per tick, 10,000 in under 25 ms. The 10,000-unit figure is measured at the 10 ticks/s rate the sim drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the 1,000-unit figure at 20 ticks/s. Workers are units and count in these figures (S-202).

## Look and behavior references

`references/E-11/notes.md`, missing: unit silhouettes and scale by category, squad rendering, ability cues (2 to 5 screenshots or clips).

## Ways this could be wrong

- Matchup matrix transposed (attacker and target swapped).
- AoE cap applied per target instead of per attack.
- Brace bonus applied during windup.
- Intercept triggers on Line or Siege units.
- Return fire overrides an existing engagement.
- Cohort stagger skips validation, so a dead target is shot at.
- Warden aura applies to enemies or stacks without bound.
- Backswing pauses attacking as well as moving.
- Workers left out of the unit count, so the budgets pass with a base that holds thousands of them.
- A unit fires at a layer outside its reach, or at a structure or worker its side cannot see.

## Open ambiguity flags

Q-082-03, Q-082-04, Q-082-05, Q-083-03, Q-087-01, Q-008-05, Q-201-01, and from E-22 Q-159-08, Q-159-10, Q-167-01, Q-167-03, Q-169-01, Q-174-02. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01 Layer system (reach by layer offset, transition window, movement kinds, the ground on land maps).
- E-22 Economy and bases (workers, costs, population, structures).
- E-15 Reinforcement, supply and hazards (non-combat units, S-129).
- E-12 Fog and sensors (visibility for acquisition).
- E-13 Movement (orders, leash, backswing, collisions).
- E-18 Combat visuals (cues).
- E-21 Offline AI pipeline (tier profiles, per-era packs).
