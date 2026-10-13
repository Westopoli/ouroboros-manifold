/* Places lane P1 unit 2: argument validation, the objective and the two bases
 * (docs/northstar/plans/2026-10-13-places-lane-spec.md, "P1 the engine", steps 1, 2 and 9).
 * Pure function of its arguments: no world, no global state. */
#include <string.h>
#include "layout_internal.h"
#include "om_internal.h"

#define LAYOUT_CANVAS_MAX     24000   /* canvas side cap, wu (spec P1 interface) */
#define LAYOUT_CANVAS_CELL    100     /* canvas is a multiple of one 100 wu cell (spec P1 interface) */
#define LAYOUT_ARCHETYPES     10      /* archetype ids 0..9 (mission.c:161-170, R-177-02 table) */
#define LAYOUT_HOME_AGE       40      /* DRAFT-home-age: growth steps a HOME base has lived */

/* R-177-02, a rule not a draft: base kind per archetype, player then enemy. HOME = a grown town, FORWARD = a camp. */
static const int32_t layout_base_kind[LAYOUT_ARCHETYPES][2] = {
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Defensive Stand */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_FORWARD },  /* Siege Breaking: relief camp, siege camp */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_HOME },     /* Reconquest: the city being taken */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_HOME },     /* Assault: the city or fortress being taken */
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Suppression: garrison in a city */
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Multi-Front Defense */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_FORWARD },  /* Interception: field camp, staging camp */
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Evacuation: the place being left */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_FORWARD },  /* Containment */
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Counterinsurgency: garrison in a city */
};

static int layout_canvas_ok(double w, double h)
{
    if (w != h || w <= 0.0 || w > (double)LAYOUT_CANVAS_MAX) return 0;
    return (int64_t)w % LAYOUT_CANVAS_CELL == 0 && (double)(int64_t)w == w;
}

static om_place layout_base(double x, double y, int32_t kind, int32_t side)
{
    om_place p;
    memset(&p, 0, sizeof p);
    p.x = x;
    p.y = y;
    p.kind = kind;
    p.side = side;
    p.age_steps = kind == OM_PLACE_BASE_HOME ? LAYOUT_HOME_AGE : 0;
    return p;
}

int om_layout_places(uint64_t seed, double canvas_w, double canvas_h, int32_t archetype, double region_economy,
                     double objective_x, double objective_y, const double *base_xy, const int32_t *base_side,
                     const om_layout_terrain *t, om_layout_result *out)
{
    om_place obj;
    const double *enemy_xy;
    (void)seed;
    (void)region_economy;
    if (!base_xy || !base_side || !t || !out) return -1;
    if (!layout_canvas_ok(canvas_w, canvas_h) || archetype < 0 || archetype >= LAYOUT_ARCHETYPES) return -1;

    enemy_xy = base_xy + 2;
    memset(out, 0, sizeof *out);
    memset(&obj, 0, sizeof obj);
    obj.x = objective_x;
    obj.y = objective_y;
    obj.kind = OM_PLACE_OBJECTIVE;
    obj.side = -1;
    out->places[out->n++] = obj;
    out->places[out->n++] = layout_base(base_xy[0], base_xy[1], layout_base_kind[archetype][0], base_side[0]);
    out->places[out->n++] = layout_base(enemy_xy[0], enemy_xy[1], layout_base_kind[archetype][1], base_side[1]);
    return out->n;
}
