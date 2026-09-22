# spec: docs/northstar/plans/push/specs/b2-collision.md::Acceptance criteria::AC-1
"""Adapter test, common brief 2026-09-22 line 9. Runs the piece's real
acceptance node ids through pytest.main and asserts exit 0."""
import pytest

ACCEPTANCE = [
    "tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py",
    "tests/csim/test_E05_S039_wiring.py",
]


def test_leaf_b2_collision_acceptance_green():
    assert pytest.main(["-q", "-p", "no:cacheprovider", "-k", "not R_039_05", *ACCEPTANCE]) == 0
