"""Inert-knob probe (rev 3 plan R6, test T2; defects D1, D10; ledger FINDING-lab-d1, FINDING-lab-d10): a knob at the band's extreme is
fought against its base at the sweep's coarse headcounts and seeds 0 and 1; it is inert on the play only when every row of
rows.fight_row is identical to its base row. survey() reports every point, inert() is the same fights stopping at the first difference."""
import dataclasses

from scripts.skilllab import contract, fight as fight_mod, rows, scan

SEEDS = (0, 1)


def coarse_heads():
    """The sweep's own first pass (scan.scan builds the same expression inline; there is no function to import)."""
    from scripts.skilllab import sweep      # here, not at import: sweep imports this module
    return sorted(set(range(sweep.ENEMY_FROM, sweep.ENEMY_TO + 1, scan.COARSE_STEP)) | {sweep.ENEMY_TO})


def _points(build, settings, heads, seeds, swap, fight_fn, base_settings, base_cache):
    """Yields ((heads, seed), {"differed", "base_cached", "invalid"}), heads major; invalid: True when the base or the moved fight broke a rule of the checker, None when either was not judged (and none broke one). base_cache, a dict the caller owns, holds the base row of (heads, seed)."""
    fight_fn = fight_fn or fight_mod.fight
    for h in coarse_heads() if heads is None else heads:
        for seed in seeds:
            setup = build(h, swap)
            cached = base_cache is not None and (h, seed) in base_cache
            if cached:
                base_row, base_invalid = base_cache[(h, seed)]
            else:
                base = fight_fn(dataclasses.replace(setup, settings={**setup.settings, **(base_settings or {})}), seed, swap)
                base_row, base_invalid = rows.fight_row(base), getattr(base, "invalid", False)
                if base_cache is not None:
                    base_cache[(h, seed)] = base_row, base_invalid
            moved = fight_fn(dataclasses.replace(setup, settings={**setup.settings, **settings}), seed, swap)
            yield (h, seed), {"differed": base_row != rows.fight_row(moved), "base_cached": cached, "invalid": contract.worst_invalid((base_invalid, getattr(moved, "invalid", False)))}


def survey(build, settings, heads=None, seeds=SEEDS, swap=False, fight_fn=None, base_settings=None, base_cache=None):
    """{(heads, seed): {"differed": bool, "base_cached": bool, "invalid": True | False | None}} for every point; never stops early. heads=None: the sweep's coarse list."""
    return dict(_points(build, settings, heads, seeds, swap, fight_fn, base_settings, base_cache))


def inert(build, settings, heads=None, seeds=SEEDS, swap=False, fight_fn=None, base_settings=None, base_cache=None):
    """True when no point differed (see survey); stops at the first differing row."""
    return not any(v["differed"] for _, v in _points(build, settings, heads, seeds, swap, fight_fn, base_settings, base_cache))
