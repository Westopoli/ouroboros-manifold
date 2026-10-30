# spec: docs/northstar/plans/push/pieces.toml row HARNESS-gate-keep-red-evidence (FINDING-c2-5-pixels-red-under-gate,
#       FINDING-baseline-cache-perturb-key, DRAFT-evidence-age, DRAFT-evidence-cap) and the interface rulings T1 to T9 and
#       D1 to D5 in scripts/specfactory/workflows/vg-wave15-harness-keepred.js (no visible-game spec paragraph exists)
# Rule pins: R-990-01@?
"""Proves what HARNESS-gate-keep-red-evidence builds in merge_gate.sh / merge_gate_support.py / drift_audit.md.

UNSTATED INTERFACE CHOICES made by this file (the builder follows these or stops with a test-defect):
  * A stage header line in REPORT.txt is any line containing the stage name (`playthrough` or `lane_plays`); the exact
    wording is not pinned. The ids that are new (T5) appear anywhere in REPORT.txt.
  * The playthrough/lane_plays CLI is driven as `merge_gate_support.py playthrough <dir> HEAD --target <file> --force
    --no-setup --known-red <file>` with MERGE_GATE_EVIDENCE_ROOT, MERGE_GATE_START_UTC and MERGE_GATE_PIECE_ID in the
    environment; the stage keeps files found under $XDG_DATA_HOME/**/qa/*.png (T3).
  * The merge_gate.sh dynamic case (T4) stubs merge_gate_support.py in a fake root: the stub answers the playthrough and
    lane_plays subcommands with canned lines and hands every other subcommand to the real file.
  * The cap test (T9) writes three 20 MiB PNG files with ascending mtimes; the oldest is dropped, and REPORT.txt names it.
  * Twins: each "is not kept" case (green on main by design) has a twin that is red on main for the no-evidence reason.
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
sys.path.insert(0, str(SPEC_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import merge_gate_support as mgs  # noqa: E402
import test_merge_gate as tmg  # noqa: E402
from gate_toy_root import write_story  # noqa: E402

SUPPORT = SPEC_DIR / "merge_gate_support.py"
GATE = SPEC_DIR / "merge_gate.sh"
PY = sys.executable
START = "20261023-1200"
RED = ("import os, pathlib\n"
       "def test_s_planted_break():\n"
       "    q = pathlib.Path(os.environ['XDG_DATA_HOME']) / 'data' / 'qa'\n"
       "    q.mkdir(parents=True, exist_ok=True)\n"
       "    (q / 'shot.png').write_bytes(b'\\x89PNG-fixture')\n"
       "    assert False\n")
GREEN = RED.replace("assert False", "assert True").replace("break", "ok")


# ---------------------------------------------------------------- fixtures

def _env(tmp_path, **extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("MERGE_GATE_EVIDENCE_ROOT", "MERGE_GATE_START_UTC", "MERGE_GATE_PIECE_ID", "MALLOC_PERTURB_")}
    env.update(MERGE_GATE_EVIDENCE_ROOT=str(tmp_path / "evidence"), XDG_DATA_HOME=str(tmp_path / "xdg"),
               MERGE_GATE_START_UTC=START, MERGE_GATE_PIECE_ID="PA,PB")
    env.update(extra)
    return {k: v for k, v in env.items() if v is not None}


def _cand(tmp_path, body, known=""):
    cand = tmp_path / "cand"
    cand.mkdir(exist_ok=True)
    (cand / "test_flow_planted.py").write_text(body)
    (tmp_path / "known_red.txt").write_text(known)
    return cand


def _pt(tmp_path, body, known="", timeout=120, **extra):
    cand = _cand(tmp_path, body, known)
    return subprocess.run([PY, str(SUPPORT), "playthrough", str(cand), "HEAD", "--python", PY, "--timeout", str(timeout),
                           "--known-red", str(tmp_path / "known_red.txt"), "--target", "test_flow_planted.py",
                           "--force", "--no-setup"],
                          capture_output=True, text=True, env=_env(tmp_path, **extra), timeout=180)


def _runs(tmp_path):
    root = tmp_path / "evidence"
    return sorted(root.iterdir()) if root.exists() else []


def _evidence(tmp_path):
    runs = _runs(tmp_path)
    assert len(runs) == 1, f"expected one run directory under the evidence root, got {runs}"
    return runs[0]


def _lane_repo(tmp_path, play_body, known=""):
    """A git repo whose second commit touches foo/a.txt; lane x owns foo/*; one play under plays/x/."""
    repo = tmp_path / "lrepo"
    play = repo / "tests" / "qa" / "desktop" / "plays" / "x"
    play.mkdir(parents=True)
    (play / "test_play_x.py").write_text(play_body)
    (repo / "foo").mkdir()
    (repo / "foo" / "a.txt").write_text("1\n")
    tmg._git(repo, "init", "-q")
    tmg._git(repo, "config", "user.email", "g@t")
    tmg._git(repo, "config", "user.name", "g")
    write_story(repo, "B1")  # H-020
    tmg._git(repo, "add", "-A")
    tmg._git(repo, "commit", "-q", "-m", "one")
    (repo / "foo" / "a.txt").write_text("2\n")
    tmg._git(repo, "add", "-A")
    tmg._git(repo, "commit", "-q", "-m", "two")
    (tmp_path / "lane_map.toml").write_text('[lanes]\nx = ["foo/*"]\n')
    (tmp_path / "lane_known.txt").write_text(known)
    return repo


def _lp(tmp_path, repo, **extra):
    return subprocess.run([PY, str(SUPPORT), "lane_plays", str(repo), "HEAD~1", "--python", PY, "--timeout", "120",
                           "--known-red", str(tmp_path / "lane_known.txt"), "--lane-map", str(tmp_path / "lane_map.toml")],
                          capture_output=True, text=True, env=_env(tmp_path, **extra), timeout=180)


# ---------------------------------------------------------------- controls (green on main)

def test_control_planted_red_and_green_behave_as_today(tmp_path, monkeypatch):
    """R-990-01 control: the planted red play returns ok False naming the test, the planted green ok True (bare call)."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    cand = _cand(tmp_path, RED)
    ok, detail = mgs.playthrough_check(cand, "HEAD", python_exe=PY, timeout=120, known_red_path=tmp_path / "known_red.txt",
                                       target="test_flow_planted.py", force=True, setup=False)
    assert not ok and "test_s_planted_break" in detail
    cand = _cand(tmp_path, GREEN)
    ok, detail = mgs.playthrough_check(cand, "HEAD", python_exe=PY, timeout=120, known_red_path=tmp_path / "known_red.txt",
                                       target="test_flow_planted.py", force=True, setup=False)
    assert ok, detail


def _perturbed(text, suite):
    """T8 detector: True when every merge_gate_support.py `regression` command naming `suite` carries the env prefix.

    Test-defect TD-HARNESS-gate-reorder-5 (ruler Architect 2026-10-29): HARNESS-gate-concurrent starts each suite as a
    background job whose command line begins with `TMPDIR=... XDG_DATA_HOME=... \\` and HARNESS-csim-xdist gives csim and
    transport a serial and an xdist branch. So the prefix is looked for anywhere before the script (not only at the
    line start) and on every command naming the suite, not only the first (decisive line: `assert (False)` in
    `_perturbed(text, 'tests/csim')`)."""
    logical = re.sub(r"\\\n\s*", " ", text)
    found = []
    for line in logical.splitlines():
        if "merge_gate_support.py" in line and re.search(r"\bregression\b(?!-)", line) \
                and re.search(r"\s" + re.escape(suite) + r"(\s|$)", line):
            found.append(bool(re.search(r"(^|\s)MALLOC_PERTURB_=255\s", line.split("merge_gate_support.py")[0])))
    if not found:
        raise AssertionError(f"no regression command naming {suite} found")
    return all(found)


def test_control_t8_detector_sees_prefix_and_its_absence():
    bare = '"$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$C" "$B" tests/csim \\\n    --python "$PYTHON"\n'
    pre = "    MALLOC_PERTURB_=255 " + bare.lstrip()
    assert not _perturbed(bare, "tests/csim")
    assert _perturbed(pre, "tests/csim")


# ---------------------------------------------------------------- T3/T4: a red keeps its evidence

def test_red_stage_keeps_pytest_output_and_names_the_path(tmp_path):
    """R-990-01 T2/T3/T4: pytest_rA.txt holds the failing assertion; the EVIDENCE line names the run directory."""
    r = _pt(tmp_path, RED)
    assert r.returncode != 0 and "REJECT" in r.stdout and "test_s_planted_break" in r.stdout, r.stdout + r.stderr
    run = _evidence(tmp_path)
    assert run.name == f"{START}-PA", run.name
    assert f"EVIDENCE {run}" in r.stdout.splitlines(), r.stdout
    assert "assert False" in (run / "playthrough" / "pytest_rA.txt").read_text()


def test_red_stage_copies_its_own_new_png(tmp_path):
    """R-990-01 T3 twin: the red stage's own new PNG IS copied, name and mtime kept."""
    _pt(tmp_path, RED)
    png = _evidence(tmp_path) / "playthrough" / "shot.png"
    assert png.is_file() and png.read_bytes() == b"\x89PNG-fixture"
    assert abs(png.stat().st_mtime - time.time()) < 3600


def test_png_older_than_the_stage_run_is_not_copied_but_the_new_one_is(tmp_path):
    """R-990-01 T3: an earlier green stage's PNG (mtime unchanged) is left out; the twin new PNG is in."""
    old = tmp_path / "xdg" / "data" / "qa" / "earlier.png"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"earlier")
    os.utime(old, (1_700_000_000, 1_700_000_000))
    _pt(tmp_path, RED)
    sub = _evidence(tmp_path) / "playthrough"
    assert (sub / "shot.png").is_file()
    assert not (sub / "earlier.png").exists()


def test_symlinked_directory_under_xdg_is_not_followed(tmp_path):
    """R-990-01 T3: xdg/godot/export_templates is a symlink; PNGs behind it are not copied; the real PNG is."""
    other = tmp_path / "other" / "qa"
    other.mkdir(parents=True)
    (other / "sneaky.png").write_bytes(b"sneaky")
    link = tmp_path / "xdg" / "godot" / "export_templates"
    link.parent.mkdir(parents=True)
    link.symlink_to(tmp_path / "other")
    _pt(tmp_path, RED)
    sub = _evidence(tmp_path) / "playthrough"
    assert (sub / "shot.png").is_file()
    assert not (sub / "sneaky.png").exists()


def test_clashing_png_names_get_a_numeric_suffix(tmp_path):
    """R-990-01 T3: two new PNGs of one name (different directories) are kept as shot.png and shot-2.png."""
    body = RED.replace("    assert False", "    d = q.parent.parent / 'second' / 'qa'\n    d.mkdir(parents=True)\n"
                       "    (d / 'shot.png').write_bytes(b'other')\n    assert False")
    _pt(tmp_path, body)
    sub = _evidence(tmp_path) / "playthrough"
    assert {p.name for p in sub.glob("*.png")} == {"shot.png", "shot-2.png"}


# ---------------------------------------------------------------- T5/T6: which stages keep nothing

def test_green_stage_creates_nothing(tmp_path):
    """R-990-01 T6: a green stage creates no run directory and prints no EVIDENCE line."""
    r = _pt(tmp_path, GREEN)
    assert r.returncode == 0 and "EVIDENCE" not in r.stdout, r.stdout + r.stderr
    assert not _runs(tmp_path)


def test_known_red_keeps_nothing(tmp_path):
    """R-990-01 T5: a red already in the known-red list keeps no evidence (stage ends OK)."""
    r = _pt(tmp_path, RED, known="test_s_planted_break\n")
    assert r.returncode == 0 and "EVIDENCE" not in r.stdout, r.stdout + r.stderr
    assert not _runs(tmp_path)


def test_suite_missing_and_no_tests_ran_keep_nothing(tmp_path):
    """R-990-01 T5: the rejects `suite missing` and `no tests ran` keep nothing."""
    r = subprocess.run([PY, str(SUPPORT), "playthrough", str(tmp_path), "HEAD", "--python", PY, "--target", "nope.py",
                        "--force", "--no-setup"], capture_output=True, text=True, env=_env(tmp_path))
    assert r.returncode != 0 and "missing" in r.stdout and not _runs(tmp_path), r.stdout
    r = _pt(tmp_path, "x = 1\n")
    assert r.returncode != 0 and "no tests ran" in r.stdout and "EVIDENCE" not in r.stdout, r.stdout
    assert not _runs(tmp_path)


def test_bare_functions_write_nothing_and_return_as_today(tmp_path):
    """R-990-01 EVIDENCE ONLY FROM THE CLI: playthrough_check called bare writes nothing under the evidence root."""
    cand = _cand(tmp_path, RED)
    os.environ["MERGE_GATE_EVIDENCE_ROOT"] = str(tmp_path / "evidence")
    os.environ["XDG_DATA_HOME"] = str(tmp_path / "xdg")
    try:
        ok, detail = mgs.playthrough_check(cand, "HEAD", python_exe=PY, timeout=120,
                                           known_red_path=tmp_path / "known_red.txt", target="test_flow_planted.py",
                                           force=True, setup=False)
    finally:
        del os.environ["MERGE_GATE_EVIDENCE_ROOT"], os.environ["XDG_DATA_HOME"]
    assert not ok and isinstance(detail, str)
    assert not _runs(tmp_path)


def test_cli_path_keeps_evidence_where_the_bare_call_does_not(tmp_path):
    """R-990-01 twin of the bare-call case: the same red through main() keeps a run directory."""
    _pt(tmp_path, RED)
    assert len(_runs(tmp_path)) == 1


def test_timeout_keeps_partial_output_and_still_rejects(tmp_path):
    """R-990-01 T5 (D3): a timed-out stage rejects, prints the EVIDENCE line and leaves pytest_rA.txt."""
    body = "import time\ndef test_s_slow():\n    time.sleep(60)\n"
    r = _pt(tmp_path, body, timeout=3)
    assert r.returncode != 0 and "timed out" in r.stdout, r.stdout + r.stderr
    run = _evidence(tmp_path)
    assert f"EVIDENCE {run}" in r.stdout.splitlines()
    assert (run / "playthrough" / "pytest_rA.txt").is_file()


# ---------------------------------------------------------------- T2/T6: run directory and REPORT.txt

def test_report_lists_the_rest_of_the_piece_list_and_the_new_red_ids(tmp_path):
    """R-990-01 T2/T5: the run directory takes the first piece id; REPORT.txt lists the rest and the new red id."""
    _pt(tmp_path, RED)
    report = (_evidence(tmp_path) / "REPORT.txt").read_text()
    assert "PB" in report and "test_s_planted_break" in report


def test_without_piece_or_start_variable_the_directory_is_nopiece_with_a_utc_stamp(tmp_path):
    """R-990-01 T2: MERGE_GATE_PIECE_ID and MERGE_GATE_START_UTC unset: <YYYYMMDD-HHMM>-nopiece."""
    _pt(tmp_path, RED, MERGE_GATE_START_UTC=None, MERGE_GATE_PIECE_ID=None)
    assert re.fullmatch(r"\d{8}-\d{4}-nopiece", _evidence(tmp_path).name)


def test_report_is_appended_by_a_later_stage_never_overwritten(tmp_path):
    """R-990-01 T6: playthrough then lane_plays share one run directory; REPORT.txt gains a header for each stage."""
    _pt(tmp_path, RED)
    run = _evidence(tmp_path)
    first = (run / "REPORT.txt").read_text()
    repo = _lane_repo(tmp_path, "def test_play_x():\n    assert False\n")
    r = _lp(tmp_path, repo)
    assert r.returncode != 0 and f"EVIDENCE {run}" in r.stdout.splitlines(), r.stdout + r.stderr
    second = (run / "REPORT.txt").read_text()
    assert second.startswith(first) and len(second) > len(first)
    assert "playthrough" in second and "lane_plays" in second


def test_lane_plays_keeps_only_red_play_output_under_a_header(tmp_path):
    """R-990-01 T3: lane_plays/pytest_rA.txt holds each RED play under `### play: <repo-relative path>`."""
    repo = _lane_repo(tmp_path, "def test_play_x():\n    assert False\n")
    r = _lp(tmp_path, repo)
    assert r.returncode != 0 and "REJECT" in r.stdout, r.stdout + r.stderr
    text = (_evidence(tmp_path) / "lane_plays" / "pytest_rA.txt").read_text()
    assert "### play: tests/qa/desktop/plays/x/test_play_x.py" in text


def test_lane_plays_stale_known_red_keeps_nothing(tmp_path):
    """R-990-01 T5: a stale-known-red reject (lane_plays only) keeps nothing."""
    repo = _lane_repo(tmp_path, "def test_play_x():\n    assert True\n",
                      known="tests/qa/desktop/plays/x/test_play_x.py::test_play_x\n")
    r = _lp(tmp_path, repo)
    assert r.returncode != 0 and "stale known-red" in r.stdout and "EVIDENCE" not in r.stdout, r.stdout + r.stderr
    assert not _runs(tmp_path)


# ---------------------------------------------------------------- T9: size cap

def test_stage_directory_over_the_cap_drops_the_oldest_file(tmp_path):
    """R-990-01 T9 (DRAFT-evidence-cap 52,428,800 bytes): oldest dropped until at or under the cap, named in REPORT.txt."""
    mib = 20 * 1024 * 1024
    body = ("import os, pathlib\n"
            "def test_s_big():\n"
            "    q = pathlib.Path(os.environ['XDG_DATA_HOME']) / 'data' / 'qa'\n"
            "    q.mkdir(parents=True, exist_ok=True)\n"
            "    import time; now = time.time()\n"
            "    for i, n in enumerate(('a.png', 'b.png', 'c.png')):\n"
            f"        f = q / n; f.write_bytes(b''); os.truncate(f, {mib}); os.utime(f, (now - 30 + i * 10,) * 2)\n"
            "    assert False\n")
    _pt(tmp_path, body)
    run = _evidence(tmp_path)
    sub = run / "playthrough"
    assert sum(p.stat().st_size for p in sub.glob("*.png")) <= 52_428_800
    assert not (sub / "a.png").exists() and (sub / "b.png").exists() and (sub / "c.png").exists()
    assert "a.png" in (run / "REPORT.txt").read_text()


# ---------------------------------------------------------------- T4: merge_gate.sh strips and echoes

STUB_SUPPORT = ("import os, sys\n"
                "REAL = %r\n"
                "if sys.argv[1] == 'playthrough':\n"
                "    print('REJECT red outside known-red list: test_stub'); print('EVIDENCE /abs/run/dir'); sys.exit(1)\n"
                "if sys.argv[1] == 'lane_plays':\n"
                "    print('REJECT red outside known-red list: play_stub'); print('EVIDENCE /abs/run/dir'); sys.exit(1)\n"
                "os.execv(sys.executable, [sys.executable, REAL, *sys.argv[1:]])\n") % str(SUPPORT)


def test_gate_strips_the_evidence_line_and_echoes_the_path_after_each_reject(tmp_path):
    """R-990-01 T4: `GATE <stage> REJECT ...` without the EVIDENCE text, then exactly `GATE evidence kept: <dir>`."""
    lines, proc, _root = tmg._gate_run(tmp_path, {"merge_gate_support.py": STUB_SUPPORT})
    for stage in ("playthrough", "lane_plays"):
        i = next(n for n, l in enumerate(lines) if l.startswith(f"GATE {stage} REJECT"))
        assert "EVIDENCE" not in lines[i] and "/abs/run/dir" not in lines[i], lines[i]
        assert lines[i + 1] == "GATE evidence kept: /abs/run/dir", proc.stdout + proc.stderr
    assert not any(l.startswith("EVIDENCE") for l in lines)


# ---------------------------------------------------------------- T7: prune

def _prune_fixture(tmp_path):
    root = tmp_path / "evidence"
    root.mkdir()
    old = time.time() - 10 * 86400
    new = time.time() - 1 * 86400
    outside = tmp_path / "outside_target"
    outside.mkdir()
    (outside / "keep.txt").write_text("x")
    made = {}
    for name, kind in (("20260101-0000-OLD", "dir"), ("20261022-0000-NEW", "dir"), ("20260101-0001-file", "file"),
                       ("notes", "dir"), ("20260101-0002-link", "link")):
        p = root / name
        if kind == "dir":
            p.mkdir()
        elif kind == "file":
            p.write_text("x")
        else:
            p.symlink_to(outside)
        if kind != "link":
            os.utime(p, (new if "NEW" in name else old,) * 2)
        else:
            os.utime(p, (old, old), follow_symlinks=False)
        made[name] = p
    return root, made, outside


def _check_pruned(root, made, outside, out):
    assert f"pruned: {made['20260101-0000-OLD']}" in out.splitlines(), out
    assert not made["20260101-0000-OLD"].exists()
    for name in ("20261022-0000-NEW", "20260101-0001-file", "notes", "20260101-0002-link"):
        assert os.path.lexists(made[name]), name
    assert (outside / "keep.txt").exists()
    assert out.count("pruned:") == 1, out


def test_prune_subcommand_deletes_only_old_run_directories(tmp_path):
    """R-990-01 T7 (DRAFT-evidence-age 7 days): old run dir goes; new dir, old file, `notes`, old symlink stay."""
    root, made, outside = _prune_fixture(tmp_path)
    r = subprocess.run([PY, str(SUPPORT), "prune-evidence"], capture_output=True, text=True, env=_env(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    _check_pruned(root, made, outside, r.stdout)


def test_gate_prune_evidence_mode_runs_the_subcommand(tmp_path):
    """R-990-01 T7: `merge_gate.sh --prune-evidence` (no other argument) does the same."""
    root, made, outside = _prune_fixture(tmp_path)
    r = subprocess.run(["bash", str(GATE), "--prune-evidence"], capture_output=True, text=True, env=_env(tmp_path),
                       timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    _check_pruned(root, made, outside, r.stdout)


def test_drift_audit_page_carries_the_prune_exception_and_cleanup_line():
    """R-990-01 T7: ONE weekly cleanup line under When and the Exception sentence in the verbatim brief."""
    text = (REPO / "docs/northstar/plans/workflows_2026-10-07/drift_audit.md").read_text()
    line = ("the weekly run invokes merge_gate.sh --prune-evidence, which deletes only run directories under "
            "MERGE_GATE_EVIDENCE_ROOT (default ~/Projects/om-push/gate-evidence/) older than 7 days (DRAFT-evidence-age); "
            "it touches nothing in the repo; the auditor stays read-only for the repo")
    assert text.count(line) == 1
    assert text.index("## When") < text.index(line) < text.index("## Who")
    sentence = ("Exception: after the report, run merge_gate.sh --prune-evidence once; it deletes only run directories "
                "under MERGE_GATE_EVIDENCE_ROOT older than 7 days and touches nothing in the repo.")
    brief = text[text.index("## The brief"):text.index("## The schema")]
    assert sentence in brief and brief.index("Edit nothing, commit nothing") < brief.index(sentence)


# ---------------------------------------------------------------- T8 / D5: MALLOC_PERTURB_

def test_gate_puts_the_perturb_prefix_on_the_csim_and_transport_commands_only():
    """R-990-01 T8: MALLOC_PERTURB_=255 prefixes the csim and transport regression commands; no other literal."""
    text = GATE.read_text()
    assert _perturbed(text, "tests/csim") and _perturbed(text, "tests/transport")
    assert not _perturbed(text, "tests/qa/t1") and not _perturbed(text, "tests/specfactory")
    code = [l for l in text.splitlines() if "MALLOC_PERTURB_" in l and not l.lstrip().startswith("#")]
    assert len(code) == 5, code  # TD-HARNESS-gate-reorder-5, TD-HARNESS-gate-tiers-4: the count follows the number of csim/transport call sites (2, then 4 with xdist, then 5 with the fast-tier csim call)
    assert all("tests/csim" in l or "tests/transport" in l or "CSIM_ARGS" in l for l in code), code


def test_perturb_sites_carry_a_see_also_and_report_records_the_env_line(tmp_path):
    """R-990-01 T8: `# See also` at both sites; REPORT.txt of a kept run holds the env line."""
    for f in (GATE, SUPPORT):
        assert re.search(r"#.*See also.*MALLOC_PERTURB_|#.*MALLOC_PERTURB_.*See also", f.read_text()), f.name
    _pt(tmp_path, RED)
    assert "env: MALLOC_PERTURB_=255 on the csim and transport stages of merge_gate.sh" in \
        (_evidence(tmp_path) / "REPORT.txt").read_text()


def _cache_repo(base):
    repo = base / "crepo"
    (repo / "tests" / "t").mkdir(parents=True)
    tmg._git(repo, "init", "-q")
    tmg._git(repo, "config", "user.email", "g@t")
    tmg._git(repo, "config", "user.name", "g")
    (repo / "tests" / "t" / "test_a.py").write_text("def test_a():\n    assert True\n")
    write_story(repo, "B1")  # H-020
    tmg._git(repo, "add", "-A")
    tmg._git(repo, "commit", "-q", "-m", "main")
    return repo


def _regress(repo, tmp_path, **extra):
    env = _env(tmp_path, MERGE_GATE_BASELINE_CACHE=str(tmp_path / "bcache"), **extra)
    return subprocess.run([PY, str(SUPPORT), "regression", str(repo), "HEAD", "tests/t", "--python", PY, "--no-junit",
                           "--merge-root", str(tmp_path / "root")], capture_output=True, text=True, env=env, timeout=120)


def test_baseline_cache_is_not_shared_between_perturbed_and_unperturbed_runs(tmp_path):
    """R-990-01 D5 (FINDING-baseline-cache-perturb-key): a perturbed call never reuses an unperturbed baseline."""
    repo = _cache_repo(tmp_path)
    assert "baseline: computed" in _regress(repo, tmp_path).stdout
    perturbed = _regress(repo, tmp_path, MALLOC_PERTURB_="255")
    assert "baseline: computed" in perturbed.stdout, perturbed.stdout + perturbed.stderr
    assert "baseline: cached" in _regress(repo, tmp_path, MALLOC_PERTURB_="255").stdout


def test_unperturbed_key_is_unchanged_so_old_cache_entries_stay_valid(tmp_path):
    """R-990-01 D5 control: with MALLOC_PERTURB_ unset the second call is still `cached` (green on main)."""
    repo = _cache_repo(tmp_path)
    _regress(repo, tmp_path)
    assert "baseline: cached" in _regress(repo, tmp_path).stdout
