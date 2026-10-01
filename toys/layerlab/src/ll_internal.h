/* ll_internal.h -- shared internal state of the layer lab (not part of the ABI).
 * Behavior is specified in SPEC.md section 5; each function names its section. */
#ifndef LL_INTERNAL_H
#define LL_INTERNAL_H

#include "layerlab.h"

#define LL_DT  (1.0 / LL_TICKS_PER_SEC)
#define LL_PI  3.14159265358979323846

/* ---- RNG (SPEC 5.13) ---- */
typedef struct ll_rng { uint64_t state, inc; } ll_rng;
void     ll_rng_seed(ll_rng *r, uint64_t seed);
uint32_t ll_rng_next32(ll_rng *r);
double   ll_rng_u(ll_rng *r);                         /* [0, 1), 53 bits */
double   ll_rng_range(ll_rng *r, double lo, double hi); /* U(lo, hi) */

/* ---- numerics (SPEC 5.12) ---- */
double ll_wrap_pi(double a);
void   ll_sincos(double a, double *s, double *c);     /* Taylor, 7 terms, wrapped to [-pi, pi] */
double ll_dist3(double dx, double dy, int dl, double layer_spacing);
int    ll_finite(double x);

/* ---- per-run state ---- */
typedef struct ll_unit {
    int    side, type, order, policy;
    int    layer;                 /* effective layer (SPEC 5.1) */
    int    alive, arrived;
    int    changing, chg_from, chg_to;   /* layer change in progress (R1; always 0 in R0) */
    int    transitions;
    int    pre_revealed;
    int    target, aim, chase;    /* -1 none; set by ll_acquire */
    int    fired;                 /* fired a shot this tick */
    double x, y, hp, hp0, cooldown;
    double fx, fy;                /* facing, unit vector */
    double gx, gy;                /* order goal */
    double arc_cos;               /* cos(arc/2); only meaningful when arc_gate */
    int    arc_gate;              /* 0 when arc_deg >= 360 */
    const ll_unit_type *ty;
} ll_unit;

typedef struct ll_state {
    const ll_scenario *sc;
    const ll_rules    *rules;
    const ll_terrain  *ter;
    int      n;
    int      tick;
    ll_unit  u[LL_MAX_UNITS];
    uint8_t  sees[2][LL_MAX_UNITS];       /* side_sees (SPEC 5.2) */
    double   direct[LL_MAX_UNITS];        /* damage queue, this tick */
    double   area_sum[LL_MAX_UNITS];
    double   area_max[LL_MAX_UNITS];
    double   cost_lost[2];
    double   damage_dealt[2];
    int      shots[2];
    int      fired_side[2];               /* shots fired this tick, per side */
} ll_state;

/* ---- errors (ll_sim.c) ---- */
void ll_err(const char *fmt, ...);

/* ---- terrain (ll_terrain.c): flat grid queries ---- */
const char *ll_terrain_validate(const ll_terrain *t);   /* NULL when fine */
int ll_terrain_cell(const ll_terrain *t, double x, double y);   /* cell index or -1 outside */
int ll_terrain_open(const ll_terrain *t, double x, double y, int layer); /* in bounds and layer open */
double ll_terrain_width(const ll_terrain *t);
double ll_terrain_height(const ll_terrain *t);

/* ---- vision (ll_vision.c) ---- */
int ll_can_see(const ll_state *s, int o, int t);        /* SPEC 5.2 steps 1-5 */
int ll_side_vision(ll_state *s);                        /* fills s->sees; 1 if any enemy is seen */

/* ---- movement (ll_move.c) ---- */
void ll_face_init(ll_unit *u, double facing_deg);
void ll_update_arrival(ll_state *s);                    /* step 2: MOVE arrival */
void ll_move_units(ll_state *s);                        /* step 5: steer, turn, separate */

/* ---- combat (ll_combat.c) ---- */
int  ll_eligible(const ll_state *s, const ll_unit *a, const ll_unit *e, int *off); /* halfway rule, SPEC 5.4 */
void ll_acquire(ll_state *s);                           /* SPEC 5.4 */
void ll_fire(ll_state *s);                              /* SPEC 5.5, queues damage */
int  ll_apply_damage(ll_state *s);                      /* step 6; returns 1 if any HP was lost */

#endif /* LL_INTERNAL_H */
