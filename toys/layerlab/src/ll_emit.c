/* ll_emit.c -- going dark (E-01 S-163, ABI 3). Stub: no effect until the emit builder replaces it. Call sites are
 * fixed in ll_vision.c (ll_emit_factor in can_see) and ll_sim.c (ll_emit_update each tick). */
#include "ll_internal.h"

const char *ll_emit_validate(const ll_scenario *sc) { (void)sc; return 0; }

void ll_emit_update(ll_state *s) { (void)s; }

double ll_emit_factor(const ll_state *s, int o, int t) { (void)s; (void)o; (void)t; return 1.0; }
