/* csrc/economy_lots.c -- VG K-e stub: lot table getters and the placement entry. E1d, E1e fill them. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>

uint32_t om_lot_count(const om_world *w) {
    return w ? w->economy.n_lots : 0;
}

int om_lot_get_at(const om_world *w, uint32_t i, om_lot *out) {
    if (!w || !out || i >= w->economy.n_lots) return 1;
    *out = w->economy.lots[i];
    return 0;
}

int om_economy_place(om_world *w, int32_t building, double x, double y) {
    (void)w;
    (void)building;
    (void)x;
    (void)y;
    return 0;
}
