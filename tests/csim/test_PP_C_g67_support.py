"""Shared helpers for the Phase C tests of steps G6 (going dark) and G7 (the targeted ping)
(docs/northstar/plans/2026-10-02-skill-lab-cascade.md section 5; plan Phase C; rulings-2 A132, A133, A143).
Holds no tests of its own. Fence: tests/csim/test_PP_C_g67_*.py; builders never edit these.

Layer numbering (A132): the bible numbers layers 1 to 5 from the bottom, the engine and every test here count
0 to 4 (bible layer n is engine layer n - 1). The brief's G7 test "a ping on layer 5 from a unit on layer 1" is
therefore a ping on engine layer 4 from a unit on engine layer 0.
"""
import ctypes
import re

from conftest import CSRC_DIR, OMEmission, OMPingAlert, OMTacParam

HEADER = CSRC_DIR / "ouroboros_sim.h"

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION, SUPPLY, EVACUATION = range(8)

# Per-type sensor radii from csrc/om_constants.h (OM_ROSTER_*_SENSOR); the INTERCEPTOR's 1,000 is the
# observer of E-01 R-005 and brief G6.
INTERCEPTOR_SENSOR = 1000.0

# Reason numbers of om_command_ping (pp_contract.md section 6; "proposed by writer" there, the brief names
# the four reasons only). A test that asserts a number below asserts the contract document's number.
PING_OK = 0
PING_REASON_CASTER = 1      # caster unknown or dead
PING_REASON_REACH = 2       # point beyond OM_TP_PING_REACH
PING_REASON_COOLDOWN = 3    # caster on cooldown
PING_REASON_LAYER = 4       # layer at or above OM_LAYER_COUNT


def layer_count():
    m = re.search(r"^[ \t]*#define[ \t]+OM_LAYER_COUNT[ \t]+(\d+)", HEADER.read_text(), re.M)
    assert m, "OM_LAYER_COUNT is not defined in csrc/ouroboros_sim.h (A132)"
    return int(m.group(1))


def step(lib, w, n=1):
    for _ in range(n):
        lib.om_tactical_step(w)


def spawn(lib, w, utype, faction, x, y, layer=0):
    uid = lib.om_unit_spawn(w, utype, faction, float(x), float(y), layer)
    assert uid != 0, "om_unit_spawn returned id 0"
    return uid


def set_param(lib, w, name, value):
    rc = lib.om_tactical_set_param(w, getattr(OMTacParam, name), float(value))
    assert rc == 0, f"om_tactical_set_param({name}, {value}) refused; the contract table says it is in range"


def set_emission(lib, w, ids, mode):
    ids = list(ids)
    arr = (ctypes.c_uint32 * max(len(ids), 1))(*ids)
    return lib.om_command_set_emission(w, arr, len(ids), mode)


def emission(lib, w, uid):
    return lib.om_unit_get_emission(w, uid)


def place(lib, w, uid, x, y):
    """Move a unit in the plane. om_unit_teleport takes a layer argument but ignores it (csrc/tactical_move.c,
    `(void)layer`): a unit's layer is the one it was spawned on until om_command_set_layer (G4) exists. Tests
    here therefore spawn each unit on the layer it needs."""
    lib.om_unit_teleport(w, uid, float(x), float(y), 0)


def can_see(lib, w, observer, target):
    """om_unit_can_see is read straight from the positions and layers as they stand (no tick needed)."""
    return int(lib.om_unit_can_see(w, observer, target))


def sees_at(lib, w, observer, target, dist):
    """Put the observer at the origin and the target `dist` wu along +x (layers are as spawned); return
    om_unit_can_see. Teleports both, so a tick run before the call cannot have moved them."""
    place(lib, w, observer, 0.0, 0.0)
    place(lib, w, target, dist, 0.0)
    return can_see(lib, w, observer, target)


def side_sees(lib, w, faction, unit):
    """The side's visible set (E-12 R-089-02, R-093-02): om_player_can_see(faction, unit) is the union over
    the faction's units; the ping puts its revealed enemies into that set (R-162-05)."""
    return int(lib.om_player_can_see(w, faction, unit))


def ping(lib, w, caster, layer, x, y):
    return lib.om_command_ping(w, caster, layer, float(x), float(y))


def alert_count(lib, w, faction):
    return lib.om_ping_alert_count(w, faction)


def alert(lib, w, faction, index):
    """(rc, tick, faction, sector) from om_ping_alert_get."""
    out = OMPingAlert()
    rc = lib.om_ping_alert_get(w, faction, index, ctypes.byref(out))
    return rc, out.tick, out.faction, out.sector
