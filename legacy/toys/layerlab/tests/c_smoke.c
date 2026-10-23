/* c_smoke.c -- R0 pass 1 smoke and determinism harness for the C core.
 * Builds the 10 v 5 raider scenario in code, runs seeds 0..19, prints one line per seed, the A win
 * count, a FNV-1a hash of all result bytes and of the seed-0 trace, and the wall time (timing is
 * harness-side only; the sim never reads a clock). Runs seed 0 twice in-process and fails if the
 * bytes differ. Exit 0 ok, 1 determinism failure or ll_run error, 2 A did not win every seed. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "layerlab.h"

#define NSEEDS 20
#define MAX_TICKS 6000

static uint64_t fnv(uint64_t h, const void *p, size_t n) {
    const unsigned char *b = (const unsigned char *)p;
    for (size_t i = 0; i < n; i++) { h ^= b[i]; h *= 1099511628211ULL; }
    return h;
}

static void build(ll_scenario *sc) {
    memset(sc, 0, sizeof *sc);
    ll_rules *r = &sc->rules;
    static const double vis[9]  = {0, 0, 0.2, 0.5, 1.0, 0.5, 0.2, 0, 0};
    static const double vant[9] = {0, 0.2, 0.4, 1.0, 1.0, 1.0, 0.4, 0.2, 0};
    static const double same[9] = {0, 0, 0, 0, 1, 0, 0, 0, 0};
    memcpy(r->vis_factor, vis, sizeof vis);
    memcpy(r->vantage_vis_factor, vant, sizeof vant);
    memcpy(r->range_mult, same, sizeof same);
    memcpy(r->dmg_mult, same, sizeof same);
    memcpy(r->aoe_layer_mult, same, sizeof same);
    r->sensor_elev_bonus_per_layer = 0.15;
    static const double cat[3][3] = {{1.0, 0.75, 1.5}, {1.5, 1.0, 0.75}, {0.20, 1.5, 1.0}};
    memcpy(r->category_mult, cat, sizeof cat);
    r->aoe_cap_mult = 4.0;
    r->pulse_radius = 500; r->pulse_reveal_s = 2.0; r->pulse_cooldown_s = 20.0;
    r->transition_speed_mult = 1.0;
    r->separation_weight = 0.5;
    r->spawn_jitter = 10;
    r->fire_requires_vision = 1;
    r->facing_gates_fire = 0;
    r->halfway_mode = LL_HALFWAY_RULE;
    r->auto_transition = 1;
    r->cover_mode = 1;
    r->chase_when_idle = 0;
    r->forced_change_penalty = 100000;
    r->timed_new_layer_at_half = 1;
    r->max_ticks = MAX_TICKS;
    r->stalemate_ticks = 400;

    ll_unit_type *t = &sc->types[0];                 /* raider, production numbers; flies */
    t->category = LL_CAT_STRIKE;
    t->movement_kind = LL_MOVE_FLY;
    t->hp = 250; t->dmg = 9.0; t->interval_s = 0.8; t->range = 200; t->speed = 150;
    t->sensor = 800; t->transition_s = 1.0; t->aoe_r = 0; t->turn_rate = 6.0; t->arc_deg = 360;
    t->cost = 250 * 9.0 / 0.8 / 31.25;
    t->body_radius = 15;
    sc->n_types = 1;

    ll_terrain *ter = &sc->terrain;
    ter->w_cells = 80; ter->h_cells = 40; ter->cell = 50; ter->layer_spacing = 0;
    memset(ter->open, 0x1F, sizeof ter->open);
    memset(ter->land, 0x1F, sizeof ter->land);

    int n = 0;
    for (int side = 0; side < 2; side++) {
        int count = side == 0 ? 10 : 5;
        for (int k = 0; k < count; k++) {
            ll_spawn *p = &sc->spawns[n++];
            p->side = side;
            p->type = 0;
            p->x = side == 0 ? 1000 : 3000;
            p->y = 1000 + (k - (count - 1) / 2.0) * 37.5;
            p->facing_deg = side == 0 ? 0 : 180;
            p->layer = 3;
            p->order = LL_ORDER_ATTACK_MOVE;
            p->gx = side == 0 ? 3000 : 1000;
            p->gy = 1000;
            p->pulse_tick = -1;
            p->ping_tick = -1;       /* test-defect fix 2026-10-01: zero means "ping at tick 0" since ABI 3 validates it */
            p->target_policy = LL_TARGET_NEAREST;
        }
    }
    sc->n_spawns = n;
}

int main(void) {
    if (ll_abi_version() != LL_ABI_VERSION) { printf("FAIL abi version\n"); return 1; }
    static ll_scenario sc;
    build(&sc);

    size_t rec = (size_t)sc.n_spawns;
    ll_trace_rec *buf = malloc((size_t)MAX_TICKS * rec * sizeof *buf);
    ll_trace_rec *buf2 = malloc((size_t)MAX_TICKS * rec * sizeof *buf2);
    if (!buf || !buf2) { printf("FAIL alloc\n"); return 1; }

    uint64_t hres = 1469598103934665603ULL, htr = 1469598103934665603ULL;
    int a_wins = 0;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int seed = 0; seed < NSEEDS; seed++) {
        ll_result res;
        ll_trace tr = {buf, MAX_TICKS, 0};
        if (ll_run(&sc, (uint64_t)seed, &res, seed == 0 ? &tr : NULL) != 0) {
            printf("FAIL ll_run seed %d: %s\n", seed, ll_last_error());
            return 1;
        }
        static const char *names[] = {"none", "A", "B", "stalemate", "cap", "mutual"};
        printf("seed %2d winner %-9s ticks %4d survivors A %2d B %2d hp_ratio A %.4f B %.4f\n",
               seed, names[res.winner], res.ticks, res.survivors[0], res.survivors[1],
               res.hp_ratio[0], res.hp_ratio[1]);
        if (res.winner == LL_WIN_A) a_wins++;
        hres = fnv(hres, &res, sizeof res);
        if (seed == 0) {
            htr = fnv(htr, &tr.ticks_written, sizeof tr.ticks_written);
            htr = fnv(htr, buf, (size_t)tr.ticks_written * rec * sizeof *buf);
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double secs = (double)(t1.tv_sec - t0.tv_sec) + (double)(t1.tv_nsec - t0.tv_nsec) * 1e-9;
    printf("A wins %d/%d\n", a_wins, NSEEDS);
    printf("HASH results %016llx trace0 %016llx\n", (unsigned long long)hres, (unsigned long long)htr);
    printf("TIME %d seeds %.3f s\n", NSEEDS, secs);

    /* in-process repeat: seed 0 twice, result and trace bytes must match */
    ll_result r1, r2;
    ll_trace t_1 = {buf, MAX_TICKS, 0}, t_2 = {buf2, MAX_TICKS, 0};
    if (ll_run(&sc, 0, &r1, &t_1) || ll_run(&sc, 0, &r2, &t_2)) { printf("FAIL repeat run\n"); return 1; }
    if (memcmp(&r1, &r2, sizeof r1) != 0 || t_1.ticks_written != t_2.ticks_written ||
        memcmp(buf, buf2, (size_t)t_1.ticks_written * rec * sizeof *buf) != 0) {
        printf("FAIL in-process determinism: seed 0 differs between two runs\n");
        return 1;
    }
    printf("OK in-process repeat identical\n");

    free(buf);
    free(buf2);
    return a_wins == NSEEDS ? 0 : 2;
}
