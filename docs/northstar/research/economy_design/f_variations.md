# Goal 1, second pass: Where People Go, expanded, with four variations

Written 2026-10-01. Westley, verbatim: "I'm leaning A and F, but I want to dig deeper into what F could look like, expand on it, come up with 4 variations of the idea, 2 close and 2 very different."

A is Three Veins and F is Where People Go, both in `resources_options.md`. Names are placeholders; the era pack skins them. Prior art not in `prior_art_resources.md` is tagged [E], from model knowledge and not sourced.

## F expanded: the base idea in detail

**Where people come from.** People arrive at the base of operations in groups (a group is the smallest thing the player sees move, a few dozen people). The arrival rate comes from the region's population and economy in the simulation, so a crowded rich region sends a steady stream and a poor planet sends a trickle.

**How they decide where to go.** Each group follows one rule, the same for every side and every seat: go to the open place with the best living, where living is yield times safety, divided by travel time along roads. There are no needs and no moods. A group already settled moves again only when its place's living drops well below another's, so settlements are sticky and do not flicker.

**What they become.** What a group does depends on where it settles:

| Settles | Becomes | Produces |
|---|---|---|
| At a resource site | Labor | materials |
| On a route between two settlements | Trade | wealth and technology |
| Behind walls near a garrison | Levy | soldiers in waiting |

**What the economy player does.** He never assigns a group. He changes the three terms of the rule:

- **Travel time:** roads, bridges, gates, lifts.
- **Safety:** walls, watch posts, and asking the commander to hold ground.
- **Yield and room:** housing (how many a place can take), works at a site (how much each group yields), markets (what a route is worth).

**How people become units.** A settlement musters units of the kind its work makes possible, and each muster removes groups from that settlement. A drained settlement yields less until new groups arrive. The commander's losses are therefore felt in the economy, and the economy player decides which settlement can afford to give.

**What the fight does to it.** Combat near a settlement lowers its safety. Groups leave along the roads for the next best place. A commander who holds a line keeps a town; one who gives ground empties it.

**With nobody in the seat.** The rule runs on the map as generated. People settle the natural sites, routes form between them, the commander draws levy from what grew.

**Keeping the load bounded.** A settlement that has been stable for a while manages its own housing and works. The player's attention moves to new settlements and to the network between them.

**Where the 1.1x to 1.2x edge lives.** An expedite action on one building or road at a time, on a cooldown.

**Open in the base idea.** Control is indirect, and the three-resource pull Westley liked is thinner here than in A: labor, trade and levy are three roles of one resource, not three resources.

---

## Close variation 1: Charter Towns (F with A's three resources, and a direct hand)

People still settle by themselves, and A's three resources exist as real goods: Staple near the base, Stock at finite sites, Prize at rare sites by the objectives. A settlement forms at every worked site. The change is the **charter**: the economy player grants each settlement one, and the charter fixes what the town makes, which resource it hauls, and which family of units it can muster. People choose where to live; the player chooses what the place is.

- **In one minute:** grant a charter to a new settlement at a Stock site; lay a road from it to the depot; add housing to a full Staple town; switch a town's charter from hauling to mustering because the commander asked for heavy units; expedite a wall.
- **Units:** cost people plus goods. A Staple town musters line troops, a Stock town musters armored and heavy units, a Prize town musters elites. Re-chartering takes time and the town produces nothing meanwhile.
- **With nobody in the seat:** each settlement takes the charter its site suggests.
- **On a poor map:** one or two towns, mostly Staple, a narrow roster.
- **Prior art:** Age of Empires 3's three resources [V]; Rise of Nations' cities as the unit of economy [V]; Battle Realms' people-into-soldiers [R].
- **Tradeoffs:** this is the plain fusion of the two options Westley leans toward, and it restores the three-resource pull and a direct lever. It is the least novel of the four, and the charter is a menu choice, not a design problem.

## Close variation 2: The Road Makes the Town (F with pathways as the only tool)

There are almost no attractor buildings. The economy player builds the network, and settlements are a result of it. People settle along roads in proportion to the traffic on them, and a place's kind comes from what its roads join:

- a road from a site to the base grows Labor at the site end;
- a road between two settlements grows Trade along it, and a junction of three or more roads grows a market town;
- a road from the base toward the front grows Levy camps at its far end.

Roads have grades (track, road, highway) with different speed, capacity and cost, and a crowded road slows. The few buildings that exist are anchors: a depot, a gate, a bridge, a wall.

- **In one minute:** extend a road to a newly held site; upgrade the crowded stretch by the river; add a second route so one cut does not strand a town; build a bridge to shorten a haul by a third; expedite a road crew.
- **Units:** mustered at Levy camps from the people there, equipped with what the roads deliver to that camp. A camp fed by a Stock road fields heavier units than one fed only by Staple.
- **With nobody in the seat:** the rules lay shortest-path tracks and never upgrade or add redundancy.
- **On a poor map:** two or three roads; a short job.
- **Prior art:** The Settlers II's roads and flags [V]; city builders where traffic shapes growth [E]. Roads as the sole lever in a live battle: none found.
- **Tradeoffs:** the purest reading of "designing efficient pathways", and the network is also what the commander must defend, so both seats read the same map. With few buildings to place, it may fall short of the city-building depth asked for in R-159-01.

---

## Very different variation 1: Trades and Arms (people carry what they did)

People do not wander. The economy player builds workplaces, and people who work somewhere take up its **trade**. Every unit type in the roster is raised from a trade: quarrymen become sappers, herders become riders, smiths become armored infantry, sailors become marines, surveyors become scouts (the era pack names the pairs). With 20 to 40 unit types, a full economy has a dozen or more trades, and the army the commander can have is the workforce the economy player has grown. Raising a unit takes those workers out of their workplace, so each muster lowers the output of the trade it came from. Survivors who return go back to work as veterans and yield more.

- **In one minute:** build a smithy because the commander wants armor in ten minutes; move apprentices from the quarry to the stables; release forty herders to muster and watch food output dip; welcome back a returning company and put them on the foundry.
- **Three resources:** the trades fall into three groups (land, craft, sea or sky by era) and each group's goods are needed by the other two, so the pull between three things is in the workforce, not in a stockpile.
- **With nobody in the seat:** trades grow in the proportions the mission type's default force needs.
- **On a poor map:** three or four trades, a small roster, which matches a small mission.
- **Prior art:** Battle Realms' peasant conversion [R]; The Settlers' soldiers needing made goods [V]. A roster mapped one-to-one onto a civilian workforce: none found.
- **Tradeoffs:** it gives the wide roster an economic meaning, every muster is a real cost, and the commander and economy player must plan composition together minutes ahead. It drops the self-settling people and visible trade between towns that Westley described on 2026-09-23, unless those are added back.

## Very different variation 2: The Contested Populace (the people are already there, and both sides want them)

Nobody arrives. The map's population is there when the mission starts, placed by the generator from the region's population and wealth, living in neutral settlements that belong to no side. Both sides' economies run on the same people. A group works for whichever side offers it the better living by the same rule (yield, safety, travel time), so the two economy players compete for the populace by building, while the two commanders compete for the ground that makes a place safe. Taking a town by storm scatters its people. Taking it intact, or simply making your side of the river the better place to live, brings them over working.

- **In one minute:** run a road to a neutral village so its people start trading with your base; wall a town the enemy has been drawing people from; open a market that outbids the enemy's for a river settlement; ask the commander to hold a ford for two minutes while a village comes over.
- **Three resources:** A's three, worked by whoever the people at each site work for.
- **Units:** levy raised from the settlements that favor you; local levy is cheaper than what the base sends.
- **What it gives the attacker:** a forward base that starts with nobody and must win locals to grow, against a defender who starts with them.
- **With nobody in the seat:** people stay where they are and work for whoever holds the ground.
- **On a poor map:** a thin populace; holding the one village matters.
- **After the mission:** where the people ended up is a result the simulation can read (population and tension in the region).
- **Prior art:** borders and attrition in Rise of Nations [V] are the nearest; culture-flipping cities in turn-based games [E]. Two economy players competing for one neutral populace during a live battle: none found.
- **Tradeoffs:** it makes the economy seat a contest against another player instead of against a timer, it explains why the fight is at a settlement at all, and it gives the commander a reason not to burn towns. It needs an opposing side with an economy, so its shape depends on the open match-shape questions (Q-141-01, Q-141-02), and against a rules-run enemy the contest is only as good as the rules.

---

## Side by side

| | Control | Three-resource pull | Building depth | Fit with A | Fit with the 2026-09-23 settlement direction | Depends on |
|---|---|---|---|---|---|---|
| F as written | indirect | weak | medium | loose | full | nothing new |
| Charter Towns | direct | strong | medium | is the fusion | full | nothing new |
| The Road Makes the Town | indirect, through roads | medium | low for buildings, high for network | goods ride the roads | full | nothing new |
| Trades and Arms | direct | strong, in the workforce | high | goods feed trades | partial | the roster's trade map |
| The Contested Populace | indirect, competitive | strong (A's) | medium | uses A whole | full | match shape (Q-141) |

These combine. Charter Towns and The Road Makes the Town differ only in which lever is primary. Trades and Arms can be the unit rule of any of the others. The Contested Populace is a starting condition (people present and neutral) that any of the others can run under.
