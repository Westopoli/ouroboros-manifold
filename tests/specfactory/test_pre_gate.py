# spec: scripts/specfactory/pre_gate.sh (method rev 2, the two-tier gate; piece HARNESS-pregate)
#       and docs/northstar/plans/2026-10-19-harness-enforcement-spec.md section 1 HARNESS-C1b and section 2 (rev 3a)
# Rule pins: R-990-01@?
"""Tests for scripts/specfactory/pre_gate.sh: noise check, revert gate, tests.

Each case builds a throwaway git repo in tmp_path (one base commit on branch
"base", HEAD one commit ahead) and a stub merge gate that the script reaches
through PRE_GATE_MERGE_GATE. The script is run by its repo path from the real
repo root; it is absent until the builder lands it, so every test that runs it
is red for that reason until then.

HARNESS-C1b (the enforcement spec, section 1 HARNESS-C1b and section 2) extends this file at the bottom: step
`pins` after the tests step ("`pre_gate.sh` with a candidate that changes a test with a stale pin prints
`PRE_GATE pins REJECT` and exit 1, a candidate changing an unrelated file prints `PRE_GATE pins WARN` and exit 0")
and step `provenance` for every spec of the landing ("a row without a `spec` key prints `PRE_GATE provenance
WARN no spec key for <id>`"). Fixture id R-990-01 (rule line in the fixture epics only): pinned @? above.
Moved under ledger row TD-HARNESS-C1: LINE_RE gains pins|provenance; test_clean_repo_ok_stub_passes_through
reads a real pieces file (the provenance step reads it); part (a) of
test_pre_gate_spec_env_runs_provenance_lint (absence of the lint without the env var) is retired by section 2
and replaced by test_provenance_warns_for_a_row_without_a_spec_key.
UNSTATED INTERFACE (reported): pre_gate.sh reads the pieces file from MERGE_GATE_PIECES, the variable the
brief's pre-gate line and the stub gate already use.
"""
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_spec_provenance import EPIC_TEXT, LEDGER_TEXT, PASSING_SPEC, REGISTER_TEXT  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "pre_gate.sh"

LINE_RE = re.compile(r"^PRE_GATE (noise|gate|tests|story|pins|provenance|verdict) (OK|REJECT|WARN)\b")

PASSING_TEST = "def test_ok():\n    assert 1 + 1 == 2\n"
FAILING_TEST = "def test_bad():\n    assert 1 + 1 == 3\n"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout


def _make_repo(tmp_path: Path, base_files=None, head_add=None, head_delete=()) -> Path:
    """Base commit (branch "base") plus one HEAD commit that adds/deletes files."""
    repo = tmp_path / "wt"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "commit.gpgsign", "false")
    for name, text in (base_files or {"readme.txt": "base\n"}).items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "-q", "base")
    for name in head_delete:
        _git(repo, "rm", "-q", name)
    head_add = {"head.txt": "head\n"} if head_add is None else head_add
    for name, text in head_add.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
        _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "head")
    return repo


def _stub_gate(tmp_path: Path, line: str, status: int) -> Path:
    """Stub merge gate: records argv and MERGE_GATE_PIECES, prints one line."""
    stub = tmp_path / "stub_gate.sh"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > "{tmp_path}/gate_args.txt"\n'
        f'printf "%s" "${{MERGE_GATE_PIECES:-}}" > "{tmp_path}/gate_pieces.txt"\n'
        f"echo '{line}'\n"
        f"exit {status}\n")
    stub.chmod(0o755)
    return stub


def _pieces(tmp_path: Path, ids, specs=None) -> Path:
    """A pieces.toml with one row per id; specs maps id -> the `spec =` path (rows not in it have no spec key)."""
    rows = []
    for pid in ids:
        row = f'[[piece]]\nid = "{pid}"\nowns = []\ndepends_on = []\n'
        if specs and pid in specs:
            row += f'spec = "{specs[pid]}"\n'
        rows.append(row)
    path = tmp_path / "pieces.toml"
    path.write_text("\n".join(rows))
    return path


def _run(repo: Path, stub: Path, *extra: str, pieces: str = "P-1",
         env_extra=None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PRE_GATE_MERGE_GATE"] = str(stub)
    env.update(env_extra or {})
    return subprocess.run(["bash", str(SCRIPT), str(repo), "base", pieces, *extra],
                          cwd=REPO, env=env, capture_output=True, text=True)


def _lines(res: subprocess.CompletedProcess):
    return res.stdout.splitlines()


# ---- positive controls: pass today, prove the harness itself works ----------

def test_control_fixture_repo_builds(tmp_path):
    repo = _make_repo(tmp_path)
    assert _git(repo, "rev-list", "--count", "base..HEAD").strip() == "1"
    assert _git(repo, "status", "--porcelain").strip() == ""
    stub = _stub_gate(tmp_path, "GATE make OK", 0)
    res = subprocess.run([str(stub), "--revert"], capture_output=True, text=True)
    assert res.returncode == 0 and "GATE make OK" in res.stdout


def test_control_format_regex_matches_hand_written_lines():
    assert LINE_RE.match("PRE_GATE noise OK clean")
    assert LINE_RE.match("PRE_GATE gate REJECT GATE footprint REJECT x")
    assert LINE_RE.match("PRE_GATE tests WARN no tests given")
    assert LINE_RE.match("PRE_GATE verdict REJECT")
    assert LINE_RE.match("PRE_GATE pins REJECT tests/test_a.py")
    assert LINE_RE.match("PRE_GATE pins WARN 1 stale outside the diff")
    assert LINE_RE.match("PRE_GATE provenance WARN no spec key for P-1")
    assert not LINE_RE.match("GATE make OK")


def test_control_format_regex_accepts_story_line_and_rejects_old_spelling():
    """H-032 control: LINE_RE takes the `story` step and still refuses the PREGATE spelling and a verdict-less pins line."""
    assert LINE_RE.match("PRE_GATE story OK 1 paths")
    assert not LINE_RE.match("PREGATE story OK 1 paths")
    assert not LINE_RE.match("PREGATE pins OK skipped: no csrc change")
    assert not LINE_RE.match("PRE_GATE pins skipped: no csrc change")
    assert LINE_RE.match("PRE_GATE pins OK skipped: no csrc change")


# ---- the script ---------------------------------------------------------------

def test_script_exists():
    assert SCRIPT.is_file(), f"{SCRIPT} is missing"


def test_untracked_uid_is_noise_reject(tmp_path):
    repo = _make_repo(tmp_path)
    (repo / "foo.uid").write_text("uid://abc\n")
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0))
    noise = [l for l in _lines(res) if l.startswith("PRE_GATE noise ")]
    assert noise and noise[0].startswith("PRE_GATE noise REJECT"), res.stdout + res.stderr
    assert "foo.uid" in noise[0]
    assert _lines(res)[-1] == "PRE_GATE verdict REJECT"
    assert res.returncode == 1


def test_clean_repo_ok_stub_passes_through(tmp_path):
    repo = _make_repo(tmp_path)
    pieces = _pieces(tmp_path, ["P-1"])
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0),
               env_extra={"MERGE_GATE_PIECES": str(pieces)})
    out = _lines(res)
    assert any(l.startswith("PRE_GATE noise OK") for l in out), res.stdout + res.stderr
    assert "GATE make OK" in out
    assert out[-1] == "PRE_GATE verdict OK"
    assert res.returncode == 0
    for l in out:
        assert l.startswith("GATE ") or LINE_RE.match(l), l
    # noise precedes the gate lines, verdict last
    noise_i = next(i for i, l in enumerate(out) if l.startswith("PRE_GATE noise "))
    assert noise_i < out.index("GATE make OK")
    # the gate was called as: --revert <wt> <base> <piece ids>, env passed through
    args = (tmp_path / "gate_args.txt").read_text().splitlines()
    assert args == ["--revert", str(repo), "base", "P-1"]
    assert (tmp_path / "gate_pieces.txt").read_text() == str(pieces)


def test_story_id_prints_story_line_and_every_line_has_the_prefix(tmp_path):
    """H-032: "Every line pre_gate.sh prints starts `PRE_GATE <step>`, as its header says". A story file in the
    toy repo (Machine lines: Flag harness, Tests naming its stub test) and its id as the piece id make
    `PRE_GATE story OK <n> paths` print; every non-`GATE ` line then matches LINE_RE (DEC-pregate-line-prefix-2026-10-31,
    ruling A: the no-csrc pins skip is `PRE_GATE pins OK skipped: no csrc change`)."""
    story = ("# H-990: stub\n\n## Machine lines\n\nFlag: harness\nTests: tests/test_stub_h990.py\n")
    repo = _make_repo(tmp_path, head_add={"docs/stories/H-990.md": story,
                                          "tests/test_stub_h990.py": PASSING_TEST})
    pieces = _pieces(tmp_path, ["H-990"])
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0), pieces="H-990",
               env_extra={"MERGE_GATE_PIECES": str(pieces), "PRE_GATE_PYTHON": sys.executable})
    out = _lines(res)
    assert "PRE_GATE story OK 1 paths" in out, res.stdout + res.stderr
    bad = [l for l in out if not (l.startswith("GATE ") or LINE_RE.match(l))]
    assert not bad, bad
    assert out[-1] == "PRE_GATE verdict OK"
    assert res.returncode == 0


def test_reject_stub_is_gate_reject(tmp_path):
    repo = _make_repo(tmp_path)
    res = _run(repo, _stub_gate(tmp_path, "GATE footprint REJECT x", 1))
    out = _lines(res)
    assert any(l.startswith("PRE_GATE gate REJECT") for l in out), res.stdout + res.stderr
    assert "GATE footprint REJECT x" in out
    assert out[-1] == "PRE_GATE verdict REJECT"
    assert res.returncode == 1


def test_new_script_with_its_uid_is_noise_ok(tmp_path):
    """Positive control for the NOTE-uid-files exception."""
    repo = _make_repo(tmp_path, head_add={"a.gd": "extends Node\n"})
    (repo / "a.gd.uid").write_text("uid://abc\n")
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0))
    noise = [l for l in _lines(res) if l.startswith("PRE_GATE noise ")]
    assert noise and noise[0].startswith("PRE_GATE noise OK"), res.stdout + res.stderr
    assert _lines(res)[-1] == "PRE_GATE verdict OK"
    assert res.returncode == 0


def test_uid_beside_unadded_script_is_noise_reject(tmp_path):
    """The exception needs a.gd added in the diff; a stray b.gd.uid is noise."""
    repo = _make_repo(tmp_path, head_add={"a.gd": "extends Node\n"})
    (repo / "b.gd.uid").write_text("uid://abc\n")
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0))
    noise = [l for l in _lines(res) if l.startswith("PRE_GATE noise ")]
    assert noise and noise[0].startswith("PRE_GATE noise REJECT"), res.stdout + res.stderr
    assert "b.gd.uid" in noise[0]
    assert res.returncode == 1


def test_deleted_import_is_noise_reject(tmp_path):
    repo = _make_repo(tmp_path, base_files={"readme.txt": "base\n", "x.glb.import": "i\n"},
                      head_add={"head.txt": "head\n"}, head_delete=["x.glb.import"])
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0))
    noise = [l for l in _lines(res) if l.startswith("PRE_GATE noise ")]
    assert noise and noise[0].startswith("PRE_GATE noise REJECT"), res.stdout + res.stderr
    assert "x.glb.import" in noise[0]
    assert _lines(res)[-1] == "PRE_GATE verdict REJECT"
    assert res.returncode == 1


def test_tests_step_passing_and_failing(tmp_path):
    repo = _make_repo(tmp_path, head_add={"test_tiny_ok.py": PASSING_TEST,
                                          "test_tiny_bad.py": FAILING_TEST})
    stub = _stub_gate(tmp_path, "GATE make OK", 0)
    ok = _run(repo, stub, "test_tiny_ok.py")
    assert any(l.startswith("PRE_GATE tests OK") for l in _lines(ok)), ok.stdout + ok.stderr
    assert _lines(ok)[-1] == "PRE_GATE verdict OK"
    assert ok.returncode == 0
    bad = _run(repo, stub, "test_tiny_bad.py")
    assert any(l.startswith("PRE_GATE tests REJECT") for l in _lines(bad)), bad.stdout + bad.stderr
    assert _lines(bad)[-1] == "PRE_GATE verdict REJECT"
    assert bad.returncode == 1


def test_no_tests_given_warns(tmp_path):
    repo = _make_repo(tmp_path)
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0))
    assert any(l.startswith("PRE_GATE tests WARN") and "no tests given" in l
               for l in _lines(res)), res.stdout + res.stderr
    assert _lines(res)[-1] == "PRE_GATE verdict OK"


def test_fewer_than_three_args_is_usage_exit_2(tmp_path):
    repo = _make_repo(tmp_path)
    env = dict(os.environ, PRE_GATE_MERGE_GATE=str(_stub_gate(tmp_path, "GATE make OK", 0)))
    res = subprocess.run(["bash", str(SCRIPT), str(repo), "base"], cwd=REPO, env=env,
                         capture_output=True, text=True)
    assert res.returncode == 2, res.stdout + res.stderr
    assert "usage" in (res.stdout + res.stderr).lower()


# DRAFT-pregate-spec-env: PRE_GATE_SPEC keeps working as an extra path (piece HARNESS-provenance; section 2 of the
# enforcement spec: "`PRE_GATE_SPEC` keeps working as an extra path").
# Spec: Rev 12b, HARNESS-provenance paragraph: "an untagged fixture under PRE_GATE_SPEC makes pre_gate.sh exit non-zero".
# TD-HARNESS-C1: part (a) of this test (no provenance output at all without the env var) is retired by section 2
# (a piece row without a spec key now prints a provenance WARN line) and lives on as the case at the bottom.
# ---- HARNESS-C1b: step pins (after tests) and step provenance (section 2) ---------------------------------------
# Fixture: the rule line of test_spec_provenance.py:34-60 (R-990-01) lives in the throwaway repo's epics; the pin of
# that line is b2a3c8 (section 3 formula, computed once; the control below proves it with the C1a tool).

RULE_PIN = "b2a3c8"
STALE_PIN = "000000"
EPICS = {"docs/bible/epics/E-99-test.md": EPIC_TEXT,
         "docs/northstar/ambiguity_register.md": REGISTER_TEXT,
         "docs/northstar/plans/push_ledger_2026-09-22.md": LEDGER_TEXT}


def _pinned_test(pin: str) -> str:
    return f"# Rule pins: R-990-01@{pin}\ndef test_x():\n    \"\"\"R-990-01\"\"\"\n    assert True\n"


def _pins_lines(res):
    return [l for l in _lines(res) if l.startswith("PRE_GATE pins ")]


def test_control_c1b_fixtures_the_pin_literal_and_the_c1a_tool_agree(tmp_path):
    """Green today: the epics fixture is readable by rule_pins.py (C1a) and gives the literal; planted stale tag flagged."""
    repo = _make_repo(tmp_path, base_files={"readme.txt": "base\n", **EPICS}, head_add={
        "good.md": f"# S\n\nThe lot draws 7 rows. [B R-990-01@{RULE_PIN}: words]\n",
        "bad.md": f"# S\n\nThe lot draws 7 rows. [B R-990-01@{STALE_PIN}: words]\n"})
    tool = REPO / "scripts" / "specfactory" / "rule_pins.py"
    run = lambda f: subprocess.run([sys.executable, str(tool), "check", f], cwd=repo, capture_output=True, text=True)
    assert run("good.md").returncode == 0
    bad = run("bad.md")
    assert bad.returncode == 1 and "stale" in bad.stdout, bad.stdout
    pieces = _pieces(tmp_path, ["P-1"])
    assert tomllib.loads(pieces.read_text())["piece"][0]["id"] == "P-1"


def test_pins_step_rejects_a_changed_test_with_a_stale_pin(tmp_path):
    repo = _make_repo(tmp_path, base_files={"readme.txt": "base\n", **EPICS},
                      head_add={"tests/test_a.py": _pinned_test(STALE_PIN)})
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0),
               env_extra={"MERGE_GATE_PIECES": str(_pieces(tmp_path, ["P-1"]))})
    pins = _pins_lines(res)
    assert any(l.startswith("PRE_GATE pins REJECT") for l in pins), res.stdout + res.stderr
    assert _lines(res)[-1] == "PRE_GATE verdict REJECT"
    assert res.returncode == 1


def test_pins_step_passes_a_changed_test_with_the_right_pin(tmp_path):
    """Pair of the reject case: the same candidate with the correct pin has a pins line and no REJECT."""
    repo = _make_repo(tmp_path, base_files={"readme.txt": "base\n", **EPICS},
                      head_add={"tests/test_a.py": _pinned_test(RULE_PIN)})
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0),
               env_extra={"MERGE_GATE_PIECES": str(_pieces(tmp_path, ["P-1"]))})
    pins = _pins_lines(res)
    assert pins and not any(l.startswith("PRE_GATE pins REJECT") for l in pins), res.stdout + res.stderr
    assert _lines(res)[-1] == "PRE_GATE verdict OK"
    assert res.returncode == 0


def test_pins_step_warns_and_exits_0_when_the_candidate_changes_an_unrelated_file(tmp_path):
    """The stale test is on the base, outside the diff; the diff is one unrelated file."""
    repo = _make_repo(tmp_path, base_files={"readme.txt": "base\n", "tests/test_old.py": _pinned_test(STALE_PIN), **EPICS},
                      head_add={"notes.txt": "unrelated\n"})
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0),
               env_extra={"MERGE_GATE_PIECES": str(_pieces(tmp_path, ["P-1"]))})
    pins = _pins_lines(res)
    assert any(l.startswith("PRE_GATE pins WARN") for l in pins), res.stdout + res.stderr
    assert not any(l.startswith("PRE_GATE pins REJECT") for l in pins)
    assert _lines(res)[-1] == "PRE_GATE verdict OK"
    assert res.returncode == 0


def test_steps_come_in_order_noise_gate_tests_pins_verdict(tmp_path):
    repo = _make_repo(tmp_path, base_files={"readme.txt": "base\n", **EPICS})
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0),
               env_extra={"MERGE_GATE_PIECES": str(_pieces(tmp_path, ["P-1"]))})
    steps = []
    for l in _lines(res):
        if l.startswith("PRE_GATE ") and (not steps or steps[-1] != l.split()[1]):
            steps.append(l.split()[1])
    # H-006 retired the provenance step (docs/stories/H-006.md; Test-defect, H-020): no spec read without pieces.toml.
    assert steps == ["noise", "gate", "tests", "pins", "verdict"], res.stdout + res.stderr


FU_ROW = "FU-HARNESS-findings"
