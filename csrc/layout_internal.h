/* Places lane P1 interface (docs/northstar/plans/2026-10-13-places-lane-spec.md, "P1 the engine").
 * om_internal.h will include this from P3 on, so it is idempotent. */
#ifndef OM_LAYOUT_INTERNAL_H
#define OM_LAYOUT_INTERNAL_H

#include <stddef.h>
#include <stdint.h>
#include "ouroboros_sim.h"

typedef enum om_place_kind {
    OM_PLACE_OBJECTIVE = 0,            /* the S-113 id; ids 1..8 are not produced here */
    OM_PLACE_BASE_HOME = 9,            /* a side's base that is a grown town (R-177-02) */
    OM_PLACE_BASE_FORWARD = 10,        /* a side's base that is a camp (R-177-02) */
    OM_PLACE_NEUTRAL_SETTLEMENT = 11,  /* R-191-06 */
    OM_PLACE_RESOURCE_SITE = 12,       /* R-191-03, R-177-06 */
    OM_PLACE_EXPANSION_SITE = 13,      /* R-191-05 */
    OM_PLACE_ECONOMIC_LOCATION = 14    /* defined, not produced in this lane */
} om_place_kind;

typedef struct om_place {
    double  x, y;        /* canvas wu */
    int32_t kind;        /* om_place_kind */
    int32_t side;        /* faction id the mission uses for a base; -1 for everything else */
    int32_t age_steps;   /* growth steps lived before the mission: bases and settlements only, else 0 */
    int32_t richness;    /* 0..100, resource sites only, else 0 */
} om_place;              /* 32 bytes, no padding */

#define OM_PLACE_CAP 64
typedef struct om_layout_result { om_place places[OM_PLACE_CAP]; int32_t n; } om_layout_result;

/* The adapter; the test stub fills the same struct with C functions. */
typedef struct om_layout_terrain {
    void *ctx;
    double (*height_at)(void *ctx, double x, double y);
    int    (*walkable_at)(void *ctx, double x, double y);
    int    (*nearest_walkable)(void *ctx, double x, double y, double *ox, double *oy); /* 0 found, as om_terrain_nearest_walkable */
} om_layout_terrain;

_Static_assert(sizeof(om_place) == 32, "om_place is 32 bytes, no padding");
_Static_assert(offsetof(om_place, x) == 0, "om_place.x offset");
_Static_assert(offsetof(om_place, y) == 8, "om_place.y offset");
_Static_assert(offsetof(om_place, kind) == 16, "om_place.kind offset");
_Static_assert(offsetof(om_place, side) == 20, "om_place.side offset");
_Static_assert(offsetof(om_place, age_steps) == 24, "om_place.age_steps offset");
_Static_assert(offsetof(om_place, richness) == 28, "om_place.richness offset");

/* csrc/layout_terrain.c: the adapter P3 passes to the engine; the engine calls none of these. */
void   om_layout_terrain_from_world(const om_world *w, om_layout_terrain *out);
int    om_layout_is_water(const om_layout_terrain *t, double x, double y);
double om_layout_slope(const om_layout_terrain *t, double canvas, double x, double y);

/* csrc/layout_engine.c: base_xy = {player_x, player_y, enemy_x, enemy_y}; base_side = {player faction, enemy faction};
 * region_economy 0..1; canvas_w == canvas_h, a multiple of 100, at most 24000.
 * Returns out->n (>= 1) or -1 on a NULL pointer, a bad canvas or archetype outside 0..9. */
int om_layout_places(uint64_t seed, double canvas_w, double canvas_h, int32_t archetype, double region_economy,
                     double objective_x, double objective_y, const double *base_xy, const int32_t *base_side,
                     const om_layout_terrain *t, om_layout_result *out);

#endif
