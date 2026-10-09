/* csrc/strongpoint.c -- VG K-e stub: strongpoint table getters. E1 later pieces fill them. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>

uint32_t om_strongpoint_count(const om_world *w) {
    return w ? w->economy.n_strongpoints : 0;
}

int om_strongpoint_get_at(const om_world *w, uint32_t i, om_strongpoint *out) {
    if (!w || !out || i >= w->economy.n_strongpoints) return 1;
    *out = w->economy.strongpoints[i];
    return 0;
}
