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

static void sp_mirror(om_world *w, uint32_t i) {
    om_strongpoint *sp = &w->economy.strongpoints[i];
    int32_t owner = om_structure_get_owner(w, sp->id);
    sp->owner = owner;
    if (sp->state != 2) sp->state = owner >= 0 ? 1 : 0;
}

/* liberty 2026-10-10 (E1h ruling): id = structure slot; best slopes are the longest, ties to the lowest index; each structure moves to its slope midpoint */
void om_strongpoint_init(om_world *w) {
    if (!w) return;
    w->economy.n_strongpoints = 0;
    uint32_t slopes = om_terrain_slope_count(w);
    uint32_t n = om_structure_count(w);
    if (n > slopes) n = slopes;
    if (n > OM_STRONGPOINT_CAP) n = OM_STRONGPOINT_CAP;
    uint32_t prev = 0;
    double prev_len = 0.0;
    for (uint32_t i = 0; i < n; i++) {
        int best = -1;
        om_slope bs = {0};
        for (uint32_t k = 0; k < slopes; k++) {
            om_slope sl;
            if (om_terrain_slope_get(w, k, &sl)) continue;
            if (i > 0 && !(sl.length < prev_len || (sl.length == prev_len && k > prev))) continue;
            if (best < 0 || sl.length > bs.length) { best = (int)k; bs = sl; }
        }
        if (best < 0) break;
        prev = (uint32_t)best;
        prev_len = bs.length;
        om_structure_set_position(w, i, bs.mx, bs.my);
        om_strongpoint *sp = &w->economy.strongpoints[i];
        sp->id = i;
        sp->x = bs.mx;
        sp->y = bs.my;
        sp->state = om_structure_is_destroyed(w, i) ? 2 : 0;
        w->economy.n_strongpoints = i + 1;
        sp_mirror(w, i);
    }
}

void om_strongpoint_step(om_world *w, uint64_t tick) {
    (void)tick;
    for (uint32_t i = 0; i < w->economy.n_strongpoints; i++) sp_mirror(w, i);
}

void om_strongpoint_on_structure_owner(om_world *w, uint32_t structure, int32_t old_owner, int32_t new_owner) {
    (void)old_owner;
    (void)new_owner;
    if (structure < w->economy.n_strongpoints) sp_mirror(w, structure);
}

void om_strongpoint_on_structure_damage(om_world *w, uint32_t structure, double hp_after) {
    if (structure < w->economy.n_strongpoints && hp_after <= 0.0) w->economy.strongpoints[structure].state = 2;
}
