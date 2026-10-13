/* csrc/economy_waves.c -- VG lane E1d: wave log (kinds 3 capture, 4 battle end; 0..2 wait for E2) and the rubble rebuild. */
#include "economy_internal.h"
#include <string.h>

#define WAVE_CAPTURE 3
#define WAVE_BATTLE_END 4
#define WAVE_FALLBACK_CENTRE_WU 12000.0 /* no terrain: the old canvas-centre constant (24000 wu canvas / 2) */
#define REBUILD_TICKS 200 /* spec rev 8 E1d ruling: a hit lot waits 10 s (200 ticks) before it rises again */

void om_waves_init(om_world *w) { w->economy.n_waves = 0; }

void om_waves_step(om_world *w, uint64_t tick) {
    om_economy_state *e = &w->economy;
    uint32_t i;
    for (i = 0; i < e->n_lots; i++)
        if (e->lots[i].stage == 0 && e->lot_hit_tick[i] != 0 && tick - e->lot_hit_tick[i] >= REBUILD_TICKS) {
            e->lots[i].stage = 1;
            e->lot_hit_tick[i] = 0;
        }
}

void om_waves_log(om_world *w, uint32_t tick, int32_t kind, double x, double y) {
    om_economy_state *e = &w->economy;
    if (e->n_waves == OM_WAVE_LOG_CAP) {
        memmove(&e->waves[0], &e->waves[1], (OM_WAVE_LOG_CAP - 1) * sizeof e->waves[0]);
        e->n_waves--;
    }
    e->waves[e->n_waves].tick = tick;
    e->waves[e->n_waves].kind = kind;
    e->waves[e->n_waves].x = x;
    e->waves[e->n_waves].y = y;
    e->n_waves++;
}

void om_waves_on_structure_owner(om_world *w, uint32_t structure, int32_t old_owner, int32_t new_owner) {
    om_vec2 p;
    (void)old_owner; (void)new_owner;
    om_structure_get_position(w, structure, &p);
    om_waves_log(w, (uint32_t)om_tactical_tick(w), WAVE_CAPTURE, p.x, p.y);
}

void om_waves_on_mission_end(om_world *w) {
    /* liberty 2026-10-10: the spec gives no place for a battle-end wave; it is logged at the canvas centre, half the terrain map. */
    uint32_t cw = 0, ch = 0;
    double cx = WAVE_FALLBACK_CENTRE_WU, cy = WAVE_FALLBACK_CENTRE_WU;
    if (om_terrain_cells(w, &cw, &ch) != 0) {
        cx = cw * OM_TERRAIN_CELL_WU / 2.0;
        cy = ch * OM_TERRAIN_CELL_WU / 2.0;
    }
    om_waves_log(w, (uint32_t)om_tactical_tick(w), WAVE_BATTLE_END, cx, cy);
}
