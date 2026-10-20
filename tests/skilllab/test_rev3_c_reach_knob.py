# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R3, test T7, defect D1); Westley 2026-10-19 on varying reach per type; ledger FINDING-lab-d1; piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, R3 / T7: the reach table is a swept input. Fast, fakes only (the real-scene half is
tests/skilllab/integration/test_rev3_c_reach_real.py).

R-164-01 gives each type a reach (up, down); the bible's table is the base point of the sweep. R3: per type, reach up and reach down are swept
values (0, 1, 2 each) and the rows say which reach configuration they belong to.

BUILDER CONTRACT (names and shapes this file pins; DRAFT where marked):
  sweep.with_reach(build, table) -> BuildFn      table {type name: (up, down)}. For every group of the build's Setup whose unit is a key of
        the table, Setup.unit_types[name]["reach"] = (up, down) (the entry is created as {"base": name} when the play wrote none, every
        other key of an existing entry is kept); a type in the table that no group uses is ignored and adds no entry; a type not in the
        table is untouched. The wrapper has `.labels`, a dict that mirrors the inner build's labels after each call (the sweep reads
        labels["prefight"] to refuse a cell). sweep._reach_zero is the same wrapper for every type at (0, 0).
        A value outside 0, 1, 2 (up or down) raises ValueError when with_reach is called. (0, 1, 2 are the plan's values; wider sweep
        values are Westley's, so with_reach refuses them rather than widening.)
  sweep.run_family(..., reach=None)              a new keyword; None is today's behaviour. With a table, every build of the family run
        (the play and every naive baseline) is wrapped with_reach(build, table), EXCEPT the reach_zero build of the null control, which
        stays at (0, 0) for every type (the null control of a reach family is the reach (0, 0) build).
  Every CSV row of the family (grid, refined and control rows) has a column `reach`: a string naming the configuration. Rows of one run
        share one value; the value of a run with reach=None differs from the value of a run with a table; the value of a table run
        names the type (contains "Raider" for {"Raider": (2, 1)}). DRAFT format; the tests pin equality, difference and that.
Red today: sweep.with_reach does not exist; run_family takes no `reach` (TypeError)."""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import _fr  # noqa: E402
from scripts.skilllab import sweep  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

PLAY = "p1"
BASE_REACH = (1, 1)
# DRAFT numbers of the scripted fight, not rules: side 0 beats up to this many enemy heads when its Raiders have this reach
BREAK_EVEN = {(1, 1): 20, (2, 1): 36, (0, 0): 4}


def raider_groups():
    return (Group(side=0, unit="Raider", count=8, formation="blob", x=-700.0, y=0.0, facing_deg=0.0, layer=1, order="attack_move",
                  params={"radius": 80.0}),
            Group(side=0, unit="Vanguard", count=8, formation="blob", x=-700.0, y=0.0, facing_deg=0.0, layer=0, order="attack_move",
                  params={"radius": 80.0}),
            Group(side=1, unit="Vanguard", count=8, formation="blob", x=700.0, y=0.0, facing_deg=180.0, layer=0, order="attack_move",
                  params={"radius": 80.0}))


def make_builds(word="ok"):
    """builds(play, role, layout): a meeting with 8 Raiders (reach (1, 1), the bible's value) and 8 Vanguards on side 0; the null
    control's role reach_zero writes (0, 0) itself, as sweep._reach_zero does."""
    def builds(play, role, layout):
        def build(enemy_heads, swap):
            build.labels["prefight"] = word
            groups = list(raider_groups())
            groups[2] = Group(**{**groups[2].__dict__, "count": enemy_heads})
            reach = (0, 0) if role == "reach_zero" else BASE_REACH
            return Setup(groups=tuple(groups), unit_types={"Raider": {"base": "Raider", "reach": reach}})
        build.labels = {"placement_shift": 0.0, "prefight": None}
        return build
    return builds


class Fights:
    """fight_fn: side 0 wins while enemy_heads <= BREAK_EVEN[the Raider reach the Setup carries]; records every Setup it was given."""

    def __init__(self):
        self.seen = []

    def __call__(self, setup, seed, swap):
        reach = setup.unit_types["Raider"]["reach"]
        self.seen.append(reach)
        enemy = sum(g.count for g in setup.groups if g.side == 1)
        return _fr("side0" if enemy <= BREAK_EVEN[tuple(reach)] else "side1", enemy)


def run_one(tmp_path, name, **kw):
    fights = Fights()
    entry = sweep.run_family("range_up", tmp_path / name, builds=make_builds(), layouts={"A": {"id": 1}}, plays=(PLAY,), fight_fn=fights,
                             replicates=1, **kw)
    with open(tmp_path / name / entry["csv"], newline="") as fh:
        return entry, list(csv.DictReader(fh)), fights


def best_won(rows):
    """The largest scanned enemy headcount the play won, read from the play's grid rows (the scan's own result, independent of the sweep)."""
    return max(int(r["enemy_heads"]) for r in rows if r["baseline"] == "none" and r["kind"] == "grid" and r["outcome"] == "side0")


# ------------------------------------------------------------------------------------------------------ the controls (green today)

def test_control_without_a_table_the_builds_are_untouched_and_the_break_even_is_the_base_one(tmp_path):
    """Positive control: the scripted fight reads the base Raider reach (1, 1) everywhere but in the null control (0, 0), and the play's
    break-even is the one scripted for (1, 1): the scan finds the exact crossing."""
    _entry, rows, fights = run_one(tmp_path, "base")
    assert set(fights.seen) == {(1, 1), (0, 0)}
    assert best_won(rows) == BREAK_EVEN[(1, 1)]


# -------------------------------------------------------------------------------------------------- T7: a swept input (red today)

def test_a_reach_configuration_reaches_every_fight_and_moves_the_break_even(tmp_path):
    """T7: the sweep with Raider reach (2, 1) shows the fights Raiders with reach (2, 1) and finds a different break-even than the base
    configuration (the scripted fight wins up to 36 with (2, 1), up to 20 with (1, 1)). Red today: TypeError, no `reach` keyword."""
    _e0, base_rows, _f0 = run_one(tmp_path, "base")
    _e1, rows, fights = run_one(tmp_path, "cfg", reach={"Raider": (2, 1)})
    assert (2, 1) in set(fights.seen) and (1, 1) not in set(fights.seen)
    assert best_won(rows) > best_won(base_rows)
    assert (best_won(rows), best_won(base_rows)) == (BREAK_EVEN[(2, 1)], BREAK_EVEN[(1, 1)])


def test_the_null_control_build_stays_at_reach_zero_under_a_configuration(tmp_path):
    """The null control of a reach family is the reach (0, 0) build; a table does not lift it. The (0, 0) fights are the control rows."""
    _entry, rows, fights = run_one(tmp_path, "cfg", reach={"Raider": (2, 1)})
    assert (0, 0) in set(fights.seen) and (2, 1) in set(fights.seen)
    assert any(r["kind"] == "control_null" for r in rows)


def test_every_row_names_its_reach_configuration(tmp_path):
    """The CSV carries `reach` on every row (grid, refined, control); one value per run; the base run and the table run differ and the
    table run's value names the type."""
    _e0, base_rows, _f0 = run_one(tmp_path, "base")
    _e1, rows, _f1 = run_one(tmp_path, "cfg", reach={"Raider": (2, 1)})
    base_labels, labels = {r["reach"] for r in base_rows}, {r["reach"] for r in rows}
    assert len(base_labels) == 1 and len(labels) == 1 and base_labels != labels
    assert "Raider" in next(iter(labels))


# ------------------------------------------------------------------------------------------------------------- with_reach itself

def inner(word="ok"):
    return make_builds(word)(PLAY, "play", "A")


def test_with_reach_sets_the_reach_of_the_types_the_setup_uses_and_nothing_else():
    wrapped = sweep.with_reach(inner(), {"Raider": (0, 1), "Interceptor": (2, 1)})
    s = wrapped(8, False)
    assert s.unit_types["Raider"] == {"base": "Raider", "reach": (0, 1)}            # the entry's other keys are kept
    assert "Interceptor" not in s.unit_types                                        # no group uses it
    assert "Vanguard" not in s.unit_types                                           # not in the table: untouched
    assert [g.count for g in s.groups] == [8, 8, 8]


def test_with_reach_makes_an_entry_for_a_type_the_play_wrote_none_for():
    def bare(enemy_heads, swap):
        return Setup(groups=raider_groups(), unit_types={})
    bare.labels = {}
    s = sweep.with_reach(bare, {"Vanguard": (0, 2)})(8, False)
    assert s.unit_types == {"Vanguard": {"base": "Vanguard", "reach": (0, 2)}}


def test_with_reach_mirrors_the_inner_builds_labels_after_a_call():
    """The sweep refuses a cell on build.labels['prefight'] (_refusal); the wrapper must carry it, as sweep._reach_zero does."""
    wrapped = sweep.with_reach(inner("no_reach"), {"Raider": (1, 1)})
    wrapped(8, False)
    assert wrapped.labels["prefight"] == "no_reach"


@pytest.mark.parametrize("bad", [(3, 1), (1, 3), (-1, 1), (1, -1), (1,), (1, 1, 1), "11"])
def test_with_reach_refuses_values_outside_the_rules(bad):
    """Reach values are 0, 1, 2 (the plan); a wider sweep value is Westley's number, so it is refused, not widened."""
    with pytest.raises(ValueError):
        sweep.with_reach(inner(), {"Raider": bad})
