# spec: docs/stories/H-053.md (arena-stage2-roles-ranges-winrates) as amended by "Scoring" (Westley's order 2026-11-02, DEC-stage-scoring-loose-2026-11-02); Flag client (library part)
"""H-053 "Scoring": `rate.rate()` scores the winner guess, not the band.

The rule is docs/stories/H-053.md "Scoring" (on main since ef64449a), summarised in the Architect's message (scratch/stage2/scoring_rule.md, c-s2run).
Lines proved here, word for word:
  "The percentages are heuristic TARGETS for where the lines cross, not expected results; agree/disagree was far too literal."
  "The rate file keeps `predict_rate` and `rate_a`, and gains `band_gap` (points, informational)."
  "`agree` = the layout's `predict` (A, B or draw) equals the measured majority winner (wins_a vs wins_b; a tie or a mutual wipe = draw)."
  "`Predict: draw` on an exact mirror is not scored: `agree: null`, `mirror: true`, flagged for Westley's eye."
  "Stall or none seeds still flag."
  "Positive control: a fixture whose predict is the other side disagrees."
  "Expected re-scoring of the eight (SIT Predict fields): L-0101 agree; L-0102 disagree (A guessed, B won); L-0103 mirror, not scored (flag: B won); L-0104 agree;
   L-0105 agree; L-0106 disagree (B guessed, A won); L-0107 agree; L-0108 agree (mutual wipe)."

Premises (the rule leaves them open; each is a question in the commit body and the report, the tests pick the narrowest reading):
  Q1 where `rate()` reads the layout's `predict`: from `fights[0]["result"]["predict"]` (the fight document carries it today).
  Q2 how `rate()` learns the layout is an exact mirror: a keyword `mirror=True` (default False), and the rate file always carries `mirror`.
  Q3 `band_gap` is |rate_a - predict_rate| * 100, a number in points (compared with a tolerance: float arithmetic, and an int or a float both pass).
  Q4 a stall or none seed leaves its seed number in `stall_seeds`/`none_seeds` (the flag); whether it also forces `agree` false is NOT pinned here.
The table-driven test uses stand-in rate data for the eight; the real SIT Predict fields are not read."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test_rate import fight, load_rate  # noqa: E402


def scored(seed, winner, predict, layout_id="L-9100"):
    doc = fight(seed, winner, 1000 + seed, layout_id)
    doc["result"]["predict"], doc["result"]["agree"] = predict, winner == predict
    return doc


def seeds_of(predict, winners, layout_id="L-9100"):
    return [scored(i + 1, w, predict, layout_id) for i, w in enumerate(winners)]


def rate_of(predict, winners, predict_rate, mirror=False):
    mod = load_rate()
    fights = seeds_of(predict, winners)
    return mod.rate(fights, predict_rate, mirror=True) if mirror else mod.rate(fights, predict_rate)


def test_control_scored_fixture_keeps_the_existing_rate_numbers():
    """Control, green today: a scored fixture of 16 A and 4 B wins gives the unchanged `rate_a` 0.8, `predict_rate` and win counts, so a red below is the missing Scoring rule."""
    rate = rate_of("A", ["A"] * 16 + ["B"] * 4, 0.60)
    assert (rate["wins_a"], rate["wins_b"], rate["rate_a"], rate["predict_rate"]) == (16, 4, 0.8, 0.60)


def test_rate_file_gains_band_gap_in_points():
    """"The rate file keeps `predict_rate` and `rate_a`, and gains `band_gap` (points, informational)." 20 A wins against 0.98 is 2 points; 16 of 20 against 0.60 is 20; the gap is absolute (0.5 against 0.75 is 25)."""
    assert rate_of("A", ["A"] * 20, 0.98)["band_gap"] == pytest.approx(2.0)
    assert rate_of("A", ["A"] * 16 + ["B"] * 4, 0.60)["band_gap"] == pytest.approx(20.0)
    assert rate_of("A", ["A"] * 10 + ["B"] * 10, 0.75)["band_gap"] == pytest.approx(25.0)


def test_band_gap_is_information_it_does_not_decide_agree():
    """"`agree` = the layout's `predict` ... equals the measured majority winner" and "Band colours are information, no verdict". 16 of 20 A wins, predicted A: a 20 point gap from 0.60
    still agrees; a 2 point gap with the other side guessed (predict B, A won every seed) still disagrees."""
    wide = rate_of("A", ["A"] * 16 + ["B"] * 4, 0.60)
    assert wide["band_gap"] == pytest.approx(20.0) and wide["agree"] is True
    narrow = rate_of("B", ["A"] * 20, 0.98)
    assert narrow["band_gap"] == pytest.approx(2.0) and narrow["agree"] is False


def test_positive_control_a_fixture_whose_predict_is_the_other_side_disagrees():
    """"Positive control: a fixture whose predict is the other side disagrees." The same eleven A / nine B seeds agree when A was guessed and disagree when B was."""
    winners = ["A"] * 11 + ["B"] * 9
    assert rate_of("A", winners, 0.55)["agree"] is True
    assert rate_of("B", winners, 0.55)["agree"] is False


@pytest.mark.parametrize("predict,winners,agree", [
    ("A", ["A"] * 11 + ["B"] * 9, True),
    ("B", ["A"] * 9 + ["B"] * 11, True),
    ("A", ["A"] * 9 + ["B"] * 11, False),
    ("draw", ["A"] * 10 + ["B"] * 10, True),     # a tie of wins is a draw
    ("A", ["A"] * 10 + ["B"] * 10, False),
    ("draw", ["A"] * 11 + ["B"] * 9, False),
    ("draw", ["none"] * 20, True),               # every seed a same-tick wipe: a mutual wipe is a draw
    ("A", ["none"] * 20, False),
], ids=["A-right", "B-right", "A-wrong", "draw-on-tie", "A-on-tie", "draw-on-A-win", "draw-on-mutual-wipe", "A-on-mutual-wipe"])
def test_agree_is_the_measured_majority_winner_guess(predict, winners, agree):
    """"`agree` = the layout's `predict` (A, B or draw) equals the measured majority winner (wins_a vs wins_b; a tie or a mutual wipe = draw)."""
    assert rate_of(predict, winners, 0.5)["agree"] is agree


def test_draw_on_an_exact_mirror_is_not_scored_and_flagged():
    """"`Predict: draw` on an exact mirror is not scored: `agree: null`, `mirror: true`." B won 14 of 20, which would disagree on a non-mirror (the control line)."""
    winners = ["A"] * 6 + ["B"] * 14
    mirrored = rate_of("draw", winners, 0.5, mirror=True)
    assert mirrored["agree"] is None and mirrored["mirror"] is True
    plain = rate_of("draw", winners, 0.5)
    assert plain["agree"] is False and plain["mirror"] is False


def test_stall_and_none_seeds_still_flag():
    """"Stall or none seeds still flag." Each is listed by seed number and counted, also on a mirror (where `agree` is null)."""
    winners = ["A", "A", "stall", "A", "none"]
    rate = rate_of("A", winners, 0.8)
    assert rate["stalls"] == 1 and rate["stall_seeds"] == [3] and rate["none_seeds"] == [5]
    mirrored = rate_of("draw", winners, 0.5, mirror=True)
    assert mirrored["stall_seeds"] == [3] and mirrored["none_seeds"] == [5] and mirrored["agree"] is None


EIGHT = [  # (id, predict, mirror, predict_rate, winners, agree, mirror flag); stand-ins for the SIT Predict fields, the outcomes are the message's
    ("L-0101", "A", False, 0.98, ["A"] * 20, True, False),
    ("L-0102", "A", False, 0.80, ["B"] * 20, False, False),                  # A guessed, B won
    ("L-0103", "draw", True, 0.50, ["A"] * 4 + ["B"] * 16, None, True),       # mirror, not scored (flag: B won)
    ("L-0104", "A", False, 0.75, ["A"] * 15 + ["B"] * 5, True, False),
    ("L-0105", "B", False, 0.60, ["B"] * 12 + ["A"] * 8, True, False),
    ("L-0106", "B", False, 0.75, ["A"] * 20, False, False),                  # B guessed, A won
    ("L-0107", "A", False, 0.60, ["A"] * 20, True, False),                   # 40 point gap, still agrees
    ("L-0108", "draw", False, 0.50, ["none"] * 20, True, False),             # mutual wipe
]


@pytest.mark.parametrize("lid,predict,mirror,pr,winners,agree,flag", EIGHT, ids=[e[0] for e in EIGHT])
def test_the_eight_rescored(lid, predict, mirror, pr, winners, agree, flag):
    """"Expected re-scoring of the eight": L-0101 agree; L-0102 disagree; L-0103 mirror, not scored; L-0104 agree; L-0105 agree; L-0106 disagree; L-0107 agree; L-0108 agree (mutual wipe)."""
    mod = load_rate()
    fights = seeds_of(predict, winners, lid)
    rate = mod.rate(fights, pr, mirror=True) if mirror else mod.rate(fights, pr)
    assert (rate["agree"], rate["mirror"]) == (agree, flag), rate
    assert rate["band_gap"] == pytest.approx(abs(winners.count("A") / len(winners) - pr) * 100)
