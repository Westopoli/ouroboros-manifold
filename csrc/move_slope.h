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

#endif
