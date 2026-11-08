"""E-11 S-083 / R-083-03 / R-084-01 (engine rule fixes 2026-11-08, F4): Wardens do not stack.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F4"; Q-084-01 closed 'no stacking' 2026-10-20; evidence
docs/reports/2026-11-07-rule-enforcement.md (sweep I10s: 1089 heals above 0.075 hp in one L-0039 fight). Bug fix, not a story. The
whole-fight twin is tests/skilllab/arena/test_engine_rules_f4_wardens.py.

Rule words (docs/bible/epics/E-11-*.md): R-083-03 the Warden's aura heals every friendly unit within 300 wu, 0.075 hp a tick, and a second
Warden adds nothing; R-084-01 the damage reduction is the sum of Brace 0.50, Fortify 0.20 and the Warden aura 0.10 (Q-084-01: no stacking).
Rule pins: R-083-03, R-084-01.

Scene: a 2000 x 2000 canvas, abilities off (as the lab runs), a friendly Vanguard (500 hp, set to 200 for the heal scenes) at (1000, 1000);
n friendly Wardens in a column at x 750 (250 wu from it, inside the 300 wu aura, and 290 wu or more from the enemy so the enemy shoots the
Vanguard, the nearer); one enemy Raider with 1e6 hp at (1000, 1150) hits the Vanguard for 9.0 x 0.75 (category) = 6.75 every 16 ticks.

Measured on the unfixed tree (2026-11-08): heal per tick with 1, 2, 3 Wardens in range 0.075, 0.150, 0.225; hp lost on a hit tick 6.0, 5.5875,
5.3438 (6.75 x (1 - 0.10), (1 - 0.15), (1 - 0.175), less the heal of that tick); an aura edge at 300 wu (290 wu heals, 310 does not).
Controls green today: one Warden heals 0.075 and reduces by 0.10; a Warden 310 wu away does nothing; a second and third Warden out of range
change nothing (heal only, see the last test).

Detector bound: EPS 1e-9 hp (the arithmetic is exact in double precision for these values; Westley owns any looser tolerance).
"""
import pytest

from conftest import OMFeature
from test_PP_unit_support import RAIDER, VANGUARD, WARDEN, hp, spawn, step

HEAL = 0.075
REDUCTION = 0.10
EPS = 1e-9
HIT_TICKS = 40          # 3 hits (every 16 ticks, the first on tick 4)


def _world(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    lib.om_tactical_disable_abilities(w)
    return w


def _vanguard(lib, w, hp0):
    v = spawn(lib, w, VANGUARD, 0, 1000, 1000)
    lib.om_unit_set_hp(w, v, hp0)
    return v


def _wardens(lib, w, in_range, out_of_range=0):
    for i in range(in_range):
        spawn(lib, w, WARDEN, 0, 750, 1000 - 20 * i)
    for i in range(out_of_range):
        spawn(lib, w, WARDEN, 0, 1000, 690 - 20 * i)        # 310 wu or more north of the Vanguard (the aura reaches 300), far from the Raider


def _heal_per_tick(lib, wf, in_range, out_of_range=0):
    """hp gained per tick with no enemy in the world (the Vanguard at 200 hp)."""
    w = _world(lib, wf)
    v = _vanguard(lib, w, 200.0)
    _wardens(lib, w, in_range, out_of_range)
    gains = []
    for _ in range(5):
        before = hp(lib, w, v)
        step(lib, w)
        gains.append(hp(lib, w, v) - before)
    assert max(gains) - min(gains) < EPS, "scene broken: the heal is not steady: %s" % gains
    return gains[0]


def _hit_loss(lib, wf, in_range, out_of_range=0):
    """(hp lost on a hit tick before that tick's heal, the heal per tick): the Raider shoots the Vanguard; the heal is read on an idle tick once the
    Vanguard is hurt, and the LAST hit is used (the first lands on a full-hp Vanguard, which cannot be healed that tick)."""
    w = _world(lib, wf)
    v = _vanguard(lib, w, 500.0)
    _wardens(lib, w, in_range, out_of_range)
    r = spawn(lib, w, RAIDER, 1, 1000, 1150)
    lib.om_unit_set_hp(w, r, 1.0e6)
    deltas = []
    for _ in range(HIT_TICKS):
        before = hp(lib, w, v)
        step(lib, w)
        deltas.append(hp(lib, w, v) - before)
    hits = [d for d in deltas if d < -1.0]
    idle = [d for d in deltas if d > -1.0]
    assert hits and idle, "scene broken: hits %s idle %s" % (hits, idle)
    heal = max(idle)
    return -(hits[-1]) + heal, heal


# ------------------------------------------------------------------ red today

@pytest.mark.parametrize("n", [2, 3])
def test_R_083_03_a_second_and_third_warden_in_range_add_no_heal(lib, world_factory, n):
    """R-083-03: 'a second Warden adds nothing': with n Wardens in range of one Vanguard the heal is 0.075 hp a tick, as with one. Red today:
    0.150 for two, 0.225 for three."""
    gain = _heal_per_tick(lib, world_factory, n)
    assert abs(gain - HEAL) < EPS, "%d Wardens heal %.6f hp a tick, one heals %.3f" % (n, gain, HEAL)


@pytest.mark.parametrize("n", [2, 3])
def test_R_084_01_a_second_and_third_warden_in_range_add_no_damage_reduction(lib, world_factory, n):
    """R-084-01 / Q-084-01 'no stacking': the Warden aura reduces damage by 0.10, once. The reduction measured on a hit tick (hp lost before
    that tick's heal, against the unreduced 6.75) is 0.10 for n Wardens in range. Red today: 0.15 for two, 0.175 for three."""
    w0 = _world(lib, world_factory)
    v0 = _vanguard(lib, w0, 500.0)
    r0 = spawn(lib, w0, RAIDER, 1, 1000, 1150)
    lib.om_unit_set_hp(w0, r0, 1.0e6)
    base = None
    for _ in range(HIT_TICKS):
        before = hp(lib, w0, v0)
        step(lib, w0)
        if hp(lib, w0, v0) < before - 1.0:
            base = before - hp(lib, w0, v0)
            break
    assert base, "scene broken: the unaided Vanguard was never hit"
    loss, heal = _hit_loss(lib, world_factory, n)
    assert abs((1 - loss / base) - REDUCTION) < 1e-6, "%d Wardens reduce a %.4f hit by %.4f (loss %.4f), expected %.2f" % (n, base, 1 - loss / base, loss, REDUCTION)


def test_R_083_03_two_wardens_and_one_leave_the_vanguard_equally_hurt_over_a_fight(lib, world_factory):
    """R-083-03 / R-084-01, the whole effect: the Vanguard's hp after 80 ticks of being shot is the same with one, two or three Wardens in
    range. Red today: the hp differs by 0.9 (two) and 1.6 (three) over 80 ticks."""
    left = []
    for n in (1, 2, 3):
        w = _world(lib, world_factory)
        v = _vanguard(lib, w, 500.0)
        r = spawn(lib, w, RAIDER, 1, 1000, 1150)       # Test-defect (F4, 2026-11-08): spawned before the Wardens so its id, and its targeting cohort, is the same for every n
        lib.om_unit_set_hp(w, r, 1.0e6)
        _wardens(lib, w, n)
        step(lib, w, 80)
        left.append(hp(lib, w, v))
    assert max(left) - min(left) < EPS, "hp after 80 ticks with 1, 2, 3 Wardens: %s" % left


# ------------------------------------------------------------------ green today: the controls

def test_R_083_03_control_one_warden_in_range_heals_0_075_and_reduces_by_0_10(lib, world_factory):
    """Control (green today and after): a single Warden heals 0.075 hp a tick and reduces a hit by 0.10; the scene and the arithmetic are
    sound, so the stacking tests above are red for the stacking."""
    assert abs(_heal_per_tick(lib, world_factory, 1) - HEAL) < EPS
    w0 = _world(lib, world_factory)
    v0 = _vanguard(lib, w0, 500.0)
    r0 = spawn(lib, w0, RAIDER, 1, 1000, 1150)
    lib.om_unit_set_hp(w0, r0, 1.0e6)
    before = hp(lib, w0, v0)
    for _ in range(HIT_TICKS):
        step(lib, w0)
        if hp(lib, w0, v0) < before - 1.0:
            break
    base = before - hp(lib, w0, v0)
    loss, _ = _hit_loss(lib, world_factory, 1)
    assert abs((1 - loss / base) - REDUCTION) < 1e-6


@pytest.mark.parametrize("out", [1, 3])
def test_R_083_03_control_a_warden_out_of_range_does_nothing(lib, world_factory, out):
    """R-083-03 control (green today): Wardens 310 wu from the Vanguard (the aura is 300 wu) heal nothing."""
    assert abs(_heal_per_tick(lib, world_factory, 0, out)) < EPS


def test_R_083_03_control_wardens_out_of_range_do_not_join_the_one_in_range(lib, world_factory):
    """R-083-03 control (green today): one Warden in range and two out of it heal 0.075, the same as one alone. (Heal only: with an enemy
    in the world an idle Warden walks into range to engage it, so the reduction cannot be measured with Wardens left standing outside.)"""
    assert abs(_heal_per_tick(lib, world_factory, 1, 2) - HEAL) < EPS
