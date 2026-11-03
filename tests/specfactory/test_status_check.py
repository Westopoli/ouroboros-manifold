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



# ---------------------------------------------------------------- lane_table





# ---------------------------------------------------------------- pieces





# ---------------------------------------------------------------- seen



# ---------------------------------------------------------------- roadmap






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






# -------- known keys





# -------- the PRE_LAUNCH_IDS tuple



# -------- check launch



















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










def _metrics_fixture(tmp_path, files):
    build_fixture(tmp_path)
    import json
    for week, statuses in files.items():
        _put(tmp_path, f"{MM_METRICS}/{week}.json", json.dumps(
            {"week": week, "metrics": [{"id": i, "status": s} for i, s in statuses.items()]}))
    _commit_dated(tmp_path, "2026-10-27")










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








# ---------------------------------------------------------------- H-050: row scope of the status check
# H-050: "The status check counts a story only when a commit changed that story's own row, not when its id is
# mentioned inside another row." (docs/method/harness.md row H-050; DEC-status-check-row-scope-2026-11-01:
# diff the row files between anchor and ref, keep lines starting `| <id> |`.)
# Fixture: anchor commit adds docs/method/README.md and a harness.md with rows; later commits edit rows.
# UNSTATED INTERFACE (reported): none; the script is run as `status_check.py --repo <dir> --base main`.

H050_HARNESS = "docs/method/harness.md"
H050_HEAD = "# Harness\n\n| Id | Story | Status | Evidence |\n|---|---|---|---|\n"


def _h050_repo(tmp_path, old_rows, new_rows):
    """Anchor commit holds old_rows; the next commit (after the anchor) rewrites harness.md to new_rows."""
    repo = tmp_path
    _git(repo, "init", "-q", "-b", "main")
    (repo / "docs/method").mkdir(parents=True)
    (repo / "docs/method/README.md").write_text("method\n")
    (repo / H050_HARNESS).write_text(H050_HEAD + old_rows)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "anchor")
    (repo / H050_HARNESS).write_text(H050_HEAD + new_rows)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit rows")


def _h050_run(tmp_path):
    return subprocess.run([sys.executable, str(SCRIPT), "--repo", str(tmp_path), "--base", "main"],
                          capture_output=True, text=True, cwd=tmp_path, timeout=60)


def test_h050_control_own_row_change_to_seen_still_counts(tmp_path):
    """H-050 control (green today): a commit that adds S-111's own row as Seen, with no `Seen S-111`
    commit, is `seen_without_commit DRIFT S-111`; so a red below means the scope is wrong, not the harness."""
    _h050_repo(tmp_path, "", "| S-111 | x | Seen | none |\n")
    res = _h050_run(tmp_path)
    assert "STATUS seen_without_commit DRIFT S-111" in res.stdout.splitlines(), res.stdout


def test_h050_control_own_row_change_to_tested_still_counts(tmp_path):
    """H-050 control (green today): adding S-112's own row as Tested with no `Land S-112` commit is
    `tested_without_land DRIFT S-112`."""
    _h050_repo(tmp_path, "", "| S-112 | x | Tested | none |\n")
    res = _h050_run(tmp_path)
    assert "STATUS tested_without_land DRIFT S-112" in res.stdout.splitlines(), res.stdout


def test_h050_mention_in_another_row_does_not_count_seen(tmp_path):
    """H-050: "counts a story only when a commit changed that story's own row, not when its id is mentioned
    inside another row." S-110's Seen row predates the anchor and is untouched; a later commit adds a row
    H-049 that mentions S-110. No `seen_without_commit DRIFT S-110`."""
    old = "| S-110 | x | Seen | none |\n"
    _h050_repo(tmp_path, old, old + "| H-049 | finding | Ready | S-110 diagnosis |\n")
    res = _h050_run(tmp_path)
    assert "STATUS seen_without_commit DRIFT S-110" not in res.stdout.splitlines(), res.stdout
    assert res.returncode == 0, res.stdout


def test_h050_mention_in_another_row_does_not_count_tested(tmp_path):
    """H-050: same rule for Tested: S-113's Tested row predates the anchor; a later row edit mentioning S-113
    does not make `tested_without_land DRIFT S-113`."""
    old = "| S-113 | x | Tested | none |\n| H-049 | finding | Ready | none |\n"
    new = "| S-113 | x | Tested | none |\n| H-049 | finding | Ready | S-113 diagnosis |\n"
    _h050_repo(tmp_path, old, new)
    res = _h050_run(tmp_path)
    assert "STATUS tested_without_land DRIFT S-113" not in res.stdout.splitlines(), res.stdout
    assert res.returncode == 0, res.stdout


def test_h050_own_row_status_edit_counts(tmp_path):
    """H-050: "counts a story only when a commit changed that story's own row". S-114's row exists before the
    anchor as Ready and a later commit edits it to Seen (the id's occurrence count is unchanged, which
    `git log -S` does not see); with no `Seen S-114` commit that is `seen_without_commit DRIFT S-114`."""
    _h050_repo(tmp_path, "| S-114 | x | Ready | none |\n", "| S-114 | x | Seen | none |\n")
    res = _h050_run(tmp_path)
    assert "STATUS seen_without_commit DRIFT S-114" in res.stdout.splitlines(), res.stdout


# ---------------------------------------------------------------- H-077: check `mail`
# H-077 (docs/stories/H-077.md, Tests 12): "an unread `block` aged 31 minutes prints `STATUS mail DRIFT`; aged 5 minutes
# prints `STATUS mail OK 1 unread`; an unknown `from` prints the sender DRIFT." DRAFT-mail-stale is 30 minutes
# (README Numbers). Interfaces: `STATUS mail DRIFT <agent> <class> unread <min>m`, `STATUS mail DRIFT sender <name>`,
# else `STATUS mail OK <n> unread`; exit 1 on DRIFT. UNSTATED INTERFACE (reported): the mail root is
# $OM_PUSH_DIR/mail and the registry is $OM_AGENTS_TOML (tests/method/mailfix.py).
# Controls (green today): the fixture builder and the unread-line writer produce a parseable inbox.

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "method"))
from mailfix import lines as _mail_lines, make_env as _mail_env, put_mail as _put_mail  # noqa: E402


def _mail_run(tmp_path, env):
    repo = tmp_path / "repo"
    repo.mkdir()
    _h050_repo(repo, "| S-1 | x | Ready | none |\n", "| S-1 | x | Ready | edited |\n")
    return subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), "--base", "main"],
                          capture_output=True, text=True, cwd=repo, timeout=60, env=env)


def _mail_lines_of(res):
    return [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS mail ")]


def test_h077_control_unread_fixture_is_parseable(tmp_path):
    env, root = _mail_env(tmp_path)
    _put_mail(root, "architect", cls="block", minutes_ago=31)
    got = _mail_lines(root / "architect" / "inbox.jsonl")
    assert len(got) == 1 and got[0]["class"] == "block" and got[0]["read"] is None


def test_h077_unread_block_aged_31_minutes_is_drift_and_exit_1(tmp_path):
    env, root = _mail_env(tmp_path)
    _put_mail(root, "architect", cls="block", minutes_ago=31)
    res = _mail_run(tmp_path, env)
    hits = _mail_lines_of(res)
    assert len(hits) == 1 and hits[0].startswith("STATUS mail DRIFT architect block unread 3"), res.stdout
    assert res.returncode == 1, res.stdout


def test_h077_unread_ask_aged_31_minutes_is_drift(tmp_path):
    env, root = _mail_env(tmp_path)
    _put_mail(root, "architect", cls="ask", minutes_ago=31)
    hits = _mail_lines_of(_mail_run(tmp_path, env))
    assert hits and hits[0].startswith("STATUS mail DRIFT architect ask unread"), hits


def test_h077_unread_block_aged_5_minutes_is_ok_one_unread(tmp_path):
    env, root = _mail_env(tmp_path)
    _put_mail(root, "architect", cls="block", minutes_ago=5)
    res = _mail_run(tmp_path, env)
    assert _mail_lines_of(res) == ["STATUS mail OK 1 unread"], res.stdout


def test_h077_old_info_is_not_stale(tmp_path):
    """Rule: only an unread `block` or `ask` goes stale."""
    env, root = _mail_env(tmp_path)
    _put_mail(root, "architect", cls="info", minutes_ago=90)
    assert _mail_lines_of(_mail_run(tmp_path, env)) == ["STATUS mail OK 1 unread"]


def test_h077_unknown_sender_is_drift(tmp_path):
    env, root = _mail_env(tmp_path)
    _put_mail(root, "architect", cls="info", frm="some-stranger")
    hits = _mail_lines_of(_mail_run(tmp_path, env))
    assert "STATUS mail DRIFT sender some-stranger" in hits, hits


def test_h077_registry_name_and_sub_agent_id_senders_are_not_drift(tmp_path):
    env, root = _mail_env(tmp_path)
    _put_mail(root, "architect", cls="info", frm="runner-lab")
    _put_mail(root, "architect", cls="info", frm="a93eaf778770b83ac")
    assert _mail_lines_of(_mail_run(tmp_path, env)) == ["STATUS mail OK 2 unread"]
