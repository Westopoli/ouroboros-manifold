"""PP-unit: the first shot (E-11 S-084, R-084-01; plan Phase A row P2, audit G09).

R-084-01: "a unit's first attack is ready on the tick its target is first in range" (no full
interval wait after spawn). Today the attack timer (`cooldown`) starts at 0 and must reach the
interval, so a unit spawned in range waits one interval (Vanguard 1.2 s = 24 ticks) before its
first hit.

Measure: step one tick at a time; the tick the unit first holds the target is the tick the target
is first in range for it (a spawn-in-range fixture has no earlier tick). The first hit must land on
that same step.
"""
import pytest

from test_PP_unit_support import SUPPLY, VANGUARD, RAIDER, hp, spawn, step, target

@pytest.fixture
def world_factory(world_factory, lib):
    """The shared factory, plus the new movement switched on."""
    def make(*args, **kwargs):
        w = world_factory(*args, **kwargs)
        # PP: runs the new movement (switch default 0, A147 option c')
        lib.om_tactical_set_param(w, 0, 1.0)
        return w
    return make



def _first_acquire_and_first_hit(lib, w, attacker, victim, max_steps=60):
    """(step the attacker first holds the victim, step the victim's hp first drops); None if never."""
    start_hp = hp(lib, w, victim)
    acquired = hit = None
    for i in range(1, max_steps + 1):
        step(lib, w)
        if acquired is None and target(lib, w, attacker) == victim:
            acquired = i
        if hit is None and hp(lib, w, victim) < start_hp:
            hit = i
        if acquired is not None and hit is not None:
            break
    return acquired, hit


def test_R_084_01_first_shot_lands_on_the_tick_the_target_is_first_in_range(lib, world_factory):
    """R-084-01: a unit spawned with its target already in range fires on the tick it first holds
    that target, not one attack interval later. Vanguard at 250 wu (range 300); the target is a
    Supply unit (never fires back, so nothing else moves hp)."""
    w = world_factory(n_regions=1)
    attacker = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    victim = spawn(lib, w, SUPPLY, 1, 250.0, 0.0)

    acquired, hit = _first_acquire_and_first_hit(lib, w, attacker, victim)

    assert acquired is not None and acquired <= 4, "attacker never acquired an in-range target"
    assert hit == acquired, (
        f"first hit landed on step {hit}, target first held on step {acquired}: "
        "R-084-01 wants the first attack ready on the tick the target is first in range")


def test_R_084_01_first_shot_each_unit_of_a_line(lib, world_factory):
    """R-084-01 across the cohort stagger (a unit acquires on its own tick of four): four Raiders
    spawned in range of four separate targets each hit on the step they first hold their target."""
    w = world_factory(n_regions=1)
    pairs = []
    for i in range(4):
        a = spawn(lib, w, RAIDER, 0, 0.0, 100.0 * i)
        v = spawn(lib, w, SUPPLY, 1, 150.0, 100.0 * i)
        pairs.append((a, v))
    start = {v: hp(lib, w, v) for _, v in pairs}
    acquired = {}
    hit = {}
    for i in range(1, 25):
        step(lib, w)
        for a, v in pairs:
            if a not in acquired and target(lib, w, a) == v:
                acquired[a] = i
            if v not in hit and hp(lib, w, v) < start[v]:
                hit[v] = i
    for a, v in pairs:
        assert a in acquired, f"unit {a} never held a target"
        assert hit.get(v) == acquired[a], (
            f"unit {a}: acquired on step {acquired[a]}, first hit on step {hit.get(v)}")


def test_control_R_084_01_detector_sees_a_hit_on_the_acquisition_step(lib, world_factory):
    """Positive control for the two tests above (must pass today): a Vanguard that has idled for a
    full interval before its target appears does hit on the step it first holds it, so the
    measure `hit == acquired` can be true and the failures above are not an artefact of it."""
    w = world_factory(n_regions=1)
    attacker = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    victim = spawn(lib, w, SUPPLY, 1, 5000.0, 0.0)          # far outside sensor range 700
    step(lib, w, 30)                                          # attack timer fully charged (24 ticks)
    lib.om_unit_teleport(w, victim, 250.0, 0.0, 0)

    acquired, hit = _first_acquire_and_first_hit(lib, w, attacker, victim)

    assert acquired is not None and hit == acquired
