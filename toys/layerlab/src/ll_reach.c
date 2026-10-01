/* ll_reach.c -- reach by unit type (E-01 S-164, SPEC 15.1, ABI 3). Call sites are in ll_combat.c. */
#include "ll_internal.h"

const char *ll_reach_validate(const ll_scenario *sc) {
    int n = sc->n_types < LL_MAX_TYPES ? sc->n_types : LL_MAX_TYPES;   /* n_types itself is checked by the caller */
    for (int i = 0; i < n; i++) {
        const ll_unit_type *t = &sc->types[i];
        if (t->reach_on != 0 && t->reach_on != 1) return "type: reach_on must be 0 or 1";
        if (!t->reach_on) continue;
        for (int k = 0; k < 9; k++)
            if (!ll_finite(t->reach[k]) || t->reach[k] < 0.0) return "type: reach entries must be finite and >= 0";
    }
    return 0;
}

double ll_reach_mult(const ll_unit *a, int off) {
    return a->ty->reach_on ? a->ty->reach[off] : 1.0;
}
