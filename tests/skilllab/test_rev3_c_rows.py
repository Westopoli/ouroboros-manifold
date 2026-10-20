# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R7 "ends as a finding row `no_reach_stall` ... never runs to the cap", test T9, defect D7); ledger FINDING-lab-d7, FINDING-lab-d11 (verdict decided_one_way_reach recorded "with that verdict tag and the tick it became decided"); piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, the verdicts as rows: what the CSV, the scan and the sweep's defect count do with a fight that ended no_reach_stall or
decided_one_way_reach. Fast, fake fights (the fight itself is in test_rev3_c_stall.py).

BUILDER CONTRACT (names DRAFT where marked):
  rows.fight_row(result) writes the columns `verdict` (None -> empty cell, else the frozen name) and `decided_tick` (empty unless the verdict is
      decided_one_way_reach), from FightResult.verdict and FightResult.decided_tick (test_rev3_c_stall.py).
  A no_reach_stall is a finding, not a lab defect and not a result: scan.cell does not mark its cell `defect`, the cell is not won;
      sweep's entry["defects"] ("cap_rows", "blind_post_rows", "draw_rows", "cells" today) gains the counters
      `no_reach_stall_rows` and `decided_one_way_reach_rows` (DRAFT key names: the frozen name plus _rows), counted over the live (non-control)
      rows whose `verdict` is that name; a stall row is in neither cap_rows nor cells (a fight that ends at a stall never reached the cap).
  A decided_one_way_reach row is an ordinary win for its side (outcome side0 or side1): a cell it fills is won when all its rows are side0.
OPEN (not asserted, plan silent): the outcome STRING of a stall (test_rev3_c_stall.py reads 'ends as a finding row' as outcome == "no_reach_stall");
the controls below use the same string. Red today: FightResult has no verdict field; the counters and columns do not exist."""
import csv
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import _fr  # noqa: E402
from test_rev3_c_reach_knob import make_builds  # noqa: E402
from scripts.skilllab import rows as rows_mod, scan, sweep  # noqa: E402

STALL, DECIDED = "no_reach_stall", "decided_one_way_reach"


def stall(heads):
    return dataclasses.replace(_fr(STALL, heads, survivors=(8, 8)), winner=None, verdict=STALL)


def decided(heads, tick=50):
    return dataclasses.replace(_fr("side0", heads), verdict=DECIDED, decided_tick=tick)


# ---- controls (green today): a stall is neither a win nor a defect ---------------------------------------------------------------------

def test_control_a_stall_outcome_cell_is_not_won_and_not_a_defect():
    """The scan's cell reads outcomes only: outcome 'no_reach_stall' is not side0 and not draw/cap. Green today and after."""
    from scripts.skilllab.contract import Group, Setup
    g = (Group(side=0, unit="Vanguard", count=4, formation="blob", x=-300.0, y=0.0, facing_deg=0.0, layer=0, order="attack_move",
               params={"radius": 40.0}),
         Group(side=1, unit="Vanguard", count=4, formation="blob", x=300.0, y=0.0, facing_deg=180.0, layer=0, order="attack_move",
               params={"radius": 40.0}))
    build = lambda heads, swap: Setup(groups=g, unit_types={})
    cell = scan.cell(build, 4, 2, fight_fn=lambda s, seed, swap: _fr(STALL, 4))
    assert (cell.won, cell.defect) == (False, False)


# ---- the row columns ---------------------------------------------------------------------------------------------------------------------

def test_the_row_carries_the_stall_verdict_and_an_empty_decided_tick(tmp_path):
    """Red today: FightResult(verdict=...) is a TypeError (the field does not exist)."""
    row = rows_mod.fight_row(stall(16))
    assert (row["verdict"], row["decided_tick"]) == (STALL, None)
    rows_mod.write_rows([row], tmp_path / "r.csv")
    with open(tmp_path / "r.csv", newline="") as fh:
        got = list(csv.DictReader(fh))[0]
    assert (got["verdict"], got["decided_tick"], got["outcome"]) == (STALL, "", STALL)


def test_the_row_carries_the_decided_verdict_and_the_tick(tmp_path):
    row = rows_mod.fight_row(decided(16, tick=7411))
    assert (row["verdict"], row["decided_tick"], row["outcome"]) == (DECIDED, 7411, "side0")
    rows_mod.write_rows([row], tmp_path / "r.csv")
    with open(tmp_path / "r.csv", newline="") as fh:
        got = list(csv.DictReader(fh))[0]
    assert (got["verdict"], got["decided_tick"]) == (DECIDED, "7411")


def test_an_ordinary_row_has_empty_verdict_cells(tmp_path):
    """Positive control for the columns' emptiness: a plain win writes no verdict and no tick. Red today only because the columns are missing."""
    row = rows_mod.fight_row(_fr("side0", 16))
    assert row["verdict"] is None and row["decided_tick"] is None


# ---- the sweep's count ------------------------------------------------------------------------------------------------------------------

def run(tmp_path, name, fight_fn):
    entry = sweep.run_family("range_up", tmp_path / name, builds=make_builds(), layouts={"A": {"id": 1}}, plays=("p1",), fight_fn=fight_fn,
                             replicates=1)
    with open(tmp_path / name / entry["csv"], newline="") as fh:
        return entry, list(csv.DictReader(fh))


def test_stall_rows_are_counted_apart_and_are_not_caps_or_defect_cells(tmp_path):
    """Every fight at 24 or more enemy heads ends no_reach_stall; fewer, side0. The stall rows are counted as no_reach_stall_rows, make no cap row
    and no defect cell. Red today: the fights cannot be built (verdict) and the counter is absent."""
    entry, rows = run(tmp_path, "stall", lambda setup, seed, swap: (
        stall(sum(g.count for g in setup.groups if g.side == 1)) if sum(g.count for g in setup.groups if g.side == 1) >= 24
        else _fr("side0", sum(g.count for g in setup.groups if g.side == 1))))
    n = sum(1 for r in rows if r["verdict"] == STALL and not r["kind"].startswith("control_"))
    assert n > 0
    d = entry["defects"]
    assert (d["no_reach_stall_rows"], d["cap_rows"], d["cells"]) == (n, 0, 0), d


def test_decided_rows_are_counted_and_stay_wins(tmp_path):
    """Every fight is a win for side 0 tagged decided: the count equals the tagged live rows, the rows' outcome is side0, nothing is a defect."""
    entry, rows = run(tmp_path, "decided", lambda setup, seed, swap: decided(sum(g.count for g in setup.groups if g.side == 1)))
    n = sum(1 for r in rows if r["verdict"] == DECIDED and not r["kind"].startswith("control_"))
    assert n > 0 and all(r["outcome"] == "side0" for r in rows if r["verdict"] == DECIDED)
    d = entry["defects"]
    assert (d["decided_one_way_reach_rows"], d["cap_rows"], d["cells"]) == (n, 0, 0), d
