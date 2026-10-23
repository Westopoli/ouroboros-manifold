"""Rung R3 tests (SPEC.md section 8): the command line and the matplotlib replay.

Red until layerlab/__main__.py and layerlab/replay.py exist. The CLI is driven by subprocess from
toys/layerlab/. The sweep CLI is expected to accept --out-dir and --no-log beside the options
SPEC section 8 lists (the tests need them to keep results/ clean).
"""
import itertools
import re
import subprocess
import sys

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.animation as mpl_anim  # noqa: E402
import pytest  # noqa: E402

from layerlab import scenario  # noqa: E402
from layerlab.replay import replay, save_gif  # noqa: E402
from layerlab.run import run  # noqa: E402

R0 = "scenarios/r0_raiders_10v5.toml"


@pytest.fixture(scope="module")
def scn(scenarios_dir):
    return scenario.load(str(scenarios_dir / "r0_raiders_10v5.toml"))


def _cli(lab_dir, *args, timeout=120):
    return subprocess.run([sys.executable, "-m", "layerlab", *args], cwd=lab_dir,
                          capture_output=True, text=True, timeout=timeout)


def _winner_line(out):
    lines = [ln for ln in out.splitlines() if "winner" in ln.lower()]
    assert lines, "no line naming the winner in:\n" + out
    return lines[0]


# --------------------------------------------------------------------------- run


def test_cli_run_prints_winner_ticks_survivors(lab_dir, scn):
    """SPEC section 8 `python3 -m layerlab run <scenario.toml> --seed N`: exits 0 and prints the
    winner (A for 10 v 5), the tick count of the run and the survivors, matching a direct run()."""
    p = _cli(lab_dir, "run", R0, "--seed", "0")
    assert p.returncode == 0, p.stderr
    out = p.stdout
    res = run(scn, seed=0)
    assert re.search(r"\bA\b", _winner_line(out)), out
    assert "ticks" in out.lower() and str(res.ticks) in out, out
    assert "survivors" in out.lower(), out
    sline = [ln for ln in out.splitlines() if "survivors" in ln.lower()][0]
    assert str(res.survivors[0]) in sline and str(res.survivors[1]) in sline, sline


def test_cli_run_set_changes_outcome(lab_dir, scn):
    """SPEC section 8 `--set path=value`: groups[0].count=3 turns the 10 v 5 win into a loss, so the
    winner line changes from A to B (detector positive; the unmodified run above is the negative)."""
    base = _cli(lab_dir, "run", R0, "--seed", "0")
    p = _cli(lab_dir, "run", R0, "--seed", "0", "--set", "groups[0].count=3")
    assert p.returncode == 0, p.stderr
    assert p.stdout != base.stdout
    assert _winner_line(p.stdout) != _winner_line(base.stdout)
    assert re.search(r"\bB\b", _winner_line(p.stdout)), p.stdout
    assert not re.search(r"\bA\b", _winner_line(p.stdout)), p.stdout
    res = run(scenario.set_path(scn, "groups[0].count", 3), seed=0)
    assert str(res.ticks) in p.stdout


def test_cli_run_seed_default_matches_seed_zero(lab_dir):
    """SPEC section 8 (`--seed` optional): omitting it runs seed 0, the same output as --seed 0."""
    a = _cli(lab_dir, "run", R0)
    b = _cli(lab_dir, "run", R0, "--seed", "0")
    assert a.returncode == 0 and a.stdout == b.stdout


def test_cli_run_bad_set_path_fails_with_message(lab_dir):
    """SPEC section 4 (a path that does not resolve is an error): a bad --set path exits nonzero and
    the message names the bad path."""
    p = _cli(lab_dir, "run", R0, "--set", "groups[9].count=3")
    assert p.returncode != 0
    msg = p.stdout + p.stderr
    assert msg.strip() and "groups[9]" in msg, msg
    p = _cli(lab_dir, "run", R0, "--set", "rules.no_such_knob=1")
    assert p.returncode != 0
    assert "no_such_knob" in p.stdout + p.stderr


def test_cli_run_missing_scenario_fails_with_message(lab_dir):
    """SPEC section 8 (CLI error path): a scenario file that does not exist exits nonzero and says so."""
    p = _cli(lab_dir, "run", "scenarios/does_not_exist.toml")
    assert p.returncode != 0
    assert "does_not_exist" in p.stdout + p.stderr


# --------------------------------------------------------------------------- sweep


def test_cli_sweep_prints_table_and_writes_png(lab_dir, tmp_path):
    """SPEC section 8 `sweep ... --var --values --seeds --metric --expect --class`, with the
    --out-dir and --no-log options this suite expects: exits 0, prints a table with every value, and
    writes a PNG under the out dir. --no-log keeps results/log.md untouched."""
    real = lab_dir / "results" / "log.md"
    before = real.read_bytes() if real.exists() else None
    p = _cli(lab_dir, "sweep", R0, "--var", "groups[0].count", "--values", "5,8,10",
             "--seeds", "3", "--metric", "win_rate", "--expect", "A", "--class", "T2",
             "--out-dir", str(tmp_path), "--no-log")
    assert p.returncode == 0, p.stderr
    tokens = re.findall(r"[0-9.]+", p.stdout)
    for v in ("5", "8", "10"):
        assert v in tokens, p.stdout
    assert "groups[0].count" in p.stdout
    pngs = list(tmp_path.glob("*.png"))
    assert len(pngs) == 1, pngs
    assert pngs[0].read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert not list(tmp_path.glob("*.md"))
    assert (real.read_bytes() if real.exists() else None) == before


def test_cli_sweep_two_variables(lab_dir, tmp_path):
    """SPEC section 8 `[--var2 ... --values2 ...]`: a two-variable sweep exits 0 and writes a PNG."""
    p = _cli(lab_dir, "sweep", R0, "--var", "groups[0].count", "--values", "4,12",
             "--var2", "groups[1].count", "--values2", "3,6", "--seeds", "2",
             "--out-dir", str(tmp_path), "--no-log")
    assert p.returncode == 0, p.stderr
    assert len(list(tmp_path.glob("*.png"))) == 1


def test_cli_sweep_bad_var_fails_with_message(lab_dir, tmp_path):
    """SPEC section 4 and 8 (unresolvable var is an error): nonzero exit, message names the path, no PNG."""
    p = _cli(lab_dir, "sweep", R0, "--var", "rules.no_such_knob", "--values", "1,2",
             "--seeds", "2", "--out-dir", str(tmp_path), "--no-log")
    assert p.returncode != 0
    assert "no_such_knob" in p.stdout + p.stderr
    assert not list(tmp_path.glob("*.png"))


def test_cli_sweep_unknown_metric_fails(lab_dir, tmp_path):
    """SPEC section 8 (unknown metric is a ValueError): the CLI exits nonzero with a message."""
    p = _cli(lab_dir, "sweep", R0, "--var", "groups[0].count", "--values", "5,10",
             "--seeds", "2", "--metric", "nonsense", "--out-dir", str(tmp_path), "--no-log")
    assert p.returncode != 0
    assert (p.stdout + p.stderr).strip()


# --------------------------------------------------------------------------- replay API


def _frames(anim, cap):
    """Frame count of a FuncAnimation, bounded so an endless generator cannot hang the suite."""
    return len(list(itertools.islice(anim.new_frame_seq(), cap)))


def test_replay_returns_funcanimation_and_runs_when_no_trace(scn):
    """SPEC section 8 replay.py: replay(scn, seed=0) runs the scenario with a trace when none is
    given and returns a matplotlib FuncAnimation under Agg; frames == ticks written."""
    anim = replay(scn, seed=0)
    assert isinstance(anim, mpl_anim.FuncAnimation)
    assert matplotlib.get_backend().lower() == "agg"
    ref = run(scn, seed=0, trace=True)
    assert len(ref.trace) > 0
    assert _frames(anim, len(ref.trace) + 50) == len(ref.trace)


def test_replay_uses_seed_when_running(scn):
    """SPEC section 8 replay.py (seed argument, negative control for the previous test): a different
    seed runs a different fight, so frames track that seed's trace length."""
    ref = run(scn, seed=3, trace=True)
    anim = replay(scn, seed=3)
    assert _frames(anim, len(ref.trace) + 50) == len(ref.trace)


def test_replay_accepts_precomputed_trace(scn):
    """SPEC section 8 replay.py trace=: a precomputed (here truncated) trace is used as given and the
    scenario is not re-run: frames == len(trace) == 7, not the full fight's tick count."""
    full = run(scn, seed=0, trace=True)
    short = full.trace[:7]
    anim = replay(scn, trace=short, seed=0)
    assert isinstance(anim, mpl_anim.FuncAnimation)
    assert _frames(anim, len(full.trace) + 50) == 7
    assert len(full.trace) > 7


def test_save_gif_writes_gif(scn, tmp_path):
    """SPEC section 8 save_gif(anim, path): writes a non-empty file with a GIF header (GIF89a or GIF87a)."""
    trace = run(scn, seed=0, trace=True).trace[:12]
    anim = replay(scn, trace=trace)
    out = tmp_path / "r.gif"
    save_gif(anim, out)
    assert out.exists() and out.stat().st_size > 100
    assert out.read_bytes()[:6] in (b"GIF89a", b"GIF87a")


def test_save_gif_accepts_string_path(scn, tmp_path):
    """SPEC section 8 save_gif(anim, path): a str path works as well as a Path."""
    trace = run(scn, seed=0, trace=True).trace[:5]
    out = str(tmp_path / "s.gif")
    save_gif(replay(scn, trace=trace), out)
    with open(out, "rb") as fh:
        assert fh.read(6) in (b"GIF89a", b"GIF87a")


# --------------------------------------------------------------------------- replay CLI


def test_cli_replay_gif(lab_dir, tmp_path):
    """SPEC section 8 `replay <scenario.toml> [--seed N] [--gif path]`: exits 0 and writes a GIF.
    A short-lived scenario (max_ticks 20) keeps the render fast; it extends r0 by absolute path."""
    short = tmp_path / "short.toml"
    short.write_text('extends = "%s"\n\n[run]\nmax_ticks = 20\n' % (lab_dir / "scenarios" / "r0_raiders_10v5.toml"))
    gif = tmp_path / "out.gif"
    p = _cli(lab_dir, "replay", str(short), "--seed", "0", "--gif", str(gif), timeout=180)
    assert p.returncode == 0, p.stderr
    assert gif.exists() and gif.read_bytes()[:6] in (b"GIF89a", b"GIF87a")


def test_cli_replay_missing_scenario_fails(lab_dir, tmp_path):
    """SPEC section 8 (CLI error path, negative control for the GIF test): a missing scenario exits
    nonzero, with a message, and writes no GIF."""
    gif = tmp_path / "none.gif"
    p = _cli(lab_dir, "replay", "scenarios/does_not_exist.toml", "--gif", str(gif))
    assert p.returncode != 0
    assert "does_not_exist" in p.stdout + p.stderr
    assert not gif.exists()
