# Rule pins: R-087-04@edc84b, R-087-06@2b0850
"""PP-unit: return fire (E-11 S-087, R-087-06; plan Phase A row P6, audit G12).

R-087-06: "Given an idle or attack-moving unit with no target taking damage, When hit, Then it
targets the attacker (return fire); if the attacker is out of range it pursues the attacker as one
engagement of its order and resumes its original point when the pursuit ends (decisions 28 and 30,
E-11 rewrite 2026-10-19; the resume is proved in test_E11_S087_redirect_resumes_original_point.py);
a plain-moving unit and an already-engaged unit ignore incoming
damage for targeting." Plan P6 adds: the attacker chosen is the lowest-id same-layer attacker.
Today return fire runs for idle units only (an attack-moving unit ignores a hit) and the attacker it
picks is the last writer (the highest id when hits arrive in id order).

Method: the hit is delivered with om_unit_deal_damage(attacker, victim, dmg); the attackers are
Supply units, which never fire, so the only hits are the ones the test delivers. The victim is a
Vanguard (range 300, sensor 700) given id 2, and the one step taken is never its own cohort turn, so
a target it holds afterwards can only have come from return fire, not from ordinary acquisition.
Out-of-range idle attackers stand beyond its 700 wu sensor so pursuit (R-087-04) cannot also claim
it. Out-of-range attack-moving attackers stand inside the sensor (beyond range 300): decision 30
point 2 ends a pursuit on the first tick the attacker is not seen, so an unseen attacker would
leave the ordered point as the goal (TD-LAB-REV2-E1b-1, -2).
"""
import pytest

from test_PP_unit_support import SUPPLY, VANGUARD, BASTION, attack_move, dest, spawn, step, target

HIT = 10.0

@pytest.fixture
def world_factory(world_factory, lib):
    """The shared factory, plus the new movement switched on."""
    def make(*args, **kwargs):
        w = world_factory(*args, **kwargs)
        return w
    return make


@pytest.fixture
def world_factory(world_factory, lib):
    """The shared factory, plus the new movement switched on."""
    def make(*args, **kwargs):
        w = world_factory(*args, **kwargs)
        return w
    return make



def _victim(lib, w, state):
    """Vanguard at the origin, id 2 (id 1 is a far-off friendly), in the given state; asserts the
    first step will not be its cohort turn."""
    spawn(lib, w, BASTION, 0, -9000.0, 0.0)
    # Test-defect, A163/A164: first step was the victim's cohort turn (tick 1) -> one idle step before spawning the victim and enemies (the first step is now tick 2, not its turn); cause: aligned targeting cohort (parity with the Python, Addendum 63).
    step(lib, w)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    if state == "attack_move":
        attack_move(lib, w, [u], -3000.0, 0.0)
    elif state == "plain_move":
        lib.om_command_move(w, u, -3000.0, 0.0)
    assert (lib.om_tactical_tick(w) + 1) % 4 != lib.om_unit_targeting_cohort(w, u), "fixture: cohort turn"
    return u


def _far(state, unseen, seen):
    """Out-of-range scene scale: the idle case keeps its unseen (beyond sensor) distance, the
    attack-moving case uses the seen distance so the pursuit it starts is not ended at once."""
    return unseen if state == "idle" else seen


def _hit_in_order(lib, w, victim, attackers):
    for a in attackers:
        lib.om_unit_deal_damage(w, a, victim, HIT)


@pytest.mark.parametrize("state", ["idle", "attack_move"])
def test_R_087_06_hit_unit_targets_an_attacker_in_range(lib, world_factory, state):
    """In range: an idle or attack-moving unit with no target that is hit by an in-range attacker
    targets it, though a nearer enemy stands beside it (that nearer one is not the one that hit it,
    and it is not the unit's cohort turn). Attack-moving fails today: the hit is ignored."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, state)
    nearer = spawn(lib, w, SUPPLY, 1, 0.0, 100.0)
    attacker = spawn(lib, w, SUPPLY, 1, 280.0, 0.0)
    _hit_in_order(lib, w, u, [attacker])

    step(lib, w)

    assert target(lib, w, u) == attacker, (
        f"{state}: hit unit should target its attacker {attacker} (not {nearer}); has {target(lib, w, u)}")


@pytest.mark.parametrize("state", ["idle", "attack_move"])
def test_R_087_06_out_of_range_attacker_becomes_the_new_goal(lib, world_factory, state):
    """Out of range: while the pursuit lasts, the unit's goal is the attacker's place. Idle: attacker
    900 wu away (range 300, sensor 700). Attack-moving: attacker 430 wu away, inside the sensor, so
    it is seen and the pursuit holds (decisions 28 and 30; the old 900 wu scene is unseen)."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, state)
    d = _far(state, 900.0, 430.0)
    attacker = spawn(lib, w, SUPPLY, 1, d, 0.0)
    _hit_in_order(lib, w, u, [attacker])

    step(lib, w)

    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx((d, 0.0), abs=1e-6), (
        f"{state}: goal is ({gx}, {gy}); want the attacker's place ({d}, 0) while the pursuit lasts")


@pytest.mark.parametrize("state", ["idle", "attack_move"])
@pytest.mark.parametrize("hit_order", ["low_first", "high_first"])
def test_R_087_06_lowest_id_same_layer_attacker_in_range(lib, world_factory, state, hit_order):
    """Three same-layer attackers in range, the lowest id the farthest, hit the unit in the same
    tick: it targets the lowest id whichever order the hits arrive in. Today it takes the LAST
    writer, so 'low_first' fails (and 'high_first' passes by coincidence: the control that the
    expected id is reachable)."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, state)
    low = spawn(lib, w, SUPPLY, 1, 290.0, 0.0)
    mid = spawn(lib, w, SUPPLY, 1, 0.0, 200.0)
    high = spawn(lib, w, SUPPLY, 1, -100.0, 0.0)
    assert low < mid < high
    _hit_in_order(lib, w, u, [low, mid, high] if hit_order == "low_first" else [high, mid, low])

    step(lib, w)

    assert target(lib, w, u) == low, f"{state}/{hit_order}: wanted lowest id {low}, got {target(lib, w, u)}"


@pytest.mark.parametrize("state", ["idle", "attack_move"])
@pytest.mark.parametrize("hit_order", ["low_first", "high_first"])
def test_R_087_06_lowest_id_same_layer_attacker_out_of_range(lib, world_factory, state, hit_order):
    """Out of range, the unit pursues the lowest-id same-layer attacker (here also the farthest),
    whichever order the hits arrive in. Idle: attackers beyond the sensor (low at 1000 wu).
    Attack-moving: attackers inside the sensor (low at 650 wu, mid 474, high 461) so all are seen."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, state)
    if state == "idle":
        low_xy, mid_xy, high_xy = (1000.0, 0.0), (800.0, 200.0), (850.0, -100.0)
    else:
        low_xy, mid_xy, high_xy = (650.0, 0.0), (430.0, 200.0), (450.0, -100.0)
    low = spawn(lib, w, SUPPLY, 1, *low_xy)
    mid = spawn(lib, w, SUPPLY, 1, *mid_xy)
    high = spawn(lib, w, SUPPLY, 1, *high_xy)
    assert low < mid < high
    _hit_in_order(lib, w, u, [low, mid, high] if hit_order == "low_first" else [high, mid, low])

    step(lib, w)

    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx(low_xy, abs=1e-6), (
        f"{state}/{hit_order}: goal ({gx}, {gy}), wanted the lowest-id attacker at {low_xy}")


@pytest.mark.parametrize("state", ["idle", "attack_move"])
def test_R_087_06_attacker_on_another_layer_is_passed_over(lib, world_factory, state):
    """The pick is the lowest-id SAME-LAYER attacker: an other-layer attacker with the lowest id
    is passed over for the lowest same-layer one."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, state)
    other_layer = spawn(lib, w, SUPPLY, 1, 250.0, 0.0, layer=1)
    same_a = spawn(lib, w, SUPPLY, 1, 270.0, 0.0)
    same_b = spawn(lib, w, SUPPLY, 1, 0.0, 260.0)
    assert other_layer < same_a < same_b
    _hit_in_order(lib, w, u, [other_layer, same_b, same_a])

    step(lib, w)

    assert target(lib, w, u) == same_a, f"{state}: got {target(lib, w, u)}, wanted lowest same-layer id {same_a}"


def test_control_R_087_06_plain_move_ignores_a_hit(lib, world_factory):
    """Positive control (green today): a plain-moving unit takes the same hit and neither targets
    the attacker nor changes its destination, so the tests above read return fire, not noise."""
    w = world_factory(n_regions=1)
    u = _victim(lib, w, "plain_move")
    attacker = spawn(lib, w, SUPPLY, 1, 280.0, 0.0)
    _hit_in_order(lib, w, u, [attacker])

    step(lib, w)

    assert target(lib, w, u) == -1
    has, gx, gy = dest(lib, w, u)
    assert has == 1 and (gx, gy) == pytest.approx((-3000.0, 0.0), abs=1e-6)
