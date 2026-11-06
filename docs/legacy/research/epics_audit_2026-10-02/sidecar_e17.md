# Sidecar: E-17 map generation (drafter: Engineer, 2026-10-02)

File rewritten: `docs/bible/epics/E-17-map-generation.md`. 22 stories, 106 rules. Every R-112-01 to R-119-03 and R-165-01 line is byte-identical to the old file (checked by script).

## 1. Catalog rows for stories.md

| Story | Epic | Summary | Status | Where |
|---|---|---|---|---|
| S-112 | E-17 | "Maps built on hand-authored strategic layouts." | Spec'd (direction changed 2026-10-02, rewrite pending; see S-186, S-191) | `epics/E-17-map-generation.md` S-112 |
| S-113 | E-17 | "Every place on the map is one of nine things." | Spec'd (direction changed, rewrite pending; see S-191, S-192) | `epics/E-17-map-generation.md` S-113 |
| S-114 | E-17 | "The space between waypoints feels dense or open, blind or clear, high or low." | Spec'd (direction changed, rewrite pending; see S-188 to S-190) | `epics/E-17-map-generation.md` S-114 |
| S-115 | E-17 | "A prosperous region's battlefield is cleaner than a war-torn one's." | Spec'd (direction changed, rewrite pending; see S-187) | `epics/E-17-map-generation.md` S-115 |
| S-116 | E-17 | "Mission maps sized to the situation." | Spec'd (direction changed, rewrite pending; see S-195) | `epics/E-17-map-generation.md` S-116 |
| S-117 | E-17 | "Maps that do not cheat me." | Spec'd (direction changed, rewrite pending; see S-197) | `epics/E-17-map-generation.md` S-117 |
| S-119 | E-17 | "Generated sections blend like real terrain, not tiles." | Spec'd (direction changed, rewrite pending; see S-186, S-196) | `epics/E-17-map-generation.md` S-119 |
| S-166 | E-17 | "Cities and bases that build themselves around what I place, on ground with real height." | Design decided 2026-10-02, not scheduled; now holds Westley's direction and the fixed principles, the rules that carry them out are S-186 to S-197 | `epics/E-17-map-generation.md` S-166 |
| S-186 | E-17 | "Every map starts as real ground, height and water from the seed." | Design decided 2026-10-02, not scheduled; flag Q-186-01 | `epics/E-17-map-generation.md` S-186 |
| S-187 | E-17 | "Mesas, canyons, island chains and fjords, not only rolling hills." | Design decided 2026-10-02, not scheduled; flags Q-187-01, Q-187-02 | `epics/E-17-map-generation.md` S-187 |
| S-188 | E-17 | "A mountainside is a stack of layers an attacker has to climb." | Design decided 2026-10-02, not scheduled; flags Q-166-04, Q-188-01, Q-188-02; land maps only (Q-166-02) | `epics/E-17-map-generation.md` S-188 |
| S-189 | E-17 | "Some ground is too steep to walk, and slopes are the ways between layers." | Design decided 2026-10-02, not scheduled; flags Q-189-01 to Q-189-03; land maps only | `epics/E-17-map-generation.md` S-189 |
| S-190 | E-17 | "The layers follow the land under my units." | Design decided 2026-10-02, not scheduled; flag Q-190-01; land maps only | `epics/E-17-map-generation.md` S-190 |
| S-191 | E-17 | "Bases, objectives and resources sit where the land puts them." | Design decided 2026-10-02, not scheduled; flags Q-191-01 to Q-191-04; land maps only | `epics/E-17-map-generation.md` S-191 |
| S-192 | E-17 | "Ways up and down I can hold, narrow places to fight over, high ground to take." | Design decided 2026-10-02, not scheduled; flags Q-192-01 to Q-192-05; land maps only | `epics/E-17-map-generation.md` S-192 |
| S-193 | E-17 | "Cities rise from scaffolds in waves, climb cliffs and reshape around what I place." | Design decided 2026-10-02, not scheduled; flags Q-166-03, Q-193-01 to Q-193-03 | `epics/E-17-map-generation.md` S-193 |
| S-194 | E-17 | "One continuous world from a single unit to the whole battlefield." | Design decided 2026-10-02, not scheduled; flag Q-194-01 | `epics/E-17-map-generation.md` S-194 |
| S-195 | E-17 | "Bigger matches have bigger maps." | Design decided 2026-10-02, not scheduled; flags Q-195-01, Q-195-02 | `epics/E-17-map-generation.md` S-195 |
| S-196 | E-17 | "A land era and a space era look different over the same kind of map." | Design decided 2026-10-02, not scheduled; space landscape itself is Q-166-02 | `epics/E-17-map-generation.md` S-196 |
| S-197 | E-17 | "A map that favors the defender is still one I can win." | Design decided 2026-10-02, not scheduled; flag Q-197-01 | `epics/E-17-map-generation.md` S-197 |

S-118 gets no row change except its flag Q-118-03 (rules untouched, no direction note). S-165 is untouched, as instructed.

## 2. Register rows (new flags)

| Flag | Where | Question | Candidates | Status | Answer |
|---|---|---|---|---|---|
| Q-118-03 | E-17 / S-118 | May a strongpoint drift along a path as an objective does? The decisions say where strongpoints stand, not whether they move. | (a) no, strongpoints are fixed at their slopes; (b) yes, under R-118-01; (c) only some archetypes | open | |
| Q-186-01 | E-17 / S-186 | The 50 ms generation and 1 µs sampling figures were confirmed for the spine-and-gradient generator. Do they stand for terrain-first generation (noise, lakes, rivers, site finding) at canvases up to 64,000 wu? The prototype takes about 0.84 s in GDScript for up to 100,000 cells. | (a) keep the figures; (b) separate budgets for generation and for sampling at each canvas size; (c) generation off the match-start path (done at campaign time) with sampling kept at 1 µs | open | |
| Q-187-01 | E-17 / S-187 | Which landforms ship? The option Westley chose from named canyon, mesa, caldera, fjord, terraced massif and island chain. | (a) all six; (b) a smaller first set; (c) a set per era | open | |
| Q-187-02 | E-17 / S-187 | How much landscape variety counts as "packed into the maps", the condition for keeping today's canvas sizes, and how is it measured? | (a) a count of distinct biome bands and landforms per map; (b) a spread measure on height and biome across the canvas; (c) judged by Westley on screenshots | open | |
| Q-188-01 | E-17 / S-188 | What is the measure and threshold for "a layer step that is only a meadow slope"? The threshold is Westley's. | (a) a minimum height difference per band step, in wu, per canvas size; (b) a minimum steepness at each band edge; (c) a minimum fraction of band edges that are cliffs or ramps | open | |
| Q-188-02 | E-17 / S-188, S-195 | Can a small canvas (8,000 to 12,000 wu) hold five real height steps? The prototype sizes are 16,000, 24,000 and 32,000. | (a) yes, relief is scaled to the canvas; (b) small canvases are exempt from five land layers; (c) small canvases are enlarged | open | |
| Q-189-01 | E-17 / S-189 | Must a walking route exist between the bases and to the objective, must every band be reachable by walking units, and for which movement kinds does the invariant "objective reachable by 2 or more routes" hold? | (a) walking route required between bases, objective and every band; (b) required for bases and objective only; (c) required for any movement kind, walking only where the map says | open | |
| Q-189-02 | E-17 / S-189 | How steep is ground too steep to cross? The number is Westley's. | (a) one steepness limit for every walking unit; (b) a limit per unit type; (c) decided in the layer lab | open | |
| Q-189-03 | E-17 / S-189 | How much of a map is benched ground and how much natural? | (a) a fixed ratio; (b) a ratio drawn per map from the seed; (c) set by landform | open | |
| Q-190-01 | E-17 / S-190 | Where does a generated cover obstacle's height in layers come from on a land map? Q-098-02 leaves asteroid height with held map content. | (a) from the terrain feature it is (boulder, wall, tree line) and the kit; (b) from the band it stands on; (c) drawn from the seed | open | |
| Q-191-01 | E-17 / S-191 | How are the sites found: one scoring that finds the first base and then the others (option 4C), or a scoring per kind of place? | (a) the prototype's scoring extended to every site; (b) a scoring per kind; (c) rule-based search over the terrain per kind | open | |
| Q-191-02 | E-17 / S-191, S-195 | How many economic locations, expansion sites and neutral settlements per map, and how far apart? | (a) fixed counts per canvas size; (b) counts scale with players and canvas; (c) counts from the situation | open | |
| Q-191-03 | E-17 / S-191 | What does "opposite the objective" measure for the significant resources? | (a) on the far side of the map from the objective; (b) farther from the objective than from the attacker's base; (c) on the other side of the objective from each side's base | open | |
| Q-191-04 | E-17 / S-191 | On a terrain-first map, what does the archetype decide and what does the terrain decide? Q-119-02 closing removes the library that carried the archetype's shape. | (a) the archetype fixes canvas category, objective type and the sides' roles, the terrain the rest; (b) the archetype also biases the landform; (c) the archetype biases the site-finding weights | open | |
| Q-192-01 | E-17 / S-192 (and E-15 S-126) | How many strongpoints does a map have when the relief gives few or many band slopes? E-15 R-126-01's count formula comes from region military and says nothing about where. | (a) one per band slope worth holding up to a cap from region military; (b) the E-15 count, placed on the best slopes; (c) all slopes above a size | open | |
| Q-192-02 | E-17 / S-192 | How wide is a generated choke? R-113-05's width ratio times 200 wu no longer applies. The width is Westley's. | (a) keep 200 wu as the formation-width measure and require a minimum width in formations; (b) a width set per choke by the terrain; (c) decided in the layer lab | open | |
| Q-192-03 | E-17 / S-192, S-197 | Must a vantage on a high band be reachable by walking units, as R-113-04 requires today? | (a) yes, by slope; (b) no, reachable by flying units only; (c) at least one vantage per map is walkable | open | |
| Q-192-04 | E-17 / S-192 | How many chokes, slope tops and tall-cover places must a map offer for the layer plays, and what happens to a map that offers none? | (a) at least a stated count of each, regenerate otherwise; (b) a count over the whole run of maps (the layer lab's 80 percent condition); (c) report only | open | |
| Q-192-05 | E-17 / S-192 (E-22 S-174, S-176) | Does the generator output raid lanes and shipment routes, or does the economy find them from the terrain during play? Not the same idea as S-165's speed lanes. | (a) generator outputs lanes; (b) found at play from the route grid; (c) set per base when the base is placed | open | |
| Q-193-01 | E-17 / S-193 | Which events start a growth wave? | (a) a shipment arrives, an expansion is founded, a season turns; (b) those plus a capture or a battle's end; (c) set per era | open | |
| Q-193-02 | E-17 / S-193 | How many lot stages are there, and at what densities does a lot rise? The numbers are Westley's. | (a) five stages: empty, staked, scaffold, small, large (option 3A); (b) fewer; (c) per kit | open | |
| Q-193-03 | E-17 / S-193 (E-01 invariants) | How does a building inside a cliff or behind a waterfall appear in the layer mask and land flag? | (a) the opening changes the land flag at that spot; (b) cosmetic only, the mask is unchanged; (c) only player-placed buildings open the mask | open | |
| Q-194-01 | E-17 / S-194 | How closely must the fine formula agree with the coarse grid where play depends on it, and which wins a disagreement? The tolerance is Westley's. | (a) fine detail is a ripple that cannot move ground across a band edge; (b) the sim's grid wins and the client snaps ground contact to it; (c) play follows the grid and visuals may differ | open | |
| Q-195-01 | E-17 / S-195 | What is the largest present canvas? The landscape decision and the prototype say 32,000 wu; R-116-01 and `OM_CANVAS_SIZE_RANGES_LARGE_HI` say 28,000 wu before the 30 percent modifier. | (a) 28,000; (b) 32,000; (c) 24,000 base plus 30 percent, about 31,200 | open | |
| Q-195-02 | E-17 / S-195 | Does the region modifier of R-116-02 (plus or minus 30 percent) apply at 64,000 wu for 4 to 6 players? | (a) yes; (b) no, the size is fixed; (c) a smaller swing | open | |
| Q-197-01 | E-17 / S-197 | How does the fairness acceptable range take the situation as an input when the map is deliberately slanted (a defender has the better position)? | (a) the range is centered on the slant the situation gives; (b) a score is logged per side and no range applies; (c) the slant is capped and fairness judged inside the cap | open | |

## 3. Flags to close

| Flag | Closed by |
|---|---|
| Q-119-02 | Landscape README "Mockup review 2", item 1, with Westley's go-ahead on the prototype: terrain first, no skeleton library, the layout derived from terrain, fairness checked on the derived spine. Candidate (b), fully generated from the seed. Closing it makes Q-112-01 and Q-113-01's library question moot, and opens Q-191-04. |
| Q-118-01 | Already closed (a); E-17's open-flag line no longer lists it. |
| Q-119-01 | Already closed (c); no longer listed. |
| Q-166-01 | Already closed. |

Not closed here: Q-118-02 (still open, kept in S-116).

## 4. Needs a ledger row (tested rules whose direction changed)

All cited by tests under `tests/csim/`, text left untouched, a direction note placed under the story heading:

- S-112: R-112-01, R-112-02, R-112-03, R-112-04, R-112-05, R-112-06 (`test_E17_S112_bones_from_the_library.py`).
- S-113: R-113-01 (also `csrc/mission.c`), R-113-02, R-113-03, R-113-04, R-113-05.
- S-114: R-114-01, R-114-02, R-114-03, R-114-04, R-114-05.
- S-115: R-115-01, R-115-02, R-115-03.
- S-116: R-116-01, R-116-02 (R-116-02 also `csrc/tactical_mapgen.c`).
- S-117: R-117-01, R-117-02, R-117-03.
- S-119: R-119-01, R-119-02.

R-118-01 to R-118-03 are cited by tests but no direction changed, so no note and no ledger row. S-165 is untouched. S-166's rules (R-166-01 to R-166-06) are cited by nothing, so they were rewritten outright (R-166-01 verbatim and R-166-04 for E-19 R-159-17's citation kept by id).

## 5. Findings resolved

Rows of `group_2_missions_maps.md`, E-17 section and the cross-epic and decisions lists:

| Finding | Resolution |
|---|---|
| Purpose | done: Purpose rewritten terrain-first. |
| S-112 R-112-01 to R-112-06 | done: direction note, rules kept (tested). Ledger row needed. |
| S-113 R-113-01 (missing types) | done: S-191 R-191-07 adds the types; R-113-01 untouched (tested). Strongpoint and reinforcement_structure link stated in S-191 and S-192. |
| S-113 R-113-04, R-113-05 | flagged: Q-192-02 (width), Q-192-03 (vantage reachability); rules untouched (tested). |
| S-114 R-114-01 elevation and layer accessibility | done: S-190 R-190-01 to R-190-04, R-190-06; R-114-01 untouched. |
| S-114 R-114-03 (node-first sources) | done: S-186 R-186-03 reverses the order; rule untouched, direction note. |
| S-114 R-114-04 (layer masks) | done: S-190 R-190-01 (ground fills below) and S-188 R-188-05 (space masks stay). |
| S-114 R-114-05 (steep ground blocked) | done: S-189 R-189-02, with Q-189-02. |
| S-114 R-114-01 cover height | done: S-190 R-190-05; Q-190-01. |
| S-115 region shapes terrain, region field | done: S-187 R-187-01 (derived from the seed, region record unchanged, DECISIONS H9); R-187-05 keeps stability and capacity flavoring. Region field flag not needed. |
| S-115 R-115-03 (layouts alone) | left: tested, direction note. |
| S-116 R-116-01 canvas ranges | done: S-195; Q-118-01 dropped from the open-flag line; Q-195-01 (28,000 against 32,000, flagged not settled); Q-118-02 stays open. |
| S-116 small canvas with fitted relief | flagged: Q-188-02. |
| S-117 R-117-01, R-117-02 fairness | done: S-197 R-197-01, R-197-02, R-197-04; Q-197-01. |
| S-117 R-117-03 library constraints | done: S-197 R-197-03 on the derived map. |
| S-118 pointer on one-way fronts | done: pointer to E-15 S-130 in the Open flags line; Q-118-03 for strongpoint drift. |
| S-119 R-119-02 procedural architecture | done: direction note, S-196 holds one generator, one field map, two kits, the placer. Open-flags line corrected (reference exists, Q-119-01 closed). |
| S-165 travel lanes | left: told to keep it as is. Raid lanes against speed lanes flagged as Q-192-05. |
| S-166 R-166-02, R-166-03 (placing buildings, three decisions on placement) | left: placement belongs to E-22 S-168 (pointer in R-166-02 and R-193-03). The conflict between "anywhere", "lots are limited" and "a solo commander does not place" is E-22's to resolve. |
| S-166 R-166-03 (site: whatever the terrain gives; second side's base, expansion, resources) | done: S-191; Q-191-01 (how sites are found), Q-191-02, Q-191-03. |
| S-166 R-166-04 (mixed ground, slopes, reachability) | done: S-189; Q-189-01, Q-189-02, Q-189-03. |
| S-166 R-166-04, R-166-06 versus space | done: S-188 R-188-05 (space layers stay pure altitude), Q-166-02 cited. |
| S-166 R-166-06 meadow-slope test | done: S-188 R-188-03 with detector and positive control; Q-188-01. |
| S-166 R-166-06 band heights output | done: S-190 R-190-04 (amends the E-01 Q-E01-01 note; E-01's own drafter owns that text). |
| S-166 R-166-03 (density field, waves, stages) | done: S-193; Q-166-03 carried; Q-193-01, Q-193-02. |
| S-166 R-166-03 (buildings in cliffs) | flagged: Q-193-03. |
| S-166 R-166-03 (region decides, landforms) | done: S-187; Q-187-01. |
| S-166 R-166-05 (one world, determinism, coarse/fine) | done: S-186 R-186-04, R-186-05 and S-194; Q-194-01. |
| Scale requirements | flagged: Q-186-01; confirmed figures kept. |
| Inputs table | done. |
| Obviously working in 60 seconds | done. |
| Ways this could be wrong | done. |
| Depends on | done (E-19 S-159, E-22, E-16, E-01; E-21 library dependency reduced to today's rules). |
| Gate table | done in form; the gate is marked "redrafted, not yet rerun" and "not passed". The architect reruns it. |
| Cross-epic: parity P4 pointer | done: line in Depends on. |
| Cross-epic: E-01 R-010-01 and Q-E01-01 pointer | done in S-190 R-190-04; E-01's drafter edits E-01. |
| Decisions with no home: bases, expansions, economic locations, resources opposite the objective, strongpoints | done: S-191, S-192. |
| Decisions with no home: space against land maps | done: S-188 R-188-05. |
| Decisions with no home: chokes, slope tops, tall cover as plays | done: S-192 R-192-04; Q-192-04. |
| Decisions with no home: blind shipments and raid lanes output | flagged: Q-192-05. |
| Could not judge: strongpoint drift | flagged: Q-118-03. |
| Could not judge: five bands on a small canvas, largest canvas, density field location | flagged: Q-188-02, Q-195-01, Q-166-03. |

## 6. Could not do

- Whether Westley's go-ahead on the prototype also approves "no skeleton library" as bible direction: the brief says to treat it as decided, so I did, and proposed closing Q-119-02. The landscape README itself still says "Nothing below is bible text yet". The architect should confirm.
- Cross-epic overlap: Q-192-01 (strongpoint count) is also the subject of the E-15 finding, and Q-191-02 and Q-192-05 touch E-22's S-175 and S-176. The E-15 and E-22 drafters may open their own flag for the same question. Merge duplicates when the register rows are added.
- S-193 R-193-03 (clear and refill) is in E-17 while E-22 S-168 takes over "the city reshapes around a placed building". I kept the self-built side here (what the pieces do) and left where and how a player places a building to S-168. Check there is no double rule.
- Count figures (how many economic locations, strongpoints, vantages, stages) and every threshold are left as flags, as instructed.
- No test, code or other doc touched. `stories.md` and the register are not edited; rows above are for the architect to apply.
