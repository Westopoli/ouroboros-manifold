"""Rung R2 tests 10 and 11 (SPEC.md section 10): the burst ability (5.6) and the arc gate (5.4, 5.12).

How the burst fixtures isolate the ability (SPEC 5.6 gives burst damage = dmg * ab_dmg_mult *
aoe_layer_mult[off], so dmg cannot be zeroed): the quiet caster is the base `caster` type with
interval_s = 1e6, so its normal fire (initial cooldown U(0, 1e6)) never lands in a test window and
every HP drop on a target is the burst. Targets hold and sit 400 from the caster, outside the
raider range of 200, so nothing fires back. Spawn jitter is 0 so geometry is exact. Normal fire
on a raider would be 6.0 (4.0 * 1.5), so a one-tick drop above 20 identifies a cast.

Timing convention (SPEC gaps filled, see the report): the ability cooldown starts at 0 (ready at
spawn); the windup starts on the first tick a cluster is visible and in range; expiry lands
ab_windup_s * 20 ticks later, read from the trace as the first row whose hp dropped. A tolerance
of +/- 1 tick covers where in the tick the windup counter is decremented.
"""
import copy
import math

import numpy as np
import pytest

from layerlab import scenario
from layerlab.run import run

TICKS_PER_S = 20


# ---------------------------------------------------------------- fixtures and helpers

@pytest.fixture(scope="module")
def base(scenarios_dir):
    return scenario.load(str(scenarios_dir / "base.toml"))


def _g(side, type_, x, y, order="hold", goal=None, count=1, facing=0.0, layer=3):
    g = {"side": side, "type": type_, "count": count, "formation": "line",
         "x": float(x), "y": float(y), "facing": float(facing), "layer": layer, "order": order}
    if goal is not None:
        g["goal"] = [float(goal[0]), float(goal[1])]
    return g


def _build(base, groups, types=None, rules=None, max_ticks=60):
    """Base scenario with no jitter, a short run, the given groups, extra or changed types and rules."""
    scn = copy.deepcopy(base)
    scn["groups"] = groups
    scn["run"]["max_ticks"] = max_ticks
    scn["run"]["stalemate_ticks"] = 6000
    scn["rules"]["spawn_jitter"] = 0.0
    scn["types"]["caster_quiet"] = {**scn["types"]["caster"], "interval_s": 1.0e6}
    for name, fields in (types or {}).items():
        scn["types"][name] = fields
    for k, v in (rules or {}).items():
        scn["rules"][k] = v
    return scn


def _drops(res, idx, hp0):
    """(row, amount) for every row on which unit idx lost HP."""
    hp = res.trace["hp"][:, idx].astype(float)
    prev = np.concatenate(([hp0], hp[:-1]))
    d = prev - hp
    return [(int(r), float(d[r])) for r in np.nonzero(d > 1e-6)[0]]


def _casts(res, idx, hp0=250.0, min_hit=20.0):
    """Rows on which unit idx took a hit of burst size (normal fire on a raider is 6.0). A scenario
    with a quiet caster (no normal fire) can pass a small min_hit so a small burst still counts."""
    return [(r, a) for r, a in _drops(res, idx, hp0) if a > min_hit]


def _cluster(type_="raider", ys=(950, 1000, 1050), x=1400):
    return [_g("B", type_, x, y) for y in ys]


# ---------------------------------------------------------------- test 10: burst ability

def test_burst_hits_every_clustered_target_for_dmg_x_mult(base):
    """SPEC test 10 / 5.6 / 5.5: a caster against 3 clustered raiders deals dmg * ab_dmg_mult *
    aoe_layer_mult[4] = 4.0 * 6.0 * 1.0 = 24.0 to each at expiry, all on one tick, once; the cast
    is the only damage (quiet caster) and counts as exactly one shot."""
    scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster())
    for seed in (0, 1, 2):
        res = run(scn, seed=seed, trace=True)
        ev = [_casts(res, i) for i in (1, 2, 3)]
        assert all(len(e) == 1 for e in ev), "each target takes exactly one burst hit, got %s" % ev
        rows = {e[0][0] for e in ev}
        assert len(rows) == 1, "all three hits land on the same tick, got %s" % ev
        for e in ev:
            assert e[0][1] == pytest.approx(24.0, abs=1e-4)
        assert res.damage_dealt[0] == pytest.approx(72.0, abs=1e-9)
        assert res.damage_dealt[1] == 0.0
        assert res.shots[0] == 1, "a cast counts as one shot (SPEC 5.6)"
        assert res.trace["hp"][-1, 0] == pytest.approx(120.0)


@pytest.mark.parametrize("aoe_mult,ab_mult,dmg,expected", [
    (1.0, 6.0, 4.0, 24.0),    # the default
    (0.5, 6.0, 4.0, 12.0),    # aoe_layer_mult[4] is applied
    (2.0, 6.0, 4.0, 48.0),
    (1.0, 3.0, 4.0, 12.0),    # ab_dmg_mult is applied
    (1.0, 6.0, 5.0, 30.0),    # dmg is applied
])
def test_burst_damage_follows_its_three_factors(base, aoe_mult, ab_mult, dmg, expected):
    """SPEC 5.6 formula dmg * ab_dmg_mult * aoe_layer_mult[off]: each factor moves the hit. The
    default row is the positive control; the others are the negative controls (a hard-coded 24
    fails them)."""
    table = [0.0, 0.0, 0.0, 0.0, aoe_mult, 0.0, 0.0, 0.0, 0.0]
    scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster(),
                 types={"caster_quiet": {**base["types"]["caster"], "interval_s": 1.0e6,
                                         "ab_dmg_mult": ab_mult, "dmg": dmg}},
                 rules={"aoe_layer_mult": table})
    res = run(scn, trace=True)
    for i in (1, 2, 3):
        ev = _casts(res, i, min_hit=1e-6)   # quiet caster: every hit is a burst, whatever its size
        assert len(ev) == 1 and ev[0][1] == pytest.approx(expected, abs=1e-4), (i, ev)
    assert res.damage_dealt[0] == pytest.approx(3 * expected, abs=1e-6)


def test_burst_with_aoe_layer_mult_zero_deals_nothing(base):
    """SPEC 5.6 / 5.4: aoe_layer_mult[4] = 0 zeroes the burst's damage (negative control for the
    factor test). Whether the cast still starts is not specified, so only damage is asserted."""
    table = [0.0] * 9
    scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster(), rules={"aoe_layer_mult": table})
    res = run(scn, trace=True)
    assert res.damage_dealt[0] == 0.0
    assert all(res.trace["hp"][:, i].min() == 250.0 for i in (1, 2, 3))


@pytest.mark.parametrize("windup_s", [0.5, 1.5, 3.0])
def test_burst_lands_windup_after_the_trigger_not_before(base, windup_s):
    """SPEC 5.6 (windup): the cast resolves ab_windup_s after the trigger tick. The cluster is in
    range and visible at tick 0 with the ability ready, so the trigger is tick 0 and the hit row
    is windup_s * 20 +/- 1. 1.5 s is the base value; 0.5 and 3.0 are the negative controls (a
    fixed delay fails them). No target loses HP in any earlier row."""
    expected = int(round(windup_s * TICKS_PER_S))
    scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster(),
                 types={"caster_quiet": {**base["types"]["caster"], "interval_s": 1.0e6,
                                         "ab_windup_s": windup_s}},
                 max_ticks=expected + 30)
    res = run(scn, trace=True)
    for i in (1, 2, 3):
        d = _drops(res, i, 250.0)
        assert d, "target %d never took the burst" % i
        assert expected - 1 <= d[0][0] <= expected + 1, "hit on row %d, windup is %d ticks" % (d[0][0], expected)
    first = min(_drops(res, i, 250.0)[0][0] for i in (1, 2, 3))
    assert (res.trace["hp"][:first, 1:4] == 250.0).all(), "no target is hurt before expiry"


def test_target_that_left_the_radius_during_windup_takes_nothing(base):
    """SPEC 5.6 (counterplay): the radius is locked at the trigger and applied at expiry; a raider
    ordered to move away at speed 150 is more than 120 from the locked centre by tick 30 and takes
    nothing, while the two that stayed take 24.0 each. Cluster: stay (1400,950), centre
    (1400,1000, nearest to the caster so it is the locked centre), leaver (1400,1050)."""
    groups = [_g("A", "caster_quiet", 1000, 1000),
              _g("B", "raider", 1400, 950), _g("B", "raider", 1400, 1000),
              _g("B", "raider", 1400, 1050, order="move", goal=(3000, 1050))]
    res = run(_build(base, groups), trace=True)
    e_stay = [_casts(res, 1), _casts(res, 2)]
    assert all(len(e) == 1 and e[0][1] == pytest.approx(24.0, abs=1e-4) for e in e_stay), e_stay
    row = e_stay[0][0][0]
    dx = float(res.trace["x"][row, 3]) - 1400.0
    dy = float(res.trace["y"][row, 3]) - 1000.0
    assert math.hypot(dx, dy) > 120.0, "fixture: the leaver must be outside the radius at expiry"
    assert _drops(res, 3, 250.0) == [], "the leaver took damage"
    assert res.damage_dealt[0] == pytest.approx(48.0, abs=1e-9)


def test_target_that_stays_is_hit_control_for_the_leaver(base):
    """SPEC 5.6 positive control for the leaver test: the same cluster with the third raider
    holding takes 24.0 as well (72 total), so the leaver result is the movement, not geometry."""
    scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster())
    res = run(scn, trace=True)
    assert res.damage_dealt[0] == pytest.approx(72.0, abs=1e-9)


KILLER = {"category": "strike", "hp": 5000.0, "dmg": 500.0, "interval_s": 0.5, "range": 600.0,
          "speed": 150.0, "sensor": 800.0, "transition_s": 1.0, "turn_rate": 6.0}


def test_caster_killed_in_windup_casts_nothing(base):
    """SPEC 5.6: a caster that dies in its windup casts nothing. A killer (500 dmg, interval 0.5 s,
    400 from the caster and 566 from the cluster so it does not join the count) kills the 120 hp
    caster within 10 ticks. No target loses HP, no ability damage, and no shot is counted."""
    groups = [_g("A", "caster_quiet", 1000, 1000)] + _cluster() + [_g("B", "killer", 1000, 1400)]
    res = run(_build(base, groups, types={"killer": KILLER}, max_ticks=80), trace=True)
    dead_row = int(np.nonzero(res.trace["alive"][:, 0] == 0)[0][0])
    assert dead_row < 29, "fixture: the caster must die inside its 30 tick windup (died on %d)" % dead_row
    assert res.damage_dealt[0] == 0.0
    assert res.shots[0] == 0, "a cast that never resolved is not a shot"
    assert (res.trace["hp"][:, 1:4] == 250.0).all()


def test_caster_not_killed_casts_control_for_the_killer(base):
    """SPEC 5.6 positive control for the killed-caster test: the same scene with a killer that
    deals 0 damage lets the cast land (72 damage), so the zero above is the kill."""
    groups = [_g("A", "caster_quiet", 1000, 1000)] + _cluster() + [_g("B", "killer", 1000, 1400)]
    res = run(_build(base, groups, types={"killer": {**KILLER, "dmg": 0.0}}), trace=True)
    assert res.damage_dealt[0] == pytest.approx(72.0, abs=1e-9)
    assert res.unit[0]["alive"] == 1


@pytest.mark.parametrize("cooldown_s", [0.0, 6.0, 12.0])
def test_second_cast_waits_for_the_cooldown(base, cooldown_s):
    """SPEC 5.6: the ability cooldown starts at expiry; the next cast needs it ready and then a
    full windup, so consecutive hit rows are cooldown_s * 20 + 30 apart (+/- 2). Hard floor for
    the spec case (12 s): the gap is never under 240 ticks. 0.0 and 6.0 are the negative controls
    (a hard-coded 12 s fails them)."""
    gap = int(round(cooldown_s * TICKS_PER_S)) + 30
    scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster(),
                 types={"caster_quiet": {**base["types"]["caster"], "interval_s": 1.0e6,
                                         "ab_cooldown_s": cooldown_s}},
                 max_ticks=30 + 2 * gap + 20)
    res = run(scn, trace=True)
    ev = _casts(res, 2)
    assert len(ev) >= 2, "expected at least two casts, saw %s" % ev
    observed = ev[1][0] - ev[0][0]
    assert gap - 2 <= observed <= gap + 2, "hit rows %d and %d, expected a gap of %d" % (ev[0][0], ev[1][0], gap)
    if cooldown_s == 12.0:
        assert observed >= 12 * TICKS_PER_S


@pytest.mark.parametrize("third_y,should_cast", [
    (None, False),     # only two raiders: below ab_min_targets
    (1140, False),     # a third raider 140 from the centre: outside the 120 radius, count stays 2
    (1090, True),      # the same third raider 90 away: count 3, casts (positive control)
])
def test_fewer_than_min_targets_in_radius_means_no_cast(base, third_y, should_cast):
    """SPEC 5.6: a cast needs >= ab_min_targets (3) eligible enemies within ab_radius (120) of the
    locked centre. Two raiders, or a third just outside the radius: no cast over 100 ticks (well
    past the windup). Third inside the radius: casts (positive control)."""
    ys = [975, 1025] if third_y is None else [950, 1000, third_y]
    scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster(ys=ys), max_ticks=100)
    res = run(scn, trace=True)
    if should_cast:
        assert res.damage_dealt[0] > 0.0 and res.shots[0] >= 1
    else:
        assert res.damage_dealt[0] == 0.0 and res.shots[0] == 0
        assert (res.trace["hp"][:, 1:] == 250.0).all()


def test_min_targets_knob_decides_the_cast(base):
    """SPEC 5.6: with the same two raiders, ab_min_targets = 2 casts (48 damage) and 3 does not
    (positive and negative control for the threshold itself)."""
    for min_t, expect in ((2, 48.0), (3, 0.0)):
        scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster(ys=[975, 1025]),
                     types={"caster_quiet": {**base["types"]["caster"], "interval_s": 1.0e6,
                                             "ab_min_targets": min_t}},
                     max_ticks=100)
        assert run(scn).damage_dealt[0] == pytest.approx(expect, abs=1e-9), min_t


@pytest.mark.parametrize("sensor,should_cast", [(420.0, False), (460.0, True)])
def test_only_visible_targets_count_toward_min_targets(base, sensor, should_cast):
    """SPEC 5.6 (visible, eligible enemies): raiders at 400.5, 400.5 and 440 from the caster, all
    within 120 of one another. With sensor 420 the third is not seen, the visible count is 2 and
    nothing casts; with sensor 460 all three are seen and it casts (positive control)."""
    groups = [_g("A", "caster_quiet", 1000, 1000),
              _g("B", "raider", 1400, 980), _g("B", "raider", 1400, 1020), _g("B", "raider", 1440, 1000)]
    scn = _build(base, groups, max_ticks=100,
                 types={"caster_quiet": {**base["types"]["caster"], "interval_s": 1.0e6, "sensor": sensor}})
    res = run(scn)
    if should_cast:
        assert res.damage_dealt[0] > 0.0
    else:
        assert res.damage_dealt[0] == 0.0 and res.shots[0] == 0


def test_caster_is_still_and_silent_during_windup_and_fires_after(base):
    """SPEC 5.6: during the windup the unit does not move or fire. The caster (normal fire kept)
    attack-moves on a cluster 600 away, stops in range, and the cast lands at row E. Over rows
    E-28 .. E-2 (inside the windup for any +/- 1 tick convention) its x, y are constant, its fired
    flag (bit 1) is clear and no target takes a normal hit. Positive controls: it moved before the
    windup, and it fires normally after the cast."""
    groups = [_g("A", "caster", 1000, 1000, order="attack_move", goal=(3000, 1000))] + \
             _cluster(x=1600)
    res = run(_build(base, groups, max_ticks=200), trace=True)
    rows = [_casts(res, i) for i in (1, 2, 3)]
    e = min(r[0][0] for r in rows if r)
    lo, hi = e - 28, e - 2
    x = res.trace["x"][:, 0]
    y = res.trace["y"][:, 0]
    assert (x[lo:hi + 1] == x[lo]).all() and (y[lo:hi + 1] == y[lo]).all(), "caster moved in its windup"
    flags = res.trace["flags"][:, 0]
    assert ((flags[lo:hi + 1] & 2) == 0).all(), "caster fired in its windup"
    for i in (1, 2, 3):
        window_hits = [(r, a) for r, a in _drops(res, i, 250.0) if lo <= r <= hi]
        assert window_hits == [], "target %d hit during the windup: %s" % (i, window_hits)
    assert x[lo] - x[0] >= 100.0, "control: the caster must have been moving before the windup"
    assert (res.trace["flags"][e + 1:e + 31, 0] & 2).any(), "control: the caster fires normally after the cast"


def test_ability_hit_ignores_category_mult_control_for_normal_fire(base):
    """SPEC 5.5 / 5.6: normal fire applies category_mult, the burst does not. Fixture check first:
    with the ability held off (ab_min_targets 99) the caster's normal hits are 4.0 * 1.5 = 6.0 on a
    Strike raider and 4.0 * 0.75 = 3.0 on a Siege bastion, so the multiplier is live here."""
    off = {"caster": {**base["types"]["caster"], "ab_min_targets": 99}}
    dud = {"category": "siege", "hp": 1050.0, "dmg": 0.0, "interval_s": 1.8, "range": 800.0,
           "speed": 40.0, "sensor": 300.0, "transition_s": 5.0, "turn_rate": 2.5}
    for tgt, per_hit in (("raider", 6.0), ("bastion_dud", 3.0)):
        scn = _build(base, [_g("A", "caster", 1000, 1000)] + _cluster(tgt), types={**off, "bastion_dud": dud},
                     max_ticks=100)
        res = run(scn)
        assert res.shots[0] > 0
        assert res.damage_dealt[0] / res.shots[0] == pytest.approx(per_hit, abs=1e-9), tgt


@pytest.mark.parametrize("target,cat_override", [
    ("raider", None),         # Strike: category_mult[line][strike] = 1.5, would give 36 if applied
    ("bastion_dud", None),    # Siege: 0.75, would give 18 if applied (a dmg 0 bastion cannot fire back)
    ("raider", 3.0),          # every category_mult entry 3.0, would give 72 if applied
])
def test_burst_ignores_category_mult(base, target, cat_override):
    """SPEC 5.5 / 5.6: burst damage carries no category multiplier: 24.0 per hit on a
    Strike cluster (normal 1.5), a Siege cluster (normal 0.75) and with every category_mult entry
    at 3.0. The two default rows differ from 24 in opposite directions, so a multiplier of either
    kind is caught. The bastion_dud copy has dmg 0 so it cannot shoot the caster."""
    dud = {"category": "siege", "hp": 1050.0, "dmg": 0.0, "interval_s": 1.8, "range": 800.0,
           "speed": 40.0, "sensor": 300.0, "transition_s": 5.0, "turn_rate": 2.5}
    rules = {} if cat_override is None else {"category_mult": [[cat_override] * 3 for _ in range(3)]}
    hp0 = 1050.0 if target == "bastion_dud" else 250.0
    scn = _build(base, [_g("A", "caster_quiet", 1000, 1000)] + _cluster(target),
                 types={"bastion_dud": dud}, rules=rules)
    res = run(scn, trace=True)
    for i in (1, 2, 3):
        ev = [(r, a) for r, a in _drops(res, i, hp0)]
        assert len(ev) == 1 and ev[0][1] == pytest.approx(24.0, abs=1e-4), (target, i, ev)
    assert res.damage_dealt[0] == pytest.approx(72.0, abs=1e-9)


# ---------------------------------------------------------------- test 11: arc gate (already built in R0)
#
# The arc test and the turning code exist in the C core (ll_combat.c, ll_move.c), so these may pass
# today: they are regression guards for R2, not red tests.

GAZER = {"category": "strike", "hp": 250.0, "dmg": 9.0, "interval_s": 0.05, "range": 200.0,
         "speed": 150.0, "sensor": 800.0, "transition_s": 1.0, "turn_rate": 6.0, "arc_deg": 60.0}
# interval 0.05 s: the initial cooldown draw is under one tick, so the first shot is set by the gate alone.
SILENT_TARGET = {"category": "strike", "hp": 1.0e6, "dmg": 0.0, "interval_s": 1.0e6, "range": 200.0,
                 "speed": 150.0, "sensor": 800.0, "transition_s": 1.0, "turn_rate": 6.0}


def _arc_scn(base, gate, facing=180.0, **gazer_over):
    groups = [_g("A", "gazer", 1000, 1000, facing=facing), _g("B", "dud", 1150, 1000, facing=180.0)]
    return _build(base, groups, types={"gazer": {**GAZER, **gazer_over}, "dud": SILENT_TARGET},
                  rules={"facing_gates_fire": gate}, max_ticks=100)


def _first_fire_row(res, idx=0):
    rows = np.nonzero(res.trace["flags"][:, idx] & 2)[0]
    return int(rows[0]) if len(rows) else None


@pytest.mark.parametrize("turn_rate", [6.0, 3.0, 1.5])
def test_gate_on_unit_facing_away_turns_then_fires(base, turn_rate):
    """SPEC test 11 / 5.4 / 5.12: arc 60, facing 180 with the enemy at +x, gate on: no shot until
    the facing is within 30 degrees of the enemy, then it fires. The turn needs
    (pi - pi/6) rad at turn_rate * 0.05 rad per tick, i.e. 9 ticks at 6.0 (about 11 with a full
    180 degree turn: 0.52 s), 18 at 3.0, 35 at 1.5. First shot within [need - 1, need + 3]; no shot
    before; first_shot_tick agrees with the trace (the target is silent)."""
    need = math.ceil((math.pi - math.radians(30.0)) / (turn_rate * 0.05))
    res = run(_arc_scn(base, 1, turn_rate=turn_rate), trace=True)
    f = _first_fire_row(res)
    assert f is not None, "the unit never fired: it did not turn into its arc"
    assert need - 1 <= f <= need + 3, "first shot on tick %d, turn needs about %d" % (f, need)
    assert res.first_shot_tick == f and res.first_shot_side == 0
    assert res.shots[1] == 0


def test_gate_off_fires_at_once(base):
    """SPEC test 11 / 5.4: the same unit facing away fires in the first ticks with
    facing_gates_fire = 0 (positive control for the gate-on test: the unit can fire and the gate
    is what held it back)."""
    res = run(_arc_scn(base, 0), trace=True)
    assert _first_fire_row(res) <= 1


def test_gate_on_unit_already_facing_fires_at_once(base):
    """SPEC test 11 / 5.12: arc 60 with the enemy dead ahead and the gate on fires in the first
    ticks (the gate is not a blanket block)."""
    res = run(_arc_scn(base, 1, facing=0.0), trace=True)
    assert _first_fire_row(res) <= 1


def test_arc_360_never_blocks_the_gate(base):
    """SPEC test 11 / 5.12: arc_deg 360 skips the arc test, so a unit facing away with the gate on
    fires at once."""
    res = run(_arc_scn(base, 1, arc_deg=360.0), trace=True)
    assert _first_fire_row(res) <= 1


def test_gate_on_unit_that_cannot_turn_never_fires(base):
    """SPEC test 11 / 5.12 (negative control for the turn time): turn_rate 0.01 rad/s turns 0.05
    rad in 100 ticks, so a unit facing away stays outside its arc and fires nothing, while the
    same unit with the gate off fires every tick it can."""
    gated = run(_arc_scn(base, 1, turn_rate=0.01), trace=True)
    assert gated.shots[0] == 0
    assert run(_arc_scn(base, 0, turn_rate=0.01)).shots[0] > 0
