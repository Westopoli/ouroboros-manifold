# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 45 item 4 (X1) and the Architect's follow-up of 2026-10-19 (relayed): the artifact header says which
# vision layouts ran and that re-engage is a stand-in; decision 46 (Westley, 2026-10-19): the firing arc is 30 degrees
"""LAB-REV2-FIX round 5: three notes in the artifact header, <section id="drafts"> (report.artifact). Ledger TD-LAB-REV2-FIX5-header-notes.

INTERFACE FOR THE BUILDER (frozen here). The header section ends with its paragraphs in this order: <ul class="drafts">, then (each only when it holds)
  1. <p class="vision-layouts" data-layouts-run="192" data-layouts-refused="81,78">vision cells: layout 192 only; 81 and 78 refuse the play: no_fit</p>
       Holds when summary["families"]["vision"]["refused"] (a family in summary["order"]) has an entry with role "play" (the play's own pre-flight; not
       "reach_zero", not a naive_ role) and reason "no_fit" on a layout that none of the rows of family "vision" ran on, and at least one layout was run.
       layouts-run = the layouts of the rows with family "vision", sorted as strings, "," joined; layouts-refused = the layouts of those entries, each once in the
       order the entries list them. The pinned text is the case ONE layout ran and TWO layouts refused: "vision cells: layout <run> only; <a> and <b> refuse the
       play: <reason as written, underscore kept>". Other counts are the builder's wording (Q-FIX5-2). No such entry: no <p>, and the page holds no "vision cells".
  2. <p class="reengage-standin">re-engage is a lab stand-in for the engine's pending sight-engagement rule</p>   (the text is exactly that sentence)
       Holds when at least one row has reengage_0 or reengage_1 above 0 (None counts as 0). All zero (or no rows): no <p>, and the page holds no "stand-in".
  3. <p class="no-defender-baseline" ...> as test_drift_fix_refused_beside.py pins it: still the LAST element child when present.
  The firing arc: with the arc family live (in summary["families"], not skipped) the <li data-draft="DRAFT-firing-arc-deg"> text holds the token `30` (Westley's
  ruling, decision 46) and no `120`; the name stays. (The arc family's grid points are not pinned here: see the ledger row's STOP.)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_report import _artifact_inputs, _page, _sec, _tree  # noqa: E402
from test_drift_fix_refused_lines import entry as refused_entry  # noqa: E402

SENTENCE = "vision cells: layout 192 only; 81 and 78 refuse the play: no_fit"
STANDIN = "re-engage is a lab stand-in for the engine's pending sight-engagement rule"


def vision_entry(layout, play="s3_layer_above", role="play", reason="no_fit", family="vision"):
    return {"family": family, "play": play, "layout": layout, "role": role, "reason": reason}


def summary_with(*refused, family="vision"):
    _, _, summary = _artifact_inputs()
    summary["families"][family] = dict(summary["families"][family], refused=list(refused))
    return summary


def rows_on(*layouts, family="vision"):
    """The fixture's rows with the vision rows moved onto `layouts` (one copy of the vision row per layout); the other families' rows stay."""
    _, rows, _ = _artifact_inputs()
    keep = [r for r in rows if r["family"] != family]
    mine = [r for r in rows if r["family"] == family]
    return keep + [dict(r, layout=l) for l in layouts for r in mine]


def header(html):
    sec = _sec(_tree(html), "drafts")
    return sec, [p for p in sec.find("p")]


def cls_p(html, name, sec=None):
    return [p for p in (header(html)[1] if sec is None else sec.find("p")) if name in p.attrs.get("class", "").split()]


FOUR = [vision_entry(l, play=p) for p in ("s3_layer_above", "s3_types_by_reach") for l in ("81", "78")]


# ---- the vision layouts ----

def test_vision_plays_refused_no_fit_on_81_and_78_with_192_run_say_so(tmp_path):
    _, _, html, _ = _page(tmp_path, rows=rows_on("192"), summary=summary_with(*FOUR))
    sec = header(html)[0]
    ps = cls_p(html, "vision-layouts", sec)
    assert len(ps) == 1 and ps[0].text().strip() == SENTENCE
    assert (ps[0].attrs["data-layouts-run"], ps[0].attrs["data-layouts-refused"]) == ("192", "81,78")
    els = sec.elements()
    assert els[-1] is ps[0] and [e.attrs.get("class") for e in els if e.name == "ul"] == ["drafts"]


def test_data_layouts_run_is_sorted_as_strings_when_two_layouts_ran(tmp_path):
    """The rows list layout 81 before 192; the attribute is sorted as strings, not in row order: "192,81"."""
    _, _, html, _ = _page(tmp_path, rows=rows_on("81", "192"), summary=summary_with(vision_entry("78")))
    ps = cls_p(html, "vision-layouts")
    assert len(ps) == 1 and ps[0].attrs["data-layouts-run"] == "192,81" and ps[0].attrs["data-layouts-refused"] == "78"


def test_the_sentence_sits_before_the_no_defender_note_which_stays_last(tmp_path):
    summary = summary_with(*FOUR, refused_entry("naive_defender", "blind_post", family="vision"))
    _, _, html, _ = _page(tmp_path, rows=rows_on("192"), summary=summary)
    els = header(html)[0].elements()
    names = [e.attrs.get("class") for e in els if e.name == "p"]
    assert names == ["vision-layouts", "no-defender-baseline"]


def test_the_order_of_the_refused_layouts_is_the_order_the_entries_list_them(tmp_path):
    entries = [vision_entry("78"), vision_entry("81"), vision_entry("78", play="s3_types_by_reach")]
    _, _, html, _ = _page(tmp_path, rows=rows_on("192"), summary=summary_with(*entries))
    assert cls_p(html, "vision-layouts")[0].text().strip() == "vision cells: layout 192 only; 78 and 81 refuse the play: no_fit"


def test_no_refusal_no_sentence(tmp_path):
    _, _, html, _ = _page(tmp_path, rows=rows_on("192"), summary=summary_with())
    assert not cls_p(html, "vision-layouts") and "vision cells" not in html


def test_a_refusal_for_another_reason_is_not_this_sentence(tmp_path):
    entries = [vision_entry(l, reason="unroutable") for l in ("81", "78")]
    _, _, html, _ = _page(tmp_path, rows=rows_on("192"), summary=summary_with(*entries))
    assert "vision cells" not in html


def test_a_naive_baseline_refusal_or_the_reach_zero_twin_is_not_a_play_refusal(tmp_path):
    entries = [vision_entry(l, role="naive_defender") for l in ("81", "78")] + [vision_entry(l, role="reach_zero") for l in ("81", "78")]
    _, _, html, _ = _page(tmp_path, rows=rows_on("192"), summary=summary_with(*entries))
    assert "vision cells" not in html


def test_refusals_of_another_family_are_not_the_vision_cells(tmp_path):
    summary = summary_with(*[vision_entry(l, family="range_up") for l in ("81", "78")], family="range_up")
    _, _, html, _ = _page(tmp_path, rows=rows_on("192"), summary=summary)
    assert "vision cells" not in html


def test_a_layout_that_ran_is_not_a_refused_one(tmp_path):
    """The vision rows ran on 81 and 78 too, so nothing is refused-only: no sentence."""
    _, _, html, _ = _page(tmp_path, rows=rows_on("81", "78", "192"), summary=summary_with(*FOUR))
    assert "vision cells" not in html


def test_no_vision_row_no_layout_to_name(tmp_path):
    _, _, html, _ = _page(tmp_path, rows=rows_on(), summary=summary_with(*FOUR))
    assert "vision cells" not in html


# ---- the re-engage stand-in ----

def with_reengage(rows, **cells):
    out = [dict(r) for r in rows]
    for k, v in cells.items():
        out[0][k] = v
    return out


def test_a_nonzero_reengage_count_says_it_is_a_stand_in(tmp_path):
    _, rows, _ = _artifact_inputs()
    for cells in ({"reengage_0": 2}, {"reengage_1": 1}):
        _, _, html, _ = _page(tmp_path, rows=with_reengage(rows, **cells))
        sec = header(html)[0]
        ps = cls_p(html, "reengage-standin", sec)
        assert len(ps) == 1 and ps[0].text().strip() == STANDIN, cells
        assert sec.elements()[-1] is ps[0]


def test_all_zero_or_missing_counts_say_nothing(tmp_path):
    _, rows, _ = _artifact_inputs()
    for rs in (rows, with_reengage(rows, reengage_0=None, reengage_1=None), []):
        _, _, html, _ = _page(tmp_path, rows=rs)
        assert not cls_p(html, "reengage-standin") and "stand-in" not in html


def test_both_notes_keep_their_order_before_the_no_defender_note(tmp_path):
    _, rows, _ = _artifact_inputs()
    summary = summary_with(*FOUR, refused_entry("naive_defender", "blind_post", family="vision"))
    rs = with_reengage(rows_on("192"), reengage_0=3)
    _, _, html, _ = _page(tmp_path, rows=rs, summary=summary)
    assert [e.attrs.get("class") for e in header(html)[0].elements() if e.name == "p"] == ["vision-layouts", "reengage-standin", "no-defender-baseline"]


# ---- the firing arc is 30 ----

def test_the_arc_draft_line_names_thirty_and_not_one_hundred_twenty(tmp_path):
    _, _, summary = _artifact_inputs()
    summary["families"]["arc"] = {"skipped": None, "refined": [], "refined_vs": {"naive_attacker": []}}
    _, _, html, _ = _page(tmp_path, summary=summary)
    lis = [li for li in _sec(_tree(html), "drafts").find("li") if li.attrs.get("data-draft") == "DRAFT-firing-arc-deg"]
    assert len(lis) == 1
    words = lis[0].text().replace(",", " ").replace(";", " ").replace("(", " ").replace(")", " ").split()
    assert "30" in words and "120" not in words, lis[0].text()


def test_control_a_skipped_arc_family_lists_no_arc_line(tmp_path):
    _, _, html, _ = _page(tmp_path)
    assert "DRAFT-firing-arc-deg" not in html
