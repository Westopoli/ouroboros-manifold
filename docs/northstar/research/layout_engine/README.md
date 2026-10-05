# Layout engine redesign: assessment and options (2026-10-04)

Written for the brief `plans/briefs/2026-10-05-layout-engine-redesign-brief.md`. Nothing here is decided. The decisions needed from Westley are at the end. Open questions are rows Q-191-06 to Q-191-10 in `ambiguity_register.md`.

## What Westley said about the present result

2026-10-04, looking at the land mockup built on the old layouts, verbatim:

> "I don't understand how the objective is supposed to move, what the layout is supposed to induce, it feels cobbled together randomly. The red are places units can't go, and while it's technically the landscape engine's scope, we can hand the landscape engine *intention* behind specific regions, and maybe require it to conform to specific requests. For example, if we're designing a point of strategic value, but the landscape engine just cuts off unit passability because the slope was too steep, it completely invalidates the work the layout engine did. Our highest goal is to induce situations that have strategic depth. The layout engine's output should be consistent with that goal."

## 1. Assessment of the present layout engine

A layout today is a hand-drawn graph: about a dozen typed dots at fixed positions on a square, joined by lines. The game does not use it; only the Python reference and the land mockup read it.

| | Finding |
|---|---|
| What it specifies | Where each dot sits (as a share of the canvas), its type (nine types), free-form hint words, and which dots are joined. |
| It says where, never why | No dot or line records what it is for. "Hold this choke", "this ridge overlooks that road" exist only in English file names. The landscape engine has nothing to protect, so a steep slope can cut a route and nothing notices. |
| A line has no numbers | An edge has no width, no length, no grade. Choke width is the word "narrow" or "moderate". The numbers that decide a fight (how many can fire, how long the way around takes) are absent. |
| It asks for open ground only | A choke works because its sides are closed. The layout cannot ask for closed ground, so walls appear by accident and everywhere (pass 5: "What's up with all the walls"). |
| The objective has no tension | In all eight layouts the objective sits beside one side. None can meet the equal-distance rule (Q-191-03). No document says what the objective does over the course of a mission. |
| The economy is missing | No type for a base, expansion site, economic location, significant resource, neutral settlement, strongpoint, or raid and shipment lane. The mockup finds these afterwards by scoring the terrain, so they land wherever flat ground happens to be. |
| Plays are not guaranteed | Layout 07 has no choke, vantage or flank. Flank routes in 02, 04 and 06 do not reach the objective. No type for a slope top or tall cover. |
| It does not scale | Positions are shares of one square for two sides. Nothing says how a layout becomes 64,000 wu or four to six players. |
| Still right | Layout comes first and terrain obeys. A graph of places and routes is the right skeleton. Region flavour, the fairness score idea, and drift along walking routes can stay. |

## 2. What a layout is for

The goal (Westley, 2026-10-01): "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force." The lab's principle: what matters is how many units get shots off, and for how long.

A map adds depth only where it makes a player choose, and where the better choice changes who gets shots off. So the proposal common to every option below is: **a layout is a list of choices the map must force, each with the numbers that make it a real choice.** Shape is free; Westley, Q-191-03: "I don't care what the shape is, I only care about those numbers."

Choices the rules already ask for, and what each needs from the map:

| Choice the player faces | What the map must contain | Numbers that make it real | Source |
|---|---|---|---|
| Go through or go around | A choke on the short route, and a longer way round | Choke width (how many can fire); extra walking time of the way round | S1 hold a choke; Lanchester frontage |
| Climb or stay low | A slope top that overlooks a route, with a second way up | Height in bands; what it overlooks; length of the second way | S1 slope top; E-01 slopes |
| Objective, resources, or both | Objective and significant resources apart, each at equal distance from the sides | Equal walking distance; walking time between objective and resource (too far for one force to cover both) | R-177-04; defeat in detail |
| Expand or stay home | Expansion sites outward from the base, each nearer its own side but reachable by a raid | Own distance, enemy distance, which lane a raid comes by | R-175-01, R-175-02, R-174 |
| Which approach to watch | At least two approaches to each key place, one out of sight of the other | Count of approaches; whether one is hidden by height or tall cover | S4 unwatched route; S3 decoy |
| Hold the stair | A strongpoint on the slope between two bands | Which bands; what it guards | R-218-01 |

How the fight is meant to move, in every option: each side opens on safe ground (base, economic locations), pushes out into contested ground (expansion sites, significant resources, strongpoints, settlements), and the objective sits where both must come. What the objective itself does over time is not written anywhere (Q-191-07).

## 3. How intent reaches the landscape engine

Also common to every option. The layout hands the landscape engine a short list of requests. Each is measurable on the finished terrain.

| Request | Meaning | Example |
|---|---|---|
| Keep open | A walkable route between two places, at least so wide, no steeper than the walk limit | Base A to the ford, 600 wu wide |
| Keep closed | A stretch no unit can walk across | Both sides of the ford for 1,500 wu |
| Height | One place stands above another, or looks down on a route | The ridge is one band above the road |
| Room | Flat ground of a given radius | A base pad, 500 wu |
| Number | A walking distance or ratio that must hold | Both bases the same distance from the objective, within tolerance; the way round is at least twice the way through |
| Free | Everything not named | The landscape engine does what it likes |

Then a check runs on the finished terrain and prints one line per request: met or broken. Blocked ground is drawn in two colours: closed on purpose, and closed by accident inside something promised. A broken request is the terrain's fault. The terrain is repaired or made again; the layout is not bent. This is the direct answer to the slope that cuts off a strategic point.

Every figure (widths, distances, tolerances) is drafted in the prototype for Westley to approve (Q-191-05).

## 4. Three shapes the engine could take

All three use sections 2 and 3. They differ in where a layout comes from.

### A. Authored layouts, rewritten with intent

About ten hand-made layouts, one or two per archetype, each a graph with real widths, the choices it forces written in, and a request list. A seed only nudges positions.

- Westley would see: a flat diagram of one layout with every route labelled (width, walking time) and every choice named, then the terrain built on it with the met-or-broken list.
- For: easiest to judge and audit by eye; each map is known to play.
- Against: few shapes, so maps repeat; each layout must be redrawn by hand for 64,000 wu and for each player count. Works against "However much we can vary the shapes given those constraints I encourage."

### B. Numbers only, solved per map

No drawn layouts. An archetype is a list of numbers and relations (equal distances, objective to resource walking time, one choke on the short route with a way round twice as long, and so on). A solver finds positions that satisfy them, different for every seed.

- Westley would see: a seed slider; each seed a different diagram satisfying the same list, with the list ticked beside it.
- For: the most variety; the numbers are the whole contract; scale and player count are just more numbers.
- Against: a solver can meet every number and still give a map that reads as noise, which is today's complaint. Hardest to build and to steer.

### C. A kit of situations, composed per map (recommended)

A small library of **situations**: choke with a way round, ridge with two ways up, twin resources, hidden approach, stair with a strongpoint, expansion on a raid lane. Each is a small piece of graph carrying its own choice, numbers and requests. An archetype is a recipe: which situations, where along the line between the sides (near a base, in the middle, at the objective), mirrored or slanted. The engine composes them per seed.

- Westley would see: a diagram where each situation is outlined and named with one sentence ("hold here: 6 can fire at you at once; the way round takes 70 s longer"), a panel listing the choices this map forces, and a seed slider that rearranges the same recipe into different shapes.
- For: variety from composition, legibility from named pieces. Each situation is one scenario for the layer lab, so its worth can be measured (how large a force a holder beats) and a slanted map can be balanced by measured worth. Scaling adds situations and sides instead of stretching one drawing. A space situation is the same piece with open-or-blocked requests.
- Against: the kit must be designed well; a poor piece repeats everywhere. More to build than A.

| | A authored | B solved | C kit |
|---|---|---|---|
| Variety of shapes | low | highest | high |
| Readable intent | high | low | high |
| Scales to 64,000 wu, 4 to 6 players | by hand | yes | yes |
| Ties to the layer lab | per layout | no | per situation |
| Effort to prototype | lowest | highest | middle |

## 5. The brief's nine questions

Candidates only; "rec." marks the Architect's recommendation, not an answer.

| # | Question | Candidates |
|---|---|---|
| 1 | What must a layout specify? | (a) rec.: every place a rule names (bases, objective, significant resources, expansion sites, strongpoints, chokes, vantages, slope tops, tall cover, raid lanes) with numbers; economic locations and neutral settlements as counts per zone, found by scoring. (b) everything placed exactly. (c) only military places; all economy found by scoring. |
| 2 | What is left to the terrain? | (a) rec.: all shape, all free ground, exact position inside each requested zone, extra features only where they break no request. (b) also the exact route lines. (c) nothing beyond looks. |
| 3 | Which plays must every layout offer, and how checked? | (a) rec.: at least one map-dependent play each for landscape, layers and enemy position, checked on the finished terrain by the request list. (b) every play in the lab's table. (c) one play of any kind (today's R-192-04). Row Q-191-08. |
| 4 | Where do layouts come from? | A, B or C above. Row Q-191-06. |
| 5 | Scale and player count | (a) rec. with C: more situations and more sides as canvas and players grow; distances set in walking time. (b) one drawing stretched. (c) separate layouts per size. |
| 6 | A slanted archetype | Q-197-01 is closed: the range is centred on the slant. Open part: the unit of slant. (a) rec.: measured worth of the situations each side holds, from the lab. (b) distance differences only. (c) by eye per archetype. Row Q-191-09. |
| 7 | The nine old node types | (a) rec.: objective, choke, vantage, flank route kept as parts of situations; staging and spawn become bases; reinforcement structure becomes strongpoint; transit and hazard anchor dropped as types (a route and a region property). (b) keep all nine and add the new kinds. |
| 8 | A layout on a space map | (a) rec.: same requests with layers in place of height: keep open on layer n, keep closed on layer n, a named crossing point open on two layers. (b) a separate space layout engine. Row Q-191-10. |
| 9 | Pairing with archetypes; the eight old layouts | (a) rec.: retire the eight as data, keep them as reference; each archetype gets a recipe (C) or new layouts (A). (b) audit and patch the eight. |

## 6. Decisions needed from Westley

1. **Q-191-06**: A, B or C. Recommended C.
2. **Q-191-07**: what the objective does. The quote above says "how the objective is supposed to move"; no rule says. Candidates: (a) it stays put, both sides equally far, value constant; (b) it stays put and its worth grows with time held, so an early grab can be answered; (c) it moves along a walking route on the three moving archetypes only (Interception, Rear Guard, Containment), fixed elsewhere; (d) the old assault shape stays where the archetype is an assault, and the equal-distance rule applies only to resources there.
3. **First prototype**, whichever option: step 1 is the flat diagram alone, no terrain, to judge whether the choices read; step 2 is the terrain reacting with the met-or-broken list. Agree, or terrain from the first pass?
