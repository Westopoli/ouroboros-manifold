/* csrc/om_internal.h — private world layout shared by the C source files.
 * Parent-owned like ouroboros_sim.h. A build card that must add state to
 * om_world lists this file in allowed_files; a card that only reads it does
 * not. Never included by the tests; the public ABI is ouroboros_sim.h. */
#ifndef OM_INTERNAL_H
#define OM_INTERNAL_H

#include "ouroboros_sim.h"

#define OM_MAX_NEIGHBORS 32

typedef struct {
    om_tier  tier;
    double   military, economy, tension, population;
    double   econ_phase, tension_phase;
    double   prev_econ_osc, prev_tension_osc;
    int32_t  faction_id;
    uint32_t neighbors[OM_MAX_NEIGHBORS];
    uint32_t n_neighbors;
    om_drift_row last_drift;
} om_region;

struct om_world {
    uint32_t n_regions;
    uint64_t seed;
    uint64_t tick;
    int      trace_on;
    int      inject;
    om_region *regions;
    double   faction_mod[OM_MAX_FACTIONS][OM_F_COUNT];
    om_trace_row *trace;
    uint64_t trace_len, trace_cap;

    /* E-05 faction, ownership, typed edges, and RNG state */
    int          features[8];
    double       faction_budget[OM_MAX_FACTIONS];
    double       faction_tech[OM_MAX_FACTIONS];
    double       faction_confidence[OM_MAX_FACTIONS];
    om_archetype faction_archetype[OM_MAX_FACTIONS];
    om_stance    faction_stance[OM_MAX_FACTIONS][OM_MAX_FACTIONS];
    double       faction_tech_attack[OM_MAX_FACTIONS];
    double       faction_tech_defense[OM_MAX_FACTIONS];
    double       faction_tech_economy[OM_MAX_FACTIONS];
    int          faction_used[OM_MAX_FACTIONS];
    uint32_t     faction_n;
    int64_t     *region_held_since;
    om_edge_type region_edge[64][64];
    uint64_t     rng_state, rng_inc;
    double       rng_forced[4096];
    uint32_t     rng_forced_head, rng_forced_len;
};

#endif /* OM_INTERNAL_H */
