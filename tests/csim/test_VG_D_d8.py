"""Visible-game lane D, piece D8: spawn placement (Westley 2026-10-09: "Army should spawn right near the home base. Right
near the player's first economy area."). Fenced: builders never edit this file.

Proves E-17 S-246 R-246-07: in a space-era mission each faction's army spawns in a cleared pocket at its own anchor, the
objective sits in its own pocket, and the pockets are carved reachable to each other.

Numbers (none invented): CLEAR_RADIUS_WU = 600 (docs/northstar/plans/2026-10-02-space-kit-mode-spec.md, constants line and
P2.3 "Clearing"); cell 100 wu, 240x240 (D5). (b)'s bound is derived: anchor distance minus 2 x CLEAR_RADIUS_WU.

Anchors: the sim has no getter for them. They are the mission's pre-snap faction anchors in csrc/mission.c
om_mission_instantiate_map: player faction (px, py) = (canvas/2, edge), enemy (ex, ey) = (canvas/2, canvas - edge),
edge = OM_UNIT_COLLISION_RADIUS = 15, canvas 24000 (the 24000 wu archetype 3). Player faction is id 0 in this scene.
Unit 'spawn cell' = the 100 wu cell holding its position at setup; 'same cell' = same position (x, y) on the same layer
(the 3x3 slots of a cell are 9 distinct positions; a repeat is the index wrap `% n_order` in om_mission_spawn_force).

RED on origin/push/vg-d7-pipe: (a) (b) (c). (d) (e) are reported by the run. Controls pass by design.
"""
import ctypes
from collections import Counter, deque

import pytest

import test_VG_D_d5 as d5

N, CELLS, CELL = d5.N, d5.CELLS, d5.CELL
CLEAR_RADIUS_WU = 600.0
CANVAS, EDGE = 24000.0, 15.0
ANCHOR = {0: (CANVAS / 2.0, EDGE), 1: (CANVAS / 2.0, CANVAS - EDGE)}
SEEDS = (1, 8, 19)  # 1 and 8 from the brief; 19 is the third seed of D5


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _reach(mask, src, dst):
    """4-neighbour BFS over open (0) cells; blocked src or dst is unreachable."""
    if mask[src] or mask[dst]:
        return False
    seen = {src}
    q = deque([src])
    while q:
        c = q.popleft()
        if c == dst:
            return True
        cx, cy = c % N, c // N
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= nx < N and 0 <= ny < N:
                n = ny * N + nx
                if not mask[n] and n not in seen:
                    seen.add(n)
                    q.append(n)
    return False


def _setup(lib, world_factory, seed):
    w = d5._scene(lib, world_factory, archetype=3, seed=seed)
    assert lib.om_space_field_present(w) == 1
    units = {0: [], 1: []}
    for u, layer, x, y in d5._units(lib, w):
        f = lib.om_unit_get_faction(w, u)
        if f in units:
            units[f].append((u, layer, x, y))
    assert units[0] and units[1]
    return w, units


def _centroid(us):
    return (sum(u[2] for u in us) / len(us), sum(u[3] for u in us) / len(us))


# ---- controls ------------------------------------------------------------------------------------------------------

def test_control_bfs_wall_and_blocked_target():
    """CONTROL: BFS finds a path in an open sheet, fails across a full wall, and fails into a blocked cell."""
    m = bytearray(CELLS)
    assert _reach(bytes(m), 5 * N + 5, 200 * N + 200)
    for i in range(N):
        m[i * N + 100] = 1
    assert not _reach(bytes(m), 5 * N + 5, 5 * N + 200)
    assert not _reach(bytes(m), 5 * N + 5, 7 * N + 100)


@pytest.mark.parametrize("seed", SEEDS)
def test_control_bfs_fails_into_a_blocked_plate_cell(lib, world_factory, seed):
    """CONTROL (positive control for (e)): on the real field the BFS from an open spawn cell to a cell inside a blocked
    plate is False. Passes by design."""
    w, units = _setup(lib, world_factory, seed)
    u = units[0][0]
    mask = d5._masks(lib, w)[u[1]]
    src = d5._cell(u[2], u[3])
    blocked = mask.index(1)
    assert not _reach(mask, src, blocked)


# ---- D8 -------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_d8_a_spawn_centroid_within_clear_radius_of_own_anchor(lib, world_factory, seed):
    """R-246-07 (a): each faction's spawn centroid is within CLEAR_RADIUS_WU (600) of its anchor.
    RED now: both armies sit in one pocket at the objective."""
    w, units = _setup(lib, world_factory, seed)
    out = []
    for f in (0, 1):
        c = _centroid(units[f])
        out.append(f"fac{f} centroid=({c[0]:.0f},{c[1]:.0f}) anchor={ANCHOR[f]} d={_dist(c, ANCHOR[f]):.0f}")
    print(f"D8 a seed {seed}: " + "; ".join(out))
    for f in (0, 1):
        assert _dist(_centroid(units[f]), ANCHOR[f]) <= CLEAR_RADIUS_WU, "; ".join(out)


@pytest.mark.parametrize("seed", SEEDS)
def test_d8_b_armies_are_an_approach_march_apart(lib, world_factory, seed):
    """R-246-07 (b): centroid distance >= anchor distance - 2 x CLEAR_RADIUS_WU.
    RED now: about 70 to 1,100 wu apart."""
    w, units = _setup(lib, world_factory, seed)
    d = _dist(_centroid(units[0]), _centroid(units[1]))
    need = _dist(ANCHOR[0], ANCHOR[1]) - 2 * CLEAR_RADIUS_WU
    print(f"D8 b seed {seed}: centroid distance {d:.0f}, need >= {need:.0f}")
    assert d >= need, f"centroids {d:.0f} wu apart, need >= {need:.0f}"


@pytest.mark.parametrize("seed", SEEDS)
def test_d8_c_no_two_units_share_a_spawn_position_and_all_are_open(lib, world_factory, seed):
    """R-246-07 (c): no two units spawn at the same position on a layer (the slot wrap), and every spawn cell is open in
    its unit's layer mask. RED now on the wrap (unit 321 on unit 20)."""
    w, units = _setup(lib, world_factory, seed)
    masks = d5._masks(lib, w)
    allu = units[0] + units[1]
    pos = Counter((round(x, 3), round(y, 3), layer) for _, layer, x, y in allu)
    dup = {k: n for k, n in pos.items() if n > 1}
    shut = [u[0] for u in allu if masks[u[1]][d5._cell(u[2], u[3])]]
    print(f"D8 c seed {seed}: {len(allu)} units, {len(dup)} shared positions, {len(shut)} on blocked cells")
    assert not dup, f"{len(dup)} positions hold more than one unit, e.g. {next(iter(dup))}"
    assert not shut, f"{len(shut)} units on blocked cells, e.g. unit {shut[0]}"


@pytest.mark.parametrize("seed", SEEDS)
def test_d8_d_objective_is_open_and_in_its_own_pocket(lib, world_factory, seed):
    """R-246-07 (d): the objective cell is open on all five layers and farther than CLEAR_RADIUS_WU from both anchors
    and both spawn centroids (not inside either spawn pocket). Reported."""
    w, units = _setup(lib, world_factory, seed)
    obj = d5._objective(lib, w)
    masks = d5._masks(lib, w)
    shut = [k for k in range(5) if masks[k][d5._cell(*obj)]]
    near = [(f, round(_dist(obj, p))) for f in (0, 1) for p in (ANCHOR[f], _centroid(units[f])) if _dist(obj, p) <= CLEAR_RADIUS_WU]
    print(f"D8 d seed {seed}: objective {obj}, blocked layers {shut}, within 600 of {near}")
    assert not shut, f"objective cell blocked on layers {shut}"
    assert not near, f"objective inside a spawn pocket: {near}"


@pytest.mark.parametrize("seed", SEEDS)
def test_d8_e_each_spawn_reaches_the_objective_on_the_layer_mask(lib, world_factory, seed):
    """R-246-07 (e): a 4-neighbour path over open cells joins each faction's spawn centroid cell to the objective cell
    on the layer most of that faction's units stand on. Reported."""
    w, units = _setup(lib, world_factory, seed)
    masks = d5._masks(lib, w)
    obj = d5._cell(*d5._objective(lib, w))
    res = {}
    for f in (0, 1):
        layer = Counter(u[1] for u in units[f]).most_common(1)[0][0]
        res[f] = _reach(masks[layer], d5._cell(*_centroid(units[f])), obj)
    print(f"D8 e seed {seed}: reachable {res}")
    assert all(res.values()), f"no path to the objective: {res}"
