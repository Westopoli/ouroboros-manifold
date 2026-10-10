/* csrc/economy_density.c -- VG K-e stub: density field getter. E1b fills it. */
#include "ouroboros_sim.h"
#include "economy_internal.h"
#include <stddef.h>

double om_density_at(const om_world *w, double x, double y) {
    (void)x;
    (void)y;
    if (!w || !w->economy.density_present) return 0.0;
    return 0.0;
}

void om_density_init(om_world *w) { (void)w; }
void om_density_step(om_world *w, uint64_t tick) { (void)w; (void)tick; }
