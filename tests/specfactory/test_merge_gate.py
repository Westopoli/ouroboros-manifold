# spec: docs/northstar/plans/briefs/2026-09-22-two-day-push.md, item 1
#       and docs/northstar/plans/2026-10-19-harness-enforcement-spec.md section 1 HARNESS-C1b and section 2 (rev 3a)
# Rule pins: R-990-01@?
"""Tests for scripts/specfactory/merge_gate.sh's own orchestration (exit
codes, step lines). The individual mechanisms it calls into --
footprint_check, symbol_ownership_check, regression_check -- have their own
unit tests in test_merge_gate_support.py against synthetic repos; this file
covers what only the shell script itself can be responsible for getting
right: the harness-timeout path (never counted as a regression, distinct
exit code, immediate stop) and that a REJECT-level step still prints its own
line. The full accept/reject path against the real ABI (libm_lint,
suite_regression, acceptance ids, checksum_trace) is exercised for real in
docs/northstar/proving_ground/evidence/push_2026-09-22/gate_replays.md --
those need the genuine csrc/tests/csim tree this repo's own scratch fixture
does not reproduce.

HARNESS-C1b extends this file at the bottom: stage `status` after the look stage ("`merge_gate.sh` stage `status`
rejects on a DRIFT fixture and passes a WARN fixture (the gate test harness's stub pattern)"; the stage runs
`"$PYTHON" "$GATE_DIR/status_check.py" --repo "$REPO_ROOT" --base "$BASE_REF"`, `reject` on any `STATUS <check>
DRIFT` line, `warn` on `STATUS <check> WARN`) and stage `rule_pins` "AFTER the `--revert` exit, full gate only,
the single-owner pattern with `reject` on REJECT and `warn` on WARN". The stub pattern: the gate finds every tool
beside itself (GATE_DIR), so a fake repo root holds symlinks to every real file of scripts/specfactory except the
stubbed tools, which are written in place and print canned lines; REPO_ROOT is then the fake root. Fixture id
R-990-01 appears only in a canned stub line: pinned @? above. The `rule_pins` stub cases are the section 1 body
text, beyond the one Tests-first sentence that names merge_gate (reported).
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GATE = REPO / "scripts" / "specfactory" / "merge_gate.sh"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_fixture_repo(base_dir: Path, *, makefile: str) -> Path:
    repo = base_dir
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    (repo / "csrc").mkdir()
    (repo / "csrc" / "stub.c").write_text("int om_stub(void) { return 0; }\n")
    (repo / "Makefile").write_text(makefile)
    (repo / "tests").mkdir()
    (repo / "tests" / "csim").mkdir()
    (repo / "tests" / "qa").mkdir()
    (repo / "tests" / "qa" / "t1").mkdir()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _write_pieces(path: Path, pieces: list[dict]) -> None:
    lines = []
    for p in pieces:
        lines.append("[[piece]]")
        lines.append(f'id = "{p["id"]}"')
        owns = p.get("owns", [])
        lines.append("owns = [" + ", ".join(f'"{o}"' for o in owns) + "]")
        acc = p.get("acceptance", [])
        lines.append("acceptance = [" + ", ".join(f'"{a}"' for a in acc) + "]")
        lines.append(f'depends_on = []')
        lines.append("")
    path.write_text("\n".join(lines))


SLEEPY_MAKEFILE = """\
.PHONY: all
libouroboros.so:
\tsleep 30 && touch $@
libouroboros_dbg.so:
\tsleep 30 && touch $@
"""

FAST_MAKEFILE = """\
libouroboros.so:
\ttouch $@
libouroboros_dbg.so:
\ttouch $@
"""


def test_positive_control_make_timeout_gives_exit_3(tmp_path):
    repo = _init_fixture_repo(tmp_path / "repo", makefile=SLEEPY_MAKEFILE)
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/stub.c"], "acceptance": []}])

    env = {"MERGE_GATE_PIECES": str(pieces), "MERGE_GATE_MAKE_TIMEOUT": "1", "PATH": "/usr/bin:/bin"}
    proc = subprocess.run(
        ["bash", str(GATE), str(repo), "HEAD", "B1"],
        capture_output=True, text=True, env=env, timeout=30,
    )
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "GATE make HARNESS" in proc.stdout


def test_every_step_before_the_first_reject_prints_a_line(tmp_path):
    """Not a reject scenario itself (fixture has no real ABI to check
    acceptance/regression against meaningfully) -- proves the mechanical
    contract: `make` and `libm_lint` and `alg_constants` and `footprint`
    each print their own `GATE <name> ...` line in order."""
    repo = _init_fixture_repo(tmp_path / "repo", makefile=FAST_MAKEFILE)
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/stub.c"], "acceptance": []}])

    env = {"MERGE_GATE_PIECES": str(pieces), "PATH": "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"}
    proc = subprocess.run(
        ["bash", str(GATE), str(repo), "HEAD", "B1"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    for step in ("make", "libm_lint", "alg_constants", "footprint", "symbol_ownership"):
        assert f"GATE {step} " in proc.stdout, proc.stdout + proc.stderr


def test_acceptance_increment_warns_full_id_rejects(tmp_path):
    """Straggler rule end-to-end (F6 item 1, straggler follow-up): a red
    acceptance test rejects under the FULL piece id, but the identical
    candidate submitted under an INCREMENT id of that piece (B10-2, push
    plan straggler rule) warns instead, naming the green/red split."""
    repo = _init_fixture_repo(tmp_path / "repo", makefile=FAST_MAKEFILE)
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{
        "id": "B10",
        "owns": ["tests/accept/test_a.py"],
        "acceptance": ["tests/accept/test_a.py::test_pass", "tests/accept/test_a.py::test_fail"],
    }])

    (repo / "tests" / "accept").mkdir()
    (repo / "tests" / "accept" / "test_a.py").write_text(
        "def test_pass():\n    assert True\n\n"
        "def test_fail():\n    assert False\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    env = {"MERGE_GATE_PIECES": str(pieces), "PATH": "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"}

    full = subprocess.run(
        ["bash", str(GATE), str(repo), "HEAD~1", "B10"],
        capture_output=True, text=True, env=env, timeout=90,
    )
    assert "GATE acceptance REJECT" in full.stdout, full.stdout + full.stderr

    increment = subprocess.run(
        ["bash", str(GATE), str(repo), "HEAD~1", "B10-2"],
        capture_output=True, text=True, env=env, timeout=90,
    )
    assert "GATE acceptance WARN" in increment.stdout, increment.stdout + increment.stderr
    assert "increment B10-2 of B10: 1/2 acceptance ids green" in increment.stdout
    assert "GATE acceptance REJECT" not in increment.stdout


FAKE_GODOT = """\
#!/usr/bin/env bash
echo "$@" >> "$GODOT_ARGS_LOG"
exit 0
"""


def test_godot_import_runs_before_desktop_acceptance_and_not_for_csim_piece(tmp_path):
    """C8's test_flow_spine.py (tests/qa/desktop/) launches the real game
    against the candidate worktree, which has no .godot/imported cache;
    without an import first, the boot fails on missing imports before its
    own assertions run (gate gap, 2026-09-22). A fake `godot` on PATH
    stands in for the real import (~60-90s); this only proves ordering and
    that a csim-only piece pays nothing."""
    repo = _init_fixture_repo(tmp_path / "repo", makefile=FAST_MAKEFILE)
    (repo / "tests" / "qa" / "desktop").mkdir()
    (repo / "tests" / "qa" / "desktop" / "test_x.py").write_text(
        "def test_pass():\n    assert True\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [
        {"id": "D1", "owns": ["tests/qa/desktop/test_x.py"],
         "acceptance": ["tests/qa/desktop/test_x.py::test_pass"]},
        {"id": "B1", "owns": ["csrc/stub.c"], "acceptance": []},
    ])

    fake_bin = tmp_path / "fakebin"
    fake_bin.mkdir()
    godot_path = fake_bin / "godot"
    godot_path.write_text(FAKE_GODOT)
    godot_path.chmod(0o755)
    args_log = tmp_path / "godot_args.log"
    fake_venv = tmp_path / "fake_venv"
    fake_venv.mkdir()

    env = {
        "MERGE_GATE_PIECES": str(pieces),
        "PATH": f"{fake_bin}:/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin",
        "GODOT_ARGS_LOG": str(args_log),
        "MERGE_GATE_VENV": str(fake_venv),
    }

    desktop = subprocess.run(
        ["bash", str(GATE), str(repo), "HEAD~1", "D1"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert "GATE godot_import OK" in desktop.stdout, desktop.stdout + desktop.stderr
    import_line = next(i for i, l in enumerate(desktop.stdout.splitlines()) if "GATE godot_import" in l)
    accept_line = next(i for i, l in enumerate(desktop.stdout.splitlines()) if "GATE acceptance " in l)
    assert import_line < accept_line, desktop.stdout
    assert "--import" in args_log.read_text()
    assert "--headless" in args_log.read_text()
    # TD-gate-venv-unlink: the gate removes the link before the playthrough stage (FINDING-gate-venv-link-vs-fresh-checkout)
    assert not (repo / ".venv").exists() and not (repo / ".venv").is_symlink(), "no .venv may remain in the candidate"
    assert fake_venv.is_dir(), "only the link goes, the target is untouched"
    venv_line = next(i for i, l in enumerate(desktop.stdout.splitlines()) if "venv_link" in l)
    assert venv_line < import_line, desktop.stdout

    args_log.write_text("")
    csim_only = subprocess.run(
        ["bash", str(GATE), str(repo), "HEAD~1", "B1"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert "GATE godot_import" not in csim_only.stdout, csim_only.stdout + csim_only.stderr
    assert "venv_link" not in csim_only.stdout, csim_only.stdout
    # TD-GATE-playthrough-import: the acceptance-stage import is not run for a
    # csim-only piece (no GATE godot_import line, no acceptance venv_link); a godot
    # import made by the playthrough stage (csrc diff) is allowed, so args_log is
    # not asserted empty.
    assert "GATE playthrough" in csim_only.stdout, csim_only.stdout


def test_unknown_candidate_dir_is_a_usage_error():
    proc = subprocess.run(
        ["bash", str(GATE), "/nonexistent/path", "HEAD", "B1"],
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 2


# ---- HARNESS-C1b: stages rule_pins (after the --revert exit) and status (after the look stage) -----------------------

SPEC_DIR = REPO / "scripts" / "specfactory"
GATE_PATH = "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"


def _stub_tool(lines, rc):
    """A stand-in for status_check.py / rule_pins*.py: records argv beside itself, prints canned lines, exits rc."""
    body = "".join(f"print({l!r})\n" for l in lines)
    return ("import sys\nfrom pathlib import Path\n"
            "Path(__file__).with_suffix('.argv').write_text('\\n'.join(sys.argv[1:]))\n"
            + body + f"sys.exit({rc})\n")


def _fake_root(tmp_path: Path, stubs: dict) -> Path:
    """Fake repo root: docs/ and every file of scripts/specfactory symlinked, except the stubbed tool names."""
    root = tmp_path / "fakeroot"
    (root / "scripts" / "specfactory").mkdir(parents=True)
    (root / "docs").symlink_to(REPO / "docs")
    for f in SPEC_DIR.iterdir():
        if f.name not in stubs:
            (root / "scripts" / "specfactory" / f.name).symlink_to(f)
    for name, text in stubs.items():
        (root / "scripts" / "specfactory" / name).write_text(text)
    return root


def _gate_run(tmp_path: Path, stubs: dict, *flags: str):
    """Run the fake root's merge_gate.sh on the fixture repo; returns (stdout lines, completed process, fake root)."""
    root = _fake_root(tmp_path, stubs)
    repo = _init_fixture_repo(tmp_path / "repo", makefile=FAST_MAKEFILE)
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/stub.c"], "acceptance": []}])
    env = {"MERGE_GATE_PIECES": str(pieces), "PATH": GATE_PATH}
    gate = root / "scripts" / "specfactory" / "merge_gate.sh"
    proc = subprocess.run(["bash", str(gate), *flags, str(repo), "HEAD", "B1"],
                          capture_output=True, text=True, env=env, timeout=60)
    return proc.stdout.splitlines(), proc, root


def _stage(lines, name):
    return [l for l in lines if l.startswith(f"GATE {name} ")]


STATUS_OK = _stub_tool(["STATUS pins OK 0 files 0 ids"], 0)
STATUS_WARN = _stub_tool(["STATUS pins WARN 1 stale"], 0)
STATUS_DRIFT = _stub_tool(["STATUS pins WARN 1 stale", "STATUS register DRIFT 2 rows"], 1)
PINS_OK = _stub_tool(["PINS OK 1 files 1 ids"], 0)
PINS_WARN = _stub_tool(["PINS WARN unknown rule R-990-01 in tests/test_x.py"], 0)
PINS_REJECT = _stub_tool(["PINS REJECT tests/test_x.py:1 R-990-01 stale 000000 b2a3c8"], 1)
RULE_PINS_QUIET = _stub_tool(["PINS OK 0 files 0 ids"], 0)


def test_control_stub_harness_runs_the_real_stages_to_the_look_line(tmp_path):
    """Green today: the fake root runs the gate to the end; the status_check stub is not called yet (no stage)."""
    lines, proc, root = _gate_run(tmp_path, {"status_check.py": STATUS_OK})
    for step in ("make", "owner_lint", "look"):
        assert _stage(lines, step), proc.stdout + proc.stderr
    assert [i for i, l in enumerate(lines) if l.startswith("GATE owner_lint ")][0] < \
        [i for i, l in enumerate(lines) if l.startswith("GATE look ")][0]
    assert (root / "scripts" / "specfactory" / "merge_gate.sh").is_symlink()
    assert (root / "scripts" / "specfactory" / "status_check.py").is_file()


def test_control_revert_mode_prints_no_rule_pins_or_status_line(tmp_path):
    """Green today and after: a revert never trips on a restored test, and stops before the later stages."""
    lines, proc, root = _gate_run(tmp_path, {"status_check.py": STATUS_DRIFT, "rule_pins_tests.py": PINS_REJECT,
                                             "rule_pins.py": PINS_REJECT}, "--revert")
    assert _stage(lines, "owner_lint"), proc.stdout + proc.stderr
    assert not _stage(lines, "rule_pins") and not _stage(lines, "status"), proc.stdout
    assert not (root / "scripts" / "specfactory" / "status_check.argv").exists()
    assert not (root / "scripts" / "specfactory" / "rule_pins_tests.argv").exists()


def test_status_stage_rejects_a_drift_line(tmp_path):
    lines, proc, root = _gate_run(tmp_path, {"status_check.py": STATUS_DRIFT})
    status = _stage(lines, "status")
    assert status and status[0].startswith("GATE status REJECT"), proc.stdout + proc.stderr
    assert proc.returncode == 1, proc.stdout + proc.stderr


def test_status_stage_passes_a_warn_line(tmp_path):
    lines, proc, root = _gate_run(tmp_path, {"status_check.py": STATUS_WARN})
    status = _stage(lines, "status")
    assert status and status[0].startswith("GATE status WARN"), proc.stdout + proc.stderr
    assert not any(l.startswith("GATE status REJECT") for l in lines), proc.stdout


def test_status_stage_ok_when_every_check_is_ok(tmp_path):
    lines, proc, root = _gate_run(tmp_path, {"status_check.py": STATUS_OK})
    status = _stage(lines, "status")
    assert status and status[0].startswith("GATE status OK"), proc.stdout + proc.stderr


def test_status_stage_comes_after_look_and_is_called_with_repo_and_base(tmp_path):
    lines, proc, root = _gate_run(tmp_path, {"status_check.py": STATUS_OK})
    look = [i for i, l in enumerate(lines) if l.startswith("GATE look ")]
    status = [i for i, l in enumerate(lines) if l.startswith("GATE status ")]
    assert look and status and look[0] < status[0], proc.stdout + proc.stderr
    argv = (root / "scripts" / "specfactory" / "status_check.argv").read_text().splitlines()
    assert argv[0] == "--repo" and os.path.realpath(argv[1]) == os.path.realpath(root), argv
    origin_main = _git(tmp_path / "repo", "rev-parse", "origin/main").stdout.strip()
    assert argv[2:] == ["--base", origin_main], argv


def test_rule_pins_stage_rejects_on_a_pins_reject(tmp_path):
    lines, proc, root = _gate_run(tmp_path, {"status_check.py": STATUS_OK, "rule_pins_tests.py": PINS_REJECT,
                                             "rule_pins.py": RULE_PINS_QUIET})
    stage = _stage(lines, "rule_pins")
    assert stage and stage[0].startswith("GATE rule_pins REJECT"), proc.stdout + proc.stderr
    assert proc.returncode == 1


def test_rule_pins_stage_warns_on_a_pins_warn_and_is_ok_on_ok(tmp_path):
    warn_lines, warn_proc, _ = _gate_run(tmp_path / "w", {"status_check.py": STATUS_OK, "rule_pins_tests.py": PINS_WARN,
                                                          "rule_pins.py": RULE_PINS_QUIET})
    stage = _stage(warn_lines, "rule_pins")
    assert stage and stage[0].startswith("GATE rule_pins WARN"), warn_proc.stdout + warn_proc.stderr
    ok_lines, ok_proc, _ = _gate_run(tmp_path / "o", {"status_check.py": STATUS_OK, "rule_pins_tests.py": PINS_OK,
                                                      "rule_pins.py": RULE_PINS_QUIET})
    stage = _stage(ok_lines, "rule_pins")
    assert stage and stage[0].startswith("GATE rule_pins OK"), ok_proc.stdout + ok_proc.stderr


def test_rule_pins_stage_comes_after_owner_lint(tmp_path):
    lines, proc, root = _gate_run(tmp_path, {"status_check.py": STATUS_OK, "rule_pins_tests.py": PINS_OK,
                                             "rule_pins.py": RULE_PINS_QUIET})
    owner = [i for i, l in enumerate(lines) if l.startswith("GATE owner_lint ")]
    pins = [i for i, l in enumerate(lines) if l.startswith("GATE rule_pins ")]
    assert owner and pins and owner[0] < pins[0], proc.stdout + proc.stderr
