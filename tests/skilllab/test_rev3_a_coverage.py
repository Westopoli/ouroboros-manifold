# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R5, test T1; defects D1, D2, D10); ledger FINDING-lab-d1, FINDING-lab-d2, FINDING-lab-d10; piece LAB-REV3-A
"""LAB-REV3-A, T1 (R5, D1, D2, D10): the coverage test over the swept plays, the mix table and the reach table. Fast half: no fight.

What "covered" means here (the test writer's reading of R5, flagged to the Architect; the plan gives no definition):
  - SWEPT PLAYS (Architect ruling 2026-10-20 on the writer's reading): "covered" means exercised by a play named in
    `sweep.PLAYS_BY_FAMILY`; a play registered in `plays_space.PLAYS` or a mix row of `plays_space.MIXES` that no family sweeps does NOT
    cover anything (the analyses count "4 of 9 cells in the sweep", and M3, M4, M3b are in `plays_space.MIXES` but their plays are in
    no family). Each play's `Setup` comes from `plays_space.PLAYS[name].setup_fn()`.
  - CATEGORY CELL (attacker category, target category) over ALG-60's three categories Strike (Raider, Interceptor), Line (Vanguard,
    Warden), Siege (Bombard, Bastion): covered when a swept Setup holds a unit of the first category on one side and a unit of the
    second on the other (so a mix of {A, B} yields every cell among A and B, as the mix analyses count). Nine cells.
  - REACH PAIRING (type, offset): offset = target layer minus shooter layer; a type can make the pairings -down..+up of its reach
    (plays_space._REACH, a type absent from it, the Warden, has reach (0, 0)); covered when a swept Setup has a group of that type
    and a group of the other side whose layer is the shooter's layer plus the offset.
  - LAYER n in 0..4 (OM_LAYER_COUNT 5): covered when any group of a swept Setup stands on it.

THE STRICT EXPECTED FAILURE (retired). `test_t1_*_real_tables` was `xfail(strict=True)` in piece A, carrying FINDING-lab-d1 and
FINDING-lab-d2. LAB-REV3-B added the mixes M5 to M9 and the all-layer plays; the ruler removed the marker (ledger TD-LAB-REV3-B-a-tests)
and the test passes plain.

BUILDER CONTRACT (the only names pinned; everything else in coverage.py is the builder's):
  scripts/skilllab/coverage.py (NEW)
    uncovered(setups, reach=None) -> {"cells": [(attacker_category, target_category), ...], "pairings": [(type_name, offset), ...],
                                       "layers": [layer, ...]}
        the items of the three kinds NOT covered by the given Setups, each list possibly empty (an empty report is "all covered").
        Category names are the strings "Strike", "Line", "Siege". `reach` is a {type name: (up, down)} dict over the six built-in
        types and defaults to plays_space._REACH with the Warden at (0, 0).
    report() -> the same dict, for the swept plays of the real tables: it reads `sweep.PLAYS_BY_FAMILY` and `plays_space.PLAYS` at call
        time (module attributes, not copies taken at import), so the fixtures of the report() tests below can replace them.
Positive controls (green on the lab tip, fixtures only): the oracle below reports nothing for a fixture that covers everything, and
names exactly the expected items for a fixture that covers what the sweep covers today."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays_space, sweep  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

CATEGORY = {"Raider": "Strike", "Interceptor": "Strike", "Vanguard": "Line", "Warden": "Line", "Bombard": "Siege", "Bastion": "Siege"}
TYPES = tuple(CATEGORY)
LAYERS = range(5)
REACH = {**plays_space._REACH, "Warden": (0, 0)}      # the bible's reach table as the lab holds it (Warden absent from _REACH)


def G(side, unit, layer):
    return Group(side=side, unit=unit, count=1, formation="blob", x=0.0, y=0.0, facing_deg=0.0, layer=layer, order="attack_move")


def S(unit0, layer0, unit1, layer1):
    return Setup(groups=(G(0, unit0, layer0), G(1, unit1, layer1)), unit_types={})


def oracle(setups, reach=REACH):
    """The three uncovered lists, computed here from the definitions in the module docstring (the test's own detector)."""
    cells, pairings, layers = set(), set(), set()
    for s in setups:
        for a in s.groups:
            layers.add(a.layer)
            for b in s.groups:
                if a.side == b.side:
                    continue
                cells.add((CATEGORY[a.unit], CATEGORY[b.unit]))
                up, down = reach[a.unit]
                if -down <= b.layer - a.layer <= up:
                    pairings.add((a.unit, b.layer - a.layer))
    want_cells = {(x, y) for x in set(CATEGORY.values()) for y in set(CATEGORY.values())}
    want_pairings = {(t, d) for t in TYPES for d in range(-reach[t][1], reach[t][0] + 1)}
    return {"cells": sorted(want_cells - cells), "pairings": sorted(want_pairings - pairings), "layers": sorted(set(LAYERS) - layers)}


def swept_setups():
    names = sorted({p for plays in sweep.PLAYS_BY_FAMILY.values() for p in plays})
    return [plays_space.PLAYS[n].setup_fn() for n in names]


def full_fixture():
    """Covers every cell, every pairing and every layer."""
    out = []
    for i, (a, b) in enumerate((a, b) for a in TYPES for b in TYPES):
        out.append(S(a, i % 5, b, i % 5))
    for t in TYPES:
        up, down = REACH[t]
        for d in range(-down, up + 1):
            lo = max(0, -d)
            out.append(S(t, lo, "Vanguard", lo + d))
    return out


def today_fixture():
    """What the sweep covers today: Vanguards and Raiders on layers 0 and 1 (M0 and M1)."""
    return [S("Raider", 1, "Vanguard", 0), S("Raider", 0, "Vanguard", 0), S("Raider", 0, "Raider", 1), S("Vanguard", 0, "Vanguard", 0)]


def names(report):
    return {k: sorted(tuple(x) if isinstance(x, (list, tuple)) else x for x in report[k]) for k in ("cells", "pairings", "layers")}


# ---- the fixtures and the detector's own positive control (green on the lab tip) ------------------------------------------------

def test_the_categories_the_oracle_uses_are_the_engines():
    """Guard for the oracle's table: Engine category 0 Strike, 1 Line, 2 Siege (ALG-60 order) for the six built-ins."""
    from scripts.skilllab.engine import Engine
    e = Engine()
    w = e.new_world(0)
    try:
        got = {n: e.type_stats(w, e.type_id(n))["category"] for n in TYPES}
    finally:
        e.free_world(w)
    assert {n: ("Strike", "Line", "Siege")[c] for n, c in got.items()} == CATEGORY


def test_positive_control_a_fixture_covering_everything_reports_nothing():
    assert oracle(full_fixture()) == {"cells": [], "pairings": [], "layers": []}


def test_positive_control_the_sweep_today_fixture_is_named_item_by_item():
    """Independent of the oracle's code: five Siege cells, eleven pairings of the Interceptor, Warden, Bombard and Bastion, layers 2 to 4."""
    got = oracle(today_fixture())
    assert got["cells"] == sorted([("Strike", "Siege"), ("Siege", "Strike"), ("Line", "Siege"), ("Siege", "Line"), ("Siege", "Siege")])
    assert got["layers"] == [2, 3, 4]
    assert got["pairings"] == sorted([("Interceptor", d) for d in (-1, 0, 1, 2)] + [("Warden", 0)]
                                     + [("Bombard", d) for d in (-2, -1, 0)] + [("Bastion", d) for d in (-2, -1, 0)])


def test_the_real_swept_plays_now_stand_on_layers_0_to_4():
    """D1 and D2 premise as of LAB-REV3-B (ledger TD-LAB-REV3-B-a-tests): the swept set holds the all-layer plays and the mixes M5 to M9, so
    it stands on every layer 0..4 and fields all six types. Replaces the piece A tripwire that pinned layers 0 and 1 and three types, whose
    docstring said piece B retires it; the positive controls above and the T1 test below are unchanged."""
    setups = swept_setups()
    assert {g.layer for s in setups for g in s.groups} == {0, 1, 2, 3, 4}
    assert {g.unit for s in setups for g in s.groups} == set(TYPES)


# ---- the module (builder contract) against the fixtures --------------------------------------------------------------------------

def test_t1_module_reports_nothing_for_the_full_fixture():
    """T1 positive control for scripts/skilllab/coverage.py. Red today only because the module does not exist (builder contract)."""
    from scripts.skilllab import coverage
    assert names(coverage.uncovered(full_fixture())) == {"cells": [], "pairings": [], "layers": []}


def test_t1_module_names_each_uncovered_cell_pairing_and_layer_of_the_today_fixture():
    """T1 detector (D1, D2, D10): the module's report equals the item-by-item expectation of the oracle test above."""
    from scripts.skilllab import coverage
    assert names(coverage.uncovered(today_fixture())) == names(oracle(today_fixture()))


class _Play:
    def __init__(self, setup):
        self.setup_fn = lambda: setup


def fake_tables(monkeypatch, swept, unswept=()):
    """Replace the real tables by fixtures: `swept` are Setups of plays named in PLAYS_BY_FAMILY (two families, one play in both),
    `unswept` are Setups registered in PLAYS that no family names."""
    plays = {"sw%d" % i: _Play(s) for i, s in enumerate(swept)}
    plays.update({"un%d" % i: _Play(s) for i, s in enumerate(unswept)})
    by_family = {"fam_a": tuple(k for k in plays if k.startswith("sw")), "fam_b": tuple(k for k in plays if k.startswith("sw"))[:1]}
    monkeypatch.setattr(plays_space, "PLAYS", plays)
    monkeypatch.setattr(sweep, "PLAYS_BY_FAMILY", by_family)


def test_t1_report_reads_the_swept_plays_of_the_tables_and_nothing_else(monkeypatch):
    """T1 (W1 of the audit): `coverage.report()` on a fixture of the real tables' shape: the swept plays cover the today fixture, and an
    unswept play in PLAYS that would cover Siege, layers 3 and 4 and the Warden adds nothing. Red today: no coverage module."""
    from scripts.skilllab import coverage
    extra = [S("Bombard", 4, "Warden", 2), S("Bastion", 3, "Interceptor", 3)]
    fake_tables(monkeypatch, today_fixture(), unswept=extra)
    assert names(coverage.report()) == names(oracle(today_fixture()))
    assert names(coverage.report()) != names(oracle(today_fixture() + extra))


def test_t1_report_is_empty_when_the_swept_plays_cover_everything(monkeypatch):
    """T1 positive control for report() (W1): a fixture whose swept plays are the full fixture reports nothing. Red today: no module."""
    from scripts.skilllab import coverage
    fake_tables(monkeypatch, full_fixture())
    assert names(coverage.report()) == {"cells": [], "pairings": [], "layers": []}


def test_t1_module_uses_the_reach_it_is_given():
    """A reach table with the Raider at (0, 0) takes the Raider's +-1 pairings out of what a type can make, so they are not reported."""
    from scripts.skilllab import coverage
    flat = {**REACH, "Raider": (0, 0)}
    assert names(coverage.uncovered(today_fixture(), reach=flat)) == names(oracle(today_fixture(), flat))
    assert not any(p[0] == "Raider" and p[1] != 0 for p in coverage.uncovered(today_fixture(), reach=flat)["pairings"])


# ---- T1 itself (piece A's strict xfail marker was removed by the LAB-REV3-B ruler: coverage is complete) ----

def test_t1_every_category_cell_reach_pairing_and_layer_is_covered_by_the_real_tables():
    """T1 (R5, D1, D2, D10): the real swept plays leave nothing uncovered. The first assertion is the oracle's answer; the second
    holds the module to the same answer."""
    left = oracle(swept_setups())
    assert left == {"cells": [], "pairings": [], "layers": []}, "uncovered: %s" % left
    from scripts.skilllab import coverage
    assert names(coverage.report()) == names(left)
