/* ll_move.c -- R0 movement (SPEC 5.10, crude by design): hold, move, attack-move, straight steering,
 * chase, facing, same-layer separation. No flow fields, no timed transfers, no slopes (R1). */
#include <math.h>
#include "ll_internal.h"

void ll_face_init(ll_unit *u, double facing_deg) {
    double s, c;
    ll_sincos(facing_deg * (LL_PI / 180.0), &s, &c);
    u->fx = c;
    u->fy = s;
}

/* Turn toward (dx,dy): snap if within one step, else rotate by turn_rate * dt (SPEC 5.12). */
static void turn_toward(ll_unit *u, double dx, double dy) {
    double d = sqrt(dx * dx + dy * dy);
    if (!(d > 0.0)) return;
    dx /= d;
    dy /= d;
    double s, c;
    ll_sincos(u->ty->turn_rate * LL_DT, &s, &c);
    if (u->fx * dx + u->fy * dy >= c) { u->fx = dx; u->fy = dy; return; }
    double sg = (u->fx * dy - u->fy * dx) >= 0.0 ? 1.0 : -1.0;
    double nx = u->fx * c - sg * u->fy * s;
    double ny = sg * u->fx * s + u->fy * c;
    double n = sqrt(nx * nx + ny * ny);
    u->fx = nx / n;
    u->fy = ny / n;
}

/* MOVE arrival is sticky: once within 1.5 body radii the unit behaves as HOLD. */
void ll_update_arrival(ll_state *s) {
    for (int i = 0; i < s->n; i++) {
        ll_unit *u = &s->u[i];
        if (!u->alive || u->order != LL_ORDER_MOVE || u->arrived) continue;
        double dx = u->gx - u->x, dy = u->gy - u->y;
        if (sqrt(dx * dx + dy * dy) <= 1.5 * u->ty->body_radius) u->arrived = 1;
    }
}

void ll_move_units(ll_state *s) {
    const ll_terrain *ter = s->ter;
    double px[LL_MAX_UNITS], py[LL_MAX_UNITS];
    for (int i = 0; i < s->n; i++) { px[i] = s->u[i].x; py[i] = s->u[i].y; }

    for (int i = 0; i < s->n; i++) {
        ll_unit *u = &s->u[i];
        if (!u->alive) continue;
        int have = 0;
        double gx = 0.0, gy = 0.0;
        double tol = 1.5 * u->ty->body_radius;
        int idle = u->order == LL_ORDER_HOLD || (u->order == LL_ORDER_MOVE && u->arrived);
        if (idle) {
            if (s->rules->chase_when_idle && u->aim < 0 && u->chase >= 0) {
                have = 1; gx = px[u->chase]; gy = py[u->chase];
            }
        } else if (u->order == LL_ORDER_MOVE) {
            have = 1; gx = u->gx; gy = u->gy;
        } else if (u->aim < 0) {                         /* ATTACK_MOVE: stands if it can fire */
            if (u->chase >= 0) {
                have = 1; gx = px[u->chase]; gy = py[u->chase];
            } else {
                double dx = u->gx - u->x, dy = u->gy - u->y;
                if (sqrt(dx * dx + dy * dy) > tol) { have = 1; gx = u->gx; gy = u->gy; }
            }
        }

        double mdx = 0.0, mdy = 0.0, d = 0.0;
        if (have) {
            mdx = gx - u->x; mdy = gy - u->y;
            d = sqrt(mdx * mdx + mdy * mdy);
            if (!(d > 0.0)) have = 0;
        }
        if (have) {
            double step = u->ty->speed * LL_DT;
            if (step > d) step = d;
            double sx = mdx / d * step, sy = mdy / d * step;
            if (ll_terrain_open(ter, u->x + sx, u->y + sy, u->layer)) { u->x += sx; u->y += sy; }
            else if (ll_terrain_open(ter, u->x + sx, u->y, u->layer)) u->x += sx;
            else if (ll_terrain_open(ter, u->x, u->y + sy, u->layer)) u->y += sy;
        }

        if (u->aim >= 0) turn_toward(u, px[u->aim] - u->x, py[u->aim] - u->y);
        else if (have) turn_toward(u, mdx, mdy);
    }

    /* same-layer separation, pairs i < j */
    double w = s->rules->separation_weight;
    for (int i = 0; i < s->n; i++) {
        ll_unit *a = &s->u[i];
        if (!a->alive) continue;
        for (int j = i + 1; j < s->n; j++) {
            ll_unit *b = &s->u[j];
            if (!b->alive || a->layer != b->layer) continue;
            double dx = b->x - a->x, dy = b->y - a->y;
            double dist = sqrt(dx * dx + dy * dy);
            double overlap = a->ty->body_radius + b->ty->body_radius - dist;
            if (!(overlap > 0.0)) continue;
            double ax = 1.0, ay = 0.0;
            if (dist > 0.0) { ax = dx / dist; ay = dy / dist; }
            double push = overlap / 2.0 * w;
            if (ll_terrain_open(ter, a->x - ax * push, a->y - ay * push, a->layer)) {
                a->x -= ax * push; a->y -= ay * push;
            }
            if (ll_terrain_open(ter, b->x + ax * push, b->y + ay * push, b->layer)) {
                b->x += ax * push; b->y += ay * push;
            }
        }
    }
}
