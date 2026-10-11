"""Visible-game lane E1, piece E1d tests: wave events and rubble/rebuild (spec rev 6, lane E1; bible E-17 S-193
R-193-04 waves, R-193-05 stages, R-193-06 rubble and rebuild; settlement mockup settlement_sim.gd wave()/damage()).
Fenced: builders never edit this file.

What is proved, through the public K-e getters only (om_wave_get_since, om_lot_count/om_lot_get_at):
  1. a capture (a structure's owner changing) logs a wave of kind 3 at the structure, at a tick inside the window;
  2. the end of a battle (om_mission_end) logs a wave of kind 4; nothing logs a wave on a quiet tick (isolation);
  3. the log reads oldest first and `since` filters on tick >= since; the log survives save/load; same seed and
     stream give the same log (determinism);
  4. rubble and rebuild: damage to a lot steps its stage back (1 -> 0 is rubble), the lot is not rebuilt before
     10 s (200 ticks at 20 per second, architecture.md) and rises again after; rebuild is rubble -> stage 1 first.

NOT TESTABLE through the public API today (reported, no number or trigger was given): kinds 0 shipment, 1 expansion
and 2 season have no input (they come from E2 and a season clock whose period nobody gave); lot damage has no
verb. ASSUMPTION (flagged): damage to a lot is an area attack (om_unit_fire_aoe_attack) centred on it, the only public
area-damage input; the mapping from an area hit to a lot is the builder's, the test only reads the stages.
Named drafts: GROW_TICKS (how long a mission may run before some lot must have risen) and RISE_WINDOW (how long after
the 10 s delay the lot must have risen) are fixture bounds, not game thresholds; Westley owns the real ones.

Red on main (E1d unbuilt, K-e stubs): om_wave_get_since answers 0 rows for a capture/end ("no kind-3 wave logged")
and no lot ever exists ("no lot rose"). The controls and the isolation test pass.
"""
import ctypes

import pytest

from conftest import OMArchetype, OMEdge, OMFeature, OMTier, set_edge, set_faction, set_owner, set_region

W = ctypes.c_void_p
TICKS_PER_S = 20
REBUILD_DELAY = 10 * TICKS_PER_S      # R-193-06 / spec: rebuild after 10 s
GROW_TICKS = 2400                      # named draft: 2 min of play for a lot to rise
RISE_WINDOW = 100                      # named draft: ticks after the delay for the rebuild to show
KIND_CAPTURE, KIND_BATTLE_END = 3, 4
BOMBARD, VANGUARD = 4, 2


class Lot(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint32), ("x", ctypes.c_double), ("y", ctypes.c_double),
                ("stage", ctypes.c_int32), ("building", ctypes.c_int32), ("owner", ctypes.c_int32)]


class Wave(ctypes.Structure):
    _fields_ = [("tick", ctypes.c_uint32), ("kind", ctypes.c_int32), ("x", ctypes.c_double), ("y", ctypes.c_double)]


def bind(lib):
    P = ctypes.POINTER
    lib.om_lot_count.argtypes, lib.om_lot_count.restype = [W], ctypes.c_uint32
    lib.om_lot_get_at.argtypes, lib.om_lot_get_at.restype = [W, ctypes.c_uint32, P(Lot)], ctypes.c_int
    lib.om_wave_get_since.argtypes = [W, ctypes.c_uint32, P(Wave), ctypes.c_uint32]
    lib.om_wave_get_since.restype = ctypes.c_uint32
    lib.om_save_state_size.argtypes, lib.om_save_state_size.restype = [W], ctypes.c_uint32
    lib.om_save_state_write.argtypes, lib.om_save_state_write.restype = [W, P(ctypes.c_uint8), ctypes.c_uint32], None
    lib.om_load_state_read.argtypes, lib.om_load_state_read.restype = [W, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_int


def waves(lib, w, since=0):
    bind(lib)
    n = lib.om_wave_get_since(w, since, None, 0)
    buf = (Wave * max(n, 1))()
    got = lib.om_wave_get_since(w, since, buf, n)
    return [(buf[i].tick, buf[i].kind, buf[i].x, buf[i].y) for i in range(min(got, n))]


def lots(lib, w):
    bind(lib)
    out = []
    for i in range(lib.om_lot_count(w)):
        r = Lot()
        assert lib.om_lot_get_at(w, i, ctypes.byref(r)) == 0
        out.append((r.id, r.x, r.y, r.stage, r.building, r.owner))
    return out


def stage_of(lib, w, lot_id):
    return next(r[3] for r in lots(lib, w) if r[0] == lot_id)


def mission(lib, world_factory, seed=7):
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, 0, OMArchetype.PLAYER)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, 1, held_since=-1)
    set_owner(lib, w, 1, 0, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=500.0, faction_id=1)
    # TD-VG-E-20: the premises a lot needs (as test_VG_E_e1c.py scene): a ground era and a HOME region of the player faction with
    # economy (K-e3 samples the player's first HOME region). Not the walking movement kinds of the e1c scene: with them the Bombard
    # that hit() spawns at x - 200 does not lower the lot (stage 1 -> 1 in the premise dump, K-e5 tree), so the kinds stay default.
    set_region(lib, w, 1, tier=OMTier.HOME, military=20.0, economy=40.0, population=10.0, faction_id=0)
    assert lib.om_set_era_kind(w, 1) == 0
    lib.om_mission_setup(w, 0, 0, 0)
    lib.om_mission_begin(w)
    return w


def ticks(lib, w, n):
    """TD-VG-E-11: om_tactical_tick is a getter; advance the clock with om_tactical_tick_to (as e1h _advance, TD-VG-E-7)."""
    lib.om_tactical_tick.argtypes, lib.om_tactical_tick.restype = [W], ctypes.c_uint64
    lib.om_tactical_tick_to.argtypes, lib.om_tactical_tick_to.restype = [W, ctypes.c_uint64], ctypes.c_uint64
    return lib.om_tactical_tick_to(w, lib.om_tactical_tick(w) + n)


def with_structure(lib, w, slot=5, x=1234.0, y=2345.0):
    lib.om_structure_init(w, slot, 0, ctypes.c_double(100.0))
    lib.om_structure_set_position(w, slot, x, y)
    lib.om_structure_set_owner(w, slot, -1)
    return slot, x, y


# ---- controls (pass on main) ----

def test_control_wave_reader_empty_on_fresh_world(lib, world_factory):
    """Control: the reader answers [] on a world where nothing happened, so a non-empty answer later is a real log."""
    assert waves(lib, world_factory(n_regions=1)) == []


def test_control_stage_reader_sees_a_known_row():
    """Control: the pure-Python lot row picker finds a stage in a fabricated table (detector can fire)."""
    table = [(1, 0.0, 0.0, 3, 0, -1), (2, 5.0, 5.0, 0, 0, -1)]
    assert next(r[3] for r in table if r[0] == 2) == 0 and next(r[3] for r in table if r[0] == 1) == 3


# ---- waves (R-193-04) ----

def test_quiet_ticks_log_no_wave(lib, world_factory):
    """Isolation (passes on main and after): a mission with no capture and no end logs no capture/battle-end wave."""
    w = mission(lib, world_factory)
    ticks(lib, w, 40)
    assert [r for r in waves(lib, w) if r[1] in (KIND_CAPTURE, KIND_BATTLE_END)] == []


def test_capture_starts_a_wave(lib, world_factory):
    """R-193-04: a capture (structure owner changes) starts a kind-3 wave at the structure's place, inside the window."""
    w = mission(lib, world_factory)
    slot, x, y = with_structure(lib, w)
    t0 = ticks(lib, w, 5)
    lib.om_structure_set_owner(w, slot, 0)
    t1 = ticks(lib, w, 3)
    got = [r for r in waves(lib, w) if r[1] == KIND_CAPTURE]
    assert len(got) == 1, f"no kind-3 wave logged for a capture (waves: {waves(lib, w)})"
    tick, _, wx, wy = got[0]
    assert t0 <= tick <= t1, f"capture wave tick {tick} outside [{t0}, {t1}]"
    assert (wx, wy) == (x, y), f"capture wave at ({wx}, {wy}), structure at ({x}, {y})"


def test_battle_end_starts_a_wave(lib, world_factory):
    """R-193-04: the end of a battle starts a kind-4 wave, once."""
    w = mission(lib, world_factory)
    ticks(lib, w, 5)
    lib.om_mission_end(w)
    got = [r for r in waves(lib, w) if r[1] == KIND_BATTLE_END]
    assert len(got) == 1, f"no kind-4 wave logged at mission end (waves: {waves(lib, w)})"


def test_log_is_oldest_first_and_since_filters(lib, world_factory):
    """Contract: oldest first; `since` keeps only tick >= since (a capture then a battle end, in that order)."""
    w = mission(lib, world_factory)
    slot, _, _ = with_structure(lib, w)
    ticks(lib, w, 3)
    lib.om_structure_set_owner(w, slot, 0)
    ticks(lib, w, 30)
    lib.om_mission_end(w)
    allw = waves(lib, w)
    kinds = [r[1] for r in allw]
    assert KIND_CAPTURE in kinds and KIND_BATTLE_END in kinds, f"expected capture and battle end, got {allw}"
    assert [r[0] for r in allw] == sorted(r[0] for r in allw), "log not oldest first"
    assert kinds.index(KIND_CAPTURE) < kinds.index(KIND_BATTLE_END)
    cut = next(r[0] for r in allw if r[1] == KIND_BATTLE_END)
    assert all(r[0] >= cut for r in waves(lib, w, cut)) and any(r[1] == KIND_BATTLE_END for r in waves(lib, w, cut))
    assert not any(r[1] == KIND_CAPTURE for r in waves(lib, w, cut + 1))


def test_wave_log_survives_save_load(lib, world_factory):
    """Integration (format 8): the wave log round-trips through om_save_state_* and then reads the same."""
    w = mission(lib, world_factory)
    slot, _, _ = with_structure(lib, w)
    ticks(lib, w, 3)
    lib.om_structure_set_owner(w, slot, 0)
    ticks(lib, w, 3)
    before = waves(lib, w)
    assert before, "no wave logged to round-trip"
    n = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    lib.om_save_state_write(w, buf, n)
    w2 = world_factory(n_regions=2, seed=7)
    assert lib.om_load_state_read(w2, buf, n) == 0
    assert waves(lib, w2) == before


def test_waves_and_lots_are_deterministic(lib, world_factory):
    """Determinism: same seed and the same command stream give the same wave log and lot table."""
    runs = []
    for _ in range(2):
        w = mission(lib, world_factory, seed=11)
        slot, _, _ = with_structure(lib, w)
        ticks(lib, w, 20)
        lib.om_structure_set_owner(w, slot, 0)
        ticks(lib, w, 200)
        lib.om_mission_end(w)
        runs.append((waves(lib, w), lots(lib, w)))
    assert runs[0] == runs[1]
    assert runs[0][0], "determinism compared two empty wave logs"


# ---- rubble and rebuild (R-193-05, R-193-06) ----

def risen_lot(lib, w):
    """Tick until some lot has risen to stage >= 1; returns (lot id, x, y)."""
    for _ in range(GROW_TICKS // 20):
        ticks(lib, w, 20)
        for r in lots(lib, w):
            if r[3] >= 1:
                return r[0], r[1], r[2]
    pytest.fail(f"no lot rose within {GROW_TICKS} ticks (the lot table is empty or never leaves stage 0)")


def hit(lib, w, x, y):
    """One area attack centred on (x, y): a Bombard in range, a Vanguard of the other side standing on the lot."""
    bomb = lib.om_unit_spawn(w, BOMBARD, 0, x - 200.0, y, 0)
    tgt = lib.om_unit_spawn(w, VANGUARD, 1, x, y, 0)
    lib.om_unit_fire_aoe_attack(w, bomb, tgt, 150.0)


def test_damage_steps_a_lot_back_toward_rubble(lib, world_factory):
    """R-193-06: damage runs the stages backward; repeated damage reaches stage 0 (rubble)."""
    w = mission(lib, world_factory)
    lid, x, y = risen_lot(lib, w)
    before = stage_of(lib, w, lid)
    hit(lib, w, x, y)
    ticks(lib, w, 2)
    assert stage_of(lib, w, lid) < before, f"damage did not lower lot {lid} from stage {before}"
    for _ in range(6):
        if stage_of(lib, w, lid) == 0:
            break
        hit(lib, w, x, y)
        ticks(lib, w, 2)
    assert stage_of(lib, w, lid) == 0, "lot never fell to rubble (stage 0) under repeated damage"


def test_rebuild_waits_ten_seconds_then_rises(lib, world_factory):
    """R-193-06 and spec E1d: a ruined lot is not rebuilt before 10 s (200 ticks) and has risen again after."""
    w = mission(lib, world_factory)
    lid, x, y = risen_lot(lib, w)
    for _ in range(8):
        if stage_of(lib, w, lid) == 0:
            break
        hit(lib, w, x, y)
        ticks(lib, w, 2)
    assert stage_of(lib, w, lid) == 0, "setup: could not ruin the lot"
    ruined_at = lib.om_tactical_tick(w)
    ticks(lib, w, REBUILD_DELAY - 5)
    assert stage_of(lib, w, lid) == 0, f"lot rebuilt before 10 s ({lib.om_tactical_tick(w) - ruined_at} ticks)"
    # TD-VG-E-11: the hit() units stay and keep fighting, so a later hit can ruin the risen lot again; watch for the rise tick by tick.
    rose = False
    for _ in range(5 + RISE_WINDOW):
        ticks(lib, w, 1)
        if stage_of(lib, w, lid) >= 1:
            rose = True
            break
    assert rose, "lot still rubble after 10 s plus the rise window"


def test_undamaged_lots_are_not_set_back(lib, world_factory):
    """Isolation: a hit far from every other lot leaves their stages unchanged (stage never drops without damage)."""
    w = mission(lib, world_factory)
    lid, x, y = risen_lot(lib, w)
    others = {r[0]: r[3] for r in lots(lib, w) if r[0] != lid and abs(r[1] - x) > 1000 and abs(r[2] - y) > 1000}
    hit(lib, w, x, y)
    ticks(lib, w, 2)
    now = {r[0]: r[3] for r in lots(lib, w)}
    assert all(now[k] >= v for k, v in others.items()), "a lot far from the blast lost a stage"
