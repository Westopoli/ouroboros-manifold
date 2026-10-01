/* ll_vision.c -- SPEC 5.2 steps 1-5 and side visibility. Cover (5.3) and pulse (5.7) are R1:
 * a scenario that needs them is rejected at validation, so nothing here ignores them silently. */
#include <math.h>
#include <string.h>
#include "ll_internal.h"

static int in_vantage(const ll_terrain *ter, const ll_unit *o) {
    for (int i = 0; i < ter->n_vantage; i++) {
        double dx = o->x - ter->vantage[i].x, dy = o->y - ter->vantage[i].y;
        if (sqrt(dx * dx + dy * dy) <= ter->vantage[i].r) return 1;
    }
    return 0;
}

int ll_can_see(const ll_state *s, int o, int t) {
    const ll_unit *uo = &s->u[o], *ut = &s->u[t];
    const ll_rules *r = s->rules;
    const ll_terrain *ter = s->ter;
    if (!uo->alive) return 0;

    /* 1. sensing factor by signed offset; vantage swaps the table */
    int off = LL_OFFS(uo->layer, ut->layer);
    double f = in_vantage(ter, uo) ? r->vantage_vis_factor[off] : r->vis_factor[off];
    if (f <= 0.0) return 0;

    /* 2. interference at the observer, zones on the observer's layer */
    double interf = 0.0;
    for (int i = 0; i < ter->n_zone; i++) {
        const ll_zone *z = &ter->zone[i];
        if (z->layer != uo->layer) continue;
        double dx = uo->x - z->x, dy = uo->y - z->y;
        double d = sqrt(dx * dx + dy * dy);
        if (d < z->r) interf += z->intensity * (1.0 - d / z->r);
    }
    if (interf > 1.0) interf = 1.0;
    if (interf < 0.0) interf = 0.0;

    /* 3. elevation bonus */
    double elev = 1.0 + r->sensor_elev_bonus_per_layer * (double)(uo->layer - ut->layer);
    if (elev < 0.0) elev = 0.0;

    /* 4. effective radius */
    double eff_r = uo->ty->sensor * (1.0 - interf) * elev * f;

    /* 5. distance, with the vertical term */
    double d3 = ll_dist3(uo->x - ut->x, uo->y - ut->y, uo->layer - ut->layer, ter->layer_spacing);
    return d3 <= eff_r;
}

int ll_side_vision(ll_state *s) {
    int any = 0;
    memset(s->sees, 0, sizeof s->sees);
    for (int o = 0; o < s->n; o++) {
        if (!s->u[o].alive) continue;
        int side = s->u[o].side;
        for (int t = 0; t < s->n; t++) {
            if (!s->u[t].alive || s->u[t].side == side) continue;
            if (s->sees[side][t]) continue;
            if (ll_can_see(s, o, t)) s->sees[side][t] = 1;
        }
    }
    for (int t = 0; t < s->n; t++) {
        if (!s->u[t].alive || !s->u[t].pre_revealed) continue;
        s->sees[1 - s->u[t].side][t] = 1;
    }
    for (int side = 0; side < 2; side++)
        for (int t = 0; t < s->n; t++)
            if (s->u[t].alive && s->u[t].side != side && s->sees[side][t]) any = 1;
    return any;
}
