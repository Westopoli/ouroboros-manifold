/* Places lane P2: the lot-order noise (R-193-01: a ragged outline at any age).
 * Spec: docs/northstar/plans/2026-10-13-places-lane-spec.md, "P2".
 * See also: csrc/growth_probe.c uses om_lot_noise_q16 for the lot order. */
#include "lot_noise.h"
#include "om_internal.h" /* the om_tn_fbm2 prototype and OM_TERRAIN_CELL_WU */
#include <math.h>
#include <stdlib.h>

/* DRAFT-lot-noise-range, measured by tests/csim/test_VG_P_p2_lot_noise_lanes.py over seeds 1 to 64 (gap 5 reading) */
#define LOT_NOISE_LO_Q16 (-64000) /* measured min -62682, 1318 below it, 1.06 percent of the span 124803 */
#define LOT_NOISE_HI_Q16 63000 /* measured max 62121, 879 above it, 0.70 percent of the span */

#define LOT_NOISE_Q16_ONE 65536   /* Q16 fixed-point scale, 2^16 */
#define LOT_NOISE_Q16_SHIFT 16    /* log2 of LOT_NOISE_Q16_ONE */
#define LOT_NOISE_SALT 420        /* spec rev 4a P2: seed + 420 */
#define LOT_NOISE_LATTICE 8192    /* DRAFT-lot-noise-lattice: cell index * 8192 (one lattice unit = 8 cells) */
#define LOT_NOISE_OCTAVES 3       /* DRAFT-lot-noise-octaves */
#define LOT_NOISE_GAIN_Q16 32768  /* DRAFT-lot-noise-octaves: gain 0.5 */
#define LOT_NOISE_G_LO_Q16 45875  /* DRAFT-lot-noise-band: 0.7 */
#define LOT_NOISE_G_SPAN_Q16 45875 /* DRAFT-lot-noise-band: 1.4 - 0.7 = 0.7 */

uint32_t om_lot_noise_q16(uint64_t seed, int32_t gx, int32_t gy) {
    int32_t f = om_tn_fbm2(seed + LOT_NOISE_SALT, gx * LOT_NOISE_LATTICE, gy * LOT_NOISE_LATTICE,
                           LOT_NOISE_OCTAVES, LOT_NOISE_GAIN_Q16);
    int64_t v = ((int64_t)(f - LOT_NOISE_LO_Q16) * LOT_NOISE_Q16_ONE) / (LOT_NOISE_HI_Q16 - LOT_NOISE_LO_Q16);
    if (v < 0) v = 0;
    if (v > LOT_NOISE_Q16_ONE) v = LOT_NOISE_Q16_ONE;
    return (uint32_t)(LOT_NOISE_G_LO_Q16 + ((v * LOT_NOISE_G_SPAN_Q16) >> LOT_NOISE_Q16_SHIFT));
}

void om_lot_noise_range(int32_t *lo_q16, int32_t *hi_q16) {
    if (lo_q16) *lo_q16 = LOT_NOISE_LO_Q16;
    if (hi_q16) *hi_q16 = LOT_NOISE_HI_Q16;
}

/* Lanes (R-193-09: streets along contour lines and rivers). Spec rev 4a P2; the water test is gap 1 (height_at < 0.0). */
#define LANE_LEVELS 4              /* spec rev 4a P2: level 0..3 */
#define LANE_CONTOUR_WU 150.0      /* DRAFT-lane-contour: interval 150 * 2^L wu */
#define LANE_FALLBACK_PERIOD 4     /* DRAFT-lane-fallback: period 4 * 2^L cells */
#define LANE_REACH 4               /* DRAFT-lane-fallback-reach: Chebyshev cells */
#define LANE_WINDOW 20             /* DRAFT-lane-window: 41 x 41 around the core cell */
#define LANE_SHARE_NUM 3          /* DRAFT-lane-share 0.30 as 3/10 */
#define LANE_SHARE_DEN 10
#define LANE_WARP_SALT_X 430       /* spec rev 4a P2: seed + 430 */
#define LANE_WARP_SALT_Y 440       /* spec rev 4a P2: seed + 440 */
#define LANE_WARP_OCTAVES 2        /* spec rev 4a P2 */
#define LANE_WARP_AMP 3            /* DRAFT-lane-fallback: warp up to +-3 cells */
#define LANE_WARP_HALF_Q16 32768   /* spec rev 4a P2: rounding term 0.5 in Q16 */

static int32_t floor_div(int32_t a, int32_t b) { /* b > 0; C division truncates toward zero */
    int32_t q = a / b;
    if ((a % b) != 0 && a < 0) q--;
    return q;
}

static int32_t floor_mod(int32_t a, int32_t b) { return a - floor_div(a, b) * b; }

void om_lane_build(const om_layout_terrain *t, uint64_t seed, int32_t side, const uint32_t *core_cells, uint32_t n_cores,
                   uint8_t *lane, uint8_t *level_out) {
    if (!t || !t->height_at || !core_cells || !lane || !level_out || n_cores == 0 || side <= 0) return;
    int32_t n = side * side;
    /* one block: heights, warps, prefix sums, then the per-cell flags and the four masks */
    double *h = malloc((size_t)n * sizeof(double));
    int32_t *wx = malloc((size_t)n * sizeof(int32_t));
    int32_t *wy = malloc((size_t)n * sizeof(int32_t));
    int32_t *pre = malloc((size_t)(side + 1) * (size_t)(side + 1) * sizeof(int32_t));
    uint8_t *flags = malloc((size_t)n * (size_t)(2 + LANE_LEVELS)); /* [0] water adjacent, [1] base, [2..5] lane mask per level */
    if (!h || !wx || !wy || !pre || !flags) { free(h); free(wx); free(wy); free(pre); free(flags); return; }
    uint8_t *wadj = flags, *base = flags + n, *mask[LANE_LEVELS];
    for (int L = 0; L < LANE_LEVELS; L++) mask[L] = flags + (size_t)n * (size_t)(2 + L);

    for (int32_t gy = 0; gy < side; gy++)
        for (int32_t gx = 0; gx < side; gx++) {
            int32_t i = gy * side + gx;
            h[i] = t->height_at(t->ctx, ((double)gx + 0.5) * OM_TERRAIN_CELL_WU, ((double)gy + 0.5) * OM_TERRAIN_CELL_WU); /* cell centre */
            int32_t fx = om_tn_fbm2(seed + LANE_WARP_SALT_X, gx * LOT_NOISE_LATTICE, gy * LOT_NOISE_LATTICE, LANE_WARP_OCTAVES, LOT_NOISE_GAIN_Q16);
            int32_t fy = om_tn_fbm2(seed + LANE_WARP_SALT_Y, gx * LOT_NOISE_LATTICE, gy * LOT_NOISE_LATTICE, LANE_WARP_OCTAVES, LOT_NOISE_GAIN_Q16);
            wx[i] = floor_div(LANE_WARP_AMP * fx + LANE_WARP_HALF_Q16, LOT_NOISE_Q16_ONE);
            wy[i] = floor_div(LANE_WARP_AMP * fy + LANE_WARP_HALF_Q16, LOT_NOISE_Q16_ONE);
        }
    for (int32_t gy = 0; gy < side; gy++)
        for (int32_t gx = 0; gx < side; gx++) {
            uint8_t a = 0; /* water lane: any of the eight on-grid neighbours is water (off-grid skipped, gap 8 reading) */
            for (int32_t dy = -1; dy <= 1; dy++)
                for (int32_t dx = -1; dx <= 1; dx++) {
                    int32_t nx = gx + dx, ny = gy + dy;
                    if ((dx || dy) && nx >= 0 && nx < side && ny >= 0 && ny < side && h[ny * side + nx] < 0.0) a = 1;
                }
            wadj[gy * side + gx] = a;
        }

    for (int L = 0; L < LANE_LEVELS; L++) {
        double interval = LANE_CONTOUR_WU * (double)(1 << L); /* DRAFT-lane-contour: 150 * 2^L */
        for (int32_t gy = 0; gy < side; gy++)
            for (int32_t gx = 0; gx < side; gx++) {
                int32_t i = gy * side + gx;
                double c = floor(h[i] / interval);
                uint8_t b = wadj[i];
                if (gx + 1 < side && floor(h[i + 1] / interval) != c) b = 1;
                if (gy + 1 < side && floor(h[i + side] / interval) != c) b = 1;
                base[i] = b;
            }
        int32_t stride = side + 1; /* prefix sums of base for the fallback-reach test */
        for (int32_t k = 0; k < stride; k++) { pre[k] = 0; pre[k * stride] = 0; }
        for (int32_t gy = 0; gy < side; gy++) {
            int32_t run = 0;
            for (int32_t gx = 0; gx < side; gx++) {
                run += base[gy * side + gx];
                pre[(gy + 1) * stride + gx + 1] = pre[gy * stride + gx + 1] + run;
            }
        }
        int32_t period = LANE_FALLBACK_PERIOD << L; /* DRAFT-lane-fallback: the period doubles with the level */
        for (int32_t gy = 0; gy < side; gy++)
            for (int32_t gx = 0; gx < side; gx++) {
                int32_t i = gy * side + gx;
                if (base[i]) { mask[L][i] = 1; continue; }
                int32_t x0 = gx - LANE_REACH < 0 ? 0 : gx - LANE_REACH, x1 = gx + LANE_REACH > side - 1 ? side - 1 : gx + LANE_REACH;
                int32_t y0 = gy - LANE_REACH < 0 ? 0 : gy - LANE_REACH, y1 = gy + LANE_REACH > side - 1 ? side - 1 : gy + LANE_REACH;
                int32_t near = pre[(y1 + 1) * stride + x1 + 1] - pre[y0 * stride + x1 + 1] - pre[(y1 + 1) * stride + x0] + pre[y0 * stride + x0];
                mask[L][i] = (near == 0 && (floor_mod(gx + wx[i], period) == period - 1 || floor_mod(gy + wy[i], period) == period - 1)) ? 1 : 0;
            }
    }

    /* a core's level: lowest L whose window share of lane over non-water cells is at most 30 percent (DRAFT-lane-share), else 3 */
    for (uint32_t c = 0; c < n_cores; c++) {
        int32_t level = LANE_LEVELS - 1;
        int32_t cx = (int32_t)(core_cells[c] % (uint32_t)side), cy = (int32_t)(core_cells[c] / (uint32_t)side);
        if (core_cells[c] < (uint32_t)n)
            for (int L = 0; L < LANE_LEVELS; L++) {
                int32_t lanes = 0, dry = 0;
                for (int32_t gy = cy - LANE_WINDOW; gy <= cy + LANE_WINDOW; gy++)
                    for (int32_t gx = cx - LANE_WINDOW; gx <= cx + LANE_WINDOW; gx++) {
                        if (gx < 0 || gx >= side || gy < 0 || gy >= side || h[gy * side + gx] < 0.0) continue; /* window clipped to the grid */
                        dry++;
                        lanes += mask[L][gy * side + gx];
                    }
                if (lanes * LANE_SHARE_DEN <= LANE_SHARE_NUM * dry) { level = L; break; }
            }
        level_out[c] = (uint8_t)level;
    }

    /* level per cell = the level of its nearest core by Chebyshev distance, ties to the lower index */
    for (int32_t gy = 0; gy < side; gy++)
        for (int32_t gx = 0; gx < side; gx++) {
            int32_t best = -1, bi = 0;
            for (uint32_t c = 0; c < n_cores; c++) {
                if (core_cells[c] >= (uint32_t)n) continue;
                int32_t dx = gx - (int32_t)(core_cells[c] % (uint32_t)side), dy = gy - (int32_t)(core_cells[c] / (uint32_t)side);
                int32_t d = (dx < 0 ? -dx : dx) > (dy < 0 ? -dy : dy) ? (dx < 0 ? -dx : dx) : (dy < 0 ? -dy : dy);
                if (best < 0 || d < best) { best = d; bi = (int32_t)c; }
            }
            lane[gy * side + gx] = best < 0 ? mask[0][gy * side + gx] : mask[level_out[bi]][gy * side + gx];
        }
    free(h); free(wx); free(wy); free(pre); free(flags);
}
