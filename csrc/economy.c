/* csrc/economy.c -- VG K-e2: economy entry points, fan-out only. */
#include "economy_internal.h"

void om_economy_init(om_world *w) {
    om_density_init(w);
    om_lots_init(w);
    om_waves_init(w);
    om_strongpoint_init(w);
}

void om_economy_step(om_world *w, uint64_t tick) {
    om_density_step(w, tick);
    om_lots_step(w, tick);
    om_waves_step(w, tick);
    om_strongpoint_step(w, tick);
}

void om_economy_on_structure_owner(om_world *w, uint32_t structure, int32_t old_owner, int32_t new_owner) {
    om_waves_on_structure_owner(w, structure, old_owner, new_owner);
    om_strongpoint_on_structure_owner(w, structure, old_owner, new_owner);
}

void om_economy_on_structure_damage(om_world *w, uint32_t structure, double hp_after) {
    om_strongpoint_on_structure_damage(w, structure, hp_after);
}

void om_economy_on_area_hit(om_world *w, double x, double y, double radius) {
    om_lots_on_area_hit(w, x, y, radius);
}

void om_economy_on_mission_end(om_world *w) {
    om_waves_on_mission_end(w);
}
