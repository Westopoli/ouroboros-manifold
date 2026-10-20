"""E-01 terrain stage 3, piece 3a (spec 2026-10-06-terrain-stage3-spec.md rev 3, piece "3a", csrc/mission.c).

Proves: in a ground era (om_set_era_kind 1, walking kinds) om_mission_setup generates terrain (seed
world_seed ^ (region * 0x9E3779B1) ^ archetype, canvas = the archetype's), snaps the objective node and structure
slots to walkable ground, spawns every unit the space era spawns, all on walkable cells, with the objective
reachable from both sides by om_walk_route; two campaign missions differ in terrain; a space mission after a
ground one leaves no terrain; space-era setup is unchanged (golden checksums captured on the contract base).
The last section pins spec-fixed text for the other pieces (3b, 3d, 3e, 3f) that a Python file can reach by reading
source; those are source-text checks, marked as such.

RED reasons on origin/push/t3-contract (mission.c never calls om_terrain_generate or om_terrain_clear):
"In om_mission_instantiate_map ... ground era: om_terrain_generate(w, seed, canvas, canvas) ... space era:
om_terrain_clear" -> om_terrain_present is 0 after a ground setup, the walk mask is empty, the seeds are absent.
Tests marked CONTROL pass on the base by design (positive controls and the byte-identical space guard).

Not testable here (reported, not guessed): "-1 fails the start with a named error" and "a force that cannot place
every unit fails the mission start": om_mission_setup is void and no C-visible failure signal is specified.
Archetypes 0, 5 and 6 spawn no battle on this base (control test records it); the "every archetype" loops cover
the seven that do. Provisional numbers (2026-10-06) are test drafts.
"""
import ctypes
import pathlib
import subprocess

import pytest

from conftest import (
    OMArchetype, OMEdge, OMFeature, OMTier, OMVec2, load_lib,
    set_edge, set_faction, set_owner, set_region,
)
from test_VG_E_e7 import _bind as e7_bind, oracle_units, owners_of, roster_of  # TD-VG-E-34: the E7 starting-force oracle

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
V = ctypes.c_void_p
P = ctypes.POINTER
PLAYER_FAC, ENEMY_FAC = 0, 1
BATTLE_ARCHETYPES = (1, 2, 3, 4, 7, 8, 9)   # spawn units on this base (control below)
NO_BATTLE_ARCHETYPES = (0, 5, 6)
MILITARY = 20.0                  # provisional (2026-10-06): small force keeps 140 setups fast
SEEDS = tuple(range(1, 21))      # "20 seeds" (spec)
N_TYPES = 6
MOVE_WALKING = 1
CELL = 100.0
SEED_MIX = 0x9E3779B1
OBJECTIVE_NODE = 0               # OM_MISSION_SPINE_NODE_OBJECTIVE (csrc/mission.c:239)
ROUTE_CAP = 16384                # points; provisional (2026-10-06)
REACH_TOL = 1.5 * CELL           # provisional (2026-10-06): route end within 1.5 cells of the goal
SLOTS = 64


def _decl(lib):
    lib.om_walk_route.argtypes = [V, ctypes.c_uint32, ctypes.c_double, ctypes.c_double,
                                  P(ctypes.c_double), ctypes.c_uint32, P(ctypes.c_double)]
    lib.om_walk_route.restype = ctypes.c_int
    lib.om_map_get_node_count.argtypes = [V]; lib.om_map_get_node_count.restype = ctypes.c_uint32
    lib.om_map_get_node_pos.argtypes = [V, ctypes.c_uint32, P(OMVec2)]; lib.om_map_get_node_pos.restype = None
    lib.om_map_get_node_type.argtypes = [V, ctypes.c_uint32]; lib.om_map_get_node_type.restype = ctypes.c_int
    lib.om_map_archetype_canvas_category.argtypes = [ctypes.c_uint32]; lib.om_map_archetype_canvas_category.restype = ctypes.c_int
    lib.om_map_get_canvas_base_dimension.argtypes = [ctypes.c_int]; lib.om_map_get_canvas_base_dimension.restype = ctypes.c_double
    lib.om_terrain_clear.argtypes = [V]; lib.om_terrain_clear.restype = None
    lib.om_world_get_state_checksum.argtypes = [V]; lib.om_world_get_state_checksum.restype = ctypes.c_uint64


def _scene(lib, world_factory, *, ground, archetype, seed=7, region=0):
    """Two regions, `region` is the enemy-held contested one, the other the player's; mission set up on `region`."""
    _decl(lib)
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    other = 1 - region
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, region, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, other, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, region, tier=OMTier.HOME, military=MILITARY, faction_id=ENEMY_FAC)
    if ground:
        assert lib.om_set_era_kind(w, 1) == 0
        for t in range(N_TYPES):
            assert lib.om_roster_set_movement_kind(w, t, MOVE_WALKING) == 0
    lib.om_mission_setup(w, region, archetype, 0)
    return w


def _canvas(lib, archetype):
    return lib.om_map_get_canvas_base_dimension(lib.om_map_archetype_canvas_category(archetype))


def _units(lib, w):
    return [lib.om_unit_id_at(w, i) for i in range(lib.om_unit_count(w))]


def _pos(lib, w, u):
    p = OMVec2()
    lib.om_unit_get_position(w, u, ctypes.byref(p))
    return p.x, p.y


def _bands(lib, w):
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    n = lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    buf = (ctypes.c_uint8 * max(n, 1))()
    assert lib.om_terrain_dump_bands(w, buf, n) == n
    return (cw.value, ch.value, bytes(buf[:n]))


def _objective_node(lib, w):
    for i in range(lib.om_map_get_node_count(w)):
        if lib.om_map_get_node_type(w, i) == OBJECTIVE_NODE:
            p = OMVec2()
            lib.om_map_get_node_pos(w, i, ctypes.byref(p))
            return p.x, p.y
    return None


def _route_end(lib, w, unit, gx, gy):
    buf = (ctypes.c_double * (2 * ROUTE_CAP))()
    sec = ctypes.c_double()
    n = lib.om_walk_route(w, unit, gx, gy, buf, ROUTE_CAP, ctypes.byref(sec))
    if n <= 0 or n > ROUTE_CAP:
        return n, None
    return n, (buf[2 * (n - 1)], buf[2 * (n - 1) + 1])


# ---- CONTROL: the scene spawns a battle where the loops below expect one --------------------------------------

def test_control_archetypes_with_and_without_a_battle(lib, world_factory):
    """CONTROL (passes on base): the scene and unit reader see units for the seven battle archetypes in the space era
    and none for 0, 5, 6; proves the counts the ground tests compare against are real."""
    for a in BATTLE_ARCHETYPES:
        w = _scene(lib, world_factory, ground=False, archetype=a)
        assert lib.om_unit_count(w) > 0, f"archetype {a} spawned nothing in the space era"
    for a in NO_BATTLE_ARCHETYPES:
        w = _scene(lib, world_factory, ground=False, archetype=a)
        assert lib.om_unit_count(w) == 0, f"archetype {a} now spawns a battle: widen BATTLE_ARCHETYPES"


# ---- generate with the spec's seed and canvas -----------------------------------------------------------------

@pytest.mark.parametrize("archetype", BATTLE_ARCHETYPES)
def test_ground_era_generates_terrain_on_the_archetype_canvas(lib, world_factory, archetype):
    """Spec 3a: ground era generates (canvas = the archetype's); cells = canvas / 100 each way."""
    w = _scene(lib, world_factory, ground=True, archetype=archetype)
    assert lib.om_terrain_present(w) == 1, "ground-era mission_setup did not call om_terrain_generate"
    cw, ch, _ = _bands(lib, w)
    cells = int(_canvas(lib, archetype) / CELL)
    assert (cw, ch) == (cells, cells)


@pytest.mark.parametrize("region", (0, 1))
def test_terrain_seed_is_world_seed_xor_region_mix_xor_archetype(lib, world_factory, region):
    """Spec seed table: seed = world_seed ^ (region * 0x9E3779B1) ^ archetype (regions 0 and 1 keep the product
    width-independent). The mission's terrain equals a standalone om_terrain_generate with that seed."""
    world_seed, a = 7, 3
    w = _scene(lib, world_factory, ground=True, archetype=a, seed=world_seed, region=region)
    assert lib.om_terrain_present(w) == 1
    ref = world_factory(n_regions=1, seed=world_seed)
    c = _canvas(lib, a)
    assert lib.om_map_set_canvas(ref, c, c) == 0
    assert lib.om_terrain_generate(ref, world_seed ^ (region * SEED_MIX) ^ a, c, c) == 0
    assert _bands(lib, w) == _bands(lib, ref)


def test_two_campaign_missions_differ_in_terrain(lib, world_factory):
    """Spec 3a: two missions of one campaign (same world seed and archetype, regions 0 and 1) differ in terrain."""
    a = _scene(lib, world_factory, ground=True, archetype=3, region=0)
    b = _scene(lib, world_factory, ground=True, archetype=3, region=1)
    assert lib.om_terrain_present(a) == 1 and lib.om_terrain_present(b) == 1
    assert _bands(lib, a) != _bands(lib, b)


# ---- clear in the space era -----------------------------------------------------------------------------------

def test_ground_then_space_mission_on_one_world_leaves_no_terrain(lib, world_factory):
    """Spec 3a: space era calls om_terrain_clear. A ground mission then a space one on the same world: no terrain.
    The first assert is the control (it needs generate, so it is red on base too, for the same reason)."""
    w = _scene(lib, world_factory, ground=True, archetype=3)
    assert lib.om_terrain_present(w) == 1, "ground setup left no terrain to clear"
    assert lib.om_set_era_kind(w, 0) == 0
    lib.om_mission_setup(w, 0, 3, 0)
    assert lib.om_terrain_present(w) == 0, "space-era setup did not call om_terrain_clear"


def test_control_space_mission_has_no_terrain(lib, world_factory):
    """CONTROL (passes on base): a space-era mission has no terrain."""
    w = _scene(lib, world_factory, ground=False, archetype=3)
    assert lib.om_terrain_present(w) == 0


# ---- spawns, anchors, reachability, 20 seeds x every battle archetype -----------------------------------------

@pytest.mark.parametrize("archetype", BATTLE_ARCHETYPES)
def test_every_unit_spawns_on_walkable_ground_and_objective_is_reachable(lib, world_factory, archetype):
    """Spec 3a: every archetype at 20 seeds, ground era: every unit spawns (same count as the space era), each on
    a walkable cell, the (snapped) objective node on a walkable cell and reachable from a player and an enemy unit
    by om_walk_route.

    TD-VG-E-34 (pin move, start-count pins move with the starting-force cut, E7, Architect 2026-10-19): the player spawns
    start_units of the composed force F in every era, with start = F * frac(share), share = p / (p + e) read from the era's own
    structure placement (the ground era caps the strongpoints at the slope count, R-218-01, so its p and e differ from the space
    era's). The expected count is the space era's enemy units (unchanged by E7) plus the ground world's start_units: it was the
    space era's total, which held while both eras spawned all of F. The premise (F, p, e, share, start_units) is in the message."""
    # See also: test_VG_E_e7.py `lib` fixture (TD-VG-E-34): e7_bind retypes om_terrain_slope_at, so it binds a private handle,
    # never the session lib other modules' tests share.
    lib = load_lib()
    e7_bind(lib)
    for seed in SEEDS:
        space = _scene(lib, world_factory, ground=False, archetype=archetype, seed=seed)
        space_enemy = sum(1 for u in _units(lib, space) if lib.om_unit_get_faction(space, u) == ENEMY_FAC)
        w = _scene(lib, world_factory, ground=True, archetype=archetype, seed=seed)
        assert lib.om_terrain_present(w) == 1, f"seed {seed}: no terrain"
        units = _units(lib, w)
        owners = owners_of(lib, w)
        F, p, e = sum(roster_of(lib, w)), owners.count(PLAYER_FAC), owners.count(ENEMY_FAC)
        start_units, _cap = oracle_units(F, p, e)
        expect = space_enemy + start_units
        print("PREMISE", f"archetype {archetype} seed {seed} F {F} p {p} e {e} share {p / (p + e) if p + e else None} start_units {start_units} enemy {space_enemy} expect {expect}")
        assert len(units) == expect, (f"seed {seed}: {len(units)} units spawned, E7 wants the enemy's {space_enemy} + start_units "
                                      f"{start_units} = {expect} (F {F}, p {p}, e {e}, share {p / (p + e) if p + e else None})")
        for u in units:
            x, y = _pos(lib, w, u)
            assert lib.om_terrain_walkable_at(w, x, y) == 1, f"seed {seed}: unit {u} spawned unwalkable at {x},{y}"
        obj = _objective_node(lib, w)
        assert obj is not None, f"seed {seed}: no objective node"
        assert lib.om_terrain_walkable_at(w, *obj) == 1, f"seed {seed}: objective node on unwalkable ground {obj}"
        for fac in (lib.om_player_faction(w), lib.om_mission_get_enemy_faction(w)):
            u = next(u for u in units if lib.om_unit_get_faction(w, u) == fac)
            n, end = _route_end(lib, w, u, *obj)
            assert end is not None, f"seed {seed}: faction {fac} route returned {n}"
            assert abs(end[0] - obj[0]) <= REACH_TOL and abs(end[1] - obj[1]) <= REACH_TOL, \
                f"seed {seed}: faction {fac} route ends at {end}, objective {obj}"


@pytest.mark.parametrize("archetype", BATTLE_ARCHETYPES)
def test_structure_slots_are_on_walkable_ground(lib, world_factory, archetype):
    """Spec 3a: each structure slot passes through om_terrain_nearest_walkable. Slots are scanned like the B9-N
    test (a slot with position != (0,0) is placed)."""
    w = _scene(lib, world_factory, ground=True, archetype=archetype)
    assert lib.om_terrain_present(w) == 1
    placed = 0
    for slot in range(SLOTS):
        p = OMVec2()
        lib.om_structure_get_position(w, slot, ctypes.byref(p))
        if p.x != 0.0 or p.y != 0.0:
            placed += 1
            assert lib.om_terrain_walkable_at(w, p.x, p.y) == 1, f"slot {slot} at {p.x},{p.y} is unwalkable"
    if lib.om_terrain_slope_count(w) > 0:  # TD-VG-E-5: R-218-01, no slopes means no strongpoints
        assert placed > 0, "no structure placed; the scan proves nothing"
    else:
        assert placed == 0


def test_flying_units_still_spawn_on_unwalkable_ground(lib, world_factory):
    """Spec 3a (grid steps over cells 'not walkable for the force's kinds'): with all kinds flying the spawn grid
    is not restricted. Ground era, no walking kinds: the unit count equals the space era's."""
    _decl(lib)
    a = 3
    space = _scene(lib, world_factory, ground=False, archetype=a)
    w = world_factory(n_regions=2, seed=7)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=MILITARY, faction_id=ENEMY_FAC)
    assert lib.om_set_era_kind(w, 1) == 0
    lib.om_mission_setup(w, 0, a, 0)
    assert lib.om_terrain_present(w) == 1, "ground era did not generate terrain"
    assert lib.om_unit_count(w) == lib.om_unit_count(space)


# ---- space era byte-identical to the contract base (and so to main) -------------------------------------------

# Captured 2026-10-06 on origin/push/t3-contract (space era, archetype 3, military 20, world seed s): sha256 of
# every unit (type, faction, x, y) and every placed structure slot after om_mission_setup. Regression guard, not a
# red test. (om_world_get_state_checksum is the same for all three seeds, so it cannot guard this.)
# TD-VG-D-2 (rule-changed, R-246-*): D5 puts the space field into every space mission (so the setup hash depends on the seed); D8 moves spawns to the faction anchors (final values).
SPACE_GOLDEN = {
    1: "b8f3a702d799bf14266a79f79d6c6399bdaa5d0966fe2544f4dd44f7f340b297",
    2: "6a87d8b5db5390c2c6b567ec6328a8c9bf85be60ffebbff07db77a9ba2aae6c5",
    3: "48b79f9e749c07d862401dbbe0480704a50c94f9faa071c0d06c57a02ff21305",
}


def _state_hash(lib, w):
    import hashlib
    rows = []
    for u in _units(lib, w):
        x, y = _pos(lib, w, u)
        rows.append((u, lib.om_unit_get_unit_type(w, u), lib.om_unit_get_faction(w, u), x, y))
    for slot in range(SLOTS):
        p = OMVec2()
        lib.om_structure_get_position(w, slot, ctypes.byref(p))
        rows.append(("s", slot, lib.om_structure_get_owner(w, slot), p.x, p.y))
    return hashlib.sha256(repr(rows).encode()).hexdigest()


@pytest.mark.parametrize("seed", (1, 2, 3))
def test_control_space_era_setup_unchanged(lib, world_factory, seed):
    """CONTROL (passes on base): the space-era mission state after setup is bit-for-bit what main produces."""
    w = _scene(lib, world_factory, ground=False, archetype=3, seed=seed)
    assert _state_hash(lib, w) == SPACE_GOLDEN[seed]


# ---- source-text checks for the other pieces (spec "audit" and "pre-flight" tables) ---------------------------

def _read(rel):
    return (REPO_ROOT / rel).read_text()


def _git_show(ref, rel):
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def test_source_pipe_parses_flat_movement_kinds_and_names_the_generate_error():
    """3b (source-text): handle_mission_start parses flat movement_kinds [t, k, t, k, ...] with get_int_array
    and answers write_error("mission_start", "terrain generate failed"). Red until 3b lands."""
    src = _read("csrc/pipe/om_pipe.c")
    start = src.index("handle_mission_start")
    body = src[src.index("{", src.index("handle_mission_start(", start)):]
    assert 'get_int_array(' in body and '"movement_kinds"' in body, "mission_start does not read movement_kinds"
    assert '"era_kind"' in body
    assert '"terrain generate failed"' in src, 'named error for generate failure (-1) missing'


def test_source_era_config_has_type_ids_and_var_active_era():
    """3e/3f (source-text): TYPE_IDS name table (raider 0, interceptor 1, vanguard 2, warden 3, bombard 4,
    bastion 5; csrc/unit.c:69-76), ACTIVE_ERA_ID a var, the --era <id> space form read. Red until 3e/3f land."""
    src = _read("autoload/era_config.gd")
    assert "const TYPE_IDS" in src
    for name, tid in (("raider", 0), ("interceptor", 1), ("vanguard", 2), ("warden", 3), ("bombard", 4), ("bastion", 5)):
        assert f'"{name}": {tid}' in src or f'"{name}":{tid}' in src, f"TYPE_IDS missing {name} {tid}"
    assert "var ACTIVE_ERA_ID" in src and "const ACTIVE_ERA_ID" not in src
    assert '"--era"' in src, "--era <id> space form (c_bridge.gd --seed <n> pattern) not read"


def test_source_ui_data_bus_keeps_era_id_setting():
    """3e (source-text): UIDataBus rebuilds settings from fixed key lists; [game] era_id must be in load and save.
    Red until 3e lands."""
    src = _read("autoload/ui_data_bus.gd")
    assert src.count('"era_id":') >= 3, 'the "era_id" key must be in both branches of _load_settings and in save_settings'
    assert '"game", "era_id"' in src, "section [game] era_id not read/written"


def test_control_proto_walkers_ramp_constants_exist():
    """CONTROL (passes where origin/push/proto-walkers is fetched): the ramp the spec fixes for 3d is on the branch."""
    src = _git_show("origin/push/proto-walkers", "scenes/mockups/walkers/walkers_mockup.gd")
    assert src is not None, "origin/push/proto-walkers not fetched"
    assert "Color(0.40, 0.72, 0.42), Color(0.72, 0.80, 0.38), Color(0.90, 0.68, 0.30), Color(0.72, 0.48, 0.30), Color(0.92, 0.90, 0.88)" in src
    assert "STEEP_COLOUR := Color(0.85, 0.10, 0.85)" in src


def test_source_terrain_layer_uses_the_mockup_ramp():
    """3d (source-text): scenes/tactical_c/terrain_layer.gd carries BAND_COLOURS (0.40,0.72,0.42) (0.72,0.80,0.38)
    (0.90,0.68,0.30) (0.72,0.48,0.30) (0.92,0.90,0.88), STEEP_COLOUR (0.85,0.10,0.85) lerped 0.5, no WATER_COLOUR
    use. Red until 3d lands (file missing)."""
    src = _read("scenes/tactical_c/terrain_layer.gd")
    for c in ("Color(0.40, 0.72, 0.42)", "Color(0.72, 0.80, 0.38)", "Color(0.90, 0.68, 0.30)",
              "Color(0.72, 0.48, 0.30)", "Color(0.92, 0.90, 0.88)", "Color(0.85, 0.10, 0.85)"):
        assert c in src, f"{c} missing"
    assert "lerp(" in src and "0.5" in src
