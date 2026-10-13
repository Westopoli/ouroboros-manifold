# spec: docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md G-G3; E-16 R-106-03, R-107-05
"""Piece C5-G3: faction name labels in Overview, label lifecycle on conquest, system hover.

Runs tests/qa/desktop/galaxy_labels_probe.gd on a real display. One test per named check.
"""
from __future__ import annotations

import pytest

from probe_runner import run_probe

CHECKS = ["labels_overview", "labels_at_centroid", "labels_follow_conquest", "hover_system", "hover_clear", "unknown_faction"]


@pytest.fixture(scope="module")
def results():
    return run_probe("res://tests/qa/desktop/galaxy_labels_probe.gd")


@pytest.mark.parametrize("check", CHECKS)
def test_galaxy_labels(results, check):
    row = results.get(check)
    assert row is not None, "probe printed no result for %s" % check
    assert row["ok"], row["msg"]
