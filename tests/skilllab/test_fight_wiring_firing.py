# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Contract::Lab data contract (FightResult, Setup) + L1/L2 seam
"""How fight.fight wires the firing seam, on a fake engine. OWNED BY L2 (LAB-REV2-L2): fight.py and contract.py are its
files, so every case here is red until L2 lands; these tests are not red for L1's reasons, and L1's builder is not asked
to satisfy them. They replace the fight-level halves of the retired test_firing_weighted.py (Setup.weighted flag,
weighted series) and test_states.py (Setup.states opt-in, order_ends).

Disposition of the old halves, with the rev 2 contract:
  - `Setup.weighted` and `FightResult.weighted` are gone: the weighted count is always taken, and
    `weighted_unit_seconds` / `weighted_window` are always populated (contract).
  - `Setup.states` stays an opt-in; `FightResult.states` is [(tick, unit, code)] with the code against the target of
    record (-1 when none), no string states; `FightResult.order_ends` is gone (the order-end tracking died with mopup).
  - Not carried over, because the contract does not fix them: the `weighted_unit_seconds_0/_1` CSV column text (rows.py
    is L2's and its own tests rewrite it) and the window edge (whether the sample at first_contact_tick is inside the
    DRAFT-opening-window-ticks window): both are only bounded here.

The fake is test_firing.CountFake: Vanguard range 100, same-layer reach, full sight, the category multiplier mult(a, b).
Units: side 0 gets ids 1.., then side 1 (swap False).
"""
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pytest  # noqa: E402
import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from scripts.skilllab.contract import TICKS_PER_SECOND, FightResult, Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from test_firing import CountFake, mult  # noqa: E402

SAMPLES = (0, 5, 10)
SETUP_FIELDS = {f.name for f in dataclasses.fields(Setup)}


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    """Units 7 wu apart in a row from the group's x: side 0 at -30, -23; side 1 at 30, 37 (all within range 100)."""
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]
    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count, x):
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=x, y=0.0,
                 facing_deg=0.0, layer=0, order="attack_move", params={"spacing": 7.0})


def S(counts=(2, 1), **kw):
    kw = dict(groups=(G(0, counts[0], -30.0), G(1, counts[1], 30.0)), unit_types={}, max_ticks=10, sample_every=5, **kw)
    if "point" in SETUP_FIELDS:        # the shared attack-move point (L2); the value decides nothing on a fake
        kw["point"] = (0.0, 0.0)
    return Setup(**kw)


def run(setup, **fake_kw):
    fake = CountFake(**fake_kw)
    return fight(setup, 0, False, engine=fake), fake


# ---------------------------------------------------------------- no weighted flag, no order_ends

def test_setup_has_no_weighted_flag_and_the_result_has_no_weighted_series_or_order_ends():
    names = {f.name for f in dataclasses.fields(FightResult)}
    assert "weighted" not in SETUP_FIELDS and "weighted" not in names and "order_ends" not in names


# ---------------------------------------------------------------- weighted_unit_seconds always populated

def test_weighted_unit_seconds_is_populated_by_a_default_fight_and_follows_the_type_weight():
    """No flag set: 2 side-0 Vanguards able at each of the three samples, 1 side-1. Weight mult(1, 1) per able unit,
    summed as unit-seconds like firing_unit_seconds (sum over samples x sample_every / TICKS_PER_SECOND)."""
    r, fake = run(S())
    m = mult(1, 1)
    assert r.firing == [(t, 2, 1) for t in SAMPLES]
    assert r.firing_unit_seconds == pytest.approx((2 * 3 * 5 / TICKS_PER_SECOND, 1 * 3 * 5 / TICKS_PER_SECOND))
    assert r.weighted_unit_seconds == pytest.approx((m * 2 * 3 * 5 / TICKS_PER_SECOND, m * 1 * 3 * 5 / TICKS_PER_SECOND))
    assert all(type(v) is float for v in r.weighted_unit_seconds)
    assert fake.calls_named("category_multiplier")


def test_weighted_unit_seconds_counts_only_the_code_zero_units():
    """A blocked shooter (code 5) adds nothing: unit 1 cannot shoot either enemy, so side 0 weighs one unit, not two."""
    r, _ = run(S(), can_shoot_fn=lambda f, a, b: a != 1)
    assert r.firing[0] == (0, 1, 1)
    assert r.weighted_unit_seconds == pytest.approx((mult(1, 1) * 3 * 5 / TICKS_PER_SECOND, mult(1, 1) * 3 * 5 / TICKS_PER_SECOND))


def test_weighted_window_is_a_pair_bounded_by_the_whole_fight():
    """The window total never exceeds the whole-fight total (edge of the window not pinned: see the module docstring)."""
    r, _ = run(S())
    assert len(r.weighted_window) == 2 and all(type(v) is float for v in r.weighted_window)
    assert all(0.0 <= win <= whole + 1e-12 for win, whole in zip(r.weighted_window, r.weighted_unit_seconds))


def test_the_weighted_seconds_are_deterministic():
    assert run(S())[0].weighted_unit_seconds == run(S())[0].weighted_unit_seconds


# ---------------------------------------------------------------- Setup.states opt-in, rows are (tick, unit, code)

def test_states_default_is_off_and_gives_no_rows():
    assert Setup.__dataclass_fields__["states"].default is False
    r, _ = run(S())
    assert not r.states


def test_states_on_gives_tick_unit_code_int_rows_ordered_by_tick_then_unit_with_every_sample_present():
    r, fake = run(S(states=True))
    assert all(isinstance(row, tuple) and len(row) == 3 and all(type(v) is int for v in row) for row in r.states)
    assert [row[:2] for row in r.states] == sorted(row[:2] for row in r.states)
    assert {t for t, _, _ in r.states} >= set(SAMPLES) and r.states[0][0] == 0
    assert [(t, u, c) for t, u, c in r.states if t == 0] == [(0, 1, 0), (0, 2, 0), (0, 3, 0)]
    assert sorted({u for _, u, _ in r.states}) == sorted(fake.spawn_order)


def test_the_state_code_is_the_first_failing_reason_against_the_target_of_record():
    """Unit 1 is blocked against both enemies (5); unit 2 and the enemy 3 can engage (0)."""
    r, _ = run(S(states=True), can_shoot_fn=lambda f, a, b: a != 1)
    assert {(u, c) for t, u, c in r.states if t == 0} == {(1, 5), (2, 0), (3, 0)}


def test_dead_units_are_omitted_from_the_states_after_they_die():
    """Unit 4 (side 1 of 2) reads hp 0 from step 2: present at tick 0, absent from the sample at tick 5 on; the other
    side-1 unit keeps its rows. (The -1 code, no living hostile, ends a fight by elimination and is pinned on the
    count itself in test_firing.py.)"""
    r, _ = run(S(counts=(2, 2), states=True), script=lambda step, f: f.set_hp(4, 0) if step == 2 else None)
    assert 4 in {u for t, u, _ in r.states if t == 0}
    assert all(u != 4 for t, u, _ in r.states if t >= 5)
    assert {3} <= {u for t, u, _ in r.states if t == 10}


def test_the_zero_codes_equal_the_firing_series_at_every_sample():
    """The zero codes are the count: with a mixed field (one blocked shooter, an enemy beyond range) states and the
    series agree sample by sample."""
    r, _ = run(S(counts=(2, 2), states=True), can_shoot_fn=lambda f, a, b: a != 1)
    for tick, able0, able1 in r.firing:
        rows = [(u, c) for t, u, c in r.states if t == tick]
        assert (sum(1 for u, c in rows if u <= 2 and c == 0), sum(1 for u, c in rows if u > 2 and c == 0)) == (able0, able1)
    assert any(a0 + a1 > 0 for _, a0, a1 in r.firing)


def test_states_do_not_change_any_other_field():
    plain, _ = run(S())
    with_states, _ = run(S(states=True))
    for f in dataclasses.fields(FightResult):
        if f.name not in ("states", "order_ends"):      # order_ends is gone after L2: nothing to compare
            assert getattr(plain, f.name) == getattr(with_states, f.name), f.name
