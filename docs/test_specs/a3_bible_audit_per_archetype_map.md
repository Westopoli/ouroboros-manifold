# A3 — Bible Audit: Per-Archetype Tactical Map Composition

Date: 2026-05-20

## Headline finding

The bible **specifies per-archetype tactical map composition directives with detailed prose clarity** for all 10 archetypes. Each archetype's "Map character" section in `docs/bible_history/bible_2_00_missions.md` contains explicit language about chokepoints, cover placement, terrain features, approach vectors, defensive positions, and spatial topology. However, **map generation plumbing is incomplete**. Six of the 10 archetypes have no layout filter entry and no compatible layouts in the system, causing runtime fallback to an empty 4000×4000 field. The remaining four archetypes have partial layout coverage but insufficient cover-gradient sourcing to match the bible's language. The specification exists and is implementable; the implementation gap is in layout authoring and gradient sourcing, not in missing bible language.

## Per-archetype findings

| archetype | bible directive on map composition? | quote + source (file:line) | spec gap |
|---|---|---|---|
| defensive_stand | Y | "Defensible terrain. Chokepoints between enemy approach vectors and the objective. Prepared positions with cover. Multiple approach routes so the player must choose where to concentrate defense. The player starts in position; the enemy approaches." (docs/bible_history/bible_2_00_missions.md:74) | Layouts exist (01, 04, 05) but cover gradient sources only emit at `staging` and `flank_route` zones. Chokepoint and objective zones have no `cover_density` emission, leaving the defender's prepared line without cover despite explicit bible language. |
| siege_breaking | Y | "The player's region is in the center with degraded but functional infrastructure. Enemy positions ring the perimeter — fortified forward bases, patrol routes, supply interdiction points. Multiple enemy positions that can be tackled in any order, but the player can't hit them all simultaneously." (docs/bible_history/bible_2_00_missions.md:95) | **No layout tagged for siege_breaking.** Map generator finds no compatible layout, crashes to empty field fallback. Bible spec is clear; layout authoring + filter entry are missing. |
| reconquest | Y | "Former friendly territory — the map has infrastructure that the occupier is repurposing. Defensive positions exist but the enemy is partially set up (some fortified, some still being established). The population is partially sympathetic — represented mechanically by the occupier's garrison being thinner than a fully entrenched defender." (docs/bible_history/bible_2_00_missions.md:116) | **No layout tagged for reconquest.** No compatible layouts exist. Bible is explicit about partial fortification + infrastructure; map gen has no entry point. |
| assault | Y | "Enemy territory. The defender has prepared positions, fortified chokepoints, established infrastructure. The player starts outside and must fight inward. Multiple approach vectors with different risk/reward profiles — a frontal assault through the main chokepoint, a flanking route through difficult terrain, a fast Raider path that's exposed." (docs/bible_history/bible_2_00_missions.md:137) | Layouts exist (01, 02, 04, 05, 06) but chokepoint/objective zones have no cover-density sourcing. Bible specifies "prepared positions, fortified chokepoints" but the defender's line currently has zero cover gradient. Attacker rear has staging cover; defender's prepared positions do not. |
| suppression | Y | "Recently revolted territory. Infrastructure is partially damaged from the revolt chain. The enemy is dispersed — multiple small positions rather than one fortified base. The player must locate and engage scattered rebel forces. Sensor interference may be present (the rebels are hiding among the population)." (docs/bible_history/bible_2_00_missions.md:158) | **No layout tagged for suppression.** No compatible layouts. Bible clearly specifies dispersed positions + sensor interference + damaged infrastructure; map gen pathway does not exist. |
| multi_front_defense | Y | "Multiple enemy approach vectors from different directions. The player's position is central with defensive infrastructure radiating outward. Interior lines allow the player to shift forces between fronts — but movement takes time, creating windows of vulnerability. Chokepoints on each front that can be held by smaller forces, rewarding the player who reads which front is the main thrust and which is a feint." (docs/bible_history/bible_2_00_missions.md:179) | Layouts exist (03, 08) but neither has `staging` cover sources within tactical range of the radial defense lines. Cover blob is central (player rear); fronts are undefended cover-wise. Bible explicitly promises "defensive infrastructure radiating outward" with chokepoints — but cover gradient is not placed at those chokepoints. Worst cover coverage of all defended archetypes. |
| interception | Y | "Open terrain. No prepared positions for either side. The enemy force is in transit — moving across the map toward an exit point (representing the target region). The player must engage before the enemy reaches the exit. Terrain features provide tactical options (cover, elevation, sensor interference) but neither side has fortifications." (docs/bible_history/bible_2_00_missions.md:200) | **No filter entry in `ARCHETYPE_FILTERS`.** Map generator `KeyError`s immediately on archetype lookup. Bible is specific: open field with sparse cover features (not fortifications). Layout authoring + filter entry missing. |
| evacuation | Y | "Collapsing perimeter. The player starts in a defensive position with evacuation points behind them and enemy forces approaching from the front. The map compresses over time — the playable area effectively shrinks as the enemy advances and the player falls back. Extraction points at the rear of the map. Multiple things to protect (evacuation convoys, key infrastructure) that can't all be defended simultaneously, forcing triage." (docs/bible_history/bible_2_00_missions.md:221) | **No filter entry in `ARCHETYPE_FILTERS`.** Map generator `KeyError`s on lookup. Bible specifies fallback positions + extraction points + shrinking playable area; map gen has no pathway. |
| containment | Y | "Wide front with a defined boundary line. Multiple approach corridors the enemy can use to bypass or overwhelm player positions. The player must garrison multiple chokepoints simultaneously. Terrain features create natural defensive positions but with gaps between them. The enemy AI sends forces through multiple corridors, testing the player's deployment." (docs/bible_history/bible_2_00_missions.md:242) | **No filter entry in `ARCHETYPE_FILTERS`.** Map generator `KeyError`s. Bible specifies wide front topology with multiple chokepoints + gaps + approach corridors; map gen does not have an entry point. |
| counterinsurgency | Y | "The player's own territory. Infrastructure that the player wants to preserve. Insurgent forces are initially hidden — scattered across the map in sensor interference zones, behind cover, in defensible pockets. The player must use sensor coverage to locate them, then engage. Destroying infrastructure (objectives, cover positions) is mechanically possible but counterproductive — it worsens the region's economy and tension in the outcome resolver." (docs/bible_history/bible_2_00_missions.md:263) | Layout exists (07 only) but has no `cover_density` gradient sources except the central `staging` blob. Bible explicitly promises insurgents "hidden… behind cover, in defensible pockets" and notes cover positions as destructible infrastructure. Current layout has only `staging` cover + `hazard_zone_anchor` (sensor interference, not cover). Cover "pockets" missing. |

## Cross-cutting directives

**Bible layout specification language** (from `docs/bible_history/bible_2_00_world.md`):

- §"Strategic Layout Authoring Framework": *"A shared library of 10–20 hand-authored spatial blueprints that define the tactical bone structure of mission maps."* (docs/bible_history/bible_2_00_world.md:~210). Layouts are the unit of reusable map composition per archetype.

- §"Spine Node Types" and §"Gradient Property Vocabulary": *"The map generator uses five gradient property types. Each is a continuous field sampled at any map position to determine terrain character at that point… `cover_density` — reduces incoming damage for units in that area. Distinct from obstacles — cover protects without necessarily blocking movement. Enables terrain like trenches, low walls, and debris fields that are easy to traverse but provide protection."* (docs/bible_history/bible_2_00_world.md:~165-170).

- §"Stage 2 — Layout Selection and Instantiation" / subpoint 5: *"Places gradient field sources based on instantiated node positions and library hints. Obstacle density gradients anchor around chokepoints. Sensor interference zones are placed according to the layout's ambush opportunity zones. Elevation gradients anchor around vantage nodes. **Cover density gradients are placed in defensible positions and approach corridors.**"* (docs/bible_history/bible_2_00_world.md:~188, emphasis added). This is the cross-cutting directive: cover is **placed at defensible positions** (chokepoint, objective zones), not just at staging + flank.

- §"Archetype Compatibility Filters": *"Each mission archetype defines 2–3 compatibility filters (formerly called topology templates). A filter is a **structural requirements checklist** — the minimum set of spatial features the archetype needs to function."* (docs/bible_history/bible_2_00_world.md:~203). Every archetype must have at least one filter defined.

**Cover as a tactical element** (from `docs/bible_history/bible_2_00_combat.md`):

- `docs/bible_history/bible_2_00_combat.md:421`: damage formula `damage_per_attack = base_damage × category_multiplier × (1.0 - cover_density_at_position)`. Cover is mechanically live.

- `docs/bible_history/bible_2_00_combat.md:440`: *"**Cover.** `cover_density` gradient at target unit's position reduces incoming damage as a percentage. Cover_density 0.4 → unit takes 60% damage. Era-agnostic."*

- `docs/bible_history/bible_2_00_combat.md:578` (ambush state): *"hold at a hidden position (ideally in a sensor interference zone or behind cover)."* Enemy AI tactics assume cover exists.

**Mission-archetype cover expectations** from prose summary:
- **Defensive Stand**: cover at chokepoints + objective (defended position).
- **Siege Breaking**: cover at fortified perimeter positions (enemy side).
- **Reconquest**: cover at partial enemy fortifications + player approach routes.
- **Assault**: cover at objective/chokepoints (defender) and approach corridors (attacker).
- **Suppression**: scattered low-cover patches (dispersed rebel positions).
- **Multi-Front Defense**: cover at chokepoints on each front.
- **Interception**: sparse cover patches for tactical options (not fortifications).
- **Evacuation**: cover at fallback/extraction positions.
- **Containment**: cover at chokepoints + boundary defensive positions.
- **Counterinsurgency**: cover "pockets" where insurgents hide.

## Recommendation for D1 decision

**The bible is well-specified for all 10 archetypes.** Each archetype's tactical map character is described explicitly in `docs/bible_history/bible_2_00_missions.md:66–273` with language about chokepoints, cover, approach vectors, and spatial topology. The cross-cutting directive from `docs/bible_history/bible_2_00_world.md:188` ("Cover density gradients are placed in defensible positions and approach corridors") provides design intent that extends across all archetypes. The system design (`docs/bible_history/bible_2_00_world.md` Generation Pipeline) is implementable as-is.

**However, implementation is incomplete.** Four archetypes (siege_breaking, reconquest, suppression, interception/evacuation/containment) have no layout filter entries and ship as empty fields. The other six archetypes have partial layout coverage but insufficient cover-gradient sourcing — gradient sources currently emit only from `staging` and `flank_route` zones, leaving chokepoints and objective zones (where the bible promises defensible positions and prepared cover) without cover. This is an **implementation gap, not a specification gap**.

**Option B (medium scope) is implementer-actionable without Design Lane redesign.** Implementer can:
1. Add filter entries for the four missing archetypes, reusing or tagging existing layouts as stopgap.
2. Extend `gradient_placer.py` to emit `cover_density` sources at `chokepoint`, `objective`, and `hazard_zone_anchor` zones (per archetype coverage needs).
3. Tune gradient radius/intensity per archetype per bible guidance.

All 10 archetypes would then have map gen pathways and plausible cover placement aligned to bible prose. Option B does not require new layout authoring or Design Lane work — it closes the gaps using the existing infrastructure and the unambiguous bible spec.

**Option D (rewrite copy) is unnecessary.** The bible is clear and implementable. Copy rewriting would lose tactically-important guidance (defender positioning, chokepoint placement, approach vectors) and would signal that the system design is weaker than it is.

**Recommendation:** Pursue **Option B**. The spec is solid and the implementer has enough direction to execute without Design Lane redesign. The eventual Steam build would ship with all 10 archetypes coherent, bible-aligned for map generation and cover placement. Post-launch, if playtesting reveals asymmetries or fairness issues with layouts, that triggers a Design Lane loop for layout rebalancing (captured separately in `stage_11e_fairness_reconciliation_spec.md`). The bible does not need rework.
