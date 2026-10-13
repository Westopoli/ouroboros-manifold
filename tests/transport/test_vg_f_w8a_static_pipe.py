"""Lane F, piece W8a (static + cross-OS pipe build scripts).

Spec: docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md "Shipping the pipe binary per OS"
(W8a row) and docs/northstar/plans/2026-10-07-visible-game-spec.md lane F.
Story S-139 (One sim, every machine), rules R-139-01 (byte-identical trace on Windows, macOS, Linux)
and R-139-05 (the three-platform diff). The shipped pipe must be the exact sim, not just a pipe.

Fenced: builders never edit this file. Positive controls are marked CONTROL.
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
PROBE = SCRIPTS / "net_xplat_checksum.py"
SEED, TICKS = "3", "100"


def _script(name: str) -> Path:
    p = SCRIPTS / name
    assert p.exists(), f"S-139/W8a: scripts/{name} does not exist (W8a not built)"
    return p


def _probe(env_pipe: str | None) -> str:
    env = dict(os.environ)
    env.pop("OM_PIPE", None)
    if env_pipe:
        env["OM_PIPE"] = env_pipe
    r = subprocess.run([sys.executable, str(PROBE), SEED, TICKS], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr[-800:]
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith("tick=")]
    assert lines, "the probe printed no checkpoint line: " + r.stdout[-400:]
    return "\n".join(lines)


def test_control_probe_is_deterministic_on_the_dynamic_pipe():
    """CONTROL (R-139-01): two probe runs on the dev pipe agree, so a later inequality means the build differs."""
    if not (ROOT / "pipe/ouroboros_pipe").exists():
        pytest.skip("pipe/ouroboros_pipe not built")
    assert _probe(None) == _probe(None)


def test_all_four_scripts_exist_and_are_executable():
    """W8a files: three build scripts (linux, windows, macos) and codesign_macos.sh."""
    for name in ("build_pipe_linux.sh", "build_pipe_windows.sh", "build_pipe_macos.sh", "codesign_macos.sh"):
        p = _script(name)
        assert p.stat().st_mode & stat.S_IXUSR, f"scripts/{name} is not executable"
        assert p.read_text().startswith("#!"), f"scripts/{name} has no shebang"


def test_windows_script_carries_the_recorded_flags():
    """Steam spec: mingw-w64, static, -D__USE_MINGW_ANSI_STDIO=1, ucrt via a -specs file, all csrc/*.c plus om_pipe.c."""
    text = _script("build_pipe_windows.sh").read_text()
    assert "x86_64-w64-mingw32-gcc" in text, "the Windows script does not use mingw-w64 gcc"
    for needle in ("-static", "-D__USE_MINGW_ANSI_STDIO=1", "-specs", "ucrt", "-ffp-contract=off", "-fno-fast-math",
                   "csrc/pipe/om_pipe.c", "dist/windows/ouroboros_pipe.exe"):
        assert needle in text, f"build_pipe_windows.sh lacks {needle!r}"
    assert "-msse2" in text and "-mfpmath=sse" in text, "x86_64 Windows keeps the Linux SSE flag set"


def test_macos_script_has_arm64_flags_and_no_sse():
    """Spec: native clang, arm64 flags, no -msse2 (arm64 rejects it)."""
    text = _script("build_pipe_macos.sh").read_text()
    assert "clang" in text and "-ffp-contract=off" in text and "dist/macos/ouroboros_pipe" in text
    assert "-msse2" not in text and "-mfpmath=sse" not in text, "arm64 must not receive the x86 SSE flags"
    assert "arm64" in text


def test_codesign_script_signs_ad_hoc():
    """Spec: ad-hoc `codesign -s -` on the Mac binaries."""
    text = _script("codesign_macos.sh").read_text()
    assert "codesign" in text and "-s -" in text, "codesign_macos.sh does not sign ad hoc (codesign -s -)"


def test_linux_static_exe_is_static_and_reproduces_the_probe(tmp_path):
    """R-139-01/R-139-05: the Linux static exe has no shared-library dependency and gives the dev pipe's probe lines."""
    script = _script("build_pipe_linux.sh")
    r = subprocess.run(["bash", str(script)], cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-800:]
    exe = ROOT / "dist/linux/ouroboros_pipe"
    assert exe.exists(), "build_pipe_linux.sh did not write dist/linux/ouroboros_pipe"
    ldd = subprocess.run(["ldd", str(exe)], capture_output=True, text=True)
    assert "not a dynamic executable" in (ldd.stdout + ldd.stderr), "the shipped pipe is dynamically linked: " + ldd.stdout
    assert _probe(str(exe)) == _probe(None), "the static pipe's probe checksums differ from the dev pipe's"


@pytest.mark.skipif(not (shutil.which("x86_64-w64-mingw32-gcc") and shutil.which("wine64")),
                    reason="mingw-w64 or wine64 not installed on this box")
def test_windows_exe_under_wine_reproduces_the_probe(tmp_path):
    """Q-NET-05 for Windows: the .exe, run under wine64, prints the same checkpoint lines as the Linux pipe."""
    r = subprocess.run(["bash", str(_script("build_pipe_windows.sh"))], cwd=ROOT, capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-800:]
    exe = ROOT / "dist/windows/ouroboros_pipe.exe"
    assert exe.exists(), "build_pipe_windows.sh did not write dist/windows/ouroboros_pipe.exe"
    assert exe.read_bytes()[:2] == b"MZ", "not a PE executable"
    wrapper = tmp_path / "pipe_wine.sh"
    wrapper.write_text(f'#!/bin/sh\nexec wine64 "{exe}" "$@" 2>/dev/null\n')
    wrapper.chmod(0o755)
    assert _probe(str(wrapper)) == _probe(None), "the Windows pipe under wine64 diverges from Linux"
