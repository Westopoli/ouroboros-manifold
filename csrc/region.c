/* csrc/region.c — E-02 region state and composites (build card 200).
 *
 * SKELETON: stub bodies below compile and link so the fenced test suite can run
 * (and fail red) before implementation. Agora's build loop rewrites this whole
 * file to make tests/csim/test_E02_S012_composites.py pass, per the equations in
 * projects/ouroboros/rules/E-02.md (S-012) and the contract in ouroboros_sim.h.
 * The tick, drift, trace, checksum, and om_sin functions live in csrc/sim.c
 * (card 201); leaving them undefined here is fine — the shared library links.
 */
#include "ouroboros_sim.h"
#include <stdlib.h>
#include <string.h>

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

/* Defined here (card 200); csrc/sim.c reads this layout via an extern in card 201. */
struct om_world {
    uint32_t n_regions;
    uint64_t seed;
    uint64_t tick;
    int      trace_on;
    int      inject;                 /* om_bug flag, debug build */
    om_region *regions;
    double   faction_mod[OM_MAX_FACTIONS][OM_F_COUNT];
    om_trace_row *trace;
    uint64_t trace_len, trace_cap;
};

om_world *om_world_new(uint32_t n_regions, uint64_t seed) {
    (void)n_regions; (void)seed; return NULL;   /* STUB */
}
void om_world_free(om_world *w) { (void)w; }     /* STUB */
void om_world_set_seed(om_world *w, uint64_t seed) { (void)w; (void)seed; }  /* STUB */

int om_region_set(om_world *w, uint32_t idx, om_tier tier,
                  double military, double economy, double tension, double population,
                  double econ_phase, double tension_phase, int32_t faction_id) {
    (void)w; (void)idx; (void)tier; (void)military; (void)economy; (void)tension;
    (void)population; (void)econ_phase; (void)tension_phase; (void)faction_id;
    return -1;                                    /* STUB */
}
void om_region_set_adjacency(om_world *w, uint32_t idx,
                             const uint32_t *neighbor_idx, uint32_t n_neighbors) {
    (void)w; (void)idx; (void)neighbor_idx; (void)n_neighbors;   /* STUB */
}
void om_region_set_faction_modifier(om_world *w, int32_t faction_id,
                                    om_field field, double value) {
    (void)w; (void)faction_id; (void)field; (void)value;        /* STUB */
}
uint32_t om_region_count(const om_world *w) { (void)w; return 0; }  /* STUB */

double om_region_field(const om_world *w, uint32_t idx, om_field f) {
    (void)w; (void)idx; (void)f; return 0.0;      /* STUB */
}
double om_region_composite(const om_world *w, uint32_t idx, om_composite c) {
    (void)w; (void)idx; (void)c; return 0.0;      /* STUB */
}
om_tier om_region_tier(const om_world *w, uint32_t idx) {
    (void)w; (void)idx; return OM_TIER_EMPTY;      /* STUB */
}

uint32_t om_abi_version(void) { return 1; }
uint32_t om_checksum_cadence(void) { return 10; }
