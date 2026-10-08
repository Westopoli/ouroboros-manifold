"""Lane F, piece W8d (Windows export preset).

Spec: docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md W8d ("export_presets.cfg: W6 adds Windows
x86_64 beside Linux and macOS; test: a Windows export builds headless"). Story S-139, rule R-139-01 (the game ships
for Windows, macOS and Linux with the same sim). One depot per OS needs one preset per OS.

Fenced: builders never edit this file.
"""
import configparser
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "export_presets.cfg"
TEMPLATES = Path.home() / ".local/share/godot/export_templates/4.6.3.stable"
GODOT = Path.home() / ".local/bin/godot.real"


def _presets() -> dict[str, dict[str, str]]:
    cp = configparser.RawConfigParser(strict=False)
    cp.optionxform = str
    cp.read(CFG)
    out = {}
    for sec in cp.sections():
        if sec.startswith("preset.") and not sec.endswith(".options"):
            out[cp[sec]["name"].strip('"')] = dict(cp[sec])
    return out


def test_control_linux_and_macos_presets_stay():
    """CONTROL: the two presets that exist today are still there, so a missing Windows one is the finding."""
    names = _presets()
    assert "Linux" in names and "macOS" in names, f"existing presets lost: {sorted(names)}"


def test_windows_desktop_x86_64_preset_exists():
    """W8d: a preset on platform 'Windows Desktop' with architecture x86_64 and a path under dist/windows."""
    names = _presets()
    win = [p for p in names.values() if p.get("platform", "").strip('"') == "Windows Desktop"]
    assert win, f"no Windows Desktop preset in export_presets.cfg (presets: {sorted(names)})"
    text = CFG.read_text()
    assert 'binary_format/architecture="x86_64"' in text.split('platform="Windows Desktop"', 1)[-1], \
        "the Windows preset is not x86_64"
    assert "dist/windows" in win[0].get("export_path", ""), "the Windows preset exports outside dist/windows"
    assert win[0].get("runnable", "").strip() == "true"


@pytest.mark.skipif(not (TEMPLATES.exists() and GODOT.exists()), reason="export templates 4.6.3 or godot.real missing (Westley step T17)")
def test_windows_export_builds_headless(tmp_path):
    """W8d done-when: `godot --headless --export-release "Windows Desktop"` builds an exe."""
    names = _presets()
    win = next((n for n, p in names.items() if p.get("platform", "").strip('"') == "Windows Desktop"), None)
    assert win, "no Windows Desktop preset to export"
    out = tmp_path / "om.exe"
    r = subprocess.run([str(GODOT), "--headless", "--path", str(ROOT), "--export-release", win, str(out)],
                       capture_output=True, text=True, timeout=900)
    assert out.exists(), "the Windows export wrote no exe:\n" + (r.stdout + r.stderr)[-800:]
    assert out.read_bytes()[:2] == b"MZ"
