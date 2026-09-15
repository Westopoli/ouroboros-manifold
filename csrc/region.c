/* csrc/region.c — E-02 region state and composites (build card 200). */
#include "ouroboros_sim.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define OM_MAX_NEIGHBORS 32
#define OM_MAX_FACTIONS 64

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
};

om_world *om_world_new(uint32_t n_regions, uint64_t seed) {
    if (n_regions == 0) return NULL;
    om_world *w = calloc(1, sizeof(om_world));
    if (!w) return NULL;
    w->n_regions = n_regions;
    w->seed = seed;
    w->tick = 0;
    w->trace_on = 0;
    w->inject = 0;
    w->regions = calloc(n_regions, sizeof(om_region));
    if (!w->regions) {
        free(w);
        return NULL;
    }
    w->trace = NULL;
    w->trace_len = 0;
    w->trace_cap = 0;
    return w;
}

void om_world_free(om_world *w) {
    if (!w) return;
    free(w->regions);
    free(w->trace);
    free(w);
}

void om_world_set_seed(om_world *w, uint64_t seed) {
    if (!w) return;
    w->seed = seed;
}

void om_world_generate(om_world *w) {
    /* Stub: no-op for E-02 isolation tests. */
    (void)w;
}

int om_region_set(om_world *w, uint32_t idx, om_tier tier,
                  double military, double economy, double tension, double population,
                  double econ_phase, double tension_phase, int32_t faction_id) {
    if (!w || idx >= w->n_regions) return -1;
    om_region *r = &w->regions[idx];
    r->tier = tier;
    r->military = military;
    r->economy = economy;
    r->tension = tension;
    r->population = population;
    r->econ_phase = econ_phase;
    r->tension_phase = tension_phase;
    r->prev_econ_osc = 0.0;
    r->prev_tension_osc = 0.0;
    r->faction_id = faction_id;
    r->n_neighbors = 0;
    return 0;
}

void om_region_set_adjacency(om_world *w, uint32_t idx,
                             const uint32_t *neighbor_idx, uint32_t n_neighbors) {
    if (!w || idx >= w->n_regions) return;
    om_region *r = &w->regions[idx];
    uint32_t count = n_neighbors < OM_MAX_NEIGHBORS ? n_neighbors : OM_MAX_NEIGHBORS;
    if (neighbor_idx) {
        memcpy(r->neighbors, neighbor_idx, count * sizeof(uint32_t));
    }
    r->n_neighbors = count;
}

void om_region_set_faction_modifier(om_world *w, int32_t faction_id,
                                    om_field field, double value) {
    if (!w) return;
    if (faction_id < 0 || faction_id >= OM_MAX_FACTIONS) return;
    if (field >= OM_F_COUNT) return;
    w->faction_mod[faction_id][field] = value;
}

uint32_t om_region_count(const om_world *w) {
    if (!w) return 0;
    return w->n_regions;
}



double om_region_field(const om_world *w, uint32_t idx, om_field f) {
    if (!w || idx >= w->n_regions) return 0.0;
    if (f >= OM_F_COUNT) return 0.0;
    const om_region *r = &w->regions[idx];
    if (r->tier == OM_TIER_EMPTY) return 0.0;
    switch (f) {
        case OM_F_MILITARY: return r->military;
        case OM_F_ECONOMY:  return r->economy;
        case OM_F_TENSION:  return r->tension;
        case OM_F_POPULATION:return r->population;
        default: return 0.0;
    }
}

double om_region_composite(const om_world *w, uint32_t idx, om_composite c) {
    if (!w || idx >= w->n_regions) return 0.0;
    if (c >= OM_C_COUNT) return 0.0;
    const om_region *r = &w->regions[idx];
    if (r->tier == OM_TIER_EMPTY) return 0.0;
    double chosen = 0.0;
    if (c == OM_C_STABILITY) {
        chosen = r->military * 0.40 + (100.0 - r->tension) * 0.35 + r->population * 0.25;
        if (r->military < 10.0) chosen *= 0.70;
        if (r->population < 20.0) chosen *= 0.75;
    } else if (c == OM_C_CAPACITY) {
        chosen = r->economy * 0.50 + r->population * 0.35 + r->military * 0.15;
        if (r->economy < 20.0) chosen *= 0.65;
        if (r->population < 20.0) chosen *= 0.70;
    }
    return round(chosen * 100.0) / 100.0;
}

om_tier om_region_tier(const om_world *w, uint32_t idx) {
    if (!w || idx >= w->n_regions) return OM_TIER_EMPTY;
    return w->regions[idx].tier;
}



uint32_t om_checksum_cadence(void) {
    return 10;
}






uint32_t om_abi_version(void) {
    return 1;
}

/* Card-201 (sim.c) functions as WEAK stubs: lets the E-02 fenced suite load the
 * library with only region.c present (card 200). When sim.c lands (card 201),
 * its strong definitions override these with no multiple-definition link error. */
__attribute__((weak)) uint64_t om_world_step(om_world *w) { if (!w) return 0; w->tick++; return w->tick; }
__attribute__((weak)) uint64_t om_world_run(om_world *w, uint64_t n) { (void)n; return w ? w->tick : 0; }
__attribute__((weak)) int om_region_drift(const om_world *w, uint32_t idx, om_drift_row *out) { (void)w;(void)idx;(void)out; return -1; }
__attribute__((weak)) uint64_t om_world_checksum(const om_world *w) { (void)w; return 0; }
__attribute__((weak)) double om_sin(double x) { return sin(x); }
__attribute__((weak)) void om_trace_enable(om_world *w, int on) { if (w) w->trace_on = on ? 1 : 0; }
__attribute__((weak)) uint64_t om_trace_len(const om_world *w) { return w ? w->trace_len : 0; }
__attribute__((weak)) uint64_t om_trace_read(const om_world *w, uint64_t s, uint64_t c, om_trace_row *o) { (void)w;(void)s;(void)c;(void)o; return 0; }
#ifdef OM_DEBUG_INJECT
__attribute__((weak)) void om_debug_inject(om_world *w, om_bug bug) { (void)w;(void)bug; }
#endif
