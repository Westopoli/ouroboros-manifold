# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R4, test T8, defect D8); ledger FINDING-lab-d8; positioning audit docs/northstar/plans/drift_audits/2026-10-19-positioning-in-code.md (section "How the paper score works", the measured table); piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, R4 / T8 / D8: the paper prediction, computed from the setup before anyone moves. Fast: no fight beyond three ticks.

R4: "per side, the units whose reach covers the enemy's layer, times the category weight, with a clear sightline through the Setup's blocks."
The definition the tests pin is the audit's measured one (the plan names no tie-break; every number below is the audit's, marked DRAFT):
  a unit COUNTS when some living enemy is at a layer offset inside its reach (R-164-01: -down <= layer(enemy) - layer(unit) <= up; reach from
  Setup.unit_types[name]["reach"], else (0, 0)) AND scenes.sight_clear finds a straight line through the Setup's blocks
  to that enemy; a counting unit adds the BEST ALG-60 category multiplier it has against the enemies it reaches and sees (not the sum). Range and
  movement are ignored. The side's score is the sum; the prediction is the larger score ("side0" | "side1" | "tie"). Setup sides, not engine
  factions: the score does not change with the fight's swap.
REACH SOURCE (audit gap F5, 2026-10-20): the reach of a unit is what the ENGINE would register for it, which is the Setup's own unit_types entry
  (engine.profile_reach after fight._register_types: the entry's "reach", else (0, 0)); a type with NO entry, or an entry without "reach", counts
  (0, 0), exactly like the engine (the real library's built-in Raider, Interceptor and Bombard all read (0, 0)). plays_space._REACH is the table
  the PLAYS copy into the Setups they build; the paper score does not read it. (The first draft of this oracle fell back to _REACH; the audit
  showed that disagrees with the engine for a type with no entry.)
THE PAPER WORD (Architect ruling 2026-10-20, implementation; Westley may veto): no reading names the winner by itself, and the paper reading
  folds in R7's structural oracle: when NOBODY can reach anybody at tick 0 (no living unit of either side has a living enemy at a layer offset
  inside its reach; sightlines and range are not part of that test) the paper word is "no_reach"; when some unit of some side can reach and the
  scores are equal it is "tie"; otherwise the larger side.

BUILDER CONTRACT (names DRAFT; the plan says only "the paper-prediction column; column name DRAFT"):
  scenes.paper_score(setup, engine=None) -> (float, float)               (score of Setup side 0, score of Setup side 1)
  scenes.paper_word(score) -> "side0" | "side1" | "tie"                  the larger; equal is "tie" (a score cannot say "no_reach")
  scenes.paper_prediction(setup, engine=None) -> "side0" | "side1" | "tie" | "no_reach"   DRAFT name: "no_reach" when the structural oracle says
                                                                          mutual no-reach at tick 0, else paper_word(paper_score(setup))
  contract.FightResult.paper_score: tuple = (0.0, 0.0)  and  .predicted_paper: str = "tie"      fight() fills both from the Setup before tick 1
                                                                          (predicted_paper from scenes.paper_prediction)
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

from scripts.skilllab import formations, plays, rows as rows_mod, scenes  # noqa: E402
from scripts.skilllab.contract import Block, FightResult, Group, Setup, Terrain  # noqa: E402
from test_rev3_c_support import oracle  # noqa: E402

ALG60 = [[1.0, 0.75, 1.5], [1.5, 1.0, 0.75], [0.2, 1.5, 1.0]]   # R-ALG-60: Strike, Line, Siege; row = attacker


def _reach(setup, g):
    """The reach the engine registers for g's type: the Setup's entry, else (0, 0). NOT plays_space._REACH (F5)."""
    r = setup.unit_types.get(g.unit, {}).get("reach")
    return tuple(r) if r is not None else (0, 0)


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


def ref_word(setup):
    """The paper word of the ruling: "no_reach" when the structural oracle (support.oracle, layers and reach only) says mutual at tick 0."""
    units = [(g.side, _reach(setup, g), g.layer) for g in setup.groups for _ in range(g.count)]
    if oracle(units) == ("mutual",):
        return "no_reach"
    a, b = ref(setup)
    return "side0" if a > b else "side1" if b > a else "tie"


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
    """Vanguards on layer 0 against Vanguards on layer 2 (reach (0, 0)): the score is (0, 0). The score-to-word map still says "tie" for
    equal scores (a score alone cannot say "no_reach"); the PREDICTION of this scene is "no_reach" (test below)."""
    s = S([G(0, "Vanguard", 3, 0), G(1, "Vanguard", 3, 2)])
    assert tuple(scenes.paper_score(s)) == (0.0, 0.0)
    assert scenes.paper_word(scenes.paper_score(s)) == "tie"


def test_the_paper_prediction_of_a_scene_where_nobody_can_reach_anybody_is_no_reach():
    """Ruling 2026-10-20 (3) and R7: no reading names the winner; the paper reading folds in the structural oracle, so a tick-0 scene in which
    no unit of either side has an enemy layer inside its reach is "no_reach" (not "tie"). Positive controls in the same test: the oracle
    agrees the scene is mutual, and the same scene with both sides on one layer is the ordinary "tie" (3.0 : 3.0, reach both ways)."""
    s = S([G(0, "Vanguard", 3, 0), G(1, "Vanguard", 3, 2)])
    assert ref_word(s) == "no_reach" and ref(s) == (0.0, 0.0)
    assert scenes.paper_prediction(s) == "no_reach"
    same_layer = S([G(0, "Vanguard", 3, 0), G(1, "Vanguard", 3, 0)])
    assert ref_word(same_layer) == "tie" and scenes.paper_prediction(same_layer) == "tie"


def test_a_reach_capable_type_with_no_target_layer_is_no_reach_in_the_prediction_too():
    """Interceptors (2, 1) on layer 0 against Raiders (1, 1) on layer 3: offset 3 is outside both reaches (the same fixture as the pre-flight and
    stall tests): (0, 0) and "no_reach", because the oracle looks at the reach table plus layers, not at the type name."""
    types = {"Raider": {"base": "Raider", "reach": (1, 1)}, "Interceptor": {"base": "Interceptor", "reach": (2, 1)}}
    s = S([G(0, "Interceptor", 2, 0), G(1, "Raider", 2, 3)], types=types)
    assert ref_word(s) == "no_reach" and scenes.paper_prediction(s) == "no_reach"


def test_one_way_reach_is_not_no_reach_in_the_prediction():
    """Interceptors (reach up 2) on layer 0 against Vanguards on layer 2: side 0 reaches, side 1 cannot. The oracle is not mutual, the
    scores are 2 x 0.75 : 0 (ALG-60, the audit's table) and the prediction is the larger side, "side0" (FINDING-lab-d11's decided case, seen from the paper)."""
    types = {"Interceptor": {"base": "Interceptor", "reach": (2, 1)}}
    s = S([G(0, "Interceptor", 2, 0), G(1, "Vanguard", 2, 2)], types=types)
    assert ref_word(s) == "side0" and ref(s) == (1.5, 0.0)
    assert scenes.paper_prediction(s) == "side0"


def test_the_best_multiplier_is_taken_not_the_sum():
    s = S([G(0, "Raider", 1, 0), G(1, "Vanguard", 1, 0), G(1, "Bombard", 1, 0, y=100.0)], types=RAIDER)
    assert scenes.paper_score(s)[0] == 1.5


def test_a_wall_between_the_sides_removes_the_sightline_and_the_score():
    """R4 'a clear sightline through the Setup's blocks'. Positive control in the same test: without the wall both sides score 3.0."""
    two = [G(0, "Vanguard", 3, 0, x=500.0, y=800.0), G(1, "Vanguard", 3, 0, x=1500.0, y=800.0)]
    wall = Terrain(canvas=(3000.0, 1600.0), blocks=(Block(900.0, 0.0, 1100.0, 1600.0),))
    assert tuple(scenes.paper_score(S(two))) == (3.0, 3.0)
    assert tuple(scenes.paper_score(S(two, terrain=wall))) == (0.0, 0.0)


def test_a_wall_makes_the_prediction_a_tie_not_no_reach():
    """The structural oracle reads reach and layers only (R7: the pre-flight's own reach test), so a wall that blocks every sightline leaves the
    scene reach-capable: scores (0, 0), word "tie". READING of the ruling's 'nobody can reach anybody' (sight is not reach); flagged in the
    report for the Architect."""
    wall = Terrain(canvas=(3000.0, 1600.0), blocks=(Block(900.0, 0.0, 1100.0, 1600.0),))
    s = S([G(0, "Vanguard", 3, 0, x=500.0, y=800.0), G(1, "Vanguard", 3, 0, x=1500.0, y=800.0)], terrain=wall)
    assert ref_word(s) == "tie"
    assert scenes.paper_prediction(s) == "tie"


def test_the_reach_a_setup_carries_beats_the_library_default():
    """Setup.unit_types[name]["reach"] is the reach read (R3: reach is a swept input): Raiders at (0, 0) on layer 1 score nothing against layer 0,
    at (1, 1) they score; the score moves with the table."""
    groups = [G(0, "Raider", 4, 1), G(1, "Vanguard", 4, 0)]
    none = S(groups, types={"Raider": {"base": "Raider", "reach": (0, 0)}})
    full = S(groups, types=RAIDER)
    assert scenes.paper_score(none)[0] == 0.0 and scenes.paper_score(full)[0] == 4 * 0.75


def test_the_paper_reach_is_the_engines_not_the_plays_table():
    """F5: a type with NO unit_types entry counts reach (0, 0), exactly like the engine, even where plays_space._REACH would say Raider (1, 1);
    an entry without a "reach" key counts (0, 0) too (the engine registers a fresh type with its default reach); the entry's own "reach" wins
    (control, same fixture): 4 Raiders on layer 1 against 4 Vanguards on layer 0."""
    groups = [G(0, "Raider", 4, 1), G(1, "Vanguard", 4, 0)]
    assert scenes.paper_score(S(groups, types={}))[0] == 0.0
    assert scenes.paper_score(S(groups, types={"Raider": {"base": "Raider"}}))[0] == 0.0
    assert scenes.paper_score(S(groups, types=RAIDER))[0] == 4 * 0.75


def test_control_the_engine_counts_a_type_without_an_entry_at_reach_zero():
    """Green on the base: the premise of the test above, read from the real library through fight._register_types and engine.profile_reach
    (the built-in Raider has no reach set; an entry with a reach sets it)."""
    from scripts.skilllab.engine import Engine
    from scripts.skilllab.fight import _register_types
    engine = Engine()
    for types, want in (({}, (0, 0)), ({"Raider": {"base": "Raider"}}, (0, 0)), (RAIDER, (1, 1))):
        w = engine.new_world(0)
        try:
            ids = _register_types(engine, w, S([G(0, "Raider", 1, 1), G(1, "Vanguard", 1, 0)], types=types))
            assert engine.profile_reach(w, ids["Raider"][0]) == want, (types, want)
        finally:
            engine.free_world(w)


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


def test_a_mutual_no_reach_fight_carries_the_word_no_reach():
    """Ruling (3): FightResult.predicted_paper is the prediction, "no_reach" for a scene where nobody can reach anybody (the fight itself
    stops at tick 1 as a no_reach_stall once C is built; today it runs its 3 ticks). Red today: no predicted_paper field."""
    from scripts.skilllab.fight import fight
    r = fight(S([G(0, "Vanguard", 3, 0), G(1, "Vanguard", 3, 2)]), 0, False)
    assert tuple(getattr(r, "paper_score")) == (0.0, 0.0)
    assert getattr(r, "predicted_paper") == "no_reach"


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
