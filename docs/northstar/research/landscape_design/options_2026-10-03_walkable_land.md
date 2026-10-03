# Land terrain: options after pass 4 (2026-10-03)

Written under the pass limit (`agile.md`, Prototype gate): pass 3, pass 4 and its rework have gone by without Westley's approval, so this page sets out directions for him to choose from. Numbers are from the pass 4 record and sweep in `README.md` (seeds 11 to 16, ramps on).

## What the prototype showed

Two of Westley's decisions pull against each other on the pass 3 terrain: huge mountains (mockup review 2), and walking units blocked at 30 to 35 degrees who must be able to reach every layer (Q-189-01, Q-189-02).

| Measure | Canvas 24,000, full relief | Canvas 48,000, full relief | Canvas 32,000, half relief |
|---|---|---|---|
| Relief | about 3,770 wu | about 3,770 wu | about 1,850 wu |
| Land too steep at 30 degrees | 65% | 34% | 21% |
| Land a walker reaches from the city core | 5% | 11% | 23% |
| Layers a walker reaches, of 5 | 3.5 | 1.8 | 2.8 |
| Peaks a walker reaches | 0.8 of 7 | 4.3 of 15 | 4.5 of 10 |
| Generate time (GDScript) | 1.6 s | 6.9 s | 1.8 s |

- Steepness falls steadily with less relief and with a larger canvas.
- Reach does not follow it. The city core often sits on a small landmass or a sliver cut off by water, and nothing bridges a river. Lowering the slope alone does not make the map playable.
- The slope footprint (100 to 500 wu) and the fine detail barely change anything; the steepness is in the large shapes.

## Options

**A. Layout first, terrain obeys (recommended).** Stop measuring how much of the land a walker can reach. Place the bases, the objective, the resources and the chokes from the layout, then make the terrain supply a walking route between them: passes cut through ridges, bridges over rivers, ramps between bands. Mountains stay huge and stay mostly impassable; they become the walls that give the routes their shape. This is what Westley ruled under Q-191-04 on 2026-10-03 ("if the layout engine calls for something like a choke, the landscape engine is required to produce it"), and it is the prototype he asked to see. Measure: every place the layout names is joined by a walking route, and both sides are the same distance from the objective and from each significant resource (Q-191-03).

**B. Gentler land.** Relief at half to three quarters on a 32,000 canvas. About 20 to 40 percent of land too steep. Mountains read as large hills. Does not fix the cut-off cores by itself.

**C. Bigger canvas, same mountains.** 48,000 wu keeps the full relief at half the steepness. Costs map size for every match, about 7 s to generate in the mockup (the C generator would be far faster; the ceiling is a 5 s loading screen, Q-186-01), and still leaves cores cut off.

**D. A higher walking limit.** 40 or 45 degrees in place of 30 to 35. Not measured. It changes what a slope means for every walking unit.

A can be combined with B or C. B, C and D alone leave the cut-off core.

## What happens next

Pass 5 is being built as option A, because it is the prototype Westley asked for by name and the direction he ruled. If he prefers another option, pass 5 is still the layout prototype he wanted to see, and the terrain under it can be changed with the relief and canvas sliders that now exist.

## Questions for Westley

1. Is option A the direction: mountains as walls, with routes the layout demands cut through them?
2. If so, is it acceptable that most high ground is for flying units only, with about 30 percent of peaks unreachable on foot being the floor, not the ceiling (Q-192-03 said about 30 percent unreachable is natural; the mockup gives 60 to 90 percent)?
3. Should the relief or the canvas also change (B or C), or stay as pass 3 had them?
