/* Places lane P2: the lot-order noise (R-193-01: a ragged outline at any age).
 * Spec: docs/northstar/plans/2026-10-13-places-lane-spec.md, "P2".
 * See also: csrc/growth_probe.c uses om_lot_noise_q16 for the lot order. */
#include "lot_noise.h"
#include "om_internal.h" /* only for the om_tn_fbm2 prototype */

/* DRAFT-lot-noise-range, measured by tests/csim/test_VG_P_p2_lot_noise_lanes.py over seeds 1 to 64 (gap 5 reading) */
#define LOT_NOISE_LO_Q16 (-64000) /* measured min -62682, 1318 below it, 1.06 percent of the span 124803 */
#define LOT_NOISE_HI_Q16 63000 /* measured max 62121, 879 above it, 0.70 percent of the span */

#define LOT_NOISE_SALT 420        /* spec rev 4a P2: seed + 420 */
#define LOT_NOISE_LATTICE 8192    /* DRAFT-lot-noise-lattice: cell index * 8192 (one lattice unit = 8 cells) */
#define LOT_NOISE_OCTAVES 3       /* DRAFT-lot-noise-octaves */
#define LOT_NOISE_GAIN_Q16 32768  /* DRAFT-lot-noise-octaves: gain 0.5 */
#define LOT_NOISE_G_LO_Q16 45875  /* DRAFT-lot-noise-band: 0.7 */
#define LOT_NOISE_G_SPAN_Q16 45875 /* DRAFT-lot-noise-band: 1.4 - 0.7 = 0.7 */

uint32_t om_lot_noise_q16(uint64_t seed, int32_t gx, int32_t gy) {
    int32_t f = om_tn_fbm2(seed + LOT_NOISE_SALT, gx * LOT_NOISE_LATTICE, gy * LOT_NOISE_LATTICE,
                           LOT_NOISE_OCTAVES, LOT_NOISE_GAIN_Q16);
    int64_t v = ((int64_t)(f - LOT_NOISE_LO_Q16) * 65536) / (LOT_NOISE_HI_Q16 - LOT_NOISE_LO_Q16);
    if (v < 0) v = 0;
    if (v > 65536) v = 65536; /* 65536 = 1.0 in Q16 */
    return (uint32_t)(LOT_NOISE_G_LO_Q16 + ((v * LOT_NOISE_G_SPAN_Q16) >> 16));
}

void om_lot_noise_range(int32_t *lo_q16, int32_t *hi_q16) {
    if (lo_q16) *lo_q16 = LOT_NOISE_LO_Q16;
    if (hi_q16) *hi_q16 = LOT_NOISE_HI_Q16;
}

/* om_lane_build goes here (unit B2L; R-193-09) */
