/* csrc/resolve.c — E-05 intent resolution: reinforce, attack, damage, conquest, colonize (build card 204).
 * Skeleton written by the parent so the fenced suite fails red on assertions,
 * not on a missing symbol, and so the build harness has a file to read; every
 * body below is a STUB the build card replaces. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>
#include <string.h>

uint32_t om_tick_attacks(const om_world *w, om_attack_result *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_reinforces(const om_world *w, om_reinforce *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_colonizations(const om_world *w, om_colonize_result *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_event_queue(const om_world *w, om_queued_event *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}
