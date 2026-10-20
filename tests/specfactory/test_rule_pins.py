# spec: docs/northstar/plans/2026-10-19-harness-enforcement-spec.md section 1 "HARNESS-C1a" (rev 3a), sections 3 and 4
# Rule pins: R-990-01@?, R-990-02@?, R-990-09@?, R-991-01@?
"""Tests for scripts/specfactory/rule_pins.py (piece HARNESS-C1a, test writer pass; the tool is C1a's, new).

Spec sentences proved (HARNESS-C1a paragraph, rev 3a):
  "`rule_pins.py pin R-###-## [R-...]` prints `R-###-##@xxxxxx` per id; an id with no rule line prints
  `R-###-##@?` and exit 2 at the end."
  "`rule_pins.py unwrap <md>...` (explicit paths only; no glob, no directory) rewrites each file in place: a
  backtick span that is exactly one tag ... loses its backticks, unless the span is a documentation
  placeholder ... (a quoted Westley text is never a placeholder; then `SKIP <file>:<line> placeholder`) ...
  any other span and everything inside a fenced block is untouched; prints `UNWRAP <file> <n> tags`."
  "`rule_pins.py rewrite <md>...` adds or refreshes `@pin` on every id of every bare `[B ...]` tag, in place,
  idempotent; prints `REPIN <file> <n> added <m> refreshed`; a tag inside backticks is reported
  `SKIP <file>:<line> tag in backticks` and left."
  "`rule_pins.py check <md>... [--only <file>...]` is `rewrite` without writing: prints one
  `PINS REJECT <file>:<line> <id> missing|stale <old> <new>` per finding and `PINS OK <files> files <ids> ids`
  when none; `--only` restricts the findings to the named files and reports the rest as
  `PINS WARN <n> stale outside the diff`; exit 1 only on a REJECT."
  "`rule_pins.py spec-of <pieces.toml> <id>[,<id>...]` prints the `spec =` path of each row ..., one per
  line (a row without the key prints `-`)."
  Pin (section 3): sha256(" ".join(rule_line_after_id.split()).encode("utf-8")).hexdigest()[:6]
  (DRAFT-pin-hex 6).

Fixture tree: the one of test_spec_provenance.py:34-60 (rule R-990-01 in docs/bible/epics/E-99-test.md), imported
from that file. UNSTATED INTERFACE (reported to the Architect): where `pin` finds the epics. These tests run
every sub-command with cwd = the fixture tree root, and `rewrite`/`check` also name files inside that tree.

Red reason on the built tree: scripts/specfactory/rule_pins.py does not exist. A raw subprocess of the script
path reports FileNotFoundError (direct exec) or exit 2 "can't open file" (python script.py); _tool raises the
FileNotFoundError itself so every case is red for that one reason.
"""
import hashlib
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_spec_provenance import EPIC_TEXT, _lint, _tree  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "rule_pins.py"

RULE_AFTER_ID = "  Given a town, When it grows, Then it never form rings around the core."
PIN_LITERAL = "b2a3c8"  # computed once with the section 3 formula on the fixture rule line
OTHER_PIN = "000000"


def _pin(text_after_id: str) -> str:
    return hashlib.sha256(" ".join(text_after_id.split()).encode("utf-8")).hexdigest()[:6]


def _tool(root: Path, *args) -> subprocess.CompletedProcess:
    if not SCRIPT.is_file():
        raise FileNotFoundError(f"[Errno 2] No such file or directory: '{SCRIPT}' (rule_pins.py is not built)")
    return subprocess.run([sys.executable, str(SCRIPT), *[str(a) for a in args]], cwd=root,
                          capture_output=True, text=True)


def _root(tmp_path: Path) -> Path:
    """The fixture tree of test_spec_provenance.py (epic, register, ledger); returns its root."""
    return _tree(tmp_path, "# Test spec\n").parent


def _md(root: Path, name: str, text: str) -> Path:
    p = root / name
    p.write_text(text)
    return p


def _lines(res):
    return res.stdout.splitlines()


# ---- positive controls: green on the base tree, no rule_pins.py needed ------------------

def test_control_pin_formula_matches_the_literal():
    # The section 3 formula on the fixture rule line gives the literal used below; whitespace is normalised.
    assert _pin(RULE_AFTER_ID) == PIN_LITERAL
    assert _pin("a   b\t c") == _pin("a b c")
    assert _pin("a b") != _pin("a  c")


def test_control_fixture_rule_is_one_physical_line_the_lint_loader_reads(tmp_path):
    root = _root(tmp_path)
    epic = (root / "docs" / "bible" / "epics" / "E-99-test.md").read_text()
    starts = [l for l in epic.splitlines() if l.startswith("- R-990-01 ")]
    assert len(starts) == 1 and starts[0] == "- R-990-01" + RULE_AFTER_ID, starts
    assert epic == EPIC_TEXT
    sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
    import spec_provenance as sp
    assert "R-990-01" in sp.load_context(root)["rules"]


def test_control_pinned_fixture_spec_is_lint_clean_and_unpinned_spec_names_the_same_id(tmp_path):
    root = _root(tmp_path)
    good = _md(root, "good.md", f"# Spec\n\nThe lot draws 7 rows. [B R-990-01@{PIN_LITERAL}: words]\n")
    assert _lint(good).returncode == 0
    bad = _md(root, "bad.md", "# Spec\n\nThe lot draws 7 rows. [B R-991-01@aaaaaa: words]\n")
    res = _lint(bad)
    assert res.returncode == 1 and "(4)" in res.stdout, res.stdout


def test_control_pieces_toml_fixture_parses():
    data = tomllib.loads(PIECES_TOML)
    assert [p["id"] for p in data["piece"]] == ["P-1", "P-2", "P-3"]
    assert [p.get("spec", "-") for p in data["piece"]] == ["docs/x.md", "-", "docs/y.md"]


# ---- pin ----------------------------------------------------------------------------------

def test_pin_prints_id_at_first_six_hex_of_the_normalised_rule_line(tmp_path):
    root = _root(tmp_path)
    res = _tool(root, "pin", "R-990-01")
    assert res.returncode == 0, res.stdout + res.stderr
    assert _lines(res) == [f"R-990-01@{PIN_LITERAL}"], res.stdout


def test_pin_unknown_id_prints_at_question_mark_and_exits_2_at_the_end(tmp_path):
    root = _root(tmp_path)
    res = _tool(root, "pin", "R-990-01", "R-990-09")
    assert _lines(res) == [f"R-990-01@{PIN_LITERAL}", "R-990-09@?"], res.stdout
    assert res.returncode == 2, res.stdout + res.stderr


# ---- unwrap -------------------------------------------------------------------------------

UNWRAP_BEFORE = (
    "# Notes\n"                                              # 1
    "\n"                                                     # 2
    "Tag `[B R-990-01]` stays a rule.\n"                     # 3
    "\n"                                                     # 4
    "Id `R-990-01` is not a tag.\n"                          # 5
    "\n"                                                     # 6
    "Doc `[B R-id@xxxxxx]` is a placeholder.\n"              # 7
    "\n"                                                     # 8
    "Words `see [B R-990-01]` stay.\n"                       # 9
    "\n"                                                     # 10
    "```\n"                                                  # 11
    "`[B R-990-01]`\n"                                       # 12
    "```\n"                                                  # 13
    "\n"                                                     # 14
    "Quote `[W 2026-10-11: \"see <path> now\"]` unwraps.\n"  # 15
    "\n"                                                     # 16
    "Row `[W Q-990-01]` too.\n"                              # 17
)
UNWRAP_AFTER = (
    UNWRAP_BEFORE
    .replace("Tag `[B R-990-01]`", "Tag [B R-990-01]")
    .replace("Quote `[W 2026-10-11: \"see <path> now\"]`", "Quote [W 2026-10-11: \"see <path> now\"]")
    .replace("Row `[W Q-990-01]`", "Row [W Q-990-01]")
)


def test_unwrap_unwraps_one_tag_spans_and_leaves_everything_else(tmp_path):
    root = _root(tmp_path)
    f = _md(root, "notes.md", UNWRAP_BEFORE)
    res = _tool(root, "unwrap", f)
    assert res.returncode == 0, res.stdout + res.stderr
    assert f.read_text() == UNWRAP_AFTER
    assert f"UNWRAP {f} 3 tags" in _lines(res), res.stdout
    assert f"SKIP {f}:7 placeholder" in _lines(res), res.stdout


# ---- rewrite ------------------------------------------------------------------------------

def test_rewrite_adds_the_pin_and_is_idempotent(tmp_path):
    root = _root(tmp_path)
    f = _md(root, "spec.md", "# Spec\n\nThe lot draws 7 rows. [B R-990-01: words]\n")
    res = _tool(root, "rewrite", f)
    assert res.returncode == 0, res.stdout + res.stderr
    assert f.read_text() == f"# Spec\n\nThe lot draws 7 rows. [B R-990-01@{PIN_LITERAL}: words]\n"
    assert f"REPIN {f} 1 added 0 refreshed" in _lines(res), res.stdout
    once = f.read_bytes()
    res2 = _tool(root, "rewrite", f)
    assert f.read_bytes() == once
    assert f"REPIN {f} 0 added 0 refreshed" in _lines(res2), res2.stdout


def test_rewrite_refreshes_a_stale_pin(tmp_path):
    root = _root(tmp_path)
    f = _md(root, "spec.md", f"# Spec\n\nThe lot draws 7 rows. [B R-990-01@{OTHER_PIN}: words]\n")
    res = _tool(root, "rewrite", f)
    assert f.read_text() == f"# Spec\n\nThe lot draws 7 rows. [B R-990-01@{PIN_LITERAL}: words]\n"
    assert f"REPIN {f} 0 added 1 refreshed" in _lines(res), res.stdout


def test_rewrite_skips_a_tag_inside_backticks(tmp_path):
    root = _root(tmp_path)
    text = "# Spec\n\nThe lot draws 7 rows. `[B R-990-01: words]`\n"
    f = _md(root, "spec.md", text)
    res = _tool(root, "rewrite", f)
    assert f.read_text() == text
    assert f"SKIP {f}:3 tag in backticks" in _lines(res), res.stdout


# ---- check --------------------------------------------------------------------------------

def _spec_with(pin: str) -> str:
    return f"# Spec\n\nThe lot draws 7 rows. [B R-990-01@{pin}: words]\n"


def test_check_clean_prints_pins_ok_with_counts_and_exits_0(tmp_path):
    root = _root(tmp_path)
    f = _md(root, "spec.md", _spec_with(PIN_LITERAL))
    res = _tool(root, "check", f)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "PINS OK 1 files 1 ids" in _lines(res), res.stdout


def test_check_stale_pin_rejects_naming_old_and_new_and_does_not_write(tmp_path):
    root = _root(tmp_path)
    f = _md(root, "spec.md", _spec_with(OTHER_PIN))
    before = f.read_bytes()
    res = _tool(root, "check", f)
    assert res.returncode == 1, res.stdout + res.stderr
    assert f"PINS REJECT {f}:3 R-990-01 stale {OTHER_PIN} {PIN_LITERAL}" in _lines(res), res.stdout
    assert f.read_bytes() == before


def test_check_missing_pin_rejects_as_missing_with_the_new_pin(tmp_path):
    root = _root(tmp_path)
    f = _md(root, "spec.md", "# Spec\n\nThe lot draws 7 rows. [B R-990-01: words]\n")
    res = _tool(root, "check", f)
    assert res.returncode == 1, res.stdout + res.stderr
    hit = [l for l in _lines(res) if l.startswith(f"PINS REJECT {f}:3 R-990-01 missing")]
    assert hit and hit[0].endswith(PIN_LITERAL), res.stdout


def test_check_only_rejects_the_named_file_and_warns_for_the_other(tmp_path):
    root = _root(tmp_path)
    a = _md(root, "a.md", _spec_with(OTHER_PIN))
    b = _md(root, "b.md", _spec_with(OTHER_PIN))
    res = _tool(root, "check", a, b, "--only", a)
    assert res.returncode == 1, res.stdout + res.stderr
    assert f"PINS REJECT {a}:3 R-990-01 stale {OTHER_PIN} {PIN_LITERAL}" in _lines(res), res.stdout
    assert not [l for l in _lines(res) if l.startswith("PINS REJECT") and str(b) in l], res.stdout
    assert "PINS WARN 1 stale outside the diff" in _lines(res), res.stdout


def test_check_only_exits_0_when_only_files_outside_the_diff_are_stale(tmp_path):
    root = _root(tmp_path)
    a = _md(root, "a.md", _spec_with(PIN_LITERAL))
    b = _md(root, "b.md", _spec_with(OTHER_PIN))
    res = _tool(root, "check", a, b, "--only", a)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "PINS WARN 1 stale outside the diff" in _lines(res), res.stdout
    assert not [l for l in _lines(res) if l.startswith("PINS REJECT")], res.stdout


# ---- spec-of ------------------------------------------------------------------------------

PIECES_TOML = (
    '[[piece]]\nid = "P-1"\nspec = "docs/x.md"\n\n'
    '[[piece]]\nid = "P-2"\n\n'
    '[[piece]]\nid = "P-3"\nspec = "docs/y.md"\n'
)


def test_spec_of_prints_the_spec_key_or_a_dash_one_per_line(tmp_path):
    root = _root(tmp_path)
    toml = _md(root, "pieces.toml", PIECES_TOML)
    res = _tool(root, "spec-of", toml, "P-1,P-2,P-3")
    assert res.returncode == 0, res.stdout + res.stderr
    assert _lines(res) == ["docs/x.md", "-", "docs/y.md"], res.stdout
