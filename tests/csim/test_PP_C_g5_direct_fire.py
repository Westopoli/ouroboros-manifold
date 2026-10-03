"""Phase C step G5, reach applied to direct fire and acquisition (E-01 R-164-02, R-008-02, R-008-04;
register Q-008-03: range and damage multiplier per signed layer offset).

Rules proved: R-164-02 'Given a target at a layer offset outside the attacker's reach, When the
attacker would fire, Then it does not, whatever the distance.' R-008-02 an idle or attack-moving unit
engages a visible enemy one layer up only if its type's reach includes one layer up; 'the range and
damage at that offset are Q-008-03'. Brief G5: 'A unit may acquire and fire at a target whose layer is
within its type's reach above or below its own effective layer, and at no other'; 'a range multiplier
of 0.5 one layer up halves the distance at which it engages; a damage multiplier applies exactly';
'The attack-target order's missing layer check ... is closed: reach applies to it too.'

Attacker: the Vanguard (range 300, sensor 700); target: an idle Supply unit. Layers are engine layers
0 to 4 (A132). 'Engaged' = the attacker holds the target and the target loses hp in the window.

Red today, and why: there is no cross-layer fire at all (acquisition, drop check and the fire check
each require equal layers) and the reach and multiplier settings are not read, so every 'engaged'
expectation fails; the attack-target order is the one exception, it fires across any layers today, so
its 'not engaged' tests fail the other way round. Each negative half sits in a test whose first half
is a positive control that must trip, so no test is red or green by accident.
"""
import pytest

from test_PP_C_g5_support import (
    BOMBARD, EDGE, INTERCEPTOR, RAIDER, SUPPLY, VANGUARD, WINDOW, attack_move, duel, engaged,
    first_hit, get_param, hp, layers_for, open_vision, pos, read_reach, set_param, set_reach, solo_pair,
    spawn, state_snapshot, step, target,
)

RANGE = 300.0  # Vanguard attack range (om_constants OM_ROSTER_VANGUARD_RANGE)
OFFSETS = [(d, n) for d in ("UP", "DOWN") for n in range(1, 5)]


def _in_reach(reach, direction, n):
    return n <= (reach[0] if direction == "UP" else reach[1])


# ---------------------------------------------------------------- reach gates acquisition and fire

@pytest.mark.parametrize("reach", [(1, 0), (0, 1), (1, 1), (2, 1), (3, 2), (4, 4)])
def test_R_164_02_a_target_is_engaged_exactly_when_its_offset_is_within_reach(lib, world_factory, reach):
    """R-164-02, R-008-02: at 100 wu (well inside range 300) a target at each signed offset 1 to 4 is
    engaged iff the offset is within the type's reach in that direction. Vision is opened so only
    reach decides. Every pair here has an in-reach offset, so the positive half trips today."""
    wrong = []
    for direction, n in OFFSETS:
        a_layer, t_layer = layers_for(direction, n)
        got, _ = duel(lib, world_factory, VANGUARD, a_layer, t_layer, 100.0, reach=reach, vision=1.0)
        want = _in_reach(reach, direction, n)
        if got != want:
            wrong.append(f"{direction} {n}: engaged={got}, reach {reach} wants {want}")
    assert not wrong, "; ".join(wrong)


@pytest.mark.parametrize("state", ["idle", "attack_move"])
def test_R_008_02_idle_and_attack_moving_units_engage_one_layer_up_only_with_reach(lib, world_factory, state):
    """R-008-02: the same enemy one layer up, in range and visible (default vision 0.5 gives 350 wu).
    Reach (1, 0): engaged, idle or attack-moving. Reach (0, 0): neither fires; the attack-moving unit
    marches off. Today the reach (1, 0) half fails."""
    got, _ = duel(lib, world_factory, VANGUARD, 2, 3, 200.0, reach=(1, 0), state=state)
    assert got, f"{state}: reach 1 up should engage a visible enemy one layer up in range"
    got, dmg = duel(lib, world_factory, VANGUARD, 2, 3, 200.0, reach=(0, 0), state=state)
    assert not got and dmg == 0.0, f"{state}: reach 0 must not engage across layers"


def test_R_164_02_reach_is_per_unit_type(lib, world_factory):
    """R-164-02: reach is a property of the type. Raider given (1, 0); a Vanguard standing with it, same
    geometry, keeps the default and does not fire up. Two fights in one world, 6,000 wu apart."""
    w = world_factory(n_regions=1)
    assert set_reach(lib, w, RAIDER, 1, 0) == 0
    r = spawn(lib, w, RAIDER, 0, 0.0, 0.0, layer=1)
    rt = spawn(lib, w, SUPPLY, 1, 100.0, 0.0, layer=2)
    v = spawn(lib, w, VANGUARD, 0, 6000.0, 0.0, layer=1)
    vt = spawn(lib, w, SUPPLY, 1, 6100.0, 0.0, layer=2)
    start = {rt: hp(lib, w, rt), vt: hp(lib, w, vt)}
    for _ in range(WINDOW):
        step(lib, w)
    assert hp(lib, w, rt) < start[rt], "control: the Raider (reach 1 up) hit its target"
    assert hp(lib, w, vt) == start[vt], "the Vanguard (reach 0) must not"


def test_R_164_02_no_reach_set_means_todays_same_layer_rule_unchanged(lib, world_factory):
    """Brief G5 invariant: 'The built-in roster's default reach is 0 up, 0 down ... nothing changes
    until a caller sets reach.' A fight with enemies on the same layer (control, they are hit) and on
    every other layer within range (none is hit), every setting at its default. The reach read comes
    first: today the stub writes nothing, so this fails there."""
    w = world_factory(n_regions=1)
    assert read_reach(lib, w, VANGUARD) == (0, 0, 0)
    a = spawn(lib, w, VANGUARD, 0, 0.0, 0.0, layer=2)
    same = spawn(lib, w, SUPPLY, 1, 100.0, 0.0, layer=2)
    others = [spawn(lib, w, SUPPLY, 1, 60.0 + 10.0 * k, 50.0, layer=l) for k, l in enumerate((0, 1, 3, 4))]
    start = {u: hp(lib, w, u) for u in [same] + others}
    for _ in range(WINDOW):
        step(lib, w)
    assert hp(lib, w, same) < start[same], "control: the same-layer enemy is fought"
    assert [hp(lib, w, u) for u in others] == [start[u] for u in others]


def test_R_164_02_reach_leaves_same_layer_fights_exactly_as_they_were(lib, world_factory):
    """Brief invariant: giving a type reach changes nothing for targets on its own layer. Two worlds
    with the same mixed same-layer fight, one with Vanguard reach (4, 4) set, 150 ticks: identical
    positions, hp, targets. The reach read comes first (fails today: stub)."""
    def run(reach):
        w = world_factory(n_regions=1, seed=7)
        if reach:
            assert set_reach(lib, w, VANGUARD, *reach) == 0
            assert read_reach(lib, w, VANGUARD) == (0, *reach)
        ids = []
        for i in range(4):
            ids.append(spawn(lib, w, VANGUARD, 0, 0.0, 120.0 * i, layer=2))
            ids.append(spawn(lib, w, VANGUARD, 1, 250.0, 120.0 * i + 30.0, layer=2))
        for _ in range(150):
            step(lib, w)
        return state_snapshot(lib, w, ids)
    assert run((4, 4)) == run(None)


def test_R_164_02_a_reach_fight_is_repeatable_and_reach_has_an_effect(lib, world_factory):
    """Determinism (R-004-05 style, same seed same ticks): the same cross-layer fight twice gives the
    same state. Control: it differs from the same fight without reach, so the comparison can trip."""
    def run(reach):
        w = world_factory(n_regions=1, seed=11)
        if reach:
            assert set_reach(lib, w, VANGUARD, *reach) == 0
        ids = []
        for i in range(3):
            ids.append(spawn(lib, w, VANGUARD, 0, 0.0, 100.0 * i, layer=1))
            ids.append(spawn(lib, w, VANGUARD, 1, 200.0, 100.0 * i, layer=2))
        for _ in range(150):
            step(lib, w)
        return state_snapshot(lib, w, ids)
    first, second, none = run((1, 1)), run((1, 1)), run(None)
    assert first == second
    assert first != none, "control: reach (1, 1) must change this fight"


# ---------------------------------------------------------------- range multiplier per signed offset

@pytest.mark.parametrize("direction,n", OFFSETS)
def test_Q_008_03_a_range_multiplier_of_one_half_halves_the_engagement_distance(lib, world_factory, direction, n):
    """Brief G5: 'a range multiplier of 0.5 one layer up halves the distance at which it engages',
    here at every signed offset. Vanguard range 300, vision opened. At the default multiplier 1.0 a
    target at 155 wu is engaged (control); with OM_TP_RANGE_<dir>_<n> = 0.5 it is not, while one at
    145 still is."""
    a_layer, t_layer = layers_for(direction, n)
    name = f"OM_TP_RANGE_{direction}_{n}"
    half = RANGE * 0.5
    got, _ = duel(lib, world_factory, VANGUARD, a_layer, t_layer, half + EDGE, reach=(n, n), vision=1.0)
    assert got, "control: at multiplier 1.0 the target at half range + 5 is in range"
    got, _ = duel(lib, world_factory, VANGUARD, a_layer, t_layer, half + EDGE, reach=(n, n), vision=1.0,
                  params={name: 0.5})
    assert not got, f"{name} 0.5: a target at {half + EDGE} wu is beyond the halved range"
    got, _ = duel(lib, world_factory, VANGUARD, a_layer, t_layer, half - EDGE, reach=(n, n), vision=1.0,
                  params={name: 0.5})
    assert got, f"{name} 0.5: a target at {half - EDGE} wu is inside the halved range"


@pytest.mark.parametrize("direction,n", [("UP", 1), ("DOWN", 1), ("UP", 3), ("DOWN", 4)])
def test_Q_008_03_a_range_multiplier_above_one_extends_acquisition_too(lib, world_factory, direction, n):
    """The multiplier moves the whole engagement distance, acquisition included, not just the shot:
    at 1.5 the Vanguard (range 300) engages at 445 wu and not at 455. Control: at 1.0 a target at 445
    is out of range, never held."""
    a_layer, t_layer = layers_for(direction, n)
    name = f"OM_TP_RANGE_{direction}_{n}"
    far = RANGE * 1.5
    got, _ = duel(lib, world_factory, VANGUARD, a_layer, t_layer, far - EDGE, reach=(n, n), vision=1.0,
                  params={name: 1.5})
    assert got, f"{name} 1.5: a target at {far - EDGE} wu is inside the extended range"
    got, _ = duel(lib, world_factory, VANGUARD, a_layer, t_layer, far + EDGE, reach=(n, n), vision=1.0,
                  params={name: 1.5})
    assert not got, f"{name} 1.5: a target at {far + EDGE} wu is beyond it"
    got, _ = duel(lib, world_factory, VANGUARD, a_layer, t_layer, far - EDGE, reach=(n, n), vision=1.0)
    assert not got, "control: at multiplier 1.0 the same target is beyond range 300"


def test_Q_008_03_range_multipliers_are_per_direction_and_per_offset(lib, world_factory):
    """Only the setting named moves. Vanguard on layer 2, reach (2, 2), RANGE_UP_1 = 0.5, a target 150
    wu out (range 300): one layer up is not engaged; one layer down, two up and two down all are."""
    cases = {("UP", 1): False, ("DOWN", 1): True, ("UP", 2): True, ("DOWN", 2): True}
    wrong = []
    for (direction, n), want in cases.items():
        t_layer = 2 + n if direction == "UP" else 2 - n
        got, _ = duel(lib, world_factory, VANGUARD, 2, t_layer, 150.0 + EDGE, reach=(2, 2), vision=1.0,
                      params={"OM_TP_RANGE_UP_1": 0.5})
        if got != want:
            wrong.append(f"{direction} {n}: engaged={got}, wanted {want}")
    assert not wrong, "; ".join(wrong)


def test_Q_008_03_range_multiplier_does_not_touch_same_layer_range(lib, world_factory):
    """Offset 0 has no parameter and stays 1.0: with every RANGE_* at 0.5 a same-layer target at 290 wu
    is still engaged, a cross-layer one at 145 is engaged (control: the halved range reaches it) and
    one at 155 is not."""
    params = {f"OM_TP_RANGE_{d}_{n}": 0.5 for d in ("UP", "DOWN") for n in range(1, 5)}
    got, _ = duel(lib, world_factory, VANGUARD, 2, 3, 145.0, reach=(1, 1), vision=1.0, params=params)
    assert got, "control: a cross-layer target at 145 is inside the halved range"
    got, _ = duel(lib, world_factory, VANGUARD, 2, 3, 155.0, reach=(1, 1), vision=1.0, params=params)
    assert not got, "a cross-layer target at 155 is beyond it"
    got, _ = duel(lib, world_factory, VANGUARD, 2, 2, 290.0, reach=(1, 1), vision=1.0, params=params)
    assert got, "same-layer range is not scaled by the cross-layer multipliers"


# ---------------------------------------------------------------- damage multiplier per signed offset

@pytest.mark.parametrize("mult", [0.5, 2.0])
@pytest.mark.parametrize("direction,n", OFFSETS)
def test_Q_008_03_a_damage_multiplier_applies_exactly(lib, world_factory, direction, n, mult):
    """Brief G5: 'a damage multiplier applies exactly.' The first hit at offset n with
    OM_TP_DAMAGE_<dir>_<n> = m is exactly m times the first hit of the same attacker on the same
    geometry on its own layer (the baseline, measured, so no roster number is pinned)."""
    a_layer, t_layer = layers_for(direction, n)
    _, base = duel(lib, world_factory, VANGUARD, a_layer, a_layer, 100.0)
    assert base > 0.0, "control: the same-layer baseline hit lands"
    _, dmg = duel(lib, world_factory, VANGUARD, a_layer, t_layer, 100.0, reach=(n, n), vision=1.0,
                  params={f"OM_TP_DAMAGE_{direction}_{n}": mult})
    assert dmg == pytest.approx(base * mult, rel=1e-9), f"hit {dmg}, baseline {base} x {mult}"


def test_Q_008_03_damage_multiplier_defaults_to_one_at_every_offset(lib, world_factory):
    """Default 1.0: a cross-layer hit with no setting touched equals the same-layer hit, at all eight
    signed offsets (engine defaults keep the lab's 'range and damage multiplier per layer 1.0')."""
    wrong = []
    for direction, n in OFFSETS:
        a_layer, t_layer = layers_for(direction, n)
        _, base = duel(lib, world_factory, VANGUARD, a_layer, a_layer, 100.0)
        _, dmg = duel(lib, world_factory, VANGUARD, a_layer, t_layer, 100.0, reach=(n, n), vision=1.0)
        if not (dmg > 0.0 and dmg == pytest.approx(base, rel=1e-9)):
            wrong.append(f"{direction} {n}: {dmg} vs baseline {base}")
    assert not wrong, "; ".join(wrong)


def test_Q_008_03_a_damage_multiplier_moves_only_its_own_offset(lib, world_factory):
    """DAMAGE_UP_1 = 2.0 doubles the hit one layer up and leaves one layer down, two up and the same
    layer alone (Vanguard on layer 2, reach (2, 2))."""
    _, base = duel(lib, world_factory, VANGUARD, 2, 2, 100.0)
    wrong = []
    for t_layer, want in ((3, 2.0), (1, 1.0), (4, 1.0), (2, 1.0)):
        _, dmg = duel(lib, world_factory, VANGUARD, 2, t_layer, 100.0, reach=(2, 2), vision=1.0,
                      params={"OM_TP_DAMAGE_UP_1": 2.0})
        if dmg != pytest.approx(base * want, rel=1e-9):
            wrong.append(f"layer {t_layer}: {dmg}, wanted {base * want}")
    assert not wrong, "; ".join(wrong)


# ---------------------------------------------------------------- the attack-target order

@pytest.mark.parametrize("direction,n", [("UP", 1), ("DOWN", 1), ("UP", 2)])
def test_R_164_02_an_attack_target_order_is_bound_by_reach_too(lib, world_factory, direction, n):
    """Brief G5: 'The attack-target order's missing layer check (csrc/unit.c, the drop check gated on
    the order kind) is closed: reach applies to it too.' A Vanguard ordered to attack a visible target
    n layers away at 100 wu: with reach n it hits it (control); with reach 0 it never does. Today the
    order fires across any layers, so the reach-0 half fails, a bug already in the engine."""
    a_layer = 2
    t_layer = a_layer + n if direction == "UP" else a_layer - n

    def run(reach):
        w = world_factory(n_regions=1)
        if reach != (0, 0):
            assert set_reach(lib, w, VANGUARD, *reach) == 0
        open_vision(lib, w, 1.0)
        a, t = solo_pair(lib, w, VANGUARD, a_layer, t_layer, 100.0)
        assert lib.om_command_attack_target(w, a, t) == 0
        start = hp(lib, w, t)
        for _ in range(WINDOW):
            step(lib, w)
        return hp(lib, w, t) < start
    assert run((n, 0) if direction == "UP" else (0, n)), "control: within reach the order fires"
    assert not run((0, 0)), "reach 0: an attack-target order must not fire across layers"


def test_R_164_02_an_attack_target_order_beyond_reach_never_fires(lib, world_factory):
    """Target two layers up, reach 1 up: the order does not fire (reach 2 control fires)."""
    def run(up):
        w = world_factory(n_regions=1)
        assert set_reach(lib, w, VANGUARD, up, 0) == 0
        open_vision(lib, w, 1.0)
        a, t = solo_pair(lib, w, VANGUARD, 0, 2, 100.0)
        lib.om_command_attack_target(w, a, t)
        start = hp(lib, w, t)
        for _ in range(WINDOW):
            step(lib, w)
        return hp(lib, w, t) < start
    assert run(2), "control: reach 2 reaches"
    assert not run(1)
