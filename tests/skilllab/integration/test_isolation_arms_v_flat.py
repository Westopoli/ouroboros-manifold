# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 arm V ("the sight, notice and leash behaviours isolated on flat ground, with one holder (guard stance, one order at tick 0 as its layout names) and one attack-mover,
# Vanguard both sides, mirrored, no features ... Reports: first tick each side sees the other; sensor distance against notice distance per side (both numbers read from the engine, printed); whether the holder steps, fires, returns;
# stand-off count ...; time to first shot. Compared with M on the same ground, so a difference is vision's"), section 1 preconditions 6 (mirror control), 7 (one click), section 4 ("not measured at V-then")
"""LI3 arm V on flat ground, whole runs of the real lab: `run_v_flat` 8 a side, holder A, seed 10, sight on, on `now` and `then` (one fight and its sight-off twin each), and the mirror (holder B) on `now`.

F1 the row is the runner's row plus the arm's keys, arm V, no stated direction (flat ground has no ruling), keyed once.   F2 the lab ran with sight on and one order each: hold_and_attack, the attacker B; at `now` the file has `sights`, `first_seen`, `guard`;
at `then` it has none of them.   F3 the vision report: sensor from the file, notice = weapon range plus the notice margin (R-087-04), first seen, holder, stand-off, first shot; `not measured at then` where the lab wrote nothing.
F4 the twin: the same layout with targeting by sight off, the lab's own `--control sight` (a difference from M's ground is then vision's); `not measured at then`.   F5 never blocks; flags and measures are LI2's.   F6 the mirror control: the other side holds, same ground."""
import pytest

import isolation_arms_fixtures as af
import isolation_fixtures as fx

NM = "not measured"


@pytest.fixture(params=["now", "then"], scope="module")
def vrow(request, iso_scratch):
    return af.v_flat(request.param, iso_scratch)


def test_f1_the_row_is_the_runners_row_plus_the_arms_keys(vrow, iso_scratch):
    ir = fx.runner()
    assert set(vrow) == af.ROW_KEYS | af.V_EXTRA, set(vrow) ^ (af.ROW_KEYS | af.V_EXTRA)
    assert vrow["error"] is None and vrow["arm"] == "V" and vrow["kind"] == "flat" and vrow["seed"] == 10 and (vrow["heads"], vrow["holder"]) == (8, "A")
    assert vrow["layout"] == af.arms().layout_id_v(8, "A") and vrow["lab_sha"] == ir.resolve_version(vrow["version"], repo=fx.ROOT).sha
    assert vrow["expected_winner"] is None and vrow["part_word"] == "no stated direction"
    assert vrow["fight_path"].startswith(str(iso_scratch)) and vrow["fight_sha256"] == fx.sha256(vrow["fight_path"])
    assert len(ir.row_key(vrow)) == 5 and af.roundtrip(vrow) == vrow


def test_f2_sight_on_one_holder_one_attacker_one_order_each(vrow):
    im = af.measures()
    doc = im.load_fight(vrow["fight_path"])
    assert doc["sight"] == "on" == vrow["sight"] and doc["layout_id"] == vrow["layout"]
    assert doc["orders"]["mode"] == "hold_and_attack" and doc["orders"]["attacker"] == "B"
    first = next(iter(doc["frames"]))
    assert first["alive"] == [8, 8] and {u["role"] for u in first["units"]} == {"Vanguard"}
    assert "built_features" not in doc, "flat ground: no feature"
    if vrow["version"] == "now":
        assert doc["orders"]["guard"] is True and doc["sights"] == {"Vanguard": 700.0} and set(doc["result"]["first_seen"]) == {"A", "B"}
    else:
        assert "sights" not in doc and "first_seen" not in doc["result"], "the then lab writes none; the arm does not synthesise it"


def test_f3_the_vision_report(vrow):
    from scripts.skilllab.invariants import NOTICE_MARGIN
    im = af.measures()
    doc, vis = im.load_fight(vrow["fight_path"]), vrow["vision"]
    assert vis == af.roundtrip(af.arms().vision_report(doc, vrow["version"]))
    assert vis["first_shot_tick"] == im.first_contact_tick(doc) or (isinstance(vis["first_shot_tick"], str) and vis["first_shot_tick"].startswith(NM))
    assert isinstance(vis["standoff_count"], int) and vis["standoff_count"] >= 0
    assert vis["holder"]["side"] == "A" and all(isinstance(vis["holder"][k], bool) for k in ("stepped", "fired", "returned"))
    if vrow["version"] == "now":
        assert vis["sensor"] == doc["sights"] == {"Vanguard": 700.0}
        assert vis["notice"] == {"Vanguard": pytest.approx(doc["ranges"]["Vanguard"] * (1 + NOTICE_MARGIN))} and vis["notice"]["Vanguard"] < vis["sensor"]["Vanguard"]
        assert vis["first_seen"] == doc["result"]["first_seen"]
    else:
        assert vis["sensor"] == vis["notice"] == vis["first_seen"] == "not measured at then"


def test_f4_the_sight_off_twin_is_the_labs_own_control(vrow, iso_scratch):
    im = af.measures()
    twin = vrow["twin"]
    if vrow["version"] == "then":
        assert twin == "not measured at then", "the then lab has no `--control sight`"
        return
    assert twin["sight"] == "off" and set(twin["result"]) == fx.RESULT_KEYS and twin["fight_path"] != vrow["fight_path"] and twin["fight_path"].startswith(str(iso_scratch))
    assert twin["fight_sha256"] == fx.sha256(twin["fight_path"]) and isinstance(twin["invalid"], bool)
    doc = im.load_fight(twin["fight_path"])
    assert doc["sight"] == "off" and doc["layout_id"] == vrow["layout"] and "sights" not in doc
    assert (doc["result"]["winner"], doc["result"]["survivors"], doc["result"]["ticks"], doc["result"]["end"]) == (twin["result"]["winner"], twin["result"]["survivors"], twin["result"]["last_tick"], twin["result"]["end"])


def test_f5_never_blocks_and_the_cells_are_li2s(vrow):
    a, im = af.arms(), af.measures()
    doc = im.load_fight(vrow["fight_path"])
    assert vrow["blocks"] is False, "only the movement-stopping check of arm M blocks (Westley 2026-11-24)"
    assert vrow["flags"] == a.flags_of(doc) and not set(vrow) & af.PASS_MARK_KEYS
    assert vrow["measures"] == af.roundtrip(im.measure_fight(doc, spread_ticks=list(a.DRAFT_SPREAD_TICKS)))


def test_f6_the_mirror_control_the_other_side_holds_on_the_same_ground(iso_scratch):
    im = af.measures()
    one, two = af.v_flat("now", iso_scratch, holder="A"), af.v_flat("now", iso_scratch, holder="B")
    assert two["error"] is None and two["holder"] == "B" and two["layout"] != one["layout"] and two["vision"]["holder"]["side"] == "B"
    d1, d2 = im.load_fight(one["fight_path"]), im.load_fight(two["fight_path"])
    assert d2["orders"]["mode"] == "hold_and_attack" and d2["orders"]["attacker"] == "A" and d2["orders"]["guard"] is True
    assert next(iter(d1["frames"]))["units"] == next(iter(d2["frames"]))["units"], "the same units at the same places; only who holds differs"
    assert one["blocks"] is False and two["blocks"] is False
