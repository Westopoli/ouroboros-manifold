"""The seer, shared sight and no blind fire (SPEC.md 5.2, 5.4, 5.11a; E-01 R-008-04, R-005; register
Q-E12-01 closed (a): a roster unit, wide cross-layer sight, no attack).

SPEC 5.4: a unit whose type has `dmg == 0` and no ability never acquires. Its target, aim and chase stay
-1, it is never counted as able to fire (5.11a), and it moves only by MOVE orders or a spawn transfer.
It still counts in `alive_ticks`, and it is an ordinary target for the other side. A side's units
share vision (`side_sees`): a seer's sight lets its friends fire at what only the seer can see.

Numbers: seer sensor 1500, so it sees across one layer to 1500 * 0.5 = 750 and across two layers to
1500 * 0.2 = 300 (default vis table); a raider (sensor 800) sees across one layer to 400. Spawn jitter 0.
"""
import numpy as np
import pytest

import layerlab.run as runmod
from conftest import add_type, grp, make_scenario, table9, unit_trace

BIG = 1.0e6
CROSS = table9(m1=1, z=1, p1=1)      # cross-layer range and damage for one layer either way


def can_fire(res, i):
    """Per-tick bool array: trace flag bit4 (unit can fire this tick, SPEC 5.11a)."""
    return (res.trace[:, i]["flags"].astype(np.uint8) & 16) != 0


def _types(scn):
    """Durable test types: `tank` (raider that does not die), `seer` made unkillable, `seer_r300` a seer with
    a non-zero range (so only `dmg == 0` can keep it from acquiring), `armed` the same with dmg 1 (control)."""
    add_type(scn, "tank", "raider", hp=BIG)
    scn["types"]["seer"] = {**scn["types"]["seer"], "hp": BIG}
    add_type(scn, "seer_r300", "seer", range=300.0)
    add_type(scn, "armed", "seer", range=300.0, dmg=1.0)
    return scn


# ---- F: a zero-damage unit never fires, never acquires, never chases ------------------------------

def _solo(a_type, *, order="hold", goal=None, rules=None, enemy_x=2100.0, ticks=120):
    """A: one `a_type` at (2000, 1000) on layer 3. B: a tank at (enemy_x, 1000) on layer 3, hold."""
    ga = {"order": order}
    if goal is not None:
        ga["goal"] = list(goal)
    scn = make_scenario(
        [grp("A", a_type, 2000.0, 1000.0, 3, **ga), grp("B", "tank", enemy_x, 1000.0, 3)],
        rules={"spawn_jitter": 0.0, **(rules or {})}, run={"max_ticks": ticks, "stalemate_ticks": 6000})
    _types(scn)
    return scn, runmod.run(scn, seed=0, trace=True)


@pytest.mark.parametrize("a_type", ["seer", "seer_r300"])
def test_a_seer_never_acquires_or_fires(a_type):
    """SPEC 5.4 / 5.11a, Q-E12-01 (a): a seer 100 from a visible enemy on its layer never fires: side shots
    0, damage 0, firing_ticks 0, trace bit4 and bit1 never set, though it is alive every tick. `seer` has range
    0; `seer_r300` has range 300 and so is in reach of the enemy, which isolates `dmg == 0` as the cause. The
    enemy tank fires at it throughout (positive control: the detector sees firing_ticks and bit4)."""
    scn, res = _solo(a_type)
    assert res.shots[0] == 0 and res.damage_dealt[0] == 0.0
    assert res.firing_ticks[0] == 0 and res.firing_weight[0] == 0.0
    assert not can_fire(res, 0).any() and not unit_trace(res, 0).fired.any()
    assert res.alive_ticks[0] == res.ticks
    assert res.shots[1] > 0 and res.firing_ticks[1] == res.ticks
    assert can_fire(res, 1).all()


def test_an_armed_twin_of_the_seer_does_fire():
    """SPEC 5.4 positive control for the test above: the same type with dmg 1.0 (and range 300) acquires the
    enemy at once: firing_ticks equals the tick count, bit4 set every tick, shots and damage both non-zero."""
    scn, res = _solo("armed")
    assert res.firing_ticks[0] == res.ticks and can_fire(res, 0).all()
    assert res.shots[0] > 0 and res.damage_dealt[0] > 0.0


def _with_seer(seer_type):
    """A: tank at (2000, 1000) layer 3, B: tank at (2100, 1000) layer 3; A's seer (listed last so no RNG draw of
    another unit moves) at (1950, 1000), 150 from B, so B's nearest target stays A's tank. Nobody can die."""
    groups = [grp("A", "tank", 2000.0, 1000.0, 3), grp("B", "tank", 2100.0, 1000.0, 3)]
    if seer_type:
        groups.append(grp("A", seer_type, 1950.0, 1000.0, 3))
    scn = make_scenario(groups, rules={"spawn_jitter": 0.0}, run={"max_ticks": 100, "stalemate_ticks": 6000})
    _types(scn)
    return runmod.run(scn, seed=0, trace=True)


@pytest.mark.parametrize("seer_type", ["seer", "seer_r300"])
def test_a_seer_is_excluded_from_firing_ticks_but_counted_alive(seer_type):
    """SPEC 5.11a: a side with one tank and one seer has the firing_ticks of the tank alone (the seer never
    can fire), and alive_ticks of both. Compared with the same fight without the seer: firing_ticks, shots,
    damage and the enemy's remaining hp are identical, alive_ticks doubles (2 x ticks), and the seer's bit4
    is never set while the tank's is."""
    solo, duo = _with_seer(None), _with_seer(seer_type)
    assert solo.ticks == duo.ticks == 100
    assert solo.firing_ticks[0] == solo.ticks and solo.alive_ticks[0] == solo.ticks
    assert duo.firing_ticks[0] == solo.firing_ticks[0], "the seer was counted as able to fire"
    assert duo.firing_weight[0] == solo.firing_weight[0]
    assert duo.alive_ticks[0] == 2 * duo.ticks, "the seer must still count in alive_ticks"
    assert duo.shots == solo.shots and duo.damage_dealt == solo.damage_dealt
    assert duo.unit[1]["hp"] == solo.unit[1]["hp"]
    assert can_fire(duo, 0).all() and not can_fire(duo, 2).any()


@pytest.mark.parametrize("order,chase", [("attack_move", 0), ("hold", 1)])
def test_a_seer_does_not_chase(order, chase):
    """SPEC 5.4 / 5.10: under ATTACK_MOVE (goal = its own spot, so it has arrived) or under HOLD with
    chase_when_idle on, a seer 600 from a visible enemy never moves toward it: x and y never change.
    Positive control: an armed twin (dmg 1.0) with the same order and rules does chase, closing to its range."""
    kw = dict(order=order, goal=(2000.0, 1000.0), rules={"chase_when_idle": chase}, enemy_x=2600.0, ticks=200)
    _, res = _solo("seer_r300", **kw)
    ut = unit_trace(res, 0)
    assert np.allclose(ut.x, 2000.0) and np.allclose(ut.y, 1000.0)
    assert not can_fire(res, 0).any()
    _, ctl = _solo("armed", **kw)
    # The enemy chases too (chase_when_idle is global), so the two meet after the armed unit has moved only
    # about 112 units (it stops once the enemy is within its range 300); 2050 is far above the seer's 2000.
    assert unit_trace(ctl, 0).x[-1] > 2050.0, "the control did not chase: the test above proves nothing"


def test_a_seer_goes_where_move_sends_it_and_then_stays():
    """SPEC 5.4 ('moves only by MOVE orders'): a seer with a MOVE order 400 north arrives within 30 units and
    stays there (no chase of the visible enemy 600 east), firing nothing. Positive control that the seer type
    can move at all, so the no-chase tests are not satisfied by a unit that never moves."""
    goal = (2000.0, 1400.0)
    _, res = _solo("seer_r300", order="move", goal=goal, enemy_x=2600.0, ticks=250)
    ut = unit_trace(res, 0)
    assert np.hypot(ut.x[-1] - goal[0], ut.y[-1] - goal[1]) <= 30.0
    assert np.hypot(ut.x[-10] - goal[0], ut.y[-10] - goal[1]) <= 30.0
    assert res.shots[0] == 0 and not can_fire(res, 0).any()


# ---- G: shared sight, positive and negative twins (R-008-04, S-005) -------------------------------

def _sight(seer=None):
    """A: a sniper (range 600, sensor 800) on layer 4 at (2000, 1000). B: a sniper on layer 3 at (2450, 1000), 450
    away: one layer apart a sensor-800 unit sees 400, so neither raider sees the other. Cross-layer range and
    damage on for one layer. `seer` is (layer, distance from B along -x) or None: A's seer at that spot.
    Groups: A sniper (0), B sniper (1), A seer (2). Everybody holds. Returns (scn, result)."""
    groups = [grp("A", "sniper", 2000.0, 1000.0, 4), grp("B", "sniper", 2450.0, 1000.0, 3)]
    if seer:
        layer, d = seer
        groups.append(grp("A", "seer", 2450.0 - d, 1000.0, layer))
    scn = make_scenario(groups, rules={"spawn_jitter": 0.0, "range_mult": CROSS, "dmg_mult": CROSS},
                        run={"max_ticks": 100, "stalemate_ticks": 6000})
    add_type(scn, "sniper", "raider", range=600.0, hp=BIG)
    scn["types"]["seer"] = {**scn["types"]["seer"], "hp": BIG}
    return scn, runmod.run(scn, seed=0, trace=True)


def test_without_a_seer_a_layer_apart_raider_cannot_fire_at_what_it_cannot_see():
    """R-008-04 / S-005 (negative twin): the sniper on layer 4 has range 600 and the target on layer 3 is 450
    away, in reach, but sensor 800 * 0.5 = 400 does not reach it. No side sees any unit, nobody can fire
    (bit4 never set), zero shots, zero damage, first_contact_tick -1 (no blind fire)."""
    scn, res = _sight()
    assert not runmod.probe_can_see(scn, 0, 1) and not runmod.probe_can_see(scn, 1, 0)
    assert res.shots == (0, 0) and res.damage_dealt == (0.0, 0.0) and res.firing_ticks == (0, 0)
    assert res.first_contact_tick == -1
    assert not can_fire(res, 0).any() and not unit_trace(res, 1).visible.any()


@pytest.mark.parametrize("layer,d,sees", [
    (4, 700.0, True),     # one layer apart: 1500 * 0.5 = 750 reaches the target
    (4, 800.0, False),    # the seer on the wrong side of that range
    (3, 1400.0, True),    # same layer as the target: 1500
    (3, 1600.0, False),
    (5, 280.0, True),     # two layers up: 1500 * 0.2 = 300
    (5, 320.0, False)])
def test_a_seer_lets_its_side_fire_at_what_only_the_seer_sees(layer, d, sees):
    """R-008-04 / S-005 shared sight (SPEC 5.2 side_sees; positive and negative twins by the seer's distance
    from the target): the seer's own sight is the only sight that reaches the layer-3 target. When it does the
    layer-4 sniper (which cannot see it itself, 450 away across a layer) fires at it: shots and damage non-zero,
    its bit4 set, the target flagged visible to the other side, contact made. When the seer is just out of
    its own range nothing at all happens, as in the twin above. The seer is the only thing that differs."""
    scn, res = _sight((layer, d))
    assert bool(runmod.probe_can_see(scn, 2, 1)) is sees          # the seer itself, not the sniper
    assert not runmod.probe_can_see(scn, 0, 1)               # the sniper still cannot
    if sees:
        assert res.shots[0] > 0 and res.damage_dealt[0] > 0.0
        assert can_fire(res, 0).all() and not can_fire(res, 2).any()
        assert unit_trace(res, 1).visible.any() and res.first_contact_tick >= 0
        assert res.firing_ticks[0] == res.ticks, "only the sniper counts in firing_ticks"
        assert res.alive_ticks[0] == 2 * res.ticks
    else:
        assert res.shots == (0, 0) and res.damage_dealt == (0.0, 0.0) and res.firing_ticks == (0, 0)
        assert res.first_contact_tick == -1 and not unit_trace(res, 1).visible.any()


@pytest.mark.parametrize("d,seen", [(300.0, True), (500.0, False)])
def test_the_seer_is_visible_to_the_other_side_like_any_unit(d, seen):
    """Q-E12-01 (a) with S-005: the seer is no stealth unit. B's sniper (layer 3, sensor 800, range 600) sees a seer
    on layer 4 at 300 (inside 400) and fires at it (shots, damage, the seer flagged visible), and does not
    at 500 (outside), by the same sensor rule as for any unit. A (the seer alone) fires nothing either way."""
    groups = [grp("A", "seer", 2450.0 - d, 1000.0, 4), grp("B", "sniper", 2450.0, 1000.0, 3)]
    scn = make_scenario(groups, rules={"spawn_jitter": 0.0, "range_mult": CROSS, "dmg_mult": CROSS},
                        run={"max_ticks": 60, "stalemate_ticks": 6000})
    add_type(scn, "sniper", "raider", range=600.0, hp=BIG)
    scn["types"]["seer"] = {**scn["types"]["seer"], "hp": 1000.0}
    res = runmod.run(scn, seed=0, trace=True)
    assert bool(runmod.probe_can_see(scn, 1, 0)) is seen
    assert res.shots[0] == 0
    if seen:
        assert res.shots[1] > 0 and res.unit[0]["hp"] < 1000.0 and unit_trace(res, 0).visible.any()
    else:
        assert res.shots == (0, 0) and res.unit[0]["hp"] == 1000.0 and not unit_trace(res, 0).visible.any()


# ---- H: fire_requires_vision (R-008-04) ------------------------------------------------------------

def _blind_duel(dist, **rules):
    """A and B: one `longshot` each on layer 3, `dist` apart, hold. Range 500 but sensor 100: in reach of each other
    at 300, out of each other's sight."""
    scn = make_scenario(
        [grp("A", "longshot", 2000.0, 1000.0, 3), grp("B", "longshot", 2000.0 + dist, 1000.0, 3)],
        rules={"spawn_jitter": 0.0, **rules}, run={"max_ticks": 100, "stalemate_ticks": 6000})
    add_type(scn, "longshot", "raider", range=500.0, sensor=100.0, hp=BIG)
    return runmod.run(scn, seed=0, trace=True)


def test_no_blind_fire_by_default():
    """R-008-04 (SPEC 5.4, fire_requires_vision 1 by default): two units 300 apart on one layer, each with
    range 500 and sensor 100, never fire at what they cannot see: zero shots, zero damage, nobody can fire, no
    contact."""
    res = _blind_duel(300.0)
    assert res.shots == (0, 0) and res.damage_dealt == (0.0, 0.0) and res.firing_ticks == (0, 0)
    assert res.first_contact_tick == -1


def test_the_harness_switch_turns_blind_fire_on():
    """SPEC 5.4: `fire_requires_vision = 0` is a harness switch for testing the lab, never a rule and never
    swept (positive control of the test above: the same duel then fires, so zero shots came from the rule)."""
    res = _blind_duel(300.0, fire_requires_vision=0)
    assert res.shots[0] > 0 and res.shots[1] > 0 and res.damage_dealt[0] > 0.0
    assert res.firing_ticks[0] == res.ticks


def test_inside_sight_the_same_duel_fires_with_the_default_rules():
    """R-008-04 positive control: the same pair 80 apart (sensor 100 sees it) fires with fire_requires_vision on."""
    res = _blind_duel(80.0)
    assert res.shots[0] > 0 and res.shots[1] > 0 and res.first_contact_tick == 0
