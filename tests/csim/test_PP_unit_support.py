"""Shared helpers for the PP-unit rule tests (plan 2026-10-02-movement-layers-and-search-plan.md,
Phase A, wave A3: csrc/unit.c). Holds no tests of its own.

Fence: tests/csim/test_PP_unit_*.py. Builders never edit these.

Contract calls that do not exist yet (om_tactical_get_param / om_tactical_set_param and the
om_tac_param enum, plan appendix "PP-contract") are resolved at call time: a missing symbol or
enum name FAILS the test with a message naming it, it does not skip. The enum's integer values are
read from csrc/ouroboros_sim.h so the tests do not pin an order the contract has not frozen.
"""
import ctypes
import re

import pytest

from conftest import CSRC_DIR, OMWorldP

HEADER = CSRC_DIR / "ouroboros_sim.h"

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION, SUPPLY, EVACUATION = range(8)

TICK_RATE = 20  # OM_TACTICAL_TICK_RATE; one om_tactical_step is one tick at 1000 or fewer live units


def step(lib, w, n=1):
    for _ in range(n):
        lib.om_tactical_step(w)


def watch_target(lib, w, uid, n):
    """The unit's target after each of n successive ticks."""
    seen = []
    for _ in range(n):
        step(lib, w)
        seen.append(lib.om_unit_target(w, uid))
    return seen


def spawn(lib, w, utype, faction, x, y, layer=0):
    uid = lib.om_unit_spawn(w, utype, faction, float(x), float(y), layer)
    assert uid != 0, "om_unit_spawn returned id 0"
    return uid


def pos(lib, w, uid):
    return (lib.om_unit_position_x(w, uid), lib.om_unit_position_y(w, uid))


def dest(lib, w, uid):
    """(has_dest, x, y) read straight from om_unit_get_destination; the conftest wrapper drops
    the has_dest return, and a unit with no goal must be told apart from one whose goal is (0, 0)."""
    x = ctypes.c_double()
    y = ctypes.c_double()
    has = lib.om_unit_get_destination.raw(w, uid, ctypes.byref(x), ctypes.byref(y))
    return int(has), x.value, y.value


def hp(lib, w, uid):
    return lib.om_unit_get_hp(w, uid)


def target(lib, w, uid):
    return lib.om_unit_target(w, uid)


def kill(lib, w, uid):
    lib.om_unit_set_hp(w, uid, 0.0)


def attack_move(lib, w, ids, x, y):
    ids = list(ids)
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_attack_move.raw(w, arr, len(ids), float(x), float(y))


# ---- contract calls not in the library yet (PP-contract) ----

def _enum_values():
    text = HEADER.read_text()
    m = re.search(r"typedef\s+enum\s*\{([^}]*)\}\s*om_tac_param\s*;", text, re.S)
    if not m:
        pytest.fail("contract missing: enum om_tac_param is not in csrc/ouroboros_sim.h "
                    "(PP-contract not landed yet; OM_TP_* settings need it)")
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    values, nxt = {}, 0
    for item in body.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            name, val = [s.strip() for s in item.split("=", 1)]
            nxt = int(val, 0)
        else:
            name = item
        values[name] = nxt
        nxt += 1
    return values


def tp(name):
    values = _enum_values()
    if name not in values:
        pytest.fail(f"contract missing: {name} is not in enum om_tac_param in csrc/ouroboros_sim.h")
    return values[name]


def _need(lib, symbol):
    if not hasattr(lib, symbol):
        pytest.fail(f"contract missing: {symbol} is not exported by libouroboros.so "
                    "(PP-contract not landed yet)")
    return getattr(lib, symbol)


def set_param(lib, w, name, value):
    fn = _need(lib, "om_tactical_set_param")
    fn.argtypes = [OMWorldP, ctypes.c_int, ctypes.c_double]
    fn.restype = ctypes.c_int
    return fn(w, tp(name), float(value))


def get_param(lib, w, name):
    fn = _need(lib, "om_tactical_get_param")
    fn.argtypes = [OMWorldP, ctypes.c_int]
    fn.restype = ctypes.c_double
    return fn(w, tp(name))
