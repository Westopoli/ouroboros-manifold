/* csrc/space_field.c -- E-17 S-246 (R-246-01), E-01 R-001-04: the space mission's five open-or-blocked layers.
 * K-d contract piece: the bodies below are PLACEHOLDER plates (a few seeded rectangles per layer), so the verb, the
 * bridge and the routing mask can be built against a real field. Lane D replaces generate with the
 * scenes/mockups/landscape/field_map_space.gd port; the getters and the state in om_internal.h stay.
 * See also: om_map_block_rect in csrc/tactical_mapgen.c, whose route grid mission_begin clears (om_map_clear). */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "space_internal.h"
#include <stddef.h>
#include <string.h>

#define SF_PLATES_PER_LAYER 4 /* placeholder count */
#define SF_PLATE_MIN_CELLS 6 /* placeholder half-sizes, cells */
#define SF_PLATE_SPAN_CELLS 10
#define SF_KIND_PLATE 0
#define SF_KIND_MASS 1
#define SF_KIND_RUBBLE 2
#define SF_RECT_PTS 4
#define SF_MASS_INDEX 2
#define SF_RUBBLE_INDEX 3
#define SF_SPLIT_A 0x9E3779B97F4A7C15ULL
#define SF_SPLIT_B 0xBF58476D1CE4E5B9ULL
#define SF_SPLIT_C 0x94D049BB133111EBULL
#define SF_SHIFT_A 30
#define SF_SHIFT_B 27
#define SF_SHIFT_C 31
#define SF_HIGH_SHIFT 33
#define SF_BYTE_SHIFT 3
#define SF_BIT_MASK 7u

static uint64_t sf_next(uint64_t *s) {
    uint64_t z = (*s += SF_SPLIT_A);
    z = (z ^ (z >> SF_SHIFT_A)) * SF_SPLIT_B;
    z = (z ^ (z >> SF_SHIFT_B)) * SF_SPLIT_C;
    return z ^ (z >> SF_SHIFT_C);
}

static uint32_t sf_range(uint64_t *s, uint32_t n) {
    return (uint32_t)((sf_next(s) >> SF_HIGH_SHIFT) % n);
}

int om_space_field_generate(om_world *w, uint32_t seed, double canvas_w, double canvas_h, double density) {
    om_space_field_state *f;
    uint64_t rs = (uint64_t)seed;
    (void)density; /* STUB K-d2: D4 passes it to om_space_plates_build */
    if (!w || canvas_w != OM_SPACE_FIELD_CANVAS_WU || canvas_h != OM_SPACE_FIELD_CANVAS_WU) return -1;
    f = &w->space_field;
    memset(f, 0, sizeof *f);
    f->present = 1;
    f->seed = seed;
    for (uint32_t k = 0; k < OM_SPACE_FIELD_LAYERS; k++) {
        for (uint32_t n = 0; n < SF_PLATES_PER_LAYER; n++) {
            uint32_t half = SF_PLATE_MIN_CELLS + sf_range(&rs, SF_PLATE_SPAN_CELLS);
            uint32_t cx = half + sf_range(&rs, OM_SPACE_FIELD_SIDE - 2 * half);
            uint32_t cy = half + sf_range(&rs, OM_SPACE_FIELD_SIDE - 2 * half);
            om_space_field_poly *p = &f->polys[f->n_polys++];
            double x0 = (double)(cx - half) * OM_SPACE_FIELD_CELL_WU, x1 = (double)(cx + half) * OM_SPACE_FIELD_CELL_WU;
            double y0 = (double)(cy - half) * OM_SPACE_FIELD_CELL_WU, y1 = (double)(cy + half) * OM_SPACE_FIELD_CELL_WU;
            p->layer = (uint8_t)k;
            p->kind = n == SF_MASS_INDEX ? SF_KIND_MASS : (n == SF_RUBBLE_INDEX ? SF_KIND_RUBBLE : SF_KIND_PLATE);
            p->n_pts = SF_RECT_PTS;
            {
                const double cxs[SF_RECT_PTS] = {x0, x1, x1, x0}, cys[SF_RECT_PTS] = {y0, y0, y1, y1};
                for (uint32_t c = 0; c < SF_RECT_PTS; c++) {
                    p->xy[2u * c] = cxs[c];
                    p->xy[2u * c + 1u] = cys[c];
                }
            }
            for (uint32_t y = cy - half; y < cy + half; y++)
                for (uint32_t x = cx - half; x < cx + half; x++) {
                    uint32_t i = y * OM_SPACE_FIELD_SIDE + x;
                    f->mask[k][i >> SF_BYTE_SHIFT] = (uint8_t)(f->mask[k][i >> SF_BYTE_SHIFT] | (1u << (i & SF_BIT_MASK)));
                }
            (void)om_map_block_rect(w, x0, y0, x1, y1, k, k);
        }
    }
    return 0;
}

int om_space_field_present(const om_world *w) {
    return w && w->space_field.present;
}

uint32_t om_space_field_get_mask(const om_world *w, uint32_t layer, uint8_t *out, uint32_t cap) {
    if (!w || !out || !w->space_field.present || layer >= OM_SPACE_FIELD_LAYERS || cap < OM_SPACE_FIELD_CELLS) return 0;
    for (uint32_t i = 0; i < OM_SPACE_FIELD_CELLS; i++)
        out[i] = (uint8_t)((w->space_field.mask[layer][i >> SF_BYTE_SHIFT] >> (i & SF_BIT_MASK)) & 1u);
    return OM_SPACE_FIELD_CELLS;
}

void om_space_field_clear(om_world *w) {
    if (w) memset(&w->space_field, 0, sizeof w->space_field);
}

uint32_t om_space_field_poly_count(const om_world *w) {
    return w && w->space_field.present ? w->space_field.n_polys : 0;
}

uint32_t om_space_field_poly_get(const om_world *w, uint32_t i, uint32_t *layer, uint32_t *kind, double *xy, uint32_t cap_pts) {
    const om_space_field_poly *p;
    if (!w || !w->space_field.present || i >= w->space_field.n_polys) return 0;
    p = &w->space_field.polys[i];
    if (cap_pts < p->n_pts) return 0;
    if (layer) *layer = p->layer;
    if (kind) *kind = p->kind;
    if (xy) memcpy(xy, p->xy, sizeof(double) * 2u * p->n_pts);
    return p->n_pts;
}
