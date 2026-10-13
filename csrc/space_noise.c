/* csrc/space_noise.c -- space landscape value noise, ported line for line from
 * scenes/mockups/landscape/field_map_space.gd (hash32, _sample_layer, _smooth). Double arithmetic, no libm.
 * Symbols are declared in csrc/ouroboros_sim.h (K-d2). */
#include "ouroboros_sim.h"
#include <stdint.h>
#include <stdlib.h>

#define SN_SPACING 100.0
#define SN_LAYERS 5
#define SN_OCTAVES 2
#define SN_PLANE_MAX 16
#define SN_HASH_X 0x8da6b343u
#define SN_HASH_Y 0xd8163841u
#define SN_HASH_Z 0xcb1ab31fu
#define SN_HASH_MIX 0x5bd1e995u
#define SN_U32_SPAN 4294967296.0

#define SN_L0X 5
#define SN_L0Y 5
#define SN_L0Z 2
#define SN_L1X 14
#define SN_L1Y 14
#define SN_L1Z 4
#define SN_W0 0.65
#define SN_W1 0.35
#define SN_SHIFT_A 13
#define SN_SHIFT_B 15
#define SN_SMOOTH_B 3.0

static const int sn_lattice[SN_OCTAVES][3] = {{SN_L0X, SN_L0Y, SN_L0Z}, {SN_L1X, SN_L1Y, SN_L1Z}};
static const double sn_weight[SN_OCTAVES] = {SN_W0, SN_W1};

uint32_t om_space_hash32(int32_t ix, int32_t iy, int32_t iz, uint32_t seed) {
    uint32_t h = (uint32_t)ix * SN_HASH_X;
    h ^= (uint32_t)iy * SN_HASH_Y;
    h ^= (uint32_t)iz * SN_HASH_Z;
    h ^= seed;
    h ^= h >> SN_SHIFT_A;
    h *= SN_HASH_MIX;
    h ^= h >> SN_SHIFT_B;
    return h;
}

static double sn_smooth(double t) { return t * t * (SN_SMOOTH_B - 2.0 * t); }
static double sn_lerp(double a, double b, double t) { return a + (b - a) * t; }
static int32_t sn_floor(double x) { int32_t i = (int32_t)x; return (double)i > x ? i - 1 : i; }

uint32_t om_space_noise_layer(uint32_t layer_seed, double canvas, uint32_t k, int independent,
                              double *out, uint32_t cap) {
    uint32_t dim = (uint32_t)(canvas / SN_SPACING) + 1;
    uint32_t total = dim * dim;
    if (cap < total) return 0;
    double *plane = malloc(sizeof(double) * SN_PLANE_MAX * SN_PLANE_MAX);
    double *col_t = malloc(sizeof(double) * dim);
    int32_t *col_i = malloc(sizeof(int32_t) * dim);
    if (!plane || !col_t || !col_i) { free(plane); free(col_t); free(col_i); return 0; }
    for (uint32_t i = 0; i < total; i++) out[i] = 0.0;
    for (int o = 0; o < SN_OCTAVES; o++) {
        int lx = sn_lattice[o][0], ly = sn_lattice[o][1], lz = sn_lattice[o][2];
        int sx = lx + 2, sy = ly + 2;
        double z = independent ? 0.5 : ((double)k + 0.5) / SN_LAYERS * lz;
        int32_t iz = sn_floor(z);
        double tz = sn_smooth(z - iz);
        for (int iy = 0; iy < sy; iy++)
            for (int ix = 0; ix < sx; ix++) {
                double v0 = om_space_hash32(ix, iy, iz, layer_seed) / SN_U32_SPAN;
                double v1 = om_space_hash32(ix, iy, iz + 1, layer_seed) / SN_U32_SPAN;
                plane[iy * sx + ix] = sn_lerp(v0, v1, tz);
            }
        for (uint32_t gx = 0; gx < dim; gx++) {
            double x = gx * SN_SPACING / canvas * lx;
            int32_t ix = sn_floor(x);
            col_i[gx] = ix;
            col_t[gx] = sn_smooth(x - ix);
        }
        for (uint32_t gy = 0; gy < dim; gy++) {
            double y = gy * SN_SPACING / canvas * ly;
            int32_t iy = sn_floor(y);
            double ty = sn_smooth(y - iy);
            int row0 = iy * sx, row1 = row0 + sx;
            uint32_t base = gy * dim;
            for (uint32_t gx = 0; gx < dim; gx++) {
                int32_t ix = col_i[gx];
                double tx = col_t[gx];
                double top = sn_lerp(plane[row0 + ix], plane[row0 + ix + 1], tx);
                double bottom = sn_lerp(plane[row1 + ix], plane[row1 + ix + 1], tx);
                out[base + gx] += sn_weight[o] * sn_lerp(top, bottom, ty);
            }
        }
    }
    free(plane); free(col_t); free(col_i);
    return total;
}
