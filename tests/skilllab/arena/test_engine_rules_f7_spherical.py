# Rule pins: R-087-10, R-098-02, R-008-04, R-190-04
"""Engine rule fixes 2026-11-08, F7, whole fights: every range test is spherical, and sight and fire agree.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F7" and "Test architecture". Evidence: docs/reports/2026-11-07-rule-enforcement/appendix-c-invariant-sweep.md
(I11nl: L-0061 ticks 59 to 61, Wardens 2 and 26). The pair geometry is tests/csim/test_E11_R087_10_spherical_distance.py. The probe is engine_rules_r2_probe.py in this directory
(per tick, from engine state; it does not import the F0 checker).

Rule words (docs/bible/epics/E-11-units-and-combat.md R-087-10 as written 2026-11-08):
  R-087-10  "Given any range or radius test between two units (attack range, sensor radius, leash, area radius), When it is evaluated, Then the distance is spherical:
             the horizontal distance and the height difference between the two units' layers (E-17 R-190-04 band heights, a unit mid-slope at its slope height) taken together."
  R-098-02  "Given a blocked cell ... or a cover obstacle between them on the layers involved, When it fires, Then the shot is blocked exactly as vision is."
  R-008-04  "a unit never fires at a target its side cannot see ... a target seen by any friendly unit or revealed by a ping may be fired at."

NEW CHECKER NAME (the implementer adds it to scripts/skilllab/invariants.py RULES and to the Monitor): "R-087-10" - a shot (attacker, target) whose slant distance (the
horizontal distance and the band-height difference of the two layers) exceeds the attacker's attack range by more than DRAFT-f7-slant-slack 1.0 wu. The tests below do not
depend on it except test_R_087_10_the_checker_knows_the_rule.

Premises dumped from the built tree (Round 1 tip 94c2fb5d, 2026-11-11, L-0061 seed 1 sight on, the whole fight 1663 ticks): the I11nl pair at ticks 57 to 63 (printed by the
failing assertion below):
  unit 2 Warden (range 350) layer 1 at (1367.9, 1864.9), unit 26 Warden layer 0 at (1018.8 to 1043.2, 1954.0): flat 360.3 (tick 57) falling to 336.7 (tick 63)
  band heights [70, 130, 190, 250, 310]: layer 1 is 60 wu above layer 0 in the layer-floor reading (the terrain height under unit 2 is 190, the plateau above its floor)
  om_unit_can_see(2, 26) = 1 on every one of those ticks; om_combat_can_shoot(2, 26) = 0; the line crosses three layer-0 ground cells of the hill, (12,18), (12,19), (13,18),
  which the engine calls blocked (band 2 at their centres), om_terrain_sight_blocks = 0 for every pair of layers; with OM_TP_ROUTE_AROUND_TERRAIN set to 0 the same call
  is 1. No planar obstacle exists in L-0061 (its only feature is the vantage). The fire side's blocked-cell walk (om_move_los_clear on the lower layer of the pair) says blocked
  where the sight side (fog.c om_fog_grid_blocks, which skips a hill's ground cells) says clear. Measured, not fixed: the cause is the implementer's to confirm.
Detector bounds (not rules; Westley's to change): DRAFT-f7-slant-slack 1.0 wu; the layer-floor reading of the height of a layer (spec F7: om_terrain_band_heights; a unit on a slope
at its slope height is the implementer's reading, report_gap); MIN_CROSS 50 cross-layer shots (a fix that stopped every cross-layer shot would pass the rule and fail the control).
"""
import pytest

import engine_rules_r2_probe as probe

SLACK = probe.SLANT_SLACK
FIGHT = "L-0061"
PAIR = (2, 26)
WATCH = ((57, PAIR), (58, PAIR), (59, PAIR), (60, PAIR), (61, PAIR), (62, PAIR), (63, PAIR))
MIN_CROSS = 50


@pytest.fixture(scope="module")
def run():
    return probe.played(FIGHT, "on", 600, WATCH)


def _cross_fires(run):
    """[(tick, attacker, target, flat, slant)] for every shot whose two units stand on different layers, with the pair's geometry at that tick."""
    held = {(r[0], r[1], r[2]): r for r in run.rows}
    out = []
    for n, a, b in run.fires:
        r = held.get((n, a, b))
        if r is not None and r[7] != r[8]:
            out.append((n, a, b, r[3], (r[3] ** 2 + r[4] ** 2) ** 0.5, r[6]))
    return out


def test_R_087_10_premise_the_cross_layer_multipliers_are_one_and_heights_exist(run):
    """Premise (green today and after): OM_TP_RANGE_UP_1 and OM_TP_RANGE_DOWN_1 are 1.0 and the world has band heights [70, 130, ...], so 'range' in the
    tests below is the type's attack range and a layer is 60 wu high. A fix that changes either is a different change."""
    assert run.range_mult == [1.0, 1.0], run.range_mult
    assert run.heights[:2] == [70.0, 130.0], run.heights
    assert run.n >= 1000


def test_R_087_10_control_units_fire_across_layers_in_the_fight(run):
    """Control (green today and after): at least MIN_CROSS shots in the L-0061 fight come from a unit on one layer at a unit on another, so the rule below is
    tested on real cross-layer fire and not on a fight where nobody shoots across. RED TODAY, by the I11nl cause: the fight has 1954 shots and 0 of them cross
    layers (a hill unit cannot shoot the flat below it). It turns green when the I11nl cause is fixed; until then the whole-run rule below passes for want of cross-layer fire,
    and the metric itself is proved red by tests/csim/test_E11_R087_10_spherical_distance.py."""
    cross = _cross_fires(run)
    assert len(cross) >= MIN_CROSS, "only %d cross-layer shots in %d ticks (%d shots in all)" % (len(cross), run.n, len(run.fires))


def test_R_087_10_no_unit_fires_at_a_target_beyond_its_range_by_slant(run):
    """R-087-10, every tick of L-0061 (sight on, walkers, the vantage hill): no shot is fired at a target whose slant distance (horizontal distance and the band-height
    difference of the two layers) exceeds the shooter's attack range by more than DRAFT-f7-slant-slack. Green today and vacuous (0 cross-layer shots in the fight, see the control above); it
    bites once cross-layer fire exists. The red for the metric is the csim file."""
    held = {(r[0], r[1], r[2]): r for r in run.rows}
    bad = []
    for n, a, b in run.fires:
        r = held.get((n, a, b))
        if r is None:
            continue
        slant = (r[3] ** 2 + r[4] ** 2) ** 0.5
        if slant > r[6] + SLACK:
            bad.append((n, a, b, round(r[3], 1), round(slant, 1), r[6], "layers %d->%d" % (r[7], r[8])))
    assert not bad, "%d shots from beyond range by slant (%d units), first %s" % (len(bad), len({x[1] for x in bad}), bad[:3])


def test_R_098_02_i11nl_the_sweeps_pair_can_shoot_when_it_sees_and_is_in_range_by_slant(run):
    """R-098-02 / R-087-10, the open case of the sweep (I11nl): L-0061 ticks 57 to 63, Warden 2 (layer 1) and Warden 26 (layer 0). Every tick on which 2 sees 26, the pair
    is inside 2's range 350 by slant, and no planar obstacle stands between them (L-0061 has none), 2 must be able to shoot 26. The failing line prints the measured premises.
    Measured: sees on all seven ticks, can_shoot false on all seven; inside range 350 by slant on ticks 61, 62, 63 (slant 349.7, 345.8, 342.0; ticks 57 to 60
    are 353.5 to 365.3, outside by slant though 348.3 flat on tick 60 is inside). Red today."""
    a, b = PAIR
    rows = []
    for n in sorted(run.dumps):
        d = run.dumps[n]
        flat = ((d[a]["x"] - d[b]["x"]) ** 2 + (d[a]["y"] - d[b]["y"]) ** 2) ** 0.5
        dz = run.heights[d[b]["layer"]] - run.heights[d[a]["layer"]]
        slant = (flat * flat + dz * dz) ** 0.5
        rows.append((n, d[a]["layer"], d[b]["layer"], round(flat, 1), round(slant, 1), d[a]["see"][b], d[a]["shoot"][b]))
    assert rows and all(r[1] == 1 and r[2] == 0 for r in rows), "premise: the Wardens are not on layers (1, 0) at those ticks: %s" % rows
    rng = run.stats[run.typ[a]]["attack_range"]
    assert rng == 350.0, "premise: unit 2's range is %s, not 350" % rng
    inside = [r for r in rows if r[5] and r[4] <= rng]
    assert inside, "premise: no tick where 2 sees 26 and is inside range 350 by slant: %s" % rows
    bad = [r for r in inside if not r[6]]
    assert not bad, "(tick, layer a, layer b, flat, slant, sees, can_shoot) sees and in range by slant but cannot shoot: %s; all rows %s" % (bad, rows)


def test_R_098_02_i11nl_a_unit_that_holds_a_target_it_sees_inside_range_by_slant_can_shoot_it(run):
    """R-098-02 / R-087-10, the whole fight: on every tick, every unit that holds a target its own eyes see, inside its range by slant, with no planar obstacle
    in the layout, can shoot it. Red today: the held-but-unshootable target (the sweep's I11nl, 185k unit-ticks in 11 hill layouts)."""
    bad = [(r[0], r[1], r[2], round(r[3], 1), round((r[3] ** 2 + r[4] ** 2) ** 0.5, 1), r[6]) for r in run.rows
           if r[9] and (r[3] ** 2 + r[4] ** 2) ** 0.5 <= r[6] - SLACK and not r[10]]
    assert not bad, "%d unit-ticks where the unit sees its target inside range by slant and cannot shoot it (%d units), first %s" % (len(bad), len({b[1] for b in bad}), bad[:3])


def test_R_087_10_the_checker_knows_the_rule():
    """The lab's checker lists the rule (spec F7 'a new checker name R-087-10'): scripts/skilllab/invariants.py RULES contains 'R-087-10', so a fight that breaks it is
    marked invalid. Red today: the name does not exist. The implementer adds the predicate (slant distance of each shot over the attacker's range + 1.0 wu) to the Monitor."""
    from scripts.skilllab import invariants
    assert "R-087-10" in invariants.RULES, invariants.RULES
