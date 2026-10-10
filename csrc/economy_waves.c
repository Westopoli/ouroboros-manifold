/* csrc/economy_waves.c -- VG K-e2: wave log entries (empty bodies). E1d fills them. */
#include "economy_internal.h"

void om_waves_init(om_world *w) { (void)w; }
void om_waves_step(om_world *w, uint64_t tick) { (void)w; (void)tick; }
void om_waves_log(om_world *w, uint32_t tick, int32_t kind, double x, double y) { (void)w; (void)tick; (void)kind; (void)x; (void)y; }
void om_waves_on_structure_owner(om_world *w, uint32_t structure, int32_t old_owner, int32_t new_owner) { (void)w; (void)structure; (void)old_owner; (void)new_owner; }
void om_waves_on_mission_end(om_world *w) { (void)w; }
