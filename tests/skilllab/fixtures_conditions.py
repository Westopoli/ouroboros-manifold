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
def row(baseline, outcome, window, whole, heads=16, agreement="both_right", predicted_count="side0", predicted_type="side0",
        family="range_up", play="s3_layer_above", layout="81"):
    """One fight row: firing_window / firing_unit_seconds are (side 0, side 1) pairs; one series (knob value 0.5, point "-", kind grid)."""
    import test_diagram
    res = test_diagram.fr(outcome, firing_window=window, firing_unit_seconds=whole, agreement=agreement,
                          predicted_count=predicted_count, predicted_type=predicted_type)
    r = rows_mod.fight_row(res, knob=test_diagram.KNOB[family], knob_value=0.5, baseline=baseline, ceiling_hit=0, prefight="ok",
                           family=family, play=play, layout=layout, kind="grid", enemy_heads=heads)
    r["point"] = "-"
    return r


def c2_rows():
    """Four play rows (no baseline). Agreement words by basis (types re-read on the whole fight from firing_unit_seconds):
        row  outcome  count  window words (the column)        whole: type from firing_unit_seconds   whole word
        1    side0    side0  (3,1) side0  both_right           (3,1) side0                            both_right
        2    side0    side0  (1,3) side1  count_right_type_wrong (3,1) side0                          both_right
        3    side1    side0  (3,1) side0  both_wrong           (1,3) side1                            count_wrong_type_right
        4    side0    side0  (3,1) side0  both_right           (2,2) tie                              n/a
    Row 4 sits at enemy_heads 24, the others at 16."""
    return [
        row("none", "side0", (3.0, 1.0), (3.0, 1.0), heads=16, agreement="both_right", predicted_type="side0"),
        row("none", "side0", (1.0, 3.0), (3.0, 1.0), heads=16, agreement="count_right_type_wrong", predicted_type="side1"),
        row("none", "side1", (3.0, 1.0), (1.0, 3.0), heads=16, agreement="both_wrong", predicted_type="side0"),
        row("none", "side0", (3.0, 1.0), (2.0, 2.0), heads=24, agreement="both_right", predicted_type="side0"),
    ]


# window / whole raw agreement counts of c2_rows(), in evidence.AGREEMENTS order
C2_COUNTS = {
    "window": {"both_right": 2, "count_wrong_type_right": 0, "both_wrong": 1, "count_right_type_wrong": 1, "n/a": 0},
    "whole": {"both_right": 2, "count_wrong_type_right": 1, "both_wrong": 0, "count_right_type_wrong": 0, "n/a": 1},
}
# (basis, scope, enemy_heads, fights) of the C2 verdict lines of c2_rows(): window then whole; pooled first, then the cells ascending
C2_LINES = [(b, s, h, n) for b in ("window", "whole") for (s, h, n) in (("pooled", "", 4), ("cell", "16", 3), ("cell", "24", 1))]


def c1_rows():
    """One series, one knob value, one headcount (16): play rows, then two baseline roles. Firing advantage (f0 - f1) / (f0 + f1):
        play (baseline none):  window (3,1) -> 0.5 and (5,3) -> 0.25: mean 0.375;  whole (1,3) -> -0.5 and (3,5) -> -0.25: mean -0.375
        naive_attacker:        window (5,3) 0.25, (3,5) -0.25, (9,7) 0.125 -> largest |.| 0.25;  whole the same three
        naive_defender:        window (1,3) -0.5, (3,3) 0.0 -> largest |.| 0.5;  whole (3,1) 0.5 -> 0.5
    (every value is exact in binary, so a strict > at the boundary is decided by the comparison, not by rounding)."""
    return [
        row("none", "side0", (3.0, 1.0), (1.0, 3.0)),
        row("none", "side0", (5.0, 3.0), (3.0, 5.0)),
        row("naive_attacker", "side1", (5.0, 3.0), (5.0, 3.0)),
        row("naive_attacker", "side1", (3.0, 5.0), (3.0, 5.0)),
        row("naive_attacker", "side1", (9.0, 7.0), (9.0, 7.0)),
        row("naive_defender", "side1", (1.0, 3.0), (3.0, 1.0)),
        row("naive_defender", "side1", (3.0, 3.0), (3.0, 1.0)),
    ]


# basis -> role -> (the play's mean firing advantage, the baseline's largest |firing advantage|) of c1_rows()
C1_NUMBERS = {
    "window": {"naive_attacker": (0.375, 0.25), "naive_defender": (0.375, 0.5)},
    "whole": {"naive_attacker": (-0.375, 0.25), "naive_defender": (-0.375, 0.5)},
}
