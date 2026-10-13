# spec: scripts/specfactory/pre_gate.sh (method rev 2, the two-tier gate; piece HARNESS-pregate)
"""Tests for scripts/specfactory/pre_gate.sh: noise check, revert gate, tests.

Each case builds a throwaway git repo in tmp_path (one base commit on branch
"base", HEAD one commit ahead) and a stub merge gate that the script reaches
through PRE_GATE_MERGE_GATE. The script is run by its repo path from the real
repo root; it is absent until the builder lands it, so every test that runs it
is red for that reason until then.
"""
import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "pre_gate.sh"

LINE_RE = re.compile(r"^PRE_GATE (noise|gate|tests|verdict) (OK|REJECT|WARN)\b")

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
        (repo / name).write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "-q", "base")
    for name in head_delete:
        _git(repo, "rm", "-q", name)
    head_add = {"head.txt": "head\n"} if head_add is None else head_add
    for name, text in head_add.items():
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
    assert not LINE_RE.match("GATE make OK")


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
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0),
               env_extra={"MERGE_GATE_PIECES": "/some/pieces.toml"})
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
    assert (tmp_path / "gate_pieces.txt").read_text() == "/some/pieces.toml"


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


# DRAFT-pregate-spec-env: the lint runs only when PRE_GATE_SPEC is set (piece HARNESS-provenance).
# Spec: Rev 12b, HARNESS-provenance paragraph: "an untagged fixture under PRE_GATE_SPEC makes pre_gate.sh exit non-zero".
def test_pre_gate_spec_env_runs_provenance_lint(tmp_path):
    repo = _make_repo(tmp_path, head_add={
        "spec.md": "The tile shows 5 wu of rubble when the player clicks.\n"})
    stub = _stub_gate(tmp_path, "GATE make OK", 0)
    # (a) PRE_GATE_SPEC unset (empty counts as unset): no provenance output at all.
    unset = _run(repo, stub, env_extra={"PRE_GATE_SPEC": ""})
    assert not any("provenance" in l for l in _lines(unset)), unset.stdout + unset.stderr
    assert _lines(unset)[-1] == "PRE_GATE verdict OK"
    assert unset.returncode == 0
    # (b) PRE_GATE_SPEC=spec.md: the untagged paragraph is a reason (1) finding.
    res = _run(repo, stub, env_extra={"PRE_GATE_SPEC": "spec.md"})
    out = _lines(res)
    assert any(l.startswith("PRE_GATE provenance REJECT spec.md") for l in out), res.stdout + res.stderr
    assert any(":1: (1)" in l for l in out), res.stdout + res.stderr
    assert out[-1] == "PRE_GATE verdict REJECT"
    assert res.returncode != 0
