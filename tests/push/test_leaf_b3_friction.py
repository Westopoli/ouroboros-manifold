# spec: docs/northstar/plans/push/specs/b3-friction.md::Acceptance criteria::AC-1
"""Adapter test, common brief 2026-09-22 line 9. Runs the piece's real
acceptance node ids through pytest.main and asserts exit 0."""
import pytest

ACCEPTANCE = [
    "tests/csim/test_E05_S040_empires_fracture.py",
    "tests/csim/test_E05_S041_hostile_borders_wear_you_down.py",
]


def test_leaf_b3_friction_acceptance_green():
    assert pytest.main(["-q", "-p", "no:cacheprovider", *ACCEPTANCE]) == 0
