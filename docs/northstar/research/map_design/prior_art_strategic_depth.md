# Prior art: which landscape conditions induce strategic depth

Research draft, 2026-10-05, for Westley. Purpose: feed the later step of choosing the pillars of intelligent map layout. Nothing here is a decision. Every number is prior art from another game or paper, not a game number. Terms follow the game: the five skills (S1 landscape, S2 formation, S3 layers, S4 enemy position, S5 unit-type matchup) from `docs/northstar/research/layer_dynamics/README.md`; "who gets shots off, and for how long" is the yardstick.

Evidence quality note. Many pages (tl.net, Liquipedia, ResearchGate, academia.edu, ACM, GameSpot) refused direct fetch (HTTP 403), so several claims below rest on the search-result summary of the named page, not on a read of the full text. Those are marked (summary). Where a page was read in full there is no mark.

## 1. StarCraft 2 and Brood War

| Finding | Source |
|---|---|
| Team Liquid Map Contest guideline: average rush distance (main ramp to main ramp) is 35 to 45 s overall; by category, rush maps 33 s or less, standard 33 to 38 s, macro 38 to 43 s (summary). Playable area guidance 16,000 to 22,000, later 14,000 to 18,000. Stated as guidelines, not rules. | https://tl.net/forum/starcraft-2/534744-team-liquid-map-contest-11 , https://tl.net/forum/starcraft-2/610110-team-liquid-map-contest-18-presented-by-monster-energy |
| Contest "challenge" maps deliberately make starts close by air but far by ground, favouring aggression from both sides (summary). | same contest pages |
| Blizzard's own map notes name the ingredients: "standard complement of chokes, open areas, and choices of expansion" (Simulacrum); central bridges for defence and forward high-ground bases as late-game focal points; rocks at both third options for early defence; mineral walls that block the shortest expansion path. | https://news.blizzard.com/en-us/starcraft2/23223597/new-ladder-maps-for-2019-season-4 |
| Zen has two natural entrances: one a single tile wide (widened by mining out minerals) and one six tiles wide. Numbers are a rare published choke width, with a way to change it during play. | same Blizzard page |
| Eternal Empire: "longer path gives a better angle", i.e. a longer route is offered as a trade, not only a cost. | same Blizzard page |
| Blizzard removed 1v1 maps to reduce maps that heavily favour one all-in (Blink), and also rotated old maps out for freshness. Reason given for removal is balance skew plus age; no published threshold. | https://news.blizzard.com/en-us/article/13480732/new-ladder-maps-for-2014-season-2 (summary) |
| High ground vision: units on high ground see low ground; ground units at the bottom see less up the ramp; Force Field on a ramp denies vision and forces a spotter air unit or a scan (summary). | https://liquipedia.net/starcraft2/High_Ground_and_Low_Ground , https://tl.net/forum/starcraft-2/143101-fixing-starcraft-2-high-ground-and-map-design |
| Map-maker advice: tighter main/natural ramps let players be more economical and are easy to wall; critics say SC2's wide, open ramps are "tactically worthless"; a natural mineral line should be safe from siege fire; a main should have a second way in for harassers (summary). | same tl.net page, https://tl.net/forum/sc2-maps/297380-mapmaking-for-beginners-part1 |
| Brood War: Fighting Spirit's middle expansion is rewarding but risky; its natural is easy to harass. Said to be part of the pro-map "trifecta" with Lost Temple and Python (summary). | https://liquipedia.net/starcraft/Mapmakers (summary) |

Reading: the strongest repeated themes are a measured rush distance, a defensible but not walled-forever natural, a choice of third bases with different risk, and ramps narrow enough to matter. Published widths are scarce.

## 2. Other RTS

| Game | Finding | Source |
|---|---|---|
| Age of Empires 2 | Arabia is open: armies reach an economy from several directions and aggression pays. Black Forest has a tree wall with chokepoints that are easy to wall, so players wall early, boom, and combat is delayed to the late game. Arena is pre-walled with a big open middle; it favours boom because a rush must cut through walls and towers. Lesson: the same economy rules give three games depending only on how closable the chokes are. | https://ageofempires2.wiki.fextralife.com/Arabia , https://ageofempires.fandom.com/wiki/Black_Forest , https://ageofempires.fandom.com/wiki/Arena (all summaries) |
| Company of Heroes | Capturable strategic points control the sector around them; income needs a contiguous connection to the base; designers wanted a front line, a relatively safe rear, and supply lines that encourage mobile play. Cover gives a large defensive bonus so open ground is a disadvantage. | https://www.gamespot.com/articles/company-of-heroes-designer-diary-5-building-a-better-real-time-strategy-battlefield/1100-6155869/ (summary), https://steamcommunity.com/sharedfiles/filedetails/?id=121561752 |
| Total War | A chokepoint (street, gate, bridge) limits how many can attack at once, prolongs the fight, and bunches the attackers so missiles and artillery do more. A small force gains most from a choke. Uphill fighting lowers charge speed and impact. | https://www.pcgamesn.com/total-war-guide-tips (summary) |
| Supreme Commander | On the largest (about 81 km) maps, air and land become slow to matter, and multiple bases are the superior option; chokepoint-heavy, resource-dense maps give long standoffs only nukes and artillery break, and remove mobile warfare. Scale alone changes the game; so does too much choke. | https://gamefaqs.gamespot.com/boards/928861-supreme-commander/44951826 , https://steamcommunity.com/app/9420/discussions/0/3266807987608632338/ (summaries) |
| Warcraft 3 | Turtle Rock was patched to open areas and ease strong chokes that favour ranged units. Guides say expansions should be placed so none is clearly one player's natural, and neutral camps and buildings define a map's identity. | https://liquipedia.net/warcraft/Twisted_Turtles , https://www.hiveworkshop.com/threads/hive-melee-maps-for-official-ladder.304573/ (summaries) |

Degenerate patterns seen: closable chokes lead to turtling (AoE2 Black Forest, Supreme Commander standoffs); a choke that favours one unit class is patched open (Warcraft 3); pure scale or open space starves the tactical layer (Supreme Commander large maps).

## 3. FPS and arena level design

| Idea | Finding | Source |
|---|---|---|
| Three lanes | Counter-Strike's archetype: a long side, a tunnel side and a mid that feeds both sites. Dust II has three main chokes (Middle, Long A, B Tunnels), simple structure, close-quarters and long-range zones, and kept its layout since 2001 with graphical not structural changes. | https://csdb.gg/maps/dust2/ , https://en.wikipedia.org/wiki/Dust_II |
| Chokes | Spread 3 to 4 chokes, one per lane; it should be impossible to defend all from one spot; both teams should reach a choke at nearly the same time, defenders a few seconds early; each entrance visible from one defender viewpoint. | https://book.leveldesignbook.com/process/combat/balance , https://www.worldofleveldesign.com/categories/csgo-tutorials/csgo-principles-choke-point-level-design.php |
| Pathway ratio | Defenders get more routes into an objective than attackers (Mirage: 3 vs 2 per site). With 5 per team, one extra route "can considerably slow an attack". Short rotation distance (Nuke) lets reinforcements arrive faster. | https://www.gamedeveloper.com/design/a-cs-go-level-design-concept-the-pathways |
| Balance method | Aim for about 50 percent win rate; symmetric maps are easiest, asymmetric are realistic but need heavy playtests; prefer fairness (perceived) over strict balance; avoid a "perfect" high-utility low-cost area that becomes the dominant strategy; "on the first pass, double or halve the value". | https://book.leveldesignbook.com/process/combat/balance |
| Sightlines and cover | Vary count and length of sightlines; give several sightlines to one landmark from different vantage points; soft cover blocks sight not fire, hard cover blocks both; in PvP err toward too little cover for clarity. | same balance page |
| Loops | Circular flow and figure-8 layouts avoid U-turns; dead ends should be few (older theory). A later source warns the 1999 anti-dead-end rule was too prescriptive; dead ends and forced indirect routes can serve a purpose. | https://www.alteredgamer.com/game-development/60255-game-design-theory-multiplayer-level-design/ (summary), https://book.leveldesignbook.com/process/layout/flow |
| Verticality | "Increases the amount of player choices in an area" and "gameplay per square meter"; but vertical flow should be purposeful, not everywhere. | https://www.alteredgamer.com/game-development/60255-game-design-theory-multiplayer-level-design/ (summary), https://book.leveldesignbook.com/process/layout/flow |
| Overwatch | Wanted a "front" to the interaction, not circular deathmatch flow; attackers push through chokes and uphill while defenders hold high ground; designers check every map with a "high pass" for flyers and snipers so every hero has options. | https://www.pcgamesn.com/overwatch/overwatch-designer-jeffrey-kaplan-on-the-art-and-science-of-building-a-new-breed-of-shooter (summary), https://dotesports.com/news/eichenwalde-overwatch-map-design-14369 (summary) |

What transfers to a top-down five-layer RTS: choke count per lane; arrival-time parity; pathway ratio (flank routes as the lever); several sightlines onto one landmark; soft vs hard cover (the game already has "ground blocks sight"); the "high pass" idea (check each map for every layer/unit class). What does not: first-person aiming sightlines, circular deathmatch flow, spawn-camping rules, jump pads. Not found as a citable talk: Totten's text, Halo's map talks, the phrase "lines of sight versus lines of fire" as a source.

## 4. Formal and academic work

| Work | Finding | Source |
|---|---|---|
| Togelius, Preuss, Yannakakis et al., "Multiobjective exploration of the StarCraft map space" | Evolves complete maps with a Pareto front. Representation: three base positions, resource positions, impassable terrain. Eight fitness terms: base space, base distance, distance to closest resource, resource ownership, resource safety, resource fairness, choke points, path. Skilled players judged that most objectives matched perceived quality; objectives conflict (base distance vs resource distance), so a front, not one score, is the output. | https://www.academia.edu/2425133/Multiobjective_exploration_of_the_StarCraft_map_space (search summary), https://www.researchgate.net/publication/224180081_Multiobjective_exploration_of_the_StarCraft_map_space (summary) |
| Togelius et al., "Controllable procedural map generation via multiobjective evolution" | Same family, adds designer control over the front. | https://dl.acm.org/doi/10.1007/s10710-012-9174-5 (summary) |
| PSMAGE, balanced StarCraft map generation | Five evaluation metrics including start-location distribution and choke-point symmetry, using standard deviation of distances and resource accessibility. | https://www.academia.edu/21774037/PSMAGE_Balanced_map_generation_for_StarCraft (summary) |
| Lara-Cabrera et al., procedural RTS map generation | Balance indicators: territorial, growth and enemy imbalance; dynamism: game length, conquering and reconquering rate; confrontation: battle rate. | https://www.researchgate.net/publication/233732668_Procedural_Map_Generation_for_a_RTS_Game (summary) |
| Perkins 2010 and BWTA2 | Standard terrain analysis: Voronoi skeleton, prune, merge regions, compute optimal chokes between regions. Voronoi-only methods miss "area" chokes. | https://cdn.aaai.org/ojs/12405/12405-52-15933-1-2-20201228.pdf (not readable by fetch), https://www.researchgate.net/publication/220978477_Terrain_Analysis_in_Real-Time_Strategy_Games_An_Integrated_Approach_to_Choke_Point_Detection_and_Region_Decomposition (summary) |

Note: none found measures strategic depth directly; they measure fairness, choke and path properties as proxies. The game's own measure (firing count per side) is closer to the target than anything published.

## 5. Space and three-dimensional play

| Game | Finding | Source |
|---|---|---|
| Sins of a Solar Empire | Movement in three dimensions is possible but play is a 2D plane; 3D manoeuvres have "no tactical value" (reviewer). | https://www.shacknews.com/article/51169/sins-of-a-solar-empire (summary) |
| Homeworld 3 | Players report trouble reading a large 3D space at combat speed; sensor overlays can obscure the field. | https://www.gamesradar.com/games/real-time-strategy/homeworld-3-review/ (summary) |
| Nebulous: Fleet Command | Players find placing waypoints in 3D space hard; the tactical map needs altitude lines and reference points; zoomed-in loses destination, zoomed-out loses origin. Suggested fix: elevation lines as references. | https://steamcommunity.com/app/887570/discussions/0/3809530424059998995/ |
| General | A screen is 2D, so a 3D layout is a projection the player must reconstruct. | https://en.wikipedia.org/wiki/3D_tactics_analysis (summary) |

Reading: free vertical space tends to become either irrelevant (a plane in practice) or illegible (cannot be read or ordered). The pattern that works in the sources is giving height a reason (terrain, sensor reach, altitude lines) and a readable reference. Not found: a source on a game with five discrete free layers plus a sensor ping.

## Candidate pillars

All numbers are prior art, not decisions. Skills S1 to S5 as above. "Both" means space and ground.

| # | Pillar (one sentence) | Evidence | Measurable the lab or layout engine could check | Skills | Kind | Prevents |
|---|---|---|---|---|---|---|
| P1 | Every objective can be reached by at least two routes with unequal cost, so a defender cannot cover all. | CS pathways and "impossible to defend all chokes from one spot"; SC2 contested thirds. | Route count to each objective at least 2; no single point on every route; flank detour 1.5 to 3 times the direct time (prior-art range, my synthesis, not sourced). | S1, S4 | Both | Single-lane stalemate; one-spot turtling. |
| P2 | A choke is real only if it limits who can fire: its width sets the firing count, and it can be widened or bypassed at a price. | Total War choke bunching; Zen one-tile vs six-tile entrances; Warcraft 3 patch. | Units able to fire into a choke mouth vs through it (the lab's firing count); two widths per map (narrow and wide) as in Zen. | S1, S2 | Both (space: a gap between obstacles) | Chokes that are too wide to matter or too closable to ever break. |
| P3 | Both sides reach the key positions in near-equal time, the defender a little early. | CS choke timing; TL rush distance bands 33 to 43 s. | Path-time difference per side to each key position under a few seconds; rush distance inside the declared band for the map type. | S4 | Both | Free first-mover advantage; unreachable far side. |
| P4 | Height has a vision rule that makes the high ground worth taking and costly to hold. | SC2 high-ground vision, Overwatch high ground and uphill pushes, Total War uphill penalties. | Ground: share of ground a high position sees versus is seen from; at least one approach up that is exposed. Space: layers whose sight reach differs. | S1, S3 | Ground mainly; space as layer reach | Dominant unreachable high ground; height that changes nothing. |
| P5 | Every strong position has a counter: another layer, a longer flank, or a type that reaches it. | AoE2 closable chokes lead to turtle; Supreme Commander standoffs; the game's own counter column (C6). | For each declared play on the map, at least one counter play on at least 60 percent of maps (the lab's draft C6 mark). | S1 to S5 | Both | Unbreakable turtle; plays with no counter. |
| P6 | Several sightlines reach each landmark from different vantages, and cover blocks sight in some places and not others. | Level Design Book sightline guidance; Overwatch "high pass". | Count of distinct viewpoints per key site; share of ground under cover vs open; ping reach (space) hitting each site from at least 2 places. | S3, S4 | Both | One camping angle; a map readable only from one place. |
| P7 | Resources and objectives sit in positions of different risk, so choices carry a price. | SC2 third bases, Fighting Spirit middle expansion, Togelius resource safety and fairness terms, Level Design Book risk and reward. | Resource safety (path distance from the nearest enemy-held position) differing by site; resource fairness between sides within a tolerance. | S1, S4 | Both | One best expansion; no reason to leave home. |
| P8 | The map has loops, not only dead ends, so a force can retreat or rotate. | Loop and figure-8 theory (with the caveat that dead ends can be deliberate). | Cycle count in the route graph; rotation time between lanes versus time to reinforce. | S4 | Both | Forced no-win positions; no way to re-route. |
| P9 | The map must be readable: a player can tell layers and heights apart on screen without extra work. | Nebulous altitude lines; Homeworld 3 readability; Sins' plane-in-practice. | Layer shown at a glance; no key site hidden by projection (a QA screenshot check). | S3 | Both, hardest in space | Free vertical space that is irrelevant or unreadable. |
| P10 | Scale fits the unit speed: not so large that fights never happen, not so small that they happen at once. | Supreme Commander big maps; TL playable-area bands; CS rotation. | Time from base to base at the slowest unit pace in the declared band; fights per hour. | S4 | Both | Empty map; instant rush. |

## Open questions for Westley

1. P3 and P10: Team Liquid's 33 to 43 s is for an RTS with individual units at a fixed pace. The game moves groups at the slowest member's pace. Does the game want its own rush-distance band, and who sets it?
2. P1 numbers: the 1.5 to 3 times flank detour is my synthesis, not sourced. No published number found. Does he want the lab to find it from firing counts instead?
3. P2: Zen's mineral wall lets a choke change width in play. Should the game have destructible or otherwise changing chokes, or fixed ones?
4. P4 in space: the five layers have no prior art. Should layer reach (what a given layer can see or hit) stand in for height? This is the biggest gap; no source found on discrete free layers plus a ping.
5. P5 against P2: AoE2 and Supreme Commander show closable or heavy chokes bring turtling, while FPS maps want chokes. How much choke is too much? Sources disagree on scale because their pace differs.
6. P8: sources disagree on dead ends (older theory bans them; newer says they serve a purpose). Does he want dead ends banned or allowed on purpose?
7. Evidence gap: which published numbers should be treated as binding priors at all? Candidate rule: none, only labelled starting guesses.
