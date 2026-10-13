/* csrc/terrain_noise.c -- terrain noise lane: integer-hash value noise, fbm, table sine and cosine.
 * Integer only: no libm, no floating point, no world rng. Signatures and fixed-point
 * conventions are documented at the prototypes in om_internal.h. */
#include "ouroboros_sim.h"
#include "om_internal.h"

#define TN_Q16_SHIFT 16
#define TN_Q16_ONE 65536
#define TN_Q16_MASK 0xFFFF
#define TN_SPLITMIX_ADD 0x9E3779B97F4A7C15ULL
#define TN_SPLITMIX_MUL1 0xBF58476D1CE4E5B9ULL
#define TN_SPLITMIX_MUL2 0x94D049BB133111EBULL
#define TN_SPLITMIX_SHIFT1 30
#define TN_SPLITMIX_SHIFT2 27
#define TN_SPLITMIX_SHIFT3 31
#define TN_HASH_PRIME_X 0xD6E8FEB86659FD93ULL
#define TN_HASH_PRIME_Y 0xA0761D6478BD642FULL
#define TN_VALUE_SHIFT 40
#define TN_VALUE_SPAN 131073
#define TN_FADE_A 6
#define TN_FADE_B 15
#define TN_FADE_C 10
#define TN_SIN_TURN_SHIFT 6
#define TN_SIN_FRAC_MASK 63
#define TN_SIN_FRAC_STEPS 64
#define TN_SIN_QUARTER 256
#define TN_SIN_QUADRANT_SHIFT 8
#define TN_SIN_QUADRANTS_MASK 1023
#define TN_QUARTER_TURN_Q16 16384

/* constants-table: docs/bible/epics/E-17-map-generation.md R-186-04, sine quarter wave round(65536 * sin(pi/2 * i / 256)), i = 0..256 (provisional 2026-10-05) */
static const int32_t tn_sin_quarter[TN_SIN_QUARTER + 1] = {
    0, 402, 804, 1206, 1608, 2010, 2412, 2814,
    3216, 3617, 4019, 4420, 4821, 5222, 5623, 6023,
    6424, 6824, 7224, 7623, 8022, 8421, 8820, 9218,
    9616, 10014, 10411, 10808, 11204, 11600, 11996, 12391,
    12785, 13180, 13573, 13966, 14359, 14751, 15143, 15534,
    15924, 16314, 16703, 17091, 17479, 17867, 18253, 18639,
    19024, 19409, 19792, 20175, 20557, 20939, 21320, 21699,
    22078, 22457, 22834, 23210, 23586, 23961, 24335, 24708,
    25080, 25451, 25821, 26190, 26558, 26925, 27291, 27656,
    28020, 28383, 28745, 29106, 29466, 29824, 30182, 30538,
    30893, 31248, 31600, 31952, 32303, 32652, 33000, 33347,
    33692, 34037, 34380, 34721, 35062, 35401, 35738, 36075,
    36410, 36744, 37076, 37407, 37736, 38064, 38391, 38716,
    39040, 39362, 39683, 40002, 40320, 40636, 40951, 41264,
    41576, 41886, 42194, 42501, 42806, 43110, 43412, 43713,
    44011, 44308, 44604, 44898, 45190, 45480, 45769, 46056,
    46341, 46624, 46906, 47186, 47464, 47741, 48015, 48288,
    48559, 48828, 49095, 49361, 49624, 49886, 50146, 50404,
    50660, 50914, 51166, 51417, 51665, 51911, 52156, 52398,
    52639, 52878, 53114, 53349, 53581, 53812, 54040, 54267,
    54491, 54714, 54934, 55152, 55368, 55582, 55794, 56004,
    56212, 56418, 56621, 56823, 57022, 57219, 57414, 57607,
    57798, 57986, 58172, 58356, 58538, 58718, 58896, 59071,
    59244, 59415, 59583, 59750, 59914, 60075, 60235, 60392,
    60547, 60700, 60851, 60999, 61145, 61288, 61429, 61568,
    61705, 61839, 61971, 62101, 62228, 62353, 62476, 62596,
    62714, 62830, 62943, 63054, 63162, 63268, 63372, 63473,
    63572, 63668, 63763, 63854, 63944, 64031, 64115, 64197,
    64277, 64354, 64429, 64501, 64571, 64639, 64704, 64766,
    64827, 64884, 64940, 64993, 65043, 65091, 65137, 65180,
    65220, 65259, 65294, 65328, 65358, 65387, 65413, 65436,
    65457, 65476, 65492, 65505, 65516, 65525, 65531, 65535,
    65536,
};
/* end constants-table */

static uint64_t tn_mix(uint64_t z) {
    z += TN_SPLITMIX_ADD;
    z = (z ^ (z >> TN_SPLITMIX_SHIFT1)) * TN_SPLITMIX_MUL1;
    z = (z ^ (z >> TN_SPLITMIX_SHIFT2)) * TN_SPLITMIX_MUL2;
    return z ^ (z >> TN_SPLITMIX_SHIFT3);
}

static int32_t tn_lattice(uint64_t seed, int64_t ix, int64_t iy) {
    uint64_t h = tn_mix(seed ^ tn_mix((uint64_t)ix * TN_HASH_PRIME_X ^ (uint64_t)iy * TN_HASH_PRIME_Y));
    return (int32_t)((h >> TN_VALUE_SHIFT) % TN_VALUE_SPAN) - TN_Q16_ONE;
}

static int64_t tn_fade(int64_t t) {
    int64_t a = t * TN_FADE_A - (int64_t)TN_FADE_B * TN_Q16_ONE;
    int64_t b = ((t * a) >> TN_Q16_SHIFT) + (int64_t)TN_FADE_C * TN_Q16_ONE;
    int64_t t2 = (t * t) >> TN_Q16_SHIFT;
    return (((t2 * b) >> TN_Q16_SHIFT) * t) >> TN_Q16_SHIFT;
}

static int64_t tn_lerp(int64_t a, int64_t b, int64_t t) {
    return a + (((b - a) * t) >> TN_Q16_SHIFT);
}

static int32_t tn_value64(uint64_t seed, int64_t x, int64_t y) {
    int64_t ix = x >> TN_Q16_SHIFT, iy = y >> TN_Q16_SHIFT;
    int64_t fx = tn_fade(x & TN_Q16_MASK), fy = tn_fade(y & TN_Q16_MASK);
    int64_t top = tn_lerp(tn_lattice(seed, ix, iy), tn_lattice(seed, ix + 1, iy), fx);
    int64_t bot = tn_lerp(tn_lattice(seed, ix, iy + 1), tn_lattice(seed, ix + 1, iy + 1), fx);
    return (int32_t)tn_lerp(top, bot, fy);
}

int32_t om_tn_value2(uint64_t seed, int32_t x_q16, int32_t y_q16) {
    return tn_value64(seed, x_q16, y_q16);
}

int32_t om_tn_fbm2(uint64_t seed, int32_t x_q16, int32_t y_q16, int octaves, int32_t gain_q16) {
    int64_t acc = 0, amp_sum = 0, amp = TN_Q16_ONE;
    for (int i = 0; i < octaves; i++) {
        acc += (int64_t)tn_value64(seed + (uint64_t)i, (int64_t)x_q16 * ((int64_t)1 << i), (int64_t)y_q16 * ((int64_t)1 << i)) * amp;
        amp_sum += amp;
        amp = (amp * gain_q16) >> TN_Q16_SHIFT;
    }
    if (amp_sum <= 0) return 0;
    return (int32_t)(acc / amp_sum);
}

static int32_t tn_sin_at(uint32_t i) {
    uint32_t q = (i & TN_SIN_QUADRANTS_MASK) >> TN_SIN_QUADRANT_SHIFT;
    uint32_t j = i & (TN_SIN_QUARTER - 1);
    int32_t v = (q & 1) ? tn_sin_quarter[TN_SIN_QUARTER - j] : tn_sin_quarter[j];
    return (q & 2) ? -v : v;
}

int32_t om_tn_sin_q16(uint32_t turn_q16) {
    uint32_t t = turn_q16 & TN_Q16_MASK;
    uint32_t i = t >> TN_SIN_TURN_SHIFT;
    int32_t a = tn_sin_at(i), b = tn_sin_at(i + 1);
    return a + (int32_t)(((int64_t)(b - a) * (int32_t)(t & TN_SIN_FRAC_MASK)) / TN_SIN_FRAC_STEPS);
}

int32_t om_tn_cos_q16(uint32_t turn_q16) {
    return om_tn_sin_q16((turn_q16 + TN_QUARTER_TURN_Q16) & TN_Q16_MASK);
}
