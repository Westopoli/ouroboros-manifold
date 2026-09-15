/* csrc/agent.c — E-05 faction agent decisions (build card 203).
 * Skeleton written by the parent so the fenced suite fails red on assertions,
 * not on a missing symbol, and so the build harness has a file to read; every
 * body below is a STUB the build card replaces. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>
#include <string.h>

uint32_t om_faction_candidates(const om_world *w, int32_t faction_id, om_candidate *out, uint32_t max) {
    /* STUB */
    (void)w; (void)faction_id; (void)out; (void)max;
    return 0;
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
