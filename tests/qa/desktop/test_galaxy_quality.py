# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md addendum 23 A54; E-16 S-106 (register Q-106-04 closed)
"""A54: galaxy quality is a manual setting. Each value changes what the galaxy view draws, and the
game never changes the value itself.

Real display (Xvfb, software GL, Compatibility renderer: the case where today's code switches to the
stand-in on its own). Boots tests/qa/desktop/galaxy_quality_probe.gd once per stored tier, on a
settings.cfg fixture in a throwaway XDG_DATA_HOME (never the player's), and reads the live galaxy view.

What each value draws (observable, structural, not pixels):
  tier 0 full               raymarch box + ShaderMaterial on forward_plus/mobile; the stand-in sphere on Compatibility (TD-VG-B-8)
  tier 1 stand-in           faction shells are SphereMesh + StandardMaterial3D
  tier 2 fewer particles    stand-in shells, the same as tier 1 (A60). Its reduced ambient field is
                            tested in tests/qa/desktop/test_galaxy_ambient.py, which waits on the
                            ambient-rig port unit.
Read at build (A60): the view reads the setting when it is built. The probe stores a different tier
after the view is built; the same view keeps its tier and shells, a view built afterwards takes the new one.
Never automatic: the probe stalls 130 frames by 60 ms (mean frame far over any step-down threshold);
qa_state quality_tier, the stored value, the settings file and what is drawn must be unchanged.
Positive controls: the stall really happened (mean frame >= 50 ms); tier 0 and tier 1 differ in what
they draw (a view that ignores the setting fails one of them); the draw is read after the stall as well.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

import pytest

from daemon_client import REPO_ROOT, find_godot

PROBE_SCRIPT = "res://tests/qa/desktop/galaxy_quality_probe.gd"
XVFB_SCREEN = "1920x1080x24"
# _boot_probe passes --rendering-driver opengl3, so the probe runs gl_compatibility. The probe does not
# expose the rendering method, so this constant mirrors that flag. Rev 4 lane B (B3b) and the Architect
# ruling of 2026-10-08 (TD-VG-B-8): on Compatibility the stand-in replaces the raymarch shell.
RENDERING_METHOD = "gl_compatibility"
RAYMARCH = {("BoxMesh", "ShaderMaterial")}
STAND_IN = {("SphereMesh", "StandardMaterial3D")}


def _boot_probe(tier: int) -> dict:
    scratch = Path(tempfile.mkdtemp(prefix="qa_galaxy_quality."))
    try:
        user_dir = scratch / "xdg" / "data"
        user_dir.mkdir(parents=True)
        (user_dir / "settings.cfg").write_text("[display]\ngalaxy_quality=%d\n" % tier)
        (scratch / "saves").mkdir()
        env = dict(os.environ)
        for var in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
            env.pop(var, None)
        env["XDG_DATA_HOME"] = str(scratch / "xdg")
        env["OM_SAVE_DIR"] = str(scratch / "saves")
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        env["GALLIUM_DRIVER"] = "llvmpipe"
        cmd = [
            "xvfb-run", "-a", "-s", "-screen 0 %s" % XVFB_SCREEN,
            find_godot(), "--path", str(REPO_ROOT),
            "--display-driver", "x11", "--rendering-driver", "opengl3",
            "--quit-after", "20000", "--script", PROBE_SCRIPT,
        ]
        proc = subprocess.Popen(cmd, cwd=str(scratch), env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, start_new_session=True, text=True)
        try:
            out, _ = proc.communicate(timeout=240)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            out, _ = proc.communicate()
            pytest.fail("quality probe timed out:\n" + out[-800:])
        finally:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        for line in out.splitlines():
            if line.startswith("PROBE "):
                return json.loads(line[6:])
        pytest.fail("no PROBE line from the quality child:\n" + out[-1200:])
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


@pytest.fixture(scope="module")
def probes():
    return {tier: _boot_probe(tier) for tier in (0, 1, 2)}


def _shell_kinds(snapshot: dict) -> set:
    return {tuple(s) for s in snapshot["shells"]}


@pytest.mark.parametrize("tier", [0, 1, 2])
def test_qa_state_reports_the_stored_tier(probes, tier):
    before = probes[tier]["before"]
    assert before["stored"] == tier, "stored galaxy_quality=%d loaded as %r" % (tier, before["stored"])
    assert before["quality_tier"] == tier, (
        "stored galaxy_quality=%d but qa_state quality_tier is %r" % (tier, before["quality_tier"]))


def test_tier0_draws_raymarch_shells(probes):
    shells = _shell_kinds(probes[0]["before"])
    assert shells, "tier 0 drew no faction shells at all (control)"
    if RENDERING_METHOD == "gl_compatibility":
        # See also: TD-VG-B-8 in docs/northstar/plans/push_ledger_2026-09-22.md
        assert shells == STAND_IN, "tier 0 (full) on Compatibility shells are %s, expected the stand-in sphere + StandardMaterial3D" % shells
    else:
        assert shells == RAYMARCH, "tier 0 (full) shells are %s, expected the raymarch box + ShaderMaterial" % shells


def test_tier1_draws_stand_in_spheres(probes):
    shells = _shell_kinds(probes[1]["before"])
    assert shells, "tier 1 drew no faction shells at all (control)"
    assert shells == {("SphereMesh", "StandardMaterial3D")}, "tier 1 (stand-in) shells are %s, expected sphere + StandardMaterial3D" % shells


def test_tier2_draws_stand_in_spheres(probes):
    # A60: tier 2 = stand-in shells (the same as tier 1) plus a thinned ambient field.
    shells = _shell_kinds(probes[2]["before"])
    assert shells, "tier 2 drew no faction shells at all (control)"
    assert shells == {("SphereMesh", "StandardMaterial3D")}, "tier 2 shells are %s, expected sphere + StandardMaterial3D" % shells
    assert shells == _shell_kinds(probes[1]["before"]), "tier 2 and tier 1 draw different shells"


def test_tiers_draw_differently(probes):
    # Positive control for the shell checks above: a view that ignores the setting fails here too.
    # Tier 0 differs from tiers 1 and 2; tiers 1 and 2 share their shells (A60).
    shells = {t: tuple(sorted(_shell_kinds(probes[t]["before"]))) for t in (0, 1, 2)}
    if RENDERING_METHOD == "gl_compatibility":
        # Compatibility: tiers 0 and 1 both draw the stand-in; tier 2 differs by its half ambient field.
        assert shells[0] == shells[1], "tier 0 and tier 1 draw different shells on Compatibility: %s" % shells
        amb = {t: probes[t]["before"]["ambient_particles"] for t in (0, 1, 2)}
        assert amb[0] == amb[1] and amb[2] < amb[0], "tier 2 does not draw a thinner field than tiers 0/1: %s" % amb
    else:
        assert shells[0] != shells[1], "tier 0 and tier 1 draw the same shells: %s" % shells
    assert shells[1] == shells[2], "tier 1 and tier 2 draw different shells: %s" % shells


@pytest.mark.parametrize("tier", [0, 1, 2])
def test_view_reads_the_setting_at_build_only(probes, tier):
    probe = probes[tier]
    changed = probe["changed_to"]
    # Positive controls: the value really changed in the store, and differs from the view's tier.
    assert changed != tier, "probe did not pick a different tier (control)"
    assert probe["stored_after_change"] == changed, "the stored value did not change (%r); control failed" % probe["stored_after_change"]
    same = probe["same_view_after_change"]
    assert same["quality_tier"] == tier, (
        "a change to %d after the view was built re-applied to the open view: quality_tier %r (was %d)" % (changed, same["quality_tier"], tier))
    assert _shell_kinds(same) == _shell_kinds(probe["before"]), "the open view's shells changed after the stored value changed"
    rebuilt = probe["rebuilt_view"]
    assert rebuilt["quality_tier"] == changed, (
        "a view built after the change reports quality_tier %r, expected the new stored value %d" % (rebuilt["quality_tier"], changed))


@pytest.mark.parametrize("tier", [0, 1, 2])
def test_slow_frames_never_change_the_value(probes, tier):
    probe = probes[tier]
    # Positive control: the planted stall was real, far over any plausible step-down threshold.
    assert probe["mean_frame_ms"] >= 50, "the stall did not slow frames (mean %.1f ms)" % probe["mean_frame_ms"]
    before, after = probe["before"], probe["after"]
    assert before["quality_tier"] == tier, "tier %d did not start at its stored value (qa_state %r)" % (tier, before["quality_tier"])
    assert after["quality_tier"] == tier, (
        "after 130 frames at %.0f ms qa_state quality_tier went %r -> %r; the game must never change it"
        % (probe["mean_frame_ms"], before["quality_tier"], after["quality_tier"]))
    assert after["stored"] == before["stored"], "the stored value changed under slow frames: %r -> %r" % (before["stored"], after["stored"])
    assert after["cfg"] == before["cfg"], "settings.cfg was rewritten under slow frames"
    assert _shell_kinds(after) == _shell_kinds(before) and after["particles"] == before["particles"], (
        "what the galaxy draws changed under slow frames (%s/%d -> %s/%d)"
        % (_shell_kinds(before), before["particles"], _shell_kinds(after), after["particles"]))
