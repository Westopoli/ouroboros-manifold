/* ll_emit.c -- going dark (E-01 S-163, SPEC 15.2, ABI 3). Call sites: ll_emit_factor in can_see (ll_vision.c),
 * ll_emit_update each tick (ll_sim.c). */
#include "ll_internal.h"

const char *ll_emit_validate(const ll_scenario *sc) {
    const ll_rules *r = &sc->rules;
    if (!r->emit_on) return 0;
    for (int k = 0; k < 2; k++)
        if (!ll_finite(r->emit_see_mult[k]) || r->emit_see_mult[k] < 0.0 ||
            !ll_finite(r->emit_seen_mult[k]) || r->emit_seen_mult[k] < 0.0)
            return "rules: emit_see_mult and emit_seen_mult entries must be finite and >= 0";
    int n = sc->n_spawns < LL_MAX_UNITS ? sc->n_spawns : LL_MAX_UNITS;   /* n_spawns itself is checked by the caller */
    for (int i = 0; i < n; i++) {
        const ll_spawn *p = &sc->spawns[i];
        if (p->emit != 0 && p->emit != 1) return "spawn: emit must be 0 or 1";
        if (p->emit_switch_to != 0 && p->emit_switch_to != 1) return "spawn: emit_switch_to must be 0 or 1";
        if (p->emit_switch_tick < -1) return "spawn: emit_switch_tick must be >= -1";
    }
    return 0;
}

void ll_emit_update(ll_state *s) {
    if (!s->rules->emit_on) return;
    for (int i = 0; i < s->n; i++) {
        const ll_spawn *p = &s->sc->spawns[i];
        if (s->u[i].alive && p->emit_switch_tick >= 0 && s->tick == p->emit_switch_tick)
            s->u[i].emit = p->emit_switch_to;
    }
}

double ll_emit_factor(const ll_state *s, int o, int t) {
    if (!s->rules->emit_on || s->u[o].layer == s->u[t].layer) return 1.0;
    return s->rules->emit_see_mult[s->u[o].emit] * s->rules->emit_seen_mult[s->u[t].emit];
}
