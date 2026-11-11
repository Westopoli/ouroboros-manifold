"""E-11 S-087 / R-087-03 / R-087-08 (rewritten 2026-11-08, DEC-target-lock-nearest-2026-11-08) / R-087-04 (engine rule fixes 2026-11-08,
F3): a target lock holds.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F3"; evidence docs/reports/2026-11-07-rule-enforcement.md and appendix B
(mutation M6: restoring the re-acquire clause turned no test red, only goldens). Bug fix, not a story. The whole-fight twin is
tests/skilllab/arena/test_engine_rules_f3_lock.py.

Rule words (docs/bible/epics/E-11-*.md as rewritten 2026-11-08): a unit locks the nearest enemy its side sees and keeps the lock until
the target dies, leaves its side's sight, or the unit gets a new order; acquisition runs only while the unit has no lock, at its cohort
turn. The leash (R-087-05) and R-087-09 are their own rules and still break a lock. R-087-04: a unit with a target out of attack range
'walks toward it until the enemy is within attack range'.
Rule pins: R-087-03, R-087-08, R-087-04, R-087-05.

Scene: a 2000 x 2000 canvas, default tactical parameters (pursuit by steering, targeting by sight, nearest-enemy policy), flying units.
The attacker is a Raider (attack range 200, 7.5 wu per tick); enemies are Supplies (never fire, never flee) and one Vanguard (3.5 wu per
tick) ordered to walk away; hp is raised so that nothing dies unless a test kills it. unit.c:2236-2240 re-acquires at a cohort turn when
'pursue && target not in attack range'; that clause is what the red tests catch.

Measured on the unfixed tree (2026-11-08): an attack-moving Raider locks the Vanguard at 146 wu, which walks away east; as the Vanguard passes 200 wu (out
of range) the Raider swaps to the Supply 160 wu away (16 ticks after the lock) and shoots it while the Vanguard walks off (608 wu at tick 120).
Controls green today: the nearest of three is locked; a nearer enemy appearing does not take a lock that is in range; a new order breaks
it; a dead target is replaced by the nearest; a target that leaves sight is dropped and the next nearest visible one taken.

Detector bounds (not rules): ACQUIRE_TICKS 12 (a cohort turn comes within OM_TARGETING_COHORT_COUNT ticks; measured 7), the run lengths.
"""

from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, VANGUARD, attack_move, kill, pos, spawn, step, target

ACQUIRE_TICKS = 12
BIG_HP = 1.0e6


def _none(t):
    """The wrapper reports no target as 0 or -1 depending on the build of the binding; a target id is positive."""
    return t is None or t <= 0


def _world(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    return w


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _tough(lib, w, *ids):
    for u in ids:
        lib.om_unit_set_hp(w, u, BIG_HP)


def _wait_for_lock(lib, w, u, limit=ACQUIRE_TICKS):
    for _ in range(limit):
        step(lib, w)
        if not _none(target(lib, w, u)):
            return target(lib, w, u)
    return None


# ------------------------------------------------------------------ red today

def _fleeing_scene(lib, wf):
    """An attack-moving Raider U at (300,400); a Vanguard V 150 wu east that walks away east (3.5 wu a tick); a Supply S 160 wu south of U
    that never moves. Both enemies are tough. U locks V first (it is the nearer)."""
    w = _world(lib, wf)
    u = spawn(lib, w, RAIDER, 0, 300, 400)
    v = spawn(lib, w, VANGUARD, 1, 450, 400)
    s = spawn(lib, w, SUPPLY, 1, 300, 560)
    _tough(lib, w, v, s)
    lib.om_command_move(w, [v], 1, 1200.0, 400.0)
    attack_move(lib, w, [u], 1800, 400)
    return w, u, v, s


def test_R_087_03_a_locked_target_that_steps_out_of_attack_range_is_not_swapped_for_the_nearest(lib, world_factory):
    """R-087-03 / R-087-08: the lock holds until the target dies, leaves the side's sight, or a new order. Per tick for 120 ticks the unit's
    target is the Vanguard once it has locked it, never the Supply. Red today: 16 ticks after the lock, as the Vanguard passes 200 wu (the
    attack range), the unit swaps to the Supply (unit.c:2236-2240)."""
    w, u, v, s = _fleeing_scene(lib, world_factory)
    assert _wait_for_lock(lib, w, u) == v, "scene broken: the unit did not lock the nearer Vanguard first"
    seen = []
    for _ in range(120):
        step(lib, w)
        seen.append(target(lib, w, u))
    swapped = [i + 1 for i, t in enumerate(seen) if t == s]
    assert not swapped, "target swapped to the Supply at tick(s) %s after the lock (Vanguard %d, Supply %d); targets %s" % (swapped[:3], v, s, sorted(set(seen)))


def test_R_087_04_a_locked_target_that_walks_away_is_chased_until_in_range(lib, world_factory):
    """R-087-04 'walks toward it until the enemy is within attack range': the unit keeps closing on its locked Vanguard. After 120 ticks it
    stands within 2 x its attack range of it (the Vanguard walked 1.5 x its own speed less than the Raider). Red today: the unit
    stands where it swapped, 610 wu behind."""
    w, u, v, s = _fleeing_scene(lib, world_factory)
    step(lib, w, 120)
    d = _dist(pos(lib, w, u), pos(lib, w, v))
    assert d <= 400.0, "the unit is %.0f wu from the target it locked (Vanguard %d), target now %s" % (d, v, target(lib, w, u))


# ------------------------------------------------------------------ green today: what must stay

def test_R_087_03_control_the_nearest_of_three_is_locked(lib, world_factory):
    """R-087-03 / R-087-08 control (green today): an idle Raider with Supplies at 300, 160 and 250 wu locks the one at 160."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, RAIDER, 0, 300, 400)
    far = spawn(lib, w, SUPPLY, 1, 600, 400)
    near = spawn(lib, w, SUPPLY, 1, 460, 400)
    mid = spawn(lib, w, SUPPLY, 1, 300, 650)
    assert _wait_for_lock(lib, w, u) == near, "far %d near %d mid %d" % (far, near, mid)


def test_R_087_03_control_a_nearer_enemy_appearing_does_not_take_a_lock_that_is_in_range(lib, world_factory):
    """R-087-03 control (green today, must stay): U has locked a Supply 160 wu away; another Supply appears 50 wu away. For 100 ticks the lock
    holds (the unit keeps firing at its target)."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, RAIDER, 0, 300, 400)
    first = spawn(lib, w, SUPPLY, 1, 460, 400)
    _tough(lib, w, first)
    assert _wait_for_lock(lib, w, u) == first
    nearer = spawn(lib, w, SUPPLY, 1, 340, 420)
    _tough(lib, w, nearer)
    for t in range(1, 101):
        step(lib, w)
        assert target(lib, w, u) == first, "tick %d: target %s, expected the lock %d (the nearer enemy is %d)" % (t, target(lib, w, u), first, nearer)


def test_R_087_03_control_a_new_order_breaks_the_lock(lib, world_factory):
    """R-087-03 'until ... the unit gets a new order' (control, green today): a locked unit given a new attack-move acquires afresh and
    takes the nearest enemy, a Supply spawned 50 wu away after the lock, within ACQUIRE_TICKS."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, RAIDER, 0, 300, 400)
    first = spawn(lib, w, SUPPLY, 1, 460, 400)
    _tough(lib, w, first)
    assert _wait_for_lock(lib, w, u) == first
    nearer = spawn(lib, w, SUPPLY, 1, 340, 420)
    _tough(lib, w, nearer)
    attack_move(lib, w, [u], 300, 400)
    assert _wait_for_lock(lib, w, u, ACQUIRE_TICKS + 2) == nearer


def test_R_087_03_control_a_dead_target_is_replaced_by_the_nearest_remaining(lib, world_factory):
    """R-087-03 'until the target dies' (control, green today): the lock goes when the target dies and the unit takes the nearest living enemy."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, RAIDER, 0, 300, 400)
    first = spawn(lib, w, SUPPLY, 1, 460, 400)
    second = spawn(lib, w, SUPPLY, 1, 300, 600)
    third = spawn(lib, w, SUPPLY, 1, 800, 400)
    _tough(lib, w, second, third)
    assert _wait_for_lock(lib, w, u) == first
    kill(lib, w, first)
    assert _wait_for_lock(lib, w, u, ACQUIRE_TICKS + 2) == second, "targets: second %d third %d" % (second, third)


def test_R_087_03_control_a_target_that_leaves_the_sides_sight_is_dropped_and_the_next_visible_one_taken(lib, world_factory):
    """R-087-03 'until the target ... leaves its side's sight' (control, green today): a wall built between U and its locked Supply (cell column x 300..400)
    blinds the side to it; within ACQUIRE_TICKS the unit holds the other Supply, which is still visible."""
    w = _world(lib, world_factory)
    u = spawn(lib, w, RAIDER, 0, 260, 400)
    behind = spawn(lib, w, SUPPLY, 1, 440, 400)
    other = spawn(lib, w, SUPPLY, 1, 260, 640)
    _tough(lib, w, behind, other)
    assert _wait_for_lock(lib, w, u) == behind
    assert lib.om_map_block_rect(w, 310.0, 310.0, 390.0, 490.0, 0, 4) == 0
    assert lib.om_player_can_see(w, 0, behind) == 0, "scene broken: the side still sees the Supply behind the wall"
    assert lib.om_player_can_see(w, 0, other) == 1, "scene broken: the side cannot see the other Supply"
    for _ in range(ACQUIRE_TICKS + 2):
        step(lib, w)
    assert target(lib, w, u) == other, "target %s, expected the visible Supply %d" % (target(lib, w, u), other)
