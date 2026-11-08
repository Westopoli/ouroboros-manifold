/* csrc/move_commit.h -- internal (not the contract header): the one commit point for a unit's own movement step (F1, engine rule fixes
 * 2026-11-08; E-13 Invariants "A unit never enters a blocked cell", R-207-06, R-207-07). Body in csrc/move_commit.c. */
#ifndef OM_MOVE_COMMIT_H
#define OM_MOVE_COMMIT_H

#include <stdint.h>
#include "ouroboros_sim.h"

/* Why a position is being written. Only the four step writers below are wired to om_move_commit; EJECT and PUSH name the other two writers
 * (om_move_leave_blocked, the collision slide), which keep their own code. */
enum {
    OM_COMMIT_STEER = 1,
    OM_COMMIT_WALK,
    OM_COMMIT_KITE,
    OM_COMMIT_FLINCH,
    OM_COMMIT_EJECT,
    OM_COMMIT_PUSH
};

/* What om_move_commit did to the step it was given (bit flags; 0 = it stood as asked). */
enum {
    OM_COMMIT_CLAMPED = 1, /* the step left the canvas and was cut to its edge (R-207-07) */
    OM_COMMIT_SLID = 2,    /* the step ended in a blocked cell and was cut to one axis */
    OM_COMMIT_HELD = 4     /* neither axis was open: the unit stays where it was */
};

/* The one definition of "blocked for this unit": cell (cx, cy) of the unit's own layer is blocked when the mapgen grid says so (a box, a wall,
 * a building, the canvas edge), its density is above the obstacle threshold, or, for a walker on a terrain world, the walk mask says so (the ground's
 * own bits in the mapgen grid are left to the walk mask for a walker: a slope is climbed through them).
 * Body in csrc/tactical_move.c, beside the density grid it reads. */
int om_move_blocked_for(const om_world *w, uint32_t unit_id, int32_t cx, int32_t cy);

/* The router's view of the same definition for a layer (walk_route.c): the planar part (mapgen box, wall, building, density), without the walk mask,
 * which the router reads itself. Body in csrc/tactical_move.c. */
int om_move_route_cell_blocked(const om_world *w, uint32_t layer, int32_t cx, int32_t cy);

/* A unit that stood at (ox, oy) is asked to stand at (*nx, *ny). Writes the position it may stand at: clamped to the canvas when one is set, and
 * if that cell is blocked for the unit, slid along x, else along y, else held at (ox, oy). A unit that starts in a blocked cell is not
 * constrained by cells (om_move_leave_blocked repairs it, R-207-06). Obstacle discs are not tested (no router sees them; a walker would stop
 * at a disc for good). Returns OM_COMMIT_* flags. Reads only; the caller writes the position. */
int om_move_commit(const om_world *w, uint32_t unit_id, double ox, double oy, double *nx, double *ny, int reason);

#endif
