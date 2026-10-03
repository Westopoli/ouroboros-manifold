"""Drive the C library (libouroboros.so) over a parity scene, through its public API only.

Calls used: om_world_new/free, om_roster_register_custom_unit, om_tactical_disable_abilities,
om_unit_spawn, om_map_set_obstacle_density, om_command_move, om_command_group_move,
om_command_attack_move, om_tactical_step, om_unit_get_pos, om_unit_get_target, om_unit_get_facing,
om_unit_alive. Every value a Trace needs has a getter today; no call is missing.

Deliberate differences from the Python that the harness itself introduces (not C behaviour):
  * C unit id = Python uid + 1 (the registry is 1-based); targets are translated back.
  * The Python map clamps positions to its 4,000 x 4,000 (or 2,000 x 1,000) canvas, so the C is given
    the same canvas through om_map_set_canvas (A159).
  * The wall map is given to the C as density cells through om_map_set_obstacle_density, with the
    same cells the Python derives from its gradient sources (rows 4-5, cols 3-18, density 1.0).
  * abilities are switched off with om_tactical_disable_abilities (the Python's abilities are
    manual only, so none ever fire in these scenes; the C auto-triggers some).
"""
import ctypes
import subprocess
from pathlib import Path

from .parity_compare import Trace, TWO_PI
from .parity_scenes import CUSTOM_TYPES

REPO = Path(__file__).resolve().parents[3]
LIB_PATH = REPO / "libouroboros.so"
_BUILTIN = {"Raider": 0, "Interceptor": 1, "Vanguard": 2, "Warden": 3, "Bombard": 4, "Bastion": 5}
# The wall of simulation/test_obstacle_navigation.py: cell rows 4 and 5, cols 3..18, one cell each.
_WALL_CELLS = [(c, r) for r in (4, 5) for c in range(3, 19)]

_lib = None


def build():
    """Build libouroboros.so the way tests/csim/conftest.py does (make is a no-op when current)."""
    res = subprocess.run(["make", "-s", "libouroboros.so"], cwd=str(REPO), capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("make libouroboros.so failed:\n" + (res.stderr or res.stdout)[-3000:])


def lib(rebuild=True):
    global _lib
    if _lib is None:
        if rebuild or not LIB_PATH.exists():
            build()
        c = ctypes
        h = c.CDLL(str(LIB_PATH))
        V, u32, u64, d, i = c.c_void_p, c.c_uint32, c.c_uint64, c.c_double, c.c_int
        pd, pu = c.POINTER(d), c.POINTER(u32)
        sigs = {
            "om_world_new": ([u32, u64], V), "om_world_free": ([V], None),
            "om_roster_register_custom_unit": ([V, u32, i, c.c_char_p, d, d, d, d, d, d, d, d, i], i),
            "om_tactical_disable_abilities": ([V], None),
            "om_tactical_set_param": ([V, i, d], i),
            "om_map_set_canvas": ([V, d, d], i),
            "om_unit_spawn": ([V, i, c.c_int32, d, d, u32], u32),
            "om_map_set_obstacle_density": ([V, u32, u32, u32, d], None),
            "om_command_move": ([V, pu, u32, d, d], i),
            "om_command_group_move": ([V, pu, u32, d, d], u32),
            "om_command_attack_move": ([V, pu, u32, d, d], i),
            "om_tactical_step": ([V], u64),
            "om_unit_get_pos": ([V, u32, pd, pd], i),
            "om_unit_get_target": ([V, u32], u32),
            "om_unit_get_facing": ([V, u32], d),
            "om_unit_alive": ([V, u32], i),
            "om_unit_get_hp": ([V, u32], d),
        }
        for name, (argtypes, restype) in sigs.items():
            fn = getattr(h, name)
            fn.argtypes, fn.restype = argtypes, restype
        _lib = h
    return _lib


def _type_id(type_name):
    return CUSTOM_TYPES[type_name]["type_id"] if type_name in CUSTOM_TYPES else _BUILTIN[type_name]


def _order(h, w, verb, uids, x, y, off=0):
    ids = [u + 1 + off for u in uids]
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    if verb == "move":
        # The game's own mapping (csrc/pipe/om_pipe.c): one unit is a plain move, several are the
        # group order with formation slots.
        if len(ids) == 1:
            h.om_command_move(w, arr, 1, x, y)
        else:
            h.om_command_group_move(w, arr, len(ids), x, y)
    elif verb == "attack_move":
        h.om_command_attack_move(w, arr, len(ids), x, y)
    else:
        raise ValueError("unknown verb %r" % verb)


def _frame(h, w, n, off=0):
    rows = []
    x, y = ctypes.c_double(), ctypes.c_double()
    for uid in range(n):
        cid = uid + 1 + off
        alive = bool(h.om_unit_alive(w, cid))
        h.om_unit_get_pos(w, cid, ctypes.byref(x), ctypes.byref(y))
        raw = int(h.om_unit_get_target(w, cid))                # 0 = none
        tgt = raw - 1 - off if raw else -1
        if not alive or (tgt >= 0 and not h.om_unit_alive(w, tgt + 1 + off)):
            tgt = -1
        rows.append((alive, x.value, y.value, tgt, h.om_unit_get_facing(w, cid) % TWO_PI))
    return rows


def run_scene(scene, seed=1, hook=None, id_offset=0):
    """Run a scene through om_tactical_step; return a Trace. hook(h, w, tick) is called before each
    step, after the scene's own orders (used by the harness test that proves the C driver is live).

    id_offset is a DIAGNOSTIC for attributing a divergence, never used by the red tests: it spawns
    that many inert far-corner units of an unrelated faction first, so C id = uid + 1 + id_offset;
    id_offset = 3 makes the C's id % 4 targeting cohort equal the Python's uid % 4."""
    h = lib(rebuild=False)
    w = ctypes.c_void_p(h.om_world_new(1, seed))
    assert w.value, "om_world_new returned NULL"
    try:
        for name, spec in CUSTOM_TYPES.items():
            rc = h.om_roster_register_custom_unit(
                w, spec["type_id"], spec["category"], name.encode(), spec["hp"], spec["base_damage"],
                spec["attack_interval"], spec["attack_range"], spec["speed"], spec["sensor_radius"],
                spec["layer_transition_time"], spec["aoe_radius"], 0)
            assert rc == 0, "register %s: %d" % (name, rc)
        h.om_tactical_disable_abilities(w)
        # A159: parity holds only with both of these. The Python runs the attack-move leash BEFORE
        # damage (OM_TP_LEASH_BEFORE_DAMAGE = 2) and always clamps positions to its map, so the C is
        # given the same order of steps and the same canvas as the Python scene assumes.
        h.om_tactical_set_param(w, 2, 1.0)
        canvas = (4000.0, 4000.0) if scene.map == "open" else (2000.0, 1000.0)
        assert h.om_map_set_canvas(w, canvas[0], canvas[1]) == 0
        if scene.map == "wall":
            for cx, cy in _WALL_CELLS:
                h.om_map_set_obstacle_density(w, cx, cy, 0, 1.0)
        corner = (3990.0, 3990.0) if scene.map == "open" else (1990.0, 990.0)
        for _ in range(id_offset):
            assert h.om_unit_spawn(w, _BUILTIN["Raider"], 9, corner[0], corner[1], 0) != 0
        for type_name, faction, x, y in scene.units:
            cid = h.om_unit_spawn(w, _type_id(type_name), faction, x, y, 0)
            assert cid != 0, "spawn %s failed" % type_name
        n = len(scene.units)
        trace = Trace(scene.name, "c")
        trace.frames.append(_frame(h, w, n, id_offset))
        for tick in range(scene.ticks):
            for t, verb, uids, x, y in scene.orders:
                if t == tick:
                    _order(h, w, verb, uids, x, y, id_offset)
            if hook:
                hook(h, w, tick)
            h.om_tactical_step(w)
            trace.frames.append(_frame(h, w, n, id_offset))
    finally:
        h.om_world_free(w)
    return trace


def type_stats(type_name):
    """The C's own stats for a unit type (profile getters), as the same dict keys the Python uses."""
    h = lib(rebuild=False)
    for fn in ("max_hp", "base_damage", "attack_interval", "attack_range", "speed", "sensor_radius",
               "layer_transition_time", "aoe_radius", "category"):
        f = getattr(h, "om_unit_profile_" + fn)
        f.argtypes = [ctypes.c_void_p, ctypes.c_int]
        f.restype = ctypes.c_int if fn == "category" else ctypes.c_double
    w = ctypes.c_void_p(h.om_world_new(1, 1))
    try:
        for name, spec in CUSTOM_TYPES.items():
            h.om_roster_register_custom_unit(
                w, spec["type_id"], spec["category"], name.encode(), spec["hp"], spec["base_damage"],
                spec["attack_interval"], spec["attack_range"], spec["speed"], spec["sensor_radius"],
                spec["layer_transition_time"], spec["aoe_radius"], 0)
        t = _type_id(type_name)
        return {"hp": h.om_unit_profile_max_hp(w, t), "base_damage": h.om_unit_profile_base_damage(w, t),
                "attack_interval": h.om_unit_profile_attack_interval(w, t),
                "attack_range": h.om_unit_profile_attack_range(w, t), "speed": h.om_unit_profile_speed(w, t),
                "sensor_radius": h.om_unit_profile_sensor_radius(w, t),
                "layer_transition_time": h.om_unit_profile_layer_transition_time(w, t),
                "aoe_radius": h.om_unit_profile_aoe_radius(w, t), "category": h.om_unit_profile_category(w, t)}
    finally:
        h.om_world_free(w)
