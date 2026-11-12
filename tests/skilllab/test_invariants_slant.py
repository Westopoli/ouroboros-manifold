# Rule pins: R-087-10
"""Engine rules round 2, T8: the checker's `R-087-10` (no shot beyond attack range by slant) knows which units are measured flat. Pure predicates on planted frames; the real
fights are tests/skilllab/ground/test_slope_top_flyer_checker.py.

R-087-10 (docs/bible/epics/E-11-units-and-combat.md): "Given a test of whether a weapon reaches (a unit's attack range to its target, an area attack's radius to each unit it would hit),
When it is evaluated, Then the distance is spherical: the horizontal distance and the height difference between the two units' layers (E-17 R-190-04 band heights) taken together ...".

DRAFT-slant-ground-only (a provisional reading pending the owner's ruling, not rule text; the same one as tests/csim/test_E11_R087_10_spherical_distance.py): the slant is used only when
BOTH units are walking units standing on ground bands. When either unit is a flyer, weapon reach is the horizontal distance and the reach table's range multipliers (1.0 here), as before
Round 2. Reason: the air layers' band floors are about 920 wu apart (measured [60.11, 979.86, 1899.61, 2819.36, 3739.11]), so by slant no flyer could reach a unit on another air layer.

THE API THIS FILE PINS (the checker's implementer builds to it; the test writer's design, the chat may rename):

    Rules.flyers          a set of unit ids whose type moves by flying (om_unit_profile_movement_kind == OM_MOVE_FLYING); default empty: every unit is a walker, which is what
                          the checker did before. The tests SET THE ATTRIBUTE on a built Rules (`r.flyers = {1, 2}`), so a constructor keyword `flyers=None` is the implementer's
                          choice and a Rules without the feature simply ignores it. The Monitor fills it from the engine for each unit it reads.
    R-087-10 violation    a shot (attacker, target) is a violation when its distance exceeds the attacker's attack range plus DRAFT-f7-slant-slack 1.0 wu, where the distance is the
                          slant (horizontal distance and the layer-height difference from Rules.layer_heights) if neither unit is in `flyers`, and the horizontal distance if either is.
                          Swimming units are not asked about (gap in the report).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_invariants import _Module, row, rules, trace  # noqa: E402,F401

GROUND = [70.0, 130.0, 190.0, 250.0, 310.0]          # the hill: layer 1 is 60 wu above layer 0 (tests/csim/test_E11_R087_10_spherical_distance.py `_hill_world`)
AIR = [70.0, 990.0, 1910.0, 2830.0, 3750.0]          # air bands 920 wu apart (measured air bands: about 920)
RANGE = 300.0


@pytest.fixture(scope="module")
def inv():
    return _Module()


def shot(inv, flat, la, lb, heights, flyers=()):
    """Unit 1 (side 0, attack range 300, layer `la`) fires at unit 2 (side 1, layer `lb`) `flat` wu away horizontally in frame 1. `flyers` the ids in Rules.flyers. Returns the R-087-10
    violations as (rule, tick, unit)."""
    units = {1: row(100, 100, layer=la), 2: row(100 + flat, 100, side=1, layer=lb)}
    r = rules(inv, attack_range={1: RANGE}, layer_heights=list(heights))
    r.flyers = set(flyers)
    got = inv.check(trace(units, (units, [(1, 2)])), r, only=["R-087-10"]).violations
    return [(v["rule"], v["tick"], v["unit"]) for v in got]


def test_R_087_10_control_two_walkers_on_a_hill_fire_outside_range_by_slant(inv):
    """R-087-10 (both units walkers on ground bands): layers 1 and 0 (60 wu apart), 297 wu horizontally (inside range 300), 303.0 by slant: the shot is beyond range: a violation. Green today
    and after (the hill case the slant exists for)."""
    assert shot(inv, 297.0, 1, 0, GROUND) == [("R-087-10", 1, 1)]


def test_R_087_10_control_two_walkers_on_a_hill_fire_inside_range_by_slant(inv):
    """R-087-10 control (green today and after): the same walkers 290 wu apart (296.2 by slant): inside range, silent."""
    assert shot(inv, 290.0, 1, 0, GROUND) == []


def test_R_087_10_draft_slant_ground_only_a_flyer_firing_inside_horizontal_range_is_not_a_violation(inv):
    """R-087-10 read DRAFT-slant-ground-only: two flyers on adjacent air layers (2 and 3), 250 wu apart horizontally, about 953 wu by slant, range 300: the shot is inside range by the flat
    measure: silent. Red today: the checker measures every pair by slant and reports a shot 953 wu away."""
    assert shot(inv, 250.0, 2, 3, AIR, flyers={1, 2}) == []


def test_R_087_10_draft_slant_ground_only_a_flyer_above_a_walker_is_measured_flat(inv):
    """R-087-10 read DRAFT-slant-ground-only, 'either unit': a flying shooter (unit 1) on layer 1 at a walking target (unit 2) on layer 0 below it, 250 wu horizontally, 953 by slant: silent.
    Red today."""
    assert shot(inv, 250.0, 1, 0, AIR, flyers={1}) == []


def test_R_087_10_draft_slant_ground_only_a_walker_firing_up_at_a_flyer_is_measured_flat(inv):
    """R-087-10 read DRAFT-slant-ground-only, 'either unit', the other direction: a walking shooter (unit 1) on layer 0 at a flying target (unit 2) on layer 1 above it, 250 wu
    horizontally, 953 by slant: silent. Red today."""
    assert shot(inv, 250.0, 0, 1, AIR, flyers={2}) == []


def test_R_087_10_draft_slant_ground_only_a_flyer_firing_beyond_horizontal_range_is_a_violation(inv):
    """R-087-10 read DRAFT-slant-ground-only, control (green today and after): the same two flyers 350 wu apart horizontally (outside range 300 whichever way it is measured): a violation. The
    flat measure still bounds fire."""
    assert shot(inv, 350.0, 2, 3, AIR, flyers={1, 2}) == [("R-087-10", 1, 1)]


def test_R_087_10_draft_slant_ground_only_a_flyer_on_the_hill_is_measured_flat_too(inv):
    """R-087-10 read DRAFT-slant-ground-only: on the hill's 60 wu step a flying shooter at a walker 297 wu away horizontally (303.0 by slant) fires inside the flat range 300: silent. Red
    today. (The rule is about the kind of unit, not about how high the band step is.)"""
    assert shot(inv, 297.0, 1, 0, GROUND, flyers={1}) == []


def test_R_087_10_draft_slant_ground_only_the_flyers_set_does_not_excuse_a_walker_pair(inv):
    """R-087-10 control (green today and after): a Rules.flyers that names other units (7, 8) leaves the walker pair (1, 2) measured by slant: a violation."""
    assert shot(inv, 297.0, 1, 0, GROUND, flyers={7, 8}) == [("R-087-10", 1, 1)]
