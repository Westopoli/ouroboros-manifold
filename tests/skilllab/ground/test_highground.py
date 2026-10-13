# spec: docs/northstar/plans/2026-10-05-proto-highground-spec.md::The sweep - height rules and climb times
"""The height rules and climb times of the high-ground instrument, as data (no engine).
Reading: HEIGHT_RULES[k] is a dict; this file looks for the keys reach_up, reach_down (layers), range_down, range_up,
damage_down, damage_up (multipliers; 1.0 when absent is NOT assumed: each must be present for H0 to H4).
'Down' means the firer is higher than the target; 'up' means the firer is lower."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.skilllab.ground import highground as HG
except Exception as e:  # noqa: BLE001
    HG, HG_ERR = None, e

KEYS = ("reach_up", "reach_down", "range_down", "range_up", "damage_down", "damage_up")


def _rule(name):
    assert HG is not None, "scripts/skilllab/ground/highground.py is missing or fails to import: %r" % (HG_ERR,)
    assert hasattr(HG, "HEIGHT_RULES"), "scripts/skilllab/ground/highground.py has no HEIGHT_RULES"
    assert name in HG.HEIGHT_RULES, "HEIGHT_RULES has no %s" % name
    r = HG.HEIGHT_RULES[name]
    for k in KEYS:
        assert k in r, "HEIGHT_RULES[%r] has no key %r" % (name, k)
    return r


def _is(r, **want):
    for k in KEYS:
        assert r[k] == pytest.approx(want.get(k, 1.0 if k.startswith(("range", "damage")) else 0)), (k, r[k])


def test_h0_reach_zero_both_ways():
    r = _rule("H0")
    assert r["reach_up"] == 0 and r["reach_down"] == 0


def test_h1_reach_one_both_ways_multipliers_one():
    _is(_rule("H1"), reach_up=1, reach_down=1)


def test_h2_range_down_125_up_075_damage_one():
    _is(_rule("H2"), reach_up=1, reach_down=1, range_down=1.25, range_up=0.75)


def test_h3_damage_down_125_up_075_range_one():
    _is(_rule("H3"), reach_up=1, reach_down=1, damage_down=1.25, damage_up=0.75)


def test_h4_both():
    _is(_rule("H4"), reach_up=1, reach_down=1, range_down=1.25, range_up=0.75, damage_down=1.25, damage_up=0.75)


def test_h5_absent_or_marked_not_expressed():
    _rule("H0")
    if "H5" in HG.HEIGHT_RULES:
        r = HG.HEIGHT_RULES["H5"]
        assert r is None or r.get("not_expressed") or all(k in r for k in KEYS)


def test_climb_seconds():
    assert HG is not None, "scripts/skilllab/ground/highground.py is missing or fails to import: %r" % (HG_ERR,)
    assert HG.CLIMB_SECONDS == (2, 4, 8, 15)
