# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 (arm W: the layout as authored beside its control twin; arm F: one ground feature, roles neutral, beside its twin), section 5 (comparison row), section 4 (not measured at then; invalid fights listed)
"""LI4-FW whole-run, L-0055 (chokepoint), on the real labs of `then` (4fa618ce7) and `now` (origin/main 893a5af7f). One chunk: arm W (seeds 10 and 1, layout and control twin, both versions: 8 fights) and
arm F (seed 10, neutral roles, layout and twin, both versions: 4 fights), about 3 to 4 minutes; run the file under `--dist loadfile` so one worker makes the fights once. Red until
`scripts/skilllab/arena/isolation_fw.py` exists. The known facts are in isolation_fw_real.py (dumped from real runs, with the one survey difference said there).

W1 `run_arms` rows: one per (version, arm, layout, variant, seed), nested in that order, every row the LI1 keys plus `variant`, `invalid`, `measures`; no error row (a fight the checker marks invalid is a row).
W2 the known results of the layout and of its control twin at both versions (arm W: the layout as authored and approved).   W3 `invalid`: the rules listed at `now` (`[]` when valid), `not measured at then` (the lab at then has no rule checker).
W4 `not measured` where `then` lacks a measure, never 0; margin and result measured.   W5 `measures` is LI2's `measure_fight` of the fight file.   W6 seed 1 gives the seed 10 result (DRAFT-seeds).
F1 arm F rows: neutral roles (Vanguard both sides), the authored positions and headcounts, the twin is the same units on ground without the feature.
C1 the comparison row: his ruling, the approved expected winner, then/now/fix results, the control twin, same-or-changed by the named rule, the first differing arm, predictions and rate shown not scored."""
import json
from pathlib import Path

import pytest

import isolation_fixtures as fx
import isolation_fw_real as real

LAYOUT = "L-0055"
FACTS = real.FACTS[LAYOUT]
CELL_KEYS = {"version", "lab_sha", "seed", "winner", "survivors", "last_tick", "end", "defect", "winners", "winner_counts", "invalid", "units_firing", "predictions", "error"}
SHAS = {"then": fx.THEN_SHA, "now": real.NOW_SHA}


def _w(rows, version, variant, seed=10):
    return real.pick(rows, version, "W", variant, seed)


def test_w1_rows_are_one_per_run_in_order_with_the_fw_keys(iso_scratch):
    rows = real.runs(iso_scratch, LAYOUT).w
    order = [(v, "W", LAYOUT, var, s) for v in ("then", "now") for var in ("layout", "control") for s in (10, 1)]
    assert [(r["version"], r["arm"], r["layout"], r["variant"], r["seed"]) for r in rows] == order, "versions, then layouts, then layout/control, then seeds"
    for r in rows:
        assert set(r) == real.FW_KEYS
        assert r["error"] is None, r["error"]
        assert r["lab_sha"] == SHAS[r["version"]]
        assert Path(r["fight_path"]).is_absolute() and Path(r["fight_path"]).is_file() and r["fight_sha256"] == fx.sha256(r["fight_path"])
        assert str(iso_scratch) in r["fight_path"], "fights are written under the scratch root"
    assert len({r["fight_path"] for r in rows}) == 8
    assert fx.runner().read_rows(Path(iso_scratch) / ("w-%s" % LAYOUT) / "rows.jsonl") == rows
    names = {r["variant"]: Path(r["fight_path"]).name for r in rows if r["seed"] == 10 and r["version"] == "now"}
    assert names["control"] == "%s-control-s10.fight.json" % LAYOUT and names["layout"] == "%s-s10.fight.json" % LAYOUT


@pytest.mark.parametrize("variant", ("layout", "control"))
@pytest.mark.parametrize("version", ("then", "now"))
def test_w2_known_results(iso_scratch, version, variant):
    winner, surv, last, end = FACTS[variant][version]
    for seed in (10, 1):
        row = _w(real.runs(iso_scratch, LAYOUT).w, version, variant, seed)
        res = row["measures"]["result"]
        assert (res["winner"], res["survivors"], res["last_tick"], res["end"]) == (winner, surv, last, end)
        assert res["defect"] is (winner in ("draw", "cap")), "a draw or a cap is a defect cell (spec 4), never a result"
        assert row["margin"] == surv[0] - surv[1] == row["measures"]["margin_survivors"]
        assert (row["result"]["survivors"], row["result"]["last_tick"], row["result"]["end"]) == (surv, last, end)


@pytest.mark.parametrize("variant", ("layout", "control"))
def test_w3_invalid_lists_the_rule_at_now_and_is_not_measured_at_then(iso_scratch, variant):
    rows = real.runs(iso_scratch, LAYOUT).w
    for seed in (10, 1):
        assert _w(rows, "now", variant, seed)["invalid"] == FACTS["invalid_now"][variant], "listed, and the row is still a result (the lab exits 2 on it; LI1 run_one turns that into an error row)"
        assert isinstance(_w(rows, "then", variant, seed)["invalid"], str) and _w(rows, "then", variant, seed)["invalid"].startswith("not measured")


def test_w4_not_measured_at_then_never_zero(iso_scratch):
    rows = real.runs(iso_scratch, LAYOUT).w
    for variant in ("layout", "control"):
        then, now = _w(rows, "then", variant), _w(rows, "now", variant)
        assert then["units_firing"] == "not measured at then"
        m = then["measures"]
        for key in ("units_firing", "first_contact_tick", "never_fired"):
            assert isinstance(m[key], str) and m[key].startswith("not measured"), key
        assert all(str(v).startswith("not measured") for v in m["predictions"].values())
        assert isinstance(m["margin_survivors"], int) and isinstance(m["margin_hp_share"], float), "what the file supports stays measured"
        assert isinstance(now["units_firing"], dict) and set(now["measures"]["predictions"]) >= {"count", "type", "agreement"}
        assert now["measures"]["predictions"]["count"] in ("A", "B", "tie") and now["measures"]["predictions"]["type"] in ("A", "B", "tie")


@pytest.mark.parametrize("version", ("then", "now"))
def test_w5_measures_are_lis_measure_fight_of_the_fight_file(iso_scratch, version):
    im = real.im()
    row = _w(real.runs(iso_scratch, LAYOUT).w, version, "layout")
    expect = json.loads(json.dumps(im.measure_fight(im.load_fight(row["fight_path"]))))
    assert row["measures"] == expect


def test_w6_seed_1_gives_the_seed_10_fight(iso_scratch):
    rows = real.runs(iso_scratch, LAYOUT).w
    for version in ("then", "now"):
        for variant in ("layout", "control"):
            a, b = _w(rows, version, variant, 10), _w(rows, version, variant, 1)
            assert (a["result"], a["margin"]) == (b["result"], b["margin"]), "DRAFT-seeds: seeds change nothing in lab fights"


def test_f1_arm_f_is_neutral_roles_against_the_same_units_without_the_feature(iso_scratch):
    r = real.runs(iso_scratch, LAYOUT)
    f = r.f
    assert [(x["version"], x["arm"], x["layout"], x["variant"], x["seed"]) for x in f] == [(v, "F", LAYOUT, var, 10) for v in ("then", "now") for var in ("layout", "control")]
    for x in f:
        assert set(x) == real.FW_KEYS and x["error"] is None, x["error"]
    for version in ("then", "now"):
        lay, ctl = real.doc_of(real.pick(f, version, "F", "layout")), real.doc_of(real.pick(f, version, "F", "control"))
        authored = real.doc_of(_w(r.w, version, "layout"))
        for doc in (lay, ctl):
            roles = {u["role"] for u in doc["frames"][0]["units"]}
            assert roles == {"Vanguard"}, "roles neutral: Vanguard both sides"
            assert doc["ranges"] == {"Vanguard": 300.0}
        assert {u["role"] for u in authored["frames"][0]["units"]} != {"Vanguard"}, "control: the W layout is the roster as authored"
        place = lambda d: [(u["id"], u["side"], u["x"], u["y"]) for u in d["frames"][0]["units"]]
        assert place(lay) == place(authored) == place(ctl), "the positions and headcounts as authored, in the twin too"
        assert Path(ctl["layout_path"]).name == "%s-control.toml" % LAYOUT or Path(ctl["layout_path"]).name.endswith("-control.toml"), "the twin is the lab's control twin (features emptied)"
        assert not Path(lay["layout_path"]).name.endswith("-control.toml")
        assert real.pick(f, version, "F", "layout")["fight_sha256"] != _w(r.w, version, "layout")["fight_sha256"], "neutral roles are a different fight from the authored one"


def _check_cell(cell, row, version):
    assert set(cell) == CELL_KEYS
    res = row["measures"]["result"]
    assert (cell["version"], cell["lab_sha"], cell["seed"]) == (version, SHAS[version], 10)
    assert (cell["winner"], cell["survivors"], cell["last_tick"], cell["end"], cell["defect"]) == (res["winner"], res["survivors"], res["last_tick"], res["end"], res["defect"])
    assert cell["invalid"] == row["invalid"] and cell["units_firing"] == row["measures"]["units_firing"]
    pr = row["measures"]["predictions"]
    assert cell["predictions"] == {"count": pr["count"], "type": pr["type"], "agreement": pr["agreement"]}
    assert cell["error"] is None


def test_c1_comparison_row(iso_scratch):
    r = real.runs(iso_scratch, LAYOUT)
    row = real.comparison(iso_scratch, LAYOUT)
    expected, rate = real.EXPECTED[LAYOUT]
    assert {"layout", "kind", "ruling", "expected_winner", "predict_rate", "then", "now", "fix", "control", "f", "matches_expected", "rate", "same_or_changed", "seeds_flipped",
            "first_differing_arm", "arm_readings", "rule"} <= set(row)
    assert (row["layout"], row["kind"], row["expected_winner"], row["predict_rate"]) == (LAYOUT, real.KIND[LAYOUT], expected, rate)
    assert row["ruling"] == real.fw().ruling(LAYOUT, repo=real.ROOT) and row["ruling"]["words"] == real.WORDS[LAYOUT]
    assert row["ruling"]["per_picture"] == (real.WORDS[LAYOUT] if LAYOUT == "L-0039" else "no per-picture verdict")
    for version in ("then", "now"):
        _check_cell(row[version], _w(r.w, version, "layout"), version)
        _check_cell(row["control"][version], _w(r.w, version, "control"), version)
        assert row[version]["winners"] == [[10, FACTS["layout"][version][0]], [1, FACTS["layout"][version][0]]]
        assert row[version]["winner_counts"] == {FACTS["layout"][version][0]: 2}
        assert row["control"][version]["winners"] == [[10, FACTS["control"][version][0]], [1, FACTS["control"][version][0]]]
        fc = row["f"][version]
        assert set(fc) == {"layout", "control", "same_winner"}
        _check_cell(fc["layout"], real.pick(r.f, version, "F", "layout"), version)
        _check_cell(fc["control"], real.pick(r.f, version, "F", "control"), version)
        assert fc["layout"]["winners"] == [[10, fc["layout"]["winner"]]] and fc["same_winner"] is (fc["layout"]["winner"] == fc["control"]["winner"])
        assert row["matches_expected"][version] == FACTS["matches"][version]
        assert (row["rate"][version]["rate_a"], row["rate"][version]["band_gap"]) == pytest.approx(real.RATE[LAYOUT][version])
        assert row["rate"][version]["predict_rate"] == rate and set(row["rate"][version]) == {"rate_a", "predict_rate", "band_gap"}
    assert row["then"]["predictions"]["agreement"].startswith("not measured") and row["then"]["units_firing"].startswith("not measured")
    assert row["fix"] == "not run" and row["control"]["fix"] == "not run" and row["f"]["fix"] == "not run" and row["matches_expected"]["fix"] == "not run" and row["rate"]["fix"] == "not run"
    verdict, flipped = FACTS["verdict"]
    assert (row["same_or_changed"], row["seeds_flipped"]) == (verdict, flipped)
    assert row["rule"] == real.fw().DRAFT_SAME_OR_CHANGED_RULE
    mod = real.fw()
    assert mod.same_or_changed(dict(row["then"]["winners"]), dict(row["now"]["winners"]))["verdict"] == verdict, "computed by the named rule"
    assert row["arm_readings"]["W"]["then"] == [row["then"]["winner"]] * 2 and row["arm_readings"]["W"]["now"] == [row["now"]["winner"]] * 2
    for version in ("then", "now"):
        assert row["arm_readings"]["F"][version] == {"layout": [row["f"][version]["layout"]["winner"]], "control": [row["f"][version]["control"]["winner"]]}
    assert row["first_differing_arm"] == mod.first_differing_arm(row["arm_readings"])
    allowed = {"F", "none"} if verdict == "same" else {"F", "none, the whole differs only at W"}
    assert row["first_differing_arm"] in allowed, "W %s: the first differing arm is F or the whole alone" % verdict
    json.dumps(row)
    assert str(iso_scratch) not in json.dumps(row), "no scratch path in the table row"
