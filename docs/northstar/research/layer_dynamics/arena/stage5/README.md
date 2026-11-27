# Lab stage 5 probe scenes (H-091, R-091-16 and R-091-17)

Architect-made probes for Westley to redraw, not catalogue layouts. Westley authors the layouts (feedback 2026-10-30): none of these is in `catalogue/` or `approved.toml`, each file says DRAFT and "Architect-made probe, not a catalogue layout" in its header, and the ids (L-9401 to L-9406) are kept clear of the catalogue's L-0001 to L-0084.

Run each with `python -m scripts.skilllab.arena.run --layout <file> --seed 1 --out <dir> --facing on` (sight off; the arc is the drafted 90 degrees). Orders are rule R2 (DEC-lab-amove-rule-2026-11-01): side A holds with no order, side B attack-moves onto side A's centre of mass; no scene has both sides moving. North is -y. Every feature is on the 100 wu grid.

| File | Id | What it isolates |
|---|---|---|
| `front.toml` | L-9401 | The holder (8 Vanguards, 2 ranks of 4, 40 wu apart, at (2000, 2000), facing east) attacked by the same block of 8 from the east, its front. The front rank is 200 wu from the holder's centre, inside the 300 wu Vanguard range, so the first shots fall in the first ticks and the holder has no time to turn. |
| `side.toml` | L-9402 | The same two blocks, the attacker's block turned 90 degrees about the holder's centre: it comes from the north, the holder's side. |
| `rear.toml` | L-9403 | The attacker's block turned 180 degrees: it comes from the west, the holder's rear. |
| `climb_flat.toml` | L-9404 | The walk alone: 8 Vanguards walk about 1700 wu over flat ground at a holder at x 2700 to 2740. |
| `climb_slope.toml` | L-9405 | The same units and distance, with the stage 3 slope (x 2000, length 600, width 200, band 0 up to band 1) between them and the holder one band up, 400 wu past the top. The only difference from `climb_flat` is the climb. |
| `objective_ring.toml` | L-9406 | Drafted from his recorded words in `docs/northstar/research/layer_dynamics/heuristics.md`: "2 groups of units come at two different angles, surrounding blue. Red would be expected to win 80%". The holder is the front scene's block; the attacker is two groups of 4 (`arc` tag 0 and 1) on rings 250 wu from its centre, 150 degrees apart. `predict_rate` 0.2 is side A's rate, red 80 percent. Headcounts, the 250 wu and the two bearings are the Architect's draft; there is no objective marker (the lab draws none). |

`front`, `side` and `rear` differ only by the direction of approach (R-091-17): the attackers are the front block rotated about the holder's centre, same shape, spacing and distance to contact. A 400 wu ring was tried for the objective ring and ended `apart` (two end units of the groups stopped 360 wu out, in the lab's known stuck-behind-the-line way), so 250 wu keeps every attacker in range from the start.

Tests: `tests/skilllab/arena/test_stage5_scenes.py`.
