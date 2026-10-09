/* csrc/economy_doctrine.c -- VG K-e stub: doctrine and wave-log getters. E1 later pieces fill them. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>

int om_doctrine_get(const om_world *w) {
    if (!w || !w->economy.doctrine_chosen) return OM_DOCTRINE_BALANCED;
    return w->economy.doctrine;
}

uint32_t om_wave_get_since(const om_world *w, uint32_t tick, om_wave *out, uint32_t cap) {
    uint32_t matched = 0;
    if (!w) return 0;
    for (uint32_t i = 0; i < w->economy.n_waves; i++) {
        if (w->economy.waves[i].tick < tick) continue;
        if (out && matched < cap) out[matched] = w->economy.waves[i];
        matched++;
    }
    return matched;
}
