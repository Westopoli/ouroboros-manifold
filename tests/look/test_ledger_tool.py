"""Tests for scripts/look/ledger.py (story look-judge-rig, spec piece 4: ledger).

CLI contract assumed (the builder must match; gap reported to the Architect):
  python3 -m scripts.look.ledger validate <ledger.toml>        exit 0 ok, nonzero + message on error
  python3 -m scripts.look.ledger list <ledger.toml>            one row id per line
  python3 -m scripts.look.ledger reopen <ledger.toml> <id>     prints reopen_command
  python3 -m scripts.look.ledger verify <ledger.toml> <id>     prints PASS or FAIL, exit 0 only on PASS
  python3 -m scripts.look.ledger replace <ledger.toml> <old_id> <new_rows.toml>
        appends the new row(s); the old row keeps its place and gains superseded_by = <new id>
Each row is a [[row]] table with an `id` key plus the spec fields.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = ["requirements", "sha", "scene", "fight_or_layout", "seed",
            "reopen_command", "frames", "words", "date", "trace_hash", "source"]
TRACE = "tick 1\ntick 2\n"
TRACE_HASH = hashlib.sha256(TRACE.encode()).hexdigest()


def head_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run(*args):
    return subprocess.run([sys.executable, "-m", "scripts.look.ledger", *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True)


def row(rid="r1", **over):
    r = {"id": rid, "requirements": ["R-001-01"], "sha": head_sha(), "scene": "lab",
         "fight_or_layout": "F1", "seed": 7,
         "reopen_command": f"{sys.executable} -c \"import sys;sys.stdout.write('tick 1\\ntick 2\\n')\"",
         "frames": ["f1.png"], "words": "looks right", "date": "2026-11-18",
         "trace_hash": TRACE_HASH, "source": "chat"}
    r.update(over)
    return r


def toml_val(v):
    if isinstance(v, list):
        return "[" + ", ".join(toml_val(x) for x in v) + "]"
    if isinstance(v, int):
        return str(v)
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def write(path, rows):
    out = []
    for r in rows:
        out.append("[[row]]")
        out += [f"{k} = {toml_val(v)}" for k, v in r.items()]
        out.append("")
    path.write_text("\n".join(out))
    return path


def test_positive_control_valid_ledger_validates(tmp_path):
    """spec piece 4 (validate): a complete row passes."""
    p = write(tmp_path / "l.toml", [row()])
    r = run("validate", p)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize("field", REQUIRED)
def test_validate_rejects_missing_field(tmp_path, field):
    """spec piece 4: a row missing any required field is rejected."""
    r_ = row()
    del r_[field]
    p = write(tmp_path / "l.toml", [r_])
    r = run("validate", p)
    assert r.returncode != 0
    assert field in r.stdout + r.stderr


def test_validate_rejects_unknown_sha(tmp_path):
    """spec piece 4: a sha not present in `git cat-file -e` is rejected."""
    p = write(tmp_path / "l.toml", [row(sha="0123456789abcdef0123456789abcdef01234567")])
    assert run("validate", p).returncode != 0


@pytest.mark.parametrize("words", ["", "   "])
def test_validate_rejects_empty_words(tmp_path, words):
    """spec piece 4: `words` (verbatim) must not be empty."""
    p = write(tmp_path / "l.toml", [row(words=words)])
    assert run("validate", p).returncode != 0


def test_list_prints_ids(tmp_path):
    """spec piece 4 (list): prints every row id."""
    p = write(tmp_path / "l.toml", [row("alpha"), row("beta")])
    r = run("list", p)
    assert r.returncode == 0
    assert "alpha" in r.stdout and "beta" in r.stdout


def test_reopen_prints_stored_command(tmp_path):
    """spec piece 4 (reopen <row>): prints the stored reopen_command."""
    r_ = row(reopen_command="godot --path . --scene lab --seed 7")
    p = write(tmp_path / "l.toml", [r_])
    r = run("reopen", p, "r1")
    assert r.returncode == 0
    assert r.stdout.strip() == "godot --path . --scene lab --seed 7"


def test_verify_match_passes(tmp_path):
    """spec piece 4 (verify): sha256 of the trace equals trace_hash -> PASS."""
    p = write(tmp_path / "l.toml", [row()])
    r = run("verify", p, "r1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout and "FAIL" not in r.stdout


def test_verify_mismatch_fails(tmp_path):
    """spec piece 4 (verify): hash mismatch -> FAIL."""
    p = write(tmp_path / "l.toml", [row(trace_hash="0" * 64)])
    r = run("verify", p, "r1")
    assert r.returncode != 0
    assert "FAIL" in r.stdout and "PASS" not in r.stdout


def test_verify_command_failure_fails_never_passes(tmp_path):
    """spec piece 4 (verify): a failing reopen_command is FAIL even if its output hashes right."""
    cmd = f"{sys.executable} -c \"import sys;sys.stdout.write('tick 1\\ntick 2\\n');sys.exit(3)\""
    p = write(tmp_path / "l.toml", [row(reopen_command=cmd)])
    r = run("verify", p, "r1")
    assert r.returncode != 0
    assert "FAIL" in r.stdout and "PASS" not in r.stdout


def test_verify_unknown_row_or_missing_command_never_passes(tmp_path):
    """spec piece 4 (verify): errors are never PASS."""
    p = write(tmp_path / "l.toml", [row(reopen_command="/nonexistent/binary --x")])
    for rid in ("r1", "nope"):
        r = run("verify", p, rid)
        assert r.returncode != 0
        assert "PASS" not in r.stdout


def test_replace_keeps_old_row_with_superseded_by_link(tmp_path):
    """spec piece 4: a ledger is append-only history; replacing an approved run keeps the old row under superseded_by."""
    p = write(tmp_path / "l.toml", [row("old")])
    new = write(tmp_path / "new.toml", [row("new", words="better now")])
    r = run("replace", p, "old", new)
    assert r.returncode == 0, r.stdout + r.stderr
    text = p.read_text()
    assert 'id = "old"' in text and 'words = "looks right"' in text
    assert 'id = "new"' in text
    import tomllib
    rows = {x["id"]: x for x in tomllib.loads(text)["row"]}
    assert rows["old"]["superseded_by"] == "new"
    assert "superseded_by" not in rows["new"]
    assert run("validate", p).returncode == 0
    assert run("list", p).stdout.count("old") >= 1


def test_validate_rejects_dangling_superseded_by(tmp_path):
    """spec piece 4: superseded_by must name an existing row."""
    p = write(tmp_path / "l.toml", [row("old", superseded_by="ghost")])
    assert run("validate", p).returncode != 0


def test_real_ledger_exists_parses_validates_data_completeness_gate():
    """spec piece 4 DATA-COMPLETENESS GATE: approved_scenes.toml exists, parses, validates, every row's sha exists."""
    import tomllib
    p = ROOT / "docs/northstar/story_reviews/westley/approved_scenes.toml"
    assert p.is_file(), "approved_scenes.toml missing"
    rows = tomllib.loads(p.read_text()).get("row", [])
    for r_ in rows:
        assert subprocess.run(["git", "cat-file", "-e", r_["sha"] + "^{commit}"], cwd=ROOT).returncode == 0, r_.get("id")
    v = run("validate", p)
    assert v.returncode == 0, v.stdout + v.stderr
