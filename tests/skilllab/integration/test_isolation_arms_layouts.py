# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 arm M ("one role (Vanguard) both sides ... flat featureless ground ... mirrored placement", "8 to 48 against 16 and 16 against 16 mirror")
# and arm V ("one holder and one attack-mover, Vanguard both sides, mirrored, no features"); section 1 precondition 5 (same units, same values, both sides) and 7 (one click per side)
"""LI3 layouts: the flat grounds the arms hand to the runner, as pure functions (no fight, a second each).

Spec 3 M: "On: one role (Vanguard) both sides, attack-move at tick 0 to the layout's shared point, flat featureless ground ... mirrored placement. Off: sight, features, roles other than Vanguard, abilities."
Spec 1.5: "Same units, same values on both sides." Spec 1.7: "One attack-move click per side at tick 0, never another."

Y1 `m_layout(own, enemy, swap)` is a lab layout (the lab's `check_layout` R1 to R7 passes) for every enemy headcount of the scan, both orders: Vanguards only, open_field on small_flat, no features, orders `both_same_point`, walkers (`movement` "walk", the stage 3 and 4 ground; `movement="fly"` is the flyer variant).
Y2 side A is `own` when not swap and `enemy` when swap, always west and spawned first; `swap` is exactly exchanging the two arguments.   Y3 equal numbers are a mirror (`run.is_mirror`) and the two spawn orders are the same layout.
Y4 both sides stand level with each other (same mean y) and A stands west of B; no two units closer than the 30 wu of R2.   Y5 deterministic; `layout_toml` is the text the lab reads (`dump_toml` plus the `movement` line it drops).
Y6 `v_layout(heads, holder)`: orders `hold:A` or `hold:B`, equal numbers, mirror, same positions whichever side holds, valid.   Y7 ids: `L-####`, unique per (own, enemy, swap) and per (heads, holder), in no catalogue of `then` or this tree."""
import re
import tomllib

import isolation_arms_fixtures as af
import isolation_fixtures as fx

SCAN = range(8, 49)


def _valid(layout):
    from scripts.skilllab.catalogue.produce import check_layout, presets, rules
    return check_layout(layout, presets(), rules())


def test_y1_every_scan_layout_is_a_lab_layout_of_one_role_on_flat_ground():
    a = af.arms()
    for swap in (False, True):
        for enemy in SCAN:
            lay = a.m_layout(16, enemy, swap)
            assert _valid(lay) == [], (enemy, swap)
            assert lay["situation"] == "open_field" and lay["landscape"] == "small_flat"
            assert lay["orders"] == "both_same_point"
            assert not lay.get("features") and lay["movement"] == "walk", "walkers: the stage 3 and 4 layouts and the beta's ground era walk (spec 8 ruling 5)"
            roles = {u["role"] for key in ("side_a", "side_b") for u in lay[key]["units"]}
            assert roles == {"Vanguard"}
            assert {len(lay["side_a"]["units"]), len(lay["side_b"]["units"])} == {16, enemy}
            assert lay["side_a"]["headcount"] == len(lay["side_a"]["units"]) and lay["side_b"]["headcount"] == len(lay["side_b"]["units"])


def test_y2_swap_is_exactly_exchanging_own_and_enemy():
    a = af.arms()
    plain, swapped = a.m_layout(16, 24, False), a.m_layout(16, 24, True)
    assert len(plain["side_a"]["units"]) == 16 and len(plain["side_b"]["units"]) == 24
    assert len(swapped["side_a"]["units"]) == 24 and len(swapped["side_b"]["units"]) == 16
    exch = a.m_layout(24, 16, False)
    for key in ("side_a", "side_b"):
        assert swapped[key] == exch[key]
    assert swapped["orders"] == exch["orders"] == "both_same_point"


def test_y3_equal_numbers_are_a_mirror_and_both_spawn_orders_are_one_layout():
    from scripts.skilllab.arena.run import is_mirror
    a = af.arms()
    one, two = a.m_layout(16, 16, False), a.m_layout(16, 16, True)
    assert is_mirror(one) and is_mirror(two)
    assert one["side_a"] == two["side_a"] and one["side_b"] == two["side_b"], "16 v 16 is the same layout in both orders; the fight differs only in who is called own"
    assert not is_mirror(a.m_layout(16, 17, False))


def test_y4_both_sides_stand_level_with_a_west_of_b_and_clear_of_each_other():
    a = af.arms()
    for enemy in (8, 16, 33, 48):
        lay = a.m_layout(16, enemy, False)
        mean = lambda key, f: sum(f(u) for u in lay[key]["units"]) / len(lay[key]["units"])
        assert abs(mean("side_a", lambda u: u["y"]) - mean("side_b", lambda u: u["y"])) <= 40.0, "level to within one unit pitch (a partial last row of a block); a geometry check of this test, not a game threshold"
        assert mean("side_a", lambda u: u["x"]) < mean("side_b", lambda u: u["x"])
        pts = [(u["x"], u["y"]) for key in ("side_a", "side_b") for u in lay[key]["units"]]
        assert min(((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5 for i, p in enumerate(pts) for q in pts[i + 1:]) >= 30.0


def test_y5_deterministic_and_the_text_the_lab_reads_carries_every_field():
    a = af.arms()
    assert a.m_layout(16, 20, False) == a.m_layout(16, 20, False)
    for lay in (a.m_layout(16, 20, True), a.m_layout(16, 20, False, movement="fly"), a.v_layout(8, "B")):
        text = a.layout_toml(lay)
        assert text == a.layout_toml(lay)
        back = tomllib.loads(text)           # the lab reads TOML; `dump_toml` alone drops `movement`, so the text must carry it
        assert back["id"] == lay["id"] and back["orders"] == lay["orders"] and back.get("movement") == lay.get("movement")
        for key in ("side_a", "side_b"):
            assert back[key]["headcount"] == lay[key]["headcount"]
            assert [(u["role"], u["x"], u["y"], u["layer"]) for u in back[key]["units"]] == [(u["role"], u["x"], u["y"], u["layer"]) for u in lay[key]["units"]]
    assert tomllib.loads(a.layout_toml(a.m_layout(16, 20, False)))["movement"] == "walk"
    assert a.m_layout(16, 20, False, movement="fly").get("movement") in (None, "fly"), "flyers: the units the movement fix steers"


def test_y6_the_vision_layout_has_one_holder_one_attacker_and_a_mirror():
    from scripts.skilllab.arena.run import is_mirror
    a = af.arms()
    holds_a, holds_b = a.v_layout(8, "A"), a.v_layout(8, "B")
    assert holds_a["orders"] == "hold:A" and holds_b["orders"] == "hold:B"
    for lay in (holds_a, holds_b):
        assert _valid(lay) == [] and is_mirror(lay)
        assert lay["situation"] == "open_field" and not lay.get("features")
        assert {u["role"] for key in ("side_a", "side_b") for u in lay[key]["units"]} == {"Vanguard"}
        assert len(lay["side_a"]["units"]) == len(lay["side_b"]["units"]) == 8
    assert holds_a["side_a"] == holds_b["side_a"] and holds_a["side_b"] == holds_b["side_b"], "the mirror control: the same ground, the other side holds"
    assert a.V_HEADS >= 8


def test_y7_layout_ids_are_four_digits_unique_and_never_a_catalogue_layout():
    a = af.arms()
    ids = {}
    for swap in (False, True):
        for enemy in SCAN:
            ids[("M", 16, enemy, swap)] = a.m_layout(16, enemy, swap)["id"]
    ids[("V", 8, "A")], ids[("V", 8, "B")] = a.v_layout(8, "A")["id"], a.v_layout(8, "B")["id"]
    assert all(re.fullmatch(r"L-\d{4}", v) for v in ids.values())
    assert len(set(ids.values())) == len(ids)
    assert a.m_layout(16, 16, False)["id"] != a.m_layout(16, 16, True)["id"], "two fights of one cell must not write one fight file"
    taken = af.catalogue_ids(fx.THEN_SHA) | af.catalogue_ids("HEAD") | af.catalogue_ids("origin/main")
    assert not set(ids.values()) & taken
    assert a.layout_id_m(16, 24, True) == a.m_layout(16, 24, True)["id"] and a.layout_id_v(8, "B") == a.v_layout(8, "B")["id"]
