# spec: docs/stories/H-053.md (arena-stage2-roles-ranges-winrates) as amended by "Scoring" (Westley's order 2026-11-02, DEC-stage-scoring-loose-2026-11-02); Flag client
"""H-053 "Scoring", the stage page. Lines proved here, word for word:
  "The page prints "heuristic target 0.98, measured 1.00, gap 2 pts (not scored)" and scores only the winner guess. Band colours are information, no verdict."
  "`Predict: draw` on an exact mirror is not scored: `agree: null`, `mirror: true`, flagged for Westley's eye."
Rate files are written by hand (the page reads the rate file, as test_page._stage2 does). Premises, each a question in the report: the page prints the sentence anywhere in the block
(not pinned to a cell); a mirror layout shows the word `mirror` and its agree cell carries neither the class `agree` nor `disagree`."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test_page import _build, _Cells, stage  # noqa: E402,F401  (stage is a fixture)


def rated(stage, rate_a, predict_rate, agree, band_gap, mirror=False):
    root, out, docs = stage
    (out / "L-0101.rate.json").write_text(json.dumps(
        {"layout_id": "L-0101", "seeds": [1], "wins_a": int(rate_a), "wins_b": 1 - int(rate_a), "stalls": 0, "stall_seeds": [], "none_seeds": [], "rate_a": rate_a,
         "predict_rate": predict_rate, "band": 0.1, "band_gap": band_gap, "agree": agree, "mirror": mirror, "firing_capable": {"A": 2.0, "B": 2.0}, "median_seed": 1}) + "\n")
    return _build(stage)[0]


def agree_classes(page):
    cells = _Cells()
    cells.feed(page)
    return [c[0] for tag, c in cells.classes if tag == "td" and ("agree" in c or "disagree" in c)]


def test_control_a_rated_layout_has_one_agree_cell_and_the_stage1_row_keeps_its_disagree(stage):
    """Control, green today: L-0101 rated with agree true gives the stage 2 block one `agree` cell class; the unrated stage 1 row L-0102 (predicted wrong) is the one `disagree`;
    L-0101 is not also listed as a stage 1 row. A red below is the missing Scoring text, not the harness."""
    tokens = agree_classes(rated(stage, 1.0, 0.98, True, 2))
    assert "agree" in tokens and tokens.count("disagree") == 1, tokens


def test_page_prints_the_heuristic_target_sentence(stage):
    """"The page prints "heuristic target 0.98, measured 1.00, gap 2 pts (not scored)"." Exact text for target 0.98, measured 1.00, gap 2."""
    page = rated(stage, 1.0, 0.98, True, 2)
    assert "heuristic target 0.98, measured 1.00, gap 2 pts (not scored)" in page


def test_page_sentence_follows_the_numbers_and_not_the_verdict(stage):
    """The sentence takes target, measured and gap from the rate file: 0.60 against 0.80 reads "heuristic target 0.60, measured 0.80, gap 20 pts (not scored)", and it is printed
    for a disagreeing layout alike (positive control: the sentence differs with the numbers, so the test above is not a constant string)."""
    page = rated(stage, 0.8, 0.60, False, 20)
    assert "heuristic target 0.60, measured 0.80, gap 20 pts (not scored)" in page
    assert "heuristic target 0.98" not in page


def test_page_scores_only_the_winner_guess(stage):
    """"scores only the winner guess": the layout's agree cell follows the rate file's `agree` and not the gap. A 20 point gap with agree true is class `agree` and no `disagree` in the
    stage 2 block; a 2 point gap with agree false is `disagree` (the unrated stage 1 row L-0102 contributes one `disagree` of its own: its class is counted, not ignored)."""
    wide_agree = agree_classes(rated(stage, 0.8, 0.60, True, 20))
    assert "agree" in wide_agree and wide_agree.count("disagree") == 1, wide_agree   # stage 2 cell agree; the unrated stage 1 row L-0102 is the one disagree
    narrow_disagree = agree_classes(rated(stage, 1.0, 0.98, False, 2))
    assert "agree" not in narrow_disagree and narrow_disagree.count("disagree") >= 2, narrow_disagree


def test_mirror_draw_is_flagged_and_not_scored_on_the_page(stage):
    """"`Predict: draw` on an exact mirror is not scored: `agree: null`, `mirror: true`, flagged for Westley's eye." The block shows the word `mirror` and no agree/disagree class for the
    mirror layout (only the stage 1 row L-0102 keeps its `disagree`)."""
    page = rated(stage, 0.2, 0.50, None, 30, mirror=True)
    assert "mirror" in page.lower()
    assert agree_classes(page) == ["disagree"], agree_classes(page)
