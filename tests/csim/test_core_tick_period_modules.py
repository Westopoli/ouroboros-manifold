"""E-13 R-099-03 -- module wiring for the tactical tick period.

R-099-03 (docs/bible/epics/E-13-movement-and-command.md, decision A, Westley
2026-09-24) requires every per-second quantity to read the same in real time
whether the tactical tick runs at period 1 (20 ticks/s, at or below 1,000
live units) or period 2 (10 ticks/s, above 1,000). test_core_tick_period.py
proves this for the tactical layer itself (unit speed, ability duration);
this file proves the same invariant for the E-14 (csrc/enemy_macro.c) and
E-15 (csrc/tactical_support.c) module rules that also count ticks: objective
and structure drift (R-130-02, R-130-03), hazard travel (R-130-04),
structure capture progress (R-127-01), the macro evaluation cadence
(R-120-04), the replay log's tick column (R-123-02), the external-
reinforcement roll's arrival window (R-124-01), and its fire check
(R-124-02). The module rule under test throughout: these modules must read
the real elapsed base-tick clock (`om_tactical_base_tick`, the sum of every
step's period) rather than the per-step counter (`om_tactical_tick`, which
advances by 1 every om_tactical_step call regardless of period) -- a period-2
step spans 2 base ticks, so a module keyed to the step counter would run at
half real speed once the population crosses the threshold.

Every test drives two worlds built from the same seed: one held at period 1
(an anchor unit only, never crossing OM_TACTICAL_HIGH_LOAD_UNITS) and one
pushed to period 2 from its first step (the anchor plus 1,000 far filler
units, the same fixture shape test_core_tick_period.py uses). Filler units
sit 1,000,000+ wu away and share faction 0 with the anchor, so they never
enter a sensor or collision radius and never turn hostile (no ability
auto-triggers, no RNG draw from combat). A period-2 step k is compared
against a period-1 step 2k -- same real elapsed base ticks, so the module
under test must land on the identical result. Where a test's setup call
draws from the world's RNG (drift-waypoint synthesis in
om_sup_synthesize_drift_wp, the external-reinforcement roll), that call runs
before any unit is spawned in both worlds, so the two RNG streams are still
in lockstep when it fires: plain om_tactical_step on an idle unit never
draws from the RNG (csrc/unit.c has no om_rng_draw call), so nothing spawned
afterward can desync them.
"""
import ctypes

import pytest

from conftest import OMFeature

OM_UT_RAIDER = 0


class OMVec2(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
    ]


class OMReinforcementWave(ctypes.Structure):
    _fields_ = [
        ("is_scheduled", ctypes.c_uint32),
        ("direction", ctypes.c_uint32),
        ("arrival_tick", ctypes.c_uint64),
        ("is_spawned", ctypes.c_uint32),
    ]


class OMReplayCommand(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("force_id", ctypes.c_uint32),
        ("command_type", ctypes.c_uint32),
        ("target_x", ctypes.c_double),
        ("target_y", ctypes.c_double),
        ("target_id", ctypes.c_uint32),
    ]


def _tactical_world(lib, world_factory, seed):
    w = world_factory(n_regions=1, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _spawn_anchor(lib, w, faction_id=0):
    return lib.om_unit_spawn(w, OM_UT_RAIDER, faction_id, 0.0, 0.0, 0)


def _spawn_fillers(lib, w, n=1000, faction_id=0, y_start=1_000_000.0, spacing=100.0):
    for i in range(n):
        lib.om_unit_spawn(w, OM_UT_RAIDER, faction_id, 0.0, y_start + i * spacing, 0)


def _center(lib, w, objective=0):
    pos = OMVec2()
    lib.om_objective_get_center(w, objective, ctypes.byref(pos))
    return pos.x, pos.y


def _position(lib, w, structure=0):
    pos = OMVec2()
    lib.om_structure_get_position(w, structure, ctypes.byref(pos))
    return pos.x, pos.y


def _replay_log(lib, w):
    count = lib.om_replay_command_count(w)
    buf = (OMReplayCommand * count)()
    lib.om_replay_get_commands(w, buf, count)
    return list(buf)


def test_R_130_02_drifting_objective_real_time_equivalence(lib, world_factory):
    """R-130-02: a drifting objective's centre is the interpolation along its
    waypoints at tick mod period; that tick must be the real base-tick clock,
    so a period-2 world 50 steps in (100 base ticks) lands on the same centre
    as a period-1 world 100 steps in (also 100 base ticks)."""
    seed = 9001

    w1 = _tactical_world(lib, world_factory, seed)
    lib.om_objective_setup_drifting(w1, 0, 100)
    _spawn_anchor(lib, w1)
    for _ in range(100):
        lib.om_tactical_step(w1)
    center_p1 = _center(lib, w1)

    w2 = _tactical_world(lib, world_factory, seed)
    lib.om_objective_setup_drifting(w2, 0, 100)
    _spawn_anchor(lib, w2)
    _spawn_fillers(lib, w2)
    assert lib.om_tactical_tick_period(w2) == 1, "setup: period only updates once a step runs"
    for _ in range(50):
        lib.om_tactical_step(w2)
    assert lib.om_tactical_tick_period(w2) == 2, "setup: 1,001 live units must already be at period 2"

    center_p2 = _center(lib, w2)
    assert center_p1[0] == pytest.approx(center_p2[0])
    assert center_p1[1] == pytest.approx(center_p2[1])


def test_R_130_03_drifting_structure_real_time_equivalence(lib, world_factory):
    """R-130-03: a drifting structure's position moves the same way, through
    om_structure_init_drifting / om_structure_get_position -- period-2 step
    50 (100 base ticks) must equal period-1 step 100 (100 base ticks)."""
    seed = 9002

    w1 = _tactical_world(lib, world_factory, seed)
    lib.om_structure_init_drifting(w1, 0, 100)
    _spawn_anchor(lib, w1)
    for _ in range(100):
        lib.om_tactical_step(w1)
    pos_p1 = _position(lib, w1)

    w2 = _tactical_world(lib, world_factory, seed)
    lib.om_structure_init_drifting(w2, 0, 100)
    _spawn_anchor(lib, w2)
    _spawn_fillers(lib, w2)
    for _ in range(50):
        lib.om_tactical_step(w2)
    assert lib.om_tactical_tick_period(w2) == 2, "setup: 1,001 live units must already be at period 2"

    pos_p2 = _position(lib, w2)
    assert pos_p1[0] == pytest.approx(pos_p2[0])
    assert pos_p1[1] == pytest.approx(pos_p2[1])


def test_R_130_04_hazard_travel_real_time_equivalence(lib, world_factory):
    """R-130-04: a moving hazard's interference at any point follows the
    source, which travels (0,0) -> (500,500) over 100 base ticks
    (om_hazard_sample_interference reads the base-tick clock). A period-2
    world 50 steps in (100 base ticks) must read the same interference at a
    fixed point as a period-1 world 100 steps in (also 100 base ticks)."""
    seed = 9003
    query_x, query_y = 250.0, 250.0

    w1 = _tactical_world(lib, world_factory, seed)
    lib.om_hazard_spawn_moving_interference(
        w1, ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(500.0), ctypes.c_double(500.0), 100
    )
    _spawn_anchor(lib, w1)
    for _ in range(100):
        lib.om_tactical_step(w1)
    inf_p1 = ctypes.c_double(lib.om_hazard_sample_interference(w1, ctypes.c_double(query_x), ctypes.c_double(query_y))).value

    w2 = _tactical_world(lib, world_factory, seed)
    lib.om_hazard_spawn_moving_interference(
        w2, ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(500.0), ctypes.c_double(500.0), 100
    )
    _spawn_anchor(lib, w2)
    _spawn_fillers(lib, w2)
    for _ in range(50):
        lib.om_tactical_step(w2)
    assert lib.om_tactical_tick_period(w2) == 2, "setup: 1,001 live units must already be at period 2"
    inf_p2 = ctypes.c_double(lib.om_hazard_sample_interference(w2, ctypes.c_double(query_x), ctypes.c_double(query_y))).value

    assert inf_p1 == pytest.approx(inf_p2)


def test_R_127_01_structure_capture_real_time_equivalence(lib, world_factory):
    """R-127-01: capture progress rises by dt / 10 s while exactly one
    non-owner faction is present. dt must be real base-tick time, so calling
    om_structure_tick_capture once per om_tactical_step at period 2 must
    reach the same progress, and flip the owner on the same real tick, as
    calling it once per step at period 1."""
    seed = 9004

    w1 = _tactical_world(lib, world_factory, seed)
    lib.om_structure_init(w1, 0, 0, ctypes.c_double(100.0))
    lib.om_structure_set_owner(w1, 0, 2)
    lib.om_structure_set_capturing_faction(w1, 0, 1)
    _spawn_anchor(lib, w1)

    for _ in range(100):
        lib.om_tactical_step(w1)
        lib.om_structure_tick_capture(w1, 0)
    assert lib.om_structure_get_owner(w1, 0) == 2, "R-127-01: 100 base ticks (5 s) must not have flipped the owner"
    progress_p1 = ctypes.c_double(lib.om_structure_get_capture_progress(w1, 0)).value

    for _ in range(98):
        lib.om_tactical_step(w1)
        lib.om_structure_tick_capture(w1, 0)
    assert lib.om_structure_get_owner(w1, 0) == 2, "R-127-01: 198 base ticks (< 10 s) must not have flipped the owner"

    lib.om_tactical_step(w1)
    lib.om_structure_tick_capture(w1, 0)
    assert lib.om_structure_get_owner(w1, 0) == 2, "R-127-01: 199 base ticks (< 10 s) must not have flipped the owner"

    lib.om_tactical_step(w1)
    lib.om_structure_tick_capture(w1, 0)
    assert lib.om_structure_get_owner(w1, 0) == 1, "R-127-01: 200 base ticks (10 s) flips the owner"

    w2 = _tactical_world(lib, world_factory, seed)
    lib.om_structure_init(w2, 0, 0, ctypes.c_double(100.0))
    lib.om_structure_set_owner(w2, 0, 2)
    lib.om_structure_set_capturing_faction(w2, 0, 1)
    _spawn_anchor(lib, w2)
    _spawn_fillers(lib, w2)

    for _ in range(50):
        lib.om_tactical_step(w2)
        lib.om_structure_tick_capture(w2, 0)
    assert lib.om_tactical_tick_period(w2) == 2, "setup: 1,001 live units must already be at period 2"
    progress_p2 = ctypes.c_double(lib.om_structure_get_capture_progress(w2, 0)).value
    assert progress_p2 == pytest.approx(progress_p1, abs=1e-3), (
        "R-099-03/R-127-01: 50 period-2 steps (100 base ticks) must match 100 period-1 steps "
        "(also 100 base ticks)"
    )
    assert progress_p2 == pytest.approx(0.5, abs=1e-3), "R-127-01: 50 period-2 steps is 100 base ticks (5 s) -> progress 0.5"
    assert lib.om_structure_get_owner(w2, 0) == 2

    for _ in range(48):
        lib.om_tactical_step(w2)
        lib.om_structure_tick_capture(w2, 0)
    assert lib.om_structure_get_owner(w2, 0) == 2, "R-127-01: 98 period-2 steps is 196 base ticks (< 10 s)"

    lib.om_tactical_step(w2)
    lib.om_structure_tick_capture(w2, 0)
    assert lib.om_structure_get_owner(w2, 0) == 2, "R-127-01: 99 period-2 steps is 198 base ticks (< 10 s)"

    lib.om_tactical_step(w2)
    lib.om_structure_tick_capture(w2, 0)
    assert lib.om_structure_get_owner(w2, 0) == 1, "R-127-01: 100 period-2 steps is 200 base ticks (10 s), flips the owner"


def test_R_120_04_macro_evaluates_on_base_tick_boundaries(lib, world_factory):
    """R-120-04: the macro evaluates every 40 ticks. That interval is real
    time (2 s), so a period-2 world must evaluate exactly when the base tick
    is a multiple of 40, the same boundaries (in real time) a period-1 world
    hits on its own 40-tick multiples."""
    seed = 9005
    boundaries = set(range(40, 201, 40))

    w1 = _tactical_world(lib, world_factory, seed)
    _spawn_anchor(lib, w1)
    evaluated_p1 = set()
    for _ in range(200):
        lib.om_tactical_step(w1)
        if lib.om_macro_has_evaluated(w1):
            evaluated_p1.add(lib.om_tactical_base_tick(w1))
    assert evaluated_p1 == boundaries, "R-099-03/R-120-04: period 1 evaluates on every 40-tick multiple, nothing else"

    w2 = _tactical_world(lib, world_factory, seed)
    _spawn_anchor(lib, w2)
    _spawn_fillers(lib, w2)
    evaluated_p2 = set()
    for _ in range(100):
        lib.om_tactical_step(w2)
        if lib.om_macro_has_evaluated(w2):
            evaluated_p2.add(lib.om_tactical_base_tick(w2))
    assert lib.om_tactical_tick_period(w2) == 2, "setup: 1,001 live units must already be at period 2"
    assert evaluated_p2 == boundaries, (
        "R-099-03/R-120-04: period 2 must evaluate on the same real-time 40-base-tick "
        "boundaries as period 1, not every 40 steps (which would be 80 base ticks)"
    )


def test_R_123_02_replay_log_tick_column_real_time_equivalence(lib, world_factory):
    """R-123-02: every enemy command enters the replay stream with a force
    id. With 3 forces evaluating every 40 base ticks, the tick column is
    [40]*3 + [80]*3 + ... + [200]*3 -- identical at period 1 and period 2,
    because the logged tick is the real base tick, not the step index."""
    seed = 9006
    expected_ticks = [t for t in range(40, 201, 40) for _ in range(3)]

    w1 = _tactical_world(lib, world_factory, seed)
    lib.om_macro_init_force(w1, 0, 1)
    lib.om_macro_init_force(w1, 1, 2)
    lib.om_macro_init_force(w1, 2, 3)
    _spawn_anchor(lib, w1)
    for _ in range(200):
        lib.om_tactical_step(w1)
    ticks_p1 = [c.tick for c in _replay_log(lib, w1)]
    assert ticks_p1 == expected_ticks

    w2 = _tactical_world(lib, world_factory, seed)
    lib.om_macro_init_force(w2, 0, 1)
    lib.om_macro_init_force(w2, 1, 2)
    lib.om_macro_init_force(w2, 2, 3)
    _spawn_anchor(lib, w2)
    _spawn_fillers(lib, w2)
    for _ in range(100):
        lib.om_tactical_step(w2)
    assert lib.om_tactical_tick_period(w2) == 2, "setup: 1,001 live units must already be at period 2"
    ticks_p2 = [c.tick for c in _replay_log(lib, w2)]
    assert ticks_p2 == expected_ticks
    assert ticks_p2 == ticks_p1, "R-099-03/R-123-02: the logged tick column is period-invariant"


def test_R_125_01_crossing_into_period_2_keeps_the_eval_interval(lib, world_factory):
    """R-125-01: the evaluation interval does not change (40 base ticks,
    2 s), including on the step that crosses into period 2 -- a period-2
    step can hop over the 40-multiple boundary instead of landing on it, but
    it must still evaluate for it exactly once, at the base tick it lands
    on. A world that stays at period 1 lands on 40 and 80 exactly; a world
    that crosses to period 2 at step 40 (base tick 39 -> 41) evaluates at 41
    and 81, logging the crossed slot (40, 80), never the landing tick."""
    seed = 9007

    # Reference: pure period 1, no crossing. Evaluations land exactly on the
    # boundary.
    w1 = _tactical_world(lib, world_factory, seed)
    _spawn_anchor(lib, w1)
    evaluated_p1 = set()
    for _ in range(81):
        lib.om_tactical_step(w1)
        if lib.om_macro_has_evaluated(w1):
            evaluated_p1.add(lib.om_tactical_base_tick(w1))
    assert evaluated_p1 == {40, 80}

    # Crossing world: 39 steps at period 1 (base tick 39), then 1,000
    # fillers land it above the threshold for every step after.
    w2 = _tactical_world(lib, world_factory, seed)
    mover = _spawn_anchor(lib, w2)
    assert mover is not None
    for _ in range(39):
        lib.om_tactical_step(w2)
    assert lib.om_tactical_base_tick(w2) == 39
    assert lib.om_tactical_tick_period(w2) == 1, "setup: still below threshold before the crossing spawn"

    _spawn_fillers(lib, w2)

    evaluated_p2 = set()
    for _ in range(21):
        lib.om_tactical_step(w2)
        if lib.om_macro_has_evaluated(w2):
            evaluated_p2.add(lib.om_tactical_base_tick(w2))
    assert lib.om_tactical_tick_period(w2) == 2, "setup: 1,001 live units crosses into period 2 on the next step"
    assert lib.om_tactical_base_tick(w2) == 81, "39 base ticks plus 21 period-2 steps (42 base ticks) is 81"
    assert evaluated_p2 == {41, 81}, (
        "R-099-03/R-125-01: the crossing step (base tick 39 -> 41) hops over 40 but still "
        "evaluates once for it, landing the flag on 41; the next boundary lands on 81"
    )

    ticks_p2 = [c.tick for c in _replay_log(lib, w2)]
    assert ticks_p2 == [40, 80], "R-099-03/R-123-02: the logged tick is the crossed slot, not the landing tick"


def test_R_124_02_reinforcement_fires_on_the_landed_base_tick(lib, world_factory):
    """R-124-02: the wave fires once om_tactical_base_tick reaches its
    arrival_tick. A period-1 world lands on any arrival tick exactly; a
    period-2 world (2 base ticks per step) can only land on even ticks, so
    an odd arrival_tick (101) fires one base tick late, at 102, the first
    tick a period-2 step lands on at or past 101 -- an even arrival_tick
    (100) fires exactly on time in both."""

    def _wave(arrival_tick):
        wave = OMReinforcementWave()
        wave.is_scheduled = 1
        wave.direction = 0
        wave.arrival_tick = arrival_tick
        wave.is_spawned = 0
        return wave

    # Period 2, arrival_tick = 100 (even): fires exactly at 100.
    w = _tactical_world(lib, world_factory, 9008)
    lib.om_mission_set_external_reinforcement(w, ctypes.byref(_wave(100)))
    _spawn_anchor(lib, w)
    _spawn_fillers(lib, w)
    fired_at = None
    for _ in range(60):
        lib.om_tactical_step(w)
        lib.om_mission_check_external_reinforcements(w)
        if lib.om_mission_is_reinforcement_spawned(w) and fired_at is None:
            fired_at = lib.om_tactical_base_tick(w)
    assert lib.om_tactical_tick_period(w) == 2
    assert fired_at == 100, "R-124-02: an even arrival_tick fires exactly on time even at period 2"

    # Period 2, arrival_tick = 101 (odd): the first base tick reachable at or
    # past 101 is 102.
    w = _tactical_world(lib, world_factory, 9009)
    lib.om_mission_set_external_reinforcement(w, ctypes.byref(_wave(101)))
    _spawn_anchor(lib, w)
    _spawn_fillers(lib, w)
    fired_at = None
    for _ in range(60):
        lib.om_tactical_step(w)
        lib.om_mission_check_external_reinforcements(w)
        if lib.om_mission_is_reinforcement_spawned(w) and fired_at is None:
            fired_at = lib.om_tactical_base_tick(w)
    assert lib.om_tactical_tick_period(w) == 2
    assert fired_at == 102, "R-124-02: an odd arrival_tick fires one base tick late at period 2, never early"

    # Period 1, the same arrival_tick = 101: lands on it exactly (real-time
    # equivalence, modulo the period-2 world's coarser landing grid).
    w = _tactical_world(lib, world_factory, 9009)
    lib.om_mission_set_external_reinforcement(w, ctypes.byref(_wave(101)))
    _spawn_anchor(lib, w)
    fired_at = None
    for _ in range(110):
        lib.om_tactical_step(w)
        lib.om_mission_check_external_reinforcements(w)
        if lib.om_mission_is_reinforcement_spawned(w) and fired_at is None:
            fired_at = lib.om_tactical_base_tick(w)
    assert fired_at == 101, "R-124-02: period 1 lands on any arrival tick exactly, including odd ones"


def test_R_124_01_arrival_window_is_period_invariant(lib, world_factory):
    """R-124-01: the wave's arrival tick is fixed at generation, in
    [base_tick, base_tick + 40] (Q-124-01: 40 base ticks, the eval
    interval). Scheduled at base tick 100 the window is (100, 140]; because
    the roll and the random offset are read from the same RNG stream at the
    same point (no draw happens between world creation and the schedule
    call except this one), a period-1 world and a period-2 world brought to
    the same base tick with the same seed compute the identical arrival
    tick, not just one inside the same window."""
    seed = None
    for candidate in range(1, 301):
        w = _tactical_world(lib, world_factory, candidate)
        _spawn_anchor(lib, w)
        _spawn_fillers(lib, w)
        for _ in range(50):
            lib.om_tactical_step(w)
        assert lib.om_tactical_base_tick(w) == 100
        wave = OMReinforcementWave()
        lib.om_mission_schedule_external_reinforcement(w, ctypes.byref(wave))
        if wave.is_scheduled:
            seed = candidate
            arrival_p2 = wave.arrival_tick
            break
    assert seed is not None, "no seed in range(1, 301) rolled a schedule at OM_MACRO_EXTERNAL_REINFORCEMENT_PROB=0.07"
    assert 100 < arrival_p2 <= 140

    w = _tactical_world(lib, world_factory, seed)
    _spawn_anchor(lib, w)
    for _ in range(100):
        lib.om_tactical_step(w)
    assert lib.om_tactical_base_tick(w) == 100
    assert lib.om_tactical_tick_period(w) == 1
    wave = OMReinforcementWave()
    lib.om_mission_schedule_external_reinforcement(w, ctypes.byref(wave))
    assert wave.is_scheduled == 1
    arrival_p1 = wave.arrival_tick

    assert 100 < arrival_p1 <= 140
    assert arrival_p1 == arrival_p2, (
        "R-099-03/R-124-01: same seed, same base tick, no intervening RNG draw at either "
        "period -- the arrival tick must be identical, not merely in the same window"
    )


def test_positive_control_period_1_and_2_diverge_at_the_same_step_count(lib, world_factory):
    """Positive control: period-1 step 50 (base tick 50) and period-2 step
    50 (base tick 100) are NOT the same real time, so a drifting objective
    must report different centres for them -- proving the equality
    assertions above are live comparisons, not vacuously-equal stubs."""
    seed = 9010

    w1 = _tactical_world(lib, world_factory, seed)
    lib.om_objective_setup_drifting(w1, 0, 100)
    _spawn_anchor(lib, w1)
    for _ in range(50):
        lib.om_tactical_step(w1)
    center_p1_at_50 = _center(lib, w1)

    w2 = _tactical_world(lib, world_factory, seed)
    lib.om_objective_setup_drifting(w2, 0, 100)
    _spawn_anchor(lib, w2)
    _spawn_fillers(lib, w2)
    for _ in range(50):
        lib.om_tactical_step(w2)
    assert lib.om_tactical_tick_period(w2) == 2, "setup: 1,001 live units must already be at period 2"
    center_p2_at_50 = _center(lib, w2)

    assert center_p1_at_50 != center_p2_at_50, (
        "positive control: 50 period-1 steps (base tick 50) and 50 period-2 steps "
        "(base tick 100) are different real times and must give different centres"
    )
