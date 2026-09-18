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
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS || !w->faction_used[faction_id]) {
        return 0;
    }

    uint32_t count = 0;
    int seen[64] = {0}; // assuming max regions is less than 64

    for (uint32_t i = 0; i < w->n_regions; ++i) {
        if (om_region_owner(w, i) == faction_id) {
            for (uint32_t j = 0; j < w->n_regions; ++j) {
                om_edge_type edge_type;
                if (om_region_edge(w, i, j, &edge_type) && i != j) {
                    int32_t target_owner = om_region_owner(w, j);
                    if (target_owner == faction_id) continue;

                    // Check stance exclusion per R-034-06
                    om_stance stance_from = om_faction_stance(w, faction_id, target_owner);
                    om_stance stance_to = om_faction_stance(w, target_owner, faction_id);
                    if (stance_from == OM_STANCE_HOSTILE && stance_to == OM_STANCE_HOSTILE) {
                        // Both hostile - can attack
                    } else if (stance_from == OM_STANCE_NEUTRAL || stance_to == OM_STANCE_NEUTRAL ||
                               stance_from == OM_STANCE_COOPERATIVE || stance_to == OM_STANCE_COOPERATIVE) {
                        // One or both are neutral/cooperative - exclude
                        continue;
                    }

                    if (seen[j]) continue; // deduplicate
                    seen[j] = 1;

                    if (count >= max) break;

                    out[count].region_idx = j;
                    out[count].kind = (target_owner == -1) ? OM_CAND_COLONIZE : OM_CAND_ATTACK;
                    out[count].attractiveness = 0.5;
                    // Other fields are not set as per instruction, only those required for this card
                    count++;
                }
            }
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
