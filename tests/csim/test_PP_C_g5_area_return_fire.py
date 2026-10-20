# Rule pins: R-008-03@854dcc, R-087-06@2b0850, R-164-02@ac58a3
"""Phase C step G5, reach applied to area attacks and to return fire (E-01 R-008-03, R-164-02;
E-11 R-087-06; register Q-008-03: area multiplier per signed layer offset).

Rules proved: R-008-03 'Given a Bombard's area attack centered on layer 3, When enemies stand on
layers 2 and 4 inside the radius, Then they take damage only at the layer offsets the Bombard's reach
includes (S-164), at the multiplier Q-008-03 sets.' Brief G5: 'The area attack and the return-fire
rule follow the same reach test.' Contract (pp_contract.md section 3): AREA_* are 'multipliers on
area-attack damage at a signed layer offset (positive up: ... above the attacker, or above the area's
centre layer)'.

Engine layers 0 to 4 (A132; the bible's layer 3 is engine layer 2).

Area fixture: a Bombard (aoe 150, range 1200, sensor 300) at the origin, the nearest enemy (the
splash centre, a Supply unit) on its own layer 250 wu out, victims on a ring 90 to 140 wu from the
centre but all farther from the Bombard than the centre is, so the centre is always the target the
Bombard picks. The centre is on the Bombard's own layer so the offset reads the same whether it is
counted from the attacker or from the centre; the report asks which the contract means. Damage is
read on the tick the first splash lands and compared with the same-layer victim hit by that very
shot (the baseline), so no roster number is pinned. DAMAGE_* are left at 1.0 throughout: whether
they also scale area damage is not stated (reported), and these tests do not depend on it.

Red today: the stubbed reach is never stored and area damage filters on `cand->layer != attacker
layer` (csrc/unit.c om_unit_fire_aoe_attack), so no other-layer victim is ever hit; return fire
treats any other-layer attacker as a flinch (om_tac_unit_ai) whatever the reach.
"""
import pytest

from test_PP_C_g5_support import (
    BOMBARD, SUPPLY, VANGUARD, WINDOW, attack_move, dest, duel, hp, open_vision, read_reach,
    set_param, set_reach, spawn, step, target,
)

RING = [(330.0, 60.0), (330.0, -60.0), (340.0, 0.0), (320.0, 110.0), (320.0, -110.0),
        (300.0, 130.0), (300.0, -130.0), (350.0, 30.0)]
CENTRE = (250.0, 0.0)
FAR = [(250.0, 200.0), (250.0, -200.0)]  # 200 wu from the centre, outside the 150 radius


def _splash(lib, world_factory, b_layer, victims, reach=(0, 0), params=None, far=()):
    """Fire one Bombard shot. `victims` is a list of (key, layer); each gets a ring point. `far` is a
    list of (key, layer) placed outside the radius. Returns {key: damage} for every victim, the centre
    under 'centre', measured on the tick the first splash lands."""
    w = world_factory(n_regions=1)
    # TD-VG-T-1: always set, so (0, 0) is named here instead of relying on the engine's default.
    assert set_reach(lib, w, BOMBARD, *reach) == 0
    for name, value in (params or {}).items():
        assert set_param(lib, w, name, value) == 0
    spawn(lib, w, BOMBARD, 0, 0.0, 0.0, layer=b_layer)
    ids = {"centre": spawn(lib, w, SUPPLY, 1, CENTRE[0], CENTRE[1], layer=b_layer)}
    for (key, layer), (x, y) in zip(victims, RING):
        ids[key] = spawn(lib, w, SUPPLY, 1, x, y, layer=layer)
    for (key, layer), (x, y) in zip(far, FAR):
        ids[key] = spawn(lib, w, SUPPLY, 1, x, y, layer=layer)
    start = {k: hp(lib, w, u) for k, u in ids.items()}
    for _ in range(WINDOW):
        step(lib, w)
        if any(hp(lib, w, u) < start[k] for k, u in ids.items()):
            return {k: start[k] - hp(lib, w, u) for k, u in ids.items()}
    return {k: 0.0 for k in ids}


def _victims_around(b_layer, direction):
    """The same-layer baseline victim plus one victim at each offset 1..4 in `direction` (where the
    layer exists), keyed 'same', 'UP1'.. or 'DOWN1'.."""
    out = [("same", b_layer)]
    for n in range(1, 5):
        layer = b_layer + n if direction == "UP" else b_layer - n
        if 0 <= layer <= 4:
            out.append((f"{direction}{n}", layer))
    return out


# ---------------------------------------------------------------- R-008-03: reach gates the splash

@pytest.mark.parametrize("reach", [(0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (2, 2)])
def test_R_008_03_splash_hits_only_the_offsets_the_bombards_reach_includes(lib, world_factory, reach):
    """R-008-03 on a Bombard in the middle layer (engine 2), victims at offsets -2 to +2 inside the
    radius: each takes the full same-layer amount if its offset is within the reach, nothing if not.
    Two victims outside the 150 wu radius (same layer, and one layer up) are never hit: the control
    that the radius still counts. The default-reach read comes first for (0, 0): it fails today
    because the stub writes nothing."""
    if reach == (0, 0):
        assert read_reach(lib, world_factory(n_regions=1), BOMBARD) == (0, 0, 0)
    victims = [("same", 2), ("UP1", 3), ("UP2", 4), ("DOWN1", 1), ("DOWN2", 0)]
    got = _splash(lib, world_factory, 2, victims, reach=reach, far=[("far_same", 2), ("far_up", 3)])
    base = got["same"]
    assert base > 0.0, "control: the same-layer victim is always splashed"
    wrong = []
    for key in ("UP1", "UP2", "DOWN1", "DOWN2"):
        n = int(key[-1])
        within = n <= (reach[0] if key.startswith("UP") else reach[1])
        want = base if within else 0.0
        if got[key] != pytest.approx(want, rel=1e-9):
            wrong.append(f"{key}: {got[key]}, wanted {want}")
    for key in ("far_same", "far_up"):
        if got[key] != 0.0:
            wrong.append(f"{key} outside the radius took {got[key]}")
    assert not wrong, "; ".join(wrong)


@pytest.mark.parametrize("direction,b_layer,reach", [
    ("UP", 0, (4, 0)), ("UP", 0, (3, 0)), ("UP", 0, (2, 0)),
    ("DOWN", 4, (0, 4)), ("DOWN", 4, (0, 3)), ("DOWN", 4, (0, 1)),
])
def test_R_008_03_splash_reach_at_the_far_offsets(lib, world_factory, direction, b_layer, reach):
    """Offsets 3 and 4 (the Bombard on the bottom or top layer so they exist): the same rule, each
    offset hit iff within reach."""
    got = _splash(lib, world_factory, b_layer, _victims_around(b_layer, direction), reach=reach)
    base = got["same"]
    assert base > 0.0, "control: the same-layer victim is splashed"
    limit = reach[0] if direction == "UP" else reach[1]
    wrong = []
    for n in range(1, 5):
        want = base if n <= limit else 0.0
        if got[f"{direction}{n}"] != pytest.approx(want, rel=1e-9):
            wrong.append(f"{direction}{n}: {got[f'{direction}{n}']}, wanted {want}")
    assert not wrong, "; ".join(wrong)


# ---------------------------------------------------------------- Q-008-03: area multiplier per offset

@pytest.mark.parametrize("mult", [0.5, 1.5])
@pytest.mark.parametrize("direction,b_layer", [("UP", 0), ("DOWN", 4)])
@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_Q_008_03_an_area_multiplier_scales_exactly_its_own_offset(lib, world_factory, direction, b_layer, n, mult):
    """OM_TP_AREA_<dir>_<n> = m: the victim n layers away takes exactly m times the same-layer
    victim's damage from the same shot; victims at the other offsets and the same layer are unchanged
    (Bombard reach (4, 4), so every offset is in reach)."""
    got = _splash(lib, world_factory, b_layer, _victims_around(b_layer, direction), reach=(4, 4),
                  params={f"OM_TP_AREA_{direction}_{n}": mult})
    base = got["same"]
    assert base > 0.0, "control: the same-layer victim is splashed"
    wrong = []
    for k in range(1, 5):
        want = base * (mult if k == n else 1.0)
        if got[f"{direction}{k}"] != pytest.approx(want, rel=1e-9):
            wrong.append(f"{direction}{k}: {got[f'{direction}{k}']}, wanted {want}")
    assert not wrong, "; ".join(wrong)


def test_Q_008_03_area_multipliers_default_to_one(lib, world_factory):
    """Default 1.0 at all eight offsets: with reach (2, 2) and no setting touched, every in-reach
    victim takes the same-layer amount."""
    got = _splash(lib, world_factory, 2, [("same", 2), ("UP1", 3), ("UP2", 4), ("DOWN1", 1), ("DOWN2", 0)],
                  reach=(2, 2))
    base = got["same"]
    assert base > 0.0
    assert [got[k] for k in ("UP1", "UP2", "DOWN1", "DOWN2")] == pytest.approx([base] * 4, rel=1e-9)


def test_Q_008_03_an_area_multiplier_does_not_scale_a_direct_shot(lib, world_factory):
    """AREA_* are 'multipliers on area-attack damage': a Vanguard's direct shot one layer up with
    AREA_UP_1 = 0.5 is the unscaled hit (the DAMAGE_* family scales direct fire). Preconditions
    asserted first: with reach it does hit across a layer, and the same shot with DAMAGE_UP_1 = 0.5
    is halved, so the comparison is live."""
    _, plain = duel(lib, world_factory, VANGUARD, 2, 3, 100.0, reach=(1, 0), vision=1.0)
    assert plain > 0.0, "control: a direct shot one layer up lands with reach 1"
    _, halved = duel(lib, world_factory, VANGUARD, 2, 3, 100.0, reach=(1, 0), vision=1.0,
                     params={"OM_TP_DAMAGE_UP_1": 0.5})
    assert halved == pytest.approx(plain * 0.5, rel=1e-9), "control: DAMAGE_UP_1 scales a direct shot"
    _, area_set = duel(lib, world_factory, VANGUARD, 2, 3, 100.0, reach=(1, 0), vision=1.0,
                       params={"OM_TP_AREA_UP_1": 0.5})
    assert area_set == pytest.approx(plain, rel=1e-9)


# ---------------------------------------------------------------- return fire follows the same reach

HIT = 10.0


def _return_fire(lib, world_factory, reach, offset, dist, params=None, victim_layer=2):
    """Vanguard (range 300, sensor 700, id 2) idle at the origin on `victim_layer`; a nearer same-layer
    enemy stands 100 wu away as a decoy; a Supply unit `offset` layers away (signed, + is up) at `dist`
    wu hits it once. The step taken is never the victim's cohort turn, so a target it holds can only
    come from return fire. Returns 'target' (it targets the attacker), 'goal' (it attack-moves to the
    attacker) or 'none'."""
    w = world_factory(n_regions=1)
    if reach != (0, 0):
        assert set_reach(lib, w, VANGUARD, *reach) == 0
    open_vision(lib, w, 1.0)
    for name, value in (params or {}).items():
        assert set_param(lib, w, name, value) == 0
    spawn(lib, w, SUPPLY, 0, -9000.0, 0.0)
    # Test-defect, A163/A164: first step was the victim's cohort turn (tick 1) -> one idle step before spawning the victim and enemies (the first step is now tick 2, not its turn); cause: aligned targeting cohort (parity with the Python, Addendum 63).
    step(lib, w)
    v = spawn(lib, w, VANGUARD, 0, 0.0, 0.0, layer=victim_layer)
    spawn(lib, w, SUPPLY, 1, 0.0, 100.0, layer=victim_layer)
    atk = spawn(lib, w, SUPPLY, 1, float(dist), 0.0, layer=victim_layer + offset)
    assert (lib.om_tactical_tick(w) + 1) % 4 != lib.om_unit_targeting_cohort(w, v), "fixture: cohort turn"
    lib.om_unit_deal_damage(w, atk, v, HIT)
    step(lib, w)
    if target(lib, w, v) == atk:
        return "target"
    has, gx, gy = dest(lib, w, v)
    if has == 1 and (gx, gy) == pytest.approx((float(dist), 0.0), abs=1e-6):
        return "goal"
    return "none"


@pytest.mark.parametrize("ok_reach,bad_reach,offset", [
    ((1, 0), (0, 0), 1),
    ((0, 1), (0, 0), -1),
    ((1, 0), (0, 1), 1),
    ((0, 1), (1, 0), -1),
    ((2, 0), (1, 0), 2),
    ((0, 2), (0, 1), -2),
])
def test_R_164_02_return_fire_in_range_follows_reach(lib, world_factory, ok_reach, bad_reach, offset):
    """R-087-06 with the brief's 'the return-fire rule follows the same reach test': an idle unit hit
    from `offset` layers away by an attacker 280 wu out (inside range 300) targets it when its reach
    includes the offset (control) and otherwise does not (today every other-layer attacker is a
    flinch). The attack-moving variant is left to PP-unit's own P6 tests."""
    assert _return_fire(lib, world_factory, ok_reach, offset, 280.0) == "target"
    assert _return_fire(lib, world_factory, bad_reach, offset, 280.0) == "none"


@pytest.mark.parametrize("ok_reach,bad_reach,offset", [((1, 0), (0, 0), 1), ((0, 1), (1, 0), -1), ((2, 0), (1, 0), 2)])
def test_R_164_02_return_fire_out_of_range_attack_moves_only_within_reach(lib, world_factory, ok_reach, bad_reach, offset):
    """Out of range (900 wu, range 300): within reach the unit attack-moves to the attacker (R-087-06),
    beyond reach it does not."""
    assert _return_fire(lib, world_factory, ok_reach, offset, 900.0) == "goal"
    assert _return_fire(lib, world_factory, bad_reach, offset, 900.0) == "none"


@pytest.mark.parametrize("direction,n", [("UP", 1), ("DOWN", 1), ("UP", 2), ("DOWN", 2)])
def test_Q_008_03_return_fire_range_uses_the_offsets_range_multiplier(lib, world_factory, direction, n):
    """The range at an offset is the roster range times OM_TP_RANGE_<dir>_<n> for return fire as for
    direct fire (brief G5: reach 'applied to direct fire, area attacks and return fire'). Attacker 250
    wu out, Vanguard range 300: multiplier 1.0 targets it (control); 0.5 (150 wu) puts it out of range,
    so the unit attack-moves to it instead. INFERRED: the brief names the multipliers and return fire
    together but states no return-fire example; reported."""
    offset = n if direction == "UP" else -n
    reach = (n, 0) if direction == "UP" else (0, n)
    assert _return_fire(lib, world_factory, reach, offset, 250.0, victim_layer=2) == "target"
    got = _return_fire(lib, world_factory, reach, offset, 250.0, victim_layer=2,
                       params={f"OM_TP_RANGE_{direction}_{n}": 0.5})
    assert got == "goal"
