# spec: docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md G-G1; E-16 R-107-01, R-107-02; A48-1, A48-2 (vertical direction suspended by A56) (docs/northstar/plans/2026-10-01-architect-rulings-2.md)
"""Piece C5-G1: the live galaxy camera takes real mouse input and has focus_region(i).

Runs tests/qa/desktop/galaxy_camera_probe.gd on a real display (headless pins the window to 64x64,
below the 14 px pick radius). One test per named check; the probe documents each check.
"""
from __future__ import annotations

import pytest

from probe_runner import run_probe

CHECKS = ["no_idle_drift", "wheel_zoom", "drag_pan", "autonomous_flag", "autonomous_cancelled_by_input", "right_drag_orbit", "click_focus", "focus_region"]


@pytest.fixture(scope="module")
def results():
    return run_probe("res://tests/qa/desktop/galaxy_camera_probe.gd")


@pytest.mark.parametrize("check", CHECKS)
def test_galaxy_camera(results, check):
    row = results.get(check)
    assert row is not None, "probe printed no result for %s" % check
    assert row["ok"], row["msg"]
