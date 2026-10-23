# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md::HARNESS-record-files
"""HARNESS-record-files: ledger, register, decisions, decision-pack batch and lane review pages are
record files (no owner): SHARED_RECORD_GLOBS lists them, owner_lint skips them in an in-flight
overlap, the footprint fence ignores them. Positive controls: csrc/mission.c still overlaps and still
trips the footprint. No R-/S- id is named by the paragraph, so none is pinned here.

UNSTATED INTERFACE CHOICES (the paragraph does not fix these):
- the "record files (no owner): ..." line is asserted on the stdout of `owner_lint.py --pieces <p>`
  (the CLI), once, with the skipped path on that line; that it is printed on an OK run is assumed
  (the case the paragraph describes: two pieces overlap only on record files).
- `owner_lint.in_flight_overlaps(pieces)` keeps returning a list of findings (empty for record files).
- the glob list is checked as membership of the five literal strings in `pieces.SHARED_RECORD_GLOBS`
  (the Westley entry stays; the order and extra entries are free).
- 'a diff touching only the ledger and the register' is built in a temp git repo as neighbouring
  footprint tests do; the piece id is a fixture piece owning only csrc/events.c.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OWNER_LINT = REPO / "scripts" / "specfactory" / "owner_lint.py"
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402
import owner_lint as ol  # noqa: E402
import pieces as pc  # noqa: E402

LEDGER = "docs/northstar/plans/push_ledger_2026-09-22.md"
REGISTER = "docs/northstar/ambiguity_register.md"
DECISIONS = "docs/northstar/story_reviews/westley/decisions.md"
BATCH = "docs/northstar/plans/decision_pack_2026-10-18/batch.md"
REVIEW_PAGES = "docs/northstar/story_reviews/*.md"


def _two_pieces(path_x, path_y=None, tmp_path=None):
    path_y = path_y or path_x
    toml = f"""
[[piece]]
id = "X"
owns = ["{path_x}"]
status = "pending"

[[piece]]
id = "Y"
owns = ["{path_y}"]
status = "pending"
"""
    f = tmp_path / "pieces.toml"
    f.write_text(toml)
    return f


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _repo(base):
    base.mkdir(parents=True)
    _git(base, "init", "-q")
    _git(base, "config", "user.email", "gate@test")
    _git(base, "config", "user.name", "gate")
    (base / "csrc").mkdir()
    (base / "csrc" / "events.c").write_text("int a;\n")
    _git(base, "add", "-A")
    _git(base, "commit", "-q", "-m", "base")
    return base


def _pieces_file(tmp_path):
    f = tmp_path / "fp_pieces.toml"
    f.write_text('[[piece]]\nid = "B1"\nowns = ["csrc/events.c"]\n')
    return f


def test_glob_list_contains_the_five_entries():
    for entry in (LEDGER, REGISTER, DECISIONS, BATCH, REVIEW_PAGES):
        assert entry in pc.SHARED_RECORD_GLOBS, entry
    assert "docs/northstar/story_reviews/westley/*" in pc.SHARED_RECORD_GLOBS


def test_two_in_flight_pieces_owning_the_ledger_give_no_overlap(tmp_path):
    pieces = pc.load_pieces(_two_pieces(LEDGER, tmp_path=tmp_path))
    assert ol.in_flight_overlaps(pieces) == []


def test_two_in_flight_pieces_owning_csrc_mission_still_overlap_positive_control(tmp_path):
    pieces = pc.load_pieces(_two_pieces("csrc/mission.c", tmp_path=tmp_path))
    findings = ol.in_flight_overlaps(pieces)
    assert len(findings) == 1 and "csrc/mission.c" in findings[0][2], findings


def test_each_record_file_is_skipped_in_an_overlap(tmp_path):
    for n, path in enumerate((LEDGER, REGISTER, DECISIONS, BATCH, "docs/northstar/story_reviews/E-04.md")):
        d = tmp_path / str(n)
        d.mkdir()
        pieces = pc.load_pieces(_two_pieces(path, tmp_path=d))
        assert ol.in_flight_overlaps(pieces) == [], path


def test_owner_lint_prints_skipped_record_files_once(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(OWNER_LINT), "--pieces", str(_two_pieces(LEDGER, tmp_path=tmp_path))],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = [ln for ln in proc.stdout.splitlines() if "record files (no owner):" in ln]
    assert len(lines) == 1 and LEDGER in lines[0], proc.stdout


def test_owner_lint_prints_no_record_files_line_for_a_real_overlap_control(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(OWNER_LINT), "--pieces",
         str(_two_pieces("csrc/mission.c", tmp_path=tmp_path))], capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "csrc/mission.c" in proc.stdout
    assert "record files (no owner):" not in proc.stdout


def test_rows_listing_record_files_in_owns_keep_working(tmp_path):
    f = tmp_path / "pieces.toml"
    f.write_text(f'''
[[piece]]
id = "X"
owns = ["{LEDGER}", "csrc/a.c"]
status = "pending"

[[piece]]
id = "Y"
owns = ["{LEDGER}", "csrc/b.c"]
status = "pending"
''')
    assert ol.in_flight_overlaps(pc.load_pieces(f)) == []


def test_diff_touching_only_ledger_and_register_passes_footprint_under_unrelated_piece(tmp_path):
    repo = _repo(tmp_path / "repo")
    pieces = _pieces_file(tmp_path)
    for rel in (LEDGER, REGISTER):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("| row |\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "records")
    ok, detail = mgs.footprint_check(repo, "HEAD~1", "B1", pieces_path=pieces)
    assert ok is True, detail


def test_diff_touching_csrc_mission_still_fails_footprint_positive_control(tmp_path):
    repo = _repo(tmp_path / "repo")
    pieces = _pieces_file(tmp_path)
    (repo / "csrc" / "mission.c").write_text("int m;\n")
    (repo / LEDGER).parent.mkdir(parents=True, exist_ok=True)
    (repo / LEDGER).write_text("| row |\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "mixed")
    ok, detail = mgs.footprint_check(repo, "HEAD~1", "B1", pieces_path=pieces)
    assert ok is False and "csrc/mission.c" in detail and "push_ledger" not in detail, detail


def test_diff_touching_only_csrc_mission_fails_footprint_pure_positive_control(tmp_path):
    repo = _repo(tmp_path / "repo")
    pieces = _pieces_file(tmp_path)
    (repo / "csrc" / "mission.c").write_text("int m;\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "mission")
    ok, detail = mgs.footprint_check(repo, "HEAD~1", "B1", pieces_path=pieces)
    assert ok is False and "csrc/mission.c" in detail, detail
