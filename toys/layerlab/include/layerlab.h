/* layerlab.h -- public ABI of the layer lab (toys/layerlab).
 *
 * Standalone. Shares no code with csrc/ and is not a game contract. The numbers
 * it starts from come from csrc/om_constants.h; the rules it carries come from
 * docs/bible/epics/E-01-layer-system.md and the register rows named in
 * toys/layerlab/SPEC.md. Everything rule-shaped is a runtime field in
 * ll_rules, never a compile-time constant.
 *
 * Contract status: this header is written by the Architect before any C. The
 * Engineer implements against it and does not edit it; a change goes back to
 * the Architect. The Python mirror (layerlab/ffi.py) is checked against
 * ll_sizeof() and ll_abi_version() at import.
 *
 * Conventions
 *   - Layers are 1-based (1..LL_LAYERS), layer 1 is the bottom. 0 means "none".
 *   - Signed offset index: LL_OFFS(from_layer, to_layer) = (to - from) + 4, 0..8.
 *     Positive means "to" is above "from". Tables indexed this way are
 *     [offset 0 -> four below] ... [4 -> same layer] ... [8 -> four above].
 *   - Units: world units, seconds, degrees at the ABI, radians inside.
 *     Sim step is 1/LL_TICKS_PER_SEC s.
 *   - Every double is IEEE binary64; the sim is built with the determinism
 *     flags in SPEC.md section 9.
 */
#ifndef LAYERLAB_H
#define LAYERLAB_H

#include <stdint.h>

#define LL_ABI_VERSION     4u

#define LL_LAYERS          5
#define LL_TICKS_PER_SEC   20
#define LL_MAX_UNITS       4096     /* both sides together */
#define LL_MAX_TYPES       16
#define LL_MAX_COVER       32
#define LL_MAX_VANTAGE     16
#define LL_MAX_ZONES       16
#define LL_MAX_SLOPES      16
#define LL_MAX_GRID_W      128      /* cells */
#define LL_MAX_GRID_H      64
#define LL_MAX_CELLS       (LL_MAX_GRID_W * LL_MAX_GRID_H)

#define LL_OFFS(from_layer, to_layer)  ((int)(to_layer) - (int)(from_layer) + 4)

/* ---- enums (int32 on the wire) ---- */
enum { LL_CAT_STRIKE = 0, LL_CAT_LINE = 1, LL_CAT_SIEGE = 2 };
enum { LL_MOVE_FLY = 0, LL_MOVE_WALK = 1 };              /* flying/swimming vs walking (Q-004-04) */
enum { LL_ABILITY_NONE = 0, LL_ABILITY_BURST = 1 };      /* the "storm" shape */
enum { LL_ORDER_HOLD = 0, LL_ORDER_MOVE = 1, LL_ORDER_ATTACK_MOVE = 2 };
enum { LL_TARGET_NEAREST = 0, LL_TARGET_LOWEST_HP = 1, LL_TARGET_HIGHEST_COST = 2 };
enum { LL_HALFWAY_BOTH = 0, LL_HALFWAY_RULE = 1, LL_HALFWAY_UNTARGETABLE = 2 };
enum { LL_WIN_NONE = 0, LL_WIN_A = 1, LL_WIN_B = 2, LL_WIN_STALEMATE = 3,
       LL_WIN_CAP = 4, LL_WIN_MUTUAL = 5 };

/* ---- the rule set: every knob the lab sweeps (SPEC.md section 4) ---- */
typedef struct ll_rules {
    /* vision, by signed offset (observer -> target) */
    double vis_factor[9];            /* cross-layer sensing factor */
    double vantage_vis_factor[9];    /* used when the observer stands in a vantage disc */
    double sensor_elev_bonus_per_layer;  /* effective *= max(0, 1 + bonus * (obs_layer - tgt_layer)) */
    /* cross-layer combat, by signed offset (attacker -> target) */
    double range_mult[9];            /* 0 = cannot fire at that offset */
    double dmg_mult[9];
    double aoe_layer_mult[9];        /* area damage to a unit at that offset from the shooter */
    double category_mult[3][3];      /* [attacker category][target category] */
    double aoe_cap_mult;             /* per target per tick: area damage <= cap * largest area hit */
    /* pulse (lab: fired at spawn.pulse_tick, never by heuristic) */
    double pulse_radius;
    double pulse_reveal_s;
    double pulse_cooldown_s;
    /* motion */
    double transition_speed_mult;    /* speed factor during a timed transfer (not on a slope) */
    double separation_weight;        /* 0..1: strength of same-layer overlap push-out */
    double spawn_jitter;             /* +- world units on x and y, drawn per spawn */
    /* going dark (E-01 S-163; ABI 3). Indexed by the state of the unit concerned: 0 silent, 1 emit. They multiply a
     * cross-layer sensing radius (own layer unchanged): the observer's state scales how far it sees, the target's
     * state scales how far it is seen from. Ignored unless emit_on = 1. */
    double emit_see_mult[2];
    double emit_seen_mult[2];
    /* targeted ping (E-01 S-162; ABI 3): a ping aimed at a layer and a place by a unit with spawn.ping_tick >= 0 */
    double ping_reach;               /* max xy distance from the pinger to the pinged place */
    double ping_radius;              /* xy radius around the place that is revealed, on the pinged layer only */
    double ping_s;                   /* seconds the reveal lasts (a very short burst) */
    double ping_cooldown_s;          /* seconds before the same unit can ping again (the only limit) */
    /* switches (0/1 unless stated) */
    int32_t fire_requires_vision;    /* target must be in the shooter's side's visible set */
    int32_t facing_gates_fire;       /* shooter must be inside its firing arc */
    int32_t halfway_mode;            /* LL_HALFWAY_* */
    int32_t auto_transition;         /* R-001-05; 0 is the control: stop at the edge */
    int32_t cover_mode;              /* 0 cover off; 1 height-interpolated LOS (SPEC.md 5.3) */
    int32_t chase_when_idle;         /* hold / arrived units chase visible enemies */
    int32_t forced_change_penalty;   /* path cost per layer of a forced change, world units;
                                        large (100000) = a detour always wins (Q-001-04 a);
                                        0 = shortest route wins (Q-001-04 b) */
    int32_t timed_new_layer_at_half; /* 1: a timed transfer counts as on the new layer from the
                                        halfway point (Q-004-05 a4); 0: old layer until done */
    int32_t max_ticks;
    int32_t stalemate_ticks;         /* consecutive ticks with no HP lost anywhere ends the run */
    int32_t emit_on;                 /* 0: the emit/silent multipliers are ignored (legacy behaviour) */
    int32_t pad0_, pad1_, pad2_;
} ll_rules;

/* ---- a unit type ---- */
typedef struct ll_unit_type {
    int32_t category;                /* LL_CAT_* */
    int32_t movement_kind;           /* LL_MOVE_* */
    double  hp;
    double  dmg;                     /* per hit */
    double  interval_s;
    double  range;
    double  speed;                   /* world units / s */
    double  sensor;                  /* sensor radius */
    double  transition_s;            /* timed transfer duration (not used on a slope) */
    double  aoe_r;                   /* 0 = single target */
    double  turn_rate;               /* rad / s */
    double  arc_deg;                 /* firing arc, 360 = no arc */
    double  cost;                    /* reporting only (cost_lost) */
    double  body_radius;
    int32_t ability_kind;            /* LL_ABILITY_* */
    int32_t ab_min_targets;
    double  ab_dmg_mult;             /* x dmg, applied to every enemy in ab_radius */
    double  ab_radius;
    double  ab_windup_s;
    double  ab_cooldown_s;
    int32_t pulse_capable;
    int32_t pad_;
    /* reach by unit type (E-01 S-164; ABI 3): multiplier on this type's range by signed offset (target layer minus
     * its own, +4; index 4 is its own layer). 0 means it cannot fire at that offset whatever the distance. Used only
     * when reach_on = 1; with 0 every offset is 1.0, the legacy behaviour. Multiplies the global rules tables. */
    double  reach[9];
    int32_t reach_on;
    int32_t pad2_;
} ll_unit_type;

/* ---- terrain ---- */
typedef struct ll_cover   { double x, y, r; int32_t height_layer; int32_t pad_; } ll_cover;
typedef struct ll_vantage { double x, y, r; } ll_vantage;
typedef struct ll_zone    { double x, y, r, intensity; int32_t layer; int32_t pad_; } ll_zone;

/* A slope is a corridor of ground joining two layers, adjacent or not.
 * (x0,y0) is the centre of the bottom edge on layer bottom_layer; (dx,dy) is the
 * unit direction toward the top edge on layer top_layer; length and width in
 * world units. Position along the slope t = projection / length, 0 at the bottom
 * edge, 1 at the top edge. Cross-overs are at t_k = (k - 0.5) / n for
 * k = 1..n, n = top_layer - bottom_layer (Q-004-05 a3); n = 1 gives the midline
 * at t = 0.5. */
typedef struct ll_slope {
    double  x0, y0, dx, dy, length, width;
    int32_t bottom_layer, top_layer;
} ll_slope;

typedef struct ll_terrain {
    int32_t  w_cells, h_cells;       /* <= LL_MAX_GRID_W, LL_MAX_GRID_H */
    double   cell;                   /* cell edge, world units; arena = (w*cell) x (h*cell) */
    double   layer_spacing;          /* world height per layer: vertical term of the sensing and range
                                        distance (SPEC.md 5.2); 0 = planar */
    uint8_t  open[LL_MAX_CELLS];     /* bit (layer-1): layer open here (flyers may occupy) */
    uint8_t  land[LL_MAX_CELLS];     /* bit (layer-1): ground a walker can stand on; subset of open */
    int32_t  n_cover, n_vantage, n_zone, n_slope;
    ll_cover   cover[LL_MAX_COVER];
    ll_vantage vantage[LL_MAX_VANTAGE];
    ll_zone    zone[LL_MAX_ZONES];
    ll_slope   slope[LL_MAX_SLOPES];
} ll_terrain;                        /* cell index = cy * w_cells + cx */

/* ---- one unit to place ---- */
typedef struct ll_spawn {
    int32_t side;                    /* 0 = A, 1 = B */
    int32_t type;                    /* index into types[] */
    double  x, y;
    double  facing_deg;
    int32_t layer;                   /* 1..LL_LAYERS, must be open (and land for walkers) at x,y */
    int32_t order;                   /* LL_ORDER_* */
    double  gx, gy;                  /* order goal */
    int32_t pre_revealed;            /* 1: visible to the other side for the whole run */
    int32_t transfer_layer;          /* 0 none; else a timed transfer to this layer (flyers only) */
    int32_t transfer_tick;           /* tick at which that transfer is ordered */
    int32_t pulse_tick;              /* -1 none; else tick at which a pulse-capable unit pulses */
    int32_t target_policy;           /* LL_TARGET_* */
    int32_t pad_;
    /* going dark (ABI 3): initial state 1 emit / 0 silent, and one scheduled switch */
    int32_t emit;
    int32_t emit_switch_tick;        /* -1 none */
    int32_t emit_switch_to;          /* state after the switch */
    /* targeted ping (ABI 3): this unit pings at ping_tick (-1 none) the layer ping_layer at (ping_x, ping_y) */
    int32_t ping_tick;
    int32_t ping_layer;
    int32_t pad2_;
    double  ping_x, ping_y;
} ll_spawn;

typedef struct ll_scenario {
    ll_rules     rules;
    ll_unit_type types[LL_MAX_TYPES];
    int32_t      n_types;
    int32_t      n_spawns;
    ll_terrain   terrain;
    ll_spawn     spawns[LL_MAX_UNITS];     /* unit id = index in this array */
} ll_scenario;

/* ---- outputs ---- */
typedef struct ll_unit_out {
    double  x, y, hp;
    int32_t layer;                   /* the layer the unit counts as being on at the end */
    int32_t alive;
    int32_t transitions;             /* completed or abandoned layer changes begun */
    int32_t pad_;
} ll_unit_out;

typedef struct ll_result {
    int32_t winner;                  /* LL_WIN_* */
    int32_t ticks;
    int32_t survivors[2];
    double  hp_ratio[2];             /* remaining HP / starting HP, per side */
    double  cost_lost[2];
    double  damage_dealt[2];
    int32_t shots[2];
    int32_t transitions;
    int32_t first_shot_side;         /* -1 none */
    int32_t first_shot_tick;         /* -1 none */
    int32_t first_contact_tick;      /* first tick a side saw an enemy; -1 none */
    int32_t unanswered_ticks[2];     /* ticks on which this side fired and the other side did not */
    int32_t alive_ticks[2];
    int32_t firing_ticks[2];
    double  firing_weight[2];
    /* ping alerts (ABI 3): when a ping first reveals at least one unit of a side, that side is alerted. The alert
     * is the tick and a unit vector from the revealed units' centroid toward the pinger (the player is shown a
     * sector of about 60 degrees around it; the engine only reports the direction). -1 / 0 when never. */
    int32_t alerted_tick[2];
    int32_t alerts[2];             /* number of pings that revealed the side */
    double  alert_dir_x[2], alert_dir_y[2];
    ll_unit_out unit[LL_MAX_UNITS];
} ll_result;

/* ---- optional per-tick trace: n_spawns records per tick, tick-major ---- */
typedef struct ll_trace_rec {        /* 20 bytes */
    float   x, y, hp;
    float   progress;                /* transition progress 0..1, 0 when not changing layer */
    uint8_t layer, side, alive, flags;   /* flags: bit0 changing layer, bit1 fired this tick,
                                            bit2 on a slope, bit3 visible to the other side,
                                            bit4 can fire this tick */
} ll_trace_rec;

typedef struct ll_trace {
    ll_trace_rec *buf;               /* caller-owned, capacity_ticks * n_spawns records */
    int32_t       capacity_ticks;
    int32_t       ticks_written;     /* set by ll_run */
} ll_trace;

/* ---- entry points ---- */
uint32_t ll_abi_version(void);

/* which: 0 ll_rules, 1 ll_unit_type, 2 ll_terrain, 3 ll_spawn, 4 ll_scenario,
 *        5 ll_result, 6 ll_trace_rec. Returns sizeof. */
uint32_t ll_sizeof(int which);

/* Runs one engagement to termination. trace may be NULL. Returns 0, or a
 * nonzero error (1 bad scenario: see ll_last_error). Deterministic: the same
 * scenario bytes and seed give a byte-identical result and trace. */
int ll_run(const ll_scenario *sc, uint64_t seed, ll_result *out, ll_trace *trace);

/* Isolation probes (tests). All evaluate the state at tick 0 after spawn
 * placement, with no draws beyond those spawn needs. */
int ll_probe_can_see(const ll_scenario *sc, uint64_t seed, int observer, int target);

const char *ll_last_error(void);

#endif /* LAYERLAB_H */
