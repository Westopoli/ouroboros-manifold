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

uint32_t om_faction_candidates(const om_world *w, int32_t faction_id, om_candidate *out, uint32_t max) {
    if (!w || !out || max == 0 || faction_id < 0 || faction_id >= OM_MAX_FACTIONS) {
        return 0;
    }

    om_archetype archetype = om_faction_archetype(w, faction_id);
    
    double w_weakness = 0.40, w_value = 0.30, w_position = 0.30;
    int can_colonize = 1;
    int tension_primary = 0;
    
    switch (archetype) {
        case OM_ARCH_CONQUEROR:
            w_weakness = 0.40; w_value = 0.25; w_position = 0.35; tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_WARLORD:
            w_weakness = 0.20; w_value = 0.35; w_position = 0.45; tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_FORTIFIER:
            w_weakness = 0.25; w_value = 0.20; w_position = 0.55; tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_OPPORTUNIST:
            w_weakness = 0.35; w_value = 0.30; w_position = 0.35; tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_SCHISM:
            w_weakness = 0.20; w_value = 0.30; w_position = 0.50; tension_primary = 1; can_colonize = 0;
            break;
        case OM_ARCH_PLAYER:
            w_weakness = 0.60; w_value = 0.25; w_position = 0.15; tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_BREAKAWAY:
            w_weakness = 0.45; w_value = 0.30; w_position = 0.25; tension_primary = 0; can_colonize = 1;
            break;
        default: // OM_ARCH_DEFAULT or fallback
            w_weakness = 0.40; w_value = 0.30; w_position = 0.30; tension_primary = 0; can_colonize = 1;
            break;
    }

    uint32_t count = 0;
    int seen[64] = {0};
    
    for (uint32_t i = 0; i < w->n_regions && count < max; ++i) {
        if (w->regions[i].faction_id != faction_id) continue;
        
        for (uint32_t j = 0; j < w->n_regions && count < max; ++j) {
            om_edge_type edge_type;
            if (i == j || !om_region_edge(w, i, j, &edge_type) || seen[j]) continue;

            int32_t target_owner = w->regions[j].faction_id;
            if (target_owner == faction_id) continue;
            
            om_candidate_kind kind = OM_CAND_ATTACK;
            if (target_owner == -1) {
                if (!can_colonize) continue;
                kind = OM_CAND_COLONIZE;
            }

            double factor_1 = 0.0;
            if (tension_primary) {
                factor_1 = w->regions[j].tension / 100.0;
            } else {
                factor_1 = (100.0 - w->regions[j].military) / 100.0;
            }

            double current_value = 0.0;
            if (target_owner == -1) {
                // Colonize case
                current_value = (w->regions[j].economy * 0.60 + w->regions[j].population * 0.40) / 100.0 * 2.0;
            } else {
                // Attack case
                current_value = (w->regions[j].economy * 0.60 + w->regions[j].population * 0.40) / 100.0 * 2.0;
                if (current_value < 0.05) continue;
            }

            double strategic_position = 0.0;
            uint32_t neighbor_count = 0;

            for (uint32_t k = 0; k < w->n_regions; ++k) {
                om_edge_type edge_type_k;
                if (j == k || !om_region_edge(w, j, k, &edge_type_k)) continue;
                
                int32_t neighbor_owner = w->regions[k].faction_id;
                if (neighbor_owner == faction_id) continue;

                double score = 0.0;
                if (neighbor_owner == -1) {
                    score = 0.15;
                } else {
                    score = (w->regions[k].economy * 0.60 + w->regions[k].population * 0.40) / 100.0;
                }
                
                strategic_position += score;
                neighbor_count++;
            }

            if (neighbor_count > 0) {
                strategic_position /= neighbor_count;
            } else {
                strategic_position = 0.0;
            }

            double attractiveness = w_weakness * factor_1 + w_value * current_value + w_position * strategic_position;

            if (archetype == OM_ARCH_OPPORTUNIST) {
                double damage_boost = om_region_damage_history(w, j) / 100.0 * 1.5;
                attractiveness *= (1.0 + damage_boost);
            }

            out[count].region_idx = j;
            out[count].kind = kind;
            out[count].weakness = factor_1;
            out[count].value = current_value;
            out[count].position = strategic_position;
            out[count].attractiveness = attractiveness;
            out[count].entrenchment = 0.0;
            out[count].net = 0.0;
            out[count].viable = 0;
            out[count]._pad = 0;

            seen[j] = 1;
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
