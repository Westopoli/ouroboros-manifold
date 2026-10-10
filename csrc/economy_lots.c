/* csrc/economy_lots.c -- VG K-e stub: lot table getters and the placement entry. E1d, E1e fill them. */
#include "ouroboros_sim.h"
#include "economy_internal.h"
#include <stddef.h>

uint32_t om_lot_count(const om_world *w) {
    return w ? w->economy.n_lots : 0;
}

int om_lot_get_at(const om_world *w, uint32_t i, om_lot *out) {
    if (!w || !out || i >= w->economy.n_lots) return 1;
    *out = w->economy.lots[i];
    return 0;
}

void om_lots_init(om_world *w) { (void)w; }
void om_lots_step(om_world *w, uint64_t tick) { (void)w; (void)tick; }
void om_lots_on_area_hit(om_world *w, double x, double y, double radius) { (void)w; (void)x; (void)y; (void)radius; }
