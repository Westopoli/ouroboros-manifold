"""S-019 -- The floor is not safe.

R-019-01 .. R-019-05. Clamp rule: algorithms.md "Apply" (economy floor 8.0
under drift/friction/standard events; conquest bypasses it; all other
fields floor at 0). Event-effect floors (tension 12.0) and the conquest
bypass are E-04/E-05 mechanics with no apply-function in this header's E-02
scope -- see the skipped tests below for the ABI gap.
"""
import pytest

from conftest import OMField, OMTier, OmTraceRow, read_drift, set_region


def test_R_019_01_economy_floor_holds_under_drift(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=8.0,
               tension=100.0, population=0.0)
    lib.om_world_step(w)
    assert lib.om_region_field(w, 0, OMField.ECONOMY) == 8.0


@pytest.mark.skip(
    reason="R-019-02 (conquest may push economy below 8.0, down to 0) needs "
           "a conquest-apply entry point that csrc/ouroboros_sim.h does not "
           "expose -- conquest (ALG-22) is E-04/E-05 scope, not part of this "
           "E-02-only ABI. Cannot be hard-fixtured at this isolation layer."
)
def test_R_019_02_conquest_may_go_below_floor():
    pass


def test_R_019_03_subsistence_at_the_floor(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0,
               tension=0.0, population=50.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.tension_subsist == pytest.approx(0.075, abs=1e-9)
    assert row.population_subsist == pytest.approx(-0.08, abs=1e-9)


@pytest.mark.skip(
    reason="R-019-04's event-floor half (event effects floor tension at "
           "12.0) needs an event-apply entry point csrc/ouroboros_sim.h "
           "does not expose -- events are E-04 scope. Only the drift-alone "
           "half (may fall below 12.0) is testable at this isolation layer; "
           "see test_R_019_04_drift_alone_may_fall_below_twelve below."
)
def test_R_019_04_event_floors_tension_at_twelve():
    pass


def test_R_019_04_drift_alone_may_fall_below_twelve(lib, world_factory):
    w = world_factory(n_regions=1)
    # High economy (prosperity) makes the economic term strongly negative;
    # nothing here is an event, so no 12.0 floor should ever engage.
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=90.0,
               tension=20.0, population=50.0)
    lib.om_trace_enable(w, 1)
    ran = lib.om_world_run(w, 300)
    assert ran == 300

    n = lib.om_trace_len(w)
    rows = (OmTraceRow * n)()
    got = lib.om_trace_read(w, 0, n, rows)
    assert got == n

    tensions = [r.tension for r in rows]
    assert min(tensions) < 12.0, "drift alone never pushed tension below 12.0"
    assert min(tensions) >= 0.0, "tension went negative; the general [0,100] clamp is not holding"


def test_R_019_05_population_never_goes_negative(lib, world_factory):
    w = world_factory(n_regions=1)
    # population near zero with economy at the floor: decline is independent
    # of population size, so an unclamped step would go negative.
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=8.0,
               tension=0.0, population=0.5)
    for _ in range(10):
        lib.om_world_step(w)
        assert lib.om_region_field(w, 0, OMField.POPULATION) >= 0.0
    assert lib.om_region_field(w, 0, OMField.POPULATION) == 0.0


def test_R_019_05_military_never_goes_negative(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=0.0,
               tension=0.0, population=0.0)
    lib.om_world_step(w)
    assert lib.om_region_field(w, 0, OMField.MILITARY) == 0.0
