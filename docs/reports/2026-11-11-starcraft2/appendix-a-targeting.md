# StarCraft II (LotV) targeting rules: sourced notes

Method: Liquipedia pages were read as wikitext through its MediaWiki API (HTML pages and sc2mapster return 403). The API then rate-limited me, so Range, Attack-Move and Hold Position pages were not read. VERIFIED = I read it on the named page (LP = Liquipedia). REPORTED = secondary or search snippet. UNVERIFIED = no source read. SC2Mapster wiki (wiki.gg) is community editor documentation: it shows a field exists, not measured behaviour. No numeric leash, flee distance or re-scan interval was found.

## 1. Acquisition
Short answer: weapon range plus a scan bonus, never sight range. Default scan range is the greater of 5 or weapon range; LotV raised it for most ground units to weapon range + 0.5 (5 for short-range units). The scan applies equally to idle, hold-position, patrol and attack-move; no per-order distance exists.
- VERIFIED: "A unit (or building) considers all valid targets within the Scan Range of its weapons. The default Scan Range of most units is 5 or Weapon Range, whichever is greater. In Legacy of the Void, the minimum scan range of most ground units was changed to Weapon Range + 0.5 (remaining at 5 for low-range units), except for the Thor's High-Impact Payload Anti-Air weapon, static defence buildings, and the Siege Tank's Siege Mode weapon." https://liquipedia.net/starcraft2/Automatic_Targeting
- VERIFIED: the page governs Stop (idle), Hold Position, Patrol, Attack-Move, Follow Ally; not Move, Attack Target or abilities. Same URL.
- VERIFIED (editor docs): Minimum Scan Range matters only above weapon range; "Acquire Scan Filters: ... acquire as targets when outside the weapon range". https://sc2mapster.wiki.gg/wiki/Data/Weapons/Legacy
- VERIFIED: Hold Position "will attack enemy units if they're in range, but won't chase after them". https://liquipedia.net/starcraft2/Micro_(StarCraft)
- So an idle ranged unit that sees an enemy inside scan range but outside weapon range walks toward it (the wiki text implies it; the Automatic Targeting examples show attack-moving Thors stopping once a target is in range). A target beyond scan range is ignored even if visible: UNVERIFIED as a direct statement.

## 2. Choice among candidates
Short answer: threat, then ATP, then weapon preference, then (only if no previous target) closest.
- VERIFIED (Automatic Targeting): criteria "from most to least important: 1. Which targets are threats to me? 2. Highest Attack Target Priority (ATP)? 3. Which targets allow me to use my primary weapon? 4. Only if I lost my previous target: Which target is the closest?" Later criteria apply only among equals.
- VERIFIED: threat = target has a weapon that can legally hit the chooser, or the type carries "Always a Threat to Attackers" (High Templar, Oracle, Disruptor, Widow Mine, Raven, unburrowed Lurker, Infestor, Swarm Host, Viper).
- VERIFIED: ATP 20 for nearly all units and defensive buildings (Photon Cannon, filled Bunker, Planetary Fortress, rooted Spine); 19 for Interceptor, unburrowed Widow Mine, uprooted Spine, Spore, Missile Turret, empty Bunker; 11 for other buildings; 10 for Cocoons and Larva; 0 for Infested Terran Egg.
- VERIFIED: closest-target exceptions: Hellbat, Thor, Battlecruiser, Ultralisk pick least turning; Colossus, Immortal, unsieged Tank pick closest to their previous target.
- VERIFIED: Workers are "defensive": they do not auto-acquire and are not threats, until attack-moving; a repairing SCV inherits its target's threat and ATP. Facing and current damage: not a factor beyond the angle exceptions.

## 3. Keeping a target
Short answer: sticky. A target is kept until it is invalid, leaves weapon range, or a more important target (criteria 1 to 3) appears. A nearer equal target never swaps it.
- VERIFIED: "Once a target is chosen, it will remain the target until it ceases being a valid target (e.g., dies, becomes invisible, or goes up a ramp), leaves the weapon range or a higher-priority target enters the weapon range." The criterion-4 text says the higher-priority target enters Scan Range; the page is inconsistent on range versus scan range.
- VERIFIED: explicit orders: Attack Target is outside Automatic Targeting; a unit attacking the highest-priority target on an explicit attack keeps it through a Stop command. AI players treat workers as ATP 10 ("Override Target Priority").
- Re-evaluation interval: UNVERIFIED. Editor docs only say "Continuous Scan ... scans more frequently".

## 4. Chasing
Short answer: Stop (idle) chases attackers; Hold Position never moves; leash exists but the number is not documented.
- VERIFIED (Blizzard): "The Stop command ensures that your units will engage and chase enemies attacking them." Hold Position units do not follow retreaters. https://news.blizzard.com/en-us/article/4552956/game-guide-basic-unit-controls
- VERIFIED (editor docs): Acquire Leash Radius: "When the unit is idle this field determines how far the unit will chase an acquired target" before giving up and returning to the original point; Acquire Leash Reset Radius governs new acquisition. https://sc2mapster.wiki.gg/wiki/Data/Units
- REPORTED (2010 forum): an idle marine chased an Overlord, then returned to its spot. https://tl.net/forum/sc2-strategy/145588-difference-between-stop-hold-position-move
- Attack-move resumption: LP says units "move to the designated location, attacking every enemy on their way" (VERIFIED, Micro); leash and resume details UNVERIFIED.

## 5. Being hit
Short answer: Stop makes fighters fight back and non-fighters flee; Hold Position does neither.
- VERIFIED (Micro): Stop: "When an enemy is in range or attacks them they will either flee (non-fighting units) or fight back (fighting units)." Hold Position: "Nor will they move when under attack."
- VERIFIED (editor docs): unit field Response has Acquire (return fire) and Flee; weapon field Acquire Call For Help Filters alerts nearby units.
- VERIFIED (Blizzard): attack-move units "will not react to any units that they are unable to attack."
- Cloaked or unseen attackers, and flee distance: UNVERIFIED.

## 6. Moving and shooting
Short answer: each weapon sets Allowed Movement; default Legacy weapons stop to fire.
- VERIFIED (editor docs): Allowed Movement None "must stop moving to fire", Moving, Slowing; Legacy weapon "prefers to stand still while it is firing"; Strafe "constantly moving forward while firing". Fields: Damage Point, Preswing, Backswing, Period, Random Delay. https://sc2mapster.wiki.gg/wiki/Data/Weapons/Legacy
- Named units firing on the move: UNVERIFIED, none listed.
- VERIFIED (also Hydralisk damage point cut 0.15 to 0.1 in Patch 5.0.11): Stutter Step is "ordered to move right as its attack animation starts ... deal damage but instantly start moving again"; units with fast fire versus acceleration, such as the Hydralisk, do not benefit. https://liquipedia.net/starcraft2/Stutter_Step

## 7. Line of fire
- VERIFIED (editor docs): flag "Use Line Of Sight": vision is "blocked by doodads, cliffs and units that block vision". Body-blocking of projectiles: UNVERIFIED.
- VERIFIED (High Ground): low-ground units cannot counterattack without vision. Explicit order on an unseen target: UNVERIFIED.

## 8. High ground
- VERIFIED: "Any Unit on high ground can see any unit on the low ground. ... Ground Units on the low ground can not see ground units on the high ground ... can only see air units ... if the air unit has attacked them. ... Units on the high ground that attack will reveal their position (but not necessarily grant vision)." Vision comes from air units, Colossus, Xel'Naga Tower, Scan or a unit on the high ground. https://liquipedia.net/starcraft2/High_Ground_and_Low_Ground
- REPORTED (TL 2013 quoting a Browder interview): miss chance removed: "we do not like chance elements". https://tl.net/forum/starcraft-2-hots/394845-another-look-at-high-ground-advantage

## What is commonly misremembered
- "Units shoot the closest enemy": closest is the last tiebreak, and only when no previous target.
- "Scan range is 5 or sight": LotV made it weapon range + 0.5 for most ground units.
- "SC2 high ground has a miss chance": removed (REPORTED).
- "Leash is 14": that is the Carrier interceptor leash (REPORTED).

## Rules in one line

| rule | status | source |
|---|---|---|
| Scan range = max(5, weapon range); most ground units weapon range + 0.5 in LotV | VERIFIED | LP Automatic Targeting, Patch 2.5.0 |
| Same scan rule for idle, hold, patrol, attack-move | VERIFIED (governed orders listed, no per-order number) | LP Automatic Targeting |
| Choice: threat, ATP, primary weapon, closest only if no previous target | VERIFIED | LP Automatic Targeting |
| ATP 20 units and defences, 19 and 11 for others | VERIFIED | LP Automatic Targeting |
| Target kept until invalid, out of range, or more important target | VERIFIED | LP Automatic Targeting |
| Explicit attack keeps target through Stop | VERIFIED | LP Automatic Targeting |
| Re-evaluation interval | UNVERIFIED | none |
| Idle chase limited by Acquire Leash Radius, returns to origin | VERIFIED (field) | SC2Mapster Data/Units |
| Leash distance value | UNVERIFIED | none |
| Hold Position never chases or moves | VERIFIED | LP Micro |
| Stop chases attackers | VERIFIED | Blizzard guide |
| Idle fighters fight back, non-fighters flee | VERIFIED | LP Micro |
| Legacy weapons stop to fire | VERIFIED (field) | SC2Mapster Weapons/Legacy |
| Vision blocked by cliffs, doodads, vision blockers | VERIFIED (flag) | SC2Mapster Data/Units |
| Projectiles blocked by bodies | UNVERIFIED | none |
| No targeting up cliff without vision; attacking reveals | VERIFIED | LP High Ground |
| High-ground miss chance removed | REPORTED | TL 394845 |
