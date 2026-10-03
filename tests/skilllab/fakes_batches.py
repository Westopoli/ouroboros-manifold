"""Fakes for the batch tests: hand-built ScanResults, a recording scan function and a defn with fake builds. No engine."""
import dataclasses

from scripts.skilllab.contract import CellResult, FightResult, ScanResult, Setup


WEIGHTED_US = (1.5, 0.75)     # what a fight reports when its Setup asked for weighted firing


def fight(ticks=100, outcome="side0", fus=(0.5, 0.25), wus=None):
    return FightResult(outcome=outcome, margin=0.1, strength_left=(0.5, 0.2), survivors=(8, 2), heads=(16, 16),
                       ticks=ticks, first_contact_tick=1, firing=[(0, 1, 1), (5, 1, 0)],
                       firing_unit_seconds=fus, weighted=None if wus is None else [(0, 1.0, 1.0)],
                       weighted_unit_seconds=wus)


def make_scan(size, enemy_from, enemy_to, beats, stalled=0, ticks=100, wus=None):
    """One cell per enemy count with two fights each; the first `stalled` fights of the first cell stall."""
    cells = []
    for i, n in enumerate(range(enemy_from, enemy_to + 1)):
        outs = ["stalemate" if (i == 0 and k < stalled) else "side0" for k in range(2)]
        cells.append(CellResult(enemy_heads=n, fights=[fight(ticks, o, wus=wus) for o in outs],
                                mean_margin=0.1, won=beats is not None and n <= beats))
    return ScanResult(size=size, cells=cells, beats=beats, loses_to=None if beats is None else beats + 1,
                      win_margin=0.05)


class FakeScan:
    """Callable like scan.scan. results: {(cell_label, policy_or_None): beats or (beats, stalled)}; default beats 15.
    Calls the build once (enemy_from, False) and records the Setup it returns."""

    def __init__(self, results=None, default=15):
        self.results, self.default, self.calls = dict(results or {}), default, []

    def __call__(self, build, size, enemy_from, enemy_to, replicates=10, **kw):
        setup = build(enemy_from, False)
        label = setup.unit_types["_cell"]
        policy = setup.settings.get("OM_TP_TARGET_POLICY")
        self.calls.append(dict(label=label, weighted=setup.weighted, policy=policy, size=size, enemy_from=enemy_from, enemy_to=enemy_to,
                               replicates=replicates, setup=setup, kw=kw))
        got = self.results.get((label, policy), self.default)
        beats, stalled = got if isinstance(got, tuple) else (got, 0)
        return make_scan(size, enemy_from, enemy_to, beats, stalled, wus=WEIGHTED_US if setup.weighted else None)


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
