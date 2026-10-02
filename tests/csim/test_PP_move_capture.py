"""PP-capture rule tests, the capture census (P9).

Proves E-15 R-127-01 and R-127-02 (S-127), plan Phase A row P9: each tick, per structure, the units within 300 wu
are counted; exactly one non-owner faction present and no owner unit starts, or continues, a 10 s capture; two or
more non-owner factions, or the owner present, keep progress at 0. The census is computed by the tick itself.

The existing tests in test_E15_S127_taking_a_garrison.py feed the census by hand
(`om_structure_set_capturing_faction`, `om_structure_set_contested`, `om_structure_tick_capture`) and so test the
state machine, not the rule; nothing here calls a setter, a caller that does not exist in play is exactly the
defect (docs/northstar/research/layer_dynamics/port_gap_audit_2026-10-02.md, G21).

Reference: simulation/reinforcement.py 23-81. 10 s at 20 ticks per second is 200 ticks; one tick adds 0.005.
Scenes keep opposing units 400 wu apart (Raider range 200) so no fight kills a unit during the run.
"""
import pytest

from conftest import OMFeature

RAIDER = 0
SX, SY = 1000.0, 1000.0   # the structure
CAPTURE_RADIUS = 300.0
TICKS_FOR_HALF = 100
TICKS_FOR_FULL = 200
PROGRESS_TOL = 1e-3       # the tolerance the existing R-127-01 test uses


@pytest.fixture
def tw(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _structure(lib, w, owner):
    lib.om_structure_init(w, 0, RAIDER, 100.0)
    lib.om_structure_set_position(w, 0, SX, SY)
    lib.om_structure_set_owner(w, 0, owner)


def _unit(lib, w, faction, dx, dy=0.0):
    return lib.om_unit_spawn(w, RAIDER, faction, SX + dx, SY + dy, 0)


def _run(lib, w, n):
    for _ in range(n):
        lib.om_tactical_step(w)


def _progress(lib, w):
    return lib.om_structure_get_capture_progress(w, 0)


@pytest.mark.parametrize("owner", [2, -1], ids=["owned_by_another_faction", "neutral"])
def test_R_127_01_exactly_one_nonowner_faction_captures_in_10_s(lib, tw, owner):
    """R-127-01: units of exactly one non-owner faction inside the 300 wu radius and no owner units: progress rises
    by dt / 10 s each tick (0.5 after 100 ticks); at 1.0 the owner flips and progress resets. Faction 1's Raider
    stands 200 wu west of the structure; no setter is called. The C leaves progress at 0 forever, because nothing
    runs the census."""
    _structure(lib, tw, owner)
    _unit(lib, tw, 1, -200.0)
    _run(lib, tw, 1)
    assert _progress(lib, tw) == pytest.approx(0.005, abs=PROGRESS_TOL), "census did not run on the first tick"
    _run(lib, tw, TICKS_FOR_HALF - 1)
    assert _progress(lib, tw) == pytest.approx(0.5, abs=PROGRESS_TOL)
    assert lib.om_structure_get_owner(tw, 0) == owner
    _run(lib, tw, TICKS_FOR_FULL - TICKS_FOR_HALF)
    assert lib.om_structure_get_owner(tw, 0) == 1, "the owner did not flip at 10 s"
    assert _progress(lib, tw) == pytest.approx(0.0, abs=PROGRESS_TOL)


def test_R_127_01_capture_runs_from_the_world_tick(lib, tw):
    """R-127-01 (wired): the census is reachable from om_world_step, the game's tick, not only from a direct
    om_tactical_step call. 100 world steps, one Raider of faction 1 at 200 wu: progress 0.5."""
    _structure(lib, tw, 2)
    _unit(lib, tw, 1, -200.0)
    for _ in range(TICKS_FOR_HALF):
        lib.om_world_step(tw)
    assert _progress(lib, tw) == pytest.approx(0.5, abs=PROGRESS_TOL)


@pytest.mark.parametrize("dx,expect", [(-290.0, 0.25), (-310.0, 0.0)], ids=["inside_290", "outside_310"])
def test_R_127_01_radius_is_300_wu(lib, tw, dx, expect):
    """R-127-01: only units within the 300 wu radius count. A Raider 290 wu away captures (progress 0.25 after 50
    ticks, the positive control); one 310 wu away does not (progress stays 0)."""
    _structure(lib, tw, 2)
    _unit(lib, tw, 1, dx)
    _run(lib, tw, 50)
    assert _progress(lib, tw) == pytest.approx(expect, abs=PROGRESS_TOL)


def test_R_127_01_dead_units_do_not_count(lib, tw):
    """R-127-01: only living units are present. The faction 1 Raider is killed (hp 0) before the first tick: no
    progress. (Python: `if not store.alive[uid]: continue`.)"""
    _structure(lib, tw, 2)
    u = _unit(lib, tw, 1, -200.0)
    lib.om_unit_set_hp(tw, u, 0.0)
    assert lib.om_unit_alive(tw, u) == 0
    _run(lib, tw, 30)
    assert _progress(lib, tw) == 0.0


@pytest.mark.parametrize("owner", [3, -1], ids=["owner_absent_from_the_field", "neutral"])
def test_R_127_02_two_nonowner_factions_present_never_capture(lib, tw, owner):
    """R-127-02: units of two or more non-owner factions inside: progress stays 0 and the owner does not flip, over
    well more than the 200 ticks a lone faction needs. Factions 1 and 2 each stand 200 wu from the structure, on
    opposite sides (400 wu apart, out of each other's range). Positive control: the test above, where faction 1
    alone captures in 200 ticks."""
    _structure(lib, tw, owner)
    _unit(lib, tw, 1, -200.0)
    _unit(lib, tw, 2, 200.0)
    for _ in range(25):
        _run(lib, tw, 10)
        assert _progress(lib, tw) == 0.0
    assert lib.om_structure_get_owner(tw, 0) == owner


def test_R_127_02_the_owner_present_blocks_capture(lib, tw):
    """R-127-02: the owner also present resets/blocks: owner faction 2 and challenger faction 1 are both inside, so
    progress stays 0 and the owner keeps the structure for 250 ticks."""
    _structure(lib, tw, 2)
    _unit(lib, tw, 1, -200.0)
    _unit(lib, tw, 2, 200.0)
    for _ in range(25):
        _run(lib, tw, 10)
        assert _progress(lib, tw) == 0.0
    assert lib.om_structure_get_owner(tw, 0) == 2


def test_R_127_02_a_second_faction_arriving_resets_progress_to_zero(lib, tw):
    """R-127-02 (progress resets to 0): faction 1 alone captures for 50 ticks (0.25); faction 2 then arrives inside the
    radius; on the next tick progress is 0 again and stays 0. Detector control: without the second faction progress
    would be 0.255."""
    _structure(lib, tw, 3)
    _unit(lib, tw, 1, -200.0)
    _run(lib, tw, 50)
    assert _progress(lib, tw) == pytest.approx(0.25, abs=PROGRESS_TOL), "R-127-01: no capture progress built up before the second faction arrived"
    _unit(lib, tw, 2, 200.0)
    _run(lib, tw, 1)
    assert _progress(lib, tw) == 0.0
    _run(lib, tw, 20)
    assert _progress(lib, tw) == 0.0
