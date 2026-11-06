/* Layout kit: a layout made from a kit of situation pieces (E-17 S-112, S-113; story S-247).
 * Contract of the cascade docs/northstar/plans/cascades/layout-kit-assault/ (spec.md).
 * Internal until the contract story S-249: not declared in ouroboros_sim.h, not on the pipe.
 * Self-contained on purpose (no include of layout_internal.h: the sibling places engine owns its own names).
 * Every figure is a DRAFT_ macro of csrc/layout_drafts.h (written by leaf 1); array sizes here are drafts too. */
#ifndef OM_LAYOUT_KIT_H
#define OM_LAYOUT_KIT_H

#include <stdint.h>

#define OM_LK_GRID          8     /* districts per side of the grid */
#define OM_LK_MAX_PLACES    32
#define OM_LK_MAX_NODES     96
#define OM_LK_MAX_LANES     96
#define OM_LK_LANE_PTS      16    /* polyline points per lane, endpoints included */
#define OM_LK_MAX_CHOKES    8
#define OM_LK_MAX_VANTAGES  8
#define OM_LK_MAX_REQUESTS  64
#define OM_LK_NAME_LEN      16

/* archetype ids are csrc/mission.c's OM_MISSION_ARCH_* (0..9); round A accepts only ASSAULT */
#define OM_LK_ARCH_ASSAULT  3

typedef enum om_lk_sides_mode { OM_LK_SIDES_MIRROR = 0, OM_LK_SIDES_ROTATE = 1, OM_LK_SIDES_SEPARATE = 2 } om_lk_sides_mode;

typedef enum om_lk_place_kind {
    OM_LK_PLACE_OBJECTIVE = 0,
    OM_LK_PLACE_BASE_HOME = 1,      /* a grown town (the defender) */
    OM_LK_PLACE_BASE_FORWARD = 2,   /* a camp (the attacker) */
    OM_LK_PLACE_RESOURCE = 3,       /* significant resource */
    OM_LK_PLACE_EXPANSION = 4,
    OM_LK_PLACE_KIND_COUNT = 5
} om_lk_place_kind;

typedef enum om_lk_lane_kind {
    OM_LK_LANE_ROUTE = 0, OM_LK_LANE_WAY_ROUND = 1, OM_LK_LANE_CLIMB = 2,
    OM_LK_LANE_HIDDEN = 3, OM_LK_LANE_OBJECTIVE_ROUTE = 4, OM_LK_LANE_KIND_COUNT = 5
} om_lk_lane_kind;

typedef enum om_lk_landform {
    OM_LK_LF_NONE = 0, OM_LK_LF_COAST, OM_LK_LF_CANYON, OM_LK_LF_MESA, OM_LK_LF_RIDGE, OM_LK_LF_HILL,
    OM_LK_LF_PLATEAU, OM_LK_LF_BASIN, OM_LK_LF_BEND, OM_LK_LF_FORD, OM_LK_LF_PASS, OM_LK_LF_GATE,
    OM_LK_LF_COUNT
} om_lk_landform;

typedef enum om_lk_req_kind { OM_LK_REQ_PAD = 0, OM_LK_REQ_CHOKE, OM_LK_REQ_VANTAGE, OM_LK_REQ_ROUTE, OM_LK_REQ_LANDFORM, OM_LK_REQ_KIND_COUNT } om_lk_req_kind;
typedef enum om_lk_req_mode { OM_LK_MODE_KEEP_OPEN = 0, OM_LK_MODE_KEEP_CLOSED, OM_LK_MODE_HEIGHT, OM_LK_MODE_ROOM, OM_LK_MODE_NUMBER, OM_LK_MODE_COUNT } om_lk_req_mode;

/* the kit pieces of round A (S-112 R-112-03); the index is the place's or choke's `piece` */
typedef enum om_lk_piece {
    OM_LK_PIECE_NONE = 0, OM_LK_PIECE_HOME_GROUND, OM_LK_PIECE_GATE, OM_LK_PIECE_CROSSING,
    OM_LK_PIECE_HEIGHTS, OM_LK_PIECE_PRIZE, OM_LK_PIECE_OBJECTIVE_GROUND, OM_LK_PIECE_COUNT
} om_lk_piece;

/* check bits in om_lk_layout.checks (S-112 R-112-05) */
#define OM_LK_CHECK_CONNECTED   (1u << 0)
#define OM_LK_CHECK_FAIRNESS    (1u << 1)
#define OM_LK_CHECK_BYPASS      (1u << 2)
#define OM_LK_CHECK_APPROACHES  (1u << 3)
#define OM_LK_CHECK_CHOKES      (1u << 4)
#define OM_LK_CHECK_BOUNDS      (1u << 5)
#define OM_LK_CHECKS_ALL        0x3Fu

/* district role ids in om_lk_layout.district[row][col] */
#define OM_LK_DIST_NONE 0
#define OM_LK_DIST_HOME_A 1
#define OM_LK_DIST_HOME_B 2
#define OM_LK_DIST_NEAR_A 3
#define OM_LK_DIST_NEAR_B 4
#define OM_LK_DIST_CONTESTED 5
#define OM_LK_DIST_OBJECTIVE 6

typedef struct om_lk_place {
    int32_t kind;     /* om_lk_place_kind */
    int32_t side;     /* 0 = A (the attacker), 1 = B (the defender), -1 = neutral */
    double  x, y;
    double  pad_r;    /* radius of ground the landscape keeps level for it */
    int32_t piece;    /* om_lk_piece */
    int32_t node;     /* index into nodes[] */
} om_lk_place;

typedef struct om_lk_node { double x, y; int32_t place; /* index into places[] or -1 */ } om_lk_node;

typedef struct om_lk_lane {
    int32_t kind;           /* om_lk_lane_kind */
    int32_t a, b;           /* node indices; pts[0] is node a, pts[n_pts-1] is node b */
    double  width;          /* wu */
    int32_t n_pts;
    double  px[OM_LK_LANE_PTS], py[OM_LK_LANE_PTS];
} om_lk_lane;

typedef struct om_lk_choke {
    double  x, y, width, length;
    int32_t axis_k;         /* the gap's axis in 15-degree steps, 0..11 */
    double  wall_span;      /* length of wall either side of the gap */
    double  frac;           /* position 0..1 along its lane */
    int32_t lane;           /* the lane it sits on */
    int32_t landform;       /* om_lk_landform */
    int32_t piece;
} om_lk_choke;

typedef struct om_lk_vantage {
    double  x, y, radius;
    int32_t height_bands;   /* 1..3 */
    int32_t overlooks;      /* lane index */
    int32_t climb[2];       /* two climb lane indices */
    int32_t landform;
    int32_t piece;
} om_lk_vantage;

/* the B3 seam: what the landscape engine is asked to make real (spec.md "The request list") */
typedef struct om_lk_request {
    int32_t kind;           /* om_lk_req_kind */
    int32_t mode;           /* om_lk_req_mode */
    int32_t piece;          /* kit piece index, 0 none */
    char    name[OM_LK_NAME_LEN];   /* "base_a", "base_b", "objective", "site_0" ... */
    double  x, y, r;        /* centre; pad or vantage radius */
    double  w, len, span, frac;     /* choke: gap width, length, wall span, position 0..1 along its lane */
    int32_t axis_k;         /* 15-degree step */
    double  height_bands;
    int32_t side;           /* +1 / -1 for a vantage, else 0 */
    int32_t landform;       /* om_lk_landform */
} om_lk_request;

typedef struct om_lk_fairness {
    double dist_a_objective, dist_b_objective;   /* route distance from each side's base, -1 when unreachable */
    double dist_a_res[2], dist_b_res[2];         /* the two significant resources */
} om_lk_fairness;

typedef struct om_lk_layout {
    uint64_t seed;
    int32_t  archetype, sides_mode;
    double   canvas;
    int32_t  candidate;     /* which of the DRAFT_CANDIDATES made from the seed was kept */
    int32_t  n_places, n_nodes, n_lanes, n_chokes, n_vantages, n_requests;
    om_lk_place   places[OM_LK_MAX_PLACES];
    om_lk_node    nodes[OM_LK_MAX_NODES];
    om_lk_lane    lanes[OM_LK_MAX_LANES];
    om_lk_choke   chokes[OM_LK_MAX_CHOKES];
    om_lk_vantage vantages[OM_LK_MAX_VANTAGES];
    om_lk_request requests[OM_LK_MAX_REQUESTS];
    om_lk_fairness fairness;
    uint32_t checks;        /* OM_LK_CHECK_* bits that PASS */
    int8_t   district[OM_LK_GRID][OM_LK_GRID];
    int32_t  route_count;   /* number of lanes of kind route, way_round or objective_route */
} om_lk_layout;

/* Returns 0 and fills *out (zeroed first), or: -1 for a NULL out; -2 for an archetype outside 0..9 or not yet
 * built (round A: only OM_LK_ARCH_ASSAULT); -3 for a canvas outside DRAFT_CANVAS_MIN..DRAFT_CANVAS_MAX or a
 * sides_mode outside 0..2. Sentinel body returns -1 until leaf 1 lands. Deterministic (spec.md "Determinism"). */
int om_lk_generate(uint64_t seed, int32_t archetype, double canvas, int32_t sides_mode, om_lk_layout *out);

/* Recomputes fairness and checks from places, nodes, lanes, chokes and vantages only (the graph is rebuilt from
 * the lanes), so a layout edited after generation is judged on what it now is. Sets out->fairness, out->checks,
 * out->route_count. NULL is ignored. */
void om_lk_run_checks(om_lk_layout *l);

/* Names for the JSON and the picture. domain: 0 place kind, 1 lane kind, 2 landform, 3 request kind,
 * 4 request mode, 5 piece. NULL for an id out of range. Strings are lower-case snake_case, listed in spec.md. */
const char *om_lk_name(int32_t domain, int32_t id);

/* The drafts table (layout_drafts.h X-macro) as data, so the CLI emits the `drafts` block and can never drift
 * from the header. i in 0..count-1, in table order. Name is the macro name, e.g. "DRAFT_EQUAL_TOL". */
int32_t     om_lk_draft_count(void);
const char *om_lk_draft_name(int32_t i);
double      om_lk_draft_value(int32_t i);

#endif /* OM_LAYOUT_KIT_H */
