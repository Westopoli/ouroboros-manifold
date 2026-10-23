/* ll_ping.c -- targeted ping (E-01 S-162, SPEC 15.3, ABI 3). Call sites: ll_ping_reveals in the side visibility
 * (ll_vision.c), ll_ping_update each tick (ll_sim.c). */
#include <math.h>
#include "ll_internal.h"

const char *ll_ping_validate(const ll_scenario *sc) {
    const ll_rules *r = &sc->rules;
    if (!ll_finite(r->ping_reach) || r->ping_reach < 0.0 || !ll_finite(r->ping_radius) || r->ping_radius < 0.0 ||
        !ll_finite(r->ping_s) || r->ping_s < 0.0 || !ll_finite(r->ping_cooldown_s) || r->ping_cooldown_s < 0.0)
        return "rules: ping_reach, ping_radius, ping_s and ping_cooldown_s must be finite and >= 0";
    int n = sc->n_spawns < LL_MAX_UNITS ? sc->n_spawns : LL_MAX_UNITS;   /* n_spawns itself is checked by the caller */
    for (int i = 0; i < n; i++) {
        const ll_spawn *p = &sc->spawns[i];
        if (p->ping_tick < -1) return "spawn: ping_tick must be >= -1";
        if (p->ping_tick >= 0) {
            if (p->ping_layer < 1 || p->ping_layer > LL_LAYERS) return "spawn: ping_layer must be 1..5";
            if (!ll_finite(p->ping_x) || !ll_finite(p->ping_y)) return "spawn: ping_x and ping_y must be finite";
        }
    }
    return 0;
}

/* 1 when the active ping of unit p reveals unit t: alive enemy on the pinged layer within ping_radius of the place */
static int ping_hits(const ll_state *s, const ll_unit *p, const ll_unit *t) {
    if (!p->alive || s->tick >= p->ping_until || !t->alive || t->side == p->side || t->layer != p->ping_layer) return 0;
    double dx = t->x - p->ping_px, dy = t->y - p->ping_py;
    return sqrt(dx * dx + dy * dy) <= s->rules->ping_radius;
}

void ll_ping_update(ll_state *s) {
    const ll_rules *r = s->rules;
    for (int i = 0; i < s->n; i++) {
        ll_unit *p = &s->u[i];
        const ll_spawn *sp = &s->sc->spawns[i];
        if (!p->alive || sp->ping_tick < 0 || s->tick != sp->ping_tick || s->tick < p->ping_ready_tick) continue;
        double dx = sp->ping_x - p->x, dy = sp->ping_y - p->y;
        if (sqrt(dx * dx + dy * dy) > r->ping_reach) continue;
        p->ping_until = s->tick + (int)(r->ping_s * 20.0 + 0.5);
        p->ping_ready_tick = s->tick + (int)(r->ping_cooldown_s * 20.0 + 0.5);
        p->ping_layer = sp->ping_layer;
        p->ping_px = sp->ping_x;
        p->ping_py = sp->ping_y;
        int side = 1 - p->side, hit = 0;
        double cx = 0.0, cy = 0.0;
        for (int t = 0; t < s->n; t++) {
            if (!ping_hits(s, p, &s->u[t])) continue;
            hit++;
            cx += s->u[t].x;
            cy += s->u[t].y;
        }
        if (!hit) continue;
        s->alerts[side]++;
        if (s->alerted_tick[side] >= 0) continue;
        s->alerted_tick[side] = s->tick;
        double vx = p->x - cx / hit, vy = p->y - cy / hit, d = sqrt(vx * vx + vy * vy);
        if (d > 0.0) { s->alert_dx[side] = vx / d; s->alert_dy[side] = vy / d; }
    }
}

int ll_ping_reveals(const ll_state *s, int side, int t) {
    for (int i = 0; i < s->n; i++)
        if (s->u[i].side == side && ping_hits(s, &s->u[i], &s->u[t])) return 1;
    return 0;
}
