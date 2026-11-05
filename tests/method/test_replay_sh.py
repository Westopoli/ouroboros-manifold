# spec: docs/northstar/plans/cascades/lab-stage3/spec.md::Acceptance criteria::AC-12
# Rule pins: none (lab harness story H-063)
"""lab-stage3 leaf-04, criteria 12 and 13 (spec lines 42 and 43): `scripts/replay.sh <fight.json> [--shots <dir>] [--dry-run]` opens the lab fight replay on Linux and
macOS, and the README tells how ("Watch a lab fight").

12: Godot is found, first match wins: `$GODOT`, `godot` on `PATH`, `~/.local/bin/godot.real`, `/Applications/Godot.app/Contents/MacOS/Godot`. It runs
    `<godot> --headless --import --path <repo>` once per checkout (marker `.godot/replay_imported`), then `<godot> --path <repo> --windowed --resolution 1919x1080
    res://scenes/proto/fight_replay/fight_replay.tscn` with `OM_FIGHT` the fight's absolute path and, with `--shots`, `OM_SHOT_OUT` its absolute path. No `timeout`,
    `flock`, `setsid` or xdotool. `--dry-run` prints the import line and the launch line and runs nothing. `OM_UNAME` overrides `uname -s`. A missing fight file exits 2
    with the file named.
13: README.md has a "Watch a lab fight" section with the Linux line and the Mac line.

Godot is a fake script on a private PATH that logs its argv and the two environment variables; nothing real is launched. The script is run directly (its own shebang
and mode), from a scratch directory, so the repo it reports is the one it lives in and a relative fight path is made absolute against the caller's directory."""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REPLAY = ROOT / "scripts" / "replay.sh"
MARKER = ROOT / ".godot" / "replay_imported"
SCENE = "res://scenes/proto/fight_replay/fight_replay.tscn"
FAKE_GODOT = '#!/bin/bash\n{ echo "ARGV $*"; echo "OM_FIGHT=${OM_FIGHT-<unset>}"; echo "OM_SHOT_OUT=${OM_SHOT_OUT-<unset>}"; echo "--"; } >> "$FAKE_LOG"\nexit 0\n'
POISON = '#!/bin/bash\necho "POISON $(basename "$0")" >> "$FAKE_LOG"\nexit 1\n'
POISONED = ("timeout", "flock", "setsid", "xdotool")


def norm(text: str) -> str:
    """A printed command line with its shell quoting taken off (backslashes and quotes), so a path with a space reads the same however the script quotes it."""
    return text.replace("\\", "").replace("'", "").replace('"', "")


def _exe(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o755)
    return path


class Rig:
    """A scratch world: a fake godot on PATH, poison stand-ins for the tools the script must not use, a fight file, a clean HOME."""

    def __init__(self, base: Path):
        self.base = base
        self.cwd = base / "work dir"   # a space in the path: the fight's absolute path must survive it
        self.cwd.mkdir()
        self.log = base / "fake.log"
        self.bin = base / "bin"
        self.godot = _exe(self.bin / "godot", FAKE_GODOT)
        for tool in POISONED:
            _exe(self.bin / tool, POISON)
        self.home = base / "home"
        self.home.mkdir()
        self.fight = self.cwd / "L-9601-s1.fight.json"
        self.fight.write_text("{}")

    def env(self, uname=None, **extra):
        env = {"PATH": "%s:/usr/bin:/bin" % self.bin, "HOME": str(self.home), "FAKE_LOG": str(self.log)}
        if uname:
            env["OM_UNAME"] = uname
        env.update(extra)
        return env

    def run(self, *args, uname=None, **extra):
        return subprocess.run([str(REPLAY), *args], cwd=self.cwd, env=self.env(uname, **extra), capture_output=True, text=True, timeout=60)

    def calls(self):
        if not self.log.exists():
            return []
        blocks = [b for b in self.log.read_text().split("--\n") if b.strip()]
        return [dict(line.split("=", 1) if not line.startswith("ARGV") else ("ARGV", line[5:]) for line in b.splitlines()) for b in blocks]


@pytest.fixture()
def rig(tmp_path):
    return Rig(tmp_path)


@pytest.fixture()
def clean_marker():
    """The once-per-checkout marker lives in the repository's `.godot`; a test that runs for real starts without it and leaves the checkout as it found it."""
    existed = MARKER.exists()
    if existed:
        MARKER.unlink()
    yield
    if MARKER.exists():
        MARKER.unlink()
    if existed:
        MARKER.parent.mkdir(parents=True, exist_ok=True)
        MARKER.touch()


# ---------------------------------------------------------------- criterion 12: --dry-run

@pytest.mark.parametrize("uname", ["Darwin", "Linux"])
def test_dry_run_prints_the_import_line_and_the_launch_line_and_runs_nothing(uname, rig):
    """Criterion 12, spec line 42: `--dry-run` with `OM_UNAME=Darwin` and with `Linux`, `GODOT` unset and a fake godot on PATH: two lines, the import line
    `<godot> --headless --import --path <repo>` and the launch line `<godot> --path <repo> --windowed --resolution 1919x1080 <scene>` carrying `OM_FIGHT=` the
    absolute fight path (given relative); nothing is run (the fake godot is never called)."""
    r = rig.run(rig.fight.name, "--dry-run", uname=uname)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    assert len(lines) == 2, lines
    assert "%s --headless --import --path %s" % (rig.godot, ROOT) in norm(lines[0])
    assert "%s --path %s --windowed --resolution 1919x1080 %s" % (rig.godot, ROOT, SCENE) in norm(lines[1])
    assert "OM_FIGHT=%s" % rig.fight in norm(lines[1])
    assert "OM_SHOT_OUT" not in r.stdout
    assert rig.calls() == []


def test_dry_run_names_the_shots_directory_as_an_absolute_path_in_either_argument_order(rig):
    """Criterion 12: `--shots <dir>` puts `OM_SHOT_OUT` (absolute, given relative) on the launch line; the arguments may come in any order."""
    for args in (("--shots", "out", rig.fight.name, "--dry-run"), ("--dry-run", rig.fight.name, "--shots", "out")):
        r = rig.run(*args, uname="Linux")
        assert r.returncode == 0, r.stdout + r.stderr
        launch = [norm(l) for l in r.stdout.splitlines() if "fight_replay.tscn" in l]
        assert len(launch) == 1 and "OM_SHOT_OUT=%s" % (rig.cwd / "out") in launch[0], r.stdout


def test_a_missing_fight_file_exits_2_and_names_it(rig):
    """Criterion 12: "a missing fight file exits 2 with the file named", with and without `--dry-run`; nothing is run."""
    for extra in ((), ("--dry-run",)):
        r = rig.run("nowhere.fight.json", *extra, uname="Linux")
        assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
        assert "nowhere.fight.json" in r.stdout + r.stderr
    assert rig.calls() == []


# ---------------------------------------------------------------- criterion 12: finding Godot

def test_godot_is_found_in_the_stated_order(rig):
    """Criterion 12: first match wins, `$GODOT` then `godot` on PATH then `~/.local/bin/godot.real`. $GODOT beats PATH; PATH beats the home one (both exist);
    with PATH having none, the home one is used."""
    home_godot = _exe(rig.home / ".local" / "bin" / "godot.real", FAKE_GODOT)
    elsewhere = _exe(rig.base / "elsewhere" / "my-godot", FAKE_GODOT)
    r = rig.run(rig.fight.name, "--dry-run", uname="Linux", GODOT=str(elsewhere))
    assert str(elsewhere) in r.stdout and str(rig.godot) not in r.stdout and str(home_godot) not in r.stdout, r.stdout + r.stderr
    r = rig.run(rig.fight.name, "--dry-run", uname="Linux")
    assert str(rig.godot) in r.stdout and str(home_godot) not in r.stdout, r.stdout + r.stderr
    rig.godot.unlink()
    r = rig.run(rig.fight.name, "--dry-run", uname="Darwin")
    assert r.returncode == 0 and str(home_godot) in r.stdout, r.stdout + r.stderr


def test_replay_sh_names_the_mac_default_godot_location():
    """Criterion 12: the fourth stated location, `/Applications/Godot.app/Contents/MacOS/Godot`, cannot be exercised on this machine, so the script's source is
    checked for the exact path."""
    assert "/Applications/Godot.app/Contents/MacOS/Godot" in REPLAY.read_text()


# ---------------------------------------------------------------- criterion 12: a real run

def test_real_run_imports_once_then_launches_with_the_fight_and_shots_in_the_environment(rig, clean_marker):
    """Criterion 12: the first run calls the fake godot twice, import then launch; the marker `.godot/replay_imported` then exists, so the second run launches only.
    The launch has `OM_FIGHT` the absolute fight path (a path with a space in it), `OM_SHOT_OUT` absolute with `--shots` and unset without, and none of `timeout`,
    `flock`, `setsid`, xdotool is used."""
    assert rig.run(rig.fight.name, "--shots", "shots", uname="Darwin").returncode == 0
    assert "POISON" not in rig.log.read_text(), rig.log.read_text()
    first = rig.calls()
    assert [c["ARGV"] for c in first] == ["--headless --import --path %s" % ROOT, "--path %s --windowed --resolution 1919x1080 %s" % (ROOT, SCENE)]
    assert first[1]["OM_FIGHT"] == str(rig.fight) and first[1]["OM_SHOT_OUT"] == str(rig.cwd / "shots")
    assert MARKER.exists()
    rig.log.unlink()
    assert rig.run(rig.fight.name, uname="Linux").returncode == 0
    assert "POISON" not in rig.log.read_text(), rig.log.read_text()
    second = rig.calls()
    assert [c["ARGV"] for c in second] == ["--path %s --windowed --resolution 1919x1080 %s" % (ROOT, SCENE)]
    assert second[0]["OM_FIGHT"] == str(rig.fight) and second[0]["OM_SHOT_OUT"] == "<unset>"


def test_dry_run_leaves_the_import_marker_alone(rig, clean_marker):
    """Criterion 12: `--dry-run` "runs nothing", so it does not write the marker either."""
    assert rig.run(rig.fight.name, "--dry-run", uname="Linux").returncode == 0
    assert not MARKER.exists()


# ---------------------------------------------------------------- criterion 13: README

def test_readme_has_a_watch_a_lab_fight_section_with_both_lines():
    """Criterion 13, spec line 43: a heading "Watch a lab fight" whose section carries the Linux line
    `OM_FIGHT=$PWD/<fight> scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn` and the Mac line `scripts/replay.sh <fight>`."""
    text = (ROOT / "README.md").read_text()
    m = re.search(r"^(#+)[ \t]+Watch a lab fight[ \t]*$", text, re.M)
    assert m, "README.md has no heading 'Watch a lab fight'"
    rest = text[m.end():]
    nxt = re.search(r"^#{1,%d}[ \t]" % len(m.group(1)), rest, re.M)
    section = rest[:nxt.start()] if nxt else rest
    assert "OM_FIGHT=$PWD/<fight> scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn" in section
    assert "scripts/replay.sh <fight>" in section
