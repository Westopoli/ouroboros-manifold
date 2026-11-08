# Why the round A1 layouts all look the same (2026-11-08)

Question (Westley, 2026-11-08): why so little variance, and why does it look like a regression from the layouts of months ago?

## Evidence

1. The October 4 prototype (`git show push/proto-layout:scenes/mockups/layout/layout_gen.gd`, 759 lines, kits in `layout_kits.json`) drew variety from five sources: three variants per piece (home: basin, plateau, bend; gate: wide, twin, ridge; crossing: choke, double; heights: ridge, stair, hill; prize: pocket, backdoor, raid; commons; hidden approach), one or two spine lanes per division pattern (band: one lane, ring and patches: two lanes joined by a link), per-waypoint jitter in the lane frame, an Assault budget of 3 crossings, 3 heights, 1 prize, 2 commons and 1 hidden approach on a 48,000 wu canvas, and growth rules picked in a shuffled order. Its sheet (`docs/northstar/research/layer_engine/pass1/sheet_interception.png`) shows ring roads, two-lane loops and widely different shapes.
2. The C engine built in S-247 has none of that: `DRAFT_ASSAULT_CROSSINGS/HEIGHTS/PRIZES` are all 1, there is one variant per piece, no commons, no hidden approach, canvas 24,000 wu, one spine lane. The plan and spec I wrote cut the Assault budget to 1/1/1 and the pieces to round A only (R-112-03, R-112-07).
3. The spec and plan said "port of `layout_gen.gd`, read with `git show push/proto-layout:...`". The leaf never saw the file: leaf-01's own note says "reference layout_gen.gd not available to me", and its brief did not carry the source. So the engine was written from the description. Leaf-01 also logged: "the division pattern only weights the district fill", "the objective's distance from the defender is a fixed draft (no jitter)", "road, crossing, prizes and heights are built once between the gates", "pure guess" on several pieces.
4. Mirror and rotate transform only the ground (base, gate, expansion); the road, crossing, prizes and heights are built once between the gates, so the choke sits nearer side A in every mode (the "choke closer to blue" finding) and mirror and rotate differ from each other only by a half-turn of the ground.
5. The choke's wall rectangles are drawn across the passage, not along it: leaf-01 logged "axis_k: direction vs perpendicular is a guess". That is the "sideways" finding.
6. Names: "keep", "heights", "prize" are the October prototype's kit labels (objective skin "Keep", kit piece "Heights", kit piece "Prize"), not bible terms. The bible says objective, vantage (R-113-04), significant resource, expansion site, base. The renderer labels (`scripts/layout/render.py` LABEL, and the strings "keep", "height", "prize") put prototype names on the picture.
7. Defender in a corner: both bases lie at `DRAFT_BASE_U` 7,600 wu from the centre along the axis, on a 24,000 wu canvas (12,000 half-width), so each base sits 63% of the way to an edge, and the objective is hung beside the defender's base (`DRAFT_OBJ_DU/DV`). The prototype did the same (`_pos(sign_t * 0.8, 0.0)`). Q-191-11 ruled the objective beside the defender; nothing ruled where on the map the defender stands, and Assault was built as a two-ends road.

## Cause

Variety was cut in the spec (budget 1/1/1, round A pieces only), the prototype source was never given to the builder, and the builder filled the gaps with a fixed structure. The tests pin that structure (exactly one choke, one vantage, two resources), so a richer engine fails them. This is a regression from the prototype, not from the old hand-drawn Python library (eight fixed layouts, `simulation/layout_library/`), which had variety only because a human drew each one.

## Not yet decided (Westley's word)

Assault geometry: defender in the centre of a much larger map, attacker's start on a ring around it at any angle (a seed-chosen bearing), several lanes in from different angles with at least one flanking way round. This replaces the two-ends road and needs a new rule text for R-112-07 and the Assault budget.
