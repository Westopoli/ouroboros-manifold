/* csrc/sim.c — E-02 tick loop, drift, oscillator, clamps, trace, checksum (build card 201).
 * Skeleton written by the parent so the fenced suite fails red (not on a missing
 * symbol) and so the build harness has a file to read; every body below is a
 * STUB that card 201 replaces. See docs/northstar/e2e/E-02.md and algorithms.md
 * ALG-01..ALG-10. */
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
#include <string.h>

double om_sin(double x) {
    /* STUB */
    (void)x;
    return 0.0;
}

uint64_t om_world_step(om_world *w) {
    /* STUB */
    if (!w) return 0;
    return w->tick;
}

uint64_t om_world_run(om_world *w, uint64_t n_ticks) {
    /* STUB */
    (void)n_ticks;
    if (!w) return 0;
    return w->tick;
}

int om_region_drift(const om_world *w, uint32_t idx, om_drift_row *out) {
    /* STUB */
    (void)w; (void)idx;
    if (out) memset(out, 0, sizeof(*out));
    return -1;
}

uint64_t om_world_checksum(const om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

void om_trace_enable(om_world *w, int on) {
    /* STUB */
    (void)w; (void)on;
}

uint64_t om_trace_len(const om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

uint64_t om_trace_read(const om_world *w, uint64_t start, uint64_t count, om_trace_row *out) {
    /* STUB */
    (void)w; (void)start; (void)count; (void)out;
    return 0;
}

#ifdef OM_DEBUG_INJECT
void om_debug_inject(om_world *w, om_bug bug) {
    /* STUB */
    (void)w; (void)bug;
}
#endif
