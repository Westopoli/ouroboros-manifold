/* ll_nav.h -- terrain helpers and flow fields shared by ll_terrain.c and ll_move.c (SPEC 5.9, 5.10). */
#ifndef LL_NAV_H
#define LL_NAV_H

#include "ll_internal.h"

#define LL_FAR 1.0e300                      /* cost-to-go (seconds) of a node with no route to the goal */

enum { LL_STEP_MOVE = 1, LL_STEP_LAYER = 2, LL_STEP_SLOPE = 3 };

typedef struct ll_field ll_field;           /* cost-to-go from a goal cell; owned by the cache in s->nav */

typedef struct ll_step {
    int kind;                               /* LL_STEP_* */
    int cell, layer;                        /* the next node */
    int slope;                              /* LL_STEP_SLOPE: the slope index */
} ll_step;

int  ll_terrain_land(const ll_terrain *t, double x, double y, int layer);       /* in bounds and land on layer */
int  ll_cell_passable(const ll_terrain *t, int cell, int layer, int walker);    /* open (and land for a walker) */
void ll_cell_centre(const ll_terrain *t, int cell, double *x, double *y);
int  ll_segment_clear(const ll_terrain *t, double x0, double y0, double x1, double y1, int layer, int walker);

void ll_slope_edge(const ll_slope *sl, int top, double *x, double *y);          /* edge centre, top = 0 bottom, 1 top */
int  ll_slope_layer(const ll_slope *sl, double t);                              /* effective layer at position t (SPEC 5.1) */

/* Nearest layer to `layer` on which `cell` is passable (ties to the lower layer), 0 if none. */
int  ll_goal_layer(const ll_terrain *t, int cell, int layer, int walker);

/* Goal cell for a point: the cell itself if it is passable on any layer, else the nearest cell passable
 * on `layer` by centre distance (*snapped = 1), else -1. */
int  ll_goal_cell(const ll_terrain *t, double gx, double gy, int layer, int walker, int *snapped);
/* Cost-to-go in seconds for unit type `type` to node (goal_cell, goal_layer); cached; NULL on bad input. */
const ll_field *ll_nav_field(ll_state *s, int goal_cell, int goal_layer, int type);
double ll_field_cost(const ll_field *f, int cell, int layer);                   /* LL_FAR when unreachable */
int  ll_field_step(const ll_state *s, const ll_field *f, int cell, int layer, ll_step *out);  /* 1 if a step exists */

#endif /* LL_NAV_H */
