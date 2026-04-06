# Ouroboros Manifold — Force and Combat Design Reference

> **Extracted from game_bible.md v1.23, updated v2.01.** This file is authoritative for unit roster,
> combat categories, abilities, unit behavior AI, and force design. If this file conflicts with game_bible.md,
> flag it for Westley — do not silently resolve the conflict.
>
> **Modification rule:** Same as the master bible — append-only unless Westley approves
> deletion. Resolved open questions get written here AND reflected back to the hub.

---

## Force and Combat Design

### Unit Combat Categories — Strike / Line / Siege

Three broad categories on a soft RPS spectrum:

**Strike** — fast, fragile, high burst damage. Good at flanking, raiding supply lines, picking off isolated targets. Weak in sustained engagements against heavy units. Think destroyers, interceptors, raider craft. Commanded as **squads** (Halo Wars model — groups of smaller units that move together).

**Line** — the backbone. Balanced durability and firepower. Wins through sustained engagement and formation. The units you build your force around. Think cruisers, frigates, standard combat units. Commanded as **individual units or small groups** depending on size.

**Siege** — slow, durable, massive damage at range. Dominates in set-piece engagements but vulnerable to flanking strikes. Think battleships, artillery platforms, carriers. Commanded as **individual high-value assets** — each one matters, losing one hurts.

**The RPS flow:** Strike flanks and kills Siege. Siege outranges and crushes Line. Line absorbs and overwhelms Strike. But it's **soft** — a well-positioned Siege unit with escort can survive a Strike attack. A Strike wing that catches Line units out of formation can win. The counters create pressure, not guarantees. Positioning and abilities can overcome a bad matchup, but you're fighting uphill.

### Unit Differentiation

Units differ through **stats + traits + abilities** (the full package):

- **Stats** — speed, firepower, durability, range, sensor radius. The baseline. AI-generated within defined ranges per unit type.
- **Traits** — passive characteristics. A unit might have "hardened hull" (extra resistance to Strike damage) or "long-range sensors" (sees further). One or two per unit type, AI-generated from a constrained trait pool.
- **Abilities** — one active ability per unit type. These are the mastery layer — a new player can ignore them and still play, a skilled player uses them to create decisive moments. See "Abilities — One Per Unit" below for the full design.

### Unit Roster — 6 Base Types

The base game ships with **6 unit types** — two per RPS category. This is the minimum viable roster that makes the RPS triangle work and produces real composition decisions. Additional unit types can be added through expansion packs (new types are expansion content, not engine changes — consistent with the skeleton/skin model).

**Strike (commanded as squads)**

**Raider** — the flanker. Fastest unit in the game, fragile, high burst damage against isolated targets. The unit you send around the side to kill artillery or cut supply lines. Excels when it catches something alone. Dies fast in a straight fight against Line. The defining Strike unit.

**Interceptor** — the screen. Fast, moderate durability for a Strike unit, lower damage than the Raider. Its job is denying enemy Strike units — it hunts Raiders and protects slower high-value assets. The defensive Strike option. Think destroyer escort.

**Line (commanded individually or in small groups)**

**Vanguard** — the frontliner. Durable, moderate damage, holds position. The unit you build your formation around. Wins through sustained engagement. Not flashy, but losing one hurts because it's holding the line.

**Warden** — the support. Lower damage, moderate durability, but provides area buffs (damage reduction, repair over time) to nearby friendly units. Force multiplier. A Vanguard next to a Warden is significantly harder to kill than a Vanguard alone. Makes positioning decisions matter — cluster for the buff, but clustering makes you vulnerable to Siege area damage.

**Siege (commanded as individual high-value assets)**

**Bombard** — long-range area damage. The classic artillery piece. Dominates open engagements at range. Crushes Line formations. Extremely vulnerable to Strike flanking — if a Raider reaches the Bombard, it dies fast. The unit that forces the enemy to move.

**Bastion** — slow, extremely durable, moderate damage at medium range. The anchor. Doesn't have the Bombard's range or area damage, but it survives Strike flanking. The Siege unit you bring when you expect to be attacked — it holds ground and absorbs punishment. Think mobile fortress.

**The soft RPS with this roster:**
- **Strike beats Siege:** Raiders flank and destroy Bombards. The Bastion is the exception — it survives Strike flanking, which is what makes it a meaningful choice over the Bombard.
- **Siege beats Line:** Bombard area damage shreds Vanguard formations. Warden buffs help but can't fully counter sustained Bombard fire. The player must close the distance or flank with Strike.
- **Line beats Strike:** Vanguards absorb and overwhelm Raiders in a straight fight. Interceptors fare better against Line than Raiders do, but they're still outmatched. Strike units need to avoid Line engagement, not win it.

### Abilities — One Per Unit

Each unit type has **one active ability** that defines its mastery ceiling. Abilities amplify what the unit already does — they don't give it a new role. A new player ignores abilities and still plays effectively. A skilled player uses them to create decisive moments. Every ability is a commitment with a tradeoff.

**The ability designs below are era-agnostic engine behaviors.** The names listed are sci-fi theme pack names for the base game. Other theme packs provide their own names and visual effects for the same mechanical behaviors. The engine knows "short burst of increased speed and damage on a Strike unit." The theme pack knows what that looks like and what it's called.

**Raider — "Surge" (sci-fi name).** Short burst of dramatically increased speed and damage. Lasts a few seconds. The Raider becomes a missile — close distance instantly, deliver a devastating alpha strike, then it's back to being fragile. Skill expression: timing the dive on an exposed, unescorted target. Cooldown: long (60–90 seconds). One or two uses per engagement.

**Interceptor — "Intercept" (sci-fi name).** Passive proximity trigger. When any enemy Strike unit moves within the Interceptor's detection radius, the Interceptor automatically gains a speed boost toward that unit and a damage bonus for the first engagement. No manual activation — it triggers on proximity. Cooldown after each trigger prevents chain-reacting to multiple Strike units simultaneously. Skill expression: positioning the Interceptor near what needs protecting. A new player parks it near their Bombard and it works. A skilled player positions multiple Interceptors to create overlapping denial zones across an entire flank.

**Vanguard — "Brace" (sci-fi name).** The Vanguard plants and becomes immobile. While braced, it takes significantly reduced damage from all sources and deals increased damage to anything in its engagement range. A braced Vanguard in a chokepoint is nearly immovable. Tradeoff: can't reposition while braced; if the threat shifts, you're stuck. **Transition time:** Brace has a windup delay (config value, e.g. 1.5–3 seconds) where the unit is immobile but does not yet have the defensive bonus. The same transition delay applies when canceling Brace. This punishes reactive Bracing (enemy already on you, panic-Brace, eat full damage during windup) and rewards predictive Bracing (read where pressure is coming, commit early). Both transition times are tuning values for playtesting. Cooldown: moderate (30–40 seconds).

**Warden — "Rally" (sci-fi name).** Burst area heal/repair to all friendly units within range. Instantly restores a chunk of durability. The emergency button — the Vanguard line is cracking under Bombard fire, Rally buys another 15 seconds. Skill expression: holding Rally for the critical moment when the line is about to break, rather than using it early. Cooldown: long (60–90 seconds). One, maybe two uses per engagement.

**Bombard — "Barrage" (sci-fi name).** Concentrated high-damage volley at a targeted area. Significantly more damage than normal fire, focused in a smaller area, over a short duration. Tradeoff: brief visual telegraph before impact gives the opponent a window to scatter. Skill expression: baiting the enemy into clustering before calling Barrage; reading the telegraph and scattering when the enemy uses theirs. Cooldown: long (75–100 seconds). One use per engagement in most cases.

**Bastion — "Fortify" (sci-fi name).** Deploys a temporary defensive zone around the Bastion. All friendly units within the zone gain moderate damage reduction for a significant duration. The Bastion can still move (slowly) while Fortify is active — the zone moves with it. Tradeoff: the zone is visible to the enemy, telegraphing where the protected area is. Skill expression: positioning the Bastion to create a safe pocket over what matters most (protecting a Bombard from Raiders, shielding a damaged Vanguard line). Cooldown: long (60–80 seconds).

### Roles Within Categories

The 6-unit roster uses a **sparse role matrix** — not every RPS category has every role. Each unit type fills exactly one role, and every cell in the matrix has a clear reason to exist:

- **Strike:** Raider (skirmisher/flanker), Interceptor (screen/escort)
- **Line:** Vanguard (frontliner), Warden (support)
- **Siege:** Bombard (artillery), Bastion (frontliner/anchor)

Deliberately absent from the base roster: Strike artillery, Strike frontliner, Line artillery, Line skirmisher, Siege support, Siege skirmisher. These are potential expansion content — each new unit type added to a category creates new composition decisions without changing the engine.

### AI-Generated Unit Variety

The engine owns the mechanics — the 6 unit types, their abilities, and their roles are hand-designed and consistent across all factions and eras. **AI tunes the numbers based on civilization traits.** A militaristic civilization's units skew toward higher firepower. An expansionist civilization gets faster, lighter units. A civilization in technological decline has units with degraded stats but maybe improvised traits.

The framework is:
- The 6 base unit types are fixed (always a Raider, always a Bombard, etc.)
- Stats within each type have defined ranges
- AI generates the specific stat profile, names, and flavor for this civilization's version
- The engine can handle any output because the constraints guarantee mechanical validity

### Unit Power Balancing and Force Parity

Because the AI library has a hand in unit stat values, the game needs a system for calculating a unit's overall **power rating** (strength value) based on its combined stats, traits, and abilities. This power rating serves as the currency for force allocation:

- Every unit generated by the library gets a computed strength score derived from its stat values, trait effects, and ability impact
- The strength score is the basis for **force parity** — ensuring every mission presents a winnable fight

**Force parity system.** When a mission is generated from a faction conflict, the enemy force's total strength is determined by the attacking faction's committed budget (translated from abstract budget into concrete unit strength). The player receives a force with a **comparable total strength**, adjusted by the civilization's current capacity:

- A thriving civilization (high capacity composite) gives the player close to 100% parity — a fair fight where skill determines the outcome
- A declining civilization gives the player 80–90% parity — still winnable, but the player is the underdog
- The capacity-to-parity curve is a config value. The penalty range is narrow enough that a skilled player can always win

**Difficulty setting** scales the parity penalty: Easy = minimal penalty even when civilization is weak (near-100% parity always), Hard = steeper penalty curve (a declining civilization gives you meaningfully less to work with). Difficulty never changes the enemy's strength — only the player's allocation.

Both sides receive their forces from the same **unit composition pools**. Each faction's units are drawn from the AI-generated library for that faction's civilization traits. Two forces with equal total strength but different unit mixes play differently — one might be heavy on Siege and weak on Strike, the other the reverse. The RPS system creates tactical decisions even at parity.

**Multi-faction battles (3–4 way).** When multiple hostile factions are in conflict in the same region (e.g., the player defending against both the Conqueror and a breakaway faction), each faction's force is sized by its own committed budget/strength. The player's force is sized to match the total enemy strength (with civilizational capacity adjustment). The hostile factions may fight each other as well as the player — exploiting inter-enemy conflict is a tactical opportunity.

The power rating formula is an implementation detail to be designed during the force/combat stages, but the principle is: **every mission should be a winnable fight where player skill is the deciding factor, not a math problem decided before the mission starts.**

### Force Allocation Algorithm

The player does not choose their force composition. The civilization decides what to give them based on the mission type and its own state. There is no loadout screen, no requisition interface, no economy management during gameplay. The player's influence over force composition is front-loaded into the **mission preference weights** set at game start — preferred mission types are received more often, and mission type determines the asset profile.

The allocation algorithm:

1. **Mission archetype defines the target asset profile.** Each mission archetype specifies what ratio of combat unit types the mission expects: a defensive stand is heavy on Line and Bastion, an interception is heavy on Raider and Interceptor, a counterinsurgency is light mobile forces only. The asset profile is authored per archetype as part of the mission template library.

2. **Force parity system defines the total strength budget.** The enemy force's total strength (from committed faction budget) sets the baseline. The civilization's current capacity composite and the difficulty setting adjust the player's allocation as described above.

3. **The strength budget fills the asset profile.** The allocation system spends the strength budget filling the archetype's target ratio from the available unit types, drawn from the AI-generated library for the player's faction. Within the combat unit allocation, composition is determined by the faction's library — a militaristic civilization's library skews toward more Siege and Line, an expansionist civilization's skews toward more Strike.

4. **Capacity shortfalls reduce quantity, not quality.** If the civilization can't fill the full asset profile (declining economy, regions lost, low capacity), some slots go unfilled — the player receives fewer units, not weaker ones. The mission briefing notes what the civilization couldn't spare ("Command was unable to provide the full escort complement — the Periphery garrisons are stretched thin"). This communicates the civilization's state through the briefing prose and creates drama through scarcity, not through invisible stat penalties.

### 2.5D Vertical Layers

Combat uses **3–5 vertical layers** rather than a flat 2D plane or full 3D movement. Units exist on a layer and can transition between adjacent layers.

**Layers are a property of the map, not of units.** The map defines which layers are accessible at each position through a **layer accessibility mask**. Terrain features block specific layers — an obstacle occupying layers 1–2 forces units to maneuver over it on layers 3–5, or find a route around it on the blocked layers. All unit types can move to any layer the map says is accessible at their position — there are no category restrictions on layer transition. Transition between layers takes time (config value per unit type — Strike transitions faster than Siege), creating natural differences in how aggressively each unit type exploits vertical movement.

**Layer accessibility is era-agnostic.** The engine knows "terrain obstacle occupying layers 1–2 at position X." The theme pack determines what that looks like: an asteroid in sci-fi, a mountain in a land theme, a reef in a naval theme. The strategic decision (go over, go around, exploit the blocked layers for cover) is identical regardless of era.

**Layer visibility is tied to sensor coverage.** Sometimes you can see all layers (good intel mission). Sometimes you're partially blind (fog of war on layers above/below your sensor range). This creates tactical uncertainty — an enemy force on a layer you can't see is invisible until they strike or enter your sensor coverage.

**Layer design is part of map generation.** The spine + gradient system includes layer accessibility as a gradient property. See "Map Generation System" for how the Strategic Layout Authoring Framework and per-archetype compatibility filters use layer blocking to create tactical terrain. Layer accessibility, like all gradient properties, can vary spatially (an area might have all 5 layers open while an adjacent area has layers 1–2 blocked) and can overlap with environmental hazards (a sensor interference zone on layer 3 but clear visibility on layers 1–2).

### Camera and Player View

The player controls a **standard RTS camera** — free pan and zoom at all times. No automatic anchoring, no camera modes, no forced following. The player manages their own viewport like Age of Empires 3 or StarCraft 2. A minimap provides strategic awareness of the broader tactical space.

The moving battlefield is communicated through **world-space movement under free camera.** Convoys move across the map, environmental features drift, gravitational effects shift unit positions — all happening in the world while the player pans freely to observe and react. The skill is in attention management: watching the convoy's front for incoming threats versus checking the rear for flanking Raiders. No special camera mechanics are needed — movement happens in the world, the player watches from wherever they choose.

### Moving Battlefields

Engagements are **not static arenas.** The tactical space shifts during combat:

- Battles can happen while forces are in transit — the convoy keeps moving, the fight happens around it
- Environmental features drift through the combat zone — terrain that provided cover shifts, opening or closing sightlines
- Gravitational or environmental forces can pull units in a direction (future expansion — noted as a natural extension of the movement drag hazard type at solar system scale)

This means positioning is never "solved" — the player must continuously adapt to a changing spatial situation.

### Environmental Hazards

The base game ships with **one environmental hazard type** as a gradient field property (position, radius, intensity, falloff) that can vary by layer and move over time. Era-agnostic — the engine defines the gameplay effect, the theme pack determines the visual presentation.

**Sensor interference zone** — units inside have reduced sensor radius. Units outside looking in can't see as far into the zone. Creates fog pockets on the map. Tactical use: hide forces inside for ambush, deny enemy information, or avoid the zone because you don't know what's inside. Era examples: nebula (sci-fi), fog bank (naval), dense forest (land), sandstorm (desert).

**[Future expansion:]** Additional hazard types (movement drag zones, damage zones, boost corridors, ability disruption zones) can be added as new gradient property tags without engine changes. The gradient field system is extensible by design — each new hazard type is a new property the engine samples, not a new system. These are noted as natural expansion points once the base game is proven and fun.

### Engagement Scale and Duration

- **Engagement scale** — the player is in the battle. Units are on screen. The player is positioning individual groups and squads.
- **Variable duration** — some engagements are quick skirmishes (a few minutes), others are prolonged campaigns within a single mission. Duration depends on mission type and what the player encounters.

### Tactical Variety — Mission Type Differentiation

Different mission types feel different through the combination of three existing systems, not through mission-type-specific tactical mechanics:

**Force composition** — the force allocation algorithm gives the player a different unit mix based on mission archetype. A defensive stand is heavy on Line and Bastion. An interception is fast Raider and Interceptor units. A counterinsurgency is a light mobile force. The units you have determine how you play.

**Map character** — the spine + gradient map generation system, guided by the Strategic Layout Authoring Framework, produces different maps per mission archetype. A defensive stand generates chokepoints and prepared positions. An interception generates open terrain for meeting engagements. A containment generates a wide front with multiple approach corridors. Each archetype defines compatibility filters that select appropriate strategic layouts from the shared library.

**Objective shape and pacing** — "hold X until Y" plays differently from "get A from B to C" even on identical maps. The timer, the success spectrum, and what counts as partial success create distinct pacing per archetype.

No additional mission-type-specific rules are needed. The combination of different forces + different maps + different objectives produces distinct tactical experiences through the same engine. This is consistent with the skeleton/skin principle — the engine is uniform, the content (force profiles, map scripts, objective templates) creates variety.

### Unit Behavior AI

> **RESOLVED (v2.01).** Unit behavior is a single universal system shared by all units on both sides across all mission archetypes. Player units and enemy units run the same decision loop. The design philosophy draws from Immortal: Gates of Pyre's accessibility approach — units handle the basics competently so the player's skill expression is in strategic direction (where to send forces, when to commit, how to position), not in babysitting individual units. Archetype differentiation happens at the mission setup and simulation level, not in per-archetype unit micro behavior.

#### Unit Decision Loop — Universal, Priority-Ordered

Every unit evaluates three checks each frame, in priority order. The first check that produces an action wins. This loop is identical for all 6 unit types, player and enemy units alike.

**1. Am I taking damage from a source I cannot engage?** If the unit is receiving damage from an attacker it cannot see (fog of war, different layer outside sensor range) or cannot reach (out of weapon range with no path to close distance), the unit automatically moves a short distance away from the damage direction. This is a flinch, not a strategic retreat — the unit breaks contact and stops. If the player wants to push back into the danger, they issue an explicit move order. Once the damage source is visible and in range, this check no longer triggers — the unit stands and fights.

**2. Do I have a player-issued order?** If the unit has an active order (move, attack-move, hold position, target specific enemy), it executes that order. Player orders always override autonomous behavior. A manual target order persists until the target dies, moves out of range, or the player issues a new order.

**3. Is there an enemy in my engagement range?** If yes, the unit attacks the **nearest enemy**. No RPS-aware targeting, no priority lists — closest threat gets shot. If the unit is already engaged with a target that is still alive and in range, it continues engaging that target rather than switching (no target ping-ponging). If no enemy is in range, the unit holds position.

**Supply unit exception.** Supply units have no attack capability, so check 3 for them is simply "hold position." Their primary survival mechanism is check 1's retreat behavior — they flinch away from any damage source since they can never fight back.

#### Abilities — Player-Activated Only

All unit abilities are **manually activated by the player**. No auto-cast, no smart suggestions, no trigger conditions evaluated by the AI. The ability bar in the UI displays each unit's ability and its cooldown state. The player learns ability timing through gameplay experience.

**Ability education happens in the tutorial**, not during missions. The tutorial teaches what each unit type's ability does, when it's useful, and how to activate it. During missions, the only ability information displayed is the cooldown indicator on the UI bar — no contextual prompts, no "ability ready" notifications beyond the bar itself.

**The one exception** is the Interceptor's "Intercept" ability, which is defined in the ability spec as a passive proximity trigger (see "Abilities — One Per Unit" above). This is not a contradiction — Intercept is a passive that the player positions for, not an active ability the player clicks. The skill expression is where you park the Interceptor, not when you press a button.

#### Enemy Units — Same Loop, No Special Intelligence

Enemy units run the identical decision loop as player units. They acquire the nearest target, return fire, flinch from damage they can't engage, and use abilities on cooldown when minimally sensible conditions are met (enemies in range for offensive abilities, friendlies nearby for defensive abilities). Enemy ability usage is simple threshold-based — no sophisticated timing optimization.

What makes each mission archetype *feel* different from the enemy's side is not AI micro behavior but **mission setup**: where enemy units are placed, what scripted macro objectives they pursue (advance toward player position, hold defensive positions, hide and ambush, patrol routes), and what composition they have. The mission generator authors these macro-level behaviors per archetype at generation time. The unit-level AI is always the same — the variety comes from the tactical situation the setup creates.

**Enemy macro objectives are a separate design question** from unit behavior AI and will be specified when the mission-level AI system is designed. The unit behavior system described here is the foundation that macro objectives build on top of.

---

### Tactical Simulation Architecture — SC2-Style Sim/Renderer Split

> **RESOLVED (v2.02).** The tactical combat system uses a strict separation between simulation and rendering, modeled on StarCraft 2's replay architecture. The simulation is the ground truth; the renderer is a visualization layer with zero gameplay logic.

**Layer 1 — Tactical Simulation Engine (Python, headless).** A deterministic, tick-based combat engine that owns all ground truth: unit positions on a continuous 2D coordinate space with vertical layers, HP, damage, ability cooldowns, movement, the unit behavior AI decision loop, objective tracking, and outcome band classification. Runs at a fixed tick rate (20 ticks/sec, config value). Every tick, it processes player commands from an input queue, runs the unit decision loop for all units, resolves damage, updates positions, and emits a state delta. Fully testable in Python with no visual dependencies — headless validation of hundreds of engagements per hour, automated balance testing, and deterministic replay reproduction.

**Layer 2 — Command Interface (the "replay feed").** A thin protocol carrying player commands into the simulation and state updates out. During live play, Godot captures player inputs and translates them into simulation commands. During replay, the same commands are read from a saved file. The simulation does not know or care which source commands come from.

**Layer 3 — Renderer (Godot).** Reads simulation state and draws it. Interpolates between tick states for smooth visuals (simulation at 20 ticks/sec, Godot at 60fps = 3 render frames per tick). Plays animations, particle effects, sound. Handles camera. Zero gameplay logic.

**Determinism guarantee.** Given the same initial state (map seed, unit positions/stats, objectives) and the same command stream (player inputs with tick numbers), the engine reproduces any engagement tick-for-tick, bit-identically. Replay files store only initial state + command stream; the engine re-derives everything else.

---

### Damage Model

> **RESOLVED (v2.02).** Multiplicative category multipliers inspired by Age of Empires 3's tag-based system, adapted for the simpler 3-category RPS triangle. Flat HP pools.

**Damage formula:**

```
damage_per_attack = base_damage × category_multiplier × (1.0 - cover_density_at_position)
```

**Category multiplier matrix** (era-agnostic — uses Strike/Line/Siege categories):

|  | Target: Strike | Target: Line | Target: Siege |
|---|---|---|---|
| **Attacker: Strike** | 1.0× | 0.75× | 1.5× |
| **Attacker: Line** | 1.5× | 1.0× | 0.75× |
| **Attacker: Siege** | 0.75× | 1.5× | 1.0× |

The RPS is **soft**: 1.5× provides a meaningful advantage (~30–40% faster time-to-kill) without being a death sentence. Positioning, abilities, and numbers can overcome an unfavorable matchup. Units within each category are differentiated by stats, not by multiplier exceptions — the Bastion survives Strike flanking because of its HP pool (1400), not a special multiplier.

**Attack timing.** Each unit has `base_damage` (per attack) and `attack_interval` (seconds between attacks). DPS = base_damage / attack_interval.

**Range.** Constant damage within weapon range. No distance falloff.

**Area damage (Bombard).** Circle AoE centered on target position. Full damage to every enemy within `aoe_radius`. Damage cap: total AoE damage per attack ≤ `base_damage × aoe_damage_cap_multiplier` (default 4.0×).

**Cover.** `cover_density` gradient at target unit's position reduces incoming damage as a percentage. Cover_density 0.4 → unit takes 60% damage. Era-agnostic.

**Elevation damage bonus.** Config flag `ELEVATION_DAMAGE_BONUS_ENABLED`. When enabled (land-based eras), higher elevation → bonus damage per tier. **Disabled for space era** — elevation affects sensor coverage only. The engine computes elevation difference always; the flag controls whether it modifies damage.

---

### Stat Philosophy — Long Engagements with Category-Specific Rhythm

> **RESOLVED (v2.02).** Engagement pacing follows an A+C hybrid: all fights are long enough for positioning and abilities to matter, but different categories fight at different tempos.

**Pacing targets:**
- Small skirmishes (5v5): minimum 10–15 seconds
- Medium engagements (25v25): 30–50 seconds
- Large battles (100+ per side): well over 60 seconds
- Mirror 50v50 (balanced composition): 45–75 seconds

HP pools create tempo differences. Strike has the lowest HP (fastest fights, ~10–15 sec minimum). Line has moderate HP (baseline, ~20–30 sec). Siege has the highest HP (slowest, ~30–45 sec). DPS is moderate across all categories; HP is the primary differentiator. In large battles, flanks resolve first (Strike), the center grinds next (Line + Warden), and Siege duels continue longest — creating layered attention-management gameplay.

---

### Unit Stat Baselines — Tier 2

> **RESOLVED (v2.02).** Hand-designed Tier 2 baseline stats. Tier 1/Tier 3 are config-level variants. AI-generated per-civilization stat variation is **on hold** — engine supports it, generation pipeline deferred. All values are config parameters.

| Stat | Raider | Interceptor | Vanguard | Warden | Bombard | Bastion |
|---|---|---|---|---|---|---|
| **Category** | Strike | Strike | Line | Line | Siege | Siege |
| **HP** | 250 | 350 | 800 | 600 | 700 | 1400 |
| **Base Damage** | 18 | 12 | 15 | 8 | 35 | 14 |
| **Attack Interval (sec)** | 0.8 | 1.0 | 1.2 | 1.5 | 3.0 | 1.8 |
| **DPS** | 22.5 | 12.0 | 12.5 | 5.3 | 11.7 | 7.8 |
| **Attack Range (wu)** | 200 | 250 | 300 | 350 | 600 | 400 |
| **Speed (wu/sec)** | 150 | 130 | 80 | 90 | 50 | 40 |
| **Sensor Radius (wu)** | 400 | 500 | 350 | 400 | 300 | 300 |
| **Layer Transition (sec)** | 1.0 | 1.2 | 2.5 | 2.0 | 4.0 | 5.0 |
| **AoE Radius (wu)** | — | — | — | — | 150 | — |

"wu" = world units. See canvas sizing in `bible_world.md`.

---

### Command Vocabulary

> **RESOLVED (v2.02).** Five commands. No patrol, no follow, no hold position, no stop.

- **`move`** — move to position
- **`attack_move`** — move to position, engaging enemies in range along the way
- **`attack_target`** — attack a specific enemy unit
- **`activate_ability`** — trigger the unit's active ability (toggle for Brace)
- **`group_move`** — all selected units move together to target position

Commands are recorded with tick numbers for replay. The engine processes all commands for the current tick before advancing state.

---

### Squad Mechanics — Visual Only

> **RESOLVED (v2.02).** Strike units (Raider, Interceptor) are "commanded as squads" — this is purely visual. In the simulation, each squad is one entity with one HP pool, one position, one set of stats. Godot renders it as 3–5 small ships in formation. The simulation does not track individual squad members.

---

### Supply and Non-Combat Units

> **RESOLVED (v2.02).** Supply units, evacuation convoys, and non-combat assets are entities in the tactical simulation with HP but no attack capability. Their decision loop skips auto-engage (check 3). Primary survival: flinch retreat (check 1). They are objective targets for evacuation and escort missions.

---

### Pathfinding — Hierarchical A* with Steering

> **RESOLVED (v2.02).** Two-level movement: coarse A* pathfinding for route planning, fine steering behaviors for organic movement between waypoints.

**Coarse level:** A* on a precomputed navmesh per layer, generated from the map's `obstacle_density` gradient. Path caching for shared destinations.

**Fine level:** Steering behaviors between waypoints — seek, obstacle avoidance, separation from friendlies. Produces smooth movement without single-file corridors.

**Layer transitions.** Unit enters transition state lasting `layer_transition_time` ticks (Strike fastest, Siege slowest). During transition, unit cannot attack or be targeted by same-layer units.

---

### Power Rating Formula

> **RESOLVED (v2.02).** Single strength value per unit for force parity.

`power = effective_hp × dps × range_factor × mobility_factor × ability_bonus`

- `effective_hp` = max_hp adjusted for typical cover
- `dps` = base_damage / attack_interval
- `range_factor` = logarithmic range bonus (diminishing returns)
- `mobility_factor` = speed / normalization constant
- `ability_bonus` = flat percentage per unit type (e.g., Surge +15%, Brace +20%)

AoE units (Bombard) receive an additional multiplier. Force total = sum of all unit power ratings.
