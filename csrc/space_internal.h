/* csrc/space_internal.h -- VG K-d2: the stage interface of the space field generator (lane D, pieces D2 to D4).
 * Internal: declared here only, never in ouroboros_sim.h. Derived from the data flow of
 * scenes/mockups/landscape/field_map_space.gd generate():
 *   noise (D1: om_space_noise_layer) -> om_space_plates_build (D2) -> om_space_raster (D3) -> om_space_carve (D3/D4)
 *   -> D4 copies masks and polygons into om_space_field_state (om_internal.h) and writes blocked_bits.
 * Stage structs are large and transient: generate heap-allocates them (malloc/free, no file-static state) and frees them
 * before it returns. The stored layout is om_space_field_state in om_internal.h: packed masks per layer plus the polygon
 * list (layer, kind, n_pts, xy); it is a pure function of (seed, canvas, density) and is neither saved nor hashed. */
#ifndef OM_SPACE_INTERNAL_H
#define OM_SPACE_INTERNAL_H

#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stdint.h>

#define OM_SPACE_KIND_PLATE 0  /* an ordinary plate (a jittered Voronoi cell) */
#define OM_SPACE_KIND_MASS 1   /* part of the one large mass a layer may grow (MASS_CHANCE) */
#define OM_SPACE_KIND_RUBBLE 2 /* a small rubble cell inside a cleared area; becomes cover */
#define OM_SPACE_MAX_LINKS 16384 /* adjacency pairs: a planar cell diagram has at most 3 per polygon; 4096 polys * 3 = 12288, up to a power of two */
#define OM_SPACE_NO_REGION 0xFFFFu /* region id of a polygon not yet labelled */
#define OM_SPACE_OBJECTIVE_CX 120u /* the main region holds layer 0 at this cell (the mission objective, field_map_space.gd) */
#define OM_SPACE_OBJECTIVE_CY 120u

/* One polygon of one layer. Counter-clockwise, simple, on the canvas, 3..OM_SPACE_FIELD_MAX_PTS points. */
typedef struct om_space_plate {
    uint8_t layer;     /* 0..4 */
    uint8_t kind;      /* OM_SPACE_KIND_* */
    uint8_t n_pts;     /* vertex count */
    uint8_t dropped;   /* 1 when carving removed it (open water); a dropped plate is not copied to the stored list */
    uint16_t id;       /* plate id, unique within the layer; index into the layer's adjacency */
    uint16_t region;   /* connected-region id after carve, OM_SPACE_NO_REGION before */
    double xy[2 * OM_SPACE_FIELD_MAX_PTS]; /* x0,y0,x1,y1,... in wu */
} om_space_plate;

/* Adjacent plates of one layer (shared edge): a, b are plate ids of that layer, a < b. */
typedef struct om_space_link {
    uint8_t layer;
    uint16_t a, b;
} om_space_link;

/* Output of om_space_plates_build. */
typedef struct om_space_plates {
    uint32_t n_plates;                                  /* entries used in plates[] */
    uint32_t n_links;                                   /* entries used in links[] */
    uint32_t per_layer[OM_SPACE_FIELD_LAYERS];          /* polygons per layer (plates, mass and rubble) */
    om_space_plate plates[OM_SPACE_FIELD_MAX_POLYS];    /* grouped by layer, ascending layer */
    om_space_link links[OM_SPACE_MAX_LINKS];
} om_space_plates;

/* Output of om_space_raster (type om_space_cells), and the working state of om_space_carve. Cells are row-major, i = cy * 240 + cx. */
typedef struct om_space_raster {
    uint8_t mask[OM_SPACE_FIELD_LAYERS][OM_SPACE_FIELD_CELLS];  /* 1 blocked, 0 open (the blocked_bits sense) */
    uint16_t owner[OM_SPACE_FIELD_LAYERS][OM_SPACE_FIELD_CELLS]; /* plate id covering the cell, 0xFFFF when none (pocket-filled or open) */
    uint8_t kind[OM_SPACE_FIELD_LAYERS][OM_SPACE_FIELD_CELLS];   /* OM_SPACE_KIND_* of the owner; meaningful only where owner != 0xFFFF */
} om_space_cells;

/* D2. Builds every layer's plate polygons from (seed, canvas, density) into out (zeroed first by the callee).
 * density is clamped to 0..90. Returns 0 ok, nonzero when canvas is not OM_SPACE_FIELD_CANVAS_WU or out is NULL. */
int om_space_plates_build(uint32_t seed, double canvas, double density, om_space_plates *out);

/* VG-D8. om_space_plates_build with the clearing nodes: node_xy holds n_nodes x,y pairs (faction 0 anchor, faction 1 anchor,
 * objective, extras; below OM_SPACE_FIELD_MIN_NODES the old diagonal nodes), node_radius[i] the clear radius at node i (0 = the
 * default 600 wu). om_space_plates_build is this call with no nodes. */
int om_space_plates_build_nodes(uint32_t seed, double canvas, double density, const double *node_xy, const double *node_radius,
                                uint32_t n_nodes, om_space_plates *out);

/* D3. Rasterises the non-dropped plates into masks and owner/kind arrays at cell_wu (OM_SPACE_FIELD_CELL_WU, 100) per cell,
 * and fills pockets under the mockup's MIN_POCKET_CELLS. Writes only raster. Returns 0 ok, nonzero on a bad argument. */
int om_space_raster(const om_space_plates *plates, double cell_wu, om_space_cells *raster);

/* D3/D4. The fill-and-carve join: labels the open regions (300 wu passage, six-neighbour flood), widens or drops plates to
 * join cut-off regions to the main region (the one holding layer 0 at objective cell obj_cx, obj_cy), updating raster and
 * plates (dropped, region). no_carve nonzero skips the join (debug inject OM_BUG_SPACE_NO_CARVE). Returns the number of
 * regions still unreachable from the main region (field_map_space.gd regions_unreachable_after), 0 when fully joined. */
int om_space_carve(om_space_plates *plates, om_space_cells *raster, uint32_t obj_cx, uint32_t obj_cy, int no_carve);

#endif
