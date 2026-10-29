# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-12 (asymmetric plays, real engine); LAB-REV2-L2 (Q-LAB-03)
"""A 4-unit-per-side fight for each role pair runs to an outcome, and two runs of the same fight are identical."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402

ROLES = ("blob", "line", "skilled", "counter")
PAIRS = [(a, b) for a in ROLES for b in ROLES if not (a == b == "counter")]
OUTCOMES = {"side0", "side1", "draw", "cap"}   # LAB-REV2-L2 (Q-LAB-03): stalemate is retired; a cap is a defect, tolerated here as the run-and-equal check


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


@pytest.mark.parametrize("role0,role1", PAIRS)
def test_role_pair_fight_runs_and_is_deterministic(library, role0, role1):
    """4 Vanguard per side: the fight ends in a named outcome with heads (4, 4); a second run is equal in every field."""
    build = asym_play(4, Side(role0), Side(role1))
    first = fight.fight(build(4, False), 0, False)
    second = fight.fight(build(4, False), 0, False)
    assert first.outcome in OUTCOMES
    assert first.heads == (4, 4) and first.ticks > 0
    assert first == second


def test_mixed_layered_pair_fight_runs_and_is_deterministic(library):
    """Mixed Vanguard/Warden layered side against a blob, swapped spawn order too: runs to an outcome, equal across runs."""
    mix = (("Vanguard", 1), ("Warden", 1))
    build = asym_play(4, Side("skilled", mix=mix, arrangement="layered"), Side("blob"))
    for swap in (False, True):
        a = fight.fight(build(4, swap), 1, swap)
        b = fight.fight(build(4, swap), 1, swap)
        assert a.outcome in OUTCOMES and a.heads == (4, 4)
        assert a == b
