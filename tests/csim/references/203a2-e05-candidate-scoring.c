/* csrc/agent.c — E-05 faction agent decisions (build card 203).
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
#include <stddef.h>
#include <string.h>

static void om_faction_arch_weights(om_archetype a, double *weakness, double *value, double *position,
                                    int *tension_primary, int *can_colonize, double *boost) {
    switch (a) {
        case OM_ARCH_CONQUEROR:   *weakness = 0.40; *value = 0.25; *position = 0.35; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        case OM_ARCH_FORTIFIER:   *weakness = 0.25; *value = 0.20; *position = 0.55; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        case OM_ARCH_OPPORTUNIST: *weakness = 0.35; *value = 0.30; *position = 0.35; *tension_primary = 0; *can_colonize = 1; *boost = 1.5; break;
        case OM_ARCH_WARLORD:     *weakness = 0.20; *value = 0.35; *position = 0.45; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        case OM_ARCH_SCHISM:      *weakness = 0.20; *value = 0.30; *position = 0.50; *tension_primary = 1; *can_colonize = 0; *boost = 0.0; break;
        case OM_ARCH_PLAYER:      *weakness = 0.60; *value = 0.25; *position = 0.15; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        case OM_ARCH_BREAKAWAY:   *weakness = 0.45; *value = 0.30; *position = 0.25; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        default:                 *weakness = 0.40; *value = 0.30; *position = 0.30; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
    }
}

static double om_current_value(const om_region *r) {
    return ((r->economy * 0.60 + r->population * 0.40) / 100.0) * 2.0;
}

static double om_strategic_position(const om_world *w, uint32_t target_idx, int32_t faction_id) {
    double sum = 0.0;
    uint32_t n = 0;
    for (uint32_t k = 0; k < w->n_regions; k++) {
        if (k == target_idx)
            continue;
        om_edge_type et;
        if (!om_region_edge(w, target_idx, k, &et))
            continue;
        if (w->regions[k].faction_id == faction_id)
            continue;
        if (w->regions[k].faction_id < 0) {
            sum += 0.15; /* EXPANSION_POTENTIAL */
        } else {
            sum += (w->regions[k].economy * 0.60 + w->regions[k].population * 0.40) / 100.0;
        }
        n++;
    }
    return n > 0 ? sum / (double)n : 0.0;
}

uint32_t om_faction_candidates(const om_world *w, int32_t faction_id, om_candidate *out, uint32_t max) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS || !w->faction_used[faction_id])
        return 0;

    double aw_weakness, aw_value, aw_position, aw_boost;
    int aw_tension_primary, aw_can_colonize;
    om_faction_arch_weights(w->faction_archetype[faction_id], &aw_weakness, &aw_value, &aw_position,
                            &aw_tension_primary, &aw_can_colonize, &aw_boost);

    uint32_t count = 0;
    unsigned char seen[64];
    memset(seen, 0, sizeof(seen));

    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != faction_id)
            continue;

        for (uint32_t j = 0; j < w->n_regions; j++) {
            if (j == i)
                continue;
            om_edge_type et;
            if (!om_region_edge(w, i, j, &et))
                continue;
            if (w->regions[j].faction_id == faction_id)
                continue;
            if (j < 64 && seen[j])
                continue;

            int32_t owner = w->regions[j].faction_id;
            uint32_t kind;
            if (owner < 0) {
                if (!aw_can_colonize)
                    continue; /* schism never colonizes (ALG-11) */
                kind = OM_CAND_COLONIZE;
            } else {
                om_stance s_out = w->faction_stance[faction_id][owner];
                om_stance s_in = w->faction_stance[owner][faction_id];
                if (s_out != OM_STANCE_HOSTILE && s_in != OM_STANCE_HOSTILE)
                    continue; /* R-034-06 */
                kind = OM_CAND_ATTACK;
            }

            const om_region *tgt = &w->regions[j];
            double value = (owner < 0) ? 0.0 : om_current_value(tgt);
            if (kind == OM_CAND_ATTACK && value < 0.05)
                continue; /* MIN_ATTACK_VALUE, R-034-04 */

            if (j < 64)
                seen[j] = 1;
            if (count >= max)
                continue;

            double factor1 = aw_tension_primary ? (tgt->tension / 100.0) : (1.0 - tgt->military / 100.0);
            double position = om_strategic_position(w, j, faction_id);
            double attractiveness = aw_weakness * factor1 + aw_value * value + aw_position * position;
            if (aw_boost > 0.0) {
                double dmg = om_region_damage_history(w, j);
                attractiveness *= 1.0 + (dmg / 100.0) * aw_boost;
            }

            out[count].region_idx = j;
            out[count].kind = kind;
            out[count].weakness = factor1;
            out[count].value = value;
            out[count].position = position;
            out[count].attractiveness = attractiveness;
            out[count].entrenchment = 0.0;
            out[count].net = 0.0;
            out[count].viable = 0;
            out[count]._pad = 0;
            count++;
        }
    }
    return count;
}

uint32_t om_tick_decisions(const om_world *w, om_decision *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_pending_telegraphs(const om_world *w, om_telegraph *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

void om_step_decisions(om_world *w) {
    /* STUB */
    (void)w;
}
