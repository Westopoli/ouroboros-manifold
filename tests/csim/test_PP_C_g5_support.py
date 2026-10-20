# Rule pins: 
"""Shared helpers for the Phase C step G5 tests (reach by unit type). Holds no tests of its own.

Plan 2026-10-02-movement-layers-and-search-plan.md Phase C and brief 2026-10-02-skill-lab-cascade.md
section 5 G5; pp_contract.md sections 3, 4 and 6. Fence: tests/csim/test_PP_C_g5_*.py. Builders never
edit these.

Layer numbering (A132): the bible numbers layers 1 to 5, the engine and these tests 0 to 4
(OM_LAYER_COUNT 5); bible layer n is engine layer n - 1. Every layer below is an engine layer.

Offsets are signed and read from the attacker (or observer): "up n" means the other unit is n layers
above it (a higher engine layer number), "down n" n layers below. Setting names follow the contract:
OM_TP_RANGE_UP_n, OM_TP_RANGE_DOWN_n, OM_TP_DAMAGE_..., OM_TP_AREA_..., OM_TP_VISION_...

Fight shape used throughout: attackers are real combat types; targets are Supply units, which never
fire (so nothing else moves hp) and take the fallback profile (STRIKE category, 100 hp). Damage is
measured RELATIVE to a baseline hit at the same distance on the attacker's own layer, so no roster
number is pinned here. The direct-fire attacker is the Vanguard (range 300, sensor 700): a Raider's
Surge ability auto-triggers only for a same-layer enemy and doubles its output, which would make a
cross-layer hit differ from its same-layer baseline for a reason that is not G5.
"""
import ctypes
import re

import pytest

from conftest import CSRC_DIR, OMWorldP
from test_PP_unit_support import (  # noqa: F401
    RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION, SUPPLY,
    attack_move, dest, hp, kill, pos, spawn, step, target,
)

HEADER = CSRC_DIR / "ouroboros_sim.h"


def _tp_values():
    """om_tac_param member -> value, read from the header. test_PP_unit_support.tp() is not used: its
    pattern needs 'typedef enum om_tac_param {', and the header has the anonymous form
    'typedef enum { ... } om_tac_param;', so it fails every call (finding, reported)."""
    text = HEADER.read_text()
    m = re.search(r"\{([^{}]*)\}\s*om_tac_param\s*;", text)
    if not m:
        pytest.fail("contract missing: enum om_tac_param is not in csrc/ouroboros_sim.h")
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    values, nxt = {}, 0
    for item in body.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            name, val = [x.strip() for x in item.split("=", 1)]
            nxt = int(val, 0)
        else:
            name = item
        values[name] = nxt
        nxt += 1
    return values


def set_param(lib, w, name, value):
    fn = lib.om_tactical_set_param
    fn.argtypes = [OMWorldP, ctypes.c_int, ctypes.c_double]
    fn.restype = ctypes.c_int
    return fn(w, _tp_values()[name], float(value))


def get_param(lib, w, name):
    fn = lib.om_tactical_get_param
    fn.argtypes = [OMWorldP, ctypes.c_int]
    fn.restype = ctypes.c_double
    return fn(w, _tp_values()[name])

LAYERS = 5            # OM_LAYER_COUNT
MAX_OFFSET = LAYERS - 1
BUILTIN_COMBAT = (RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION)

# A window long enough for one cohort turn (4 ticks) plus the slowest first attack interval among
# the types used here that is not instant (Bombard 3.0 s = 60 ticks), with margin.
WINDOW = 120

# Geometry margin: a target this many wu inside / outside a computed reach distance. Pure fixture
# geometry (kept well above float noise and well below any radius used), not a game threshold.
EDGE = 5.0


def set_reach(lib, w, utype, up, down):
    return lib.om_roster_set_reach(w, utype, up, down)


def read_reach(lib, w, utype):
    """(rc, up, down); up and down start at 99 so a call that writes nothing is visible."""
    up = ctypes.c_uint32(99)
    down = ctypes.c_uint32(99)
    rc = lib.om_unit_profile_reach(w, utype, ctypes.byref(up), ctypes.byref(down))
    return rc, up.value, down.value


def fresh_hp(lib, w, ids):
    return {i: hp(lib, w, i) for i in ids}


def open_vision(lib, w, factor=1.0):
    """Every cross-layer vision factor (offsets 1 to 4, both directions) to `factor`, so a test of
    reach or of range/damage multipliers is not also a test of sight. Defaults are 0.5, 0.2, 0, 0
    each way."""
    for d in ("UP", "DOWN"):
        for n in range(1, 5):
            assert set_param(lib, w, f"OM_TP_VISION_{d}_{n}", factor) == 0


def first_hit(lib, w, victim, steps=WINDOW):
    """Step until the victim's hp first drops; returns (damage, steps_taken) or (0.0, None)."""
    start = hp(lib, w, victim)
    for i in range(1, steps + 1):
        step(lib, w)
        now = hp(lib, w, victim)
        if now < start:
            return start - now, i
    return 0.0, None


def engaged(lib, w, attacker, victim, steps=WINDOW):
    """True when the attacker holds the victim as its target at some tick of the window AND the
    victim loses hp in it (so 'engaged' means acquired and fired, not merely noticed)."""
    start = hp(lib, w, victim)
    held = False
    for _ in range(steps):
        step(lib, w)
        if target(lib, w, attacker) == victim:
            held = True
        if hp(lib, w, victim) < start and held:
            return True
    return False


def solo_pair(lib, w, a_type, a_layer, t_layer, dist, a_faction=0, t_faction=1):
    """Attacker at the origin, one Supply target `dist` wu along +x, on the given layers.
    Returns (attacker_id, target_id)."""
    a = spawn(lib, w, a_type, a_faction, 0.0, 0.0, layer=a_layer)
    t = spawn(lib, w, SUPPLY, t_faction, float(dist), 0.0, layer=t_layer)
    return a, t


def state_snapshot(lib, w, ids):
    """Per unit (x, y, hp, target, layer): everything a fight can change, for equality checks."""
    return [(pos(lib, w, i), hp(lib, w, i), target(lib, w, i), lib.om_unit_get_layer(w, i)) for i in ids]


def duel(lib, world_factory, a_type, a_layer, t_layer, dist, reach=(0, 0), params=None,
         vision=None, state="idle", steps=WINDOW):
    """One attacker against one Supply target `dist` wu away, in a fresh world. `reach` is set on the
    attacker's type; `params` is {setting name: value}; `vision` opens every cross-layer vision factor
    to that value (None leaves the defaults). `state` is 'idle' or 'attack_move' (marching away from the
    target, so a unit that does not stop for it walks off). Returns (engaged, first_hit_damage)."""
    w = world_factory(n_regions=1)
    # TD-VG-T-1: always set, so a "reach 0" case names (0, 0) instead of relying on the engine's default.
    assert set_reach(lib, w, a_type, *reach) == 0
    if vision is not None:
        open_vision(lib, w, vision)
    for name, value in (params or {}).items():
        assert set_param(lib, w, name, value) == 0
    a, t = solo_pair(lib, w, a_type, a_layer, t_layer, dist)
    if state == "attack_move":
        attack_move(lib, w, [a], -3000.0, 0.0)
    start = hp(lib, w, t)
    held = False
    for _ in range(steps):
        step(lib, w)
        if target(lib, w, a) == t:
            held = True
        now = hp(lib, w, t)
        if now < start:
            return held, start - now
    return held, 0.0


def layers_for(direction, n):
    """(attacker_layer, target_layer) for a target n layers 'up' or 'down' from the attacker, the
    attacker on the layer that leaves room for the full offset (0 going up, 4 going down)."""
    a = 0 if direction == "UP" else MAX_OFFSET
    return a, (a + n if direction == "UP" else a - n)
