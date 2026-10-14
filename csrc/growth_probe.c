/* Places lane P2: the growth probe (docs/northstar/plans/2026-10-13-places-lane-spec.md rev 4a, "P2 ... the growth probe").
 * Exported for tests, called from no production path, no header, no world. It is the copy of the P3 hop, per-core
 * maturity and economy, pre-growth schedule and lot rule on dry flat ground with no lanes (R-193-01: a ragged outline at
 * any age comes from the lot order, om_lot_noise_q16).
 * See also: csrc/economy_density.c (om_density_step, factor, q16: the hop and ease this copies byte for byte; P3 must
 * match this file), csrc/economy_lots.c (THRESHOLD_1), csrc/economy_lot_noise.c (the lot order key). */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "lot_noise.h"

/* The divergence test (tests/csim/test_VG_P_p2_probe_shape.py) patches these two lines, each defined once. */
#define PROBE_BASE_DECAY 0.99
#define PROBE_NONWATER_FAR 0.99
#define PROBE_DIAG_DECAY 0.9917     /* DRAFT-diag-decay (P3 replaces DIAG_DECAY 0.99, economy_density.c:28, by it) */
#define P_EPS 0.0005                /* economy_density.c:35 */
#define P_MIN 0.02                  /* economy_density.c:36 */
#define EASE 0.35                   /* economy_density.c:37 */
#define M_START 0.6                 /* economy_density.c:38 */
#define M_FULL_TICKS 6000.0         /* economy_density.c:39: 300 s at 20 Hz */
#define THRESHOLD_1 0.10            /* economy_lots.c:14 (used by lot_step, unit B3) */
/* OM_LOT_CAP is 2048 at csrc/om_internal.h:79; P3 raises it to 8192 (DRAFT-lot-cap). The probe does not include
 * om_internal.h, so it carries the raised value. A lot_cap argument of 0 or less selects it (gap 2 ruling). */
#define PROBE_LOT_CAP 8192
#define PROBE_MAX_CORES 6           /* DRAFT-towns-max 6, spec rev 4a */
#define PROBE_MAX_SIDE 240          /* spec rev 4a: the probe's largest grid */
#define PROBE_MAX_AGE 400           /* spec rev 4a: ages 0..400 growth steps */
#define PROBE_NO_LOT 255            /* spec rev 4a: out_lot_core 255 = no lot */
#define PROBE_ECONOMY 1.0           /* DRAFT-probe-economy */
#define PROBE_CORE_ECON_FLOOR 0.5   /* DRAFT-core-economy: econ_c = economy * (0.5 + 0.5 * min(1, age / 40)) */
#define PROBE_CORE_ECON_AGE 40.0    /* DRAFT-core-economy: the age at which a core's economy is full */
#define PROBE_STEP_TICKS 60         /* spec rev 4a: one growth step is 60 ticks (OM_DENSITY_RING_TICKS) */
#define PROBE_LOT_EVERY 4           /* DRAFT-pregrow-lot-ratio: one lot step after every 4th growth step */
#define PROBE_Q16_ONE 65536.0       /* OM_DENSITY_Q16_ONE, the Q16 scale of the density truncation */

static double q16(double v) { return (double)(int64_t)(v * PROBE_Q16_ONE) / PROBE_Q16_ONE; } /* economy_density.c:41 */

typedef struct {
    int32_t side;
    uint32_t n_cores;
    const uint32_t *core_cells;
    const int32_t *ages;
    double *P;
    double *density;
    uint8_t *core_of;
    uint8_t *lot_core;   /* side*side, 255 = no lot */
} probe_t;

/* One hop-and-ease step at virtual tick `tick` (negative during pre-growth). act and next are side*side lists. */
static void probe_step(probe_t *p, int64_t tick, uint32_t *act, uint32_t *n_act, uint32_t *next, uint8_t *queued) {
    int32_t side = p->side;
    uint32_t n = (uint32_t)side * (uint32_t)side, nn = 0;
    memset(queued, 0, n);
    /* economy_density.c:210-236: in place, active in stored order, dy then dx over -1..1 (NW N NE W E SW S SE) */
    for (uint32_t k = 0; k < *n_act; k++) {
        uint32_t i = act[k];
        int32_t cx = (int32_t)(i % (uint32_t)side), cy = (int32_t)(i / (uint32_t)side);
        for (int32_t dy = -1; dy <= 1; dy++)
            for (int32_t dx = -1; dx <= 1; dx++) {
                if (dx == 0 && dy == 0) continue;
                int32_t nx = cx + dx, ny = cy + dy;
                if (nx < 0 || ny < 0 || nx >= side || ny >= side) continue;
                uint32_t j = (uint32_t)ny * (uint32_t)side + (uint32_t)nx;
                /* economy_density.c:180-191 on dry flat ground: the water, climb and slope factors are exactly 1.0 */
                double f = PROBE_BASE_DECAY;
                if (dx != 0 && dy != 0) f *= PROBE_DIAG_DECAY;
                f *= PROBE_NONWATER_FAR;
                double v = p->P[i] * f;
                if (v > p->P[j] + P_EPS && v > P_MIN) {
                    p->P[j] = v;
                    p->core_of[j] = p->core_of[i];
                    if (!queued[j]) { queued[j] = 1; next[nn++] = j; }
                }
            }
    }
    memcpy(act, next, (size_t)nn * sizeof(uint32_t));
    *n_act = nn;
    /* economy_density.c:195-199 row-major, with the per-core maturity and economy (DRAFT-core-economy) */
    for (uint32_t i = 0; i < n; i++) {
        if (p->P[i] <= 0.0) continue;
        uint32_t c = p->core_of[i];
        double age = (double)p->ages[c];
        double clock = age * PROBE_STEP_TICKS + (double)tick;       /* clock_c = age_c * 60 + tick */
        double mat = M_START + (1.0 - M_START) * fmin(1.0, clock / M_FULL_TICKS);
        double econ = PROBE_ECONOMY * (PROBE_CORE_ECON_FLOOR + (1.0 - PROBE_CORE_ECON_FLOOR) * fmin(1.0, age / PROBE_CORE_ECON_AGE));
        if (p->n_cores == 1 && p->ages[0] == 0) econ = PROBE_ECONOMY;  /* the single fallback core with age 0: full economy */
        double tgt = fmin(1.0, p->P[i] * mat * econ);
        if (tgt > p->density[i]) p->density[i] += (tgt - p->density[i]) * EASE;
        p->density[i] = q16(p->density[i]);
        p->P[i] = q16(p->P[i]);
    }
}

/* One lot step; returns the lots standing afterwards. B3 fills this. */
static int32_t lot_step(probe_t *p, uint64_t seed, int32_t lot_cap) {
    (void)p; (void)seed; (void)lot_cap;
    return 0;
}

int32_t om_growth_probe_run(uint64_t seed, int32_t side, uint32_t n_cores, const uint32_t *core_cells, const int32_t *ages,
                            double *out_P, double *out_density, uint8_t *out_lot_core, int32_t *out_death_step, int32_t lot_cap) {
    if (!core_cells || !ages || n_cores == 0 || n_cores > PROBE_MAX_CORES || side <= 0 || side > PROBE_MAX_SIDE) return -1;
    uint32_t n = (uint32_t)side * (uint32_t)side;
    int32_t max_age = 0;
    for (uint32_t c = 0; c < n_cores; c++) {
        if (ages[c] < 0 || ages[c] > PROBE_MAX_AGE || core_cells[c] >= n) return -1;
        if (ages[c] > max_age) max_age = ages[c];
    }
    if (lot_cap <= 0) lot_cap = PROBE_LOT_CAP;

    probe_t p;
    p.side = side; p.n_cores = n_cores; p.core_cells = core_cells; p.ages = ages;
    p.P = calloc(n, sizeof(double));
    p.density = calloc(n, sizeof(double));
    p.core_of = malloc(n);
    p.lot_core = malloc(n);
    uint32_t *act = malloc(((size_t)n + PROBE_MAX_CORES) * sizeof(uint32_t)); /* room for the cores activated onto a full list */
    uint32_t *next = malloc((size_t)n * sizeof(uint32_t));
    uint8_t *queued = malloc(n);
    int32_t lots = -1;
    if (p.P && p.density && p.core_of && p.lot_core && act && next && queued) {
        memset(p.core_of, PROBE_NO_LOT, n);
        memset(p.lot_core, PROBE_NO_LOT, n);
        uint32_t n_act = 0;
        for (uint32_t c = 0; c < n_cores; c++)   /* cores with age 0 are active at the start */
            if (ages[c] == 0) { p.P[core_cells[c]] = 1.0; p.core_of[core_cells[c]] = (uint8_t)c; act[n_act++] = core_cells[c]; }
        int32_t death = -1;
        lots = 0;
        for (int32_t k = 1; k <= max_age; k++) {
            for (uint32_t c = 0; c < n_cores; c++)   /* activate every core with age == max_age - k + 1 */
                if (ages[c] == max_age - k + 1) { p.P[core_cells[c]] = 1.0; p.core_of[core_cells[c]] = (uint8_t)c; act[n_act++] = core_cells[c]; }
            probe_step(&p, (int64_t)(k - max_age) * PROBE_STEP_TICKS, act, &n_act, next, queued);
            if (n_act == 0 && death < 0) death = k;
            if (k % PROBE_LOT_EVERY == 0 || k == max_age) lots = lot_step(&p, seed, lot_cap);
        }
        if (max_age == 0) lots = lot_step(&p, seed, lot_cap);   /* no growth step: the one lot step after the last */
        if (out_P) memcpy(out_P, p.P, (size_t)n * sizeof(double));
        if (out_density) memcpy(out_density, p.density, (size_t)n * sizeof(double));
        if (out_lot_core) memcpy(out_lot_core, p.lot_core, n);
        if (out_death_step) *out_death_step = death;
    }
    free(p.P); free(p.density); free(p.core_of); free(p.lot_core); free(act); free(next); free(queued);
    return lots;
}
