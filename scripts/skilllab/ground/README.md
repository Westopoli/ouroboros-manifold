# Ground lab

Ground scenes on the generated field of seed 11 (canvas 12000, era kind ground; seed 11 generates no slope at 4000). Code: `scenes_ground.py`. Tests: `tests/skilllab/ground/`, `tests/skilllab/integration/test_ground_slope_real.py`.

## s1_slope_top

M1 (Vanguard and Raider in equal halves) on both sides, walking, reach table applied (Vanguard 0 up 0 down, Raider 1 up 1 down; a type walks through `unit_types[name]["movement"] = "walking"`). The holder guards the slope's upper band (layer 2) past the midline of slope 2 (foot (9350, 3150), top (8850, 3150)). The attacker starts at the foot on layer 1 and attack-moves to the holder's placed mean. Setup.point is that mean; nothing is shifted to fit; `build.labels["prefight"]` is `scenes.preflight` of the built Setup (`ok`).

Knobs (`SLOPE_TOP_KNOBS`; the second point of each grid is the engine default):

| knob | grid |
|---|---|
| `OM_TP_SIGHT_EYE_HEIGHT` | 25, 50, 100, 200 |
| `OM_TP_GROUND_FLYER_SEEN_MULT` | 1.25, 1.5, 2, 3 |
| `OM_TP_SLOPE_UP_DIV` | 1.0, 1.1, 1.3, 2.0 (DRAFT: the 0.25x band means nothing for a divisor near 1) |

`OM_TP_SLOPE_UP_DIV` is the knob that moves this scene (walkers climb slower with a larger divisor). `OM_TP_SIGHT_EYE_HEIGHT` and `OM_TP_GROUND_FLYER_SEEN_MULT` are inert here (`INERT_KNOBS`; the first batch reports them inert): every sight line from the top of the slope to its foot is clear at eye 25 and up, and the multiplier acts only on a flyer above the ground's layer, and these Raiders walk. Making them live in the natural scene is a later design call for the Architect and Westley.

## Variants carrying the two controls

- `s1_slope_top_marginal`: the attackers lie along the thin ribbon of band 2 north of the foot, and the holders' post at (8900, 3220) sees none of them at eye 25 and 50 and all of them at eye 100 and 200.
- `s1_slope_top_flyer` (R-005-11): the Raider flies on both sides. The attacker Raiders hover on layer 2 over band 2 ground 1900 wu from the holders, so the holders see them from 2400 wu at multiplier 3 and not at 1.25 to 2. `scenes.preflight` routes a flyer (a type that does not walk) by a straight line over blocks of its own layer, since it has no path on the ground's walk mask.

`INERT_KNOBS_BY_SCENE` lists what each scene leaves inert. In both variants the carried knob changes who is seen first but not the fight's result.

## Parked

`tall_cover` and `tall_cover_counter` (nine cover discs between a blob and guarding defenders, unconfirmed draft) stay for the landscape batch in `scripts/skilllab/batches.py`. The height-rule sweep that stood in for a slope with a timed layer change is retired (R-005-09, S-164): what it showed is now the slope climb (`OM_TP_SLOPE_UP_DIV`), holders on guard on the top band, and the reach table.
