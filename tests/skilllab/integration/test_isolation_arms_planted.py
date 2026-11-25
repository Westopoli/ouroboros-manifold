# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 arm M ("Arrival and finishing, per unit: the stopping check ... orders ended short must be 0 ... a finding, not a pass or fail"),
# arm V (sensor against notice distance, first seen, holder steps/fires/returns, stand-off count, time to first shot), section 1.3 ("Flags are signals, never verdicts"), section 8 ruling 2
# ("the movement-stopping check (an order ended short, M arm) blocks a landing. Role and layout flags stay labels"), section 3 readings ("a side wins that he said wins"; "no stated direction")
"""LI3 pure checks on planted fight documents (om-fight-2 with a known answer; no engine, no fight, a second each). Each detector has its positive control (the clean document) beside it.

P1 `stopping_check(doc)`: a planted unit ended short (still 1,000 ticks, 1,600 wu from the point, no target, no enemy near) is counted and listed by id with its tick and place; the clean document counts 0; a unit that died short is listed
apart and never counted; a document whose orders carry no point (a trap's groups) is `not measured` and never 0.   P2 `blocks_of(doc, arm)`: True only for arm M with an order ended short; arm V and every other flag never block.
P3 `flags_of(doc)`: names (a signal list), never a pass mark: clean `[]`; a stall `defect`; `invalid` when the lab marked the fight invalid; an ended-short unit `orders_ended_short`.
P4 `vision_report(doc, version_name)`: sensor distance per role is `doc["sights"]`, notice distance per role is the weapon range plus `invariants.NOTICE_MARGIN` of it (E-11 R-087-04: "never the sensor radius"), first seen per side is
`result.first_seen`; the holder (hold_and_attack: the side that is not the attacker) stepped / fired / returned; stand-off count; time to first shot is LI2's `first_contact_tick`; a document with no `sights` says `not measured at <version>`, never 0.
P5 `part_word_m(points)`: the C0 direction (README 4: "the larger force wins"), the three words of LI2's `reading`; defect cells are not read; `part_word_v(winner, expected)`."""
import copy

import pytest

import isolation_arms_fixtures as af

NM = "not measured"


def test_control_the_planted_documents_are_valid_lab_files():
    from scripts.skilllab.arena import snapshot
    for d in (af.clean_doc(), af.short_doc(), af.short_doc(also_dead=True), af.draw_doc(), af.vision_doc(), af.vision_doc(both_alive=True)):
        assert snapshot.validate(d) == []


def test_p1_an_order_ended_short_is_found_listed_by_id_and_a_clean_run_is_not_flagged():
    a, im = af.arms(), af.measures()
    bad = a.stopping_check(af.short_doc())
    assert bad["orders_ended_short"] == 1 and bad["blocks"] is True
    (u,) = bad["units"]
    assert u["id"] == 1 and u["x"] == 400.0 and u["y"] == 400.0 and u["tick"] == 1600 and u["since"] <= 1600 - im.DRAFT_STUCK_TICKS
    clean = a.stopping_check(af.clean_doc())
    assert clean["orders_ended_short"] == 0 and clean["units"] == [] and clean["blocks"] is False
    assert a.stopping_check(af.short_doc())["orders_ended_short"] == len(im.orders_ended_short(af.short_doc())["alive_at_end"]), "the count is LI2's, not a second reading"


def test_p1_a_unit_that_died_short_is_listed_apart_and_never_counted():
    a = af.arms()
    res = a.stopping_check(af.short_doc(also_dead=True))
    assert res["orders_ended_short"] == 1 and [u["id"] for u in res["units"]] == [1]
    assert [u["id"] for u in res["died_short"]] == [3] and res["blocks"] is True


def test_p1_no_destination_in_the_file_is_not_measured_never_zero():
    a = af.arms()
    d = af.short_doc()
    d["orders"] = {"attacker": None, "mode": "groups", "point": [2000.0, 2000.0]}
    res = a.stopping_check(d)
    assert str(res["orders_ended_short"]).startswith(NM) and res["units"] == [] and res["blocks"] is None
    d2 = copy.deepcopy(af.short_doc())
    del d2["orders"]["point"]
    assert str(a.stopping_check(d2)["orders_ended_short"]).startswith(NM)


def test_p2_only_the_stopping_check_in_arm_m_blocks():
    a = af.arms()
    assert a.blocks_of(af.short_doc(), "M") is True
    assert a.blocks_of(af.clean_doc(), "M") is False
    assert a.blocks_of(af.draw_doc(), "M") is False, "a stall is a defect flag, a label, never a block"
    assert a.blocks_of(af.short_doc(), "V") is False, "arm V never blocks, whatever it finds"
    assert a.blocks_of(af.vision_doc(both_alive=True), "V") is False
    invalid = af.clean_doc()
    invalid["invalid"] = True
    assert a.blocks_of(invalid, "M") is False, "a rule-checker flag is a label"


def test_p3_flags_are_names_of_signals_never_a_pass_mark():
    a = af.arms()
    assert a.flags_of(af.clean_doc()) == []
    assert "defect" in a.flags_of(af.draw_doc())
    assert "orders_ended_short" in a.flags_of(af.short_doc())
    invalid = af.clean_doc()
    invalid["invalid"] = True
    assert a.flags_of(invalid) == ["invalid"]
    for d in (af.clean_doc(), af.draw_doc(), af.short_doc(), invalid):
        flags = a.flags_of(d)
        assert isinstance(flags, list) and all(isinstance(f, str) for f in flags) and flags == sorted(set(flags))
        assert not set(flags) & af.PASS_MARK_KEYS and "pass" not in flags


def test_p4_sensor_is_the_files_and_notice_is_the_weapon_range_plus_the_margin():
    from scripts.skilllab.invariants import NOTICE_MARGIN
    a = af.arms()
    rep = a.vision_report(af.vision_doc(), "now")
    assert rep["sensor"] == {"Vanguard": 700.0}
    assert rep["notice"] == {"Vanguard": pytest.approx(300.0 * (1 + NOTICE_MARGIN))}
    assert rep["notice"]["Vanguard"] < rep["sensor"]["Vanguard"], "an enemy seen beyond the notice distance is not acquired (R-087-04)"
    assert rep["first_seen"] == {"A": 440, "B": 460}


def test_p4_the_holder_steps_fires_and_returns_or_does_not():
    a = af.arms()
    moved = a.vision_report(af.vision_doc(holder_steps=True, holder_fires=True), "now")["holder"]
    assert moved["side"] == "A" and moved["stepped"] is True and moved["fired"] is True and moved["returned"] is True
    assert a.DRAFT_HOLDER_STEP_WU < 40.0, "the planted step is 40 wu; the DRAFT step threshold must be under it"
    still = a.vision_report(af.vision_doc(holder_steps=False, holder_fires=False), "now")["holder"]
    assert still["side"] == "A" and still["stepped"] is False and still["fired"] is False and still["returned"] is False


def test_p4_stand_off_count_and_time_to_first_shot():
    a, im = af.arms(), af.measures()
    ok = a.vision_report(af.vision_doc(), "now")
    assert ok["standoff_count"] == 0
    assert ok["first_shot_tick"] == im.first_contact_tick(af.vision_doc()) == 600
    stuck = a.vision_report(af.vision_doc(both_alive=True), "now")
    assert stuck["standoff_count"] == 1, "B1 stands still at (1700, 2000), 900 wu from the holders, both sides alive at the end: one unit arrived beyond notice"
    assert a.vision_report(af.draw_doc(), "now")["first_shot_tick"] == 300
    assert a.vision_report(af.vision_doc(holder_fires=False), "now")["first_shot_tick"] == 1000


def test_p4_a_file_the_lab_of_that_version_did_not_write_is_not_measured_at_the_version():
    a = af.arms()
    d = af.vision_doc()
    del d["sights"], d["result"]["first_seen"]
    rep = a.vision_report(d, "then")
    for key in ("sensor", "notice", "first_seen"):
        assert rep[key] == "not measured at then", key
    nofire = af.doc([(1, "A", "Vanguard"), (11, "B", "Vanguard")], lambda u, t: (1000.0, 1000.0), with_fired=False)
    assert str(a.vision_report(nofire, "then")["first_shot_tick"]).startswith(NM)


def test_p5_the_c0_direction_word():
    a = af.arms()
    point = lambda e, outcomes, own=16: {"enemy_heads": e, "own_heads": own, "outcomes": outcomes, "won": all(o == "side0" for o in outcomes)}
    good = [point(8, ["side0", "side0"]), point(16, ["side0", "side1"]), point(24, ["side1", "side1"])]
    assert a.part_word_m(good) == "pass", "the larger force wins in every read cell; equal numbers are not read"
    wrong = [point(8, ["side0", "side1"]), point(24, ["side1", "side1"])]
    assert a.part_word_m(wrong) == "fail"
    assert a.part_word_m([point(16, ["side0", "side1"])]) == "no stated direction", "only the mirror cell was scanned: no larger force to read"
    defect = [point(8, ["draw", "side0"]), point(24, ["cap", "side1"])]
    assert a.part_word_m(defect) == "no stated direction", "a draw or cap is a defect, never a result, and is not read"
    assert a.part_word_m([]) == "no stated direction"


def test_p5_the_stated_direction_word_for_a_fight_with_a_ruling():
    a = af.arms()
    assert a.part_word_v("A", "A") == "pass" and a.part_word_v("B", "A") == "fail"
    assert a.part_word_v("A", None) == "no stated direction" and a.part_word_v("B", "draw") == "no stated direction"
