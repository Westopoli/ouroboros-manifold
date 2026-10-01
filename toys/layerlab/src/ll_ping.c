/* ll_ping.c -- targeted ping (E-01 S-162, ABI 3). Stub: no effect until the ping builder replaces it. Call sites are
 * fixed in ll_vision.c (ll_ping_reveals in the side visibility) and ll_sim.c (ll_ping_update each tick). */
#include "ll_internal.h"

const char *ll_ping_validate(const ll_scenario *sc) { (void)sc; return 0; }

void ll_ping_update(ll_state *s) { (void)s; }

int ll_ping_reveals(const ll_state *s, int side, int t) { (void)s; (void)side; (void)t; return 0; }
