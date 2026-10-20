# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R4, test T8, defect D8); ledger FINDING-lab-d8; positioning audit docs/northstar/plans/drift_audits/2026-10-19-positioning-in-code.md (section "How the paper score works", the measured table); piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, R4 / T8 / D8: the paper prediction, computed from the setup before anyone moves. Fast: no fight beyond three ticks.

R4: "per side, the units whose reach covers the enemy's layer, times the category weight, with a clear sightline through the Setup's blocks."
The definition the tests pin is the audit's measured one (the plan names no tie-break; every number below is the audit's, marked DRAFT):
  a unit COUNTS when some living enemy is at a layer offset inside its reach (R-164-01: -down <= layer(enemy) - layer(unit) <= up; reach from
  Setup.unit_types[name]["reach"], else plays_space._REACH, else (0, 0)) AND scenes.sight_clear finds a straight line through the Setup's blocks
  to that enemy; a counting unit adds the BEST ALG-60 category multiplier it has against the enemies it reaches and sees (not the sum). Range and
  movement are ignored. The side's score is the sum; the prediction is the larger score ("side0" | "side1" | "tie"). Setup sides, not engine
  factions: the score does not change with the fight's swap.

BUILDER CONTRACT (names DRAFT; the plan says only "the paper-prediction column; column name DRAFT"):
  scenes.paper_score(setup, engine=None) -> (float, float)               (score of Setup side 0, score of Setup side 1)
  scenes.paper_word(score) -> "side0" | "side1" | "tie"                  the larger; equal is "tie"
  contract.FightResult.paper_score: tuple = (0.0, 0.0)  and  .predicted_paper: str = "tie"      fight() fills both from the Setup before tick 1
  rows.fight_row writes the columns paper_score_0, paper_score_1, predicted_paper (the CSV has them on every row).
Red today: scenes.paper_score does not exist; FightResult has no paper fields; the rows have no paper columns. The reference oracle below is
green on the base (its own controls are the first tests)."""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import formations, plays, plays_space, rows as rows_mod, scenes  # noqa: E402
from scripts.skilllab.contract import Block, FightResult, Group, Setup, Terrain  # noqa: E402

ALG60 = [[1.0, 0.75, 1.5], [1.5, 1.0, 0.75], [0.2, 1.5, 1.0]]   # R-ALG-60: Strike, Line, Siege; row = attacker


def _reach(setup, g):
    entry = setup.unit_types.get(g.unit, {})
    r = entry.get("reach")
    return tuple(r) if r is not None else plays_space._REACH.get(entry.get("base", g.unit), (0, 0))


def _units(setup, side):
    out = []
    for g in setup.groups:
        if g.side == side:
            base = setup.unit_types.get(g.unit, {}).get("base", g.unit)
            for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
                out.append((x, y, g.layer, plays.unit_stats(base)["category"], _reach(setup, g)))
    return out


def ref_score(setup, side):
    """The audit's paper score of one Setup side (independent of the builder)."""
    total = 0.0
    for x, y, la, cat, (up, down) in _units(setup, side):
        seen = [e for e in _units(setup, 1 - side) if -down <= e[2] - la <= up
                and scenes.sight_clear(setup.terrain, (x, y), la, (e[0], e[1]), e[2])]
        if seen:
            total += max(ALG60[cat][e[3]] for e in seen)
    return total


def ref(setup):
    return ref_score(setup, 0), ref_score(setup, 1)


def G(side, unit, count, layer, x=None, y=0.0, order="attack_move"):
    return Group(side=side, unit=unit, count=count, formation="line", x=(-300.0 if side == 0 else 300.0) if x is None else x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=layer, order=order, goal=None, params={"spacing": 30.0})


def S(groups, terrain=None, types=None, cap=3):
    return Setup(groups=tuple(groups), unit_types=types if types is not None else {}, terrain=terrain, max_ticks=cap)


RAIDER = {"Raider": {"base": "Raider", "reach": (1, 1)}}


# ---- the oracle's own controls (green on the base): the hand-computed numbers --------------------------------------------------------

def test_oracle_hand_numbers_reach_filter_and_best_multiplier():
    """4 Raiders (Strike, reach (1, 1)) on layer 1 and 4 Vanguards (Line) on layer 0 against 8 Vanguards on layer 0: side 0 = 4 x 0.75 (a Raider
    hits a Line from layer 1) + 4 x 1.0 = 7.0; side 1 = 8 x 1.0 (a Vanguard reaches only the layer-0 Vanguards) = 8.0."""
    s = S([G(0, "Raider", 4, 1), G(0, "Vanguard", 4, 0, y=200.0), G(1, "Vanguard", 8, 0)], types=RAIDER)
    assert ref(s) == (7.0, 8.0)


def test_oracle_best_multiplier_not_the_sum():
    """One Raider (Strike) against a Line and a Siege on its own layer scores the better 1.5, not 0.75 + 1.5."""
    s = S([G(0, "Raider", 1, 0), G(1, "Vanguard", 1, 0), G(1, "Bombard", 1, 0, y=100.0)], types=RAIDER)
    assert ref_score(s, 0) == 1.5


def test_oracle_out_of_reach_scores_zero_and_a_wall_blocks_the_line():
    assert ref(S([G(0, "Vanguard", 3, 0), G(1, "Vanguard", 3, 2)])) == (0.0, 0.0)
    wall = Terrain(canvas=(3000.0, 1600.0), blocks=(Block(900.0, 0.0, 1100.0, 1600.0),))
    two = [G(0, "Vanguard", 3, 0, x=500.0, y=800.0), G(1, "Vanguard", 3, 0, x=1500.0, y=800.0)]
    assert ref(S(two)) == (3.0, 3.0) and ref(S(two, terrain=wall)) == (0.0, 0.0)


# ---- T8 / R4: scenes.paper_score (red today: no such function) -----------------------------------------------------------------------

def test_the_paper_score_counts_reach_and_the_best_category_weight():
    """R4: the same hand fixture as the oracle's first control. Red today: AttributeError, scenes.paper_score."""
    s = S([G(0, "Raider", 4, 1), G(0, "Vanguard", 4, 0, y=200.0), G(1, "Vanguard", 8, 0)], types=RAIDER)
    assert tuple(scenes.paper_score(s)) == (7.0, 8.0) == ref(s)
    assert scenes.paper_word(scenes.paper_score(s)) == "side1"


def test_a_unit_that_cannot_reach_any_enemy_layer_adds_nothing():
    """Vanguards on layer 0 against Vanguards on layer 2 (reach (0, 0)): (0, 0) and the word is a tie."""
    s = S([G(0, "Vanguard", 3, 0), G(1, "Vanguard", 3, 2)])
    assert tuple(scenes.paper_score(s)) == (0.0, 0.0)
    assert scenes.paper_word(scenes.paper_score(s)) == "tie"


def test_the_best_multiplier_is_taken_not_the_sum():
    s = S([G(0, "Raider", 1, 0), G(1, "Vanguard", 1, 0), G(1, "Bombard", 1, 0, y=100.0)], types=RAIDER)
    assert scenes.paper_score(s)[0] == 1.5


def test_a_wall_between_the_sides_removes_the_sightline_and_the_score():
    """R4 'a clear sightline through the Setup's blocks'. Positive control in the same test: without the wall both sides score 3.0."""
    two = [G(0, "Vanguard", 3, 0, x=500.0, y=800.0), G(1, "Vanguard", 3, 0, x=1500.0, y=800.0)]
    wall = Terrain(canvas=(3000.0, 1600.0), blocks=(Block(900.0, 0.0, 1100.0, 1600.0),))
    assert tuple(scenes.paper_score(S(two))) == (3.0, 3.0)
    assert tuple(scenes.paper_score(S(two, terrain=wall))) == (0.0, 0.0)


def test_the_reach_a_setup_carries_beats_the_library_default():
    """Setup.unit_types[name]["reach"] is the reach read (R3: reach is a swept input): Raiders at (0, 0) on layer 1 score nothing against layer 0,
    at (1, 1) they score; the score moves with the table."""
    groups = [G(0, "Raider", 4, 1), G(1, "Vanguard", 4, 0)]
    none = S(groups, types={"Raider": {"base": "Raider", "reach": (0, 0)}})
    full = S(groups, types=RAIDER)
    assert scenes.paper_score(none)[0] == 0.0 and scenes.paper_score(full)[0] == 4 * 0.75


# ---- the fight carries it; the rows write it -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("swap", [False, True])
def test_a_fight_result_carries_the_paper_score_of_the_setup_whatever_the_swap(swap):
    """The score is computed before tick 1 from the Setup's own sides; a swap of the engine factions does not change it. Real library, 3
    ticks. Red today: FightResult has no paper_score."""
    from scripts.skilllab.fight import fight
    s = S([G(0, "Raider", 4, 1), G(0, "Vanguard", 4, 0, y=200.0), G(1, "Vanguard", 8, 0)], types=RAIDER)
    r = fight(s, 0, swap)
    assert tuple(getattr(r, "paper_score")) == (7.0, 8.0)
    assert getattr(r, "predicted_paper") == "side1"


def _result(**kw):
    base = dict(outcome="side0", margin=0.5, strength_left=(0.5, 0.0), survivors=(8, 0), heads=(16, 16), ticks=300, first_contact_tick=20,
                firing=[], firing_unit_seconds=(100.0, 50.0))
    base.update(kw)
    return FightResult(**base)


def test_the_row_has_the_three_paper_columns_and_the_csv_keeps_them(tmp_path):
    """T8 'the paper prediction exists in the CSV'. Red today: FightResult(paper_score=...) is a TypeError."""
    r = _result(paper_score=(20.0, 16.0), predicted_paper="side0")
    row = rows_mod.fight_row(r)
    assert (row["paper_score_0"], row["paper_score_1"], row["predicted_paper"]) == (20.0, 16.0, "side0")
    rows_mod.write_rows([row], tmp_path / "r.csv")
    with open(tmp_path / "r.csv", newline="") as fh:
        got = list(csv.DictReader(fh))[0]
    assert (got["paper_score_0"], got["paper_score_1"], got["predicted_paper"]) == ("20.0", "16.0", "side0")


def test_control_a_result_without_paper_fields_still_makes_a_row():
    """Green today and after: the existing columns of a fight row are untouched."""
    row = rows_mod.fight_row(_result())
    assert row["outcome"] == "side0" and row["predicted_count"] == "tie"
