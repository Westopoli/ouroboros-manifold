# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md line 316, Rev 12e paragraph
# "HARNESS-userdir (lane H ...)", tests (1) to (6) below; piece HARNESS-userdir
# (docs/northstar/plans/push/pieces.toml).
"""Proves HARNESS-userdir (finding FINDING-ambient-user-dir, ledger rows
FINDING-ambient-user-dir, FINDING-settings-writer-flips, TD-HARNESS-qadir).

The rule, spec line 316, word for word:
  "a gate, a test run and a desktop play never read or write the machine's user directory"
The Architect 2026-10-12 text, word for word:
  "merge_gate.sh exports XDG_DATA_HOME=$SCRATCH_ROOT/xdg with
   $SCRATCH_ROOT/xdg/godot/export_templates symlinked to
   ~/.local/share/godot/export_templates and nothing else"

Gap rulings used (Architect 2026-10-13/14):
  * Gap 1 (G1 (b), per instance): GodotGame.user_dir and DaemonClient.user_dir are
    computed at CONSTRUCTION of the instance (the spec word "start time" is read as
    "construction time"; same intent, never at import) from the env the instance will
    launch with: Path(godot_env(os.environ, scratch, save_dir)["XDG_DATA_HOME"]) / "data".
    write_privacy_flag is a METHOD of the instance; the module constants _USER_DATA_DIR and
    PRIVACY_FLAG_PATH and the module function write_privacy_flag go away. Sites call
    client.user_dir / "qa" or game.user_dir / "qa".
  * Gap 2 (G2 (a)): module function godot_env(base_env, scratch, save_dir) -> dict returns the
    whole child env, pure (no Godot, no filesystem write).
  * Gaps 3 to 7 (null actions, no ruling): gap 3 the planted file goes in a FAKE home and the
    observable is _ground_keys(qa); gap 4 the display-bound control carries a skipif naming the
    missing tool; gap 5 the export block sits right after the trap cleanup EXIT line of
    merge_gate.sh, links $HOME/.local/share/godot/export_templates only, skips the link silently
    when the source is missing; gap 6 test (2) uses a stub godot on PATH plus a read-only
    before/after listing.

Controls first (green on the built tree), then the red-until-built cases.
"""
from __future__ import annotations

import copy
import os
import pwd
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tests" / "qa" / "desktop"))

import daemon_client as dc  # noqa: E402

GATE = REPO_ROOT / "scripts" / "specfactory" / "merge_gate.sh"
RUNNER = REPO_ROOT / "scripts" / "run_godot_tests.sh"
DRIVER = REPO_ROOT / "tests" / "qa" / "desktop" / "daemon_client.py"

SITES = [
    "tests/qa/desktop/test_galaxy_pixels.py",
    "tests/qa/desktop/test_flow_spine.py",
    "tests/qa/desktop/plays/A/play_support.py",
    "tests/qa/desktop/plays/B/_play.py",
    "tests/qa/desktop/plays/C/_play.py",
    "tests/qa/desktop/plays/F/_play.py",
    "tests/qa/desktop/plays/K/_k_common.py",
]


def _real_home() -> Path:
    """The machine's real home, from the password database (never from $HOME,
    which tests below repoint at fake homes)."""
    return Path(pwd.getpwuid(os.getuid()).pw_dir)


def _code_lines(text: str) -> list[tuple[int, str]]:
    """(1-based line number, line) for every line that is not a comment line."""
    return [(i, ln) for i, ln in enumerate(text.splitlines(), 1) if not ln.lstrip().startswith("#")]


# ---------------------------------------------------------------------------
# Embedded pre-piece excerpts (positive controls must not depend on origin/main,
# which holds the built piece after the landing). Each excerpt is the relevant
# lines of the text on origin/main at 01c2e752.
# ---------------------------------------------------------------------------

# scripts/specfactory/merge_gate.sh at 01c2e752, lines 52-57 and 316-324: no export.
OLD_GATE_EXCERPT = '''\
SCRATCH_ROOT="$(mktemp -d -t merge_gate.XXXXXX)"
cleanup() {
    [[ -d "$SCRATCH_ROOT/mainpipe_base" ]] && git -C "$CANDIDATE" worktree remove --force "$SCRATCH_ROOT/mainpipe_base" >/dev/null 2>&1
    rm -rf "$SCRATCH_ROOT"
}
trap cleanup EXIT
    GODOT_BIN=""
    if command -v godot >/dev/null 2>&1; then
        GODOT_BIN="godot"
'''

# tests/qa/desktop/test_galaxy_pixels.py at 01c2e752, line 41.
OLD_SITE_EXCERPT = '''\
QA_SHOT_DIR = Path.home() / ".local/share/data/qa"
img = _read_png_rgb(QA_SHOT_DIR / (shot_name + ".png"))
'''

NEW_SITE_EXCERPT = '''\
def _shot_dir(client):
    return client.user_dir / "qa"
img = _read_png_rgb(_shot_dir(client) / (shot_name + ".png"))
'''


# ---------------------------------------------------------------------------
# Detectors (pure text functions, each with a positive control below)
# ---------------------------------------------------------------------------

_EXPORT_RE = re.compile(r'^\s*export\s+XDG_DATA_HOME\s*=\s*"\$SCRATCH_ROOT/xdg"\s*$')
_GODOT_BIN_USE_RE = re.compile(r'GODOT_BIN=|"\$GODOT_BIN"|\$GODOT_BIN\b')


def _gate_export_problems(text: str) -> list[str]:
    """Spec test (1): the export line, its place, the one link, nothing else."""
    problems: list[str] = []
    code = _code_lines(text)
    export_at = next((i for i, ln in code if _EXPORT_RE.match(ln)), None)
    godot_at = next((i for i, ln in code if _GODOT_BIN_USE_RE.search(ln)), None)
    trap_at = next((i for i, ln in code if re.match(r"^\s*trap\s+cleanup\s+EXIT\b", ln)), None)
    if export_at is None:
        problems.append('no line `export XDG_DATA_HOME="$SCRATCH_ROOT/xdg"`')
    if godot_at is None or trap_at is None:
        problems.append("fixture lacks a GODOT_BIN use or the trap cleanup EXIT line")
    if export_at is not None and godot_at is not None and not export_at < godot_at:
        problems.append("export line %d is not before the first GODOT_BIN use at line %d" % (export_at, godot_at))
    if export_at is not None and trap_at is not None and not export_at > trap_at:
        problems.append("export line %d is not after the trap cleanup EXIT line %d (gap 5)" % (export_at, trap_at))
    links = [(i, ln) for i, ln in code
             if re.search(r"\bln\s+-\w*s", ln) and "export_templates" in ln]
    if not any(".local/share/godot/export_templates" in ln for _, ln in links):
        problems.append("no `ln -s` line linking $HOME/.local/share/godot/export_templates")
    for i, ln in code:
        if re.search(r"\b(ln\s+-\w*s|mkdir|touch)\b", ln) and "xdg" in ln:
            if (i, ln) in links:
                continue
            if re.search(r"\bmkdir\b", ln) and "xdg/godot" in ln and "xdg/" not in ln.replace("xdg/godot", ""):
                continue
            problems.append("line %d creates something else under xdg: %s" % (i, ln.strip()))
    for i, ln in code:
        if "xdg/data" in ln or "app_userdir" in ln:
            problems.append("line %d names xdg/data or app_userdir: %s" % (i, ln.strip()))
    return problems


def _site_violations(text: str) -> list[str]:
    """Spec test (5) for one of the seven sites; empty list = clean."""
    out: list[str] = []
    for i, ln in enumerate(text.splitlines(), 1):
        if re.search(r"Path\.home\(\)", ln) and ".local/share/data" in ln:
            out.append("line %d: Path.home() next to .local/share/data" % i)
        if "~/.local/share/data" in ln and not ln.lstrip().startswith("#"):
            out.append("line %d: ~/.local/share/data outside a comment" % i)
        if re.search(r"\b_USER_DATA_DIR\b|\bPRIVACY_FLAG_PATH\b", ln):
            out.append("line %d: import-time user dir constant" % i)
        if re.match(r"^QA_SHOT_DIR\s*=", ln):
            out.append("line %d: module-level QA_SHOT_DIR evaluated at import" % i)
    if not re.search(r'\.user_dir\b.{0,80}?["\']qa["\']', text, re.DOTALL):
        out.append('no `<client or game>.user_dir / "qa"` frame dir')
    return out


_PIPE_BUILD_RE = re.compile(r"\bmake\s+-s\s+pipe/ouroboros_pipe(?![\w])")
_FIRST_REGRESSION_RE = re.compile(r'merge_gate_support\.py"\s+regression\b')


def _pipe_before_regression_problems(text: str) -> list[str]:
    """Ruling 2026-10-14 (A): the `make -s pipe/ouroboros_pipe` line comes before the first
    regression stage line in merge_gate.sh (non-comment lines only)."""
    code = _code_lines(text)
    build_at = next((i for i, ln in code if _PIPE_BUILD_RE.search(ln)), None)
    reg_at = next((i for i, ln in code if _FIRST_REGRESSION_RE.search(ln)), None)
    if build_at is None:
        return ["no `make -s pipe/ouroboros_pipe` line"]
    if reg_at is None:
        return ["no regression stage line (merge_gate_support.py regression)"]
    if not build_at < reg_at:
        return ["pipe build line %d is not before the first regression stage line %d" % (build_at, reg_at)]
    return []


def _env_xdg_ok(fn, scratch: Path) -> tuple[bool, bool]:
    """The two XDG assertions of spec test (3) for a godot_env-like callable: (base without
    XDG_DATA_HOME gets the scratch dir, base with an EMPTY one gets the scratch dir)."""
    base = {"PATH": "/usr/bin"}
    unset_ok = fn(dict(base), scratch, None).get("XDG_DATA_HOME") == str(scratch / "xdg")
    empty_ok = fn({**base, "XDG_DATA_HOME": ""}, scratch, None).get("XDG_DATA_HOME") == str(scratch / "xdg")
    return unset_ok, empty_ok


def _env_keeps_caller_xdg(fn, scratch: Path) -> bool:
    return fn({"PATH": "/usr/bin", "XDG_DATA_HOME": "/somewhere"}, scratch, None).get("XDG_DATA_HOME") == "/somewhere"


def _ground_keys(qa: dict) -> dict:
    # Copied by value from tests/qa/desktop/test_ground_era.py:21-25 (TD-T3-ground-keys).
    def _on(v):
        return bool(v.get("present")) if isinstance(v, dict) and "present" in v else bool(v)
    return {k: v for k, v in qa.items() if "ground" in str(k).lower() and _on(v)}


# ===========================================================================
# POSITIVE CONTROLS (green on the built tree)
# ===========================================================================

def test_c0_files_exist_and_text_tests_read_the_right_file():
    # Control for tests (1) to (3): the three files the cases read exist and the gate
    # file holds the two anchors test (1) measures against.
    for p in (GATE, RUNNER, DRIVER):
        assert p.is_file(), "%s is missing" % p
    code = _code_lines(GATE.read_text())
    assert any(re.match(r"^\s*GODOT_BIN=", ln) for _, ln in code), "merge_gate.sh has no GODOT_BIN= assignment"
    assert any(re.match(r"^\s*trap\s+cleanup\s+EXIT\b", ln) for _, ln in code), "merge_gate.sh has no trap cleanup EXIT line"


def test_c1_ground_key_detector_works():
    # Control for test (6): the predicate of test_3e_control_space_era_has_no_ground_layer
    # (tests/qa/desktop/test_ground_era.py:21-25) sees a ground key and ignores its absence.
    assert _ground_keys({"scene": "tactical", "ground_layer": True}), "detector missed a truthy ground key"
    assert not _ground_keys({"scene": "tactical", "ground_layer": {"present": False}, "tick": 3}), \
        "detector fired without a truthy ground key"
    assert not _ground_keys({"scene": "tactical"}), "detector fired on a dict with no ground key"


def test_c2_text_detectors_have_positive_controls():
    # Controls for tests (1) and (5): the pre-piece text fails, a clean new text passes.
    assert _gate_export_problems(OLD_GATE_EXCERPT), "pre-piece merge_gate.sh text passed the export assertion"
    good = OLD_GATE_EXCERPT.replace(
        "trap cleanup EXIT\n",
        'trap cleanup EXIT\n'
        '# FINDING-ambient-user-dir\n'
        'export XDG_DATA_HOME="$SCRATCH_ROOT/xdg"\n'
        'mkdir -p "$SCRATCH_ROOT/xdg/godot"\n'
        'ln -s "$HOME/.local/share/godot/export_templates" "$SCRATCH_ROOT/xdg/godot/export_templates"\n')
    assert _gate_export_problems(good) == [], _gate_export_problems(good)
    assert _gate_export_problems(good + 'mkdir -p "$SCRATCH_ROOT/xdg/data"\n'), "xdg/data line not caught"
    assert _site_violations(OLD_SITE_EXCERPT), "main text of test_galaxy_pixels.py passed the site assertion"
    assert any("Path.home()" in v for v in _site_violations(OLD_SITE_EXCERPT)), _site_violations(OLD_SITE_EXCERPT)
    assert any("QA_SHOT_DIR" in v for v in _site_violations(OLD_SITE_EXCERPT)), _site_violations(OLD_SITE_EXCERPT)
    assert _site_violations(NEW_SITE_EXCERPT) == [], _site_violations(NEW_SITE_EXCERPT)


def test_c3_godot_env_stub_that_skips_the_export_fails_both_xdg_assertions(tmp_path):
    # Positive control of spec test (3): a stub returning the base environment unchanged
    # fails both XDG assertions (pure; no Godot).
    stub = lambda base, scratch, save_dir: dict(base)  # noqa: E731
    unset_ok, empty_ok = _env_xdg_ok(stub, tmp_path / "scratch")
    assert not unset_ok, "stub passed the unset-case XDG assertion"
    assert not empty_ok, "stub passed the empty-case XDG assertion"
    # The keep-the-caller's-value assertion separates a real godot_env from a stub that
    # blindly overwrites: a stub that always uses the scratch dir fails it.
    overwrite = lambda base, scratch, save_dir: {**base, "XDG_DATA_HOME": str(scratch / "xdg")}  # noqa: E731
    assert _env_xdg_ok(overwrite, tmp_path / "scratch") == (True, True)
    assert not _env_keeps_caller_xdg(overwrite, tmp_path / "scratch"), "overwriting stub kept the caller's value"
    assert _env_keeps_caller_xdg(stub, tmp_path / "scratch")


def test_c4_runner_stub_can_fail(tmp_path):
    # Positive control of spec test (2): a copy of the runner with `export XDG_DATA_HOME`
    # neutralised (until the block exists it equals the original) leaves the stub godot with
    # NO XDG_DATA_HOME. The stub must be able to fail.
    text = RUNNER.read_text()
    copy_text = re.sub(r"\bexport\s+XDG_DATA_HOME\b", ": XDG_DATA_HOME", text)
    rec = _run_runner_copy(tmp_path, copy_text, preset=None)
    assert rec["xdg"] == "<unset>", "neutralised runner still exports XDG_DATA_HOME: %r" % rec["xdg"]
    assert rec["rc"] == 0, "stub run did not pass: %r" % rec


# ---------------------------------------------------------------------------
# helpers for spec test (2)
# ---------------------------------------------------------------------------

_STUB_GODOT = """#!/usr/bin/env bash
# stub godot: records the environment it was given, prints a passing summary.
if [ "${XDG_DATA_HOME+set}" = set ]; then
    echo "$XDG_DATA_HOME" > "$STUB_RECORD"
    if [ -d "$XDG_DATA_HOME" ]; then echo yes > "$STUB_RECORD.exists"; fi
else
    echo "<unset>" > "$STUB_RECORD"
fi
echo "PASS: 1  FAIL: 0"
exit 0
"""


def _runner_env(root: Path, preset: Path | None) -> dict:
    (root / "bin").mkdir(parents=True, exist_ok=True)
    (root / "home").mkdir(exist_ok=True)
    (root / "t").mkdir(exist_ok=True)
    stub = root / "bin" / "godot"
    stub.write_text(_STUB_GODOT)
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    env = {
        "PATH": "%s:/usr/bin:/bin" % (root / "bin"),
        "HOME": str(root / "home"),
        "TMPDIR": str(root / "t"),
        "STUB_RECORD": str(root / "record"),
    }
    if preset is not None:
        env["XDG_DATA_HOME"] = str(preset)
    return env


def _read_record(root: Path) -> dict:
    rec = root / "record"
    return {
        "xdg": rec.read_text().strip() if rec.exists() else "<no record>",
        "existed_during_run": (root / "record.exists").exists(),
    }


def _run_runner_copy(root: Path, text: str, preset: Path | None) -> dict:
    """Run a COPY of the runner (at <root>/copy/scripts/, so REPO_ROOT is the copy dir)."""
    base = root / "copy"
    (base / "scripts").mkdir(parents=True, exist_ok=True)
    (base / "tests").mkdir(parents=True, exist_ok=True)
    (base / "tests" / "one_line.gd").write_text("extends SceneTree\n")
    script = base / "scripts" / "run_godot_tests.sh"
    script.write_text(text)
    script.chmod(0o755)
    env = _runner_env(root, preset)
    r = subprocess.run(["bash", str(script), "tests/one_line.gd"], env=env, cwd=str(base),
                       capture_output=True, text=True, timeout=120)
    rec = _read_record(root)
    rec["rc"] = r.returncode
    rec["out"] = r.stdout[-300:] + r.stderr[-300:]
    return rec


def _listing(d: Path) -> dict:
    """Read-only recursive listing with mtimes; absent dir = empty."""
    out: dict = {}
    if not d.exists():
        return out
    for dirpath, dirnames, filenames in os.walk(d):
        for n in dirnames + filenames:
            p = os.path.join(dirpath, n)
            try:
                st = os.lstat(p)
            except OSError:
                continue
            out[p] = (st.st_mtime_ns, st.st_size)
    return out


def test_c5_pipe_before_regression_detector_fails_when_the_build_line_moves_after():
    # Positive control for test_7: a copy of the real gate text with the build block moved
    # after the first regression stage must fail the detector; the real text must pass it.
    text = GATE.read_text()
    assert _pipe_before_regression_problems(text) == []
    lines = text.splitlines()
    build_idx = next(i for i, ln in enumerate(lines) if _PIPE_BUILD_RE.search(ln) and not ln.lstrip().startswith("#"))
    moved = lines[:build_idx] + lines[build_idx + 1:]
    reg_idx = next(i for i, ln in enumerate(moved) if _FIRST_REGRESSION_RE.search(ln))
    moved.insert(reg_idx + 1, lines[build_idx])
    problems = _pipe_before_regression_problems("\n".join(moved))
    assert problems and "is not before" in problems[0], problems


# ===========================================================================
# RED UNTIL BUILT
# ===========================================================================

def test_1_merge_gate_exports_xdg_data_home_before_first_godot_use():
    # Spec test (1): the export line before the first GODOT_BIN use, by text, with the
    # variable name; the one link; nothing else created under xdg. Gap 5 placement: after
    # the trap cleanup EXIT line. Comment lines count as neither export nor GODOT_BIN use.
    # Reading: the "no xdg/data or app_userdir" assertion looks at non-comment lines (a
    # comment creates nothing).
    problems = _gate_export_problems(GATE.read_text())
    assert not problems, "merge_gate.sh: " + "; ".join(problems)


def test_1b_merge_gate_block_comment_names_the_finding_and_sources():
    # INTERFACE item 1: the block's comment names FINDING-ambient-user-dir and its sources.
    text = GATE.read_text()
    assert "FINDING-ambient-user-dir" in text, "merge_gate.sh does not name FINDING-ambient-user-dir"
    assert "See also: scripts/run_godot_tests.sh, tests/qa/desktop/daemon_client.py" in text, \
        "merge_gate.sh block lacks the See also line"


def test_2_runner_with_xdg_unset_exports_a_temp_dir_and_leaves_the_real_user_dir_alone(tmp_path):
    # Spec test (2), gap 6: stub godot on PATH, XDG_DATA_HOME removed from the environment.
    real_data = _real_home() / ".local" / "share" / "data"
    before = _listing(real_data)
    env = _runner_env(tmp_path, preset=None)
    one_liner = REPO_ROOT / "tests" / "specfactory" / "test_gate_userdir.py"  # any existing file; stub ignores it
    r = subprocess.run(["bash", str(RUNNER), str(one_liner.relative_to(REPO_ROOT))], env=env,
                       cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120)
    after = _listing(real_data)
    rec = _read_record(tmp_path)
    assert r.returncode == 0, "stub run did not pass (rc=%d): %s" % (r.returncode, (r.stdout + r.stderr)[-400:])
    assert rec["xdg"] != "<unset>" and rec["xdg"] != "<no record>", \
        "runner left XDG_DATA_HOME unset for the godot it launched (record=%r)" % rec["xdg"]
    xdg = Path(rec["xdg"])
    assert str(xdg).startswith(str(tmp_path / "t") + os.sep), \
        "XDG_DATA_HOME %s is not under the temp root %s" % (xdg, tmp_path / "t")
    assert rec["existed_during_run"], "the exported XDG_DATA_HOME did not exist while godot ran"
    assert not xdg.exists(), "the runner did not remove its XDG_DATA_HOME %s on exit" % xdg
    assert before == after, "the real %s changed during the run" % real_data


def test_2b_runner_leaves_a_preset_xdg_data_home_alone(tmp_path):
    # Spec test (2), preset half: the gate's value wins and is never removed.
    preset = tmp_path / "preset_xdg"
    preset.mkdir()
    env = _runner_env(tmp_path, preset=preset)
    one_liner = "tests/specfactory/test_gate_userdir.py"
    r = subprocess.run(["bash", str(RUNNER), one_liner], env=env, cwd=str(REPO_ROOT),
                       capture_output=True, text=True, timeout=120)
    rec = _read_record(tmp_path)
    assert r.returncode == 0, "stub run did not pass (rc=%d): %s" % (r.returncode, (r.stdout + r.stderr)[-400:])
    assert rec["xdg"] == str(preset), "recorded XDG_DATA_HOME %r != preset %r" % (rec["xdg"], str(preset))
    assert preset.is_dir(), "the runner removed a caller-owned XDG_DATA_HOME"


def test_3_godot_env_returns_whole_child_env(tmp_path):
    # Spec test (3), gap 2 (G2 (a)): pure function, no Godot, no filesystem write.
    godot_env = getattr(dc, "godot_env", None)
    assert godot_env is not None, "tests/qa/desktop/daemon_client.py has no module function godot_env"
    scratch = tmp_path / "does_not_exist"
    save_dir = tmp_path / "saves"
    base = {"PATH": "/usr/bin", "HOME": "/h", "FOO": "bar",
            "DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0", "XAUTHORITY": "/x"}
    snapshot = copy.deepcopy(base)
    # LIBGL_ALWAYS_SOFTWARE="1" and GALLIUM_DRIVER="llvmpipe": daemon_client.py:160-161 on
    # origin/main (start() builds the env); OM_SAVE_DIR=str(self.save_dir): :159; the pops of
    # DISPLAY, WAYLAND_DISPLAY, XAUTHORITY: :157-158 (builder constraint 3: they stay in godot_env).
    got = godot_env(base, scratch, save_dir)
    expected = {"PATH": "/usr/bin", "HOME": "/h", "FOO": "bar",
                "OM_SAVE_DIR": str(save_dir), "LIBGL_ALWAYS_SOFTWARE": "1", "GALLIUM_DRIVER": "llvmpipe",
                "XDG_DATA_HOME": str(scratch / "xdg")}
    assert got == expected, "godot_env (no XDG in base): %r != %r" % (got, expected)
    assert base == snapshot, "godot_env mutated base_env"
    assert not scratch.exists(), "godot_env wrote to the filesystem (scratch exists)"
    # base's own XDG_DATA_HOME is returned unchanged
    got = godot_env({**base, "XDG_DATA_HOME": "/somewhere/else"}, scratch, save_dir)
    assert got["XDG_DATA_HOME"] == "/somewhere/else", "godot_env replaced the caller's XDG_DATA_HOME: %r" % got
    # an EMPTY value counts as unset
    got = godot_env({**base, "XDG_DATA_HOME": ""}, scratch, save_dir)
    assert got["XDG_DATA_HOME"] == str(scratch / "xdg"), "empty XDG_DATA_HOME not replaced: %r" % got
    # OM_SAVE_DIR absent when save_dir is None
    got = godot_env(base, scratch, None)
    assert "OM_SAVE_DIR" not in got, "OM_SAVE_DIR present with save_dir=None: %r" % got
    assert got["LIBGL_ALWAYS_SOFTWARE"] == "1" and got["GALLIUM_DRIVER"] == "llvmpipe"
    assert not scratch.exists(), "godot_env wrote to the filesystem (scratch exists)"
    # the same two XDG assertions as the positive control uses
    assert _env_xdg_ok(godot_env, scratch) == (True, True) and _env_keeps_caller_xdg(godot_env, scratch)


def _clean_env(monkeypatch, home: Path, xdg: Path | None) -> None:
    monkeypatch.setenv("HOME", str(home))
    if xdg is None:
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    else:
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg))


def _make_game(port: int = 47590):
    return dc.GodotGame(qa_port=port, seed=1)


def _drop(game) -> None:
    sc = Path(game.scratch)
    if str(sc).startswith(tempfile.gettempdir()) and sc.name.startswith("qa_flow_spine."):
        shutil.rmtree(sc, ignore_errors=True)


def test_4_user_dir_is_per_instance_from_the_launch_env(tmp_path, monkeypatch):
    # Spec test (4), gap 1 (G1 (b)). The spec word "start time" is read as "construction
    # time" (Architect ruling 2026-10-13/14; recorded as the reason in TD-HARNESS-qadir):
    # the dir is computed when the instance is built, never at import.
    home = tmp_path / "home"
    home.mkdir()
    xdg = tmp_path / "xdg_set"
    xdg.mkdir()
    _clean_env(monkeypatch, home, xdg)
    g = _make_game()
    try:
        assert getattr(g, "user_dir", None) == xdg / "data", \
            "GodotGame.user_dir (XDG set) = %r, want %s" % (getattr(g, "user_dir", None), xdg / "data")
        assert getattr(g.client, "user_dir", None) == xdg / "data", \
            "DaemonClient.user_dir (XDG set) = %r, want %s" % (getattr(g.client, "user_dir", None), xdg / "data")
    finally:
        _drop(g)


def test_4b_user_dir_unset_uses_the_game_scratch_xdg(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    _clean_env(monkeypatch, home, None)
    g = _make_game()
    try:
        want = Path(g.scratch) / "xdg" / "data"
        assert getattr(g, "user_dir", None) == want, "GodotGame.user_dir (XDG unset) = %r, want %s" % (getattr(g, "user_dir", None), want)
        assert (Path(g.scratch) / "xdg").is_dir(), "the scratch xdg dir does not exist right after construction"
        assert getattr(g.client, "user_dir", None) == want
        assert not (home / ".local").exists(), "construction touched the (fake) home"
    finally:
        _drop(g)


def test_4c_two_games_under_different_environments_keep_different_user_dirs(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    a, b = tmp_path / "xdg_a", tmp_path / "xdg_b"
    a.mkdir()
    b.mkdir()
    _clean_env(monkeypatch, home, a)
    g1 = _make_game(47591)
    _clean_env(monkeypatch, home, b)
    g2 = _make_game(47592)
    try:
        assert getattr(g1, "user_dir", None) == a / "data", "first game user_dir = %r" % (getattr(g1, "user_dir", None),)
        assert getattr(g2, "user_dir", None) == b / "data", \
            "second game user_dir = %r, want %s (per instance, not module state)" % (getattr(g2, "user_dir", None), b / "data")
    finally:
        _drop(g1)
        _drop(g2)


def test_4d_write_privacy_flag_is_an_instance_method_under_user_dir(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    xdg = tmp_path / "xdg_flag"
    xdg.mkdir()
    _clean_env(monkeypatch, home, xdg)
    g = _make_game()
    try:
        assert hasattr(g, "write_privacy_flag"), "GodotGame has no write_privacy_flag method"
        g.write_privacy_flag()
        assert (xdg / "data" / "privacy_accepted").is_file(), "no privacy_accepted under %s" % (xdg / "data")
        assert not (home / ".local").exists(), "write_privacy_flag touched the (fake) home"
    finally:
        _drop(g)
    # with XDG unset the flag lands in the game's scratch xdg
    _clean_env(monkeypatch, home, None)
    g = _make_game(47593)
    try:
        g.write_privacy_flag()
        assert (Path(g.scratch) / "xdg" / "data" / "privacy_accepted").is_file()
        assert not (home / ".local").exists(), "write_privacy_flag touched the (fake) home"
    finally:
        _drop(g)


def test_4e_module_has_no_import_time_user_dir_or_module_level_flag_writer():
    for name in ("_USER_DATA_DIR", "PRIVACY_FLAG_PATH", "write_privacy_flag"):
        assert not hasattr(dc, name), "daemon_client still exposes module-level %s" % name


def test_4f_import_time_constant_stub_fails_the_per_instance_assertion(tmp_path):
    # Positive control of spec test (4): an import-time constant (computed once, then the
    # env changes and a second game is built) gives the second game the first game's dir.
    a, b = tmp_path / "xdg_a", tmp_path / "xdg_b"
    frozen = a / "data"  # "computed once at import"
    second_game_user_dir = frozen  # an import-time constant cannot follow the changed env
    assert second_game_user_dir != b / "data", "import-time stub satisfied the per-instance assertion"


def test_5_sites_use_the_per_instance_user_dir():
    # Spec test (5) (sites, static) for the seven TD-HARNESS-qadir sites.
    bad = {}
    for rel in SITES:
        v = _site_violations((REPO_ROOT / rel).read_text())
        if v:
            bad[rel] = v
    assert not bad, "sites still on the machine user dir: " + "; ".join("%s: %s" % (k, v) for k, v in bad.items())


def test_5b_flow_spine_saves_root_and_privacy_flag_order():
    text = (REPO_ROOT / "tests/qa/desktop/test_flow_spine.py").read_text()
    assert re.search(r'\.user_dir\b.{0,80}?["\']saves["\']', text, re.DOTALL), \
        "test_flow_spine.py saves root does not use <game>.user_dir / \"saves\""
    assert not re.search(r"(?<![.\w])write_privacy_flag\b", text), \
        "test_flow_spine.py still uses the module-level write_privacy_flag"
    m = re.search(r"def test_s_c8_07\w*\(.*?(?=\ndef |\Z)", text, re.DOTALL)
    assert m, "S-C8-07 test not found"
    body = m.group(0)
    i_ctor, i_flag, i_start = body.find("GodotGame("), body.find(".write_privacy_flag()"), body.find(".start()")
    assert -1 < i_ctor < i_flag < i_start, \
        "S-C8-07 order wrong (GodotGame( at %d, .write_privacy_flag() at %d, .start() at %d)" % (i_ctor, i_flag, i_start)


# ---------------------------------------------------------------------------
# Spec test (6) / gap 3: the planted-settings control, display-bound.
# ---------------------------------------------------------------------------

_NEEDS = [t for t in ("xvfb-run", "godot") if shutil.which(t) is None]
_skip_display = pytest.mark.skipif(bool(_NEEDS), reason="needs %s on PATH (display-bound control)" % ", ".join(_NEEDS or ["xvfb-run", "godot"]))


def _boot_to_tactical_qa(fake_home: Path, xdg: Path | None, monkeypatch) -> dict:
    """Boot the real game through GodotGame with HOME=fake_home and the given XDG_DATA_HOME
    (None = removed from the process environment), walk to the tactical view, return qa."""
    if not (REPO_ROOT / "pipe" / "ouroboros_pipe").exists():  # autoload/c_bridge.gd loads res://pipe/ouroboros_pipe
        pytest.skip("pipe/ouroboros_pipe not built: run make pipe/ouroboros_pipe")
    from test_ground_era import _to_tactical  # noqa: PLC0415 (tests/qa/desktop on sys.path)
    _clean_env(monkeypatch, fake_home, xdg)
    g = dc.GodotGame(qa_port=dc.pick_free_port(), seed=1, reset_privacy_flag=False)
    g.start()
    try:
        g.wait_for_port(timeout=60.0)
        _to_tactical(g)
        return g.client.state()["result"]["qa"]
    finally:
        g.stop()
        _drop(g)


def _plant(fake_home: Path) -> Path:
    real = _real_home()
    assert fake_home != real and real not in fake_home.parents, "fake home %s is inside the real home" % fake_home
    data = fake_home / ".local" / "share" / "data"
    data.mkdir(parents=True)
    (data / "settings.cfg").write_text('[game]\nera_id="greek_placeholder"\n')
    return data


@pytest.fixture()
def isolated_qa(tmp_path, monkeypatch):
    fake_home = tmp_path / "fake_home_isolated"
    _plant(fake_home)
    monkeypatch.setenv("HOME", str(fake_home))
    assert Path.home() == fake_home and Path.home() != _real_home(), "Path.home() is the real home"
    return _boot_to_tactical_qa(fake_home, None, monkeypatch)


@pytest.fixture()
def visible_qa(tmp_path, monkeypatch):
    fake_home = tmp_path / "fake_home_visible"
    _plant(fake_home)
    monkeypatch.setenv("HOME", str(fake_home))
    assert Path.home() == fake_home and Path.home() != _real_home(), "Path.home() is the real home"
    return _boot_to_tactical_qa(fake_home, fake_home / ".local" / "share", monkeypatch)


@_skip_display
def test_6_planted_settings_in_the_home_do_not_change_the_era(isolated_qa):
    # Spec test (6) / Architect 2026-10-12: "a planted data/settings.cfg in the real home does
    # not change qa_state() era" (planted in a FAKE home here, gap 3). XDG_DATA_HOME removed
    # from the process environment: the child must not read the fake home's settings.cfg.
    gk = _ground_keys(isolated_qa)
    assert not gk, "planted settings.cfg in the home reached the game (era changed): ground keys %s" % sorted(gk)


@_skip_display
def test_6b_detector_control_planted_settings_change_the_era_when_visible(visible_qa):
    # Detector control for (6): the same plant made visible (XDG_DATA_HOME=<fake>/.local/share)
    # gives a NON-empty _ground_keys(qa): the plant works, so the isolation case can fail.
    gk = _ground_keys(visible_qa)
    assert gk, "detector control: planted era_id greek_placeholder produced no ground layer; keys=%s" % sorted(visible_qa)


def test_7_merge_gate_builds_the_pipe_before_the_first_regression_stage():
    # Architect ruling 2026-10-14 (A): specfactory_regression boots Godot (test_6/6b), which
    # needs pipe/ouroboros_pipe; the transport stage builds it too late. By text.
    problems = _pipe_before_regression_problems(GATE.read_text())
    assert not problems, "merge_gate.sh: " + "; ".join(problems)
