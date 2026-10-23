# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S::first bullet (per-tick trace)
# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase B::first paragraph (position trace, wave A1)
"""The per-tick trace of fight(), on a FakeEngine (no compiler, no library).

Contract these tests fix (the implementation under scripts/skilllab comes later):
  Setup.trace: bool = False       opt-in; the default records nothing and reads nothing extra from the library.
  FightResult.trace: list | None  None when Setup.trace is False; else one tuple per unit per recorded tick,
                                  (tick, unit, x, y, target, facing, alive), the library's own unit ids,
                                  target = the unit id aimed at (0 none), facing in radians, alive a bool.
  Recorded ticks are 0 (after orders, before the first step) through result.ticks, every tick; sample_every
  (the firing samples) does not thin it. Entries are ordered by tick, then by unit id (side and group do not
  matter, and a swapped spawn order does not change the rule).
  Units that die stay in the trace for every remaining tick: alive False from the first tick the fight's own
  hp reading is <= 0 (the same rule the fight loop uses), x, y and facing frozen at the last live reading,
  target 0.
"""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes_trace import TraceFakeEngine  # noqa: E402
from scripts.skilllab.contract import FightResult, Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from scripts.skilllab.rows import fight_row  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=2, order="attack_move"):
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=-300.0 if side == 0 else 300.0,
                 y=0.0, facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=None,
                 params={"spacing": 30.0})


def S(trace=True, max_ticks=12, sample_every=5, counts=(2, 2)):
    return Setup(groups=(G(0, counts[0]), G(1, counts[1])), unit_types={}, max_ticks=max_ticks, sample_every=sample_every, trace=trace)


def run(setup, seed=0, swap=False, **fake_kw):
    fake = TraceFakeEngine(**fake_kw)
    return fight(setup, seed, swap, engine=fake), fake


def by_tick(trace):
    out = {}
    for e in trace:
        out.setdefault(e[0], []).append(e)
    return out


# ---- shape -------------------------------------------------------------------------------------------------

def test_trace_is_off_by_default_and_reads_nothing_extra():
    """Phase S: opt-in. Default Setup.trace is False, result.trace is None, and the library is never asked
    for a target or a facing."""
    assert Setup(groups=(G(0), G(1)), unit_types={}).trace is False
    result, fake = run(S(trace=False))
    assert result.trace is None
    assert not fake.calls_named("unit_target") and not fake.calls_named("unit_facing")


def test_constructors_without_a_trace_leave_it_none():
    """Backward compatible: a FightResult built with the contract fields only (no trace) has trace None.
    LAB-REV2-L2: the contract adds firing_window, weighted_unit_seconds, weighted_window, predicted_count, predicted_type and
    agreement, so they are named here; the old pin `names.index("trace") == 10` (TD-LAB-trace-index) is dropped, since field
    order is not part of the 2026-10-14 contract."""
    r = FightResult(outcome="cap", margin=0.0, strength_left=(1.0, 1.0), survivors=(1, 1), heads=(1, 1), ticks=1,
                    first_contact_tick=-1, firing=[], firing_unit_seconds=(0.0, 0.0), firing_window=(0.0, 0.0),
                    weighted_unit_seconds=(0.0, 0.0), weighted_window=(0.0, 0.0), predicted_count="tie",
                    predicted_type="tie", agreement="n/a")
    assert r.trace is None and r.winner is None
    assert "trace" in [f.name for f in dataclasses.fields(FightResult)]


def test_one_entry_per_unit_per_recorded_tick():
    result, fake = run(S(trace=True, max_ticks=12, sample_every=5))
    assert result.ticks == 12
    ids = sorted(fake.spawn_order)
    assert len(ids) == 4
    assert len(result.trace) == (result.ticks + 1) * len(ids)
    ticks = by_tick(result.trace)
    assert sorted(ticks) == list(range(result.ticks + 1))
    assert all(sorted(e[1] for e in v) == ids for v in ticks.values())
    assert all(len(e) == 7 for e in result.trace)


def test_sample_every_does_not_thin_the_trace():
    a, _ = run(S(sample_every=1))
    b, _ = run(S(sample_every=7))
    assert a.trace == b.trace


@pytest.mark.parametrize("swap", [False, True])
def test_entries_are_ordered_by_tick_then_unit_id(swap):
    result, fake = run(S(counts=(3, 2)), swap=swap)
    keys = [(e[0], e[1]) for e in result.trace]
    assert keys == sorted(keys)
    assert len(set(keys)) == len(keys)


def test_trace_leaves_the_rest_of_the_result_and_the_engine_calls_alone():
    """Recording is read-only: same row, same firing series, same mutating call sequence as with trace off."""
    on, fake_on = run(S(trace=True))
    off, fake_off = run(S(trace=False))
    assert fight_row(on, play="x") == fight_row(off, play="x")
    assert on.firing == off.firing and on.ticks == off.ticks
    assert fake_on.mutating_calls() == fake_off.mutating_calls()


# ---- values ------------------------------------------------------------------------------------------------

def test_values_are_read_from_the_library_after_each_step():
    """tick 0 is the spawn state; tick t (>= 1) is the state after t steps. Position, target and facing each
    come from the engine (position, unit_target, unit_facing)."""
    def script(k, fake):    # k = steps taken before this one, so the state it writes shows at tick k + 1
        for u in fake.spawn_order:
            fake.set_pos(u, 100.0 * u + k, -5.0 * u + 0.5 * k)
            fake.set_target(u, (u + k) % 4)
            fake.set_facing(u, 0.25 * k + u)

    result, fake = run(S(), script=script)
    spawn = {u: (x, y) for (u, _t, _f, x, y, _l) in fake.spawn_log()}
    ticks = by_tick(result.trace)
    for (_t, u, x, y, target, facing, alive) in ticks[0]:
        assert (x, y) == spawn[u] and target == 0 and facing == 0.0 and alive is True
    for t in range(1, result.ticks + 1):
        k = t - 1
        for (tick, u, x, y, target, facing, alive) in ticks[t]:
            assert (tick, x, y, target, facing, alive) == (
                t, 100.0 * u + k, -5.0 * u + 0.5 * k, (u + k) % 4, 0.25 * k + u, True)


# ---- units that die ----------------------------------------------------------------------------------------

def test_dead_units_stay_in_the_trace_frozen_with_alive_false():
    """Unit 2 is killed during step 3, so its hp reads 0 at tick 4. From tick 4 on: alive False, x, y and facing
    frozen at the tick-3 reading, target 0 (the script keeps moving and aiming it to prove the freeze)."""
    victim = {}

    def script(k, fake):
        u2 = fake.spawn_order[1]
        victim["id"] = u2
        for u in fake.spawn_order:
            fake.set_pos(u, 10.0 * u + k, 0.0)
            fake.set_facing(u, 0.1 * k)
            fake.set_target(u, 3)
        if k == 3:
            fake.set_hp(u2, 0)

    result, fake = run(S(max_ticks=10), script=script)
    assert result.ticks == 10
    assert len(result.trace) == 11 * 4
    mine = [e for e in result.trace if e[1] == victim["id"]]
    assert [e[0] for e in mine] == list(range(11))
    assert [e[6] for e in mine] == [True] * 4 + [False] * 7
    live = mine[3]
    assert live[6] is True and live[4] == 3
    for e in mine[4:]:
        assert (e[2], e[3], e[5]) == (live[2], live[3], live[5])
        assert e[4] == 0
    others = [e for e in result.trace if e[1] != victim["id"]]
    assert all(e[6] is True for e in others)


def test_all_dead_on_one_side_ends_the_fight_and_every_unit_is_still_in_the_final_tick():
    def script(k, fake):
        if k == 2:
            for u in fake.units_of(1):
                fake.set_hp(u, 0)

    result, fake = run(S(max_ticks=50), script=script)
    assert result.outcome == "side0" and result.ticks == 3
    last = by_tick(result.trace)[3]
    assert len(last) == 4
    assert {e[1] for e in last if not e[6]} == set(fake.units_of(1))


def test_a_dead_unit_never_comes_back():
    def script(k, fake):
        u = fake.spawn_order[0]
        fake.set_hp(u, 0 if k == 1 else 50.0)       # the script revives it; the fight loop does not

    result, fake = run(S(max_ticks=8), script=script)
    flags = [e[6] for e in result.trace if e[1] == fake.spawn_order[0]]
    assert flags == [True, True, False, False, False, False, False, False, False]


# ---- determinism -------------------------------------------------------------------------------------------

def test_same_setup_and_seed_give_byte_identical_traces():
    def script(k, fake):
        for u in fake.spawn_order:
            fake.set_pos(u, fake.units[u]["x"] + 0.1, fake.units[u]["y"])

    a, _ = run(S(), seed=4, script=script)
    b, _ = run(S(), seed=4, script=script)
    assert len(a.trace) > 0
    assert repr(a.trace).encode() == repr(b.trace).encode()


def test_determinism_positive_control_other_seeds_and_swap_differ():
    """The byte comparison can see a difference: the replicate shifts move the spawn positions with the seed,
    and swap changes which side owns which ids."""
    a, _ = run(S(), seed=4)
    assert repr(a.trace) != repr(run(S(), seed=5)[0].trace)
    assert repr(a.trace) != repr(run(S(), seed=4, swap=True)[0].trace)
