# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md "Lane H part 3: the spec provenance lint (HARNESS-provenance ...)"
#       and "Rev 12b rulings on the script drafters' gaps" (HARNESS-provenance paragraph) and "Rev 12c (2026-10-12), batch 2"
# Rule pins: R-990-01@?, R-990-02@?, R-991-01@?
"""Tests for scripts/specfactory/spec_provenance.py (piece HARNESS-provenance, method rev 3).

Westley's recorded words (spec, Lane H part 3): "#14: approved" (2026-10-11).
Rule proved here (spec Lane H part 3): the lint "exits 1 and prints file:line:
<reason>" for reasons (1) to (7); Rev 12b: "Output line <path>:<line>: (<n>)
<text>"; "The unit of a behaviour sentence is a heading, a list item or a
blank-separated paragraph, whole words; a heading that claims approval with no
file:line fails by reason (3), which is why rev 10 line 86 counts"; "The
acceptance case asserts at least 39 reports on the rev 10 fixture; fewer is a
STOP that says the lint is weaker than the audit, not a tune."

HARNESS-C1a (docs/northstar/plans/2026-10-19-harness-enforcement-spec.md section 1, rev 3a) extends this file at
the bottom: reason (8) (a [B R-id] tag carries a pin, "no pin" / "pin is stale"), a multi-id [B] tag checked per id,
and the heading exemption of reason (1). Fixture ids are pinned @? above: the fixture epics are the only place
R-990-01 has a rule line. Moved under ledger row TD-HARNESS-C1: PASSING_SPEC carries the pin in its [B] tag.

HARNESS-C235 (same spec, section 1 HARNESS-C235, rev 3a) extends this file below the C1a block: reason (9)
quantified quotes ([ASSERT tests/<path>::<name>], W_TAG parse, key clause inside an assertion line), reason (10)
numbers after a quote (DRAFT-delay style names in the sentence), reason (11) set-asides ([OPEN Q-x] on an open
register row whose Answer names a piece id or an FU- row), the register status `reading`, and the malformed-row
finding under reason (5). Named drafts used: DRAFT-quantifiers (the twelve words), DRAFT-set-aside-phrases (the
seven phrases). Nothing above moves: _tree and _run_text gained optional trailing arguments (register text, extra
files) and keep their old behaviour. The fixture ids stay R-990-01 (pinned @? above) and the register ids Q-990-xx.
UNSTATED INTERFACES (reported): the reason number of the `unquoted [W] text contains "["` finding (the spec names the
text, not the number, so only the text is asserted); the wording of reason (5)'s finding for a `deferred`/`superseded`
row (only "(5)" at the unit's line is asserted).

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

FINDING_RE = re.compile(r":(\d+): \((\d+)\)")
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

# Section 3 of the harness enforcement spec: sha256(" ".join(rule_line_after_id.split()))[:6] of the rule line above.
PIN_990_01 = hashlib.sha256(" ".join(EPIC_TEXT.splitlines()[2].split(None, 2)[2].split()).encode("utf-8")
                            ).hexdigest()[:6]
STALE_PIN = "000000"

# A ten-line spec; every behaviour paragraph carries exactly one tag.
PASSING_SPEC = (
    "# Test spec\n\n"
    "The tile shows 5 wu of rubble when asked. [W Q-990-01]\n\n"
    "The tile refuses 3 clicks. [W 2026-10-11: \"ok\"]\n\n"
    f"The lot draws 7 rows. [B R-990-01@{PIN_990_01}]\n\n"
    "The view sees 12 cells. [P csrc/x.c:12]\n\n"
    "The default is 4 ticks. [DRAFT-test-thing]\n"
)


def _tree(tmp_path: Path, spec_text: str, register: str = REGISTER_TEXT, files=()) -> Path:
    root = tmp_path / "tree"
    (root / "docs" / "bible" / "epics").mkdir(parents=True)
    (root / "docs" / "northstar" / "plans").mkdir(parents=True)
    (root / "docs" / "bible" / "epics" / "E-99-test.md").write_text(EPIC_TEXT)
    (root / "docs" / "northstar" / "ambiguity_register.md").write_text(register)
    (root / "docs" / "northstar" / "plans" / "push_ledger_2026-09-22.md").write_text(LEDGER_TEXT)
    for rel, body in files:                      # HARNESS-C235: files under the spec's root (a test for [ASSERT])
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body)
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


def _run_text(tmp_path: Path, text: str, register: str = REGISTER_TEXT, files=()):
    spec = _tree(tmp_path, text, register, files)
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
        "97b18ad0f4d9f2d7c29a89c1c51348551ab6415615c6a4721302cbbf50aae95e"
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


# ---- HARNESS-C1a: reason (8) pins, multi-id tags, heading exemption --------------------
# Spec sentences (HARNESS-C1a, rev 3a): "New reason (8), emitted beside reason 4: `[B R-id] has no pin` when the
# pin group is empty, and `[B R-id@xxxxxx] pin is stale: the rule line is now yyyyyy` when it differs; an id
# absent from the epics is reason 4's finding only."; "A `[B ...]` tag may name several rules; each id carries its
# own pin"; "Reason 1 skips heading units: a heading is a title, not a behaviour unit".

def test_control_pin_constant_is_the_known_value():
    # Green today: the in-file formula gives the value the rule_pins tests use as their literal.
    assert PIN_990_01 == "b2a3c8"
    assert STALE_PIN != PIN_990_01


def test_control_pinned_tag_with_the_right_pin_still_passes(tmp_path):
    # Green today and after: a pin group on a present rule is no finding (reasons 4 and 8 both quiet).
    spec, res, found = _run_text(tmp_path, f"# Test spec\n\nThe lot draws 7 rows. [B R-990-01@{PIN_990_01}]\n")
    assert res.returncode == 0, res.stdout + res.stderr
    assert res.stdout.strip() == ""


def test_control_multi_id_tag_checks_every_id_for_reason_4(tmp_path):
    # Green today and after (audit M5): the id after the comma is reason 4's, the present id is not.
    text = "# Test spec\n\nThe lot draws 7 rows. [B R-990-01, R-990-02: words]\n"
    spec, res, found = _run_text(tmp_path, text)
    r4 = [l for _, n, l in found if n == 4]
    assert len(r4) == 1 and "R-990-02" in r4[0] and "R-990-01" not in r4[0], res.stdout


def test_control_backticked_b_tag_stays_invisible_to_the_lint(tmp_path):
    # Green today and after: a tag in backticks is blanked (CODE_SPAN), so the unit is untagged (reason 1);
    # this is the blindness `rule_pins.py unwrap` removes, and the reason `unwrap` leaves placeholders alone.
    text = "# Test spec\n\nThe lot draws 7 rows. `[B R-990-01]`\n"
    spec, res, found = _run_text(tmp_path, text)
    assert (3, 1) in [(l, n) for l, n, _ in found], res.stdout


def test_control_reason1_flags_a_numbered_paragraph(tmp_path):
    # Green today and after: the text of the heading case below, as a paragraph, is a reason 1 finding.
    spec, res, found = _run_text(tmp_path, "# Test spec\n\nHeading 2026\n")
    assert (3, 1) in [(l, n) for l, n, _ in found], res.stdout


def test_reason8_tag_without_a_pin_is_a_finding(tmp_path):
    spec, res, found = _run_text(tmp_path, "# Test spec\n\nThe lot draws 7 rows. [B R-990-01]\n")
    assert "(8)" in res.stdout, "reason (8) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 1, res.stdout + res.stderr
    assert any(l.startswith(f"{spec}:3: (8)") and "[B R-990-01] has no pin" in l for _, _, l in found), res.stdout


def test_reason8_stale_pin_names_both_pins(tmp_path):
    text = f"# Test spec\n\nThe lot draws 7 rows. [B R-990-01@{STALE_PIN}]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert "(8)" in res.stdout, "reason (8) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 1, res.stdout + res.stderr
    want = f"[B R-990-01@{STALE_PIN}] pin is stale: the rule line is now {PIN_990_01}"
    assert any(l.startswith(f"{spec}:3: (8)") and want in l for _, _, l in found), res.stdout


def test_reason8_multi_id_tag_checks_each_id_and_an_absent_id_is_reason_4_only(tmp_path):
    text = f"# Test spec\n\nThe lot draws 7 rows. [B R-990-01@{STALE_PIN}, R-990-02@aaaaaa: words]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert "(8)" in res.stdout, "reason (8) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 1, res.stdout + res.stderr
    r8 = [l for _, n, l in found if n == 8]
    r4 = [l for _, n, l in found if n == 4]
    assert len(r8) == 1 and "R-990-01@" + STALE_PIN in r8[0] and "R-990-02" not in r8[0], res.stdout
    assert len(r4) == 1 and "R-990-02" in r4[0], res.stdout


def test_reason8_editing_the_rule_line_makes_a_passing_spec_fail(tmp_path):
    text = f"# Test spec\n\nThe lot draws 7 rows. [B R-990-01@{PIN_990_01}]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert res.returncode == 0, res.stdout + res.stderr          # passes on the fixture rule line
    epic = spec.parent / "docs" / "bible" / "epics" / "E-99-test.md"
    edited = EPIC_TEXT.replace("never form rings", "never form squares")
    epic.write_text(edited)
    new_pin = hashlib.sha256(" ".join(edited.splitlines()[2].split(None, 2)[2].split()).encode("utf-8")
                             ).hexdigest()[:6]
    assert new_pin != PIN_990_01
    res = _lint(spec)
    assert "(8)" in res.stdout, "reason (8) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 1, res.stdout + res.stderr
    want = f"[B R-990-01@{PIN_990_01}] pin is stale: the rule line is now {new_pin}"
    assert any(f"{spec}:3: (8)" in l and want in l for l in res.stdout.splitlines()), res.stdout


def test_reason1_skips_a_heading_unit(tmp_path):
    # "a `### Heading 2026` unit gives no reason 1" (a title, not a behaviour unit).
    spec, res, found = _run_text(tmp_path, "# Test spec\n\n### Heading 2026\n")
    assert [n for _, n, _ in found if n == 1] == [], res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


# ---- HARNESS-C235: reasons 9, 10, 11, [ASSERT]/[OPEN], reading status ------------------------------------
# Spec sentences (HARNESS-C235, rev 3a), cited by the case that proves each; "Tests first: ..." gives the inputs.

NEVER = "never a square at any age"
PY_GOOD = ("import pytest\n\n@pytest.mark.slow\ndef test_x():\n    # " + NEVER + "\n    shape = 'round'\n"
           "    assert shape != 'square', \"" + NEVER + "\"\n\n\ndef test_other():\n    assert True\n")
PY_COMMENT_ONLY = "def test_x():\n    # " + NEVER + "\n    assert True\n"
PY_NEXT_FUNCTION = ("def test_x():\n    assert True\n\n@pytest.mark.slow\ndef test_y():\n"
                    "    assert shape != 'square', \"" + NEVER + "\"\n")
PY_CONTINUED = "def test_x():\n    assert shape != 'square', (\n        \"" + NEVER + "\"\n    )\n"
GD_STATIC = ("extends SceneTree\n\nstatic func test_x() -> void:\n\tvar shape = 'round'\n"
             "\t_assert(shape != 'square', \"" + NEVER + "\")\n\nfunc test_other() -> void:\n\tpass\n")
GD_NEXT_FUNCTION = ("extends SceneTree\n\nstatic func test_x() -> void:\n\tpass\n\n"
                    "func test_y() -> void:\n\t_assert(true, \"" + NEVER + "\")\n")
GD_ASSERT_HELPER = "func test_x() -> void:\n\tassert_eq(shape, 'round', \"" + NEVER + "\")\n"


def _w(quote, extra=""):
    return f"# Test spec\n\nShape rule. [W 2026-10-11: \"{quote}\"]{extra}\n"


def _rows(*rows):
    return REGISTER_TEXT + "".join(rows)


def _row(qid, status, answer):
    return f"| {qid} | E-99 | A question? | (a) yes; (b) no | {status} | {answer} |\n"


def _out_has(res, n, needle):
    return any(f"({n})" in l and needle in l for l in res.stdout.splitlines())


def test_control_c235_fixture_files_assert_the_quote_on_an_assertion_line():
    # Green today and after: the fixture test files carry the key clause where the spec says it must be
    # (an `assert ` / `_assert(` / `assert_` line), and PY_COMMENT_ONLY carries it only in a comment.
    for body in (PY_GOOD, PY_NEXT_FUNCTION, PY_CONTINUED, GD_STATIC, GD_ASSERT_HELPER):
        assert NEVER in body
    assert not [l for l in PY_COMMENT_ONLY.splitlines() if l.strip().startswith("assert") and NEVER in l]


def test_control_unquantified_quote_needs_no_assert(tmp_path):
    # Green today and after ("only whole words"): "soon" and "allowed" hold none of the twelve words.
    for quote in ("soon", "an allowed shape", "the alloy"):
        sub = tmp_path / quote.replace(" ", "_")
        sub.mkdir()
        spec, res, found = _run_text(sub, _w(quote))
        assert res.returncode == 0 and res.stdout.strip() == "", (quote, res.stdout + res.stderr)


def test_control_assert_with_a_body_that_asserts_the_clause_passes(tmp_path):
    # Green today and after: "passes with [ASSERT tests/t.py::test_x] whose body has assert ..., \"never a square at
    # any age\"" (today the tag is simply not looked at).
    spec, res, found = _run_text(tmp_path, _w(NEVER, " [ASSERT tests/t.py::test_x]"),
                                 files=[("tests/t.py", PY_GOOD)])
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr


def test_control_combined_w_tag_with_a_closed_row_and_a_date_passes(tmp_path):
    # Green today and after: "[W Q-990-01, 2026-10-11: \"x\"]" has a closed first id.
    spec, res, found = _run_text(tmp_path, '# Test spec\n\nShape rule. [W Q-990-01, 2026-10-11: "x"]\n')
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr


def test_reason9_quantified_quote_without_assert_is_a_finding(tmp_path):
    # "fixture spec with [W 2026-10-11: \"never a square at any age\"] fails reason 9 without [ASSERT]"
    spec, res, found = _run_text(tmp_path, _w(NEVER))
    assert "(9)" in res.stdout, "reason (9) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 0, res.stdout + res.stderr  # mm-5: reason 9 is a WARN (G03)
    assert any(l.startswith(f"{spec}:3: (9)") and "quantified quote has no [ASSERT]" in l for _, _, l in found), \
        res.stdout


def test_reason9_each_of_the_twelve_quantifiers_triggers(tmp_path):
    # DRAFT-quantifiers: "at least, at most, never, always, every, all, only, no more than, any age, within,
    # exactly, none", whole words, case-insensitive.
    words = ["at least", "at most", "never", "always", "every", "all", "only", "no more than", "any age",
             "within", "exactly", "none"]
    assert len(words) == 12
    for i, word in enumerate(words):
        sub = tmp_path / f"w{i}"
        sub.mkdir()
        quote = f"the tile is {word.upper() if i % 2 else word} round"
        spec, res, found = _run_text(sub, _w(quote))
        assert _out_has(res, 9, "quantified quote has no [ASSERT]"), (word, res.stdout + res.stderr)


def test_reason9_assert_whose_test_asserts_the_clause_in_a_python_file_with_a_decorator(tmp_path):
    # Section 5 (c): body slicing on a `.py` test with a decorator; a clause only in the NEXT function fails.
    spec, res, found = _run_text(tmp_path, _w(NEVER, " [ASSERT tests/t.py::test_x]"),
                                 files=[("tests/t.py", PY_NEXT_FUNCTION)])
    assert "(9)" in res.stdout, "reason (9) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 0, res.stdout + res.stderr  # mm-5: reason 9 is a WARN (G03)
    assert _out_has(res, 9, f"the test does not assert the quote's words: \"{NEVER}\""), res.stdout


def test_reason9_clause_only_in_a_comment_names_the_clause(tmp_path):
    # "fails naming the clause when the words sit only in a comment"
    spec, res, found = _run_text(tmp_path, _w(NEVER, " [ASSERT tests/t.py::test_x]"),
                                 files=[("tests/t.py", PY_COMMENT_ONLY)])
    assert "(9)" in res.stdout, "reason (9) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 0, res.stdout + res.stderr  # mm-5: reason 9 is a WARN (G03)
    assert any(l.startswith(f"{spec}:3: (9)") and f"[ASSERT tests/t.py::test_x] the test does not assert the "
               f"quote's words: \"{NEVER}\"" in l for _, _, l in found), res.stdout


def test_reason9_missing_file_and_missing_function_are_test_not_found(tmp_path):
    # "fails when the file is missing"; the function is found by `^\s*(?:async\s+)?def <name>\(`.
    spec, res, found = _run_text(tmp_path, _w(NEVER, " [ASSERT tests/missing.py::test_x]"))
    assert "(9)" in res.stdout, "reason (9) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 0, res.stdout + res.stderr  # mm-5: reason 9 is a WARN (G03)
    assert _out_has(res, 9, "[ASSERT tests/missing.py::test_x] test not found"), res.stdout
    sub = tmp_path / "nofn"
    sub.mkdir()
    spec, res, found = _run_text(sub, _w(NEVER, " [ASSERT tests/t.py::test_nope]"), files=[("tests/t.py", PY_GOOD)])
    assert _out_has(res, 9, "[ASSERT tests/t.py::test_nope] test not found"), res.stdout


def test_reason9_assertion_may_continue_over_lines_and_case_is_ignored(tmp_path):
    # Audit S2: an assertion line includes its continuation lines up to the closing parenthesis; the match is
    # whitespace-normalised and case-insensitive.
    quote = "Never   a square at any age"
    spec, res, found = _run_text(tmp_path, _w(quote, " [ASSERT tests/t.py::test_x]"),
                                 files=[("tests/t.py", PY_CONTINUED)])
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr
    sub = tmp_path / "second"
    sub.mkdir()
    spec, res, found = _run_text(sub, _w(quote), files=[("tests/t.py", PY_CONTINUED)])
    assert _out_has(res, 9, "quantified quote has no [ASSERT]"), "reason (9) is never emitted\n" + res.stdout


def test_reason9_key_clause_is_the_clause_with_the_first_quantifier(tmp_path):
    # "the quote's key clause (the clause holding the first quantifier, split on `.`, `;`, ` and `, ` so `)".
    quote = "the tile grows; it never forms a square and it is round"
    body = "def test_x():\n    assert grows, \"the tile grows\"\n"
    spec, res, found = _run_text(tmp_path, _w(quote, " [ASSERT tests/t.py::test_x]"), files=[("tests/t.py", body)])
    assert "(9)" in res.stdout, "reason (9) is never emitted\n" + res.stdout + res.stderr
    assert _out_has(res, 9, "the test does not assert the quote's words: \"it never forms a square\""), res.stdout
    sub = tmp_path / "good"
    sub.mkdir()
    body = "def test_x():\n    assert ok, \"it never forms a square\"\n"
    spec, res, found = _run_text(sub, _w(quote, " [ASSERT tests/t.py::test_x]"), files=[("tests/t.py", body)])
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr


def test_reason9_gd_static_func_body_ends_at_the_next_func(tmp_path):
    # Section 5 (c): body slicing on a `.gd` file with `static func`; `_assert(` and `assert_` lines count.
    spec, res, found = _run_text(tmp_path, _w(NEVER, " [ASSERT tests/t.gd::test_x]"), files=[("tests/t.gd", GD_STATIC)])
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr
    sub = tmp_path / "next"
    sub.mkdir()
    spec, res, found = _run_text(sub, _w(NEVER, " [ASSERT tests/t.gd::test_x]"),
                                 files=[("tests/t.gd", GD_NEXT_FUNCTION)])
    assert "(9)" in res.stdout, "reason (9) is never emitted\n" + res.stdout + res.stderr
    assert _out_has(res, 9, f"the test does not assert the quote's words: \"{NEVER}\""), res.stdout
    sub = tmp_path / "helper"
    sub.mkdir()
    spec, res, found = _run_text(sub, _w(NEVER, " [ASSERT tests/t.gd::test_x]"),
                                 files=[("tests/t.gd", GD_ASSERT_HELPER)])
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr


def test_w_tag_combined_form_parses_the_quote_after_the_date(tmp_path):
    # "the combined `[W Q-990-01, 2026-10-11: \"x\"]` parses with the date in group 2" (group 3 is then the quote).
    spec, res, found = _run_text(tmp_path, '# Test spec\n\nShape rule. [W Q-990-01, 2026-10-11: "never x"]\n')
    assert "(9)" in res.stdout, "reason (9) is never emitted\n" + res.stdout + res.stderr
    assert _out_has(res, 9, "quantified quote has no [ASSERT]"), res.stdout


def test_w_tag_quote_may_hold_a_closing_bracket_when_double_quoted(tmp_path):
    # W_TAG: group 3 "ends at `\"]`, so a `]` inside the quote is allowed".
    spec, res, found = _run_text(tmp_path, '# Test spec\n\nShape rule. [W 2026-10-11: "never a [square] at once"]\n')
    assert _out_has(res, 9, "quantified quote has no [ASSERT]"), "reason (9) is never emitted\n" + res.stdout
    assert not _out_has(res, 9, "unquoted"), res.stdout


def test_w_tag_unquoted_quote_with_an_open_bracket_is_the_quote_it_finding(tmp_path):
    # "an unquoted quote with `[` gives the quote-it finding" (the reason number is not given: text asserted).
    spec, res, found = _run_text(tmp_path, "# Test spec\n\nShape rule. [W Q-990-01: some [thing] here]\n")
    assert res.returncode == 1, res.stdout + res.stderr
    assert 'unquoted [W] text contains "[": put the quote in double quotes' in res.stdout, res.stdout


def test_assert_and_open_tags_start_a_provenance_tag(tmp_path):
    # TAG_START gains `\[ASSERT |\[OPEN Q-`: a unit with only one of them is covered for reason (1).
    text = ("# Test spec\n\nThe tile shows 5 wu. [OPEN Q-990-02]\n\n"
            "The tile shows 6 wu. [ASSERT tests/t.py::test_x]\n")
    spec, res, found = _run_text(tmp_path, text, files=[("tests/t.py", PY_GOOD)])
    assert [n for _, n, _ in found if n == 1] == [], res.stdout


def test_control_numbers_before_or_excluded_after_a_quote_pass(tmp_path):
    # Green today and after ("a number before the tag passes"; NUMBER matches that are a CITATION, a date, an id,
    # a `@pin`, or a `rev`/`wave` number are not checked).
    tails = ["the delay is 3 s. [W Q-990-01: \"soon\"]",
             "[W Q-990-01: \"soon\"] this lands in wave 9",
             "[W Q-990-01: \"soon\"] see rev 3",
             "[W Q-990-01: \"soon\"] see scripts/x.py:36",
             "[W Q-990-01: \"soon\"] on 2026-10-11",
             "[W Q-990-01: \"soon\"] under TD-HARNESS-C1 and FU-HARNESS-findings"]
    for i, tail in enumerate(tails):
        sub = tmp_path / f"t{i}"
        sub.mkdir()
        spec, res, found = _run_text(sub, "# Test spec\n\n" + tail + "\n")
        assert res.returncode == 0 and res.stdout.strip() == "", (tail, res.stdout + res.stderr)


def test_reason10_number_after_a_quote_with_no_draft_in_its_sentence(tmp_path):
    # "`[W Q-990-01: \"soon\"] the delay is 3 s` fails reason 10" (the spec names Q-990-03; Q-990-01 is the closed
    # fixture row here).
    spec, res, found = _run_text(tmp_path, '# Test spec\n\n[W Q-990-01: "soon"] the delay is 3 s\n')
    assert "(10)" in res.stdout, "reason (10) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 1, res.stdout + res.stderr
    assert any(l.startswith(f"{spec}:3: (10)") and "number 3 after a quote with no DRAFT in its sentence" in l
               for _, _, l in found), res.stdout


def test_reason10_a_draft_in_the_sentence_passes_a_draft_in_another_sentence_does_not(tmp_path):
    # "`... 3 s (DRAFT-delay)` passes"; the sentence is split on `. `.
    spec, res, found = _run_text(tmp_path, '# Test spec\n\n[W Q-990-01: "soon"] the delay is 3 s (DRAFT-delay)\n')
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr
    sub = tmp_path / "other"
    sub.mkdir()
    spec, res, found = _run_text(sub, '# Test spec\n\n[W Q-990-01: "soon"] the delay is 3 s. See DRAFT-delay.\n')
    assert "(10)" in res.stdout, "reason (10) is never emitted\n" + res.stdout + res.stderr
    assert _out_has(res, 10, "number 3 after a quote with no DRAFT in its sentence"), res.stdout


def test_reason11_set_aside_rule_without_an_open_flag(tmp_path):
    # "`R-990-01 is deferred to a later piece` fails reason 11"
    spec, res, found = _run_text(tmp_path, "# Test spec\n\nR-990-01 is deferred to a later piece\n")
    assert "(11)" in res.stdout, "reason (11) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 1, res.stdout + res.stderr
    assert any(l.startswith(f"{spec}:3: (11)") and "R-990-01 set aside with no [OPEN Q-x]" in l
               for _, _, l in found), res.stdout


def test_reason11_each_of_the_seven_phrases_triggers_and_a_unit_without_a_rule_does_not(tmp_path):
    # DRAFT-set-aside-phrases: "not in scope, out of scope, set aside, not this piece, deferred, later, follow-up".
    phrases = ["not in scope", "out of scope", "set aside", "not this piece", "deferred", "later", "follow-up"]
    assert len(phrases) == 7
    for i, phrase in enumerate(phrases):
        sub = tmp_path / f"p{i}"
        sub.mkdir()
        spec, res, found = _run_text(sub, f"# Test spec\n\nR-990-01 is {phrase}\n")
        assert _out_has(res, 11, "R-990-01 set aside with no [OPEN Q-x]"), (phrase, res.stdout + res.stderr)
    sub = tmp_path / "norule"
    sub.mkdir()
    spec, res, found = _run_text(sub, "# Test spec\n\nThis piece is deferred to a later piece\n")
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr


def test_control_reason11_open_flag_on_an_open_row_naming_a_piece_passes(tmp_path):
    # Green today and after: "with `[OPEN Q-990-02]` (open, names `VG-X1`) passes"; an `FU-` row also counts.
    text = "# Test spec\n\nR-990-01 is deferred to a later piece. [OPEN Q-990-02]\n"
    reg = REGISTER_TEXT.replace("| open | none yet |", "| open | waits on VG-X1 |")
    spec, res, found = _run_text(tmp_path, text, register=reg)
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr
    sub = tmp_path / "fu"
    sub.mkdir()
    reg = REGISTER_TEXT.replace("| open | none yet |", "| open | waits on FU-LATER-1 |")
    spec, res, found = _run_text(sub, text, register=reg)
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr


def test_reason11_open_flag_on_a_closed_row_is_a_finding(tmp_path):
    # "with a closed row fails" (Q-990-01 is the closed fixture row).
    text = "# Test spec\n\nR-990-01 is deferred to a later piece. [OPEN Q-990-01]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert "(11)" in res.stdout, "reason (11) is never emitted\n" + res.stdout + res.stderr
    assert res.returncode == 1, res.stdout + res.stderr
    assert any(l.startswith(f"{spec}:3: (11)") and "[OPEN Q-990-01] row is not open" in l for _, _, l in found), \
        res.stdout


def test_reason11_open_row_that_names_no_piece_is_a_finding(tmp_path):
    # Q-990-02 is open with the Answer "none yet": "[OPEN Q-x] row names no piece that waits".
    text = "# Test spec\n\nR-990-01 is deferred to a later piece. [OPEN Q-990-02]\n"
    spec, res, found = _run_text(tmp_path, text)
    assert "(11)" in res.stdout, "reason (11) is never emitted\n" + res.stdout + res.stderr
    assert any(l.startswith(f"{spec}:3: (11)") and "[OPEN Q-990-02] row names no piece that waits" in l
               for _, _, l in found), res.stdout


def test_control_w_tag_on_open_deferred_superseded_or_missing_rows_is_reason_5(tmp_path):
    # Green today and after: reason 5 "rejects `open`, `deferred`, `superseded` and a missing row".
    reg = _rows(_row("Q-990-04", "deferred", "(a)"), _row("Q-990-05", "superseded", "(a)"))
    text = ("# Test spec\n\nThe tile shows 1 wu. [W Q-990-02]\n\nThe tile shows 2 wu. [W Q-990-04]\n\n"
            "The tile shows 3 wu. [W Q-990-05]\n\nThe tile shows 4 wu. [W Q-990-09]\n")
    spec, res, found = _run_text(tmp_path, text, register=reg)
    assert sorted((l, n) for l, n, _ in found if n == 5) == [(3, 5), (5, 5), (7, 5), (9, 5)], res.stdout


def test_reason5_reading_row_passes(tmp_path):
    # "`[W Q-990-03]` on a `reading` row passes reason 5" (the row's own Answer holds "default": a reading row is
    # what such an answer is re-statused to).
    reg = _rows(_row("Q-990-03", "reading (Westley to confirm)", "(a), the default."))
    spec, res, found = _run_text(tmp_path, "# Test spec\n\nThe tile shows 5 wu. [W Q-990-03]\n", register=reg)
    assert res.returncode == 0 and res.stdout.strip() == "", res.stdout + res.stderr


def test_reason5_seven_cell_row_is_malformed(tmp_path):
    # "a row whose cells cannot be split into six is finding `register row Q-x is malformed` under reason 5"
    # (a seven-cell row whose status cell still reads closed: the cells are what is wrong).
    bad = "| Q-990-06 | E-99 | A question? | (a) yes | closed | (a) | stray |\n"
    spec, res, found = _run_text(tmp_path, "# Test spec\n\nThe tile shows 5 wu. [W Q-990-06]\n",
                                 register=_rows(bad))
    assert "(5)" in res.stdout, "register row is never reported malformed\n" + res.stdout + res.stderr
    assert res.returncode == 1, res.stdout + res.stderr
    assert any(l.startswith(f"{spec}:3: (5)") and "register row Q-990-06 is malformed" in l for _, _, l in found), \
        res.stdout


# ---- method rev 3, HARNESS-mm-5 (spec G03): reason 9 becomes a WARN
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md G03 "Fix" ("the provenance lint's reason 9 becomes WARN")
# Interface fixed here: a reason-9 finding is still printed as `<spec>:<line>: (9) <text>`, but a spec whose only
# findings are reason 9 exits 0 and prints a line `PROVENANCE WARN <spec> reason9=<n>`; any other reason still exits 1.
# The reason-9 cases above that asserted exit 1 for a reason-9-only spec are changed to exit 0 (superseded ruling).
def test_mm5_reason9_only_spec_exits_0_with_a_warn_line(tmp_path):
    spec, res, found = _run_text(tmp_path, _w(NEVER))
    assert any(l.startswith(f"{spec}:3: (9)") for _, _, l in found), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr
    assert any(l.startswith("PROVENANCE WARN") and "reason9=1" in l for l in res.stdout.splitlines()), res.stdout


def test_mm5_reason9_next_to_another_reason_still_exits_1(tmp_path):
    text = _w(NEVER) + "\nThe tile shows 5 wu of rubble.\n"  # an untagged behaviour paragraph: reason 1
    spec, res, found = _run_text(tmp_path, text)
    assert any(n == 1 for _, n, _ in found) and any(n == 9 for _, n, _ in found), res.stdout
    assert res.returncode == 1, res.stdout + res.stderr
