/* Places lane P2 interface (docs/northstar/plans/2026-10-13-places-lane-spec.md, "P2 lot-order noise, lanes and the growth probe"). */
#ifndef OM_LOT_NOISE_H
#define OM_LOT_NOISE_H

#include <stdint.h>
#include "layout_internal.h"

/* g of cell (gx, gy), Q16 45875..91750 (0.7..1.4). Lots are created in ascending key = dist_cells * g (R-193-01: a ragged outline at any age). */
uint32_t om_lot_noise_q16(uint64_t seed, int32_t gx, int32_t gy);
/* the pinned fbm range used for the rescale: lo <= every om_tn_fbm2 result the noise takes, hi >= every one (Q16, measured) */
void     om_lot_noise_range(int32_t *lo_q16, int32_t *hi_q16);
/* lane cells (R-193-09). core_cells: n_cores cell indices (side*side grid). level_out[n_cores] 0..3. lane[side*side] 1 = lane. */
void     om_lane_build(const om_layout_terrain *t, uint64_t seed, int32_t side, const uint32_t *core_cells, uint32_t n_cores,
                       uint8_t *lane, uint8_t *level_out);

#endif
