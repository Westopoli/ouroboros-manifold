"""H-041 (unit-scale-readthrough), CONTRACT LANDING tests: the per-type collision radius, om_roster_set_collision_radius.
This file belongs to the contract landing (phase 1 of the builder). tests/qa/test_unit_scale_readthrough.py is the
consumers landing (phase 2) and is not in this commit.

Story H-041, Contract change: "`int om_roster_set_collision_radius(om_world *w, int unit_type, double radius);` beside
`om_roster_set_reach` (line 2008). Returns 0, or -1 for an unknown type or a radius outside DRAFT-radius-bounds 1 to
200." and "When a type's radius is never set, its value stays `OM_UNIT_COLLISION_RADIUS` 15, so every existing trace,
golden and lab fight is byte-identical (a test pins this)." and "Determinism: the radius is read once at `om_roster_*`
time, never from the file inside the tick."
Story H-041, Tests: "`tests/csim/test_collision_radius.py`: two roles with radii 15 and 30 push apart at the sum of
their radii (ALG-68); unknown type and out-of-bounds radius return -1 (positive control); same seed and command stream
give a byte-identical trace when every value is 15 or the function is never called."
ALG-68: "After movement, same-layer pairs closer than `2 * 15` are pushed apart along their axis ... two such units split
the push equally" (an idle pair); H-041 replaces the 15 with the type's own radius, so a pair ends r_a + r_b apart.

The function does not exist on this tree, so every test that calls it is red with one reason: the symbol is not
exported (the lib has no `om_roster_set_collision_radius`). conftest.py does not bind it (tests/csim/conftest.py is not
this story's file), so _set_radius binds argtypes and restype here, from the story's signature.

Controls (green today and after): the pair of two default units ends 30 apart; the existing om_roster_set_reach shows
the -1 / 0 pattern the bounds tests read; TRACE_R15 is reproduced with the function never called; the boundaries 1 and
200 are accepted (those two sit behind the missing symbol too, so they are red today, and are the positive control of
the -1 tests once the function exists).

TRACE_R15 and the mixed scene are the ones recorded in tests/csim/test_PP_collision_radius_runtime.py (see its module
docstring for how it was recorded); this file reuses them so the "never called" and "every value is 15" runs are pinned
to the same bytes.

Not tested here, said in the report: the OM_TP_UNIT_COLLISION_RADIUS multiplier reading (the story says it "keeps
working as a multiplier on the per-type value; its reading is documented at the knob" and gives no formula), the
roster's-largest-radius at sites with no unit type in hand, and "read once at om_roster_* time" (no observable).
"""
import ctypes
import hashlib
import math
import struct

import pytest

from conftest import OMFeature

FACTION = 0
LAYER = 0
RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION = range(6)   # unit_visuals.gd TYPE_NAMES order
SIX_TYPES = (RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION)
DEFAULT_RADIUS = 15.0
RADIUS_MIN, RADIUS_MAX = 1.0, 200.0   # DRAFT-radius-bounds 1 to 200 (story)
STEP_TOL = 0.05                       # numeric slack for the C's cheap trig, as in test_PP_collision_radius_runtime.py

# Recorded on the unmodified tree by test_PP_collision_radius_runtime.py (origin/main 37858c8e, no csrc change).
TRACE_R15 = "9266aad512c513ca24883b28e4cca87963685878a14136619d98caf703b4c5a2"


def _set_radius(lib, w, unit_type, radius):
    fn = getattr(lib, "om_roster_set_collision_radius", None)
    assert fn is not None, "om_roster_set_collision_radius is not exported by the lib: the H-041 contract is not landed"
    fn.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
    fn.restype = ctypes.c_int
    return fn(w, unit_type, float(radius))


def _world(lib):
    w = lib.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(1))
    assert w
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _spawn(lib, w, unit_type, x, y):
    return lib.om_unit_spawn(w, unit_type, FACTION, x, y, LAYER)


def _pos(lib, w, u):
    return tuple(lib.om_unit_get_pos(w, u))


def _gap(lib, w, a, b):
    pa, pb = _pos(lib, w, a), _pos(lib, w, b)
    return math.hypot(pb[0] - pa[0], pb[1] - pa[1])


def _idle_pair_gap(lib, type_a, radius_a, type_b, radius_b):
    """Two idle units 5 wu apart on the same layer, each type's radius set (None = never set), five ticks of the
    tactical step (the tick, so the push is reached the way play reaches it). Returns their distance."""
    w = _world(lib)
    try:
        if radius_a is not None:
            assert _set_radius(lib, w, type_a, radius_a) == 0
        if radius_b is not None:
            assert _set_radius(lib, w, type_b, radius_b) == 0
        a = _spawn(lib, w, type_a, 1000.0, 1000.0)
        b = _spawn(lib, w, type_b, 1005.0, 1000.0)
        for _ in range(5):
            lib.om_tactical_step(w)
        return _gap(lib, w, a, b)
    finally:
        lib.om_world_free(w)


# ---- ALG-68: a pair pushes apart at the sum of its radii -----------------------------------------------------------

def test_H_041_roles_with_radii_15_and_30_push_apart_at_45(lib):
    """H-041 Tests, first line: "two roles with radii 15 and 30 push apart at the sum of their radii (ALG-68)".
    A Raider at 15 and a Bombard at 30, idle, 5 wu apart: they end 45 apart. Red today: the symbol is not exported
    (and with it unset the pair ends 30 apart, whatever the roles)."""
    assert _idle_pair_gap(lib, RAIDER, 15.0, BOMBARD, 30.0) == pytest.approx(45.0, abs=STEP_TOL)


def test_H_041_the_sum_does_not_depend_on_which_unit_is_first(lib):
    """The same pair with the 30 unit spawned first: the sum is symmetric (ALG-68 pushes along the axis, equal split).
    Red today: symbol not exported."""
    w = _world(lib)
    try:
        assert _set_radius(lib, w, RAIDER, 15.0) == 0
        assert _set_radius(lib, w, BOMBARD, 30.0) == 0
        big = _spawn(lib, w, BOMBARD, 1000.0, 1000.0)
        small = _spawn(lib, w, RAIDER, 1005.0, 1000.0)
        for _ in range(5):
            lib.om_tactical_step(w)
        assert _gap(lib, w, big, small) == pytest.approx(45.0, abs=STEP_TOL)
    finally:
        lib.om_world_free(w)


def test_H_041_radius_of_one_type_does_not_move_a_pair_of_another(lib):
    """Isolation: setting the Bombard to 30 leaves two Raiders (never set) 30 apart, 15 + 15. Red today: symbol not
    exported."""
    w = _world(lib)
    try:
        assert _set_radius(lib, w, BOMBARD, 30.0) == 0
        a = _spawn(lib, w, RAIDER, 1000.0, 1000.0)
        b = _spawn(lib, w, RAIDER, 1005.0, 1000.0)
        for _ in range(5):
            lib.om_tactical_step(w)
        assert _gap(lib, w, a, b) == pytest.approx(30.0, abs=STEP_TOL)
    finally:
        lib.om_world_free(w)


def test_H_041_control_pair_of_default_roles_ends_30_apart(lib):
    """Control (green today and after): the same scene with no radius ever set ends 30 apart (ALG-68, 2 * 15), so
    the 45 above is a measurement of the radii and not of a scene that always pushes to one figure."""
    assert _idle_pair_gap(lib, RAIDER, None, BOMBARD, None) == pytest.approx(30.0, abs=STEP_TOL)


# ---- bounds and unknown type ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("unit_type", [99, -1])
def test_H_041_unknown_type_returns_minus_one(lib, unit_type):
    """H-041 Tests, second line: "unknown type ... return -1". Red today: symbol not exported."""
    w = _world(lib)
    try:
        assert _set_radius(lib, w, unit_type, 15.0) == -1
    finally:
        lib.om_world_free(w)


@pytest.mark.parametrize("radius", [0.99, 0.0, -15.0, 200.01, 1000.0])
def test_H_041_out_of_bounds_radius_returns_minus_one(lib, radius):
    """H-041 Tests, second line: "out-of-bounds radius return -1"; Contract: "a radius outside DRAFT-radius-bounds 1
    to 200". Red today: symbol not exported."""
    w = _world(lib)
    try:
        assert _set_radius(lib, w, RAIDER, radius) == -1
    finally:
        lib.om_world_free(w)


def test_H_041_a_refused_radius_leaves_the_type_at_15(lib):
    """A -1 call changes nothing: after a refused 0.5 and a refused 500 a Raider pair still ends 30 apart. Red today:
    symbol not exported."""
    w = _world(lib)
    try:
        assert _set_radius(lib, w, RAIDER, 0.5) == -1
        assert _set_radius(lib, w, RAIDER, 500.0) == -1
        a = _spawn(lib, w, RAIDER, 1000.0, 1000.0)
        b = _spawn(lib, w, RAIDER, 1005.0, 1000.0)
        for _ in range(5):
            lib.om_tactical_step(w)
        assert _gap(lib, w, a, b) == pytest.approx(30.0, abs=STEP_TOL)
    finally:
        lib.om_world_free(w)


@pytest.mark.parametrize("unit_type", SIX_TYPES)
@pytest.mark.parametrize("radius", [RADIUS_MIN, 4.05, 15.0, 30.0, RADIUS_MAX])
def test_H_041_positive_control_a_valid_call_returns_zero(lib, unit_type, radius):
    """Positive control of the -1 tests (story: "(positive control)"): every one of the six types takes a radius
    inside 1 to 200, the bounds 1 and 200 and Westley's 4.05 and 30 included, and returns 0. Without this a -1
    could be a function that refuses everything. Red today: symbol not exported."""
    w = _world(lib)
    try:
        assert _set_radius(lib, w, unit_type, radius) == 0
    finally:
        lib.om_world_free(w)


def test_H_041_control_reach_setter_returns_minus_one_for_an_unknown_type_and_zero_for_a_known_one(lib):
    """Control (green today and after): om_roster_set_reach, the function the new one sits beside, returns -1 for
    type 99 and 0 for the Raider, so the -1 / 0 reading above has a known-good counterpart on this harness."""
    w = _world(lib)
    try:
        assert lib.om_roster_set_reach(w, 99, 0, 0) == -1
        assert lib.om_roster_set_reach(w, RAIDER, 0, 0) == 0
    finally:
        lib.om_world_free(w)


# ---- determinism: radius 15 everywhere is byte-identical to never calling the function ----------------------------

def _trace_hash(lib, set_all_to=None, ticks=300):
    """The mixed scene of test_PP_collision_radius_runtime.py (the gap crossing; an idle overlapping pair; a 3 x 2 group
    move through overlap; a lone mover that arrives), one seed, one command stream. sha256 over the little-endian
    double x, y of every unit in id order after every tick. set_all_to: None = the function is never called; a
    number = every one of the six types is set to it before the first spawn."""
    w = _world(lib)
    try:
        if set_all_to is not None:
            for t in SIX_TYPES:
                assert _set_radius(lib, w, t, set_all_to) == 0
        ids = [_spawn(lib, w, RAIDER, 1000.0, 1000.0), _spawn(lib, w, RAIDER, 1080.0, 1000.0)]
        m = _spawn(lib, w, RAIDER, 1040.0, 1200.0)
        ids.append(m)
        lib.om_command_move(w, m, 1040.0, 800.0)
        ids += [_spawn(lib, w, RAIDER, 2000.0, 1000.0), _spawn(lib, w, RAIDER, 2005.0, 1003.0)]
        grp = [_spawn(lib, w, RAIDER, 1500.0 + 12.0 * (i % 3), 1500.0 + 12.0 * (i // 3)) for i in range(6)]
        ids += grp
        arr = (ctypes.c_uint32 * len(grp))(*grp)
        lib.om_command_group_move(w, arr, len(grp), 1500.0, 1900.0)
        lone = _spawn(lib, w, RAIDER, 500.0, 500.0)
        ids.append(lone)
        lib.om_command_move(w, lone, 500.0, 700.0)
        h = hashlib.sha256()
        for _ in range(ticks):
            lib.om_tactical_step(w)
            for u in ids:
                h.update(struct.pack("<dd", *_pos(lib, w, u)))
        return h.hexdigest()
    finally:
        lib.om_world_free(w)


def test_H_041_control_never_calling_the_function_reproduces_the_recorded_trace(lib):
    """Control (green today and after): "same seed and command stream give a byte-identical trace when ... the
    function is never called". The fence the builder may not cross: an unset type stays OM_UNIT_COLLISION_RADIUS 15
    and the trace equals TRACE_R15."""
    assert _trace_hash(lib, None) == TRACE_R15, "function never called: trace differs from the one recorded on main"


def test_H_041_every_value_15_reproduces_the_recorded_trace(lib):
    """H-041 Tests, third line: "same seed and command stream give a byte-identical trace when every value is 15".
    All six types set to 15.0 give TRACE_R15 and the never-called trace. Red today: symbol not exported."""
    h = _trace_hash(lib, 15.0)
    assert h == TRACE_R15, "every type set to 15: trace differs from the never-called trace"
    assert h == _trace_hash(lib, None)


def test_H_041_control_the_trace_hash_sees_a_changed_radius(lib):
    """Positive control for the two hashes above: all six types at 30 hash differently from TRACE_R15, so equality
    at 15 means the radius was read as 15 and not that the hash cannot see a radius. Red today: symbol not exported."""
    assert _trace_hash(lib, 30.0) != TRACE_R15, "every type at 30 hashes like 15: the hash cannot see the radius"
