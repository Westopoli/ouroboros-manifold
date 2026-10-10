/* csrc/strongpoint.c -- VG K-e stub: strongpoint table getters. E1 later pieces fill them. */
#include "ouroboros_sim.h"
#include "economy_internal.h"
#include <stddef.h>

uint32_t om_strongpoint_count(const om_world *w) {
    return w ? w->economy.n_strongpoints : 0;
}

int om_strongpoint_get_at(const om_world *w, uint32_t i, om_strongpoint *out) {
    if (!w || !out || i >= w->economy.n_strongpoints) return 1;
    *out = w->economy.strongpoints[i];
    return 0;
}

void om_strongpoint_init(om_world *w) { (void)w; }
void om_strongpoint_step(om_world *w, uint64_t tick) { (void)w; (void)tick; }
void om_strongpoint_on_structure_owner(om_world *w, uint32_t structure, int32_t old_owner, int32_t new_owner) { (void)w; (void)structure; (void)old_owner; (void)new_owner; }
void om_strongpoint_on_structure_damage(om_world *w, uint32_t structure, double hp_after) { (void)w; (void)structure; (void)hp_after; }
