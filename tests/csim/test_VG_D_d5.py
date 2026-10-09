"""Visible-game lane D, piece D5 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane D; pre-flight
docs/northstar/plans/preflight_2026-10-07/5-space-kit.md, "Mission wiring"). Fenced: builders never edit this file.

Proves S-246: R-246-01 (a space-era mission has the generated field: om_mission_setup in a space era calls
om_space_field_generate_nodes after om_map_set_canvas, Q-STAGE3-03 b), the layer masks are the ones routing reads, and
R-246-05 / Q-166-08 (nodes, unit spawns and structure slots are cleared to open cells; in single player no production
building stands in an enclosed section, i.e. an open region cut off from the objective). Era kind 1 drops the field.

RED on main (mission.c never calls om_space_field_generate_nodes): om_space_field_present is 0 after a space-era setup.
Tests marked CONTROL pass on main by design.

Provisional definitions (test drafts, 2026-10-08; none is given in the spec):
 - "Open cell": get_mask byte 0 (the blocked_bits sense). Nodes and structure slots must be open on ALL five layers
   ("cleared", kit CLEAR_RADIUS_WU 600); a unit must be open on its own layer (om_unit_get_layer).
 - "Enclosed section": on a layer, a 4-connected open region of 100 wu cells that does not contain the objective node's
   cell. Every unit and every owned structure on a layer must lie in the objective's region on that layer.
 - Only archetypes whose canvas is 24000 wu are asserted: om_space_field_generate_nodes refuses any other canvas and the
   spec gives no rule for 8000 / 16000 wu missions (reported as an open question; test_control_canvas_table records it).
 - Seed: the spec says only "the mission seed"; the formula is not asserted. Determinism and seed sensitivity are.
"""
import ctypes
import pathlib
from collections import deque

import pytest

from conftest import (
    OMArchetype, OMEdge, OMFeature, OMTier, OMVec2,
    set_edge, set_faction, set_owner, set_region,
)

V = ctypes.c_void_p
PLAYER_FAC, ENEMY_FAC = 0, 1
FIELD_CANVAS = 24000.0
N = 240
CELLS = N * N
LAYERS = 5
CELL = 100.0
OBJECTIVE_NODE = 0               # OM_MISSION_SPINE_NODE_OBJECTIVE (csrc/mission.c)
BATTLE_ARCHETYPES = (1, 2, 3, 4, 7, 8, 9)
CANVAS_24K = (1, 3, 8)           # archetypes whose canvas is 24000 wu on main (control below records it)
SEEDS = (3, 7, 19)               # provisional: three seeds keep the loops fast
MILITARY = 20.0


def _scene(lib, world_factory, *, era=0, archetype=3, seed=7, region=0):
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    other = 1 - region
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, region, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, other, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, region, tier=OMTier.HOME, military=MILITARY, faction_id=ENEMY_FAC)
    assert lib.om_set_era_kind(w, era) == 0
    lib.om_mission_setup(w, region, archetype, 0)
    return w


def _masks(lib, w):
    out = []
    for k in range(LAYERS):
        buf = (ctypes.c_uint8 * CELLS)()
        n = lib.om_space_field_get_mask(w, k, buf, CELLS)
        assert n == CELLS, f"layer {k}: get_mask returned {n}, expected {CELLS} (no field held?)"
        out.append(bytes(buf))
    return out


def _cell(x, y):
    return int(y // CELL) * N + int(x // CELL)


def _regions(mask):
    """4-connected labels of open (0) cells; blocked cells get -1."""
    lab = [-1] * CELLS
    nxt = 0
    for s in range(CELLS):
        if mask[s] or lab[s] != -1:
            continue
        lab[s] = nxt
        q = deque([s])
        while q:
            c = q.popleft()
            cx, cy = c % N, c // N
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if 0 <= nx < N and 0 <= ny < N:
                    n = ny * N + nx
                    if not mask[n] and lab[n] == -1:
                        lab[n] = nxt
                        q.append(n)
        nxt += 1
    return lab


def _enclosed(mask, objective_cell, points):
    """Indices of `points` (cells) that are blocked or not in the objective's region on this layer."""
    lab = _regions(mask)
    home = lab[objective_cell]
    return [p for p in points if lab[p] == -1 or lab[p] != home] if home != -1 else list(points)


def _objective(lib, w):
    for i in range(lib.om_map_get_node_count(w)):
        if lib.om_map_get_node_type(w, i) == OBJECTIVE_NODE:
            p = OMVec2()
            lib.om_map_get_node_pos(w, i, ctypes.byref(p))
            return p.x, p.y
    return None


def _nodes(lib, w):
    out = []
    for i in range(lib.om_map_get_node_count(w)):
        p = OMVec2()
        lib.om_map_get_node_pos(w, i, ctypes.byref(p))
        out.append((p.x, p.y))
    return out


def _structures(lib, w):
    out = []
    for i in range(lib.om_structure_count(w)):
        s = lib.om_structure_get_at(w, i)
        p = OMVec2()
        lib.om_structure_get_position(w, s, ctypes.byref(p))
        out.append((s, lib.om_structure_get_owner(w, s), p.x, p.y))
    return out


def _units(lib, w):
    out = []
    for i in range(lib.om_unit_count(w)):
        u = lib.om_unit_id_at(w, i)
        p = OMVec2()
        lib.om_unit_get_position(w, u, ctypes.byref(p))
        out.append((u, lib.om_unit_get_layer(w, u), p.x, p.y))
    return out


def _in_field(x, y):
    return 0.0 <= x < FIELD_CANVAS and 0.0 <= y < FIELD_CANVAS


# ---- CONTROLS (pass on main) ---------------------------------------------------------------------------------------

def test_control_enclosed_detector_finds_a_planted_pocket():
    """CONTROL: _enclosed flags a cell walled off from the objective and ignores one in the objective's region."""
    m = bytearray(CELLS)
    for i in range(N):                       # wall across column 100
        m[i * N + 100] = 1
    obj = 5 * N + 50
    assert _enclosed(bytes(m), obj, [7 * N + 60]) == []
    assert _enclosed(bytes(m), obj, [7 * N + 150]) == [7 * N + 150]
    assert _enclosed(bytes(m), obj, [3 * N + 100]) == [3 * N + 100], "a blocked cell must count as not open"


def test_control_canvas_table(lib, world_factory):
    """CONTROL: records which battle archetypes have a 24000 wu canvas on this base (the ones asserted below);
    the others have 8000 or 16000 wu and no spec rule for the field there (open question, see module doc)."""
    got = []
    for a in BATTLE_ARCHETYPES:
        w = _scene(lib, world_factory, archetype=a)
        assert lib.om_unit_count(w) > 0, f"archetype {a} spawned no battle"
        cat = lib.om_map_archetype_canvas_category(a)
        if lib.om_map_get_canvas_base_dimension(cat) == FIELD_CANVAS:
            got.append(a)
    assert tuple(got) == CANVAS_24K, f"24000 wu archetypes are {got}; update CANVAS_24K"


def test_control_ground_era_holds_no_space_field(lib, world_factory):
    """CONTROL: a ground era (kind 1) mission has no space field (era kind 1 drops it)."""
    w = _scene(lib, world_factory, era=1, archetype=3)
    assert lib.om_space_field_present(w) == 0


# ---- wiring: a space-era setup generates the field ------------------------------------------------------------------

@pytest.mark.parametrize("archetype", CANVAS_24K)
def test_space_era_setup_generates_the_field(lib, world_factory, archetype):
    """R-246-01: after om_mission_setup in a space era the world holds a field: five layers, each with open and blocked."""
    w = _scene(lib, world_factory, archetype=archetype)
    assert lib.om_space_field_present(w) == 1, "om_mission_setup did not call om_space_field_generate_nodes"
    for k, m in enumerate(_masks(lib, w)):
        assert set(m) == {0, 1}, f"layer {k}: not both open and blocked"


def test_ground_then_space_then_ground_drops_and_regenerates(lib, world_factory):
    """Era kind 1 drops the field, a later space-era setup on the same world generates it again."""
    w = _scene(lib, world_factory, archetype=3)
    assert lib.om_space_field_present(w) == 1, "space-era setup generated no field"
    assert lib.om_set_era_kind(w, 1) == 0
    lib.om_mission_setup(w, 0, 3, 0)
    assert lib.om_space_field_present(w) == 0, "ground-era setup kept the space field"
    assert lib.om_set_era_kind(w, 0) == 0
    lib.om_mission_setup(w, 0, 3, 0)
    assert lib.om_space_field_present(w) == 1


def test_mission_field_is_deterministic_and_seed_dependent(lib, world_factory):
    """Same world seed and mission: byte-identical masks; a different world seed: some layer differs."""
    a = _scene(lib, world_factory, archetype=3, seed=7)
    b = _scene(lib, world_factory, archetype=3, seed=7)
    c = _scene(lib, world_factory, archetype=3, seed=8)
    assert lib.om_space_field_present(a) == 1 and lib.om_space_field_present(c) == 1, "no field generated"
    assert _masks(lib, a) == _masks(lib, b)
    assert _masks(lib, a) != _masks(lib, c), "world seeds 7 and 8 gave the same field"


def test_mission_masks_are_what_routing_reads(lib, world_factory):
    """R-246-01 / R-001-04: the mission's reported mask equals om_map_sample_layer_accessibility (1 open) on a sample."""
    w = _scene(lib, world_factory, archetype=3)
    assert lib.om_space_field_present(w) == 1, "no field generated"
    f = lib.om_map_sample_layer_accessibility
    f.argtypes, f.restype = [V, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_int
    bad = []
    for k, m in enumerate(_masks(lib, w)):
        for cy in range(0, N, 7):
            for cx in range(0, N, 7):
                if f(w, (cx + .5) * CELL, (cy + .5) * CELL, k) != (0 if m[cy * N + cx] else 1):
                    bad.append((k, cx, cy))
    assert not bad, f"{len(bad)} cells where the mask disagrees with routing, first {bad[:3]}"


# ---- cleared anchors and R-246-05 ----------------------------------------------------------------------------------

@pytest.mark.parametrize("archetype", CANVAS_24K)
def test_nodes_are_cleared_to_open_cells_on_every_layer(lib, world_factory, archetype):
    """Pre-flight 5 flag 4 / spec: layout nodes (objective, spawns) are cleared to open cells."""
    for seed in SEEDS:
        w = _scene(lib, world_factory, archetype=archetype, seed=seed)
        assert lib.om_space_field_present(w) == 1, f"seed {seed}: no field"
        masks = _masks(lib, w)
        nodes = [n for n in _nodes(lib, w) if _in_field(*n)]
        assert nodes, "no node inside the field"
        bad = [(k, n) for n in nodes for k in range(LAYERS) if masks[k][_cell(*n)]]
        assert not bad, f"seed {seed}: node cells blocked, first {bad[:3]}"


@pytest.mark.parametrize("archetype", CANVAS_24K)
def test_unit_spawns_and_structure_slots_are_cleared(lib, world_factory, archetype):
    """Spawns and structure slots are cleared to open cells: each unit open on its own layer, each structure on all."""
    for seed in SEEDS:
        w = _scene(lib, world_factory, archetype=archetype, seed=seed)
        assert lib.om_space_field_present(w) == 1, f"seed {seed}: no field"
        masks = _masks(lib, w)
        units = [u for u in _units(lib, w) if _in_field(u[2], u[3])]
        structs = [s for s in _structures(lib, w) if _in_field(s[2], s[3])]
        assert units and structs, "scene has no unit or structure inside the field"
        bu = [u[0] for u in units if not 0 <= u[1] < LAYERS or masks[u[1]][_cell(u[2], u[3])]]
        assert not bu, f"seed {seed}: {len(bu)} of {len(units)} units spawn in blocked cells, first {bu[:3]}"
        bs = [(s[0], k) for s in structs for k in range(LAYERS) if masks[k][_cell(s[2], s[3])]]
        assert not bs, f"seed {seed}: structure slots in blocked cells, first {bs[:3]}"


@pytest.mark.parametrize("archetype", CANVAS_24K)
def test_no_production_building_in_an_enclosed_section(lib, world_factory, archetype):
    """R-246-05 / Q-166-08: in single player no owned structure stands in a section cut off from the objective,
    on any layer; likewise no unit on its own layer."""
    for seed in SEEDS:
        w = _scene(lib, world_factory, archetype=archetype, seed=seed)
        assert lib.om_space_field_present(w) == 1, f"seed {seed}: no field"
        masks = _masks(lib, w)
        obj = _objective(lib, w)
        assert obj is not None and _in_field(*obj)
        oc = _cell(*obj)
        structs = [s for s in _structures(lib, w) if s[1] >= 0 and _in_field(s[2], s[3])]
        assert structs, "no owned structure inside the field"
        for k in range(LAYERS):
            bad = _enclosed(masks[k], oc, [_cell(s[2], s[3]) for s in structs])
            assert not bad, f"seed {seed} layer {k}: structure cells {bad[:3]} in an enclosed section"
        for u in _units(lib, w):
            if _in_field(u[2], u[3]) and 0 <= u[1] < LAYERS:
                assert not _enclosed(masks[u[1]], oc, [_cell(u[2], u[3])]), f"seed {seed}: unit {u[0]} enclosed"
