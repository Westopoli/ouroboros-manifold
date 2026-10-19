"""Hand-built ProfileMap/ScanResult objects for the profile and conditions-all tests. No engine."""
import dataclasses

from scripts.skilllab.contract import CellResult, FightResult, ScanResult, Setup
from scripts.skilllab.evidence import Thresholds
from scripts.skilllab.profile import PROFILE_SKILLS, ProfileMap, subsets

FULL = frozenset(PROFILE_SKILLS)
EMPTY = frozenset()


def S(*names):
    return frozenset(names)


def by_size(*vals):
    """beats as a function of how many skills the subset holds: vals[len(subset)]."""
    return lambda s: vals[len(s)]


def thresholds(**over):
    """Placeholder marks for tests only (not Westley's); every field explicit."""
    base = dict(
        c0_tolerance_units=1, c1_min_firing_advantage=0.25, c1_map_share=0.5, c2_rank_agreement=0.8,
        c2_off_trend_margin=0.12, c2_off_trend_share=0.25, c3_stack_gain=0.0, c4_max_share=1.0,
        c5_min_loss=0.0, c6_return_share=0.0, c6_map_share=0.0, c8_map_share=0.0,
        c7_ceiling_targets=(1.0, 2.0), c9_length_bounds_ticks=(0, 1000000), guard_tolerance_units=0)
    base.update(over)
    return Thresholds(**base)


def fight(adv=0.0, ticks=100):
    """One fight whose firing advantage is exactly adv."""
    return FightResult(outcome="side0", margin=0.0, strength_left=(0.0, 0.0), survivors=(0, 0), heads=(0, 0),
                       ticks=ticks, first_contact_tick=0, firing=[], firing_unit_seconds=(1 + adv, 1 - adv),
                       firing_window=(1 + adv, 1 - adv))     # window == whole: the default basis is the window (TD-LAB-REV2-L5-basis)


def cell(heads, fights, won=True):
    return CellResult(enemy_heads=heads, fights=list(fights), mean_margin=0.0, won=won)


def scan_of(size, beats, cells, ceiling_hit=False, multi_flip=False):
    """LAB-REV2-L4: ScanResult has no win_margin and carries ceiling_hit and multi_flip. Written to build on both sides of L4's
    contract change (it passes win_margin only while the field exists), so other pieces' tests that use it stay green."""
    names = {f.name for f in dataclasses.fields(ScanResult)}
    extra = {}
    if "win_margin" in names:
        extra["win_margin"] = 0.05
    if "ceiling_hit" in names:
        extra["ceiling_hit"], extra["multi_flip"] = ceiling_hit, multi_flip
    return ScanResult(size=size, cells=list(cells), beats=beats,
                      loses_to=None if beats is None or ceiling_hit else beats + 1, **extra)


def make_map(map_id="m", base=None, over=None, size=10, kind="open", offers=PROFILE_SKILLS,
             counters=None, skilled_adv=0.5, mirror_adv=0.0, full_ticks=(100,), other_ticks=100):
    """base: callable subset -> beats (default by_size(10,20,40,80,160,320)); over: {subset: beats or None}.
    The mirror scan holds cells size-1..size+1 (won below size) so C0 can read it; every other scan one cell at size."""
    base = base or by_size(10, 20, 40, 80, 160, 320)
    over = over or {}
    scans = {}
    for s in subsets():
        b = over[s] if s in over else base(s)
        if s == EMPTY:
            cells = [cell(h, [fight(mirror_adv, other_ticks)], won=h < size) for h in (size - 1, size, size + 1)]
        else:
            if isinstance(skilled_adv, dict):
                adv = skilled_adv.get(next(iter(s)), 0.5) if len(s) == 1 else 0.5
            else:
                adv = skilled_adv
            ticks = full_ticks if s == FULL else (other_ticks,)
            cells = [cell(size, [fight(adv, t) for t in ticks])]
        scans[s] = scan_of(size, b, cells)
    cs = {}
    for k, v in (counters or {}).items():
        cs[k] = scan_of(size, v, [cell(size, [fight(0.0)])])
    return ProfileMap(map_id=map_id, kind=kind, offers=frozenset(offers), size=size, scans=scans, counters=cs)


# ---- LAB-REV2-L4: fakes for the sweep and smoke tests. No engine, no map. -------------------------------------------------

def _fr(outcome, enemy_heads, firing=((0, 16, 16),), fus=(1.0, 1.0), margin=None, survivors=None):
    """A FightResult with the new fields left at their decision-1 defaults; side0 wins, side1 wins, draw or cap."""
    won0 = outcome == "side0"
    if survivors is None:
        survivors = (16, 16) if outcome == "cap" else ((8, 0) if won0 else (0, 8)) if outcome in ("side0", "side1") else (0, 0)
    return FightResult(outcome=outcome, margin=margin if margin is not None else 0.5 if won0 else -0.5 if outcome == "side1" else 0.0,
                       strength_left=(0.5, 0.0) if won0 else (0.0, 0.5), survivors=survivors, heads=(16, enemy_heads),
                       ticks=100, first_contact_tick=0, firing=list(firing), firing_unit_seconds=fus,
                       winner="side0" if won0 else "side1" if outcome == "side1" else None)


def fake_builds(refuse=None, log=None):
    """builds(play, role, layout) -> BuildFn, the sweep's seam (test_sweep.py header). The Setup carries what the sweep put on it;
    unit_types holds the cell's identity so a fight_fn can read it. `refuse`: {(play, role): prefight word}. `log`: appended
    (play, role) per builds call. build.labels['prefight'] is set at call time, as scenes.placed_scene does."""
    refuse = refuse or {}

    def builds(play, role, layout):
        if log is not None:
            log.append((play, role))
        word = refuse.get((play, role), "ok")

        def build(enemy_heads, swap):
            build.labels["prefight"] = word
            return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap, "_play": play, "_role": role})
        build.labels = {"placement_shift": 0.0, "prefight": None}
        return build
    return builds


class ScriptedFight:
    """fight_fn(setup, seed, swap): side0 wins when enemy_heads <= be_of(setup), else side1 wins. be_of(setup) -> int, or None
    for 'always lost'; `result_of`, when given, replaces the result entirely. Records every call as a dict."""

    def __init__(self, be_of=None, result_of=None):
        self.be_of, self.result_of, self.calls = be_of, result_of, []

    def __call__(self, setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        self.calls.append(dict(setup=setup, seed=seed, swap=swap, enemy=enemy, role=setup.unit_types["_role"],
                               play=setup.unit_types["_play"], settings=dict(setup.settings), states=setup.states,
                               key=(setup.unit_types["_play"], setup.unit_types["_role"], tuple(sorted(setup.settings.items())),
                                    enemy, seed, swap)))
        if self.result_of is not None:
            return self.result_of(setup, seed, swap)
        be = self.be_of(setup)
        return _fr("side0" if be is not None and enemy <= be else "side1", enemy)


class FakePool:
    """Stands in for pool.FightPool: map(jobs) fights each (setup, seed, swap) job through `fight_fn` in order."""
    instances = []

    def __init__(self, workers, library_path=None, lean=False):
        self.workers, self.lean, self.fight_fn, self.maps = workers, lean, FakePool.fight_fn, []
        FakePool.instances.append(self)

    fight_fn = None

    def map(self, jobs):
        jobs = list(jobs)
        self.maps.append(len(jobs))
        return [self.fight_fn(*job) for job in jobs]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
