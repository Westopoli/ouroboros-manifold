# Layout engine, round A1: an Assault layout

What this is: the first pictures of a layout the new engine made for an Assault mission (S-247). Nothing here is in the game yet; it is the engine's output drawn flat so you can say whether it reads as a map you would fight on. Every number below is a named draft you can veto. Built 2026-11-05 on branch `s/S-247-layout-kit-assault`; these pictures are engine data, no agent has opened them (DEC-no-look-pass-2026-11-05).

How to read a picture: the attacker (side A) starts at the forward camp (square, one colour); the defender (side B) holds the town (square, the other colour) and the keep (star) beside it. Diamonds are the two prizes (significant resources), hollow circles the expansion sites, the gap between hatched walls is the choke (its width is to scale), the triangle with a circle is the high ground and the dashed line shows the lane it overlooks, the dashed strip is the way round the choke. The sidebar on a map lists the seed, the sides mode, both sides' walking distances and every check (green or red).

The sides-mode question (Q-191-13): the three modes show how the defender's ground relates to the attacker's. Mirror: its mirror image. Rotate: a rotated copy. Separate: grown apart with equal numbers.

## What to look at

| Picture | What to expect | Approve means | Deny means |
|---|---|---|---|
| `map_assault_s1_mirror.png` | Seed 1, mirror. One clear road from the forward camp to the town, one choke on it with a longer way round, one hill overlooking the road, two prizes at equal walking distance, the keep beside the town. | This reads as an Assault map I would fight on. | Say what is wrong: the road, the choke, where the keep sits, the height, the prizes. |
| `map_assault_s1_rotate.png` | Same seed, rotate. | Same question; and rotate is acceptable as a mode. | Say what is wrong, or that rotate looks worse than mirror. |
| `map_assault_s1_separate.png` | Same seed, separate (the defender's ground grown apart). | Same question; and separate is acceptable as a mode. | Say what is wrong. |
| `sheet_assault_mirror.png` | Seeds 1 to 12 in a grid, each with `6/6` under it. The twelve should differ from one another. | The twelve are different enough and fair enough. | They look the same, or one looks wrong (name the seed). |
| `sheet_assault_rotate.png` | Same, rotate. | As above. | As above. |
| `sheet_assault_separate.png` | Same, separate. | As above. | As above. |

Your word on the three sides modes (which one a map uses, or all three) closes Q-191-13. Say "approve" for the engine when it reads right; any denial becomes round A2 (a number change edits the drafts below, a rule change amends the spec and reruns the build).

Walking distances of seed 1 (separate), for the record: side A to the first prize 10171.8, side B 10171.68; side A to the keep 16045.87, side B 2690.73 (the keep is deliberately beside the defender).

## The drafts (all yours to veto, none final until the simulation lab reports)

| Name | Value |
|---|---|
| `DRAFT_CANVAS_MIN` | 8000.0 |
| `DRAFT_CANVAS_MAX` | 64000.0 |
| `DRAFT_CANVAS_ASSAULT` | 24000.0 |
| `DRAFT_CHOKE_W_MIN` | 300.0 |
| `DRAFT_CHOKE_W_MAX` | 700.0 |
| `DRAFT_BYPASS_MIN` | 1.5 |
| `DRAFT_BYPASS_MAX` | 2.4 |
| `DRAFT_ASSAULT_CROSSINGS` | 1.0 |
| `DRAFT_ASSAULT_HEIGHTS` | 1.0 |
| `DRAFT_ASSAULT_PRIZES` | 1.0 |
| `DRAFT_VANTAGE_BANDS_MIN` | 1.0 |
| `DRAFT_VANTAGE_BANDS_MAX` | 3.0 |
| `DRAFT_MEANDER_MIN` | 1.0 |
| `DRAFT_MEANDER_MAX` | 1.6 |
| `DRAFT_MEANDER_STEPS` | 12.0 |
| `DRAFT_EQUAL_TOL` | 0.1 |
| `DRAFT_CANDIDATES` | 5.0 |
| `DRAFT_APPROACHES_MIN` | 2.0 |
| `DRAFT_JSON_QUANT` | 0.01 |
| `DRAFT_PX_WU` | 20.0 |
| `DRAFT_AXIS_STEPS` | 24.0 |
| `DRAFT_TURN_Q16` | 65536.0 |
| `DRAFT_MIRROR_AXIS_STEP` | 6.0 |
| `DRAFT_PATTERN_COUNT` | 3.0 |
| `DRAFT_PATTERN_WIDE` | 1.4 |
| `DRAFT_EPS` | 0.0 |
| `DRAFT_INF` | 9000000000000000.0 |
| `DRAFT_SOLVE_STEPS` | 40.0 |
| `DRAFT_BULGE_PTS` | 7.0 |
| `DRAFT_BASE_U` | 7600.0 |
| `DRAFT_BASE_U_JIT` | 900.0 |
| `DRAFT_BASE_V` | 1500.0 |
| `DRAFT_GATE_U` | 4800.0 |
| `DRAFT_GATE_U_JIT` | 600.0 |
| `DRAFT_GATE_V` | 1000.0 |
| `DRAFT_EXP_DU` | 600.0 |
| `DRAFT_EXP_DU_JIT` | 900.0 |
| `DRAFT_EXP_DV` | 2600.0 |
| `DRAFT_EXP_DV_JIT` | 800.0 |
| `DRAFT_OBJ_DU` | 1800.0 |
| `DRAFT_OBJ_DV` | 2000.0 |
| `DRAFT_CROSS_T_MIN` | 0.08 |
| `DRAFT_CROSS_T_MAX` | 0.14 |
| `DRAFT_CROSS_V` | 600.0 |
| `DRAFT_CROSS_LEN` | 2000.0 |
| `DRAFT_CROSS_LEN_JIT` | 500.0 |
| `DRAFT_CROSS_TURN_MAX` | 1.0 |
| `DRAFT_CHOKE_FRAC_MIN` | 0.35 |
| `DRAFT_CHOKE_FRAC_MAX` | 0.65 |
| `DRAFT_CHOKE_LEN` | 900.0 |
| `DRAFT_WALL_SPAN` | 1400.0 |
| `DRAFT_WAYROUND_MARGIN` | 0.05 |
| `DRAFT_VANT_OFFSET` | 2200.0 |
| `DRAFT_VANT_R` | 700.0 |
| `DRAFT_PRIZE_SPUR` | 1500.0 |
| `DRAFT_M_FRAC_MIN` | 0.12 |
| `DRAFT_M_FRAC_MAX` | 0.88 |
| `DRAFT_PAD_BASE_A` | 700.0 |
| `DRAFT_PAD_BASE_B` | 1100.0 |
| `DRAFT_PAD_OBJ` | 800.0 |
| `DRAFT_PAD_RES` | 500.0 |
| `DRAFT_PAD_EXP` | 600.0 |
| `DRAFT_LANE_W_ROUTE` | 160.0 |
| `DRAFT_LANE_W_WAY` | 120.0 |
| `DRAFT_LANE_W_CLIMB` | 60.0 |
| `DRAFT_LANE_W_OBJ` | 140.0 |

`layout_assault_s1_*.json` are the engine's output for the three maps, kept so the pictures can be regenerated: `build/layout_dump --seed 1 --archetype assault --sides separate --out file.json` then `.venv/bin/python scripts/layout/render.py map file.json out.png`.
