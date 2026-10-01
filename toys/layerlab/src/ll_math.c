/* ll_math.c -- PCG32 (SPEC 5.13), Taylor sincos (SPEC 5.12), small helpers. */
#include <float.h>
#include <math.h>
#include "ll_internal.h"

/* ---- PCG32, PCG-XSH-RR 64/32 ---- */
uint32_t ll_rng_next32(ll_rng *r) {
    uint64_t old = r->state;
    r->state = old * 6364136223846793005ULL + r->inc;
    uint32_t xorshifted = (uint32_t)(((old >> 18u) ^ old) >> 27u);
    uint32_t rot = (uint32_t)(old >> 59u);
    return (xorshifted >> rot) | (xorshifted << ((0u - rot) & 31u));
}

void ll_rng_seed(ll_rng *r, uint64_t seed) {
    r->inc = ((seed ^ 0xDA3E39CB94B95BDBULL) << 1) | 1ULL;
    r->state = 0;
    (void)ll_rng_next32(r);
    r->state += seed;
    (void)ll_rng_next32(r);
}

double ll_rng_u(ll_rng *r) {
    uint32_t a = ll_rng_next32(r) >> 5;
    uint32_t b = ll_rng_next32(r) >> 6;
    return ((double)a * 67108864.0 + (double)b) * (1.0 / 9007199254740992.0);
}

double ll_rng_range(ll_rng *r, double lo, double hi) {
    return lo + (hi - lo) * ll_rng_u(r);
}

/* ---- sincos ---- */
/* Wrap to [-pi, pi] without libm floor: truncate toward zero, then correct. */
double ll_wrap_pi(double a) {
    double k = (a + LL_PI) / (2.0 * LL_PI);
    if (!(fabs(k) < 4.0e15)) return 0.0;      /* NaN, inf or absurd: not a real angle here */
    long long ik = (long long)k;
    if ((double)ik > k) ik -= 1;              /* floor */
    return a - (double)ik * (2.0 * LL_PI);
}

void ll_sincos(double a, double *s, double *c) {
    double r = ll_wrap_pi(a), r2 = r * r;
    /* sin: r - r^3/3! + ... - r^13/13!   (7 terms)
     * cos: 1 - r^2/2! + ... - r^12/12!   (7 terms) */
    *s = r * (1.0 + r2 * (-1.0 / 6.0 + r2 * (1.0 / 120.0 + r2 * (-1.0 / 5040.0
         + r2 * (1.0 / 362880.0 + r2 * (-1.0 / 39916800.0 + r2 * (1.0 / 6227020800.0)))))));
    *c = 1.0 + r2 * (-1.0 / 2.0 + r2 * (1.0 / 24.0 + r2 * (-1.0 / 720.0
         + r2 * (1.0 / 40320.0 + r2 * (-1.0 / 3628800.0 + r2 * (1.0 / 479001600.0))))));
}

double ll_dist3(double dx, double dy, int dl, double layer_spacing) {
    double dz = (double)dl * layer_spacing;
    return sqrt(dx * dx + dy * dy + dz * dz);
}

int ll_finite(double x) {
    return x == x && fabs(x) <= DBL_MAX;
}
