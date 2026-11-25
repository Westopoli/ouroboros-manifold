# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 4 (result, survivors, margin) and section 1 precondition 8 ("draws are lab bugs")
"""LI2, result, survivors and the two named margins. Each test names the section it proves.

Spec 4: "Reused as they are (cite the file): result (`side0`, `side1`, `draw`, `cap`), survivors, margin".
README 4: "Margin. Reported beside every fight: the share of one side's strength left, minus the other's."
Spec 4: "A `draw` or `cap` in any cell marks the cell `defect`, never a result (Q-LAB-03)."
LI1 interface: "`margin` ... `survivors[0] - survivors[1]` (side A minus side B; positive means A ended ahead)" and that definition is Open for the chat, so BOTH
definitions are measured and named: `margin_survivors` (A survivors minus B survivors) and `margin_hp_share` (A's summed hp fraction left over A's heads, minus B's).
A bare `margin` key must not exist: the name would hide which definition a row means.

Control (green today): the synthetic document builder writes a document the lab's own `snapshot.validate` accepts."""
import copy

import pytest

import measures_fixtures as fx

ROSTER = [(1, "A", "Vanguard"), (2, "A", "Vanguard"), (3, "A", "Vanguard"), (4, "A", "Vanguard"), (5, "B", "Raider"), (6, "B", "Raider")]
TICKS = [0, 50, 100]


def _hp_doc(res=None):
    """A: four units of 100 hp, left with 100, 50, 0, 0 (two alive); B: two units of 200 hp, left with 100, 200 (two alive)."""
    left = {1: 100.0, 2: 50.0, 3: 0.0, 4: 0.0, 5: 100.0, 6: 200.0}
    start = {1: 100.0, 2: 100.0, 3: 100.0, 4: 100.0, 5: 200.0, 6: 200.0}
    return fx.make_doc(ROSTER, TICKS, pos=fx.static({u: (100.0 * u, 0.0) for u, _, _ in ROSTER}),
                       hp=lambda u, t: start[u] if t < 100 else left[u], res=res)


def _plain(winner, survivors, end="wipe", ticks=100):
    return fx.make_doc(ROSTER, TICKS, pos=fx.static({u: (100.0 * u, 0.0) for u, _, _ in ROSTER}), res=fx.result(winner, survivors, ticks, end))


def test_control_synthetic_documents_are_valid_lab_files():
    """Positive control: the builder's output passes the lab's own validator, so a red below is the missing module, not a malformed fixture."""
    from scripts.skilllab.arena import snapshot
    assert snapshot.validate(_plain("A", [3, 0])) == []
    assert snapshot.validate(_plain("A", [3, 0], "apart")) == []


@pytest.mark.parametrize("winner,surv,end,word,defect", [
    ("A", [3, 0], "wipe", "A", False),
    ("B", [0, 5], "wipe", "B", False),
    ("draw", [14, 22], "apart", "draw", True),
    ("none", [0, 0], "wipe", "draw", True),
    ("stall", [2, 2], "silence", "draw", True),
    ("draw", [6, 11], "cap", "cap", True),
])
def test_result_word_and_defect(winner, surv, end, word, defect):
    """Spec 4 and README 4: the result is A, B, draw or cap; a draw or a cap is a defect, never a result (both sides alive at the end, a stall and both dead on one
    tick are all `draw`; the end word `cap` wins over a `draw` winner)."""
    r = fx.m().result_of(_plain(winner, surv, end))
    assert r["winner"] == word
    assert r["defect"] is defect
    assert r["end"] == end
    assert r["survivors"] == surv
    assert r["last_tick"] == 100


def test_survivors_come_from_the_result_not_the_last_frame():
    """The last frame of a real every-2-ticks file can be one tick before `result.ticks` (SIT-0106 approved: last frame 2314, ticks 2315), so the engine's own
    `result.survivors` is the answer; the last frame alone would say a unit still lives."""
    doc = _hp_doc(res=fx.result("A", [1, 0], 100))          # frames say 2 and 2 alive at the end; the result says 1 and 0
    assert fx.m().survivors(doc) == [1, 0]
    assert fx.m().margin_survivors(doc) == 1


@pytest.mark.parametrize("surv,expected", [([3, 0], 3), ([0, 5], -5), ([4, 4], 0), ([14, 22], -8)])
def test_margin_survivors_is_a_minus_b(surv, expected):
    """Named definition one: A survivors minus B survivors; positive means A ended ahead."""
    assert fx.m().margin_survivors(_plain("A", surv)) == expected


def test_margin_hp_share_is_strength_share_left_a_minus_b():
    """Named definition two (README 4 'the share of one side's strength left, minus the other's'; fight.py `_strength`: summed hp fraction of the living over the
    side's heads). A: (100/100 + 50/100) / 4 = 0.375. B: (100/200 + 200/200) / 2 = 0.75. Margin -0.375, while the survivors margin is 0 (2 and 2):
    the two definitions disagree here, which is why both are named."""
    doc = _hp_doc(res=fx.result("none", [2, 2], 100))
    assert fx.m().margin_hp_share(doc) == pytest.approx(-0.375, abs=1e-9)
    assert fx.m().margin_survivors(doc) == 0


def test_margin_hp_share_uses_the_last_frame_and_the_first_frame_hp_as_the_start():
    """Strength is read against each unit's own hp at tick 0 (the file carries no max hp): a unit that started at 200 and is at 100 is half, not a full unit."""
    doc = _hp_doc()
    full = copy.deepcopy(doc)
    assert fx.m().margin_hp_share(doc) == pytest.approx(-0.375, abs=1e-9)
    assert doc == full, "a measure must not change the document it reads"


def test_measure_row_names_both_margins_and_never_a_bare_margin():
    """A row carries `margin_survivors` and `margin_hp_share`; a bare `margin` is absent so a reader never has to guess which one it holds."""
    row = fx.m().measure_fight(_hp_doc(res=fx.result("none", [2, 2], 100)))
    assert "margin_survivors" in row and "margin_hp_share" in row
    assert "margin" not in row
