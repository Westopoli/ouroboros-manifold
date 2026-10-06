# Pillars of map design that induce strategic depth

Research synthesis, 2026-10-05, for Westley. Nothing here is a decision. Every number is prior art from another game or paper, not a game number; Westley owns the game's numbers. Skills S1 to S5 are those of `docs/northstar/research/layer_dynamics/README.md` section 3 (S1 landscape, S2 formation, S3 layers, S4 enemy position, S5 unit-type matchup). The yardstick is the game's own: who gets shots off, and for how long (`docs/bible/game_bible.md`, principle 4).

Sources: the Gemini deep research, `deep_research_2026-10-05_strategic_multiplayer_map_design.md` (called DR, cited, though much of its evidence is forum posts and wikis), and the Sonnet draft, `prior_art_strategic_depth.md` (called DRAFT). Claims that rest only on a search-result summary, not a page read in full, are marked **(summary)**.

## 1. Why this page exists

Map layout is where strategic depth is won or lost before the first unit moves, and other games have already paid for most of the lessons. This page is held to by the layout engine (E-17 S-112, S-191, S-192), the landscape engine, and both labs (the skill lab and the landscape lab): each pillar names a number they can check.

## 2. The pillars

Eight pillars, merged from DR's five and DRAFT's ten. "Kind" is space, ground, or both (E-01 era kinds).

### P1. Equal numbers, free shapes (topological fairness)

- Principle: fairness is equal travel time and equal exposure to objectives and resources for both sides, not mirror geometry.
- Evidence: Procedural-generation work (PSMAGE) separates geometric symmetry from topological fairness; maps may look different if path-time to resources, chokes and enemy bases is equal. Togelius et al. score "resource fairness" as variance of distance from each start to nearby resources, and "base space" as the share of passable ground near a start. Brood War's Fighting Spirit and SC2's Overgrowth are cited as topologically fair. Level Design Book: aim near 50 percent win rate, fairness perceived beats strict balance. DR: http://julian.togelius.com/Togelius2010Multiobjective.pdf, https://www.researchgate.net/publication/265338188_Geometrical_vs_topological_measures_for_the_evolution_of_aesthetic_maps_in_a_RTS_game ; DRAFT: https://book.leveldesignbook.com/process/combat/balance
- Measurable: path-time difference between the two sides to the objective and to each significant resource; target near zero (Q-191-03 asks exactly this). Also base space inside a fixed walking range of each start.
- Skills: S1, S4. Kind: both.
- Prevents: snowball from a lucky spawn; a map whose fairness is faked by a mirror and solved by memory.

### P2. Paced distance

- Principle: the first contact time between the sides is set on purpose, per map type, and fitted to how fast the units actually move.
- Evidence: Team Liquid Map Contest rush distance (worker from main ramp to opposing main ramp): rush 33 s or less, standard 33 to 38 s, macro 38 to 43 s, with matching playable-area bands. Steppes of War, under 30 s on a 124 by 124 map, made expansion builds unviable and was removed. Metalopolis was removed for close starts that favoured one side. Supreme Commander's very large maps went slow and empty (summary); too-close and too-big both fail. DR: https://tl.net/forum/starcraft-2/599940-team-liquid-map-contest-17 , https://liquipedia.net/starcraft2/Steppes_of_War ; DRAFT: https://gamefaqs.gamespot.com/boards/928861-supreme-commander/44951826 (summary)
- Measurable: base-to-base travel time at the slowest-member group pace, inside a declared band per archetype; fights per hour of play (lab).
- Skills: S4. Kind: both.
- Prevents: matches decided by an early rush before any counter exists; maps so wide that nothing meets.
- Note: the 33/38/43 s bands are for individual workers at a fixed pace. This game moves groups at the slowest member's pace, so the bands are a shape to copy, not numbers to reuse.

### P3. Chokes that bind, and can be paid for

- Principle: a choke is real only if its width limits how many can fire, and the defender or attacker can change that at a price.
- Evidence: Total War: a choke limits how many attack at once and bunches the attackers (summary). Valve-style principles: place chokes before the objective, both sides arrive near the same time, and the defender a few seconds early; 3 to 4 chokes, impossible to defend all from one spot. Togelius "choke points" term scores the narrowest region on the shortest path. Zen (SC2): one entrance a single tile wide (widened by mining out minerals) and one six tiles wide, so width changes in play. Warcraft 3's Turtle Rock was patched open because its chokes favoured ranged units (summary). DR: https://www.worldofleveldesign.com/categories/csgo-tutorials/csgo-principles-choke-point-level-design.php ; DRAFT: https://news.blizzard.com/en-us/starcraft2/23223597/new-ladder-maps-for-2019-season-4 , https://book.leveldesignbook.com/process/combat/balance , https://liquipedia.net/warcraft/Twisted_Turtles (summary), https://www.pcgamesn.com/total-war-guide-tips (summary)
- Measurable: firing count into a choke mouth versus through it (the lab's measure); arrival-time gap of the two sides at each choke; number of chokes per lane.
- Skills: S1, S2. Kind: both (in space, a gap between obstacles).
- Prevents: chokes too wide to matter; chokes so closable the map becomes a stand-off (Age of Empires 2 Black Forest, Supreme Commander (summary)).

### P4. Several routes, unequal cost, with loops

- Principle: every objective has at least two routes of different cost and length, and the route graph has cycles, so one defender cannot cover everything and a force can rotate.
- Evidence: Counter-Strike pathway ratio (defender gets more routes than attacker; one extra route "can considerably slow an attack") and the three-lane archetype; Halo's Lockout is praised because no power position is a dead end; Halo Infinite's long narrow sightlines without loops are criticised. Blizzard: "longer path gives a better angle" (Eternal Empire). Caveat: a later source says anti-dead-end rules were too prescriptive. DR: https://www.destructoid.com/10-best-halo-multiplayer-maps-of-all-time/ ; DRAFT: https://www.gamedeveloper.com/design/a-cs-go-level-design-concept-the-pathways , https://book.leveldesignbook.com/process/layout/flow
- Measurable: route count per objective at least 2; no single point on every route; cycle count in the route graph. The DRAFT's flank-detour ratio of 1.5 to 3 is its own synthesis and has no source.
- Skills: S1, S4. Kind: both.
- Prevents: one-lane stand-off; one-spot turtling; forced no-win positions.

### P5. Height with a rule, and a readable reference

- Principle: height must change what units can see or hit, in a way a player can read, or it is decoration.
- Evidence: see the table below. SC2 vision-only, Brood War miss chance, Total War slope damage, XCOM aim, with the SC2 late-game critique. Space: Nebulous Fleet Command needs altitude lines to read free vertical space; Sins of a Solar Empire's third dimension became a plane in practice (summary); Homeworld 3 players report trouble reading 3D at combat speed (summary). DR: https://tl.net/forum/starcraft-2/143101-fixing-starcraft-2-high-ground-and-map-design , https://tl.net/forum/bw-strategy/528346-how-to-damage-units-under-dark-swarm , https://www.reddit.com/r/Xcom/comments/pjrfjh/xcom_2_does_height_confer_a_defense_buff_or_just/ , https://www.reddit.com/r/totalwar/comments/gns66k/explanation_of_elevation_effects_from_ca/ ; DRAFT: https://steamcommunity.com/app/887570/discussions/0/3809530424059998995/ , https://www.shacknews.com/article/51169/sins-of-a-solar-empire (summary), https://www.gamesradar.com/games/real-time-strategy/homeworld-3-review/ (summary)
- Measurable: share of ground a high position sees versus is seen from; at least one exposed approach up; in space, layers whose reach differs; a QA screenshot check that the layer reads at a glance.
- Skills: S1, S3. Kind: ground mainly; space as layer reach.
- Prevents: unreachable dominant high ground; height that changes nothing; free vertical space that is irrelevant or illegible.

| Game | What height does | Number |
|---|---|---|
| StarCraft 2 | Vision only; full damage once seen | none (deterministic) |
| Brood War | Ground-to-ground attackers miss from low ground | 120/256 miss (46.875 percent); air 0 percent from height |
| Total War | Downhill attackers deal extra damage, per model | up to +30 percent; uphill tires and slows charges |
| XCOM 2 | Aim bonus for the high side; no defence bonus (a defence penalty exists in the files, commented out) | +20 aim |

### P6. Cover and sightlines that alternate open and sheltered

- Principle: the map alternates exposed ground (long sightlines, tension) with sheltered ground (short sightlines, relief), and cover protects from some directions, not all.
- Evidence: Company of Heroes heavy cover: minus 50 percent accuracy and minus 50 percent damage received, directional (nullified if flanked), ignored inside 10 m; the machine gun suppression arc is 90 to 120 degrees (DR's summary table quotes 120 degrees for cover; its text ties 90 to 120 to the gun's arc, so treat the cover arc as unconfirmed); suppression area radius 13 m in CoH2, 15 m in CoH3, with players disagreeing on which is better. Totten's prospect and refuge: an all-open map is a chaotic shoot-out, an all-closed one is camping. Level Design Book: several sightlines onto one landmark from different vantages; soft cover blocks sight not fire. Overwatch's "high pass" check gives every unit class an option. DR: https://steamcommunity.com/sharedfiles/filedetails/?id=3677494697 , https://www.reddit.com/r/CompanyOfHeroes/comments/15k7o8f/why_your_spread_out_units_are_being_suppressed/ , https://www.gamedeveloper.com/design/designing-better-levels-through-human-survival-instincts ; DRAFT: https://book.leveldesignbook.com/process/combat/balance , https://dotesports.com/news/eichenwalde-overwatch-map-design-14369 (summary)
- Measurable: share of ground under cover versus open; distinct viewpoints per key site; longest unbroken sightline; ratio of sheltered to exposed stretches along each route (alternation, not just ratio).
- Skills: S1, S3, S4. Kind: both (on the ground cover is terrain; in space it is obstacles and ping reach onto a site).
- Prevents: one camping angle; the unbreakable static defence; raw aim or raw numbers deciding everything.

### P7. Escalating exposure

- Principle: value sits in the open map, and each further gain needs more risk, so staying home is never the best play.
- Evidence: Fighting Spirit: safe main and natural, then a risky wide middle expansion. Warcraft 3: power in neutral camps, items and experience, with camp spacing setting early pace and a strong camp item able to skew hero balance. DR: https://www.reddit.com/r/WC3/comments/kzruie/competitive_map_pool_2021_discussion/ ; DRAFT: https://liquipedia.net/starcraft/Mapmakers (summary), https://www.hiveworkshop.com/threads/hive-melee-maps-for-official-ladder.304573/ (summary), plus the Togelius "resource safety" term.
- Measurable: resource safety (path distance to the nearest enemy-held position) differs by site; every site beyond the first needs a longer exposed route than the one before.
- Skills: S1, S4. Kind: both.
- Prevents: infinite turtling; one best expansion; no reason to leave home.

### P8. Every strong position has a counter

- Principle: a position that wins is answered by another layer, a longer flank, or a unit type that reaches it.
- Evidence: Age of Empires 2: the same economy gives three games depending on how closable the chokes are (Arabia open, Black Forest and Arena walled, boom) (summary). Brood War: Terran is held to favour open maps, while short-range and splash units want chokes; a chokeless map gives endless kiting. Daedalus Point (SC2) let blink units hit and retreat over dead air where no ground unit could follow. A healing shrine on Ghost River was stripped from ladder versions because attackers could retreat, heal and strike again. DR: https://www.reddit.com/r/broodwar/comments/13zoz30/balancing_the_game_by_balancing_the_maps/ , https://www.reddit.com/r/starcraft/comments/1xxdzc/daedalus_point_a_case_study_in_how_to_make_a/ ; DRAFT: https://ageofempires.fandom.com/wiki/Black_Forest (summary)
- Measurable: each declared play on a map has a counter that takes back at least half its advantage on at least 60 percent of maps (the lab's draft C6 mark, not confirmed by Westley); no dead zone that a whole unit class cannot reach.
- Skills: S1 to S5. Kind: both.
- Prevents: unbreakable turtles; plays with no answer; unpunishable harassment from safe dead space.

Not carried as pillars: Rainbow Six floor beams and Overwatch payload geometry (DR) are first-person micro-architecture with no counterpart in a top-down game.

## 3. Findings that bear on decisions already taken

| Finding | Decision it bears on |
|---|---|
| SC2's high ground is deterministic vision (low ground cannot see up; full damage once seen). | Matches R-005-09 (high ground sees down, low ground never sees up, "zero, like starcraft 2"). Its known late-game critique, that spotters make height irrelevant (DR), bears on the ground era's seer and scout units (R-005-12): if spotters are cheap and universal, the rule loses its value. |
| Fairness is equal path-time, not mirror geometry (PSMAGE). | Matches Q-191-03 ("I don't care what the shape is, I only care about those numbers") and the switch of Q-191-13. Both name the same check: path-time difference per resource and objective. |
| Power in the open map, not at home (Warcraft 3). | Matches S-177 (significant resources opposite the objective). It gives the check: each further site carries more exposure. |
| The open/closed paradox: wide maps favour long-range kiters; chokes exist so short-range and splash units can balance them (Brood War, Warcraft 3). | The lab's composition axis must be read against choke count. A composition result on a choke-rich map and on an open map are different questions; averaging them hides it. |
| Pacing tools: slow zones, speed zones, destructible debris on a third-base path (Team Liquid contest maps), and Zen's mineral wall. | A layout knob the engine lacks. Travel time can be tuned without changing size, and a path can open or close in play. |

## 4. Decisions this raises for Westley

Candidate register rows; no recommendation. Ids are placeholders until entered in `docs/northstar/ambiguity_register.md`.

| Id | Question | Candidates |
|---|---|---|
| Q-MAP-01 | What does high ground do on the ground, beyond vision (R-005-09)? | (a) nothing, vision only, as SC2; (b) a miss chance for ground attackers from low ground, as Brood War (120/256); (c) damage scaled by slope, as Total War (up to +30 percent downhill); (d) an aim bonus for the high side with no defence, as XCOM (+20) |
| Q-MAP-02 | Does ground cover protect by direction? | (a) height-only cover: cover is whatever blocks sight (R-005-10), no direction; (b) directional cover, damage and accuracy cut only from the front arc, void when flanked or at close range, as Company of Heroes (minus 50 percent, close-range void under 10 m); (c) directional only for chosen strongpoints |
| Q-MAP-03 | Does the layout kit get pacing tools? | (a) no, distance only; (b) slow and speed zones; (c) destructible blockers on route openings (debris, as Zen's mineral wall); (d) both (b) and (c) |
| Q-MAP-04 | Are rush-distance bands set per mission archetype, and who sets them? | (a) one band for all; (b) a band per archetype, the lab proposes numbers from group pace and Westley confirms; (c) bands only for archetypes with a rush play |
| Q-MAP-05 | Is prospect-refuge alternation a layout check? | (a) no, left to the landscape engine's judgement; (b) a check on routes (exposed and sheltered stretches alternate); (c) a check on key sites only (every site has an open approach and a sheltered one) |

## 5. What has no prior art

Discrete free layers plus a sensor ping, the space era kind (E-01 S-005, S-006, S-162), has no precedent found in either source. The nearest games reduce the third dimension to a plane (Sins of a Solar Empire, summary) or to something players cannot read (Homeworld 3, Nebulous: Fleet Command), and none gives layers a hard pass-or-fail sight limit that a ping crosses. P5's evidence for space is therefore about legibility, not balance. Pillars P3, P4 and P6 carry over in the plan view, but nothing about layer reach, going dark, or pinging is supported by prior art; those are tested by the game's own skill lab.

## Closing note: what could not be found

- No published measurement of strategic depth itself; the formal work measures fairness, choke and path properties as proxies, and the lab's firing count is closer to the target than any of them.
- Published choke widths are scarce (Zen's one tile and six tiles are the exception).
- No citable source for Totten's text beyond the Game Developer article, for Halo map talks, or for the phrase "lines of sight versus lines of fire".
- The flank-detour ratio (1.5 to 3 times) is the draft's own estimate, not sourced.
- Many cited pages refused direct fetch (tl.net, Liquipedia, ResearchGate, academia.edu, ACM, GameSpot); claims through them are marked (summary) where only the search summary was read.
- DR's hard numbers come largely from forum posts (Reddit, Steam guides, tl.net threads); treat them as starting guesses, not binding priors. The DRAFT proposes the same rule: labelled starting guesses only.
