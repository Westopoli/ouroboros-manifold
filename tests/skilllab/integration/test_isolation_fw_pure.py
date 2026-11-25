# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 (arms F and W), section 5 (comparison row), section 1 (his stage 3 rulings), section 8 (DRAFT-seeds, DRAFT-same-or-changed-rule)
"""LI4-FW, the parts that need no fight (every test red until `scripts/skilllab/arena/isolation_fw.py` exists; the last test of the file is a green control on the records).

P1 constants: the four stage 3 layouts, seeds 10 as approved plus seed 1 (DRAFT-seeds), the same-or-changed rule named (DRAFT-same-or-changed-rule: identical winner over the seeds, no tolerance),
   the arm order M, V, R, F, P, W.   P2 `approved()` reads the stage 3 rows of arena/approved.toml: expected winner and predict_rate.
P3 `ruling()` gives his words verbatim and dated from the records; where the records hold only the stage-level approval of 2026-11-05 the picture row says 'no per-picture verdict'.
P4 `neutral_layout()` is arm F's layout: one factor, roles neutral (every unit Vanguard, Vanguard range, both sides), ground feature, positions, headcounts as authored.
P5 `same_or_changed()` is the named rule and nothing else.   P6 `first_differing_arm()` names the first arm of M, V, R, F, P, W whose reading differs.   P7 `measured_rate()` shows the gap to predict_rate, scored nowhere.
P8 the records the tests quote are on the tree (green control)."""
import copy
import tomllib

import pytest

import isolation_fw_real as real


def test_p1_constants():
    mod = real.fw()
    assert tuple(mod.STAGE3_LAYOUTS) == real.STAGE3
    assert tuple(mod.DRAFT_SEEDS) == (10, 1)                                  # DRAFT-seeds: 10 as approved, plus 1; seeds change nothing in lab fights
    assert mod.DRAFT_SAME_OR_CHANGED_RULE == "identical winner over the seeds"  # DRAFT-same-or-changed-rule
    assert tuple(mod.ARM_ORDER) == ("M", "V", "R", "F", "P", "W")


def test_p2_approved_rows_are_the_stage3_rows_of_approved_toml():
    got = real.fw().approved(repo=real.ROOT)
    assert {k: (v["expected_winner"], v["predict_rate"]) for k, v in got.items()} == real.EXPECTED, "only the stage 3 rows, side A's predict_rate (0.25 where he said B wins 75%)"
    assert all(v["decision"] == "DEC-stage3-layouts-2026-11-05" for v in got.values())


@pytest.mark.parametrize("layout", real.STAGE3)
def test_p3_ruling_is_verbatim_and_dated(layout):
    got = real.fw().ruling(layout, repo=real.ROOT)
    assert got["words"] == real.WORDS[layout]
    assert got["date"] == "2026-11-01"
    assert got["stage_approval"] == {"words": real.STAGE_WORDS, "date": real.STAGE_DATE}, "the only thing recorded for the three redrawn layouts is the stage-level approval"
    expect = real.WORDS[layout] if layout == "L-0039" else real.NO_PICTURE     # L-0039 is the layout he denied by id (verdicts.md); the others were redrawn and approved only with the stage
    assert got["per_picture"] == expect


def test_p3_ruling_of_a_layout_he_never_ruled_on_is_an_error_not_an_invention():
    with pytest.raises(ValueError):
        real.fw().ruling("L-0047", repo=real.ROOT)


@pytest.mark.parametrize("layout", real.STAGE3)
def test_p4_neutral_layout_changes_roles_and_nothing_else(layout):
    mod = real.fw()
    authored = tomllib.load(open(real.LD / "catalogue" / (layout + ".toml"), "rb"))
    before = copy.deepcopy(authored)
    got = mod.neutral_layout(authored)
    assert authored == before, "the input is not changed"
    assert got["id"] != authored["id"], "a variant never wears the authored id"
    for side in ("side_a", "side_b"):
        units, was = got[side]["units"], authored[side]["units"]
        assert len(units) == len(was) == authored[side]["headcount"]
        assert {u["role"] for u in units} == {"Vanguard"}
        assert {u["range"] for u in units} == {300.0}, "Vanguard's range, the one the authored Vanguards carry"
        for u, w in zip(units, was):
            assert {k: v for k, v in u.items() if k not in ("role", "range")} == {k: v for k, v in w.items() if k not in ("role", "range")}      # position, facing, layer, arc as drawn
        assert {k: v for k, v in got[side].items() if k != "units"} == {k: v for k, v in authored[side].items() if k != "units"}
    assert {k: v for k, v in got.items() if k not in ("id", "side_a", "side_b")} == {k: v for k, v in authored.items() if k not in ("id", "side_a", "side_b")}, "features, orders, landscape as authored"
    assert got["features"] == authored["features"] and got["features"], "the one ground feature stays: the isolation is the twin without it"


def test_p5_same_or_changed_is_the_named_rule():
    f = real.fw().same_or_changed
    rule = real.fw().DRAFT_SAME_OR_CHANGED_RULE
    assert f({10: "A", 1: "A"}, {10: "A", 1: "A"}) == {"verdict": "same", "seeds_flipped": 0, "rule": rule}
    assert f({10: "A", 1: "A"}, {10: "B", 1: "B"}) == {"verdict": "changed", "seeds_flipped": 2, "rule": rule}
    assert f({10: "A", 1: "A"}, {10: "A", 1: "B"}) == {"verdict": "changed", "seeds_flipped": 1, "rule": rule}, "one differing winner is a change: no tolerance is invented"
    assert f({10: "cap", 1: "cap"}, {10: "A", 1: "A"})["verdict"] == "changed"
    assert f({10: "draw", 1: "draw"}, {10: "draw", 1: "draw"})["verdict"] == "same", "the same defect on both sides is the same winner"
    assert set(f({10: "A"}, {10: "A"})) == {"verdict", "seeds_flipped", "rule"}, "never 'regressed' or 'improved'"
    with pytest.raises(ValueError):
        f({10: "A"}, {10: "A", 1: "A"})                     # the seeds must be the same seeds


def test_p5_a_side_that_could_not_run_is_not_measured_never_same():
    f = real.fw().same_or_changed
    got = f({10: "not measured: fight: the lab wrote no fight file"}, {10: "A"})
    assert got["verdict"].startswith("not measured")
    assert f({10: "not measured: build: x"}, {10: "not measured: build: x"})["verdict"].startswith("not measured"), "two failures are not 'identical winner'"


def test_p6_first_differing_arm_follows_the_arm_order():
    f = real.fw().first_differing_arm
    same, diff = {"then": "A", "now": "A"}, {"then": "A", "now": "B"}
    assert f({"F": same, "W": diff}) == "none, the whole differs only at W"
    assert f({"F": diff, "W": diff}) == "F"
    assert f({"F": diff, "W": same}) == "F"
    assert f({"F": same, "W": same}) == "none"
    assert f({"W": diff, "F": diff, "R": diff}) == "R", "the order is M, V, R, F, P, W whatever order the readings come in"
    assert f({"W": diff, "M": diff}) == "M"
    assert f({"W": diff}) == "none, the whole differs only at W"
    assert f({"F": {"then": {"layout": ["A"], "control": ["A"]}, "now": {"layout": ["A"], "control": ["B"]}}, "W": same}) == "F", "a reading may be any value; it differs when the two versions' readings are unequal"
    assert f({"F": {"then": "x", "now": "x", "fix": "y"}, "W": same}) == "none", "then against now only: the fix column is later"
    with pytest.raises(ValueError):
        f({"Q": diff})


def test_p7_measured_rate_shows_the_gap_and_scores_nothing():
    f = real.fw().measured_rate
    got = f(["A", "A"], 0.98)
    assert set(got) == {"rate_a", "predict_rate", "band_gap"}, "shown, not scored: no pass, agree or flag key"
    assert got["rate_a"] == 1.0 and got["predict_rate"] == 0.98 and got["band_gap"] == pytest.approx(2.0)
    assert f(["cap", "cap"], 0.25) == {"rate_a": 0.0, "predict_rate": 0.25, "band_gap": pytest.approx(25.0)}, "a cap is not a win for A"
    assert f(["A", "B"], 0.5)["band_gap"] == pytest.approx(0.0)
    assert f(["B", "B"], 0.6)["band_gap"] == pytest.approx(60.0)


def test_p8_control_the_records_the_tests_quote_are_on_the_tree():
    """Green today: the verbatim words, the stage approval and the approved rows exist in the records the module must read."""
    heur = (real.LD / "heuristics.md").read_text()
    verd = (real.LD / "catalogue" / "verdicts.md").read_text()
    ruled = (real.ROOT / "docs/northstar/story_reviews/westley/ruled.md").read_text()
    for layout in ("L-0055", "L-0073", "L-0084"):
        assert '"%s"' % real.WORDS[layout] in heur
    assert real.WORDS["L-0039"] in verd and "| L-0039 | deny | Westley 2026-11-01:" in verd
    assert real.STAGE_WORDS in ruled and "Westley 2026-11-05" in ruled
    rows = [r for r in tomllib.load(open(real.LD / "arena" / "approved.toml", "rb"))["fight"] if r["stage"] == 3]
    assert {r["layout"]: (r["expected_winner"], r["predict_rate"]) for r in rows} == real.EXPECTED
