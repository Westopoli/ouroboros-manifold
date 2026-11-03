"""H-071 review-apply-reads-the-verdict-words: `review.py apply` applies the verdicts as written.

Story: docs/stories/H-071.md ("The catalogue applies the verdicts as written."). Parts proved:
  - Change 1: "`review.py apply` accepts the seven words A, B, draw, deny, hold, redraw and out." (test_seven_words_applied)
  - Change 2: "When a layout id has several rows, the last row wins" (test_amended_row_last_wins, also hold-then-deny)
  - Change 3: "`apply` writes the winning verdict and feedback into each layout toml's `verdict` and `feedback` fields"
  - Change 4: "An unknown id or an unknown word is rejected with the line number of the row in the verdicts file, and nothing is written."
  - Change 5: "`review.py denied` then lists the round-two denies (L-0039, L-0047 and the batch-one rows) from the tomls." (real-file test)
Controls (green on main): the four old words still apply; an unknown word and an unknown id are already refused with exit 1.
Red on main for the story's reason: VERDICTS = ("A", "B", "draw", "deny") refuses hold, redraw and out, and the real
verdicts.md therefore applies nothing.
Hermetic: scratch catalogue in tmp_path, copied from the real L-*.toml files; no network, Godot or GPU.
"""
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "scripts" / "skilllab" / "catalogue" / "review.py"
REAL = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "catalogue"
SEVEN = ["A", "B", "draw", "deny", "hold", "redraw", "out"]
OLD_FOUR = ["A", "B", "draw", "deny"]


def _review(*args):
    return subprocess.run([sys.executable, str(REVIEW), *map(str, args)], cwd=ROOT, capture_output=True, text=True, timeout=60)


def _scratch(tmp_path, ids):
    """A scratch catalogue holding only the named real layout tomls, verdict and feedback blanked ("")."""
    cat = tmp_path / "cat"
    cat.mkdir()
    for lid in ids:
        text = (REAL / (lid + ".toml")).read_text()
        text = re.sub(r'^verdict = ".*"$', 'verdict = ""', text, flags=re.M)
        text = re.sub(r'^feedback = ".*"$', 'feedback = ""', text, flags=re.M)
        (cat / (lid + ".toml")).write_text(text)
    return cat


def _toml(cat, lid):
    with open(cat / (lid + ".toml"), "rb") as f:
        return tomllib.load(f)


def _verdicts(tmp_path, rows, header=("# scratch verdicts", "", "| id | verdict | feedback |", "|---|---|---|")):
    p = tmp_path / "verdicts.md"
    p.write_text("\n".join([*header, *("| %s | %s | %s |" % r for r in rows)]) + "\n")
    return p


def _ids(n):
    return ["L-%04d" % i for i in range(1, n + 1)]


def test_control_old_four_words_apply(tmp_path):
    """CONTROL (green on main). Change 3: the four words accepted today are written to the tomls with their feedback."""
    ids = _ids(4)
    cat = _scratch(tmp_path, ids)
    v = _verdicts(tmp_path, [(i, w, "fb " + w) for i, w in zip(ids, OLD_FOUR)])
    r = _review("apply", "--dir", cat, "--verdicts", v)
    assert r.returncode == 0, r.stderr
    for i, w in zip(ids, OLD_FOUR):
        t = _toml(cat, i)
        assert (t["verdict"], t["feedback"]) == (w, "fb " + w)


def test_control_unknown_word_and_id_refused_and_nothing_written(tmp_path):
    """CONTROL (green on main). Change 4, the exit code and the no-write half: 'sure' and an unknown id are refused, tomls untouched."""
    ids = _ids(3)
    cat = _scratch(tmp_path, ids)
    for rows in ([("L-0001", "A", "ok"), ("L-0002", "sure", "x")], [("L-0001", "A", "ok"), ("L-0999", "A", "x")]):
        r = _review("apply", "--dir", cat, "--verdicts", _verdicts(tmp_path, rows))
        assert r.returncode != 0
        assert all(_toml(cat, i)["verdict"] == "" for i in ids)


def test_seven_words_applied(tmp_path):
    """Change 1 and 3: one row per word; each toml carries its word and feedback."""
    ids = _ids(7)
    cat = _scratch(tmp_path, ids)
    v = _verdicts(tmp_path, [(i, w, "fb " + w) for i, w in zip(ids, SEVEN)])
    r = _review("apply", "--dir", cat, "--verdicts", v)
    assert r.returncode == 0, "apply refused the seven words: " + r.stderr
    for i, w in zip(ids, SEVEN):
        t = _toml(cat, i)
        assert (t["verdict"], t["feedback"]) == (w, "fb " + w)


@pytest.mark.parametrize("first,last", [("A", "deny"), ("hold", "deny"), ("deny", "hold"), ("redraw", "out")])
def test_amended_row_last_wins(tmp_path, first, last):
    """Change 2: same id, later line wins. (hold, deny) is Westley's real L-0039 amendment."""
    cat = _scratch(tmp_path, _ids(2))
    v = _verdicts(tmp_path, [("L-0001", first, "first"), ("L-0002", "A", "other"), ("L-0001", last, "amended")])
    r = _review("apply", "--dir", cat, "--verdicts", v)
    assert r.returncode == 0, r.stderr
    t = _toml(cat, "L-0001")
    assert (t["verdict"], t["feedback"]) == (last, "amended")
    assert _toml(cat, "L-0002")["verdict"] == "A"


def test_unknown_word_rejected_with_line_number_and_nothing_written(tmp_path):
    """Change 4: an unknown word is rejected naming the row's line in the verdicts file; the good rows before it are not written."""
    ids = _ids(3)
    cat = _scratch(tmp_path, ids)
    v = _verdicts(tmp_path, [("L-0001", "A", "ok"), ("L-0002", "deny", "ok"), ("L-0003", "maybe", "bad")])
    bad_line = v.read_text().splitlines().index(next(l for l in v.read_text().splitlines() if "maybe" in l)) + 1
    r = _review("apply", "--dir", cat, "--verdicts", v)
    assert r.returncode != 0
    assert re.search(r"(?<!\d)%d(?!\d)" % bad_line, r.stderr), "line %d not in: %s" % (bad_line, r.stderr)
    assert all(_toml(cat, i)["verdict"] == "" for i in ids)


def test_unknown_id_rejected_with_line_number_and_nothing_written(tmp_path):
    """Change 4: an unknown id is rejected naming the row's line; nothing is written."""
    cat = _scratch(tmp_path, _ids(2))
    v = _verdicts(tmp_path, [("L-0001", "hold", "ok"), ("L-0777", "A", "no such layout")])
    bad_line = [i for i, l in enumerate(v.read_text().splitlines(), 1) if "L-0777" in l][0]
    r = _review("apply", "--dir", cat, "--verdicts", v)
    assert r.returncode != 0
    assert re.search(r"(?<!\d)%d(?!\d)" % bad_line, r.stderr), "line %d not in: %s" % (bad_line, r.stderr)
    assert all(_toml(cat, i)["verdict"] == "" for i in _ids(2))


def test_real_verdicts_apply_cleanly_and_denied_lists_round_two(tmp_path):
    """Change 5 and Tests item 4: the real verdicts.md applies to a scratch copy of the catalogue; `denied` lists L-0039 and L-0047."""
    cat = tmp_path / "cat"
    cat.mkdir()
    for p in REAL.glob("L-*.toml"):
        shutil.copy(p, cat / p.name)
    r = _review("apply", "--dir", cat, "--verdicts", REAL / "verdicts.md")
    assert r.returncode == 0, "real verdicts.md did not apply: " + r.stderr[:300]
    listed = {l.split()[0] for l in _review("denied", "--dir", cat).stdout.splitlines() if l.strip()}
    assert {"L-0039", "L-0047"} <= listed, sorted(listed)
    assert "L-0001" in listed  # a batch-one row
    assert "L-0037" not in listed  # approved A, not denied
    assert _toml(cat, "L-0039")["verdict"] == "deny"  # the amended row, not the first-pass hold
