/* Layout kit sentinel bodies (S-247). Leaf 1 of the cascade docs/northstar/plans/cascades/layout-kit-assault/
 * replaces this file; until then every entry point reports "not built". See also: csrc/layout_kit.h. */
#include <stddef.h>
#include "layout_kit.h"

int om_lk_generate(uint64_t seed, int32_t archetype, double canvas, int32_t sides_mode, om_lk_layout *out) {
    (void)seed; (void)archetype; (void)canvas; (void)sides_mode; (void)out;
    return -1;
}

void om_lk_run_checks(om_lk_layout *l) { (void)l; }

const char *om_lk_name(int32_t domain, int32_t id) { (void)domain; (void)id; return NULL; }

int32_t om_lk_draft_count(void) { return 0; }
const char *om_lk_draft_name(int32_t i) { (void)i; return NULL; }
double om_lk_draft_value(int32_t i) { (void)i; return 0.0; }
