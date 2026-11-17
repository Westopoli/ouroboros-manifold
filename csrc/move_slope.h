/* csrc/move_slope.h -- internal (not the contract header): "two units stand on the same slope" (E-13 R-097-05, R-097-03; engine rule fixes, Round 5, G5).
 * Body in csrc/move_slope.c. Read by the collision pass (om_move_collide_pair) and the steering probe's blocker gather in csrc/tactical_move.c. */
#ifndef OM_MOVE_SLOPE_H
#define OM_MOVE_SLOPE_H

#include <stdint.h>
#include "ouroboros_sim.h"

/* 1 when both units stand on one and the same slope: the terrain's slope record at each position is the same (om_terrain_slope_at), each unit's layer is
 * one the slope joins (lower band - 1 to upper band - 1), and the ground under each is not flat (it rises or falls along the slope: the bible's "band of
 * ground that joins two layers", R-001-06; the record itself can run the whole row, so the record alone is not membership). Else 0, also when there is no terrain. */
int om_move_same_slope(const om_world *w, double ax, double ay, int32_t layer_a, double bx, double by, int32_t layer_b);

/* R-097-05 / round5.md G5: a unit does not change layer across a slope's midline a third time inside OM_SLOPE_FLIP_WINDOW ticks of the one before the last (up and back is a
 * legal pass, a jitter of pushes and route changes at the line is not). `chg` holds the ticks of the unit's last two such changes, newest first, 0 for none.
 * See also: om_move_walker_tick in csrc/tactical_move.c, which asks before it changes a layer and notes the change. */
int om_move_layer_flip_allowed(const uint64_t chg[2], uint64_t tick);
void om_move_layer_flip_note(uint64_t chg[2], uint64_t tick);

#endif
