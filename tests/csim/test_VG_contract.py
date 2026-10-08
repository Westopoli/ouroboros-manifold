"""Visible-game programme lane K, piece K-a (sim side: unit.c, tactical_support.c, mission.c,
tactical_mapgen.c, terrain.c; the K0 symbols they implement). Written against
docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, section 1 "Contract gates" and section 2
(the field table). Fenced: builders never edit this file.

The getters are driven against a hand-built fixture world (no pipe). fog.c and tactical_move.c reuse
existing getters (om_fog_get_drawn_sensor_circle_radius, om_unit_get_target_layer,
om_unit_transition_progress), so their field shapes are proved through the pipe frame in
tests/transport/test_pipe_vg_contract.py, not here.

Assumed prototypes (section 1 names the symbols, not their arguments; reconcile with K0's
signatures.toml if it differs -- a mismatch is a K0 question, not a test defect):
  uint32_t om_tactical_event_count(om_world*)                      events of the last om_tactical_step call
  int      om_tactical_event_get_at(om_world*, uint32_t i, int32_t *kind, uint32_t *a, int32_t *b, uint64_t *tick)
  uint32_t om_structure_count(const om_world*)                     structures in the world
  uint32_t om_structure_get_at(const om_world*, uint32_t i)        the i-th structure's slot id (UINT32_MAX out of range)
  int      om_objective_get_done(const om_world*, uint32_t idx)     0 open, 1 complete, 2 failed, -1 no such objective
  uint32_t om_map_obstacle_count(const om_world*)
  int      om_map_get_obstacle_at(const om_world*, uint32_t i, double *x, double *y, double *r)  (mirrors om_map_cover_at)
  uint32_t om_terrain_get_heights(const om_world*, int32_t *out, uint32_t cap)   cm, row-major, returns the cell count
Event kinds: 0 fire(a shooter, b target), 1 ability, 2 kill(a unit, b killer or -1), 3 capture(a structure, b new owner).
"""
import ctypes

import pytest

from b1_macro_scene import ENEMY_FAC, PLAYER_FAC, tactical_world

W = ctypes.c_void_p
NEW_SYMBOLS = [
    "om_tactical_event_count", "om_tactical_event_get_at", "om_structure_count", "om_structure_get_at",
    "om_objective_get_done", "om_map_obstacle_count", "om_map_get_obstacle_at", "om_terrain_get_heights",
]
EVENT_CAP = 512
U32, I32, U64, DBL = ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint64, ctypes.c_double


def bind(lib):
    """Fail (AttributeError -> red) when a K0 symbol is missing, then set the assumed prototypes."""
    missing = [n for n in NEW_SYMBOLS if not hasattr(lib, n)]
    assert not missing, f"K0 symbols missing from libouroboros.so: {missing}"
    lib.om_tactical_event_count.argtypes, lib.om_tactical_event_count.restype = [W], U32
    lib.om_tactical_event_get_at.argtypes = [W, U32, ctypes.POINTER(I32), ctypes.POINTER(U32),
                                             ctypes.POINTER(I32), ctypes.POINTER(U64)]
    lib.om_tactical_event_get_at.restype = ctypes.c_int
    lib.om_structure_count.argtypes, lib.om_structure_count.restype = [W], U32
    lib.om_structure_get_at.argtypes, lib.om_structure_get_at.restype = [W, U32], U32
    lib.om_objective_get_done.argtypes, lib.om_objective_get_done.restype = [W, U32], ctypes.c_int
    lib.om_map_obstacle_count.argtypes, lib.om_map_obstacle_count.restype = [W], U32
    lib.om_map_get_obstacle_at.argtypes = [W, U32, ctypes.POINTER(DBL), ctypes.POINTER(DBL), ctypes.POINTER(DBL)]
    lib.om_map_get_obstacle_at.restype = ctypes.c_int
    lib.om_terrain_get_heights.argtypes, lib.om_terrain_get_heights.restype = [W, ctypes.POINTER(I32), U32], U32


def events(lib, w):
    out = []
    for i in range(lib.om_tactical_event_count(w)):
        k, a, b, t = I32(), U32(), I32(), U64()
        assert lib.om_tactical_event_get_at(w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0
        out.append((k.value, a.value, b.value, t.value))
    return out


def duel(lib, world_factory, n_each=1):
    """Two opposing groups 100 wu apart (inside Raider range 200), on layer 0, phase 1 (begun)."""
    w = tactical_world(lib, world_factory, seed=11)
    mine = [lib.om_unit_spawn(w, 0, PLAYER_FAC, 8000.0 + 30 * i, 8000.0, 0) for i in range(n_each)]
    theirs = [lib.om_unit_spawn(w, 0, ENEMY_FAC, 8100.0 + 30 * i, 8000.0, 0) for i in range(n_each)]
    return w, mine, theirs


def run_collect(lib, w, steps):
    out = []
    for _ in range(steps):
        lib.om_tactical_step(w)
        out.append(events(lib, w))
    return out


# ---- K0 presence (hasattr only; K0's own test also pins ABI 5) ----

@pytest.mark.parametrize("name", NEW_SYMBOLS)
def test_k0_symbol_is_exported(lib, name):
    """S-087 (K-a data lane): every K0 symbol exists in libouroboros.so. Positive control: an existing symbol
    (om_unit_spawn) is found by the same check, and a made-up one is not."""
    assert hasattr(lib, "om_unit_spawn") and not hasattr(lib, "om_not_a_symbol_vg")
    assert hasattr(lib, name), f"{name} is not exported"


# ---- unit.c: fire and kill events ----

def test_duel_emits_fire_events_naming_shooter_and_target_with_the_call_tick(lib, world_factory):
    """S-087 (R-087-04 shoots the nearest thing in range), S-085: a one-step call that fires has fire events
    [0, shooter, target, tick]; the tick equals the world's tactical tick for that call. Red on main: no getter."""
    bind(lib)
    w, mine, theirs = duel(lib, world_factory)
    per_call = run_collect(lib, w, 200)
    fires = [(i, e) for i, evs in enumerate(per_call) for e in evs if e[0] == 0]
    assert fires, "no fire event in 200 steps of a 100 wu duel"
    for _, (k, a, b, t) in fires:
        assert a in mine + theirs and b in mine + theirs and a != b
    ticks = {e[3] for _, e in fires}
    assert all(isinstance(t, int) and t >= 0 for t in ticks)
    assert per_call[0] == [] or all(e[3] == per_call[0][0][3] for e in per_call[0])


def test_events_reset_each_call_and_never_exceed_the_cap(lib, world_factory):
    """S-087 (R-087-04), spec section 2 "cap 512 per call": the count is per om_tactical_step call (a quiet
    call after the duel reads 0, so the ring does not accumulate) and a 150-unit melee stays <= 512. Red on main."""
    bind(lib)
    w, _, _ = duel(lib, world_factory, n_each=75)
    worst = 0
    for _ in range(300):
        lib.om_tactical_step(w)
        n = lib.om_tactical_event_count(w)
        worst = max(worst, n)
        assert n <= EVENT_CAP
    assert worst > 0, "control: the melee produced no events at all"
    quiet = tactical_world(lib, world_factory, seed=12)
    lib.om_unit_spawn(quiet, 0, ENEMY_FAC, 100_000.0, 100_000.0, 0)
    lib.om_tactical_step(quiet)
    assert lib.om_tactical_event_count(quiet) == 0


def test_a_dead_unit_gets_one_kill_event_naming_its_killer(lib, world_factory):
    """S-087, S-085 (R-087-04): when a unit's hp reaches 0 exactly one kill event [2, victim, killer, tick] is
    emitted for it, with the killer an opposing unit id (or -1). Red on main."""
    bind(lib)
    w, mine, theirs = duel(lib, world_factory, n_each=3)
    kills = [e for evs in run_collect(lib, w, 3000) for e in evs if e[0] == 2]
    dead = [u for u in mine + theirs if not lib.om_unit_alive(w, u)]
    assert dead, "control: nobody died in 3000 steps"
    assert sorted(e[1] for e in kills) == sorted(dead), (kills, dead)
    for _, victim, killer, _t in kills:
        assert killer == -1 or lib.om_unit_get_faction(w, killer) != lib.om_unit_get_faction(w, victim)


def test_ability_events_come_from_the_ability_ring(lib, world_factory):
    """S-086 (R-096-05), S-135: an activated ability gives an ability event [1, unit, ability id, tick] in that
    call, matching om_tick_read_ability_events (read once per call by the pipe). Red on main: no getter."""
    bind(lib)
    w, mine, _ = duel(lib, world_factory)
    assert lib.om_command_activate_ability(w, (U32 * 1)(mine[0]), 1, DBL(0.0), DBL(0.0)) == 0
    lib.om_tactical_step(w)
    evs = [e for e in events(lib, w) if e[0] == 1]
    assert evs and evs[0][1] == mine[0], evs


# ---- tactical_support.c: structures ----

def hand_structures(lib, w):
    # slots 3 and 4: the seed-11 world already holds mission structures in slots 0..2 (TD-VG-K-9)
    for slot, (x, y, owner) in enumerate(((3000.0, 3000.0, PLAYER_FAC), (9000.0, 9000.0, ENEMY_FAC)), start=3):
        lib.om_structure_init(w, slot, 0, DBL(100.0))
        lib.om_structure_set_owner(w, slot, owner)
        lib.om_structure_set_position(w, slot, x, y)


def test_structure_getters_enumerate_the_world_structures(lib, world_factory):
    """S-209 (R-126-*), R-205-02: om_structure_count equals the structures built (2) and om_structure_get_at(i)
    lists each slot once, in ascending order, past the end answers the out-of-range value. Red on main."""
    bind(lib)
    w = tactical_world(lib, world_factory, seed=11)
    n0 = lib.om_structure_count(w)
    hand_structures(lib, w)
    assert lib.om_structure_count(w) == n0 + 2
    ids = [lib.om_structure_get_at(w, i) for i in range(lib.om_structure_count(w))]
    assert len(set(ids)) == len(ids) and ids == sorted(ids)
    assert lib.om_structure_get_at(w, lib.om_structure_count(w)) == 0xFFFFFFFF


def test_structure_capture_emits_a_capture_event(lib, world_factory):
    """S-209 (R-126-*): when a structure changes owner during a step, a capture event [3, structure, new owner,
    tick] is in that call's events. Fixture: an enemy-held structure with a player unit parked at it. Red on main."""
    bind(lib)
    w, mine, theirs = duel(lib, world_factory)
    hand_structures(lib, w)
    lib.om_unit_spawn(w, 0, PLAYER_FAC, 9000.0, 9000.0, 0)
    seen = [e for evs in run_collect(lib, w, 6000) for e in evs if e[0] == 3]
    assert seen, "no capture event in 6000 steps with a player unit on an enemy structure"
    assert seen[0][2] == PLAYER_FAC and lib.om_structure_get_owner(w, seen[0][1]) == PLAYER_FAC


# ---- mission.c: objective done ----

def test_objective_done_reads_open_complete_and_missing(lib, world_factory):
    """S-209, R-104-01 (objectives {i,progress,done}): 0 while open, 1 once its stored completion is 1.0, -1 for an index that does not exist. Red on main: no getter."""
    bind(lib)
    w = tactical_world(lib, world_factory, seed=11)
    lib.om_mission_build_objectives(w, 0)
    assert lib.om_mission_objective_count(w) >= 1
    assert lib.om_objective_get_done(w, 0) == 0
    lib.om_mission_set_objective_completion(w, 0, DBL(1.0))   # stored completion 1.0 reads as done, no step needed
    assert lib.om_objective_get_done(w, 0) == 1
    assert lib.om_objective_get_done(w, 999) == -1


# ---- tactical_mapgen.c: obstacles ----

def test_obstacle_getters_return_what_was_added(lib, world_factory):
    """S-007 (R-007-*), spec section 2 `map.obstacles[{x,y,r}]`: om_map_obstacle_count counts
    om_map_add_obstacle calls and om_map_get_obstacle_at returns each one's x, y, r in order; out of range
    answers non-zero. Red on main: no getter."""
    bind(lib)
    w = tactical_world(lib, world_factory, seed=11)
    n0 = lib.om_map_obstacle_count(w)
    rows = [(1000.0, 2000.0, 120.0), (5000.0, 6000.0, 300.0)]
    for x, y, r in rows:
        assert lib.om_map_add_obstacle(w, DBL(x), DBL(y), DBL(r)) != 0xFFFFFFFF
    assert lib.om_map_obstacle_count(w) == n0 + 2
    for i, (x, y, r) in enumerate(rows):
        ox, oy, orr = DBL(), DBL(), DBL()
        assert lib.om_map_get_obstacle_at(w, n0 + i, ctypes.byref(ox), ctypes.byref(oy), ctypes.byref(orr)) == 0
        assert (ox.value, oy.value, orr.value) == (x, y, r)
    ox, oy, orr = DBL(), DBL(), DBL()
    assert lib.om_map_get_obstacle_at(w, n0 + 2, ctypes.byref(ox), ctypes.byref(oy), ctypes.byref(orr)) != 0


# ---- terrain.c: heights ----

def test_terrain_heights_match_the_height_field_in_cm(lib, world_factory):
    """S-236, R-001-* (terrain_dump `heights`): om_terrain_get_heights fills one int32 per cell (cm, row-major)
    and returns cells_w*cells_h; each value is the cell-centre height from om_terrain_height_at times 100,
    rounded (1 cm of rounding allowed). Red on main: no getter."""
    bind(lib)
    w = world_factory(n_regions=1)
    canvas = 16000.0
    assert lib.om_map_set_canvas(w, DBL(canvas), DBL(canvas)) == 0
    assert lib.om_terrain_generate(w, 11, DBL(canvas), DBL(canvas)) == 0
    cw, ch = U32(), U32()
    lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    n = cw.value * ch.value
    buf = (I32 * n)()
    assert lib.om_terrain_get_heights(w, buf, n) == n
    cell = canvas / cw.value
    for cy, cx in ((0, 0), (3, 7), (ch.value // 2, cw.value // 2), (ch.value - 1, cw.value - 1)):
        want = lib.om_terrain_height_at(w, DBL((cx + 0.5) * cell), DBL((cy + 0.5) * cell)) * 100.0
        assert abs(buf[cy * cw.value + cx] - want) <= 1.0, (cx, cy, buf[cy * cw.value + cx], want)
    assert len(set(buf)) > 1, "heights are flat"
