/* tests/csim/layout_stub_terrain.c -- TEST FIXTURE for VG-P1 (tests/csim/test_VG_P_p1_layout.py).
 * Never linked into the shipped library (the csrc wildcard does not see it, places-lane spec P1,
 * Architect gap 2 ruling 2026-10-14). Fenced: builders do not edit it.
 *
 * A stub terrain behind the layout engine's adapter struct, so the engine builds into its own
 * .so with csrc/terrain_noise.c and this file and needs no world (gap 3). It includes neither
 * layout_internal.h nor ouroboros_sim.h nor om_internal.h.
 * Geometry is for a 16,000 wu square canvas, in absolute wu (gap 1 ruling). Every number is a
 * named draft DRAFT-stub-*, vetoable like the spec's drafts. */
#include <stdint.h>

/* mirror of layout_internal.h, kept equal by the P1 test that compiles both (gap 8: its own
 * typedef and tag, om_stub_layout_terrain) */
typedef struct om_stub_layout_terrain {
    void *ctx;
    double (*height_at)(void *ctx, double x, double y);
    int    (*walkable_at)(void *ctx, double x, double y);
    int    (*nearest_walkable)(void *ctx, double x, double y, double *ox, double *oy);
} om_stub_layout_terrain;

/* mirror of the prototype at om_internal.h:473 */
int32_t om_tn_fbm2(uint64_t seed, int32_t x_q16, int32_t y_q16, int octaves, int32_t gain_q16);

#define STUB_FLAT_H 50.0            /* DRAFT-stub-flat-h: kind 0 height, and the dry height of kind 1 */
#define STUB_LAKE_H (-20.0)         /* DRAFT-stub-lake-h: kind 1 lake height, kind 3 height */
#define STUB_LAKE_CX 8000.0         /* DRAFT-stub-lake-cx */
#define STUB_LAKE_CY 8000.0         /* DRAFT-stub-lake-cy */
#define STUB_LAKE_R 2000.0          /* DRAFT-stub-lake-r */
#define STUB_CLIFF_X 11000.0        /* DRAFT-stub-cliff-x: height steps at x >= this */
#define STUB_CLIFF_H 650.0          /* DRAFT-stub-cliff-h: the plateau height */
#define STUB_BAND_LO 10900.0        /* DRAFT-stub-band-lo: unwalkable band, inclusive */
#define STUB_BAND_HI 11100.0        /* DRAFT-stub-band-hi */
#define STUB_ROLL_BASE 35.0         /* DRAFT-stub-roll-base */
#define STUB_ROLL_AMP 100.0         /* DRAFT-stub-roll-amp */
#define STUB_ROLL_SEED 1234         /* DRAFT-stub-roll-seed */
#define STUB_ROLL_LATTICE 3200      /* DRAFT-stub-roll-lattice, wu */
#define STUB_ROLL_OCTAVES 3         /* DRAFT-stub-roll-octaves */
#define STUB_ROLL_GAIN 32768        /* DRAFT-stub-roll-gain: 0.5 in Q16 */
#define STUB_Q16 65536              /* Q16 one */
#define STUB_NEAR_STEP 100.0        /* DRAFT-stub-near-step: nearest_walkable ring step, wu (a stub detail, not a spec number) */
#define STUB_NEAR_RINGS 40          /* DRAFT-stub-near-rings: ring count, reach 4,000 wu */
#define STUB_NEAR_DIRS 8

static const int32_t stub_kinds[4] = {0, 1, 2, 3};   /* the ctx of a stub is a pointer to its kind */

static double stub_height(void *ctx, double x, double y) {
    int32_t kind = *(const int32_t *)ctx;
    if (kind == 0) return STUB_FLAT_H;
    if (kind == 1) {
        double dx = x - STUB_LAKE_CX, dy = y - STUB_LAKE_CY;
        if (dx * dx + dy * dy <= STUB_LAKE_R * STUB_LAKE_R) return STUB_LAKE_H;
        return x >= STUB_CLIFF_X ? STUB_CLIFF_H : STUB_FLAT_H;
    }
    if (kind == 2) {
        int64_t xi = (int64_t)x, yi = (int64_t)y;           /* truncated to integers, int64 arithmetic */
        int32_t xq = (int32_t)(xi * STUB_Q16 / STUB_ROLL_LATTICE);
        int32_t yq = (int32_t)(yi * STUB_Q16 / STUB_ROLL_LATTICE);
        int32_t f = om_tn_fbm2(STUB_ROLL_SEED, xq, yq, STUB_ROLL_OCTAVES, STUB_ROLL_GAIN);
        return STUB_ROLL_BASE + STUB_ROLL_AMP * (double)f / (double)STUB_Q16;
    }
    return STUB_LAKE_H;                                      /* kind 3: all water */
}

static int stub_walkable(void *ctx, double x, double y) {
    int32_t kind = *(const int32_t *)ctx;
    if (kind == 0) return 1;
    if (kind == 3) return 0;
    if (stub_height(ctx, x, y) < 0.0) return 0;              /* water */
    if (kind == 1 && x >= STUB_BAND_LO && x <= STUB_BAND_HI) return 0;
    return 1;
}

static int stub_nearest(void *ctx, double x, double y, double *ox, double *oy) {
    static const double dir[STUB_NEAR_DIRS][2] = {{1, 0}, {0, 1}, {-1, 0}, {0, -1}, {1, 1}, {-1, 1}, {-1, -1}, {1, -1}};
    for (int r = 0; r <= STUB_NEAR_RINGS; r++) {
        for (int k = 0; k < STUB_NEAR_DIRS; k++) {
            double px = x + dir[k][0] * STUB_NEAR_STEP * r, py = y + dir[k][1] * STUB_NEAR_STEP * r;
            if (stub_walkable(ctx, px, py)) { *ox = px; *oy = py; return 0; }
            if (r == 0) break;
        }
    }
    return -1;
}

/* kinds: 0 flat, 1 lake and cliff, 2 rolling, 3 all water; any other kind leaves *out zeroed */
void om_stub_terrain(int32_t kind, om_stub_layout_terrain *out) {
    out->ctx = 0; out->height_at = 0; out->walkable_at = 0; out->nearest_walkable = 0;
    if (kind < 0 || kind > 3) return;
    out->ctx = (void *)&stub_kinds[kind];
    out->height_at = stub_height;
    out->walkable_at = stub_walkable;
    out->nearest_walkable = stub_nearest;
}
