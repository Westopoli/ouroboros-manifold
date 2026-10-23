# Rule pins: R-097-06@519df5, R-097-10@a759df, R-101-01@5b5b1e
"""PP-move wave A5: Westley's collision fix (Addendum 57, A156 to A158).

Proves E-13 R-097-10 (the collision rule, renumbered from the second R-097-06 by A158): every unit, moving or
stopped, starts pair checks; the push pass repeats up to COLLISION_PASSES = 10 per tick and stops early when
no pair is closer than 30 wu; the stationary-pair split rule and the push-out stay (ALG-68). Also R-101-01
(S-101) for the 20-unit scene at its A157 tolerance. This is a deliberate difference from the Python rule
"only a moving, lower-id unit starts a pair check"; the Python gets the same change
(simulation/test_collision_all_start_checks.py).

Red on the old rule for these reasons (the engine checks a pair only when its lower-id unit moved this tick,
and runs 3 passes): a stopped lower-id unit never pushes a higher-id arrival; two idle overlapping units are
never touched; the 20-unit scene bottoms out at 4.98 wu (A154 pile-up); a long pile needs more than 3 passes.

Early stop: no om_* debug counter of the number of passes exists (grep csrc/ouroboros_sim.h), so the early-stop
rule is tested by its outcome only (a world with no pair under 30 wu is left exactly as it was).
Positions are compared with POS_TOL, numeric slack for the cheap trig of the C, not a rule threshold.
"""
import ctypes
import math
import pathlib
import re
import subprocess

import pytest

import conftest
from conftest import OMFeature

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RAIDER = 0
FRIEND = 0
ENEMY = 1   # TD-VG-E-idle-own (test-defect, assumption-changed by the R-097-10 rewrite, Architect 2026-10-23): the idle unit is an enemy
POS_TOL = 0.05
DIAMETER = 30.0  # 2 x radius 15
CANVAS = 4000.0  # the Python's open_field, A157's scene


@pytest.fixture
def tw(lib, world_factory):
    """A world with the tactical feature on and the new movement on (PURSUE_BY_STEERING = param 0)."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    lib.om_tactical_set_param(w, 0, 1.0)
    return w


def _arr(ids):
    return (ctypes.c_uint32 * len(ids))(*ids)


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _min_pair(lib, w, ids):
    ps = [lib.om_unit_get_pos(w, u) for u in ids]
    return min(_dist(ps[i], ps[j]) for i in range(len(ps)) for j in range(i + 1, len(ps)))


# ------------------------------------------------------------------ every unit starts pair checks

def test_R_097_10_unit_walking_into_a_stopped_one_is_pushed_out(lib, tw):
    """R-097-10: S (id 1, stopped) at (110,0); M (id 2, the HIGHER id) at (120,0) walks -x to (112.5,0), 2.5 wu
    from S. M takes the full displacement and S none: M ends at (140,0), S still at (110,0), 30 apart. The old
    rule checks the pair only when its lower-id unit (S) moved, so M ends at (112.5,0)."""
    s = lib.om_unit_spawn(tw, RAIDER, ENEMY, 110.0, 0.0, 0)
    m = lib.om_unit_spawn(tw, RAIDER, FRIEND, 120.0, 0.0, 0)
    assert s < m, "scene error: the stopped unit must have the lower id"
    lib.om_command_move(tw, m, -1000.0, 0.0)
    lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, s) == (110.0, 0.0), "the stopped unit was pushed"
    pm = lib.om_unit_get_pos(tw, m)
    assert pm == pytest.approx((140.0, 0.0), abs=POS_TOL)
    assert _dist(pm, (110.0, 0.0)) >= DIAMETER - POS_TOL


def test_R_097_10_lower_id_mover_still_pushes_control(lib, tw):
    """Positive control for the test above (green today, stays green): the mirror scene with the MOVER at the
    lower id. M (id 1) at (100,0) goes -x to (92.5,0), 17.5 from the stopped S (id 2) at (110,0): pushed back to
    (80,0), S unmoved."""
    m = lib.om_unit_spawn(tw, RAIDER, FRIEND, 100.0, 0.0, 0)
    s = lib.om_unit_spawn(tw, RAIDER, ENEMY, 110.0, 0.0, 0)
    lib.om_command_move(tw, m, -1000.0, 0.0)
    lib.om_tactical_step(tw)
    assert lib.om_unit_get_pos(tw, s) == (110.0, 0.0)
    assert lib.om_unit_get_pos(tw, m) == pytest.approx((80.0, 0.0), abs=POS_TOL)


def test_R_097_10_two_stopped_overlapping_units_split_the_displacement(lib, tw):
    """R-097-10 (the split rule, kept): three stopped units in a row at x 100, 115, 140 (y 0). Nobody moves, yet
    every unit starts pair checks: the first pair (15 apart) splits its overlap 7.5 each, which displaces the
    middle unit, so it splits again with the third. Within the tick no pair is closer than 30 wu, and because
    every push of two stopped units is split equally along x the sum of the x positions is unchanged (355) and y
    stays 0. Old rule: nobody moved, nothing is checked, the row is left at 100, 115, 140."""
    ids = [lib.om_unit_spawn(tw, RAIDER, FRIEND, x, 0.0, 0) for x in (100.0, 115.0, 140.0)]
    assert _min_pair(lib, tw, ids) < DIAMETER, "scene error: the row must start overlapped"
    lib.om_tactical_step(tw)
    assert _min_pair(lib, tw, ids) >= DIAMETER - POS_TOL
    ps = [lib.om_unit_get_pos(tw, u) for u in ids]
    assert sum(p[0] for p in ps) == pytest.approx(355.0, abs=POS_TOL)
    assert all(p[1] == pytest.approx(0.0, abs=POS_TOL) for p in ps)


# ------------------------------------------------------------------ early stop

def test_R_097_10_world_with_no_overlap_is_left_alone(lib, tw):
    """R-097-10 (stop early when no pair is closer than 30 wu): stopped units 31 wu apart are not moved by any
    pass, however many the cap allows. Outcome only (no pass counter exists, see the module note). Control: the
    same row at 29 wu (below 30) does get pushed, so the detector can trip."""
    far = [lib.om_unit_spawn(tw, RAIDER, FRIEND, 100.0 + 31.0 * i, 0.0, 0) for i in range(4)]
    for _ in range(3):
        lib.om_tactical_step(tw)
    for i, u in enumerate(far):
        assert lib.om_unit_get_pos(tw, u) == (100.0 + 31.0 * i, 0.0)


def test_R_097_10_overlap_control_is_pushed(lib, tw):
    """Positive control for the early-stop test: stopped units 29 wu apart move (every unit starts checks)."""
    near = [lib.om_unit_spawn(tw, RAIDER, FRIEND, 100.0 + 29.0 * i, 0.0, 0) for i in range(2)]
    lib.om_tactical_step(tw)
    assert _min_pair(lib, tw, near) >= DIAMETER - POS_TOL
    assert lib.om_unit_get_pos(tw, near[0]) != (100.0, 0.0)


# ------------------------------------------------------------------ the pass cap

def test_R_097_10_a_pile_needing_more_than_three_passes_converges_within_the_cap(lib, tw):
    """R-097-10 (up to COLLISION_PASSES = 10 passes a tick): three stopped units 12 wu apart along x
    (1000, 1012, 1024). The pushes of one pass displace the units they have just separated, so the row needs
    more passes: measured on a scratch build of the new rule, 3 passes leave the closest pair at 29.16 wu and
    10 reach 30.0. One tick later every pair is >= 30 (POS_TOL slack). On the old rule nobody moved, so
    nothing is checked and the row stays at 12 wu."""
    ids = [lib.om_unit_spawn(tw, RAIDER, FRIEND, 1000.0 + 12.0 * i, 1000.0, 0) for i in range(3)]
    lib.om_tactical_step(tw)
    assert _min_pair(lib, tw, ids) >= DIAMETER - POS_TOL


# ------------------------------------------------------------------ the R-101-01 scene

def test_R_101_01_shared_scene_keeps_every_pair_at_29_over_200_ticks(lib, tw):
    """R-101-01 at A157's tolerance (30.0 - 1.0, the worst pair with the fix is 29.11 wu; A154 measured 4.98 on
    the old rule). The 20-unit scene of test_E13_S101_movement_that_reads.py: 4 x 5 block 35 wu apart, one
    group move to (1000,70), canvas 4000 x 4000 as the Python's map. Every pair >= 29.0 on every tick."""
    assert lib.om_map_set_canvas(tw, CANVAS, CANVAS) == 0
    ids = [lib.om_unit_spawn(tw, RAIDER, FRIEND, r * 35.0, c * 35.0, 0) for r in range(4) for c in range(5)]
    assert lib.om_command_group_move(tw, _arr(ids), 20, 1000.0, 70.0) != 0
    for tick in range(200):
        lib.om_tactical_step(tw)
        worst = _min_pair(lib, tw, ids)
        assert worst >= 29.0, f"tick {tick}: worst pair {worst:.2f} wu"


def test_R_101_01_scene_control_old_rule_would_trip_the_detector(lib, tw):
    """Positive control for the detector above: the same measure applied to two stopped units 20 wu apart,
    which the 29.0 bar must flag as overlapped before any tick runs."""
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 0.0, 0.0, 0)
    b = lib.om_unit_spawn(tw, RAIDER, FRIEND, 20.0, 0.0, 0)
    assert _min_pair(lib, tw, [a, b]) < 29.0


# ------------------------------------------------------------------ determinism, O0 vs O2

def _load_build(opt):
    path = REPO_ROOT / "build" / opt / "libouroboros.so"
    res = subprocess.run(["make", "-s", str(path.relative_to(REPO_ROOT))], cwd=str(REPO_ROOT),
                         capture_output=True, text=True, timeout=300)
    assert res.returncode == 0, res.stderr[-2000:]
    h = ctypes.CDLL(str(path))
    conftest._configure_common(h)
    conftest._bind_generated(h)
    return h


def _pile_positions(h):
    """The 20-unit scene plus a stopped lower-id unit that a late arrival walks into, 60 ticks."""
    w = h.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(1))
    try:
        h.om_world_set_feature(w, OMFeature.TACTICAL, 1)
        h.om_tactical_set_param(w, 0, 1.0)
        assert h.om_map_set_canvas(w, CANVAS, CANVAS) == 0
        ids = [h.om_unit_spawn(w, RAIDER, FRIEND, r * 35.0, c * 35.0, 0) for r in range(4) for c in range(5)]
        h.om_unit_spawn(w, RAIDER, FRIEND, 300.0, 70.0, 0)   # stopped, higher id
        assert h.om_command_group_move(w, _arr(ids), 20, 1000.0, 70.0) != 0
        for _ in range(60):
            h.om_tactical_step(w)
        return [h.om_unit_get_pos(w, u) for u in range(1, 22)]
    finally:
        h.om_world_free(w)


def test_R_097_10_positions_are_identical_at_O0_and_O2():
    """Determinism contract: the new pass gives byte-identical positions from the -O0 and -O2 builds
    (make build/O0/libouroboros.so build/O2/libouroboros.so)."""
    assert _pile_positions(_load_build("O0")) == _pile_positions(_load_build("O2"))


# ------------------------------------------------------------------ documentation

def test_R_097_10_constants_header_defines_collision_passes():
    """csrc/om_constants.h defines COLLISION_PASSES = 10 (generated by scripts/specfactory/alg_constants.py
    --emit from ALG-68, like the other ALG-68 constants). Red until written."""
    text = (REPO_ROOT / "csrc/om_constants.h").read_text()
    assert re.search(r"#define\s+(OM_)?COLLISION_PASSES\s+10\b", text), "COLLISION_PASSES (10) not defined in om_constants.h"


def test_R_097_10_collision_passes_is_documented_in_algorithms_md():
    """R-097-10 / ALG-68: docs/bible/algorithms.md ALG-68 names COLLISION_PASSES = 10 (the file the constants
    are generated from, scripts/specfactory/alg_constants.py). Red until written on this branch."""
    text = (REPO_ROOT / "docs/bible/algorithms.md").read_text()
    m = re.search(r"\*\*ALG-68[^\n]*", text)
    assert m, "ALG-68 paragraph missing"
    assert re.search(r"COLLISION_PASSES\s*=\s*10\b", m.group(0)), "ALG-68 does not name COLLISION_PASSES = 10"
