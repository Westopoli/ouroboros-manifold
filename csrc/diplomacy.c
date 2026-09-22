/* csrc/diplomacy.c — E-06 diplomacy and technology (tick wiring only; the
 * epic's own stance and tech-growth math lands with card B5).
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

void om_step_diplomacy(om_world *w) {
    /* STUB */
    (void)w;
}

void om_step_technology(om_world *w) {
    /* STUB */
    (void)w;
}

/* ---- generated stubs from signatures.toml ---- */
double om_archetype_betrayal_weight(om_archetype archetype) {
    /* STUB */
    (void)archetype;
    return 0.0;
}

double om_archetype_peace_disposition(om_archetype archetype) {
    /* STUB */
    (void)archetype;
    return 0.0;
}

int32_t om_breakaway_create(om_world *w, int32_t parent, uint32_t region_idx) {
    /* STUB */
    (void)w; (void)parent; (void)region_idx;
    return 0;
}

uint32_t om_chronicle_distill_candidates(const om_world *w, uint32_t *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

void om_diplomacy_init(om_world *w) {
    /* STUB */
    (void)w;
}

void om_diplomacy_step(om_world *w) {
    /* STUB */
    (void)w;
}

double om_faction_betrayal_chance(const om_world *w, int32_t betrayer, int32_t partner) {
    /* STUB */
    (void)w; (void)betrayer; (void)partner;
    return 0.0;
}

double om_faction_betrayal_opportunity(const om_world *w, int32_t betrayer, int32_t partner) {
    /* STUB */
    (void)w; (void)betrayer; (void)partner;
    return 0.0;
}

uint64_t om_faction_cooperative_since(const om_world *w, int32_t p0, int32_t p1) {
    /* STUB */
    (void)w; (void)p0; (void)p1;
    return 0;
}

void om_faction_create_breakaway(om_world *w, int32_t parent, uint32_t p1) {
    /* STUB */
    (void)w; (void)parent; (void)p1;
}

int64_t om_faction_last_knowledge_lost(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

uint32_t om_faction_next_mission_unit_tier(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

void om_faction_set_last_knowledge_lost(om_world *w, int32_t faction_id, int64_t tick) {
    /* STUB */
    (void)w; (void)faction_id; (void)tick;
}

void om_faction_set_stance_counter(om_world *w, int32_t p0, int32_t p1, uint32_t counter) {
    /* STUB */
    (void)w; (void)p0; (void)p1; (void)counter;
}

uint32_t om_faction_stance_counter(const om_world *w, int32_t p0, int32_t faction) {
    /* STUB */
    (void)w; (void)p0; (void)faction;
    return 0;
}

double om_faction_tech_attack(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0.0;
}

double om_faction_tech_defense(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0.0;
}

double om_faction_tech_economy(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0.0;
}

void om_faction_tech_multipliers(const om_world *w, int32_t faction_id, double *attack, double *defense, double *economy) {
    /* STUB */
    (void)w; (void)faction_id; (void)attack; (void)defense; (void)economy;
}

uint32_t om_faction_tech_tier(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

int om_faction_tier_transition_candidate(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

uint32_t om_faction_unit_tier(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

uint32_t om_mission_start(om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

uint32_t om_mission_unit_tier(const om_world *w, uint32_t mission_id) {
    /* STUB */
    (void)w; (void)mission_id;
    return 0;
}

void om_tech_step(om_world *w) {
    /* STUB */
    (void)w;
}

uint32_t om_tech_tier(double tech) {
    /* STUB */
    (void)tech;
    return 0;
}

int om_tier_transition_candidate_exists(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}
/* ---- end generated stubs ---- */
