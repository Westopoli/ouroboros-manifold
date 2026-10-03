"""PP collision settle clause: ruling A184 on E-13 R-097-10 / ALG-68.

Rule under test (A184): in the collision pass, a push pass in which no unit is displaced by more than
COLLISION_SETTLE_EPS = 0.1 wu ends the sequence for that tick (the small pass is applied, no further pass
runs). It sits beside the existing stop "no pair is closer than 2 * 15" and the cap COLLISION_PASSES = 10.

Observation without new ABI: no om_* pass counter exists (grep csrc/ouroboros_sim.h), so the sequence length
is read from its outcome. om_collision_pass(w) runs exactly one tick's push sequence on the current
positions. A pure-Python all-pairs reference (the one of test_core_collision_reference.py, here with
every unit moving, plus an optional settle eps) is run on the same start; the C positions must equal the
reference to 1e-9 wu (numeric slack for the C's arithmetic, not a rule threshold). The reference with
eps = 0.1 and the reference with eps = 0 (the pre-rule behaviour) differ on the jam scene, so matching one
or the other tells which rule the build runs. The jam tests are red until the rule lands.
Displacement of a unit in a pass is its distance moved over the whole pass.
"""
import ctypes
import math
import pathlib
import random
import re

import pytest

from conftest import OMFeature

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RAIDER = 0
FACTION = 0
LAYER = 0
TARGET = 30.0            # 2 x UNIT_COLLISION_RADIUS 15
COLLISION_PASSES = 10
SETTLE_EPS = 0.1         # A184, COLLISION_SETTLE_EPS
EXACT_EPS = 1e-9
SLACK = 1e-9
DEST = 1e6


def reference(positions, max_iter=COLLISION_PASSES, settle_eps=0.0):
    """All-pairs i<j push passes, every unit moving (equal split). Returns (positions, passes_run).
    settle_eps > 0: stop after a pass in which no unit moved more than settle_eps."""
    ids = sorted(positions)
    passes = 0
    for _ in range(max_iter):
        before = {u: list(positions[u]) for u in ids}
        changed = False
        for ii, i in enumerate(ids):
            for j in ids[ii + 1:]:
                ax, ay = positions[i]
                bx, by = positions[j]
                dx, dy = bx - ax, by - ay
                if dx * dx + dy * dy >= TARGET * TARGET:
                    continue
                dist = math.sqrt(dx * dx + dy * dy)
                if dist >= TARGET:
                    continue
                changed = True
                if dist < EXACT_EPS:
                    positions[i][0] = ax + TARGET / 2.0
                    positions[j][0] = bx - TARGET / 2.0
                else:
                    ov = (TARGET - dist) * 0.5
                    ux, uy = dx / dist, dy / dist
                    positions[i][0], positions[i][1] = ax - ux * ov, ay - uy * ov
                    positions[j][0], positions[j][1] = bx + ux * ov, by + uy * ov
        if not changed:
            break
        passes += 1
        if settle_eps > 0.0:
            worst = max(math.hypot(positions[u][0] - before[u][0], positions[u][1] - before[u][1]) for u in ids)
            if worst <= settle_eps:
                break
    return positions, passes


def _world(lib, seed=1):
    w = lib.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(seed))
    assert w
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    lib.om_tactical_set_param(w, 0, 1.0)   # PURSUE_BY_STEERING: the 10-pass sequence
    return w


def _spawn(lib, w, pts):
    ids = [lib.om_unit_spawn(w, RAIDER, FACTION, x, y, LAYER) for x, y in pts]
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    lib.om_command_group_move(w, arr, len(ids), DEST, DEST)   # every unit has a move target
    return ids


def _jam_points(n, seed, box):
    rng = random.Random(seed)
    return [(rng.uniform(0.0, box), rng.uniform(0.0, box)) for _ in range(n)]


def _c_after_pass(lib, pts):
    w = _world(lib)
    try:
        ids = _spawn(lib, w, pts)
        start = {u: list(lib.om_unit_get_pos(w, u)) for u in ids}
        lib.om_collision_pass(w)
        return start, {u: list(lib.om_unit_get_pos(w, u)) for u in ids}
    finally:
        lib.om_world_free(w)


def _max_diff(a, b):
    return max(max(abs(a[u][0] - b[u][0]), abs(a[u][1] - b[u][1])) for u in a)


# ---- scenes: jam seeds (dense, a few hundred units) and a sparse scene -----------------------------

JAM_SEEDS = (1, 2, 3, 4)
JAM_N, JAM_BOX = 300, 1000.0


def _jam_diverges(seed):
    pts = _jam_points(JAM_N, seed, JAM_BOX)
    base = {i + 1: list(p) for i, p in enumerate(pts)}
    no_rule, p0 = reference({u: list(v) for u, v in base.items()})
    rule, p1 = reference({u: list(v) for u, v in base.items()}, settle_eps=SETTLE_EPS)
    return _max_diff(no_rule, rule) > SLACK, p0, p1


# ---- 3. detector positive control ------------------------------------------------------------------

def test_R_097_10_A184_jam_early_stop_can_trip_reference():
    """Positive control (A184): on the jam scenes the settle rule shortens the sequence (fewer passes than
    COLLISION_PASSES) and moves the result away from the eps = 0 path, so the detector below is live."""
    tripped = []
    for seed in JAM_SEEDS:
        div, p0, p1 = _jam_diverges(seed)
        if div:
            assert p1 < p0 and p1 < COLLISION_PASSES, f"seed {seed}: rule path ran {p1} passes, no-rule {p0}"
            tripped.append(seed)
    assert tripped, "no jam seed separates the rule from the pre-rule path; the scene cannot test A184"


# ---- 1. the jam ends early (red until the rule lands) ----------------------------------------------

@pytest.mark.parametrize("seed", JAM_SEEDS)
def test_R_097_10_A184_jam_passes_end_when_no_unit_moves_more_than_eps(lib, seed):
    """R-097-10 / A184: on a jam where the settle rule and the pre-rule path differ, the C positions equal the
    reference with COLLISION_SETTLE_EPS = 0.1 (and so differ from the eps = 0 path). Red on today's build,
    which always runs to the cap or to no-overlap."""
    div, _, _ = _jam_diverges(seed)
    assert div, f"seed {seed} does not separate the settle rule from the pre-rule path; drop it from JAM_SEEDS"
    pts = _jam_points(JAM_N, seed, JAM_BOX)
    start, got = _c_after_pass(lib, pts)
    rule, _ = reference({u: list(v) for u, v in start.items()}, settle_eps=SETTLE_EPS)
    assert _max_diff(got, rule) <= SLACK, f"seed {seed}: C differs from the settle-rule reference by {_max_diff(got, rule):.3e}"


def test_R_097_10_A184_jam_scene_is_not_vacuous():
    """The jam scenes must separate the two paths on at least one seed (else the test above is vacuous)."""
    assert any(_jam_diverges(s)[0] for s in JAM_SEEDS)


# ---- 2. sparse scene: bit-identical to today's build (green now, must stay green) ------------------

SPARSE_PTS = [(100.0, 100.0), (110.0, 100.0), (400.0, 400.0), (700.0, 100.0), (700.0, 125.0),
              (1000.0, 1000.0), (1500.0, 300.0), (2000.0, 2000.0)]
# Golden from the pre-rule build (origin/push/pp-c3-coll-land, 7fd467da), one om_collision_pass.
SPARSE_GOLDEN = [
    '0x1.6800000000000p+6',
    '0x1.9000000000000p+6',
    '0x1.e000000000000p+6',
    '0x1.9000000000000p+6',
    '0x1.9000000000000p+8',
    '0x1.9000000000000p+8',
    '0x1.5e00000000000p+9',
    '0x1.8600000000000p+6',
    '0x1.5e00000000000p+9',
    '0x1.fe00000000000p+6',
    '0x1.f400000000000p+9',
    '0x1.f400000000000p+9',
    '0x1.7700000000000p+10',
    '0x1.2c00000000000p+8',
    '0x1.f400000000000p+10',
    '0x1.f400000000000p+10',
]
# Hex floats, x then y per unit in id order.


def test_R_097_10_A184_sparse_scene_bit_identical_to_pre_rule_build(lib):
    """Regression guard (A184): two overlapping pairs settle within the first passes by a larger move than
    eps then end by no-overlap; the settle rule must not change a single bit."""
    start, got = _c_after_pass(lib, SPARSE_PTS)
    flat = [v.hex() for u in sorted(got) for v in got[u]]
    assert flat == SPARSE_GOLDEN


# ---- 4. constant lint ------------------------------------------------------------------------------

def test_R_097_10_A184_algorithms_md_names_settle_eps():
    """ALG-68 text names COLLISION_SETTLE_EPS = 0.1 (A184); the generator reads it from algorithms.md."""
    text = (REPO_ROOT / "docs/bible/algorithms.md").read_text()
    m = re.search(r"\*\*ALG-68[^\n]*", text)
    assert m, "ALG-68 paragraph missing"
    assert re.search(r"COLLISION_SETTLE_EPS\s*=\s*0\.1\b", m.group(0)), "ALG-68 does not name COLLISION_SETTLE_EPS = 0.1"


def test_R_097_10_A184_constants_header_defines_settle_eps():
    """csrc/om_constants.h (generated by scripts/specfactory/alg_constants.py) defines OM_COLLISION_SETTLE_EPS 0.1."""
    text = (REPO_ROOT / "csrc/om_constants.h").read_text()
    assert re.search(r"#define\s+OM_COLLISION_SETTLE_EPS\s+0\.1\b", text), "OM_COLLISION_SETTLE_EPS 0.1 not defined"


def test_R_097_10_A184_epic_clause_present():
    """E-13 carries the settle clause (A184) in the collision rule's row. On this branch the epic has no
    R-097-10 row (the collision row at line 73 still reads R-097-06, the A158 renumbering is not here), so the
    check is on the epic's collision rules: some R-097 row names COLLISION_SETTLE_EPS."""
    text = next(REPO_ROOT.glob("docs/bible/epics/E-13-*.md")).read_text()
    rows = [ln for ln in text.splitlines() if re.match(r"- R-097-\d+", ln)]
    assert any("COLLISION_SETTLE_EPS" in ln for ln in rows), "no R-097 row names COLLISION_SETTLE_EPS"
