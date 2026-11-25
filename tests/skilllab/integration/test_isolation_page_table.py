# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 5 (Comparison output), section 2 (the cell says "not measured at V-then", "never a blank or a zero"), piece LI5 part 1
"""The comparison table. Spec 5: "| layout | his ruling (verbatim, date) | V-then result | V-now result | same or changed | first differing arm |". Every value traces to a row: a planted change to one
input row changes exactly that cell. Interface: docs/reports/2026-11-24-li5-interface.md (column keys `data-col`: layout, ruling, then, now, [fix], change, first_arm).
Red today: `scripts/skilllab/arena/isolation_page.py` does not exist."""
import re

import pytest

import isolation_page_fixtures as pf

COLS = ["layout", "ruling", "then", "now", "change", "first_arm"]


def render(tmp_path, rows=None, **kw):
    out, _ = pf.build(tmp_path, rows or pf.synthetic_rows(), **kw)
    return pf.page_root(out)


def main_rows(root):
    return {k[0]: v for k, v in pf.table_cells(root, "comparison").items() if k[1] is None}


def test_columns_are_those_of_spec_5_in_order(tmp_path):
    root = render(tmp_path)
    head = [th.attrs.get("data-col") for th in root.one("table", data_table="comparison").find("th")]
    assert head == COLS
    assert list(main_rows(root)) == ["L-0055", "L-0084"]            # STAGE3_LAYOUTS order, one row per layout present


def test_his_ruling_is_verbatim_with_its_date_and_predict_rate(tmp_path):
    """spec 5: "his ruling (verbatim, date)"; `predict_rate` beside it, "shown, not scored"."""
    cells = main_rows(render(tmp_path))
    for layout, rate in (("L-0055", "0.98"), ("L-0084", "0.6")):
        c = cells[layout]["ruling"]
        assert pf.WORDS[layout] in c and "2026-11-01" in c and rate in c
        assert "no per-picture verdict" in c
    assert pf.STAGE_WORDS in cells["L-0055"]["ruling"] and pf.STAGE_DATE in cells["L-0055"]["ruling"]


def test_result_cells_carry_winner_survivors_ticks_and_counts(tmp_path):
    """spec 5: "Result is the winner at seed 10 plus the winner counts over the 20 seeds, survivors and ticks": `A 21:0 t3394`, counts `A 2` (two seeds here)."""
    c = main_rows(render(tmp_path))
    assert "A 21:0 t3394" in c["L-0055"]["then"] and "A 19:0 t1963" in c["L-0055"]["now"]
    assert "B 0:6 t2268" in c["L-0084"]["then"] and "A 18:0 t2097" in c["L-0084"]["now"]
    assert "B 2" in c["L-0084"]["then"] and "A 2" in c["L-0084"]["now"]
    assert "draw" not in c["L-0084"]["now"]


def test_same_or_changed_names_the_rule_and_the_count_never_better_or_worse(tmp_path):
    """spec 5: "`same` when the winner count ... is identical ... and `changed` otherwise, plus the number of seeds that flipped; it is never "regressed" or "improved"."; the cell names the DRAFT rule."""
    root = render(tmp_path)
    c = main_rows(root)
    assert c["L-0055"]["change"].startswith("same") and "DRAFT-same-or-changed-rule" in c["L-0055"]["change"]
    assert c["L-0084"]["change"].startswith("changed") and "2" in c["L-0084"]["change"] and "DRAFT-same-or-changed-rule" in c["L-0084"]["change"]
    text = root.text().lower()
    assert "regressed" not in text and "improved" not in text


def test_first_differing_arm_is_the_value_of_the_row(tmp_path):
    c = main_rows(render(tmp_path))
    assert c["L-0084"]["first_arm"] == "none, the whole differs only at W"      # only arm W was run: spec 5
    assert c["L-0055"]["first_arm"] == "none"


def test_a_changed_row_carries_its_control_twin_row(tmp_path):
    """spec 5: "Every `changed` row carries its control twin row and its decisive clip"."""
    cells = pf.table_cells(render(tmp_path), "comparison")
    twin = cells[("L-0084", "control", None)]
    assert "draw 40:56 t820" in twin["then"] and "B 0:27 t1361" in twin["now"]
    assert ("L-0055", "control", None) not in cells


def test_a_changed_row_links_its_decisive_clip(tmp_path):
    manifest = pf.clip_dir(tmp_path / "src", [("l0084-changed", "L-0084", "changed", ["then", "now"])])
    root = render(tmp_path, clips=manifest)
    row = [tr for tr in root.one("table", data_table="comparison").find("tr") if tr.attrs.get("data-layout") == "L-0084" and "data-variant" not in tr.attrs][0]
    (a,) = row.find("a", data_clipset="l0084-changed")
    assert a.attrs["href"] == "#l0084-changed" and root.find(id="l0084-changed")


def test_sentences_in_soldiers_not_ratios(tmp_path):
    """spec 5: "Open with the sentence for each layout in soldiers, not ratios (README 5: "beats 17, loses to 18")"."""
    root = render(tmp_path)
    for layout in ("L-0055", "L-0084"):
        s = root.one(data_sentence=layout).text()
        assert layout in s and not re.search(r"%|ratio|\d+(\.\d+)?\s*x\b", s)
    s84 = root.one(data_sentence="L-0084").text()
    assert re.search(r"\b18\b", s84) and re.search(r"\b6\b", s84)       # then: B ends with 6; now: A ends with 18


def test_planted_change_in_one_row_changes_exactly_that_cell(tmp_path):
    """Every table value traces to a row: change the `now` last_tick of L-0055 layout (both seeds, so the cell's counts hold) and only that cell differs."""
    base = main_rows(render(tmp_path / "a"))
    planted = main_rows(render(tmp_path / "b", pf.synthetic_rows({("now", "L-0055", "layout"): {"ticks": 7771}})))
    diff = [(l, k) for l in base for k in base[l] if base[l][k] != planted[l][k]]
    assert diff == [("L-0055", "now")] and "t7771" in planted["L-0055"]["now"] and "t1963" in base["L-0055"]["now"]


@pytest.mark.parametrize("plant, layout, col", [
    ({("then", "L-0084", "layout"): {"surv": (0, 4)}}, "L-0084", "then"),
    ({("now", "L-0084", "layout"): {"winner": "B", "surv": (0, 3), "ticks": 2050}}, "L-0084", "now"),
])
def test_planted_winner_or_survivors_reach_the_result_cell(tmp_path, plant, layout, col):
    base = main_rows(render(tmp_path / "a"))[layout][col]
    got = main_rows(render(tmp_path / "b", pf.synthetic_rows(plant)))[layout][col]
    assert got != base


def test_planted_winner_flip_reaches_same_or_changed(tmp_path):
    """L-0055 now winner A to B in both seeds: the row turns `changed`, 2 seeds."""
    rows = pf.synthetic_rows({("now", "L-0055", "layout"): {"winner": "B", "surv": (0, 4)}})
    c = main_rows(render(tmp_path, rows))["L-0055"]["change"]
    assert c.startswith("changed") and "2" in c


def test_not_measured_renders_as_that_text_never_as_zero(tmp_path):
    """spec 2: "Where a V-then measure does not exist in its lab, the cell says "not measured at V-then", never a blank or a zero." A build error row at `now`."""
    rows = [r for r in pf.synthetic_rows() if not (r["version"] == "now" and r["layout"] == "L-0055" and r["variant"] == "layout")]
    rows += [pf.row("now", "L-0055", "layout", s, None, None, None, error=("build", "make failed: no cc\nsecond line")) for s in pf.SEEDS]
    c = main_rows(render(tmp_path, rows))["L-0055"]
    assert "not measured at now" in c["now"] and "build: make failed: no cc" in c["now"]
    assert "second line" not in c["now"] and not re.search(r"\b0:0\b|\bt0\b|\b0\b", c["now"])
    assert c["change"].startswith("not measured")


def test_a_version_with_no_rows_is_not_run_never_zero(tmp_path):
    rows = [r for r in pf.synthetic_rows() if r["version"] == "then"]
    c = main_rows(render(tmp_path, rows))
    assert c["L-0055"]["now"] == "not run" and c["L-0055"]["change"] == "not run" and c["L-0055"]["first_arm"] == "not run"


def test_fix_column_only_when_a_fix_run_exists(tmp_path):
    root = render(tmp_path)
    assert "fix" not in [th.attrs.get("data-col") for th in root.one("table", data_table="comparison").find("th")]
