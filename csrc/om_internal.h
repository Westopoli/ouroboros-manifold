/* csrc/om_internal.h — private world layout shared by the C source files.
 * Parent-owned like ouroboros_sim.h. A build card that must add state to
 * om_world lists this file in allowed_files; a card that only reads it does
 * not. Never included by the tests; the public ABI is ouroboros_sim.h. */
#ifndef OM_INTERNAL_H
#define OM_INTERNAL_H

#include "ouroboros_sim.h"

#define OM_MAX_NEIGHBORS 32
/* HDR5 (A27): raised 128 -> 512 so every region-indexed and per-tick-record
 * bound covers E-03's full draw range (OM_WORLD_REGION_COUNT_RANGE_HI = 400,
 * om_constants.h). om_world_new rejects more than this. */
#define OM_MAX_REGIONS 512
#define OM_DAMAGE_HISTORY_CAP 64
#define OM_TIE_EPSILON 1e-12
/* F2j: named so save.c (T2c) can bound-check a loaded count against the
 * same cap the struct below was declared with, instead of repeating the
 * bare literal (alg_constants.py --lint csrc only globs csrc slash star
 * dot c, not this header, but save.c's own lines must still name every
 * cap). */
#define OM_RNG_FORCED_CAP 4096
#define OM_FEATURE_COUNT 9
#define OM_EVENT_QUEUE_CAP 64

/* F2j: save.c (S-111, card T2c) format constants. Magic is the save
 * blob's first 4 bytes; a mismatch is R-111-03's version refusal.
 * Format version bumps whenever save.c's own field layout changes shape
 * (not on unrelated om_world additions with no save-format impact). Byte
 * bits/mask are named so save.c's manual little-endian pack/unpack loops
 * never carry a bare shift/mask literal the lint would flag. Slot ids fix
 * the on-disk order of the nine per-module blobs below (om_world's own
 * field order, F2i). */
#define OM_SAVE_MAGIC "OMSV"
#define OM_SAVE_MAGIC_LEN 4
#define OM_SAVE_FORMAT_VERSION 11 /* bumped 10 -> 11 (VG W2: the movement section stores the walk routes: plan_layer, route_n, route_i, route_ends_at_goal and the route cells): version-10 saves are refused, no migration (R-111-03). Earlier: bumped 9 -> 10 (VG K-e5: density_side, P, n_active, active, core_cell, next_lot_id; lot_hit_tick sized OM_LOT_CAP 2048): version-9 saves are refused, no migration (R-111-03). Earlier: bumped 8 -> 9 (VG K-e3: density_economy, lot_hit_tick): version-8 saves are refused, no migration (R-111-03). Earlier: bumped 7 -> 8 (VG K-e: lots, density grid, strongpoints, doctrine, wave log): version-7 saves are refused, no migration (R-111-03). Earlier: bumped 6 -> 7 (terrain stage 3): version-6 saves are refused. Earlier: bumped 5 -> 6 (lockstep spec 2026-10-05): version-5 saves are refused. Earlier: bumped 4 -> 5 (HDR5): the edge matrix is OM_MAX_REGIONS (512) square, so the layout grew; version-4 saves are refused, no migration. Version 4 added: gen_state gained current commander/lineage, chosen archetype, no-candidate flag, last end reason; version-3 saves are rejected, no migration */
#define OM_SAVE_BYTE_BITS 8
#define OM_SAVE_BYTE_MASK 0xFFu
#define OM_SAVE_SLOT_TACTICAL     0
#define OM_SAVE_SLOT_GENERATIONAL 1
#define OM_SAVE_SLOT_EVENTS       2
#define OM_SAVE_SLOT_MISSION      3
#define OM_SAVE_SLOT_FOG          4
#define OM_SAVE_SLOT_CHRONICLE    5
#define OM_SAVE_SLOT_MOVE         6
#define OM_SAVE_SLOT_MACRO        7
#define OM_SAVE_SLOT_SUPPORT      8
#define OM_SAVE_SLOT_MAPGEN       9
#define OM_SAVE_SLOT_TERRAIN      10
#define OM_SAVE_SLOT_COUNT        11

typedef struct {
    om_tier  tier;
    double   military, economy, tension, population;
    double   econ_phase, tension_phase;
    double   prev_econ_osc, prev_tension_osc;
    int32_t  faction_id;
    uint32_t neighbors[OM_MAX_NEIGHBORS];
    uint32_t n_neighbors;
    om_drift_row last_drift;

    /* ALG-11 damage history (om_region_add_damage / om_region_damage_history,
     * ouroboros_sim.h ~line 254): a ring of (tick, military_loss, economy_loss)
     * entries, one per recorded attack-resolution loss, oldest overwritten past
     * OM_DAMAGE_HISTORY_CAP. Persists across ticks; never reset in sim.c. The
     * reader sums entries with tick within DAMAGE_HISTORY_WINDOW = 150 of the
     * current world tick (docs/bible/algorithms.md ALG-11; R-034-07). */
    uint64_t damage_tick[OM_DAMAGE_HISTORY_CAP];
    double   damage_military[OM_DAMAGE_HISTORY_CAP];
    double   damage_economy[OM_DAMAGE_HISTORY_CAP];
    uint32_t damage_head, damage_len;
} om_region;

#define OM_NET_SECTION_COUNT 9

/* VG K-e (lane E1, ABI 6): economy fields held inline in om_world, saved at format 8 and hashed in the factions section.
 * No spec number gives a cap for any of these; each is a liberty 2026-10-09, the smallest sensible, for E1b to E1h to
 * revise. Density is a coarse grid of OM_DENSITY_SIDE x OM_DENSITY_SIDE cells over the 24000 wu canvas. */
#define OM_LOT_CAP 2048 /* DRAFT-lot-cap (K-e5; was 256, liberty 2026-10-09) */
#define OM_STRONGPOINT_CAP 32 /* liberty 2026-10-09 */
#define OM_WAVE_LOG_CAP 128 /* liberty 2026-10-09 */
#define OM_DENSITY_SIDE 120 /* legacy: liberty 2026-10-09, 200 wu cells. E1q deletes it. See also: Lane E1 part c (the settlement port). */
#define OM_DENSITY_MAX_SIDE 240 /* K-e5: cells per side of the 100 wu terrain grid on a 24000 wu canvas */
#define OM_DENSITY_MAX_CELLS (OM_DENSITY_MAX_SIDE * OM_DENSITY_MAX_SIDE)
#define OM_DOCTRINE_BALANCED 3
typedef struct om_economy_state {
    uint32_t n_lots;
    om_lot lots[OM_LOT_CAP];
    uint8_t density_present;
    uint32_t density_side; /* K-e5, saved and hashed with density_present: cells per side, at most OM_DENSITY_MAX_SIDE (120 on the K-e5 tree) */
    double density[OM_DENSITY_MAX_CELLS]; /* D: saved and hashed, density_side squared entries, Q16 */
    double P[OM_DENSITY_MAX_CELLS]; /* P (K-e5; E1q-field grows it, all zero on the K-e5 tree): saved and hashed like D */
    uint32_t n_active; /* K-e5: the growth frontier, saved and hashed */
    uint32_t active[OM_DENSITY_MAX_CELLS];
    uint32_t core_cell; /* K-e5: saved and hashed */
    uint32_t n_strongpoints;
    om_strongpoint strongpoints[OM_STRONGPOINT_CAP];
    uint8_t doctrine_chosen; /* 0: the world is calloc-zeroed, so a fresh world reads OM_DOCTRINE_BALANCED */
    int32_t doctrine;
    uint32_t n_waves;
    om_wave waves[OM_WAVE_LOG_CAP];
    double density_economy; /* VG K-e3: the player's home region economy, sampled once at om_economy_init */
    uint32_t lot_hit_tick[OM_LOT_CAP]; /* VG K-e3: tick of the last area hit that knocked lot i back; 0 = never */
    uint32_t next_lot_id; /* K-e5, saved and hashed, always written; 1 on the K-e5 tree (the old code numbers lots n_lots + 1), E1q switches both lot creators to it */
    /* K-e5: derived grids, density_side squared, unsaved and unhashed; E1q-field fills them in om_density_rebuild_inputs, E1q-lots writes lot_at when it creates a lot. */
    int32_t elev_cm[OM_DENSITY_MAX_CELLS];
    uint8_t water[OM_DENSITY_MAX_CELLS];
    uint8_t wdist[OM_DENSITY_MAX_CELLS];
    uint16_t slope_q[OM_DENSITY_MAX_CELLS];
    uint8_t lane[OM_DENSITY_MAX_CELLS];
    int32_t lot_at[OM_DENSITY_MAX_CELLS];
} om_economy_state;

/* VG K-d (lane D, 2026-10-07 spec rev 4): five layers of 240 x 240 cells of 100 wu on a 24000 wu canvas. */
#define OM_SPACE_FIELD_LAYERS 5
#define OM_SPACE_FIELD_SIDE 240
#define OM_SPACE_FIELD_CELLS (OM_SPACE_FIELD_SIDE * OM_SPACE_FIELD_SIDE)
#define OM_SPACE_FIELD_CELL_WU 100.0
#define OM_SPACE_FIELD_CANVAS_WU 24000.0
#define OM_SPACE_FIELD_DENSITY_DEFAULT 35.0 /* field_map_space.gd default density; the era manifest may override later (lane D leftover) */
/* Caps (K-d2). POLYS: tests/csim/test_VG_D_d2.py D2_POLYS_PER_LAYER hi 530 x 5 layers = 2650 (mockup field_map_space.gd
 * plate_polygon_count 417 to 496 per layer = 2480), rounded up to a power of two. PTS: D2_MAX_PTS 16 in the same file (the
 * mockup's rubble cells are 8-sided, _cell_polygon(..., 8, ...); plates are a square cut by bisectors); the D4 test's
 * poly_get buffer (64) and the pipe's PIPE_SPACE_FIELD_POLY_PTS (64) are larger and unaffected. */
#define OM_SPACE_FIELD_MAX_POLYS 4096
#define OM_SPACE_FIELD_MAX_PTS 16
typedef struct om_space_field_poly {
    uint8_t layer, kind, n_pts;
    double xy[2 * OM_SPACE_FIELD_MAX_PTS];
} om_space_field_poly;
typedef struct om_space_field_state {
    uint8_t present;
    uint32_t seed;
    uint32_t n_nodes; /* VG-D8: the clearing nodes the held field was generated with, so om_space_field_generate_nodes on the same seed repeats it */
    double node_xy[2 * OM_SPACE_FIELD_MAX_NODES];
    uint32_t node_slots[OM_SPACE_FIELD_MAX_NODES];
    uint8_t mask[OM_SPACE_FIELD_LAYERS][OM_SPACE_FIELD_CELLS / 8]; /* bit (i & 7) of byte (i >> 3), i = cy * side + cx, 1 blocked */
    uint32_t n_polys;
    om_space_field_poly polys[OM_SPACE_FIELD_MAX_POLYS];
} om_space_field_state;

struct om_world {
    uint32_t n_regions;
    uint64_t seed;
    uint64_t tick;
    int      trace_on;
    int      inject;
    om_region *regions;
    double   faction_mod[OM_MAX_FACTIONS][OM_F_COUNT];
    om_trace_row *trace;
    uint64_t trace_len, trace_cap;

    /* E-05 faction, ownership, typed edges, and RNG state.
     * features[] is sized for every om_feature id (OM_FEAT_EVENTS ..
     * OM_FEAT_TACTICAL, 9 today); bump alongside a new om_feature value. */
    int          features[OM_FEATURE_COUNT];
    double       faction_budget[OM_MAX_FACTIONS];
    double       faction_budget_snapshot[OM_MAX_FACTIONS];
    double       faction_tech[OM_MAX_FACTIONS];
    double       faction_confidence[OM_MAX_FACTIONS];
    om_archetype faction_archetype[OM_MAX_FACTIONS];
    om_stance    faction_stance[OM_MAX_FACTIONS][OM_MAX_FACTIONS];
    double       faction_tech_attack[OM_MAX_FACTIONS];
    double       faction_tech_defense[OM_MAX_FACTIONS];
    double       faction_tech_economy[OM_MAX_FACTIONS];
    int          faction_used[OM_MAX_FACTIONS];
    uint32_t     faction_n;
    int64_t     *region_held_since;
    om_edge_type region_edge[OM_MAX_REGIONS][OM_MAX_REGIONS];
    uint64_t     rng_state, rng_inc;
    double       rng_forced[OM_RNG_FORCED_CAP];
    uint32_t     rng_forced_head, rng_forced_len;

    /* E-05 decision and resolution state. Each log holds at most one record
     * per region per tick, so it is sized OM_MAX_REGIONS (F2d), matching the
     * n_regions bound every writer already loops on. */
    om_decision        decisions[OM_MAX_REGIONS];
    uint32_t           decisions_n;
    om_telegraph       telegraphs[OM_MAX_REGIONS];
    uint32_t           telegraphs_n;
    om_attack_result   attacks[OM_MAX_REGIONS];
    uint32_t           attacks_n;
    om_collision       collisions[OM_MAX_REGIONS];
    uint32_t           collisions_n;
    om_reinforce       reinforces[OM_MAX_REGIONS];
    uint32_t           reinforces_n;
    om_colonize_result colonizations[OM_MAX_REGIONS];
    uint32_t           colonizations_n;
    om_friction        frictions[OM_MAX_REGIONS];
    uint32_t           frictions_n;
    om_admin_roll      admin_rolls[OM_MAX_REGIONS];
    uint32_t           admin_rolls_n;

    /* event queue, shared with E-04 (ouroboros_sim.h ~line 454): entries are
     * queued by E-05 (conquest-unrest, admin-separatist chains) and resolved
     * by E-04 (ALG-36). Persists across ticks; never reset in sim.c. */
    om_queued_event    event_queue[OM_EVENT_QUEUE_CAP];
    uint32_t           event_queue_n;

    /* E-03 generation config and result (freeze/F2b). Config is written by
     * the om_gen_set_* setters (ouroboros_sim.h ~line 690, csrc/worldgen.c)
     * and read by om_world_generate; defaults are set in om_world_new
     * (csrc/region.c) from om_constants.h. gen_home_range is indexed
     * [archetype - OM_ARCH_CONQUEROR][mil_lo, mil_hi, eco_lo, eco_hi]
     * (R-022-05). faction_template holds each faction's rolled template
     * (OM_TMPL_NONE before generation); generated and edge_count back
     * om_world_generated / om_world_edge_count. */
    uint32_t    gen_region_min, gen_region_max;
    uint32_t    gen_faction_count;
    double      gen_extra_edge_ratio;
    om_template gen_player_pref;
    double      gen_preference_weight;
    int         gen_extra_edges_on;
    double      gen_home_range[3][4];
    om_template faction_template[OM_MAX_FACTIONS];
    int         generated;
    uint32_t    edge_count;

    /* F2c: E-07 lifecycle storage (docs/bible/epics/E-07-civilizational-lifecycle.md,
     * ALG-41..44). csrc/lifecycle.c (card B6) is the sole writer; these are
     * distinct from E-05's admin_rolls[] above (S-040 admin revolts, not
     * lifecycle revolts). Named lc_* so a lifecycle revolt/reversion/
     * absorption is never confused with an E-05 record of the same shape.
     * Per-tick logs like attacks[]/reinforces[]/decisions[] above: the tests
     * (tests/csim/test_E07_S049/S050/S051) only ever check a log for the
     * same tick that produced the record, so om_step_lifecycle must zero
     * lc_revolts_n/lc_reversions_n/lc_absorptions_n at its own top, the way
     * om_step_resolve zeros attacks_n (csrc/resolve.c) -- not done here
     * because om_step_lifecycle's body is card B6's, not F2c's. */
    om_revolt_record     lc_revolts[OM_MAX_REGIONS];
    uint32_t             lc_revolts_n;
    om_reversion_record  lc_reversions[OM_MAX_REGIONS];
    uint32_t             lc_reversions_n;
    om_absorption_record lc_absorptions[OM_MAX_REGIONS];
    uint32_t             lc_absorptions_n;
    uint64_t faction_created_tick[OM_MAX_FACTIONS];
    int      faction_conquered_this_tick[OM_MAX_FACTIONS];
    uint32_t faction_window_total[OM_MAX_FACTIONS];
    uint32_t faction_window_revolts[OM_MAX_FACTIONS];
    uint32_t faction_window_attacks[OM_MAX_FACTIONS];
    uint32_t faction_window_colonizations[OM_MAX_FACTIONS];
    /* -1 default (no previous owner). Lazily calloc'd on first write, same
     * convention as region_held_since above: NULL until
     * om_region_set_previous_owner's first call, -1 returned by
     * om_region_previous_owner while NULL (both in csrc/lifecycle.c,
     * card B6). Unlike region_held_since, om_world_free below does free
     * this one -- region_held_since's own leak is pre-existing and out of
     * F2c's scope. */
    int32_t *region_previous_owner;

    /* tactical modules keep per-world state here, never in file statics
     * keyed by om_world* (save/load and the checksum must see it) */
    void *tactical_state;
    void (*tactical_state_free)(void *);
    /* F2j: save hooks beside tactical_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*tactical_state_size)(const om_world *w);
    void (*tactical_state_write)(const om_world *w, uint8_t *out);
    int (*tactical_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* E-08 generational module state, same convention as tactical_state
     * above: never a file static keyed by om_world*. */
    void *generational_state;
    void (*generational_state_free)(void *);
    /* F2j: save hooks beside generational_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*generational_state_size)(const om_world *w);
    void (*generational_state_write)(const om_world *w, uint8_t *out);
    int (*generational_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* B1-3: csrc/events.c per-world state, same convention as
     * tactical_state above -- events.c kept it in a file-static slot table
     * keyed by om_world*, invisible to save/load and the checksum. */
    void *events_state;
    void (*events_state_free)(void *);
    /* F2j: save hooks beside events_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*events_state_size)(const om_world *w);
    void (*events_state_write)(const om_world *w, uint8_t *out);
    int (*events_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* B9: csrc/mission.c per-world state, same convention as tactical_state
     * above. */
    void *mission_state;
    void (*mission_state_free)(void *);
    /* F2j: save hooks beside mission_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*mission_state_size)(const om_world *w);
    void (*mission_state_write)(const om_world *w, uint8_t *out);
    int (*mission_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* F2i: csrc/fog.c per-world state, same convention as tactical_state
     * above. */
    void *fog_state;
    void (*fog_state_free)(void *);
    /* F2j: save hooks beside fog_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*fog_state_size)(const om_world *w);
    void (*fog_state_write)(const om_world *w, uint8_t *out);
    int (*fog_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* F2i: csrc/chronicle.c per-world state, same convention as
     * tactical_state above. */
    void *chronicle_state;
    void (*chronicle_state_free)(void *);
    /* F2j: save hooks beside chronicle_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*chronicle_state_size)(const om_world *w);
    void (*chronicle_state_write)(const om_world *w, uint8_t *out);
    int (*chronicle_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* F2i: csrc/tactical_move.c per-world state, same convention as
     * tactical_state above. */
    void *move_state;
    void (*move_state_free)(void *);
    /* F2j: save hooks beside move_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*move_state_size)(const om_world *w);
    void (*move_state_write)(const om_world *w, uint8_t *out);
    int (*move_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* F2i: csrc/enemy_macro.c per-world state, same convention as
     * tactical_state above. */
    void *macro_state;
    void (*macro_state_free)(void *);
    /* F2j: save hooks beside macro_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*macro_state_size)(const om_world *w);
    void (*macro_state_write)(const om_world *w, uint8_t *out);
    int (*macro_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* F2i: csrc/tactical_support.c per-world state, same convention as
     * tactical_state above. */
    void *support_state;
    void (*support_state_free)(void *);
    /* F2j: save hooks beside support_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*support_state_size)(const om_world *w);
    void (*support_state_write)(const om_world *w, uint8_t *out);
    int (*support_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* F2k: csrc/tactical_mapgen.c per-world state, same convention as
     * tactical_state above. */
    void *mapgen_state;
    void (*mapgen_state_free)(void *);
    /* F2j-2: save hooks beside mapgen_state_free above (same convention). NULL means the slot is not saved; see csrc/save.c. */
    uint32_t (*mapgen_state_size)(const om_world *w);
    void (*mapgen_state_write)(const om_world *w, uint8_t *out);
    int (*mapgen_state_read)(om_world *w, const uint8_t *buf, uint32_t len);

    /* F2e: E-06 diplomacy storage backing the om_faction_stance_counter /
     * om_faction_cooperative_since / om_faction_last_knowledge_lost
     * accessors (csrc/ouroboros_sim.h; card B5 fills the read/write bodies
     * in csrc/diplomacy.c, still STUBs here). ALG-38: per neutral ordered
     * pair sharing a border edge, ticks since the last attack between them,
     * reset to 0 on an attack; 0 is also the pair's never-counted-yet
     * starting value, so 0 carries both meanings, matching the STUB
     * accessors' current 0 return. ALG-39: cooperative_since is the tick a
     * successful overture applied (S-043 R-043-05); 0 doubles as "never
     * cooperative" since om_faction_cooperative_since's restype is the
     * unsigned uint64_t tick counter (no negative sentinel available,
     * unlike the int64_t fields below). */
    uint32_t faction_stance_counter[OM_MAX_FACTIONS][OM_MAX_FACTIONS];
    uint64_t faction_cooperative_since[OM_MAX_FACTIONS][OM_MAX_FACTIONS];

    /* ALG-27b Knowledge Lost: tick of each faction's last Knowledge Lost
     * event. -1 sentinel for "never", matching the header's existing
     * int64_t never-yet convention (om_region_held_since, om_event_last_fired
     * both < 0 = never); om_faction_last_knowledge_lost's restype is the
     * signed int64_t, unlike cooperative_since above, so -1 is available and
     * unambiguous. */
    int64_t faction_last_knowledge_lost[OM_MAX_FACTIONS];

    /* ALG-27b pop-drop leg: per-faction ring of avg_p samples (window = 50 ticks,
     * literal below -- OM_KNOWLEDGE_LOST_POP_WINDOW is a local #define in
     * diplomacy.c; struct array dimensions are exempt from the alg_constants lint).
     * Window = OM_KNOWLEDGE_LOST_POP_WINDOW (om_constants.h, ALG-27b); dimension
     * stays literal 50 here since om_constants.h is not included in this header.
     * head = next write index (0..49); len = samples stored (0..50).
     * Initialized to 0 at world creation (calloc in om_world_new/region.c).
     * Serialized by SAVE-1 (save.c sv_write_body / sv_parse_body). */
    double   faction_pop_history[OM_MAX_FACTIONS][50];
    uint32_t faction_pop_history_head[OM_MAX_FACTIONS];
    uint32_t faction_pop_history_len[OM_MAX_FACTIONS];

    /* Bumped from a file-static counter in om_world_new (csrc/region.c),
     * starting at 1: a cheap way for any module to detect a reused
     * om_world* address (e.g. a stale cached pointer after free/realloc). */
    uint64_t world_serial;

    /* Lockstep spec 2026-10-05: per-section checksum hooks (csrc/checksum_full.c),
     * installed by each module's om_<module>_install_net_hooks; NULL hashes as 0.
     * Order: 0 regions, 1 factions, 2 rng, 3 units, 4 movement, 5 mission,
     * 6 fog, 7 macro, 8 support and map. */
    uint64_t (*net_section_hash[OM_NET_SECTION_COUNT])(const om_world *w);
    uint32_t (*net_unit_hashes)(const om_world *w, uint64_t *out, uint32_t cap);
    /* csrc/cmd_stream.c per-world state, same convention as tactical_state. */
    void *net_state;
    void (*net_state_free)(void *);
    /* Terrain stage 1 (spec 2026-10-05): per-world terrain field (csrc/terrain.c),
     * NULL until om_terrain_generate; freed through terrain_state_free. */
    void *terrain_state;
    void (*terrain_state_free)(void *);
    /* Save hooks beside terrain_state_free (same convention as mapgen_state_*); see csrc/save.c OM_SAVE_SLOT_TERRAIN. */
    uint32_t (*terrain_state_size)(const om_world *w);
    void (*terrain_state_write)(const om_world *w, uint8_t *out);
    int (*terrain_state_read)(om_world *w, const uint8_t *buf, uint32_t len);
    /* VG K-d: the space field (csrc/space_field.c), held inline so om_world_free needs no hook. Not hashed or saved on its
     * own: the masks reach routing through the mapgen blocked_bits (hashed and saved in the mapgen slot), and the whole
     * field, polygons included, is a pure function of (seed, canvas), so a loaded world regenerates it from the seed at
     * mission_start; no save version bump. */
    om_space_field_state space_field;
    /* VG K-e: lots, density grid, strongpoints, doctrine, wave log (csrc/economy_*.c, csrc/strongpoint.c). */
    om_economy_state economy;
};

/* Debug-build mirror of the E-03 generation fields above, for the F2b storage
 * test (tests/csim/test_E03_wiring_storage.py). Not part of the public ABI. */
#ifdef OM_DEBUG_INJECT
typedef struct {
    uint32_t region_min, region_max;
    uint32_t faction_count;
    double   extra_edge_ratio;
    int32_t  player_pref;
    double   preference_weight;
    int32_t  extra_edges_on;
    double   home_range[3][4];
    int32_t  generated;
    uint32_t edge_count;
} om_debug_gen_config_row;
void om_debug_gen_config(const om_world *w, om_debug_gen_config_row *out);
#endif

/* F2m: wires each module's save hooks onto a fresh world at om_world_new
 * (csrc/region.c) time, so a world that never touched the module still has
 * a working events_state_read/generational_state_read before any save/load
 * -- the module's own lazy allocators (evt_alloc csrc/events.c,
 * gen_get_state csrc/generational.c) set the same three pointers again the
 * first time state is actually needed, so this only pre-wires the hooks;
 * it never allocates the state itself. */
void om_events_install_save_hooks(om_world *w);

/* Terrain stage 1 (spec 2026-10-05). Sizes are provisional (2026-10-05). */
#define OM_TERRAIN_CELL_WU 100.0 /* R-186-05: one cell is 100 wu */
#define OM_TERRAIN_BANDS 5 /* R-200-01 */
#define OM_TERRAIN_MAX_CELLS 280 /* cells a side: OM_MAP_MAX_CANVAS / OM_TERRAIN_CELL_WU */
#define OM_TERRAIN_SLOPE_CAP 4096 /* most slopes held; provisional (2026-10-05) */
typedef struct om_terrain_state {
    uint8_t present;
    uint64_t seed;
    uint32_t cells_w, cells_h;
    int32_t band_floor_cm[OM_TERRAIN_BANDS]; /* band floors, cm */
    int32_t *height_cm;   /* cells_w * cells_h, row-major, cm (fixed point) */
    uint8_t *band;        /* 1 to OM_TERRAIN_BANDS per cell */
    uint8_t *walkable;    /* 0 or 1 per cell */
    uint8_t *walk[OM_TERRAIN_BANDS]; /* terrain stage 2: per engine layer, 1 where a walker may stand; NULL until derived */
    om_slope *slopes;     /* OM_TERRAIN_SLOPE_CAP entries allocated */
    uint32_t slope_count;
    uint32_t gen_id;      /* unsaved, unhashed: identifies a generation for the walk-route caches. See also: csrc/walk_route.c, csrc/terrain.c */
} om_terrain_state;
void om_terrain_state_free(void *state);
void om_terrain_install_net_hooks(om_world *w);
/* Writes the blocked bits for the ground (R-200-02): layers 1..k-1 blocked at every cell; cleared on regenerate. */
void om_terrain_apply_ground(om_world *w);

/* Terrain stage 2 (spec 2026-10-06). Route for a walking unit over the walk mask of its layer, crossing layers only
 * by slope links; see the spec for the return values. Body in csrc/walk_route.c. */
int om_walk_route(const om_world *w, uint32_t unit, double gx, double gy, double *pts, uint32_t cap, double *seconds);
/* Steers every walking unit one tick along its om_walk_route; body in csrc/tactical_move.c. */
void om_move_walker_tick(om_world *w);
/* The route-cache epoch om_move_terrain_changed and om_move_set_canvas_size bump; body in csrc/tactical_move.c, caller csrc/walk_route.c. */
uint32_t om_move_terrain_epoch(om_world *w);
/* Internal, not in the header: the stored walk route of a unit (W2); returns route_n, writes route_i and min(route_n, cap)
 * interleaved (x, y) pairs, a read that changes no checksum. Body in csrc/tactical_move.c.
 * See also: tests/csim/test_VG_W_w2_routes.py */
uint32_t om_move_route_get(const om_world *w, uint32_t unit_id, uint32_t *route_i, double *pts, uint32_t cap);

/* Terrain noise (csrc/terrain_noise.c), integer only, no libm, no world rng.
 * Fixed point is Q16.16 (1.0 = 65536). Lattice spacing is 1.0 in input units.
 *  om_tn_value2: value noise at (x_q16, y_q16), output in [-65536, 65536].
 *  om_tn_fbm2: octaves summed, octave i has amplitude gain_q16^i and double the frequency;
 *    output normalised by the amplitude sum so it stays in [-65536, 65536].
 *  om_tn_sin_q16 / om_tn_cos_q16: angle is a turn fraction in Q16 (65536 = one full turn);
 *    output in [-65536, 65536], exact at the quarter points. */
int32_t om_tn_value2(uint64_t seed, int32_t x_q16, int32_t y_q16);
int32_t om_tn_fbm2(uint64_t seed, int32_t x_q16, int32_t y_q16, int octaves, int32_t gain_q16);
int32_t om_tn_sin_q16(uint32_t turn_q16);
int32_t om_tn_cos_q16(uint32_t turn_q16);

/* Lockstep spec 2026-10-05: net hooks and the per-tick command apply. */
void om_cmd_apply_tick(om_world *w);
void om_unit_install_net_hooks(om_world *w);
void om_move_install_net_hooks(om_world *w);
void om_macro_install_net_hooks(om_world *w);
void om_fog_install_net_hooks(om_world *w);
void om_support_install_net_hooks(om_world *w);
void om_mission_install_net_hooks(om_world *w);
void om_mapgen_install_net_hooks(om_world *w);
void om_generational_install_save_hooks(om_world *w);

/* Internal step hooks. om_step_collisions runs between om_step_reinforce
 * (3e) and om_step_resolve (3f): it groups this tick's pending intents in
 * w->decisions[] by target, resolves every target with two or more intents
 * (ALG-23/24, S-039), writes w->collisions[]/w->collisions_n, and removes
 * the colliding intents from w->decisions[] so om_step_resolve never
 * double-resolves them. See docs/bible/epics/E-05-faction-agents-and-conflict.md
 * R-039-01..06 and csrc/sim.c's tick-order wiring in om_world_step. */
void om_step_events(om_world *w);
void om_faction_step_budget(om_world *w);
void om_step_telegraphs(om_world *w);
void om_step_decisions(om_world *w);
void om_step_reinforce(om_world *w);
void om_step_collisions(om_world *w);
void om_step_resolve(om_world *w);
void om_step_friction(om_world *w);
void om_step_admin_revolts(om_world *w);
/* Tick steps 4.25, 4.5 (E-06) and 6 (E-07); wired in csrc/sim.c between
 * om_step_admin_revolts and the drift loop, and after it, respectively (F2
 * freeze). STUB bodies in csrc/diplomacy.c and csrc/lifecycle.c until B5/B6
 * land. */
void om_step_diplomacy(om_world *w);
void om_step_technology(om_world *w);
void om_step_lifecycle(om_world *w);
/* Per-tick drifting-objective centre refresh (csrc/tactical_support.c); called by unit.c om_tactical_step right after om_macro_tick. */
void om_support_tick(om_world *w);
/* Deadline-baseline hook (csrc/mission.c); called by fog.c om_mission_begin right after the phase moves to tactical. */
void om_mission_on_begin(om_world *w);
/* Resets the one-shot mission_started latch (csrc/fog.c); called by mission.c
 * om_mission_setup so a new mission's recon phase can be re-entered via
 * om_mission_begin. Without this, om_mission_is_started stays true forever
 * after the first mission, and the pipe's in_recon() refuses every later
 * mission_begin ("not in recon"). */
void om_mission_reset_started(om_world *w);
/* B9-N (R-075-02/03/06, R-075-07): the live per-tactical-tick objective
 * evaluation and termination check (csrc/mission.c); called by unit.c
 * om_tactical_step right after om_support_tick, so unit positions/HP are
 * current for the tick. No-op before a mission is set up, before
 * om_mission_build_objectives has run, or after the mission has already
 * ended. */
void om_mission_tactical_tick(om_world *w);
/* Engine visibility (csrc/fog.c; ignores the player-fog switch, S-093 R-093-01): 1 if any living unit of `faction` can see `target`, else 0; unknown ids or no state: 0. */
int om_fog_faction_sees(const om_world *w, int32_t faction, uint32_t target);

/* Spatial hash grid over the tactical units (csrc/unit.c; state in
 * w->tactical_state, rebuilt every tactical tick, updated in place when
 * unit.c moves or spawns a unit). Indexes every living unit (hp > 0; a unit
 * that dies is dropped, one revived by om_unit_set_hp is added back) regardless
 * of faction or layer, at the position unit.c caches (refreshed at the top of
 * each om_tactical_step, so a caller running inside that refresh sees the
 * previous tick's positions: pad r by one tick of movement and re-test with
 * its own positions). A unit matches when dx*dx + dy*dy <= r*r; callers
 * filter everything else.
 * om_grid_query_circle: writes the matching unit ids ascending into out_ids
 * (the lowest `max` when more match) and returns the total match count, so a
 * return above `max` means truncated; a buffer of om_unit_count(w) entries
 * never truncates. The result order is the all-pairs id order.
 * om_grid_iter: for order-independent reductions (any-of, count, sum of
 * per-unit independent updates). Call om_grid_iter_begin, then
 * om_grid_iter_next until it returns 0 (no unit has id 0). Order is
 * deterministic but NOT id order (cell row-major, then last-linked first). The
 * grid must not change (spawn, move, a unit dying) while an iterator is live. */
typedef struct {
    void    *state;
    double   x, y, r;
    int32_t  cx0, cx1, cx, cy, cy1;
    uint32_t cur;
    int      done;
} om_grid_iter;
uint32_t om_grid_query_circle(om_world *w, double x, double y, double r, uint32_t *out_ids, uint32_t max);
void     om_grid_iter_begin(om_grid_iter *it, om_world *w, double x, double y, double r);
uint32_t om_grid_iter_next(om_grid_iter *it);
uint32_t om_grid_query_circle_faction(om_world *w, int32_t faction, double x, double y, double r, uint32_t *out_ids, uint32_t max);
void     om_grid_iter_begin_faction(om_grid_iter *it, om_world *w, int32_t faction, double x, double y, double r);
/* For tactical_move.c: sets unit.c's cached position of a living or dead unit
 * and moves it in the grid, so a query made before the next om_tactical_step
 * sees the new position. Unknown id, NULL world or a world with no tactical
 * state: no-op. Call it after every write of a unit's position outside
 * om_tactical_step (teleport, set_pos, move sync). */
void om_tac_unit_sync_position(om_world *w, uint32_t unit_id, double x, double y);

/* VG K-a: append one event (kind 0 fire, 1 ability, 2 kill, 3 capture) to the tactical event ring (csrc/unit.c). */
#define OM_TAC_EV_CAPTURE 3
void om_tac_event_push(om_world *w, int kind, int a, int b);
/* For fog.c: clear only target_id, no order change. Unknown id: no-op. */
void om_unit_clear_target(om_world *w, uint32_t unit_id);

/* The world RNG (ouroboros_sim.h "the world RNG contract"), csrc/sim.c.
 * om_rng_seed derives rng_state/rng_inc from the seed (om_world_new,
 * om_world_set_seed). om_rng_draw is the one uniform-in-[0,1) draw every
 * consumer calls: forced queue first (om_rng_force), else one PCG32 u. */
void   om_rng_seed(om_world *w, uint64_t seed);
double om_rng_draw(om_world *w);

/* ALG-26 cache recompute (csrc/faction.c). Called by om_faction_set whenever
 * archetype/tech change, and by csrc/worldgen.c's om_world_generate after it
 * writes w->faction_archetype/faction_tech directly (it bypasses om_faction_set
 * to avoid that setter's RNG-consuming confidence roll, R-022-04). */
void om_faction_tech_multipliers_recalc(om_world *w, int32_t faction_id);

#endif /* OM_INTERNAL_H */
