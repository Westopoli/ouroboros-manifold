"""LAB-REV2-E1 -- an attack-move group resumes toward its point after every engagement (E-13 S-096, R-096-02).

R-096-02 (rewritten 2026-10-13, Westley, option (a)): "after every fight the group resumes toward the
point as a unit attack-moved alone does ... an attack-move is not finished until the unit reaches its
point". The engine today ends a group once every living member has engaged and never resumes it
(csrc/unit.c, om_tac_am_group_done inside om_tac_release). Measured 2026-10-13: two groups attack-moved
to one point stalled 303 to 336 wu apart with range 300, while the same units ordered one by one fought
to elimination. Spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, ruling 6 and the E1 row.

What is here
  - the stall scene (8 Vanguards and 8 Raiders per side, the blobs 600 wu apart, both sides attack-moved
    to the midpoint as GROUP orders) ends by elimination (S-096 / R-096-02) -- red today;
  - the control (green today): the same scene, one attack-move per unit, ends by elimination;
  - an isolation test: a group member resumes toward its point after it kills its target -- red today;
  - an integration test: the whole scene, ticked to the end with a cap, one side wiped out and the run
    ending by elimination rather than by the stalemate break -- red today.
The scene numbers (8 and 8, 600 wu, midpoint) are the ones the spec's E1 row names; the blob shape
and radius (the lab's objective scene, Vanguards and Raiders alternating along the spiral) are the scene's,
not a rule threshold. No tolerance is asserted. Measured on the unmodified tree: the group-ordered scene
stalls with both factions alive for each of three type orders tried (V then R, R then V, alternating); the
per-unit scene eliminates for all three. The alternating scene used here stalls with 2 and 6 survivors, the
nearest pair 301.7 wu apart (range 300), and every survivor without a goal.

Superseded by R-096-02 (2026-10-13) -- tests that encode the ruling "once every member of the group has
engaged, the group ends and its members do not resume the march" (the engine clause of the Architect,
A124 build). NOT edited here; the E1 landing clerk retires or rewrites them under a ledger row quoting
R-096-02:
  1. tests/csim/test_PP_move_group.py::test_R_096_02_group_ends_when_every_member_has_engaged_and_does_not_resume
  2. tests/csim/test_PP_unit_attack_move_group.py::test_R_096_02_group_ends_when_every_member_has_engaged
  3. tests/csim/test_PP_unit_attack_move_group.py::test_control_R_096_02_group_goes_on_while_a_member_has_not_engaged
     (the spec row says "and its control"; it is the control of test 2 and states the group-end ruling in
     its docstring. Its assertion, that the engaged member resumes while another has not engaged, stays
     true under the new ruling, so it should stay green; the clerk decides if it is kept or retired.)
Docstrings that quote the old wording (no assertion depends on them): the module docstrings of
tests/csim/test_PP_move_group.py (its "A unit attack-moved alone is not a group" line stays true) and
tests/csim/test_PP_unit_attack_move_group.py ("once every member of the group has engaged, the group
ends"), the section comment "the group ends / the lone unit resumes" in the former, and the "# ---- the
group ends once every member has engaged" comment in the latter. The grep for am_group_done / group_ends /
"group ends" found no other test, parity file or .gd test that asserts the old ruling.
tests/csim/parity/ baselines are not touched here; the E1 landing re-records them under the ledger row.
"""
import math

import pytest

from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, attack_move, dest, kill, pos, spawn, step, target

SEP = 600.0                       # blob separation named by the spec's E1 row
MID = (0.0, 0.0)                  # the shared attack-move point: the midpoint between the blob centres at +-300
PER_TYPE = 8
CAP_TICKS = 12000                 # the lab's max_ticks for a bug detector (spec: Setup.max_ticks); not a result
_GOLDEN_ANGLE = 2.399963229728653


def _blob_points(n, x, y, radius):
    """n points of the lab's blob formation (scripts/skilllab/formations.py, a Fermat spiral and its reflection),
    reproduced here so the test does not import the lab, which this piece does not own."""
    pairs = n // 2
    out = [(x, y)] if n % 2 else []
    for i in range(pairs):
        d = radius * math.sqrt((i + 0.5) / pairs)
        a = i * _GOLDEN_ANGLE
        out.append((x + d * math.cos(a), y + d * math.sin(a)))
        out.append((x - d * math.cos(a), y - d * math.sin(a)))
    return out


def _blob(lib, w, faction, cx):
    """A blob of 8 Vanguards and 8 Raiders (alternating along the spiral) centred on (cx, 0). The radius 128 is the
    lab's objective-scene radius for 16 units, 80 + 12 * sqrt(16); it is the scene's, not a rule threshold."""
    pts = _blob_points(2 * PER_TYPE, cx, 0.0, 128.0)
    return [spawn(lib, w, (VANGUARD, RAIDER)[i % 2], faction, x, y) for i, (x, y) in enumerate(pts)]


def _scene(lib, w):
    """The 2026-10-13 stall scene: side 0 centred at x = -300, side 1 at x = +300, 600 wu apart."""
    return _blob(lib, w, 0, -SEP / 2.0), _blob(lib, w, 1, SEP / 2.0)


def _alive(lib, w, ids):
    return sum(1 for u in ids if lib.om_unit_get_hp(w, u) > 0.0)


def _order_as_groups(lib, w, west, east):
    attack_move(lib, w, west, *MID)
    attack_move(lib, w, east, *MID)


def _order_per_unit(lib, w, west, east):
    for u in west + east:
        attack_move(lib, w, [u], *MID)


def _eliminated(lib, w, west, east):
    return min(_alive(lib, w, west), _alive(lib, w, east)) == 0


def _both_alive_line(lib, w, west, east, ticks):
    return (f"om_tactical_run_until_eliminated returned after {ticks} ticks with both factions alive "
            f"(side 0: {_alive(lib, w, west)} of {len(west)}, side 1: {_alive(lib, w, east)} of {len(east)})")


def test_S096_R_096_02_two_attack_moved_groups_fight_to_elimination(lib, world_factory):
    """S-096 / R-096-02: two groups of 16 (8 Vanguards and 8 Raiders each), 600 wu apart, both attack-moved to
    the midpoint as GROUP orders, fight until one side is eliminated. Red today: each member engages once, the
    group ends, nobody resumes, and the sides stall just out of range with both factions alive."""
    w = world_factory(n_regions=1)
    west, east = _scene(lib, w)
    _order_as_groups(lib, w, west, east)

    ticks = lib.om_tactical_run_until_eliminated(w)

    assert _eliminated(lib, w, west, east), _both_alive_line(lib, w, west, east, ticks)


def test_control_S096_R_096_02_one_attack_move_per_unit_fights_to_elimination(lib, world_factory):
    """Positive control (green today): the same scene with one attack-move per unit (each unit is its own
    group of one and resumes after every fight) ends by elimination. Shows the scene can be won and that the
    elimination check can tell a finished fight from a stall."""
    w = world_factory(n_regions=1)
    west, east = _scene(lib, w)
    _order_per_unit(lib, w, west, east)

    ticks = lib.om_tactical_run_until_eliminated(w)

    assert _eliminated(lib, w, west, east), _both_alive_line(lib, w, west, east, ticks)


def _engage_pair(lib, w):
    """Two Raiders attack-moved together toward (3000, 50), each beside its own Supply target (a unit that never
    fires, so the end of the fight is exact). Returns (a, b, sa, sb) once both have held a target."""
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    b = spawn(lib, w, RAIDER, 0, 0.0, 100.0)
    sa = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    sb = spawn(lib, w, SUPPLY, 1, 150.0, 100.0)
    attack_move(lib, w, [a, b], 3000.0, 50.0)
    for _ in range(8):
        step(lib, w)
        if target(lib, w, a) == sa and target(lib, w, b) == sb:
            return a, b, sa, sb
    pytest.fail("fixture: both members should have engaged within 8 ticks")


def test_S096_R_096_02_a_group_member_resumes_toward_its_point_after_its_target_dies(lib, world_factory):
    """Isolation, S-096 / R-096-02: both members of an attack-move group have engaged and both targets die; each
    member marches on toward the group's point (it has a goal again and moves along +x) as a lone unit does.
    Red today: the group ends, positions stay put and no member has a goal."""
    w = world_factory(n_regions=1)
    a, b, sa, sb = _engage_pair(lib, w)
    kill(lib, w, sa)
    kill(lib, w, sb)
    x0 = {a: pos(lib, w, a)[0], b: pos(lib, w, b)[0]}

    step(lib, w, 30)      # past the 10 tick backswing a first shot leaves, so "not moving" is not a pause

    for u in (a, b):
        assert pos(lib, w, u)[0] > x0[u], f"member {u} did not resume toward the point after its target died"
        assert dest(lib, w, u)[0] == 1, f"member {u} has no goal after its target died: the group ended"


def test_control_S096_R_096_02_a_lone_unit_resumes_toward_its_point_after_its_target_dies(lib, world_factory):
    """Positive control for the isolation test (green today): the same fight with one Raider attack-moved alone;
    it resumes toward (3000, 50) after its target dies, so the isolation test's check can tell a march from a halt."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    sa = spawn(lib, w, SUPPLY, 1, 150.0, 0.0)
    attack_move(lib, w, [a], 3000.0, 50.0)
    for _ in range(8):
        step(lib, w)
        if target(lib, w, a) == sa:
            break
    assert target(lib, w, a) == sa, "fixture: the lone unit should have engaged"
    kill(lib, w, sa)
    x0 = pos(lib, w, a)[0]

    step(lib, w, 30)

    assert pos(lib, w, a)[0] > x0
    assert dest(lib, w, a)[0] == 1


def test_S096_R_096_02_integration_whole_scene_ticked_to_one_side_wiped_out(lib, world_factory):
    """Integration, S-096 / R-096-02: the whole stall scene as group orders, ticked one step at a time (not
    through om_tactical_run_until_eliminated, whose stalemate break could end the run early) until one side has
    no living unit or the 12000 tick cap passes. The cap is a bug detector only: reaching it is a failure.
    Red today: the sides stall out of range and the cap is reached with both factions alive."""
    w = world_factory(n_regions=1)
    west, east = _scene(lib, w)
    _order_as_groups(lib, w, west, east)

    ticks = 0
    while ticks < CAP_TICKS and not _eliminated(lib, w, west, east):
        step(lib, w)
        ticks += 1

    assert _eliminated(lib, w, west, east), (
        f"the cap of {CAP_TICKS} ticks passed with both factions alive "
        f"(side 0: {_alive(lib, w, west)} of {len(west)}, side 1: {_alive(lib, w, east)} of {len(east)})")
