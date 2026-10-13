#include "pipe_internal.h"


/* Mirrors OM_TERRAIN_CELL_WU in om_internal.h (not visible to the pipe). */
#define PIPE_TERRAIN_CELL_WU 100.0

void handle_terrain_generate(const char *json) {
    if (!W) {
        write_error("terrain_generate", "no world");
        return;
    }
    int64_t seed;
    double canvas;
    if (!get_i64(json, "seed", &seed) || !get_f64(json, "canvas", &canvas)) {
        write_error("terrain_generate", "missing field");
        return;
    }
    int code = om_terrain_generate(W, (uint64_t)seed, canvas, canvas);
    uint32_t cw = 0, ch = 0;
    double bh[5];
    uint32_t nb = 0;
    if (code == 0) {
        om_terrain_cells(W, &cw, &ch);
        nb = om_terrain_band_heights(W, bh, 5);
    }
    jbuf j;
    jb_init(&j);
    jb_raw(&j, "{\"type\":\"terrain_ack\",\"name\":\"terrain_generate\",\"code\":");
    jb_int(&j, code);
    jb_raw(&j, ",\"cells_w\":");
    jb_uint(&j, cw);
    jb_raw(&j, ",\"cells_h\":");
    jb_uint(&j, ch);
    jb_raw(&j, ",\"band_heights\":[");
    for (uint32_t i = 0; i < nb; i++) {
        if (i) jb_putc(&j, ',');
        jb_double(&j, bh[i]);
    }
    jb_raw(&j, "]}");
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

void handle_lots_dump(void) {
    if (!W) {
        write_error("lots_dump", "no world");
        return;
    }
    jbuf j;
    jb_init(&j);
    jb_raw(&j, "{\"type\":\"lots\",\"lots\":[");
    uint32_t n = om_lot_count(W);
    int wrote = 0;
    for (uint32_t i = 0; i < n; i++) {
        om_lot l;
        if (om_lot_get_at(W, i, &l) != 0) continue;
        if (wrote) jb_putc(&j, ',');
        wrote = 1;
        write_lot_row(&j, &l);
    }
    jb_raw(&j, "]}");
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

void handle_terrain_dump(void) {
    if (!W) {
        write_error("terrain_dump", "no world");
        return;
    }
    if (!om_terrain_present(W)) {
        write_error("terrain_dump", "no terrain");
        return;
    }
    uint32_t cw = 0, ch = 0;
    om_terrain_cells(W, &cw, &ch);
    uint32_t n = cw * ch;
    uint8_t *bands = malloc(n ? n : 1);
    uint8_t *walk = malloc(n ? n : 1);
    n = om_terrain_dump_bands(W, bands, n);
    for (uint32_t cy = 0; cy < ch; cy++)
        for (uint32_t cx = 0; cx < cw; cx++)
            walk[cy * cw + cx] = (uint8_t)(om_terrain_walkable_at(W, (cx + 0.5) * PIPE_TERRAIN_CELL_WU,
                                                                  (cy + 0.5) * PIPE_TERRAIN_CELL_WU) != 0);
    jbuf j;
    jb_init(&j);
    jb_raw(&j, "{\"type\":\"terrain\",\"cells_w\":");
    jb_uint(&j, cw);
    jb_raw(&j, ",\"cells_h\":");
    jb_uint(&j, ch);
    jb_raw(&j, ",\"bands\":");
    hex_put(&j, bands, n);
    jb_raw(&j, ",\"walkable\":");
    hex_put(&j, walk, cw * ch);
    {
        int32_t *hv = malloc(sizeof *hv * (n ? n : 1));
        uint8_t *hb = malloc(4 * (size_t)(n ? n : 1));
        uint32_t nh = om_terrain_get_heights(W, hv, n);
        for (uint32_t i = 0; i < nh; i++) {
            uint32_t u = (uint32_t)hv[i];
            for (int b = 0; b < 4; b++) hb[4 * i + b] = (uint8_t)(u >> (8 * b));
        }
        jb_raw(&j, ",\"heights\":");
        hex_put(&j, hb, 4 * nh);
        free(hv);
        free(hb);
    }
    {
        double lf[5];
        uint32_t nl = om_terrain_band_heights(W, lf, 5);
        jb_raw(&j, ",\"layer_floors_wu\":[");
        for (uint32_t i = 0; i < nl; i++) {
            if (i) jb_putc(&j, ',');
            jb_double(&j, lf[i]);
        }
        jb_raw(&j, "],\"flyer_types\":[");
        int first = 1;
        for (int t = 0; t < g_roster_types; t++) {
            if (om_unit_profile_movement_kind(W, t) != OM_MOVE_FLYING) continue;
            if (!first) jb_putc(&j, ',');
            first = 0;
            jb_uint(&j, (uint32_t)t);
        }
        jb_putc(&j, ']');
    }
    jb_raw(&j, ",\"slopes\":[");
    uint32_t ns = om_terrain_slope_count(W);
    for (uint32_t i = 0; i < ns; i++) {
        om_slope s;
        if (om_terrain_slope_get(W, i, &s) != 0) continue;
        if (i) jb_putc(&j, ',');
        const char *k[7] = {"x0", "y0", "x1", "y1", "mx", "my", "length"};
        const double v[7] = {s.x0, s.y0, s.x1, s.y1, s.mx, s.my, s.length};
        jb_putc(&j, '{');
        for (int f = 0; f < 7; f++) {
            jb_key(&j, k[f]);
            jb_double(&j, v[f]);
            jb_putc(&j, ',');
        }
        jb_raw(&j, "\"lower_band\":");
        jb_int(&j, s.lower_band);
        jb_raw(&j, ",\"upper_band\":");
        jb_int(&j, s.upper_band);
        jb_putc(&j, '}');
    }
    jb_raw(&j, "]}");
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
    free(bands);
    free(walk);
}

void handle_terrain_probe(const char *json) {
    if (!W) {
        write_error("terrain_probe", "no world");
        return;
    }
    if (!om_terrain_present(W)) {
        write_error("terrain_probe", "no terrain");
        return;
    }
    double x, y;
    int64_t layer = 0;
    if (!get_f64(json, "x", &x) || !get_f64(json, "y", &y)) {
        write_error("terrain_probe", "missing field");
        return;
    }
    get_i64(json, "layer", &layer);
    jbuf j;
    jb_init(&j);
    jb_raw(&j, "{\"type\":\"terrain_probe\",\"x\":");
    jb_double(&j, x);
    jb_raw(&j, ",\"y\":");
    jb_double(&j, y);
    jb_raw(&j, ",\"height\":");
    jb_double(&j, om_terrain_height_at(W, x, y));
    jb_raw(&j, ",\"band\":");
    jb_int(&j, om_terrain_band_at(W, x, y));
    jb_raw(&j, ",\"walkable\":");
    jb_int(&j, om_terrain_walkable_at(W, x, y) != 0);
    jb_raw(&j, ",\"ground\":");
    jb_int(&j, om_terrain_ground_at(W, (int)layer, x, y));
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}
