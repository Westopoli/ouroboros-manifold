"""Steam wiring spec (docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md), piece W7
portability. Rules: E-19 R-140-02..04 (every peer's sim agrees byte for byte, so the checksum
exchange of the session never desyncs on another OS or compiler) and the determinism contract
(CLAUDE.md: same seed and command stream, byte-identical trace on every platform).

Spec W7 gate: the probe reproduces the Linux reference checksums, the lint rejects a planted
hypot, `nm -D` lists no sin, the Makefile flags are gated per target.

Probe interface assumed (the spec fixes seed 3, 2,000 ticks, ticks 100/500/1000/2000 and the
script path, not the output format): scripts/net_xplat_checksum.py prints, per checkpoint, a line
holding the tick and `full=<uint64 decimal>` (section words may follow on the line); exit 0.

PINNED VALUES: re-pinned under ledger row TD-NET-probe-pins (Architect ruling 2026-10-06). They are
what scripts/net_xplat_checksum.py (the probe route: harness Pipe, driver make_script, net_submit
then net_step) measures; this reproduces main and the spec's reference (17857234444101692619 at
tick 100). The earlier pins came from a different route (start_mission then net_step only).
"""
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"
PROBE = ROOT / "scripts/net_xplat_checksum.py"
LINT = ROOT / "scripts/specfactory/libm_lint.py"
PYTHON = sys.executable

# Tick -> full checksum word, seed 3, measured by the probe route (TD-NET-probe-pins-2).
# These move whenever a ruled sim change moves the hashed state; re-pin under a ledger row; the
# cross-OS check compares each OS's probe output to these values.
# Re-recorded 2026-10-11 (TD-VG-E-21): E1q changes the growth hashed in the economy block; old values in the ledger row
# TD-VG-W-2: W2 stored routes add the route block to the movement section; old values 100: 14414279078877383414,
# 500: 2462771596946682441, 1000: 2825217407474388049, 2000: 263473283203217348 (new values below).
PINNED_FULL = {
    100: 15870404153552538785,
    500: 5368266331726284326,
    1000: 1335582271474088983,
    2000: 6505739661716914864,
}


# ----------------------------------------------------------------------------- probe
def test_W7_probe_script_is_committed():
    """W7: the probe script is committed under scripts/. RED: file absent on main."""
    assert PROBE.is_file(), "scripts/net_xplat_checksum.py is missing"


def test_W7_probe_reproduces_pinned_checksums():
    """W7 gate: the probe on this box reproduces the pinned seed-3 checksums at 100/500/1000/2000.
    RED: the probe script does not exist."""
    assert PROBE.is_file(), "scripts/net_xplat_checksum.py is missing"
    res = subprocess.run([PYTHON, str(PROBE)], cwd=str(ROOT), capture_output=True, text=True,
                         timeout=300)
    assert res.returncode == 0, res.stderr[-2000:]
    got = {}
    for line in res.stdout.splitlines():
        m = re.search(r"\b(100|500|1000|2000)\b.*?full\W{0,3}(\d{10,})", line)
        if m:
            got[int(m.group(1))] = int(m.group(2))
    assert got == PINNED_FULL, f"probe output {got} != pinned {PINNED_FULL}"


# ----------------------------------------------------------------------------- lint
def _lint(tmp_path, body):
    (tmp_path / "planted.c").write_text(f"double f(double a, double b) {{ return {body}; }}\n")
    return subprocess.run([PYTHON, str(LINT), str(tmp_path)], capture_output=True, text=True)


def test_W7_lint_positive_control_rejects_planted_sin(tmp_path):
    """Positive control, passes today: the lint already rejects sin."""
    res = _lint(tmp_path, "sin(a)")
    assert res.returncode == 1 and "sin" in res.stdout


@pytest.mark.parametrize("fn,body", [
    ("hypot", "hypot(a, b)"), ("fma", "fma(a, b, a)"), ("ldexp", "ldexp(a, 2)"),
    ("frexp", "frexp(a, (int *)0)"), ("rint", "rint(a)"),
])
def test_W7_lint_rejects_planted_call(tmp_path, fn, body):
    """W7: libm_lint gains fma hypot ldexp frexp rint. RED: exit 0, the name is not in BANNED."""
    res = _lint(tmp_path, body)
    assert res.returncode == 1, f"lint accepted a planted {fn}(): {res.stdout!r}"
    assert fn in res.stdout


def test_W7_lint_real_csrc_still_clean():
    """Control, passes today: the sim itself calls none of the newly banned functions."""
    res = subprocess.run([PYTHON, str(LINT)], capture_output=True, text=True)
    assert res.returncode == 0, res.stdout


# ----------------------------------------------------------------------------- symbols
def test_W7_library_imports_no_sin():
    """W7: nm -D lists no `sin` (the dead weak stub kept it an undefined symbol).
    RED: region.c:358 `om_sin ... return sin(x)` leaves `sin` undefined in libouroboros.so."""
    import conftest  # noqa: F401  (importing it builds libouroboros.so, as every csim test does)
    lib = ROOT / "libouroboros.so"
    assert lib.is_file(), "libouroboros.so did not build"
    out = subprocess.run(["nm", "-D", str(lib)], capture_output=True, text=True, check=True).stdout
    names = {ln.split()[-1].split("@")[0] for ln in out.splitlines() if ln.strip()}
    assert "sin" not in names, "libouroboros.so still references libm sin"


def test_W7_region_c_has_no_weak_sin_stub():
    """W7: the dead weak sin stub in region.c is deleted. RED: line 358 is still there."""
    src = (ROOT / "csrc/region.c").read_text()
    assert not re.search(r"__attribute__\s*\(\(\s*weak\s*\)\)\s*double\s+om_sin", src)
    assert not re.search(r"return\s+sin\s*\(", src)


def test_W7_tactical_move_has_no_ctz_builtin():
    """W7: __builtin_ctzll (no MSVC form) is replaced by a portable helper.
    RED: tactical_move.c:952 still calls it. (Same results are proven by the probe pins and the
    recorded hash tests, which must stay unchanged.)"""
    src = (ROOT / "csrc/tactical_move.c").read_text()
    assert "__builtin_ctz" not in src


# ----------------------------------------------------------------------------- Makefile
def _fake_toolchain(tmp_path, machine, accept_excess):
    """A compiler stub and a uname stub that report `machine`; with `accept_excess` False the
    stub fails any probe compile carrying -fexcess-precision=standard (clang behaviour)."""
    cc = tmp_path / "fakecc"
    cc.write_text(
        "#!/bin/sh\n"
        'for a in "$@"; do\n'
        f'  case "$a" in -dumpmachine) echo {machine}-linux-gnu; exit 0;;\n'
        f'    -fexcess-precision=standard) [ "{accept_excess}" = "1" ] || exit 1;;\n'
        "  esac\n"
        "done\n"
        "exit 0\n")
    un = tmp_path / "uname"
    un.write_text(f'#!/bin/sh\ncase "$1" in -m) echo {machine};; *) echo Linux;; esac\n')
    for f in (cc, un):
        f.chmod(f.stat().st_mode | stat.S_IXUSR)
    return cc


def _dry_run(tmp_path, machine, arch_var, accept_excess):
    cc = _fake_toolchain(tmp_path, machine, int(accept_excess))
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}")
    res = subprocess.run(["make", "-n", "-B", f"CC={cc}", f"ARCH={arch_var}", "libouroboros.so"],
                         cwd=str(ROOT), capture_output=True, text=True, env=env)
    assert res.returncode == 0, res.stderr
    return res.stdout


def test_W7_makefile_arm64_has_no_x86_flags(tmp_path):
    """W7: -msse2 -mfpmath=sse only on x86 targets. RED: both are unconditional (Makefile:27-28)."""
    out = _dry_run(tmp_path, "aarch64", "arm64", True)
    assert "-msse2" not in out and "-mfpmath=sse" not in out


def test_W7_makefile_x86_keeps_sse_flags(tmp_path):
    """Control, passes today: an x86_64 target still gets -msse2 -mfpmath=sse."""
    out = _dry_run(tmp_path, "x86_64", "x86_64", True)
    assert "-msse2" in out and "-mfpmath=sse" in out


def test_W7_makefile_excess_precision_only_when_accepted(tmp_path):
    """W7: -fexcess-precision=standard only when the compiler accepts it.
    RED: unconditional, so a clang-like compiler that rejects it still gets it."""
    out = _dry_run(tmp_path, "x86_64", "x86_64", False)
    assert "-fexcess-precision" not in out


def test_W7_makefile_excess_precision_kept_when_accepted(tmp_path):
    """Control, passes today: a compiler that accepts it still gets it."""
    assert "-fexcess-precision=standard" in _dry_run(tmp_path, "x86_64", "x86_64", True)


@pytest.mark.parametrize("machine,arch", [("x86_64", "x86_64"), ("aarch64", "arm64")])
def test_W7_makefile_fp_contract_off_always(tmp_path, machine, arch):
    """Control, passes today: -ffp-contract=off on every target (dropping it diverges at tick 100)."""
    assert "-ffp-contract=off" in _dry_run(tmp_path, machine, arch, True)


def test_W7_makefile_documents_msvc_equivalents():
    """W7: a Makefile comment names the MSVC equivalents. RED: no such comment."""
    text = MAKEFILE.read_text()
    assert "/fp:precise" in text and "/fp:contract-" in text
