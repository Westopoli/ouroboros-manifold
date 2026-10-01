/* ll_combat.c -- acquisition (SPEC 5.4), fire and damage (5.5), the burst ability (5.6). */
#include <math.h>
#include <string.h>
#include "ll_internal.h"

/* Halfway eligibility (SPEC 5.4). On return *off is the signed offset the tables are read at.
 * Nothing changes layer in R0, so the changing branch is reachable only once R1 sets it. */
int ll_eligible(const ll_state *s, const ll_unit *a, const ll_unit *e, int *off) {
    *off = LL_OFFS(a->layer, e->layer);
    if (!e->changing) return 1;
    switch (s->rules->halfway_mode) {
    case LL_HALFWAY_RULE:
        if (a->layer != e->layer) return 0;
        *off = 4;
        return 1;
    case LL_HALFWAY_BOTH:
        if (a->layer != e->chg_from && a->layer != e->chg_to) return 0;
        *off = 4;
        return 1;
    default: /* LL_HALFWAY_UNTARGETABLE */
        return 0;
    }
}

/* Strict improvement of candidate e (distance d) over the current best; ties keep the earlier
 * candidate, and iteration is in index order, so ties end nearest then lowest index. */
static int better(int policy, const ll_unit *e, double d, const ll_unit *cur, double curd) {
    if (policy == LL_TARGET_LOWEST_HP) {
        if (e->hp != cur->hp) return e->hp < cur->hp;
    } else if (policy == LL_TARGET_HIGHEST_COST) {
        if (e->ty->cost != cur->ty->cost) return e->ty->cost > cur->ty->cost;
    }
    return d < curd;
}

/* Fills u->target (full eligibility), u->aim (everything but the arc), u->chase (nearest visible
 * enemy it could hit, range ignored). aim and chase exist so a unit outside its arc still turns and
 * stands, and an out-of-range unit still closes (SPEC 5.10). */
void ll_acquire(ll_state *s) {
    const ll_rules *r = s->rules;
    for (int i = 0; i < s->n; i++) {
        ll_unit *u = &s->u[i];
        u->target = u->aim = u->chase = -1;
        if (!u->alive || u->winding) continue;                    /* a winding caster does not fire (SPEC 5.6) */
        if (u->ty->dmg == 0.0 && u->ty->ability_kind == LL_ABILITY_NONE) continue;   /* a seer never acquires (SPEC 5.4) */
        if (u->order == LL_ORDER_MOVE && !u->arrived) continue;   /* does not acquire or fire */
        double dt_ = 0.0, da = 0.0, dc = 0.0;
        for (int j = 0; j < s->n; j++) {
            const ll_unit *e = &s->u[j];
            if (!e->alive || e->side == u->side) continue;
            int vis = s->sees[u->side][j];
            int fire_vis = r->fire_requires_vision ? vis : 1;
            if (!vis && !fire_vis) continue;
            int off;
            if (!ll_eligible(s, u, e, &off)) continue;
            if (!(r->range_mult[off] > 0.0) || !(ll_reach_mult(u, off) > 0.0)) continue;
            if (u->ty->aoe_r > 0.0 ? !(r->aoe_layer_mult[off] > 0.0) : !(r->dmg_mult[off] > 0.0)) continue;
            double dx = e->x - u->x, dy = e->y - u->y;
            double d3 = ll_dist3(dx, dy, u->layer - e->layer, s->ter->layer_spacing);
            if (vis && (u->chase < 0 || d3 < dc)) { u->chase = j; dc = d3; }
            if (!fire_vis) continue;
            if (d3 > u->ty->range * r->range_mult[off] * ll_reach_mult(u, off)) continue;
            if (u->aim < 0 || better(u->policy, e, d3, &s->u[u->aim], da)) { u->aim = j; da = d3; }
            if (u->arc_gate && d3 > 0.0) {
                double bd = sqrt(dx * dx + dy * dy);
                if (bd > 0.0 && (u->fx * dx + u->fy * dy) / bd < u->arc_cos) continue;
            }
            if (u->target < 0 || better(u->policy, e, d3, &s->u[u->target], dt_)) { u->target = j; dt_ = d3; }
        }
    }
}

void ll_fire(ll_state *s) {
    const ll_rules *r = s->rules;
    memset(s->direct, 0, sizeof s->direct);
    memset(s->area_sum, 0, sizeof s->area_sum);
    memset(s->area_max, 0, sizeof s->area_max);
    s->fired_side[0] = s->fired_side[1] = 0;
    for (int i = 0; i < s->n; i++) {
        ll_unit *u = &s->u[i];
        u->fired = 0;
        if (!u->alive) continue;
        if (u->target < 0 || u->cooldown > 0.0) {
            if (u->cooldown < 0.0) u->cooldown = 0.0;   /* idle: no banked shots (SPEC 5.5 reading) */
            continue;
        }
        const ll_unit *t = &s->u[u->target];
        int off;
        (void)ll_eligible(s, u, t, &off);
        double cat = r->category_mult[u->ty->category][t->ty->category];
        if (u->ty->aoe_r <= 0.0) {
            s->direct[u->target] += u->ty->dmg * cat * r->dmg_mult[off];
        } else {
            double cx = t->x, cy = t->y;
            for (int j = 0; j < s->n; j++) {
                const ll_unit *e = &s->u[j];
                if (!e->alive || e->side == u->side) continue;
                double dx = e->x - cx, dy = e->y - cy;
                if (sqrt(dx * dx + dy * dy) > u->ty->aoe_r) continue;
                int eoff;
                if (!ll_eligible(s, u, e, &eoff)) continue;
                if (!(r->aoe_layer_mult[eoff] > 0.0)) continue;
                double hit = u->ty->dmg * r->category_mult[u->ty->category][e->ty->category] * r->aoe_layer_mult[eoff];
                s->area_sum[j] += hit;
                if (hit > s->area_max[j]) s->area_max[j] = hit;
            }
        }
        u->fired = 1;
        s->shots[u->side]++;
        s->fired_side[u->side]++;
        u->cooldown += u->ty->interval_s;
    }
}

int ll_apply_damage(ll_state *s) {
    int any = 0;
    for (int j = 0; j < s->n; j++) {
        ll_unit *t = &s->u[j];
        if (!t->alive) continue;
        double area = s->area_sum[j];
        double cap = s->rules->aoe_cap_mult * s->area_max[j];
        if (area > cap) area = cap;
        double total = s->direct[j] + area;
        if (!(total > 0.0)) continue;
        double dealt = total < t->hp ? total : t->hp;     /* counted after clamping to remaining HP */
        t->hp -= dealt;
        s->damage_dealt[1 - t->side] += dealt;
        if (dealt > 0.0) any = 1;
        if (t->hp <= 0.0) {
            t->hp = 0.0;
            t->alive = 0;
            s->cost_lost[t->side] += t->ty->cost;
        }
    }
    return any;
}

/* ---- burst ability (SPEC 5.6) ---- */

const char *ll_combat_validate(const ll_scenario *sc) {
    for (int i = 0; i < sc->n_spawns; i++) {
        const ll_spawn *p = &sc->spawns[i];
        if (p->type < 0 || p->type >= sc->n_types) continue;   /* reported by the spawn check */
        const ll_unit_type *t = &sc->types[p->type];
        if (t->ability_kind != LL_ABILITY_BURST) continue;
        if (t->ab_min_targets < 1) return "type: burst ab_min_targets must be >= 1";
        if (!ll_finite(t->ab_radius) || !(t->ab_radius > 0.0)) return "type: burst ab_radius must be > 0";
        if (!ll_finite(t->ab_windup_s) || t->ab_windup_s < 0.0) return "type: burst ab_windup_s must be >= 0";
        if (!ll_finite(t->ab_cooldown_s) || t->ab_cooldown_s < 0.0) return "type: burst ab_cooldown_s must be >= 0";
        if (!ll_finite(t->ab_dmg_mult)) return "type: burst ab_dmg_mult must be finite";
    }
    return 0;
}

static double xy_dist(double dx, double dy) { return sqrt(dx * dx + dy * dy); }

/* Resolves the cast: every alive enemy within ab_radius of the locked centre takes
 * dmg * ab_dmg_mult * aoe_layer_mult[off], no category multiplier, uncapped (s->direct). */
static void burst_cast(ll_state *s, ll_unit *u) {
    const ll_rules *r = s->rules;
    for (int j = 0; j < s->n; j++) {
        const ll_unit *e = &s->u[j];
        if (!e->alive || e->side == u->side) continue;
        if (xy_dist(e->x - u->ab_cx, e->y - u->ab_cy) > u->ty->ab_radius) continue;
        int off;
        if (!ll_eligible(s, u, e, &off)) continue;
        if (!(r->aoe_layer_mult[off] > 0.0)) continue;
        s->direct[j] += u->ty->dmg * u->ty->ab_dmg_mult * r->aoe_layer_mult[off];
    }
    s->shots[u->side]++;
    s->fired_side[u->side]++;
    u->fired = 1;
    u->ab_cd = u->ty->ab_cooldown_s;
    u->winding = 0;
}

/* Picks the cast centre: among visible, eligible enemies in range, the one with the most eligible
 * visible enemies within ab_radius of it (ties nearest, then lowest index). Returns its index when
 * the count reaches ab_min_targets, else -1. */
static int burst_pick(const ll_state *s, const ll_unit *u) {
    const ll_rules *r = s->rules;
    int best = -1, best_n = 0;
    double best_d = 0.0;
    for (int j = 0; j < s->n; j++) {
        const ll_unit *e = &s->u[j];
        if (!e->alive || e->side == u->side) continue;
        if (r->fire_requires_vision && !s->sees[u->side][j]) continue;
        int off;
        if (!ll_eligible(s, u, e, &off)) continue;
        if (!(r->range_mult[off] > 0.0) || !(r->dmg_mult[off] > 0.0) || !(ll_reach_mult(u, off) > 0.0)) continue;
        double d3 = ll_dist3(e->x - u->x, e->y - u->y, u->layer - e->layer, s->ter->layer_spacing);
        if (d3 > u->ty->range * r->range_mult[off] * ll_reach_mult(u, off)) continue;
        int n = 0;
        for (int k = 0; k < s->n; k++) {
            const ll_unit *f = &s->u[k];
            if (!f->alive || f->side == u->side) continue;
            if (r->fire_requires_vision && !s->sees[u->side][k]) continue;
            int foff;
            if (!ll_eligible(s, u, f, &foff)) continue;
            if (!(r->aoe_layer_mult[foff] > 0.0)) continue;
            if (xy_dist(f->x - e->x, f->y - e->y) <= u->ty->ab_radius) n++;
        }
        if (n > best_n || (n == best_n && n > 0 && d3 < best_d)) { best = j; best_n = n; best_d = d3; }
    }
    return best_n >= u->ty->ab_min_targets ? best : -1;
}

void ll_burst_update(ll_state *s) {
    for (int i = 0; i < s->n; i++) {
        ll_unit *u = &s->u[i];
        if (u->ty->ability_kind != LL_ABILITY_BURST) continue;
        if (!u->alive) { u->winding = 0; continue; }          /* died in its windup: no cast, no shot */
        u->ab_cd -= LL_DT;
        if (u->winding) {
            u->ab_wind_left -= LL_DT;
            if (u->ab_wind_left <= 0.0) burst_cast(s, u);
            continue;
        }
        if (u->ab_cd > 0.0) continue;
        if (u->order == LL_ORDER_MOVE && !u->arrived) continue;
        int c = burst_pick(s, u);
        if (c < 0) continue;
        u->ab_cx = s->u[c].x;
        u->ab_cy = s->u[c].y;
        u->winding = 1;
        u->ab_wind_left = u->ty->ab_windup_s;
        if (u->ab_wind_left <= 0.0) burst_cast(s, u);
    }
}
