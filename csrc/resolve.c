/* csrc/resolve.c — E-05 intent resolution: reinforce, attack, damage, conquest, colonize (build card 204).
 * Skeleton written by the parent so the fenced suite fails red on assertions,
 * not on a missing symbol, and so the build harness has a file to read; every
 * body below is a STUB the build card replaces. */
/* PRIVATE LAYOUT, verbatim from csrc/om_internal.h (already included below).
 * Use exactly these member names; there are no others. Inventing a member
 * (previous_economy_osc, region_state, trace_enabled, adjacencies, faction_modifiers)
 * is a compile error and fails every test.
 * #define OM_MAX_NEIGHBORS 32
 * 
 * typedef struct {
 *     om_tier  tier;
 *     double   military, economy, tension, population;
 *     double   econ_phase, tension_phase;
 *     double   prev_econ_osc, prev_tension_osc;
 *     int32_t  faction_id;
 *     uint32_t neighbors[OM_MAX_NEIGHBORS];
 *     uint32_t n_neighbors;
 *     om_drift_row last_drift;
 * } om_region;
 * 
 * struct om_world {
 *     uint32_t n_regions;
 *     uint64_t seed;
 *     uint64_t tick;
 *     int      trace_on;
 *     int      inject;
 *     om_region *regions;
 *     double   faction_mod[OM_MAX_FACTIONS][OM_F_COUNT];
 *     om_trace_row *trace;
 *     uint64_t trace_len, trace_cap;
 * };
 */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <math.h>
#include <stddef.h>
#include <string.h>

uint32_t om_tick_attacks(const om_world *w, om_attack_result *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_reinforces(const om_world *w, om_reinforce *out, uint32_t max) {
    if (!w || !out || max == 0) return 0;
    
    uint32_t count = fmin(w->reinforces_n, max);
    for (uint32_t i = 0; i < count; ++i) {
        out[i] = w->reinforces[i];
    }
    return count;
}

uint32_t om_tick_colonizations(const om_world *w, om_colonize_result *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_event_queue(const om_world *w, om_queued_event *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

int om_intent_inject(om_world *w, int32_t faction_id, om_action action, uint32_t target_idx,
                     uint32_t source_idx, double commit, om_attack_mode mode) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS || !w->faction_used[faction_id]) return -1;
    if (target_idx >= w->n_regions || source_idx >= w->n_regions) return -1;
    if (w->regions[source_idx].faction_id != faction_id) return -1;
    if (commit > w->faction_budget[faction_id]) return -1;

    if (w->decisions_n >= 64) return -1;
    om_decision *d = &w->decisions[w->decisions_n++];
    memset(d, 0, sizeof(*d));
    d->tick = w->tick;
    d->faction_id = faction_id;
    d->action = (uint32_t)action;
    d->target_idx = target_idx;
    d->source_idx = source_idx;
    d->commit = commit;
    d->mode = (uint32_t)mode;
    return 0;
}

void om_region_add_damage(om_world *w, uint32_t idx, double military_loss, double economy_loss, uint64_t tick) {
    /* STUB */
    (void)w; (void)idx; (void)military_loss; (void)economy_loss; (void)tick;
}

double om_region_damage_history(const om_world *w, uint32_t idx) {
    /* STUB */
    (void)w; (void)idx;
    return 0.0;
}

void om_step_telegraphs(om_world *w) {
    /* STUB */
    (void)w;
}

void om_step_reinforce(om_world *w) {
    if (!w) return;
    w->reinforces_n = 0;
    
    for (uint32_t i = 0; i < w->telegraphs_n; ++i) {
        om_telegraph *t = &w->telegraphs[i];
        if (t->declared_tick != w->tick) continue;
        
        int32_t f = w->regions[t->target_idx].faction_id;
        if (f < 0) continue;
        
        double w_defend;
        switch (w->faction_archetype[f]) {
            case OM_ARCH_CONQUEROR:   w_defend = 0.4; break;
            case OM_ARCH_WARLORD:     w_defend = 0.3; break;
            case OM_ARCH_FORTIFIER:   w_defend = 1.5; break;
            case OM_ARCH_OPPORTUNIST: w_defend = 0.6; break;
            case OM_ARCH_SCHISM:      w_defend = 0.5; break;
            case OM_ARCH_PLAYER:      w_defend = 1.5; break;
            case OM_ARCH_BREAKAWAY:   w_defend = 0.8; break;
            default:                  w_defend = 0.8; break;
        }
        
        double reinforce_prob = fmin(1.0, w_defend / 1.5);
        
        double u;
        if (w->rng_forced_len > 0) {
            u = w->rng_forced[w->rng_forced_head];
            w->rng_forced_head++;
            w->rng_forced_len--;
        } else {
            uint32_t a = (uint32_t)(w->rng_state >> 5);
            uint32_t b = (uint32_t)(w->rng_state >> 6);
            u = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
            w->rng_state = w->rng_state * 6364136223846793005ULL + w->rng_inc;
        }
        
        if (u > reinforce_prob) continue;
        
        double commit = fmin(w->faction_budget_snapshot[f] * 0.30, t->commit * 0.5);
        if (commit < 1.0) continue;
        
        w->faction_budget[f] -= commit;
        
        double tier_cap = (w->regions[t->target_idx].tier == OM_TIER_HOME) ? 100.0 : 60.0;
        double headroom = fmax(0.0, (tier_cap - w->regions[t->target_idx].military) / tier_cap);
        double base = commit * 0.5 * headroom;
        
        double tension = w->regions[t->target_idx].tension;
        double lo = 0.85 - (tension / 100.0) * 0.20;
        double hi = 1.15 + (tension / 100.0) * 0.20;
        
        double u2;
        if (w->rng_forced_len > 0) {
            u2 = w->rng_forced[w->rng_forced_head];
            w->rng_forced_head++;
            w->rng_forced_len--;
        } else {
            uint32_t a = (uint32_t)(w->rng_state >> 5);
            uint32_t b = (uint32_t)(w->rng_state >> 6);
            u2 = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
            w->rng_state = w->rng_state * 6364136223846793005ULL + w->rng_inc;
        }
        
        double variance = lo + (hi - lo) * u2;
        double d_military = base * variance;
        
        if (w->reinforces_n < 64) {
            om_reinforce *r = &w->reinforces[w->reinforces_n];
            r->tick = w->tick;
            r->faction_id = f;
            r->target_idx = t->target_idx;
            r->commit = commit;
            r->headroom = headroom;
            r->base = base;
            r->variance = variance;
            r->d_military = d_military;
            w->reinforces_n++;
        }
        
        w->regions[t->target_idx].military += d_military;
    }
}

void om_step_resolve(om_world *w) {
    /* STUB */
    (void)w;
}
