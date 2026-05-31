# Missions

Spoke. Authoritative for mission generation, archetypes, objectives, difficulty, outcome band classification, briefings. If this conflicts with `game_bible.md`, the hub wins.

Rewrite-not-append, like every bible file.

---

## Missions

### Mission Generation

Missions are generated from the simulation state using **a curated library of mission archetypes** with variables filled in by the current world context. The library is built by the AI library builder pipeline (same infrastructure that generates chronicle templates). This means missions are structurally recognizable (the player learns mission types over time) but contextually unique every time.

### Mission Generator Algorithm

After a time jump, the generator must select a (region, archetype) pair and fill variable slots to produce a mission briefing. The selection uses a **weighted random draw from scored candidates**, where each candidate is a possible (region, archetype) pairing.

**Step 1: Build the candidate pool.** Every region in the player's faction (and adjacent contested regions) is evaluated against each archetype's simulation trigger condition. A region under attack triggers Defensive Stand and potentially Multi-Front Defense. A recently conquered region triggers Reconquest. A region with active revolt chains triggers Counterinsurgency. An adjacent hostile faction with a high-attractiveness target triggers Assault. Each (region, archetype) pair where the trigger condition is met enters the candidate pool. Regions with no active trigger conditions produce no candidates — the mission generator only responds to real simulation events.

**Step 2: Score each candidate.** Each (region, archetype) pair receives a single score computed as a weighted sum of three factors:

```
score = (w1 * urgency) + (w2 * relevance) + (w3 * preference)
```

**Urgency (0–1)** — how much does this region need attention? Derived from how far its composite axes have dropped, how active faction conflicts are there (hostile forces at borders, recent attacks, territory recently lost), and whether event chains are in critical stages. A region with stability at 15 under active enemy assault scores near 1.0. A region with moderate tension and no immediate threat scores low.

**Relevance (0–1)** — how connected is this commander to this region and this type of problem? Combines lineage history (has this family operated in or near this region before? — read from the coherence ledger), regional proximity (distance from the commander's lineage "home" region), and archetype fit (does the pressure type align with what this lineage has historically been assigned to?). A frontier military family scoring against a military mission in their home region gets high relevance. The same family scoring against a political crisis across the world gets low relevance.

**Preference (0–1)** — the player's mission archetype weights from game start. Preferred archetypes get a high value. Archetypes marked "rare" get a very low value (e.g., 0.1 — not zero, because extreme urgency can still pull them through).

The three weights (w1, w2, w3) are tuning values in config. In calm periods, urgency scores are modest across the board, so relevance and preference have significant influence — the commander gets sent where it makes sense for who they are. In crisis, one region's urgency score dominates the sum regardless of the other factors — the world stops caring about your specialty and sends whoever's available. This desperation behavior emerges naturally from the math without special-case logic.

**[Future consideration if tuning reveals the need:]** A desperation threshold toggle — when the world's worst urgency score exceeds a threshold, the formula switches to urgency-only: `score = urgency`. This would provide explicit control over the transition from "send the right person" to "send anyone" if the weighted sum's natural behavior proves too gradual or too abrupt during testing. The probable reason for needing this: if the w1 weight on urgency needs to be high enough to dominate in crisis, it might also dominate in calm periods, reducing the influence of relevance and preference below useful levels. The toggle would let urgency be weighted moderately during calm periods while still guaranteeing it takes over in crisis.

**Step 3: Select.** Take the top N candidates by score (configurable, ~5), and do a weighted random draw from those. The highest-scored candidate usually wins, but not always — maintaining stochasticity.

**Step 4: Fill variable slots.** The selected archetype template has variable slots (which system, which faction, what named characters are involved, what's the time pressure). The generator fills these from the selected region's current state, active event chains, and coherence ledger entries. The result is a structured mission briefing ready for presentation to the player.

### Mission Archetypes

Every mission is a military operation. The player is a commander — variety comes from different military situations driven by different simulation states, not from non-military mission categories. A defense against a Conqueror's main force is a completely different tactical problem than suppressing a breakaway insurgency, even though both involve combat. The map, the force composition, the enemy behavior, the objective shape — all differ because the simulation context differs.

Each archetype is a template with fixed structure and variable slots:

- **Simulation trigger** — the specific simulation condition that makes this archetype eligible for selection. The mission generator detects these conditions and pairs them with the appropriate archetype. No fabricated scenarios — every mission responds to something actually happening in the simulation.
- **Objective shape** — what "done" looks like structurally. "Hold X until Y." "Destroy A before B." "Extract C from D." These are the verbs of the mission grammar.
- **Asset profile** — what ratio of combat unit types the mission expects from the force allocation system. This is a recommendation to the civilization's allocation system, not a hard rule — if the civilization is broke, you get less.
- **Map character** — what the spine + gradient map generation system produces for this archetype, guided by the Strategic Layout Authoring Framework. Defensive positions, open terrain, urban infrastructure, boundary lines. Each archetype defines compatibility filters that select appropriate strategic layouts from the shared library. The per-archetype map character descriptions below serve as design intent for authoring those filters.
- **Canvas size** — base size category (small, medium, large) with simulation modifier direction.
- **Success spectrum** — 5 outcome bands (total success, strong success, partial success, partial failure, total failure) with proportional consequence deltas per band. See "Mission Outcome Resolver" below for the full algorithm.
- **Complication table** *(deferred — implement after core missions are working)* — a weighted list of mid-mission events this archetype is susceptible to. Each complication is itself a mini-template with variables. **This system layers on top of working missions — missions must function successfully without complications first.**

The **variable slots** are what the simulation fills in: which region, which faction(s), what named characters are involved, what's the time pressure, what's the force balance. Same archetype, completely different feel depending on context. The simulation's job is picking an archetype and filling the blanks.

**10 mission archetypes**, each mapping directly to a simulation condition the mission generator can detect:

---

**1 — Defensive Stand**

*Simulation trigger:* A hostile faction's agent has launched an attack against one of the player's faction's regions. An attack event is in the pipeline or has recently fired, and the region's military is under pressure.

*Objective shape:* Hold the region against the incoming assault. "Defend X until Y" — survive the enemy's committed force. The time constraint is the duration of the assault; the enemy has a finite committed budget and the attack ends when their force is spent or destroyed.

*Asset profile:* Heavy on Line and Bastion (defensive backbone), moderate Interceptor (area control), light Bombard (ranged suppression from prepared positions). Skews toward units that hold ground.

*Map character:* Defensible terrain. Chokepoints between enemy approach vectors and the objective. Prepared positions with cover. Multiple approach routes so the player must choose where to concentrate defense. The player starts in position; the enemy approaches.

*Canvas size:* Medium. Simulation modifier: wealthier/more developed regions produce larger canvases (more developed space to defend).

*Success spectrum:*
- **Total success** — enemy force destroyed or routed with minimal losses. Military +15% of deficit, tension -10% of current, economy -2% of current (minor war disruption).
- **Strong success** — region held, enemy repelled with moderate losses on both sides. Military +8% of deficit, tension -5% of current, economy -5% of current.
- **Partial success** — region held but at heavy cost. Defensive infrastructure damaged, significant casualties. Military -5% of current, tension +5% of deficit from 100, economy -10% of current.
- **Partial failure** — position overrun but orderly withdrawal preserved some forces. Military -15% of current, tension +10% of deficit from 100, economy -15% of current.
- **Total failure** — position overrun, force destroyed or scattered. Region may fall to conquest on the next simulation tick. Military -30% of current, tension +20% of deficit from 100, economy -20% of current, population -5% of current.

---

**2 — Siege Breaking**

*Simulation trigger:* A region has been under sustained border friction from a heavily militarized hostile neighbor for many ticks (detected by: military and economy have declined significantly while a hostile faction with high military occupies adjacent territory). The region hasn't been conquered but is being strangled.

*Objective shape:* Break the siege. Push the enemy back from the border, reopen supply lines, relieve the garrison. "Destroy enemy forward positions" — offensive action from a defensive starting position. The player starts inside the besieged region and must push outward.

*Asset profile:* Balanced offensive/defensive. Vanguard and Raider (breakthrough and flanking), Line (holding gained ground), moderate Bombard (softening fortified enemy positions). The player needs to attack but also hold what they take.

*Map character:* The player's region is in the center with degraded but functional infrastructure. Enemy positions ring the perimeter — fortified forward bases, patrol routes, supply interdiction points. Multiple enemy positions that can be tackled in any order, but the player can't hit them all simultaneously. Rewards prioritization.

*Canvas size:* Large. Simulation modifier: regions under longer siege produce smaller canvases (the siege has compressed the defensive perimeter).

*Success spectrum:*
- **Total success** — all enemy forward positions destroyed, siege fully broken. Military +10% of deficit, tension -15% of current, economy +10% of deficit (supply lines restored).
- **Strong success** — most enemy positions destroyed, siege pressure significantly reduced. Military +5% of deficit, tension -10% of current, economy +5% of deficit.
- **Partial success** — some enemy positions destroyed but siege not fully broken. Pressure reduced but not eliminated. Military -3% of current, tension -5% of current, economy +3% of deficit.
- **Partial failure** — failed to break through. Enemy positions intact, player forces damaged. Siege continues. Military -10% of current, tension +5% of deficit from 100, economy -5% of current.
- **Total failure** — sortie crushed. Garrison weakened by the failed attempt, siege tightens. Military -20% of current, tension +15% of deficit from 100, economy -10% of current.

---

**3 — Reconquest**

*Simulation trigger:* One of the player's faction's regions was recently conquered by a hostile faction. The conquest event fired within the last time jump. The region has conquest unrest (high tension) and the occupier's garrison is relatively thin (recently placed, hasn't had time to build up).

*Objective shape:* Retake the region. "Destroy the occupying garrison and secure the region." Offensive assault against a weakened but fortifying defender. Time-sensitive — the longer the player waits (in simulation terms), the more entrenched the occupier becomes, so this archetype scores high urgency when the conquest is recent and lower as ticks pass.

*Asset profile:* Offensive-heavy. Raider (fast strikes on dispersed garrison), Vanguard (breakthrough against fortified positions), Bombard (reduce defensive structures). Light on defensive units — you're attacking, not holding.

*Map character:* Former friendly territory — the map has infrastructure that the occupier is repurposing. Defensive positions exist but the enemy is partially set up (some fortified, some still being established). The population is partially sympathetic — represented mechanically by the occupier's garrison being thinner than a fully entrenched defender and the conquest unrest making the region unstable for them.

*Canvas size:* Medium. Simulation modifier: regions with higher pre-conquest development produce larger canvases.

*Success spectrum:*
- **Total success** — garrison destroyed, region retaken with minimal damage to infrastructure. Military set to garrison value (from conquest resolution), tension -10% of current (population relieved), economy +5% of deficit (infrastructure preserved).
- **Strong success** — region retaken but with significant fighting. Some infrastructure damaged. Military set to garrison value minus losses, tension -5% of current, economy -5% of current.
- **Partial success** — occupier driven out but at heavy cost. Region retaken in a damaged state. Military set to low garrison, tension +5% of deficit from 100 (protracted battle stressed the population), economy -15% of current.
- **Partial failure** — assault failed. Player forces withdrew. Occupier retains the region and is now more entrenched. No field changes to the region (it remains enemy-held). Player faction takes a morale/tension hit in adjacent regions: tension +5% of deficit from 100 in bordering player regions.
- **Total failure** — assault crushed. Significant player force losses. Occupier retains the region with strengthened garrison. Adjacent player regions: tension +10% of deficit from 100, military -5% of current (forces lost in the failed assault).

---

**4 — Assault**

*Simulation trigger:* The player's faction agent has identified an enemy region as an attack target (the attack scored highest in the attractiveness evaluation and passed the confidence threshold). The player is the instrument of that attack.

*Objective shape:* Conquer the enemy region. "Destroy the defending force and take the position." Full offensive operation against an established enemy position. The defender is dug in on their own territory with full infrastructure and garrison.

*Asset profile:* Heavy offensive. Vanguard (main assault force), Bombard (reduce fortifications from range), Raider (flanking and disruption), Interceptor (area denial to prevent defender repositioning). Minimal defensive units — you're bringing the fight to them.

*Map character:* Enemy territory. The defender has prepared positions, fortified chokepoints, established infrastructure. The player starts outside and must fight inward. Multiple approach vectors with different risk/reward profiles — a frontal assault through the main chokepoint, a flanking route through difficult terrain, a fast Raider path that's exposed. The map rewards scouting and planning during the recon phase.

*Canvas size:* Large. Simulation modifier: well-developed enemy regions produce larger canvases (more infrastructure to fight through).

*Success spectrum:*
- **Total success** — defender destroyed, region conquered with infrastructure largely intact. Region transfers to player faction. Conquest event fires with standard consequences (tension spike, garrison placement) but economy damage is minimal.
- **Strong success** — region conquered after significant fighting. Moderate infrastructure damage. Conquest event fires with higher economy damage.
- **Partial success** — enemy force severely weakened but not destroyed. Region not conquered but the defender is crippled — their military is reduced significantly, making them vulnerable to follow-up attack on subsequent ticks. Target region: military -30% of current.
- **Partial failure** — assault repelled. Player forces take moderate losses. Enemy holds but is somewhat weakened. Target region: military -10% of current. Player's home region: tension +5% of deficit from 100.
- **Total failure** — assault crushed. Significant player force losses. Enemy emboldened. Target region: military -3% of current (minimal). Player's home region: tension +15% of deficit from 100, military -10% of current (forces lost).

---

**5 — Suppression**

*Simulation trigger:* An admin revolt or tension revolt has produced a breakaway faction inside or adjacent to the player's territory. The new faction holds one region with degraded fields (the revolt chain's intermediate events damaged it). The breakaway is recent — it hasn't had time to consolidate.

*Objective shape:* Eliminate the breakaway faction's military capability before they consolidate. "Destroy the rebel force." Quick, decisive strike against a newly formed faction. Time pressure is implicit — a prolonged fight gives them time to build up, and the mission's urgency score decays as the breakaway ages.

*Asset profile:* Fast and aggressive. Raider (speed and flanking), Vanguard (decisive engagement), Interceptor (prevent escape and consolidation). Light force overall — the enemy is weak, you don't need a full army. This is one of the smaller-scale missions.

*Map character:* Recently revolted territory. Infrastructure is partially damaged from the revolt chain. The enemy is dispersed — multiple small positions rather than one fortified base. The player must locate and engage scattered rebel forces. Sensor interference may be present (the rebels are hiding among the population). Rewards aggressive pursuit over static defense.

*Canvas size:* Small. Simulation modifier: regions with higher pre-revolt development produce slightly larger canvases.

*Success spectrum:*
- **Total success** — rebel force destroyed, region stabilized. Region returns to player faction control. Military set to moderate garrison, tension -15% of current (revolt crushed decisively), economy +5% of deficit (order restored quickly).
- **Strong success** — rebel force mostly destroyed, region retaken with some residual instability. Region returns to player faction. Military set to low garrison, tension -8% of current, economy stable.
- **Partial success** — rebel force damaged but not eliminated. They retreat to a defensible position. Region may or may not return to player control depending on remaining rebel strength. Tension -3% of current (if retaken) or no change (if not).
- **Partial failure** — suppression failed. Rebel force intact and now more consolidated. The breakaway faction survives and begins normal agent behavior. Region remains under rebel control. Player's adjacent regions: tension +5% of deficit from 100.
- **Total failure** — suppression force defeated. Rebels emboldened, potentially inspiring further revolts. Region remains under rebel control. Player's adjacent regions: tension +10% of deficit from 100.

---

**6 — Multi-Front Defense**

*Simulation trigger:* Two or more hostile factions are attacking the same region simultaneously, or attacking adjacent regions within the same time jump window. Detected by multiple active attack events or high-military hostile factions on multiple borders of the same region.

*Objective shape:* Survive attacks from multiple directions. "Defend against all incoming forces" — but the player cannot be everywhere. The core tactical challenge is prioritization: which threat do you address first? Where do you accept losses to concentrate force elsewhere? This is where the game's "the world is too big for one commander" feeling hits hardest.

*Asset profile:* Balanced but stretched thin. The player gets a force sized to the combined enemy strength (per the force parity system) but must split it across multiple fronts. All unit types represented — the player decides how to distribute them. The force feels adequate in total but insufficient at any single point.

*Map character:* Multiple enemy approach vectors from different directions. The player's position is central with defensive infrastructure radiating outward. Interior lines allow the player to shift forces between fronts — but movement takes time, creating windows of vulnerability. Chokepoints on each front that can be held by smaller forces, rewarding the player who reads which front is the main thrust and which is a feint.

*Canvas size:* Large. This is the biggest-scale mission type. Simulation modifier: more hostile factions involved produce larger canvases.

*Success spectrum:*
- **Total success** — all fronts held, all enemy forces repelled or destroyed. Military +10% of deficit, tension -10% of current, economy -5% of current (war disruption).
- **Strong success** — all fronts held but at significant cost on at least one front. Military stable, tension -5% of current, economy -10% of current.
- **Partial success** — one front held, one front partially overrun. The player saved the core but lost peripheral positions. Military -10% of current, tension +5% of deficit from 100, economy -15% of current.
- **Partial failure** — multiple fronts overrun. The region is severely damaged even if technically held. Military -20% of current, tension +15% of deficit from 100, economy -20% of current, population -5% of current.
- **Total failure** — position overrun from multiple directions. Catastrophic loss. Military -35% of current, tension +25% of deficit from 100, economy -25% of current, population -10% of current.

---

**7 — Interception**

*Simulation trigger:* A hostile faction has launched an attack against one of the player's regions, and the attack force must traverse space to reach the target. The player intercepts the enemy force in the field before it reaches the region — on neutral ground, in transit corridors, or in contested border space.

*Objective shape:* Destroy or turn back the enemy force before it reaches the target region. "Intercept and destroy the attacking force." Pure force-on-force engagement on open ground. No defensive infrastructure to rely on. If the player fails to stop the enemy, the target region faces the attack undefended (or with only its garrison).

*Asset profile:* Mobile and aggressive. Raider (fast engagement), Interceptor (area control and pursuit), Vanguard (main striking power). Light on Bastion and Bombard (no positions to hold, no fortifications to reduce). This is a meeting engagement — speed and aggression matter more than defense.

*Map character:* Open terrain. No prepared positions for either side. The enemy force is in transit — moving across the map toward an exit point (representing the target region). The player must engage before the enemy reaches the exit. Terrain features provide tactical options (cover, elevation, sensor interference) but neither side has fortifications. Rewards aggressive positioning and fast decision-making.

*Canvas size:* Medium. Simulation modifier: larger enemy committed budget produces larger canvases (bigger forces need more room to maneuver).

*Success spectrum:*
- **Total success** — enemy force destroyed in the field. Target region untouched. Target region: no negative effects. Player's faction: tension -5% of current in the target region (threat eliminated).
- **Strong success** — enemy force severely damaged and turned back. Remnants retreat. Target region: military -3% of current (minor skirmishing at the border).
- **Partial success** — enemy force damaged but a significant portion breaks through to the target. Target region suffers a reduced attack (the attack's committed budget is effectively halved for resolution purposes).
- **Partial failure** — interception failed. Most of the enemy force reached the target. Target region suffers the full attack as if the interception hadn't occurred.
- **Total failure** — player force destroyed in the field. Enemy force proceeds to target at full strength. Target region suffers the full attack. Player faction: military -15% of current in the target region (forces lost in the failed interception).

---

**8 — Rear Guard / Evacuation**

*Simulation trigger:* A region is about to fall — military is critically low, economy is cratered, stability is near zero. The simulation has effectively written it off. The region is adjacent to hostile territory with a high-military enemy faction. The mission generator detects that the region is unrecoverable and generates an evacuation rather than a defense.

*Objective shape:* You're not trying to win. You're trying to save what you can. "Extract valuable assets and cover the retreat." Protect evacuation points while delaying the enemy advance. Success is measured by how much you save, not whether you hold the position. The time constraint is the evacuation timer — once it expires (or the evacuation targets are extracted), the mission ends regardless of battlefield state.

*Asset profile:* Defensive and mobile. Line and Bastion (delaying force), Raider (screening and harassment), light overall — this is a fighting retreat, not a pitched battle. The force is explicitly undersized relative to the enemy, reinforcing the "you can't win this" feeling. Non-combat assets (supply convoys representing evacuation targets) are present and must be protected.

*Map character:* Collapsing perimeter. The player starts in a defensive position with evacuation points behind them and enemy forces approaching from the front. The map compresses over time — the playable area effectively shrinks as the enemy advances and the player falls back. Extraction points at the rear of the map. Multiple things to protect (evacuation convoys, key infrastructure) that can't all be defended simultaneously, forcing triage.

*Canvas size:* Medium. Simulation modifier: regions with higher remaining population produce larger canvases (more to evacuate).

*Success spectrum:*
- **Total success** — all evacuation targets extracted, delaying force withdraws intact. The region falls (it was going to anyway) but the faction preserves its assets. Adjacent player regions: economy +5% of deficit (evacuated resources), population +3% of deficit (refugees resettled). Lost region: no mitigation — it falls on the next simulation tick.
- **Strong success** — most evacuation targets extracted, moderate losses to the delaying force. Adjacent regions: economy +3% of deficit, population +2% of deficit.
- **Partial success** — some evacuation targets extracted, heavy losses to the delaying force. Adjacent regions: economy +1% of deficit, population +1% of deficit.
- **Partial failure** — evacuation mostly failed. Few assets extracted, delaying force overrun. Adjacent regions: minimal benefit. Lost region: falls with no mitigation.
- **Total failure** — delaying force destroyed, evacuation targets captured or destroyed. Total loss. Adjacent regions: tension +10% of deficit from 100 (shock and demoralization from the catastrophe). Lost region: falls with no mitigation.

---

**9 — Containment**

*Simulation trigger:* A Schism faction or rapidly expanding hostile faction is spreading through adjacent regions. Multiple regions bordering the player's territory are under hostile control or at risk (high tension, adjacent to the spreading faction). The threat is diffuse — not a single attacking force but an expanding territorial presence.

*Objective shape:* Draw a line and hold it. "Prevent the hostile faction from advancing past the boundary." The player chooses where to concentrate defense along a front. The enemy isn't trying to destroy the player head-on — they're trying to flow around the player's positions and take territory. The player can't be everywhere, so they must choose which approaches to block and which to concede.

*Asset profile:* Defensive and spread. Line and Bastion (holding positions), Interceptor (covering gaps between positions), Warden (area influence over wide front). Light on offensive units — you're holding, not attacking. The force is spread across a wide front rather than concentrated at a single point.

*Map character:* Wide front with a defined boundary line. Multiple approach corridors the enemy can use to bypass or overwhelm player positions. The player must garrison multiple chokepoints simultaneously. Terrain features create natural defensive positions but with gaps between them. The enemy AI sends forces through multiple corridors, testing the player's deployment. Rewards reading the enemy's main effort and redeploying reserves.

*Canvas size:* Large. Simulation modifier: more border regions at risk produce larger canvases.

*Success spectrum:*
- **Total success** — boundary held completely. No enemy forces penetrated past the line. Regions behind the boundary: tension -5% of current (threat contained). Hostile faction's advance is stalled — their recently conquered regions continue to drain their budget without further expansion.
- **Strong success** — boundary mostly held. Minor penetrations contained. Regions behind: tension -3% of current.
- **Partial success** — boundary breached in one sector but held elsewhere. The player chose which corridor to concede. One adjacent region is now exposed to the hostile faction's border friction. Regions behind the held sectors: no change. Exposed region: tension +5% of deficit from 100.
- **Partial failure** — boundary breached in multiple sectors. The containment line failed. Multiple adjacent regions now exposed. Exposed regions: tension +10% of deficit from 100, economy -5% of current (border friction from new hostile neighbor).
- **Total failure** — containment collapsed. The hostile faction flows past the player's positions. All adjacent regions now have hostile border friction. Exposed regions: tension +15% of deficit from 100, economy -10% of current.

---

**10 — Counterinsurgency**

*Simulation trigger:* A region the player's faction holds has active revolt event chains — tension is above the revolt threshold, there may be an ongoing resistance movement from a previous conquest, or the conquest consequence chain has spawned unrest events. The threat is internal, not from an external faction.

*Objective shape:* Find and neutralize insurgent forces within your own territory. "Destroy rebel military capability without destroying the region." The enemy is scattered, mobile, and embedded in civilian infrastructure. The player must hunt them down while minimizing collateral damage — heavy-handed tactics may win the battle but worsen the underlying tension problem.

*Asset profile:* Light and mobile. Raider (pursuit and flanking), Interceptor (area search and control), light Vanguard (engagement when insurgents are found). Minimal heavy units — Bombard and Bastion are ill-suited to counterinsurgency (too destructive, too slow). The force is deliberately smaller than a standard combat force, reflecting the asymmetric nature of the fight.

*Map character:* The player's own territory. Infrastructure that the player wants to preserve. Insurgent forces are initially hidden — scattered across the map in sensor interference zones, behind cover, in defensible pockets. The player must use sensor coverage to locate them, then engage. Destroying infrastructure (objectives, cover positions) is mechanically possible but counterproductive — it worsens the region's economy and tension in the outcome resolver. The map rewards patient, methodical clearing over brute-force assault.

*Canvas size:* Small to medium. Simulation modifier: higher-tension regions produce larger canvases (insurgency is more widespread).

*Success spectrum:*
- **Total success** — insurgent force eliminated with minimal collateral damage. Tension -20% of current (revolt crushed, order restored), military +5% of deficit (local militia rallies), economy stable (infrastructure preserved).
- **Strong success** — most insurgents eliminated, minor collateral damage. Tension -12% of current, military +3% of deficit, economy -3% of current.
- **Partial success** — insurgent force reduced but not eliminated. Some collateral damage. Tension -5% of current (partial suppression) but economy -8% of current (infrastructure damage from fighting).
- **Partial failure** — insurgents largely intact. Significant collateral damage from the attempt. Tension +5% of deficit from 100 (heavy-handed military action worsened resentment), economy -12% of current.
- **Total failure** — suppression failed completely. Insurgents emboldened, infrastructure damaged, population hostile. Tension +15% of deficit from 100, economy -15% of current, military -5% of current (forces lost or defected). The region may cross the breakaway threshold on the next simulation tick.

---

**Fairness target profiles** — each archetype has a `FairnessTargetProfile` controlling what map shapes the fairness evaluator accepts. The 4 prototype archetypes (defensive_stand, assault, multi_front_defense, counterinsurgency) were tuned in Stage 7. The remaining 6 (siege_breaking, reconquest, suppression, evacuation, raid, rear_guard) were given directionally-grounded profiles in Stage 11e based on the bible prose above. All 6 non-prototype profiles may need further tuning after playtesting — tolerances are deliberately wide (±0.20–0.30) pending real gameplay data.

**Inheritance missions** are not a separate archetype — they are a rare narrative modifier the coherence ledger can apply to any of the 10 archetypes. "This is a reconquest mission... reconquering a system your great-grandmother lost." The connection is highlighted in the chronicle, but mechanically it's still a standard mission of its base archetype.

### Mission Objectives

Missions have:
- **A primary objective** — what the civilization sent you to do
- **A time constraint** — you don't have forever; the world is moving
- **Success conditions that exist on a spectrum** — not binary pass/fail. You might secure the system but lose half your force. You might fail the primary but save something unexpected. The degree and nature of success/failure feeds back into the simulation differently.

### Difficulty Scaling

Difficulty scales primarily through **constraint compression** — tighter resources, shorter timelines, more frequent complications, heavier stakes. Easy/Medium/Hard is chosen at the start of a playthrough — a permanent choice for the entire generational arc.

As pressure mounts across generations, the simulation compresses what the player has to work with: time gets shorter, resources get thinner, objectives get compound, complications get more frequent, and stakes get heavier. A late-game defense mission and an early-game defense mission use the same archetype, but the late-game version is a desperate nightmare because you have half the force, two extra problems, and twenty fewer years of civilization health backing you up.

Note: because the AI library generates unit stat profiles (see AI-Generated Unit Variety and Unit Power Balancing), unit power levels do vary — but they vary equally for both the player and the enemy. Difficulty does not come from enemy factions having stronger units. It comes from the player having less to work with.

Difficulty setting adjusts: resource allocation generosity, complication frequency and overlap, time constraint width, and how quickly the constraint compression ramps across generations. It does **not** change: the simulation itself (same stochasticity, same faction agent behavior, same coherence ledger), mission archetypes and objective shapes, or narrative quality.

### Era Scaling

Tech era doesn't just mean "better units" — it means **different units.** Early era might be slow, tanky, short-range. Mid era opens up speed and range. Late era (if the civilization is thriving) might introduce exotic capabilities that change how you approach problems entirely. But if the civilization is declining, late era might mean losing capabilities — fielding patched-together relics because the production facilitys are gone. Better tools always come with harder problems.

Unit classes and roles are consistent across eras (there's always a Strike skirmisher, always a Siege artillery) but the specific units are fundamentally different — not just "the same unit with bigger numbers." AND within an era, the AI generates per-civilization variation based on civilization traits. The result: every playthrough's force feels authored without being mechanically unpredictable.

### Mission Preference

The player marks any subset of the 10 mission archetypes as **"rare"** at game start. Rare-marked archetypes receive a strong down-weight (0.1 in the preference term — see the "Preference" factor above), making the simulation almost never pick them, though it reserves the right in extreme world states where no other archetype fits. Unmarked archetypes share the default preference weight. The interaction is binary per archetype (rare or default) — there is no per-archetype gradation. The player can mark as many archetypes as they want, with one constraint: **at least one archetype must remain unmarked**, so the generator always has a non-rare pool to bias toward. When the simulation has multiple viable pressure points, it biases away from rare-marked archetypes toward the default-weighted ones.

The simulation always has final say. Preferences are a request, not a command. If the world is on fire and only an evacuation mission makes sense, that's what you get. The commander doesn't choose their orders — but command tries to play to their strengths when they can. Preferences are set at game start and not changeable mid-playthrough.

### Mission Briefing

The briefing comes from the civilization, not from a game menu. Delivered as if a superior officer is handing you your orders. Three sections:

- **Situation** — what's happening in the world that made this mission necessary. Drawn from the simulation state and the chronicle.
- **Objective** — what you're being sent to do, with the success spectrum made implicit through the framing. The player reads between the lines.
- **Assets** — what you're being given. Force composition, non-military assets, and a note on what the civilization couldn't spare.

The player reads, then accepts. No negotiation, no loadout screen — you get what the civilization gives you. The only choice is whether to refuse the mission entirely (rare, with consequences — the simulation treats refusal as a failed mission with its own consequence bundle).

### Mission Time Limits

Each archetype has a base time limit (in tactical ticks at 20/sec) scaled by urgency. Higher urgency compresses the time limit by up to 20%. The time limit never drops below 60% of the base. Formula: `time_limit = base_time * (1.0 - urgency * TIME_PRESSURE_SCALING)`, clamped at `base_time * TIME_LIMIT_FLOOR_PCT`. See `config.py` `ARCHETYPE_TIME_LIMITS` for per-archetype base values. Implemented in `objectives.compute_time_limit()`.

### Complications (Deferred — implement after core missions work)

Mid-mission complications are **rare and pre-computed, not driven by a live simulation.** The simulation is stopped during missions. When a mission is generated, the archetype's complication table identifies what *could* go wrong based on the current world state. Probability determines whether a complication actually fires — roughly every third mission, not every mission. If one fires, the timing and nature are determined at generation, not dynamically.

This means complications feel like memorable disruptions, not background noise. A faction collapsing mid-evacuation is a story the player tells later. It shouldn't happen often enough to become routine.

**This entire system is implemented after missions work end-to-end without complications. Missions on their own should be a complete, satisfying experience first.**

**Implementation target: Stage 7 or later.** Depends on working core missions (Stages 5.5 + 6).

### Outcome Band Classification System

> **RESOLVED (v2.01).** The classification system is the bridge between tactical gameplay and simulation consequences. It evaluates the player's mission performance and produces a single outcome band that the Mission Outcome Resolver consumes.

**Two-component scoring function evaluated at mission end.** The classification runs once when the mission concludes (either all objectives are resolved, the time deadline expires, or the player's force is eliminated). The result is revealed to the player at mission end, not during gameplay.

**Component 1 — Objective completion score (0.0 to 1.0).** Each mission instance defines a weighted set of objectives generated from the archetype's objective shape. One primary objective carries dominant weight (e.g., 0.6 of the objective score). Zero to three secondary objectives split the remaining weight. Each objective produces a completion value: binary objectives are 0 or 1 (did you hold the position? did the convoy survive?), graduated objectives scale linearly (what percentage of enemy forces were eliminated? how many defensive positions were held?). The weighted sum produces the objective score. Per-archetype objective sets are authored separately — the classification system is objective-agnostic, it just consumes completion values and weights.

**Component 2 — Force retention ratio (0.0 to 1.0).** Total surviving unit value (using the power rating system) divided by total deployed unit value. Lose nothing, it's 1.0. Lose everything, it's 0.0. This is a straightforward accounting of what survived.

**Final score formula:** `final_score = (objective_score × w_obj) + (retention_ratio × w_ret)` where `w_obj` is the dominant weight (e.g., 0.75) and `w_ret` is the secondary weight (e.g., 0.25). All weights are config values tuned during playtesting. Objectives carry the most weight — completing the mission matters more than preserving forces. But a commander who achieves the objective AND brings their people home scores higher than one who wins through attrition.

**Per-archetype threshold boundaries.** The final score maps to one of 5 outcome bands through threshold boundaries that are **defined per archetype, not universal**. The same final score means different things for different mission types. A Rear Guard / Evacuation mission where you save 60% of the evacuees is a strong success — you weren't expected to save everyone. An Assault mission where you only neutralize 60% of the enemy garrison is a partial failure — you didn't finish the job. Per-archetype thresholds let the system calibrate "what good looks like" for each tactical situation. Threshold values are config per archetype, tuned during playtesting.

**Time is a constraint, not a scoring input.** Missions have time deadlines. The deadline is pass/fail — you either complete objectives before time runs out, or whatever objective state exists when the deadline expires becomes your final objective score. Completing the mission faster does not improve the score.

### Mission Outcome Resolver

After a mission ends, the outcome resolver translates the tactical result into simulation consequences. The resolver sits between the tactical layer (which classifies what happened) and the simulation (which needs field deltas to process).

**Input: outcome band.** The Outcome Band Classification System (see above) evaluates the player's tactical performance and produces a single outcome band from the archetype's 5-band spectrum. The resolver receives this single band classification — one value, thin interface.

**Transformation: proportional lookup table per archetype.** Each mission archetype defines a consequence table mapping each outcome band to field deltas for the mission region. Deltas are defined as **proportional to the region's current state** rather than absolute numbers. Instead of "military +10," the table says "military +10% of deficit from 100." A region at military 20 gets a bigger absolute boost from a successful defense mission than a region at military 80. A region already near collapse gets hit harder by failure.

This proportional scaling means consequences feel appropriate to the situation. Saving a desperate region has a bigger impact than reinforcing a strong one. Failing in a strong region is a setback; failing in a weak region is a catastrophe. The scaling emerges from one design choice (proportional vs. absolute) without special-case logic.

**Scope: mission region only.** The consequence bundle is field deltas applied to the mission region. There is no separate world-wide momentum, vector nudge, or ripple system. The simulation handles world-wide propagation naturally: improved stability in one region affects neighboring regions through existing inter-region dependencies (trade, military support, faction dynamics) as the time jump runs forward. The world "learns" about the mission outcome organically through hundreds of ticks of simulation, not through an artificial broadcast.

**Why no vector nudge:** The bible previously referenced "a direct vector nudge for intangible civilizational effect" as part of consequence bundles. This has been simplified away. Region stat changes applied to the mission region, processed through the simulation's existing composite axes and inter-region mechanics during the time jump, already capture the full civilizational impact. A military victory that boosts military strength and drops factional tension in a key region IS the civilizational impact — the composite axes propagate it, and the time jump's hundreds of ticks let it ripple through the world's interconnected systems.

---

### Objective Tracking — Tactical Engine Implementation

> **RESOLVED (v2.02).** This section specifies how mission objectives are represented and evaluated in the headless tactical simulation engine. The objective system bridges between the mission generator (which defines what the player must accomplish) and the outcome band classification system (which evaluates how well they did).

**Objective data model.** Each mission instance carries an ordered list of objectives. Each objective has:
- **Type** — one of: `hold_zone` (defend an area for a duration), `destroy_targets` (eliminate specific enemy units or a percentage of enemy force), `escort_to_extraction` (get designated units to an extraction point alive), `survive_duration` (keep player force alive for a time period), `eliminate_force` (destroy a percentage of total enemy HP).
- **Weight** — contribution to the objective completion score. One primary objective carries dominant weight (e.g., 0.6). Zero to three secondary objectives split the remaining weight. All weights sum to 1.0.
- **Parameters** — type-specific: zone center/radius and hold duration for `hold_zone`, target unit IDs for `destroy_targets`, extraction point position for `escort_to_extraction`, duration in ticks for `survive_duration`.
- **Completion value** — 0.0 to 1.0, updated per tick. Binary objectives produce 0 or 1. Graduated objectives scale linearly (e.g., 60% of targets destroyed = 0.6 completion).

**Per-tick evaluation.** The tactical engine evaluates all objectives every tick:
- `hold_zone`: timer advances while the zone contains no enemy units. Enemies entering the zone pause the timer. Completion = elapsed hold time / required hold time.
- `destroy_targets`: completion = fraction of designated targets destroyed.
- `escort_to_extraction`: completion = fraction of escort units that reached extraction alive.
- `survive_duration`: completion = elapsed time / required time. Fails to 0.0 if all player units die before time expires.
- `eliminate_force`: completion = fraction of total enemy force HP destroyed.

**Terminal conditions.** The mission ends when any of these is met:
1. All objectives are resolved (primary objective complete or definitively failed).
2. The mission's time deadline expires — whatever objective state exists becomes the final score.
3. The player's entire force is eliminated — objective completion freezes at current values.

Time is a constraint, not a scoring input. Completing objectives faster does not improve the score. The deadline is pass/fail — either objectives are resolved before time runs out, or the current state at deadline becomes the final assessment.
