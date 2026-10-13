"""E-13 R-207-05 / E-01 R-004-07 / R-200-04: least-time routes for walking units (terrain stage 2).

Spec 2026-10-06 (docs/northstar/plans/2026-10-06-terrain-stage2-spec.md), lane "planner-a" (part A) and
"planner-b" (part B, slope links, appended later by the same test writer).

om_walk_route (csrc/om_internal.h, internal, declared with ctypes below) is Dijkstra over the walk mask of the
unit's layer: 8-neighbour steps costed by distance over the unit's speed (diagonal = sqrt 2, Q16 92682), a step
that rises in terrain height costed at speed / OM_TP_SLOPE_UP_DIV, a step that falls at speed *
OM_TP_SLOPE_DOWN_MULT (R-004-07, Westley's 1.1 rule), lowest cell index on a tie, nearest reachable cell when the
goal cannot be reached (R-200-04), `cap` too small returns the needed point count and writes nothing, no layer
change in part A. `cap` counts points (x, y pairs); `pts` holds 2 * cap doubles.

Assumption flagged for the planner-a builder: with no terrain generated (the open map) every cell of the canvas
is walkable, so the route is the straight line (the spec's open-map test); the contract mask returns 0 cells there.
Numbers marked "provisional (2026-10-06)" are test drafts; Westley may tighten them.
"""
import ctypes
import json
import math
import pathlib
import subprocess
import sys

import pytest

from conftest import OMFeature, OMTacParam

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CSIM_DIR = pathlib.Path(__file__).resolve().parent

SEED = 11
CANVAS = 16000.0
CELL = 100.0
VANGUARD = 2
CLONE_TYPE = 40                 # provisional (2026-10-06): a free custom type id
KIND_WALKING = 1                # OM_MOVE_WALKING
BIG_CAP = 8192                  # points; a 160-cell crossing needs far fewer. provisional (2026-10-06)
SECONDS_REL = 1e-3              # provisional (2026-10-06): Q16 cost arithmetic tolerance
MIN_RISE_WU = 5.0               # provisional (2026-10-06): a step must climb this much to count as rising
DIAG = 92682 / 65536.0          # Q16 sqrt 2, as the spec fixes it
OPEN_EAST_CELLS = 30            # provisional (2026-10-06)
OPEN_DIAG_CELLS = 20            # provisional (2026-10-06)
SENTINEL = -12345.0

_lib_ready = set()


def _declare(lib):
    if id(lib) in _lib_ready:
        return
    lib.om_walk_route.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double,
                                  ctypes.POINTER(ctypes.c_double), ctypes.c_uint32,
                                  ctypes.POINTER(ctypes.c_double)]
    lib.om_walk_route.restype = ctypes.c_int
    _lib_ready.add(id(lib))


# ---------------------------------------------------------------- world and unit helpers

def _setup(lib, w, terrain=True):
    _declare(lib)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    if terrain:
        assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    rc = lib.om_roster_register_custom_unit(
        w, CLONE_TYPE, lib.om_unit_profile_category(w, VANGUARD), b"vanguard_clone",
        lib.om_unit_profile_max_hp(w, VANGUARD), lib.om_unit_profile_base_damage(w, VANGUARD),
        lib.om_unit_profile_attack_interval(w, VANGUARD), lib.om_unit_profile_attack_range(w, VANGUARD),
        lib.om_unit_profile_speed(w, VANGUARD), lib.om_unit_profile_sensor_radius(w, VANGUARD),
        lib.om_unit_profile_layer_transition_time(w, VANGUARD), lib.om_unit_profile_aoe_radius(w, VANGUARD), 0)
    assert rc == 0, f"register clone: {rc}"
    assert lib.om_roster_set_movement_kind(w, CLONE_TYPE, KIND_WALKING) == 0
    return w


def _new_world(lib):
    w = lib.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(1))
    assert w
    return w


def _centre(cx, cy):
    return (cx + 0.5) * CELL, (cy + 0.5) * CELL


def _cell_of(x, y):
    return int(x // CELL), int(y // CELL)


def _spawn(lib, w, cx, cy, layer):
    x, y = _centre(cx, cy)
    u = lib.om_unit_spawn(w, CLONE_TYPE, 0, x, y, layer)
    assert u != 0, "spawn failed"
    return u


def _route(lib, w, unit, gx, gy, cap=BIG_CAP):
    """Returns (n, [(x, y)] for the written points, seconds). pts is pre-filled with a sentinel."""
    buf = (ctypes.c_double * (2 * cap))(*([SENTINEL] * (2 * cap)))
    sec = ctypes.c_double(SENTINEL)
    n = lib.om_walk_route(w, unit, gx, gy, buf, cap, ctypes.byref(sec))
    pts = [(buf[2 * i], buf[2 * i + 1]) for i in range(max(0, min(n, cap)))]
    return n, pts, sec.value


def _grid(lib, w):
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    return cw.value, ch.value


def _mask(lib, w, layer):
    cw, ch = _grid(lib, w)
    n = cw * ch
    buf = (ctypes.c_uint8 * n)()
    assert lib.om_terrain_walk_mask(w, layer, buf, n) == n
    return bytes(buf)


def _component_cells(mask, cw, ch, start):
    seen = {start}
    stack = [start]
    while stack:
        i = stack.pop()
        cx, cy = i % cw, i // cw
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = cx + dx, cy + dy
                if (dx or dy) and 0 <= nx < cw and 0 <= ny < ch:
                    j = ny * cw + nx
                    # R-001-07 no corner cutting: a diagonal needs both orthogonals walkable.
                    if dx and dy and not (mask[cy * cw + nx] and mask[ny * cw + cx]):
                        continue
                    if mask[j] and j not in seen:
                        seen.add(j)
                        stack.append(j)
    return seen


def _pick_layer_and_component(lib, w):
    """The engine layer with the most masked cells, and its component (8-neighbour) holding the lowest masked cell."""
    cw, ch = _grid(lib, w)
    best = None
    for layer in range(5):
        m = _mask(lib, w, layer)
        count = sum(m)
        if best is None or count > best[0]:
            best = (count, layer, m)
    count, layer, mask = best
    assert count > 0, "walk mask is empty on every layer (mask lane not landed or generator gave no ground)"
    comp = sorted(_component_cells(mask, cw, ch, mask.index(1)))
    return layer, mask, comp, cw, ch


def _same_band_pairs(comp):
    """Three (start, goal) cell index pairs inside one component; provisional (2026-10-06)."""
    n = len(comp)
    assert n >= 40, f"largest component only {n} cells"
    return [(comp[0], comp[n * 3 // 4]), (comp[n // 3], comp[n // 2]), (comp[n * 2 // 3], comp[n // 5])]


def _nearest_expected(comp, cw, goal_cell):
    """Reachable cell nearest the goal cell centre by Euclidean distance, lowest index on a tie; integer cell units."""
    gx, gy = goal_cell % cw, goal_cell // cw
    best = None
    ties = 0
    for i in comp:
        d = (i % cw - gx) ** 2 + (i // cw - gy) ** 2
        if best is None or d < best[0]:
            best, ties = (d, i), 1
        elif d == best[0]:
            ties += 1
    return best[1], ties


def _cells_of(pts):
    return [_cell_of(x, y) for x, y in pts]


def _path_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


# ---------------------------------------------------------------- scenario shared with the child process

def collect(lib, w):
    """Routes for every case that must repeat byte for byte; JSON-able."""
    layer, mask, comp, cw, ch = _pick_layer_and_component(lib, w)
    out = {"layer": layer, "routes": []}
    goals = [(s, g) for s, g in _same_band_pairs(comp)]
    outside = next(i for i in range(len(mask) - 1, -1, -1) if i not in set(comp))
    goals.append((comp[0], outside))
    for s, g in goals:
        u = _spawn(lib, w, s % cw, s // cw, layer)
        gx, gy = _centre(g % cw, g // cw)
        n, pts, sec = _route(lib, w, u, gx, gy)
        out["routes"].append({"n": n, "pts": pts, "sec": sec})
    return out


_CHILD = """
import ctypes, json, sys
sys.path.insert(0, sys.argv[1])
import conftest
import test_E13_R207_05_walker_routes as m
lib = conftest.load_lib()
w = m._setup(lib, m._new_world(lib))
print(json.dumps(m.collect(lib, w)))
"""


# ---------------------------------------------------------------- fixtures

@pytest.fixture
def ground(lib, world_factory):
    return _setup(lib, world_factory(n_regions=1))


@pytest.fixture
def open_map(lib, world_factory):
    return _setup(lib, world_factory(n_regions=1), terrain=False)


# ================================================================ PART A: planner-a

@pytest.mark.parametrize("which", [0, 1, 2])
def test_R_207_05_same_band_route_stays_on_masked_cells(lib, ground, which):
    """R-207-05: on seed 11 a route between two cells of one band stays on the unit's layer mask, step by step."""
    layer, mask, comp, cw, ch = _pick_layer_and_component(lib, ground)
    s, g = _same_band_pairs(comp)[which]
    u = _spawn(lib, ground, s % cw, s // cw, layer)
    gx, gy = _centre(g % cw, g // cw)
    n, pts, sec = _route(lib, ground, u, gx, gy)
    assert n >= 2, f"no route written, om_walk_route returned {n}"
    assert pts[0] == _centre(s % cw, s // cw)
    assert pts[-1] == (gx, gy), "reachable goal: the last point is the goal cell centre"
    cells = _cells_of(pts)
    for (ax, ay), (bx, by) in zip(cells, cells[1:]):
        assert max(abs(ax - bx), abs(ay - by)) == 1, f"not an 8-neighbour step: {(ax, ay)} to {(bx, by)}"
    for cx, cy in cells:
        assert mask[cy * cw + cx] == 1, f"route leaves the layer {layer} mask at cell {(cx, cy)}"
    # time lies between the all-falling and all-rising bounds (R-004-07)
    speed = lib.om_unit_effective_speed(ground, u)
    up_div = lib.om_tactical_get_param(ground, OMTacParam.SLOPE_UP_DIV)
    down_mult = lib.om_tactical_get_param(ground, OMTacParam.SLOPE_DOWN_MULT)
    length = _path_len(pts)
    assert length / (speed * down_mult) * (1 - SECONDS_REL) <= sec <= length / (speed / up_div) * (1 + SECONDS_REL), \
        f"seconds {sec} outside [{length / (speed * down_mult)}, {length / (speed / up_div)}]"


def test_R_200_04_unreachable_goal_ends_at_nearest_reachable_cell(lib, ground):
    """R-200-04: the goal cell is outside the unit's component; the route ends at the reachable cell nearest it."""
    layer, mask, comp, cw, ch = _pick_layer_and_component(lib, ground)
    inside = set(comp)
    goal = max((i for i in range(cw * ch) if i not in inside),
               key=lambda i: ((i % cw - comp[0] % cw) ** 2 + (i // cw - comp[0] // cw) ** 2, -i))
    want, _ties = _nearest_expected(comp, cw, goal)
    u = _spawn(lib, ground, comp[0] % cw, comp[0] // cw, layer)
    gx, gy = _centre(goal % cw, goal // cw)
    n, pts, sec = _route(lib, ground, u, gx, gy)
    assert n >= 2, f"om_walk_route returned {n}"
    assert pts[-1] == _centre(want % cw, want // cw), f"ended at {_cell_of(*pts[-1])}, expected cell {(want % cw, want // cw)}"
    assert sec > 0.0


def test_R_200_04_tie_goes_to_the_lower_cell_index(lib, ground):
    """R-200-04: two reachable cells equally near the goal: the lower cell index wins."""
    layer, mask, comp, cw, ch = _pick_layer_and_component(lib, ground)
    inside = set(comp)
    found = None
    for i in comp:
        cx, cy = i % cw, i // cw
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx, ny = cx + dx, cy + dy
                j = ny * cw + nx
                if (dx or dy) and 0 <= nx < cw and 0 <= ny < ch and j not in inside:
                    _want, ties = _nearest_expected([c for c in comp if abs(c % cw - nx) <= 4 and abs(c // cw - ny) <= 4], cw, j)
                    if ties >= 2:
                        found = j
                        break
            if found is not None:
                break
        if found is not None:
            break
    assert found is not None, "positive control: no unreachable goal with two equally near reachable cells on this layer"
    want, ties = _nearest_expected(comp, cw, found)
    assert ties >= 2
    u = _spawn(lib, ground, comp[0] % cw, comp[0] // cw, layer)
    gx, gy = _centre(found % cw, found // cw)
    n, pts, _sec = _route(lib, ground, u, gx, gy)
    assert n >= 2, f"om_walk_route returned {n}"
    assert pts[-1] == _centre(want % cw, want // cw), f"ended at {_cell_of(*pts[-1])}, lowest-index nearest is {(want % cw, want // cw)}"


def test_R_207_05_cap_too_small_returns_the_needed_count_and_writes_nothing(lib, ground):
    layer, mask, comp, cw, ch = _pick_layer_and_component(lib, ground)
    s, g = _same_band_pairs(comp)[0]
    u = _spawn(lib, ground, s % cw, s // cw, layer)
    gx, gy = _centre(g % cw, g // cw)
    full, pts, _ = _route(lib, ground, u, gx, gy)
    assert full >= 3, f"om_walk_route returned {full}"
    n, got, sec = _route(lib, ground, u, gx, gy, cap=full - 1)
    assert n == full, f"cap {full - 1}: returned {n}, needed {full}"
    assert got == [] or all(p == (SENTINEL, SENTINEL) for p in got)
    n2, again, _ = _route(lib, ground, u, gx, gy, cap=full)
    assert n2 == full and again == pts, "a cap equal to the needed count writes the whole route"


def test_R_207_05_goal_in_own_cell_returns_zero(lib, ground):
    layer, mask, comp, cw, ch = _pick_layer_and_component(lib, ground)
    u = _spawn(lib, ground, comp[0] % cw, comp[0] // cw, layer)
    gx, gy = _centre(comp[0] % cw, comp[0] // cw)
    n, _pts, sec = _route(lib, ground, u, gx + 10.0, gy - 10.0)
    assert (n, sec) == (0, 0.0), f"unit already in the final cell: got {(n, sec)}"
    # positive control: a different cell does give a route
    other = comp[len(comp) // 2]
    n2, _p, _s = _route(lib, ground, u, *_centre(other % cw, other // cw))
    assert n2 >= 2


def test_R_207_05_two_processes_give_identical_routes(lib):
    runs = []
    for _ in range(2):
        res = subprocess.run([sys.executable, "-c", _CHILD, str(CSIM_DIR)], capture_output=True, text=True,
                             timeout=300, cwd=str(REPO_ROOT))
        assert res.returncode == 0, res.stderr[-2000:]
        runs.append(json.loads(res.stdout.strip().splitlines()[-1]))
    assert runs[0] == runs[1]
    # positive control: stubs returning -1 everywhere agree with themselves
    assert all(r["n"] >= 2 for r in runs[0]["routes"]), [r["n"] for r in runs[0]["routes"]]


def test_R_207_05_open_map_route_is_the_straight_line(lib, open_map):
    """No terrain: east along a row, and a pure 45 degree diagonal; every point on the line, time = length / speed."""
    cw = int(CANVAS / CELL)
    sx, sy = 20, 20
    u = _spawn(lib, open_map, sx, sy, 0)
    speed = lib.om_unit_effective_speed(open_map, u)
    gx, gy = _centre(sx + OPEN_EAST_CELLS, sy)
    n, pts, sec = _route(lib, open_map, u, gx, gy)
    assert n >= 2, f"om_walk_route returned {n}"
    assert pts[0] == _centre(sx, sy) and pts[-1] == (gx, gy)
    assert all(y == pts[0][1] for _x, y in pts), "east route leaves its row"
    assert all(b[0] > a[0] for a, b in zip(pts, pts[1:])), "east route not monotone"
    assert sec == pytest.approx(OPEN_EAST_CELLS * CELL / speed, rel=SECONDS_REL)
    gx, gy = _centre(sx + OPEN_DIAG_CELLS, sy + OPEN_DIAG_CELLS)
    n, pts, sec = _route(lib, open_map, u, gx, gy)
    assert n >= 2 and pts[-1] == (gx, gy)
    x0, y0 = pts[0]
    assert all(abs((x - x0) - (y - y0)) < 1e-6 for x, y in pts), "diagonal route leaves the diagonal"
    assert sec == pytest.approx(OPEN_DIAG_CELLS * CELL * DIAG / speed, rel=SECONDS_REL)
    assert cw > sx + OPEN_EAST_CELLS


def test_R_004_07_a_rising_step_costs_more_than_a_falling_one(lib, ground):
    """One 4-neighbour step, both ways: up costs 100 / (speed / UP_DIV), down costs 100 / (speed * DOWN_MULT)."""
    layer, mask, comp, cw, ch = _pick_layer_and_component(lib, ground)
    best = None
    for i in comp:
        for j in (i + 1, i + cw):
            if j < cw * ch and mask[j] and (j != i + 1 or j % cw != 0):
                ax, ay = _centre(i % cw, i // cw)
                bx, by = _centre(j % cw, j // cw)
                dh = lib.om_terrain_height_at(ground, bx, by) - lib.om_terrain_height_at(ground, ax, ay)
                if best is None or abs(dh) > abs(best[0]):
                    best = (dh, i, j)
    assert best is not None and abs(best[0]) >= MIN_RISE_WU, f"no neighbour pair climbs {MIN_RISE_WU} wu: {best}"
    dh, i, j = best
    lo, hi = (i, j) if dh > 0 else (j, i)
    ulo = _spawn(lib, ground, lo % cw, lo // cw, layer)
    uhi = _spawn(lib, ground, hi % cw, hi // cw, layer)
    n_up, pts_up, t_up = _route(lib, ground, ulo, *_centre(hi % cw, hi // cw))
    n_dn, pts_dn, t_dn = _route(lib, ground, uhi, *_centre(lo % cw, lo // cw))
    assert (n_up, n_dn) == (2, 2), f"a one-cell step is two points: {(n_up, n_dn)}"
    speed = lib.om_unit_effective_speed(ground, ulo)
    up_div = lib.om_tactical_get_param(ground, OMTacParam.SLOPE_UP_DIV)
    down_mult = lib.om_tactical_get_param(ground, OMTacParam.SLOPE_DOWN_MULT)
    assert t_up == pytest.approx(CELL / (speed / up_div), rel=SECONDS_REL)
    assert t_dn == pytest.approx(CELL / (speed * down_mult), rel=SECONDS_REL)
    assert t_up / t_dn == pytest.approx(up_div * down_mult, rel=SECONDS_REL)
    assert t_up > t_dn


# ================================================================ PART B: planner-b (slope links)

RAIDER_TYPE = 41                # provisional (2026-10-06): speed 150 clone
BASTION_TYPE = 42               # provisional (2026-10-06): speed 40 clone
TICK_SECONDS = 0.05             # provisional (2026-10-06): 20 Hz tactical tick (speed 150 steps 7.5 wu per tick)
CROSS_TICKS = 2                 # spec: within 2 ticks
SLOPE_600 = 600.0
NEAR_MIN, NEAR_MAX = 3, 8       # provisional (2026-10-06): cells away from a slope end for the steep-ground cases


class _Slope(ctypes.Structure):
    _fields_ = [(n, ctypes.c_double) for n in ("x0", "y0", "x1", "y1", "mx", "my", "length")] + \
               [("lower_band", ctypes.c_int32), ("upper_band", ctypes.c_int32)]


def _slopes(lib, w):
    out = []
    for i in range(lib.om_terrain_slope_count(w)):
        s = _Slope()
        assert lib.om_terrain_slope_get(w, i, ctypes.byref(s)) == 0
        out.append(s)
    return out


def _on_slope(lib, w, x, y):
    return lib.om_terrain_slope_at(w, x, y, ctypes.byref(_Slope())) >= 0


def _usable_slopes(lib, w, length=None):
    """Slopes whose bottom cell is masked on the lower layer and top cell on the upper layer."""
    cw, _ch = _grid(lib, w)
    res = []
    for s in _slopes(lib, w):
        if length is not None and s.length != length:
            continue
        lo, up = s.lower_band - 1, s.upper_band - 1
        bc, tc = _cell_of(s.x0, s.y0), _cell_of(s.x1, s.y1)
        if _mask(lib, w, lo)[bc[1] * cw + bc[0]] and _mask(lib, w, up)[tc[1] * cw + tc[0]]:
            res.append(s)
    return res


def _register_speed_types(lib, w):
    for t, spd in ((RAIDER_TYPE, 150.0), (BASTION_TYPE, 40.0)):
        rc = lib.om_roster_register_custom_unit(
            w, t, lib.om_unit_profile_category(w, VANGUARD), b"clone", lib.om_unit_profile_max_hp(w, VANGUARD),
            lib.om_unit_profile_base_damage(w, VANGUARD), lib.om_unit_profile_attack_interval(w, VANGUARD),
            lib.om_unit_profile_attack_range(w, VANGUARD), spd, lib.om_unit_profile_sensor_radius(w, VANGUARD),
            lib.om_unit_profile_layer_transition_time(w, VANGUARD), lib.om_unit_profile_aoe_radius(w, VANGUARD), 0)
        assert rc == 0, f"register {t}: {rc}"
        assert lib.om_roster_set_movement_kind(w, t, KIND_WALKING) == 0


def _spawn_at(lib, w, utype, x, y, layer):
    u = lib.om_unit_spawn(w, utype, 0, x, y, layer)
    assert u != 0, "spawn failed"
    return u


def _assert_layer_changes_only_on_slopes(lib, w, pts, lo_mask, up_mask, cw):
    """Each consecutive pair of route points that changes mask membership does so with a point on a slope cell."""
    cells = _cells_of(pts)
    for (ax, ay), (bx, by), pa, pb in zip(cells, cells[1:], pts, pts[1:]):
        ia, ib = ay * cw + ax, by * cw + bx
        in_lo_a, in_lo_b = lo_mask[ia], lo_mask[ib]
        in_up_a, in_up_b = up_mask[ia], up_mask[ib]
        if (in_lo_a and not in_up_a and in_up_b and not in_lo_b) or (in_up_a and not in_lo_a and in_lo_b and not in_up_b):
            raise AssertionError(f"jumped bands without a slope cell: {(ax, ay)} to {(bx, by)}")
    for (cx, cy) in cells:
        assert lo_mask[cy * cw + cx] or up_mask[cy * cw + cx], f"route leaves both masks at {(cx, cy)}"


def test_R_207_05_goal_on_another_band_is_reached_by_a_slope_and_nowhere_else(lib, ground):
    """R-207-05: bottom-edge cell on the lower layer to a top-edge cell on the upper layer; the route crosses a slope."""
    cw, _ch = _grid(lib, ground)
    usable = _usable_slopes(lib, ground)
    assert usable, "no slope with both ends masked on seed 11 (mask lane or generator)"
    s = usable[0]
    lo, up = s.lower_band - 1, s.upper_band - 1
    lo_mask, up_mask = _mask(lib, ground, lo), _mask(lib, ground, up)
    u = _spawn_at(lib, ground, CLONE_TYPE, s.x0, s.y0, lo)
    n, pts, sec = _route(lib, ground, u, s.x1, s.y1)
    assert n >= 2, f"slope links do not exist: om_walk_route returned {n}"
    assert pts[-1] == (s.x1, s.y1) or _cell_of(*pts[-1]) == _cell_of(s.x1, s.y1), f"ended at {pts[-1]}"
    assert any(_on_slope(lib, ground, x, y) for x, y in pts), "route never stands on a slope cell"
    _assert_layer_changes_only_on_slopes(lib, ground, pts, lo_mask, up_mask, cw)
    assert sec > 0.0


def test_R_207_05_without_the_slope_the_other_band_is_not_reachable_on_the_layer(lib, ground):
    """Control for the test above: the route's last cell is on the upper layer, which the unit did not start on."""
    cw, _ch = _grid(lib, ground)
    s = _usable_slopes(lib, ground)[0]
    lo = s.lower_band - 1
    u = _spawn_at(lib, ground, CLONE_TYPE, s.x0, s.y0, lo)
    n, pts, _sec = _route(lib, ground, u, s.x1, s.y1)
    assert n >= 2, f"om_walk_route returned {n}"
    up_mask = _mask(lib, ground, s.upper_band - 1)
    ex, ey = _cell_of(*pts[-1])
    assert up_mask[ey * cw + ex] == 1, "the route's last cell is on the upper layer (only a slope can have taken it there)"


def test_R_207_05_goal_across_steep_ground_is_reached_by_a_slope(lib, ground):
    """R-207-05 / S-200: start and goal on two bands with unwalkable ground on the straight line between them."""
    cw, ch = _grid(lib, ground)
    found = None
    for s in _usable_slopes(lib, ground):
        lo, up = s.lower_band - 1, s.upper_band - 1
        lo_mask, up_mask = _mask(lib, ground, lo), _mask(lib, ground, up)
        bc, tc = _cell_of(s.x0, s.y0), _cell_of(s.x1, s.y1)
        lo_comp = _component_cells(lo_mask, cw, ch, bc[1] * cw + bc[0])
        up_comp = _component_cells(up_mask, cw, ch, tc[1] * cw + tc[0])
        starts = [i for i in sorted(lo_comp) if NEAR_MIN <= max(abs(i % cw - bc[0]), abs(i // cw - bc[1])) <= NEAR_MAX]
        goals = [i for i in sorted(up_comp) if NEAR_MIN <= max(abs(i % cw - tc[0]), abs(i // cw - tc[1])) <= NEAR_MAX]
        for a in starts:
            for b in goals:
                ax, ay = _centre(a % cw, a // cw)
                bx, by = _centre(b % cw, b // cw)
                steps = int(max(abs(bx - ax), abs(by - ay)) / CELL)
                line = [(ax + (bx - ax) * k / steps, ay + (by - ay) * k / steps) for k in range(1, steps)]
                if steps >= 2 and any(not lib.om_terrain_walkable_at(ground, x, y) for x, y in line):
                    found = (s, a, b, lo_mask, up_mask)
                    break
            if found:
                break
        if found:
            break
    assert found, "positive control: no start and goal across steep ground near one slope on seed 11"
    s, a, b, lo_mask, up_mask = found
    u = _spawn_at(lib, ground, CLONE_TYPE, *_centre(a % cw, a // cw), s.lower_band - 1)
    gx, gy = _centre(b % cw, b // cw)
    n, pts, sec = _route(lib, ground, u, gx, gy)
    assert n >= 2, f"slope links do not exist: om_walk_route returned {n}"
    assert pts[-1] == (gx, gy), f"ended at {pts[-1]}, goal {(gx, gy)}"
    assert any(_on_slope(lib, ground, x, y) for x, y in pts), "route never stands on a slope cell"
    _assert_layer_changes_only_on_slopes(lib, ground, pts, lo_mask, up_mask, cw)
    for x, y in pts:
        cx, cy = _cell_of(x, y)
        assert lo_mask[cy * cw + cx] or up_mask[cy * cw + cx]


@pytest.mark.parametrize("speed,utype", [(150.0, RAIDER_TYPE), (40.0, BASTION_TYPE)])
@pytest.mark.parametrize("going_up", [True, False])
def test_R_004_07_600wu_slope_crossing_time(lib, ground, speed, utype, going_up):
    """R-004-07: a 600 wu slope takes 4.4 s / 16.5 s up (speed / 1.1) and 3.6 s / 13.6 s down (speed x 1.1), within 2 ticks."""
    _register_speed_types(lib, ground)
    cands = _usable_slopes(lib, ground, SLOPE_600)
    assert cands, "positive control: no 600 wu slope with both ends masked on seed 11"
    s = cands[0]
    lo, up = s.lower_band - 1, s.upper_band - 1
    if going_up:
        u = _spawn_at(lib, ground, utype, s.x0, s.y0, lo)
        gx, gy = s.x1, s.y1
    else:
        u = _spawn_at(lib, ground, utype, s.x1, s.y1, up)
        gx, gy = s.x0, s.y0
    assert lib.om_unit_effective_speed(ground, u) == pytest.approx(speed)
    n, pts, sec = _route(lib, ground, u, gx, gy)
    assert n >= 2, f"slope links do not exist: om_walk_route returned {n}"
    want = SLOPE_600 / (speed / 1.1) if going_up else SLOPE_600 / (speed * 1.1)
    assert abs(sec - want) <= CROSS_TICKS * TICK_SECONDS, f"crossing took {sec} s, R-004-07 says {want} s"
