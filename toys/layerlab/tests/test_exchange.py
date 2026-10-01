"""Windowed firing-share exchange: SPEC section 8 (the `analysis.py` bullet: `exchange`, `ExchangeTable`,
`check_exchange`, and the `exchange` CLI command) and README 6.3 and 8
(docs/northstar/research/layer_dynamics/README.md: "the sustained form should compare rates, not predict
the winner from totals: per window of ticks, each side's share of units firing against its share of damage
dealt and of losses taken"; "an even exchange is not an even outcome when the totals differ").

The form (SPEC 8): windows are consecutive blocks of `window` ticks from `result.first_shot_tick` to the
last trace tick (the last may be short; none when no shot was fired). Per window and side: `firing_s` =
mean number of the side's units with trace flag bit4 per tick; `dealt_s` = HP removed from the OTHER side's
units (sum over units of max(0, hp at the tick before the window - hp at the window's last tick)); `lost_s`
= the side's units with alive 1 at the previous tick and 0 at the window's last tick. Shares f_A, d_A, l_A
= A / (A + B), `None` when the denominator is 0. State: agree / disagree / even / idle.

Conventions:
- Stand-in results are `types.SimpleNamespace` objects with a real-dtype trace and only the fields SPEC 8
  says `exchange` reads: `trace`, `first_shot_tick`, `unit`, `survivors`. A reader of any other field
  (firing_ticks, alive_ticks, firing_weight, winner) hits AttributeError: that is the no-leak check.
- The analysis module is imported inside each test, so a missing function fails that test only.
- Scenario counts come from scenarios/r0_raiders_10v5.toml edited with set_path (raider hp 250).

Choices this file makes where SPEC 8 is silent (a builder who reads SPEC 8 differently must raise it,
not bend the tests):
- `start` is the first tick of a window and `end` is one past its last tick (the same convention as
  `predict_early`), so `end - start == window` except for the last window, whose `end` is the trace length.
- First-window HP reference: the hand-built traces hold every unit at its starting HP (the raider's 250)
  on every tick before the first shot, so "start HP from the scenario" and "HP at first_shot_tick - 1" agree.
  The shot at first_shot_tick lands on that same tick (hp already lower at tick t0), so a reference of
  hp[t0] would lose it: a test pins that.
- `even` takes precedence over agree / disagree (both shares within 0.02 of 0.5 is noise, whichever side of
  0.5 each lands), and `idle` (a `None` f or d) takes precedence over everything.
- `check_exchange` returns a dict with the keys `agree_fraction`, `firing_ratio`, `damage_ratio`,
  `higher_firing_won`. `firing_ratio` / `damage_ratio` are means over the seeds where the ratio is not
  `None` (`None` when no seed has one); `higher_firing_won` is, over seeds with a decisive winner (A or B)
  and a `firing_ratio` that is not `None` and not 1, the fraction where the side with the higher firing
  ratio won.
"""
import re
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

import layerlab.run as runmod
from conftest import LAB
from layerlab import scenario
from layerlab.ffi import WIN_A, WIN_B

BIT4 = 16
SCEN = LAB / "scenarios"
HP0 = 250.0
_DTYPE = np.dtype([("x", "<f4"), ("y", "<f4"), ("hp", "<f4"), ("progress", "<f4"),
                   ("layer", "u1"), ("side", "u1"), ("alive", "u1"), ("flags", "u1")])


def _analysis():
    import layerlab.analysis as analysis
    return analysis


def _load(name):
    return scenario.load(str(SCEN / name))


def _counts(n_a, n_b):
    """The 10 v 5 raider scenario with start counts (n_a, n_b)."""
    scn = scenario.set_path(_load("r0_raiders_10v5.toml"), "groups[0].count", n_a)
    return scenario.set_path(scn, "groups[1].count", n_b)


def _build(sides, ticks, fire=(), hp_steps=(), dead_from=None):
    """A trace (ticks, units) with every unit alive and at HP0 unless told otherwise.
    `fire`: (unit, lo, hi) half-open tick ranges with bit4 set. `hp_steps`: (unit, from_tick, hp) in
    tick order per unit (hp holds from that tick on). `dead_from`: unit -> first tick with alive 0."""
    units = len(sides)
    tr = np.zeros((ticks, units), dtype=_DTYPE)
    tr["side"] = np.asarray(sides, dtype=np.uint8)[None, :]
    tr["alive"] = 1
    tr["hp"] = HP0
    for u, lo, hi in fire:
        tr["flags"][lo:hi, u] = BIT4
    for u, t, hp in hp_steps:
        tr["hp"][t:, u] = hp
    for u, t in (dead_from or {}).items():
        tr["alive"][t:, u] = 0
    return tr


def _result(trace, first_shot_tick, survivors=(1, 1), **extra):
    """Stand-in carrying only what exchange may read (SPEC 8). `unit` is the final state per unit."""
    last = trace[-1]
    unit = [{"x": float(r["x"]), "y": float(r["y"]), "hp": float(r["hp"]), "layer": int(r["layer"]),
             "alive": int(r["alive"]), "transitions": 0} for r in last]
    return SimpleNamespace(trace=trace, first_shot_tick=first_shot_tick, unit=unit,
                           survivors=tuple(survivors), **extra)


SIDES8 = [0, 0, 0, 0, 1, 1, 1, 1]


def _hand():
    """The hand-built 4 v 4 case: 30 ticks, first_shot_tick 5, window 10 -> windows [5,15) [15,25) [25,30).

    Window 0 (ticks 5..14): A0 A1 A2 fire all 10 ticks (3.0); B4 and B6 fire 5 ticks each (1.0).
      B4 loses 50 (hp 200 from tick 5 = the first-shot tick itself), B5 loses 20 (tick 12), B6 dies at
      tick 11 (250), B7 loses 30 (tick 10): dealt_A = 350. A0 loses 10 (tick 9): dealt_B = 10.
      lost_A = 0, lost_B = 1 (B6). f_A = 3/4, d_A = 350/360: agree.
    Window 1 (ticks 15..24): A0 fires 10 ticks, A2 fires 5 (then dies at tick 20): 1.5; B4 fires 10: 1.0.
      B4 loses 10 more (tick 17); B7 HEALS 20 (220 -> 240 at tick 20: counts 0, not -20); B6 is dead
      since window 0 (not a new loss, no new damage). A2 dies at tick 20 (250 lost): dealt_B = 250.
      lost_A = 1, lost_B = 0. f_A = 1.5/2.5 = 0.6, d_A = 10/260: disagree.
    Window 2 (ticks 25..29, 5 ticks): nobody fires, nothing changes: idle, short.
    """
    fire = [(0, 5, 25), (1, 5, 15), (2, 5, 20), (4, 5, 10), (4, 15, 25), (6, 5, 10)]
    steps = [(4, 5, 200.0), (4, 17, 190.0), (5, 12, 230.0), (6, 11, 0.0), (7, 10, 220.0), (7, 20, 240.0),
             (0, 9, 240.0), (2, 20, 0.0)]
    tr = _build(SIDES8, 30, fire=fire, hp_steps=steps, dead_from={6: 11, 2: 20})
    return _result(tr, 5, survivors=(3, 3))


def _exchange(res, scn=None, window=10):
    return _analysis().exchange(res, scn if scn is not None else _counts(4, 4), window=window)


# ---- 1. window layout ---------------------------------------------------------------------------

def test_windows_are_consecutive_blocks_from_first_shot_to_trace_end_last_short():
    """SPEC 8: 45 ticks, first_shot_tick 7, window 10: [7,17) [17,27) [27,37) [37,45), the last one
    short (8 ticks). start/end: end is one past the last tick (file docstring)."""
    tr = _build(SIDES8, 45)
    t = _exchange(_result(tr, 7), window=10)
    assert [(w["start"], w["end"]) for w in t.windows] == [(7, 17), (17, 27), (27, 37), (37, 45)]
    assert t.window == 10


def test_windows_exact_multiple_has_no_extra_empty_window():
    """SPEC 8 (twin of the short-last case): 47 ticks, first 7, window 10 -> exactly 4 windows, the last
    [37, 47) full length; no empty fifth window."""
    t = _exchange(_result(_build(SIDES8, 47), 7), window=10)
    assert [(w["start"], w["end"]) for w in t.windows] == [(7, 17), (17, 27), (27, 37), (37, 47)]


def test_window_larger_than_the_rest_gives_one_short_window():
    """SPEC 8: window 100 over a 45-tick trace from tick 7: a single window [7, 45)."""
    t = _exchange(_result(_build(SIDES8, 45), 7), window=100)
    assert [(w["start"], w["end"]) for w in t.windows] == [(7, 45)]


def test_window_of_one_tick_gives_one_window_per_tick():
    """SPEC 8: window 1 from tick 7 of a 12-tick trace: 5 windows, (7,8) .. (11,12)."""
    t = _exchange(_result(_build(SIDES8, 12), 7), window=1)
    assert [(w["start"], w["end"]) for w in t.windows] == [(s, s + 1) for s in range(7, 12)]




def test_no_shot_gives_no_windows_and_a_shot_does():
    """SPEC 8: first_shot_tick == -1 gives no windows: every count 0, both ratios None, survivors still
    reported, text still a string. Twin: the same trace with first_shot_tick 0 gives windows (a stub
    that always returns an empty table fails the twin)."""
    tr = _build(SIDES8, 30)
    t = _exchange(_result(tr, -1, survivors=(4, 4)))
    assert t.windows == []
    assert (t.n_agree, t.n_disagree, t.n_even, t.n_idle) == (0, 0, 0, 0)
    assert (t.lead_A_windows, t.lead_B_windows) == (0, 0)
    assert t.firing_ratio is None and t.damage_ratio is None
    assert t.survivors == (4, 4)
    assert isinstance(t.text, str)
    assert len(_exchange(_result(tr, 0)).windows) == 3


@pytest.mark.parametrize("bad", [0, -1, -20, 20.0, 2.5, True, False])
def test_window_must_be_a_positive_int(bad):
    """SPEC 8: window must be a positive int: 0, negative, float and bool raise ValueError."""
    with pytest.raises(ValueError):
        _exchange(_result(_build(SIDES8, 30), 5), window=bad)


def test_window_positive_int_is_accepted():
    """SPEC 8 (twin of the ValueError cases): window 1 and window 20 are fine."""
    res = _result(_build(SIDES8, 30), 5)
    assert _exchange(res, window=1).window == 1
    assert _exchange(res, window=20).window == 20


def test_missing_trace_raises_value_error_and_a_trace_does_not():
    """SPEC 8: `exchange` needs `result.trace`: None raises ValueError, even with a shot recorded."""
    res = _result(_build(SIDES8, 30), 5)
    res.trace = None
    with pytest.raises(ValueError):
        _exchange(res)
    res.trace = _build(SIDES8, 30)
    assert _exchange(res).windows


# ---- 2. per-window quantities on the hand-built trace --------------------------------------------

def test_hand_case_firing_is_mean_bit4_units_per_tick():
    """SPEC 8: firing_s = mean over the window's ticks of the count of the side's units with bit4.
    W0: A 3.0, B 1.0 (4 and 6 fire 5 ticks each). W1: A 1.5 (A0 10 ticks, A2 5 ticks), B 1.0.
    W2 (ticks 25..29): nothing fires: 0 and 0."""
    w = _exchange(_hand()).windows
    assert [(x["start"], x["end"]) for x in w] == [(5, 15), (15, 25), (25, 30)]
    assert [x["firing_A"] for x in w] == pytest.approx([3.0, 1.5, 0.0])
    assert [x["firing_B"] for x in w] == pytest.approx([1.0, 1.0, 0.0])


def test_short_last_window_firing_is_a_mean_over_its_own_ticks():
    """SPEC 8: the last window is short; its mean divides by its own length. One A unit fires on ticks
    25..29 only (the 5-tick last window of [25, 30)): firing_A = 1.0, not 0.5."""
    tr = _build(SIDES8, 30, fire=[(0, 25, 30)])
    w = _exchange(_result(tr, 5), window=10).windows
    assert (w[2]["start"], w[2]["end"]) == (25, 30)
    assert w[2]["firing_A"] == pytest.approx(1.0) and w[2]["firing_B"] == pytest.approx(0.0)
    assert w[0]["firing_A"] == pytest.approx(0.0) and w[1]["firing_A"] == pytest.approx(0.0)


def test_hand_case_dealt_is_hp_removed_from_the_other_side():
    """SPEC 8: dealt_A = HP removed from B's units. W0: B4 -50 (hp drops on the first-shot tick 5
    itself), B5 -20, B6 -250 (dies), B7 -30 = 350; dealt_B = A0 -10 = 10. W1: B4 -10 (190 vs 200 at
    the previous window's end) and B7's heal (220 -> 240) counts 0 not -20 = 10; dealt_B = A2 -250
    (dies). W2: 0 and 0. Damage taken earlier is not counted again in a later window."""
    w = _exchange(_hand()).windows
    assert [x["dealt_A"] for x in w] == pytest.approx([350.0, 10.0, 0.0])
    assert [x["dealt_B"] for x in w] == pytest.approx([10.0, 250.0, 0.0])


def test_first_window_reference_is_the_hp_before_the_first_shot_tick():
    """SPEC 8 (the first-window HP reference): a shot at first_shot_tick lands on that tick, so the trace
    already shows the lower HP there. The reference is hp at first_shot_tick - 1 (= the starting HP):
    B4 at 200 from tick 5 = first_shot_tick gives dealt_A 50 in window 0. A reference of hp[5] would
    give 0 (this is _hand W0's B4 term: 350 needs it, 300 would not)."""
    tr = _build(SIDES8, 20, hp_steps=[(4, 5, 200.0)])
    w = _exchange(_result(tr, 5), window=10).windows
    assert w[0]["dealt_A"] == pytest.approx(50.0)
    assert w[1]["dealt_A"] == pytest.approx(0.0)


def test_first_window_reference_at_tick_zero_is_the_starting_hp_from_the_scenario():
    """SPEC 8: when the first shot is on tick 0 there is no tick -1, so the reference is the unit's
    starting HP from the scenario types (raider 250): B4 is 200 from tick 0 -> dealt_A 50. (Chosen
    reading, file docstring: SPEC 8 names the scenario types for exactly this case.)"""
    tr = _build(SIDES8, 12, hp_steps=[(4, 0, 200.0)])
    w = _exchange(_result(tr, 0), window=10).windows
    assert (w[0]["start"], w[0]["end"]) == (0, 10)
    assert w[0]["dealt_A"] == pytest.approx(50.0) and w[0]["dealt_B"] == pytest.approx(0.0)


def test_hand_case_lost_counts_deaths_in_the_window_once():
    """SPEC 8: lost_s = own units alive 1 at the previous tick and 0 at the window's last tick.
    W0: B6 dies at tick 11: lost_B 1, lost_A 0. W1: A2 dies at tick 20: lost_A 1; B6 is dead in both
    boundary ticks of W1 so it is not counted again: lost_B 0. W2: 0 and 0."""
    w = _exchange(_hand()).windows
    assert [x["lost_A"] for x in w] == [0, 1, 0]
    assert [x["lost_B"] for x in w] == [1, 0, 0]


def test_a_death_on_a_windows_first_tick_belongs_to_that_window():
    """SPEC 8: lost counts alive 1 at the PREVIOUS tick and 0 at the window's last tick. A2 dies on
    tick 15, the first tick of window 1 (alive at 14, dead at 15): lost_A is 1 in window 1 and 0 in
    window 0; B6 dies on tick 5, the first-shot tick itself: lost_B is 1 in window 0."""
    tr = _build(SIDES8, 30, hp_steps=[(2, 15, 0.0), (6, 5, 0.0)], dead_from={2: 15, 6: 5})
    w = _exchange(_result(tr, 5), window=10).windows
    assert [x["lost_A"] for x in w] == [0, 1, 0]
    assert [x["lost_B"] for x in w] == [1, 0, 0]


def test_hand_case_shares_and_none_on_zero_denominator():
    """SPEC 8: f_A = firing_A / (firing_A + firing_B), d_A and l_A likewise; None when the denominator
    is 0. W0 f 3/4, d 350/360, l 0/1 = 0.0 (a zero numerator is a share, not None). W1 f 0.6,
    d 10/260, l 1/1 = 1.0. W2: all three None."""
    w = _exchange(_hand()).windows
    assert w[0]["f_A"] == pytest.approx(0.75) and w[0]["d_A"] == pytest.approx(350 / 360)
    assert w[0]["l_A"] == 0.0
    assert w[1]["f_A"] == pytest.approx(0.6) and w[1]["d_A"] == pytest.approx(10 / 260)
    assert w[1]["l_A"] == 1.0
    assert w[2]["f_A"] is None and w[2]["d_A"] is None and w[2]["l_A"] is None


def _one_window(fire_a, fire_b, dealt_a, dealt_b, sides=None):
    """One 10-tick window from tick 0 (first_shot_tick 0, window 10). `fire_a`/`fire_b` are unit-ticks
    with bit4 (filled 10 per unit in turn, so the mean is unit-ticks / 10); `dealt_a` HP removed from
    the first B unit and `dealt_b` from the first A unit at tick 2 (each <= 250)."""
    sides = sides if sides is not None else SIDES8
    a_units = [i for i, s in enumerate(sides) if s == 0]
    b_units = [i for i, s in enumerate(sides) if s == 1]
    fire, steps = [], []
    for units, total in ((a_units, fire_a), (b_units, fire_b)):
        left = total
        for u in units:
            n = min(10, left)
            if n:
                fire.append((u, 0, n))
            left -= n
    if dealt_a:
        steps.append((b_units[0], 2, HP0 - dealt_a))
    if dealt_b:
        steps.append((a_units[0], 2, HP0 - dealt_b))
    return _result(_build(sides, 10, fire=fire, hp_steps=steps), 0)


STATE_CASES = [
    # fire_a, fire_b, dealt_a, dealt_b, state, f_A, d_A
    (30, 10, 80, 20, "agree", 0.75, 0.8),         # A leads both
    (10, 30, 20, 80, "agree", 0.25, 0.2),         # B leads both
    (30, 10, 20, 80, "disagree", 0.75, 0.2),      # firing leader A, damage leader B
    (10, 30, 80, 20, "disagree", 0.25, 0.8),      # firing leader B, damage leader A
    (20, 20, 50, 50, "even", 0.5, 0.5),           # exactly level
    (20, 19, 49, 51, "even", 20 / 39, 0.49),      # both within 0.02 of 0.5, f above and d below
    (30, 20, 55, 45, "agree", 0.6, 0.55),         # f is outside 0.02: not even
    (20, 19, 70, 30, "agree", 20 / 39, 0.7),      # d is outside 0.02: not even
    (0, 0, 50, 50, "idle", None, 0.5),            # nobody fires: f None
    (20, 20, 0, 0, "idle", 0.5, None),            # nothing damaged: d None
    (20, 0, 0, 0, "idle", 1.0, None),             # one-sided firing, no damage
]


@pytest.mark.parametrize("fa,fb,da,db,state,f_a,d_a", STATE_CASES)
def test_window_state(fa, fb, da, db, state, f_a, d_a):
    """SPEC 8 states: agree (firing leader is damage leader), disagree (not), even (both shares within
    0.02 of 0.5, ahead of agree / disagree), idle (f or d None, ahead of everything). Positive and
    negative twins for each; the share values are checked so a state label alone cannot pass."""
    w = _exchange(_one_window(fa, fb, da, db), window=10).windows
    assert len(w) == 1
    assert w[0]["state"] == state
    for key, want in (("f_A", f_a), ("d_A", d_a)):
        if want is None:
            assert w[0][key] is None
        else:
            assert w[0][key] == pytest.approx(want)


@pytest.mark.parametrize("fa,fb,da,db,state,f_a,d_a", [c for c in STATE_CASES if c[5] is not None and c[6] is not None])
def test_swapping_the_sides_swaps_the_shares_and_keeps_the_state(fa, fb, da, db, state, f_a, d_a):
    """SPEC 8: the B shares are 1 - the A shares. The same fight with the side labels swapped (the A
    force now sits in the units labelled side 1) gives f_A' = 1 - f_A, d_A' = 1 - d_A, and the same state."""
    swapped = [1, 1, 1, 1, 0, 0, 0, 0]
    a = _exchange(_one_window(fa, fb, da, db), window=10).windows[0]
    b = _exchange(_one_window(fb, fa, db, da, sides=swapped), window=10).windows[0]
    # in `b` the side-0 force fired fb unit-ticks: the roles are mirrored
    assert b["f_A"] == pytest.approx(1.0 - a["f_A"]) and b["d_A"] == pytest.approx(1.0 - a["d_A"])
    assert b["state"] == a["state"]


def test_summary_counts_add_up_and_lead_windows_use_the_margin():
    """SPEC 8: n_agree + n_disagree + n_even + n_idle == number of windows. lead_A_windows / lead_B_windows
    count windows with f_A above 0.52 / below 0.48. Five 10-tick windows from tick 0:
    W0 A 3 : B 1 (f .75, B4 loses 100 at tick 3 -> d 1.0: agree, lead A); W1 A 1 : B 3 (f .25, A0 loses
    40 at tick 13 -> d 0.0: agree, lead B); W2 2 : 2 (f .5, no damage: idle, no lead); W3 nobody (idle);
    W4 A 2.0 : B 1.9 (f .5128: within 0.02, no lead, no damage: idle).
    firing_ratio = (3 + 1 + 2 + 0 + 2) / (1 + 3 + 2 + 0 + 1.9) = 8 / 7.9; damage_ratio = 100 / 40."""
    fire = [(0, 0, 10), (1, 0, 10), (2, 0, 10), (4, 0, 10),
            (0, 10, 20), (4, 10, 20), (5, 10, 20), (6, 10, 20),
            (0, 20, 30), (1, 20, 30), (4, 20, 30), (5, 20, 30),
            (0, 40, 50), (1, 40, 50), (4, 40, 50), (5, 40, 49)]
    steps = [(4, 3, 150.0), (0, 13, 210.0)]
    t = _exchange(_result(_build(SIDES8, 50, fire=fire, hp_steps=steps), 0), window=10)
    assert [w["state"] for w in t.windows] == ["agree", "agree", "idle", "idle", "idle"]
    assert (t.n_agree, t.n_disagree, t.n_even, t.n_idle) == (2, 0, 0, 3)
    assert (t.lead_A_windows, t.lead_B_windows) == (1, 1)
    assert t.firing_ratio == pytest.approx(8 / 7.9)
    assert t.damage_ratio == pytest.approx(2.5)


def test_hand_case_summary():
    """SPEC 8 on the hand trace: one agree (W0), one disagree (W1), one idle (W2); lead_A 2 (f .75, .6),
    lead_B 0; firing_ratio 4.5 / 2.0 = 2.25; damage_ratio 360 / 260; survivors as given."""
    t = _exchange(_hand())
    assert [w["state"] for w in t.windows] == ["agree", "disagree", "idle"]
    assert (t.n_agree, t.n_disagree, t.n_even, t.n_idle) == (1, 1, 0, 1)
    assert (t.lead_A_windows, t.lead_B_windows) == (2, 0)
    assert t.firing_ratio == pytest.approx(2.25) and t.damage_ratio == pytest.approx(360 / 260)
    assert t.survivors == (3, 3)
    assert t.window == 10


def test_ratios_are_none_on_zero_denominator_and_zero_on_zero_numerator():
    """SPEC 8: firing_ratio / damage_ratio are None when the B sum is 0 (A fires, B never does; A deals
    damage, B none). The twin: A never fires and B does: ratio 0.0, not None."""
    a_only = _result(_build(SIDES8, 20, fire=[(0, 0, 20)], hp_steps=[(4, 3, 200.0)]), 0)
    t = _exchange(a_only, window=10)
    assert t.firing_ratio is None and t.damage_ratio is None
    b_only = _result(_build(SIDES8, 20, fire=[(4, 0, 20)], hp_steps=[(0, 3, 200.0)]), 0)
    t = _exchange(b_only, window=10)
    assert t.firing_ratio == pytest.approx(0.0) and t.damage_ratio == pytest.approx(0.0)


# ---- 4. no leak ---------------------------------------------------------------------------------

def test_exchange_ignores_whole_fight_totals_and_winner():
    """SPEC 8 / README 8: `exchange` never reads firing_ticks, alive_ticks, firing_weight or winner.
    The same trace under a result that favours A in every total, one that favours B, and one carrying
    none of them (an attribute read would raise AttributeError) gives the same windows, ratios,
    counts and text."""
    base = _hand()
    tr = base.trace
    favour_a = _result(tr, 5, survivors=(3, 3), winner=WIN_A, firing_ticks=(900, 10), alive_ticks=(1000, 1000),
                       firing_weight=(900.0, 10.0))
    favour_b = _result(tr, 5, survivors=(3, 3), winner=WIN_B, firing_ticks=(10, 900), alive_ticks=(1000, 1000),
                       firing_weight=(10.0, 900.0))
    ref = _exchange(base)
    for other in (_exchange(favour_a), _exchange(favour_b)):
        assert other.windows == ref.windows
        assert (other.n_agree, other.n_disagree, other.n_even, other.n_idle) == \
            (ref.n_agree, ref.n_disagree, ref.n_even, ref.n_idle)
        assert (other.firing_ratio, other.damage_ratio) == (ref.firing_ratio, ref.damage_ratio)
        assert (other.lead_A_windows, other.lead_B_windows) == (ref.lead_A_windows, ref.lead_B_windows)
        assert other.text == ref.text
    assert ref.windows and ref.firing_ratio is not None


def test_survivors_is_reported_but_changes_nothing_else():
    """SPEC 8: `survivors` (from result.survivors) is reported in the table and in its text and changes
    nothing else: the same trace with survivors (3, 3) and (1, 6) gives the same windows, counts and
    ratios and the same window lines; the text differs (header only) and the attribute follows."""
    tr = _hand().trace
    a = _exchange(_result(tr, 5, survivors=(3, 3)))
    b = _exchange(_result(tr, 5, survivors=(1, 6)))
    assert a.survivors == (3, 3) and b.survivors == (1, 6)
    assert a.windows == b.windows
    assert (a.firing_ratio, a.damage_ratio) == (b.firing_ratio, b.damage_ratio)
    assert (a.n_agree, a.n_disagree, a.n_even, a.n_idle) == (b.n_agree, b.n_disagree, b.n_even, b.n_idle)
    assert a.text != b.text
    n = len(a.windows)
    la, lb = a.text.splitlines(), b.text.splitlines()
    assert len(la) == len(lb) and len(la) > n
    assert la[-n:] == lb[-n:]
    assert la[:-n] != lb[:-n]


# ---- the even-exchange / uneven-outcome case ------------------------------------------------------

def test_even_exchange_is_not_an_even_outcome():
    """README 6.3 ("an even exchange is not an even outcome when the totals differ") / SPEC 8: 10 A
    against 4 B over one 20-tick window. Three units per side fire the whole window (firing_ratio 1.0);
    A loses three units outright (750 HP), B loses one unit outright and 500 spread over its
    survivors (750 HP): damage_ratio 1.0. Survivors are (7, 3). The table reports all three side by
    side: ratios near 1.0, survivors (7, 3), and the loss share 3 / (3 + 1) = 0.75 (A has lost more
    units, the exchange in HP is level)."""
    sides = [0] * 10 + [1] * 4
    fire = [(3, 0, 20), (4, 0, 20), (5, 0, 20), (11, 0, 20), (12, 0, 20), (13, 0, 20)]
    steps = [(0, 4, 0.0), (1, 6, 0.0), (2, 8, 0.0), (10, 5, 0.0), (11, 7, 50.0), (12, 9, 50.0), (13, 11, 150.0)]
    dead = {0: 4, 1: 6, 2: 8, 10: 5}
    tr = _build(sides, 20, fire=fire, hp_steps=steps, dead_from=dead)
    t = _analysis().exchange(_result(tr, 0, survivors=(7, 3)), _counts(10, 4), window=20)
    assert len(t.windows) == 1
    assert t.firing_ratio == pytest.approx(1.0, abs=0.05)
    assert t.damage_ratio == pytest.approx(1.0, abs=0.05)
    assert t.survivors == (7, 3)
    assert t.windows[0]["state"] == "even"
    assert t.windows[0]["lost_A"] == 3 and t.windows[0]["lost_B"] == 1
    assert t.windows[0]["l_A"] == pytest.approx(0.75)
    assert "7" in t.text and "3" in t.text


# ---- 5. real runs ---------------------------------------------------------------------------------

def _real(scn, seed, window=20):
    res = runmod.run(scn, seed=seed, trace=True)
    return res, _analysis().exchange(res, scn, window=window)


def test_x2_blind_side_never_fires_so_every_window_is_one_sided():
    """README pass 1 (X2: B cannot see up, 0 B shots) / SPEC 8: seeds 0..4, window 20: every window after
    the first shot has firing_B == 0; f_A is 1.0 wherever defined (A fires) and at least one window is
    defined (a table of idle windows would pass the rest); firing_ratio is None (B sum 0); no window
    is "disagree" (B deals no damage: d_A is 1.0 or None). A wins every seed (control)."""
    scn = _load("x2_high_ground_blind.toml")
    for seed in range(5):
        res, t = _real(scn, seed)
        assert res.winner == WIN_A
        assert t.windows and t.windows[0]["start"] == res.first_shot_tick
        assert all(w["firing_B"] == 0 for w in t.windows)
        assert all(w["dealt_B"] == 0 for w in t.windows)
        defined = [w for w in t.windows if w["f_A"] is not None]
        assert defined and all(w["f_A"] == 1.0 for w in defined)
        assert t.firing_ratio is None
        assert t.n_disagree == 0
        assert all(w["d_A"] in (1.0, None) for w in t.windows)
        assert t.damage_ratio is None


def test_x4_real_windows_are_consecutive_and_counts_add_up():
    """SPEC 8 on real traces (X4, seeds 0..2, window 20): windows start at first_shot_tick, are
    consecutive, all of length 20 but the last, which ends at the trace length; the four state counts add
    up to the number of windows; every share is in [0, 1] or None; survivors equal the run's."""
    scn = _load("x4_high_ground_both_answer.toml")
    for seed in range(3):
        res, t = _real(scn, seed)
        w = t.windows
        assert w and w[0]["start"] == res.first_shot_tick and w[-1]["end"] == len(res.trace)
        assert all(a["end"] == b["start"] for a, b in zip(w, w[1:]))
        assert all(x["end"] - x["start"] == 20 for x in w[:-1]) and 0 < w[-1]["end"] - w[-1]["start"] <= 20
        assert t.n_agree + t.n_disagree + t.n_even + t.n_idle == len(w)
        assert all(x["state"] in ("agree", "disagree", "even", "idle") for x in w)
        assert all(x[k] is None or 0.0 <= x[k] <= 1.0 for x in w for k in ("f_A", "d_A", "l_A"))
        assert t.survivors == tuple(res.survivors)


def test_x0_mirror_check_exchange_agrees_and_ratio_is_near_one():
    """README 6.3 / SPEC 8: in the mirror (X0, 20 seeds, window 20) both sides field the same force, so
    the firing leader is the damage leader in most windows: mean agree fraction >= 0.7 (measured 0.81 with
    soft, overlapping bodies and 0.76 with hard bodies; a sanity bound, not a design number), and the mean
    firing_ratio is within 0.15 of 1.0 (no positional edge)."""
    r = _analysis().check_exchange(_load("x0_mirror.toml"), range(20), window=20)
    assert r["agree_fraction"] is not None and r["agree_fraction"] >= 0.7
    assert r["firing_ratio"] == pytest.approx(1.0, abs=0.15)


def test_bigger_force_fires_with_more_units():
    """README 6.3 ("the number we care about is the number of units firing") / SPEC 8: 20 against 10
    raiders on flat ground, window 20, seeds 0..9: A wins every seed; the mean over seeds of the firing
    ratio taken over the first three windows is above 1.5 (the bigger force fires with more units)."""
    scn = _counts(20, 10)
    ratios = []
    for seed in range(10):
        res, t = _real(scn, seed, window=20)
        assert res.winner == WIN_A
        first3 = t.windows[:3]
        assert len(first3) == 3
        fb = sum(w["firing_B"] for w in first3)
        assert fb > 0
        ratios.append(sum(w["firing_A"] for w in first3) / fb)
    assert sum(ratios) / len(ratios) > 1.5


# ---- 6. check_exchange ----------------------------------------------------------------------------

KEYS = {"agree_fraction", "firing_ratio", "damage_ratio", "higher_firing_won"}


def test_check_exchange_returns_the_spec_keys_and_runs_with_traces_on():
    """SPEC 8: check_exchange(scn, seeds, window=20, lib="O2") -> dict with the mean agree fraction, the
    mean firing_ratio and damage_ratio, and the fraction of seeds where the side with the higher firing
    ratio won (key names: file docstring). It runs the seeds with traces on (it would fail on a
    trace-less run). The fraction is in [0, 1]; the means are floats here (X0 is two-sided)."""
    r = _analysis().check_exchange(_load("x0_mirror.toml"), 3)
    assert isinstance(r, dict) and KEYS <= set(r)
    for k in ("agree_fraction", "firing_ratio", "damage_ratio", "higher_firing_won"):
        assert isinstance(r[k], float)
    assert 0.0 <= r["agree_fraction"] <= 1.0 and 0.0 <= r["higher_firing_won"] <= 1.0
    assert r["firing_ratio"] > 0 and r["damage_ratio"] > 0


def test_check_exchange_matches_direct_runs_and_default_window_is_20():
    """SPEC 8: check_exchange is `exchange` over the seeds: on X0 seeds 0..5 the means equal a direct
    run(trace=True) + exchange loop (agree fraction n_agree / (n_agree + n_disagree) per seed, then the
    mean; firing_ratio and damage_ratio means; higher_firing_won over decisive seeds with a ratio that
    is not None and not 1), the default window is 20 and `seeds` as an int means seeds 0..N-1."""
    scn = _load("x0_mirror.toml")
    agree, fr, dr, won, counted = [], [], [], 0, 0
    for seed in range(6):
        res, t = _real(scn, seed, window=20)
        if t.n_agree + t.n_disagree:
            agree.append(t.n_agree / (t.n_agree + t.n_disagree))
        if t.firing_ratio is not None:
            fr.append(t.firing_ratio)
        if t.damage_ratio is not None:
            dr.append(t.damage_ratio)
        if t.firing_ratio not in (None, 1.0) and res.winner in (WIN_A, WIN_B):
            counted += 1
            won += (res.winner == WIN_A) == (t.firing_ratio > 1.0)
    r = _analysis().check_exchange(scn, 6)
    assert r["agree_fraction"] == pytest.approx(sum(agree) / len(agree))
    assert r["firing_ratio"] == pytest.approx(sum(fr) / len(fr))
    assert r["damage_ratio"] == pytest.approx(sum(dr) / len(dr))
    assert counted > 0 and r["higher_firing_won"] == pytest.approx(won / counted)
    assert _analysis().check_exchange(scn, range(6), window=20) == r


def test_check_exchange_higher_firing_side_wins_when_the_bigger_force_fires_more():
    """SPEC 8: 20 v 10 raiders, seeds 0..4: A fires with more units and wins every seed, so the higher
    firing-ratio side won in every seed: higher_firing_won == 1.0, firing_ratio > 1 (the twin of the
    X0 case, where the key must be able to read below 1.0 as well)."""
    scn = _counts(20, 10)
    r = _analysis().check_exchange(scn, 5, window=20)
    assert r["higher_firing_won"] == pytest.approx(1.0)
    assert r["firing_ratio"] > 1.0


def test_check_exchange_one_sided_run_has_no_firing_ratio():
    """SPEC 8 (ratio None when its denominator is 0): X2, 3 seeds, B never fires, so no seed has a
    firing_ratio and the mean is None; the agree fraction is still defined (no disagreement: 1.0)."""
    r = _analysis().check_exchange(_load("x2_high_ground_blind.toml"), 3, window=20)
    assert r["firing_ratio"] is None
    assert r["agree_fraction"] == pytest.approx(1.0)


@pytest.mark.parametrize("bad", [0, -5, 2.0, True])
def test_check_exchange_bad_window_raises_value_error(bad):
    """SPEC 8: the window rule of `exchange` holds for check_exchange too."""
    with pytest.raises(ValueError):
        _analysis().check_exchange(_load("x0_mirror.toml"), 1, window=bad)


def test_text_window_lines_are_fixed_width():
    """SPEC 8: `.text` is fixed-width: a header (ratios and survivors), then one line per window, all
    window lines the same width and each showing the window's start tick. Hand-built (3 windows with
    values of different widths) and a real X4 run."""
    for t in (_exchange(_hand()), _real(_load("x4_high_ground_both_answer.toml"), 0)[1]):
        lines = t.text.splitlines()
        n = len(t.windows)
        assert n >= 3 and len(lines) > n
        body = lines[-n:]
        assert len({len(x) for x in body}) == 1
        for line, w in zip(body, t.windows):
            assert re.search(r"(?<!\d)%d(?!\d)" % w["start"], line)


# ---- 7. the exchange CLI ------------------------------------------------------------------------------

def _cli(*args):
    return subprocess.run([sys.executable, "-m", "layerlab", *args], cwd=LAB, capture_output=True, text=True)


def test_cli_exchange_prints_the_ratios_and_the_windows_of_seed_zero():
    """SPEC 8: `exchange scenarios/x0_mirror.toml --seeds 3 --window 20` exits 0 and prints the
    check_exchange numbers (ratios) and the windows of seed 0: every window's start tick shows up."""
    r = _cli("exchange", "scenarios/x0_mirror.toml", "--seeds", "3", "--window", "20")
    assert r.returncode == 0, r.stderr
    out = r.stdout.lower()
    assert "firing" in out and "damage" in out
    _, t = _real(_load("x0_mirror.toml"), 0, window=20)
    for w in t.windows:
        assert re.search(r"(?<!\d)%d(?!\d)" % w["start"], r.stdout)


def test_cli_exchange_accepts_set_overrides():
    """SPEC 8: `exchange ... --set path=value` like the other commands: 20 v 10 raiders runs and exits 0."""
    r = _cli("exchange", "scenarios/r0_raiders_10v5.toml", "--seeds", "2", "--window", "20",
             "--set", "groups[0].count=20", "--set", "groups[1].count=10")
    assert r.returncode == 0, r.stderr
    assert "firing" in r.stdout.lower()


def test_cli_exchange_window_zero_is_an_error_about_the_window():
    """SPEC 8: `--window 0` is rejected (exit nonzero) with a message naming the window, and prints no
    traceback. (Not satisfied by an unknown command: argparse would say "invalid choice".)"""
    r = _cli("exchange", "scenarios/x0_mirror.toml", "--seeds", "1", "--window", "0")
    assert r.returncode != 0
    assert "invalid choice" not in r.stderr
    assert "window" in r.stderr.lower()
    assert "Traceback" not in r.stderr


def test_cli_exchange_bad_scenario_path_is_an_error():
    """SPEC 8: a scenario path that does not exist exits nonzero with an error naming the file, no
    traceback, and prints no ratios on stdout. (Not satisfied by an unknown command.)"""
    r = _cli("exchange", "scenarios/no_such_scenario.toml", "--seeds", "1", "--window", "20")
    assert r.returncode != 0
    assert "invalid choice" not in r.stderr
    assert "no_such_scenario" in r.stderr
    assert "Traceback" not in r.stderr
    assert r.stdout.strip() == ""
