/* ll_terrain.c -- flat grid queries (R0). Slopes, land and flow fields are R1. */
#include "ll_internal.h"

double ll_terrain_width(const ll_terrain *t)  { return (double)t->w_cells * t->cell; }
double ll_terrain_height(const ll_terrain *t) { return (double)t->h_cells * t->cell; }

int ll_terrain_cell(const ll_terrain *t, double x, double y) {
    if (!(x >= 0.0 && y >= 0.0)) return -1;
    if (!(x < ll_terrain_width(t) && y < ll_terrain_height(t))) return -1;
    int cx = (int)(x / t->cell), cy = (int)(y / t->cell);
    if (cx >= t->w_cells) cx = t->w_cells - 1;    /* guards x/cell rounding up at the edge */
    if (cy >= t->h_cells) cy = t->h_cells - 1;
    return cy * t->w_cells + cx;
}

int ll_terrain_open(const ll_terrain *t, double x, double y, int layer) {
    int c = ll_terrain_cell(t, x, y);
    if (c < 0 || layer < 1 || layer > LL_LAYERS) return 0;
    return (t->open[c] >> (layer - 1)) & 1;
}

const char *ll_terrain_validate(const ll_terrain *t) {
    if (t->w_cells < 1 || t->w_cells > LL_MAX_GRID_W) return "terrain: w_cells out of range";
    if (t->h_cells < 1 || t->h_cells > LL_MAX_GRID_H) return "terrain: h_cells out of range";
    if (!ll_finite(t->cell) || t->cell <= 0.0) return "terrain: cell must be positive";
    if (!ll_finite(t->layer_spacing) || t->layer_spacing < 0.0) return "terrain: layer_spacing must be >= 0";
    if (t->n_cover < 0 || t->n_cover > LL_MAX_COVER) return "terrain: n_cover out of range";
    if (t->n_vantage < 0 || t->n_vantage > LL_MAX_VANTAGE) return "terrain: n_vantage out of range";
    if (t->n_zone < 0 || t->n_zone > LL_MAX_ZONES) return "terrain: n_zone out of range";
    if (t->n_slope < 0 || t->n_slope > LL_MAX_SLOPES) return "terrain: n_slope out of range";
    if (t->n_slope > 0) return "unimplemented feature: slopes (n_slope > 0) arrive in rung R1";
    for (int i = 0; i < t->n_cover; i++) {
        const ll_cover *c = &t->cover[i];
        if (!ll_finite(c->x) || !ll_finite(c->y) || !ll_finite(c->r) || c->r < 0.0)
            return "terrain: cover disc has a bad field";
        if (c->height_layer < 0 || c->height_layer > LL_LAYERS) return "terrain: cover height_layer out of range";
    }
    for (int i = 0; i < t->n_vantage; i++) {
        const ll_vantage *v = &t->vantage[i];
        if (!ll_finite(v->x) || !ll_finite(v->y) || !ll_finite(v->r) || v->r < 0.0)
            return "terrain: vantage disc has a bad field";
    }
    for (int i = 0; i < t->n_zone; i++) {
        const ll_zone *z = &t->zone[i];
        if (!ll_finite(z->x) || !ll_finite(z->y) || !ll_finite(z->r) || z->r < 0.0 ||
            !ll_finite(z->intensity) || z->intensity < 0.0)
            return "terrain: interference zone has a bad field";
        if (z->layer < 1 || z->layer > LL_LAYERS) return "terrain: zone layer out of range";
    }
    return 0;
}
