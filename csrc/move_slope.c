/* csrc/move_slope.c -- "two units stand on the same slope" (E-13 R-097-05, R-097-03; engine rule fixes, Round 5, G5). See move_slope.h.
 * Integer-backed reads only (om_terrain_slope_at, om_terrain_height_at); no transcendental, no hash-order input. */
#include "ouroboros_sim.h"
#include "move_slope.h"

/* The slope index the unit stands on, or -1: inside a slope record, on a layer the slope joins, with ground that is not flat along the slope's axis.
 * The probe is half a terrain cell either side along the axis (the slopes are axis-aligned, so the step is a unit vector times 50 wu, no sqrt). */
static int om_move_slope_under(const om_world *w, double x, double y, int32_t layer) {
    om_slope s;
    int idx = om_terrain_slope_at(w, x, y, &s);
    double ux, uy;
    if (idx < 0) return -1;
    if (layer < s.lower_band - 1 || layer > s.upper_band - 1) return -1;
    ux = (s.x1 > s.x0) - (s.x1 < s.x0);
    uy = (s.y1 > s.y0) - (s.y1 < s.y0);
    if (om_terrain_height_at(w, x + 50.0 * ux, y + 50.0 * uy) == om_terrain_height_at(w, x - 50.0 * ux, y - 50.0 * uy)) return -1;
    return idx;
}

int om_move_same_slope(const om_world *w, double ax, double ay, int32_t layer_a, double bx, double by, int32_t layer_b) {
    int sa, sb;
    if (!om_terrain_present(w)) return 0;
    sa = om_move_slope_under(w, ax, ay, layer_a);
    if (sa < 0) return 0;
    sb = om_move_slope_under(w, bx, by, layer_b);
    return sa == sb;
}
