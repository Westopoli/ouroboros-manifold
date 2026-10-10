/* csrc/economy_density.c -- VG E1b: settlement density field (R-193-01, R-193-06, R-193-08; Q-222-01 a).
 * Ported from scenes/mockups/settlement/settlement_sim.gd (read-only mockup; terms cited below).
 * Grid: OM_DENSITY_SIDE cells of OM_DENSITY_CELL_WU. A ring grows when tick % 60 == 0 (3 s at 20 Hz); no new state
 * field: the propagated potential P is recomputed from the core for the ring count the tick implies, and only the
 * eased density D is stored (w->economy.density), so it is saved and hashed by K-e. Q16 on D.
 * Not ported: water crossing (WATER_CROSS), climb (CLIMB_WU) and shore terms (no per-cell elevation or water in the sim),
 * the Q-168-05 base cap is not enforced (flagged, spec rev 8). */
#include "ouroboros_sim.h"
#include "economy_internal.h"
#include "om_constants.h"
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define OM_DENSITY_CELL_WU 200.0
#define OM_DENSITY_CANVAS_WU (OM_DENSITY_SIDE * OM_DENSITY_CELL_WU)
#define OM_DENSITY_RING_TICKS 60   /* liberty 2026-10-10: 3 s at OM_TACTICAL_TICK_RATE 20 */
#define OM_DENSITY_STEEP_WU 50.0   /* liberty 2026-10-10: a slope segment within 50 wu of the cell centre makes it steep */
#define OM_DENSITY_BASE_DECAY 0.99 /* mockup BASE_DECAY */
#define OM_DENSITY_DIAG 0.99       /* mockup diagonal factor */
#define OM_DENSITY_STEEP_TERM 0.25 /* mockup 1 - 0.25 x slope, slope now 0 or 1 */
#define OM_DENSITY_P_MIN 0.02      /* mockup reach cut-off */
#define OM_DENSITY_EASE 0.35       /* mockup EASE */
#define OM_DENSITY_M_START 0.6     /* mockup M_START */
#define OM_DENSITY_M_FULL_TICKS (300.0 * 20.0) /* mockup M_FULL_S 300 s at 20 Hz */
#define OM_DENSITY_N (OM_DENSITY_SIDE * OM_DENSITY_SIDE)

double om_density_at(const om_world *w, double x, double y) {
    if (!w || !w->economy.density_present) return 0.0;
    if (!(x >= 0.0) || !(y >= 0.0) || x >= OM_DENSITY_CANVAS_WU || y >= OM_DENSITY_CANVAS_WU) return 0.0;
    int cx = (int)(x / OM_DENSITY_CELL_WU), cy = (int)(y / OM_DENSITY_CELL_WU);
    return w->economy.density[cy * OM_DENSITY_SIDE + cx];
}

static int core_cell(void) {
    /* liberty 2026-10-10: no contract names the core; the canvas centre (the mission objective) */
    return (OM_DENSITY_SIDE / 2) * OM_DENSITY_SIDE + OM_DENSITY_SIDE / 2;
}

static double q16(double v) { return (double)(int64_t)(v * 65536.0) / 65536.0; }

static void steep_mark(const om_world *w, unsigned char *steep) {
    memset(steep, 0, OM_DENSITY_N);
    om_slope s;
    uint32_t n = om_terrain_slope_count(w);
    double r2 = OM_DENSITY_STEEP_WU * OM_DENSITY_STEEP_WU;
    for (uint32_t k = 0; k < n; k++) {
        if (om_terrain_slope_get(w, k, &s) != 0) continue;
        double lox = (s.x0 < s.x1 ? s.x0 : s.x1) - OM_DENSITY_STEEP_WU, hix = (s.x0 < s.x1 ? s.x1 : s.x0) + OM_DENSITY_STEEP_WU;
        double loy = (s.y0 < s.y1 ? s.y0 : s.y1) - OM_DENSITY_STEEP_WU, hiy = (s.y0 < s.y1 ? s.y1 : s.y0) + OM_DENSITY_STEEP_WU;
        int c0 = (int)(lox / OM_DENSITY_CELL_WU), c1 = (int)(hix / OM_DENSITY_CELL_WU);
        int r0 = (int)(loy / OM_DENSITY_CELL_WU), r1 = (int)(hiy / OM_DENSITY_CELL_WU);
        if (lox < 0.0) c0 = 0;
        if (loy < 0.0) r0 = 0;
        if (c1 >= OM_DENSITY_SIDE) c1 = OM_DENSITY_SIDE - 1;
        if (r1 >= OM_DENSITY_SIDE) r1 = OM_DENSITY_SIDE - 1;
        double dx = s.x1 - s.x0, dy = s.y1 - s.y0, len2 = dx * dx + dy * dy;
        for (int cy = r0; cy <= r1; cy++)
            for (int cx = c0; cx <= c1; cx++) {
                double px = (cx + 0.5) * OM_DENSITY_CELL_WU, py = (cy + 0.5) * OM_DENSITY_CELL_WU;
                double t = len2 > 0.0 ? ((px - s.x0) * dx + (py - s.y0) * dy) / len2 : 0.0;
                if (t < 0.0) t = 0.0;
                if (t > 1.0) t = 1.0;
                double ex = px - (s.x0 + t * dx), ey = py - (s.y0 + t * dy);
                if (ex * ex + ey * ey <= r2) steep[cy * OM_DENSITY_SIDE + cx] = 1;
            }
    }
}

void om_density_init(om_world *w) {
    if (!w) return;
    memset(w->economy.density, 0, sizeof w->economy.density);
    w->economy.density_present = 0;
    if (om_era_kind(w) != 1 || !om_terrain_present(w)) return;
    w->economy.density_present = 1;
}

void om_density_step(om_world *w, uint64_t tick) {
    if (!w || !w->economy.density_present || (tick % OM_DENSITY_RING_TICKS) != 0) return;
    /* K-e3: the target reads the economy sampled once at om_economy_init, not the live region. */
    double econ = w->economy.density_economy / (double)OM_FIELD_MAX;
    if (econ < 0.0) econ = 0.0;
    if (econ > 1.0) econ = 1.0;
    double mt = (double)tick / OM_DENSITY_M_FULL_TICKS;
    double mat = OM_DENSITY_M_START + (1.0 - OM_DENSITY_M_START) * (mt < 1.0 ? mt : 1.0);

    double *P = calloc(OM_DENSITY_N, sizeof(double));
    unsigned char *steep = malloc(OM_DENSITY_N);
    unsigned char *mark = calloc(OM_DENSITY_N, 1);
    int *act = malloc(OM_DENSITY_N * sizeof(int));
    int *nxt = malloc(OM_DENSITY_N * sizeof(int));
    double *val = malloc(OM_DENSITY_N * sizeof(double));
    if (!P || !steep || !mark || !act || !nxt || !val) goto out;
    steep_mark(w, steep);
    int core = core_cell();
    P[core] = 1.0;
    int na = 1;
    act[0] = core;
    for (uint64_t ring = 0; ring < tick / OM_DENSITY_RING_TICKS && na > 0; ring++) {
        for (int k = 0; k < na; k++) val[k] = P[act[k]];
        int nn = 0;
        for (int k = 0; k < na; k++) {
            int cx = act[k] % OM_DENSITY_SIDE, cy = act[k] / OM_DENSITY_SIDE;
            for (int dy = -1; dy <= 1; dy++)
                for (int dx = -1; dx <= 1; dx++) {
                    if (!dx && !dy) continue;
                    int nx = cx + dx, ny = cy + dy;
                    if (nx < 0 || ny < 0 || nx >= OM_DENSITY_SIDE || ny >= OM_DENSITY_SIDE) continue;
                    int j = ny * OM_DENSITY_SIDE + nx;
                    double f = OM_DENSITY_BASE_DECAY;
                    if (dx && dy) f *= OM_DENSITY_DIAG;
                    if (steep[j]) f *= 1.0 - OM_DENSITY_STEEP_TERM;
                    double v = val[k] * f;
                    if (v > P[j] && v > OM_DENSITY_P_MIN) {
                        P[j] = v;
                        if (!mark[j]) { mark[j] = 1; nxt[nn++] = j; }
                    }
                }
        }
        for (int k = 0; k < nn; k++) mark[nxt[k]] = 0;
        int *t = act; act = nxt; nxt = t;
        na = nn;
    }
    double *D = w->economy.density;
    for (int i = 0; i < OM_DENSITY_N; i++) {
        if (P[i] <= 0.0) continue;
        double tgt = P[i] * mat * econ;
        if (tgt > 1.0) tgt = 1.0;
        if (tgt > D[i]) D[i] = q16(D[i] + (tgt - D[i]) * OM_DENSITY_EASE);
    }
out:
    free(P); free(steep); free(mark); free(act); free(nxt); free(val);
}
