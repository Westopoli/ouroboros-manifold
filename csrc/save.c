/* csrc/save.c — S-111 saving (T2c). om_save_state_size/om_save_state_write/
 * om_load_state_read: the whole binary save contract. Moved out of
 * generational.c's STUBs (B7-6) once F2j-2/om_internal.h had the format
 * constants and the per-slot save hooks to build against.
 *
 * Format (see the piece report for the full field-by-field layout): magic
 * (OM_SAVE_MAGIC, 4 bytes) + format version (u32), then every om_world
 * field the state checksum covers or that feeds a future tick's math
 * (tick, seed, RNG state, world serial, region count, every per-region
 * field, ownership/held-since, edges, the faction table incl. stances,
 * lifecycle window counters, the two persistent pending queues --
 * event_queue and telegraphs), then one length-prefixed blob per om_world
 * module slot (om_internal.h) in a fixed order -- 0 bytes when that
 * slot's _size hook is NULL. F2m wires the events and generational hooks
 * onto every world at om_world_new (csrc/region.c), so those two slots
 * round-trip (events.c's om_chain_counter among them) even on a world that
 * never otherwise touched the module; the other eight slots stay NULL,
 * i.e. empty, until their own module lands its hooks.
 *
 * Everything is explicit little-endian, fixed width, no struct memcpy, no
 * padding: om_save_writer/om_save_reader below pack/unpack one scalar at a
 * time through OM_SAVE_BYTE_BITS/OM_SAVE_BYTE_MASK so no shift/mask is a
 * bare literal (alg_constants.py --lint csrc). Doubles go through their
 * IEEE-754 bit pattern (memcpy of a scalar reinterpret, not a struct).
 *
 * om_load_state_read validates the ENTIRE buffer (magic, version, every
 * count against its compile-time cap, every blob's bounds, and -- F2m --
 * every module slot's own read hook run against a scratch shadow world,
 * not the destination) before it is run a second time to actually apply --
 * so a refused load never touches the destination world (R-111-03), even
 * when the refusal is a module's own semantic failure on an
 * otherwise well-formed slot blob, not just a top-level bounds/cap miss.
 * Both passes walk the identical field sequence, so a bounds/cap failure
 * caught in the first pass is guaranteed to be caught at the same offset
 * in the second (or never reached, since the first pass returning ok
 * means every subsequent read in the second pass is
 * in-bounds). */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include "economy_internal.h"
#include <stdlib.h>
#include <string.h>

/* ---------------------------------------------------------------- writer */

typedef struct {
    uint8_t *buf;   /* NULL: size-only pass, no bytes written, pos still counted */
    uint32_t cap;
    uint32_t pos;
} sv_writer;

static void sv_put_bytes(sv_writer *sw, const uint8_t *src, uint32_t n) {
    if (sw->buf && sw->pos <= sw->cap && n <= sw->cap - sw->pos) {
        memcpy(sw->buf + sw->pos, src, n);
    }
    sw->pos += n;
}

static void sv_put_uint(sv_writer *sw, uint64_t v, uint32_t width) {
    uint8_t tmp[sizeof(uint64_t)];
    for (uint32_t i = 0; i < width; i++) {
        tmp[i] = (uint8_t)((v >> (OM_SAVE_BYTE_BITS * i)) & OM_SAVE_BYTE_MASK);
    }
    sv_put_bytes(sw, tmp, width);
}

static void sv_put_u8(sv_writer *sw, uint8_t v)   { sv_put_uint(sw, v, (uint32_t)sizeof(uint8_t)); }
static void sv_put_u32(sv_writer *sw, uint32_t v) { sv_put_uint(sw, v, (uint32_t)sizeof(uint32_t)); }
static void sv_put_u64(sv_writer *sw, uint64_t v) { sv_put_uint(sw, v, (uint32_t)sizeof(uint64_t)); }
static void sv_put_i32(sv_writer *sw, int32_t v)  { sv_put_uint(sw, (uint32_t)v, (uint32_t)sizeof(int32_t)); }
static void sv_put_i64(sv_writer *sw, int64_t v)  { sv_put_uint(sw, (uint64_t)v, (uint32_t)sizeof(int64_t)); }

static uint64_t sv_f64_bits(double v) {
    uint64_t bits;
    memcpy(&bits, &v, sizeof(bits));
    return bits;
}

static void sv_put_f64(sv_writer *sw, double v) { sv_put_u64(sw, sv_f64_bits(v)); }

/* ---------------------------------------------------------------- reader */

typedef struct {
    const uint8_t *buf;
    uint32_t len;
    uint32_t pos;
    int ok;
} sv_reader;

static const uint8_t *sv_get_span(sv_reader *sr, uint32_t n) {
    if (!sr->ok) return NULL;
    if (n > sr->len || sr->pos > sr->len - n) {
        sr->ok = 0;
        return NULL;
    }
    const uint8_t *p = sr->buf + sr->pos;
    sr->pos += n;
    return p;
}

static uint64_t sv_get_uint(sv_reader *sr, uint32_t width) {
    const uint8_t *p = sv_get_span(sr, width);
    if (!p) return 0;
    uint64_t v = 0;
    for (uint32_t i = 0; i < width; i++) {
        v |= ((uint64_t)p[i]) << (OM_SAVE_BYTE_BITS * i);
    }
    return v;
}

static uint8_t  sv_get_u8(sv_reader *sr)  { return (uint8_t)sv_get_uint(sr, (uint32_t)sizeof(uint8_t)); }
static uint32_t sv_get_u32(sv_reader *sr) { return (uint32_t)sv_get_uint(sr, (uint32_t)sizeof(uint32_t)); }
static uint64_t sv_get_u64(sv_reader *sr) { return sv_get_uint(sr, (uint32_t)sizeof(uint64_t)); }
static int32_t  sv_get_i32(sv_reader *sr) { return (int32_t)sv_get_uint(sr, (uint32_t)sizeof(int32_t)); }
static int64_t  sv_get_i64(sv_reader *sr) { return (int64_t)sv_get_uint(sr, (uint32_t)sizeof(int64_t)); }

static double sv_bits_f64(uint64_t bits) {
    double v;
    memcpy(&v, &bits, sizeof(v));
    return v;
}

static double sv_get_f64(sv_reader *sr) { return sv_bits_f64(sv_get_u64(sr)); }

/* ---------------------------------------------------------- slot helpers */

/* Fixed slot order, matching om_world's own field order (F2i/F2j/F2k). A
 * NULL _size hook means the slot writes a 0-length blob; a NULL _read hook
 * means a nonempty blob (from an older/other build that did have the hook)
 * is skipped, not applied -- the slot's own module rebuilds lazily on next
 * use either way, the same lazy-alloc-on-first-access pattern every module
 * already uses for these pointers (e.g. csrc/generational.c's
 * gen_get_state). */
/* The eleven slots' hook fields differ in type per slot (void* state vs.
 * function pointers of distinct signatures), which is not safely tabled
 * without incompatible-pointer casts under -Wall -Werror, so each slot
 * below is one explicit call instead of a generic loop over a descriptor
 * array -- same convention om_world_free already uses in csrc/region.c. */
static void sv_write_one_slot(sv_writer *sw, const om_world *w, uint8_t id,
                               uint32_t (*size_fn)(const om_world *),
                               void (*write_fn)(const om_world *, uint8_t *)) {
    sv_put_u8(sw, id);
    uint32_t blen = size_fn ? size_fn(w) : 0;
    sv_put_u32(sw, blen);
    if (blen > 0) {
        if (sw->buf && write_fn && sw->pos <= sw->cap && blen <= sw->cap - sw->pos) {
            write_fn(w, sw->buf + sw->pos);
        }
        sw->pos += blen;
    }
}

static void sv_write_slots(sv_writer *sw, const om_world *w) {
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_TACTICAL,     w->tactical_state_size,     w->tactical_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_GENERATIONAL, w->generational_state_size, w->generational_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_EVENTS,       w->events_state_size,       w->events_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_MISSION,      w->mission_state_size,      w->mission_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_FOG,          w->fog_state_size,          w->fog_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_CHRONICLE,    w->chronicle_state_size,    w->chronicle_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_MOVE,         w->move_state_size,         w->move_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_MACRO,        w->macro_state_size,        w->macro_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_SUPPORT,      w->support_state_size,      w->support_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_MAPGEN,       w->mapgen_state_size,       w->mapgen_state_write);
    sv_write_one_slot(sw, w, OM_SAVE_SLOT_TERRAIN,      w->terrain_state_size,      w->terrain_state_write);
}

/* F2m (R-111-03 atomic refusal): apply == 0 (the validate pass) used to
 * skip read_fn entirely, so a structurally-valid but semantically-corrupt
 * slot blob (right id, right length, garbage inside -- e.g. a module count
 * over its own cap) was only ever caught in the apply pass, by which point
 * sv_parse_body had already written tick/seed/regions/factions/etc onto
 * the real w above (R-111-03 violation: a refused load must never touch
 * the target). Validate now runs read_fn too, but against shadow (a
 * scratch om_world, own module-slot fields only, allocated once by the
 * caller) instead of w, so a semantic failure is caught before the apply
 * pass -- and therefore before any core field write -- ever runs; the
 * fresh state read_fn built on shadow is then discarded through shadow's
 * own newly-set free hook (shadow_state/shadow_free_fn), never through
 * w's, which may still be NULL on a world that has not allocated this slot
 * yet. */
static void sv_parse_one_slot(sv_reader *sr, om_world *w, om_world *shadow, int apply,
                               uint8_t expect_id,
                               void **state, void (*free_fn)(void *),
                               void **shadow_state, void (**shadow_free_fn)(void *),
                               int (*read_fn)(om_world *, const uint8_t *, uint32_t)) {
    uint8_t id = sv_get_u8(sr);
    if (sr->ok && id != expect_id) sr->ok = 0;
    uint32_t blen = sv_get_u32(sr);
    const uint8_t *blob = (blen > 0) ? sv_get_span(sr, blen) : NULL;
    if (!sr->ok) return;
    if (apply) {
        if (*state && free_fn) free_fn(*state);
        *state = NULL;
        if (read_fn) {
            if (read_fn(w, blob, blen) != 0) sr->ok = 0;
        }
    } else if (read_fn) {
        if (read_fn(shadow, blob, blen) != 0) sr->ok = 0;
        if (*shadow_state && *shadow_free_fn) (*shadow_free_fn)(*shadow_state);
        *shadow_state = NULL;
        *shadow_free_fn = NULL;
    }
}

static void sv_parse_slots(sv_reader *sr, om_world *w, int apply) {
    /* Only the validate pass (apply == 0) needs a shadow target; the apply
     * pass reads straight into w as before. One shadow, calloc'd so the
     * (large, OM_MAX_REGIONS/OM_MAX_FACTIONS-sized) om_world is never put
     * on the stack, covers all eleven slot calls below -- each call only ever
     * touches its own module's pair of fields on it. */
    om_world *shadow = NULL;
    if (!apply) {
        shadow = calloc(1, sizeof(om_world));
        if (!shadow) { sr->ok = 0; return; }
    }
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_TACTICAL,
                       &w->tactical_state, w->tactical_state_free,
                       shadow ? &shadow->tactical_state : NULL,
                       shadow ? &shadow->tactical_state_free : NULL,
                       w->tactical_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_GENERATIONAL,
                       &w->generational_state, w->generational_state_free,
                       shadow ? &shadow->generational_state : NULL,
                       shadow ? &shadow->generational_state_free : NULL,
                       w->generational_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_EVENTS,
                       &w->events_state, w->events_state_free,
                       shadow ? &shadow->events_state : NULL,
                       shadow ? &shadow->events_state_free : NULL,
                       w->events_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_MISSION,
                       &w->mission_state, w->mission_state_free,
                       shadow ? &shadow->mission_state : NULL,
                       shadow ? &shadow->mission_state_free : NULL,
                       w->mission_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_FOG,
                       &w->fog_state, w->fog_state_free,
                       shadow ? &shadow->fog_state : NULL,
                       shadow ? &shadow->fog_state_free : NULL,
                       w->fog_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_CHRONICLE,
                       &w->chronicle_state, w->chronicle_state_free,
                       shadow ? &shadow->chronicle_state : NULL,
                       shadow ? &shadow->chronicle_state_free : NULL,
                       w->chronicle_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_MOVE,
                       &w->move_state, w->move_state_free,
                       shadow ? &shadow->move_state : NULL,
                       shadow ? &shadow->move_state_free : NULL,
                       w->move_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_MACRO,
                       &w->macro_state, w->macro_state_free,
                       shadow ? &shadow->macro_state : NULL,
                       shadow ? &shadow->macro_state_free : NULL,
                       w->macro_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_SUPPORT,
                       &w->support_state, w->support_state_free,
                       shadow ? &shadow->support_state : NULL,
                       shadow ? &shadow->support_state_free : NULL,
                       w->support_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_MAPGEN,
                       &w->mapgen_state, w->mapgen_state_free,
                       shadow ? &shadow->mapgen_state : NULL,
                       shadow ? &shadow->mapgen_state_free : NULL,
                       w->mapgen_state_read);
    sv_parse_one_slot(sr, w, shadow, apply, OM_SAVE_SLOT_TERRAIN,
                       &w->terrain_state, w->terrain_state_free,
                       shadow ? &shadow->terrain_state : NULL,
                       shadow ? &shadow->terrain_state_free : NULL,
                       w->terrain_state_read);
    if (shadow) free(shadow);
}

/* ------------------------------------------------------------- the body */

static void sv_write_body(sv_writer *sw, const om_world *w) {
    sv_put_bytes(sw, (const uint8_t *)OM_SAVE_MAGIC, OM_SAVE_MAGIC_LEN);
    sv_put_u32(sw, OM_SAVE_FORMAT_VERSION);

    {
        uint64_t tick = w->tick;
#ifdef OM_DEBUG_INJECT
        /* OM_BUG_SAVE_SKIPS_TICK (1601, tests/csim/controls/
         * test_control_e16_window_save_skips_tick.py): the save writes 0
         * instead of the real tick, so a load leaves the destination world
         * at tick 0 and its next step returns 1, not tick + 1. */
        if (w->inject == OM_BUG_SAVE_SKIPS_TICK) tick = 0;
#endif
        sv_put_u64(sw, tick);
    }
    sv_put_u64(sw, w->seed);
    {
        uint64_t rng_state = w->rng_state;
        uint64_t rng_inc = w->rng_inc;
#ifdef OM_DEBUG_INJECT
        /* OM_BUG_SAVE_SKIPS_RNG_STATE (1600, test_E16_S111_saving.py's own
         * positive control): the save writes a fixed placeholder instead
         * of the real PCG32 stream, so a load restores the wrong stream
         * and the loaded copy's future draws desync from continuing the
         * original. */
        if (w->inject == OM_BUG_SAVE_SKIPS_RNG_STATE) {
            rng_state = 0;
            rng_inc = 0;
        }
#endif
        sv_put_u64(sw, rng_state);
        sv_put_u64(sw, rng_inc);
    }
    sv_put_u64(sw, w->world_serial);
    sv_put_u32(sw, w->n_regions);
    sv_put_u32(sw, w->faction_n);

    sv_put_u32(sw, w->rng_forced_len);
    for (uint32_t i = 0; i < w->rng_forced_len; i++) {
        uint32_t idx = (w->rng_forced_head + i) % OM_RNG_FORCED_CAP;
        sv_put_f64(sw, w->rng_forced[idx]);
    }

    for (uint32_t i = 0; i < w->n_regions; i++) {
        const om_region *r = &w->regions[i];
        sv_put_u8(sw, (uint8_t)r->tier);
        sv_put_i32(sw, r->faction_id);
        sv_put_f64(sw, r->military);
        sv_put_f64(sw, r->economy);
        sv_put_f64(sw, r->tension);
        sv_put_f64(sw, r->population);
        sv_put_f64(sw, r->econ_phase);
        sv_put_f64(sw, r->tension_phase);
        sv_put_u32(sw, r->n_neighbors);
        for (uint32_t k = 0; k < r->n_neighbors; k++) sv_put_u32(sw, r->neighbors[k]);
        sv_put_u32(sw, r->damage_head);
        sv_put_u32(sw, r->damage_len);
        for (uint32_t k = 0; k < OM_DAMAGE_HISTORY_CAP; k++) {
            sv_put_u64(sw, r->damage_tick[k]);
            sv_put_f64(sw, r->damage_military[k]);
            sv_put_f64(sw, r->damage_economy[k]);
        }
    }

    uint8_t has_held_since = w->region_held_since ? 1 : 0;
    sv_put_u8(sw, has_held_since);
    if (has_held_since) {
        for (uint32_t i = 0; i < w->n_regions; i++) sv_put_i64(sw, w->region_held_since[i]);
    }
    uint8_t has_previous_owner = w->region_previous_owner ? 1 : 0;
    sv_put_u8(sw, has_previous_owner);
    if (has_previous_owner) {
        for (uint32_t i = 0; i < w->n_regions; i++) sv_put_i32(sw, w->region_previous_owner[i]);
    }

    for (uint32_t a = 0; a < OM_MAX_REGIONS; a++) {
        for (uint32_t b = 0; b < OM_MAX_REGIONS; b++) {
            sv_put_i32(sw, (int32_t)w->region_edge[a][b]);
        }
    }

    for (uint32_t i = 0; i < OM_FEATURE_COUNT; i++) sv_put_u8(sw, (uint8_t)w->features[i]);

    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_f64(sw, w->faction_budget[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_f64(sw, w->faction_tech[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_f64(sw, w->faction_confidence[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_i32(sw, (int32_t)w->faction_archetype[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_f64(sw, w->faction_tech_attack[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_f64(sw, w->faction_tech_defense[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_f64(sw, w->faction_tech_economy[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u8(sw, (uint8_t)(w->faction_used[f] ? 1 : 0));
    for (uint32_t a = 0; a < OM_MAX_FACTIONS; a++) {
        for (uint32_t b = 0; b < OM_MAX_FACTIONS; b++) sv_put_u8(sw, (uint8_t)w->faction_stance[a][b]);
    }
    for (uint32_t a = 0; a < OM_MAX_FACTIONS; a++) {
        for (uint32_t b = 0; b < OM_MAX_FACTIONS; b++) sv_put_u32(sw, w->faction_stance_counter[a][b]);
    }
    for (uint32_t a = 0; a < OM_MAX_FACTIONS; a++) {
        for (uint32_t b = 0; b < OM_MAX_FACTIONS; b++) sv_put_u64(sw, w->faction_cooperative_since[a][b]);
    }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_i64(sw, w->faction_last_knowledge_lost[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        for (uint32_t j = 0; j < OM_KNOWLEDGE_LOST_POP_WINDOW; j++) {
            sv_put_f64(sw, w->faction_pop_history[f][j]);
        }
    }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u32(sw, w->faction_pop_history_head[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u32(sw, w->faction_pop_history_len[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u64(sw, w->faction_created_tick[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u8(sw, (uint8_t)(w->faction_conquered_this_tick[f] ? 1 : 0));
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u32(sw, w->faction_window_total[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u32(sw, w->faction_window_revolts[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u32(sw, w->faction_window_attacks[f]);
    for (uint32_t f = 0; f < OM_MAX_FACTIONS; f++) sv_put_u32(sw, w->faction_window_colonizations[f]);

    sv_put_u32(sw, w->event_queue_n);
    for (uint32_t i = 0; i < w->event_queue_n; i++) {
        const om_queued_event *e = &w->event_queue[i];
        sv_put_u64(sw, e->due_tick);
        sv_put_u32(sw, e->region_idx);
        sv_put_u32(sw, e->template_id);
        sv_put_f64(sw, e->probability);
        sv_put_i32(sw, e->chain_tag);
        sv_put_i32(sw, e->source_faction);
        sv_put_u32(sw, e->chain_length);
        sv_put_u32(sw, e->cond_kind);
        sv_put_u32(sw, e->cond_field);
        sv_put_u32(sw, e->exclusion_tag);
        sv_put_f64(sw, e->cond_value);
    }

    sv_put_u32(sw, w->telegraphs_n);
    for (uint32_t i = 0; i < w->telegraphs_n; i++) {
        const om_telegraph *t = &w->telegraphs[i];
        sv_put_u64(sw, t->declared_tick);
        sv_put_i32(sw, t->attacker);
        sv_put_u32(sw, t->target_idx);
        sv_put_u32(sw, t->source_idx);
        sv_put_f64(sw, t->commit);
    }

    {
        const om_economy_state *e = &w->economy;
        sv_put_u32(sw, e->n_lots);
        for (uint32_t i = 0; i < e->n_lots; i++) {
            sv_put_u32(sw, e->lots[i].id);
            sv_put_f64(sw, e->lots[i].x);
            sv_put_f64(sw, e->lots[i].y);
            sv_put_i32(sw, e->lots[i].stage);
            sv_put_i32(sw, e->lots[i].building);
            sv_put_i32(sw, e->lots[i].owner);
        }
        sv_put_u32(sw, e->density_present);
        if (e->density_present) {
            uint32_t cells = e->density_side * e->density_side;
            sv_put_u32(sw, e->density_side);
            for (uint32_t i = 0; i < cells; i++) sv_put_f64(sw, e->density[i]);
            for (uint32_t i = 0; i < cells; i++) sv_put_f64(sw, e->P[i]);
            sv_put_u32(sw, e->n_active);
            for (uint32_t i = 0; i < e->n_active; i++) sv_put_u32(sw, e->active[i]);
            sv_put_u32(sw, e->core_cell);
        }
        sv_put_u32(sw, e->n_strongpoints);
        for (uint32_t i = 0; i < e->n_strongpoints; i++) {
            sv_put_u32(sw, e->strongpoints[i].id);
            sv_put_f64(sw, e->strongpoints[i].x);
            sv_put_f64(sw, e->strongpoints[i].y);
            sv_put_i32(sw, e->strongpoints[i].owner);
            sv_put_i32(sw, e->strongpoints[i].state);
        }
        sv_put_u32(sw, e->doctrine_chosen);
        sv_put_i32(sw, e->doctrine);
        sv_put_u32(sw, e->n_waves);
        for (uint32_t i = 0; i < e->n_waves; i++) {
            sv_put_u32(sw, e->waves[i].tick);
            sv_put_i32(sw, e->waves[i].kind);
            sv_put_f64(sw, e->waves[i].x);
            sv_put_f64(sw, e->waves[i].y);
        }
        sv_put_f64(sw, e->density_economy);
        for (uint32_t i = 0; i < OM_LOT_CAP; i++) sv_put_u32(sw, e->lot_hit_tick[i]);
        sv_put_u32(sw, e->next_lot_id);
    }

    sv_write_slots(sw, w);
}

/* Returns 0 (refuse) or 1 (ok) via sr->ok; never mutates w unless apply is
 * set. Both the validate call (apply=0) and the apply call (apply=1) run
 * this exact function against the same buffer, so they walk the identical
 * cursor sequence -- a bound/cap failure in the validate pass happens at
 * the same offset the apply pass would have hit. w->n_regions is read
 * (never written) in both passes purely to bound-check the saved
 * n_regions against it: this contract requires the caller to have already
 * created the destination world with the same region count as the save
 * (om_world_new is the only region-count allocator; there is no
 * accessor here to resize regions[] mid-load). */
static void sv_parse_body(sv_reader *sr, om_world *w, int apply) {
    uint8_t magic[4];
    for (uint32_t i = 0; i < OM_SAVE_MAGIC_LEN; i++) {
        const uint8_t *p = sv_get_span(sr, (uint32_t)sizeof(uint8_t));
        if (!p) return;
        magic[i] = p[0];
    }
    if (!sr->ok || memcmp(magic, OM_SAVE_MAGIC, OM_SAVE_MAGIC_LEN) != 0) { sr->ok = 0; return; }
    uint32_t version = sv_get_u32(sr);
    if (!sr->ok || version != OM_SAVE_FORMAT_VERSION) { sr->ok = 0; return; }

    uint64_t tick = sv_get_u64(sr);
    uint64_t seed = sv_get_u64(sr);
    uint64_t rng_state = sv_get_u64(sr);
    uint64_t rng_inc = sv_get_u64(sr);
    uint64_t world_serial = sv_get_u64(sr);
    uint32_t n_regions = sv_get_u32(sr);
    uint32_t faction_n = sv_get_u32(sr);
    if (!sr->ok) return;
    if (n_regions != w->n_regions) { sr->ok = 0; return; }
    if (faction_n > OM_MAX_FACTIONS) { sr->ok = 0; return; }

    if (apply) {
        w->tick = tick;
        w->seed = seed;
        w->rng_state = rng_state;
        w->rng_inc = rng_inc;
        w->world_serial = world_serial;
        w->faction_n = faction_n;
    }

    uint32_t rng_forced_len = sv_get_u32(sr);
    if (!sr->ok) return;
    if (rng_forced_len > OM_RNG_FORCED_CAP) { sr->ok = 0; return; }
    for (uint32_t i = 0; i < rng_forced_len && sr->ok; i++) {
        double v = sv_get_f64(sr);
        if (apply) w->rng_forced[i] = v;
    }
    if (!sr->ok) return;
    if (apply) {
        w->rng_forced_head = 0;
        w->rng_forced_len = rng_forced_len;
    }

    for (uint32_t i = 0; i < n_regions && sr->ok; i++) {
        om_region *r = apply ? &w->regions[i] : NULL;
        uint8_t tier = sv_get_u8(sr);
        int32_t faction_id = sv_get_i32(sr);
        double military = sv_get_f64(sr);
        double economy = sv_get_f64(sr);
        double tension = sv_get_f64(sr);
        double population = sv_get_f64(sr);
        double econ_phase = sv_get_f64(sr);
        double tension_phase = sv_get_f64(sr);
        uint32_t n_neighbors = sv_get_u32(sr);
        if (!sr->ok) break;
        if (n_neighbors > OM_MAX_NEIGHBORS) { sr->ok = 0; break; }
        uint32_t neighbors[OM_MAX_NEIGHBORS];
        for (uint32_t k = 0; k < n_neighbors; k++) neighbors[k] = sv_get_u32(sr);
        uint32_t damage_head = sv_get_u32(sr);
        uint32_t damage_len = sv_get_u32(sr);
        if (!sr->ok) break;
        if (damage_len > OM_DAMAGE_HISTORY_CAP) { sr->ok = 0; break; }
        for (uint32_t k = 0; k < OM_DAMAGE_HISTORY_CAP && sr->ok; k++) {
            uint64_t dtick = sv_get_u64(sr);
            double dmil = sv_get_f64(sr);
            double deco = sv_get_f64(sr);
            if (apply) {
                r->damage_tick[k] = dtick;
                r->damage_military[k] = dmil;
                r->damage_economy[k] = deco;
            }
        }
        if (!sr->ok) break;
        if (apply) {
            r->tier = (om_tier)tier;
            r->faction_id = faction_id;
            r->military = military;
            r->economy = economy;
            r->tension = tension;
            r->population = population;
            r->econ_phase = econ_phase;
            r->tension_phase = tension_phase;
            r->n_neighbors = n_neighbors;
            memcpy(r->neighbors, neighbors, (size_t)n_neighbors * sizeof(uint32_t));
            r->damage_head = damage_head;
            r->damage_len = damage_len;
        }
    }
    if (!sr->ok) return;

    uint8_t has_held_since = sv_get_u8(sr);
    if (!sr->ok) return;
    if (has_held_since) {
        for (uint32_t i = 0; i < n_regions && sr->ok; i++) {
            int64_t v = sv_get_i64(sr);
            if (apply) {
                if (!w->region_held_since) w->region_held_since = calloc(w->n_regions, sizeof(int64_t));
                if (w->region_held_since) w->region_held_since[i] = v;
            }
        }
    } else if (apply) {
        free(w->region_held_since);
        w->region_held_since = NULL;
    }
    if (!sr->ok) return;

    uint8_t has_previous_owner = sv_get_u8(sr);
    if (!sr->ok) return;
    if (has_previous_owner) {
        for (uint32_t i = 0; i < n_regions && sr->ok; i++) {
            int32_t v = sv_get_i32(sr);
            if (apply) {
                if (!w->region_previous_owner) w->region_previous_owner = calloc(w->n_regions, sizeof(int32_t));
                if (w->region_previous_owner) w->region_previous_owner[i] = v;
            }
        }
    } else if (apply) {
        free(w->region_previous_owner);
        w->region_previous_owner = NULL;
    }
    if (!sr->ok) return;

    for (uint32_t a = 0; a < OM_MAX_REGIONS && sr->ok; a++) {
        for (uint32_t b = 0; b < OM_MAX_REGIONS && sr->ok; b++) {
            int32_t e = sv_get_i32(sr);
            if (apply) w->region_edge[a][b] = (om_edge_type)e;
        }
    }
    if (!sr->ok) return;

    for (uint32_t i = 0; i < OM_FEATURE_COUNT && sr->ok; i++) {
        uint8_t v = sv_get_u8(sr);
        if (apply) w->features[i] = v;
    }
    if (!sr->ok) return;

    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { double v = sv_get_f64(sr); if (apply) w->faction_budget[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { double v = sv_get_f64(sr); if (apply) w->faction_tech[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { double v = sv_get_f64(sr); if (apply) w->faction_confidence[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { int32_t v = sv_get_i32(sr); if (apply) w->faction_archetype[f] = (om_archetype)v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { double v = sv_get_f64(sr); if (apply) w->faction_tech_attack[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { double v = sv_get_f64(sr); if (apply) w->faction_tech_defense[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { double v = sv_get_f64(sr); if (apply) w->faction_tech_economy[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint8_t v = sv_get_u8(sr); if (apply) w->faction_used[f] = v ? 1 : 0; }
    if (!sr->ok) return;
    for (uint32_t a = 0; a < OM_MAX_FACTIONS && sr->ok; a++) {
        for (uint32_t b = 0; b < OM_MAX_FACTIONS && sr->ok; b++) {
            uint8_t v = sv_get_u8(sr);
            if (apply) w->faction_stance[a][b] = (om_stance)v;
        }
    }
    for (uint32_t a = 0; a < OM_MAX_FACTIONS && sr->ok; a++) {
        for (uint32_t b = 0; b < OM_MAX_FACTIONS && sr->ok; b++) {
            uint32_t v = sv_get_u32(sr);
            if (apply) w->faction_stance_counter[a][b] = v;
        }
    }
    for (uint32_t a = 0; a < OM_MAX_FACTIONS && sr->ok; a++) {
        for (uint32_t b = 0; b < OM_MAX_FACTIONS && sr->ok; b++) {
            uint64_t v = sv_get_u64(sr);
            if (apply) w->faction_cooperative_since[a][b] = v;
        }
    }
    if (!sr->ok) return;
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { int64_t v = sv_get_i64(sr); if (apply) w->faction_last_knowledge_lost[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) {
        for (uint32_t j = 0; j < OM_KNOWLEDGE_LOST_POP_WINDOW && sr->ok; j++) {
            double v = sv_get_f64(sr); if (apply) w->faction_pop_history[f][j] = v;
        }
    }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint32_t v = sv_get_u32(sr); if (apply) w->faction_pop_history_head[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint32_t v = sv_get_u32(sr); if (apply) w->faction_pop_history_len[f] = v; }
    if (!sr->ok) return;
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint64_t v = sv_get_u64(sr); if (apply) w->faction_created_tick[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint8_t v = sv_get_u8(sr); if (apply) w->faction_conquered_this_tick[f] = v ? 1 : 0; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint32_t v = sv_get_u32(sr); if (apply) w->faction_window_total[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint32_t v = sv_get_u32(sr); if (apply) w->faction_window_revolts[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint32_t v = sv_get_u32(sr); if (apply) w->faction_window_attacks[f] = v; }
    for (uint32_t f = 0; f < OM_MAX_FACTIONS && sr->ok; f++) { uint32_t v = sv_get_u32(sr); if (apply) w->faction_window_colonizations[f] = v; }
    if (!sr->ok) return;

    uint32_t event_queue_n = sv_get_u32(sr);
    if (!sr->ok) return;
    if (event_queue_n > OM_EVENT_QUEUE_CAP) { sr->ok = 0; return; }
    for (uint32_t i = 0; i < event_queue_n && sr->ok; i++) {
        uint64_t due_tick = sv_get_u64(sr);
        uint32_t region_idx = sv_get_u32(sr);
        uint32_t template_id = sv_get_u32(sr);
        double probability = sv_get_f64(sr);
        int32_t chain_tag = sv_get_i32(sr);
        int32_t source_faction = sv_get_i32(sr);
        uint32_t chain_length = sv_get_u32(sr);
        uint32_t cond_kind = sv_get_u32(sr);
        uint32_t cond_field = sv_get_u32(sr);
        uint32_t exclusion_tag = sv_get_u32(sr);
        double cond_value = sv_get_f64(sr);
        if (apply && sr->ok) {
            om_queued_event *e = &w->event_queue[i];
            e->due_tick = due_tick;
            e->region_idx = region_idx;
            e->template_id = template_id;
            e->probability = probability;
            e->chain_tag = chain_tag;
            e->source_faction = source_faction;
            e->chain_length = chain_length;
            e->cond_kind = cond_kind;
            e->cond_field = cond_field;
            e->exclusion_tag = exclusion_tag;
            e->cond_value = cond_value;
        }
    }
    if (!sr->ok) return;
    if (apply) w->event_queue_n = event_queue_n;

    uint32_t telegraphs_n = sv_get_u32(sr);
    if (!sr->ok) return;
    if (telegraphs_n > OM_MAX_REGIONS) { sr->ok = 0; return; }
    for (uint32_t i = 0; i < telegraphs_n && sr->ok; i++) {
        uint64_t declared_tick = sv_get_u64(sr);
        int32_t attacker = sv_get_i32(sr);
        uint32_t target_idx = sv_get_u32(sr);
        uint32_t source_idx = sv_get_u32(sr);
        double commit = sv_get_f64(sr);
        if (apply && sr->ok) {
            om_telegraph *t = &w->telegraphs[i];
            t->declared_tick = declared_tick;
            t->attacker = attacker;
            t->target_idx = target_idx;
            t->source_idx = source_idx;
            t->commit = commit;
        }
    }
    if (!sr->ok) return;
    if (apply) w->telegraphs_n = telegraphs_n;

    {
        om_economy_state *e = &w->economy;
        uint32_t n = sv_get_u32(sr);
        if (!sr->ok || n > OM_LOT_CAP) { sr->ok = 0; return; }
        for (uint32_t i = 0; i < n && sr->ok; i++) {
            om_lot l;
            l.id = sv_get_u32(sr);
            l.x = sv_get_f64(sr);
            l.y = sv_get_f64(sr);
            l.stage = sv_get_i32(sr);
            l.building = sv_get_i32(sr);
            l.owner = sv_get_i32(sr);
            if (apply && sr->ok) e->lots[i] = l;
        }
        if (!sr->ok) return;
        if (apply) e->n_lots = n;

        uint32_t present = sv_get_u32(sr);
        if (!sr->ok || present > 1) { sr->ok = 0; return; }
        if (present) {
            uint32_t side = sv_get_u32(sr), cells = 0, n_active = 0, core_cell = 0;
            if (!sr->ok || side > OM_DENSITY_MAX_SIDE) { sr->ok = 0; return; }
            cells = side * side;
            for (uint32_t i = 0; i < cells && sr->ok; i++) {
                double v = sv_get_f64(sr);
                if (apply && sr->ok) e->density[i] = v;
            }
            for (uint32_t i = 0; i < cells && sr->ok; i++) {
                double v = sv_get_f64(sr);
                if (apply && sr->ok) e->P[i] = v;
            }
            n_active = sv_get_u32(sr);
            if (!sr->ok || n_active > cells) { sr->ok = 0; return; }
            for (uint32_t i = 0; i < n_active && sr->ok; i++) {
                uint32_t cell = sv_get_u32(sr);
                if (sr->ok && cell >= cells) { sr->ok = 0; return; }
                if (apply && sr->ok) e->active[i] = cell;
            }
            core_cell = sv_get_u32(sr);
            if (!sr->ok || core_cell >= cells) { sr->ok = 0; return; }
            if (apply) { e->density_side = side; e->n_active = n_active; e->core_cell = core_cell; }
        }
        if (!sr->ok) return;
        if (apply) e->density_present = (uint8_t)present;

        n = sv_get_u32(sr);
        if (!sr->ok || n > OM_STRONGPOINT_CAP) { sr->ok = 0; return; }
        for (uint32_t i = 0; i < n && sr->ok; i++) {
            om_strongpoint p;
            p.id = sv_get_u32(sr);
            p.x = sv_get_f64(sr);
            p.y = sv_get_f64(sr);
            p.owner = sv_get_i32(sr);
            p.state = sv_get_i32(sr);
            if (apply && sr->ok) e->strongpoints[i] = p;
        }
        if (!sr->ok) return;
        if (apply) e->n_strongpoints = n;

        uint32_t chosen = sv_get_u32(sr);
        int32_t doctrine = sv_get_i32(sr);
        if (!sr->ok || chosen > 1) { sr->ok = 0; return; }
        if (apply) { e->doctrine_chosen = (uint8_t)chosen; e->doctrine = doctrine; }

        n = sv_get_u32(sr);
        if (!sr->ok || n > OM_WAVE_LOG_CAP) { sr->ok = 0; return; }
        for (uint32_t i = 0; i < n && sr->ok; i++) {
            om_wave wv;
            wv.tick = sv_get_u32(sr);
            wv.kind = sv_get_i32(sr);
            wv.x = sv_get_f64(sr);
            wv.y = sv_get_f64(sr);
            if (apply && sr->ok) e->waves[i] = wv;
        }
        if (!sr->ok) return;
        if (apply) e->n_waves = n;

        double density_economy = sv_get_f64(sr);
        for (uint32_t i = 0; i < OM_LOT_CAP && sr->ok; i++) {
            uint32_t ht = sv_get_u32(sr);
            if (apply && sr->ok) e->lot_hit_tick[i] = ht;
        }
        uint32_t next_lot_id = sv_get_u32(sr);
        if (!sr->ok) return;
        if (apply) { e->density_economy = density_economy; e->next_lot_id = next_lot_id; }
    }

    sv_parse_slots(sr, w, apply);
    /* K-e5: the terrain slot has loaded; the derived grids follow it (a no-op until E1q-field fills the stub). */
    if (apply && sr->ok) om_density_rebuild_inputs(w);
}

/* ------------------------------------------------------------ public ABI */

uint32_t om_save_state_size(const om_world *w) {
    if (!w) return 0;
    sv_writer sw = { NULL, 0, 0 };
    sv_write_body(&sw, w);
    return sw.pos;
}

void om_save_state_write(const om_world *w, uint8_t *out, uint32_t capacity) {
    if (!w || !out) return;
    uint32_t needed = om_save_state_size(w);
    if (capacity < needed) return;
    sv_writer sw = { out, capacity, 0 };
    sv_write_body(&sw, w);
}

int om_load_state_read(om_world *w, const uint8_t *buffer, uint32_t length) {
    if (!w || !buffer) return 1;

    sv_reader validate = { buffer, length, 0, 1 };
    sv_parse_body(&validate, w, 0);
    if (!validate.ok) return 1;

    sv_reader apply = { buffer, length, 0, 1 };
    sv_parse_body(&apply, w, 1);
    return apply.ok ? 0 : 1;
}
