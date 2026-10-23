# Force and Combat Design

Spoke. Authoritative for unit roster, combat categories, abilities, damage model, stat baselines, command vocabulary, pathfinding, power rating, AI-generated variety, force allocation, enemy macro behavior, combat visuals. If this conflicts with `game_bible.md`, the hub wins.

Rewrite-not-append, like every bible file.

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

**Era-specific unit-type layer restrictions.** The engine supports an optional **per-unit-type layer restriction mask** configured at the era-skin level. When an era defines layer restrictions, each unit type has a set of layers it is permitted to occupy. The engine enforces this alongside the map's layer accessibility mask — a unit can only be on a layer that is both accessible at its position AND permitted for its unit type. Eras that do not define restrictions (e.g., the Settled Reach sci-fi era, where all units are spacecraft capable of any altitude) leave the mask unrestricted and the system behaves exactly as designed above. Eras that define restrictions use them to create thematic layer assignments: a 1980s-era expansion might restrict submarines to layers 4–5 (underwater), ships and land units to layer 3 (surface), and aircraft to layers 1–2 (airspace). A Roman-era expansion might restrict all units to the top layer only (ground combat, no vertical movement). This is a skin-level decision — the engine behavior is identical regardless of whether restrictions are active. The restriction mask is part of the era pack's JSON config, not hardcoded.

### Layer Assignment Hotkey

> **RESOLVED (v2.05).** Two layer-interaction commands accessible through the layer UI and keyboard shortcuts. Part of the Stage 8 command interface.

The player has two distinct ways to control unit layer behavior:

**Hard layer transfer** — an immediate command to move selected units to a specific layer. The unit transitions to the target layer as soon as it reaches a position where the layer is accessible (per the map's layer accessibility mask and any era-specific unit-type layer restrictions). If the unit is already at an accessible position, it transitions immediately. This is a one-time command, not a persistent setting. Issued via clicking a layer on the layer UI panel or via a keyboard shortcut (implementation TBD, Stage 8).

**Layer preference assignment** — a persistent preference that tells selected units to favor a specific layer whenever accessible. A modifier hotkey (user-rebindable, default TBD) temporarily remaps keys 1–5 to layer assignment. While held, pressing 1–5 sets the selected units' layer preference to that layer. The same assignment can be made by clicking the corresponding layer on the visual layer panel while the modifier is held. Units with a layer preference will transition to their preferred layer whenever the map's accessibility mask and era-specific restrictions permit it at their current position. When the preferred layer is inaccessible (terrain obstacle, layer blocked at that position), the unit continues executing its current orders on whatever layer it occupies — it does not stop or get stuck. It transitions to the preferred layer as soon as it reaches a position where the preference can be fulfilled. Layer preference persists until the player clears it (re-assign with the modifier, or a "clear preference" action) or issues a hard layer transfer, which overrides the preference.

**Interaction with control groups.** The modifier key remapping is temporary — it only applies while the modifier is held. Releasing the modifier restores the standard 1–0 control group bindings. The two systems (control groups and layer assignment) share no keys during normal play.

**Visual feedback.** Units with an active layer preference display a small layer-color indicator (consistent with the layer indicator ring system described in Open Design Question #16) showing which layer they prefer. This is distinct from the indicator showing which layer they are currently on.

### All-Army Hotkey — Re-Open Flag Per Principle 4

The current launch implementation includes a persistent all-army hotkey (per `game_bible.md` Stage 8 roadmap) that selects every player-owned combat unit and auto-includes newly produced units. This feature is **flagged for re-opening** under Foundational Principle 4 in `bible_design_vision.md` (Positional Thinking Over Command Shortcuts), which excludes features that allow the player to command the entire force as a single entity from the design at all difficulty levels.

**Status:**
- The launch implementation **is not changed** by this flag. The all-army hotkey continues to function as currently specified in Stage 8 until a future stage explicitly addresses the conflict.
- **Removal is not scheduled.** This flag is a marker that the current design contradicts a binding principle and that a future stage will need to either remove the hotkey, replace it with a non-conflicting alternative (e.g., camera-jump-to-engagement without selection), or formally re-decide the principle.
- Control group exclusive membership (already implemented per Track B/B3) is the canonical positive instance of Principle 4 and is unaffected by this flag.

**Accessibility implication.** Removing the all-army hotkey raises the effective skill floor of the base game. Principle 3 (Opt-In Complexity) and the existing "low floor, high ceiling" heuristic in `game_bible.md` Design Decision Heuristics both still apply — accessibility for new players must be preserved through other means when this flag is acted on. Possible affordances (none decided): generous Easy-mode parity tuning, simplified opponent behavior at low difficulties, opt-in assistive toggles labeled as accommodations, or a redesigned multi-group control flow that lowers the overhead of managing several groups. The specific solution is part of the future stage that addresses this flag.

### Camera and Player View

The player controls a **standard RTS camera** — free pan and zoom at all times. No automatic anchoring, no camera modes, no forced following. The player manages their own viewport like Age of Empires 3 or StarCraft 2. A minimap provides strategic awareness of the broader tactical space.

The moving battlefield is communicated through **world-space movement under free camera.** Convoys move across the map, environmental features drift, gravitational effects shift unit positions — all happening in the world while the player pans freely to observe and react. The skill is in attention management: watching the convoy's front for incoming threats versus checking the rear for flanking Raiders. No special camera mechanics are needed — movement happens in the world, the player watches from wherever they choose.

### Mid-Mission HUD Layout

> **RESOLVED (v2.13).** Layout reference: Immortal: Gates of Pyre. See `docs/legacy/design_questions/igop_hud_reference_alpha.png` and `igop_hud_reference_beta.png`.

The mid-mission HUD inherits IGoP's clustered-bottom-bar layout and restrained UI chrome, with IGoP's economy/production surfaces subtracted (Ouroboros has no resource currency, no tech tree, no unit-production grid — reinforcements come from captured structures) and Ouroboros-specific surfaces added (reinforcement-structure panel, layer selector).

**Top-left — persistent info column.** Stacks (a) the mission objectives list with progress indicators and (b) an event ticker surfacing significant in-mission beats (reinforcement structure captured / lost, force routed, objective threshold hit). Text-forward, low visual weight — the same register as IGoP's event ticker.

**Top-center — banner channel.** Empty by default. Used only for significant alerts (a captured structure falling to the enemy, an objective band crossing a threshold). Matches IGoP's boss-banner slot but is reserved for mission-significance moments, not permanent identity.

**Top-right — game clock, elapsed mission time, and pause/menu button.** Minimal.

**Bottom-center — main command cluster.** Single continuous horizontal bar:
- **Selected-unit portrait panel** (left-of-center): portraits + summed HP for current selection + ability slots showing cooldown rings. Ability bar is **cooldown-only** per "Abilities — Player-Activated Only" above — no contextual prompts, no "ready" notifications beyond the ring itself.
- **Minimap** (center or right-of-center): friendly units (bright), visible enemies (dim), terrain contours from the map's obstacle / elevation gradients, objective markers, reinforcement-structure icons colored by ownership.
- **Reinforcement-structure panel** (right of minimap): replaces IGoP's TRAIN / TECH / BUILD / POWER grid. One row per **player-owned** structure showing production-timer bar + next-unit icon + structure HP bar. Neutral and enemy-owned structures are visible on the world map but are not listed here — the panel is a "what am I producing" view, not a map overview.

**Bottom-center-right — control-group tabs.** Numbered tabs (1..0, with 0 representing group 10) showing unit-type icon + count for each bound group. Mirrors IGoP's exact treatment.

**Bottom-right — commander portrait.** Persistent identity element: the current commander's portrait, name, and lineage marker. Reinforces the named-commander framing that runs through the generational structure.

**Right sidebar — reserved.** IGoP's BUILD ASSIST slot has no Ouroboros equivalent at launch. The vertical strip on the right edge is kept as whitespace for now; future features (the chronicle-as-intelligence-feed line from `game_bible.md §Frontend — Fresh Start`, or event-reaction prompts) can occupy it without an HUD rework.

**Layer selector — new to Ouroboros, no IGoP equivalent.** A vertical 5-layer strip (right edge, above the commander portrait) showing layer indicators with the active layer highlighted. Click or Tab to switch layer focus. Matches Open Design Question #16's tier-1 active-layer treatment.

**In-world chrome** (all layered onto the world view, not HUD panels): thin HP bars above each unit; layer-color indicator rings beneath each unit per Open Design Question #16; selection rings at the base of selected units. Low visual weight throughout — the world is the primary visual focus, the HUD is the edges.

**Scope at launch.** Stage 8 ships all panels above. The event-ticker content is hardcoded to a small beat set (capture / loss / rout / objective threshold) — polished authored content is a Beyond-Stage-9 pass. There is no enemy composition readout (fog of war exists to be played through, not summarized).

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

### Information Warfare — Fog-of-War and Sensor Model

> **NEW SECTION (v3.00 / Q-mon8.1 v2, April 17, 2026).** This section consolidates the fog-of-war and sensor mechanics that were previously described inline across multiple sections (2.5D layers, environmental hazards, unit behavior AI, stat baselines) into a dedicated design reference, and flags the per-branch parameterization required by the branch system.

The tactical battlefield uses **fog of war** — the player sees only what their units can detect. Everything outside sensor coverage is hidden. The engine resolves combat identically regardless of what the player can see; fog is a player-information constraint, not an engine behavior modifier.

**Sensor model.** Each unit has a `sensor_radius` stat defining how far it can detect enemy units on its own layer. Cross-layer detection uses a separate `cross_layer_sensor_range` — typically shorter than same-layer sensor range, creating vertical blind spots that reward layer transitions for flanking and scouting. Both values are per-unit-type stats in the engine config.

**Sensor interference zones** (see Environmental Hazards above) create localized fog pockets by reducing sensor radius for units inside the zone and reducing detection range for units looking into it. These zones are positioned by the map generation system as gradient field properties.

**Layer visibility** is tied to sensor coverage. Full cross-layer sight means the player can see enemy units on adjacent layers within sensor range. Partial or absent cross-layer sight means units on other layers are invisible until they transition to the player's layer or enter a narrow cross-layer detection cone. The degree of cross-layer visibility is a config value.

**RE-OPEN FLAG (v3.00 / Q-mon8.1 v2).** Fog density, sensor range, cross-layer detection range, and any future ECM / counter-stealth mechanics become **per-era config values with branch-signature defaults**:

- **Branch 1 (sci-fi/future):** near-total awareness baseline. High sensor radius, free cross-layer sight, counter-stealth as an active cost rather than a passive limitation. The player sees almost everything — plan quality and execution speed are the differentiators, not information advantage.
- **Branch 2 (modern/recent history):** partial sensor asymmetry. Moderate sensor radius, radar/intel/recon all partial, ECM and scouts matter. Information management is a meaningful tactical layer alongside force positioning.
- **Branch 3 (ancient, post-launch):** heavy fog, scout-dependent. Low sensor radius, cross-layer detection largely absent, recon units (scouts) are the primary information-gathering tool. Ambush is a real and frequent tactical event. The player who scouts better wins.
- **Roman (standalone free tier):** Branch-3-adjacent fog and sensor values with reduced information-warfare depth for onboarding simplicity. Working assumption — specific values are a post-Stage 13 tuning decision.

The engine is branch-blind. All sensor and fog parameters are consumed uniformly from per-era config. No `if branch == ...` logic anywhere (Sacred Principle #3). **Implementation deferred to post-Stage 13.** The friends-ZIP ships Settled Reach with current sensor values unchanged. The parameterization work (moving sensor/fog values from global constants to per-era manifest entries) is post-ZIP infrastructure.

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

**Move orders are non-combat.** A unit executing a plain `move` command is in pure-displacement mode: it does not acquire targets, does not return fire, and does not stop if attacked. The player has explicitly chosen movement over engagement. This is what makes `move` distinct from `attack_move` — `attack_move` halts to engage enemies in range, `move` does not. Check 3 (auto-engage) is suppressed while a `move` order is active. If the player wants the unit to shoot back, they issue `attack_move` or `attack_target` instead.

**3. Is there an enemy in my engagement range?** If yes, the unit attacks the **nearest enemy**. No RPS-aware targeting, no priority lists — closest threat gets shot. If the unit is already engaged with a target that is still alive and in range, it continues engaging that target rather than switching (no target ping-ponging). If no enemy is in range, the unit holds position. This check is the default behavior for halted units and for units executing `attack_move`; it is suppressed under a plain `move` order (see check 2).

**Supply unit exception.** Supply units have no attack capability, so check 3 for them is simply "hold position." Their primary survival mechanism is check 1's retreat behavior — they flinch away from any damage source since they can never fight back.

**Return fire.** When a unit takes damage and has no current target and no active move order, it automatically targets the attacker. This gives idle units basic self-defense without player intervention. Return fire does **not** override an existing engagement — a unit that is already attacking a target (or waiting to re-acquire via the normal targeting cycle) ignores incoming damage for targeting purposes. Only genuinely idle units with no target respond to return fire. The player can always override with an explicit command.

#### Abilities — Player-Activated Only

All unit abilities are **manually activated by the player**. No auto-cast, no smart suggestions, no trigger conditions evaluated by the AI. The ability bar in the UI displays each unit's ability and its cooldown state. The player learns ability timing through gameplay experience.

**Ability education happens in the tutorial**, not during missions. The tutorial teaches what each unit type's ability does, when it's useful, and how to activate it. During missions, the only ability information displayed is the cooldown indicator on the UI bar — no contextual prompts, no "ability ready" notifications beyond the bar itself.

**The one exception** is the Interceptor's "Intercept" ability, which is defined in the ability spec as a passive proximity trigger (see "Abilities — One Per Unit" above). This is not a contradiction — Intercept is a passive that the player positions for, not an active ability the player clicks. The skill expression is where you park the Interceptor, not when you press a button.

#### Enemy Units — Same Loop, No Special Intelligence

Enemy units run the identical decision loop as player units. They acquire the nearest target, return fire, flinch from damage they can't engage, and use abilities on cooldown when minimally sensible conditions are met (enemies in range for offensive abilities, friendlies nearby for defensive abilities). Enemy ability usage is simple threshold-based — no sophisticated timing optimization.

What makes each mission archetype *feel* different from the enemy's side is not AI micro behavior but **mission setup**: where enemy units are placed, what scripted macro objectives they pursue (advance toward player position, hold defensive positions, hide and ambush, patrol routes), and what composition they have. The mission generator authors these macro-level behaviors per archetype at generation time. The unit-level AI is always the same — the variety comes from the tactical situation the setup creates.

**Enemy macro objectives are specified in the "Enemy Macro Behavior System" section below.** The macro behavior system issues commands to enemy unit groups using the same 4-command protocol as the player. The unit behavior system described here is the foundation that macro behavior builds on top of — the macro layer controls force-level intent, the unit layer executes commands through this decision loop.

#### Unit Facing

> **RESOLVED (April 16, 2026 — combat visual polish design session).** Unit facing uses a target-priority rule. The engine sets `facing_rad` per unit per tick; the renderer interpolates it for smooth visual rotation.

**Facing priority rule:**

1. **If the unit has an active target and is attacking:** `facing_rad` points at the target.
2. **If the unit is moving with no target** (plain `move` command, or `attack_move` with no enemy in range): `facing_rad` points in the movement direction.
3. **If the unit is stationary with no target:** `facing_rad` holds its last value.

**Rotation speed cap.** Transitions between facing directions use a rotation speed limit (config value per unit type — Strike rotates fastest, Siege slowest) so units visually turn rather than snapping. The renderer interpolates `facing_rad` between ticks using the same linear interpolation it uses for position.

**Design rationale.** Standard RTS model — units face what they're shooting, face where they're going otherwise. Retreating units face their pursuer (firing while backing away), which reads correctly for military behavior. A unit executing a plain `move` command (non-combat, suppresses auto-engage) faces its movement direction, not any attacker — mechanically correct since the unit is explicitly ignoring combat. The rotation speed cap is the key detail that makes facing feel smooth rather than mechanical.

---

### Tactical Simulation Architecture — SC2-Style Sim/Renderer Split

> **RESOLVED (v2.02).** The tactical combat system uses a strict separation between simulation and rendering, modeled on StarCraft 2's replay architecture. The simulation is the ground truth; the renderer is a visualization layer with zero gameplay logic.

**Layer 1 — Tactical Simulation Engine (Python, headless).** A deterministic, tick-based combat engine that owns all ground truth: unit positions on a continuous 2D coordinate space with vertical layers, HP, damage, ability cooldowns, movement, the unit behavior AI decision loop, objective tracking, and outcome band classification. Runs at a fixed tick rate (20 ticks/sec, config value). Every tick, it processes player commands from an input queue, runs the unit decision loop for all units, resolves damage, updates positions, and emits a state delta. Fully testable in Python with no visual dependencies — headless validation of hundreds of engagements per hour, automated balance testing, and deterministic replay reproduction.

**Layer 2 — Command Interface (the "replay feed").** A thin protocol carrying player commands into the simulation and state updates out. During live play, Godot captures player inputs and translates them into simulation commands. During replay, the same commands are read from a saved file. The simulation does not know or care which source commands come from.

**Layer 3 — Renderer (Godot).** Reads simulation state and draws it. Interpolates between tick states for smooth visuals (simulation at 20 ticks/sec, Godot at 60fps = 3 render frames per tick). Plays animations, particle effects, sound. Handles camera. Zero gameplay logic.

**Determinism guarantee.** Given the same initial state (map seed, unit positions/stats, objectives) and the same command stream (player inputs with tick numbers), the engine reproduces any engagement tick-for-tick, bit-identically. Replay files store only initial state + command stream; the engine re-derives everything else.

#### Attack Event Protocol

> **RESOLVED (April 16, 2026 — combat visual polish design session).** Hybrid model: normal auto-attacks are renderer-inferred; ability activations are engine-emitted events.

**Normal attacks — renderer-inferred.** The Godot renderer tracks each unit's attack interval and target from the state it already receives (target ID, `attack_interval`, `facing_rad`). When the interpolated time crosses an attack boundary, the renderer spawns the appropriate visual effect (projectile, beam, etc.) toward the target. The engine does not emit explicit "attack happened" events for normal attacks. This keeps the delta stream lean — no hundreds of attack events per tick in large battles.

**Ability activations — engine-emitted.** The engine emits an explicit event in the delta stream when an ability activates: `{"type": "ability", "unit_id": ..., "ability_id": ..., "target_pos": [...], ...}`. The renderer receives these events and plays the corresponding ability visual with perfect sync.

**Rationale.** Normal attacks happen at regular, predictable intervals where renderer inference is indistinguishable from perfect sync (inference error <50ms at 20 ticks/sec). Abilities are one-shot dramatic moments on 60–100 second cooldowns where timing precision matters — a Barrage's visual must land exactly when the damage hits, a Surge's glow must begin exactly when the speed burst starts. The hybrid gives precision where it matters and simplicity where it doesn't.

#### Unit Rendering — MultiMesh Batching

> **RESOLVED (April 20, 2026 — Metal driver deadlock investigation).** Unit rendering uses `MultiMeshInstance3D` batching, not individual `MeshInstance3D` nodes per unit. This is a hard architectural constraint, not an optimization toggle.

**Problem.** Individual MeshInstance3D nodes (one per unit model + layer ring + selection ring) cause ~1200 draw calls at 200v200. On macOS Metal, the driver accumulates per-draw GPU state until the render pipeline deadlocks — total main-thread freeze at ~10 seconds with 400 units, ~22 seconds with 100 units. OpenGL3 delays the freeze (~85 seconds) but does not eliminate it. The issue is structural: too many individual draw calls with unique material instances.

**Solution.** All units sharing the same mesh are batched into a single `MultiMeshInstance3D`. One draw call renders all instances of that mesh with different transforms. Grouping key: `(unit_type, tier, faction)` — each combination gets one batch. Squad units (Raider, Interceptor with `squad_count=4`) contribute 4 instances per unit to their batch.

**Draw call budget:** ~30 total (one per active batch + layer ring batches + selection rings) vs ~1200 with individual nodes. Scales to 1000+ units without GPU state growth.

**Per-instance variation.** MultiMesh instances support: transform (position/rotation/scale), instance color, and 4 floats of custom data. This is sufficient for unit rendering (position, layer height, faction tint). Per-instance effects beyond these parameters (death animations, ability glows, damage bloom) use an **escape hatch**: the affected unit temporarily breaks out of its MultiMesh batch into an individual node for the duration of the effect, then returns to the batch. At any given moment, only a handful of units need individual treatment.

**Selection rings.** Rendered as individual MeshInstance3D nodes spawned only for selected units. Selection is typically <20 units — negligible draw call cost.

**Layer rings.** Batched into one `MultiMeshInstance3D` per layer color (4 batches max). All layer-1 rings share one draw call regardless of unit count.

**Debugging.** MultiMesh batches are opaque — no per-unit entries in the scene tree. A uid→(batch_key, instance_index) mapping is maintained internally for debugging. The watchdog in `tactical_bridge.gd` tracks batch counts and instance totals.

---

### Damage Model

> **RESOLVED (v2.02).** Multiplicative category multipliers inspired by Age of Empires 3's tag-based system, adapted for the simpler 3-category RPS triangle. Flat HP pools.

**Damage formula:**

```
damage_per_attack = base_damage × category_multiplier
```

**Category multiplier matrix** (era-agnostic — uses Strike/Line/Siege categories):

|  | Target: Strike | Target: Line | Target: Siege |
|---|---|---|---|
| **Attacker: Strike** | 1.0× | 0.75× | 1.5× |
| **Attacker: Line** | 1.5× | 1.0× | 0.75× |
| **Attacker: Siege** | 0.75× | 1.5× | 1.0× |

The RPS is **soft**: 1.5× provides a meaningful advantage (~30–40% faster time-to-kill) without being a death sentence. Positioning, abilities, and numbers can overcome an unfavorable matchup. Stat differentiation within a category (e.g., the Bastion's large HP pool letting it survive Strike flanking where the Bombard cannot) is the primary tool for matchup nuance, but the matrix itself is also a tuning surface — specific cells can deviate from the canonical 1.0/0.75/1.5 pattern when the design needs it.

**Attack timing.** Each unit has `base_damage` (per attack) and `attack_interval` (seconds between attacks). DPS = base_damage / attack_interval.

**Range.** Constant damage within weapon range. No distance falloff.

**Area damage (Bombard).** Circle AoE centered on target position. Full damage to every enemy within `aoe_radius`. Damage cap: total AoE damage per attack ≤ `base_damage × aoe_damage_cap_multiplier` (default 4.0×).

**Cover & Vision.** Cover is a cluster of asteroid LOS-blockers, not a damage modifier. Visibility is determined by 3D ray-cylinder geometry: a ray from observer center to target center is blocked if any asteroid cylinder intersects the ray within its vertical extent. Each asteroid blocks line of sight at layer i if its height ≥ LAYER_Z_FLOORS[i] — a tiny asteroid blocks only the lowest layer; a tall asteroid blocks all layers it exceeds. There is no fire-reveal — a defender who fires from behind asteroid cover remains hidden to outside observers; the attack lands but its origin is not exposed. Cover does not reduce damage and does not block movement; once an attacker can see a target, full damage applies. Era-agnostic.

**Elevation damage bonus.** Config flag `ELEVATION_DAMAGE_BONUS_ENABLED`. When enabled (land-based eras), higher elevation → bonus damage per tier. **Disabled for space era** — elevation affects sensor coverage only. The engine computes elevation difference always; the flag controls whether it modifies damage.

---

### Stat Philosophy — Long Engagements with Category-Specific Rhythm

> **RESOLVED (v2.02, updated v2.03, rebalance applied v2.07).** Engagement pacing follows an A+C hybrid: all fights are long enough for positioning, abilities, and retreat decisions to matter, but different categories fight at different tempos.
>
> **RE-OPEN FLAG (v3.00 / Q-mon8.1 v2, April 17, 2026).** The pacing targets below become **per-branch targets** rather than global. Branch 1 (sci-fi/future) → 30–45s short-decisive engagements; Branch 2 (modern/recent history) → near current 1–2min; Branch 3 (ancient, post-launch) → 2min+ attritional grind. Each era within a branch can vary within the branch's target range. The design principle ("long enough for positioning, abilities, and retreat decisions to matter") holds universally — Branch 1's shorter engagements compress the decision window rather than eliminating it. The current global targets become the Branch 2 / moderate-tempo defaults. **Settled Reach retcon:** Settled Reach's current slow/high-HP/methodical identity inverts under Branch 1 fast tempo — HP values likely drop, engagement floor shifts from 45s toward 20–30s. This is a substantial rebalance deferred to post-Stage 13 implementation. The friends-ZIP ships with current Settled Reach values unchanged.

**Pacing targets (current — global, pending per-branch split):**
- Minimum brawl (force-on-force, no tactics): 45 seconds
- Tactical engagement (positioning, abilities, retreat and re-engage): ~2 minutes
- Large battles (100+ per side): well over 2 minutes
- Mirror 50v50 (balanced composition): 150–200 seconds

**Stat rebalance (v2.07):** The stats originally specified for Tier 2 produced engagements significantly shorter than these targets, and the rebalance was tracked as Open Design Question #14. The rebalance has been applied. HP and damage values were adjusted together to lengthen engagements. The rebalance is **non-uniform across unit types** — not a flat multiplier — because the original ratios produced degenerate matchups at the new durations (e.g., Strike's HP pool vs Siege burst). Specific HP and damage values are implementation parameters and live in the engine config, not in the bible. The design contract the rebalance preserves is: engagements hit the pacing targets above, the soft RPS triangle still produces the expected winners, and positioning/abilities remain decisive within a matchup.

HP pools create tempo differences. Strike has the lowest HP (fastest fights within a category). Line has moderate HP (baseline). Siege has the highest HP (slowest). DPS is moderate across all categories; HP is the primary differentiator. In large battles, flanks resolve first (Strike), the center grinds next (Line + Warden), and Siege duels continue longest — creating layered attention-management gameplay.

The longer engagement floor (45 seconds minimum) serves a critical design purpose: it gives the player time to read the battle, recognize when they're losing, and execute a retreat. Retreat is a real tactical option, not a panic button — the player has time to recognize "this fight isn't going my way, the enemy has more units and is decreasing my HP faster" and pull back to regroup. This supports the 30–60 minute mission pacing and the "deliberate, not frantic" philosophy.

---

### Unit Stat Baselines — Tier 2

> **RESOLVED (v2.02, values moved to config v2.07).** The bible does not carry the discrete Tier 2 stat values. Hand-designed baseline stats (HP, base damage, attack interval, attack range, speed, sensor radius, layer transition time, AoE radius per unit type) live in the engine config as the single source of truth, so tuning passes do not require bible edits. Tier 1 and Tier 3 are config-level variants of the same profiles. AI-generated per-civilization stat variation is **on hold** — the engine supports it, the generation pipeline is deferred.
>
> **RE-OPEN FLAG (v3.00 / Q-mon8.1 v2, April 17, 2026).** Global HP multipliers and damage values become **per-era tunable** within branch signature ranges. The engine config already holds these values (per v2.07 move); the change is that each era's manifest provides its own stat profile rather than all eras sharing one. Branch 1 eras configure lower HP (faster kills, higher lethality); Branch 2 near current values; Branch 3 higher HP (attritional). The 6 base unit types and the soft RPS triangle are universal — what varies is the absolute scale of HP and damage, which controls engagement tempo. **Settled Reach specifically:** HP is retconned downward for Branch 1 fast-burst compatibility. The v2.07 rebalance's non-uniform HP adjustments remain valid as ratios between unit types; the absolute values shift downward. **Implementation deferred to post-Stage 13.**

The design constraints the stat table must satisfy:

- Each unit type's category assignment (Strike / Line / Siege) is fixed and matches the role description above.
- Relative mobility is preserved: Strike fastest, Line middle, Siege slowest. Speed spread is wide by design — every unit always moves at its own native speed (no speed matching, no group-move), so mixed forces arrive strung out by speed tier. Maintaining combined-arms cohesion is a player skill, not an engine guarantee.
- Relative durability is preserved: Bastion is the highest-HP unit in the game by a wide margin; Strike units have the lowest HP pools.
- Sensor radius roughly tracks category (Strike units see further than Siege units) — the screen role depends on this.
- Bombard is the only AoE unit in the base roster.

"wu" = world units. See canvas sizing in `bible_world.md`.

---

### Command Vocabulary

> **RESOLVED (v2.02, updated v2.03, clarified v2.07).** Four commands. No patrol, no follow, no hold position, no stop, no group-move, no speed matching.

- **`move`** — move to position. **Pure displacement, non-combat.** The unit does not acquire targets, does not return fire, and does not stop if attacked along the way. This is the player explicitly choosing movement over engagement — a retreat, a reposition, a sprint through a contested zone. If the player wants the unit to fight on the way, they use `attack_move` instead.
- **`attack_move`** — move to position, **stopping to engage any enemy that enters weapon range**. The unit halts at the point of first engagement, fires at the nearest in-range enemy, and resumes movement toward the commanded point when the target dies or leaves range. Attack-move uses an **engagement leash**: when the unit first acquires a target, it sets an anchor at its current position; if the engaged target moves beyond a bounded distance from that anchor, the unit drops the target and resumes movement rather than chasing indefinitely. The leash prevents an attack-moving force from peeling apart to chase a fleeing target far from its commanded path.
- **`attack_target`** — attack a specific enemy unit.
- **`activate_ability`** — trigger the unit's active ability (toggle for Brace).

All movement commands accept a single unit or a selection. When issued to a selection, the command is applied to each unit independently — every unit travels at its own speed. There is no cohesion enforcement, no speed matching to the slowest unit, no group-move primitive. A mixed force commanded to a point will arrive strung out by speed tier: Strike first, Line middle, Siege last. This is intentional — combined-arms cohesion is the player's responsibility, achieved through command timing (sending Siege ahead, sending Strike later) rather than an engine-enforced group pace. The player's tools for keeping a force together are smaller selections, staggered commands, and waypointing — not a speed-matched group move.

**Formation-preserving group move.** When a multi-unit selection receives a move or attack_move command, the engine computes each unit's offset from the group centroid and assigns per-unit destination slots that preserve the group's current shape at the target point. This keeps tight formations intact during repositioning — units don't collapse into a ball at the click point. A move group is registered and terminated when the group's centroid arrives at the destination or all units have reached their slots. Formation offsets are computed once at command time and are not updated during movement.

**Magic box scatter detection.** If any unit in the selection is farther than `MAGIC_BOX_SPREAD_RADIUS` (config value, default 450wu) from the group centroid at command time, formation offsets are abandoned entirely — all units receive the raw click point as their destination and converge. This prevents scattered units from maintaining absurd offsets (e.g., two units 2000wu apart staying 2000wu apart at the destination). The threshold is a one-time check at command time, not a per-tick evaluation. Groups that fail the magic box check are still registered as move groups for centroid-arrival termination; they just have zero offsets.

Commands are recorded with tick numbers for replay. The engine processes all commands for the current tick before advancing state.

### Squad Mechanics — Visual Only

> **RESOLVED (v2.02).** Strike units (Raider, Interceptor) are "commanded as squads" — this is purely visual. In the simulation, each squad is one entity with one HP pool, one position, one set of stats. Godot renders it as 3–5 small ships in formation. The simulation does not track individual squad members.

---

### Supply and Non-Combat Units

> **RESOLVED (v2.02).** Supply units, evacuation convoys, and non-combat assets are entities in the tactical simulation with HP but no attack capability. Their decision loop skips auto-engage (check 3). Primary survival: flinch retreat (check 1). They are objective targets for evacuation and escort missions.

---

### Pathfinding and Movement — Hierarchical A* with Directional Probe Steering

> **RESOLVED (v2.02, updated v2.06, rewritten v2.07).** Two-level movement: coarse A* pathfinding for route planning, local steering for collision-free movement between waypoints. The v2.06 attempt to use ORCA/RVO for fine-layer steering was reverted — reciprocal velocity obstacles produced unstable formations at our unit counts and could not express the "immovable engaged unit" behavior the combat design requires. The current fine-layer system is a custom directional-probe steering model paired with a deterministic hard-collision pass. Friendly line-of-fire blocking was tested and removed — ranged units fire through friendly units, and formation geometry emerges from physical collision, not shot occlusion.

**Coarse level:** A* on a precomputed navmesh per layer, generated from the map's `obstacle_density` gradient. Path caching for shared destinations.

**Fine level — directional probe steering.** Each moving unit seeks toward its next waypoint. Before committing to the straight-ahead direction, it probes a short distance along its heading to check whether an ally is in the way. If the path is clear, the unit moves straight — no steering force is applied. If the path is blocked by an ally, the unit sweeps a small set of alternate angles to either side of its heading and takes the first clear direction. This produces deliberate, legible lateral flow around obstacles without the jitter of a continuously-accumulated separation vector.

**Detour commitment.** When a unit picks a deflected angle, it commits to traveling a bounded distance in that direction before re-evaluating. Commitment prevents the per-tick oscillation failure mode where a unit sees two symmetric probe results, alternates between them each tick, and makes no lateral progress. Commitment distance is a tuning value.

**Hard collision (deterministic push-apart).** After each movement tick, a collision-resolution pass iterates over same-layer unit pairs. Any pair within two collision radii is separated along the vector between them until no longer overlapping. The pass runs multiple iterations per tick (tuning value) to resolve chain overlaps. Both friendly and enemy units physically collide — a unit cannot walk through another unit of either faction.

**Stationary units are immovable.** A unit that is not moving — because it has no move target, or because it is held in place by engagement (see `attack_move` in the command vocabulary) — absorbs **zero** push from the collision pass. The moving unit on the other side of the overlap takes the full displacement. This is the mechanical backbone of the combat design: a unit that has committed to fire cannot be shunted out of firing position by allies walking into it. Concave formations emerge from this rule — the front rank halts on engagement and becomes immovable, so later arrivals have to flow around rather than through it, and they deflect via the probe steering into the next open firing slot.

**Speed-dependent positioning.** Because probing and detour commitment are per-unit, faster units resolve their lateral movement around blockers sooner than slower units. A Strike wing approaching an engaged Line force flows around the Line's flanks faster than a mirrored Line force would — the positioning advantage that Strike needs to exploit formation breaks is produced by the speed differential through the same steering system, not by special-case rules.

**No friendly line-of-fire blocking.** Ranged units fire through friendly units. There is no friendly unit occlusion check on attacks. Formation advantages come from collision-driven concave geometry (immovable front rank forcing later units into flanking positions), not from shot blocking. Terrain obstacles still block line of sight — units cannot fire through navmesh obstacles. Asteroid clusters are additional line-of-sight blockers (per `bible_world.md` `cover_density` and the Cover & Vision section above); they remain distinct from obstacles in that they do not block movement.

**Determinism.** Probe sweep order, detour commitment, and collision resolution all use deterministic tie-breaking (fixed probe angle order; lower unit ID pushes in a canonical direction on zero-distance overlap). Given identical initial state and command stream, the engine reproduces movement tick-for-tick.

**Layer transitions.** Unit enters transition state lasting `layer_transition_time` ticks (Strike fastest, Siege slowest). During transition, unit cannot attack or be targeted by same-layer units.

**Gradient obstacle avoidance scope.** In addition to probe steering (unit-to-unit), `update_movement` samples `obstacle_density` ahead of the unit and applies a repulsion force opposing movement when density > 0.3. This fires only for **direct-move units** (no A*-computed waypoints). Units following A*-computed waypoints are exempt: A* already routes them around blocked cells, and applying avoidance on top cancels the waypoint-seek direction when the probe enters a wall boundary cell, freezing the unit.

**Open design question — soft terrain speed effects.** The gradient avoidance force is normalized after application, so it only has a visible effect at density = 1.0 (it freezes the unit). At lower densities the force is normalized away entirely — it does not slow units down. If soft terrain (debris, heavy cover, partial obstruction) should impede movement speed without breaking A* navigation, the right mechanism is a **speed multiplier** sampled from the terrain gradient, applied to `move_dist` for all units including waypoint-following ones. That feature is not built; this note records where it would go.

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

---

### Enemy Macro Behavior System

> **RESOLVED (v2.03).** The enemy macro behavior system sits on top of the Unit Behavior AI (the per-unit decision loop) and the tactical engine's command protocol. It controls *what enemy forces do at the force level* — where they go, what they're trying to accomplish, and how they respond to player actions. The system is universal across all mission archetypes; differentiation comes from how the behavior script is authored per archetype, not from different AI systems.

#### Architecture — Shared Behavior Scripts with Reactive Hooks

Each mission instance includes a **behavior script** that defines the enemy's plan. The script is a state machine composed from a shared vocabulary of behaviors. Each enemy force group (a named set of unit IDs) runs its own script instance. The script moves through states based on transition conditions. Layered on top of the state machine are **reactive hooks** — condition → action pairs that fire when the player does something the script's base flow didn't anticipate. The script is the skeleton (authored pacing); the hooks are the muscles (authored reactivity).

The behavior script issues Stage 6 commands (`move`, `attack_move`, `attack_target`, `activate_ability`) to groups of enemy units. Individual units then execute those commands through their existing decision loop. The macro layer re-evaluates its state and issues updated commands at a regular cadence (config value, targeting every 2 seconds). Between evaluations, units rely on their existing auto-engage and flinch behaviors.

**This replaces the earlier roadmap concept of "per-archetype enemy scripted behaviors."** The macro behavior system is a single shared system. Each archetype authors a script using the shared vocabulary — the archetype provides the *content* (which states, which transitions, which hooks), the system provides the *infrastructure* (how states execute, how transitions evaluate, how hooks fire). Adding a new archetype requires authoring a new script, not writing new AI code.

#### Behavior Vocabulary — 5 Base Behaviors + 3 Modifiers

The behavior vocabulary is **compositional**: 5 base behaviors combined with 3 modifiers that adjust execution parameters. A script state is specified as a `behavior_modifier` pair (e.g., `advance_cautious`, `defend_aggressive`). The modifier adjusts speed multipliers, engagement thresholds, spacing, and break-off conditions — not the behavior's fundamental logic.

**Base behaviors:**

- **`advance`** — move the force group toward a target position, engaging enemies along the way. The group issues `attack_move` commands toward the target. The target can be a map position, a spine node, or a unit group.
- **`defend`** — hold a position and engage enemies that enter range. The group holds at its assigned position. Units auto-engage per the existing decision loop. The force does not pursue enemies that retreat out of range.
- **`patrol`** — move between a sequence of waypoints, engaging enemies on contact. The group issues `move` commands cycling through waypoints. On contact, units auto-engage. After the engagement resolves, the group resumes patrol.
- **`ambush`** — hold at a hidden position (ideally in a sensor interference zone or behind cover). When enemy units enter a trigger zone (config radius around the ambush position), the force activates — transitioning to `advance_aggressive` toward the triggering units. The ambush is a one-shot state: once triggered, it doesn't reset.
- **`retreat`** — move the force group away from the engagement toward a designated fallback position. The group issues `move` commands (not `attack_move`) toward the fallback point. Units still auto-engage if enemies pursue into range, but the group prioritizes disengagement over fighting.

**Modifiers:**

- **`cautious`** — slower movement speed (config multiplier, e.g., 0.6×), wider unit spacing, the force breaks off and transitions to `retreat` or `defend` on first significant contact (contact threshold: config percentage of force HP lost). Approximates probing behavior when combined with `advance`.
- **`aggressive`** — faster movement speed (config multiplier, e.g., 1.2×), tighter unit spacing, the force presses through losses and does not break off unless a retreat transition fires. The committed posture.
- **`phased`** — the force advances in echelons. The group is internally divided into 2–3 sub-groups. The first sub-group advances while the rest hold. When the first engages or reaches its waypoint, the next sub-group advances. Creates a staggered arrival that prevents the entire force from being committed simultaneously.

The combinatorial space (5 behaviors × 3 modifiers = 15 distinct behavior flavors) provides enough variety to compose diverse mission scripts from a small code base. Not all combinations are used — `ambush_phased` and `retreat_cautious` are unlikely to appear in practice — but the system supports them without special cases.

#### Behavior Transitions — Timer + Threshold + Noise

Each state in the behavior script defines its transition conditions. Transitions fire from two independent systems: **thresholds** (reactive to tactical state) and **timers** (pacing-driven). Both are subject to **noise** — random offsets rolled at mission start that persist for the mission's duration.

**Threshold transitions.** Each transition has a condition evaluated against current tactical state: "force HP below X% of starting," "player units within Y wu of objective," "force has advanced past map position Z." The threshold value has a noise range (e.g., 30% ± 10%), rolled once at mission start. When the condition is met against the noised threshold, the transition fires.

**Timer transitions.** Each state has a duration range (e.g., 60–90 seconds). A specific duration is rolled from the range at mission start. When the timer expires, the transition fires regardless of tactical state. Timers ensure the mission keeps moving even if the player is passive — the bible's "static = broken" principle enforced at the tactical level.

**Conflict resolution.** When both a timer and a threshold fire on the same evaluation tick, the threshold transition takes priority — reacting to the player is always more important than following the schedule. Exception: if the timer transition leads to a more aggressive state (escalation) while the threshold leads to retreat, retreat wins. The precedence rule is: **survival transitions override all, then threshold transitions, then timer transitions.**

**Noise philosophy.** The noise offsets use the same pattern as the simulation's event threshold noise (rolled once, persists for the duration, applied as an offset to a base value). This means the same mission archetype on the same map plays differently each time — the enemy's decision points shift by 10–20%, creating the "genuine stochasticity" the bible demands without producing degenerate behavior.

#### Multi-Force Coordination — Independent with Trigger Bus

When a mission involves multiple enemy force groups (Multi-Front Defense, Containment, etc.), each force runs its own behavior script instance independently. Coordination uses two mechanisms:

**Timer-staggered synchronization.** The archetype's script authors the relative timing of each force's actions: "Force A begins `advance_cautious` at T+0, Force B at T+30 sec, Force C at T+60 sec." Timer noise means the actual timing varies per run (each force's timer is rolled independently). This creates the appearance of coordinated multi-vector pressure through authored timing.

**Shared trigger bus for key moments.** A lightweight shared state — a dictionary of named boolean flags — exists for the mission. When something significant happens to one force, it sets a flag on the bus: `force_a_routed`, `objective_alpha_contested`, `player_force_split`. Other forces' scripts include reactive hooks that read these flags: "if `force_a_routed`, transition from `advance_cautious` to `advance_aggressive`." Forces don't communicate directly — they react to shared state.

The trigger bus fires rarely — typically 2–5 times per mission. Most of the time, forces operate independently and that's fine. The trigger moments create memorable beats where the enemy visibly adapts ("they noticed I destroyed the northern force and now the southern force is pushing harder"). Each archetype defines its trigger vocabulary as part of its script — simple archetypes may have 1–2 triggers, complex multi-front archetypes may have 4–5.

#### Pacing and Reinforcement

**In-mission pacing** comes primarily from the behavior script's timer-driven state transitions (ensuring the enemy escalates over time) and the tactical reinforcement system (ensuring both sides receive replacement units). The combination creates a natural pacing arc: early mission is probing and positioning, mid-mission is committed engagement, late mission is escalation with depleted forces supplemented by reinforcements.

**External reinforcement events** are rare authored complications — approximately 1 in 10–20 missions. When an external reinforcement event fires, additional enemy forces arrive from map-edge spawn points during the mission. This is pre-determined at mission generation (not reactive to player performance) and foreshadowed in the mission briefing: the player knows reinforcements may arrive, knows roughly which direction, but not exactly when. External reinforcement arrival is a trigger bus event that other forces can react to. The rarity ensures reinforcement events feel like memorable disruptions, not routine occurrences.

Most reinforcements come from the **tactical reinforcement system** (see below) — both the player and enemy produce replacement units from local military infrastructure throughout the mission. External reinforcement events are a separate, much rarer system layered on top.

#### Relationship to Unit Behavior AI

The macro behavior system and the Unit Behavior AI (per-unit decision loop) are cleanly separated:

- The **macro layer** decides force-level intent: where a group should go, what posture to adopt, when to transition between states. It issues commands to unit groups.
- The **unit layer** executes those commands through the existing priority-ordered decision loop: flinch → command → auto-engage. The unit layer does not know about behavior states, transitions, or the trigger bus.
- The **interface** between them is the Stage 6 command protocol. The macro layer issues the same 4 commands the player does. No special enemy-only commands exist. This means enemy macro behavior is fully replayable — the replay file captures enemy commands alongside player commands.

---

### Tactical Reinforcement System

> **RESOLVED (v2.03).** In-mission unit production through local military infrastructure. The player's starting force is roughly half of what they'll field over a full mission. The other half comes from reinforcement structures that both sides capture, hold, and produce units from.
>
> **RE-OPEN FLAG (v3.00 / Q-mon8.1 v2, April 17, 2026).** Under the branch system, reinforcement rate, structure density, structure placement rule, structure cost, and production time become **per-era config values** rather than global constants. The engine continues to consume these parameters uniformly — no branch-aware logic (Sacred Principle #3). Branch-level variation is achieved through the era manifest: Branch 1 eras configure rapid replacement / high structure density; Branch 2 configures moderate industrial replacement; Branch 3 (post-launch) configures slow replacement where casualties matter. The current hardcoded values become the Settled Reach defaults. **Implementation deferred to post-Stage 13** — the friends-ZIP ships a single era, so parameterization has no immediate effect. The design contract is unchanged; only the constants move from global to per-era.

#### Narrative Frame

The player is a commander operating in a region that has its own military infrastructure — garrison posts, militia stations, forward operating bases. These structures represent the local population's military capacity. Capturing and holding them gives the commander access to local reinforcements — militia, reserves, garrison troops rallied to the cause. This is not base-building and not economy management. The infrastructure already exists in the region. The commander leverages what's there.

The enemy has access to the same system. Enemy-held structures produce enemy reinforcements. Structures in contested areas are strategic assets — capturing one denies the enemy production while increasing your own.

#### Structure Properties

Reinforcement structures are **fixed-placement entities on the tactical map**, placed by the map generation system as a spine node type (alongside objectives, chokepoints, vantage points, etc.). Each structure has:

- **Owner** — player faction, enemy faction, or neutral at mission start. Ownership can change through capture.
- **HP** — structures can be destroyed. A destroyed structure is gone for the rest of the mission (no rebuilding). Destruction is a deliberate strategic choice: the player (or enemy) can destroy a structure they can't hold to deny it to the other side. Structure HP is high enough that destruction requires a committed attack, not accidental splash damage.
- **Capture mechanic** — move friendly units near the structure with no enemy units in the capture zone and hold for a duration (config value). The structure flips ownership. Same mechanic as zone-based objectives.
- **Production rate** — each structure produces one reinforcement unit at a fixed interval (config value, targeting roughly one unit per 45–60 seconds per structure). The owning side chooses which unit type is produced. Production is automatic and continuous while the structure is held.

#### Simulation-Driven Capacity

The **total reinforcement capacity** across all structures on a mission map is derived from the mission region's military field value in the simulation. A region with high military strength has more productive local infrastructure (more structures, or faster production, or both — the specific mapping is a tuning question). A region with depleted military has fewer and slower structures.

This creates the direct link between strategic simulation and tactical experience that the bible demands: commanding forces in a thriving, well-militarized region means abundant local reinforcements. Commanding forces in a depleted frontier means scraping together whatever the local garrison can spare. The player feels the simulation's state through the tactical experience without needing to read numbers.

The chronicle briefing communicates the expected reinforcement level as part of the mission context: "Local military infrastructure is extensive — expect steady reinforcement from regional garrisons" vs. "The region's military capacity has been gutted — local reinforcements will be sparse." In rare situations where intelligence is incomplete, the briefing may understate or omit reinforcement information, creating surprise (positive or negative) during the mission.

#### Player and Enemy Production

**Player production.** The player selects which unit type each structure produces. This is a simple UI interaction — click a held structure, pick from the 6 unit types. The player can change production type at any time. Newly produced units spawn at the structure's location and await orders. The player's freedom to produce any unit type creates composition flexibility: a player who lost all their Strike units can shift production to replace them, or double down on Line if the situation calls for it.

**Enemy production.** The enemy AI uses a **target ratio** — a desired composition expressed as percentages across the 6 unit types (e.g., 40% Line, 25% Strike, 20% Siege, 15% support). The ratio is defined per archetype's behavior script. Each production cycle, the AI compares its current force composition to the target ratio and produces the unit type that is most underrepresented. This is simpler than the player's free choice but produces coherent force compositions that align with the archetype's tactical approach. The AI does not deviate from its ratio — it always produces toward the target composition. This creates a predictable (but not exploitable) production pattern: the player can observe what the enemy is building and adapt.

#### Open Tuning Questions

The following tuning values are open and will be resolved during Stage 7 implementation:

- **Production rate per structure** — units per minute. Too fast and the mission becomes a production race; too slow and structures don't matter enough.
- **Structure count per map size** — how many structures per canvas size category. Probably 2–4 for small, 3–6 for medium, 4–8 for large.
- **Region military → capacity mapping** — the formula that converts the simulation's military field value to total reinforcement throughput. Linear? Stepped? Floor and ceiling values?
- **Unit cost model** — flat cost per unit regardless of type? Scaled by power rating? Per-type costs? This determines whether the player is incentivized to produce cheap units or expensive ones.
- **Baseline trickle** — should there be a minimum reinforcement rate even with zero structures held, representing the civilization's supply line to the mission area? If yes, how slow?
- **Structure placement strategy per archetype** — see Open Design Question #12 in the hub.

See Open Design Questions #12, #13, and #14 in the hub for the full set of unresolved reinforcement and rebalance questions.

---

### Combat Visuals

> **RESOLVED (April 16, 2026 — combat visual polish design session).** This section covers the visual presentation of combat: what attacks look like, how impacts read, and how units die. All systems are era-agnostic — the engine provides abstract events and state, the per-era manifest maps them to visual configs. The aesthetic reference for the Settled Reach is the opening battle of Star Wars: Revenge of the Sith — slow, massive, weighty. Everything conveys mass and scale. Nothing snaps or pops.

#### Attack Visual Categories

Every unit attack visual falls into one of four rendering categories. The era manifest maps each unit type to a category and provides era-specific visual assets.

**1. Projectile** — a single object travels from attacker to target. The workhorse for most unit types. See "Projectile Rendering" below for construction.

**2. Volley** — multiple projectiles fired in a staggered burst. Same rendering behavior as projectile but N objects launched with slight timing and angle offsets. Creates visual density for heavy-hitter and sustained-fire units. Volley count and stagger timing are per-unit-type config values in the era manifest.

**3. Beam** — an instant line connecting attacker to target for a brief duration. Glow, shimmer, thickness variation over the beam's lifetime. Suited for continuous-fire or support/healing visual registers.

**4. Area pulse** — an expanding ring or sphere centered on a position. No travel — blooms outward from the source. Natural fit for Rally (heal pulse), Fortify (defensive zone), and AoE ability impacts.

**Era-agnostic design.** The four categories are engine-level rendering behaviors, not era-specific content. Each era's manifest maps its 6 unit types to categories and provides the visual assets (meshes, particle materials, colors, timing values). Adding a new era requires filling in the manifest, not writing new rendering code.

#### Projectile Rendering

Each projectile (whether fired singly or as part of a volley) consists of two layers:

**Mesh head** — a small 3D mesh providing shape identity. Era-specific: a tiny glowing sphere for Settled Reach, an arrow for Roman, a tracer round for 1980s. The mesh is what makes eras visually distinct at close zoom.

**GPU particle trail** — a `GPUParticles3D` emitter attached to the mesh head, emitting particles along the travel path. Provides atmosphere, trailing glow, and visual continuity with the game's particle-driven aesthetic (the main menu's `world_view_structure.tscn` particle galaxy). The trail is what makes projectiles feel alive.

**Impact burst** — a brief GPU particle burst at the target position on projectile arrival. Separate from the hit reaction on the target unit (see "Impact Feedback" below).

**LOD tiers for performance at scale (200v200):**

- **Close/medium zoom:** full mesh + particle trail.
- **Far zoom:** mesh replaced by billboard sprite, particle trail continues.
- **Very far zoom / frame budget pressure:** billboard only, no trail particles.
- **Extreme density:** projectiles beyond a count threshold are culled entirely. Damage still applies — this is renderer-only.

**Era manifest fields per unit type:** `projectile_mesh_scene`, `trail_particle_material`, `impact_particle_scene`, `visual_travel_speed`, `projectile_scale`, `volley_count` (for volley category), `volley_stagger_sec`. All values are visual-only — they do not affect gameplay. Damage is resolved by the engine independently of visual travel time.

**Settled Reach identity.** The mesh head is a tiny glowing sphere similar to the main menu's particle objects, creating visual continuity between the menu atmosphere and tactical combat. Trail is a warm-toned energy ribbon. Impact is a small radial flash.

#### Ability Visual Treatment

Abilities use their unit's normal attack visual category as a base with enhanced parameters (more projectiles, bigger trails, brighter emission). On top of the enhanced base, a shared library of **overlay effects** creates the visual step-up that says "ability in progress."

**Overlay library — three era-agnostic effect types:**

**1. Ring telegraph** — an expanding ground ring showing the affected area. Used for Barrage (danger zone), Fortify (defensive zone), Rally (heal radius). Color-coded: hostile/offensive abilities use warm/red tones, friendly/defensive abilities use cool/blue tones. Ring persists for the ability's duration, then fades.

**2. Unit glow/aura** — the casting unit receives a brief full-body emission boost via a shader uniform toggle. Used for Surge (speed burst glow), Brace (defensive stance glow). Color matches the ability's hostile/friendly register. Duration matches the ability's active window.

**3. Screen-space distortion** — a subtle post-process ripple centered on the ability's effect point. Reserved for the most dramatic moments only (Barrage impact, large-scale Rally). Brief duration (0.3–0.5s). Tunable intensity — atmospheric, not nauseating.

**Ability-to-overlay mapping:**

- **Raider — Surge:** projectile (enhanced) + unit glow.
- **Interceptor — Intercept:** projectile (enhanced) + unit glow (on trigger).
- **Vanguard — Brace:** no attack change, unit glow only.
- **Warden — Rally:** area pulse + ring telegraph + screen-space distortion.
- **Bombard — Barrage:** volley (heavy enhanced) + ring telegraph + screen-space distortion.
- **Bastion — Fortify:** no attack change, ring telegraph (persistent for duration).

**Era-agnostic design.** The three overlay types are engine-level rendering behaviors. Ring color, glow intensity, and distortion strength are config values per era. Eras do not author custom overlay assets — the overlays are abstract visual communication tools that work identically regardless of theme.

#### Impact Feedback

> **Aesthetic reference:** Star Wars: Revenge of the Sith opening battle — turbolaser bolts connecting with capital ships, the glow spreading across the hull, debris drifting away slowly. Not twitchy arcade impacts.

When an attack hits a target, two layers of visual feedback play:

**1. Impact particle burst.** GPU particles spawn at the target's position and drift outward slowly over 0.5–1.0 seconds with gentle deceleration. Small debris-like particles that tumble and fade — energy dissipation, not explosion. Color matches the attacker's projectile trail color. Burst scale varies with damage dealt (Bombard hits produce larger bursts than Raider hits).

**2. Hit reaction — slow emission bloom.** The target unit's material receives a slow additive emission spike: 0.3–0.5 second rise, 0.3 second fade. A warm glow that spreads across the model's surface and dissipates. This is NOT a snappy white-frame flash — the cinematic register demands everything feel massive and deliberate. The bloom is the primary feedback that tells the player "this unit is taking damage" during a battlefield scan.

**Explicitly excluded at this stage:**

- **Micro-jitter / position displacement.** At the cinematic scale and pacing, jitter reads as a rendering bug. Units absorb hits stoically. The bloom is the feedback.
- **Progressive damage state visuals** (scorch marks, hull breaches at HP thresholds). Deferred to per-era polish passes. The system architecture supports adding damage-state shader overlays later without redesign.

**Timing is per-era config.** The Settled Reach uses the cinematic register (slow blooms, drifting particles). Faster-paced eras (1980s tank combat) can tighten impact timings through the era manifest. The rendering system is the same; the feel varies per era.

#### Unit Destruction Visuals

When a unit reaches 0 HP, the engine removes it from gameplay state. The renderer plays a destruction sequence and manages the resulting wreckage as a renderer-only visual artifact with no gameplay significance.

**Destruction sequence (2–3 seconds):**

1. **Death bloom** (0.5s) — the unit flares with a slow emission burst, brighter than any hit flash. The unmistakable "moment of death."
2. **Damage onset** — persistent damage particle emitters activate on the model: fire, sparks, venting atmosphere (era-specific particle materials from the manifest). These were not present during combat — they signal the unit is now dead.
3. **Drift begins** — the unit begins drifting in a direction biased by its last movement heading (so the drift feels physical, not arbitrary). Slow, decelerating. The unit no longer responds to any commands or collision. It becomes a battlefield artifact.
4. **Darkening** — the unit's material gradually shifts toward a dark, desaturated version of its faction color over 3–5 seconds, signaling its transition from active unit to debris.

**Wreckage lifecycle — LOD demotion ladder:**

- **Fresh wreck (0–5s):** full 3D model, damage particles (fire/sparks), slow drift. Moderate render cost.
- **Cooling wreck (5–15s):** particles reduced to a single faint emitter (smoke). Material fully darkened. Low cost.
- **Cold wreck (15s+):** particles off entirely. Dark, drifting mesh only. Near-zero cost.

Cold wrecks persist as dark debris drifting through the battlefield until they leave the visible area plus a buffer distance, then despawn.

**Performance safety — hybrid cull.** When the frame budget is tight, cold wrecks despawn **farthest from camera center first**. Camera-center distance is the metric, not battle-center distance — if the player is zoomed into one flank, cold wrecks on the opposite flank are culled first since no one is looking at them. Fresh and cooling wrecks are never culled (their destruction sequences are active visual events the player may be watching).

**Strike squads.** Individual squad members play abbreviated destruction sequences: bloom + fade over 1.0 second, staggered across members. No drift phase — small ships flare and go dark. A squad wipe reads as a cascade of small fades, not a series of capital-ship death events.

**Fragment breakup (deferred).** Model splitting into 2–4 tumbling fragment meshes is a future per-era polish option. The destruction system architecture supports inserting a fragment phase between bloom and drift without redesign. Not in scope for the friends-ZIP build.

