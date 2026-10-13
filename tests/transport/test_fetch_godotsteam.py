"""W6 Export (Steam wiring spec rev 5, docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md).

Proves the fetch script, the gitignore rules, the committed .gdextension, the
export presets and one headless Linux export. Session rule context: E-19
R-140-02..04 (a match needs the Steam addon in the shipped build). The
determinism rule is W7's, not tested here.

Interface assumed from the spec: `scripts/fetch_godotsteam.sh [local_zip]`
resolves the repo root as the parent of its own directory, verifies the pinned
sha256 (of the local zip when given, else of the download of URL), and unpacks
`addons/godotsteam/` under that root. The tests copy the script into a temp
tree so they never write into the checkout, except the export test, which needs
the real addon folder (gitignored by W6).

Red on origin/main: scripts/fetch_godotsteam.sh, the .gdextension,
export_presets.cfg and the .gitignore rules do not exist yet.
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/fetch_godotsteam.sh"
SCRATCH = Path.home() / ".claude/jobs/cb87e7a3/tmp"
ZIP = Path(os.environ.get("GODOTSTEAM_ZIP", SCRATCH / "godotsteam/gs.zip"))
PIN_SHA = "c1728b4bf330da851a00eaf64dab2e99c506018b1d9f529511b25d7fe7649e97"
PIN_URL = ("https://codeberg.org/godotsteam/godotsteam/releases/download/v4.23-gde/"
           "godotsteam-4.23-gdextension-plugin-4.4.zip")
GDEXT = "addons/godotsteam/godotsteam.gdextension"
LINUX_LIB = "addons/godotsteam/linux64/libgodotsteam.linux.template_release.x86_64.so"
GODOT = Path.home() / ".local/bin/godot.real"
TEMPLATES = Path.home() / ".local/share/godot/export_templates/4.6.3.stable"


def _tree(tmp_path):
    """A temp repo root holding a copy of the script (needs the script to exist)."""
    assert SCRIPT.is_file(), "W6: scripts/fetch_godotsteam.sh does not exist"
    (tmp_path / "scripts").mkdir()
    shutil.copy(SCRIPT, tmp_path / "scripts/fetch_godotsteam.sh")
    return tmp_path


def _run(root, *args, timeout=300):
    return subprocess.run(["bash", str(root / "scripts/fetch_godotsteam.sh"), *args],
                          cwd=root, capture_output=True, text=True, timeout=timeout)


def test_fetch_script_exists_and_pins_url_and_sha():
    """W6: the script exists, is executable, and carries the pinned URL and sha256."""
    assert SCRIPT.is_file(), "W6: scripts/fetch_godotsteam.sh does not exist"
    assert os.access(SCRIPT, os.X_OK)
    text = SCRIPT.read_text()
    assert PIN_URL in text
    assert PIN_SHA in text


def test_fetch_refuses_wrong_sha256(tmp_path):
    """W6: a local zip with the wrong hash is refused, nothing unpacked."""
    root = _tree(tmp_path)
    bad = root / "bad.zip"
    bad.write_bytes(b"not the pinned release")
    assert hashlib.sha256(bad.read_bytes()).hexdigest() != PIN_SHA
    r = _run(root, str(bad))
    assert r.returncode != 0, r.stdout + r.stderr
    assert not (root / "addons/godotsteam").exists()


def test_fetch_local_zip_unpacks_gdextension_and_linux_lib(tmp_path):
    """W6: after a real fetch from the pinned zip the .gdextension and the linux64 release lib exist."""
    if not ZIP.is_file():
        pytest.skip(f"pinned zip not at {ZIP}")
    assert hashlib.sha256(ZIP.read_bytes()).hexdigest() == PIN_SHA  # positive control on the fixture
    root = _tree(tmp_path)
    r = _run(root, str(ZIP))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (root / GDEXT).is_file()
    assert (root / LINUX_LIB).is_file()
    assert (root / "addons/godotsteam/osx/libsteam_api.dylib").is_file()


def _check_ignore(path):
    r = subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=ROOT)
    return r.returncode == 0


def test_gitignore_excludes_addon_but_keeps_gdextension():
    """W6: addons/godotsteam/* ignored, the .gdextension re-included."""
    lines = (ROOT / ".gitignore").read_text().splitlines()
    assert "addons/godotsteam/*" in lines
    assert "!addons/godotsteam/*.gdextension" in lines
    assert _check_ignore(LINUX_LIB)
    assert not _check_ignore(GDEXT)


def test_gitignore_still_ignores_so_elsewhere():
    """W6 positive control (passes today): *.so stays ignored outside the addon."""
    assert "*.so" in (ROOT / ".gitignore").read_text().splitlines()
    assert _check_ignore("build/libfoo.so")


def test_gdextension_committed_with_macos_dylib_dependency():
    """W6: the committed .gdextension declares libsteam_api.dylib under [dependencies] for macOS."""
    p = ROOT / GDEXT
    assert p.is_file(), "W6: addons/godotsteam/godotsteam.gdextension is not committed"
    text = p.read_text()
    assert "[dependencies]" in text
    deps = text.split("[dependencies]", 1)[1]
    assert any(l.startswith("macos") and "libsteam_api.dylib" in l for l in deps.splitlines())
    assert subprocess.run(["git", "ls-files", "--error-unmatch", GDEXT], cwd=ROOT,
                          capture_output=True).returncode == 0


def test_export_presets_linux_and_macos():
    """W6: export_presets.cfg has a Linux x86_64 preset named Linux and a macOS preset."""
    p = ROOT / "export_presets.cfg"
    assert p.is_file(), "W6: export_presets.cfg does not exist"
    text = p.read_text()
    assert 'name="Linux"' in text
    assert 'platform="Linux"' in text
    assert 'binary_format/architecture="x86_64"' in text
    assert 'platform="macOS"' in text


@pytest.mark.skipif(not (GODOT.exists() and (TEMPLATES / "linux_release.x86_64").exists()),
                    reason="Godot 4.6.3 or its export templates are not installed")
def test_headless_linux_export_builds():
    """W6: fetch the addon, import, then `--export-release Linux` produces a binary (needs T17 templates)."""
    assert SCRIPT.is_file(), "W6: scripts/fetch_godotsteam.sh does not exist"
    if not ZIP.is_file():
        pytest.skip(f"pinned zip not at {ZIP}")
    r = subprocess.run(["bash", str(SCRIPT), str(ZIP)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    out = SCRATCH / "export_w6" / "ouroboros.x86_64"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    subprocess.run([str(GODOT), "--headless", "--path", str(ROOT), "--import"],
                   capture_output=True, text=True, timeout=900)
    r = subprocess.run([str(GODOT), "--headless", "--path", str(ROOT),
                        "--export-release", "Linux", str(out)],
                       capture_output=True, text=True, timeout=1800)
    assert r.returncode == 0 and out.is_file(), r.stdout[-2000:] + r.stderr[-2000:]
