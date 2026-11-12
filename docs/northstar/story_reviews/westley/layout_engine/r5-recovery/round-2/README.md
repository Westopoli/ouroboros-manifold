# R5 study, round 2: the same three sets after your round 1 feedback (2026-11-08)

Same generators and seeds as `../` (round 1), re-shot after four changes. Nothing in them is game code. 1920x1080. The investigation behind the changes: `docs/reports/2026-11-08-r5-round1-water-and-reach.md`. Your round 1 words: `docs/northstar/story_reviews/westley/ruled.md` (2026-11-08 rows).

What changed since round 1:
1. **Water is one thing in every view.** The 3D view (`raw_layout`) used to draw water as a flat sea at height zero, so mountain lakes showed in `walk` and not in `raw_layout` (your L06 example, west of `choke_pass_entrance`). Now every view paints the same cells, and each lake is drawn at its own surface height.
2. **One line of text.** Bottom-left: `seed N  reachable P%`, with ` FAIL` when the prototype's own check fails. Everything else is hidden in a picture. (The small 3D place names on the ground are still drawn; say if they go too.)
3. **Vantages over traffic, lanes by width, loud failures** (assault set only): a vantage must overlook a carved road or a resource site within 600 wu; an unreachable vantage fails loudly (red ring, FAIL in the line and in the file name); lanes per place = 720 / lane width (180 wu gives 4, 600 wu gives 1), at least 3 roads reach the objective; a corridor narrower than the thin road outside a choke's walls is an accidental restriction and fails; dead-end regions are counted.
4. Not yet changed: reachable share and feature scale (peak ramps), bases on hillsides (footings). Those wait on your word on the options in the report (recommended: peak ramps plus footings, relief untouched).

Reading the `reachable` number: percent of land a walker reaches from the player's base at the walk limit (35 degrees in the generator sets, 30 in the library set).

## Set A: terrain-obeys as it is (`obey/`)

| Picture | What to expect | Approve means | Deny means |
|---|---|---|---|
| `obey/obey_16000_1.png` | Seed 1, PASS; water now visible in 3D where the walk view had it | The water and the text fixes read right | Say what still looks wrong |
| `obey/obey_16000_2.png` | Seed 2, PASS | same | same |
| `obey/obey_16000_3.png` | Seed 3, PASS | same | same |
| `obey/obey_16000_4.png` | Seed 4, FAIL (ring): site_1's pad skirt 35.2 degrees, the prototype's own flat-pad check; goes away with footings | same | same |
| `obey/obey_16000_5.png` | Seed 5, FAIL (ring): base_b's skirt 41.2 degrees, same cause | same | same |

Known and not yet fixed in set A: a library drawing (seed modulo 8) still shapes the terrain under the generator's edits in this prototype; the round after removes it so the generator stands alone.

## Set C: the modified R5, assault mode (`obey-assault/`)

All five PASS, no `_FAIL` file. Per seed from the panels:

| Picture | Vantage | Overlooks | Lanes (thin / wide) | Bend of main road | Dead ends | Approve means | Deny means |
|---|---|---|---|---|---|---|---|
| `obey-assault/obey_assault_16000_1.png` | beside the choke | road | 4 / 1 | 1.36 | 0 | The vantage and lane rules read right on this map | Say which rule misfires here |
| `obey-assault/obey_assault_16000_2.png` | beside base B | road | 4 / 1 | 1.30 | 1 | same | same |
| `obey-assault/obey_assault_16000_3.png` | beside the choke | road | 4 / 1 | 3.23 | 1 | same | same |
| `obey-assault/obey_assault_16000_4.png` | beside base B | road | 4 / 1 | 1.38 | 2 | same | same |
| `obey-assault/obey_assault_16000_5.png` | beside the choke | road | 4 / 1 | 1.34 | 0 (2 narrowings, both inside the choke) | same | same |

## Set B: the library drawings bent to terrain (`pass5/`)

Same five layouts as round 1 (01, 03, 05, 06, 08 at seed 11), re-shot with consistent water and the one-line text. L08 is the one you asked to keep; its lane additions come with the reach work in the next round. The `FAIL` on the line here is pass 5's own equal-distance check, which these April drawings never met.

| Picture | What to expect | Approve means | Deny means |
|---|---|---|---|
| `pass5/L0N_s11_raw_layout.png` | The node graph on the 3D ground; lakes now visible | Water matches the walk view | Point to a cell that differs |
| `pass5/L0N_s11_react.png` | Terrain bent to the graph | as above | as above |
| `pass5/L0N_s11_walk.png` | Walkable ground; the one line of text | The text level is right | Say what else to hide or show |

Panel numbers for every picture are in the `.txt` beside it (full panel text, as the `V` key would show it).
