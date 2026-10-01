/* ll_reach.c -- reach by unit type (E-01 S-164, ABI 3). Stub: returns the legacy behaviour (every offset 1.0)
 * until the reach builder replaces it. Call sites are fixed in ll_combat.c. */
#include "ll_internal.h"

const char *ll_reach_validate(const ll_scenario *sc) { (void)sc; return 0; }

double ll_reach_mult(const ll_unit *a, int off) { (void)a; (void)off; return 1.0; }
