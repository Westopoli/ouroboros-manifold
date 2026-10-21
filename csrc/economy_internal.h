/* csrc/economy_internal.h -- VG K-e2 (VG-CONTRACT-E2): internal economy entry points, never in ouroboros_sim.h.
 * Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md rev 8, "Lane E1 part a2"; docs/architecture.md
 * "Visible-game economy entries". Fan-out order is the order listed in economy.c. */
#ifndef OM_ECONOMY_INTERNAL_H
#define OM_ECONOMY_INTERNAL_H
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stdint.h>

/* economy.c: fan-out only. */
void om_economy_init(om_world *w);
void om_economy_step(om_world *w, uint64_t tick);
void om_economy_on_structure_owner(om_world *w, uint32_t structure, int32_t old_owner, int32_t new_owner);
void om_economy_on_structure_damage(om_world *w, uint32_t structure, double hp_after);
void om_economy_on_area_hit(om_world *w, double x, double y, double radius);
void om_economy_on_mission_end(om_world *w);

void om_structure_refound(om_world *w, uint32_t structure, int32_t owner); /* tactical_support.c */

/* economy_density.c (E1b) */
void om_density_init(om_world *w);
void om_density_step(om_world *w, uint64_t tick);
void om_density_rebuild_inputs(om_world *w); /* K-e5: no-op stub, E1q-field fills it; see the K-e5 paragraph of docs/architecture.md */

/* economy_lots.c (E1c; E1d fills om_lots_on_area_hit) */
void om_lots_init(om_world *w);
void om_lots_step(om_world *w, uint64_t tick);
void om_lots_on_area_hit(om_world *w, double x, double y, double radius);
void om_lots_remove_row(om_world *w, uint32_t row); /* E1r: drop one lot row, shift the table, rebuild lot_at; See also: economy_place.c */

/* economy_waves.c (E1d) */
void om_waves_init(om_world *w);
void om_waves_step(om_world *w, uint64_t tick);
void om_waves_log(om_world *w, uint32_t tick, int32_t kind, double x, double y);
void om_waves_on_structure_owner(om_world *w, uint32_t structure, int32_t old_owner, int32_t new_owner);
void om_waves_on_mission_end(om_world *w);

/* strongpoint.c (E1h) */
void om_strongpoint_init(om_world *w);
void om_strongpoint_step(om_world *w, uint64_t tick);
void om_strongpoint_on_structure_owner(om_world *w, uint32_t structure, int32_t old_owner, int32_t new_owner);
void om_strongpoint_on_structure_damage(om_world *w, uint32_t structure, double hp_after);
#endif
