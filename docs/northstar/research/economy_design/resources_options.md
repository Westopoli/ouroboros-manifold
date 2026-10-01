# Goal 1 options: resources and how they become units

Written 2026-10-01 for Westley to pick from, fuse or modify. Three regular, three wild. Prior art and its confidence tags ([V] verified, [R] reported, [E] estimated) are in `prior_art_resources.md`. Resource names are placeholders; the era pack names and skins them.

## What every option has to satisfy

- One economy, two drivers: rules when nobody holds the economy seat, a human when someone does.
- The economy player's work is building, and designing efficient pathways and systems.
- Resources become units from a roster of 20 to 40 types per era, and connect to the reinforcement structures a commander captures and holds (E-15).
- Every side has a base of operations it must protect. It receives resources from elsewhere, generates them on site, or both, depending on the simulation and the mission (Q-159-06).
- The simulation can pick a poor planet and a small force. The system has to be playable when the map is poor.
- Settlements crop up at resource sites; trade moves visibly; the home base is not the only source.
- Speed of hand gives a small bounded edge, about 1.1x to 1.2x (Q-159-05).
- Same seed and commands give the same result.

## What made the three-resource dynamic work

In Age of Empires 3 each resource is gathered in a different way and changes character over a match, unit costs mix two of the three, so the economy steers the army's composition, and a fourth channel (shipments) arrives from off the map. Halo Wars has one resource and one question: how many pads. The options below keep "three things that behave differently and pull against each other" and change what the three things are and how they move.

---

## Regular

### A. Three Veins

Three resources that differ by where they are found, and all of them are hauled.

- **Staple** is grown or drawn over an area next to the base. It is plentiful, safe and slow. It pays for bodies: every unit costs some.
- **Stock** comes from finite sites out on the map. It pays for structures, armor and heavy units. Sites run out, so the economy moves outward over a mission.
- **Prize** comes from a few rare sites that sit on or beside the mission's objectives. It pays for technology and elite units.

Every unit costs Staple plus one of the other two, so what the commander can field follows what the pair holds. Goods travel on carriers along roads the economy player lays; a longer or steeper road delivers less per minute, a cut road delivers nothing, and a settlement grows at each worked site.

- **Economy player's work:** place sites and depots, lay and upgrade roads, shorten hauls, move the economy outward as Stock sites empty.
- **With nobody in the seat:** carriers take the shortest path on roads the rules lay to the nearest sites.
- **On a poor map:** few Stock sites and maybe no Prize; the force is mostly Staple-cost units.
- **Prior art:** Age of Empires 3's three resources [V]; The Settlers II's carried goods and roads [V]; Company of Heroes' cut-off [V].
- **Tradeoffs:** the most familiar shape and the easiest to learn. Its novelty is the hauling, not the resources.

### B. Line and Yield

No workers and no stockpile. Resources are rates, and a site pays only while it is connected to the base.

- **Muster** flows from the base itself and its population. It is steady and sets how fast anything is raised.
- **Materiel** flows from held sites.
- **Charge** flows from rare sites and powers technology, abilities and the top of the roster.

A site pays only through an unbroken chain of links (roads, relays, pipes) the economy player builds back to the base. Each link has a capacity, so the network has bottlenecks to find and widen. Production draws on the three rates at once; when one runs short, everything that uses it slows in proportion instead of stopping. The commander's holding of ground is the income, and the economy player's network is what turns held ground into units.

- **Economy player's work:** design the network, widen bottlenecks, build redundancy so one cut does not starve the base, choose what the rates feed.
- **With nobody in the seat:** the rules link each held site by the shortest path, with no redundancy.
- **On a poor map:** Muster alone still raises a basic force; a short network is a small job.
- **Prior art:** Company of Heroes' territory income and supply connection [V]; Supreme Commander's flow economy with proportional slowdown [V]; Dawn of War's strategic points [R].
- **Tradeoffs:** ties the two seats together tightly, since every fight over ground is a fight over income. It gives up the gathering and worker management that the StarCraft 2 register includes.

### C. Home and Field

Two resources are made on the map. The third comes from the civilization.

- **Provision** and **Works** are local, gathered and built up on site (in the manner of A or B).
- **Writ** is the civilization's support. It arrives as convoys at the map edge on a schedule set by the region's economic state, and the convoys travel across the map to the base, where they can be escorted, raided or cut off.

The economy player chooses what each convoy carries from a manifest (units, materials, a technology, a specialist), builds the receiving yards and the route, and decides how much to lean on home against the field. A rich civilization on a poor planet plays convoy-heavy with a long line to guard. A declining civilization on a rich planet plays local-heavy with little help coming. This is the simulation's state turned directly into the shape of the economy, and it is the same split as "receiving resources from someplace else or generating them on site".

- **Economy player's work:** build the route and yards, pick manifests, balance local production against convoys, time convoys to the commander's needs.
- **With nobody in the seat:** a default manifest follows the mission type, as the starting force already does.
- **On a poor map:** this is the option built for it; Writ carries the mission.
- **Prior art:** Age of Empires 3's home city shipments [V], here made physical and tied to the simulation instead of experience points; Foxhole's physically delivered supply [V].
- **Tradeoffs:** the strongest link between the civilization simulation and the battle. A critic of Age of Empires 3 found shipments excessive [V]; convoys that are too generous would make the local economy feel optional.

---

## Wild

### D. The Foundry Line

Raw resources are never spent on units. Units are assembled.

Three raws (say **Ore**, **Grain**, **Timber**) feed workshops that make about six components (for example bodies, arms, armor, mounts, engines, charges). Each unit type in the roster is a recipe of two or three components, so 20 to 40 unit types share a small set of parts. Goods move visibly from site to workshop to muster yard. The economy player lays out the line, and its throughput per component is the army the commander can have. Changing what the army is made of means retooling: reassigning workshops and rerouting goods, which takes time and is visible to an enemy who scouts it.

- **Economy player's work:** lay out workshops and routes, balance component rates, retool when the commander's needs change, save and reuse layouts that work.
- **With nobody in the seat:** a standard line per mission type produces a fixed mix.
- **On a poor map:** a short line with two or three components and a narrow roster.
- **Prior art:** The Settlers' goods chains, where soldiers need made goods [V]; Factorio's layout-as-economy and blueprints [V]. No shipped real-time battle game found where a partner's assembly line sets a teammate's army.
- **Tradeoffs:** the deepest version of "designing efficient systems", and a wide roster becomes a reason for depth instead of a balance burden. The known failure is a chain that stalls without the player seeing why (The Settlers 7 [V]); the line would need to show its own blockages.

### E. The Lift

The three resources are sorted by layer.

- **Bulk** lies on the lower layers (1 and 2), plentiful and heavy.
- **Worked goods** are made on the middle layer (3), where most building happens.
- **Rare** is found only on the upper layers (4 and 5).

Carrying goods along a layer is cheap. Carrying them between layers needs a lift (a ramp, a hoist, a tether, by era), which is expensive, slow to build, limited in capacity and exposed. The economy player's pathways are vertical as much as horizontal, and each lift is a chokepoint the commander has to hold on two layers at once. An enemy that takes a lift cuts a whole layer's wealth off from the base.

- **Economy player's work:** decide where lifts go and how many, route each layer's goods to them, trade a short exposed lift against a long safe one.
- **With nobody in the seat:** the rules build one lift per layer pair at the nearest slope.
- **On a poor map:** resources on only two layers, one lift, a small job.
- **Prior art:** none found. No game in the digest sorts resources by a vertical layer system.
- **Tradeoffs:** the economy becomes something only this game has, and it gives both seats a reason to care about the same layer crossings. It leans on cross-layer rules that are still being settled in the layer lab, so it cannot be finished before they are.

### F. Where People Go

There is one thing to gather: people. The three resources are what people become where they settle.

Population arrives at the base and moves, by itself, toward wherever there is a living to be made. People who settle at a site become **Labor** (materials), people who settle on a route between settlements become **Trade** (wealth and technology), and people who settle behind walls near a garrison become **Levy** (soldiers). The economy player does not assign anyone. He builds what draws them: roads, housing, markets, wells, walls. Units are raised from the settlement they come from, and its specialty decides the unit type, so the army's makeup follows the geography of the settlements. Raising soldiers shrinks the settlement that gave them.

- **Economy player's work:** build attractors to steer settlement, link settlements so trade flows, keep specialties in the proportions the commander needs, decide which settlement can afford to give up soldiers.
- **With nobody in the seat:** people go where the map's yields already are. This is the self-running city Westley described, with no extra system.
- **On a poor map:** few people arrive; one small settlement and its levy.
- **Prior art:** Battle Realms, where peasants are the one pool and are converted into soldiers [R]. Steering a population by building attractors on a live battlefield: none found.
- **Tradeoffs:** opted-out and opted-in are the same system at two levels of attention, and the settlement direction from 2026-09-23 comes for free. Control is indirect, so the seat may feel less hands-on than the StarCraft 2 register asks, and there are no needs or moods to manage: people follow yield and safety only.

---

## Pieces that can bolt onto any option

- **Weather in the economy.** Sources that pulse, drift or regrow on the simulation's oscillators, so a pathway is never finished. Northgard's winter is the reference [V].
- **Commerce cap.** A ceiling on income per resource that building raises, as in Rise of Nations [V]. It bounds runaway economies and is one way to keep a mission's economy within what its region can support.
- **Expedite.** A manual, cooldown-limited action that speeds one building or route by a fixed amount. This is where the 1.1x to 1.2x edge for a fast hand can live: perfect use gives the bound, no use gives 1.0x. StarCraft 2's macro abilities are the reference, and their designers' own complaint was that nobody watching can tell how well it is done [V], so the action should be visible on the map.
- **Exchange.** Convert one resource to another at a rate that worsens with use, so a pair short of one resource has a costly way out.

## Fusions worth noting

- **C with any other.** Home and Field is a channel, not a full economy; it sits on top of A, B, D, E or F as the "from elsewhere" half.
- **A or B with E.** The Lift is a rule about where resources lie and what crossing costs; it can be the geography of Three Veins or of Line and Yield.
- **D with F.** Settlements are the workshops; a settlement's specialty is the component it makes.
