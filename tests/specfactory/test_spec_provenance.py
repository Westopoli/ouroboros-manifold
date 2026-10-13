# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md "Lane H part 3: the spec provenance lint (HARNESS-provenance ...)"
#       and "Rev 12b rulings on the script drafters' gaps" (HARNESS-provenance paragraph) and "Rev 12c (2026-10-12), batch 2"
"""Tests for scripts/specfactory/spec_provenance.py (piece HARNESS-provenance, method rev 3).

Westley's recorded words (spec, Lane H part 3): "#14: approved" (2026-10-11).
Rule proved here (spec Lane H part 3): the lint "exits 1 and prints file:line:
<reason>" for reasons (1) to (7); Rev 12b: "Output line <path>:<line>: (<n>)
<text>"; "The unit of a behaviour sentence is a heading, a list item or a
blank-separated paragraph, whole words; a heading that claims approval with no
file:line fails by reason (3), which is why rev 10 line 86 counts"; "The
acceptance case asserts at least 39 reports on the rev 10 fixture; fewer is a
STOP that says the lint is weaker than the audit, not a tune."

Each case builds a throwaway tree in tmp_path (docs/bible/epics/E-99-test.md
with rule R-990-01, a register with a closed row Q-990-01 and an open row
Q-990-02, a ledger row for DRAFT-test-thing) so the repo root rule (first
ancestor of the spec holding docs/bible/epics) finds it. The lint is run as a
subprocess; it is absent on the built tree, so every case that runs it is red
(exit 2, "can't open file") until the builder lands it.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "spec_provenance.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "spec_rev10.md"

FINDING_RE = re.compile(r":(\d+): \((\d)\)")
TAG_RE = re.compile(r"\[W Q-|\[W \d{4}-\d\d-\d\d|\[B R-|\[P |\[DRAFT-")

EPIC_TEXT = (
    "# E-99 Test epic\n\n"
    "- R-990-01  Given a town, When it grows, Then it never form rings around the core.\n"
)
REGISTER_TEXT = (
    "# Ambiguity Register\n\n"
    "| Flag | Epic / story | Question | Candidate answers | Status | Answer |\n"
    "|---|---|---|---|---|---|\n"
    "| Q-990-01 | E-99 | A closed test question? | (a) yes; (b) no | closed | (a). |\n"
    "| Q-990-02 | E-99 | An open test question? | (a) yes; (b) no | open | none yet |\n"
)
LEDGER_TEXT = (
    "# Ledger\n\n"
    "| day | what | where | note |\n"
    "|---|---|---|---|\n"
    "| day31 | DRAFT-test-thing (named draft) | x.c | 5 units. Architect draft. |\n"
)

# A ten-line spec; every behaviour paragraph carries exactly one tag.
PASSING_SPEC = (
    "# Test spec\n\n"
    "The tile shows 5 wu of rubble when asked. [W Q-990-01]\n\n"
    "The tile refuses 3 clicks. [W 2026-10-11: \"ok\"]\n\n"
    "The lot draws 7 rows. [B R-990-01]\n\n"
    "The view sees 12 cells. [P csrc/x.c:12]\n\n"
    "The default is 4 ticks. [DRAFT-test-thing]\n"
)


def _tree(tmp_path: Path, spec_text: str) -> Path:
    root = tmp_path / "tree"
    (root / "docs" / "bible" / "epics").mkdir(parents=True)
    (root / "docs" / "northstar" / "plans").mkdir(parents=True)
    (root / "docs" / "bible" / "epics" / "E-99-test.md").write_text(EPIC_TEXT)
    (root / "docs" / "northstar" / "ambiguity_register.md").write_text(REGISTER_TEXT)
    (root / "docs" / "northstar" / "plans" / "push_ledger_2026-09-22.md").write_text(LEDGER_TEXT)
    spec = root / "spec.md"
    spec.write_text(spec_text)
    return spec


def _lint(spec: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), str(spec)], cwd=REPO,
                          capture_output=True, text=True)


def _findings(res: subprocess.CompletedProcess):
    """[(line, reason, full output line)] for every finding line on stdout."""
    out = []
    for l in res.stdout.splitlines():
        m = FINDING_RE.search(l)
        if m:
            out.append((int(m.group(1)), int(m.group(2)), l))
    return out


def _line_of(text: str, needle: str) -> int:
    for i, l in enumerate(text.splitlines(), 1):
        if needle in l:
            return i
    raise AssertionError(f"{needle!r} not in fixture text")


def _run_text(tmp_path: Path, text: str):
    spec = _tree(tmp_path, text)
    res = _lint(spec)
    return spec, res, _findings(res)


# ---- positive control: green today, needs no script -------------------------------

def test_control_rev10_fixture_is_the_quoted_file():
    # Proves the committed fixture is the rev 10 spec the audit counted 39 on.
    text = FIXTURE.read_text()
    lines = text.splitlines()
    assert "rev 10, 2026-10-10: lane E1 part c" in lines[0]
    assert len(lines) == 290
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == \
        "91945bfafc33ed6e10c287b0893427658e122d93b39dc55be95d9bc7572bc748"
    assert lines[85].startswith("### Lane B: galaxy") and "look approved 2026-10-07" in lines[85]
    assert lines[116].startswith("Pieces. Part a:") and "E1e placement + footprint clearing" in lines[116]
    assert lines[145].startswith("- E1b density (REPLACED by part c, rev 10)")
    assert lines[148].startswith("- E1e placement: as the builder drafted") and "refused" in lines[148]
    assert not TAG_RE.search(text), "rev 10 carries no provenance tags"


# ---- the passing case --------------------------------------------------------------

def test_tagged_ten_line_spec_passes(tmp_path):
    # Reasons (1) to (6) all satisfied: one tag per behaviour paragraph, each
    # tag valid ("a tag covers its paragraph"); exit 0, no output.
    spec, res, found = _run_text(tmp_path, PASSING_SPEC)
    assert res.returncode == 0, res.stdout + res.stderr
    assert res.stdout.strip() == ""


# ---- one red case per reason ---------------------------------------------------------

def test_reason1_untagged_behaviour_paragraph(tmp_path):
    # (1) "a behaviour sentence without a provenance tag": 'refuses' plus a
    # number with a unit; reported at the paragraph's first line.
    text = "# Test spec\n\nThe tile refuses 5 wu of rubble.\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    assert (3, 1) in [(l, n) for l, n, _ in found], res.stdout
    assert any(l.startswith(f"{spec}:3: (1)") for _, _, l in found), res.stdout


def test_reason1_tag_covers_its_paragraph(tmp_path):
    # (1) "a tag covers its paragraph": the same paragraph with a tag after it,
    # even on a continuation line, exits 0.
    text = "# Test spec\n\nThe tile refuses 5 wu of rubble.\nSecond line. [W Q-990-01]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 0, res.stdout + res.stderr
    assert found == []


def test_reason1_multiline_paragraph_reported_at_first_line(tmp_path):
    # Rev 12b: "reported at its first line" for the blank-separated paragraph.
    text = "# Test spec\n\nIntro words only.\n\nThe tile sees\nthe 5 wu of rubble.\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, n) for l, n, _ in found if n == 1] == [(5, 1)], res.stdout


def test_reason2_words_that_stand_in_for_a_source(tmp_path):
    # (2) the words "liberty", "as the builder drafted", "Architect default"
    # anywhere (here in tagged, otherwise valid paragraphs).
    for phrase in ("liberty", "as the builder drafted", "Architect default"):
        sub = tmp_path / phrase.replace(" ", "_")
        sub.mkdir()
        text = f"# Test spec\n\nA note: {phrase}, nothing more. [W Q-990-01]\n"
        spec, res, found = _run_text(sub, text)
        assert res.returncode == 1, (phrase, res.stdout + res.stderr)
        assert (3, 2) in [(l, n) for l, n, _ in found], (phrase, res.stdout)


def test_reason3_p_tag_without_file_line(tmp_path):
    # (3) "a [P ...] paragraph with no file:line citation".
    text = "# Test spec\n\nThe view sees 12 cells. [P csrc/x.c]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    assert (3, 3) in [(l, n) for l, n, _ in found], res.stdout


def test_reason3_heading_claiming_approval_without_file_line(tmp_path):
    # (3) Rev 12b: "a heading that claims approval with no file:line fails by
    # reason (3), which is why rev 10 line 86 counts".
    text = "# Test spec\n\n### Lane Z (look approved 2026-10-07)\n\nPlain words only.\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    assert (3, 3) in [(l, n) for l, n, _ in found], res.stdout


def test_reason3_heading_with_file_line_citation_is_clean(tmp_path):
    # (3) negative: the same heading carrying a [P csrc/x.c:12] citation does not fail.
    text = "# Test spec\n\n### Lane Z (look approved 2026-10-07) [P csrc/x.c:12]\n\nPlain words only.\n"
    spec, res, found = _run_text(tmp_path, text)
    assert [n for _, n, _ in found if n == 3] == [], res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_reason4_bible_rule_id_absent_from_epics(tmp_path):
    # (4) "a [B R-id] whose id is absent from docs/bible/epics/*.md".
    text = "# Test spec\n\nThe lot draws 7 rows. [B R-991-01]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    assert (3, 4) in [(l, n) for l, n, _ in found], res.stdout


def test_reason5_register_row_open_or_missing(tmp_path):
    # (5) "a [W Q-id] whose register row is not closed": an open row, and no row.
    text = ("# Test spec\n\nThe tile shows 5 wu. [W Q-990-02]\n\n"
            "The tile shows 6 wu. [W Q-990-03]\n")
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    got = [(l, n) for l, n, _ in found]
    assert (3, 5) in got, res.stdout
    assert (5, 5) in got, res.stdout


def test_reason6_draft_without_ledger_or_register_row(tmp_path):
    # (6) "a [DRAFT-name] with no ledger or register row of that name".
    text = "# Test spec\n\nThe default is 4 ticks. [DRAFT-nothing-here]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    assert (3, 6) in [(l, n) for l, n, _ in found], res.stdout


E1E_REFUSE = "**E1e, placement, the building is refused on overlap. [W Q-990-01]"
E1E_CLEAR = "**E1e (rubble), the ground is cleared first. [W Q-990-01]"


def test_reason7_refuse_versus_clear_on_one_piece_id(tmp_path):
    # (7) "two sentences in one spec naming the same piece id with 'refuse' in
    # one and 'clear' in the other" (CLASH_PAIRS first pair, substrings).
    text = f"# Test spec\n\n{E1E_REFUSE}\n\n{E1E_CLEAR}\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    assert any(n == 7 for _, n, _ in found), res.stdout


def test_reason7_needs_both_words(tmp_path):
    # (7) negative: only one paragraph has either word.
    text = f"# Test spec\n\n{E1E_REFUSE}\n\n**E1e (rubble), the ground is flat. [W Q-990-01]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 0, res.stdout + res.stderr
    assert found == []


def test_reason7_needs_the_same_piece_id(tmp_path):
    # (7) negative: the ids differ, so no clash.
    text = f"# Test spec\n\n{E1E_REFUSE}\n\n**E2f (rubble), the ground is cleared first. [W Q-990-01]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 0, res.stdout + res.stderr
    assert found == []


def test_reason7_ring_versus_cited_rule_never_form_rings(tmp_path):
    # (7) "'ring' in one and 'never form rings' in a cited rule": R-990-01 in the
    # tmp epic reads "never form rings"; a paragraph of the same piece uses 'ring'.
    text = ("# Test spec\n\n"
            "**E3a, the lots follow the street. [B R-990-01]\n\n"
            "**E3a (view), the town grows a ring of lots. [W Q-990-01]\n")
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 1, res.stdout + res.stderr
    assert any(n == 7 for _, n, _ in found), res.stdout


# ---- the acceptance case: the rev 10 fixture ----------------------------------------

def test_acceptance_rev10_fixture_reports_at_least_39(tmp_path):
    # Spec: "reports at least 39 untagged behaviour lines including lines 146,
    # 149 and 86 ... and reason (7) fires on the E1e pair (117 versus 149)".
    # 39 is the spec's number: fewer is a STOP for the Architect (the lint is
    # weaker than the audit), never a tune.
    res = _lint(FIXTURE)
    found = _findings(res)
    assert res.returncode == 1, res.stdout + res.stderr
    assert len(found) >= 39, f"{len(found)} findings, spec says at least 39\n{res.stdout}"
    got = {(l, n) for l, n, _ in found}
    assert (146, 1) in got, res.stdout
    assert (149, 1) in got, res.stdout
    assert (86, 3) in got, res.stdout
    clash = [l for _, n, l in found if n == 7
             and re.search(r"\b117\b", l.split("(7)", 1)[1])
             and re.search(r"\b149\b", l.split("(7)", 1)[1])]
    assert clash, "no (7) finding naming both line 117 and line 149\n" + res.stdout
