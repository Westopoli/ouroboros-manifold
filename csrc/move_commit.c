/* csrc/move_commit.c -- F1 (engine rule fixes 2026-11-08): the commit point for a unit's own movement step.
 * Appendix A of docs/reports/2026-11-07-rule-enforcement.md: of the position writers only the steer step guarded entry to a blocked cell;
 * the walker step, the kiting move and the flinch step had none, and om_move_leave_blocked ejected the unit on the next tick (the saw-tooth).
 * See also: csrc/tactical_move.c (the callers and om_move_blocked_for), csrc/walk_route.c (the router, which reads the same definition). */
#include <math.h>
#include <stdint.h>
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include "move_commit.h"

void om_move_get_canvas_size(om_world *w, double *width, double *height); /* csrc/tactical_move.c */

/* The cell a coordinate is in; a coordinate on the canvas's far edge is in the last cell, not in the blocked cell beyond the canvas (a unit may stand
 * on the edge, R-207-07). `extent` is the canvas size on that axis, 0 when none is set. */
static int omc_cell_of(double v, double extent) {
    int c = (int)floor(v / (double)OM_NAVMESH_CELL_SIZE);
    if (extent > 0.0 && v >= extent) c = (int)ceil(extent / (double)OM_NAVMESH_CELL_SIZE) - 1;
    return c;
}

static int omc_blocked_at(const om_world *w, uint32_t unit_id, double cw, double ch, double x, double y) {
    return om_move_blocked_for(w, unit_id, omc_cell_of(x, cw), omc_cell_of(y, ch));
}

int om_move_commit(const om_world *w, uint32_t unit_id, double ox, double oy, double *nx, double *ny, int reason) {
    double cw = 0.0, ch = 0.0, rx = *nx, ry = *ny;
    int result = 0;
    (void)reason; /* named for the callers and for a debugger; every writer follows the same rule */
    om_move_get_canvas_size((om_world *)w, &cw, &ch);
    if (cw > 0.0 && ch > 0.0) {
        rx = rx < 0.0 ? 0.0 : (rx > cw ? cw : rx);
        ry = ry < 0.0 ? 0.0 : (ry > ch ? ch : ry);
        if (rx != *nx || ry != *ny) result |= OM_COMMIT_CLAMPED;
    }
    *nx = rx;
    *ny = ry;
    if ((rx == ox && ry == oy) || omc_blocked_at(w, unit_id, cw, ch, ox, oy) || !omc_blocked_at(w, unit_id, cw, ch, rx, ry)) return result;
    if (!omc_blocked_at(w, unit_id, cw, ch, rx, oy)) {
        *ny = oy;
        return result | OM_COMMIT_SLID;
    }
    if (!omc_blocked_at(w, unit_id, cw, ch, ox, ry)) {
        *nx = ox;
        return result | OM_COMMIT_SLID;
    }
    *nx = ox;
    *ny = oy;
    return result | OM_COMMIT_HELD;
}
