/* Layout kit drafts (S-247): every figure of the kit is a DRAFT_ macro here, listed once in LK_DRAFT_TABLE(X) so the
 * CLI prints the same table (om_lk_draft_count/name/value) and the picture's sidebar can never drift from the header.
 * Westley owns every threshold and tolerance; each value is a draft until the lab reports. Lengths are wu on a canvas
 * of DRAFT_CANVAS_ASSAULT and are scaled by canvas / DRAFT_CANVAS_ASSAULT; widths (choke, lane) are not scaled.
 * Also holds the kit-internal declarations shared by layout_kit.c, layout_kit_pieces.c and layout_kit_graph.c
 * (names lk_*, never in layout_kit.h). */
#ifndef OM_LAYOUT_DRAFTS_H
#define OM_LAYOUT_DRAFTS_H

#include <stdint.h>
#include "layout_kit.h"

/* ---- splitmix64 (the pattern of csrc/chronicle.c chron_splitmix_next) ---- */
#define LK_RNG_GOLDEN     0x9E3779B97F4A7C15ULL
#define LK_RNG_MIX1       0xBF58476D1CE4E5B9ULL
#define LK_RNG_MIX2       0x94D049BB133111EBULL
#define LK_RNG_SHIFT1     30
#define LK_RNG_SHIFT2     27
#define LK_RNG_SHIFT3     31
#define LK_RNG_OUT_SHIFT  11
#define LK_RNG_SCALE      (1.0 / 9007199254740992.0)

/* ---- canvas and the named drafts of the spec ---- */
#define DRAFT_CANVAS_MIN          8000
#define DRAFT_CANVAS_MAX          64000
#define DRAFT_CANVAS_ASSAULT      24000
#define DRAFT_CHOKE_W_MIN         300
#define DRAFT_CHOKE_W_MAX         700
#define DRAFT_BYPASS_MIN          1.5
#define DRAFT_BYPASS_MAX          2.4
#define DRAFT_ASSAULT_CROSSINGS   1
#define DRAFT_ASSAULT_HEIGHTS     1
#define DRAFT_ASSAULT_PRIZES      1
#define DRAFT_VANTAGE_BANDS_MIN   1
#define DRAFT_VANTAGE_BANDS_MAX   3
#define DRAFT_MEANDER_MIN         1.0
#define DRAFT_MEANDER_MAX         1.6
#define DRAFT_MEANDER_STEPS       12
#define DRAFT_EQUAL_TOL           0.10
#define DRAFT_CANDIDATES          5
#define DRAFT_APPROACHES_MIN      2
#define DRAFT_JSON_QUANT          0.01
#define DRAFT_PX_WU               20
#define DRAFT_AXIS_STEPS          24     /* a 15-degree step: turn k * DRAFT_TURN_Q16 / DRAFT_AXIS_STEPS */

/* ---- further drafts (reasons in leaf-01.ASSUMPTIONS.md) ---- */
#define DRAFT_TURN_Q16            65536  /* one full turn in the Q16 angle tables of terrain_noise.c */
#define DRAFT_MIRROR_AXIS_STEP    6      /* mirror needs an axis along x or y: a quarter turn is 6 steps */
#define DRAFT_PATTERN_COUNT       3      /* division patterns: band, ring, two patches */
#define DRAFT_PATTERN_WIDE        1.4    /* the district role a pattern favours claims cells at this weight */
#define DRAFT_EPS                 1.0e-9
#define DRAFT_INF                 1.0e30 /* an unreachable route distance while searching */
#define DRAFT_SOLVE_STEPS         40     /* bisection steps that fit a bulge to a length ratio */
#define DRAFT_BULGE_PTS           7      /* polyline points of a meandering lane, endpoints included */
#define DRAFT_BASE_U              7600   /* a base lies this far from the centre along the axis ... */
#define DRAFT_BASE_U_JIT          900    /* ... plus up to this much */
#define DRAFT_BASE_V              1500   /* sideways wander of a base */
#define DRAFT_GATE_U              4800   /* gate distance from the centre along the axis */
#define DRAFT_GATE_U_JIT          600
#define DRAFT_GATE_V              1000
#define DRAFT_EXP_DU              600    /* expansion site: further out than its gate by this ... */
#define DRAFT_EXP_DU_JIT          900
#define DRAFT_EXP_DV              2600   /* ... and to one side by this */
#define DRAFT_EXP_DV_JIT          800
#define DRAFT_OBJ_DU              1800   /* objective: toward the centre from the defender's base by this */
#define DRAFT_OBJ_DV              2000   /* and to the side opposite its expansion by this */
#define DRAFT_CROSS_T_MIN         0.08   /* crossing starts this fraction of the way gate to gate */
#define DRAFT_CROSS_T_MAX         0.14
#define DRAFT_CROSS_V             600    /* sideways wander of the crossing's near end */
#define DRAFT_CROSS_LEN           2000   /* length of the lane the choke sits on */
#define DRAFT_CROSS_LEN_JIT       500
#define DRAFT_CROSS_TURN_MAX      1      /* the lane leans off the road by up to this many 15-degree steps */
#define DRAFT_CHOKE_FRAC_MIN      0.35   /* where on its lane the gap sits */
#define DRAFT_CHOKE_FRAC_MAX      0.65
#define DRAFT_CHOKE_LEN           900    /* passage length of the gap */
#define DRAFT_WALL_SPAN           1400   /* wall either side of the gap */
#define DRAFT_WAYROUND_MARGIN     0.05   /* way round stays this far inside the bypass band (survives rounding) */
#define DRAFT_VANT_OFFSET         2200   /* vantage stands this far off the crossing lane's midpoint */
#define DRAFT_VANT_R              700
#define DRAFT_PRIZE_SPUR          1500   /* each prize lies this far off the road at the fair point */
#define DRAFT_M_FRAC_MIN          0.12   /* the fair point stays between these fractions of the post-crossing road */
#define DRAFT_M_FRAC_MAX          0.88
#define DRAFT_PAD_BASE_A          700
#define DRAFT_PAD_BASE_B          1100
#define DRAFT_PAD_OBJ             800
#define DRAFT_PAD_RES             500
#define DRAFT_PAD_EXP             600
#define DRAFT_LANE_W_ROUTE        160
#define DRAFT_LANE_W_WAY          120
#define DRAFT_LANE_W_CLIMB        60
#define DRAFT_LANE_W_OBJ          140

#define LK_DRAFT_TABLE(X) \
    X(DRAFT_CANVAS_MIN, DRAFT_CANVAS_MIN) \
    X(DRAFT_CANVAS_MAX, DRAFT_CANVAS_MAX) \
    X(DRAFT_CANVAS_ASSAULT, DRAFT_CANVAS_ASSAULT) \
    X(DRAFT_CHOKE_W_MIN, DRAFT_CHOKE_W_MIN) \
    X(DRAFT_CHOKE_W_MAX, DRAFT_CHOKE_W_MAX) \
    X(DRAFT_BYPASS_MIN, DRAFT_BYPASS_MIN) \
    X(DRAFT_BYPASS_MAX, DRAFT_BYPASS_MAX) \
    X(DRAFT_ASSAULT_CROSSINGS, DRAFT_ASSAULT_CROSSINGS) \
    X(DRAFT_ASSAULT_HEIGHTS, DRAFT_ASSAULT_HEIGHTS) \
    X(DRAFT_ASSAULT_PRIZES, DRAFT_ASSAULT_PRIZES) \
    X(DRAFT_VANTAGE_BANDS_MIN, DRAFT_VANTAGE_BANDS_MIN) \
    X(DRAFT_VANTAGE_BANDS_MAX, DRAFT_VANTAGE_BANDS_MAX) \
    X(DRAFT_MEANDER_MIN, DRAFT_MEANDER_MIN) \
    X(DRAFT_MEANDER_MAX, DRAFT_MEANDER_MAX) \
    X(DRAFT_MEANDER_STEPS, DRAFT_MEANDER_STEPS) \
    X(DRAFT_EQUAL_TOL, DRAFT_EQUAL_TOL) \
    X(DRAFT_CANDIDATES, DRAFT_CANDIDATES) \
    X(DRAFT_APPROACHES_MIN, DRAFT_APPROACHES_MIN) \
    X(DRAFT_JSON_QUANT, DRAFT_JSON_QUANT) \
    X(DRAFT_PX_WU, DRAFT_PX_WU) \
    X(DRAFT_AXIS_STEPS, DRAFT_AXIS_STEPS) \
    X(DRAFT_TURN_Q16, DRAFT_TURN_Q16) \
    X(DRAFT_MIRROR_AXIS_STEP, DRAFT_MIRROR_AXIS_STEP) \
    X(DRAFT_PATTERN_COUNT, DRAFT_PATTERN_COUNT) \
    X(DRAFT_PATTERN_WIDE, DRAFT_PATTERN_WIDE) \
    X(DRAFT_EPS, DRAFT_EPS) \
    X(DRAFT_INF, DRAFT_INF) \
    X(DRAFT_SOLVE_STEPS, DRAFT_SOLVE_STEPS) \
    X(DRAFT_BULGE_PTS, DRAFT_BULGE_PTS) \
    X(DRAFT_BASE_U, DRAFT_BASE_U) \
    X(DRAFT_BASE_U_JIT, DRAFT_BASE_U_JIT) \
    X(DRAFT_BASE_V, DRAFT_BASE_V) \
    X(DRAFT_GATE_U, DRAFT_GATE_U) \
    X(DRAFT_GATE_U_JIT, DRAFT_GATE_U_JIT) \
    X(DRAFT_GATE_V, DRAFT_GATE_V) \
    X(DRAFT_EXP_DU, DRAFT_EXP_DU) \
    X(DRAFT_EXP_DU_JIT, DRAFT_EXP_DU_JIT) \
    X(DRAFT_EXP_DV, DRAFT_EXP_DV) \
    X(DRAFT_EXP_DV_JIT, DRAFT_EXP_DV_JIT) \
    X(DRAFT_OBJ_DU, DRAFT_OBJ_DU) \
    X(DRAFT_OBJ_DV, DRAFT_OBJ_DV) \
    X(DRAFT_CROSS_T_MIN, DRAFT_CROSS_T_MIN) \
    X(DRAFT_CROSS_T_MAX, DRAFT_CROSS_T_MAX) \
    X(DRAFT_CROSS_V, DRAFT_CROSS_V) \
    X(DRAFT_CROSS_LEN, DRAFT_CROSS_LEN) \
    X(DRAFT_CROSS_LEN_JIT, DRAFT_CROSS_LEN_JIT) \
    X(DRAFT_CROSS_TURN_MAX, DRAFT_CROSS_TURN_MAX) \
    X(DRAFT_CHOKE_FRAC_MIN, DRAFT_CHOKE_FRAC_MIN) \
    X(DRAFT_CHOKE_FRAC_MAX, DRAFT_CHOKE_FRAC_MAX) \
    X(DRAFT_CHOKE_LEN, DRAFT_CHOKE_LEN) \
    X(DRAFT_WALL_SPAN, DRAFT_WALL_SPAN) \
    X(DRAFT_WAYROUND_MARGIN, DRAFT_WAYROUND_MARGIN) \
    X(DRAFT_VANT_OFFSET, DRAFT_VANT_OFFSET) \
    X(DRAFT_VANT_R, DRAFT_VANT_R) \
    X(DRAFT_PRIZE_SPUR, DRAFT_PRIZE_SPUR) \
    X(DRAFT_M_FRAC_MIN, DRAFT_M_FRAC_MIN) \
    X(DRAFT_M_FRAC_MAX, DRAFT_M_FRAC_MAX) \
    X(DRAFT_PAD_BASE_A, DRAFT_PAD_BASE_A) \
    X(DRAFT_PAD_BASE_B, DRAFT_PAD_BASE_B) \
    X(DRAFT_PAD_OBJ, DRAFT_PAD_OBJ) \
    X(DRAFT_PAD_RES, DRAFT_PAD_RES) \
    X(DRAFT_PAD_EXP, DRAFT_PAD_EXP) \
    X(DRAFT_LANE_W_ROUTE, DRAFT_LANE_W_ROUTE) \
    X(DRAFT_LANE_W_WAY, DRAFT_LANE_W_WAY) \
    X(DRAFT_LANE_W_CLIMB, DRAFT_LANE_W_CLIMB) \
    X(DRAFT_LANE_W_OBJ, DRAFT_LANE_W_OBJ)

/* ---- kit-internal declarations ---- */

/* return codes of om_lk_generate (layout_kit.h) */
enum { LK_RC_OK = 0, LK_RC_NULL_OUT = -1, LK_RC_ARCH = -2, LK_RC_RANGE = -3 };

/* one stream per concern, so a change in one piece never shifts the draws of another */
enum { LK_S_DISTRICT = 0, LK_S_SIDE_A, LK_S_SIDE_B, LK_S_PIECES, LK_S_MEANDER, LK_S_COUNT };

typedef struct lk_rng { uint64_t s; } lk_rng;

void     lk_rng_seed(lk_rng *r, uint64_t seed, int32_t cand, int32_t concern);
uint64_t lk_rng_next(lk_rng *r);
double   lk_rng_unit(lk_rng *r);                              /* [0, 1) */
double   lk_rng_range(lk_rng *r, double lo, double hi);       /* [lo, hi) */
int32_t  lk_rng_int(lk_rng *r, int32_t lo, int32_t hi);       /* lo..hi inclusive */
double   lk_rng_sign(lk_rng *r);                              /* -1.0 or 1.0 */

/* local frame: u along the axis from side A toward side B, v sideways; u, v in wu at the default canvas */
typedef struct lk_frame { double cx, cy, ux, uy, s; } lk_frame;
void lk_pt(const lk_frame *f, double u, double v, double *x, double *y);

/* the ground of one side, in local coordinates: base, gate, expansion site */
typedef struct lk_ground { double bu, bv, gu, gv, eu, ev; int32_t landform; } lk_ground;

/* everything one candidate needs while it is built */
typedef struct lk_ctx {
    om_lk_layout *l;
    lk_frame f;
    int32_t mode, pattern;
    lk_rng st[LK_S_COUNT];
    lk_ground ga, gb;
    int32_t n_a, n_b, n_o, n_ga, n_gb, n_j1, n_j2, n_m, n_v;   /* node indices */
    int32_t lane_cross, lane_way, lane_mb;                      /* lane indices */
    double  m_pref;                                             /* side B's preferred meander (separate) */
    double  way_sign, mb_sign;                                  /* which side the way round and the meander bulge to */
} lk_ctx;

/* layout_kit_pieces.c: the six kit pieces and the request list; each returns 0, or -1 when a cap is exceeded */
int32_t lk_add_node(om_lk_layout *l, double x, double y, int32_t place);
int32_t lk_add_place(om_lk_layout *l, int32_t kind, int32_t side, double x, double y, double pad_r, int32_t piece);
int32_t lk_add_lane(om_lk_layout *l, int32_t kind, int32_t a, int32_t b, double width);
void    lk_set_bulge(om_lk_layout *l, int32_t lane, double ratio, double sign);
int32_t lk_piece_home_ground(lk_ctx *c, int32_t side);
int32_t lk_piece_objective_ground(lk_ctx *c);
int32_t lk_piece_crossing(lk_ctx *c);
int32_t lk_piece_prize(lk_ctx *c, double meander);
int32_t lk_piece_heights(lk_ctx *c);
int32_t lk_build_requests(lk_ctx *c);

/* layout_kit_graph.c: the route graph, built from lanes alone */
double lk_lane_len(const om_lk_layout *l, int32_t lane);
void   lk_dijkstra(const om_lk_layout *l, int32_t src, int32_t skip_lane, double *dist);
int32_t lk_checks_passed(uint32_t checks);

#endif /* OM_LAYOUT_DRAFTS_H */
