"""SV-4: run the sim viewer on macOS (docs/northstar/plans/2026-10-12-simviewer-spec.md,
section "SV-4: run on macOS").

Proves:
  - `--pipe PATH` is an option; its default is computed when parsing:
    dist/macos/ouroboros_pipe_dbg on darwin, pipe/ouroboros_pipe_dbg elsewhere.
  - `main` runs the real dbg pipe given by `--pipe` (headless `--shot`).
  - Positive control: a missing binary returns 1 and prints a `simviewer: ...` line
    to stderr (the test would fail if `--pipe` were ignored and the default used).
  - scripts/simviewer/build_pipe_dbg_macos.sh exists with the recorded flags (not
    runnable on Linux: text and `bash -n` only).
  - README.md has an "On a Mac" section naming the build script and `--shot`.

Red on the built tree: `--pipe` is an unknown argument (argparse exits 2) and
scripts/simviewer/build_pipe_dbg_macos.sh does not exist.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.simviewer.__main__ import _parse  # noqa: E402

PIPE_DBG = ROOT / "pipe" / "ouroboros_pipe_dbg"
MAC_SCRIPT = ROOT / "scripts" / "simviewer" / "build_pipe_dbg_macos.sh"
README = ROOT / "scripts" / "simviewer" / "README.md"


def _norm(path):
    return str(path).replace("\\", "/")


def _main_in_child(argv, timeout=120):
    code = ("import sys; from scripts.simviewer.__main__ import main; "
            "sys.exit(main(%r))" % (argv,))
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    return subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env,
                          capture_output=True, timeout=timeout)


# ------------------------------------------------------------ 1-2. option and default

def test_pipe_option_is_parsed():
    """SV-4: `--pipe /x/y` is accepted and kept verbatim."""
    assert _parse(["--pipe", "/x/y"]).pipe == "/x/y"


def test_default_pipe_is_the_macos_build_on_darwin(monkeypatch):
    """SV-4: with sys.platform == "darwin" the parsed default is
    dist/macos/ouroboros_pipe_dbg (computed at parse time, not import time)."""
    monkeypatch.setattr(sys, "platform", "darwin")
    assert _norm(_parse([]).pipe).endswith("dist/macos/ouroboros_pipe_dbg")


def test_default_pipe_is_the_make_build_elsewhere(monkeypatch):
    """SV-4: with sys.platform == "linux" the parsed default is
    pipe/ouroboros_pipe_dbg (the Makefile target)."""
    monkeypatch.setattr(sys, "platform", "linux")
    assert _norm(_parse([]).pipe).endswith("pipe/ouroboros_pipe_dbg")


# ------------------------------------------------------------ 3-4. main with --pipe

@pytest.mark.skipif(not PIPE_DBG.exists(),
                    reason="pipe/ouroboros_pipe_dbg not built: run make pipe/ouroboros_pipe_dbg")
def test_main_runs_the_pipe_given_by_the_option(tmp_path):
    """SV-4: `main([... --pipe <dbg binary> --shot DIR])` returns 0 and writes tick_mode.png."""
    res = _main_in_child(["--seed", "1", "--n-regions", "80", "--pipe", str(PIPE_DBG),
                          "--shot", str(tmp_path)])
    assert res.returncode == 0, res.stderr.decode()[-2000:]
    data = (tmp_path / "tick_mode.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_missing_pipe_binary_returns_1_with_a_simviewer_line(tmp_path, capsys):
    """SV-4 POSITIVE CONTROL: a nonexistent `--pipe` path returns 1 and prints a line
    starting `simviewer:` on stderr; nothing is written."""
    from scripts.simviewer.__main__ import main
    rc = main(["--seed", "1", "--n-regions", "80", "--pipe", str(tmp_path / "does_not_exist"),
               "--shot", str(tmp_path)])
    err = capsys.readouterr().err
    assert rc == 1
    assert any(line.startswith("simviewer:") for line in err.splitlines()), err
    assert not (tmp_path / "tick_mode.png").exists()


# ------------------------------------------------------------ 5. the macOS build script

def _script_text():
    assert MAC_SCRIPT.exists(), "SV-4: scripts/simviewer/build_pipe_dbg_macos.sh does not exist"
    return MAC_SCRIPT.read_text()


def test_macos_script_exists_and_parses():
    """SV-4: the script exists and `bash -n` accepts it."""
    _script_text()
    r = subprocess.run(["bash", "-n", str(MAC_SCRIPT)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_macos_script_carries_the_recorded_flags():
    """SV-4: debug-inject define, output name, clang, signing, cross-reference, -arch."""
    text = _script_text()
    for needle in ("-DOM_DEBUG_INJECT", "ouroboros_pipe_dbg", "clang", "codesign_macos.sh",
                   "See also: scripts/build_pipe_macos.sh", "-arch", "arm64",
                   "dist/macos", "csrc/pipe/om_pipe.c", "csrc/pipe/pipe_"):
        assert needle in text, f"build_pipe_dbg_macos.sh lacks {needle!r}"


def test_macos_script_keeps_x86_sse_flags_inside_an_x86_64_conditional():
    """SV-4: arm64 rejects -msse2/-mfpmath=sse, so any line naming them (after joining
    split strings like -m""sse2, as build_pipe_macos.sh does) also tests for x86_64."""
    text = _script_text().replace('""', "")
    for line in text.splitlines():
        if re.search(r"-msse2|-mfpmath=sse", line):
            assert "x86_64" in line, f"x86 SSE flag outside an x86_64 conditional: {line!r}"
    # the conditional must exist at all (Intel Macs keep the sim's float contract)
    assert "x86_64" in text


def test_macos_script_avoids_flags_clang_or_the_mac_linker_reject():
    """SV-4: clang rejects -fexcess-precision; macOS has no ELF -rpath $ORIGIN."""
    text = _script_text()
    assert "-fexcess-precision" not in text
    assert "-rpath" not in text


# ------------------------------------------------------------ 6. README

def test_readme_has_an_on_a_mac_section():
    """SV-4: a section titled "On a Mac" names the build script and `--shot`."""
    text = README.read_text()
    m = re.search(r"^#+\s*On a Mac\s*$(.*?)(?=^#+\s|\Z)", text, re.M | re.S)
    assert m, 'README.md has no "On a Mac" section'
    body = m.group(1)
    assert "build_pipe_dbg_macos.sh" in body
    assert "--shot" in body
