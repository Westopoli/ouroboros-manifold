"""engine.py: build the production C library outside the repo and drive it through ctypes (spec AC 2 and 3)."""
import ctypes
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_X86 = ("x86_64", "AMD64", "i386", "i686", "x86")
# Makefile CFLAGS_COMMON and CFLAGS_DET_BASE (without -Icsrc, handled below), plus -O2; the sse pair is added on x86 only.
_FLAGS = ["-O2", "-std=c11", "-Wall", "-Wextra", "-fPIC", "-fno-fast-math", "-ffp-contract=off",
          "-fexcess-precision=standard", "-fno-math-errno"]
_BUILTIN = {"Raider": 0, "Interceptor": 1, "Vanguard": 2, "Warden": 3, "Bombard": 4, "Bastion": 5}
_lib_cache = None
_param_ids = None


def _load_param_ids():
    """The om_tac_param enum of csrc/ouroboros_sim.h as {name: value}; the header is the contract's source of truth."""
    global _param_ids
    if _param_ids is None:
        text = (ROOT / "csrc" / "ouroboros_sim.h").read_text()
        body = re.search(r"typedef enum \{([^}]*OM_TP_PURSUE_BY_STEERING[^}]*)\}\s*om_tac_param\s*;", text).group(1)
        ids, value = {}, 0
        for m in re.finditer(r"\b(OM_TP_\w+)\s*(?:=\s*(\d+))?\s*,?", re.sub(r"/\*.*?\*/", "", body, flags=re.S)):
            value = int(m.group(2)) if m.group(2) is not None else value
            ids[m.group(1)] = value
            value += 1
        _param_ids = ids
    return _param_ids


def build_library(scratch_dir=None):
    """Compile csrc/*.c into libouroboros.{dylib,so} in scratch_dir (a fresh temp dir if None); return its path."""
    scratch = Path(scratch_dir) if scratch_dir is not None else Path(tempfile.mkdtemp(prefix="skilllab_"))
    scratch.mkdir(parents=True, exist_ok=True)
    out = scratch / ("libouroboros.dylib" if sys.platform == "darwin" else "libouroboros.so")
    flags = list(_FLAGS)
    if platform.machine() in _X86:
        flags += ["-msse2", "-mfpmath=sse"]
    srcs = sorted(str(p) for p in (ROOT / "csrc").glob("*.c"))
    cmd = ["cc"] + flags + ["-I" + str(ROOT / "csrc"), "-shared", "-o", str(out)] + srcs
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(_tail(e.stderr)) from e
    except OSError as e:
        raise RuntimeError("cc could not be run: %s" % e) from e
    if res.returncode != 0:
        raise RuntimeError(_tail(res.stderr))
    return out


def _tail(err):
    if isinstance(err, bytes):
        err = err.decode(errors="replace")
    return str(err or "")[-2000:]


def _cached_library():
    global _lib_cache
    if _lib_cache is None:
        _lib_cache = build_library()
    return _lib_cache


class Engine:
    """The ctypes wrapper of the production library; every method takes the world handle first (except new_world)."""

    def __init__(self, lib_path=None):
        path = Path(lib_path) if lib_path is not None else _cached_library()
        self._lib = ctypes.CDLL(str(path))      # a nonexistent path raises OSError
        self._bind()
        self._px, self._py = ctypes.c_double(), ctypes.c_double()
        self._pbx, self._pby = ctypes.byref(self._px), ctypes.byref(self._py)
        self._own = {}      # (world address, faction) -> unit ids spawned through this wrapper

    def _bind(self):
        c, V, u32, u64, d, i = (ctypes, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_double,
                                ctypes.c_int)
        pd = c.POINTER(d)
        sigs = {
            "om_world_new": ([u32, u64], V),
            "om_world_free": ([V], None),
            "om_roster_register_custom_unit": ([V, u32, i, c.c_char_p, d, d, d, d, d, d, d, d, i], i),
            "om_unit_profile_category": ([V, i], i),
            "om_unit_profile_max_hp": ([V, i], d),
            "om_unit_profile_base_damage": ([V, i], d),
            "om_unit_profile_attack_interval": ([V, i], d),
            "om_unit_profile_attack_range": ([V, i], d),
            "om_unit_profile_speed": ([V, i], d),
            "om_unit_profile_sensor_radius": ([V, i], d),
            "om_unit_profile_layer_transition_time": ([V, i], d),
            "om_unit_profile_aoe_radius": ([V, i], d),
            "om_unit_profile_reach": ([V, i, c.POINTER(u32), c.POINTER(u32)], i),
            "om_tactical_disable_abilities": ([V], None),
            "om_unit_spawn": ([V, i, c.c_int32, d, d, u32], u32),
            "om_command_attack_move": ([V, c.POINTER(u32), u32, d, d], i),
            "om_command_move": ([V, c.POINTER(u32), u32, d, d], i),
            "om_command_group_move": ([V, c.POINTER(u32), u32, d, d], u32),
            "om_command_guard": ([V, c.POINTER(u32), u32], i),
            "om_roster_set_reach": ([V, i, u32, u32], i),
            "om_tactical_step": ([V], u64),
            "om_unit_get_hp": ([V, u32], d),
            "om_unit_get_pos": ([V, u32, pd, pd], i),
            "om_unit_get_destination": ([V, u32, pd, pd], i),
            "om_unit_get_layer": ([V, u32], c.c_int32),
            "om_unit_alive": ([V, u32], i),
            "om_unit_get_target": ([V, u32], u32),
            "om_unit_get_facing": ([V, u32], d),
            "om_unit_get_unit_type": ([V, u32], c.c_int32),
            "om_unit_transition_progress": ([V, u32], d),
            "om_tactical_category_multiplier": ([V, i, i], d),
            "om_tactical_get_param": ([V, i], d),
            "om_tactical_set_param": ([V, i, d], i),
            "om_combat_can_shoot": ([V, u32, u32], i),
            "om_unit_can_see": ([V, u32, u32], i),
            "om_unit_clear_orders": ([V, u32], None),
            "om_map_add_obstacle": ([V, d, d, d], u32),
            "om_map_set_canvas": ([V, d, d], i),
            "om_map_block_rect": ([V, d, d, d, d, u32, u32], i),
            "om_map_add_cover": ([V, d, d, d, d], u32),
            "om_command_ping": ([V, u32, u32, d, d], i),
            "om_command_set_layer": ([V, c.POINTER(u32), u32, u32], i),
            "om_command_set_emission": ([V, c.POINTER(u32), u32, i], i),
            "om_player_can_see": ([V, c.c_int32, u32], i),
            "om_terrain_generate": ([V, u64, d, d], i),
            "om_terrain_band_at": ([V, d, d], i),
            "om_terrain_walkable_at": ([V, d, d], i),
            "om_terrain_cells": ([V, c.POINTER(u32), c.POINTER(u32)], u32),
            "om_terrain_dump_bands": ([V, c.c_char_p, u32], u32),
            "om_terrain_walk_mask": ([V, i, c.c_char_p, u32], u32),
            "om_terrain_slope_at": ([V, d, d, V], i),
            "om_set_era_kind": ([V, i], i),
            "om_roster_set_movement_kind": ([V, i, i], i),
            "om_unit_profile_movement_kind": ([V, i], i),
        }
        for name, (argtypes, restype) in sigs.items():
            fn = getattr(self._lib, name)
            fn.argtypes = argtypes
            fn.restype = restype
        fn = getattr(self._lib, "om_roster_set_cone", None)    # absent until E0 lands
        if fn is not None:
            fn.argtypes = [V, i, d, d, d]
            fn.restype = i
        fn = getattr(self._lib, "om_combat_can_engage", None)    # absent until E0 lands
        if fn is not None:
            fn.argtypes = [V, u32, u32]
            fn.restype = i

    def new_world(self, seed):
        w = self._lib.om_world_new(1, int(seed))
        if not w:
            raise RuntimeError("om_world_new returned NULL")
        return ctypes.c_void_p(w)

    def free_world(self, w):
        for k in [k for k in self._own if k[0] == w.value]:
            del self._own[k]
        self._lib.om_world_free(w)

    def register_unit_type(self, w, type_id, stats):
        rc = self._lib.om_roster_register_custom_unit(
            w, int(type_id), int(stats["category"]), str(stats["role"]).encode(), float(stats["max_hp"]),
            float(stats["base_damage"]), float(stats["attack_interval"]), float(stats["attack_range"]),
            float(stats["speed"]), float(stats["sensor_radius"]), float(stats["layer_transition_time"]),
            float(stats["aoe_radius"]), int(stats["ability_id"]))
        if rc != 0:
            raise ValueError("om_roster_register_custom_unit(%r) returned %d" % (type_id, rc))

    def type_id(self, name):
        if name not in _BUILTIN:
            raise ValueError("unknown built-in unit type %r" % (name,))
        return _BUILTIN[name]

    def type_stats(self, w, type_id):
        L, t = self._lib, int(type_id)
        return {"category": L.om_unit_profile_category(w, t), "max_hp": L.om_unit_profile_max_hp(w, t),
                "base_damage": L.om_unit_profile_base_damage(w, t),
                "attack_interval": L.om_unit_profile_attack_interval(w, t),
                "attack_range": L.om_unit_profile_attack_range(w, t), "speed": L.om_unit_profile_speed(w, t),
                "sensor_radius": L.om_unit_profile_sensor_radius(w, t),
                "layer_transition_time": L.om_unit_profile_layer_transition_time(w, t),
                "aoe_radius": L.om_unit_profile_aoe_radius(w, t)}

    def profile_reach(self, w, type_id):
        up, down = ctypes.c_uint32(0), ctypes.c_uint32(0)    # the library body may write nothing
        if self._lib.om_unit_profile_reach(w, int(type_id), ctypes.byref(up), ctypes.byref(down)) != 0:
            raise ValueError("om_unit_profile_reach(%r) refused" % (type_id,))
        return (int(up.value), int(down.value))

    def set_reach(self, w, type_id, up, down):
        rc = self._lib.om_roster_set_reach(w, int(type_id), int(up), int(down))
        if rc != 0:
            raise ValueError("om_roster_set_reach(%r, %r, %r) returned %d" % (type_id, up, down, rc))

    def set_cone(self, w, type_id, range, half_angle, share):
        rc = self._lib.om_roster_set_cone(w, int(type_id), float(range), float(half_angle), float(share))
        if rc != 0:
            raise ValueError("om_roster_set_cone(%r, %r, %r, %r) returned %d" % (type_id, range, half_angle, share, rc))

    def disable_abilities(self, w):
        self._lib.om_tactical_disable_abilities(w)

    def spawn(self, w, type_id, faction, x, y, layer):
        uid = int(self._lib.om_unit_spawn(w, int(type_id), int(faction), float(x), float(y), int(layer)))
        if uid:
            self._own.setdefault((w.value, int(faction)), []).append(uid)
        return uid

    def ping(self, w, caster, layer, x, y):
        return int(self._lib.om_command_ping(w, int(caster), int(layer), float(x), float(y)))

    def set_layer(self, w, ids, layer):
        ids = [int(u) for u in ids]
        self._lib.om_command_set_layer(w, (ctypes.c_uint32 * len(ids))(*ids), len(ids), int(layer))

    def set_emission(self, w, ids, on):
        ids = [int(u) for u in ids]
        self._lib.om_command_set_emission(w, (ctypes.c_uint32 * len(ids))(*ids), len(ids), 1 if on else 0)

    def visible_enemies(self, w, side, enemy_ids):
        return {int(e) for e in enemy_ids if self._lib.om_player_can_see(w, int(side), int(e))}

    def seen_by_sight(self, w, side, enemy_ids):
        own = [o for o in self._own.get((w.value, int(side)), []) if self.unit_alive(w, o)]
        return {int(e) for e in enemy_ids if any(self._lib.om_unit_can_see(w, o, int(e)) for o in own)}

    def set_ping_params(self, w, radius=None, reach=None, reveal_ticks=None, cooldown_ticks=None):
        for name, v in (("OM_TP_PING_RADIUS", radius), ("OM_TP_PING_REACH", reach),
                        ("OM_TP_PING_REVEAL_TICKS", reveal_ticks), ("OM_TP_PING_COOLDOWN_TICKS", cooldown_ticks)):
            if v is not None:
                self.set_param(w, self.param_id(name), v)

    def order_attack_move(self, w, unit_ids, x, y):
        self._order(self._lib.om_command_attack_move, w, unit_ids, x, y)

    def order_move(self, w, unit_ids, x, y):
        # om_command_move, not om_unit_order_move: the latter only records a destination and never moves the unit.
        self._order(self._lib.om_command_move, w, unit_ids, x, y)

    def order_group_move(self, w, unit_ids, x, y):
        ids = [int(u) for u in unit_ids]
        return int(self._lib.om_command_group_move(w, (ctypes.c_uint32 * len(ids))(*ids), len(ids), float(x), float(y)))

    def order_guard(self, w, unit_ids):
        ids = [int(u) for u in unit_ids]
        rc = self._lib.om_command_guard(w, (ctypes.c_uint32 * len(ids))(*ids), len(ids))
        if rc != 0:
            raise ValueError("om_command_guard returned %d" % rc)

    @staticmethod
    def _order(fn, w, unit_ids, x, y):
        ids = [int(u) for u in unit_ids]
        fn(w, (ctypes.c_uint32 * len(ids))(*ids), len(ids), float(x), float(y))

    def can_see(self, w, observer, target):
        return bool(self._lib.om_unit_can_see(w, int(observer), int(target)))

    def clear_orders(self, w, unit_ids):
        for u in unit_ids:
            self._lib.om_unit_clear_orders(w, int(u))

    def step(self, w):
        self._lib.om_tactical_step(w)

    def unit_hp(self, w, u):
        return self._lib.om_unit_get_hp(w, u)

    def unit_pos(self, w, u):
        self._lib.om_unit_get_pos(w, u, self._pbx, self._pby)
        return (self._px.value, self._py.value)

    def unit_destination(self, w, u):
        x, y = ctypes.c_double(), ctypes.c_double()
        if not self._lib.om_unit_get_destination(w, int(u), ctypes.byref(x), ctypes.byref(y)):
            return None
        return (float(x.value), float(y.value))

    def unit_layer(self, w, u):
        return self._lib.om_unit_get_layer(w, u)

    def unit_alive(self, w, u):
        return bool(self._lib.om_unit_alive(w, u))

    def unit_target(self, w, u):
        return int(self._lib.om_unit_get_target(w, int(u)))

    def unit_facing(self, w, u):
        return float(self._lib.om_unit_get_facing(w, int(u)))

    def unit_type(self, w, u):
        return int(self._lib.om_unit_get_unit_type(w, int(u)))

    def transition_progress(self, w, u):
        return float(self._lib.om_unit_transition_progress(w, int(u)))

    def category_multiplier(self, w, attacker_category, target_category):
        return float(self._lib.om_tactical_category_multiplier(w, int(attacker_category), int(target_category)))

    def can_engage(self, w, a, b):
        """om_combat_can_engage; -1 when the library has no such symbol (before E0), as the E0 stub answers."""
        fn = getattr(self._lib, "om_combat_can_engage", None)
        return -1 if fn is None else int(fn(w, int(a), int(b)))

    def param_id(self, name):
        ids = _load_param_ids()
        if name not in ids or name.endswith("__COUNT"):
            raise ValueError("unknown tactical parameter %r" % (name,))
        return ids[name]

    def get_param(self, w, param):
        return float(self._lib.om_tactical_get_param(w, int(param)))

    def set_param(self, w, param, value):
        if self._lib.om_tactical_set_param(w, int(param), float(value)) != 0:
            raise ValueError("om_tactical_set_param(%r, %r) refused" % (param, value))

    def can_shoot(self, w, a, b):
        return bool(self._lib.om_combat_can_shoot(w, a, b))

    def add_blocker(self, w, x, y, radius):
        if not radius > 0:
            raise ValueError("blocker radius must be positive, got %r" % (radius,))
        self._lib.om_map_add_obstacle(w, float(x), float(y), float(radius))

    def set_canvas(self, w, width, height):
        if self._lib.om_map_set_canvas(w, float(width), float(height)) != 0:
            raise ValueError("om_map_set_canvas(%r, %r) refused (set_canvas)" % (width, height))

    def block_rect(self, w, x0, y0, x1, y1, layer_lo, layer_hi):
        if self._lib.om_map_block_rect(w, float(x0), float(y0), float(x1), float(y1), int(layer_lo),
                                       int(layer_hi)) != 0:
            raise ValueError("om_map_block_rect(%r, %r, %r, %r, %r, %r) refused (block_rect)"
                             % (x0, y0, x1, y1, layer_lo, layer_hi))

    def add_cover(self, w, x, y, radius, height):
        idx = int(self._lib.om_map_add_cover(w, float(x), float(y), float(radius), float(height)))
        if idx == 0:
            raise ValueError("om_map_add_cover(%r, %r, %r, %r) refused (add_cover)" % (x, y, radius, height))
        return idx

    def terrain_generate(self, w, seed, canvas):
        return int(self._lib.om_terrain_generate(w, int(seed), float(canvas), float(canvas)))

    def terrain_band_at(self, w, x, y):
        return int(self._lib.om_terrain_band_at(w, float(x), float(y)))

    def terrain_walkable_at(self, w, x, y):
        return bool(self._lib.om_terrain_walkable_at(w, float(x), float(y)))

    def terrain_dump_bands(self, w):
        cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
        n = int(self._lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch)))
        buf = ctypes.create_string_buffer(n)
        self._lib.om_terrain_dump_bands(w, buf, n)
        return int(cw.value), int(ch.value), buf.raw

    def terrain_walk_mask(self, w, layer):
        cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
        n = int(self._lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch)))
        buf = ctypes.create_string_buffer(n)
        self._lib.om_terrain_walk_mask(w, int(layer), buf, n)
        return buf.raw

    def terrain_slope_at(self, w, x, y):
        return int(self._lib.om_terrain_slope_at(w, float(x), float(y), None))

    def set_era_kind(self, w, kind):
        return int(self._lib.om_set_era_kind(w, int(kind)))

    def set_movement_kind(self, w, type_id, kind):
        return int(self._lib.om_roster_set_movement_kind(w, int(type_id), int(kind)))

    def movement_kind(self, w, type_id):
        return int(self._lib.om_unit_profile_movement_kind(w, int(type_id)))
