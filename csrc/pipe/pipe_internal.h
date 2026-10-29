#ifndef OM_PIPE_INTERNAL_H
#define OM_PIPE_INTERNAL_H
/* Shared by csrc/pipe/pipe_*.c: the frame/JSON helpers and the pipe's world state (split out of om_pipe.c). */
#include <dirent.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ouroboros_sim.h"
#include "om_constants.h"

#define OM_PIPE_SAVE_FORMAT_VERSION 13

/* csrc/generational.c GEN_PHASE_BRIEFING / GEN_PHASE_MISSION, not exported
 * by ouroboros_sim.h. See the file-header comment above. */
#define OM_PIPE_CHAPTER_PHASE_BRIEFING 0
#define OM_PIPE_CHAPTER_PHASE_MISSION 2
/* csrc/mission.c OM_MISSION_BAND_REFUSAL, not exported by ouroboros_sim.h. */
#define OM_PIPE_MISSION_BAND_REFUSAL 5
/* Upper bound on unit slots scanned with om_unit_id_at. */
#define OM_PIPE_UNIT_SCAN_MAX 1000000
/* docs/architecture.md tactical frame: a full frame every 20th step. */
#define OM_PIPE_FULL_PERIOD 20

typedef struct {
    char *buf;
    size_t len;
    size_t cap;
} jbuf;

typedef struct {
    uint32_t id;
    int32_t faction, type, layer, target;
    double x, y, hp, facing;
    uint64_t seen;
    int32_t tier, state, tl, sight;
    int64_t acd, ld;
} tac_unit;

typedef struct {
    int in;
    int32_t type, owner, cap, next_type;
    int64_t nst, period;
    double x, y, hp;
    uint64_t seen;
} tac_struct;

/* A7 delta-frame state: the unit values in the last tactical frame written,
 * indexed by unit id, and the sim steps run since mission_begin. */
typedef struct {
    tac_unit *by_id;
    uint32_t cap;
    uint32_t *prev_ids;
    uint32_t n_prev, cap_prev;
    uint64_t serial, steps;
    tac_struct *st_by_id;
    uint32_t st_cap;
    uint32_t *st_prev;
    uint32_t n_st_prev, cap_st_prev;
} pipe_tac_state;

extern om_world *W;
extern uint64_t g_tick;
extern int g_roster_types;
extern uint32_t g_n_regions;
extern uint64_t g_tactical_tick;
extern int g_net_full_next;
extern uint32_t g_n_placed_structures;
extern uint32_t g_mission_archetype;
extern pipe_tac_state g_tac;
extern int g_fog_filter;

int read_frame(char **out_buf, uint32_t *out_len);
void write_frame(const char *buf, uint32_t len);
void jb_init(jbuf *j);
void jb_free(jbuf *j);
void jb_reserve(jbuf *j, size_t extra);
void jb_raw(jbuf *j, const char *s);
void jb_putc(jbuf *j, char c);
void jb_str(jbuf *j, const char *s);
void jb_key(jbuf *j, const char *k);
void jb_int(jbuf *j, int64_t v);
void jb_uint(jbuf *j, uint64_t v);
void jb_double(jbuf *j, double v);
void jb_bool(jbuf *j, int v);
const char *find_key(const char *json, const char *key);
int get_str(const char *json, const char *key, char *out, size_t cap);
int get_i64(const char *json, const char *key, int64_t *out);
int get_f64(const char *json, const char *key, double *out);
int get_bool(const char *json, const char *key, int *out);
int get_int_array(const char *json, const char *key, int *out, int max);
void realloc_regions(uint32_t n);
void capture_baseline(void);
void write_ack(const char *name);
void write_error(const char *name, const char *reason);
void write_snapshot(void);
int in_recon(void);
int mission_refused(void);
void hex_put(jbuf *j, const uint8_t *b, uint32_t n);
void write_tactical(int full);
void ev_reset(void);
void ev_collect_step(void);
void ev_collect_abilities(void);
void handle_net_reset(void);
void handle_net_submit(const char *json);
void handle_net_step(const char *json);
void handle_net_checksum(void);
void handle_net_log_dump(void);
void handle_net_log_load(const char *json);
void handle_net_state_get(void);
void handle_net_state_put(const char *json);
void handle_net_state_diff(const char *json);
void handle_terrain_generate(const char *json);
void handle_terrain_dump(void);
void handle_lots_dump(void);
void write_lot_row(jbuf *j, const om_lot *l);
void handle_terrain_probe(const char *json);

#endif
