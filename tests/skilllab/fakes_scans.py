"""Hand-built ProfileMap/ScanResult objects for the profile and conditions-all tests. No engine."""
from scripts.skilllab.contract import CellResult, FightResult, ScanResult
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
                       ticks=ticks, first_contact_tick=0, firing=[], firing_unit_seconds=(1 + adv, 1 - adv))


def cell(heads, fights, won=True):
    return CellResult(enemy_heads=heads, fights=list(fights), mean_margin=0.0, won=won)


def scan_of(size, beats, cells):
    return ScanResult(size=size, cells=list(cells), beats=beats,
                      loses_to=None if beats is None else beats + 1, win_margin=0.05)


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
