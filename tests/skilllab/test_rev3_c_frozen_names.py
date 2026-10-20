# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (test T2 "Frozen names": "C adds no_reach_stall and decided_one_way_reach"); Architect ruling 2026-10-20 on the names list; piece LAB-REV3-C
"""LAB-REV3-C, the frozen names: contract.FROZEN_NAMES (a tuple of strings, created by piece A as ("inert_knob", "category")) gains
"no_reach_stall" and "decided_one_way_reach" in this piece (adding is fine; renaming or removing is a contract change). The verdict strings
fight() writes are those entries, read from the constant by the code, so a rename moves code and artifact together or fails here.

If piece A's FROZEN_NAMES is not on the base, the tests fail on the missing names (getattr with a default), not on an import.
BUILDER CONTRACT: both strings are in contract.FROZEN_NAMES after A's two (A's entries keep their positions: these tests pin membership
and A's first two positions, never the length); FightResult.verdict (see test_rev3_c_stall.py) is exactly one of them or None."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_rev3_c_support import DECIDED, STALL, G, kill, run  # noqa: E402
from scripts.skilllab import contract  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")


def frozen():
    return getattr(contract, "FROZEN_NAMES", ())


def test_both_new_names_are_frozen_names_and_a_keeps_its_two_first():
    """Red today: FROZEN_NAMES is missing on the base (A's piece) or lacks both names."""
    names = frozen()
    assert STALL in names and DECIDED in names, "contract.FROZEN_NAMES = %r" % (names,)
    assert tuple(names[:2]) == ("inert_knob", "category")
    assert isinstance(names, tuple) and all(isinstance(n, str) for n in names)


def test_the_stall_verdict_the_fight_writes_is_a_frozen_name():
    """The stall fight's verdict equals the FROZEN_NAMES entry (looked up in the constant, not repeated as a literal)."""
    r, _f = run([G(0, "Vanguard", 2, 0), G(1, "Vanguard", 2, 2)], cap=100)
    entry = next((n for n in frozen() if n == getattr(r, "verdict", None)), None)
    assert entry is not None, "verdict %r is not in FROZEN_NAMES %r (outcome %s, ticks %d)" % (getattr(r, "verdict", None), frozen(), r.outcome, r.ticks)
    assert entry == STALL


def test_the_decided_verdict_the_fight_writes_is_a_frozen_name():
    """The decided fight's verdict equals the FROZEN_NAMES entry."""
    r, _f = run([G(0, "Interceptor", 1, 0), G(1, "Vanguard", 1, 2)], cap=100)
    entry = next((n for n in frozen() if n == getattr(r, "verdict", None)), None)
    assert entry is not None, "verdict %r is not in FROZEN_NAMES %r (outcome %s, ticks %d)" % (getattr(r, "verdict", None), frozen(), r.outcome, r.ticks)
    assert entry == DECIDED


def test_control_an_ordinary_win_has_no_verdict():
    """Green today: a win by elimination carries no verdict (None), so the constant is not consulted for it."""
    r, _f = run([G(0, "Interceptor", 1, 0), G(1, "Raider", 1, 1)], cap=100, events={9: [kill(1, 0)]})
    assert r.outcome == "side0" and getattr(r, "verdict", None) is None
