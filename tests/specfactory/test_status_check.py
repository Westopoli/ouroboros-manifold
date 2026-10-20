# spec: docs/northstar/plans/2026-10-07-visible-game-programme.md Lane table
#       and docs/northstar/plans/2026-10-19-harness-enforcement-spec.md section 1 HARNESS-C1b (rev 3a)
# Rule pins: R-990-01@?
"""Tests for scripts/specfactory/status_check.py.

Method rev 2, guard 7: the status copies (programme lane table, pieces.toml
attach shas, Seen vs approved queue rows, the ROADMAP lane row) are checked
against one another and against git. See also:
docs/northstar/plans/2026-10-07-visible-game-programme.md Lane table.

Every case builds a throwaway git repo in tmp_path (two commits on main, a
branch named "base" at the first, one unrelated commit on a side branch) and
runs the script by its repo path with --repo tmp_path --base base. Relative
fixture paths are passed with cwd = tmp_path = --repo, so either resolution
rule (against cwd or against --repo) finds the same file.

HARNESS-C1b extends this file at the bottom with check `pins`: "`status_check.py` on the fixture repo prints
`STATUS pins WARN 1 stale` with no `FU-HARNESS-findings` row and `DRIFT` with an attached one (the four-line
assertion of `test_status_check.py` becomes a per-line check, `TD-HARNESS-C1`)"; "prints `STATUS pins WARN <n>
stale|missing` while the row `FU-HARNESS-findings` is not attached in `pieces.toml` and `STATUS pins DRIFT ...`
after ... exit 0 on WARN"; check `pins` is "whole-tree `rule_pins_tests.py check` plus `rule_pins.py check` over
the specs named by every row's `spec` key". Fixture id R-990-01 (rule line in the fixture epics only): pinned @?
above. Moved under TD-HARNESS-C1: LINE_RE gains WARN; test_clean_fixtures_give_four_ok_lines_and_exit_0 checks
the four original lines one by one instead of the whole list of lines (a fifth line `STATUS pins` appears).
UNSTATED INTERFACE (reported): the pins check runs the two tools that sit beside status_check.py on --repo; a row
of pieces.toml names its spec with `spec = "<md path>"`, relative to --repo; the row is `FU-HARNESS-findings`,
state `attached` (only that state flips the switch, as owner_lint reads it).

Controls: the fixture builds (base sha is an ancestor of base, the side sha is
not) and the STATUS line format regex matches a hand-written line; both pass
without the script. Every other test needs the script.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "status_check.py"

PROGRAMME = "docs/northstar/plans/2026-10-07-visible-game-programme.md"
PIECES = "docs/northstar/plans/push/pieces.toml"
STORIES = "docs/bible/stories.md"
REVIEWS = "docs/northstar/story_reviews"
ROADMAP = "docs/northstar/ROADMAP.md"

LINE_RE = re.compile(r"^STATUS (\w+) (OK|WARN|DRIFT)\b.*$")

REVIEW_HEADER = (
    "| story | lane | run id | screenshot path | qa_state file | reviewer | "
    "reviewer verdict (yes/no/unclear + evidence) | "
    "Westley verdict (pending/approved/rejected) | date |\n"
    "|---|---|---|---|---|---|---|---|---|\n"
)


def _git(repo, *args):
    r = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _review_row(story, verdict):
    return (f"| {story} | lane-a | 20261010-0900-abc1234 | shots/{story}.png | "
            f"shots/{story}.json | sonnet | yes: seen | {verdict} | 2026-10-10 |\n")


def build_fixture(tmp_path, side_in_lane=False, side_in_pieces=False,
                  third_approved=False, roadmap_lane_row=False,
                  roadmap_missing_path=False):
    """Return (base_sha7, side_sha7). Files are written then committed."""
    repo = tmp_path
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README.txt").write_text("base\n")
    _git(repo, "add", "README.txt")
    _git(repo, "commit", "-q", "-m", "first")
    base_full = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "base")
    # unrelated commit on a side branch (a descendant of base, never an ancestor of it)
    _git(repo, "checkout", "-q", "-b", "side")
    (repo / "side.txt").write_text("side\n")
    _git(repo, "add", "side.txt")
    _git(repo, "commit", "-q", "-m", "side")
    side_full = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "main")
    b7, s7 = base_full[:7], side_full[:7]

    def put(rel, text):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    lane_extra = (f"| Lane Zeta | landed at {s7} on the side branch | next | n/a | none |\n"
                  if side_in_lane else "")
    put(PROGRAMME,
        "# Programme\n\nSome prose.\n\n"
        "| Lane | On main | Next piece | First look | Westley row |\n"
        "|---|---|---|---|---|\n"
        f"| Lane Alpha | pieces one to three at {b7} | next | n/a | none |\n"
        f"| Lane Beta | nothing yet | next | n/a | none |\n"
        f"| Lane Gamma | landed at {b7}, again {base_full} | next | n/a | none |\n"
        + lane_extra +
        "\nA later table; only the first lane table is checked.\n\n"
        "| Lane | On main | Next piece |\n|---|---|---|\n"
        f"| Lane Late | landed at {s7} | next |\n")

    attach2 = s7 if side_in_pieces else b7
    put(PIECES,
        "# comment line with an inline table: { state = \"attached\", attach_sha = \"0000000\" }\n\n"
        "[[piece]]\n"
        'id = "P-ONE"\nmanager = "M0"\nowns = ["a.c"]\nowns_glob = []\n'
        'acceptance = ["t.py"]\ndepends_on = []\n'
        f'status = {{ state = "attached", attach_sha = "{b7}" }}\n'
        "tests_pending = false\n\n"
        "[[piece]]\n"
        'id = "P-TWO"\nmanager = "M0"\nowns = ["b.c"]\nowns_glob = []\n'
        'acceptance = ["t.py"]\ndepends_on = []\n'
        f'status = {{ state = "attached", attach_sha = "{attach2}" }}\n'
        "tests_pending = false\n\n"
        "[[piece]]\n"
        'id = "P-FLY"\nmanager = "M0"\nowns = ["c.c"]\nowns_glob = []\n'
        'acceptance = ["t.py"]\ndepends_on = []\n'
        'status = { state = "in_flight" }\n'
        "tests_pending = true\n")

    put(STORIES,
        "# Story Catalog\n\n"
        "| Story | Epic | In the commander's words | Status | Depth |\n"
        "|---|---|---|---|---|\n"
        '| S-001 | E-01 | "One." | Seen | `e1.md` S-001 |\n'
        '| S-002 | E-01 | "Two." | Seen, revised once | `e1.md` S-002 |\n'
        "| S-003 | E-01 | \"Three.\" | Spec'd | `e1.md` S-003 |\n")

    rows = _review_row("S-001", "approved") + _review_row("S-002", "approved")
    if third_approved:
        rows += _review_row("S-004", "approved")
    rows += _review_row("S-003", "pending")
    put(f"{REVIEWS}/lane-a.md", "# Lane A\n\n" + REVIEW_HEADER + rows)
    # the README table in the real dir has a header cell that merely contains "approved"
    put(f"{REVIEWS}/README.md",
        "# Story review queue\n\n" + REVIEW_HEADER)

    road_path = "" if roadmap_missing_path else f" (`{PROGRAMME}`)"
    lane_row = ("| Visible game lane A | push/vg-a | IN FLIGHT | next |\n"
                if roadmap_lane_row else "")
    put(ROADMAP,
        "# Roadmap\n\n## 0. Intro\n\nText.\n\n"
        "## 1. Now building\n\nUpdated today.\n\n"
        "| Lane | Branch | State | Next |\n|---|---|---|---|\n"
        f"| **The visible game programme**{road_path}: every prototype | the lane table | IN FLIGHT | next |\n"
        + lane_row +
        "\n## 2. Later\n\n"
        "| Lane | Branch | State | Next |\n|---|---|---|---|\n"
        "| Visible game lane Q (outside section 1, ignored) | none | none | none |\n")

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "second")
    return b7, s7


def run_check(tmp_path, *extra):
    cmd = [sys.executable, str(SCRIPT), "--repo", str(tmp_path), "--base", "base",
           "--programme", PROGRAMME, "--pieces", PIECES, "--stories", STORIES,
           "--reviews", REVIEWS, "--roadmap", ROADMAP, *extra]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path, timeout=60)


def status_lines(res):
    return [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS ")]


def line_for(res, check):
    hits = [ln for ln in status_lines(res) if ln.startswith(f"STATUS {check} ")]
    assert hits, f"no STATUS {check} line; stdout={res.stdout!r} stderr={res.stderr!r}"
    return hits


# ---------------------------------------------------------------- controls (green without the script)

def test_control_status_line_format_regex():
    assert LINE_RE.match("STATUS lane_table OK 3 shas checked")
    assert LINE_RE.match("STATUS seen DRIFT 3 approved vs 2 Seen")
    assert LINE_RE.match("STATUS pins WARN 1 stale")
    assert not LINE_RE.match("status seen drift")


def test_control_fixture_build_has_base_and_side_shas(tmp_path):
    b7, s7 = build_fixture(tmp_path)
    assert b7 != s7
    ok = subprocess.run(["git", "-C", str(tmp_path), "merge-base", "--is-ancestor", b7, "base"])
    assert ok.returncode == 0
    bad = subprocess.run(["git", "-C", str(tmp_path), "merge-base", "--is-ancestor", s7, "base"])
    assert bad.returncode == 1


# ---------------------------------------------------------------- positive control for the script

def test_clean_fixtures_give_four_ok_lines_and_exit_0(tmp_path):
    # TD-HARNESS-C1: was `[m.group(1) for m in map(LINE_RE.match, lines)] == ["lane_table", "pieces", "seen",
    # "roadmap"]` and `all(LINE_RE.match(ln).group(2) == "OK" for ln in lines)`; the pins line is a fifth one now.
    build_fixture(tmp_path)
    res = run_check(tmp_path)
    for name in ("lane_table", "pieces", "seen", "roadmap"):
        hits = line_for(res, name)
        assert len(hits) == 1 and LINE_RE.match(hits[0]).group(2) == "OK", (name, res.stdout)
    assert all(LINE_RE.match(ln) for ln in status_lines(res)), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


# ---------------------------------------------------------------- lane_table

def test_lane_table_side_sha_is_drift_naming_lane_and_sha(tmp_path):
    _, s7 = build_fixture(tmp_path, side_in_lane=True)
    res = run_check(tmp_path)
    drift = [ln for ln in line_for(res, "lane_table") if "DRIFT" in ln]
    assert drift, res.stdout
    assert any("Lane Zeta" in ln and s7 in ln for ln in drift), drift
    assert res.returncode == 1


def test_lane_table_only_first_table_is_checked(tmp_path):
    # the clean fixture has a bad sha in a later table; it must not count
    build_fixture(tmp_path)
    res = run_check(tmp_path)
    ln = line_for(res, "lane_table")
    assert all("DRIFT" not in x for x in ln), ln


# ---------------------------------------------------------------- pieces

def test_pieces_side_attach_sha_is_drift_naming_piece_and_sha(tmp_path):
    _, s7 = build_fixture(tmp_path, side_in_pieces=True)
    res = run_check(tmp_path)
    drift = [ln for ln in line_for(res, "pieces") if "DRIFT" in ln]
    assert drift, res.stdout
    assert any("P-TWO" in ln and s7 in ln for ln in drift), drift
    assert res.returncode == 1


def test_pieces_ok_line_lists_in_flight_ids(tmp_path):
    build_fixture(tmp_path)
    res = run_check(tmp_path)
    ok = [ln for ln in line_for(res, "pieces") if " OK" in ln]
    assert len(ok) == 1, res.stdout
    assert "in_flight:" in ok[0] and "P-FLY" in ok[0], ok[0]
    assert "P-ONE" not in ok[0].split("in_flight:")[1], ok[0]


# ---------------------------------------------------------------- seen

def test_seen_mismatch_is_drift_with_both_numbers(tmp_path):
    build_fixture(tmp_path, third_approved=True)
    res = run_check(tmp_path)
    hits = line_for(res, "seen")
    assert any("STATUS seen DRIFT 3 approved vs 2 Seen" in ln for ln in hits), hits
    assert res.returncode == 1


# ---------------------------------------------------------------- roadmap

def test_roadmap_lane_row_in_now_building_is_drift(tmp_path):
    build_fixture(tmp_path, roadmap_lane_row=True)
    res = run_check(tmp_path)
    drift = [ln for ln in line_for(res, "roadmap") if "DRIFT" in ln]
    assert drift, res.stdout
    assert any("Visible game lane A" in ln for ln in drift), drift
    assert res.returncode == 1


def test_roadmap_programme_row_without_path_is_drift(tmp_path):
    build_fixture(tmp_path, roadmap_missing_path=True)
    res = run_check(tmp_path)
    drift = [ln for ln in line_for(res, "roadmap") if "DRIFT" in ln]
    assert drift, res.stdout
    assert res.returncode == 1



# ---------------------------------------------------------------- HARNESS-C1b: check pins

EPIC_TEXT = "# E-99 Test epic\n\n- R-990-01  Given a town, When it grows, Then it never form rings around the core.\n"
RULE_PIN = "b2a3c8"  # section 3 formula on the rule line above (proved by the control below)
STALE_PIN = "000000"
FU_ROW = "FU-HARNESS-findings"


def _put(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _pins_fixture(tmp_path, test_pin=RULE_PIN, spec_tag=None, fu_state=None):
    """build_fixture plus the fixture epics, one test citing R-990-01 with `Rule pins: R-990-01@<test_pin>`, an
    optional spec named by a pieces row (`spec_tag` is the text of its [B] tag), an optional FU-HARNESS-findings row."""
    build_fixture(tmp_path)
    _put(tmp_path, "docs/bible/epics/E-99-test.md", EPIC_TEXT)
    _put(tmp_path, "tests/test_x.py",
         f"# Rule pins: R-990-01@{test_pin}\ndef test_x():\n    \"\"\"R-990-01\"\"\"\n    assert True\n")
    pieces = (tmp_path / PIECES).read_text()
    if spec_tag is not None:
        _put(tmp_path, "docs/spec.md", f"# Spec\n\nThe lot draws 7 rows. {spec_tag}\n")
        pieces += ('\n[[piece]]\nid = "P-SPEC"\nmanager = "M0"\nowns = ["d.c"]\nowns_glob = []\n'
                   'acceptance = ["t.py"]\ndepends_on = []\nspec = "docs/spec.md"\n'
                   'status = { state = "in_flight" }\ntests_pending = true\n')
    if fu_state is not None:
        pieces += (f'\n[[piece]]\nid = "{FU_ROW}"\nmanager = "M0"\nowns = ["e.c"]\nowns_glob = []\n'
                   f'acceptance = ["t.py"]\ndepends_on = []\nstatus = {{ state = "{fu_state}" }}\n'
                   f'tests_pending = false\n')
    (tmp_path / PIECES).write_text(pieces)


def test_control_pins_fixture_builds_and_the_other_four_checks_stay_ok(tmp_path):
    """Green today: the fixture with a stale test and an attached FU row changes none of the four old checks."""
    _pins_fixture(tmp_path, test_pin=STALE_PIN, fu_state="attached")
    res = run_check(tmp_path)
    for name in ("lane_table", "pieces", "seen", "roadmap"):
        assert all(LINE_RE.match(ln).group(2) == "OK" for ln in line_for(res, name)), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_pins_ok_when_every_pin_is_right(tmp_path):
    _pins_fixture(tmp_path, test_pin=RULE_PIN)
    res = run_check(tmp_path)
    hits = line_for(res, "pins")
    assert len(hits) == 1 and hits[0].startswith("STATUS pins OK"), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_pins_stale_test_pin_warns_without_an_attached_follow_up_row(tmp_path):
    _pins_fixture(tmp_path, test_pin=STALE_PIN)
    res = run_check(tmp_path)
    assert "STATUS pins WARN 1 stale" in line_for(res, "pins")[0], res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_pins_stale_test_pin_is_drift_with_an_attached_follow_up_row(tmp_path):
    _pins_fixture(tmp_path, test_pin=STALE_PIN, fu_state="attached")
    res = run_check(tmp_path)
    assert line_for(res, "pins")[0].startswith("STATUS pins DRIFT"), res.stdout
    assert res.returncode == 1, res.stdout + res.stderr


def test_pins_follow_up_row_that_is_not_attached_still_warns(tmp_path):
    """The switch reads the row state the way owner_lint does: only `attached` flips it (queued or in flight do not)."""
    for state in ("queued", "in_flight"):
        sub = tmp_path / state
        sub.mkdir()
        _pins_fixture(sub, test_pin=STALE_PIN, fu_state=state)
        res = run_check(sub)
        assert line_for(res, "pins")[0].startswith("STATUS pins WARN 1 stale"), (state, res.stdout)
        assert res.returncode == 0, (state, res.stdout + res.stderr)


def test_pins_missing_pin_in_a_row_spec_warns_as_missing(tmp_path):
    """The specs named by every row's spec key are checked too (rule_pins.py check)."""
    _pins_fixture(tmp_path, test_pin=RULE_PIN, spec_tag="[B R-990-01: words]")
    res = run_check(tmp_path)
    assert line_for(res, "pins")[0].startswith("STATUS pins WARN 1 missing"), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_pins_right_pin_in_a_row_spec_is_ok(tmp_path):
    _pins_fixture(tmp_path, test_pin=RULE_PIN, spec_tag=f"[B R-990-01@{RULE_PIN}: words]")
    res = run_check(tmp_path)
    assert line_for(res, "pins")[0].startswith("STATUS pins OK"), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr
