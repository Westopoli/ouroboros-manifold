# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md addendum 24 A60 (and A54); E-16 S-106; R-106-05 ambient field
"""A60: the live scenes/galaxy view carries the ambient particle field (the port of
scenes/mockups/galaxy/legacy_ambient_rig.gd), and the quality tier thins it.

  tier 0 full               raymarch shells, full ambient field
  tier 1 stand-in           stand-in shells, full ambient field (same amount as tier 0)
  tier 2 fewer particles    stand-in shells, ambient field at HALF the amount of tiers 0 and 1
                            (provisional value, A60)

The field is the subtree under the node named "AmbientRig" (name chosen by this test; the porting
unit must use it). Its amount is read from the live nodes: the sum of `amount` over every
GPUParticles3D / CPUParticles3D under it, and each emitter's own `amount`; nothing here hard-codes
the rig's particle counts, so the port may retune them. Reuses the probe and boot helper of
tests/qa/desktop/test_galaxy_quality.py (real display, throwaway XDG_DATA_HOME).

Tolerance: tier 2 / tier 0 must be 0.5 within 0.02 (integer rounding per emitter; the mockup rig's
emitters are all even, so the expected error is 0).
Positive controls: tier 0 has a non-zero field (so a ratio means something); the field is read from
the AmbientRig subtree and the whole view carries no other particles at tier 0 (a field living
elsewhere is not counted and fails); tier 1 equals tier 0 (the field thins only at tier 2).
"""
from __future__ import annotations

import pytest

from test_galaxy_quality import _boot_probe, _shell_kinds

HALF = 0.5
TOLERANCE = 0.02


@pytest.fixture(scope="module")
def probes():
    return {tier: _boot_probe(tier) for tier in (0, 1, 2)}


@pytest.mark.parametrize("tier", [0, 1])
def test_full_tiers_carry_an_ambient_field(probes, tier):
    before = probes[tier]["before"]
    assert before["ambient_particles"] > 0, (
        "tier %d: the live galaxy view has no ambient particle field (no particles under a node named AmbientRig; "
        "view-wide particle total %d)" % (tier, before["particles"]))
    assert all(a > 0 for a in before["emitter_amounts"]), "tier %d has an emitter with no particles" % tier


def test_tier0_and_tier1_carry_the_same_field(probes):
    p0, p1 = probes[0]["before"]["ambient_particles"], probes[1]["before"]["ambient_particles"]
    assert p0 > 0, "tier 0 carries no ambient field (control: there must be one to compare)"
    assert p1 == p0, "tier 1 changes the ambient field (%d vs %d); it changes only the shells" % (p1, p0)


def test_tier2_has_stand_in_shells_and_half_the_field(probes):
    b0, b2 = probes[0]["before"], probes[2]["before"]
    assert b0["ambient_particles"] > 0, "tier 0 carries no ambient field (control: there must be one to halve)"
    assert _shell_kinds(b2) == {("SphereMesh", "StandardMaterial3D")}, "tier 2 shells are %s, expected the stand-in" % _shell_kinds(b2)
    ratio = b2["ambient_particles"] / b0["ambient_particles"]
    assert abs(ratio - HALF) <= TOLERANCE, (
        "tier 2 ambient field is %d particles against tier 0's %d: ratio %.3f, expected %.2f within %.2f"
        % (b2["ambient_particles"], b0["ambient_particles"], ratio, HALF, TOLERANCE))


def test_tier2_never_loses_an_emitter_or_drops_below_half(probes):
    b0, b2 = probes[0]["before"], probes[2]["before"]
    assert b0["emitter_amounts"], "tier 0 has no particle emitters (control)"
    assert len(b2["emitter_amounts"]) == len(b0["emitter_amounts"]), (
        "tier 2 has %d emitters, tier 0 has %d; tier 2 thins amounts, it does not delete emitters"
        % (len(b2["emitter_amounts"]), len(b0["emitter_amounts"])))
    assert all(a >= 1 for a in b2["emitter_amounts"]), "tier 2 has an emitter with no particles: %s" % b2["emitter_amounts"]
    assert b2["ambient_particles"] >= (HALF - TOLERANCE) * b0["ambient_particles"], "tier 2 is below half the field"
    assert b2["ambient_particles"] <= b0["ambient_particles"], "tier 2 carries more particles than tier 0"


def test_the_field_is_only_the_ambient_rig(probes):
    # Control for the counting: at tier 0 every particle in the view is under AmbientRig, so the
    # AmbientRig reading really is the field and not a slice of it.
    b0 = probes[0]["before"]
    assert b0["ambient_particles"] > 0, "no ambient field (control)"
    assert b0["particles"] == b0["ambient_particles"], (
        "particles exist in the view outside the AmbientRig node (%d vs %d under it)" % (b0["particles"], b0["ambient_particles"]))


@pytest.mark.parametrize("tier", [0, 1, 2])
def test_the_field_is_not_changed_by_slow_frames(probes, tier):
    p = probes[tier]
    assert p["before"]["ambient_particles"] > 0, "no ambient field at tier %d (control)" % tier
    assert p["after"]["ambient_particles"] == p["before"]["ambient_particles"], (
        "the ambient field changed under slow frames at tier %d: %d -> %d"
        % (tier, p["before"]["ambient_particles"], p["after"]["ambient_particles"]))
