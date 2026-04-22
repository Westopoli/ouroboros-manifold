# Ouroboros Manifold — World Reference

> **Extracted from game_bible.md v1.23.** This file is authoritative for world generation,
> topology, lifecycle, and map generation. If this file conflicts with game_bible.md,
> flag it for Westley — do not silently resolve the conflict.
>
> **Modification rule:** Same as the master bible — append-only unless Westley approves
> deletion. Resolved open questions get written here AND reflected back to the hub.

---

## The World

### Scale

Small enough for a solo dev to build, large enough to feel vast:
- The number of systems, inhabited regions, and uninhabited space is **variable** — determined by the simulation's configuration and the needs of the current playthrough. The world should feel vast without being unmanageable.
- The civilization starts small — a handful of inhabited regions in a mostly dark world
- Expansion happens through the simulation over time, not given for free
- Uninhabited systems serve as strategic buffer zones and colonization targets
- The world is the same one across all chapters and cycles — it changes over time, but it's persistent. Ruins from previous cycles accumulate.

### World Generation — Tiered Templates

The world's starting state is generated from a **starting template** — a hand-designed topology skeleton with randomized field values within defined ranges. Templates ensure every start is playable while providing variety across playthroughs.

Each template defines: the number and arrangement of starting regions (home, frontier, empty/unexplored), the adjacency graph connecting them, and stat ranges per region tier. The home region starts with strong field values (the civilization's established core). Frontier regions start weaker (recently settled, resource-constrained). Empty regions have no state and are activated when expansion events fire during the simulation.

**Starting templates (2–3 to start, more added if needed):**

- **Isolated start** — 1 home region, 2 adjacent frontier regions, 4–6 empty regions beyond. The civilization is a single cluster pushing outward. Straightforward, good for learning the game.
- **Twin colony** — 2 home regions connected to each other, 1–2 frontier regions each, empty space around and between. The civilization has two centers of power from the start, creating natural factional dynamics and resource competition.
- **Archipelago** — 1 home region, 3 frontier regions with sparse connections (not all adjacent to each other or to home). The civilization is stretched across disconnected outposts with fragile supply lines. High early pressure, strategic isolation.

Field values within each template are randomized within ranges (e.g., home military 55–70, home economy 60–75) so two playthroughs on the same template feel different. The template is selected at game start — either player choice or random.

**Implementation approach (Stage 0):** Build one template first (isolated start). Get the simulation proven on it. Then add templates incrementally, verifying each produces meaningfully different simulation behavior before adding the next.

**Multi-faction starting positions.** Templates define starting territories for NPC factions alongside the player's civilization. For the isolated start template, the Conqueror starts with **1–2 regions on the far side of the empty space**, separated from the player's frontier by one uninhabited buffer region. This creates a natural early-game rhythm: both factions expand into empty space, the buffer region becomes a contested flashpoint, and first military contact is an emergent event rather than a starting condition. The Conqueror's starting regions use their own field value ranges (config values per archetype — e.g., Conqueror home military 50–65, economy 40–55), reflecting a different civilization with different strengths.

Other templates follow the same principle: NPC factions are placed with at least one uninhabited region separating them from the player's territory. The exact placement varies per template — the twin colony template might place the Conqueror between the player's two home regions (threatening to cut them off), while the archipelago template might place the Conqueror adjacent to the player's most isolated outpost.

Template extensions for additional archetypes (the Warlord, the Fortifier, the Opportunist, the Schism) are designed when those archetypes are implemented. The Schism does not have a starting template position — it spawns from revolts during gameplay. The template format supports any number of starting factions — each defined by archetype, starting region count, position in the graph, and field value ranges.

### Inter-Region Topology — Typed Adjacency Graph

Regions are nodes in a graph. Edges represent connections between regions and carry a **type tag** that determines what propagates through them:

- **Border** — military adjacency. Antagonist pressure spreads through border edges. Military reinforcement and garrison support propagate through borders. A region with no border connection to the civilization's core is militarily isolated.
- **Trade route** — economic connection. Trade, supply, and economic interdependence propagate through trade route edges. A region connected only by trade route receives economic benefits but no military support.
- **Both** — full connection. Military and economic effects both propagate.

This separation creates strategic situations where military and economic geography don't perfectly overlap. A frontier region might be economically connected to the core via trade but militarily exposed because no border edge exists. Cutting a trade route (through blockade, hostile faction action, or regional collapse) has different consequences than losing a border (through conquest or territorial withdrawal).

Effects that reference "nearby" or "adjacent" regions specify which edge types they care about. Passive drift modifiers, faction attack propagation, event chain propagation, and the character selector's "nearby region" checks all specify edge type in their queries.

The graph is defined at world generation (part of the starting template) and grows as expansion events add new regions and edges. New edges can also form during simulation (a trade route opens between previously disconnected regions) or break (a trade route collapses due to regional instability).

**Implementation approach (Stage 0):** Start with plain untyped adjacency — all edges are "both." Get passive drift, event propagation, and faction interactions working through simple adjacency. Then add edge types as a second step and verify that separating military and economic connections produces meaningfully different simulation behavior. If the distinction doesn't matter in practice, simplify back to untyped.

**Implemented (bible-spec reconciliation Phase 2, April 2026).** All adjacency queries specify edge type. Edge type assignment rules:

| Event | Edge type assigned |
|---|---|
| Cooperative peace formed | Shared edges → "both" |
| Betrayal | Shared edges → "border" |
| Conquest | Conqueror's same-faction neighbors → "both"; former owner's neighbors → "border"; cooperative partner's neighbors → "both" |
| Colonization | Same-faction neighbors → "both"; cooperative partner's neighbors → "both" |

Dynamic updates via `world.set_edge_type()` and `world.update_faction_pair_edges()`. Queries via `world.get_neighbors(rid, edge_type=)` with filter support for "border", "trade", "both", or None (all edges).

### World Evolution — Per-Faction Lifecycle

The world does not have global eras. Individual factions have lifecycles, and multiple factions at different lifecycle stages coexist simultaneously. A young breakaway faction expanding into empty space exists alongside a centuries-old empire in decline. The player experiences whatever lifecycle stage their current faction is in — the "era feeling" comes from faction state, not from a global game clock or chapter number.

**What the player experiences depends on their faction's state, not the world's age:**

- **In a young faction** (few regions, low budget, expanding into empty space): missions are about establishing footholds, defending fragile frontiers, first military contacts with neighbors. The feeling is pioneer survival — scrappy, resource-scarce, every mission matters because the faction can't absorb a loss.

- **In an established faction** (multiple mature regions, strong economy, contested borders): missions involve border wars, political maneuvering, choosing which fronts to prioritize. The feeling is strategic depth — the player is a commander in a real military with real logistics and real enemies.

- **In an overextended faction** (many regions including conquered husks, budget stretched thin, revolts brewing): missions are about holding crumbling frontiers, quelling revolts, choosing what to save and what to abandon. The feeling is imperial weight — too much territory, not enough resources, every solution creates a new problem.

- **In a declining faction** (losing territory, economy degraded, breakaways forming): missions are desperate — last stands, fighting former allies, protecting the last intact core regions. The feeling is elegiac — the player watches an institution die from the inside while trying to save what they can.

- **In a faction born from collapse** (breakaway from a revolt, inheriting fragments of a destroyed empire): missions are about survival and identity — a new faction finding its footing in a dangerous world, surrounded by the wreckage of what came before.

The player may experience all of these feelings across a single playthrough as the lineage rotation moves them between factions at different lifecycle stages. A player who spends three chapters defending an empire's borders might rotate to a breakaway faction that formed from a revolt they failed to prevent — experiencing the consequences of their own failure from the other side.

**Technology loss** remains a valid mechanic but attaches to faction state, not world age. A faction whose stability and economic infrastructure have been degrading may trigger technology loss events — losing the ability to produce certain unit types, experiencing equipment unreliability, or forgetting maintenance procedures for complex systems. A thriving faction retains its capabilities regardless of how many centuries have passed. Technology loss is a symptom of decline, not of age.

### Civilizational Lifecycle — Mechanical Drivers

The world evolution described above is not scripted — it emerges from the interaction of existing simulation mechanics. This section maps the full lifecycle to the specific mechanical drivers that produce each phase. These phases describe the lifecycle of **individual factions**, not the game as a whole — multiple factions at different phases coexist simultaneously, and the world is always a mix of expanding, consolidating, fighting, and fragmenting factions.

**Phase 1 — Expansion.** Factions start with few regions and low budgets. Empty regions adjacent to faction territory are cheap to colonize (no resistance) and score well in attractiveness evaluations (maximum weakness, strategic position value from what they border). Budget is too low for confident attacks against defended regions. Result: factions expand into empty space rather than fighting each other. The world fills up. Colonized regions start with minimal field values and grow slowly through passive drift. The territorial adjacency bonus accelerates development for colonies near strong core regions, creating natural economic gradients — rich core, developing middle, bare frontier.

**Phase 2 — Consolidation.** Empty regions become scarce. Faction budgets have grown from accumulated economic output across multiple regions. Colonization opportunities dry up, so the agent's candidate pool increasingly contains only enemy-owned targets. Factions that expanded aggressively have more territory but weaker per-region fields (colonies haven't matured). Factions that expanded cautiously have fewer but stronger regions. Border friction applies where factions share borders, slowly elevating tension and dragging economy in contested frontier regions.

**Phase 3 — Conflict.** Budgets are now large enough to pass the attack confidence threshold against degraded frontier regions. Inter-faction attacks begin. The attack resolution formula favors attackers against weak frontiers. Conquered regions suffer tension spikes, economy disruption, and population loss. The conquering faction gains territory but also gains a high-tension, low-economy region that drains reinforcement budget to hold. Successful conquest attracts further aggression — neighboring factions see the newly conquered region's low military as an attractive target.

**Phase 4 — Overextension.** A faction that has conquered multiple regions faces compounding costs. Each conquered region has high tension, low economy, and low military. The faction must choose between reinforcing these regions (spreading budget thin) or accumulating for the next attack (leaving conquered territory vulnerable). Reinforcement has diminishing returns as regions approach their continuous capacity cap (derived from economy and population — see "Reinforcement diminishing returns" above), so even heavy spending can't make a conquered region with cratered economy as strong as a developed core region. Meanwhile, budget growth depends on total economic output across all owned regions — conquered regions sitting at the economy floor contribute almost nothing. The faction's effective budget growth per region *decreases* as it conquers more damaged territory. Administrative revolt pressure compounds the problem: each additional region increases the per-tick revolt probability quadratically, so a faction holding 8+ regions is constantly losing periphery to breakaway factions regardless of how well it manages tension.

**Phase 5 — Fragmentation.** Two independent revolt systems drive fragmentation. Conquered regions with sustained high tension cross revolt event thresholds, producing tension-triggered breakaway factions. Simultaneously, the administrative revolt system fires with increasing frequency as the faction holds more territory — these revolts are non-interruptible and produce breakaway factions regardless of regional tension levels. The combination is devastating for overextended empires: tension revolts hit the weakest regions while admin revolts can strike anywhere, including well-managed core territory. Each breakaway becomes a new hostile neighbor, adding border friction to adjacent regions and potentially pushing them closer to their own tension thresholds. This can cascade: a faction that overextended may lose multiple regions in rapid succession from both revolt systems firing simultaneously, fragmenting into several smaller factions. Each territorial loss reduces the parent faction's admin revolt pressure slightly (fewer regions = lower quadratic term), creating a natural self-correcting floor — the empire sheds territory until it reaches a sustainable size. The breakaway factions then operate as independent agents — they may fight each other, fight the parent faction, or be reconquered.

**Phase 6 — Equilibrium or collapse.** The simulation naturally tends toward one of several late-game states depending on the stochastic path: a dominant faction that managed overextension successfully (possible but requires favorable conditions), a fractured world of many small factions in shifting conflict, or a grinding multi-front war where no faction can achieve decisive advantage. The proportional tension decay mechanic prevents permanent runaway spirals — even high-tension regions eventually stabilize if external pressure stops. This means the world can reach dynamic equilibria where factions hold stable borders, punctuated by periodic wars when budget accumulation crosses attack thresholds again.

**Why this matters for the player.** The player experiences these phases from the inside — whichever faction they currently serve. In the expansion phase, missions are about establishing footholds. In the consolidation phase, missions involve border disputes and political maneuvering. In the conflict phase, the player commands forces in real wars with real stakes. In the overextension phase, the player is sent to hold crumbling frontiers or quell revolts in conquered territory. In the fragmentation phase, the player may be fighting former allies, choosing which fragments of their civilization to save, or leading a desperate defense of the last intact core region. Because the player can rotate between factions at different lifecycle stages, they experience the full range of these situations across a playthrough — not as a scripted progression, but as the world's natural churn viewed from different perspectives.

**Tuning the lifecycle.** The lifecycle's *shape* is emergent from the mechanics already designed. The *pacing* is tunable through existing parameters: conquest consequences control how costly expansion is, border friction rates control how fast contested borders degrade, revolt thresholds control when tension-driven overextension triggers fragmentation, administrative revolt scaling controls the hard ceiling on sustainable empire size, the continuous reinforcement cap weights control how tough regions are relative to their development level, and reinforcement efficiency controls how effectively factions can hold distant territory. If testing shows a faction can conquer everything without fragmenting, increase the admin revolt scaling rate or lower the inflection point. If fragmentation happens too fast, reduce them.

### Spatial Navigation

The player operates within the world spatially at two zoom levels connected by seamless camera transitions (no loading screens).

**Galaxy view (strategic scale).** Between missions, the player views the world as a 3D star map with orbital camera. Faction territory is shown through colored regions with defined borders. Military activity appears as rapid light flashes. The scroll narrates history while the galaxy evolves. See "Galaxy View — The Strategic Layer Between Missions" in the Sci-Fi Era section for the full design (era-specific presentation, era-agnostic concept).

**Tactical view (mission scale).** During missions, the player controls a standard RTS camera in the mission space. See "Camera and Player View" in Force and Combat Design.

**The transition between views is continuous** — the camera pulls back from tactical to galaxy, runs the time jump, then pushes in to the next mission's system. One unbroken shot. The galaxy view is a zoom level, not a separate screen. See "Seamless Transition — No Loading Screens" in the Sci-Fi Era section.

### Map Generation System — Spine + Gradient Hybrid

> **RESOLVED (updated v1.23).** All map generation design questions are decided. See below for the Strategic Layout Authoring Framework, gradient property vocabulary, archetype compatibility filters (formerly topology templates), fog of war, recon phase, canvas sizing, and simulation-to-gradient mappings.

Mission maps are procedurally generated using a **spine + gradient hybrid** system. The generator produces a small data seed. The engine interprets that seed into a full traversable 3D space. Small data in, big interpretation out.

**The Spine** is a graph of waypoints that defines the map's strategic topology — where the objectives are, where the chokepoints are, how different areas connect, where the player starts, where enemies come from. A typical mission spine is 10–30 nodes with edges between them. Each node has a position, a type tag, and a few property values. Each edge has a connection type. The spine guarantees that the map has deliberate tactical structure — flanking routes exist because the generator placed them, not by accident.

**The Gradient Fields** fill the space between and around the spine nodes with organic navigational texture. A gradient field is a continuous function over the map space — a set of field sources, each with a position, a property type, radius, intensity, and falloff curve. The engine samples these fields to place geometry, apply environmental effects, and determine terrain character. Where a gradient says "obstacle_density 0.7," the engine places dense obstacles appropriate to the theme. Where it says "sensor_interference 0.6," the engine applies a moderate visibility reduction. Gradient fields overlap and combine naturally, producing organic terrain with no grid artifacts and no hard boundaries between zones.

#### Gradient Property Vocabulary — Five Properties

The map generator uses five gradient property types. Each is a continuous field sampled at any map position to determine terrain character at that point. All are era-agnostic — the engine defines the gameplay effect, the theme pack determines visual presentation.

**`sensor_interference`** — reduces unit sensor radius at that position. Creates fog pockets, ambush opportunities, and information denial zones. Era examples: nebula (sci-fi), fog bank (naval), dense forest (land), sandstorm (desert).

**`elevation`** — continuous height field. Higher elevation provides range bonuses, vision bonuses, and defensive advantage. Vantage spine nodes anchor elevation gradient peaks — the slope around them is a continuous advantage curve, not a binary flag. Era examples: hills and mountains (land), orbital plane advantage (space), ridgelines (naval).

**`obstacle_density`** — blocks unit movement. High density creates walls, barriers, and terrain that must be navigated around. Distinct from cover — obstacles impede movement, cover provides protection without necessarily blocking paths.

**`cover_density`** — reduces incoming damage for units in that area. Distinct from obstacles — cover protects without necessarily blocking movement. Enables terrain like trenches, low walls, and debris fields that are easy to traverse but provide protection. Era examples: fortifications (land), debris clouds (space), reefs (naval).

**`layer_accessibility_mask`** — defines which vertical layers (see 2.5D Vertical Layers) are open at each map position. Binary per-layer — a layer is either accessible or blocked at a given point. Terrain features that block layers force units to navigate over (on higher layers) or around (on the blocked layers).

**[Future expansion:]** Additional gradient properties (damage_intensity, movement_drag, ability disruption zones) can be added as new property tags without engine changes. The gradient field system is extensible by design — each new property is a new field the engine samples, not a new system.

**The division of labor:** The spine handles the decisions a level designer would make — "there should be a chokepoint here and a flanking path there." The gradient fields handle what a terrain artist would do — "this area should feel dense and dangerous, this area should feel open and exposed." Together they produce maps that are both tactically sound and visually organic.

**Why this hybrid:** The spine alone leaves the space between waypoints empty and uninteresting. Gradient fields alone produce organic terrain but can't guarantee specific tactical structures (chokepoints, flanking corridors, defensible positions). The hybrid solves both problems — the spine provides structure, the gradients provide texture.

#### Spine Node Type Vocabulary

Nine abstract node types define the tactical vocabulary for map generation. All are era-agnostic — the engine places them as abstract gameplay markers, the theme pack determines visual presentation.

**Objective** — a location the player must interact with to complete the mission. Defend this, capture this, reach this, extract from this. The mission archetype determines what the objective means. Every map has at least one.

**Staging** — a relatively safe area where the player starts or regroups. Usually near the player's entry point. Lower hazard density, defensible approaches. The recon phase starts focused here.

**Transit** — a connection area between more important nodes. Not a destination, a path. Can be open (fast movement, exposed) or constrained (slow but covered). Transit nodes define the map's circulation.

**Chokepoint** — a narrow passage between areas. Forces funnel through. Defensible from one side, dangerous to push through. The tactical structure that makes positioning matter.

**Flank route** — an alternate path bypassing a chokepoint or main approach. Longer, possibly hazardous, but avoids the obvious route. Rewards the player who reads the map and sends Strike units the long way around. Generation rules require at least one flank route per chokepoint to prevent pure-grind maps.

**Vantage** — an elevated or advantageous position. Units here get a combat bonus (range, damage, visibility). Controlling a vantage point is a positioning objective within the larger mission. Must be contestable (reachable by both sides) — never pre-owned by one side.

**Hazard zone anchor** — a node that anchors a gradient hazard field. Defines where the hazard is centered; the gradient defines falloff. Not a destination — a spatial anchor for environmental danger.

**Spawn point** — where enemy forces enter the map. Can be at the edge (enemies approach from outside) or at a node (enemies pre-positioned). Multiple spawn points create multi-vector threats.

**Extraction** — where the player needs to get something out. Different from an objective — the objective might be "retrieve the asset," the extraction point is "bring it here." Creates two-phase mission structure.

#### Generation Pipeline

The map generation pipeline transforms mission context into a unique, playable map seed in four stages.

**Stage 1 — Inputs.** The generation script receives: the **mission archetype** (which compatibility filters to apply), the **region state** (simulation field values for the mission region — drives simulation-flavored map character), **library hints** (optional per-archetype map modifiers from the AI-generated content library — small data packets that add specific flavor, e.g. "narrow canyon approach" or "debris-heavy area"), and a **random seed** (ensures reproducibility for replays and bug reports).

**Stage 2 — Layout selection and instantiation.** The generation script selects and instantiates a strategic layout from the shared library.

1. **Runs the archetype compatibility filter.** The mission archetype's compatibility filter — a structural requirements checklist (e.g., "at least 2 chokepoints, at least 1 flank route, central defensive position, enemy approach from multiple vectors") — is evaluated against every layout in the Strategic Layout Library. All layouts that satisfy the filter enter the candidate pool. Library hints can bias selection toward layouts with specific characteristics.

2. **Selects a layout.** One layout is selected from the candidate pool (weighted random, with library hints as optional bias). The selected layout provides the authored strategic arrangement: zone positions, spatial relationships, chokepoint specifications, and the node placement guide.

3. **Instantiates zone positions at canvas scale.** The layout's relative coordinates (percentage-based) are mapped to the current canvas dimensions. Zone positions become concrete spine node positions. Spatial relationships (path length ratios, sightline connections, chokepoint width ratios) are preserved through the scaling. Minor positional jitter within zones provides organic variation without disrupting authored relationships.

4. **Connects nodes with edges** following the layout's connectivity spec and the archetype's structural requirements: minimum path count between staging and objective (never just one route), maximum dead-end count, flank routes must connect to at least two non-flank nodes.

5. **Places gradient field sources** based on instantiated node positions and library hints. Obstacle density gradients anchor around chokepoints. Sensor interference zones are placed according to the layout's ambush opportunity zones. Elevation gradients anchor around vantage nodes. Cover density gradients are placed in defensible positions and approach corridors. Layer accessibility masks create vertical terrain features.

6. **Applies simulation flavoring.** Region state modifies gradient intensities through a two-layer mapping. **Composite axis baselines:** low stability → higher sensor_interference, more hazard zone anchors, higher cover_density (fortified terrain); high stability → cleaner sightlines, fewer hazards. High capacity → lower obstacle_density, smoother terrain; low capacity → higher obstacles (debris, degradation). **Individual field deltas** (bounded, cannot overwhelm baselines): economy → reduces obstacle_density along paths, adds cover from infrastructure. Tension → boosts cover_density (fortification, barricades). Military → increases obstacle_density near defensive positions. Population → scales overall feature density. All mapping values are config parameters.

7. **Applies library hint modifiers.** The hint adds specific flavor: "large sensor interference zone in the center," "vantage node overlooking primary approach," "elevated ridge along the eastern flank." Small tweaks that make each instance feel unique within the authored structure.

**Stage 3 — Fairness evaluation.** The generated map seed is scored by an **algorithmic fairness evaluator** before being accepted. The evaluator computes: path count from player staging to objectives vs. enemy spawns to objectives, average travel time balance for both sides, vantage point accessibility balance, hazard zone distribution symmetry. If the score falls outside an acceptable range (config thresholds), the map is regenerated with a new random seed. The evaluator runs on top of **hard constraint rules** validated during layout authoring that prevent gross violations (e.g., all player approaches can't be blocked by hazards while enemy approaches are clear, vantage points must be reachable by both sides). The constraint rules handle 90% of fairness; the evaluator catches edge cases from canvas scaling and gradient interactions. Map seeds are tiny (~400–500 bytes) and layout instantiation is fast, so regenerating a few times is cheap.

**[Future consideration:]** A learned evaluator (neural network trained on playtested maps rated by fairness) can supplement or replace the algorithmic evaluator once sufficient playtest data exists. This is a post-launch evolution — the algorithmic evaluator is sufficient for launch.

**Stage 4 — Output.** The script outputs the map seed: spine (nodes + edges) and gradient field sources (position, type, radius, intensity, falloff). The engine interprets this into a traversable 3D space using the theme pack's visual vocabulary.

#### What Makes Each Mission Unique

Even within the same archetype, variety comes from four independent layers:

1. **Strategic layout selection** — the archetype's compatibility filter draws from a shared pool of 10–20 authored layouts, each providing a distinct tactical arrangement with guaranteed strategic depth
2. **Positional jitter and canvas scaling** — the same layout instantiated at different canvas sizes and with minor zone-level jitter produces visually distinct maps that share strategic bones
3. **Library hint selection** — dozens of per-archetype flavor modifiers from a large AI-generated pool bias layout selection and add gradient-level detail
4. **Simulation-driven flavoring** — region state produces different gradient intensities based on world history, so the same layout in a prosperous core region feels completely different from the same layout in a war-torn frontier

The combinatorial space (layout × canvas scale × library hint × simulation state × gradient texture) is large enough that effectively every map is unique while every map is guaranteed strategically sound by the authored layout structure and the fairness evaluator.

#### Generator Decides, Engine Interprets

The generator produces the spine and gradient fields as abstract gameplay data. The engine interprets that data into era-appropriate 3D geometry. Neither the spine nor the gradients contain any era-specific content.

The spine speaks in abstract types — "objective," "chokepoint," "vantage" — not "space station" or "fortress." The gradient fields speak in gameplay properties — "obstacle_density," "sensor_interference," "elevation," "cover_density" — not "asteroids" or "mountains." The theme pack maps abstract types to visual content: "obstacle_density 0.8" becomes a dense asteroid field in the sci-fi theme, a mountain pass in a land theme, a reef chain in a naval theme.

This is the same era-agnostic architecture the rest of the game uses. The map system never says "asteroid." It says "dense obstacle region." The theme pack decides what that looks like.

#### Continuous Movement and No Loading Screens

A single chapter may involve the player moving forces across a region or system. The map system supports this without loading screens. The spine and gradient fields define a continuous canvas — the player's forces move freely through rendered 3D space, and the engine streams geometry based on what's near the camera (standard LOD culling). There are no discrete zones to load, no boundaries to cross. The space is one continuous field from the player's perspective.

#### Moving Battlefields

The game specifies that engagements are not static arenas — the tactical space shifts during combat (see "Force and Combat Design — Moving Battlefields"). The spine + gradient system supports this naturally. Spine nodes can drift over time (the objective's position changes, the chokepoint narrows or widens). Gradient sources can move (the hazard zone drifts across the map, the obstacle density shifts as debris scatters). The result is smooth, continuous spatial change — the battlefield evolves under the player's feet without discontinuities.

#### Simulation State as Map Input

The simulation already tracks per-region state as continuous values (military strength, economic output, factional tension, population). These values feed into map generation parameters through the simulation flavoring step. A prosperous, stable region produces maps with more infrastructure and lower hazard intensity. A contested, declining region produces maps with debris, damaged structures, and higher hazard density. The map reflects the history of the region the player is operating in.

The specific simulation-to-gradient mappings use the two-layer approach described in the generation pipeline's simulation flavoring step: composite axes (stability, capacity) set baselines, individual fields (economy, tension, military, population) apply bounded deltas. The pipeline supports simulation flavoring from the start, but the generator can work with strategic layouts and library hints alone if simulation coupling is disabled.

#### Strategic Layout Authoring Framework

The map generation system's equivalent of the Chronicle Template Authoring Framework. A shared library of **10–20 hand-authored spatial blueprints** that define the tactical bone structure of mission maps. Each layout is a complete strategic arrangement — authored for depth, reusable across archetypes through compatibility tagging. The chronicle template pattern applied to spatial design: fixed authored structure with variable slots filled by context.

**What a layout contains:**

- **Zone positions** — relative coordinates as percentages of canvas dimensions (e.g., "objective zone: 50% x / 80% y," "primary chokepoint: 45% x / 50% y," "player staging: 50% x / 10% y"). Positions scale to any canvas size while preserving spatial relationships. Each zone maps to one or more of the 9 spine node types.
- **Spatial relationships** — the strategic DNA of the layout. Path length ratios between routes (e.g., "flank route is 1.4× the length of the direct approach"), sightline connections between zones (e.g., "vantage point has line of sight to objective but not to flank corridor"), and relative distance constraints (e.g., "chokepoint A and chokepoint B are far enough apart that a single force cannot cover both simultaneously").
- **Chokepoint specifications** — width as a ratio to standard unit formation width (e.g., "primary chokepoint: 2.0× formation width" allows two units abreast; "secondary chokepoint: 1.2× formation width" forces single file). Length, number of approach angles, and whether the chokepoint has adjacent cover or elevation.
- **Node placement guide** — which of the 9 spine node types go in which zones. A layout specifies "zone A is an objective, zone B is a chokepoint, zones C and D are spawn points from separate vectors." The archetype determines what those abstract types mean tactically.
- **Connectivity spec** — required edges between zones, minimum path count between key zones, dead-end allowances. The layout guarantees that its strategic structure works as a connected graph.

**What a layout does NOT contain:** gradient field values (those come from simulation flavoring), era-specific visuals (those come from the theme skin), absolute coordinates or fixed dimensions (those scale with canvas size), enemy AI behavior (that comes from the archetype spec), or difficulty modifiers (difficulty comes from force composition, time pressure, and complication frequency as specced elsewhere).

**Archetype compatibility filters.** Each mission archetype defines 2–3 compatibility filters (formerly called topology templates). A filter is a **structural requirements checklist** — the minimum set of spatial features the archetype needs to function. Example: Defensive Stand requires "at least 2 chokepoints between player staging and enemy approach, at least 1 flank route, player starts in a defensible position." The generator evaluates each layout in the library against the archetype's filters. Any layout that satisfies at least one filter enters the candidate pool for that mission.

A layout with "central defensive position, multiple radial approach corridors" satisfies filters for Defensive Stand, Multi-Front Defense, and Containment. A layout with "two forces converging on open ground with sparse cover" satisfies filters for Interception and Assault. Each layout is compatible with multiple archetypes; each archetype draws from multiple layouts. The cross-pollination is deliberate — it means the player encounters familiar strategic arrangements in unfamiliar tactical contexts, building map literacy over time.

**Layouts are data, not code** — the zone/relationship specification language is shared across all layouts and all archetypes. New layouts can be added to the library without engine changes. Layouts are validated against the fairness evaluator's hard constraints during authoring. The target count of 10–20 layouts provides each archetype with approximately 4–8 compatible options — enough variety for replay value, few enough for each layout to be hand-tuned for strategic depth.

**The design philosophy: authored bones, procedural skin.** The strategic arrangement — where chokepoints sit relative to the objective, how flanking routes compare in length to direct approaches, which positions have sightline advantage — is hand-authored because these are the decisions that create strategic depth. The organic terrain character — gradient textures, obstacle placement within zones, environmental hazard intensity — is procedural because this is what makes each instance feel like a real place rather than a board game. Simulation flavoring on top means the same layout in a prosperous core region plays differently from the same layout in a war-torn frontier. The player learns the strategic vocabulary of layouts over time (the way StarCraft players learn map archetypes) while the procedural and simulation layers ensure no two instances feel identical.

#### Fog of War — Multiplicative Sensor Radius

Each unit has a base sensor radius defining a circle of revealed map around it. The `sensor_interference` gradient at the unit's current position scales that radius downward: interference 0.0 = full base radius, interference 1.0 = zero visibility. The revealed area on the map is the union of all friendly units' sensor circles.

**Cross-layer visibility.** Units reveal only their own layer by default. Vantage spine nodes grant cross-layer visibility — a unit at a vantage position can see units on adjacent layers within a reduced sensor radius.

#### Recon Phase — Terrain Visibility, Enemy Hidden

During the recon phase (pre-mission free camera, no time pressure), the player sees all terrain features: elevation contours, cover and obstacle density, hazard zones, spine node types (chokepoints, flanking routes, objectives, extraction points), and layer accessibility. Enemy positions and spawn points are hidden.

When the player hits "Begin Mission," fog of war activates based on sensor coverage rules. The player retains knowledge of the terrain they studied but must discover enemy positions through sensor contact.

This requires no new simulation variables. Recon quality is uniform across all missions — the player always gets full terrain visibility regardless of world state.

#### Canvas Sizing — Archetype Base with Simulation Modifier

Each mission archetype has a base canvas size category (small, medium, large) that maps to a dimension range. The simulation state of the mission region applies a bounded modifier (±30% of base) derived from existing region fields (economy, military, tension, population).

The modifier direction is per-archetype — the archetype determines whether a wealthy/stable region means bigger or smaller canvas for its tactical situation. A defensive stand in a wealthy core region produces a larger canvas (more developed space to defend). A counterinsurgency in a high-tension region produces a larger canvas (insurgency is more widespread). A suppression mission against a newly formed breakaway produces a smaller, tighter canvas (quick decisive engagement).

#### Data Budget

A complete mission map seed is approximately 400–500 bytes of data:
- **Spine:** ~15 nodes × ~14 bytes each (position, type, properties, layer mask) + ~25 edges × ~4 bytes each = ~310 bytes
- **Gradients:** ~12 field sources × ~8 bytes each (position, type, radius, intensity, falloff) = ~96 bytes
- **Library hint reference + simulation flavoring metadata:** ~50 bytes

The engine turns ~450 bytes into an entire traversable 3D space. Seeds are small enough to log for replay and bug reports.

### Visual Style

Low-poly, Art of Rally aesthetic. Solo developer. 3D stylized.

### Sci-Fi Era — "The Settled Reach"

> **RESOLVED (v1.19).** This section defines the creative direction for the base game's sci-fi theme pack: the era identity, the three-tier visual progression, unit visual designs across tiers, tactical map structure assets, the galaxy view design, and the seamless transition system. This is theme pack content — it maps onto the engine's era-agnostic architecture through the standard skeleton/skin interface.

The base game ships with the sci-fi era. The era identity is **"The Settled Reach"** — a pocket of 20–30 solar systems that humanity has colonized over the past few centuries. FTL exists but is costly — transit between systems takes days to weeks, not hours. The frontier is genuinely remote. Communication is faster than travel but not instant. Each system is a meaningful place with its own character, not a dot on a galactic map. The scale is intimate enough that losing one system matters — it's not one star among ten thousand, it's a significant fraction of the civilization's territory.

**Why this scale.** 20–30 systems provides enough regions for the simulation to breathe — faction expansion into empty space, multi-faction border friction, fragmentation, breakaway factions all need room to develop. Later lifecycle stages expand significantly, with commensurate complexity growth over time. The contained scale leaves room for future sci-fi expansion packs at galactic scope — the Settled Reach is a pocket, not the whole galaxy. This also avoids "maxing out the range" on the first era, preserving commercial headroom for the skeleton/skin model.

**Why this feeling.** The Foundation parallel is strongest at this scale — a civilization big enough to have politics and momentum, small enough that one commander's mission matters. The 2.5D tactical layer showcases naturally in space combat (orbital planes, asteroid fields, system-edge encounters). The Asimov DNA is most at home here. The era identity is defined by what interstellar travel *feels like*, not by a calendar date — this provides creative freedom without accuracy constraints.

#### Three-Tier Visual Progression

The engine's tech tier system (3 tiers, uniform boundaries at 0–33/34–66/67–100, discrete jumps) maps onto the sci-fi era through a visual and narrative progression that tells a story about the civilization fielding it. Each tier is instantly readable at tactical zoom through silhouette and material language — consistent with the low-poly Art of Rally style where silhouette is the primary information channel.

**Tier 1 — "The Frontier."** What humanity looks like when it's building with what it has. Young colonies, recovering factions, breakaway states that lost access to parent supply chains. Technology works but is utilitarian. Ships are built for function — thick hulls, visible structural reinforcement, exposed systems. Nothing is elegant. Everything is legible — the engineering is on the surface. Visual language: boxy, angular silhouettes; visible paneling and seams; asymmetric where function demands it (bolted-on sensor arrays, weapon mounts that weren't part of the original design). Structures look assembled, not manufactured — modular sections joined together. Material palette: muted metallics (steel gray, gunmetal, industrial yellow/orange hazard markings). Faction color appears as painted hull markings — livery on a working vehicle. At tactical zoom: chunky, grounded, readable. A Tier 1 force looks like a construction fleet that someone armed.

**Tier 2 — "The Establishment."** What happens when a society has had a few generations of stability. Resources flow. Dedicated military shipyards exist. Ships are purpose-built, not repurposed from civilian hulls. The engineering has moved inside — smooth outer surfaces, integrated weapon systems, deliberate styling. Visual language: smoother silhouettes with deliberate curves; integrated systems (weapons are part of the hull, not bolted on); bilateral symmetry becomes dominant. Structures look manufactured — uniform surfaces, consistent proportions, ships from the same shipyard tradition. Material palette: cleaner metallics (polished silver, titanium white); faction color appears as integrated hull plating; accent lighting begins to appear (subtle glows along seam lines, controlled engine signatures). At tactical zoom: professional, cohesive, purposeful. A Tier 2 force looks like a real military.

**Tier 3 — "The Zenith."** Peak civilization. Centuries of compounding technological growth. Ships don't just work well — they work on principles Tier 1 engineers wouldn't recognize. The engineering has become invisible. Hulls are smooth to the point of abstraction. Weapons fire from surfaces with no visible emitter. Propulsion leaves exotic signatures. An uncanny quality — clearly made things, but the manufacturing process is opaque. Visual language: organic-geometric hybrid silhouettes; minimal visible surface detail (complexity is implied, not displayed); sweeping curves suggesting efficiency beyond human intuition. Slight asymmetries return but read as intentional optimization, not Tier 1's bolted-on pragmatism. The low-poly style becomes an asset — geometric abstraction reads as "technology so advanced it's become simple again." Material palette: luminous materials (surfaces that emit subtle light rather than just reflecting it); deep saturated faction colors integrated into the hull material as a property of the alloy; accent lighting is a primary visual element (energy signatures, field boundaries, drive emissions casting light on nearby geometry). At tactical zoom: alien-familiar. Clearly human-made, but from a humanity that's had centuries you haven't.

**The three-word readability test:** Tier 1 = boxy, seamed, matte. Tier 2 = smooth, integrated, polished. Tier 3 = flowing, luminous, abstract. If a unit's tier reads from these adjectives at tactical zoom distance on a low-poly model, the visual language is working.

**Tier regression — the visual story of collapse.** A faction dropping from Tier 3 to Tier 2 loses the luminous materials and organic forms — ships become conventional again. Dropping from Tier 2 to Tier 1 loses the integration and symmetry — things start looking improvised. The chronicle's "patched relics" line becomes visible: a faction that peaked at Tier 3 and fell to Tier 1 is fielding angular, seam-heavy ships in a world where their neighbors glow.

#### Cross-Era Unit Silhouette Archetypes

Each of the 6 unit types owns a **silhouette archetype** that persists across all eras. A Raider should read as "small, fast, forward-aggressive" whether it's a sci-fi interceptor craft, a Viking longship, or a WW2 fighter plane. A Bastion should read as "wide, dense, immovable" whether it's an armored space fortress, a Roman tower shield formation, or a WW2 bunker complex. The principle: the era provides the visual vocabulary, but the shape grammar is universal. A player who has learned to read the battlefield in one era can parse unit types in any other era at a glance.

The six silhouette archetypes (hard constraint for all era packs):

- **Raider:** Narrow, elongated, swept-back. The smallest unit. Reads as "fast and directional."
- **Interceptor:** Wider lateral profile than Raider, flatter. Reads as "coverage and presence."
- **Vanguard:** Front-heavy wedge or slab. Large. Reads as "mass and forward armor."
- **Warden:** Vertical or radial emphasis, central projection feature. Reads as "influence beyond its hull."
- **Bombard:** Longest silhouette, dominated by a single linear feature (the weapon axis). Reads as "range and focused power."
- **Bastion:** Widest and most compact. Wider than it is long. Reads as "density and immovability."

#### Sci-Fi Unit Designs — All 6 Types Across 3 Tiers

**STRIKE CATEGORY** (commanded as squads — multiple small models per group)

**Raider — "The Knife."** Core identity: small, fast-reading, forward-aggressive. Narrow profile, elongated proportions, everything swept back. At squad scale (3–5 models moving together), the group reads as a shoal of predators. The smallest unit model in the game. The Raider's weapon is always forward-facing and identifiable — the attack run fantasy (Surge, close distance, deliver burst damage) requires a visible "business end."

- *Tier 1:* Angular dart shape. Visible thruster clusters at the rear, oversized relative to the hull (raw thrust is how Tier 1 achieves speed). Weapon hardpoints visible on the nose or wing edges, clearly bolted on. A weaponized shuttle — fast for another reason and got repurposed. Exposed sensor dish or antenna. The squad looks like a scrambled patrol.
- *Tier 2:* Sleeker dart — same forward-aggressive proportions but with integrated engine housing, flush weapon mounts, unified hull surface. The swept-back geometry becomes deliberate rather than purely functional. Engine glow is cleaner. The squad looks like a formation — purpose-built interceptor craft designed as a set.
- *Tier 3:* Blade-like profile, razor-thin geometry. Energy concentrates visibly along leading edges and converges at the nose — the weapon is readable but elegant. Faint energy traces along the leading edges. The squad moves like a murmuration. Surge at Tier 3 is a streak of light — the ship is so fast during the burst that it reads as a luminous line rather than a moving object.

**Interceptor — "The Shield."** Core identity: wider, more stable silhouette than the Raider. Broader wingspan or lateral profile — "coverage area" rather than "attack vector." Slightly larger than the Raider but still a squad unit. Where the Raider's silhouette is a needle, the Interceptor's is a spread hand.

- *Tier 1:* Broad, flat-bodied craft with visible sensor arrays (the hardware is prominent because sensor coverage is the point). Stubby weapon mounts on wings or flanks. A patrol boat — wide scan profile, moderate armament, built to loiter and watch. The squad looks like a patrol screen.
- *Tier 2:* Sensor arrays integrate into the hull — the entire surface becomes the sensor. Wing geometry refined, smooth curves suggesting optimized scan patterns. Flush-integrated weapons. A distinctive "guardian" stance in the resting silhouette. The squad looks like a coordinated net.
- *Tier 3:* Distinction between sensor and hull dissolves. Broad, almost disc-like or manta-ray profile with luminous edges suggesting an active detection field extending beyond the physical hull. The squad barely looks like individual units — overlapping detection fields create a visible web. The Intercept ability (passive proximity trigger) feels visually inevitable at this tier.

**LINE CATEGORY** (commanded individually or in small groups)

**Vanguard — "The Wall."** Core identity: the biggest frontline silhouette. Reads as mass and presence. Broad and heavy-reading. The unit formations are built around. Front-heavy, armored-forward, with a "face" that says "come and get it." Individual unit, larger and more detailed model than Strike squad members.

- *Tier 1:* Blocky, heavily armored prow. Visible armor plating — layered panels added over time. Blunt, aggressive posture — a battering ram that shoots back. Weapons forward-mounted, short-to-medium range. Wedge or slab shape — maximum frontal cross-section (at Tier 1, more steel means more protection). Brace reads naturally — of course this barely-mobile thing plants itself.
- *Tier 2:* The slab refines into a proper warship. Armor is designed — smooth contoured plating with deliberate deflection angles. Weapon systems integrated into forward hull. Bilateral symmetry is strong — a product of proper shipyards. The visual step from Tier 1 is the difference between a fortified cargo hauler and a battlecruiser.
- *Tier 3:* Armor becomes hull — no distinction between structural and protective material. The wedge smooths into something organic but still front-heavy, still massive. Surfaces have the Tier 3 luminous quality but subdued — dense, heavy, absorbing rather than emitting. Brace at Tier 3 feels like the ship is becoming part of space itself.

**Warden — "The Hearth."** Core identity: the support ship. Distinctly different from the Vanguard — not a frontliner, a force multiplier. Visual language suggests emission, projection, an area of influence. Where the Vanguard is a wall, the Warden is a lighthouse. Slightly smaller than the Vanguard, more vertical or radial silhouette. Visible area-effect hardware — whatever projects Rally and passive buffs.

- *Tier 1:* Prominent central structure — antenna array, repair drone bay, or field projector dish. The support hardware is the most visible feature (dorsal turret position). Hull is practical, understated. A field hospital crossed with a communications relay. Visible drone bays or repair arms — Tier 1 fixes things by sending something physical to weld the hole shut.
- *Tier 2:* Support projection becomes elegant — integrated emitter rings or hull-embedded projector arrays instead of a bolted-on dish. Clear "broadcast" geometry (concentric rings, radial profile — "this ship's influence extends beyond its hull"). Rally looks like a coordinated system pulse.
- *Tier 3:* The most visually unique Tier 3 unit. The entire ship reads as a projection platform — hull secondary to the visible energy field surrounding it. Luminous aura extends beyond the physical model, giving the Warden a visual footprint larger than its actual geometry. Support effect visible as ambient light around nearby friendlies. Less a vessel, more a contained phenomenon.

**SIEGE CATEGORY** (commanded as individual high-value assets — largest models)

**Bombard — "The Hammer."** Core identity: the long-range killer. Reads as range and power from silhouette alone. Elongated profile with a clear "business end" — the weapon is the ship's defining feature. Largest model alongside the Bastion. The visual should make the player nervous when Raiders get close — powerful but exposed.

- *Tier 1:* Long chassis built around an oversized weapon. The gun/launcher/projector is visibly the biggest component — a hull built around a cannon. Structural reinforcement visible along the weapon axis (recoil bracing, power conduits, heat sinks). Rear section is all engine and power plant. Minimal armor — engineering budget went into the gun. Barrage at Tier 1 feels like the ship barely contains the weapon's output.
- *Tier 2:* Weapon integrates into a proper hull — still clearly the primary feature but housed in a designed platform. Longer, sleeker, weapon running along or through the central axis. Fire control integrated, weapon profile cleaner. A dedicated artillery platform designed by people who know artillery. Barrage at Tier 2 is precise and devastating — controlled power.
- *Tier 3:* Weapon and ship are indistinguishable — the entire hull is the weapon system. Smooth, tapered form with no visible barrel. Energy gathers along the hull surface and releases from the entire forward section. Less projectile fire, more directed phenomena. The Tier 3 Bombard is one of the most visually striking units — beautiful and terrifying. Barrage at Tier 3 is a spectacle — a distortion, something that bends the space it hits.

**Bastion — "The Mountain."** Core identity: the immovable anchor. Where the Bombard is long and specialized, the Bastion is broad, dense, and massive. Survives Strike flanking — looks like hitting it would hurt you more. Compact and heavy rather than elongated. The visual promise is durability. Fortify reads as a natural extension of what the ship already is.

- *Tier 1:* Squat, heavily-plated block. Thickest visible armor in the game. Multiple redundant systems visible (backup sensors, secondary weapons, emergency thrusters) — the design philosophy is survive through redundancy. Angular, faceted armor surfaces (deflection geometry designed by engineers who've been shot at). Wider than long. Fortify looks like deploying additional armor panels or shield generators — mechanical, physical.
- *Tier 2:* Redundancy becomes elegance — contoured integrated armor, internal systems, designed density. Still compact and wide but with the Tier 2 clean-line aesthetic. Weapons medium-range, hull-integrated, covering multiple firing arcs (armored everywhere — doesn't need to face its target). Fortify projects a visible defensive field.
- *Tier 3:* The densest-looking object in the game. Hull has the Tier 3 luminous quality but subdued and heavy — a deep glow reading as absorbed energy. Made of something that doesn't exist at lower tiers — too heavy, too dense, too present for its size. Compact silhouette becomes almost geometric — a polyhedron of impossible density. Fortify at Tier 3 is spatial — the area around the Bastion changes, as if imposing its own physics.

**Full roster readability check at each tier.** At Tier 1, the force looks like a frontier militia — angular, bolted-together, visibly mechanical. Faction color is painted on. At Tier 2, the force looks like a professional navy — smooth, integrated, purposeful. Faction color is built in. At Tier 3, the force looks like something from the next age — luminous, organic-geometric, subtly alien. Faction color is a material property. Cross-tier encounters produce immediate visual contrast that tells the story before combat begins.

#### Tactical Map Structures — Sci-Fi Theme Pack Assets

> **Clarification (added during Stage 8.5 / era-agnostic amendment reconciliation).** The single interactive structure type on the tactical map is the **settlement** — a population center that the player captures for unit production (see `bible_combat.md` "Tactical Reinforcement System"). Settlements have three tier variants matching the three-tier visual progression below. The settlement has its own silhouette archetype (compact, symmetric, clearly inhabited) distinct from all six unit silhouettes. The Station, Military Installation, and Resource Node visual categories described below persist as non-interactive visual dressing for other spine node types (objectives, staging areas, extraction points) but are distinct from the capturable settlement.

The spine + gradient map generation system places objects by abstract type. The sci-fi theme pack provides visual assets for these categories. **Only points of interest receive tier variants.** Obstacles, cover, and hazard zone visuals are universal across tiers — one asset set per category. Environmental fill receives light tier variation but leans primarily on the map engine.

**Obstacles** (maps to `obstacle_density` gradient — universal, no tier variants): Asteroid clusters, derelict ship hulls, mining debris, scaffold structures from abandoned construction. A mix of natural space objects and human-made industrial refuse. Boxy, angular, visibly material. The space reads as a frontier that's been lived in.

**Cover** (maps to `cover_density` gradient — universal, no tier variants): Debris fields (scrap metal clouds, fragmented hull sections, dense particulate zones), hastily deployed shield pylons, cargo container barricades. Cover is accidental — exists because the frontier is messy. Functional, effective.

**Hazard zones** (maps to `sensor_interference` gradient — universal, no tier variants): Nebula gas — visible particulate clouds with warm or amber tint. Dense, physical, obviously obscuring. At low-poly scale, soft geometric shapes suggesting gaseous volume.

**Points of interest** (spine nodes — objectives, staging, extraction — **three tier variants**):

- *Tier 1 structures:* Modular, visibly assembled stations — hab rings, docking arms, cargo bays bolted together over time. Grown organically through addition. Antenna arrays, solar panel clusters, docking pylons at odd angles. Military installations are blockier — armored, hardened. Resource nodes are industrial — mining rigs, processing platforms, visible pipes and tanks.
- *Tier 2 structures:* Designed stations — unified architecture, consistent hull language, planned expansion. Built from blueprints by a civilization with shipyard infrastructure. Symmetrical layouts, integrated systems. Military installations are proper fortifications. Resource nodes are efficient, automated, clean.
- *Tier 3 structures:* Monolithic stations — single-form, looking cast or grown rather than assembled. Smooth hulls with luminous accent lines. Scale is larger than Tier 2 for the same functional role (a Tier 3 outpost is the size of a Tier 1 major station). Military installations are subtle — defensive capability embedded in structures that don't look overtly military. Resource nodes are nearly invisible — small, automated, exotic sources.

**Environmental fill** (ambient non-interactive geometry — light tier variation): Scattered small asteroids, distant star fields, navigation beacons, comm relay satellites, background civilian vessel silhouettes. The space feels used. Tier variation is subtle: Tier 1 fill is industrial (working frontier with traffic), Tier 2 fill is administered (cleaner, organized, beacon networks), Tier 3 fill is sparse but significant (fewer objects but each carries visual weight, distant megastructure silhouettes on the skybox).

#### Galaxy View — The Strategic Layer Between Missions

The galaxy view is the player's primary experience between missions. It renders the Settled Reach as a **3D star map** that the player orbits like a tabletop. The camera orbits slowly and automatically during time jumps; the player can click-drag to override the auto-orbit at any time (mechanism exists from the previous fate space implementation).

**System nodes.** Each system is a luminous point positioned in 3D space. Node size communicates significance (population, economic weight). The player's capital or core systems are the brightest, largest points. A frontier colony is a small dim point at the edge. Uncolonized systems are dim neutral (gray or cool white).

**Faction territory.** Faction ownership reads through **colored regions with clearly defined borders** in 3D space — not just node color, but volumetric territory coloration that gives faction control a visible shape. When a system changes hands, the territory boundaries shift — the colored volume expands or contracts. Conquest reads as territory being nibbled away. Expansion reads as color blooming into neutral space.

The visualization uses a **metaball influence field** projected on the galactic plane. Each owned system emits a smooth radial influence field; same-faction fields are summed (metaball merge), producing organic blob-shaped territory regions with no internal boundaries between same-faction systems. The result is translucent faction-colored fill so the underlying galaxy particle structure remains visible through it. Fill is brightest near the territory outline and fades to transparent deeper inside. Neutral or unowned systems produce no territory fill — they show only as dim points in unclaimed void.

**Territory outlines** render as smooth glowing tubes at the metaball threshold isoline — bright faction-colored borders with a symmetric gaussian falloff that reads as a 3D pipe in the scene. Where two rival factions' territories approach each other, a gap-margin ensures they don't overlap — both outlines remain visible with dark space between them. When a system changes hands, the territory shape shifts (snap transition, masked by the accompanying combat flash VFX).

Fill opacity, influence radius, threshold, tube width, gap margin, and transition duration are tuning values. The metaball field is computed in a SubViewport and projected onto a plane quad in the 3D scene. At higher system counts (100+), the brute-force per-pixel computation can be replaced with a Jump Flood Algorithm (JFA) pipeline for the same visual output at O(log₂ n) cost — an implementation optimization, not a design change.

**Connections.** Trade routes and border connections rendered as faint lines between nodes in 3D. Border connections are solid lines in faction color. Trade routes are thinner or dashed. Connection lines provide depth cues during camera orbit (lines receding into space reinforce the 3D volume).

**Military activity visualization.** In regions with active conflict (attacks, border friction, military buildup), small rapid flashes of light pulse between or around the involved systems. Sped up to match the time jump's accelerated pace, these read as distant combat — brief, bright, gone. During a major conflict, a contested border region flickers with rapid exchanges. During peace, the space is calm. The player learns to read the galaxy's mood through the light.

The flashes are driven by **specific combat events** from the time jump's event log — attack events, conquest events, and revolt events. Each such event contributes a flash at the position of the involved system(s): attacks and conquests flash between the attacker's and defender's nodes, revolts flash at the revolting region's node. The simulation signals *what happened and where* as part of the keyframe message the renderer consumes (see the galaxy view data flow below); the renderer produces the visual effect itself using its particle system. Events drive occurrence and position; the renderer owns duration, intensity, color, and all visual tuning. Flash intensity and duration are tuning values; the simulation does not prescribe visual parameters.

**Ambient particle field.** The space between systems is filled with ambient particles — dust, distant stars, the fabric of the galaxy providing depth cues as the camera orbits. Not gameplay objects — visual atmosphere that makes the 3D volume feel inhabited and real. The particle structure is implemented as a scene (`scenes/shared/world_view/world_view_structure.tscn`) with ~5,200 particles across 12 tilted orbital rings, 6 radial inflow streams, ambient dust, a static starfield, and a central glow. This scene serves as the main menu background (at 70% opacity with autonomous camera choreography) and as the Settled Reach world view during inter-mission time jumps. In the main menu, the galaxy runs without region data — pure ambient atmosphere. During time jumps, the same scene is populated with region nodes, faction territory coloration, connections, and military flashes overlaid on the living galaxy. The particle structure remains visible through the territory visualization (per the low-opacity fill described above). Other space-themed eras may reuse or modify this scene; non-space eras (Roman provinces, 1980s globe) use entirely different renderer scenes coordinated through the same data and shell architecture.

**The pivot point.** For the Settled Reach era, the camera orbits around a specific section of the galaxy — a corner or pocket. The edges of the Reach fade into the ambient star field (systems at the frontier are at the visual boundary where settled space meets the unknown). Future eras or late-game expansion pull the camera back further, revealing more galaxy, the pivot shifting to encompass a larger volume.

**No tier progression on this view.** Tier information would be noise at this zoom level. The player gets tier information from the scroll narrative and from the tactical layer during missions. The galaxy view communicates faction geography and the feeling of time passing.

#### Seamless Transition — No Loading Screens

The transition from mission to galaxy view to next mission is one continuous camera movement, inspired by No Man's Sky's seamless planetary transitions. The player's screen never changes abruptly.

1. **Mission ends.** The tactical camera is in the mission space — ships, obstacles, the battlefield.
2. **Pull back.** The camera smoothly pulls back and up. The tactical space shrinks. The system the mission was in becomes a single point of light. The galaxy view renders full-screen during this pull-back — no split layout yet.
3. **Galaxy view emerges; narration begins.** Other systems fade into view around the mission system. The full Settled Reach is visible. The chronicle scroll panel slides in from the right and the galaxy viewport resizes to occupy the left ~60–65% of the screen. The scroll begins printing its first entry while the galaxy lives and breathes beside it.
4. **Time jump runs.** The galaxy animation is the master clock. The camera orbits slowly. Faction territory colors shift. Military flashes pulse. The scroll entries print in sequence, each queued to the keyframe tick range its events cover. The player watches history happen.
5. **Time jump ends; player-confirmed continuation.** When the last chronicle entry finishes printing, the galaxy settles into a slow ambient orbit and the scroll panel stays visible. The player reviews at their own pace — expanding entries to read their full form, or simply sitting with what just happened. The scroll panel's footer displays two actions: a primary **Proceed** action (triggers the push-in into the next mission) and a secondary **Exit to Main Menu** action (cleanly exits the run). Neither is on a countdown — the player continues or exits when ready. The player always has a clean exit at this chapter boundary.
6. **Push in.** On Proceed, the scroll panel slides back out, the next mission's target system is highlighted, and the camera begins pushing toward it. The galaxy shrinks. The target system grows. The tactical space materializes — new map, new forces, new mission. The briefing appears.

The galaxy view is not a separate screen — it is a zoom level. The player is always in the same space, at different scales.

**Chapter-boundary exits.** Chapter boundaries are the natural save-and-quit points for the game. Stage 11 treats the post-narration moment as a first-class exit opportunity: the player has just watched the time jump finish, has not yet been handed a new force, and the world state is at a clean boundary consistent with the simulation-state snapshot cadence (every time jump + every mission start and end). The Exit action at this moment cleanly terminates the run. Save serialization on exit is a separate system — its wiring to this exit point lands in a later stage — but the *offer* of a clean exit at this boundary is part of the transition design itself. A symmetric exit offer is made at the post-mission moment before the pull-back begins (the other natural boundary).

**Exit transition treatment.** Exit and Proceed are treated as thematically opposite transitions and animate differently. Proceed preserves continuity of motion — the scroll panel slides back out, the galaxy resumes full screen, and the camera pushes into the next system as one continuous move. Exit breaks continuity cleanly — the entire screen fades to black over a short duration, then the main menu loads. There is no scroll-panel slide-out on Exit, no camera choreography, no attempt to visually connect the in-run state to the main menu state. The design reason is that Proceed keeps the player inside the cycle, so motion continuity is right; Exit leaves the experience, so a clean cut is right.

#### Era Creation Template — Process for Designing Future Eras

> This framework was established during the design of the sci-fi era (v1.19) and documents the process for creating future era packs. Following this template ensures consistent quality and completeness across eras without reinventing the process each time.

**Layer 1 — Era identity.** Define the era's setting, spatial scale, narrative tone, and how it maps to the Foundation-inspired themes. Decide what distance and travel feel like. Constrain the scope to leave commercial headroom for future expansion.

**Layer 2 — Tier identity.** Define three tiers following the engine's 0–33/34–66/67–100 boundaries. Each tier needs: a civilization story (what stage of development it represents), a visual language (silhouette characteristics, surface detail level, symmetry), and a material palette (color, finish, lighting). The tiers must be instantly distinguishable at tactical zoom and must tell a regression story (dropping tiers should feel like loss).

**Layer 3 — Unit visual progression.** Apply the tier identity to all 6 unit types. Each unit must conform to its **cross-era silhouette archetype** (Raider = narrow/elongated, Interceptor = wide/flat, Vanguard = front-heavy wedge, Warden = radial/vertical, Bombard = longest/linear, Bastion = widest/compact). Design each unit at all three tiers, describing the tier-to-tier transformation. Verify that abilities read naturally at each tier.

**Layer 4 — Tactical map structures.** Define visual assets for the map generation system's abstract types. Only points of interest require tier variants. Obstacles, cover, and hazard zones get one universal asset set per era. Environmental fill gets light tier variation. Keep asset scope minimal — the map engine does most of the environmental work.

**Layer 5 — Strategic/galaxy view.** Define how the era's world looks at the strategic zoom level. This layer varies significantly by era — the sci-fi era uses a 3D star map; a land-based era would use a different spatial representation. Define faction territory visualization, ambient atmosphere, and any era-specific strategic view features.

**Layer 6 — Asset production spec.** Concrete 3D-Agent/Meshy prompts, polygon budgets, color palettes per tier, material direction. Reference images and silhouette guides. This is the final layer before production begins.

**The constraint:** Every era must map onto the same engine abstractions (6 unit types with fixed RPS relationships, spine + gradient maps with 5 property types, abstract structure types, tech tiers with uniform boundaries). The era creation template ensures the creative work stays within these constraints while maximizing visual and narrative variety.

---

### Tactical Spatial Model

> **RESOLVED (v2.02).** The tactical engine uses continuous 2D coordinates with discrete vertical layers. All spatial values are measured in "world units" (wu) — an abstract unit that scales with canvas dimensions.

**Coordinate system.** Unit position = `(x: float, y: float, layer: int)`. Continuous floats for x/y (no tile grid, no hex grid). Layers are integers (1 through N, typically 3–5 per map). The map is a rectangular play area defined by `(width, height)` in world units.

**Canvas dimensions.** Each mission archetype specifies a base canvas size (small, medium, large) with a ±30% simulation modifier (per the canvas sizing section above). The concrete dimensions:

| Canvas Size | Dimensions (world units) | Raider crossing time | Bastion crossing time |
|---|---|---|---|
| Small | 4,000 × 4,000 | ~27 sec | ~100 sec |
| Medium | 8,000 × 8,000 | ~53 sec | ~200 sec |
| Large | 12,000 × 12,000 | ~80 sec | ~300 sec |

Crossing times assume Raider speed 150 wu/sec and Bastion speed 40 wu/sec (Tier 2 baseline stats from `bible_combat.md`). The large canvas is deliberately vast — the bible's "Continuous Movement and No Loading Screens" section describes forces traversing large operational spaces over the course of a 30–60 minute mission, with battles happening en route. Moving a Bastion across a large canvas is a 5-minute commitment.

**Formation width reference.** The Strategic Layout Authoring Framework references chokepoint width as a ratio to "standard unit formation width." Standard formation width = 200 world units (approximately one Vanguard's attack range). A "2.0× formation width" chokepoint (400 wu) allows two Vanguards abreast; a "1.2× formation width" chokepoint (240 wu) forces single file.

---

### Cross-Layer Visibility — Combined Cone and Pulse Model

> **RESOLVED (v2.02).** Cross-layer detection uses two complementary systems: passive degraded detection (cone) and active full-range snapshots (pulse). This combines baseline awareness with proactive information warfare.

**Passive cone detection.** Units detect enemies on adjacent layers at degraded sensor range. Detection radius degrades with layer distance:
- Layer distance 1 (adjacent): sensor radius × 0.50
- Layer distance 2: sensor radius × 0.20
- Layer distance 3+: no passive detection

Vantage spine nodes double these factors and extend passive detection by one additional layer.

**Active sensor pulse.** Designated sensor-capable units can trigger a pulse that reveals all layers within a large radius for a short duration (2 seconds default). After the reveal expires, the information is gone — the player knows what was there, but the engine state returns to "not visible." Pulse has a cooldown (20 seconds default). This creates information warfare: the player must decide when to spend their pulse (scouting before committing forces vs. saving it for mid-engagement intel).

**Interaction with sensor interference.** Both cone detection and pulse are subject to the multiplicative sensor_interference reduction. A unit in a high-interference zone has reduced cone detection range and reduced pulse radius. Hiding in a nebula (space era) or dense forest (land era) degrades cross-layer detection as well as same-layer detection.

---

### Elevation in the Space Era — Sensor Advantage Only

> **RESOLVED (v2.02).** For the base sci-fi era ("The Settled Reach"), elevation provides sensor and visibility advantages only — no combat damage bonus. The `elevation` gradient affects sensor radius (higher elevation = bonus to sensor coverage) but does not modify damage dealt or received.

This is an **era-specific config setting**, not a code distinction. The engine supports elevation combat bonuses generically through a config flag (`ELEVATION_DAMAGE_BONUS_ENABLED`). The space era sets this to false. Future land-based eras (Roman, Medieval, etc.) set it to true, gaining the range, damage, and defensive bonuses that elevation provides on physical terrain. The engine code is identical — the config determines behavior.

**Rationale.** In space, "elevation" maps to orbital plane advantage — a higher orbital plane gives better sensor coverage over the volume below, but energy weapons and projectiles work identically regardless of relative orbital position. On land, height advantage is a fundamental military principle (range, gravity, visibility) and should be mechanically rewarded.
