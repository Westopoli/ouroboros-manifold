# E-11 — Units, Abilities, and Damage

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 8 stories, 46 rules, numbers from `algorithms.md` ALG-60 through ALG-64 and the unit table. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 6 new flags, Q-081-01, Q-082-01, Q-083-01, Q-084-01, Q-086-01, Q-088-01. |
| Every visible-surface story has a reference | **No.** S-088 (how units read on screen, squads, ability cues) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on open flags and one missing reference. Q-081-01 (the Siege-versus-Strike multiplier is 0.20 in code and 0.75 in the bible) and the roster flags Q-082-03 to Q-082-05 (how a 20 to 40 type roster is shaped, balanced, and sized per era) are the load-bearing ones.

## Purpose

A roster of 20 to 40 unit types per era, in the register of Age of Empires 3 and Age of Empires Online, on three categories and a soft rock-paper-scissors: Strike flanks Siege, Siege crushes Line, Line absorbs Strike. The six Settled Reach types below are the first of them and the tuning baseline. Every unit has stats and exactly one ability; how roles and the roster invariants extend past six types is open (Q-082-03), the roster is balanced by a scoring mechanism still to be designed (Q-082-04), and an era built around a named conflict may weight its roster toward that conflict's sides (Q-082-05). Damage is flat: base damage times a category multiplier, no falloff, no cover reduction. Fights last long enough to read and retreat from; HP, not damage, sets the tempo, so flanks resolve first, the center grinds, and Siege duels last longest. Every unit on both sides runs the same three-check decision loop: flinch from what you cannot fight, obey the player, shoot the nearest thing in range. Abilities are the mastery layer: ignorable by a new player, decisive in skilled hands, every one a commitment with a tradeoff.

The numbers below are the Tier 2 Settled Reach baseline; they are tuned by headless simulation, not by hand (Stage 1 A-261).

## Obviously working in 60 seconds

Spawn 10 Vanguards versus 10 Raiders at 250 wu apart on layer 3 and attack-move both. The Vanguards win with 5 or more survivors; the fight lasts at least 45 s. Swap the Raiders for 10 Bombards at 1,000 wu with one Raider forward as their eyes: the Bombards fire on the Vanguards as they close; without the Raider the Bombards hold fire until the Vanguards are within their 300 wu sensor (E-12 R-093-02). Send 4 Raiders around the flank into 4 Bombards: the Bombards die. Pop Surge on a Raider: it moves at 375 wu/s and hits for 18 for 3 s, then cannot Surge again for 75 s. Same seed, same fight, tick for tick.

## Stories

### S-081 — Three categories, a soft triangle
As a commander, I want Strike to beat Siege, Siege to beat Line, and Line to beat Strike, with none of it a death sentence, so that composition matters and positioning can still overturn it.

Rules
- R-081-01  Given an attacker of category A and a target of category B, When damage is dealt, Then damage = base damage × M[A][B] with M: Strike→Strike 1.0, Strike→Line 0.75, Strike→Siege 1.5; Line→Strike 1.5, Line→Line 1.0, Line→Siege 0.75; Siege→Strike [Q-081-01: 0.20 in code, 0.75 in the bible], Siege→Line 1.5, Siege→Siege 1.0.
- R-081-02  Given equal power of Line versus Strike in a straight fight, When resolved, Then Line wins with at least 30 percent of its HP remaining; the same for Siege versus Line and Strike versus Siege from the flank.
- R-081-03  Given a Bastion attacked by 4 Raiders from the flank, When resolved, Then the Bastion survives at least 20 s (the Siege exception to Strike-beats-Siege).
- R-081-04  Given any matchup, When resolved, Then time to kill at a 1.5× advantage is 30 to 40 percent shorter than at 1.0×.

Inputs: unit categories; base damage.
Outputs: damage events in the tick delta; HP.
Open flags: Q-081-01.

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
- R-082-05  Given the roster, When AoE is read, Then only the Bombard has an area attack.
- R-082-06  Given an expansion pack adds a unit type, When loaded, Then it declares category, role, the stats above, and one ability, and no engine code changes.
- R-082-07  Given an era pack, When its roster is validated, Then it declares between 20 and 40 unit types, each with category, role, the stats above, and one ability, and the roster passes the balance scoring mechanism [Q-082-04]; an era built around a named conflict may weight its roster toward that conflict's sides [Q-082-05].
- R-082-08  Given Tier 1 and Tier 3, When profiles are read, Then HP and damage are 0.8× and 1.2× the Tier 2 values and all other ratios scale uniformly.

Inputs: unit profile table (per tier, per era pack).
Outputs: loaded roster; contract test.
Open flags: Q-082-03 (categories, roles, and the roster invariants past six types), Q-082-04 (the balance scoring mechanism), Q-082-05 (launch roster size per era and the conflict swing).

### S-083 — Stats, trait cards, ability
As a commander, I want to unlock trait cards and build a force that plays my way, so that units differ in kind, and never in a way that beats positioning.

Rules
- R-083-01  Given a unit type, When its profile is read, Then it has the stats of S-082, zero to two trait cards the player has chosen, and exactly one ability.
- R-083-02  Given a trait card, When applied, Then it changes a stat or a rule; no card or ability ever outweighs positioning: layer position and cross-layer geometry weigh more than any trait or ability, and cards granting vision across layers are kept to a minimum [Q-083-03: the weighting test].
- R-083-04  Given a player, When they play, Then trait cards are unlocked through play, in the register of Dead by Daylight and Age of Empires 3, and abused cards are nerfed after launch [Q-083-03: what earns a card, where it persists, whether the enemy fields cards].
- R-083-03  Given a Warden, When any friendly unit is within 300 wu, Then that unit takes 10 percent less damage and regains 0.075 HP per tick (the Warden's passive aura); a second Warden in range adds 0.05 reduction, not 0.10, and healing stacks per Warden.

Inputs: profile table.
Outputs: effective stats.
Open flags: Q-083-03 (unlock mechanism and the positioning-over-cards weighting test). Q-083-01 is closed: cards ship after launch; launch units are stats plus one ability. Q-084-01 is closed: a second Warden's reduction diminishes to 0.05. Chosen through the options pass, `docs/northstar/research/options/unit-traits/`, Q-083-02.

### S-084 — Flat damage
As a commander, I want damage to be simple and legible: base times matchup, full damage at any range within reach, area damage capped, so that I can predict a fight.

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
Open flags: Q-086-01 (bible cooldown ranges differ from code in places: Surge 60 to 90 vs 75, Barrage 75 to 100 vs 90, Fortify 60 to 80 vs 70, Brace 30 to 40 vs 35; confirm the code values as the design).

### S-087 — Every unit thinks the same way
As a commander, I want every unit on both sides to flinch from what it cannot fight, obey my orders, and otherwise shoot the nearest enemy in range, so that my skill is direction, not babysitting.

Rules
- R-087-01  Given a unit taking damage from an attacker it cannot see or cannot reach, When the loop runs, Then it moves 200 wu directly away from the damage direction and stops; once the attacker is visible and in range it stands and fights.
- R-087-02  Given a unit with an active player order, When the loop runs, Then the order wins over auto-engagement; a plain move never acquires or returns fire.
- R-087-03  Given an idle or attack-moving unit with an enemy within attack range on its layer, When targets are evaluated, Then it attacks the nearest such enemy; an engaged target still alive and in range is kept.
- R-087-04  Given an attack-moving unit whose target is not within its attack range and a visible enemy within sensor range, When evaluated, Then its move goal becomes the nearest visible enemy and it walks there by its ordinary movement (R-097-03), steering around units in its way; it holds position only while its own target is within its attack range, and pursues again when the target leaves that range.
- R-087-05  Given an attack-moving unit that acquires a target, When it does, Then it anchors at its position, and if the target moves more than 200 wu from the anchor it drops the target and resumes its path.
- R-087-06  Given an idle or attack-moving unit with no target taking damage, When hit, Then it targets the attacker (return fire); if the attacker is out of range it attack-moves to the attacker, dropping its earlier destination; a plain-moving unit and an already-engaged unit ignore incoming damage for targeting.
- R-087-07  Given a supply or evacuation unit, When the loop runs, Then it never attacks; it flinches and otherwise holds.
- R-087-08  Given target acquisition, When it runs, Then each unit re-acquires on every 4th tick (cohort stagger) and validates its current target every tick.

Inputs: unit states; visibility (E-12); orders (E-13).
Outputs: target ids and attack events in the tick delta.
Open flags: Q-088-01 (the "cannot reach" branch of the flinch check has no definition of reach; code flinches only on return-fire failure).

### S-088 — Reading units on screen
As a commander, I want a Strike squad to read as a small group, a Siege unit as a single heavy asset, and every ability to have an unmistakable cue, so that I never misjudge what I am looking at.

Rules
- R-088-01  Given a Raider or Interceptor, When drawn, Then it appears as 3 to 5 small craft in formation sharing one HP bar and one position; the sim tracks one entity.
- R-088-02  Given an ability event, When received by the renderer, Then a cue plays at that tick for the event's duration (Barrage shows its telegraph ring at the target for 1.5 s before impact; Fortify shows its zone; Brace shows a planted state).
- R-088-03  Given a T2 screenshot of a mixed force, When inspected, Then category is distinguishable by silhouette size: Strike smallest, Siege largest.

Inputs: unit types; ability events.
Outputs: screen.
Open flags: none beyond the missing reference. Reference required: `references/E-11/notes.md`, missing.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Unit profile table | Era pack, per tier | 20 to 40 types per era, stats as S-082 | missing field fails load |
| Ability activation | Player (E-13 command) or enemy macro | unit ids | on cooldown or dead: rejected |
| Positions, layers, visibility | E-01, E-12, E-13 | | |
| Elevation flag | Era pack | bool, false for the Settled Reach | |

## Outputs

| Output | Observable where |
|---|---|
| HP, target, ability state, cooldown | Tick delta per unit; HUD portrait panel; unit HP bars |
| Damage and ability events | Tick delta events; renderer cues; T1 trace |
| Pacing invariants | T1 trace |

## Invariants

- HP in [0, max]; a unit at 0 HP is dead on that tick and never acts again.
- Exactly one ability per type; at most one active per unit.
- No damage across layers (pending Q-008-01).
- Total AoE per attack ≤ 4 × base.
- Same seed and commands, same fight, all platforms.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): targeting and damage for 1,000 units in under 2 ms per tick, 10,000 in under 25 ms. The 10,000-unit figure is measured at the 10 ticks/s rate the sim drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the 1,000-unit figure at 20 ticks/s.

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

## Open ambiguity flags

Q-081-01, Q-082-01, Q-083-01, Q-084-01, Q-086-01, Q-088-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01 Layer system (same-layer targeting, transition window).
- E-12 Fog and sensors (visibility for acquisition).
- E-13 Movement (orders, leash, backswing, collisions).
- E-18 Combat visuals (cues).
- E-21 Offline AI pipeline (tier profiles, per-era packs).
