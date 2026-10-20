# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirements R3 "the artifact reports crossings per reach configuration" and R4 "the artifact says which of the three called the winner", tests T7 and T8, defect D8); ledger FINDING-lab-d8; piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, what the diagram and the artifact say about reach configurations and about the three predictions. Fast, fake rows only.

BUILDER CONTRACT (names DRAFT; the plan fixes the content, not the markup):
  R3  The rows carry a `reach` column (test_rev3_c_reach_knob.py). diagram.notables treats the reach configuration as part of a series: two
      configurations never merge into one scan. diagram.Notable gets a field `reach` (the row's `reach` string, None when the rows have no such
      column). A crossing is found per configuration; ids stay unique. report.artifact names the configuration in a crossing's h2 sentence
      when the rows hold MORE THAN ONE configuration (with one, or with no `reach` column, the sentences are exactly today's).
  R4  (Architect ruling 2026-10-20, implementation; Westley may veto: no reading names the winner by itself, so the artifact only COUNTS; the paper
      word "no_reach" names no winner, like "tie"; a stall row, outcome no_reach_stall, is not a call.)
  R4  report.artifact's section "agreement" gains, for each reading in ("window", "paper", "whole"), one element with class "called" and the
      attributes data-reading, data-right, data-fights: over the rows whose outcome is side0 or side1 (a cap or draw is not a call), data-fights
      is their number and data-right the number of them in which that reading named the winner. window: the row's predicted_count (the
      window total's larger side); paper: predicted_paper; whole: the larger side of firing_unit_seconds (decision 35 item 2). A tie names no
      winner. The elements are NOT a <table> and come after the chart (test_report pins exactly one table in this section, and the chart
      html verbatim). (The fixture keeps predicted_type equal to predicted_count and the weighted totals in the same direction as the counts, so the
      window and whole readings do not depend on the type reading.)
  R4  A both_wrong notable's diagram gains a "prediction" arrow for the column predicted_paper when the row has it (value side0/side1).
Red today: no reach split, no `reach` attribute, no called elements, no paper arrow. Controls are green today."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import diagram, rows as rows_mod  # noqa: E402

A, B = "Raider=(1, 1)", "Raider=(2, 1)"   # DRAFT labels: the tests pin that rows of one run share one string, not its format
FLAT16 = {0.25: 16, 0.5: 16, 0.75: 16, 1.0: 16}
PLAY_A = {0.25: 8, 0.5: 8, 0.75: 32, 1.0: 40}      # ahead of the flat 16 from 0.75: crossing between 0.5 and 0.75
PLAY_B = {0.25: 8, 0.5: 32, 0.75: 32, 1.0: 40}     # ahead from 0.5: crossing between 0.25 and 0.5


def td():
    import test_diagram
    return test_diagram


def cfg_rows(play_be, label, **kw):
    t = td()
    out = []
    for v, b in sorted(play_be.items()):
        out += t.scan_rows("range_up", "s3_layer_above", "81", v, "none", b, **({"reach": label} if label else {}), **kw)
    for v, b in sorted(FLAT16.items()):
        out += t.scan_rows("range_up", "s3_layer_above", "81", v, "naive_attacker", b, **({"reach": label} if label else {}), **kw)
    return out


def crossings(rows):
    return [n for n in diagram.notables(rows) if n.kind == diagram.CROSSING]


def span(n):
    return (n.knob_lo, n.knob_hi)


# ---- R3: crossings per reach configuration ---------------------------------------------------------------------------------------------

def test_control_each_configuration_alone_has_its_own_crossing():
    """Green today: configuration A alone crosses between 0.5 and 0.75, B alone between 0.25 and 0.5."""
    assert [span(n) for n in crossings(cfg_rows(PLAY_A, A))] == [(0.5, 0.75)]
    assert [span(n) for n in crossings(cfg_rows(PLAY_B, B))] == [(0.25, 0.5)]


def test_two_configurations_in_one_batch_give_two_crossings_not_one_merged_scan():
    """R3: 'the artifact reports crossings per reach configuration'. Today the rows of A and B share (family, play, layout, point), so a cell is
    won only when both won it and the pair yields A's crossing alone (the B crossing is lost). Red today: one crossing."""
    found = crossings(cfg_rows(PLAY_A, A) + cfg_rows(PLAY_B, B))
    assert sorted(span(n) for n in found) == [(0.25, 0.5), (0.5, 0.75)], [span(n) for n in found]
    assert len({n.id for n in found}) == 2


def test_each_crossing_names_its_configuration():
    found = crossings(cfg_rows(PLAY_A, A) + cfg_rows(PLAY_B, B))
    assert {(getattr(n, "reach", None), span(n)) for n in found} == {(A, (0.5, 0.75)), (B, (0.25, 0.5))}


def test_rows_without_a_reach_column_keep_their_notables():
    """Green today and after (the older CSVs): no `reach` column, one series, the crossing as before; the field reads None."""
    found = crossings(cfg_rows(PLAY_A, None))
    assert [span(n) for n in found] == [(0.5, 0.75)]
    assert getattr(found[0], "reach", None) is None


def _h2(html):
    import test_report
    return [h.text() for h in test_report._tree(html).find("h2") if "data-notable" in h.attrs]


def test_the_artifact_names_the_configuration_in_each_crossing_sentence(tmp_path):
    """R3 in the artifact: with two configurations in the rows, the sentence of the crossing of A names A and not B, and the B sentence names B."""
    import test_report
    _t, _rows, html, _p = test_report._page(tmp_path, rows=cfg_rows(PLAY_A, A) + cfg_rows(PLAY_B, B))
    crossing = [t for t in _h2(html) if "gain crosses" in t]
    assert len(crossing) == 2, crossing
    assert sum(A in t and B not in t for t in crossing) == 1 and sum(B in t and A not in t for t in crossing) == 1


def test_control_one_configuration_leaves_the_sentences_as_they_are(tmp_path):
    """Green today and after: the rows of one run, with and without the reach column, give the same crossing sentence."""
    import test_report
    plain = [t for t in _h2(test_report._page(tmp_path / "a", rows=cfg_rows(PLAY_A, None))[2]) if "gain crosses" in t]
    tagged = [t for t in _h2(test_report._page(tmp_path / "b", rows=cfg_rows(PLAY_A, A))[2]) if "gain crosses" in t]
    assert len(plain) == len(tagged) == 1 and plain == tagged


# ---- R4: which of the three called the winner ---------------------------------------------------------------------------------------------

def called_row(outcome, window, paper, whole):
    """A fight row: the window reading `window`, the paper reading `paper`, the whole-fight totals favouring `whole` ('side0'/'side1').
    The paper columns are set on the row dict after fight_row, so these tests are red for the artifact's sake and not for FightResult's."""
    t = td()
    fus = (100.0, 50.0) if whole == "side0" else (50.0, 100.0)
    wus = (110.0, 55.0) if whole == "side0" else (55.0, 110.0)
    row = rows_mod.fight_row(t.fr(outcome=outcome, predicted_count=window, predicted_type=window, agreement="n/a", firing_unit_seconds=fus,
                                  weighted_unit_seconds=wus), knob="OM_TP_RANGE_UP_1", knob_value=0.5, baseline="none", ceiling_hit=0,
                             prefight="ok", family="range_up", play="s3_layer_above", layout="81", kind="grid", enemy_heads=16)
    row["point"] = "-"
    row["paper_score_0"], row["paper_score_1"] = ((20.0, 16.0) if paper == "side0" else (16.0, 20.0) if paper == "side1" else
                                                  (0.0, 0.0) if paper == "no_reach" else (18.0, 18.0))
    row["predicted_paper"] = paper
    return row


# outcome, window, paper, whole
CALLS = [("side0", "side0", "side0", "side0"),         # all three right
         ("side1", "side0", "side1", "side0"),         # only paper right
         ("side0", "side1", "side0", "side1"),         # only paper right
         ("side1", "side1", "side0", "side0"),         # only window right
         ("cap", "side0", "side1", "side0"),           # a cap is not a call
         ("side0", "tie", "tie", "side0"),             # a tie names no winner; whole right
         ("side1", "side0", "no_reach", "side1"),      # "no_reach" names no winner either; only whole right
         ("side0", "side1", "no_reach", "side0"),      # only whole right
         ("no_reach_stall", "tie", "no_reach", "side0")]   # a stall is not a call (ruling 2026-10-20: outcome no_reach_stall)


def test_the_artifact_says_which_reading_called_the_winner(tmp_path):
    """R4: of the 7 fights that ended side0 or side1 (the cap and the stall are out), the window was right in 2 (rows 1 and 4), the paper in 3
    (rows 1, 2, 3; a tie and a no_reach name no winner) and the whole-fight totals in 4 (rows 1, 6, 7, 8). The three counts differ, so a
    builder that swaps two labels fails. Red today: no `called` element in the agreement section."""
    import test_report
    rows = [called_row(*c) for c in CALLS]
    _t, _r, html, _p = test_report._page(tmp_path, rows=rows)
    sec = test_report._sec(test_report._tree(html), "agreement")
    called = {n.attrs["data-reading"]: (int(n.attrs["data-right"]), int(n.attrs["data-fights"]))
              for n in sec.iter() if "called" in (n.attrs.get("class") or "").split()}
    assert called == {"window": (2, 7), "paper": (3, 7), "whole": (4, 7)}


# ---- R4: the diagram's prediction arrows ----------------------------------------------------------------------------------------------

def test_a_both_wrong_diagram_gains_the_paper_prediction_arrow():
    """The both_wrong finding shows the paper reading beside the window's count and type. Red today: no predicted_paper arrow."""
    t = td()
    row = t.both_wrong_row()
    row["paper_score_0"], row["paper_score_1"], row["predicted_paper"] = 16.0, 20.0, "side1"
    n = t.one([row], diagram.BOTH_WRONG)
    facts = {f["column"]: f for f in t.arrow_facts(t.parse(diagram.render(n, [row], t.fake_setup())))}
    assert "predicted_paper" in facts, sorted(facts)
    assert facts["predicted_paper"]["kind"] == "prediction" and facts["predicted_paper"]["side"] == "1"
    assert facts["predicted_paper"]["value"] == "side1"
