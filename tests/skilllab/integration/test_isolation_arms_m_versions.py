# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 2 ("the runner uses each version's own lab for its own column and records which lab SHA ran ... Where a V-then measure does not exist in its lab, the cell says
# 'not measured at V-then', never a blank or a zero"), section 5 (one row per version, keyed), section 4 ("If the V-then lab lacks a field the runner does not synthesise it")
"""LI3 arm M on `then` and on `now`: both columns present, keyed by (version, lab sha, arm, layout, seed), each from its own lab; the cells `then` cannot measure say so. One headcount (8 against 16), both spawn orders, both versions: 4 fights.

W1 four rows, four keys; `then` is the stage 3 approval sha and `now` is origin/main; the two versions ran the same layouts (same ids, same units at tick 0) in their own labs and the fight files differ.
W2 `then` has no per-unit `fired`: every firing cell of a `then` row is `not measured at then` / `not measured: ...`, never 0, never an empty list; the cells that file can support (margin, spread, idle, overlap, stopping) are measured.
W3 `now` rows carry the firing cells as numbers.   W4 the flags and `blocks` are computed in `then` rows as in `now` rows (the stopping check needs only positions)."""
import isolation_arms_fixtures as af
import isolation_fixtures as fx

NM = "not measured"


def _both(iso_scratch):
    return af.m_scan("then", iso_scratch, heads=(8,)), af.m_scan("now", iso_scratch, heads=(8,))


def test_w1_both_columns_are_present_keyed_and_each_from_its_own_lab(iso_scratch):
    ir, im = fx.runner(), af.measures()
    then, now = _both(iso_scratch)
    rows = then["rows"] + now["rows"]
    assert len(rows) == 4 and len({ir.row_key(r) for r in rows}) == 4
    assert {r["version"] for r in then["rows"]} == {"then"} and {r["lab_sha"] for r in then["rows"]} == {fx.THEN_SHA}
    assert {r["version"] for r in now["rows"]} == {"now"} and {r["lab_sha"] for r in now["rows"]} == {fx.git(fx.ROOT, "rev-parse", "origin/main")} and then["lab_sha"] != now["lab_sha"]
    assert [r["layout"] for r in then["rows"]] == [r["layout"] for r in now["rows"]], "the same cells, the same layout ids"
    for t, n in zip(then["rows"], now["rows"]):
        dt, dn = im.load_fight(t["fight_path"]), im.load_fight(n["fight_path"])
        place = lambda d: [(u["id"], u["side"], u["role"], u["x"], u["y"]) for u in next(iter(d["frames"]))["units"]]
        assert place(dt) == place(dn), "the same units at tick 0"
        assert t["fight_sha256"] != n["fight_sha256"] and dt["layout_id"] == dn["layout_id"] and dt["seed"] == dn["seed"] == 10
    assert af.roundtrip(then) == then and af.roundtrip(now) == now


def test_w2_what_then_cannot_measure_says_so_and_what_it_can_is_measured(iso_scratch):
    then, _ = _both(iso_scratch)
    for r in then["rows"]:
        assert r["units_firing"] == "not measured at then", "the runner's own cell"
        m = r["measures"]
        for cell in (m["units_firing"], m["predictions"]["count"], m["predictions"]["type"], m["predictions"]["agreement"], m["first_contact_tick"], m["never_fired"]):
            assert isinstance(cell, str) and cell.startswith(NM), cell
        assert isinstance(m["margin_survivors"], int) and isinstance(m["overlap"], dict) and isinstance(m["idle_units"], dict)
        assert isinstance(m["spread"]["0"]["A"], float) and isinstance(m["spread"]["0"]["B"], float), "spread needs positions only, which then writes"
        assert all(isinstance(x, float) or (isinstance(x, str) and x.startswith(NM)) for v in m["spread"].values() if isinstance(v, dict) for x in v.values())
        assert isinstance(r["stopping"]["orders_ended_short"], int)
    p = then["points"][0]
    assert all(isinstance(t, str) and t.startswith(NM) for t in p["first_contact_ticks"])


def test_w3_now_rows_carry_the_firing_cells_as_numbers(iso_scratch):
    _, now = _both(iso_scratch)
    for r in now["rows"]:
        assert isinstance(r["units_firing"], dict) and r["units_firing"]["peak"][0] >= 0
        assert isinstance(r["measures"]["units_firing"], dict) and isinstance(r["measures"]["first_contact_tick"], int)
        assert r["measures"]["predictions"]["agreement"] in ("both_right", "count_wrong_type_right", "count_right_type_wrong", "both_wrong", "n/a")


def test_w4_the_stopping_check_and_flags_do_not_depend_on_the_version(iso_scratch):
    a, im = af.arms(), af.measures()
    for scan in _both(iso_scratch):
        for r in scan["rows"]:
            assert r["stopping"]["orders_ended_short"] == len(im.orders_ended_short(im.load_fight(r["fight_path"]))["alive_at_end"])
            assert r["blocks"] is (r["stopping"]["orders_ended_short"] > 0) and ("orders_ended_short" in r["flags"]) is r["blocks"]
            assert r["flags"] == a.flags_of(im.load_fight(r["fight_path"]))
