# SIT-0000 open_field (template; copy, renumber, fill)

Stage: 1
Kind: open_field            (one of: open_field, chokepoint, vantage, cover, objective, staging, transit, flank_route, hazard_anchor, slope, city, trap)
Field: small_flat           (a preset name from scripts/skilllab/catalogue/presets.toml; small_flat is 4000 x 4000, one layer)
Predict: A                  (A, B or draw)
Expected win rate: 0.98     (the probability of the side named in Predict, your heuristic; see ../heuristics.md. The converter stores side A's: this number for Predict A, one minus it for B, 0.50 for draw where the number is ignored)
Orders: both_same_point     (both_same_point, hold:A or hold:B; see docs/stories/H-052.md)
Orders point: midpoint      (midpoint, or x y in world units: the exact spot both sides attack-move to)
What to expect: A closes and wins    (optional, one sentence: what the replay should show; the stage 2 page prints it)
Approve means: The role numbers are right    (optional: what an approve says about the game)
Deny means: The role numbers need tuning    (optional: what a deny says)
Why: Equal roles and equal counts, but A starts closer to the centre and engages first.
Measures: Whether starting closer to the centre decides a fight between equal forces: A winning means the closer start is worth the walk it saves, B winning or a draw means it is not.   (required, one sentence: what this situation tests and what each result would mean; no Measures, no layout, H-076)

## Sides

| side | role     | count | anchor x | anchor y | facing | range | layer | shape | centre_x | centre_y | radius | start_deg | end_deg |
|------|----------|-------|----------|----------|--------|-------|-------|-------|----------|----------|--------|-----------|---------|
| A    | Vanguard | 16    | 800      | 2000     | east   | 0     | 0     | block |          |          |        |           |         |
| B    | Vanguard | 16    | 3200     | 2000     | west   | 0     | 0     | block |          |          |        |           |         |

One row per block of one role on one side; several rows per side are fine. `count` is 8 to 256 per side in total. `anchor` is the block's centre in world units; units are placed in 40 wu blocks around it. `facing` is one of north, south, east, west or a number in degrees. `range` 0 means the role's own weapon range from the engine. `layer` is 0 on a one-layer field. `shape` is `block` (the default when blank; the arc columns stay empty) or `arc` (stage 2): the row's units sit on one ring of `radius` around (`centre_x`, `centre_y`) from `start_deg` to `end_deg` (degrees, 0 east, 90 south, running clockwise on screen), neighbours 40 wu apart, each facing the centre; `count` must fit the span at that spacing or the converter prints `arc too small` with the radius it needs; the anchor, facing and block columns are ignored for an arc. Each row is its own block or arc: two arc rows are two arcs (each with its own ring columns), and a side may mix arc and block rows. The converter records them as `side_x.arcs`, one entry per arc row.

## Features

| kind      | x    | y    | size      | notes                              |
|-----------|------|------|-----------|------------------------------------|
|           |      |      |           | (none on an open field)            |

Kinds and sizes follow the H-025 round-two schema: `walls` (gap), `plateau` (r), `boxes` (w x h), `ring` (r), `buildings` (r, pitch), `band` (length x width), `ridge` (w x h), `disc` (r), `pocket` (U walls). Leave the table empty for stage 1.

## Defender

none                        (or A or B; the defender holds on guard instead of attack-moving; stage 4 and after)

## Notes for the eye

What I expect to see in the replay, in one or two sentences, so what I expect and what I see can be compared.
