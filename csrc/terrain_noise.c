/* csrc/terrain_noise.c -- terrain noise lane: integer-hash value noise, fbm, table sine and cosine.
 * Stubs (contract piece, terrain stage 1 spec 2026-10-05); the noise lane implements them.
 * Signatures and fixed-point conventions are documented at the prototypes in om_internal.h. */
#include "ouroboros_sim.h"
#include "om_internal.h"

int32_t om_tn_value2(uint64_t seed, int32_t x_q16, int32_t y_q16) {
    (void)seed; (void)x_q16; (void)y_q16;
    return 0;
}

int32_t om_tn_fbm2(uint64_t seed, int32_t x_q16, int32_t y_q16, int octaves, int32_t gain_q16) {
    (void)seed; (void)x_q16; (void)y_q16; (void)octaves; (void)gain_q16;
    return 0;
}

int32_t om_tn_sin_q16(uint32_t turn_q16) {
    (void)turn_q16;
    return 0;
}

int32_t om_tn_cos_q16(uint32_t turn_q16) {
    (void)turn_q16;
    return 0;
}
