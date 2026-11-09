# R5 study, round 1: water across views, reachable ground, bases (2026-11-08)

Westley's round 1 general feedback on the R5 pictures (`docs/northstar/story_reviews/westley/ruled.md`, rows of 2026-11-08) raised four things: water shown in `walk.png` but not in `raw_layout.png`; too little reachable ground and a landscape that is too large-scale; too much text on the pictures; bases always flat. This report holds the two investigations. The text fix and the water fix are built tests-first on the two prototype branches (`wip/r5-obey-shots`, `wip/r5-pass5-shots`); the reach and bases options wait for his pick.

## 1. Water in `walk.png` versus `raw_layout.png`

Cause: the two views use different water definitions. The walk and react views paint every cell whose water value is 0.5 or more (`pass5_ui.gd:469-483`, flag from `pass5_layout.gd:276`). The `visual` view, which the `raw_layout` shot uses (`qa/r5_pass5.json` steps 46-49: `p4_view=visual`, react off, graph on), draws the ground mesh at its real height (`ground.gd:20-60`) with no water test, and water as one plane at y=0 across the canvas (`placer.gd:621-634`, kit `greek.json` `water_is: surface`). The lake fill of the 2026-11-08 water fix (`_flood_lake`, fill level seed elevation + 150 wu) marks cells at positive elevation as water; the plane sits under the ground there, so the lake is blue in walk and plain ground in raw_layout.

His example, L06 seed 11, west of `choke_pass_entrance` (node ratio 0.5, 0.6 on 24,000 wu; cell 120,144): row 144 has water cells at columns 98 to 105 with elevations 413 to 626 wu, all flagged water, none walkable, none a bridge. Map-wide, 4,947 of 15,095 flagged cells (33 percent) lie above 0 and are invisible in the 3D view. The react on/off difference between the two shots moves 92 cells map-wide and none of these. The graph overlay hides nothing.

Fix (tests first, `tests/test_mockup_landscape_water_views.gd`): one function `FieldMap.is_water(i)` is the only water test; every view paints exactly its cells; the visual view draws each lake's surface at its own fill level, so a mountain lake reads as water in 3D. Scratch probe: `scratchpad/probe.gd` of this session.

## 2. Reachable ground, feature scale, bases

Method: the real scenes were run headless (pass 5 layouts 01, 03, 05, 06, 08 at seed 11 on 24,000 wu; terrain-obeys as-is seeds 1 to 5 on 16,000 wu) and the finished ground measured. Pass 5 walks at 30 degrees (`pass5_layout.gd:35`), terrain-obeys at 35 and counts its carved roads. Scratch scripts of this session: `measure.gd`, `run_p5.gd`, `run_obey.gd`, `run_ramp.gd`, `exp.gd` to `exp3.gd`.

Finding on the as-is set: in the terrain-obeys scene a library layout (seed modulo 8) still shapes the terrain under the obey edits (`p5_layout` set, `p6_info.applied` true), so the set A pictures are not pure terrain-obeys. To be removed for round 2 so the generator stands alone.

### The numbers (percent of land cells; "reached" is flooded from the player base)

| Map | Walkable | Reached | Steep | Cut-off flat | Peaks reached / total | Tall hills (2,000 wu+) reached / total | Hills | Mean / max height wu | Base height wu |
|---|---|---|---|---|---|---|---|---|---|
| L01 | 47 | 35 | 53 | 12 | 1/22 | 1/18 | 27 | 1,624 / 4,017 | 455 |
| L03 | 41 | 29 | 59 | 12 | 5/47 | 1/18 | 19 | 1,601 / 3,543 | 537 |
| L05 | 41 | 24 | 59 | 17 | 0/22 | 0/20 | 24 | 1,579 / 4,514 | 452 |
| L06 | 47 | 37 | 53 | 10 | 1/14 | 4/17 | 22 | 1,524 / 4,524 | 455 |
| L08 | 41 | 23 | 59 | 18 | 0/15 | 1/20 | 26 | 1,535 / 4,122 | 958 |
| Obey 1 | 78 | 73 | 22 | 5 | 5/14 | 2/4 | 13 | 1,178 / 2,731 | 120 |
| Obey 2 | 68 | 65 | 32 | 4 | 10/25 | 2/8 | 13 | 1,248 / 3,193 | 929 |
| Obey 3 | 76 | 71 | 24 | 4 | 3/8 | 2/6 | 9 | 1,200 / 2,830 | 1,078 |
| Obey 4 | 55 | 47 | 45 | 8 | 2/20 | 1/8 | 11 | 1,363 / 4,217 | 831 |
| Obey 5 | 67 | 63 | 33 | 4 | 10/20 | 3/5 | 9 | 1,338 / 2,976 | 1,497 |

Westley's "11%" on L03 is the peaks line ("peaks 5 of 47 reachable (11%)"); land reached there is 28.9 percent. The pass 4 panel floods from the objective and gives the same land figures (34.9, 28.9, 24.5, 36.8, 23.0). Water is 26 to 45 percent of the pass 5 canvas and rings only 0 to 4 points of the cut-off flat ground; steep ground rings 10 to 16 points. Peaks are the pass 4 definition (a local maximum on band 4 or 5); hills are local maxima over 300 wu in a 1,000 wu window.

### Causes

1. Steepness, not water. On pass 5, 53 to 59 percent of land is over the 30 degree limit and a further 10 to 18 percent is flat ground ringed by steep ground. Terrain-obeys: steep 22 to 45, cut-off flat 4 to 8 (smaller map, 35 degrees, carved roads).
2. The slope histogram is flat (L03 per 5-degree bin from 0: 8.9, 8.9, 5.5, 5.5, 5.7, 6.7, 7.3, 8.2, 9.1, 8.5, 8.1, 7.0, 5.3, 3.1, 2.0, 0.3), so every 5 degrees of limit moves 7 to 8 points of land; connection jumps faster (largest walkable region on raw seed 11: 13 percent at 35, 28 at 40, 58 at 45). Limit 30 to 35 lifts pass 5 reach by 2 to 8 points.
3. Feature scale. Noise at 24,000 wu: a continent octave of 16,000 wu wavelength (3,000 to 6,300 wu spread), a hills octave of 3,000 wu (1,300 to 2,200), detail at 600 wu, pass 6 belt noise 4,800, benching every 4,000 wu in 300 wu steps (`field_map.gd:77-79`, `pass6_shape.gd:132`, `pass4_terrain.gd:176`). The hills octave carries about 400 to 680 wu on a 3,000 wu wave, about three times what 35 degrees allows (330 wu); the continent octave alone puts 40 percent of seed 11 over 35. A mountain is 4,000 to 7,700 wu across at half height (17 to 32 percent of the canvas); 19 to 27 hills per map, 17 to 20 of them 2,000 wu or taller. A 5,000 wu peak needs a 7,100 wu run at 35 degrees.
4. Peaks today. `cut_ramps` (`pass4_terrain.gd:~320-390`) only checks that each band has some reached ground, starts at the lowest unreached band and stops after 8 passes; L03 spent all 8 on band 1 and never reached bands 4 and 5. Terrain-obeys cuts 28-degree roads to named places only (`ramp-grade` 28, `ramp-reach` 2,400); peaks are not targets.
5. Bases. Terrain-obeys: `_stamp` levels a 1,200 wu pad flat to the median height within 2r, a 28-degree skirt out to 2,400 wu; the `ring` check demands 35 degrees or less on the skirt. Pass 6 (the valley cause): `HEIGHT_FRAC` puts staging at 0.10 and spawn at 0.13 of relief, objective 0.30, vantage 0.70, a 700 wu valley floor with 1,300 wu shoulders (`pass6_shape.gd:20,160-168`). Pass 5 levels each node with a 250 wu shoulder and scores base cells 0.4 flat, 0.3 open, 0.3 near. Result: base heights 450 to 540 wu (L08 958) against a mean land height of about 1,550. Bible: R-166-03 a base site is "whatever the terrain gives"; R-166-02 a base may span layers.

### Probes (raw recipe, seeds 11 and 13, directional only)

Relief x0.7: over-35 from 58 to 37 percent, largest walkable region 13 to 55 percent; x0.5: 18 and 82. More hill octaves at today's weights: worse (over-35 67 to 72, largest region under 4). Hill weight 0.3 to 0.1 plus 16 and 32 cycle octaves: hills up, steepness flat, region unchanged. Terracing without connectors: 12 to 20 separate walkable terraces, region shrinks. Peak ramps: a straight 28-degree ramp from the nearest reached ground to each unreached hill of 1,500 wu or more is 13 to 17 ramps of 100 to 4,000 wu, 30,000 to 38,000 wu of road, 3.5 to 5.5 percent of land at 500 wu wide.

### Options: reachable ground with the scale kept

- T1 Peak-ramp pass. After the ground is final, every unreached hill of 1,500 wu or more gets a 28-degree, 500 wu ramp from the nearest reached cell; about 30 percent of non-vantage peaks stay uncut (R-192-03); vantages always get two (R-189-07). Tall hills reached from 0 to 4 of 17 to 20 up to about 70 percent; peaks reached from 11 to about 70 percent on L03; land reached up 3 to 5 points only. Cost: 1,200 to 4,000 wu of climb per peak (8 to 27 s for a Raider, 30 to 100 s for a Bastion with the 1.1x uphill). Risk: a straight cut through a 50-degree face scars. Scale unchanged.
- T2 Tame the continent octave (relief x0.7) with 3 to 5 set-piece massifs at 1.2x the old height marked as natural no-go ground. Over-35 from 58 to 37, largest region 13 to 55. Cost: mean peaks 30 percent lower outside the massifs. Risk: against "keep the scale".
- T3 Terraces with guaranteed slopes between bands (28-degree risers, one slope per adjacent pair). Only works with T1 (terracing alone fragments). About 15 to 20 slopes per map; the walk graph connected by construction. Cost: lowering the band step is a bible change (R-166-04, R-166-06).
- T4 Slope-budgeted hill octave (more, smaller hills). More hills, steepness unchanged: does not fix reach alone.
- T5 Raise the walk limit to 40. Land reached up 7 to 8 points per 5 degrees; largest region 13 to 28 on seed 11. Rule change to R-189-02 (35); pass 5's 30 is already stricter than the rule.

### Options: bases in the environment

- B1 Footing, not levelling: the pad request becomes "a connected walkable area of radius r on any band, any slope under the limit", terraced into 2 to 4 steps on a hillside; objective, sites and strongpoints (R-218-01, slope midpoints) use the same footing; `ring` becomes "footing connected, steps under 28 degrees, two routes in".
- B2 Small flat core of 300 wu, the rest of the radius left as the mountain is, one carved road out; sites and strongpoints 100 to 150 wu cores; `ring` replaced by the road's grade check.
- B3 No pad: the base goes where the ground already has a walkable area of the needed size, scored by area, open frontage and height (pass 5's `_pick_base` is roughly this, but it still scores low flat ground and the pass 6 floor decides anyway).

### Recommendation for round 2

T1 (28 degrees, 500 wu, peaks over 1,500 wu) plus B1 with 3 steps; relief and octaves untouched so the scale stays; pass 6 `HEIGHT_FRAC` for bases raised from 0.10/0.13 toward 0.35 so bases can sit on slopes. T2 and T5 held for Westley's word on scale and the limit.
