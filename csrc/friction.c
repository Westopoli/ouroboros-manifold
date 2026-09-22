/* csrc/friction.c — E-05 border friction and admin revolt rolls (build card 206).
 * Border friction (ALG-25, docs/bible/algorithms.md) and admin revolt rolls
 * (ALG-29) — tick steps 4 and 4.1, wired in csrc/sim.c's om_world_step. */
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
#include "om_constants.h"
#include <math.h>
#include <stddef.h>
#include <string.h>

uint32_t om_tick_friction(const om_world *w, om_friction *out, uint32_t max) {
    if (!w || !out || max == 0) return 0;

    uint32_t count = w->frictions_n < max ? w->frictions_n : max;
    for (uint32_t i = 0; i < count; ++i) {
        out[i] = w->frictions[i];
    }
    return count;
}

uint32_t om_tick_admin_rolls(const om_world *w, om_admin_roll *out, uint32_t max) {
    if (!w || !out || max == 0) return 0;

    uint32_t count = w->admin_rolls_n < max ? w->admin_rolls_n : max;
    for (uint32_t i = 0; i < count; ++i) {
        out[i] = w->admin_rolls[i];
    }
    return count;
}

/* Same forced-RNG-then-LCG draw every other module uses (csrc/resolve.c's
 * om_step_reinforce, csrc/sim.c's conquest-unrest draw). */
static double om_friction_draw(om_world *w) {
    if (w->rng_forced_len > 0) {
        double u = w->rng_forced[w->rng_forced_head];
        w->rng_forced_head++;
        w->rng_forced_len--;
        return u;
    }
    uint32_t a = (uint32_t)(w->rng_state >> 5);
    uint32_t b = (uint32_t)(w->rng_state >> 6);
    double unif = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
    w->rng_state = w->rng_state * 6364136223846793005ULL + w->rng_inc;
    return unif;
}

void om_step_friction(om_world *w) {
    if (!w) return;
    w->frictions_n = 0;

    int trade_counts = 0;
#ifdef OM_DEBUG_INJECT
    trade_counts = (w->inject == OM_BUG_FRICTION_COUNTS_TRADE);
#endif

    for (uint32_t i = 0; i < w->n_regions; ++i) {
        om_region *r = &w->regions[i];
        if (r->tier == OM_TIER_EMPTY) continue;
        if (r->faction_id < 0) continue;

        uint32_t hostile_neighbors = 0;
        for (uint32_t j = 0; j < w->n_regions; ++j) {
            if (i == j) continue;

            om_edge_type edge;
            if (!om_region_edge(w, i, j, &edge)) continue;
            if (edge == OM_EDGE_TRADE && !trade_counts) continue;

            int32_t nb_faction = w->regions[j].faction_id;
            if (nb_faction < 0) continue;
            if (nb_faction == r->faction_id) continue;

            om_stance a_to_b = om_faction_stance(w, r->faction_id, nb_faction);
            om_stance b_to_a = om_faction_stance(w, nb_faction, r->faction_id);
            if (a_to_b != OM_STANCE_HOSTILE && b_to_a != OM_STANCE_HOSTILE) continue;

            hostile_neighbors++;
        }

        if (hostile_neighbors == 0) continue;

        double sum_tension = OM_BORDER_FRICTION_TENSION * (double)hostile_neighbors;
        double sum_economy = OM_BORDER_FRICTION_ECONOMY * (double)hostile_neighbors;

        double tension_before = r->tension;
        double economy_before = r->economy;
        double tension_after = fmin(100.0, tension_before + sum_tension);
        double economy_after = fmax(OM_ECONOMY_FLOOR, economy_before - sum_economy);
        r->tension = tension_after;
        r->economy = economy_after;

        if (w->frictions_n < 64) {
            om_friction *f = &w->frictions[w->frictions_n++];
            f->region_idx = i;
            f->hostile_neighbors = hostile_neighbors;
            f->d_tension = tension_after - tension_before;
            f->d_economy = economy_after - economy_before;
        }
    }
}

void om_step_admin_revolts(om_world *w) {
    if (!w) return;
    w->admin_rolls_n = 0;

    int per_faction_bug = 0;
#ifdef OM_DEBUG_INJECT
    per_faction_bug = (w->inject == OM_BUG_ADMIN_ROLL_PER_FACTION);
#endif
    int seen_faction[OM_MAX_FACTIONS];
    memset(seen_faction, 0, sizeof(seen_faction));

    for (uint32_t i = 0; i < w->n_regions; ++i) {
        int32_t fid = w->regions[i].faction_id;
        if (fid < 0) continue;

        if (per_faction_bug) {
            if (fid < OM_MAX_FACTIONS && seen_faction[fid]) continue;
            if (fid < OM_MAX_FACTIONS) seen_faction[fid] = 1;
        }

        uint32_t territory = om_faction_territory(w, fid);
        uint32_t excess = territory > OM_ADMIN_REVOLT_INFLECTION_POINT
            ? territory - OM_ADMIN_REVOLT_INFLECTION_POINT : 0;
        double chance = OM_ADMIN_REVOLT_BASE_RATE
            + OM_ADMIN_REVOLT_SCALING_RATE * (double)excess * (double)excess;

        double draw = om_friction_draw(w);
        uint32_t triggered = draw < chance ? 1 : 0;

        if (w->admin_rolls_n < 64) {
            om_admin_roll *roll = &w->admin_rolls[w->admin_rolls_n++];
            roll->tick = w->tick;
            roll->faction_id = fid;
            roll->region_idx = i;
            roll->chance = chance;
            roll->draw = draw;
            roll->triggered = triggered;
            roll->_pad = 0;
        }

        if (!triggered) continue;

        double l_draw = om_friction_draw(w);
        int32_t chain_length = 3 + (int32_t)floor(l_draw * 6.0);

        if (w->event_queue_n < 64) {
            om_queued_event *ev = &w->event_queue[w->event_queue_n++];
            ev->due_tick = w->tick + 1;
            ev->region_idx = i;
            ev->template_id = OM_EVT_ADMIN_SEPARATIST;
            ev->probability = 1.0;
            /* No public setter for the shared chain-tag counter exists in
             * this contract; mirrors csrc/resolve.c's own ALG-22 queue write
             * (chain_tag = 0 placeholder there too). Logged in
             * leaf-01.ASSUMPTIONS.md. */
            ev->chain_tag = 0;
            ev->source_faction = fid;
            ev->chain_length = (uint32_t)chain_length;
            ev->cond_kind = OM_COND_NONE;
            ev->cond_field = 0;
            ev->exclusion_tag = 0;
            ev->cond_value = 0.0;
        }
    }
}
