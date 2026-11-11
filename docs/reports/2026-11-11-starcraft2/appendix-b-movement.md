# StarCraft II movement and orders (Legacy of the Void)

Research note, rev 2, 2026-11-11. Status words: VERIFIED = I read it on the named page (Liquipedia pages via its API through a summarising fetch tool, so quotes are the tool's extracts; Fandom pages read as raw wikitext). REPORTED = search snippet or secondary source. UNVERIFIED = memory. Liquipedia then rate-limited my IP (HTTP 429, CAPTCHA), so I stopped; TeamLiquid, SC2Mapster and archive.org stayed unreachable. No source gives Blizzard's exact radii or arrival thresholds.
Short names: LP = https://liquipedia.net/starcraft2/ ; FD = https://starcraft.fandom.com/ ; GUIDE-BASIC = https://news.blizzard.com/en-us/article/4552956/game-guide-basic-unit-controls ; GUIDE-CONTROL = https://news.blizzard.com/en-us/article/4552957/game-guide-unit-control

## 1. Orders
Short: Move ignores everything. Attack goes for one unit. Attack-move engages whatever it meets, kills it, and resumes toward the point. Hold Position fires in range and never moves. Stop cancels orders; the unit is then idle and still pursues if needed. Patrol is an attack-move along waypoints and back.
- Move: units "walk by towers, enemy units, or anything else that crosses their path", even when attacked. VERIFIED, GUIDE-BASIC.
- Attack on a unit: move toward and attack "until it or the enemy dies"; they move until they have "a clear shot". VERIFIED, GUIDE-BASIC / GUIDE-CONTROL.
- Attack-move: engages "any enemy units or buildings that come into their range"; takes "the next closest unit rather than chasing a single retreating unit"; ignores targets it cannot attack. VERIFIED, GUIDE-BASIC / GUIDE-CONTROL. LP Hotkeys: "move toward that location, engaging any enemy units they encounter along the way". VERIFIED, LP api.php?action=parse&page=Hotkeys.
- After the target dies: "attack that enemy until it is killed. They will repeat this until all encountered enemies are dead, then resume moving to their original destination." VERIFIED (fan wiki, general text), FD api.php?action=parse&page=Attack_move. A Liquipedia snippet adds that a-move units do not chase out-of-range enemies (REPORTED).
- Auto-target applies to Stop (idle), Hold Position, Patrol, Attack-Move and Follow Ally; not to Move, Attack Target or spells. VERIFIED, LP api.php?action=parse&page=Automatic_Targeting.
- Hold Position: "will not move to engage enemies in its sight range, even if it is being attacked by ranged fire" (VERIFIED, GUIDE-BASIC); "hold their ground instead of pursuing enemies that are moving out of range" (VERIFIED, LP Hotkeys). Units on it "will not move aside" for allies or your own units (VERIFIED, FD page Hold_position). Hold Position units can block a ramp (VERIFIED, LP Oddities).
- Stop: "A unit which has been stopped will still pursue enemies if necessary." VERIFIED, LP Hotkeys. Also GUIDE-BASIC.
- Patrol: back and forth between current position and destination, attacking hostiles it detects (VERIFIED, GUIDE-BASIC). Several waypoints; after the last it returns to origin and repeats (VERIFIED, LP Hotkeys). If attacked without a counter "the patrolling unit will run and lose its patrol route" (VERIFIED, LP Hotkeys).
- Move ends on arrival, a barrier or a new command. REPORTED (snippet of GUIDE-BASIC).
- Follow: the follower stops when its target dies. REPORTED, LP Micro_(StarCraft).

## 2. Pathfinding
Short: navmesh, A*, funnel smoothing, then a local steering layer for units. Pathfinding is engine code, not editable.
- "triangulated Navigation Mesh over which A* is run" (Anhalt, GDC 2011). REPORTED, https://github.com/lucho1/JumpPointSearch/blob/master/docs/README.md
- Paths run inside expanded vertices (radius-expanded), funnel at the end; dynamic obstacles rebuilt locally from a base mesh. REPORTED, https://www.jdxdev.com/blog/author/jdtec/ (the blogger's reading; the talk was "light on implementation details").
- "Pathfinding ... is handled by code, and will not be able to be edited within the map editor"; footprints, speed and unit size are editable. VERIFIED (Blizzard Q&A relayed on fan wiki), FD api.php?action=parse&page=StarCraft_II_Q&A_batches/40.
- Each unit gets its own A* path (sized, ledge-aware). VERIFIED as a claim of the paper, sourced to a private Anhalt email: https://www.sbgames.org/proceedings2021/ComputacaoFull/217610.pdf
- Patch 1.5: "Pathing has been adjusted. Units will once again take the most optimal route." VERIFIED, FD Patch_1.5 wikitext.
- Blocked path: detour vs stop. REPORTED only: "repath an alternate route" (anecdotal GameDev.net comment). A Hold Position unit blocks a ramp (above).
- Unreachable destination: UNVERIFIED. Nothing found; I could not read any page that states it.

## 3. Collision between units
Short: ground units do not overlap. Push priority decides who moves aside; enemies never push each other.
- Allied push priority 0 to 1 for Ultralisks: "now pushes allied units out of the way when moving". VERIFIED, LP Patch_5.0.14. Thor and Siege Tank raised "to assist bulky units in pathfinding when surrounded by many small friendly units". VERIFIED, LP Patch_5.0.15. So the data field is numeric, per unit, and an own moving unit with higher value shoves lower-valued own units.
- Enemies: "Fixed an issue where units could push opposing units when they shouldn't have been able to" (VERIFIED, FD Patch_1.2). The AlliancePushable setting "controls whether a player's units will move through another player's units, pushing them out of the way" (VERIFIED, LP Patch_1.3.0). Default enemy rule: REPORTED, "opposing players can not push each others' units at all" (SC2Mapster, search snippet).
- Hold Position units resist pushing: "Fixed an issue where you could push Hold Position units by Move/Hold Position spamming." VERIFIED, LP Patch_1.3.0. Push Priority "does not apply to units on hold position" (REPORTED, SC2Mapster).
- Idle (stopped) units yield; units holding, attacking, patrolling or moving still block. REPORTED, SC2Mapster thread 187903 (describes a mod, not stock values).
- Other pushers: Force Fields push units (VERIFIED, LP Patch_1.3.0); an Archon can be pushed while merging (VERIFIED, LP Oddities).
- Surround: UNVERIFIED.
- Air: "Flying units on patrol will ignore collision and stack up." VERIFIED, LP Oddities. Patch 1.3 fixed stacking air units with a queued stop. VERIFIED, FD Patch_1.3. Idle air separation uses a Separation Radius that only affects flyers with a non-zero radius. REPORTED, SC2Mapster.
- Structure collision radius for Archons 0.75 to 0.56 in 5.0.11. VERIFIED, LP search extract (Patch 5.0.11).

## 4. Group movement
Short: no formation speed. Each unit paths on its own and the group clumps on arrival.
- Move and a-move arrive "clumped up"; patrol keeps spacing. VERIFIED (player post), https://us.forums.blizzard.com/en/sc2/t/new-move-command-reposition/16303
- Units separate "due to enemy attacks, unit movement speed or terrain". VERIFIED, GUIDE-CONTROL.
- Magic box: a fan wiki says SC2 keeps air units spread in formation when engaged (VERIFIED, FD Magical_box; no sizes). Fixed box 195x195 px ground, 255x255 px air, tight-box rule: Brood War only (REPORTED, https://liquipedia.net/starcraft/Magic_Boxes). SC2 sizes and rule: UNVERIFIED.

## 5. Buildings and terrain
- Footprints "sectioned off a grid area where neither unit pathing nor building can occur". VERIFIED, https://s2editor-guides.readthedocs.io/New_Tutorials/04_Data_Editor/073_Footprints/
- A burrowed Zerg unit can block building placement. VERIFIED, LP Oddities. Own units move aside for a placed building: REPORTED (SC2Mapster).
- Ramps: ramp control funnels enemies "into a narrow corridor". VERIFIED, https://news.blizzard.com/en-us/article/4546768/game-guide-map-elements. Ramps as the only ground link: UNVERIFIED.

## 6. Arrival
Short: units stop near the point. No source gives the threshold. Spread attributed to collision/separation: REPORTED. UNVERIFIED for numbers.

## 7. High ground and vision
- "Ground Units on the low ground can not see ground units on the high ground." "Ground Units at the bottom of a ramp have reduced vision up the ramp." "Units on the high ground that attack will reveal their position (but not necessarily grant vision)." VERIFIED, LP api.php?action=parse&page=High_Ground_and_Low_Ground.
- "If the attacking units move halfway up the ramp, they get their full vision radius above the ramp. If the ramp is blocked at the bottom, the attacking units will not be able to target what is beyond the top ... they will be able to see snapshots of units that attack them." VERIFIED (Blizzard Q&A relayed on fan wiki), FD StarCraft_II_Q&A_batches/40.
- Air units on high ground are revealed only when they attack. VERIFIED, LP High Ground page.

## 8. Response when attacked
- Move ignores; attack-move engages; Stop engages and chases; Hold Position fires only. VERIFIED (GUIDE-BASIC).
- Auto-acquire detail: scan range is 5 or weapon range, whichever is greater; LotV ground units with long range get weapon range + 0.5. A target is kept until it is invalid, leaves range, or a higher-priority one enters weapon range. Priority: threats first, then attack target priority (20 for most units, 11 other buildings, 10 larva), then whether the primary weapon can hit it, then closest. VERIFIED, LP Automatic_Targeting.
- Workers default to "defensive" acquire and do not auto-acquire unless attack-moving. VERIFIED, LP Automatic_Targeting.
- Idle unit attacked by something it cannot see or reach: not documented. UNVERIFIED. The only related lines: targets must be in scan range; high-ground units cannot be fired back at without vision; a patrolling unit attacked without a counter runs.

## What is commonly misremembered
- Hold Position stops movement, not firing. VERIFIED.
- Stop is not passive: the unit pursues if needed. VERIFIED.
- Magic box is a Brood War term with measured sizes; SC2's version is unmeasured. VERIFIED / REPORTED.
- There is no formation speed. VERIFIED.
- "Attack-move ignores units it cannot attack" and "never chases" are not the same thing as "engages anything"; chase range is not documented. VERIFIED / UNVERIFIED.
- Enemy units are not pushed; only own and allied units, and only per push priority. VERIFIED.

## Table
| rule in one line | status | source |
|---|---|---|
| Move ignores enemies | VERIFIED | GUIDE-BASIC |
| Attack-move engages in range, then resumes to the point | VERIFIED | GUIDE-BASIC, FD Attack_move |
| Hold Position fires in range, never moves, resists pushing | VERIFIED | GUIDE-BASIC, LP Patch_1.3.0 |
| Stop engages and pursues | VERIFIED | LP Hotkeys |
| Patrol is an attack-move cycle, flees if attacked without counter | VERIFIED | GUIDE-BASIC, LP Hotkeys |
| Auto-target applies to idle, hold, patrol, a-move, follow; not move or attack | VERIFIED | LP Automatic_Targeting |
| Scan range 5 or weapon range (+0.5 for ground in LotV) | VERIFIED | LP Automatic_Targeting |
| Target priority: threat, ATP, weapon, closest | VERIFIED | LP Automatic_Targeting |
| Own moving units with higher push priority shove lower own units | VERIFIED | LP Patch_5.0.14, 5.0.15 |
| Enemy units are not pushed | VERIFIED (default rule REPORTED) | FD Patch_1.2, LP Patch_1.3.0 |
| Idle own units yield to moving own units | REPORTED | SC2Mapster 187903 |
| Air units on patrol stack | VERIFIED | LP Oddities |
| Move and a-move clump on arrival | VERIFIED (player post) | Blizzard forum 16303 |
| SC2 magic box: size and rule | UNVERIFIED | none |
| Navmesh + A* + funnel + local steering | REPORTED | JumpPointSearch README, jdxdev |
| Pathfinding is engine code | VERIFIED | FD Q&A batches/40 |
| Footprints block ground pathing | VERIFIED | s2editor-guides |
| Low ground cannot see high ground; ramp vision partial | VERIFIED | LP High_Ground_and_Low_Ground |
| Halfway up a ramp full vision radius above the ramp | VERIFIED | FD Q&A batches/40 |
| Idle unit attacked by an unseen or unreachable attacker | UNVERIFIED | none |
| Unreachable destination | UNVERIFIED | none |
| Blocked path: detour or stop | REPORTED | gamedev.net comment |
| Arrival threshold and spread radius | UNVERIFIED | none |
| Surround behaviour; ramps as the only ground link | UNVERIFIED | none |
