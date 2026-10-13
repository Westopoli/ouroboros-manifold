"""ALG-61 Area damage (docs/bible/algorithms.md), proving R-084-03 and R-086-05 (S-084, E-11) in the direct Bombard path (om_unit_fire_aoe_attack).

Every enemy on the attacker's layer within the aoe radius (150) of the target takes ALG-60 damage in
unit-id order until the running total reaches base * AOE_DAMAGE_CAP_MULTIPLIER (4.0); the last hit
is truncated to the cap. ALG-60 here is base * CATEGORY_MULTIPLIER[Siege][target category] (output
multiplier 1 and reduction 0: no ability, no Brace/Fortify/Warden in play). Bombard base damage 17.5
and the roster categories are the E-11 S-082 table. The expectation is computed here from those.
"""
import math

from test_PP_unit_support import BASTION, BOMBARD, INTERCEPTOR, RAIDER, VANGUARD, WARDEN, hp, spawn

BOMBARD_BASE = 17.5
AOE_RADIUS = 150.0
CAP_MULT = 4.0
# ALG-60 matrix row for a Siege attacker; category of each roster type from S-082.
SIEGE_VS = {"strike": 0.20, "line": 1.5, "siege": 1.0}
CATEGORY = {RAIDER: "strike", INTERCEPTOR: "strike", VANGUARD: "line", WARDEN: "line", BASTION: "siege", BOMBARD: "siege"}

TARGET_POS = (600.0, 0.0)
# (type, x, y, faction, layer) in SPAWN order. Spawn order is deliberately not distance order, so unit-id
# order and nearest-first order give different truncation. The target (a Bastion at TARGET_POS) is
# spawned last, so it is the highest id and takes its hit last.
FIELD = [
    (RAIDER, 600.0, 140.0, 1, 0),       # 140 from T: in radius, strike  -> 3.5
    (VANGUARD, 600.0, -151.0, 1, 0),    # 151 from T: just outside the radius -> untouched
    (VANGUARD, 520.0, -60.0, 1, 0),     # 100 from T: in radius, line -> 26.25
    (WARDEN, 700.0, 0.0, 0, 0),         # a friendly of the Bombard in radius -> untouched
    (BASTION, 600.0, 120.0, 1, 0),      # 120 from T: in radius, siege -> 17.5
    (VANGUARD, 600.0, 60.0, 1, 1),      # in radius but on layer 1, the Bombard is on layer 0 -> untouched
    (VANGUARD, 640.0, 30.0, 1, 0),      # 50 from T: line -> would be 26.25, running total reaches 73.5 > 70
    (RAIDER, 610.0, -10.0, 1, 0),       # past the cap: 0
    (BASTION, TARGET_POS[0], TARGET_POS[1], 1, 0),  # the target itself, last id: past the cap, 0
]


def _ref_damage(field, cap_mult=CAP_MULT, order=None, radius=AOE_RADIUS):
    """Expected damage per field index. `order` overrides the iteration order (control only)."""
    cap = BOMBARD_BASE * cap_mult
    total = 0.0
    dmg = [0.0] * len(field)
    for i in (order if order is not None else range(len(field))):
        utype, x, y, faction, layer = field[i]
        if faction != 1 or layer != 0:
            continue
        if math.hypot(x - TARGET_POS[0], y - TARGET_POS[1]) > radius:
            continue
        if total >= cap:
            break
        hit = min(BOMBARD_BASE * SIEGE_VS[CATEGORY[utype]], cap - total)
        dmg[i] = hit
        total += hit
    return dmg


def _fire(lib, world_factory, field):
    w = world_factory(n_regions=1)
    bombard = spawn(lib, w, BOMBARD, 0, 0.0, 0.0, layer=0)
    ids = [spawn(lib, w, t, f, x, y, layer=l) for (t, x, y, f, l) in field]
    before = [hp(lib, w, u) for u in ids]
    lib.om_unit_fire_aoe_attack(w, bombard, ids[-1], AOE_RADIUS)
    return [before[i] - hp(lib, w, u) for i, u in enumerate(ids)]


def test_control_ALG_61_a_wrong_cap_or_order_is_detected(lib, world_factory):
    """Positive control: a reference with cap 5x, cap 3x, nearest-first order, or no layer filter disagrees with the C result, so the exact comparison below can fail."""
    got = _fire(lib, world_factory, FIELD)

    def differs(ref):
        return any(abs(a - b) > 1e-6 for a, b in zip(got, ref))

    assert differs(_ref_damage(FIELD, cap_mult=5.0))
    assert differs(_ref_damage(FIELD, cap_mult=3.0))
    nearest = sorted(range(len(FIELD)), key=lambda i: math.hypot(FIELD[i][1] - TARGET_POS[0], FIELD[i][2] - TARGET_POS[1]))
    assert differs(_ref_damage(FIELD, order=nearest))
    assert differs(_ref_damage([(t, x, y, f, 0) for (t, x, y, f, l) in FIELD]))


def test_ALG_61_in_radius_enemies_in_id_order_capped_at_four_times_base(lib, world_factory):
    """ALG-61 / R-084-03: damage per unit equals the ALG-60 hit (3.5 strike, 26.25 line, 17.5 siege), in spawn (unit-id) order, the last hit truncated so the total is exactly 4 * 17.5 = 70; outside the radius, friendly and other-layer units take nothing."""
    got = _fire(lib, world_factory, FIELD)
    want = _ref_damage(FIELD)
    for i, (g, e) in enumerate(zip(got, want)):
        assert abs(g - e) <= 1e-6, (i, FIELD[i], g, e)
    assert abs(sum(got) - BOMBARD_BASE * CAP_MULT) <= 1e-6
    assert want[6] == 70.0 - (3.5 + 26.25 + 17.5)  # the truncated hit: 22.75 of the 26.25


def test_ALG_61_below_the_cap_every_in_radius_enemy_takes_the_full_hit(lib, world_factory):
    """ALG-61 / R-084-03: with three in-radius enemies (3.5 + 17.5 + 17.5 = 38.5 < 70) nobody is truncated; an enemy 300 wu from the target takes nothing."""
    field = [
        (RAIDER, 600.0, 100.0, 1, 0),
        (BASTION, 560.0, 0.0, 1, 0),
        (INTERCEPTOR, 900.0, 0.0, 1, 0),  # 300 from T: outside
        (BASTION, TARGET_POS[0], TARGET_POS[1], 1, 0),  # the target
    ]
    got = _fire(lib, world_factory, field)
    want = _ref_damage(field)
    assert want == [3.5, 17.5, 0.0, 17.5]
    for i, (g, e) in enumerate(zip(got, want)):
        assert abs(g - e) <= 1e-6, (i, field[i], g, e)
