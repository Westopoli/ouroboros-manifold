/* ll_move.c -- layers in motion and movement (SPEC 5.1, 5.8, 5.9, 5.10; crude by design): timed
 * transfers, slopes and walking, goals (hold, move, attack-move, chase), straight steering or flow-field
 * descent, facing, same-layer separation. Flow fields live in ll_terrain.c. */
#include <math.h>
#include "ll_nav.h"

#define EPS 1e-9    /* absorbs the rounding of a time or position accumulated tick by tick */
#define LL_SEPARATION_PASSES 8    /* SPEC 5.10 */
#define LL_MOUTH_RADIUS 40.0      /* SPEC 5.10 slope mouths */
#define LL_LANE_PITCH 30.0        /* SPEC 5.9 lanes: a body width, fixed in the lab */

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

static int is_walker(const ll_unit *u) { return u->ty->movement_kind == LL_MOVE_WALK; }

/* The unit's layer takes a new value: that is one transition (SPEC 5.8). */
static void set_layer(ll_unit *u, int layer) {
    if (u->layer == layer) return;
    u->layer = layer;
    u->transitions++;
}

/* ---- validation ---- */

const char *ll_move_validate(const ll_scenario *sc) {
    for (int i = 0; i < sc->n_spawns; i++) {
        const ll_spawn *p = &sc->spawns[i];
        if (p->type < 0 || p->type >= sc->n_types || p->type >= LL_MAX_TYPES) continue;   /* reported by the spawn check */
        int walker = sc->types[p->type].movement_kind == LL_MOVE_WALK;
        if (p->transfer_layer != 0) {
            if (p->transfer_layer < 0 || p->transfer_layer > LL_LAYERS) return "spawn: transfer_layer out of range";
            if (walker) return "spawn: transfer_layer is for flying types only (walkers change layer by slope)";
        }
        if (walker && p->layer >= 1 && p->layer <= LL_LAYERS && !ll_terrain_land(&sc->terrain, p->x, p->y, p->layer))
            return "spawn: a walking unit must start on a land cell of its layer";
    }
    return 0;
}

/* ---- step 2: transfers, effective layer, changing flags (SPEC 5.1, 5.8) ---- */

static void begin_transfer(ll_unit *u, int layer) {
    u->xfer_to = layer;
    u->xfer_elapsed = 0.0;
    u->chg_from = u->layer;
    u->chg_to = layer;
    u->changing = 1;
    u->progress = 0.0;
}

/* Try to start a wanted transfer; 1 when it is settled (started, or already on that layer), 0 when it must
 * keep waiting for the target layer to be open at the unit's position (R-002-02). */
static int try_start(const ll_state *s, ll_unit *u, int layer) {
    if (layer == u->layer) return 1;
    if (!ll_terrain_open(s->ter, u->x, u->y, layer)) return 0;
    begin_transfer(u, layer);
    return 1;
}

void ll_layers_update(ll_state *s) {
    for (int i = 0; i < s->n; i++) {
        ll_unit *u = &s->u[i];
        if (!u->alive) continue;
        double dur = u->ty->transition_s;
        if (u->xfer_to) {
            u->xfer_elapsed += LL_DT;
            if (u->xfer_elapsed >= dur - EPS) {
                set_layer(u, u->xfer_to);
                u->xfer_to = 0;
                u->xfer_elapsed = 0.0;
            }
        }
        if (u->xfer_ordered && s->tick >= s->sc->spawns[i].transfer_tick) {
            if (u->xfer_to) { u->xfer_pending = u->xfer_ordered; u->xfer_ordered = 0; }   /* R-004-04 */
            else if (try_start(s, u, u->xfer_ordered)) u->xfer_ordered = 0;
        }
        if (!u->xfer_to && u->xfer_pending && try_start(s, u, u->xfer_pending)) u->xfer_pending = 0;

        if (u->xfer_to) {
            int half = u->xfer_elapsed >= dur * 0.5 - EPS;
            set_layer(u, half && s->rules->timed_new_layer_at_half ? u->chg_to : u->chg_from);
            u->changing = 1;
            u->progress = dur > 0.0 ? u->xfer_elapsed / dur : 1.0;
            if (u->progress > 1.0) u->progress = 1.0;
        } else if (u->slope >= 0) {
            const ll_slope *sl = &s->ter->slope[u->slope];
            set_layer(u, ll_slope_layer(sl, u->slope_t));
            u->changing = 1;
            u->chg_from = sl->bottom_layer;
            u->chg_to = sl->top_layer;
            u->progress = u->slope_t;
        } else {
            u->changing = 0;
            u->chg_from = u->chg_to = 0;
            u->progress = 0.0;
        }
    }
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

/* ---- step 5: goals, steering, slopes ---- */

/* The goal point of a unit this tick (SPEC 5.10), or 0 when it has none. */
static int pick_goal(const ll_state *s, const ll_unit *u, const double *px, const double *py,
                     double *gx, double *gy) {
    int idle = u->order == LL_ORDER_HOLD || (u->order == LL_ORDER_MOVE && u->arrived);
    if (idle) {
        if (s->rules->chase_when_idle && u->aim < 0 && u->chase >= 0) {
            *gx = px[u->chase]; *gy = py[u->chase];
            return 1;
        }
        return 0;
    }
    if (u->order == LL_ORDER_MOVE) { *gx = u->gx; *gy = u->gy; return 1; }
    if (u->aim >= 0) return 0;                           /* ATTACK_MOVE: stands if it can fire */
    if (u->chase >= 0) { *gx = px[u->chase]; *gy = py[u->chase]; return 1; }
    double dx = u->gx - u->x, dy = u->gy - u->y;
    if (!(sqrt(dx * dx + dy * dy) > 1.5 * u->ty->body_radius)) return 0;
    *gx = u->gx; *gy = u->gy;
    return 1;
}

/* Where a unit may stand: a walker on land of its layer; a flyer on cells open on its layer, or on both
 * layers of a timed transfer in progress. */
static int can_stand(const ll_state *s, const ll_unit *u, double x, double y) {
    const ll_terrain *t = s->ter;
    if (is_walker(u)) return ll_terrain_land(t, x, y, u->layer);
    if (u->xfer_to) return ll_terrain_open(t, x, y, u->chg_from) && ll_terrain_open(t, x, y, u->chg_to);
    return ll_terrain_open(t, x, y, u->layer);
}

/* Hard bodies (SPEC 5.10): the step to (x,y) is refused when it lands closer than r_i + r_j to an alive unit on
 * the same effective layer (neither on a slope), unless already that close and not getting nearer. */
static int body_blocked(const ll_state *s, const ll_unit *u, double x, double y) {
    for (int j = 0; j < s->n; j++) {
        const ll_unit *o = &s->u[j];
        if (o == u || !o->alive || o->slope >= 0 || o->layer != u->layer) continue;
        double reach = u->ty->body_radius + o->ty->body_radius;
        double nx = x - o->x, ny = y - o->y;
        double after = nx * nx + ny * ny;
        if (!(after < reach * reach)) continue;
        double bx = u->x - o->x, by = u->y - o->y;
        if (bx * bx + by * by < reach * reach && after >= bx * bx + by * by) continue;
        return 1;
    }
    return 0;
}

/* Bodies on a slope (SPEC 5.9): the step to (x,y) is refused when it lands closer than r_i + r_j to another alive
 * unit on the SAME slope, unless already that close and not getting nearer. Units off the slope never count. */
static int slope_blocked(const ll_state *s, const ll_unit *u, double x, double y) {
    for (int j = 0; j < s->n; j++) {
        const ll_unit *o = &s->u[j];
        if (o == u || !o->alive || o->slope != u->slope) continue;
        double reach = u->ty->body_radius + o->ty->body_radius;
        double nx = x - o->x, ny = y - o->y;
        double after = nx * nx + ny * ny;
        if (!(after < reach * reach)) continue;
        double bx = u->x - o->x, by = u->y - o->y;
        if (bx * bx + by * by < reach * reach && after >= bx * bx + by * by) continue;
        return 1;
    }
    return 0;
}

/* Slope mouths (SPEC 5.10): 1 when (x,y) is within LL_MOUTH_RADIUS of the centre of a slope edge that lies on
 * `layer`. Inside it bodies neither block steps nor are pushed, or two walkers a body width apart at the entry,
 * whose centre can sit on a flow-field cell boundary, each stand where the other must step and wait forever. */
static int in_mouth(const ll_terrain *t, int layer, double x, double y) {
    for (int k = 0; k < t->n_slope; k++) {
        const ll_slope *sl = &t->slope[k];
        for (int top = 0; top < 2; top++) {
            if ((top ? sl->top_layer : sl->bottom_layer) != layer) continue;
            double ex, ey;
            ll_slope_edge(sl, top, &ex, &ey);
            double dx = x - ex, dy = y - ey;
            if (dx * dx + dy * dy <= LL_MOUTH_RADIUS * LL_MOUTH_RADIUS) return 1;
        }
    }
    return 0;
}

static int can_step(const ll_state *s, const ll_unit *u, double x, double y) {
    return can_stand(s, u, x, y) && (in_mouth(s->ter, u->layer, x, y) || !body_blocked(s, u, x, y));
}

/* How near a walker must be to a slope's edge centre to mount it (SPEC 5.9). */
static double mount_reach(const ll_state *s, const ll_unit *u) {
    return u->ty->body_radius > 0.5 * s->ter->cell ? u->ty->body_radius : 0.5 * s->ter->cell;
}

/* SPEC 5.9 lanes: lane i of a slope for a unit of body radius r is at offset 0, +30, -30, +60, -60, ... along the left
 * normal; there are 1 + 2 * m lanes where m is the number of multiples of 30 within the usable half-width. */
static int lane_count(const ll_slope *sl, double r) {
    double h = 0.5 * sl->width - r;
    int m = 0;
    while ((double)(m + 1) * LL_LANE_PITCH <= h + EPS) m++;
    return 1 + 2 * m;
}

static double lane_offset(int i) {
    return (double)((i + 1) / 2) * LL_LANE_PITCH * (i & 1 ? 1.0 : -1.0);
}

/* Mounts at the unit's lane (SPEC 5.9): the nearest lane to its own lateral position, or the nearest free one when
 * another unit on the slope is within a body width of the entry along the axis on that lane. Returns 0, leaving the
 * unit where it is, when every lane is occupied. Mounting is never blocked by bodies off the slope. */
static int mount(const ll_state *s, ll_unit *u, const ll_slope *sl, int index, int dir) {
    int n = lane_count(sl, u->ty->body_radius);
    double h = 0.5 * (double)(n - 1) * LL_LANE_PITCH;
    double lat = (u->x - sl->x0) * -sl->dy + (u->y - sl->y0) * sl->dx;
    if (lat > h) lat = h;
    if (lat < -h) lat = -h;
    double t0 = dir > 0 ? 0.0 : 1.0;
    int best = -1;
    double bestd = 0.0;
    for (int i = 0; i < n; i++) {
        double off = lane_offset(i);
        int taken = 0;
        for (int j = 0; j < s->n && !taken; j++) {
            const ll_unit *o = &s->u[j];
            if (o == u || !o->alive || o->slope != index) continue;
            double d = (o->slope_t - t0) * sl->length;
            if ((d < 0.0 ? -d : d) < LL_LANE_PITCH - EPS && o->slope_lane - off < EPS && off - o->slope_lane < EPS) taken = 1;
        }
        if (taken) continue;
        double d = lat - off;
        if (d < 0.0) d = -d;
        if (best < 0 || d < bestd - EPS) { best = i; bestd = d; }
    }
    if (best < 0) return 0;
    u->slope = index;
    u->slope_dir = dir;
    u->slope_t = t0;
    u->slope_lane = lane_offset(best);
    ll_slope_edge(sl, dir < 0, &u->x, &u->y);
    u->x -= sl->dy * u->slope_lane;
    u->y += sl->dx * u->slope_lane;
    u->changing = 1;
    u->chg_from = sl->bottom_layer;
    u->chg_to = sl->top_layer;
    u->progress = u->slope_t;
    return 1;
}

enum { STEER_STAND = 0, STEER_TARGET = 1, STEER_MOUNTED = 2 };

/* Chooses the point to steer toward: straight at the goal when the segment is clear, else down the flow
 * field. Starts a forced timed transfer or mounts a slope when the field says so (SPEC 5.10). `olayer` is
 * the layer the unit was ordered on, or 0 when it has none (a spawn transfer chose its layer for it). */
static int steer(ll_state *s, ll_unit *u, int olayer, double gx, double gy, double *tx, double *ty) {
    const ll_terrain *t = s->ter;
    int wk = is_walker(u);
    for (int pass = 0; pass < 2; pass++) {
        int nl = u->xfer_to ? u->xfer_to : u->layer;
        int ol = olayer ? olayer : nl;
        if (ll_segment_clear(t, u->x, u->y, gx, gy, nl, wk)) {
            /* Past the obstacle that forced a change: the route ends on the ordered layer (SPEC 5.10 goal layer). */
            int snapped0;
            int gc0 = ll_goal_cell(t, gx, gy, ol, wk, &snapped0);
            int gl0 = gc0 < 0 ? 0 : snapped0 ? ol : ll_goal_layer(t, gc0, ol, wk);
            if (!wk && !u->xfer_to && gl0 && gl0 != nl && ll_segment_clear(t, u->x, u->y, gx, gy, gl0, 0)) {
                begin_transfer(u, gl0);
                continue;
            }
            *tx = gx; *ty = gy;
            return STEER_TARGET;
        }
        int snapped;
        int gc = ll_goal_cell(t, gx, gy, ol, wk, &snapped);
        if (gc < 0) return STEER_STAND;
        int gl = snapped ? ol : ll_goal_layer(t, gc, ol, wk);
        const ll_field *f = gl ? ll_nav_field(s, gc, gl, u->type) : 0;
        int cell = ll_terrain_cell(t, u->x, u->y);
        double cost = f && cell >= 0 ? ll_field_cost(f, cell, nl) : LL_FAR;
        ll_step st = {0, 0, 0, -1};
        if (cost >= LL_FAR || (cost > 0.0 && !ll_field_step(s, f, cell, nl, &st))) {
            *tx = gx; *ty = gy;           /* no route (a blocked region, no auto-transition): walk at it and stop at the edge */
            return STEER_TARGET;
        }
        if (cost <= 0.0) {                /* in the goal cell: go to the point, or stop at a snapped cell's centre */
            if (snapped) ll_cell_centre(t, gc, tx, ty); else { *tx = gx; *ty = gy; }
            return STEER_TARGET;
        }
        if (st.kind == LL_STEP_MOVE) { ll_cell_centre(t, st.cell, tx, ty); return STEER_TARGET; }
        if (st.kind == LL_STEP_LAYER) {
            if (u->xfer_to) return STEER_STAND;
            begin_transfer(u, st.layer);  /* forced change; keep following the field from the new node */
            continue;
        }
        const ll_slope *sl = &t->slope[st.slope];
        int dir = st.layer == sl->top_layer ? 1 : -1;
        double ex, ey;
        ll_slope_edge(sl, dir < 0, &ex, &ey);
        double reach = mount_reach(s, u);
        if (sqrt((ex - u->x) * (ex - u->x) + (ey - u->y) * (ey - u->y)) <= reach) {
            return mount(s, u, sl, st.slope, dir) ? STEER_MOUNTED : STEER_STAND;
        }
        *tx = ex; *ty = ey;
        return STEER_TARGET;
    }
    return STEER_STAND;
}

static double edge_cost(const ll_terrain *t, const ll_field *f, const ll_slope *sl, int top) {
    double x, y;
    ll_slope_edge(sl, top, &x, &y);
    int c = ll_terrain_cell(t, x, y);
    return c < 0 ? LL_FAR : ll_field_cost(f, c, top ? sl->top_layer : sl->bottom_layer);
}

/* A unit on a slope re-chooses its goal each tick and heads for the edge with the cheaper cost-to-go
 * (ties keep the direction); with no goal it stops (SPEC 5.9). Returns the travel direction, 0 if stopped. */
static int ride(ll_state *s, ll_unit *u, int olayer, int have, double gx, double gy) {
    const ll_terrain *t = s->ter;
    const ll_slope *sl = &t->slope[u->slope];
    if (!have) return 0;
    int snapped, ol = olayer ? olayer : u->layer;
    int gc = ll_goal_cell(t, gx, gy, ol, 1, &snapped);
    int gl = gc < 0 ? 0 : snapped ? ol : ll_goal_layer(t, gc, ol, 1);
    const ll_field *f = gl ? ll_nav_field(s, gc, gl, u->type) : 0;
    if (f) {
        double cb = edge_cost(t, f, sl, 0), ct = edge_cost(t, f, sl, 1);
        if (ct < cb) u->slope_dir = 1;
        else if (cb < ct) u->slope_dir = -1;
    }
    double nt = u->slope_t + (double)u->slope_dir * u->ty->speed * LL_DT / sl->length;
    int done = u->slope_dir > 0 ? nt >= 1.0 - EPS : nt <= EPS;
    double ax = sl->x0 + sl->dx * sl->length * nt, ay = sl->y0 + sl->dy * sl->length * nt;
    if (done) ll_slope_edge(sl, u->slope_dir > 0, &ax, &ay);
    ax -= sl->dy * u->slope_lane;
    ay += sl->dx * u->slope_lane;
    if (slope_blocked(s, u, ax, ay)) return u->slope_dir;
    if (done) {
        u->slope = -1;
        u->changing = 0;
        u->chg_from = u->chg_to = 0;
        u->progress = 0.0;
        u->x = ax;
        u->y = ay;
        set_layer(u, u->slope_dir > 0 ? sl->top_layer : sl->bottom_layer);
        return 0;
    }
    u->slope_t = nt;
    u->x = ax;
    u->y = ay;
    u->progress = u->slope_t;
    return u->slope_dir;
}

void ll_move_units(ll_state *s) {
    const ll_terrain *ter = s->ter;
    double px[LL_MAX_UNITS], py[LL_MAX_UNITS];
    for (int i = 0; i < s->n; i++) { px[i] = s->u[i].x; py[i] = s->u[i].y; }

    for (int i = 0; i < s->n; i++) {
        ll_unit *u = &s->u[i];
        if (!u->alive || u->winding) continue;
        double gx = 0.0, gy = 0.0;
        int have = pick_goal(s, u, px, py, &gx, &gy);
        const ll_spawn *sp = &s->sc->spawns[i];
        int olayer = sp->transfer_layer ? 0 : sp->layer;

        if (u->slope >= 0) {
            const ll_slope *sl = &ter->slope[u->slope];
            int dir = ride(s, u, olayer, have, gx, gy);
            if (u->aim >= 0) turn_toward(u, px[u->aim] - u->x, py[u->aim] - u->y);
            else if (dir) turn_toward(u, sl->dx * (double)dir, sl->dy * (double)dir);
            continue;
        }

        double tx = 0.0, ty = 0.0, mdx = 0.0, mdy = 0.0;
        int steering = STEER_STAND;
        if (have) steering = steer(s, u, olayer, gx, gy, &tx, &ty);
        if (steering == STEER_TARGET) {
            mdx = tx - u->x; mdy = ty - u->y;
            double d = sqrt(mdx * mdx + mdy * mdy);
            if (d > 0.0) {
                double step = u->ty->speed * (u->xfer_to ? s->rules->transition_speed_mult : 1.0) * LL_DT;
                if (step > d) step = d;
                double sx = mdx / d * step, sy = mdy / d * step;
                if (can_step(s, u, u->x + sx, u->y + sy)) { u->x += sx; u->y += sy; }
                else if (can_step(s, u, u->x + sx, u->y)) u->x += sx;
                else if (can_step(s, u, u->x, u->y + sy)) u->y += sy;
                else {
                    /* sidestep (SPEC 5.10): +45, -45, +90, -90 degrees for even indices, mirrored for odd */
                    static const double rcos[4] = {0.7071067811865476, 0.7071067811865476, 0.0, 0.0};
                    static const double rsin[4] = {0.7071067811865476, -0.7071067811865476, 1.0, -1.0};
                    double side = (i & 1) ? -1.0 : 1.0;
                    for (int k = 0; k < 4; k++) {
                        double rx = rcos[k] * sx - side * rsin[k] * sy;
                        double ry = side * rsin[k] * sx + rcos[k] * sy;
                        if (can_step(s, u, u->x + rx, u->y + ry)) { u->x += rx; u->y += ry; break; }
                    }
                }
            } else steering = STEER_STAND;
        }

        if (u->aim >= 0) turn_toward(u, px[u->aim] - u->x, py[u->aim] - u->y);
        else if (steering == STEER_TARGET) turn_toward(u, mdx, mdy);
    }

    /* same-layer separation, LL_SEPARATION_PASSES times, pairs i < j; units on a slope or winding up are not pushed */
    double w = s->rules->separation_weight;
    for (int pass = 0; pass < LL_SEPARATION_PASSES; pass++) {
        for (int i = 0; i < s->n; i++) {
            ll_unit *a = &s->u[i];
            if (!a->alive || a->slope >= 0) continue;
            for (int j = i + 1; j < s->n; j++) {
                ll_unit *b = &s->u[j];
                if (!b->alive || b->slope >= 0 || a->layer != b->layer) continue;
                if (in_mouth(s->ter, a->layer, a->x, a->y) || in_mouth(s->ter, b->layer, b->x, b->y)) continue;
                double dx = b->x - a->x, dy = b->y - a->y;
                double dist = sqrt(dx * dx + dy * dy);
                double overlap = a->ty->body_radius + b->ty->body_radius - dist;
                if (!(overlap > 0.0)) continue;
                double ax = 1.0, ay = 0.0;
                if (dist > 0.0) { ax = dx / dist; ay = dy / dist; }
                double push = overlap / 2.0 * w;
                if (!a->winding && can_stand(s, a, a->x - ax * push, a->y - ay * push)) {
                    a->x -= ax * push; a->y -= ay * push;
                }
                if (!b->winding && can_stand(s, b, b->x + ax * push, b->y + ay * push)) {
                    b->x += ax * push; b->y += ay * push;
                }
            }
        }
    }
}
