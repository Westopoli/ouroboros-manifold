"""Phase C, step G3 ("Units act on what their side can see"): shared helpers. Holds no tests.

Fence: tests/csim/test_PP_C_g3_*.py. Builders never edit these.

Rules and sources: E-12 R-089-01, R-089-02, R-093-01, R-093-02 (as rewritten for side sight, rulings-2
Addendum 45 A125/A126); E-01 R-004-02 ("its sight"), R-004-04, R-008-04, R-162-05; E-11 R-087-01, R-087-04;
plan docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md (Phase C, G3); brief
docs/northstar/plans/2026-10-02-skill-lab-cascade.md section 5 G3. Layers are engine layers 0 to 4 (A132).

Method notes shared by the files:
- A "target" that must be hit hard and never hit back is a Supply unit given 5,000 hp (om_unit_set_hp
  does not clamp). Supply never fires, so the only damage in a scene is the damage the scene means to test.
- Numbers come from csrc/om_constants.h (roster): Raider range 200 / sensor 800; Interceptor 250 / 1000;
  Bombard 1200 / 300; Bastion 800 / 300. Each scene asserts its own sight geometry with om_unit_can_see
  before it relies on it, so a roster change fails loudly there and not as a false pass.
- "Side" is the faction int; the scenes run both factions 0 and 1 in the siege role (R-093-01: the rule is
  the same for the player's units and the enemy's).
- One tick is one om_tactical_step (1,000 or fewer live units).
"""
import ctypes

from conftest import OMTacParam

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION, SUPPLY, EVACUATION = range(8)

BIG_HP = 5000.0


def spawn(lib, w, utype, faction, x, y, layer=0):
    uid = lib.om_unit_spawn(w, utype, faction, float(x), float(y), layer)
    assert uid != 0, "om_unit_spawn returned id 0"
    return uid


def inert(lib, w, faction, x, y, layer=0):
    """A Supply unit with 5,000 hp: takes any amount of fire in a scene, never fires back."""
    uid = spawn(lib, w, SUPPLY, faction, x, y, layer)
    lib.om_unit_set_hp(w, uid, BIG_HP)
    return uid


def step(lib, w, n=1):
    for _ in range(n):
        lib.om_tactical_step(w)


def hp(lib, w, uid):
    return lib.om_unit_get_hp(w, uid)


def target(lib, w, uid):
    """The unit's target id; <= 0 means none (om_unit_target returns -1 for none)."""
    return lib.om_unit_target(w, uid)


def kill(lib, w, uid):
    lib.om_unit_set_hp(w, uid, 0.0)


def pos(lib, w, uid):
    return (lib.om_unit_position_x(w, uid), lib.om_unit_position_y(w, uid))


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def attack_move(lib, w, ids, x, y):
    ids = list(ids)
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_attack_move(w, arr, len(ids), float(x), float(y))


def can_see(lib, w, observer, tgt):
    lib.om_visibility_compute(w)
    return lib.om_unit_can_see(w, observer, tgt)


def set_param(lib, w, name, value):
    return lib.om_tactical_set_param(w, getattr(OMTacParam, name), float(value))


def get_param(lib, w, name):
    return lib.om_tactical_get_param(w, getattr(OMTacParam, name))


def cohort_cycle(lib, w):
    """One full targeting cohort cycle in ticks: every unit has had its retarget turn within it
    (OM_TP_TARGETING_COHORTS, default 4). G3: a target that leaves the side's visible set is dropped
    'at the next acquisition', so 'dropped' is checked within one cycle."""
    return int(get_param(lib, w, "TARGETING_COHORTS"))


def run_and_watch(lib, w, n, watch_hp_of, watch_target_of=None, target_id=None):
    """Step n ticks; return (list of the watched unit's hp after each tick, True when the unit named by
    watch_target_of ever had target_id as its target after a tick)."""
    hps, held = [], False
    for _ in range(n):
        step(lib, w)
        hps.append(hp(lib, w, watch_hp_of))
        if watch_target_of is not None and target(lib, w, watch_target_of) == target_id:
            held = True
    return hps, held


def siege_scene(lib, w, siege_faction, spotter):
    """A Bombard (range 1200, sensor 300) with an enemy Supply 1,000 wu away: inside its range, far
    outside its sensor (and the Supply's), so nobody on the Bombard's side sees the Supply unless a
    spotter is added. The spotter is an Interceptor (range 250, sensor 1000) 100 wu in front of the
    Bombard: it sees the Supply at 900 and cannot fire at it. Returns (bombard, supply, spotter_or_None)."""
    ef = 1 - siege_faction
    bombard = spawn(lib, w, BOMBARD, siege_faction, 0.0, 0.0)
    supply = inert(lib, w, ef, 1000.0, 0.0)
    spot = spawn(lib, w, INTERCEPTOR, siege_faction, 100.0, 0.0) if spotter else None
    assert can_see(lib, w, bombard, supply) == 0, "fixture: the Bombard must not see the target itself"
    if spot is not None:
        assert can_see(lib, w, spot, supply) == 1, "fixture: the spotter must see the target"
        assert dist(pos(lib, w, spot), pos(lib, w, supply)) > 250.0, "fixture: the spotter must be unable to fire"
    return bombard, supply, spot
