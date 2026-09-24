# Self-running city spectacle: perception brief

## 1. Feature and status

E-19 S-159 R-159-02 (`docs/bible/epics/E-19-multiplayer.md:110`), deferred, no rule at launch. Open flags Q-159-02 (how it runs itself and renders cheaply, `docs/northstar/ambiguity_register.md:149`), Q-159-03 (which pieces the player builds, `:159`), Q-159-04 (grows during or between missions, `:160`). The landscape design phase (`docs/northstar/research/landscape_design/README.md`) moved the city onto the tactical battlefield and approved the "one generator, two mappers" concept in mockup review 2. The paired mode where a human runs the city has its own brief in `../paired-economy/`.

## 2. Player-facing goal as documented

R-159-02: "the same economy and its city are present in every match, including the core single-commander game where no second player has opted into the pairing; when nobody is managing it, it runs itself, driven by the region's existing simulated economic state (E-02), not by a real decision-making agent — a scripted or rule-based growth process is acceptable and preferred over an intelligent agent. The visible result is a deliberate spectacle, not a side effect: buildings rise, infrastructure spreads, and activity visibly increases as the region's economy grows, cheaply enough to keep the screen busy at scale without heavy rendering cost... The self-running city should be something a player is drawn to and wants to watch, and something they can also choose to influence and grow, not merely observe, even outside the paired mode; the extent of that influence outside the paired mode is unspecified. This does not change the core single-commander game's rule that the player does not manage an economy." (`E-19:110`)

Landscape design: "The city is the battlefield. Every fight happens at a city; the city is the player's long-term home base and the thing being protected." (`landscape_design/README.md:32`)

## 3. Westley's own words

Landscape answer 4, 2026-09-21 (`landscape_design/README.md:14`): "cities will be like your homebase long term, something you'll need to protect. Every "fight" at the moment is happening at a city in a civilization, the economy/buildings will be the city itself. I'd like it to be expansive, huge scale... the player doesn't build everything, just pieces (to be designed)".

Answer 2 (`:12`): "2: C" (biome is look now, play effects later). Answer 6 (`:17`): "6: C" (biome lives in the theme pack now, door open for the sim later). Answer 7 (`:16`): "Settled reach city: A, placeholders are ok for now, model generation will happen later. - greek skin, settled reach skin."

Mockup review 2 (`:63`): "City has distinct onion layers, if this is a prototype of the map generation/landscape system, I'd hoped it'd be much more dynamic, more variety, not simple circular cities, cities that follow rivers like reality or nestle in valleys/peaks, hillsides. Stochiastic seperations, very similar to the Roblox biome/landscape generation tool."

Q-159-02 framing (`ambiguity_register.md:149`): "Westley wants this to be a visual draw players are pulled toward and, ideally, can influence and grow even alone, not a passive backdrop; core-game economy management stays off."

Commit 28f7ace: "Westley wants the same economy and city visible in the core single-commander game too, not just the paired mode: when nobody opts into managing it, it runs itself off the region economic field (E-02), no real agent needed, and the visible growth (buildings rising, activity increasing, cheap at scale like E-17/E-18's procedural and LOD approach) is meant to be a visual draw on its own."

E-17 references, 2026-09-13 (`docs/bible/references/E-17/notes.md:42-43`): "Dramatic elevation differences... the player should physically feel the height and get a real sense of scale." "Major sense of scale via distant landmarks. Huge objects far in the background — mountains, clouds... The battlefield should feel small against something vast."

## 4. Fixed constraints any option must honor

- No intelligent agent runs the city; scripted or rule-based growth driven by the region's economic state is preferred (R-159-02).
- The solo commander never administers the economy; the extent of nudging is open (R-159-02; `game_bible.md:87,89`).
- Cheap at scale: procedural authored pieces (E-17 S-119), LOD and culling discipline (E-18 S-134, S-136).
- One generator, one field map, two mappers (landscape and city), two kits per era, one placement engine (`landscape_design/README.md:26-30`); kits swap cleanly (`:59`).
- Terrain first; big elevation; cities follow rivers, coasts, and contours, never rings; larger canvas; camera height floor (`:67-71`).
- Three zoom bands; the map view overlay (`:34`, `:65`).
- The region's economy ticks per region year in the strategic sim, which is stopped during a mission; a mission lasts minutes (Q-159-04).
- Same seed, same city (determinism).
- Era-agnostic: the city's pieces come from the era pack; the engine never names a temple.
- The player's units may need to path through it; whether buildings block movement is part of the design.

## 5. Prior art already named

Age of Empires Online (register, "playful bright animations"). World of Warships (map view). Roblox biome and island generators, Minecraft biome blending (A-157). Halo Wars (camera floor). Concept images `docs/bible/references/E-17/E-17-5..7-macro-city*.png`.

## 6. Contradictions, as questions for Westley

1. R-159-02 was written as a strategic-layer spectacle; landscape answer 4 chose the city on the tactical battlefield, same placer. Confirm the city the player watches grow is the one they fight in, not a separate backdrop.
2. Does the city grow during a mission, or only between missions (Q-159-04)? If during, is that real growth or theatre seeded from the region state?
3. "Influence and grow, not merely observe": what is the smallest nudge you have in mind for the solo commander (choose where a wall goes, spend a mission reward, protect a district so it grows), and what would cross the line into managing an economy?
4. When the city is damaged in a fight, does the damage persist into the next mission at that city, and does the city rebuild on its own?

## 7. Proposed option width

Three options, one wild. Each option describes what the player sees the city do over one mission and over one campaign, what draws their eye, and the one or two ways they can touch it.

## 8. Westley confirms

Batch 2, 2026-09-22, verbatim: "yes city is in teh same map. Yes grows during mission (economic player will be managing that growth). Their city will always need to be protected, if it's an attacker than it's their "forward base" or "base of operations", the piont from which they're launching the attack. If it dies, the battle is over, re-enforcements can't come and you can't replenish your forces (classic RTS). Damage can persist if the time jump is short, it kinda depends on the situation of the civilization: big economy, quick rebuild, slow economy and they took a massive hit in the simulation numbers, slow rebuild."

Folded into the brief:

- Question 1: confirmed. The city the player watches grow is on the tactical map they fight in.
- Question 2: the city grows during the mission. With an economy player it is their growth; in solo play it runs itself during the mission.
- Every side has a city on the map. The defender's city is home; the attacker's is a forward base, the point the attack launches from. If a side's city dies, its battle is over: reinforcements stop and forces cannot be replenished, in the classic RTS sense. This is a new loss condition that touches E-10 outcomes and E-15 reinforcement; the options describe it from the player's chair, and the epics are rewritten later.
- Question 4: damage persists when the time jump is short, and rebuilding depends on the civilization's state: a big economy rebuilds fast, a weak one that took a hit in the simulation rebuilds slowly.
- Question 3 (the smallest nudge for the solo commander): not answered. Options propose it.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 3, of which 1 wild.
- The city is on the tactical map and grows during the mission; in solo play it runs itself.
- Every side has a city: the defender's home, the attacker's forward base. If a side's city dies, its battle is over: no reinforcements, no replenishment.
- Damage persists after a short time jump; rebuilding speed follows the civilization's economic state.
- Propose the smallest nudge a solo commander has over the city, and what would cross into managing an economy.

## 10. Decision (2026-09-23)

Westley, verbatim: "For self-running city, I'm not a fan of any of these. What would be cool is if the types of buildings that players don't build (static visual architecture) expands outward automatically as the city grows, but small settlements (that can get bigger) crop up where the production facilities or resource objectives are. If a resource is critical enough, a whole city can be built around it, with trade visibly moving between cities on the map. The home base should have a reason it's there in terms of resources, but it should not be the only source of resources, and people go where money can be made (resources to be found), and trade to happen (between cities with various resources). Let's explore a couple ideas based off of this in a second pass."

Recorded as: None. New direction: static architecture expands outward on its own as the city grows; small settlements crop up at production facilities and resource objectives and can grow into cities around a critical resource; trade moves visibly between cities; the home base has a resource reason to exist but is not the only source; people go where money and resources are. Second pass with a couple of ideas on this.
