# Stage 4, L-0039 (cover) investigation, 2026-11-06

Investigator: Sonnet 5.5 sub-agent, read-only, worktree from origin/main. Westley's report: the boxes do not completely obstruct literal line of sight with both sides, yet neither side attacks, so the LOS blocker must be larger than the object; in the real game LOS has to match the physical objects.

## Cause (PROVEN)

- Three boxes are drawn at 120 x 60 with two 140 wu gaps (x 1890-2010; y 1770-1830, 1970-2030, 2170-2230).
- The engine holds one solid blocker of 100 wu cells, x 1800-2100 by y 1700-2300: 300 x 600 with no gaps. Read from the real library with `om_mapgen_cell_blocked`.
- Per box the blocker is 300 x 200, 8.3 times the area, with 90 wu extra each side in x and 70 wu in y.
- How it is made: `scripts/skilllab/arena/features.py:37-49` (`_engine_boxes`) pads each box by 1 wu; `features.py:98` calls `block_rect`, which rounds the box out to whole cells (`csrc/tactical_mapgen.c:851-882`). The cell size is 100 (`om_constants.h:585`, R-097-01, ALG-67). `features.py:20,24` assume 50. The 50 repeats in DEC-stage3-reach-engine-rule, H-063 and the `h088_fixtures.py` header comment.
- Sight (`csrc/fog.c:353-389`, `om_fog_grid_blocks`), fire (`csrc/tactical_move.c:2800-2826`, `om_combat_can_shoot`) and walker collision all read these same cells. No eye-height, radius or height term is involved (no cover discs, one layer). The drawing is `scenes/proto/layout_shot/layout_shot.gd:290-300`, an exact rectangle.

## Hidden despite a clear drawn line (PROVEN)

- Fight files, 16 frames, sight on: 1080 in-sensor-range pairs, 521 have a clear segment between the drawn rectangles, 0 are seen. The control has 511 clear pairs.
- Engine sweep (Vanguards at x 2200 and 1700): 586 pairs are clear of the drawn boxes but cross the blocker, 581 of them hidden. The 74 pairs that miss the blocker are all seen. The 749 pairs crossing a drawn box are all hidden. Visibility follows the blocker, not the drawn box.
- Example: tick 800, Vanguard 1 at (2107, 2091) to Bastion 10 at (1660, 2005), 455 wu apart; the line clears the middle box by 19-42 wu and is not seen.

## Bible

- R-007-06: a box blocks only a line that passes through it. R-007-01/02/07 are the other cover rules. The blocker is bigger than the drawn object and fills the gaps: divergence.
- R-007-05: cover never blocks movement. These cells do block walkers.
- The sim's own cover object is a disc with a height (`om_map_add_cover`); the lab does not use it.

## Why nobody fires (PROVEN)

- Sight on: every A-B line crosses the wall (can_see 0 of 128 directions), so no unit has a target. 72 pairs in sensor range and 56 in weapon range at the last frame: range is not the limit.
- Control: all 16 units hold a target, but `can_shoot` is 0 for all 64 pairs, because fire uses the same cells.
- With `features` emptied the fight happens (hp 8350 to 3178 sight on, 3484 control).
- Movement is a second cause: a single walker never routes around the wall, even with only the middle box (300 x 200 blocker); it ends at (2099, 2050). Likely because with no terrain `walk_route.c` ignores block cells (UNPROVEN as the only fault).

## Smallest candidate fix (not done)

Make the blocker match the drawn shape (the sim's cover disc, or a new rectangle primitive: a contract story). Correct `NAV_CELL` to 100 everywhere. Decide separately how walkers route around planar blocks. Stop-gap: redraw L-0039 on the 100 wu grid.

## Shared with L-0083

Every wall, building and box uses the same rounding, so each is over-blocked by up to 99 wu a side. That hides things; it does not by itself explain shooting through.

## Open questions

Should lab cover be a disc or blocked cells? Walkers ignoring planar blocks when routing is a separate engine gap. H-088 criterion 6 passes today because it checks only 50 wu crossings.
