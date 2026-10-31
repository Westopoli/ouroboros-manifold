# spec: docs/stories/H-024.md::Interfaces (fixed)
# spec: docs/stories/H-024.md::Tests
"""H-024 round 1: the nine-field trace row, the row validator and the snapshot sampler.

Contract these tests fix (docs/stories/H-024.md, "Interfaces (fixed)"):
  Trace row   (tick, unit, x, y, target, facing, alive, layer, unit_type); layer and unit_type are appended after
              alive and read in fight.py record() through engine.unit_layer(w, u) and engine.unit_type(w, u).
  Validator   scripts/skilllab/trace_rows.py: validate_row(row) and validate_trace(rows) -> int.
  Sampler     scripts/skilllab/snapshots.py: first_contact_tick(rows, side_a, side_b) and sample_ticks(...).
The qa_state() inventory is round 2 and is not tested here.

The new modules are imported inside the tests (not at module level), so a missing module reds only its own tests
and the controls stay green. The unit_type getter is added to the fake engine here, because fakes_trace.py has none.
"""
import dataclasses
import importlib
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
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402



@pytest.fixture(autouse=True)
def fake_seam(request):
    """fight() on a fake engine reads the firing counts through the L1/L2 seam (fakes.Seam); the two tests that take
    the `library` fixture run the production firing code instead."""
    if "library" not in request.fixturenames:
        request.getfixturevalue("seam")


def trace_rows():
    return importlib.import_module("scripts.skilllab.trace_rows")


def snapshots():
    return importlib.import_module("scripts.skilllab.snapshots")


class LayerTypeFakeEngine(TraceFakeEngine):
    """TraceFakeEngine plus unit_type(w, u) -> int (the stand-in for om_unit_get_unit_type)."""

    def unit_type(self, w, u):
        self.calls.append(("unit_type", w, u))
        return self.units[u]["type"]


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, unit, count=2):
    return Group(side=side, unit=unit, count=count, formation="line", x=-300.0 if side == 0 else 300.0,
                 y=0.0, facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None,
                 params={"spacing": 30.0})


def S(trace=True, max_ticks=10):
    # side 0 Vanguard (fake type id 2), side 1 Raider (fake type id 0): two different unit types
    return Setup(groups=(G(0, "Vanguard"), G(1, "Raider")), unit_types={}, max_ticks=max_ticks, sample_every=5,
                 trace=trace)


def run(setup, seed=0, **fake_kw):
    fake = LayerTypeFakeEngine(**fake_kw)
    return fight(setup, seed, False, engine=fake), fake


def row(tick=3, unit=7, x=1.5, y=-2.0, target=0, facing=0.25, alive=True, layer=0, unit_type=2):
    return (tick, unit, x, y, target, facing, alive, layer, unit_type)


# ---- positive controls: green today, and still green once the nine fields land ---------------------------------

def test_control_the_first_seven_fields_read_as_the_existing_row():
    """H-024 control: "Before this story its row was `(tick, unit, x, y, target, facing, alive)`". The first seven
    fields of every trace row decode that way today and after the story."""
    result, fake = run(S())
    assert result.trace and result.ticks == 10
    ids = sorted(fake.spawn_order)
    assert [(e[0], e[1]) for e in result.trace] == [(t, u) for t in range(result.ticks + 1) for u in ids]
    for e in result.trace:
        t, u, x, y, target, facing, alive = e[:7]
        assert isinstance(x, float) and isinstance(y, float) and isinstance(facing, float)
        assert isinstance(alive, bool) and isinstance(target, int)


def test_control_dead_rows_carry_target_zero_and_alive_false():
    """H-024 control for the sampler premise: "dead rows carry `target` 0" (fight.py record() writes 0 for dead
    rows). Unit 2 dies in step 3 while still aimed at unit 3; its rows from tick 4 read alive False and target 0."""
    def script(k, fake):
        for u in fake.spawn_order:
            fake.set_target(u, 3)
        if k == 3:
            fake.set_hp(fake.spawn_order[1], 0)

    result, fake = run(S(), script=script)
    victim = fake.spawn_order[1]
    mine = [e for e in result.trace if e[1] == victim]
    assert [e[6] for e in mine] == [True] * 4 + [False] * 7
    assert mine[3][4] == 3
    assert all(e[4] == 0 for e in mine[4:])


# ---- trace: record() emits nine fields -------------------------------------------------------------------------

def test_trace_rows_have_nine_fields():
    """H-024: "Trace row: `(tick, unit, x, y, target, facing, alive, layer, unit_type)`, nine fields." """
    result, _ = run(S())
    assert result.trace
    assert {len(e) for e in result.trace} == {9}


def test_trace_layer_and_unit_type_come_from_the_engine_getters():
    """H-024: "`layer` and `unit_type` are appended after `alive` and read in `fight.py` `record()` through
    `engine.unit_layer(w, u)` and `engine.unit_type(w, u)`." The script moves every unit between layers each step,
    so a layer frozen at spawn is caught; tick 0 is read before the first step (spawn layer 0)."""
    seen = {}

    def script(k, fake):
        for u in fake.spawn_order:
            fake.units[u]["layer"] = (u + k) % 3
            seen[(k + 1, u)] = (u + k) % 3

    result, fake = run(S(), script=script)
    types = {u: fake.units[u]["type"] for u in fake.spawn_order}
    assert set(types.values()) == {0, 2}
    for e in result.trace:
        tick, unit = e[0], e[1]
        assert e[7] == (0 if tick == 0 else seen[(tick, unit)]), "layer of unit %d at tick %d" % (unit, tick)
        assert e[8] == types[unit], "unit_type of unit %d at tick %d" % (unit, tick)
    assert len({e[7] for e in result.trace}) == 3, "layers never varied, the control is vacuous"
    assert fake.calls_named("unit_layer") and fake.calls_named("unit_type")


def test_a_dead_unit_keeps_its_last_layer_and_type():
    """H-024: "A dead unit keeps its last layer and type, like its position." Unit 2 dies in step 3 (hp 0 at tick 4);
    afterwards the script keeps changing its layer and type, and the dead rows still show the tick-3 values."""
    def script(k, fake):
        u2 = fake.spawn_order[1]
        if k < 3:
            fake.units[u2]["layer"] = k + 1
        else:
            fake.units[u2]["layer"] = 90 + k
            fake.units[u2]["type"] = 80 + k
        if k == 3:
            fake.set_hp(u2, 0)

    result, fake = run(S(), script=script)
    mine = [e for e in result.trace if e[1] == fake.spawn_order[1]]
    assert [e[6] for e in mine] == [True] * 4 + [False] * 7
    live = mine[3]
    assert len(live) == 9 and live[7] == 3
    for e in mine[4:]:
        assert (e[7], e[8]) == (live[7], live[8])


def test_trace_off_reads_no_layer_or_type():
    """H-024: the lab records the nine-field row only "when `Setup.trace` is on"; off, the result trace is None and
    the unit_type getter is never called."""
    result, fake = run(S(trace=False))
    assert result.trace is None
    assert not fake.calls_named("unit_type")


def test_the_lab_validates_the_trace_once_per_fight_when_trace_is_on(monkeypatch):
    """H-024: "The lab calls `validate_trace` once per fight when `Setup.trace` is on." The call receives the
    fight's trace; it is silent when the trace is off."""
    mod = trace_rows()
    calls = []
    real = mod.validate_trace

    def counting(rows):
        calls.append(list(rows))
        return real(rows)

    monkeypatch.setattr(mod, "validate_trace", counting)
    monkeypatch.setattr(fight_mod, "validate_trace", counting, raising=False)
    result, _ = run(S())
    assert len(calls) == 1 and calls[0] == result.trace
    calls.clear()
    run(S(trace=False))
    assert calls == []


# ---- validator -------------------------------------------------------------------------------------------------

def test_validate_row_accepts_a_nine_field_row_and_returns_none():
    """H-024: "`validate_row(row: tuple) -> None`". Ints are fine for x, y and facing; 0/1 for alive."""
    v = trace_rows().validate_row
    assert v(row()) is None
    assert v(row(x=4, y=-3, facing=1, alive=False)) is None
    assert v(row(alive=0)) is None and v(row(alive=1)) is None


@pytest.mark.parametrize("n", [0, 7, 8, 10])
def test_validate_row_wrong_length_raises_with_the_count(n):
    """H-024: "raises `ValueError("trace row needs 9 fields, got <n>")` on any other length". n=7 is the old row,
    the positive control: a row missing layer and unit_type fails."""
    v = trace_rows().validate_row
    with pytest.raises(ValueError) as err:
        v(row()[:n] if n <= 9 else row() + (0,) * (n - 9))
    assert str(err.value) == "trace row needs 9 fields, got %d" % n


def test_validate_row_a_seven_field_row_missing_layer_and_type_fails():
    """H-024: "Positive controls: a 7-field row raises". The old row, as the trace gave it before the story."""
    v = trace_rows().validate_row
    with pytest.raises(ValueError, match=r"^trace row needs 9 fields, got 7$"):
        v((3, 7, 1.5, -2.0, 0, 0.25, True))


@pytest.mark.parametrize("name,value", [
    ("tick", 3.5), ("tick", None),
    ("unit", 7.5), ("unit", None),
    ("target", 0.5), ("target", None),
    ("layer", 1.5), ("layer", None),
    ("unit_type", 2.5), ("unit_type", None),
    ("x", None), ("y", None), ("facing", None),
    ("alive", 2), ("alive", None), ("alive", 0.5),
])
def test_validate_row_bad_field_raises_with_name_and_value(name, value):
    """H-024: "`ValueError("trace row field <name> bad: <value>")` when tick, unit, target, layer or unit_type is not
    an int, x, y or facing is not a float or int, or alive is not a bool or 0/1." """
    v = trace_rows().validate_row
    with pytest.raises(ValueError) as err:
        v(row(**{name: value}))
    assert str(err.value) == "trace row field %s bad: %s" % (name, value)


def test_validate_row_checks_the_length_before_the_fields():
    """H-024: "raises ... on any other length": a short row with a bad field still reports the length."""
    v = trace_rows().validate_row
    with pytest.raises(ValueError, match=r"^trace row needs 9 fields, got 7$"):
        v((3.5, 7, 1.5, -2.0, 0, 0.25, True))


def test_validate_trace_returns_the_row_count():
    """H-024: "`validate_trace(rows: list) -> int` validates each row and returns the row count." """
    vt = trace_rows().validate_trace
    assert vt([]) == 0
    assert vt([row(tick=t, unit=u) for t in range(3) for u in (1, 2)]) == 6


def test_validate_trace_raises_on_a_bad_row_anywhere_in_the_list():
    """H-024: "`validate_trace` validates each row": the first row is fine, the last is the old seven-field row."""
    vt = trace_rows().validate_trace
    with pytest.raises(ValueError, match=r"^trace row needs 9 fields, got 7$"):
        vt([row(), row(tick=4), (5, 7, 1.5, -2.0, 0, 0.25, True)])
    with pytest.raises(ValueError) as err:
        vt([row(), row(tick=4), row(tick=5, layer=1.5)])
    assert str(err.value) == "trace row field layer bad: 1.5"


def test_a_real_fight_trace_passes_the_validator():
    """H-024: the rows `fight.py` records are the rows `validate_trace` accepts (count = rows)."""
    result, _ = run(S())
    assert trace_rows().validate_trace(result.trace) == len(result.trace) == 11 * 4


# ---- sampler: first_contact_tick -------------------------------------------------------------------------------

A, B = {1, 2}, {3, 4}


def test_first_contact_is_the_first_tick_an_alive_unit_targets_the_other_side():
    """H-024: "the first tick at which any row with `alive` true has a `target` that is a member of the other side's
    id set"."""
    fc = snapshots().first_contact_tick
    rows = [row(tick=t, unit=u, target=(3 if (t, u) == (5, 1) else 0)) for t in range(8) for u in (1, 2, 3, 4)]
    assert fc(rows, A, B) == 5


def test_first_contact_works_for_a_side_b_unit_targeting_side_a():
    """H-024: "(a side A unit targeting a side B id, or the reverse)"."""
    fc = snapshots().first_contact_tick
    rows = [row(tick=t, unit=u, target=(2 if (t, u) == (4, 3) else 0)) for t in range(8) for u in (1, 2, 3, 4)]
    rows += [row(tick=6, unit=1, target=4)]
    assert fc(rows, A, B) == 4
    assert fc(rows, B, A) == 4


def test_first_contact_ignores_targets_on_the_own_side_and_zero():
    """H-024: contact is a target "that is a member of the other side's id set"; a friendly id or 0 is not."""
    fc = snapshots().first_contact_tick
    rows = [row(tick=t, unit=1, target=2) for t in range(5)] + [row(tick=t, unit=3, target=4) for t in range(5)]
    rows += [row(tick=t, unit=2, target=0) for t in range(5)]
    assert fc(rows, A, B) is None


def test_first_contact_skips_dead_rows():
    """H-024: "dead rows carry `target` 0 and are skipped". A dead row that names an enemy at tick 2 does not count;
    the alive contact at tick 9 does."""
    fc = snapshots().first_contact_tick
    rows = [row(tick=2, unit=1, target=3, alive=False), row(tick=3, unit=2, target=0, alive=False),
            row(tick=9, unit=2, target=4, alive=True)]
    assert fc(rows, A, B) == 9
    assert fc(rows[:2], A, B) is None


def test_first_contact_is_the_smallest_tick_whatever_the_row_order():
    """H-024: "the first tick at which" contact happens."""
    fc = snapshots().first_contact_tick
    rows = [row(tick=9, unit=1, target=3), row(tick=4, unit=2, target=4), row(tick=6, unit=3, target=1)]
    assert fc(rows, A, B) == 4


def test_first_contact_is_none_when_nothing_is_ever_targeted():
    """H-024: "None when it never happens."; empty trace included."""
    fc = snapshots().first_contact_tick
    assert fc([], A, B) is None
    assert fc([row(tick=t, unit=u) for t in range(4) for u in (1, 2, 3, 4)], A, B) is None


def test_first_contact_on_a_recorded_fight_trace():
    """H-024: the sampler reads the rows `fight.py` records. Side 0 unit 1 starts aiming at side 1 unit 3 in step 4,
    so the trace shows it from tick 5; every unit aims at its own side (or nothing) before that."""
    def script(k, fake):
        if k == 4:
            fake.set_target(fake.spawn_order[0], fake.units_of(1)[0])

    result, fake = run(S(), script=script)
    side_a, side_b = set(fake.units_of(0)), set(fake.units_of(1))
    assert snapshots().first_contact_tick(result.trace, side_a, side_b) == 5


# ---- sampler: sample_ticks -------------------------------------------------------------------------------------

def even_ticks(first, last, n_even=12):
    """The story's formula, written out: round(first + k * (last - first) / (n_even - 1)) for k in 0..n_even-1."""
    if n_even == 1:
        return [first]
    return [round(first + k * (last - first) / (n_even - 1)) for k in range(n_even)]


def test_sample_ticks_without_contact_gives_exactly_twelve_even_ticks():
    """H-024: "a trace where no alive row ever targets the other side gives None and exactly n_even ticks". The
    default n_even is 12; the contact is what first_contact_tick returns for a trace with no targets."""
    contact = snapshots().first_contact_tick([row(tick=t, unit=u) for t in range(4) for u in (1, 3)], A, B)
    assert contact is None
    out = snapshots().sample_ticks(0, 110, contact)
    assert out == [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
    assert len(snapshots().sample_ticks(0, 1000, None)) == 12
    assert snapshots().sample_ticks(0, 1000, None) == even_ticks(0, 1000)


def test_sample_ticks_even_ticks_start_at_first_and_end_at_last():
    """H-024: "even ticks are `round(first + k * (last - first) / (n_even - 1))` for k in 0..n_even-1"."""
    out = snapshots().sample_ticks(37, 412, None)
    assert out == even_ticks(37, 412)
    assert out[0] == 37 and out[-1] == 412
    assert all(isinstance(t, int) for t in out)


def test_sample_ticks_rounds_with_round():
    """H-024: even ticks are `round(...)`; first 0, last 5, n_even 3 puts the middle at 2.5, which Python's round
    gives as 2 (round half to even)."""
    assert snapshots().sample_ticks(0, 5, None, n_even=3) == [0, 2, 5]
    assert snapshots().sample_ticks(0, 3, None, n_even=3) == [0, 2, 3]       # 1.5 -> 2


def test_sample_ticks_adds_four_contact_ticks_and_sorts():
    """H-024: "contact ticks are `contact + o` for each offset when contact is not None; the result is ... sorted
    ascending". On 0..1000 none of 480, 490, 510, 520 is an even tick, so the page has 12 + 4 = 16 shots."""
    out = snapshots().sample_ticks(0, 1000, 500)
    assert out == sorted(even_ticks(0, 1000) + [480, 490, 510, 520])
    assert len(out) == 16


def test_sample_ticks_deduplicates():
    """H-024: "the result is clipped to [first, last], deduplicated and sorted ascending". Even ticks are multiples of
    20 on 0..220; contact 100 gives 80, 90, 110, 120 of which 80 and 120 are already even ticks."""
    out = snapshots().sample_ticks(0, 220, 100)
    assert out == [0, 20, 40, 60, 80, 90, 100, 110, 120, 140, 160, 180, 200, 220]
    assert len(out) == len(set(out))


def test_sample_ticks_clips_contact_ticks_below_first():
    """H-024: "clipped to [first, last]". Contact 5: 5-20 and 5-10 fall below first 0; 5+10 and 5+20 stay."""
    out = snapshots().sample_ticks(0, 220, 5)
    assert out == [0, 15, 20, 25, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220]
    assert min(out) == 0


def test_sample_ticks_clips_contact_ticks_above_last():
    """H-024: "clipped to [first, last]". Contact 215: 215+10 and 215+20 fall above last 220; 195 and 205 stay."""
    out = snapshots().sample_ticks(0, 220, 215)
    assert out == [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 195, 200, 205, 220]
    assert max(out) == 220


def test_sample_ticks_stays_inside_first_and_last_for_any_contact():
    """H-024: "the result is clipped to [first, last]" even when contact is outside the range."""
    for contact in (-500, 0, 100, 400, 10000):
        out = snapshots().sample_ticks(50, 400, contact)
        assert min(out) >= 50 and max(out) <= 400 and out == sorted(set(out))


def test_sample_ticks_one_even_tick_is_first():
    """H-024: "(all `first` when n_even is 1)"; with contact 30 the contact ticks join it."""
    assert snapshots().sample_ticks(5, 50, None, n_even=1) == [5]
    assert snapshots().sample_ticks(5, 50, 30, n_even=1) == [5, 10, 20, 40, 50]


def test_sample_ticks_custom_offsets():
    """H-024: "`offsets: tuple = (-20, -10, 10, 20)`": the offsets argument replaces them."""
    assert snapshots().sample_ticks(0, 200, 100, n_even=2, offsets=(0,)) == [0, 100, 200]
    assert snapshots().sample_ticks(0, 200, 100, n_even=2, offsets=(-30, 7)) == [0, 70, 107, 200]
    assert snapshots().sample_ticks(0, 200, 100, n_even=2, offsets=()) == [0, 200]


def test_sample_ticks_first_equal_last_is_one_tick():
    """H-024: the even ticks all equal first and are deduplicated."""
    assert snapshots().sample_ticks(7, 7, None) == [7]


# ---- integration: the real library -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def library():
    from scripts.skilllab import engine
    return engine.Engine()


def test_control_real_library_trace_still_reads_seven_fields(library):
    """H-024 control, through the production library: the first seven fields of a real trace row are
    (tick, unit, x, y, target, facing, alive) with alive a bool."""
    from scripts.skilllab import plays
    setup = dataclasses.replace(plays.blob_play(4)(4, False), trace=True, max_ticks=40)
    r = fight_mod.fight(setup, 1, False)
    assert r.trace
    assert all(isinstance(e[6], bool) and isinstance(e[1], int) for e in r.trace)


def test_real_library_trace_rows_carry_layer_and_unit_type(library):
    """H-024: the nine-field row read through `engine.unit_layer` and `engine.unit_type` of the production library:
    every row has nine fields, passes the validator, and a unit's type does not change over the fight."""
    from scripts.skilllab import plays
    setup = dataclasses.replace(plays.blob_play(4)(4, False), trace=True, max_ticks=40)
    r = fight_mod.fight(setup, 1, False)
    assert {len(e) for e in r.trace} == {9}
    assert trace_rows().validate_trace(r.trace) == len(r.trace)
    by_unit = {}
    for e in r.trace:
        by_unit.setdefault(e[1], set()).add(e[8])
    assert all(len(t) == 1 for t in by_unit.values())
