/* Places lane P1: the adapter over the real terrain that P3 hands to the engine (layout_engine.c calls none of it).
 * See also: csrc/layout_internal.h, docs/northstar/plans/2026-10-13-places-lane-spec.md (P1, gaps 3 and 4). */
#include <math.h>
#include "layout_internal.h"

#define LAYOUT_SLOPE_STEP 100.0    /* one terrain cell in wu: the neighbour distance of om_layout_slope */

static double layout_world_height(void *ctx, double x, double y)
{
    return ctx ? om_terrain_height_at((const om_world *)ctx, x, y) : 0.0;
}

static int layout_world_walkable(void *ctx, double x, double y)
{
    return ctx ? om_terrain_walkable_at((const om_world *)ctx, x, y) : 0;
}

static int layout_world_nearest(void *ctx, double x, double y, double *ox, double *oy)
{
    return ctx ? om_terrain_nearest_walkable((const om_world *)ctx, x, y, ox, oy) : -1;
}

void om_layout_terrain_from_world(const om_world *w, om_layout_terrain *out)
{
    if (!out) return;
    out->ctx = (void *)w;
    out->height_at = layout_world_height;
    out->walkable_at = layout_world_walkable;
    out->nearest_walkable = layout_world_nearest;
}

int om_layout_is_water(const om_layout_terrain *t, double x, double y)
{
    if (!t || !t->height_at) return 0;
    return t->height_at(t->ctx, x, y) < 0.0;
}

/* Max of the two forward height steps over one cell, per 100 wu; a step that would leave the canvas goes inward. */
double om_layout_slope(const om_layout_terrain *t, double canvas, double x, double y)
{
    double x1, y1, h, dx, dy;
    if (!t || !t->height_at) return 0.0;
    x1 = x + LAYOUT_SLOPE_STEP;
    y1 = y + LAYOUT_SLOPE_STEP;
    if (x1 >= canvas) x1 = x - LAYOUT_SLOPE_STEP;
    if (y1 >= canvas) y1 = y - LAYOUT_SLOPE_STEP;
    h = t->height_at(t->ctx, x, y);
    dx = fabs(t->height_at(t->ctx, x1, y) - h);
    dy = fabs(t->height_at(t->ctx, x, y1) - h);
    return fmax(dx, dy) / LAYOUT_SLOPE_STEP;
}
