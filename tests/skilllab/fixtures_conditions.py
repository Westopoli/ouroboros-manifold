# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md::34 item 2 (Architect 2026-10-19, corrected): the artifact's conditions section
"""Shared fixtures of the `artifact` conditions tests (test_report.py, test_main_artifact.py): rows, and PLACEHOLDER pass marks.

Every number named DRAFT_UNCONFIRMED_* below is a placeholder for the test, NOT a Westley pass mark: the pass marks are his and an
input (evidence.Thresholds has no defaults). The tests assert plumbing only (which field name is shown, which value is used, which side
of a strict comparison), never that any of these numbers is right.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from scripts.skilllab import rows as rows_mod  # noqa: E402

# ---- placeholder pass marks (clearly drafts) --------------------------------------------------------------------------------------
DRAFT_UNCONFIRMED_C1_MIN_FIRING_ADVANTAGE = 0.0625       # placeholder: binary-exact on purpose, see c1_rows
DRAFT_UNCONFIRMED_C2_RANK_AGREEMENT_ALWAYS_MET = -2.0     # placeholder: below every Spearman value, so "met" whatever the rows are
DRAFT_UNCONFIRMED_C2_RANK_AGREEMENT_NEVER_MET = 2.0       # placeholder: above every Spearman value, so "not met" whatever the rows are
DRAFT_UNCONFIRMED_C2_OFF_TREND_SHARE_ALWAYS_MET = 1.0     # placeholder: a share never exceeds 1
DRAFT_UNCONFIRMED_C2_OFF_TREND_SHARE_NEVER_MET = -1.0     # placeholder: a share is never below 0
DRAFT_UNCONFIRMED_C2_OFF_TREND_MARGIN = 0.125             # placeholder

# every field of evidence.Thresholds (scripts/skilllab/evidence.py); tuples are lists in JSON
THRESHOLD_FIELDS = ("c0_tolerance_units", "c1_min_firing_advantage", "c1_map_share", "c2_rank_agreement", "c2_off_trend_margin",
                    "c2_off_trend_share", "c3_stack_gain", "c4_max_share", "c5_min_loss", "c6_return_share", "c6_map_share",
                    "c8_map_share", "c7_ceiling_targets", "c9_length_bounds_ticks", "guard_tolerance_units")


def thresholds_dict(**over):
    """The JSON object of a --thresholds file (plain dict; the two tuple fields are lists). Placeholders only."""
    base = dict(c0_tolerance_units=1, c1_min_firing_advantage=DRAFT_UNCONFIRMED_C1_MIN_FIRING_ADVANTAGE, c1_map_share=0.5,
                c2_rank_agreement=DRAFT_UNCONFIRMED_C2_RANK_AGREEMENT_ALWAYS_MET,
                c2_off_trend_margin=DRAFT_UNCONFIRMED_C2_OFF_TREND_MARGIN,
                c2_off_trend_share=DRAFT_UNCONFIRMED_C2_OFF_TREND_SHARE_ALWAYS_MET,
                c3_stack_gain=0.0, c4_max_share=0.0, c5_min_loss=0.0, c6_return_share=0.0, c6_map_share=0.0, c8_map_share=0.0,
                c7_ceiling_targets=[0.0, 0.0], c9_length_bounds_ticks=[0, 0], guard_tolerance_units=0)
    base.update(over)
    assert tuple(base) == THRESHOLD_FIELDS or set(base) == set(THRESHOLD_FIELDS), "placeholder dict out of step with evidence.Thresholds"
    return base


def thresholds(**over):
    """The same placeholders as an evidence.Thresholds (tuples restored)."""
    from scripts.skilllab.evidence import Thresholds
    d = thresholds_dict(**over)
    d["c7_ceiling_targets"], d["c9_length_bounds_ticks"] = tuple(d["c7_ceiling_targets"]), tuple(d["c9_length_bounds_ticks"])
    return Thresholds(**d)


# ---- rows ------------------------------------------------------------------------------------------------------------------------
EQUAL_NUMBERS = 16                                        # decision 35 item 3: the equal-numbers cell, C1 reads this headcount only


def row(baseline, outcome, window, whole, heads=16, agreement="both_right", predicted_count="side0", predicted_type="side0",
        family="range_up", play="s3_layer_above", layout="81", knob_value=0.5, weighted=None):
    """One fight row. window / whole / weighted are (side 0, side 1) pairs: firing_window, firing_unit_seconds, weighted_unit_seconds
    (weighted None keeps test_diagram.fr's default). The predicted_count, predicted_type and agreement arguments are the WINDOW-basis columns."""
    import test_diagram
    extra = {} if weighted is None else {"weighted_unit_seconds": weighted}
    res = test_diagram.fr(outcome, firing_window=window, firing_unit_seconds=whole, agreement=agreement,
                          predicted_count=predicted_count, predicted_type=predicted_type, **extra)
    r = rows_mod.fight_row(res, knob=test_diagram.KNOB[family], knob_value=knob_value, baseline=baseline, ceiling_hit=0, prefight="ok",
                           family=family, play=play, layout=layout, kind="grid", enemy_heads=heads)
    r["point"] = "-"
    return r


def c2_rows():
    """Six play rows (no baseline). Window words are the `agreement` column; whole words are re-derived (decision 35 item 2):
    count = larger side of firing_unit_seconds (F), type = larger side of weighted_unit_seconds (W), equal = tie -> n/a.
        row  outcome  window word (column)        F      count  W      type   whole word
        1    side0    both_right                  (3,1)  side0  (3,1)  side0  both_right
        2    side0    count_right_type_wrong      (3,1)  side0  (3,1)  side0  both_right
        3    side1    both_wrong                  (1,3)  side1  (3,1)  side0  count_right_type_wrong     F and W DISAGREE
        4    side0    both_right                  (2,2)  tie    (3,1)  side0  n/a                        (count tie)
        5    side0    both_right                  (3,1)  side0  (2,2)  tie    n/a                        (type tie)
        6    side1    both_wrong                  (3,1)  side0  (1,3)  side1  count_wrong_type_right     F and W DISAGREE
    A builder that reads the whole-fight type from firing_unit_seconds gets rows 3 and 6 wrong (both_right / both_wrong); one that reads
    the count from weighted_unit_seconds gets them wrong the other way. Row 4 sits at enemy_heads 24, the others at 16."""
    return [
        row("none", "side0", (3.0, 1.0), (3.0, 1.0), agreement="both_right", predicted_type="side0", weighted=(3.0, 1.0)),
        row("none", "side0", (1.0, 3.0), (3.0, 1.0), agreement="count_right_type_wrong", predicted_type="side1", weighted=(3.0, 1.0)),
        row("none", "side1", (3.0, 1.0), (1.0, 3.0), agreement="both_wrong", predicted_type="side0", weighted=(3.0, 1.0)),
        row("none", "side0", (3.0, 1.0), (2.0, 2.0), heads=24, agreement="both_right", predicted_type="side0", weighted=(3.0, 1.0)),
        row("none", "side0", (3.0, 1.0), (3.0, 1.0), agreement="both_right", predicted_type="side0", weighted=(2.0, 2.0)),
        row("none", "side1", (3.0, 1.0), (3.0, 1.0), agreement="both_wrong", predicted_type="side0", weighted=(1.0, 3.0)),
    ]


# window / whole raw agreement counts of c2_rows(), in evidence.AGREEMENTS order
C2_COUNTS = {
    "window": {"both_right": 3, "count_wrong_type_right": 0, "both_wrong": 2, "count_right_type_wrong": 1, "n/a": 0},
    "whole": {"both_right": 2, "count_wrong_type_right": 1, "both_wrong": 0, "count_right_type_wrong": 1, "n/a": 2},
}
# (basis, scope, enemy_heads, fights) of the C2 verdict lines of c2_rows(): window then whole; pooled first, then the cells ascending
C2_LINES = [(b, s, h, n) for b in ("window", "whole") for (s, h, n) in (("pooled", "", 6), ("cell", "16", 5), ("cell", "24", 1))]


def c1_rows(knob_value=0.5):
    """One series, one knob value, one headcount (16 = the equal-numbers cell): play rows, then two baseline roles. Firing advantage
    (f0 - f1) / (f0 + f1):
        play (baseline none):  window (3,1) -> 0.5 and (5,3) -> 0.25: mean 0.375;  whole (1,3) -> -0.5 and (3,5) -> -0.25: mean -0.375
        naive_attacker:        window (5,3) 0.25, (3,5) -0.25, (9,7) 0.125 -> largest |.| 0.25;  whole the same three
        naive_defender:        window (1,3) -0.5, (3,3) 0.0 -> largest |.| 0.5;  whole (3,1) 0.5 -> 0.5
    (every value is exact in binary, so a strict > at the boundary is decided by the comparison, not by rounding)."""
    k = dict(knob_value=knob_value)
    return [
        row("none", "side0", (3.0, 1.0), (1.0, 3.0), **k),
        row("none", "side0", (5.0, 3.0), (3.0, 5.0), **k),
        row("naive_attacker", "side1", (5.0, 3.0), (5.0, 3.0), **k),
        row("naive_attacker", "side1", (3.0, 5.0), (3.0, 5.0), **k),
        row("naive_attacker", "side1", (9.0, 7.0), (9.0, 7.0), **k),
        row("naive_defender", "side1", (1.0, 3.0), (3.0, 1.0), **k),
        row("naive_defender", "side1", (3.0, 3.0), (3.0, 1.0), **k),
    ]


# basis -> (knob value, role) -> (the play's mean firing advantage, the baseline's largest |firing advantage|) of c1_rows()
C1_NUMBERS = {
    "window": {(0.5, "naive_attacker"): (0.375, 0.25), (0.5, "naive_defender"): (0.375, 0.5)},
    "whole": {(0.5, "naive_attacker"): (-0.375, 0.25), (0.5, "naive_defender"): (-0.375, 0.5)},
}


def c1_off_cell_rows():
    """Rows at enemy_heads 24 that would change every C1 number if they were read: the play loses badly there and the attacker wins badly.
    Added to c1_rows(), they must change nothing (C1 reads the equal-numbers cell only)."""
    return [
        row("none", "side1", (1.0, 9.0), (1.0, 9.0), heads=24),
        row("naive_attacker", "side0", (9.0, 1.0), (9.0, 1.0), heads=24),
        row("naive_defender", "side0", (9.0, 1.0), (9.0, 1.0), heads=24),
    ]


def c1_two_knob_rows():
    """c1_rows() at knob 0.5 plus a knob 0.25 series (attacker only): play window (1,3) -> -0.5 twice, whole (3,1) -> 0.5 twice; attacker
    window (5,3) -> 0.25, whole (5,3) -> 0.25. With the minimum 0.0625 the attacker line is true on the window at 0.5 and false at 0.25,
    and true on the whole fight at 0.25 and false at 0.5: pooling the knob values (play mean -0.0625 on the window) would match neither."""
    k = dict(knob_value=0.25)
    return c1_rows() + [
        row("none", "side0", (1.0, 3.0), (3.0, 1.0), **k),
        row("none", "side0", (1.0, 3.0), (3.0, 1.0), **k),
        row("naive_attacker", "side1", (5.0, 3.0), (5.0, 3.0), **k),
    ]


C1_TWO_KNOB_NUMBERS = {
    "window": {(0.25, "naive_attacker"): (-0.5, 0.25), **C1_NUMBERS["window"]},
    "whole": {(0.25, "naive_attacker"): (0.5, 0.25), **C1_NUMBERS["whole"]},
}


def c1_cut_rows():
    """A scan cut below the equal-numbers cell (baseline_no_fit): the play and the attacker have rows at enemy_heads 8 only. No C1."""
    return [
        row("none", "side0", (3.0, 1.0), (3.0, 1.0), heads=8),
        row("naive_attacker", "side1", (5.0, 3.0), (5.0, 3.0), heads=8),
    ]


def c1_baseline_missing_rows():
    """The play has the cell (16) at knob 0.5; the attacker has rows at 8 only (not placed at 16): no C1 for that role at that knob.
    The defender has its row at 16 and keeps its line."""
    return [
        row("none", "side0", (3.0, 1.0), (1.0, 3.0)),
        row("naive_attacker", "side1", (5.0, 3.0), (5.0, 3.0), heads=8),
        row("naive_defender", "side1", (1.0, 3.0), (3.0, 1.0)),
    ]
