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
    int    changing, chg_from, chg_to;   /* layer change in progress: timed transfer or slope */
    int    transitions;                  /* times u->layer changed value */
    int    pre_revealed;
    int    target, aim, chase;    /* -1 none; set by ll_acquire */
    int    fired;                 /* fired a shot this tick */
    double x, y, hp, hp0, cooldown;
    double fx, fy;                /* facing, unit vector */
    double gx, gy;                /* order goal */
    double arc_cos;               /* cos(arc/2); only meaningful when arc_gate */
    int    arc_gate;              /* 0 when arc_deg >= 360 */
    const ll_unit_type *ty;

    /* ---- movement state (owner: ll_move.c, SPEC 5.8-5.10). Zeroed by setup; slope = -1. ---- */
    int    xfer_to;               /* timed transfer in progress: target layer, else 0 */
    double xfer_elapsed;          /* seconds into the transfer */
    int    xfer_pending;          /* layer to start when the current transfer completes, else 0 */
    int    xfer_ordered;          /* spawn.transfer_layer not yet started (waiting for its tick or an open cell) */
    int    slope;                 /* index into terrain slope[] while on one, else -1 */
    int    slope_dir;             /* +1 climbing toward the top edge, -1 toward the bottom */
    double slope_t;               /* position along the slope, 0 bottom .. 1 top */
    double slope_lane;            /* lateral offset from the slope axis along its left normal while on it (SPEC 5.9 lanes) */
    double progress;              /* 0..1 transition progress for the trace (0 when not changing) */
    /* ---- vision state (owner: ll_vision.c, SPEC 5.7) ---- */
    int    pulse_until;           /* tick before which this unit's pulse reveal is active, else 0 */
    int    pulse_ready_tick;      /* first tick the pulse may be used again */
    /* ---- combat state (owner: ll_combat.c, SPEC 5.6) ---- */
    int    winding;               /* 1 while casting: no move, no fire */
    double ab_wind_left;          /* seconds of windup remaining */
    double ab_cd;                 /* ability cooldown remaining, seconds */
    double ab_cx, ab_cy;          /* locked cast centre */
    /* ---- going dark (owner: ll_emit.c, E-01 S-163, ABI 3) ---- */
    int    emit;                  /* current state: 1 emit, 0 silent */
    /* ---- targeted ping (owner: ll_ping.c, E-01 S-162, ABI 3) ---- */
    int    ping_until;            /* tick before which this unit's ping reveal is active, else 0 */
    int    ping_ready_tick;       /* first tick this unit may ping again */
    int    ping_layer;            /* the pinged layer of the active ping */
    double ping_px, ping_py;      /* the pinged place of the active ping */
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
    void    *nav;                         /* flow-field cache (owner: ll_terrain.c); NULL until ll_nav_init */
    /* ping alerts (owner: ll_ping.c, ABI 3): per side, filled by ll_ping_update, copied to ll_result */
    int      alerted_tick[2];             /* first alert tick, -1 none */
    int      alerts[2];
    double   alert_dx[2], alert_dy[2];    /* unit vector toward the first pinger (revealed units' centroid to pinger) */
} ll_state;

/* ---- errors (ll_sim.c) ---- */
void ll_err(const char *fmt, ...);

/* ---- terrain and navigation (ll_terrain.c) ---- */
int  ll_nav_init(ll_state *s);                          /* allocate caches; 0 ok, 1 error (ll_err set) */
void ll_nav_free(ll_state *s);                          /* always safe, even after a failed init */
const char *ll_terrain_validate(const ll_terrain *t);   /* NULL when fine */
int ll_terrain_cell(const ll_terrain *t, double x, double y);   /* cell index or -1 outside */
int ll_terrain_open(const ll_terrain *t, double x, double y, int layer); /* in bounds and layer open */
double ll_terrain_width(const ll_terrain *t);
double ll_terrain_height(const ll_terrain *t);

/* ---- vision (ll_vision.c) ---- */
const char *ll_vision_validate(const ll_scenario *sc);  /* NULL when fine; the R1 feature gates live here */
void ll_pulse_update(ll_state *s);                      /* step 3a: start scheduled pulses, expire reveals (SPEC 5.7) */
int ll_can_see(const ll_state *s, int o, int t);        /* SPEC 5.2 steps 1-5 */
int ll_side_vision(ll_state *s);                        /* fills s->sees; 1 if any enemy is seen */

/* ---- movement (ll_move.c) ---- */
const char *ll_move_validate(const ll_scenario *sc);    /* NULL when fine; walking, transfers, slopes gates live here */
void ll_layers_update(ll_state *s);                     /* step 2: scheduled transfers, effective layer, changing flags (SPEC 5.1, 5.8, 5.9) */
void ll_face_init(ll_unit *u, double facing_deg);
void ll_update_arrival(ll_state *s);                    /* step 2: MOVE arrival */
void ll_move_units(ll_state *s);                        /* step 5: steer, turn, separate */

/* ---- reach by unit type (ll_reach.c, E-01 S-164, ABI 3) ---- */
const char *ll_reach_validate(const ll_scenario *sc);   /* NULL when fine */
double ll_reach_mult(const ll_unit *a, int off);        /* multiplier on a's range at signed offset index `off`; 1.0 when the type has no table; 0 = cannot fire */

/* ---- going dark (ll_emit.c, E-01 S-163, ABI 3) ---- */
const char *ll_emit_validate(const ll_scenario *sc);
void   ll_emit_update(ll_state *s);                     /* step 3a: apply scheduled emit/silent switches */
double ll_emit_factor(const ll_state *s, int o, int t); /* cross-layer sight multiplier for observer o looking at target t: 1.0 when rules.emit_on is 0 or on the same layer */

/* ---- targeted ping (ll_ping.c, E-01 S-162, ABI 3) ---- */
const char *ll_ping_validate(const ll_scenario *sc);
void ll_ping_update(ll_state *s);                       /* step 3a: start scheduled pings, expire windows, record alerts */
int  ll_ping_reveals(const ll_state *s, int side, int t); /* 1 when an active ping of `side` reveals unit t now */

/* ---- combat (ll_combat.c) ---- */
const char *ll_combat_validate(const ll_scenario *sc);  /* NULL when fine; the burst-ability gate lives here */
void ll_burst_update(ll_state *s);                      /* step 4b: ability cooldowns, windups, casts (SPEC 5.6); queues damage */
int  ll_eligible(const ll_state *s, const ll_unit *a, const ll_unit *e, int *off); /* halfway rule, SPEC 5.4 */
void ll_acquire(ll_state *s);                           /* SPEC 5.4 */
void ll_fire(ll_state *s);                              /* SPEC 5.5, queues damage */
int  ll_apply_damage(ll_state *s);                      /* step 6; returns 1 if any HP was lost */

#endif /* LL_INTERNAL_H */
