"""ctypes mirror of include/layerlab.h, checked against the loaded library at load time."""
import ctypes as C
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent

LAYERS = 5
TICKS_PER_SEC = 20
MAX_UNITS = 4096
MAX_TYPES = 16
MAX_COVER = 32
MAX_VANTAGE = 16
MAX_ZONES = 16
MAX_SLOPES = 16
MAX_GRID_W = 128
MAX_GRID_H = 64
MAX_CELLS = MAX_GRID_W * MAX_GRID_H

CAT_STRIKE, CAT_LINE, CAT_SIEGE = 0, 1, 2
MOVE_FLY, MOVE_WALK = 0, 1
ABILITY_NONE, ABILITY_BURST = 0, 1
ORDER_HOLD, ORDER_MOVE, ORDER_ATTACK_MOVE = 0, 1, 2
TARGET_NEAREST, TARGET_LOWEST_HP, TARGET_HIGHEST_COST = 0, 1, 2
HALFWAY_BOTH, HALFWAY_RULE, HALFWAY_UNTARGETABLE = 0, 1, 2
WIN_NONE, WIN_A, WIN_B, WIN_STALEMATE, WIN_CAP, WIN_MUTUAL = 0, 1, 2, 3, 4, 5

ABI_VERSION = 4

d, i32, u8, f32 = C.c_double, C.c_int32, C.c_uint8, C.c_float


class ll_rules(C.Structure):
    _fields_ = [
        ("vis_factor", d * 9),
        ("vantage_vis_factor", d * 9),
        ("sensor_elev_bonus_per_layer", d),
        ("range_mult", d * 9),
        ("dmg_mult", d * 9),
        ("aoe_layer_mult", d * 9),
        ("category_mult", (d * 3) * 3),
        ("aoe_cap_mult", d),
        ("pulse_radius", d),
        ("pulse_reveal_s", d),
        ("pulse_cooldown_s", d),
        ("transition_speed_mult", d),
        ("separation_weight", d),
        ("spawn_jitter", d),
        ("emit_see_mult", d * 2),
        ("emit_seen_mult", d * 2),
        ("ping_reach", d),
        ("ping_radius", d),
        ("ping_s", d),
        ("ping_cooldown_s", d),
        ("fire_requires_vision", i32),
        ("facing_gates_fire", i32),
        ("halfway_mode", i32),
        ("auto_transition", i32),
        ("cover_mode", i32),
        ("chase_when_idle", i32),
        ("forced_change_penalty", i32),
        ("timed_new_layer_at_half", i32),
        ("max_ticks", i32),
        ("stalemate_ticks", i32),
        ("emit_on", i32),
        ("pad0_", i32),
        ("pad1_", i32),
        ("pad2_", i32),
    ]


class ll_unit_type(C.Structure):
    _fields_ = [
        ("category", i32),
        ("movement_kind", i32),
        ("hp", d),
        ("dmg", d),
        ("interval_s", d),
        ("range", d),
        ("speed", d),
        ("sensor", d),
        ("transition_s", d),
        ("aoe_r", d),
        ("turn_rate", d),
        ("arc_deg", d),
        ("cost", d),
        ("body_radius", d),
        ("ability_kind", i32),
        ("ab_min_targets", i32),
        ("ab_dmg_mult", d),
        ("ab_radius", d),
        ("ab_windup_s", d),
        ("ab_cooldown_s", d),
        ("pulse_capable", i32),
        ("pad_", i32),
        ("reach", d * 9),
        ("reach_on", i32),
        ("pad2_", i32),
    ]


class ll_cover(C.Structure):
    _fields_ = [("x", d), ("y", d), ("r", d), ("height_layer", i32), ("pad_", i32)]


class ll_vantage(C.Structure):
    _fields_ = [("x", d), ("y", d), ("r", d)]


class ll_zone(C.Structure):
    _fields_ = [("x", d), ("y", d), ("r", d), ("intensity", d), ("layer", i32), ("pad_", i32)]


class ll_slope(C.Structure):
    _fields_ = [
        ("x0", d), ("y0", d), ("dx", d), ("dy", d), ("length", d), ("width", d),
        ("bottom_layer", i32), ("top_layer", i32),
    ]


class ll_terrain(C.Structure):
    _fields_ = [
        ("w_cells", i32),
        ("h_cells", i32),
        ("cell", d),
        ("layer_spacing", d),
        ("open", u8 * MAX_CELLS),
        ("land", u8 * MAX_CELLS),
        ("n_cover", i32),
        ("n_vantage", i32),
        ("n_zone", i32),
        ("n_slope", i32),
        ("cover", ll_cover * MAX_COVER),
        ("vantage", ll_vantage * MAX_VANTAGE),
        ("zone", ll_zone * MAX_ZONES),
        ("slope", ll_slope * MAX_SLOPES),
    ]


class ll_spawn(C.Structure):
    _fields_ = [
        ("side", i32),
        ("type", i32),
        ("x", d),
        ("y", d),
        ("facing_deg", d),
        ("layer", i32),
        ("order", i32),
        ("gx", d),
        ("gy", d),
        ("pre_revealed", i32),
        ("transfer_layer", i32),
        ("transfer_tick", i32),
        ("pulse_tick", i32),
        ("target_policy", i32),
        ("pad_", i32),
        ("emit", i32),
        ("emit_switch_tick", i32),
        ("emit_switch_to", i32),
        ("ping_tick", i32),
        ("ping_layer", i32),
        ("pad2_", i32),
        ("ping_x", d),
        ("ping_y", d),
    ]


class ll_scenario(C.Structure):
    _fields_ = [
        ("rules", ll_rules),
        ("types", ll_unit_type * MAX_TYPES),
        ("n_types", i32),
        ("n_spawns", i32),
        ("terrain", ll_terrain),
        ("spawns", ll_spawn * MAX_UNITS),
    ]


class ll_unit_out(C.Structure):
    _fields_ = [
        ("x", d), ("y", d), ("hp", d),
        ("layer", i32), ("alive", i32), ("transitions", i32), ("pad_", i32),
    ]


class ll_result(C.Structure):
    _fields_ = [
        ("winner", i32),
        ("ticks", i32),
        ("survivors", i32 * 2),
        ("hp_ratio", d * 2),
        ("cost_lost", d * 2),
        ("damage_dealt", d * 2),
        ("shots", i32 * 2),
        ("transitions", i32),
        ("first_shot_side", i32),
        ("first_shot_tick", i32),
        ("first_contact_tick", i32),
        ("unanswered_ticks", i32 * 2),
        ("alive_ticks", i32 * 2),
        ("firing_ticks", i32 * 2),
        ("firing_weight", d * 2),
        ("alerted_tick", i32 * 2),
        ("alerts", i32 * 2),
        ("alert_dir_x", d * 2),
        ("alert_dir_y", d * 2),
        ("unit", ll_unit_out * MAX_UNITS),
    ]


class ll_trace_rec(C.Structure):
    _fields_ = [
        ("x", f32), ("y", f32), ("hp", f32), ("progress", f32),
        ("layer", u8), ("side", u8), ("alive", u8), ("flags", u8),
    ]


class ll_trace(C.Structure):
    _fields_ = [
        ("buf", C.POINTER(ll_trace_rec)),
        ("capacity_ticks", i32),
        ("ticks_written", i32),
    ]


# ll_sizeof(which) order: 0 rules, 1 unit_type, 2 terrain, 3 spawn, 4 scenario, 5 result, 6 trace_rec
_SIZEOF_ORDER = [ll_rules, ll_unit_type, ll_terrain, ll_spawn, ll_scenario, ll_result, ll_trace_rec]

_libs = {}


def lib_path(lib="O2"):
    if lib in ("O0", "O2"):
        return LAB / "build" / lib / "liblayerlab.so"
    return Path(lib)


def load_lib(lib="O2"):
    path = str(lib_path(lib).resolve())
    if path in _libs:
        return _libs[path]
    dll = C.CDLL(path)
    dll.ll_abi_version.argtypes = []
    dll.ll_abi_version.restype = C.c_uint32
    dll.ll_sizeof.argtypes = [C.c_int]
    dll.ll_sizeof.restype = C.c_uint32
    dll.ll_run.argtypes = [C.POINTER(ll_scenario), C.c_uint64, C.POINTER(ll_result), C.POINTER(ll_trace)]
    dll.ll_run.restype = C.c_int
    dll.ll_probe_can_see.argtypes = [C.POINTER(ll_scenario), C.c_uint64, C.c_int, C.c_int]
    dll.ll_probe_can_see.restype = C.c_int
    dll.ll_last_error.argtypes = []
    dll.ll_last_error.restype = C.c_char_p
    assert dll.ll_abi_version() == ABI_VERSION, (
        "%s: ll_abi_version %d != %d" % (path, dll.ll_abi_version(), ABI_VERSION))
    for which, cls in enumerate(_SIZEOF_ORDER):
        assert C.sizeof(cls) == dll.ll_sizeof(which), (
            "%s: sizeof(%s) is %d in ctypes, %d in C" % (path, cls.__name__, C.sizeof(cls), dll.ll_sizeof(which)))
    _libs[path] = dll
    return dll


if lib_path("O2").exists():
    load_lib("O2")
