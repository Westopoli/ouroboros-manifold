/* csrc/economy_density.c -- VG K-e stub: density field getter. E1b fills it. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>

double om_density_at(const om_world *w, double x, double y) {
    (void)x;
    (void)y;
    if (!w || !w->economy.density_present) return 0.0;
    return 0.0;
}
