# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 4 (units firing, opening window, two predictions, agreement, units never fired)
"""LI2, units firing over time, the two predictions and their agreement word, first contact, units never fired, and `not measured` propagation.

README 4: "Units firing, per side, through the fight." and "Two predictions per fight, both from the opening window after first contact. The count-only prediction is
the side with more unit-seconds firing. The type-weighted prediction weights each firing unit by the category multiplier of its category against its target of
record's category and nothing else (never damage, interval, health or a cross-layer damage multiplier; a unit that cannot fire contributes 0). The `agreement`
column says which prediction matched the outcome: `both_right`, `count_wrong_type_right`, `count_right_type_wrong`, `both_wrong`, or `n/a` (a draw, a cap, or a tie
in either prediction)."
Spec 4: "units firing over time with the opening window (40 ticks, DRAFT-opening-window-40, Westley's) and the whole fight". "If the V-then lab lacks a field the runner
does not synthesise it": a unit-firing cell with no `fired` in the file is `not measured`, never 0.
Weights (csrc/om_constants.h:518-526): Line->Line 1.0, Line->Siege 0.75, Line->Strike 1.5, Siege->Line 1.5, Siege->Siege 1.0, Siege->Strike 0.20, Strike->Line 0.75,
Strike->Siege 1.5, Strike->Strike 1.0; Vanguard and Warden are Line, Raider and Interceptor Strike, Bombard and Bastion Siege (scripts/skilllab/coverage.py CATEGORY).
Unit-seconds of a frame = units that fired in it times (tick - previous frame tick) / tick_rate: the file's `fired` is "fired since the previous captured frame".

Controls (green today): the lab's `evidence.agreement_word` is the word table this measure must reproduce (mapped side0/side1 to A/B)."""
import copy

import pytest

import measures_fixtures as fx

NM = fx.NOT_MEASURED
TICKS = list(range(0, 101, 10))
SIDE = {"A": "side0", "B": "side1"}


def _roster(*items):
    return [(i + 1, s, r) for i, (s, r) in enumerate(items)]


def _count_doc(winner="B", with_fired=True):
    """A1 Vanguard, A2 Bombard, B3 Raider, B4 Vanguard. First shot at tick 20. Window [20, 60): frames 20, 30, 40, 50.
    window A: 1 + 2 + 2 + 0 = 5 unit-frames = 2.5 s; window B: 0 + 1 + 2 + 1 = 4 = 2.0 s (count says A).
    whole A: 5 + 1 (tick 60) + 1 (tick 70) = 7 = 3.5 s; whole B: 4 + 2 + 2 + 2 (ticks 80 to 100) = 10 = 5.0 s (the whole fight says B)."""
    roster = _roster(("A", "Vanguard"), ("A", "Bombard"), ("B", "Raider"), ("B", "Vanguard"))
    fires = {20: {1}, 30: {1, 2, 3}, 40: {1, 2, 3, 4}, 50: {3}, 60: {1}, 70: {1}, 80: {3, 4}, 90: {3, 4}, 100: {3, 4}}
    tgt = {1: 3, 2: 3, 3: 1, 4: 2}              # A1 -> B3, A2 -> B3, B3 -> A1, B4 -> A2
    return fx.make_doc(roster, TICKS, pos=fx.static({1: (0, 0), 2: (0, 50), 3: (200, 0), 4: (200, 50)}),
                       fired=lambda u, t: u in fires.get(t, ()), target=lambda u, t: tgt[u], with_fired=with_fired,
                       res=fx.result(winner, [2, 0] if winner == "A" else [0, 2], 100))


def test_control_word_table_exists_in_the_lab():
    """Positive control: the lab's agreement words (scripts/skilllab/evidence.py) are the ones the measure must return."""
    from scripts.skilllab import evidence
    assert evidence.agreement_word("side0", "side0", "side1") == "count_right_type_wrong"
    assert evidence.agreement_word("side0", "tie", "side0") == "n/a"


def test_first_contact_is_the_first_frame_with_a_shot():
    assert fx.m().first_contact_tick(_count_doc()) == 20


def test_units_firing_by_frame_whole_and_window():
    """Spec 4: units firing over time. by_frame is [[tick, A units that fired, B units that fired], ...] as LI1's row writes it; the window is [first contact,
    first contact + DRAFT_OPENING_WINDOW_40); both in unit-seconds."""
    uf = fx.m().units_firing(_count_doc())
    assert uf["by_frame"] == [[0, 0, 0], [10, 0, 0], [20, 1, 0], [30, 2, 1], [40, 2, 2], [50, 0, 1], [60, 1, 0], [70, 1, 0], [80, 0, 2], [90, 0, 2], [100, 0, 2]]
    assert uf["first_contact"] == 20
    assert uf["window_ticks"] == fx.m().DRAFT_OPENING_WINDOW_40 == 40
    assert uf["window"] == pytest.approx([2.5, 2.0])
    assert uf["whole"] == pytest.approx([3.5, 5.0])
    assert uf["peak"] == [2, 2]


def test_window_length_is_a_parameter_not_a_constant_inside():
    """DRAFT-opening-window-40 is Westley's: the window can be asked for at another length (20 ticks: frames 20, 30 only)."""
    uf = fx.m().units_firing(_count_doc(), window_ticks=20)
    assert uf["window_ticks"] == 20
    assert uf["window"] == pytest.approx([1.5, 0.5])


def test_predictions_count_and_type_weighted_from_the_window():
    """Count-only: A (2.5 s against 2.0 s). Type-weighted, window frames 20 to 50:
    A1 (Line) at B3 (Strike) 1.5 in frames 20, 30, 40; A2 (Siege) at B3 (Strike) 0.20 in frames 30, 40; B3 (Strike) at A1 (Line) 0.75 in frames 30, 40, 50 (50: A1 stands
    in the file as the target); B4 (Vanguard, Line) at A2 (Siege) 0.75 in frame 40. A: (1.5 + 1.7 + 1.7) * 0.5 = 2.45. B: (0 + 0.75 + 1.5 + 0.75) * 0.5 = 1.5."""
    p = fx.m().predictions(_count_doc())
    assert p["count"] == "A" and p["type"] == "A"
    assert p["window_count"] == pytest.approx([2.5, 2.0])
    assert p["window_weighted"] == pytest.approx([2.45, 1.5])
    assert p["agreement"] == "both_wrong"           # the winner is B (the whole fight said so too), both window predictions say A


def test_agreement_word_follows_the_window_never_the_whole_fight():
    """Same shots, winner A: both window predictions say A: both_right, though the whole-fight totals (3.5 s against 5.0 s) point at B. The totals sit beside the
    window and never decide the word."""
    assert fx.m().predictions(_count_doc(winner="A"))["agreement"] == "both_right"


def _type_flip_doc(winner):
    """Count says A (3 Bombard firing at a Raider, 3 x 0.20) and type says B (2 Raiders firing at a Bombard, 2 x 1.5): one frame of shots at tick 20."""
    roster = _roster(("A", "Bombard"), ("A", "Bombard"), ("A", "Bombard"), ("B", "Raider"), ("B", "Raider"))
    tgt = {1: 4, 2: 4, 3: 4, 4: 1, 5: 1}
    return fx.make_doc(roster, [0, 10, 20, 30, 40, 50], pos=fx.static({1: (0, 0), 2: (0, 40), 3: (0, 80), 4: (300, 0), 5: (300, 40)}),
                       fired=lambda u, t: t == 20, target=lambda u, t: tgt[u], res=fx.result(winner, [0, 2] if winner == "B" else [3, 0], 50))


def test_type_weighting_can_flip_the_count_prediction():
    """Spec 3 R-arm: 'the count-only and type-weighted prediction beside the result'. Count A (1.5 s v 1.0 s); type B (0.3 v 1.5)."""
    p = fx.m().predictions(_type_flip_doc("B"))
    assert (p["count"], p["type"]) == ("A", "B")
    assert p["window_weighted"] == pytest.approx([0.3, 1.5])
    assert p["agreement"] == "count_wrong_type_right"
    assert fx.m().predictions(_type_flip_doc("A"))["agreement"] == "count_right_type_wrong"


def test_target_of_record_falls_back_to_nearest_living_enemy_and_a_dead_target_still_has_its_role():
    """A shooter with `target` null is weighed against the nearest living enemy at that frame (the lab's target of record rule), a shooter whose target died in the
    frame is weighed by that target's role. A1 (Vanguard) fires at tick 20 with no target: nearest living enemy is the Raider at 100 wu (not the Bombard at 500): 1.5.
    At tick 30 it fires at B4 (Bombard, dead in this frame): Line to Siege 0.75. A: (1.5 + 0.75) * 0.5 = 1.125."""
    roster = _roster(("A", "Vanguard"), ("B", "Raider"), ("B", "Bombard"), ("B", "Bombard"))
    pos = {1: (0, 0), 2: (100, 0), 3: (500, 0), 4: (600, 0)}
    doc = fx.make_doc(roster, [0, 10, 20, 30, 40, 50], pos=fx.static(pos), fired=lambda u, t: u == 1 and t in (20, 30),
                      target=lambda u, t: 4 if (u == 1 and t == 30) else None, alive=lambda u, t: not (u == 4 and t >= 30),
                      res=fx.result("A", [1, 2], 50))
    assert fx.m().predictions(doc)["window_weighted"] == pytest.approx([1.125, 0.0])


def test_no_shot_means_no_first_contact_and_a_tie_which_is_n_a():
    """Measured and quiet is not unmeasured: first contact None, windows 0.0, both predictions tie, agreement n/a."""
    roster = _roster(("A", "Vanguard"), ("B", "Vanguard"))
    doc = fx.make_doc(roster, [0, 10, 20], pos=fx.static({1: (0, 0), 2: (900, 0)}), fired=lambda u, t: False)
    assert fx.m().first_contact_tick(doc) is None
    uf = fx.m().units_firing(doc)
    assert uf["first_contact"] is None and uf["window"] == [0.0, 0.0] and uf["whole"] == [0.0, 0.0]
    p = fx.m().predictions(doc)
    assert (p["count"], p["type"], p["agreement"]) == ("tie", "tie", "n/a")


def _all_words():
    out = []
    for winner in ("A", "B", "draw", "cap"):
        for c in ("A", "B", "tie"):
            for t in ("A", "B", "tie"):
                out.append((winner, c, t))
    return out


@pytest.mark.parametrize("winner,count,typ", _all_words())
def test_agreement_word_matches_the_lab_word_table(winner, count, typ):
    """README 4: both_right, count_wrong_type_right, count_right_type_wrong, both_wrong, or n/a (a draw, a cap, or a tie in either prediction). Compared with the
    lab's `evidence.agreement_word` on the same cases, A and B standing for side0 and side1."""
    from scripts.skilllab import evidence
    side = lambda s: SIDE.get(s, s)                 # noqa: E731
    expected = evidence.agreement_word(side(winner) if winner in SIDE else winner, side(count), side(typ))
    assert fx.m().agreement_word(winner, count, typ) == expected


@pytest.mark.parametrize("winner,count,typ", [("A", NM, "A"), ("A", "A", NM), ("B", NM, NM)])
def test_agreement_word_with_an_unmeasured_prediction_is_not_measured(winner, count, typ):
    """Spec 4: a cell the file cannot support says so; it is not n/a (which is a measured draw, cap or tie) and never a guess."""
    assert fx.m().agreement_word(winner, count, typ).startswith(NM)


def test_not_measured_propagates_from_a_file_with_no_fired_flag():
    """A fight file with no per-unit `fired` (a lab that writes none): every firing-based cell is `not measured`, a string, never 0, 'tie' or 'n/a'; the cells the
    file does support are still measured (the row is not blanked)."""
    doc = _count_doc(with_fired=False)
    assert all("fired" not in u for f in doc["frames"] for u in f["units"])
    for cell in (fx.m().units_firing(doc), fx.m().first_contact_tick(doc), fx.m().never_fired(doc)):
        assert isinstance(cell, str) and cell.startswith(NM)
    p = fx.m().predictions(doc)
    assert all(isinstance(p[k], str) and p[k].startswith(NM) for k in ("count", "type", "agreement"))
    row = fx.m().measure_fight(doc)
    assert row["units_firing"].startswith(NM) and row["predictions"]["agreement"].startswith(NM) and row["never_fired"].startswith(NM)
    assert not isinstance(row["margin_survivors"], str) and not isinstance(row["margin_hp_share"], str)
    assert row["result"]["winner"] == "B"


def test_never_fired_counts_units_that_never_have_fired_true():
    """Units spawned (rows of frame 0) that have no frame with fired true, per side. A1 fires, A2 never, B3 fires, B4 never and dies, B5 never."""
    roster = _roster(("A", "Vanguard"), ("A", "Vanguard"), ("B", "Vanguard"), ("B", "Vanguard"), ("B", "Vanguard"))
    doc = fx.make_doc(roster, [0, 10, 20, 30], pos=fx.static({i: (50.0 * i, 0.0) for i in range(1, 6)}),
                      fired=lambda u, t: (u == 1 and t == 20) or (u == 3 and t == 30), alive=lambda u, t: not (u == 4 and t >= 20))
    assert fx.m().never_fired(doc) == {"A": 1, "B": 2, "total": 3, "units_start": 5}


def test_measures_do_not_change_the_document():
    doc = _count_doc()
    before = copy.deepcopy(doc)
    fx.m().measure_fight(doc)
    assert doc == before
