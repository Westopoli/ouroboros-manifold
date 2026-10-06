/* csrc/walk_route.c -- terrain stage 2 (spec 2026-10-06): least-time routes for walking units.
 * Contract stub: planner-a writes above the marker, planner-b below it. */
#include <stdint.h>
#include "ouroboros_sim.h"
#include "om_internal.h"

int om_walk_route(const om_world *w, uint32_t unit, double gx, double gy, double *pts, uint32_t cap, double *seconds) {
    (void)w; (void)unit; (void)gx; (void)gy; (void)pts; (void)cap;
    if (seconds) *seconds = 0.0;
    return -1;
}

/* ---- slope links ---- */
