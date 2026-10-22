# Batch C: the open design flags, in plain words

Answer by key and letter, one per line, for example `Q-082-03: a` or `Q-082-03: c, plus your words`. The economy numbers (which you tune by feel), the flags the Architect already took, and the parked ones are not here; they are listed in the register extract. Fights are timed in seconds here (twenty steps of the fight clock make a second). A unit is about 23 world units across, so "a unit" below is a width, and a map canvas of 16,000 world units is about 700 units wide.

## 1. Beta blockers and the Now table

### 1. Map and scroll in step?
**Story.** "I watch the map change on the left while the scroll writes itself on the right, and I can stop and read." [S-069]
**Today.** Chronicle entries now print one at a time, as you ruled on 2026-10-13. If the map replay reaches the next entry's picture while the last entry is still printing, nothing says whether the map waits.
**The choice.** (a) The map holds until the entry has finished printing, so scroll and map stay in step like a book with pictures. (b) The map runs on at two steps a second and the scroll catches up, so an entry may describe a change the map already showed.
**Recommended.** None marked. The smaller change is (b); (a) would be a second piece of work.
<sub>key: Q-069-03</sub>

### 2. Which renderer is the look?
**Story.** "A 3D star map where territory glows, borders touch, and war flashes." [S-106]
**Today.** Under the shipped graphics renderer the translucent faction shells wash over the system dots, so the dot-visibility test sees 6 of 18 dots. Under the other renderer the test and the merge gate use, it passes.
**The choice.** (a) The shipped renderer is the look, and the test gains a run under it (its pass mark is yours). (b) The shell-over-dot wash is the approved look and the finding closes as accepted. (c) A lane B piece lowers shell opacity over the dots.
<sub>key: Q-B23b-01</sub>

### 3. Do Mac and Linux peers match?
**Story.** "Find a match, invite friends, get into the game." [S-144]
**Today.** Two peers must tick byte for byte alike, and the worry was that Mac and Linux machines round differently. The sim has its own sine and power code, and a build of the pipe under a Windows emulator already matched Linux exactly; Mac and native Windows are still to be run.
**The choice.** (a) Identical, nothing to do. (b) Only players on the same platform match in the beta. (c) Replace the maths with fully deterministic versions, a sim piece.
**Recommended.** None marked. The Architect leans to fixing the compiler settings and running the three-system probe, taking (c) only if it still differs.
<sub>key: Q-NET-05</sub>

### 4. Who hosts the next sitting?
**Story.** "Find a match, invite friends, get into the game." [S-144]
**Today.** A locked universe is a multiplayer campaign, a session is one sitting of it, and every peer holds an identical save. You answered a different question (which era comes next) and that rule is now in the bible; this one is who may host the next sitting. Your earlier words: "6: if not all players own the next universe, than that universe is skipped. We while loop down the line of eras checking if all players own each one. The one that every player owns is the one chosen for the next *transition* of time forward. If no players ever own one, than the time jump is cancelled and they proceed in the existing universe forever. Unless you mean something else by \"session\"."
**The choice.** (a) Any peer of the locked group may host. (b) Only the creator hosts. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-144-03</sub>

### 5. Who sets asteroid density?
**Story.** "In space each layer is a sheet of open and blocked space with real obstacles filling it, and the layers sit visibly apart." [S-246]
**Today.** A space mission needs an asteroid-field density, and the mockup uses one value (35). You said on 2026-10-13: "I'd like to see a prototype of the different options before locking in a decision." That prototype is queued.
**The choice.** (a) One default for every mission. (b) The region decides, tight fields in some and open in others, within a range. (c) The mission type decides.
<sub>key: Q-246-02</sub>

### 6. What happens when history loops?
**Story.** "A campaign moves chronologically through the eras I own." [S-148]
**Today.** The campaign walks through the eras in order, and at the end of the list it loops. Nothing says whether technology rescales again, whether characters and the ledger continue, whether the galaxy keeps its ownership, or how this relates to the deferred Ouroboros restart (a rebirth after ruins and amnesia).
**The choice.** (a) The loop works like any era boundary: the same rescale, characters continue, ledger and galaxy carry over unchanged. (b) The loop is the Ouroboros restart: ruins, amnesia, and that story designed here. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-148-04</sub>

### 7. When has an age been outgrown?
**Story.** "A campaign moves chronologically through the eras I own." [S-148]
**Today.** The Long Horizon (the chronicle noticing an age being outgrown) needs a measure of how far a civilization has outgrown its age, and a ceiling per age that makes the next time jump cross into the next era. The measure is not chosen.
**The choice.** (a) Technology reaches the era's top tier and holds there for two chapters. (b) A blend of technology, number of regions and economy, against a ceiling per age set in the era pack. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-148-05</sub>

### 8. Does the target marker show the enemy?
**Story.** "One primary objective I can see progressing, up to three secondary ones." [S-075]
**Today.** An eliminate-the-force objective needs a marker on the map, but fog hides the enemy. You said on 2026-10-07: "#3: C but remember we're not doing "match types" that don't involve a home base for both enemy and player, let's shelve this one for post-beta." The direction is a vague area.
**The choice.** (a) The marker shows the enemy's true centre. (b) It appears only once the enemy has been seen. (c) It shows a vague area.
<sub>key: Q-210-08</sub>

### 9. How is "you have the means" guaranteed?
**Story.** "The resources on the map fit the situation, tilted toward the better position, and I always have the means to do the job." [S-211]
**Today.** The mission generator shaves your force by up to 20 percent for a weak civilization and keeps a parity floor of 0.75, yet promises you can always win. You said: "#6: I want to explore what A would look like with more context without locking in the decision right now, architect weigh in." The Architect owes an options page on (a).
**The choice.** (a) The generator checks that the starting force plus reachable resources can reach the objective. (b) A floor on your share of the map's resources. (c) The parity floor alone.
<sub>key: Q-211-02</sub>

### 10. Building onto a building?
**Story.** "I place buildings where I choose and the city reshapes around them." [S-168]
**Today.** Placing a building over natural lots clears them and never refuses. Placing one that overlaps another placed building is refused today.
**The choice.** (a) Refuse the placement, as now. (b) The new building replaces the old one. (c) The two may overlap.
<sub>key: Q-168-06</sub>

### 11. How even must a city grow?
**Story.** "Cities rise from scaffolds in waves, climb cliffs and reshape around what I place, and dense districts slow units and give cover but always leave natural paths through." [S-193]
**Today.** On a flat open canvas the city's growth field should be mirror-symmetric about the core. Only the flip across the diagonal is exact in the port; mirrors and quarter turns differ by 1 to 3 fixed-point units. The test carries a draft of 4 units; this does not block anything.
**The choice.** (a) 4 fixed-point units (the draft). (b) Exact only, dropping the seven other symmetries. (c) 8 fixed-point units.
<sub>key: Q-193-08</sub>

### 12. Which region feeds a city's growth?
**Story.** "Cities rise from scaffolds in waves, climb cliffs and reshape around what I place, and dense districts slow units and give cover but always leave natural paths through." [S-193]
**Today.** At mission start the growth field reads an economy density from one region. An experiment found it read your first home-tier region (region 0, tier 2) rather than the region the mission is in (76, tier 1). Not blocking; nothing applies a fix yet.
**The choice.** (a) The mission's region. (b) Your home region. (c) The region holding the objective.
<sub>key: Q-193-09</sub>

### 13. Which key sets layer preference?
**Story.** "I give units a standing layer preference and they keep to it without me re-ordering at every obstacle." [S-003]
**Today.** Holding a modifier and pressing 1 to 5 should make a group prefer that layer when it moves on its own, but no modifier is named. Alt already means transfer to a layer and Ctrl means control groups. You said on 2026-10-13: "shift is still free."
**The choice.** (a) Shift plus the number sets the preference. (b) Drop the preference assignment from the beta and retire the rule.
<sub>key: Q-003-02</sub>

## 2. Combat framework

### 1. How does a big roster keep its shape?
**Story.** "A roster of 20 to 40 unit types per era, each with a job I can learn." [S-082]
**Today.** The Settled Reach (the space era) has six unit types in three soft rock-paper-scissors categories, with ordered speed, health and sensor rules and one area-attack type. With 20 to 40 types per era, it is open how those categories and orderings stretch, and whether the six types stay as roles every era fills.
**The choice.** (a) Every unit belongs to one of the three categories and one of the six roles; the orderings hold within each category. (b) Categories only, roles free, orderings hold within each category. (c) A free roster, balanced by the scoring check alone.
**Recommended.** (a).
<sub>key: Q-082-03</sub>

### 2. What says a roster is balanced?
**Story.** "A roster of 20 to 40 unit types per era, each with a job I can learn." [S-082]
**Today.** The per-unit power rating was deferred; an interim one scores health times damage over attack interval, set so a Vanguard (the basic line unit) is 100. Nothing yet says what scores a whole roster as balanced or who runs the check.
**The choice.** (a) The interim power formula plus headless matchup simulations, with a tolerance band per category. (b) The old bible's full rating, including traits and ability impact. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-082-04</sub>

### 3. How many units per launch era?
**Story.** "A roster of 20 to 40 unit types per era, each with a job I can learn." [S-082]
**Today.** The Settled Reach ships six types. It is open how many each launch era carries, and whether an era built around a named conflict gives each side its own roster, which would override the rule that unit profiles are the same in every era.
**The choice.** (a) Launch eras carry the six plus a shared set growing toward 20, identical across eras. (b) Each launch era carries its own 20 to 40, and profiles are no longer identical across eras. (c) Other: your words.
**Recommended.** (b).
<sub>key: Q-082-05</sub>

### 4. Fights run too long
**Story.** "Fights last long enough to read, reposition, and retreat." [S-085]
**Today.** A balanced 50-against-50 fight reliably runs 216 seconds, about 8 percent over the 150 to 200 second window, on every seed. The question is which lever brings it inside.
**The choice.** (a) Raise every unit's base damage by 20 percent. (b) Relax the upper bound to 225 seconds as a revised spec. (c) Cut every unit's health by 15 percent.
<sub>key: Q-085-01</sub>

### 5. Strike mirror fights drag
**Story.** "Fights last long enough to read, reposition, and retreat." [S-085]
**Today.** The rule wants Strike fights shorter than Line, shorter than Siege. Strike against Strike takes 124 seconds while Line against Line takes 30, because ranged Strike units keep their minimum distance and fire slowly.
**The choice.** (a) Give Strike a melee fallback when all enemies are inside minimum range: they close and hit for 1.5 times. (b) Halve Strike health so pure fights end faster. (c) The ordering applies to mixed forces only, not same-type mirrors.
<sub>key: Q-085-02</sub>

### 6. Where do fight-time targets come from?
**Story.** "Fights last long enough to read, reposition, and retreat." [S-085]
**Today.** The tests pin a 200-second cap (measured 204, with an invented force and layout) and Line-against-Line at 124 seconds against Siege-against-Siege at about 30. No bible text gave those numbers.
**The choice.** (a) Keep the tests' numbers and tune unit stats to them. (b) Retarget the tests to the measured values. (c) Drop the timing checks and keep the ordering claims.
<sub>key: Q-085-03</sub>

### 7. The default test army is invented
**Story.** "Fights last long enough to read, reposition, and retreat." [S-085]
**Today.** The standard balanced force (15, 10, 15, 5, 3 and 2 per 50) and the two-grid layout used by the combat runner were invented by the builder. Two non-combat unit types have no speed or health in the roster.
**The choice.** (a) Write that force and layout into the combat epic as the beta default. (b) Make the force a mission setting and leave layout to the map generator.
<sub>key: Q-085-04</sub>

### 8. Leash before or after damage?
**Story.** "Every unit on both sides flinches, obeys, then shoots the nearest thing in range." [S-087]
**Today.** An attack-moving unit stays within about 9 unit-widths (200 world units) of its anchor. Tested before damage, a unit with longer reach never shoots a target beyond that; tested after, it does. The plan is a switch the lab runs both ways, and you pick.
**The choice.** (a) Before damage, as the old Python. (b) After damage. (c) Decided from the lab's chart.
<sub>key: Q-087-01</sub>

### 9. Two units on one spot
**Story.** "Units route around terrain and flow around each other; nothing walks through anything." [S-097]
**Today.** You said on 2026-10-02 the Python's collision "was perfect" and should migrate. The Python shoves the lower-numbered unit the other way (minus x) by a thousand times the normal push, flinging it; the C version nudges it plus x by the normal push.
**The choice.** (a) Port the Python's collision but keep the normal-sized push, direction as the Python (minus x). (b) Port it exactly, fling included. (c) Keep the C rule as written (plus x).
**Recommended.** (a).
<sub>key: Q-097-02</sub>

### 10. Do obstacles push units away?
**Story.** "Units route around terrain and flow around each other; nothing walks through anything." [S-097]
**Today.** The rule says units are pushed away from obstacles but gives no strength or range, and the Python's version turns out to do nothing. Blocked cells already keep units out, and a unit found inside one is moved to the nearest open cell; nothing is built beyond that.
**The choice.** (a) Leave repulsion unbuilt; blocked cells alone keep units out. (b) A push proportional to density within a stated range, both numbers yours. (c) The Python's do-nothing version, documented.
<sub>key: Q-097-03</sub>

### 11. Can a force hold fire?
**Story.** "I can put units on guard at a post so a choke or a slope top holds without them running out." [S-208]
**Today.** A guard steps up to engage and returns to its post. Nothing lets you order a force to wait unseen and not shoot, so it is open whether an ambush needs that.
**The choice.** (a) A hold-fire setting on the guard stance. (b) A separate hold-fire order. (c) No hold fire; an ambush is made by going silent alone.
<sub>key: Q-208-01</sub>

### 12. What is a scout?
**Story.** "I ping a layer I choose at a place I choose and see it for a moment; whoever I ping learns roughly where I am." [S-162]
**Today.** Scouts stay, "less aggressively than the pinging, we'll play around with what we do based on what players like" (you, 2026-10-05). What a scout is, what it reveals, for how long, and in which eras is open.
**The choice.** (a) A free, slow, killable unit that sees normally. (b) A cast like the ping, with a longer cooldown and a smaller radius. (c) Decided after players try both.
<sub>key: Q-162-06</sub>

### 13. The land era's eyes
**Story.** "The land era has units that walk, so slopes and strongpoints at slopes decide where an army can go." [S-201]
**Today.** The land era needs a vision unit. You said on 2026-10-01: "the pinging should replace the seer, or make the seer really expensive", and on 2026-10-05: "a simple placeholder unit that's a scout is sufficient for now".
**The choice.** (a) A placeholder scout now (a Raider re-skin with longer sight and no weapon), with the seer designed alongside the land roster. (b) The seer now, expensive, as the 2026-10-01 words say. (c) Another: your words.
<sub>key: Q-201-02</sub>

### 14. Does higher ground still add sight?
**Story.** "An elevated position sees farther." [S-091]
**Today.** The elevation sensor bonus has tiers in steps of 0.25, but on land maps the height field now gives both elevation and the five layers (terraces of the land). The sign of the tier difference is unstated, and cross-layer vision is symmetric by layer distance.
**The choice.** (a) Drop the tiers; layers are the only elevation and the bonus goes. (b) Keep them, derived from the height field, with the bonus for the higher observer only (asymmetric vision, which you allowed only with a counter). (c) Keep them, with the bonus symmetric by tier difference.
<sub>key: Q-091-01</sub>

## 3. Era roster and packs

### 1. Name the land era and the roster
**Story.** "An era in space and an era on land to play, all one game." [S-147]
**Today.** The land era is Greek antiquity, built as the era named Greek; its setting, tone and scale are unwritten. The order of eras after the first two is only a brainstorm of twenty plus your spoken additions (World War I, the 2020s, Imperial China).
**The choice.** Open: your words. Name and brief the land era, write the roster in order, and mark each era earnable or purchase-only.
<sub>key: Q-147-01</sub>

### 2. Same map seeds in every era?
**Story.** "An era in space and an era on land to play, all one game." [S-147]
**Today.** One campaign seed makes one galaxy. It is open whether each era draws the same layouts from it or may weight layouts its own way.
**The choice.** (a) Identical seeds and layouts. (b) Eras may weight layouts.
<sub>key: Q-147-02</sub>

### 3. Names versus mechanics
**Story.** "A checklist of exactly what an era pack contains." [S-146]
**Today.** The bible says eras differ in names but share mechanics. Resource names, doctrine names and environmental troubles (weather and other hazards) sit on the line between the two.
**The choice.** (a) Names and troubles differ, mechanics identical. (b) All identical for the two launch eras. (c) You decide item by item.
<sub>key: Q-146-02</sub>

### 4. How is an era earned?
**Story.** "A fair price and the chance to earn expansions by playing." [S-149]
**Today.** Eras can be earned by play as well as bought. The condition for earning one is not set.
**The choice.** (a) Complete a 10-chapter campaign in the preceding era. (b) Reach Tier 3 in any campaign. (c) Other: your words.
<sub>key: Q-149-01</sub>

### 5. Which eras are purchase-only?
**Story.** "A fair price and the chance to earn expansions by playing." [S-149]
**Today.** Which eras are exclusive to purchase and which earnable is yours to say, as is the naming of the base three on the store.
**The choice.** Open: your words.
<sub>key: Q-149-02</sub>

### 6. What carries between eras?
**Story.** "Maps, civilizations, and era systems transfer between eras like skins." [S-150]
**Today.** Archetype weights and naming subsets transfer. What else counts as civilization content that moves is unsettled.
**The choice.** (a) Archetypes, names, colours. (b) Also unit skins per civilization. (c) Other: your words.
<sub>key: Q-150-01</sub>

### 7. What may an era change in production?
**Story.** "Eras that feel different." [S-151]
**Today.** The Climate of War (each era's own fog, pace and production rate) has a reinforcement rate that now means pace of production plus strongpoint reinforcement. Which economy values an era may set is open.
**The choice.** (a) Production pace only. (b) Pace and resource yields. (c) None until the economy is built.
<sub>key: Q-151-02</sub>

### 8. When the naming pool runs dry
**Story.** "People, places, units, and factions have names that sound like they belong together." [S-154]
**Today.** Names come from pools. What happens when a pool is exhausted is undecided.
**The choice.** (a) Reuse the oldest historical name. (b) Fall back to a numbered name. (c) Refuse and log the failure.
<sub>key: Q-155-01</sub>

### 9. How many pieces build a settlement?
**Story.** "A faction's technology tier shows in how its ships look, and shows loss when it falls." [S-133]
**Today.** Each era pack must supply building pieces for settlements, and the 3 to 6 structures named in the rules may be points of interest only. How many pieces per era is open, and the number is yours.
**The choice.** (a) A fixed small set per era. (b) A count range, like the polygon budgets. (c) Set together with the settlement generator.
<sub>key: Q-133-01</sub>

### 10. Polygon budget for workers and pieces
**Story.** "Every unit type has a shape I can read at a glance in any era." [S-132]
**Today.** Structures carry a polygon budget of 200 to 800, but workers and the many small pieces of a settlement have none. The numbers are yours.
**The choice.** (a) The same 200 to 800 as structures. (b) A lower range per piece. (c) You set them.
<sub>key: Q-236-02</sub>

## 4. Client HUD and screens

### 1. The sand table
**Story.** "I pull the camera back until the battle reads as a map and give groups move orders from there." [S-161]
**Today.** You said on 2026-09-23 you like the Dune-style sand table but want a prototype first: low resolution with large blocks for height, a grain-size dial from coarse to fine, and a 45-degree view with layers pulled apart so unit sets read. Also open is whether an always-visible corner glance survives once the minimap is replaced.
**The choice.** (a) Prototype it: block-resolution table, grain dial, and the 45-degree layered view; commit on your approval. (b) Ship the flat War Table first and the sand table later. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-103-05</sub>

### 2. How the map shows a group's layer
**Story.** "I pull the camera back until the battle reads as a map and give groups move orders from there." [S-161]
**Today.** From the map view you need to read which layer a group is on. You said: "I'd like to brainstorm additional options for indicating which layer specific units and unit groups are one, because the pin option is a good option but I don't think it has to be the only one. Mark further research needed." A group wholly on layer 3 is also open.
**The choice.** (a) Pins, tall, sunk or full rod, as in the sand table option. (b) Stacked icon slices, one per occupied layer. (c) Colour-banded icons keyed to the layer strip. (d) A research pass first.
**Recommended.** (d).
<sub>key: Q-103-06</sub>

### 3. Player-bound cameras
**Story.** "A free camera I manage myself, with the Angle Rack, the Layer Peel, and a flip key." [S-103]
**Today.** You asked for an idea to be recorded, not decided: the player binds keys to camera angles relative to a unit's forward direction, with a view that tracks it as it moves and a default non-following mode on a key. Everything about it would be adjustable. It is not a blocker.
**The choice.** (a) Keep the chosen camera (Angle Rack for preset angles, Layer Peel, flip key). (b) Replace the Angle Rack with player-bound tracking views. (c) Offer both.
<sub>key: Q-103-07</sub>

### 4. What loading screens show
**Story.** "A main menu that sets the tone and settings that cover the basics." [S-110]
**Today.** Loading screens will carry information the player would not otherwise see, in the chronicle's voice, with the content chosen before launch. There is no loading screen between a mission and the galaxy.
**The choice.** (a) Chronicle entries you have not read yet. (b) The Long Horizon's foreshadowing of the age being outgrown. (c) Lineage and legend fragments. (d) Decide before launch, after a mockup.
**Recommended.** (d).
<sub>key: Q-110-03</sub>

## 5. Enemy, difficulty, missions

### 1. When does the enemy rout?
**Story.** "Enemy forces advance, hold, patrol, ambush, or retreat, cautiously, aggressively, or in echelons." [S-120]
**Today.** The enemy script has "routed" and "retreating" conditions, but nothing says what moves a force from advancing or holding into a rout.
**The choice.** (a) Enemy health falls under 25 percent of its starting total. (b) Fewer than 30 percent of its starting units survive. (c) Each enemy unit routs on its own once its own health drops under 20 percent.
<sub>key: Q-120-02</sub>

### 2. How hard is each difficulty?
**Story.** "Hard mode gives me less to work with, never gives the enemy better units." [S-080]
**Today.** Difficulty compression (time width, resource generosity, odds of complications around 1 percent, and the ramp across generations) is a no-op until its values exist. You deferred it past the MVP on 2026-09-30.
**The choice.** (a) Easy gets 1.2 times the time and hard 0.85; generosity through parity only; complication odds 0.5, 1 and 1.5 percent; the ramp a fixed step per generation. (b) Other: your words.
**Recommended.** (a).
<sub>key: Q-080-03</sub>

### 3. How does a trouble travel?
**Story.** "My region's trouble travels across the map where both sides see it and shuts down what it passes over." [S-219]
**Today.** You said on 2026-10-06: "7: mark to be designed, I think it'd be cool if the player didn't see it coming." So its path is not shown ahead; its route, speed and whether fog hides it are still open.
**The choice.** (a) It ping-pongs or loops on a drift setting. (b) A one-way front across the map. (c) Other: your words.
<sub>key: Q-219-02</sub>

### 4. Which maps grow, which shrink?
**Story.** "Mission maps sized to the situation." [S-116]
**Today.** Map size is already set by the situation, within 30 percent either way of a base size. Which kinds of map lean toward the larger or smaller end is not.
**The choice.** (a) Open, aggressive layouts (Siege Field, Open Plains) lean large; defensive ones (Fortified Ridge, Narrow Pass) lean small; neutral ones draw from the middle. (b) All draw evenly across the band. (c) Each layout has an explicit bias setting.
<sub>key: Q-118-02</sub>

### 5. Urgency arithmetic does not reach 0.8
**Story.** "My missions come from real trouble in the galaxy, weighted toward where I belong and what I do best." [S-072]
**Today.** A rule says a region at stability 15, attacked by a neighbour at military 80, must score urgency at least 0.8. The weights as written reach 0.8 only if every field sits at zero; with the test's values the ceiling is about 0.75.
**The choice.** (a) The scenario includes an active revolt chain in the region (two revolt events add 0.12). (b) The threshold becomes 0.7. (c) The weights change, for example conflict weighted 0.5.
<sub>key: Q-072-02</sub>

## 6. Sim and chronicle bridge

### 1. What does technology do?
**Story.** "the economy and bases as a whole"
**Today.** You decided a mission's starting technology is derived, only slightly, from the simulation's technology level, with an era spanning a range such as 1 to 5 and a timed match rising one or two. You said: "what tech will do exactly is undecided, mark that as something that needs designing."
**The choice.** Open: to be designed.
<sub>key: Q-159-12</sub>

### 2. Does base damage survive a jump?
**Story.** "the economy and bases as a whole" (also the region fields and drift epic)
**Today.** Whether damage to a base persists across a time jump, and how fast it is rebuilt, depends on the situation. You said: "Depends on the situation, this is simulation work that is tbd".
**The choice.** Open: to be designed with the simulation.
<sub>key: Q-159-13</sub>

### 3. Does an occupied base get recorded?
**Story.** "What I did in a mission shows in the region when I come back." [S-220]
**Today.** A mission changes a region only through four field changes and, for a transfer band, ownership. When a base is occupied or the original main base is lost, nothing says whether the simulation records it.
**The choice.** (a) Nothing beyond the field changes and ownership already there. (b) The region record gains base state, a contract change counted against its 2,048-byte budget. (c) Recorded in the ledger and chronicle only.
<sub>key: Q-220-01</sub>

### 4. Where does a contested populace end up?
**Story.** "What I did in a mission shows in the region when I come back." [S-220]
**Today.** A populace contested during a mission has no defined landing in the simulation.
**The choice.** (a) It moves the region's population or tension. (b) It changes the region's ownership. (c) Nowhere; it is mission-only.
<sub>key: Q-220-02</sub>

### 5. Generation time at 400 regions
**Story.** "A 400-region galaxy starts within a time Westley has confirmed." [S-224]
**Today.** 5 milliseconds was confirmed at 110 regions; the region range is now 250 to 400. Separately, a 150-step jump at 400 regions must finish under 2 seconds.
**The choice.** (a) Scale linearly, about 18 milliseconds. (b) Keep 5 milliseconds at 400. (c) Drop the small budget and fold generation under the 2-second figure.
<sub>key: Q-224-01</sub>

### 6. Does weather touch the strategic sim?
**Story.** "The history I read agrees with the ground I fight on." [S-225]
**Today.** A region's environmental trouble exists in missions. Whether it also drives events in the strategic simulation is open; the launch library is closed at 26 event templates.
**The choice.** (a) Tactical only. (b) A new template family that reads the trouble. (c) Decided with the map generator and weather design.
<sub>key: Q-225-01</sub>

### 7. What are the city "events"?
**Story.** "The history I read agrees with the ground I fight on." [S-225]
**Today.** Settlement growth is timed in waves by "events". It is unclear whether those are the strategic events (one chain per region-year) or in-mission events such as a shipment arriving or a season turning.
**The choice.** (a) In-mission events only. (b) Strategic events only. (c) Both.
<sub>key: Q-225-02</sub>

### 8. Does mission technology flow back?
**Story.** "A mission starts from the faction's technology, only slightly." [S-227]
**Today.** It is open whether anything a pair reaches in a mission feeds back into the faction's technology number, and whether Knowledge Lost (a collapse destroying technology) touches a mission's technology.
**The choice.** (a) Nothing flows back; the two are independent. (b) The mission's result nudges the faction's number. (c) Decided together with what technology does.
<sub>key: Q-227-02</sub>

### 9. Tiers versus levels
**Story.** "A mission starts from the faction's technology, only slightly." [S-227]
**Today.** The simulation reads technology in three tiers, while an era has a finer range of levels, for example 1 to 5. Their relationship is not settled.
**The choice.** (a) Tiers stay the sim's coarse reading and levels are the mission's finer scale. (b) The tiers become the levels. (c) Decided together with what technology does.
<sub>key: Q-227-03</sub>

### 10. Who gets a ledger character in a team?
**Story.** "My pair is part of the chapter, the ledger and the world." [S-228]
**Today.** A chapter has one commander today. How the economy seat of a pair and each sub-commander enter the chapter record, ledger and character selector is unsettled.
**The choice.** (a) Only the commanding seat has a ledger character; the economy seat has none. (b) Every player has a ledger character and a lineage. (c) Other: your words.
<sub>key: Q-228-01</sub>

### 11. A pair in a one-faction world
**Story.** "My pair is part of the chapter, the ledger and the world." [S-228]
**Today.** A pair is a sub-civilization inside the over-arching civilization, but the simulation has one faction per civilization.
**The choice.** (a) The pair maps onto the chapter only; the simulation keeps one faction. (b) Onto a set of the faction's regions. (c) Onto its own faction.
<sub>key: Q-228-02</sub>

### 12. Do mission events reach the jump log?
**Story.** "Each entry reads like a passage from a real history, different every campaign." [S-068]
**Today.** In-mission happenings (base occupied, retaken, fall back, expansion made) may or may not reach the time-jump log and so shape the chronicle's consequence text and chain expansion. It depends on a companion question about what missions report.
**The choice.** (a) No, only the outcome reaches the log. (b) Yes, as content for the consequence slots. (c) Decided with that companion question.
<sub>key: Q-068-03</sub>

### 13. Where is the economy player in the chronicle?
**Story.** "Events near my family bubble up into the scroll, as the deeds of a military family." [S-070]
**Today.** Lineage members are framed as military. Who the economy player is in the chronicle, and who the others are in a team of up to six, is unsettled.
**The choice.** (a) The economy player is not in the lineage. (b) A lineage member in a support role, framed as military. (c) Other: your words.
<sub>key: Q-070-02</sub>

### 14. How are trait cards earned?
**Story.** "I unlock trait cards and build a force that plays my way, and cards never beat positioning." [S-083]
**Today.** Unlocking, persistence, whether the enemy fields cards, and how "positioning outweighs any card" is checked in tuning are all undecided. This is post-launch work.
**The choice.** (a) Cards earned by play milestones, account-wide, the enemy draws from the same pool, and the headless matchup check rejects any card that lets a worse-positioned force win. (b) Per-campaign unlocks. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-083-03</sub>

### 15. Travel lanes as a mode?
**Story.** "Someday, perhaps: lanes where my troops move faster and strategic ground where they move slower." [S-165]
**Today.** Your idea of 2026-10-01, marked as an idea only: the map generator makes tree-like lanes of travel giving troops 1.3 times speed, slowdowns at key high ground and layers, and normal speed elsewhere.
**The choice.** (a) A separate game mode. (b) Part of the standard map generator. (c) Dropped.
<sub>key: Q-165-01</sub>

## 8. Everything else open, alphabetical by id

### 1. Cross-layer numbers
**Story.** "I know whether my unit can shoot an enemy one layer up." [S-008]
**Today.** The ranges and damage multipliers by layer offset (up differs from down), area damage by offset, and the halfway rule during a transition are to be decided by the skill lab, not by argument. Whether firing needs vision is settled.
**The choice.** (a) The lab sweeps the parameter families: range and damage by signed offset, area by offset, a fire-needs-vision flag, and the halfway rule (both always targetable, per rule, or untargetable). (b) Fewer knobs, fixed by analysis alone.
<sub>key: Q-008-03</sub>

### 2. Does concentration of fire count?
**Story.** "I know whether my unit can shoot an enemy one layer up." [S-008]
**Today.** In the lab's first run every unit on both sides fired, yet the side whose fire fell on a few enemies won (11 alive against 15 at equal total health). Your ruling of 2026-10-02: nearest target stays the game's rule, and one lab-only focus-fire batch measures the effect.
**The choice.** (a) It joins the principle: what counts is units firing and how their fire is concentrated. (b) It is tuned out, so the result follows the firing count alone. (c) Decide from the focus-fire batch.
<sub>key: Q-008-05</sub>

### 3. Checking that refusal works
**Story.** "I know whether my unit can shoot an enemy one layer up." [S-008]
**Today.** You said refusing a fight counts as a counter, but in the lab the larger side is made to attack, so refusal cannot be played.
**The choice.** (a) A stand-off, with no unit in reach for the stalemate window, is recorded as a refusal and reported beside the counters check. (b) The larger side gets a scripted choice to decline when its scouting shows the play. (c) Not checked; the counters check covers the other counters only.
<sub>key: Q-008-06</sub>

### 4. Judging unit-type matchups
**Story.** "I know whether my unit can shoot an enemy one layer up." [S-008]
**Today.** The matchup skill acts through damage per hit, not through who can fire, while two of the lab's conditions judge every skill by firing count.
**The choice.** (a) For this skill the firing count is weighted by the category multiplier against the target's type, as the README says (you, 2026-09-30: "not just unit values but their type as well"). (b) Judge it on break-even alone. (c) Other: your words.
<sub>key: Q-008-07</sub>

### 5. A galaxy count that comes up short
**Story.** "A galaxy small enough to learn, large enough to feel vast, different every campaign." [S-021]
**Today.** With equal template weights about one seed in five drew a region count 8 or more under the feasible minimum, and would have failed to generate. The design lane chose the first option on 2026-09-22 and the builder implemented it; confirm or change.
**The choice.** (a) Chosen: lift the drawn count to the feasible minimum after the template roll, with no extra draw, so every seed generates; a pinned count below the minimum still fails cleanly. (b) Re-roll the templates until feasible, which changes the draw-order contract. (c) Keep the failure and have the client retry with the next seed, a visible hitch that breaks "same seed, same world".
<sub>key: Q-021-07</sub>

### 6. When does Rally trigger?
**Story.** "Each unit has exactly one ability that amplifies its role and costs something." [S-086]
**Today.** Rally fires on "a damaged friendly in radius" with no threshold. Two fixtures need it to ignore a friendly at 400 of 500 health and fire at one at 200 of 500, so the builder used under half health for now.
**The choice.** (a) Chosen for now: under 0.5 of maximum health, named as a constant. (b) Any damage, moving the other fixture out of Rally's radius. (c) A threshold per unit type.
<sub>key: Q-086-02</sub>

### 7. Refusing a mismatched save
**Story.** "Saved at every chapter boundary without asking." [S-111]
**Today.** Loading a save of another version is refused with a message naming both versions, but no code accessor returns the versions.
**The choice.** (a) The load call returns a status, and the client reads the two versions through separate accessors. (b) The load call gives the two versions as extra outputs. (c) A separate last-error accessor.
<sub>key: Q-111-02</sub>

### 8. Fine detail against the grid
**Story.** "One continuous world from a single unit to the whole battlefield." [S-194]
**Today.** The fine terrain formula and the sim's coarse grid can disagree. You said on 2026-10-06: "2: This question requires deeper investigation, mark in the repo that when it comes time to design this part we'll need to do some research on how we can keep the backend (what's happening in the game) *true* to what's really happening (b) while still maintaining the quality of the player experience (we don't want too much snapping that comes with b)." The agreement tolerance is yours; research is queued.
**The choice.** (a) Fine detail is a ripple that cannot move ground across a band edge. (b) The sim's grid wins and the client snaps ground contact to it. (c) Play follows the grid and visuals may differ.
**Recommended.** None marked; you leaned to (b) with research to avoid heavy snapping.
<sub>key: Q-194-01</sub>

## 11. Dropped by the lab filter, asked anyway

### 1. A ground flyer's sight
**Story.** "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage." [S-005]
**Today.** A ground-era flyer sees down and "is visible from farther away than it can see" (you, 2026-10-05). Parked for the beta ("#5: Not for beta, skip"); the two distances and what else it borrows from the space model are open.
**The choice.** (a) Seen-from distance is its sensor radius times a multiplier above 1, and it sees down with the ground model. (b) Numbers from the skill lab. (c) Another: your words.
<sub>key: Q-005-06</sub>

### 2. Space sight beyond two layers
**Story.** "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage." [S-005]
**Today.** Passive cross-layer sight in space is "very limited" (you) and the ping reaches past it. The factors 0.50, 0.20 and 0 beyond two layers were never yours; you answered "#4: A, architect decision. Should be close to what it was for the python version of the game".
**The choice.** (a) Keep 0.50, 0.20 and 0 as provisional and let the space lab sweep them. (b) Smaller, such as 0.25, 0.10 and 0. (c) A fixed short radius rather than a factor.
<sub>key: Q-005-07</sub>

### 3. One silhouette per type?
**Story.** "Every unit type has a shape I can read at a glance in any era." [S-132]
**Today.** With 20 to 40 types per era, silhouette carries the information. Parked for the beta ("#5: TBD, beta doesn't need to answer questions like this").
**The choice.** (a) One persistent silhouette per type across every era. (b) Silhouette families per category, with variants read by size and detail. (c) Other: your words.
**Recommended.** (b).
<sub>key: Q-132-02</sub>

### 4. Firing arc
**Story.** "Units face what they shoot and where they go, and turn rather than snap." [S-100]
**Today.** You ruled on 2026-10-13 to add a firing-arc rule: a unit fires only at targets inside an arc about its facing, and turn-rate limits then cost time to bring a target in. Today facing is cosmetic. Width, whether it varies by category, and what a flanked unit does are yours to rule after the lab shows the effect.
**The choice.** (a) One arc for every type, 120 degrees as a draft the lab sweeps. (b) Width per category: Strike wide, Line medium, Siege narrow. (c) An arc for Siege only; the others fire all round.
<sub>key: Q-100-01</sub>

### 5. Where the solo controls sit
**Story.** "Alone, I have a dial, a doctrine switch, unit-mix switches and I ask by pointing, even from the map view." [S-231]
**Today.** The right sidebar holds only the layer strip, so the commander's dial and switches need a home. You said: "#6: architect choice, I provide feedback post-product."
**The choice.** (a) The right sidebar. (b) A bar at bottom centre beside the ability slots. (c) A panel opened by a key.
<sub>key: Q-231-01</sub>

### 6. Overriding the mix and acknowledging
**Story.** "Alone, I have a dial, a doctrine switch, unit-mix switches and I ask by pointing, even from the map view." [S-231]
**Today.** How the commander overrides the mix the rules pick, and whether the screen confirms a request made by pointing or says when the rules cannot carry it out, is open. You said: "#7: architect choice".
**The choice.** (a) A mix panel and a short acknowledgement on the ticker. (b) A marker on the map where the request stands. (c) No acknowledgement.
<sub>key: Q-231-02</sub>

### 7. The economy player's portrait
**Story.** "As the economy player of a pair, my screen shows resources, workers, the yield of a lot before I place, my schedule, technology and defenses, and no list of what the commander needs." [S-230]
**Today.** The commander's portrait place shows the commander, but the economy player is not the commander. Parked for the beta ("#4: skip for beta").
**The choice.** (a) The same commander portrait. (b) The economy player's own identity. (c) Nothing.
<sub>key: Q-230-02</sub>

### 8. Drawing a disguised building
**Story.** "I see workers walk and gather, weather cross the map, and disguised buildings look like what they pretend to be." [S-238]
**Today.** How a disguised or hidden building looks, to its owner and to the enemy, follows how disguise works at all. Parked ("#4: skipped for now").
**The choice.** (a) The enemy sees a decoy look and the owner sees the true building. (b) Both see the true building, with a cover mark for the owner. (c) Decided with the disguise design.
<sub>key: Q-238-01</sub>

### 9. How difficulty scales a smarter enemy
**Story.** "A difficulty knob changes how much the enemy has, not how well its units fight." [S-125]
**Today.** How difficulty scales the enemy's prosperity and its multi-layer intelligence, and what hard mode strives for (positional awareness, informed surrounds on chosen layers), is open. You answered "#8: C", read as leaving numbers to the skill lab; the rules keep only that both scale.
**The choice.** (a) Prosperity through reinforcement structures and rate, intelligence through which layer-aware behaviours the enemy's macro layer may use per difficulty. (b) Other, decided with the lab.
**Recommended.** (a).
<sub>key: Q-125-03</sub>

### 10. Does archetype pick economy doctrine?
**Story.** "A faction's standing in the galaxy carries into the economy it fights with." [S-226]
**Today.** Whether a faction's archetype, weights or confidence link to the doctrine running its economy, for the enemy and for your civilization, is open. Parked ("#2: skip characters (individual playstyles of enemies) for the beta").
**The choice.** (a) No link; doctrine is chosen apart from archetype. (b) Archetype sets the enemy's default doctrine. (c) Other, with the doctrine design.
<sub>key: Q-226-02</sub>

### 11. Disguising a building
**Story.** "A real economy: run by a partner, or running itself." [S-159]
**Today.** You said on 2026-10-01: "we should also give players a way to disguise/hide their buildings." How, and at what cost, is open. Parked ("#3: skip this for now").
**The choice.** (a) Buildings are unidentified from a distance until scouted, with cheap decoys. (b) A paid cover that hides one building's schedule. (c) Both.
<sub>key: Q-159-09</sub>

### 12. How mission tech is derived
**Story.** "I choose the technology my side goes for, and a normal match has time to go up one or two levels." [S-173]
**Today.** The formula taking the simulation's technology level to a mission's starting technology, and what "only slightly" means, is open. Parked as post-beta.
**The choice.** (a) At most one step up or down. (b) A band around the level. (c) Set in the lab.
<sub>key: Q-173-01</sub>

### 13. Technology levels per era
**Story.** "I choose the technology my side goes for, and a normal match has time to go up one or two levels." [S-173]
**Today.** The number of levels per era, and the cost and time per level so a timed match fits one or two, are open. Parked as post-beta.
**The choice.** (a) 5 levels per era, your example. (b) Set per era pack. (c) Set by playtest.
<sub>key: Q-173-02</sub>

## 9. Finish-the-loop items (parked, now reachable by the sim lane)

### 1. Noise on event thresholds
**Story.** "Every crisis has a cause I can point to; history reads as consequence, not dice." [S-026]
**Today.** Event thresholds are meant to be noised at the start of each jump, but live noise is always 0. Wiring it changes every campaign's history and every recorded golden run, by well over 5 percent, and balance items are held for you.
**The choice.** Wire it now, or wire it together with the balance simulation. Or: your words.
<sub>key: F1</sub>

### 2. Successor after a collapse
**Story.** "When my civilization is gone I keep playing in a surviving one." [S-062]
**Today.** The register records your answer as normal pools restricted to surviving factions, falling back to the faction with the most regions. The code and an Architect ruling use "most regions" only and call the question open. Two records disagree on your answer.
**The choice.** Which is right: pools restricted to survivors with fallback, or most regions only? Or: your words.
<sub>key: F2</sub>

### 3. Chronicle words for a fall and a death
**Story.** "When my civilization is gone I keep playing in a surviving one." [S-062]
**Today.** The chronicle should record a fallen faction and a dead commander ("the chronicle frames it"). Its category and wording are new chronicle content nobody has written.
**The choice.** Open: your words.
<sub>key: F3</sub>

### 4. Telling the client the campaign ended
**Story.** "When my civilization is gone I keep playing in a surviving one." [S-062]
**Today.** When no faction survives, the campaign ends, but nothing tells the client. A fix adds a new field to the pipe between sim and client.
**The choice.** Open: your words.
<sub>key: F4</sub>

### 5. A second enemy force
**Story.** "A second enemy force reacts when I rout the first." [S-122]
**Today.** No mission registers a second force and no hook scripts exist. The choice is whether setup gets a default hook now or waits for the script pipeline.
**The choice.** A default hook at mission setup now, or wait for the script pipeline. Or: your words.
<sub>key: F5</sub>

### 6. How long a timed transition takes
**Story.** "The enemy escalates on a schedule and reacts to me, with the moment shifting each time." [S-121]
**Today.** Enemy forces switch behaviour on timed transitions, and the duration per force is a number nobody has given.
**The choice.** Open: your words (a duration).
<sub>key: F6</sub>

### 7. The cautious break-off threshold
**Story.** "Enemy forces advance, hold, patrol, ambush, or retreat, cautiously, aggressively, or in echelons." [S-120]
**Today.** A cautious enemy breaks off contact at some "contact threshold" that has no value.
**The choice.** Open: your words (a number).
<sub>key: F7</sub>

### 8. Who reads a faction's phase?
**Story.** "The sim knows whether my civilization is expanding, at war, overextended, fragmenting, or settled." [S-053]
**Today.** The sim computes each faction's lifecycle phase, but it is unsettled whether the chronicle or the mission generator consumes it.
**The choice.** Open: your words (chronicle, mission generator, or both).
<sub>key: F8</sub>

### 9. Clamping the jump length
**Story.** "Decades pass while I am gone, and the world decides how many." [S-056]
**Today.** The client sends the raw step count for a time jump with no clamp to the intended 20 to 100 steps of the strategic clock (50 of them pass in a time jump).
**The choice.** Open: your words.
<sub>key: F9</sub>

### 10. Regional commander on conquest
**Story.** "The people the chronicle names are born, serve, age, and die, and someone takes their place." [S-060]
**Today.** A regional commander should appear when a region is conquered, but never does in play, and where it hooks in is unclear. It needs a scout of the code first.
**The choice.** Open: your words.
<sub>key: F10</sub>

### 11. Two helpers that disagree with the rules
**Story.** "When my civilization is gone I keep playing in a surviving one." [S-062]
**Today.** The player-faction-collapsed check and the fallback-pool selector disagree with their rules or the live path. The tests are the spec.
**The choice.** Fix them to match the rules, or remove them with their tests. Or: your words.
<sub>key: F11</sub>

### 12. What objectives are made of
**Story.** "One primary objective I can see progressing, up to three secondary ones." [S-075]
**Today.** Unsettled: what a designated target is and how many there are, who is escorted and how many, where the extraction point is, and where an interception's enemy force comes from.
**The choice.** Open: your words.
<sub>key: F12</sub>

### 13. What counts as brought home
**Story.** "The result is a spectrum weighing what I achieved and who I brought home." [S-077]
**Today.** Retention counts who you brought home. Open: whether the commander's unit, units made mid-mission and structures count, and whether a unit that leaves the map counts as alive.
**The choice.** Open: your words.
<sub>key: F13</sub>

## 10. Skill lab pass marks (you set each)

The skill lab is where tactical combat is measured on the real sim, to prove your sentence: "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force." It judges rule sets with ten conditions. The marks below are drafts; none is confirmed. A "play" is a scripted skilled or naive way of fighting, and "the firing count" is how many units can get shots off, which your principle says decides a fight. The five skills are landscape, formation, layers, enemy position and unit-type matchup.

### C0. What the lab must show before we trust it: a fair mirror
**Today.** Two identical, mirrored forces fight. This is the control that proves the lab itself is sound.
**The choice.** Draft mark: the larger force wins and the break-even sits at equal numbers. The tolerance is yours.
<sub>key: C0</sub>

### C1. What the lab must show before we trust it: skill wins the firing count
**Today.** A skilled play should get more units shooting than a naive one on the same map.
**The choice.** Draft mark: the skilled side's firing advantage is above the mirror control's noise, on at least four maps in five that offer the play. How large it must be is not a fixed ratio and is yours.
<sub>key: C1</sub>

### C2. What the lab must show before we trust it: the result follows the firing count
**Today.** More units firing should mean a better result, so the firing count really is what decides the fight.
**The choice.** Draft mark: results rise with firing advantage (rank agreement at least 0.8), and no more than one fight in five lies over 25 percent off the trend.
<sub>key: C2</sub>

### C3. What the lab must show before we trust it: skills stack
**Today.** Using several skills together should be worth more than the best one alone.
**The choice.** Draft mark: a combination beats its best single part by at least 5 percent.
<sub>key: C3</sub>

### C4. What the lab must show before we trust it: no dominant skill
**Today.** No one trick should carry the game.
**The choice.** Draft mark: no single skill gives more than 60 percent of the full set's advantage.
<sub>key: C4</sub>

### C5. What the lab must show before we trust it: no dead skill
**Today.** Every skill must matter.
**The choice.** Draft mark: removing any one skill from the full set costs at least 10 percent.
<sub>key: C5</sub>

### C6. What the lab must show before we trust it: counters exist
**Today.** Every skilled play needs an answer on most maps (some situations, like a full surround, are unbeatable).
**The choice.** Draft mark: the counter takes back at least half the advantage, on at least three maps in five.
<sub>key: C6</sub>

### C7. What the lab must show before we trust it: the ceiling is high
**Today.** A great player should beat a much larger force; you gave rough sizes only, about 2 times for all skills at first, then singles near 30 percent and full mastery 3 times or more.
**The choice.** Reported, not pass or fail: the best situations against the rough sizes of 2 times and 3 times. Do you want a pass mark on it?
<sub>key: C7</sub>

### C8. What the lab must show before we trust it: it holds across maps
**Today.** The results should not depend on one lucky map. Space maps must pass; land maps are reported and do not block.
**The choice.** Draft mark: conditions C1 to C6 hold on four space maps in five.
<sub>key: C8</sub>

### C9. What the lab must show before we trust it: fights stay readable
**Today.** Skill should not make fights too short or too long to follow.
**The choice.** Reported, not pass or fail: fight length against the fights-last-long-enough story.
<sub>key: C9</sub>

### Lab 1. Confirm the pass marks
**Story.** "Headless bot matches flag broken matchups automatically." [S-156]
**Today.** The draft marks above are unconfirmed: the mirror break-even tolerance, skill beating the mirror's noise, rank agreement, stacking, dominance and dead-skill shares, and counters.
**The choice.** (a) The draft marks as written. (b) You set each. (c) Report only until the marks are confirmed.
<sub>key: Q-156-02</sub>

### Lab 2. Fights that end as ties
**Story.** "the skill lab as a whole"
**Today.** Fights were flagged as ties when units simply stood waiting and nothing came (you, 2026-10-06). The cap on fight length is raised (provisionally to ten minutes), and later a rule was ruled that a fight ends only by elimination. Parked, lab only ("#7 doesn't pertain to beta"), and superseded by the newer layout-search spec.
**The choice.** (a) A side that sees nothing is sent toward the last known or expected enemy position. (b) In the space lab the ping policies find the enemy and the rule fires on a reveal. (c) A fight where a side never engaged is reported as "never engaged", not a tie.
<sub>key: Q-LAB-01</sub>

### Lab 3. Constants nobody set
**Story.** "the skill lab as a whole"
**Today.** The lab runs on draft constants: win margin 5 percent, stalemate window of 20 seconds, a starting gap of about 30 unit-widths, play counts and factors, layout grid values, corridor width of about 26 unit-widths, the ping search set, and others. "Rough sizes only, not pass marks" applies until you set them. You ruled fights end by elimination only, with both sides attack-moving to one point, so the hold timer, hold radius, blind window and draw band are retired; a capped fight is a defect to trace, never a result.
**The choice.** (a) They stay drafts until the first chart, then you set what the chart shows matters. (b) Set them now.
<sub>key: Q-LAB-03</sub>

### Lab 4. Depth score rule
**Story.** "the skill lab as a whole"
**Today.** The layout search scores depth from skills that give a gain of at least a threshold G (draft 2 units). The first chart decides.
**The choice.** (a) G is 2 units, and a skill scores if its gain is at least G and it has no counter or its counter works. (b) Another G. (c) Another rule.
<sub>key: Q-LS-01</sub>

### Lab 5. Sweeping the enemy mix
**Story.** "the skill lab as a whole"
**Today.** Whether the enemy's mix of unit types is swept for each layout in the second run; a 3 by 3 grid triples the cost.
**The choice.** (a) Fixed per layout. (b) Swept.
<sub>key: Q-LS-02</sub>

### Lab 6. Likely-places ping in the layout search
**Story.** "the skill lab as a whole"
**Today.** Whether the "likely places" ping policy joins the layout search once chokes exist.
**The choice.** (a) Yes, in the second run. (b) No.
<sub>key: Q-LS-03</sub>

### Lab 7. Scoring the ping
**Story.** "I ping a layer I choose at a place I choose and see it for a moment; whoever I ping learns roughly where I am." [S-162]
**Today.** The ping changes nothing in a fight by itself, so it cannot be scored like the other skills. You said on 2026-10-05: "Maybe we could look at the ratio that a specific player detected the enemy against the enemy's ratio that they detected the player, and then look at the outcome. I don't know, this is an area of investigation." Parked as lab work, not beta.
**The choice.** (a) The five readings of the proposal: policy spread, counter cost, value of knowing, warning time against set-up time, and give-away; pass values set by you after the first chart. (b) Detection ratio against outcome only. (c) Another measure.
<sub>key: Q-162-05</sub>
