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

HARNESS-C235 extends this file below the C1b block with checks `register` and `reviews` (spec section 1
HARNESS-C235, rev 3a): "check `register` (new `--register` arg, default `docs/northstar/ambiguity_register.md`): a row
whose status starts `closed` and whose Answer cell contains `until Westley`, `Westley to confirm`, `Westley answers`,
`Architect default` or the whole word `default` is a finding, and so is a malformed row (cell count not 6 after
stripping the outer pipes ...); check `reviews`: every row of the top-level `story_reviews/*.md` whose date cell
(index 8) is on or after `DRAFT-review-fields-from` 2026-10-20 must have, inside its reviewer-verdict cell (index 6),
the three labelled fields `legend=`, `unit=`, `band=` (presence only ...). Both print `WARN` until
`FU-HARNESS-findings` is attached and `DRIFT` after (C1b's switch)." Nothing above moves. UNSTATED INTERFACES
(reported): the detail text of a register or reviews finding (only the prefix `STATUS <check> WARN|DRIFT` is
asserted, plus the Q-id for a malformed row, which the spec says is named); what a missing register file prints (the
older cases write none, so they are the guard that it must not crash); the register path is given by default only.

HARNESS-C4 extends this file below the C235 block with the known-key check and check `launch` (spec section 1
HARNESS-C4, rev 3a): "`status_check.py` prints `STATUS pieces DRIFT unknown key scritp`, `STATUS launch DRIFT` for a
row with `script` and no `launch`, OK with the right sha, OK with `launch = "-"` on an id in `PRE_LAUNCH_IDS` and
DRIFT on one that is not, OK with `args = "-"`, DRIFT with a wrong sha, DRIFT with an `args` path not in git, OK for a
row with none of the keys." These cases run with `--base main` (the commit that holds the fixture script), except the
one that proves the path test reads git at --base. UNSTATED INTERFACES (reported): `PRE_LAUNCH_IDS` is a module-level
tuple of row ids read at call time (the cases patch it through a one-line runner, so a REPIN id list is never
needed); the detail text after `STATUS launch DRIFT` (only the prefix is asserted); one `STATUS launch OK` line when
no row drifts; `launch = "-"` exempts only the sha test (the script path must still be in git at --base); the sha is
of the committed file (`git show <base>:<script>`), not of the working copy. No existing case moves.

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


def _pins_fixture(tmp_path, test_pin=RULE_PIN, spec_tag=None, fu_state=None, fu_bare=False):
    """build_fixture plus the fixture epics, one test citing R-990-01 with `Rule pins: R-990-01@<test_pin>`, an
    optional spec named by a pieces row (`spec_tag` is the text of its [B] tag), an optional FU-HARNESS-findings row
    (`fu_bare` writes its status as the bare string `status = "<state>"` instead of the inline table)."""
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
        status = f'"{fu_state}"' if fu_bare else f'{{ state = "{fu_state}" }}'
        pieces += (f'\n[[piece]]\nid = "{FU_ROW}"\nmanager = "M0"\nowns = ["e.c"]\nowns_glob = []\n'
                   f'acceptance = ["t.py"]\ndepends_on = []\nstatus = {status}\n'
                   f'tests_pending = false\n')
    (tmp_path / PIECES).write_text(pieces)


def test_control_pins_fixture_builds_and_the_other_four_checks_stay_ok(tmp_path):
    """With a current pin and the attached FU row, pins is OK, the four old checks are OK and rc is 0."""
    _pins_fixture(tmp_path, test_pin=RULE_PIN, fu_state="attached")
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


def test_pins_stale_test_pin_is_drift_with_a_bare_string_attached_follow_up_row(tmp_path):
    """owner_lint.py:37-44 reads both status shapes; 37 rows on main use the bare string `status = "attached"`."""
    _pins_fixture(tmp_path, test_pin=STALE_PIN, fu_state="attached", fu_bare=True)
    res = run_check(tmp_path)
    assert line_for(res, "pins")[0].startswith("STATUS pins DRIFT"), res.stdout
    assert res.returncode == 1, res.stdout + res.stderr


def test_pins_bare_string_follow_up_row_that_is_not_attached_still_warns(tmp_path):
    """Control of the bare-string case: `status = "queued"` does not flip the switch."""
    _pins_fixture(tmp_path, test_pin=STALE_PIN, fu_state="queued", fu_bare=True)
    res = run_check(tmp_path)
    assert line_for(res, "pins")[0].startswith("STATUS pins WARN 1 stale"), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


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


# ---------------------------------------------------------------- HARNESS-C235: checks register and reviews

REGISTER = "docs/northstar/ambiguity_register.md"
REGISTER_HEAD = (
    "# Ambiguity Register\n\n"
    "| Flag | Epic / story | Question | Candidate answers | Status | Answer |\n"
    "|---|---|---|---|---|---|\n"
)
CLEAN_ROW = "| Q-990-01 | E-99 | A closed question? | (a) yes; (b) no | closed | (a). |\n"


def _reg_row(qid, status, answer):
    return f"| {qid} | E-99 | A question? | (a) yes; (b) no | {status} | {answer} |\n"


def _register_fixture(tmp_path, *rows, fu_state=None):
    build_fixture(tmp_path)
    _put(tmp_path, REGISTER, REGISTER_HEAD + CLEAN_ROW + "".join(rows))
    if fu_state is not None:
        (tmp_path / PIECES).write_text((tmp_path / PIECES).read_text() +
            f'\n[[piece]]\nid = "{FU_ROW}"\nmanager = "M0"\nowns = ["e.c"]\nowns_glob = []\n'
            f'acceptance = ["t.py"]\ndepends_on = []\nstatus = {{ state = "{fu_state}" }}\ntests_pending = false\n')


def _review_late_row(story, verdict_cell, date):
    return (f"| {story} | lane-a | 20261021-0900-abc1234 | shots/{story}.png | shots/{story}.json | sonnet | "
            f"{verdict_cell} | pending | {date} |\n")


def _reviews_fixture(tmp_path, *rows, fu_state=None, subdir_rows=()):
    _register_fixture(tmp_path, fu_state=fu_state)
    text = (tmp_path / REVIEWS / "lane-a.md").read_text() + "".join(rows)
    (tmp_path / REVIEWS / "lane-a.md").write_text(text)
    if subdir_rows:
        _put(tmp_path, f"{REVIEWS}/westley/README.md", "# Westley\n\n" + REVIEW_HEADER + "".join(subdir_rows))


FIELDS = "legend=green is built unit=wu band=Local"


def test_control_register_fixture_keeps_the_old_checks_ok_and_the_new_row_files_exist(tmp_path):
    # Green today and after: the fixture register and the late review row do not disturb lane_table, pieces,
    # seen, roadmap (the late row is `pending`, so the approved = Seen count stays 2 = 2).
    _reviews_fixture(tmp_path, _review_late_row("S-005", "yes: seen", "2026-10-21"))
    res = run_check(tmp_path)
    for name in ("lane_table", "pieces", "seen", "roadmap"):
        assert all(LINE_RE.match(ln).group(2) == "OK" for ln in line_for(res, name)), res.stdout
    assert (tmp_path / REGISTER).is_file()


def test_register_clean_rows_are_ok_and_the_header_and_rule_rows_are_not_rows(tmp_path):
    # "defaults" and "defaulted" are not the whole word `default`.
    _register_fixture(tmp_path, _reg_row("Q-990-02", "open", "none yet"),
                      _reg_row("Q-990-03", "closed", "(b), the defaults table, defaulted."),
                      _reg_row("Q-990-04", "reading (Westley to confirm)", "(a), the default."))
    res = run_check(tmp_path)
    hits = line_for(res, "register")
    assert len(hits) == 1 and hits[0].startswith("STATUS register OK"), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_register_closed_row_with_a_stand_in_answer_warns_without_the_attached_row(tmp_path):
    # Each of the five markers; "WARN until FU-HARNESS-findings is attached" (exit 0 on WARN).
    for i, answer in enumerate(["(a) until Westley rules.", "(a). Westley to confirm.", "(a) Westley answers later.",
                                "(a). Architect default.", "(a), by default."]):
        sub = tmp_path / f"a{i}"
        sub.mkdir()
        _register_fixture(sub, _reg_row("Q-990-07", "closed", answer))
        res = run_check(sub)
        hits = line_for(res, "register")
        assert hits and all(h.startswith("STATUS register WARN") for h in hits), (answer, res.stdout)
        assert res.returncode == 0, (answer, res.stdout + res.stderr)


def test_register_closed_row_with_a_stand_in_answer_is_drift_with_the_attached_row(tmp_path):
    _register_fixture(tmp_path, _reg_row("Q-990-07", "closed", "(a) until Westley rules."), fu_state="attached")
    res = run_check(tmp_path)
    assert any(h.startswith("STATUS register DRIFT") for h in line_for(res, "register")), res.stdout
    assert res.returncode == 1, res.stdout + res.stderr


def test_register_follow_up_row_not_attached_still_warns(tmp_path):
    # The switch reads the row state the way owner_lint does: only `attached` flips it.
    for state in ("queued", "in_flight"):
        sub = tmp_path / state
        sub.mkdir()
        _register_fixture(sub, _reg_row("Q-990-07", "closed", "(a) until Westley rules."), fu_state=state)
        res = run_check(sub)
        assert all(h.startswith("STATUS register WARN") for h in line_for(res, "register")), (state, res.stdout)
        assert res.returncode == 0, (state, res.stdout + res.stderr)


def test_register_re_statused_reading_row_is_ok_even_when_attached(tmp_path):
    # "OK once re-statused `reading (Westley to confirm)`" (the Answer is untouched).
    _register_fixture(tmp_path, _reg_row("Q-990-07", "reading (Westley to confirm)", "(a) until Westley rules."),
                      fu_state="attached")
    res = run_check(tmp_path)
    hits = line_for(res, "register")
    assert len(hits) == 1 and hits[0].startswith("STATUS register OK"), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_register_malformed_row_is_a_finding_naming_it(tmp_path):
    # "a seven-cell row is a finding naming it" (cell count not 6 after stripping the outer pipes; five too).
    seven = "| Q-990-08 | E-99 | A question? | (a) yes | closed | (a) | stray |\n"
    five = "| Q-990-09 | E-99 | A question? | closed | (a) |\n"
    _register_fixture(tmp_path, seven, five)
    res = run_check(tmp_path)
    hits = line_for(res, "register")
    assert all(h.startswith("STATUS register WARN") for h in hits), res.stdout
    assert any("Q-990-08" in h for h in hits), res.stdout
    assert any("Q-990-09" in h for h in hits), res.stdout
    assert not any("Q-990-01" in h for h in hits), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_register_path_can_be_given_with_the_register_argument(tmp_path):
    _register_fixture(tmp_path)
    _put(tmp_path, "elsewhere/register.md", REGISTER_HEAD + CLEAN_ROW +
         _reg_row("Q-990-07", "closed", "(a) until Westley rules."))
    res = run_check(tmp_path, "--register", "elsewhere/register.md")
    assert all(h.startswith("STATUS register WARN") for h in line_for(res, "register")), res.stdout
    res = run_check(tmp_path)
    assert line_for(res, "register")[0].startswith("STATUS register OK"), res.stdout


def test_reviews_rows_before_the_cutoff_or_with_all_three_fields_are_ok(tmp_path):
    # DRAFT-review-fields-from 2026-10-20: dated 2026-10-12 is not a finding; all three fields is not either; the
    # fixture's own rows (2026-10-10, no fields) are not either.
    _reviews_fixture(tmp_path, _review_late_row("S-005", "yes: seen", "2026-10-12"),
                     _review_late_row("S-006", "yes: seen " + FIELDS, "2026-10-21"))
    res = run_check(tmp_path)
    hits = line_for(res, "reviews")
    assert len(hits) == 1 and hits[0].startswith("STATUS reviews OK"), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_reviews_row_on_or_after_the_cutoff_without_a_field_warns_then_drifts(tmp_path):
    # "a reviews row dated 2026-10-21 without `legend=` is a finding"; the cutoff day itself counts ("on or after");
    # a row missing only `band=` is a finding too.
    for i, (verdict, date) in enumerate([("yes: seen", "2026-10-21"),
                                         ("yes: seen unit=wu band=Local", "2026-10-21"),
                                         ("yes: seen legend=x unit=wu", "2026-10-21"),
                                         ("yes: seen", "2026-10-20")]):
        sub = tmp_path / f"r{i}"
        sub.mkdir()
        _reviews_fixture(sub, _review_late_row("S-005", verdict, date))
        res = run_check(sub)
        hits = line_for(res, "reviews")
        assert hits and all(h.startswith("STATUS reviews WARN") for h in hits), (verdict, date, res.stdout)
        assert res.returncode == 0, (verdict, date, res.stdout + res.stderr)
    sub = tmp_path / "attached"
    sub.mkdir()
    _reviews_fixture(sub, _review_late_row("S-005", "yes: seen", "2026-10-21"), fu_state="attached")
    res = run_check(sub)
    assert any(h.startswith("STATUS reviews DRIFT") for h in line_for(res, "reviews")), res.stdout
    assert res.returncode == 1, res.stdout + res.stderr


def test_reviews_only_the_top_level_files_are_read(tmp_path):
    # "every row of the top-level `story_reviews/*.md`": a late row without fields in a subfolder is not read.
    _reviews_fixture(tmp_path, subdir_rows=[_review_late_row("S-007", "yes: seen", "2026-10-21")])
    res = run_check(tmp_path)
    assert line_for(res, "reviews")[0].startswith("STATUS reviews OK"), res.stdout


# ---------------------------------------------------------------- HARNESS-C4: known keys and check launch

import hashlib  # noqa: E402

SPECFACTORY = REPO / "scripts" / "specfactory"
JS = "docs/northstar/plans/workflows_2026-10-07/vg-x.js"
ARGS = "docs/northstar/plans/workflows_2026-10-07/vg-x.args.json"
JS_TEXT = "// fixture script\nconst a = 1\n"
ARGS_TEXT = '{"stage": "contract"}\n'
JS_SHA = hashlib.sha256(JS_TEXT.encode()).hexdigest()
KEYS_FOUR = ("script", "args", "launch", "spec")


def _row_toml(rid, state="in_flight", **extra):
    lines = [f'id = "{rid}"', 'manager = "M0"', 'owns = ["z.c"]', 'owns_glob = []', 'acceptance = ["t.py"]',
             'depends_on = []', f'status = {{ state = "{state}" }}', 'tests_pending = true']
    lines += [f'{k} = "{v}"' for k, v in extra.items()]
    return "\n[[piece]]\n" + "\n".join(lines) + "\n"


def _launch_fixture(tmp_path, rows="", files=None):
    """build_fixture, then one more commit on main (so --base main sees them) holding `files` (default the script
    and its args file) and `rows` appended to pieces.toml."""
    build_fixture(tmp_path)
    for rel, text in (files if files is not None else {JS: JS_TEXT, ARGS: ARGS_TEXT}).items():
        _put(tmp_path, rel, text)
    (tmp_path / PIECES).write_text((tmp_path / PIECES).read_text() + rows)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "third")


def run_main(tmp_path, *extra):
    return run_check(tmp_path, "--base", "main", *extra)


def run_main_patched(tmp_path, pre_launch_ids, *extra):
    """run_main with status_check.PRE_LAUNCH_IDS set to `pre_launch_ids` (a tuple of row ids) inside the process."""
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import status_check as s; "
            "s.PRE_LAUNCH_IDS = tuple(sys.argv[2].split(',')) if sys.argv[2] else (); "
            "sys.exit(s.main(sys.argv[3:]))")
    cmd = [sys.executable, "-c", code, str(SPECFACTORY), ",".join(pre_launch_ids), "--repo", str(tmp_path),
           "--base", "main", "--programme", PROGRAMME, "--pieces", PIECES, "--stories", STORIES,
           "--reviews", REVIEWS, "--roadmap", ROADMAP, *extra]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path, timeout=60)


def _launch_ok(res, why):
    hits = line_for(res, "launch")
    assert len(hits) == 1 and hits[0].startswith("STATUS launch OK"), (why, res.stdout)
    assert res.returncode == 0, (why, res.stdout + res.stderr)


def _launch_drift(res, why):
    hits = line_for(res, "launch")
    assert hits and all(h.startswith("STATUS launch DRIFT") for h in hits), (why, res.stdout)
    assert res.returncode == 1, (why, res.stdout + res.stderr)


def test_control_launch_fixture_sha_is_of_the_committed_script_and_the_old_checks_stay_ok(tmp_path):
    # Green today and after: rows carrying the four new keys do not disturb the other checks and parse_pieces still
    # reads their ids (P-L is listed as in flight); the fixture sha is the sha256 of `git show main:<script>`.
    _launch_fixture(tmp_path, _row_toml("P-L", script=JS, args=ARGS, launch=JS_SHA))
    shown = subprocess.run(["git", "-C", str(tmp_path), "show", f"main:{JS}"], capture_output=True, check=True).stdout
    assert hashlib.sha256(shown).hexdigest() == JS_SHA
    res = run_main(tmp_path)
    for name in ("lane_table", "pieces", "seen", "roadmap"):
        assert all(LINE_RE.match(ln).group(2) == "OK" for ln in line_for(res, name)), res.stdout
    assert "P-L" in line_for(res, "pieces")[0].split("in_flight:")[1], res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_control_runner_that_patches_pre_launch_ids_runs_the_checks(tmp_path):
    # Green today: the one-line runner of the PRE_LAUNCH_IDS cases prints the four old lines like the script does.
    _launch_fixture(tmp_path)
    res = run_main_patched(tmp_path, ("P-PRE",))
    for name in ("lane_table", "pieces", "seen", "roadmap"):
        assert all(LINE_RE.match(ln).group(2) == "OK" for ln in line_for(res, name)), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


# -------- known keys

def test_pieces_all_fourteen_known_keys_give_no_unknown_key_line(tmp_path):
    # Positive control, green today: the ten keys in use (id manager wave owns owns_glob acceptance depends_on
    # status tests_pending size_estimate) plus script args launch spec are known; a comment line holding an unknown
    # key and a trailing comment after a value are not keys. On the built tree the row is a good launch row too.
    row = (_row_toml("P-ALL", wave="13", size_estimate="x", script=JS, args=ARGS, launch=JS_SHA,
                     spec="docs/spec.md")
           .replace('owns_glob = []', 'owns_glob = []  # scritp = "a trailing comment is no key"')
           + '# scritp = "a comment is no key"\n')
    _launch_fixture(tmp_path, row, files={JS: JS_TEXT, ARGS: ARGS_TEXT, "docs/spec.md": "# Spec\n"})
    res = run_main(tmp_path)
    assert not any("unknown key" in ln for ln in status_lines(res)), res.stdout
    assert all(LINE_RE.match(ln).group(2) == "OK" for ln in line_for(res, "pieces")), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_pieces_unknown_key_is_drift_naming_key_and_row(tmp_path):
    # "`STATUS pieces DRIFT unknown key scritp`": the line reads `unknown key <k> in <id>`, in any row state.
    for state in ("in_flight", "attached", "queued"):
        sub = tmp_path / state
        sub.mkdir()
        _launch_fixture(sub, _row_toml("P-BAD", state=state, scritp=JS))
        res = run_main(sub)
        assert "STATUS pieces DRIFT unknown key scritp in P-BAD" in line_for(res, "pieces"), (state, res.stdout)
        assert res.returncode == 1, (state, res.stdout + res.stderr)


# -------- the PRE_LAUNCH_IDS tuple

def test_pre_launch_ids_is_a_module_level_tuple():
    sys.path.insert(0, str(SPECFACTORY))
    try:
        import status_check
    finally:
        sys.path.remove(str(SPECFACTORY))
    assert isinstance(status_check.PRE_LAUNCH_IDS, tuple), type(getattr(status_check, "PRE_LAUNCH_IDS", None))


# -------- check launch

def test_launch_row_with_none_of_the_keys_is_ok(tmp_path):
    # "a row with none of the keys is exempt": the fixture's own three rows carry none; one STATUS launch OK line.
    _launch_fixture(tmp_path)
    _launch_ok(run_main(tmp_path), "no row has a launch key")


def test_launch_right_sha_is_ok_with_args_dash_or_an_args_path_in_git(tmp_path):
    # "OK with the right sha", "OK with `args = "-"`", and an args path that is in git at --base
    for i, args in enumerate(["-", ARGS]):
        sub = tmp_path / f"a{i}"
        sub.mkdir()
        _launch_fixture(sub, _row_toml("P-L", script=JS, args=args, launch=JS_SHA))
        _launch_ok(run_main(sub), f"args = {args!r}")


def test_launch_sha_is_of_the_committed_script_not_the_working_copy(tmp_path):
    # "a row with `launch = "<sha>"` whose sha differs from `sha256sum` of `git show <base>:<script>` is DRIFT": a
    # working copy that was edited after the commit changes nothing; the sha of the edited copy is the drift.
    _launch_fixture(tmp_path, _row_toml("P-L", script=JS, args="-", launch=JS_SHA))
    (tmp_path / JS).write_text(JS_TEXT + "// edited after the commit\n")
    _launch_ok(run_main(tmp_path), "right sha of the committed file, edited working copy")
    sub = tmp_path / "w"
    sub.mkdir()
    _launch_fixture(sub, _row_toml("P-L", script=JS, args="-", launch=hashlib.sha256(
        (JS_TEXT + "// edited after the commit\n").encode()).hexdigest()))
    (sub / JS).write_text(JS_TEXT + "// edited after the commit\n")
    _launch_drift(run_main(sub), "sha of the working copy, not of the committed file")


def test_launch_wrong_sha_is_drift(tmp_path):
    _launch_fixture(tmp_path, _row_toml("P-L", script=JS, args="-", launch="0" * 64))
    _launch_drift(run_main(tmp_path), "wrong sha")


def test_launch_row_with_a_script_and_no_launch_key_is_drift(tmp_path):
    # "a row with `script` and no `launch` key at all is DRIFT (a new row must carry one)"
    _launch_fixture(tmp_path, _row_toml("P-L", script=JS, args="-"))
    _launch_drift(run_main(tmp_path), "script without launch")


def test_launch_dash_is_ok_only_for_an_id_in_pre_launch_ids(tmp_path):
    # "`launch = "-"` ... is exempt from the sha test only for the ids in `PRE_LAUNCH_IDS`; `-` on any other id is DRIFT"
    _launch_fixture(tmp_path, _row_toml("P-PRE", script=JS, args="-", launch="-"))
    _launch_ok(run_main_patched(tmp_path, ("P-PRE",)), "- on an id in PRE_LAUNCH_IDS")
    sub = tmp_path / "other"
    sub.mkdir()
    _launch_fixture(sub, _row_toml("P-NOT", script=JS, args="-", launch="-"))
    _launch_drift(run_main_patched(sub, ("P-PRE",)), "- on an id not in PRE_LAUNCH_IDS")
    _launch_drift(run_main(sub), "- with the shipped PRE_LAUNCH_IDS (no fixture id is in it)")


def test_launch_dash_exempts_only_the_sha_test_the_script_must_still_be_in_git(tmp_path):
    # "exempt from the sha test only": an id in PRE_LAUNCH_IDS whose script path is not in git is still DRIFT
    _launch_fixture(tmp_path, _row_toml("P-PRE", script=JS, args="-", launch="-"), files={ARGS: ARGS_TEXT})
    _launch_drift(run_main_patched(tmp_path, ("P-PRE",)), "- with a script not in git")


def test_launch_script_path_not_in_git_at_base_is_drift(tmp_path):
    # "a `script` path not in git at `--base` is DRIFT": absent from every commit, and present on main but not at
    # --base base (the first commit): the path test reads git at --base, not the working tree or HEAD.
    _launch_fixture(tmp_path, _row_toml("P-L", script=JS, args="-", launch=JS_SHA), files={ARGS: ARGS_TEXT})
    _launch_drift(run_main(tmp_path), "script not in git anywhere")
    sub = tmp_path / "later"
    sub.mkdir()
    _launch_fixture(sub, _row_toml("P-L", script=JS, args="-", launch=JS_SHA))
    _launch_drift(run_check(sub), "script in git on main but not at --base base")


def test_launch_args_path_not_in_git_is_drift_and_dash_is_exempt(tmp_path):
    # "`args = "-"` means no args file and is exempt from the path test, any other `args` path must be in git"
    _launch_fixture(tmp_path, _row_toml("P-L", script=JS, args="docs/northstar/plans/workflows_2026-10-07/nope.json",
                                        launch=JS_SHA))
    _launch_drift(run_main(tmp_path), "args path not in git")
    sub = tmp_path / "dash"
    sub.mkdir()
    _launch_fixture(sub, _row_toml("P-L", script=JS, args="-", launch=JS_SHA), files={JS: JS_TEXT})
    _launch_ok(run_main(sub), "args = - with no args file in git")


# ---------------------------------------------------------------- method rev 3, HARNESS-mm-3 (spec G17, A1, A2)
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" item 3 (check findings), G17, Amendments A1 and A2
# Interfaces fixed here (the spec leaves them open): the ledger is read from its default path
# docs/northstar/plans/push_ledger_2026-09-22.md under --repo and the date of a row is the author date of the commit
# that added its line (git blame); `check metrics` reads the lexicographically last
# docs/northstar/plans/method_rev3_2026-10-26/metrics/*.json, `{"week": ..., "metrics": [{"id":..., "status":...}]}`,
# prints `STATUS metrics WARN <ids>` (comma-joined) when any status is FAIL, else `STATUS metrics OK`; `check
# method_pins` reads docs/northstar/plans/method_rev3_2026-10-26/pins.toml and runs with `--base main` here.
MM_LEDGER = "docs/northstar/plans/push_ledger_2026-09-22.md"
MM_METRICS = "docs/northstar/plans/method_rev3_2026-10-26/metrics"
MM_PINS = "docs/northstar/plans/method_rev3_2026-10-26/pins.toml"
LEDGER_HEAD = "# Ledger\n\n| Time | Event | Detail |\n|---|---|---|\n"


def _commit_dated(repo, date, msg="mm"):
    import os
    env = {**os.environ, "GIT_AUTHOR_DATE": f"{date}T12:00:00+0000", "GIT_COMMITTER_DATE": f"{date}T12:00:00+0000"}
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                    "commit", "-q", "-m", msg], check=True, capture_output=True, env=env)


def _ledger_fixture(tmp_path, rows, date="2026-10-27"):
    build_fixture(tmp_path)
    _put(tmp_path, MM_LEDGER, LEDGER_HEAD + "".join(r + "\n" for r in rows))
    _commit_dated(tmp_path, date)


def _findings(res):
    return [ln for ln in status_lines(res) if ln.startswith("STATUS findings ")]


def test_mm3_findings_drift_on_finding_without_found_by(tmp_path):
    _ledger_fixture(tmp_path, ["| day40 | FINDING-bare | no token |"])
    res = run_check(tmp_path)
    assert any("DRIFT" in ln and "FINDING-bare" in ln for ln in _findings(res)), res.stdout + res.stderr
    assert res.returncode == 1


def test_mm3_findings_drift_on_td_without_ruler(tmp_path):
    _ledger_fixture(tmp_path, ["| day40 | TD-bare | no token |"])
    res = run_check(tmp_path)
    assert any("DRIFT" in ln and "TD-bare" in ln for ln in _findings(res)), res.stdout + res.stderr


def test_mm3_findings_ok_for_tagged_rows(tmp_path):
    _ledger_fixture(tmp_path, ["| day40 | FINDING-ok found-by=test | x |", "| day40 | TD-ok ruler=clerk | x |"])
    res = run_check(tmp_path)
    assert _findings(res) and all(" OK" in ln for ln in _findings(res)), res.stdout + res.stderr
    assert res.returncode == 0, res.stdout


def test_mm3_findings_ignores_rows_dated_before_2026_10_26(tmp_path):
    _ledger_fixture(tmp_path, ["| day30 | FINDING-old | x |", "| day30 | TD-old | x |"], date="2026-10-20")
    res = run_check(tmp_path)
    assert _findings(res) and all(" OK" in ln for ln in _findings(res)), res.stdout + res.stderr


def _metrics_fixture(tmp_path, files):
    build_fixture(tmp_path)
    import json
    for week, statuses in files.items():
        _put(tmp_path, f"{MM_METRICS}/{week}.json", json.dumps(
            {"week": week, "metrics": [{"id": i, "status": s} for i, s in statuses.items()]}))
    _commit_dated(tmp_path, "2026-10-27")


def test_mm3_metrics_warn_names_the_failing_ids(tmp_path):
    _metrics_fixture(tmp_path, {"2026-W44": {"M04": "FAIL", "M06": "FAIL", "M23": "PASS"}})
    res = run_check(tmp_path)
    hits = [ln for ln in status_lines(res) if ln.startswith("STATUS metrics ")]
    assert hits and hits[0].startswith("STATUS metrics WARN") and "M04" in hits[0] and "M06" in hits[0] \
        and "M23" not in hits[0], res.stdout + res.stderr
    assert res.returncode == 0, "WARN must not fail the gate"


def test_mm3_metrics_only_the_latest_week_counts(tmp_path):
    _metrics_fixture(tmp_path, {"2026-W43": {"M04": "FAIL"}, "2026-W44": {"M04": "PASS"}})
    res = run_check(tmp_path)
    hits = [ln for ln in status_lines(res) if ln.startswith("STATUS metrics ")]
    assert hits and hits[0].startswith("STATUS metrics OK"), res.stdout + res.stderr


def test_mm3_story_and_contract_are_accepted_piece_keys(tmp_path):
    build_fixture(tmp_path)
    p = tmp_path / PIECES
    p.write_text(p.read_text() + '\n[[piece]]\nid = "P-NEWKEYS"\nowns = ["n.c"]\nstory = "S-001"\n'
                 'contract = true\nstatus = { state = "queued" }\n')
    _commit_dated(tmp_path, "2026-10-27")
    res = run_check(tmp_path)
    assert not [ln for ln in status_lines(res) if "unknown key" in ln], res.stdout


def test_mm3_unknown_key_still_drifts_next_to_the_new_ones(tmp_path):
    build_fixture(tmp_path)
    p = tmp_path / PIECES
    p.write_text(p.read_text() + '\n[[piece]]\nid = "P-BAD"\nowns = ["n.c"]\nstory = "S-001"\nstroy = "x"\n'
                 'status = { state = "queued" }\n')
    _commit_dated(tmp_path, "2026-10-27")
    res = run_check(tmp_path)
    assert any("unknown key stroy in P-BAD" in ln for ln in status_lines(res)), res.stdout


SENT = "Every sim, pipe and lab story exists as failing tests before any code."


def _pins_toml(since):
    return f'[[pin]]\nfile = "CLAUDE.md"\nsentence = "{SENT}"\nsince = "{since}"\ngap = "G01"\n'


def _method_pins_fixture(tmp_path, since, claude_text):
    build_fixture(tmp_path)
    _put(tmp_path, "CLAUDE.md", claude_text)
    _put(tmp_path, MM_PINS, _pins_toml(since))
    _commit_dated(tmp_path, "2026-10-27")


def _mp(res):
    return [ln for ln in status_lines(res) if ln.startswith("STATUS method_pins ")]


def test_mm3_method_pins_drift_when_a_dated_pin_is_missing(tmp_path):
    _method_pins_fixture(tmp_path, "2026-10-30", "# Rules\nSomething else.\n")
    res = run_check(tmp_path, "--base", "main")
    assert any("DRIFT" in ln for ln in _mp(res)), res.stdout + res.stderr
    assert res.returncode == 1


def test_mm3_method_pins_ok_when_the_sentence_is_present(tmp_path):
    _method_pins_fixture(tmp_path, "2026-10-30", f"# Rules\n{SENT} More text.\n")
    res = run_check(tmp_path, "--base", "main")
    assert _mp(res) and all(" OK" in ln for ln in _mp(res)), res.stdout + res.stderr


def test_mm3_method_pins_empty_since_is_skipped_without_a_drift_line(tmp_path):
    _method_pins_fixture(tmp_path, "", "# Rules\nSomething else.\n")
    res = run_check(tmp_path, "--base", "main")
    assert not [ln for ln in _mp(res) if "DRIFT" in ln], res.stdout + res.stderr
    assert not [ln for ln in status_lines(res) if SENT[:30] in ln or "G01" in ln], res.stdout
    assert res.returncode == 0, res.stdout
