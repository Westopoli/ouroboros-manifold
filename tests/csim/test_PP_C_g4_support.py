"""Shared helpers for the Phase C step G4 tests (changing layer: hard transfers, the cross-over, routing across
layers). Holds no tests of its own. Fence: tests/csim/test_PP_C_g4_*.py; builders never edit these.

Sources: docs/northstar/plans/2026-10-02-skill-lab-cascade.md section 5 "G4. Changing layer"; E-01 S-002
(R-002-01 to R-002-07), S-004 (R-004-01 to R-004-05), R-001-05, R-001-07; Addendum 46 A132 (the engine counts layers
0 to 4, bible layer n is engine layer n - 1, so the bible's "layer 3 to layer 4" is engine 2 to 3); the contract
document docs/northstar/plans/push/pp_contract.md (return values of the three calls).

What the three calls are today: inert stubs in csrc/tactical_move.c. `om_command_set_layer` returns 0 for any
input and changes nothing, `om_unit_transition_progress` returns 0.0 for every unit, and
`om_unit_get_target_layer` returns 0 for every unit.

Tick conventions the tests rely on (they come from the plan's own numbers: "a Raider ordered up a layer is on it 20
ticks later (1.0 s) and a Bastion 100 ticks later", "before tick 10 ... from tick 10", at 20 ticks per second):
- an order is issued between steps; the transition begins on the first `om_tactical_step` after it when the target
  layer is open at the unit's position (R-002-01, "begins its transition on the same tick");
- a transition that is first seen (progress > 0) after step s, with duration d ticks (the type's
  layer_transition_time * 20), has progress in (0, 1) after steps s .. s + d - 2 and is settled (progress 0.0, on the
  new layer) after step s + d - 1; so ordered at step 0, begun at s = 1, a Raider (d = 20) is settled after step 20;
- the cross-over is halfway: `om_unit_get_layer` is the old layer after step d/2 - 1 and the new layer after step d/2
  (the Raider's tick 10).
Where an assertion would pin an order of operations inside one tick that the rules do not fix (a hit landing on the
cross-over tick itself, the tick on which a target is dropped), the tests leave that single tick out and say so.
"""
import ctypes
import pathlib
import re

import pytest

from conftest import OMFeature

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
HEADER = REPO_ROOT / "csrc/ouroboros_sim.h"

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION = range(6)
FRIEND, ENEMY = 0, 1
TICK_RATE = 20  # OM_TACTICAL_TICK_RATE

# E-01 Q-004-01 (closed by Westley, 2026-09-13, "as is"): seconds per unit type; ticks = seconds * 20.
DURATION_S = {RAIDER: 1.0, INTERCEPTOR: 1.2, VANGUARD: 2.5, WARDEN: 2.0, BOMBARD: 4.0, BASTION: 5.0}
DURATION_TICKS = {t: round(s * TICK_RATE) for t, s in DURATION_S.items()}
TYPE_NAME = {RAIDER: "raider", INTERCEPTOR: "interceptor", VANGUARD: "vanguard",
             WARDEN: "warden", BOMBARD: "bombard", BASTION: "bastion"}

CANVAS = 2000.0


def layer_count():
    """OM_LAYER_COUNT from the header (A132: the named constant; valid layers are 0 .. count - 1)."""
    m = re.search(r"#define\s+OM_LAYER_COUNT\s+(\d+)", HEADER.read_text())
    assert m, "csrc/ouroboros_sim.h has no OM_LAYER_COUNT (PP-contract has not landed)"
    return int(m.group(1))


def tp(name):
    """Integer value of OM_TP_<name> read from the header's enum om_tac_param (the enum order is not pinned here)."""
    text = HEADER.read_text()
    m = re.search(r"enum\s+(?:om_tac_param\s*)?\{([^{}]*?\bOM_TP_[A-Z0-9_]+[^{}]*?)\}\s*(?:om_tac_param)?\s*;", text, re.S)
    assert m, "csrc/ouroboros_sim.h has no enum om_tac_param (PP-contract has not landed)"
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    nxt = 0
    for item in body.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            key, val = [t.strip() for t in item.split("=", 1)]
            nxt = int(val, 0)
        else:
            key = item
        if key == "OM_TP_" + name:
            return nxt
        nxt += 1
    raise AssertionError(f"OM_TP_{name} is not a member of om_tac_param")


def new_world(world_factory, lib, canvas=None):
    """A tactical world; with `canvas` set to 2000 x 2000 (needed by om_map_block_rect)."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    if canvas:
        assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    return w


def spawn(lib, w, utype, faction, x, y, layer):
    u = lib.om_unit_spawn(w, utype, faction, float(x), float(y), layer)
    assert u != 0, "om_unit_spawn returned id 0"
    return u


def step(lib, w, n=1):
    for _ in range(n):
        lib.om_tactical_step(w)


def set_layer(lib, w, ids, layer):
    """The hard transfer order. `om_command_set_layer` has no list wrapper in conftest, so build the array here."""
    ids = list(ids)
    arr = (ctypes.c_uint32 * max(len(ids), 1))(*ids)
    return lib.om_command_set_layer(w, arr, len(ids), layer)


def snap(lib, w, u):
    """(effective layer, transition progress, target layer, x, y) now."""
    x, y = lib.om_unit_get_pos(w, u)
    return (lib.om_unit_get_layer(w, u), lib.om_unit_transition_progress(w, u),
            lib.om_unit_get_target_layer(w, u), x, y)


def run(lib, w, u, n):
    """Snapshots after each of n steps, index 0 = after step 1. `trace[k - 1]` is the state after step k."""
    out = []
    for _ in range(n):
        lib.om_tactical_step(w)
        out.append(snap(lib, w, u))
    return out


def first_begun(trace):
    """Step number (1-based) after which the unit is first in transition (progress > 0), else None."""
    for k, s in enumerate(trace, start=1):
        if s[1] > 0.0:
            return k
    return None


def block_column(lib, w, layer_lo, layer_hi, x0=500.0, x1=600.0, y_hi=1800.0):
    """Hand-placed terrain: the 100 wu column x0..x1 (one route-grid cell wide), y 0..y_hi, blocked on engine layers
    layer_lo..layer_hi. The rectangle is given strictly inside the cell edges so it covers exactly those cells."""
    assert lib.om_map_block_rect(w, x0 + 10.0, 10.0, x1 - 10.0, y_hi - 10.0, layer_lo, layer_hi) == 0
    # Phase A dependency (om_map_block_rect and the accessibility read are stubs until wave A4): fail on that first,
    # named, so that a red G4 test says whether the wall or the layer change is what is missing.
    for layer in range(layer_lo, layer_hi + 1):
        assert lib.om_map_sample_layer_accessibility(w, (x0 + x1) / 2.0, 400.0, layer) == 0, \
            "the wall is not there: om_map_block_rect / om_map_sample_layer_accessibility are Phase A stubs (wave A4)"
    assert lib.om_map_sample_layer_accessibility(w, x0 - 50.0, 400.0, layer_lo) == 1, \
        "open ground reads 0: om_map_sample_layer_accessibility is a Phase A stub returning 0 (wave A4)"


def accessible(lib, w, x, y, layer):
    return lib.om_map_sample_layer_accessibility(w, x, y, layer)
