# spec: docs/northstar/spec_factory.md pipeline (pre-queue mechanical gate)
"""Tests for scripts/specfactory/libm_lint.py (audit 2026-09-21, item 1:
csrc/sim.c called libm pow() -- om_sin already existed for exactly this
reason and pow() was missed)."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LIBM_LINT = REPO / "scripts" / "specfactory" / "libm_lint.py"


def _run(csrc_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LIBM_LINT), str(csrc_dir)],
        capture_output=True, text=True,
    )


def test_positive_control_pow_call_fails(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "fixture.c").write_text(
        "#include <math.h>\n"
        "double f(double x) { return pow(x, 0.3); }\n"
    )
    proc = _run(csrc)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "pow()" in proc.stdout
    assert "fixture.c:2" in proc.stdout
    assert "LIBM LINT FAILED (1)" in proc.stdout


def test_every_banned_function_is_caught(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    banned = ["pow", "exp", "log", "log2", "log10", "sin", "cos", "tan",
              "asin", "acos", "atan", "atan2", "sinh", "cosh", "tanh", "exp2", "cbrt"]
    body = "\n".join(f"double r{i} = {fn}(1.0);" for i, fn in enumerate(banned))
    (csrc / "fixture.c").write_text(f"void f(void) {{\n{body}\n}}\n")
    proc = _run(csrc)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert f"LIBM LINT FAILED ({len(banned)})" in proc.stdout
    for fn in banned:
        assert f"{fn}()" in proc.stdout


def test_allowed_functions_never_flagged(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    allowed = ["sqrt", "fabs", "floor", "ceil", "round", "trunc", "fmin", "fmax", "fmod"]
    body = "\n".join(f"double r{i} = {fn}(1.0);" for i, fn in enumerate(allowed))
    (csrc / "fixture.c").write_text(f"void f(void) {{\n{body}\n}}\n")
    proc = _run(csrc)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LIBM LINT OK" in proc.stdout


def test_deterministic_replacements_are_not_flagged(tmp_path):
    """om_sin( and om_pow( must never be mistaken for sin(/pow(."""
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "fixture.c").write_text(
        "double om_sin(double x) { return x; }\n"
        "double om_pow(double b, double e) { return b; }\n"
        "double f(void) { return om_sin(1.0) + om_pow(1.0, 2.0); }\n"
    )
    proc = _run(csrc)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LIBM LINT OK" in proc.stdout


def test_comment_mentioning_a_banned_function_is_not_flagged(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "fixture.c").write_text(
        "/* the sim never calls libm sin() or pow() -- see om_sin, om_pow */\n"
        "// pow() and exp() are also banned\n"
        "double f(double x) { return x; }\n"
    )
    proc = _run(csrc)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LIBM LINT OK" in proc.stdout


def test_weak_fallback_stub_is_not_flagged(tmp_path):
    """csrc/region.c's own convention: a `__attribute__((weak))` one-line
    body that a later strong definition (sim.c) always overrides at link
    time, so its libm call never actually executes."""
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "fixture.c").write_text(
        "__attribute__((weak)) double om_sin(double x) { return sin(x); }\n"
    )
    proc = _run(csrc)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LIBM LINT OK" in proc.stdout


def test_debug_inject_branch_is_exempt_but_its_else_is_not(tmp_path):
    """A fault-injection branch's own libm call (OM_BUG_LIBM_POW's whole
    reason to exist) is exempt; the #else (release) path is still checked."""
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "fixture.c").write_text(
        "double f(double x) {\n"
        "#ifdef OM_DEBUG_INJECT\n"
        "    double r = pow(x, 0.3);\n"
        "#else\n"
        "    double r = pow(x, 0.3);\n"
        "#endif\n"
        "    return r;\n"
        "}\n"
    )
    proc = _run(csrc)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "LIBM LINT FAILED (1)" in proc.stdout
    assert "fixture.c:5" in proc.stdout
    assert "fixture.c:3" not in proc.stdout


def test_negative_control_real_csrc_after_the_om_pow_fix_is_clean():
    proc = _run(REPO / "csrc")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LIBM LINT OK" in proc.stdout


def test_missing_csrc_dir_exits_2(tmp_path):
    proc = _run(tmp_path / "does_not_exist")
    assert proc.returncode == 2, proc.stdout + proc.stderr
