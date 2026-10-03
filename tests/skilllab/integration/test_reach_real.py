# spec: R-096-04 layer reach by unit type - om_roster_set_reach through a fight setup, real library
"""A custom type registered by fight() with "reach": (0, 2) reads back (0, 2); a built-in type is unchanged."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402


class _Spy(engine.Engine):
    """Reads the reach of the first custom type (id 100) and of Vanguard just before the world is freed."""
    def free_world(self, w):
        self.read = {"custom": self.profile_reach(w, 100), "vanguard": self.profile_reach(w, self.type_id("Vanguard"))}
        super().free_world(w)


def _setup(types):
    g = lambda side, unit, x: Group(side=side, unit=unit, count=1, formation="line", x=x, y=400.0, facing_deg=0.0,
                                    layer=0, order="attack_move", params={"spacing": 30.0})
    return Setup(groups=(g(0, "Tall", 300.0), g(1, "Vanguard", 900.0)), unit_types=types, max_ticks=5)


def test_custom_type_reads_back_its_reach_and_a_builtin_is_unchanged():
    spy = _Spy()
    fight.fight(_setup({"Tall": {"base": "Vanguard", "scale": {}, "set": {}, "reach": (0, 2)}}), 0, False, engine=spy)
    assert spy.read == {"custom": (0, 2), "vanguard": (0, 0)}


def test_full_stats_entry_reads_back_its_reach_too():
    spy = _Spy()
    w = spy.new_world(0)
    try:
        stats = dict(spy.type_stats(w, spy.type_id("Vanguard")), role="Vanguard", ability_id=0, reach=(1, 2))
    finally:
        super(_Spy, spy).free_world(w)
    fight.fight(_setup({"Tall": stats}), 0, False, engine=spy)
    assert spy.read["custom"] == (1, 2) and spy.read["vanguard"] == (0, 0)


def test_no_reach_key_leaves_the_custom_type_at_the_library_default():
    spy = _Spy()
    fight.fight(_setup({"Tall": {"base": "Vanguard", "scale": {"speed": 1.5}, "set": {}}}), 0, False, engine=spy)
    assert spy.read["custom"] == (0, 0)
