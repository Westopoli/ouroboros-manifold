# Rule pins: R-207-06, R-207-07, R-087-04, R-084-04, R-087-03, R-087-09, R-083-03, R-093-02, R-004-06
"""Engine rules round 2, T3, check 5: the rule checker runs wherever the lab steps the engine.

Where the lab steps the engine (read 2026-11-11): scripts/skilllab/arena/run.py::fight (already checked), scripts/skilllab/fight.py::_run (through
fight.fight; scan.cell, scan.scan, probe.survey, sweep.run_family, pool.run_job and breakeven all call fight.fight and carry its FightResult), and
scripts/skilllab/search.py::run_search (its own loop). scenes.py builds Setups and steps nothing, so it has no test of its own (it is checked through the
fight of every Setup it builds).

THE INTERFACE THIS FILE PINS (the smallest common one):
    FightResult.violations   list of {"rule", "tick", "unit", "detail"} (the first 20, ordered by (tick, rule, unit)); [] when clean
    FightResult.invalid      bool, True when any rule was broken
    FightResult.suspended    {rule: switch}, the rules the run cannot judge ({} here: targeting by sight on)
    SearchResult.violations / .invalid   the same two, for scripts/skilllab/search.py::run_search
    CellResult.invalid, ScanResult.invalid   True when any fight in them is invalid
    probe.survey(...)[(heads, seed)]["invalid"]   True when the base or the moved fight of that point is invalid
    rows.fight_row(result)["invalid"]   1 or 0; sweep.run_family's CSV carries the column
"INVALID" in this lab is the `invalid` flag; the arena's stdout line (`INVALID <layout> <rule> tick N unit U`, exit 2) stays arena/run.py's.
The planted layout: a wrapper of Engine.step sets side 0's first unit down 900 wu away on step 5 of every world (a leap no unit can make; a continuity
violation whatever else the checker knows). Real engine, no fakes; 2 against 2 Vanguards, 80 ticks.
"""
import ctypes
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight, probe, rows, scan  # noqa: E402
from scripts.skilllab.contract import Group, Setup, trim_series  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402

PLANT_STEP = 5
LEAP = 900.0


def build(enemy_heads=2, swap=False, max_ticks=80, settings=None):
    def side(s, n, x):
        return Group(side=s, unit="Vanguard", count=n, formation="blob", x=x, y=1000.0, facing_deg=0.0 if s == 0 else 180.0, layer=0,
                     order="attack_move", params={"radius": 60.0})
    return Setup(groups=(side(0, 2, 1000.0), side(1, enemy_heads, 1700.0)), unit_types={}, max_ticks=max_ticks, settings=settings or {})


@pytest.fixture
def plant(monkeypatch):
    """Engine.step puts side 0's first unit 900 wu north of where it is, after step 5 of every world it steps."""
    real, count = Engine.step, {}

    def step(self, w):
        real(self, w)
        count[w.value] = count.get(w.value, 0) + 1
        if count[w.value] == PLANT_STEP:
            lib = self._lib
            lib.om_unit_set_pos.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
            u = sorted(self._own[(w.value, 0)])[0]
            x, y = self.unit_pos(w, u)
            lib.om_unit_set_pos(w, u, x, y + LEAP)
    monkeypatch.setattr(Engine, "step", step)
    return count


def said(violations):
    return {v["rule"] for v in violations}


# ------------------------------------------------------------------ fight.py

def test_control_a_planted_fight_still_runs_and_returns_a_result(plant):
    """Control (green today): the planted fight through fight.fight returns its result (the harness works; only the verdict is missing)."""
    r = fight.fight(build(), 0, False)
    assert r.ticks > 0 and r.heads == (2, 2) and plant


def test_fight_result_of_a_clean_fight_is_valid():
    """Check 5: a fight through fight.fight carries `violations` ([]) and `invalid` (False) when no rule was broken."""
    r = fight.fight(build(), 0, False)
    assert (r.violations, r.invalid, r.suspended) == ([], False, {})


def test_fight_result_of_a_planted_leap_is_invalid(plant):
    """Check 5: the leap makes fight.fight's result invalid, with a continuity violation at tick 5."""
    r = fight.fight(build(), 0, False)
    assert r.invalid is True and ("continuity", PLANT_STEP) in {(v["rule"], v["tick"]) for v in r.violations}


def test_fight_result_with_targeting_by_sight_off_reports_the_suspended_checks():
    """R-087-03 and R-093-02 with OM_TP_TARGET_BY_SIGHT 0 (Setup.settings): no verdict on them, `suspended` names the switch, never a silent pass."""
    r = fight.fight(build(settings={"OM_TP_TARGET_BY_SIGHT": 0.0}), 0, False)
    assert r.suspended == {"R-087-03": "OM_TP_TARGET_BY_SIGHT", "R-093-02": "OM_TP_TARGET_BY_SIGHT"}


def test_the_lean_pool_trim_keeps_the_verdict(plant):
    """pool.run_job drops the per-tick series with trim_series; the verdict survives it (the sweep's workers use that)."""
    assert trim_series(fight.fight(build(), 0, False)).invalid is True


# ------------------------------------------------------------------ scan.py and what calls it

def _bld(enemy_heads, swap):
    return build(enemy_heads, swap)


def test_cell_of_planted_fights_is_invalid(plant):
    """scan.cell (replicates 1, both spawn orders): CellResult.invalid is True when its fights are."""
    assert scan.cell(_bld, 2, 1).invalid is True


def test_cell_of_clean_fights_is_valid():
    """scan.cell control: valid when its fights are."""
    assert scan.cell(_bld, 2, 1).invalid is False


def test_scan_of_planted_fights_is_invalid(plant):
    """scan.scan over one headcount: ScanResult.invalid is True."""
    assert scan.scan(_bld, 2, 2, 2, replicates=1).invalid is True


def test_probe_survey_marks_a_point_with_an_invalid_fight(plant):
    """probe.survey (settings: sight on, a no-op knob): every point of the survey says invalid."""
    got = probe.survey(_bld, {"OM_TP_TARGET_BY_SIGHT": 1.0}, heads=[2], seeds=(0,))
    assert got[(2, 0)]["invalid"] is True


def test_probe_survey_of_clean_fights_is_valid():
    """probe.survey control: valid points say so."""
    assert probe.survey(_bld, {"OM_TP_TARGET_BY_SIGHT": 1.0}, heads=[2], seeds=(0,))[(2, 0)]["invalid"] is False


def test_the_sweep_row_of_an_invalid_fight_says_so(plant):
    """sweep rows (rows.fight_row, what sweep.run_family writes): `invalid` is 1 for the planted fight and 0 for a clean one."""
    bad = rows.fight_row(fight.fight(build(), 0, False))["invalid"]
    assert bad == 1


def test_the_sweep_row_of_a_clean_fight_says_zero():
    """sweep rows control: `invalid` 0."""
    assert rows.fight_row(fight.fight(build(), 0, False))["invalid"] == 0


# ------------------------------------------------------------------ search.py (its own step loop)

def _search(cap=40):
    from scripts.skilllab import search
    from scripts.skilllab.search_policies import HIDER_SCRIPTS, POLICIES
    setting = search.SearchSetting(radius=500.0, reach=2000.0, reveal_ticks=100, cooldown_ticks=200, force=4)
    placement = search.Placement(dx=6000.0, dy=0.0, layer=2, heading_deg=0.0, script=sorted(HIDER_SCRIPTS)[0])
    policy = sorted(POLICIES)[0]
    return search.run_search(setting, policy, policy, placement, 0, cap_ticks=cap)


def test_search_result_of_a_clean_run_is_valid():
    """search.run_search carries `violations` and `invalid` too (no unit leaps, none fires: a clean run)."""
    r = _search()
    assert (r.violations, r.invalid) == ([], False)


def test_search_result_of_a_planted_leap_is_invalid(plant):
    """search.run_search: the leap makes the run invalid (the planted unit is the seeker's first)."""
    r = _search()
    assert r.invalid is True and "continuity" in said(r.violations)
