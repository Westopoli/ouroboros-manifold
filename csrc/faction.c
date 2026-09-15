/* csrc/faction.c — E-05 faction state, ownership, typed edges, feature switches, forced RNG, budget accumulation (build card 202).
 * Skeleton written by the parent so the fenced suite fails red on assertions,
 * not on a missing symbol, and so the build harness has a file to read; every
 * body below is a STUB the build card replaces. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>
#include <string.h>

void om_world_set_feature(om_world *w, om_feature f, int on) {
    /* STUB */
    (void)w; (void)f; (void)on;
}

int om_world_feature(const om_world *w, om_feature f) {
    /* STUB */
    (void)w; (void)f;
    return 0;
}

int om_faction_set(om_world *w, int32_t faction_id, om_archetype archetype, double budget, double tech, double attack_confidence) {
    /* STUB */
    (void)w; (void)faction_id; (void)archetype; (void)budget; (void)tech; (void)attack_confidence;
    return 0;
}

void om_faction_set_stance(om_world *w, int32_t from, int32_t toward, om_stance s) {
    /* STUB */
    (void)w; (void)from; (void)toward; (void)s;
}

void om_faction_set_tech_multipliers(om_world *w, int32_t faction_id, double attack, double defense, double economy) {
    /* STUB */
    (void)w; (void)faction_id; (void)attack; (void)defense; (void)economy;
}

uint32_t om_faction_count(const om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

om_archetype om_faction_archetype(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

double om_faction_budget(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0.0;
}

double om_faction_confidence(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0.0;
}

double om_faction_tech(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0.0;
}

om_stance om_faction_stance(const om_world *w, int32_t from, int32_t toward) {
    /* STUB */
    (void)w; (void)from; (void)toward;
    return 0;
}

uint32_t om_faction_territory(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

void om_region_set_owner(om_world *w, uint32_t idx, int32_t faction_id, int64_t held_since_tick) {
    /* STUB */
    (void)w; (void)idx; (void)faction_id; (void)held_since_tick;
}

int32_t om_region_owner(const om_world *w, uint32_t idx) {
    /* STUB */
    (void)w; (void)idx;
    return 0;
}

int64_t om_region_held_since(const om_world *w, uint32_t idx) {
    /* STUB */
    (void)w; (void)idx;
    return 0;
}

void om_region_set_edge(om_world *w, uint32_t a, uint32_t b, om_edge_type t) {
    /* STUB */
    (void)w; (void)a; (void)b; (void)t;
}

int om_region_edge(const om_world *w, uint32_t a, uint32_t b, om_edge_type *out) {
    /* STUB */
    (void)w; (void)a; (void)b; (void)out;
    return 0;
}

void om_rng_force(om_world *w, const double *draws, uint32_t n) {
    /* STUB */
    (void)w; (void)draws; (void)n;
}

uint32_t om_rng_forced_remaining(const om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}
