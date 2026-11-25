# spec: the brief for piece LI5 (clips), 2026-11-24, no story file; interface docs/reports/2026-11-24-clip-pipeline-interface.md
"""Clip pipeline, story `clip-pipeline` (Story: clip-pipeline, Tests: clips): the CLI `python -m scripts.skilllab.arena.clip` where it must stop before or without Godot.

Rules proved (the brief's words):
- "missing Godot or ffmpeg is an error not a silent skip" (exit 3, the tool named, no output files)
- "CLI `python -m scripts.skilllab.arena.clip ...`" with "a layout+seed+engine tree (or an existing fight file)" as input (bad input is exit 2)
- "into `<name>.mp4` + `<name>-poster.jpg` + `<name>.facts.json`" (a failed run leaves none of the three)

Controls (green today): closeup, the module this one sits beside, exits 2 with REJECT for the same rejected layout; an empty PATH makes the tool lookup fail the way the
missing-tool test relies on.
Red today: the module does not exist, so `python -m` exits 1 with "No module named scripts.skilllab.arena.clip" instead of the exit codes the interface names.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import clip_pipeline_support as S  # noqa: E402


@pytest.fixture()
def fight6(tmp_path) -> Path:
    return S.write_fight(tmp_path / "f6.fight.json", S.synthetic_fight(frames=6))


def _outputs(out: Path) -> list:
    return sorted(p.name for p in out.iterdir()) if out.exists() else []


def _run(fight: Path, out: Path, *extra, env=None):
    return S.run_clip(["--fight", fight, "--out", out, "--name", "t", *extra], env=env)


# ================================================================ controls

def test_control_closeup_rejects_the_rejected_layout_with_exit_2(tmp_path):
    """CONTROL: the harness reaches the repo's modules and the REJECT/exit-2 convention the clip CLI shares: closeup on L-0001 prints `REJECT L-0001 R6`, exit 2."""
    r = subprocess.run([S.PY, "-m", "scripts.skilllab.arena.closeup", "--layout", S.LAYOUT_REJECTED, "--seed", "1", "--every-ticks", "100", "--out", str(tmp_path)],
                       cwd=str(S.ROOT), capture_output=True, text=True, env=S.env_clean())
    assert r.returncode == 2 and "REJECT L-0001" in r.stdout


def test_control_an_empty_path_hides_ffmpeg(tmp_path):
    """CONTROL for the missing-tool tests: with PATH set to an empty directory `ffmpeg` is not found, and the interpreter itself (absolute path) still runs."""
    empty = tmp_path / "empty"
    empty.mkdir()
    env = S.env_clean({"PATH": str(empty)})
    assert shutil.which("ffmpeg", path=str(empty)) is None
    r = subprocess.run([S.PY, "-c", "print(1)"], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "1"


# ================================================================ argument errors, exit 2

@pytest.mark.parametrize("args,why", [
    ([], "no source"),
    (["--layout", S.LAYOUT_SMALL, "--fight", "x.fight.json", "--seed", "1", "--every", "2"], "two sources"),
    (["--layout", S.LAYOUT_SMALL], "layout with no seed and no every"),
    (["--layout", S.LAYOUT_SMALL, "--seed", "1"], "layout with no every"),
    (["--situation", "SIT-0101", "--seed", "1"], "situation with no every"),
    (["--max-mb", "0"], "max-mb 0"),
    (["--chunk", "0"], "chunk 0"),
    (["--box", "1,2,3"], "box of three numbers"),
    (["--box", "a,b,c,d"], "box of words"),
])
def test_bad_arguments_exit_2_and_leave_nothing(tmp_path, fight6, args, why):
    """Brief: "CLI `python -m scripts.skilllab.arena.clip ...`": arguments that cannot make a clip (%s) exit 2 and write nothing under --out."""
    out = tmp_path / "out"
    base = ["--out", out, "--name", "t"]
    if "--layout" not in args and "--fight" not in args and "--situation" not in args:
        base += ["--fight", fight6]
    r = S.run_clip(base + args)
    assert r.returncode == 2, "%s: rc %s\nstdout %s\nstderr %s" % (why, r.returncode, r.stdout[-300:], r.stderr[-300:])
    assert _outputs(out) == []


def test_fight_file_with_refused_content_exits_2(tmp_path):
    """Brief: "(or an existing fight file)": a fight path that is missing, not JSON, or has no frames is exit 2 and writes nothing."""
    out = tmp_path / "out"
    missing = tmp_path / "missing.fight.json"
    junk = tmp_path / "junk.fight.json"
    junk.write_text("not json {")
    empty = S.write_fight(tmp_path / "empty.fight.json", dict(S.synthetic_fight(frames=3), frames=[]))
    for f in (missing, junk, empty):
        r = _run(f, out)
        assert r.returncode == 2, "%s: rc %s %s" % (f.name, r.returncode, r.stderr[-300:])
    assert _outputs(out) == []


def test_rejected_layout_exits_2_with_the_reject_line(tmp_path):
    """Brief: "a layout+seed+engine tree": a layout the lab rejects (L-0001, R6) exits 2 with `REJECT L-0001 ...` on stdout, as closeup does, and writes nothing."""
    out = tmp_path / "out"
    r = S.run_clip(["--layout", S.LAYOUT_REJECTED, "--seed", "1", "--every", "100", "--out", out, "--name", "t"])
    assert r.returncode == 2 and "REJECT L-0001" in r.stdout, r.stdout + r.stderr
    assert _outputs(out) == []


# ================================================================ missing tools, exit 3

def test_missing_godot_is_exit_3_naming_godot(tmp_path, fight6):
    """Brief: "missing Godot or ffmpeg is an error not a silent skip": --godot at a path that is not there exits 3, stderr names godot and that path, and no output
    file is written."""
    out = tmp_path / "out"
    bad = tmp_path / "no-godot"
    r = _run(fight6, out, "--godot", bad)
    assert r.returncode == 3, "rc %s\n%s" % (r.returncode, r.stderr[-400:])
    assert "godot" in r.stderr.lower() and str(bad) in r.stderr
    assert _outputs(out) == []


def test_missing_ffmpeg_is_exit_3_naming_ffmpeg(tmp_path, fight6):
    """Brief: "missing Godot or ffmpeg is an error not a silent skip": --ffmpeg at a path that is not there exits 3 before any rendering (it names ffmpeg and the
    path), and no output file is written."""
    out = tmp_path / "out"
    bad = tmp_path / "no-ffmpeg"
    r = _run(fight6, out, "--ffmpeg", bad)
    assert r.returncode == 3, "rc %s\n%s" % (r.returncode, r.stderr[-400:])
    assert "ffmpeg" in r.stderr.lower() and str(bad) in r.stderr
    assert _outputs(out) == []


def test_no_tools_on_path_is_exit_3(tmp_path, fight6):
    """Brief: "missing Godot or ffmpeg is an error not a silent skip": with PATH an empty directory (no ffmpeg, ffprobe or xvfb-run) the run exits 3 and names
    the first missing tool; no output file."""
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    r = _run(fight6, out, env=S.env_clean({"PATH": str(empty)}))
    assert r.returncode == 3, "rc %s\n%s" % (r.returncode, r.stderr[-400:])
    assert any(t in r.stderr for t in ("ffmpeg", "ffprobe", "xvfb-run"))
    assert _outputs(out) == []


# ================================================================ a failed render leaves nothing, exit 4

def test_a_godot_that_renders_nothing_is_exit_4_and_leaves_no_clip(tmp_path, fight6):
    """Brief: "into `<name>.mp4` + `<name>-poster.jpg` + `<name>.facts.json`": with --godot /bin/false (present, exits 1, saves no frame) the run exits 4, and none of the
    three files is left under --out; the --work dir is removed (no --keep-work)."""
    out, work = tmp_path / "out", tmp_path / "work"
    r = _run(fight6, out, "--godot", "/bin/false", "--work", work)
    assert r.returncode == 4, "rc %s\n%s" % (r.returncode, r.stderr[-400:])
    assert _outputs(out) == []
    assert not work.exists() or not any(work.iterdir())
