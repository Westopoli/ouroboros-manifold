# Arranging puzzle pieces into a map: methods (2026-10-04)

For Q-191-12. Follows `README.md` in this folder. Nothing here is decided; the decisions needed are at the end.

Westley, 2026-10-04, verbatim: "Instead of having a kit for the whole map, I'd like to have kits for specific **puzzle pieces** of the map, and then organize the puzzle pieces differently every time. This is a complex mechanism, and it needs more archetecting than just the words I'm saying, but we're looking for a system that induces strategic depth without being too repetative."

## 1. What a puzzle piece is

A piece is one part of the map with one job. Each **kind** of piece has its own kit of variants.

| Part of a piece | Meaning |
|---|---|
| Kind | Its job on the map (table below) |
| Variant | One design from that kind's kit |
| Doors | Where routes enter and leave, each with a width and a layer |
| Choice | The decision it forces, in one sentence |
| Numbers | Ranges, not fixed values: widths, walking times, heights |
| Requests | Keep open, keep closed, height, room, number (README section 3) |
| Skin | The landform that carries it: the same choke as a ford, a pass, a gate or a canyon |

Draft kinds, for approval with the prototype (Q-191-05 covers the figures):

| Kind | Job | Example variants |
|---|---|---|
| Home ground | A side's base and safe economy | Walled basin; plateau; river bend |
| Gate | The way out of home ground | One wide mouth; two narrow mouths; mouth under a ridge |
| Crossing | Through or around | Choke with a long way round; two chokes, one hidden; choke with a second way on another layer |
| Heights | Climb or stay low | Ridge with two ways up; stair with a strongpoint; hill overlooking a crossing |
| Prize | A significant resource or expansion site worth leaving the main line for | Dead-end pocket; pocket with a back door; open ground on a raid lane |
| Commons | Open contested ground where formation decides | Wide plain; plain broken by tall cover; settlement |
| Objective ground | Where the objective sits or travels | Keep with three approaches; open crossing; walking route for a moving objective |

Two shapes recur and carry the depth. A **loop** is two routes between the same two points with unequal costs: every "through or around", "climb or stay low" and "open or hidden" choice is a loop. A **spur** is a dead end that holds a prize: taking it is a commitment.

## 2. What makes generated maps feel the same, and what makes them unfair

From shipped games and published work (sources at the end; two research papers could not be read and are cited from summaries only):

- Players of Age of Empires II report that several random maps are one basic map with different settings. Variety in numbers alone does not read as variety.
- Kate Compton's "10,000 bowls of oatmeal": the measure is whether a player perceives two results as different. Fewer, more distinct things beat many near-identical ones.
- Age of Empires IV and Northgard players complain most about luck near the start: one side gets forward gold, the other does not.
- Unexplored builds each level from a small set of loop types (two routes with different obstacles, lock and key, hub). Levels read as different because their structure differs, not their decoration.
- Spelunky fixes a guaranteed route first, then fills rooms from templates typed by their exits, so every level is connected by construction.
- Methods that only match neighbours (wave function collapse, tiles) cannot hold a whole-map number such as equal walking distance without an extra global check.

Rules taken from this for every method below:

1. **Five independent sources of difference**: which variants, how pieces connect, where they sit, each piece's numbers, and its skin. Connection matters most to the eye.
2. **Numbers straddle the break-even.** A 300 wu choke rewards holding; a 700 wu choke rewards going round. Each variant's range crosses the point where the right answer flips (the layer lab measures where that is), so the player has to read the map, not remember it.
3. **Fairness is built in, then checked.** Home ground and gate come from the same kit with matched numbers for every side; the luck is in the contested middle, which both sides reach equally. The request check and the equal-distance check run on every map.
4. **Sameness is measured.** Each map gets a signature (its loop structure and the order of piece kinds along each side's route to the objective). A map too close to a recent one is thrown away and made again.

## 3. Four methods of arrangement

### M1. Slots on a skeleton

A handful of drawn skeletons (two lanes with a cross-link, a ring, an hourglass, three lanes). Each has typed slots: "crossing here", "heights here". A seed picks the skeleton and fills each slot from that kind's kit.

- For: simplest; always connected; easy to audit.
- Against: the skeleton is the part the eye learns. With five skeletons, players will name them within a week.

### M2. Growth by rules

Start from the barest map: home, objective, home. Apply rules one at a time; each rule inserts a piece. "Replace a stretch of route with a crossing." "Hang a prize spur off this route." "Lay heights beside this stretch." The archetype gives the budget: how many of each kind, and where (near home, middle, at the objective).

- For: the structure itself differs from map to map, which is the difference players notice most. The order of rules is a readable account of why each piece is there.
- Against: a grown graph has no shape; placing it on the canvas with the right walking times is the hard step. Unexplored avoids it by growing on a fixed coarse grid. More rules to write and test.

### M3. Jigsaw on a grid

The canvas is cut into coarse squares (about 4,000 to 8,000 wu). Each piece covers one to four squares and has doors on its edges. A solver lays pieces so doors meet. This is the most literal puzzle.

- For: pieces are concrete and can be drawn and judged one at a time; terrain for a piece can be designed with it.
- Against: neighbour matching cannot hold equal walking distance or "the way round is twice as long" without a second global pass; many layouts get rejected. A grid shows through unless the terrain bends it.

### M4. Districts first, then pieces

Two levels. First divide the canvas into districts by role: each side's home, each side's near ground, the contested middle, the objective district. The division itself varies per seed (the middle may be a band, a ring, or two separate patches). Then each district is filled from kits allowed there, by M1 or M2 inside it.

- For: matches how the fight moves (safe ground, contested ground, objective); fairness is easy because home districts are matched and the contested district is shared; scales to four to six sides by adding home districts round the middle.
- Against: two levels to design; district borders must not become a visible pattern.

### Add-on for any method: make several, keep the best

Generate a few candidates per map, score each on the checks (requests met, distances equal, choices present, signature far from recent maps), keep the best. Search-based research on StarCraft and Planet Wars maps works this way. It cannot replace a method; it guards one.

| | M1 slots | M2 growth | M3 jigsaw | M4 districts |
|---|---|---|---|---|
| Maps differ in structure | low | high | middle | high |
| Whole-map numbers hold | easy | middle | hard | easy |
| Intent stays readable | high | high | middle | high |
| Scales to 4 to 6 sides | by hand | yes | yes | yes |
| Effort to prototype | low | middle | high | middle |

## 4. Recommendation

**M4 with M2 inside the contested and objective districts, M1 inside the home districts, and the add-on.**

- Home ground and gate: slots, matched between sides. No luck at the start.
- Contested middle and objective: grown by rules on a coarse grid, so structure differs every map.
- Each grown piece draws a variant, numbers across its break-even, and a skin.
- Every candidate is checked and its signature compared with recent maps.

Whether two sides' halves are mirror images, rotated copies, or different shapes with equal numbers is open (decision 2). Westley's Q-191-03 answer allows different shapes: "I don't care what the shape is, I only care about those numbers."

## 5. What the first prototype pass would show

Flat diagram only, as agreed.

- One map: districts tinted, each piece outlined and named with its choice in one sentence, every route labelled with width and walking time.
- A panel listing the choices this map forces and each check, met or broken.
- A replay key that grows the map one rule at a time.
- A sheet of twelve seeds for one archetype side by side, to judge sameness by eye, with the signature difference printed.
- A switch that turns growth off (leaving slots only), so M1 and the recommendation can be compared directly.

## 6. Decisions needed from Westley

1. **Q-191-12**: the method. Recommended: M4 with growth in the middle, as section 4.
2. **Q-191-13**: how the sides' ground relates. (a) mirror image; (b) rotated copy; (c) different shapes, equal numbers; (d) recommended: the prototype has a switch for all three and he rules after seeing them.
3. **Q-191-11** (open from before): where a fixed objective sits on the seven archetypes where it does not move.
4. The draft list of piece kinds in section 1: add, remove or rename any before the kits are drawn.

## Sources

- Unexplored's cyclic generation: boristhebrave.com/2021/04/10/dungeon-generation-in-unexplored/ ; gamedeveloper.com/design/unexplored-s-secret-cyclic-dungeon-generation-
- Spelunky: tinysubversions.com/spelunkyGen/
- Age of Empires II and IV: liquipedia.net/ageofempires/Black_Forest ; forums.ageofempires.com/t/case-for-fixed-starting-resource-spawn/223626 ; forums.ageofempires.com/t/megarandom-map-generation/224242
- Northgard: steamcommunity.com/app/466560/discussions/2/3062995463270630845
- Wave function collapse limits: boristhebrave.com/2020/02/08/wave-function-collapse-tips-and-tricks/
- Compton: gamedeveloper.com/design/practical-procedural-generation-for-everyone-
- StarCraft and Planet Wars map search (Togelius and others; Lara-Cabrera and others): summaries only, papers not read. link.springer.com/article/10.1007/s10710-012-9174-5 ; link.springer.com/chapter/10.1007/978-3-642-37192-9_28
