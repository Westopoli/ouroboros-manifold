# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md paragraph HARNESS-provenance-scope (lane H; Tool: Workflow)
#       and the Architect derivation brief of 2026-10-21 (items 1 to 3); piece HARNESS-provenance-scope, tests first
# Rule pins: none (tooling piece, Architect derivation brief 2026-10-21)
"""Tests for the --pieces scope and the cited-number rule of scripts/specfactory/spec_provenance.py.

The four test sentences of the brief, word for word (method rev 3):
  1. (spec paragraph) "Tests first: a spec with one clean and one dirty paragraph under their own piece ids and a
     third paragraph of another piece, `--pieces` of the clean id passes and of the dirty id rejects; positive
     control: today's whole-file mode rejects on the dirty and the third paragraph."
  2. (spec paragraph) "The cite rule (reason 10): a number is not a finding when a `[P file:line]` tag appears
     anywhere in the same unit (the lint's unit: a heading, a list item with its continuation lines, or a
     blank-separated paragraph) as the number, before or after it; a `[P ...]` tag with no `file:line` does not
     count, a tag in another unit does not count, and reasons 3, 8 and 9 are unchanged."
  3. (brief item 3) "Tests first: a fixture spec with one clean and one dirty paragraph: the clean id passes, the
     dirty id rejects; positive control: today's whole-file mode rejects both."
  4. (brief item 2) "One lint rule, stated in its paragraph: a number followed by a `[P file:line]` cite within the
     same sentence is cited, not a draft" (widened by ruling R2 and the paragraph to the same unit, before or
     after: the paragraph wins).

Other sentences proved here (each case names its sentence): "`spec_provenance.py <spec.md> --pieces ID[,ID...]`
computes every reason over the whole file as today and prints only the findings whose line lies inside a paragraph
that names one of the listed ids"; "without `--pieces` the output is byte for byte today's, and `--pieces \"\"` is an
empty list, not a usage error"; [DRAFT-provscope-forms] "A paragraph names an id when its opening is the bold token
`**ID` followed by a space, a comma or an open parenthesis, or a list item whose opening is `- ID` or ``- `ID` ``";
"a paragraph matched by two ids counts once"; "With `--pieces` the lint prints, after the findings, one line
`PROVSCOPE <path> pieces=<ids> paragraphs=<k> in-scope=<n> whole-file=<N>`"; [DRAFT-provscope-nomatch] "when no
listed id names a paragraph the whole file is checked as today, every finding is printed and no WARN line is
printed; when at least one id matched, each listed id that names no paragraph gets one line `PROVSCOPE WARN <path>
id=<id> opens no paragraph`, and a WARN line never changes the exit code"; "`pre_gate.sh` passes its piece list as
`--pieces` to every spec it lints, so ids that belong to another spec print WARN lines and never reject"; "A plain
`- ID` list item takes the bold form's follower set (space, comma, open parenthesis) plus end of line; the
backticked ``- `ID` `` form is closed by its backtick."

UNSTATED INTERFACES assumed (reported):
  - The usage text: the paragraph says a usage error, stderr, exit 2 (IFACE item 2); only "usage" and the word
    "--pieces" are asserted in stderr (the base usage line is `usage: spec_provenance.py <spec.md>`).
  - The finding line is reported at the unit's first line (the lint's rule, docstring "reported at its first line"),
    so a bare `- ID` line followed by a continuation line reports at the BARE line, not the continuation line the
    brief's case T7 words; the range of that paragraph covers both lines, and the test asserts the bare line.
  - Whether the `pieces=` field of the PROVSCOPE line shows a repeated id once is not stated; no test asserts the
    field for a repeated id (an empty token is dropped, IFACE item 2, and is asserted).
  - The PROVSCOPE line goes to stdout after the finding lines and the WARN lines after it (IFACE item 5).
  - Whether a list-item line directly under a bold paragraph's opening line opens its own paragraph is not stated;
    only the printed finding (once) is asserted there.
  - The wording of the reason (10) cite sentence in the module docstring is not stated; the test asserts only that
    the docstring text for reason (10) mentions a `[P` tag, and that --pieces, PROVSCOPE and WARN appear.

Isolation: each case builds a tree in tmp_path with _tree of test_spec_provenance.py (closed register row Q-990-01,
rule R-990-01) and runs the lint by subprocess. On the base tree (no feature) every --pieces case exits 2 with the
one-argument usage line.
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_spec_provenance import (REGISTER_TEXT, SCRIPT, _findings, _line_of, _tree)  # noqa: E402
from test_pre_gate import (EPICS, _make_repo, _pieces, _run, _stub_gate)  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
PRE_GATE = REPO / "scripts" / "specfactory" / "pre_gate.sh"

DIRTY_P = "**VG-X-dirty (lane X; Tool: Workflow).** The tile shows 5 wu of rubble when asked."
CLEAN_P = '**VG-X-clean (lane X; Tool: Workflow).** The tile shows 5 wu of rubble when asked. [W Q-990-01]'
OTHER_P = "**VG-X-other (lane X; Tool: Workflow).** The lot draws 7 rows when asked."
FIXTURE_TEXT = f"# Test spec\n\n{CLEAN_P}\n\n{DIRTY_P}\n\n{OTHER_P}\n"
CLEAN_ONLY_TEXT = f"# Test spec\n\n{CLEAN_P}\n"


def _go(tmp_path, text, *args, pieces=None):
    """Write the tree, run the lint; pieces=None is one-argument mode, else `--pieces <pieces>` (a string)."""
    spec = tmp_path / "tree" / "spec.md"
    if spec.is_file():                           # a second run in the same test reuses the tree
        spec.write_text(text)
    else:
        spec = _tree(tmp_path, text)
    cmd = [sys.executable, str(SCRIPT), str(spec), *args]
    if pieces is not None:
        cmd += ["--pieces", pieces]
    res = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    return spec, res, _findings(res)


def _provscope(res):
    """The PROVSCOPE information lines (not WARN) on stdout."""
    return [l for l in res.stdout.splitlines() if l.startswith("PROVSCOPE ") and not l.startswith("PROVSCOPE WARN")]


def _prov0(res):
    """The first PROVSCOPE line, or the whole stderr when there is none (a red reads the usage line)."""
    return (_provscope(res) or ["NO PROVSCOPE LINE: " + res.stderr])[0]


def _warns(res):
    return [l for l in res.stdout.splitlines() if l.startswith("PROVSCOPE WARN")]


def _expect_line(spec, ids, k, n, total):
    return f"PROVSCOPE {spec} pieces={ids} paragraphs={k} in-scope={n} whole-file={total}"


DIRTY_LINE = _line_of(FIXTURE_TEXT, "VG-X-dirty")
OTHER_LINE = _line_of(FIXTURE_TEXT, "VG-X-other")
CLEAN_LINE = _line_of(FIXTURE_TEXT, "VG-X-clean")


# ---- T11: positive controls, green on the base tree --------------------------------------------------------------

def test_control_fixture_line_numbers():
    assert (CLEAN_LINE, DIRTY_LINE, OTHER_LINE) == (3, 5, 7)


def test_control_whole_file_mode_rejects_the_dirty_and_the_other_paragraph_byte_for_byte(tmp_path):
    """T11 / spec paragraph: 'without --pieces the output is byte for byte today's'; today's mode prints exactly two
    reason-1 findings (dirty and other), no PROVSCOPE line."""
    spec, res, found = _go(tmp_path, FIXTURE_TEXT)
    assert res.returncode == 1, res.stdout + res.stderr
    expected = (f"{spec}:{DIRTY_LINE}: (1) behaviour unit without a provenance tag: {DIRTY_P[:70]}\n"
                f"{spec}:{OTHER_LINE}: (1) behaviour unit without a provenance tag: {OTHER_P[:70]}\n")
    assert res.stdout == expected, res.stdout
    assert "PROVSCOPE" not in res.stdout


def test_control_clean_paragraph_alone_passes_with_empty_stdout(tmp_path):
    """T11: the detector is not always-failing."""
    spec, res, found = _go(tmp_path, CLEAN_ONLY_TEXT)
    assert res.returncode == 0 and res.stdout == "", res.stdout + res.stderr


def test_control_existing_reason10_case_has_no_cite(tmp_path):
    """T11: `[W Q-990-01: "soon"] the delay is 3 s` still gives (10) when there is no cite anywhere."""
    spec, res, found = _go(tmp_path, '# Test spec\n\n[W Q-990-01: "soon"] the delay is 3 s\n')
    assert res.returncode == 1 and [(l, r) for l, r, _ in found] == [(3, 10)], res.stdout + res.stderr
    assert "number 3 after a quote with no DRAFT in its sentence" in found[0][2]


def test_control_names_that_rule_pins_import_stay():
    """IFACE item 1: nothing is renamed or removed (rule_pins.py and rule_pins_tests.py import spec_provenance as sp)."""
    sys.path.insert(0, str(SCRIPT.parent))
    import spec_provenance as sp
    for name in ("find_root", "load_context", "rule_pin", "PIN_RE", "B_TAG", "split_units", "REASONS", "main"):
        assert hasattr(sp, name), name


# ---- T1 to T5b: the scope --------------------------------------------------------------------------------------

def test_t1_the_clean_id_passes(tmp_path):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-clean")
    assert res.returncode == 0, res.stdout + res.stderr
    assert found == []
    assert res.stdout.splitlines() == [_expect_line(spec, "VG-X-clean", 1, 0, 2)], res.stdout + res.stderr


def test_t2_the_dirty_id_rejects_at_its_own_line(tmp_path):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-dirty")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(DIRTY_LINE, 1)], res.stdout + res.stderr
    assert res.stdout.splitlines() == [
        f"{spec}:{DIRTY_LINE}: (1) behaviour unit without a provenance tag: {DIRTY_P[:70]}",
        _expect_line(spec, "VG-X-dirty", 1, 1, 2)], res.stdout


def test_t3_both_ids_one_finding_two_paragraphs(tmp_path):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-clean,VG-X-dirty")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(DIRTY_LINE, 1)]
    assert _provscope(res) == [_expect_line(spec, "VG-X-clean,VG-X-dirty", 2, 1, 2)], res.stdout


@pytest.mark.parametrize("ident", ["VG-X-clean", "VG-X-dirty"])
def test_t4_the_whole_file_count_is_information_the_other_finding_is_never_printed(tmp_path, ident):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces=ident)
    assert OTHER_LINE not in [l for l, _, _ in found], res.stdout + res.stderr
    assert "VG-X-other" not in res.stdout
    assert "whole-file=2" in _prov0(res), res.stdout + res.stderr


def test_t5_no_listed_id_names_a_paragraph_the_whole_file_is_checked_and_no_warn(tmp_path):
    """[DRAFT-provscope-nomatch]: whole file, every finding printed, paragraphs=0, no WARN line."""
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-nothing")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(DIRTY_LINE, 1), (OTHER_LINE, 1)], res.stdout + res.stderr
    assert _provscope(res) == [_expect_line(spec, "VG-X-nothing", 0, 2, 2)], res.stdout
    assert _warns(res) == [] and "WARN" not in res.stdout


def test_t5b_warn_line_for_each_listed_id_that_opens_no_paragraph(tmp_path):
    """[DRAFT-provscope-nomatch] with at least one id matched: one WARN per unmatched id (a repeated id once), after
    the PROVSCOPE line; the exit code is the findings' (dirty matched, so 1)."""
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-clean,VG-X-ghost,VG-X-dirty,VG-X-ghost")
    assert res.returncode == 1, res.stdout + res.stderr
    lines = res.stdout.splitlines()
    assert [(l, r) for l, r, _ in found] == [(DIRTY_LINE, 1)]
    prov = [i for i, l in enumerate(lines) if l.startswith("PROVSCOPE ") and not l.startswith("PROVSCOPE WARN")]
    assert len(prov) == 1 and re.search(r" paragraphs=2 in-scope=1 whole-file=2$", lines[prov[0]]), res.stdout
    assert lines[prov[0] + 1:] == [f"PROVSCOPE WARN {spec} id=VG-X-ghost opens no paragraph"], res.stdout


def test_t5b_a_warn_never_changes_the_exit_code(tmp_path):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-clean,VG-X-ghost")
    assert res.returncode == 0, res.stdout + res.stderr
    assert found == []
    assert res.stdout.splitlines() == [_expect_line(spec, "VG-X-clean,VG-X-ghost", 1, 0, 2),
                                       f"PROVSCOPE WARN {spec} id=VG-X-ghost opens no paragraph"], res.stdout


def test_t5b_warn_lines_follow_the_order_the_ids_were_given(tmp_path):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-g2,VG-X-clean,VG-X-g1")
    assert res.returncode == 0, res.stdout + res.stderr
    assert _warns(res) == [f"PROVSCOPE WARN {spec} id=VG-X-g2 opens no paragraph",
                           f"PROVSCOPE WARN {spec} id=VG-X-g1 opens no paragraph"], res.stdout


def test_output_is_the_same_on_a_second_run(tmp_path):
    """No clock, hash order or other path in any line (IFACE item 5)."""
    a = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-g2,VG-X-clean,VG-X-dirty,VG-X-g1")[1]
    spec = tmp_path / "tree" / "spec.md"
    b = subprocess.run([sys.executable, str(SCRIPT), str(spec), "--pieces", "VG-X-g2,VG-X-clean,VG-X-dirty,VG-X-g1"],
                       cwd=REPO, capture_output=True, text=True)
    assert a.returncode == 1 and a.stdout == b.stdout and a.stdout.count("PROVSCOPE") == 3, a.stdout + a.stderr


# ---- T14: the empty list ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["", ",,"])
def test_t14_empty_list_is_whole_file_mode_not_a_usage_error(tmp_path, value):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces=value)
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(DIRTY_LINE, 1), (OTHER_LINE, 1)]
    assert _provscope(res) == [_expect_line(spec, "", 0, 2, 2)], res.stdout
    assert _warns(res) == []


def test_t14_empty_list_on_the_clean_only_fixture_passes(tmp_path):
    spec, res, found = _go(tmp_path, CLEAN_ONLY_TEXT, pieces="")
    assert res.returncode == 0, res.stdout + res.stderr
    assert res.stdout.splitlines() == [_expect_line(spec, "", 0, 0, 0)], res.stdout


def test_an_empty_token_in_the_list_is_dropped(tmp_path):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-clean,,VG-X-dirty")
    assert res.returncode == 1 and [(l, r) for l, r, _ in found] == [(DIRTY_LINE, 1)], res.stdout + res.stderr
    assert _provscope(res) == [_expect_line(spec, "VG-X-clean,VG-X-dirty", 2, 1, 2)], res.stdout


def test_a_repeated_matching_id_counts_one_paragraph(tmp_path):
    spec, res, found = _go(tmp_path, FIXTURE_TEXT, pieces="VG-X-dirty,VG-X-dirty")
    assert res.returncode == 1 and [(l, r) for l, r, _ in found] == [(DIRTY_LINE, 1)], res.stdout + res.stderr
    assert re.search(r" paragraphs=1 in-scope=1 whole-file=2$", _prov0(res)), res.stdout


# ---- T6: the cited-number rule, both modes ----------------------------------------------------------------------

MODES = [pytest.param(None, id="one-arg"), pytest.param("VG-X-nothing", id="pieces-opens-nothing")]
W = '[W Q-990-01: "soon"]'


def _cite_run(tmp_path, body, mode):
    spec, res, found = _go(tmp_path, f"# Test spec\n\n{body}\n", pieces=mode)
    return spec, res, found


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("body", [
    f"{W} the delay is 3 s [P csrc/x.c:12]",
    f"{W} the delay is 3 s. See [P csrc/x.c:12]",
    f"see [P csrc/x.c:12] {W} the delay is 3 s",
], ids=["cite-after-in-sentence", "cite-in-another-sentence", "cite-before-in-the-opening-tag-run"])
def test_t6_a_cite_anywhere_in_the_unit_clears_reason10(tmp_path, body, mode):
    spec, res, found = _cite_run(tmp_path, body, mode)
    assert res.returncode == 0, res.stdout + res.stderr
    assert found == [], res.stdout


@pytest.mark.parametrize("mode", MODES)
def test_t6_a_p_tag_with_no_line_does_not_count(tmp_path, mode):
    spec, res, found = _cite_run(tmp_path, f"{W} the delay is 3 s [P csrc/x.c]", mode)
    assert res.returncode == 1, res.stdout + res.stderr
    assert sorted((l, r) for l, r, _ in found) == [(3, 3), (3, 10)], res.stdout
    assert any("(10) number 3 " in l for _, _, l in found), res.stdout


@pytest.mark.parametrize("mode", MODES)
def test_t6_a_cite_in_the_next_blank_separated_paragraph_does_not_count(tmp_path, mode):
    spec, res, found = _cite_run(tmp_path, f"{W} the delay is 3 s.\n\nSee [P csrc/x.c:12].", mode)
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(3, 10)], res.stdout
    assert "number 3 " in found[0][2]


@pytest.mark.parametrize("mode", MODES)
def test_t6_a_cite_in_the_next_list_item_does_not_count(tmp_path, mode):
    spec, res, found = _cite_run(tmp_path, f"- {W} the delay is 3 s.\n- See [P csrc/x.c:12].", mode)
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(3, 10)], res.stdout
    assert "number 3 " in found[0][2]


@pytest.mark.parametrize("mode", MODES)
def test_t6_a_cite_in_a_heading_does_not_count(tmp_path, mode):
    spec, res, found = _cite_run(tmp_path, f"{W} the delay is 3 s.\n## See [P csrc/x.c:12]", mode)
    assert [(l, r) for l, r, _ in found] == [(3, 10)], res.stdout + res.stderr


@pytest.mark.parametrize("mode", MODES)
def test_t6_a_cite_does_not_clear_reason_9(tmp_path, mode):
    spec, res, found = _cite_run(tmp_path, '[W Q-990-01: "the delay is never 3 s"] see [P csrc/x.c:12]', mode)
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(3, 9)], res.stdout


@pytest.mark.parametrize("mode", MODES)
def test_t6_a_cite_does_not_clear_reason_8(tmp_path, mode):
    spec, res, found = _cite_run(tmp_path, "The lot draws 7 rows. [B R-990-01] [P csrc/x.c:12]", mode)
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(3, 8)], res.stdout


# ---- T7: the list-item openings ----------------------------------------------------------------------------------

LIST_TEXT = (
    "# Test spec\n\n"
    "- `VG-X-item`: The tile shows 5 wu of rubble when asked.\n"
    "- `VG-X-next`: The tile shows 5 wu of rubble when asked. [W Q-990-01]\n"
    "- VG-X-plain (note): The tile shows 5 wu of rubble when asked.\n"
    "- VG-X-bare\n"
    "  The tile shows 5 wu of rubble when asked.\n"
    "- see VG-X-item for the rubble\n")
ITEM_LINE, NEXT_LINE, PLAIN_LINE, BARE_LINE = (_line_of(LIST_TEXT, "`VG-X-item`"), _line_of(LIST_TEXT, "`VG-X-next`"),
                                              _line_of(LIST_TEXT, "VG-X-plain"), _line_of(LIST_TEXT, "- VG-X-bare"))


def test_t7_fixture_whole_file_has_three_reason1_findings(tmp_path):
    """Control (green on base): item, plain and bare are untagged; next carries a [W] tag; the mention bullet is clean."""
    spec, res, found = _go(tmp_path, LIST_TEXT)
    assert [(l, r) for l, r, _ in found] == [(ITEM_LINE, 1), (PLAIN_LINE, 1), (BARE_LINE, 1)], res.stdout + res.stderr


def test_t7_backticked_item_rejects_at_its_own_line_and_the_mention_bullet_opens_nothing(tmp_path):
    spec, res, found = _go(tmp_path, LIST_TEXT, pieces="VG-X-item")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(ITEM_LINE, 1)], res.stdout
    assert _provscope(res) == [_expect_line(spec, "VG-X-item", 1, 1, 3)], res.stdout


def test_t7_next_item_passes_its_range_ends_at_the_next_list_item(tmp_path):
    spec, res, found = _go(tmp_path, LIST_TEXT, pieces="VG-X-next")
    assert res.returncode == 0, res.stdout + res.stderr
    assert found == [] and _provscope(res) == [_expect_line(spec, "VG-X-next", 1, 0, 3)], res.stdout


def test_t7_plain_item_with_open_parenthesis_follower_rejects_at_its_own_line(tmp_path):
    spec, res, found = _go(tmp_path, LIST_TEXT, pieces="VG-X-plain")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(PLAIN_LINE, 1)], res.stdout
    assert _provscope(res) == [_expect_line(spec, "VG-X-plain", 1, 1, 3)], res.stdout


def test_t7_bare_plain_item_end_of_line_is_a_follower(tmp_path):
    """The bare `- VG-X-bare` line opens a paragraph (end of line is a follower). The unit's finding is reported at
    its first line, the bare line (UNSTATED INTERFACES: the brief words 'at the continuation line'); the paragraph
    runs over the continuation line and stops before the mention bullet."""
    spec, res, found = _go(tmp_path, LIST_TEXT, pieces="VG-X-bare")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(BARE_LINE, 1)], res.stdout
    assert _provscope(res) == [_expect_line(spec, "VG-X-bare", 1, 1, 3)], res.stdout


EXTRA_LIST = (
    "# Test spec\n\n"
    "- VG-X-colon: The tile shows 5 wu of rubble when asked.\n"
    "- `VG-X-itemize`: The tile shows 5 wu of rubble when asked.\n"
    "  - VG-X-nest, with a comma follower: The lot draws 7 rows when asked.\n")


def test_t7_a_plain_item_followed_by_a_colon_opens_nothing(tmp_path):
    spec, res, found = _go(tmp_path, EXTRA_LIST, pieces="VG-X-colon")
    assert _provscope(res) == [_expect_line(spec, "VG-X-colon", 0, 3, 3)], res.stdout + res.stderr
    assert _warns(res) == []


def test_t7_the_backtick_form_is_closed_by_its_backtick(tmp_path):
    """`- `VG-X-itemize`` opens for VG-X-itemize only; its prefix VG-X-item opens nothing."""
    spec, res, found = _go(tmp_path, EXTRA_LIST, pieces="VG-X-item")
    assert _provscope(res) == [_expect_line(spec, "VG-X-item", 0, 3, 3)], res.stdout + res.stderr
    spec, res, found = _go(tmp_path, EXTRA_LIST, pieces="VG-X-itemize")
    line = _line_of(EXTRA_LIST, "VG-X-itemize")
    assert [(l, r) for l, r, _ in found] == [(line, 1)], res.stdout + res.stderr


def test_t7_an_indented_item_with_a_comma_follower_opens_a_paragraph(tmp_path):
    """IFACE item 3: a list item may be indented; the comma is a follower of the plain form."""
    spec, res, found = _go(tmp_path, EXTRA_LIST, pieces="VG-X-nest")
    assert [(l, r) for l, r, _ in found] == [(_line_of(EXTRA_LIST, "VG-X-nest"), 1)], res.stdout + res.stderr
    assert re.search(r" paragraphs=1 in-scope=1 whole-file=3$", _prov0(res)), res.stdout


# ---- T8: the bold opening is exactly the paragraph's rule ---------------------------------------------------------

BOLD_TEXT = (
    "# Test spec\n\n"
    "**VG-X-dirty (lane X; Tool: Workflow).** The tile shows 5 wu of rubble when asked.\n\n"
    "**VG-X-dirty-more (lane X).** The lot draws 7 rows when asked.\n\n"
    "**VG-X-two, VG-X-three (lane X).** The lot draws 8 cells when asked.\n\n"
    "**VG-X-dot.** The lot draws 9 cells when asked.\n\n"
    "**VG-X-host (lane X).** VG-X-after names a thing: the lot draws 4 cells when asked, see VG-X-body.\n\n"
    "Note **VG-X-pre (lane X).** The lot draws 6 cells when asked.\n")
B_DIRTY, B_MORE, B_TWO, B_DOT, B_HOST, B_PRE = (_line_of(BOLD_TEXT, k) for k in (
    "**VG-X-dirty (", "**VG-X-dirty-more", "**VG-X-two", "**VG-X-dot", "**VG-X-host", "Note **VG-X-pre"))


def test_t8_fixture_whole_file_rejects_every_paragraph(tmp_path):
    """Control (green on base): six untagged behaviour paragraphs, six findings."""
    spec, res, found = _go(tmp_path, BOLD_TEXT)
    assert [(l, r) for l, r, _ in found] == [(x, 1) for x in (B_DIRTY, B_MORE, B_TWO, B_DOT, B_HOST, B_PRE)], res.stdout


@pytest.mark.parametrize("ident,line", [("VG-X-dirty", B_DIRTY), ("VG-X-dirty-more", B_MORE), ("VG-X-two", B_TWO)])
def test_t8_an_id_followed_by_a_space_comma_or_open_parenthesis_names_exactly_one_paragraph(tmp_path, ident, line):
    spec, res, found = _go(tmp_path, BOLD_TEXT, pieces=ident)
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(line, 1)], res.stdout
    assert _provscope(res) == [_expect_line(spec, ident, 1, 1, 6)], res.stdout


@pytest.mark.parametrize("ident", ["VG-X-dir", "VG-X-three", "VG-X-dot", "VG-X-after", "VG-X-body", "VG-X-pre"])
def test_t8_prefix_second_id_full_stop_closing_bold_body_and_text_before_open_nothing(tmp_path, ident):
    """VG-X-dir: a prefix; VG-X-three: a second id inside a bold opening is a mention (the negative control of the
    widening of the first draft); VG-X-dot: a full stop follows; VG-X-after / VG-X-body: after the closing ** or in
    the body; VG-X-pre: text before the **. paragraphs=0 means the whole file is checked, no WARN."""
    spec, res, found = _go(tmp_path, BOLD_TEXT, pieces=ident)
    assert res.returncode == 1, res.stdout + res.stderr
    assert len(found) == 6, res.stdout
    assert _provscope(res) == [_expect_line(spec, ident, 0, 6, 6)], res.stdout
    assert _warns(res) == []


# ---- T9: the range -----------------------------------------------------------------------------------------------

RANGE_TEXT = (
    "# Test spec\n\n"
    "**VG-X-span (lane X).** A block of two lines.\n"
    "- The tile shows 5 wu of rubble when asked.\n\n"
    "**VG-X-after (lane X).** The lot draws 7 rows when asked.\n\n"
    "**VG-X-head (lane X).** A block of one line.\n"
    "## Next heading\n"
    "The lot draws 8 cells when asked.\n")


def test_t9_a_two_line_paragraph_reports_on_the_second_line_and_the_next_paragraph_is_outside(tmp_path):
    spec, res, found = _go(tmp_path, RANGE_TEXT, pieces="VG-X-span")
    second, after = _line_of(RANGE_TEXT, "- The tile shows"), _line_of(RANGE_TEXT, "**VG-X-after")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(second, 1)], res.stdout
    assert re.search(r" paragraphs=1 in-scope=1 whole-file=3$", _prov0(res)), res.stdout
    spec, res, found = _go(tmp_path, RANGE_TEXT, pieces="VG-X-after")
    assert [(l, r) for l, r, _ in found] == [(after, 1)], res.stdout + res.stderr


def test_t9_a_heading_line_ends_the_paragraph(tmp_path):
    spec, res, found = _go(tmp_path, RANGE_TEXT, pieces="VG-X-head")
    assert res.returncode == 0 and found == [], res.stdout + res.stderr
    assert _provscope(res) == [_expect_line(spec, "VG-X-head", 1, 0, 3)], res.stdout


FENCE_TEXT = (
    "# Test spec\n\n"
    "**VG-X-fence (lane X).** A block with a fence.\n"
    "```text\n"
    "first\n"
    "\n"
    "second\n"
    "```\n"
    "The lot draws 7 rows when asked.\n\n"
    "The tile shows 5 wu of rubble when asked.\n")


def test_t9_a_blank_line_inside_a_fence_does_not_end_the_paragraph(tmp_path):
    spec, res, found = _go(tmp_path, FENCE_TEXT, pieces="VG-X-fence")
    inside, outside = _line_of(FENCE_TEXT, "The lot draws"), _line_of(FENCE_TEXT, "The tile shows")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(inside, 1)], res.stdout
    assert outside > inside and re.search(r" paragraphs=1 in-scope=1 whole-file=2$", _prov0(res)), res.stdout


def test_t9_a_finding_inside_two_overlapping_paragraphs_is_printed_once(tmp_path):
    text = ("# Test spec\n\n**VG-X-top (lane X).** A block.\n"
            "- VG-X-sub (note): The tile shows 5 wu of rubble when asked.\n")
    spec, res, found = _go(tmp_path, text, pieces="VG-X-top,VG-X-sub")
    assert res.returncode == 1, res.stdout + res.stderr
    assert [(l, r) for l, r, _ in found] == [(4, 1)], res.stdout


# ---- T10: usage --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("extra", [["--pieces"], ["--bogus"], ["SECOND"], ["--pieces", "A", "--pieces", "B"]],
                         ids=["missing-value", "unknown-option", "two-spec-arguments", "second-pieces"])
def test_t10_usage_errors_exit_2_with_a_usage_line_naming_pieces(tmp_path, extra):
    spec = _tree(tmp_path, FIXTURE_TEXT)
    args = [str(spec) if a == "SECOND" else a for a in extra]
    res = subprocess.run([sys.executable, str(SCRIPT), str(spec), *args], cwd=REPO, capture_output=True, text=True)
    assert res.returncode == 2, res.stdout + res.stderr
    assert "usage" in res.stderr.lower() and "--pieces" in res.stderr, res.stderr
    assert res.stdout == ""


# ---- source and docstring (IFACE items 2, 6, 7) -----------------------------------------------------------------------

def test_module_docstring_gains_the_option_the_lines_and_the_cite_rule():
    doc = ast.get_docstring(ast.parse(SCRIPT.read_text()))
    assert "--pieces" in doc and "PROVSCOPE" in doc and "WARN" in doc, doc
    reason10 = doc[doc.index("(10)"):doc.index("(11)")]
    assert "[P" in reason10, reason10


def test_source_names_the_two_drafts_in_comments():
    src = SCRIPT.read_text()
    assert "DRAFT-provscope-forms" in src and "DRAFT-provscope-nomatch" in src


def test_pre_gate_passes_its_piece_list_as_pieces():
    src = PRE_GATE.read_text()
    assert '"$VENV_PYTHON" "$HERE/spec_provenance.py" "$WT/$spec" --pieces "$PIECES"' in src


# ---- T12: through pre_gate.sh ----------------------------------------------------------------------------------------

def _pre_gate(tmp_path, pieces, env_extra=None, ids=("VG-X-clean", "VG-X-dirty", "VG-X-ghost")):
    repo = _make_repo(tmp_path, base_files={"readme.txt": "base\n", **EPICS}, head_add={"spec.md": FIXTURE_TEXT})
    specs = {i: "spec.md" for i in ids if i != "VG-X-ghost"}
    toml = _pieces(tmp_path, list(ids), specs=specs)
    env = {"MERGE_GATE_PIECES": str(toml), "PRE_GATE_SPEC": ""}
    env.update(env_extra or {})
    res = _run(repo, _stub_gate(tmp_path, "GATE make OK", 0), pieces=pieces, env_extra=env)
    return repo, res, res.stdout.splitlines()


def test_t12_clean_id_passes_pre_gate_provenance(tmp_path):
    repo, res, out = _pre_gate(tmp_path, "VG-X-clean")
    assert "PRE_GATE provenance OK spec.md" in out, res.stdout + res.stderr
    assert out[-1] == "PRE_GATE verdict OK" and res.returncode == 0, res.stdout + res.stderr


def test_t12_dirty_id_rejects_pre_gate_provenance_at_its_own_paragraph_only(tmp_path):
    repo, res, out = _pre_gate(tmp_path, "VG-X-dirty")
    assert "PRE_GATE provenance REJECT spec.md" in out, res.stdout + res.stderr
    assert any(re.search(rf"spec\.md:{DIRTY_LINE}: \(1\)", l) for l in out), res.stdout
    assert not any(re.search(rf"spec\.md:{OTHER_LINE}: \(1\)", l) for l in out), res.stdout
    assert out[-1] == "PRE_GATE verdict REJECT" and res.returncode == 1, res.stdout + res.stderr


def test_t12_a_listed_id_of_another_spec_prints_a_warn_and_the_verdict_stays_ok(tmp_path):
    """The row VG-X-ghost has no spec key: its own 'no spec key' WARN is expected too."""
    repo, res, out = _pre_gate(tmp_path, "VG-X-clean,VG-X-ghost")
    assert any(l.startswith("PROVSCOPE WARN ") and l.endswith("id=VG-X-ghost opens no paragraph") for l in out), res.stdout
    assert "PRE_GATE provenance WARN no spec key for VG-X-ghost" in out
    assert "PRE_GATE provenance OK spec.md" in out
    assert out[-1] == "PRE_GATE verdict OK" and res.returncode == 0, res.stdout + res.stderr


def test_t12_control_the_extra_spec_path_with_no_matching_id_is_checked_whole_file(tmp_path):
    """Green today and after: PRE_GATE_SPEC=spec.md, piece list P-1 (no id opens a paragraph) rejects whole-file."""
    repo, res, out = _pre_gate(tmp_path, "P-1", env_extra={"PRE_GATE_SPEC": "spec.md"}, ids=("P-1",))
    assert "PRE_GATE provenance REJECT spec.md" in out, res.stdout + res.stderr
    for n in (DIRTY_LINE, OTHER_LINE):
        assert any(re.search(rf"spec\.md:{n}: \(1\)", l) for l in out), res.stdout
    assert out[-1] == "PRE_GATE verdict REJECT" and res.returncode == 1
