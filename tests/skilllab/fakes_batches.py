"""Fakes for the batch tests: hand-built ScanResults, a recording scan function and a defn with fake builds. No engine."""
import dataclasses

from scripts.skilllab.contract import CellResult, FightResult, ScanResult, Setup


def fight(ticks=100, outcome="side0", fus=(0.5, 0.25)):
    return FightResult(outcome=outcome, margin=0.1, strength_left=(0.5, 0.2), survivors=(8, 2), heads=(16, 16),
                       ticks=ticks, first_contact_tick=1, firing=[(0, 1, 1), (5, 1, 0)],
                       firing_unit_seconds=fus)


def make_scan(size, enemy_from, enemy_to, beats, stalled=0, ticks=100):
    """One cell per enemy count with two fights each; the first `stalled` fights of the first cell stall."""
    cells = []
    for i, n in enumerate(range(enemy_from, enemy_to + 1)):
        outs = ["stalemate" if (i == 0 and k < stalled) else "side0" for k in range(2)]
        cells.append(CellResult(enemy_heads=n, fights=[fight(ticks, o) for o in outs],
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
        self.calls.append(dict(label=label, policy=policy, size=size, enemy_from=enemy_from, enemy_to=enemy_to,
                               replicates=replicates, setup=setup, kw=kw))
        got = self.results.get((label, policy), self.default)
        beats, stalled = got if isinstance(got, tuple) else (got, 0)
        return make_scan(size, enemy_from, enemy_to, beats, stalled)


def faked(defn):
    """The same BatchDef with a fake build per scannable cell; the build marks its Setup with the cell label."""
    cells = []
    for c in defn.cells:
        if c.build is None:
            cells.append(c)
            continue
        cells.append(dataclasses.replace(
            c, build=lambda enemy_heads, swap, _l=c.label: Setup(groups=(), unit_types={"_cell": _l})))
    return dataclasses.replace(defn, cells=tuple(cells))
