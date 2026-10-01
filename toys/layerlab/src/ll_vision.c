/* ll_vision.c -- SPEC 5.2 can_see (steps 1-6), 5.3 cover, 5.7 pulse, side visibility. */
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

/* Sum of zone interference on `layer` at (x, y), clamped to [0, 1] (SPEC 5.2 step 2). */
static double interference(const ll_terrain *ter, double x, double y, int layer) {
    double interf = 0.0;
    for (int i = 0; i < ter->n_zone; i++) {
        const ll_zone *z = &ter->zone[i];
        if (z->layer != layer) continue;
        double dx = x - z->x, dy = y - z->y;
        double d = sqrt(dx * dx + dy * dy);
        if (d < z->r) interf += z->intensity * (1.0 - d / z->r);
    }
    if (interf > 1.0) interf = 1.0;
    if (interf < 0.0) interf = 0.0;
    return interf;
}

/* SPEC 5.3: 1 when a cover disc blocks the sight line from o to t. */
static int cover_blocks(const ll_terrain *ter, const ll_unit *o, const ll_unit *t) {
    double sx = t->x - o->x, sy = t->y - o->y;
    double len2 = sx * sx + sy * sy;
    for (int i = 0; i < ter->n_cover; i++) {
        const ll_cover *c = &ter->cover[i];
        double ox = o->x - c->x, oy = o->y - c->y, tx = t->x - c->x, ty = t->y - c->y;
        if (sqrt(ox * ox + oy * oy) <= c->r || sqrt(tx * tx + ty * ty) <= c->r) continue;
        double p = 0.0;
        if (len2 > 0.0) {
            p = ((c->x - o->x) * sx + (c->y - o->y) * sy) / len2;
            if (p < 0.0) p = 0.0;
            if (p > 1.0) p = 1.0;
        }
        double px = o->x + p * sx - c->x, py = o->y + p * sy - c->y;
        if (sqrt(px * px + py * py) >= c->r) continue;
        double layer = (double)o->layer + p * (double)(t->layer - o->layer);
        if (layer <= (double)c->height_layer) return 1;
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
    double interf = interference(ter, uo->x, uo->y, uo->layer);

    /* 3. elevation bonus */
    double elev = 1.0 + r->sensor_elev_bonus_per_layer * (double)(uo->layer - ut->layer);
    if (elev < 0.0) elev = 0.0;

    /* 4. effective radius */
    double eff_r = uo->ty->sensor * (1.0 - interf) * elev * f * ll_emit_factor(s, o, t);   /* going dark, ABI 3 */

    /* 5. distance, with the vertical term */
    double d3 = ll_dist3(uo->x - ut->x, uo->y - ut->y, uo->layer - ut->layer, ter->layer_spacing);
    if (d3 > eff_r) return 0;

    /* 6. cover */
    if (r->cover_mode == 1 && cover_blocks(ter, uo, ut)) return 0;
    return 1;
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
        if (s->tick < s->u[o].pulse_until) {                /* active pulse (SPEC 5.7) */
            const ll_unit *p = &s->u[o];
            double reach = s->rules->pulse_radius * (1.0 - interference(s->ter, p->x, p->y, p->layer));
            for (int t = 0; t < s->n; t++) {
                if (!s->u[t].alive || s->u[t].side == side) continue;
                double dx = s->u[t].x - p->x, dy = s->u[t].y - p->y;
                if (sqrt(dx * dx + dy * dy) <= reach) s->sees[side][t] = 1;
            }
        }
    }
    for (int t = 0; t < s->n; t++) {
        if (!s->u[t].alive || !s->u[t].pre_revealed) continue;
        s->sees[1 - s->u[t].side][t] = 1;
    }
    for (int side = 0; side < 2; side++)                    /* targeted pings, ABI 3 */
        for (int t = 0; t < s->n; t++)
            if (s->u[t].alive && s->u[t].side != side && ll_ping_reveals(s, side, t)) s->sees[side][t] = 1;
    for (int side = 0; side < 2; side++)
        for (int t = 0; t < s->n; t++)
            if (s->u[t].alive && s->u[t].side != side && s->sees[side][t]) any = 1;
    return any;
}

const char *ll_vision_validate(const ll_scenario *sc) {
    const ll_terrain *t = &sc->terrain;
    if (t->n_cover < 0 || t->n_cover > LL_MAX_COVER) return "terrain: n_cover out of range";
    if (t->n_vantage < 0 || t->n_vantage > LL_MAX_VANTAGE) return "terrain: n_vantage out of range";
    if (t->n_zone < 0 || t->n_zone > LL_MAX_ZONES) return "terrain: n_zone out of range";
    for (int i = 0; i < t->n_cover; i++) {
        const ll_cover *c = &t->cover[i];
        if (!ll_finite(c->x) || !ll_finite(c->y) || !ll_finite(c->r) || c->r <= 0.0)
            return "cover: x, y, r must be finite and r > 0";
        if (c->height_layer < 1 || c->height_layer > LL_LAYERS) return "cover: height_layer out of range";
    }
    for (int i = 0; i < t->n_vantage; i++) {
        const ll_vantage *v = &t->vantage[i];
        if (!ll_finite(v->x) || !ll_finite(v->y) || !ll_finite(v->r) || v->r <= 0.0)
            return "vantage: x, y, r must be finite and r > 0";
    }
    for (int i = 0; i < t->n_zone; i++) {
        const ll_zone *z = &t->zone[i];
        if (!ll_finite(z->x) || !ll_finite(z->y) || !ll_finite(z->r) || z->r <= 0.0)
            return "zone: x, y, r must be finite and r > 0";
        if (!ll_finite(z->intensity) || z->intensity < 0.0 || z->intensity > 1.0)
            return "zone: intensity must be in [0, 1]";
        if (z->layer < 1 || z->layer > LL_LAYERS) return "zone: layer out of range";
    }
    const ll_rules *r = &sc->rules;
    if (!ll_finite(r->pulse_radius) || r->pulse_radius < 0.0 || !ll_finite(r->pulse_reveal_s) ||
        r->pulse_reveal_s < 0.0 || !ll_finite(r->pulse_cooldown_s) || r->pulse_cooldown_s < 0.0)
        return "rules: pulse_radius, pulse_reveal_s, pulse_cooldown_s must be finite and >= 0";
    for (int i = 0; i < sc->n_spawns && i < LL_MAX_UNITS; i++) {
        const ll_spawn *p = &sc->spawns[i];
        if (p->pulse_tick < -1) return "spawn: pulse_tick must be >= -1";
        if (p->pulse_tick >= 0 && p->type >= 0 && p->type < sc->n_types &&
            sc->types[p->type].pulse_capable != 1)
            return "spawn: pulse_tick >= 0 on a type that is not pulse_capable";
    }
    return 0;
}

/* SPEC 5.7, step 3a: start scheduled pulses. The active window is read by ll_side_vision. */
void ll_pulse_update(ll_state *s) {
    for (int i = 0; i < s->n; i++) {
        ll_unit *u = &s->u[i];
        int pt = s->sc->spawns[i].pulse_tick;
        if (!u->alive || !u->ty->pulse_capable || pt < 0) continue;
        if (s->tick != pt || s->tick < u->pulse_ready_tick) continue;
        u->pulse_until = s->tick + (int)(s->rules->pulse_reveal_s * (double)LL_TICKS_PER_SEC + 0.5);
        u->pulse_ready_tick = s->tick + (int)(s->rules->pulse_cooldown_s * (double)LL_TICKS_PER_SEC + 0.5);
    }
}
