/* ll_sim.c -- ll_run: validation, spawn placement, the tick loop, termination, results, trace.
 *
 * Tick order (one tick = 1/20 s):
 *   1 cooldowns tick down          2 effective layer, MOVE arrival      3 side visibility
 *   4 acquisition, then fire (decisions only, damage queued)            5 movement, facing, separation
 *   6 queued damage applied, deaths, cost_lost    then termination (5.11) and the trace record
 * R0 implements fixed-layer combat; features owned by R1/R2 are rejected here, never ignored. */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ll_internal.h"

static char g_err[256];

void ll_err(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(g_err, sizeof g_err, fmt, ap);
    va_end(ap);
}

const char *ll_last_error(void) { return g_err; }

uint32_t ll_abi_version(void) { return LL_ABI_VERSION; }

uint32_t ll_sizeof(int which) {
    switch (which) {
    case 0: return (uint32_t)sizeof(ll_rules);
    case 1: return (uint32_t)sizeof(ll_unit_type);
    case 2: return (uint32_t)sizeof(ll_terrain);
    case 3: return (uint32_t)sizeof(ll_spawn);
    case 4: return (uint32_t)sizeof(ll_scenario);
    case 5: return (uint32_t)sizeof(ll_result);
    case 6: return (uint32_t)sizeof(ll_trace_rec);
    default: return 0;
    }
}

/* ---- validation ---- */

static int bool01(int32_t v) { return v == 0 || v == 1; }

static int table_ok(const double *t, int n) {
    for (int i = 0; i < n; i++)
        if (!ll_finite(t[i]) || t[i] < 0.0) return 0;
    return 1;
}

static int nonneg(double v) { return ll_finite(v) && v >= 0.0; }

static const char *validate_rules(const ll_rules *r) {
    if (!table_ok(r->vis_factor, 9)) return "rules: vis_factor must be finite and >= 0";
    if (!table_ok(r->vantage_vis_factor, 9)) return "rules: vantage_vis_factor must be finite and >= 0";
    if (!ll_finite(r->sensor_elev_bonus_per_layer)) return "rules: sensor_elev_bonus_per_layer not finite";
    if (!table_ok(r->range_mult, 9)) return "rules: range_mult must be finite and >= 0";
    if (!table_ok(r->dmg_mult, 9)) return "rules: dmg_mult must be finite and >= 0";
    if (!table_ok(r->aoe_layer_mult, 9)) return "rules: aoe_layer_mult must be finite and >= 0";
    if (!table_ok(&r->category_mult[0][0], 9)) return "rules: category_mult must be finite and >= 0";
    if (!nonneg(r->aoe_cap_mult)) return "rules: aoe_cap_mult must be finite and >= 0";
    if (!nonneg(r->pulse_radius) || !nonneg(r->pulse_reveal_s) || !nonneg(r->pulse_cooldown_s))
        return "rules: pulse parameters must be finite and >= 0";
    if (!nonneg(r->transition_speed_mult)) return "rules: transition_speed_mult must be finite and >= 0";
    if (!ll_finite(r->separation_weight) || r->separation_weight < 0.0 || r->separation_weight > 1.0)
        return "rules: separation_weight must be in [0, 1]";
    if (!nonneg(r->spawn_jitter)) return "rules: spawn_jitter must be finite and >= 0";
    if (!bool01(r->fire_requires_vision)) return "rules: fire_requires_vision must be 0 or 1";
    if (!bool01(r->facing_gates_fire)) return "rules: facing_gates_fire must be 0 or 1";
    if (r->halfway_mode < LL_HALFWAY_BOTH || r->halfway_mode > LL_HALFWAY_UNTARGETABLE)
        return "rules: halfway_mode out of range";
    if (!bool01(r->auto_transition)) return "rules: auto_transition must be 0 or 1";
    if (!bool01(r->cover_mode)) return "rules: cover_mode must be 0 or 1";
    if (!bool01(r->chase_when_idle)) return "rules: chase_when_idle must be 0 or 1";
    if (r->forced_change_penalty < 0) return "rules: forced_change_penalty must be >= 0";
    if (!bool01(r->timed_new_layer_at_half)) return "rules: timed_new_layer_at_half must be 0 or 1";
    if (r->max_ticks < 1) return "rules: max_ticks must be >= 1";
    if (r->stalemate_ticks < 1) return "rules: stalemate_ticks must be >= 1";
    return 0;
}

static const char *validate_type(const ll_unit_type *t) {
    if (t->category < LL_CAT_STRIKE || t->category > LL_CAT_SIEGE) return "type: category out of range";
    if (t->movement_kind != LL_MOVE_FLY && t->movement_kind != LL_MOVE_WALK) return "type: movement_kind out of range";
    if (t->ability_kind != LL_ABILITY_NONE && t->ability_kind != LL_ABILITY_BURST) return "type: ability_kind out of range";
    if (!ll_finite(t->hp) || t->hp <= 0.0) return "type: hp must be > 0";
    if (!ll_finite(t->interval_s) || t->interval_s <= 0.0) return "type: interval_s must be > 0";
    if (!nonneg(t->dmg) || !nonneg(t->range) || !nonneg(t->speed) || !nonneg(t->sensor) ||
        !nonneg(t->transition_s) || !nonneg(t->aoe_r) || !nonneg(t->turn_rate) || !nonneg(t->cost))
        return "type: dmg, range, speed, sensor, transition_s, aoe_r, turn_rate, cost must be finite and >= 0";
    if (!ll_finite(t->arc_deg) || t->arc_deg <= 0.0) return "type: arc_deg must be > 0";
    if (!ll_finite(t->body_radius) || t->body_radius <= 0.0) return "type: body_radius must be > 0";
    if (t->ab_min_targets < 0) return "type: ab_min_targets must be >= 0";
    if (!nonneg(t->ab_dmg_mult) || !nonneg(t->ab_radius) || !nonneg(t->ab_windup_s) || !nonneg(t->ab_cooldown_s))
        return "type: ability parameters must be finite and >= 0";
    if (!bool01(t->pulse_capable)) return "type: pulse_capable must be 0 or 1";
    return 0;
}

static const char *validate_spawn(const ll_scenario *sc, int i) {
    const ll_spawn *p = &sc->spawns[i];
    if (p->side != 0 && p->side != 1) return "spawn: side must be 0 or 1";
    if (p->type < 0 || p->type >= sc->n_types) return "spawn: type index out of range";
    if (!ll_finite(p->x) || !ll_finite(p->y) || !ll_finite(p->facing_deg) ||
        !ll_finite(p->gx) || !ll_finite(p->gy)) return "spawn: position, facing or goal not finite";
    if (p->layer < 1 || p->layer > LL_LAYERS) return "spawn: layer out of range";
    if (p->order < LL_ORDER_HOLD || p->order > LL_ORDER_ATTACK_MOVE) return "spawn: order out of range";
    if (!bool01(p->pre_revealed)) return "spawn: pre_revealed must be 0 or 1";
    if (p->transfer_layer < 0 || p->transfer_layer > LL_LAYERS) return "spawn: transfer_layer out of range";
    if (p->pulse_tick < -1) return "spawn: pulse_tick must be >= -1";
    if (p->target_policy < LL_TARGET_NEAREST || p->target_policy > LL_TARGET_HIGHEST_COST)
        return "spawn: target_policy out of range";
    return 0;
}

static int validate(const ll_scenario *sc) {
    const char *e = validate_rules(&sc->rules);
    if (!e) e = ll_terrain_validate(&sc->terrain);
    /* Feature gates belong to the module that implements the feature. */
    if (!e) e = ll_move_validate(sc);
    if (!e) e = ll_vision_validate(sc);
    if (!e) e = ll_combat_validate(sc);
    if (!e) e = ll_reach_validate(sc);
    if (!e) e = ll_emit_validate(sc);
    if (!e) e = ll_ping_validate(sc);
    if (!e && (sc->n_types < 1 || sc->n_types > LL_MAX_TYPES)) e = "scenario: n_types out of range";
    if (!e && (sc->n_spawns < 0 || sc->n_spawns > LL_MAX_UNITS)) e = "scenario: n_spawns out of range";
    for (int i = 0; !e && i < sc->n_types; i++) e = validate_type(&sc->types[i]);
    for (int i = 0; !e && i < sc->n_spawns; i++) e = validate_spawn(sc, i);
    if (e) { ll_err("%s", e); return 1; }
    return 0;
}

/* ---- setup: validation and spawn placement (draw order of SPEC 5.13) ---- */

static int setup(ll_state *s, const ll_scenario *sc, uint64_t seed) {
    if (validate(sc)) return 1;
    memset(s, 0, sizeof *s);
    s->alerted_tick[0] = s->alerted_tick[1] = -1;
    s->sc = sc;
    s->rules = &sc->rules;
    s->ter = &sc->terrain;
    s->n = sc->n_spawns;

    ll_rng rng;
    ll_rng_seed(&rng, seed);
    double j = sc->rules.spawn_jitter;
    for (int i = 0; i < s->n; i++) {
        const ll_spawn *p = &sc->spawns[i];
        ll_unit *u = &s->u[i];
        if (!ll_terrain_open(&sc->terrain, p->x, p->y, p->layer)) {
            ll_err("spawn %d: (%g, %g) is outside the arena or blocked on layer %d", i, p->x, p->y, p->layer);
            return 1;
        }
        double jx = ll_rng_range(&rng, -j, j);
        double jy = ll_rng_range(&rng, -j, j);
        double cd = ll_rng_range(&rng, 0.0, sc->types[p->type].interval_s);
        u->ty = &sc->types[p->type];
        u->side = p->side;
        u->type = p->type;
        u->order = p->order;
        u->policy = p->target_policy;
        u->layer = p->layer;
        u->alive = 1;
        u->pre_revealed = p->pre_revealed;
        u->x = p->x + jx;
        u->y = p->y + jy;
        if (!ll_terrain_open(&sc->terrain, u->x, u->y, u->layer)) {
            ll_err("spawn %d: jitter moved the unit outside the arena or onto a blocked cell", i);
            return 1;
        }
        u->hp = u->hp0 = u->ty->hp;
        u->cooldown = cd;
        u->gx = p->gx;
        u->gy = p->gy;
        u->target = u->aim = u->chase = -1;
        u->slope = -1;
        u->emit = p->emit;
        u->xfer_ordered = p->transfer_layer;
        ll_face_init(u, p->facing_deg);
        u->arc_gate = sc->rules.facing_gates_fire && u->ty->arc_deg < 360.0;   /* SPEC 5.4, 5.12 */
        if (u->arc_gate) {
            double sn, cs;
            ll_sincos(u->ty->arc_deg * 0.5 * (LL_PI / 180.0), &sn, &cs);
            u->arc_cos = cs;
        }
    }
    return 0;
}

int ll_probe_can_see(const ll_scenario *sc, uint64_t seed, int observer, int target) {
    ll_err("%s", "");
    if (!sc) { ll_err("null scenario"); return -1; }
    ll_state *s = malloc(sizeof *s);
    if (!s) { ll_err("out of memory"); return -1; }
    int r = -1;
    if (!setup(s, sc, seed)) {
        if (observer < 0 || observer >= s->n || target < 0 || target >= s->n)
            ll_err("probe: unit index out of range");
        else
            r = ll_can_see(s, observer, target);
    }
    free(s);
    return r;
}

/* ---- the run ---- */

int ll_run(const ll_scenario *sc, uint64_t seed, ll_result *out, ll_trace *trace) {
    ll_err("%s", "");
    if (!sc || !out) { ll_err("null scenario or result"); return 1; }
    if (trace && (!trace->buf || trace->capacity_ticks < 0)) { ll_err("trace: bad buffer"); return 1; }
    memset(out, 0, sizeof *out);
    out->first_shot_side = out->first_shot_tick = out->first_contact_tick = -1;
    out->winner = LL_WIN_NONE;
    out->alerted_tick[0] = out->alerted_tick[1] = -1;
    if (trace) trace->ticks_written = 0;

    ll_state *s = malloc(sizeof *s);
    if (!s) { ll_err("out of memory"); return 1; }
    if (setup(s, sc, seed)) { free(s); return 1; }
    if (ll_nav_init(s)) { free(s); return 1; }

    double hp0[2] = {0.0, 0.0};
    for (int i = 0; i < s->n; i++) hp0[s->u[i].side] += s->u[i].hp0;

    int stale = 0, ran = 0;
    const int max_ticks = sc->rules.max_ticks;
    for (int tick = 0; tick < max_ticks; tick++) {
        s->tick = tick;
        int alive_start[2] = {0, 0};
        for (int i = 0; i < s->n; i++) {                       /* step 1 */
            if (!s->u[i].alive) continue;
            alive_start[s->u[i].side]++;
            s->u[i].cooldown -= LL_DT;
        }
        ll_layers_update(s);                                 /* step 2: effective layers, transfers */
        ll_update_arrival(s);
        ll_pulse_update(s);                                  /* step 3: pulses, then vision */
        ll_emit_update(s);                                   /* step 3: going dark switches, pings (ABI 3) */
        ll_ping_update(s);
        if (ll_side_vision(s) && out->first_contact_tick < 0)
            out->first_contact_tick = tick;
        ll_acquire(s);                                       /* step 4 */
        ll_fire(s);
        ll_burst_update(s);
        uint8_t can_fire[LL_MAX_UNITS];                       /* SPEC 5.11a: measurement only */
        for (int i = 0; i < s->n; i++) {
            const ll_unit *u = &s->u[i];
            can_fire[i] = 0;
            if (!u->alive) continue;
            out->alive_ticks[u->side]++;
            if (u->winding || u->target < 0) continue;
            can_fire[i] = 1;
            out->firing_ticks[u->side]++;
            out->firing_weight[u->side] += sc->rules.category_mult[u->ty->category][s->u[u->target].ty->category];
        }
        if (out->first_shot_tick < 0 && (s->fired_side[0] || s->fired_side[1])) {
            out->first_shot_tick = tick;
            out->first_shot_side = s->fired_side[0] ? 0 : 1;
        }
        if (alive_start[0] > 0 && alive_start[1] > 0) {
            if (s->fired_side[0] && !s->fired_side[1]) out->unanswered_ticks[0]++;
            if (s->fired_side[1] && !s->fired_side[0]) out->unanswered_ticks[1]++;
        }
        ll_move_units(s);                                    /* step 5 */
        int hurt = ll_apply_damage(s);                       /* step 6 */
        ran = tick + 1;

        int alive[2] = {0, 0};
        for (int i = 0; i < s->n; i++) if (s->u[i].alive) alive[s->u[i].side]++;
        stale = hurt ? 0 : stale + 1;

        if (trace && trace->ticks_written < trace->capacity_ticks) {
            ll_trace_rec *rec = trace->buf + (size_t)trace->ticks_written * (size_t)s->n;
            for (int i = 0; i < s->n; i++) {
                const ll_unit *u = &s->u[i];
                rec[i].x = (float)u->x;
                rec[i].y = (float)u->y;
                rec[i].hp = (float)u->hp;
                rec[i].progress = (float)u->progress;
                rec[i].layer = (uint8_t)u->layer;
                rec[i].side = (uint8_t)u->side;
                rec[i].alive = (uint8_t)u->alive;
                rec[i].flags = (uint8_t)((u->changing ? 1 : 0) | (u->fired ? 2 : 0) |
                                         (u->slope >= 0 ? 4 : 0) | (s->sees[1 - u->side][i] ? 8 : 0) |
                                         (can_fire[i] ? 16 : 0));
            }
            trace->ticks_written++;
        }

        if (alive[0] == 0 || alive[1] == 0) {
            out->winner = (alive[0] == 0 && alive[1] == 0) ? LL_WIN_MUTUAL : (alive[0] ? LL_WIN_A : LL_WIN_B);
            break;
        }
        if (stale >= sc->rules.stalemate_ticks) { out->winner = LL_WIN_STALEMATE; break; }
        if (tick + 1 == max_ticks) { out->winner = LL_WIN_CAP; break; }
    }

    ll_nav_free(s);
    for (int k = 0; k < 2; k++) {
        out->alerted_tick[k] = s->alerted_tick[k]; out->alerts[k] = s->alerts[k];
        out->alert_dir_x[k] = s->alert_dx[k]; out->alert_dir_y[k] = s->alert_dy[k];
    }
    out->ticks = ran;
    double hp_left[2] = {0.0, 0.0};
    for (int i = 0; i < s->n; i++) {
        const ll_unit *u = &s->u[i];
        if (u->alive) { out->survivors[u->side]++; hp_left[u->side] += u->hp; }
        out->transitions += u->transitions;
        out->unit[i].x = u->x;
        out->unit[i].y = u->y;
        out->unit[i].hp = u->hp;
        out->unit[i].layer = u->layer;
        out->unit[i].alive = u->alive;
        out->unit[i].transitions = u->transitions;
    }
    for (int side = 0; side < 2; side++) {
        out->hp_ratio[side] = hp0[side] > 0.0 ? hp_left[side] / hp0[side] : 0.0;
        out->cost_lost[side] = s->cost_lost[side];
        out->damage_dealt[side] = s->damage_dealt[side];
        out->shots[side] = s->shots[side];
    }
    free(s);
    return 0;
}
