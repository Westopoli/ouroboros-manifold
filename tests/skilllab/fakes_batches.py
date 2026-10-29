"""Fakes for the batch tests: hand-built ScanResults, a recording scan function and a defn with fake builds. No engine."""
import dataclasses

import pytest

from scripts.skilllab.contract import CellResult, FightResult, ScanResult, Setup


WEIGHTED_US = (1.5, 0.75)     # what every fight reports: weighted_unit_seconds is always populated (LAB-REV2 L1/L2; Setup.weighted is gone)


def fight(ticks=100, outcome="side0", fus=(0.5, 0.25), wus=WEIGHTED_US):
    return FightResult(outcome=outcome, margin=0.1, strength_left=(0.5, 0.2), survivors=(8, 2), heads=(16, 16),
                       ticks=ticks, first_contact_tick=1, firing=[(0, 1, 1), (5, 1, 0)],
                       firing_unit_seconds=fus, weighted_unit_seconds=wus)


def make_scan(size, enemy_from, enemy_to, beats, capped=0, ticks=100, wus=WEIGHTED_US, ceiling=False):
    """One cell per enemy count with two fights each (side0 where won, side1 where lost); the first `capped` fights of the first
    cell are caps (a lab defect). ceiling=True: won all the way, beats = enemy_to, loses_to None, ceiling_hit."""
    cells = []
    for i, n in enumerate(range(enemy_from, enemy_to + 1)):
        won = ceiling or (beats is not None and n <= beats)
        outs = ["cap" if (i == 0 and k < capped) else ("side0" if won else "side1") for k in range(2)]
        cells.append(CellResult(enemy_heads=n, fights=[fight(ticks, o, wus=wus) for o in outs], mean_margin=0.1,
                                won=won and "cap" not in outs, defect="cap" in outs))
    if ceiling:
        beats = enemy_to
    return ScanResult(size=size, cells=cells, beats=beats, loses_to=None if beats is None or ceiling else beats + 1,
                      ceiling_hit=ceiling)


class FakeScan:
    """Callable like scan.scan. results: {(cell_label, policy_or_None): beats or (beats, capped)}; default beats 15.
    Calls the build once (enemy_from, False) and records the Setup it returns."""

    def __init__(self, results=None, default=15):
        self.results, self.default, self.calls = dict(results or {}), default, []

    def __call__(self, build, size, enemy_from, enemy_to, replicates=10, **kw):
        setup = build(enemy_from, False)
        label = setup.unit_types["_cell"]
        policy = setup.settings.get("OM_TP_TARGET_POLICY")
        self.calls.append(dict(label=label, policy=policy, size=size, enemy_from=enemy_from, enemy_to=enemy_to,
                               replicates=replicates, setup=setup, kw=kw))
        got = self.results.get((label, policy), self.default)
        beats, capped = got if isinstance(got, tuple) else (got, 0)
        return make_scan(size, enemy_from, enemy_to, beats, capped)


def _marked(build, label):
    """The same build, with the cell label added to the Setup it returns (the real groups and terrain stay)."""
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        return dataclasses.replace(setup, unit_types={**setup.unit_types, "_cell": label})
    return wrapped


def _empty(label):
    return lambda enemy_heads, swap: Setup(groups=(), unit_types={"_cell": label})


def faked(defn, real=False):
    """The same BatchDef with a fake build per scannable cell (and per reference, labelled <cell>#ref); the build marks
    its Setup with the cell label. real=True keeps the real builds and only adds the mark (asym.unit_stats must be faked)."""
    cells = []
    for c in defn.cells:
        if c.build is None:
            cells.append(c)
            continue
        make = _marked if real else (lambda b, l: _empty(l))
        extra = {}
        if getattr(c, "reference", None) is not None:
            extra["reference"] = make(c.reference, c.label + "#ref")
        cells.append(dataclasses.replace(c, build=make(c.build, c.label), **extra))
    return dataclasses.replace(defn, cells=tuple(cells))


def fake_sensors(monkeypatch):
    """asym.unit_stats faked (every type sees 700), so real builds run without the engine."""
    from scripts.skilllab import asym
    monkeypatch.setattr(asym, "unit_stats", lambda name: {"category": 1, "max_hp": 100.0, "base_damage": 10.0,
                                                          "attack_interval": 20.0, "attack_range": 100.0, "speed": 5.0,
                                                          "sensor_radius": 700.0, "layer_transition_time": 0.0,
                                                          "aoe_radius": 0.0})


@pytest.fixture(autouse=True)
def stub_summary_write(monkeypatch):
    """Import this into a test module and it applies to every test there. summary.py is L5's file and still reads
    FightResult.mopup_orders (retired by L2), so batches.run would crash in it until L5 rewrites it. L4's tests are about the batch
    definitions, the run file, the page and the csv; they replace summary.write with a stub that writes an empty object.
    # See also: test_batches.py::test_run_hands_the_summary_to_summary_write_with_the_rule_note (the call itself is pinned there)."""
    from scripts.skilllab import summary
    monkeypatch.setattr(summary, "write", lambda defn, scans, path, rule, *a, **k: path.write_text("{}", encoding="utf-8"))
