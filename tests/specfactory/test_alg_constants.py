# spec: docs/northstar/plans/briefs/2026-09-22-two-day-push.md decision 5 (F3)
"""Tests for scripts/specfactory/alg_constants.py: `--emit` turns
docs/bible/algorithms.md's ALG-01..75 paragraphs into csrc/om_constants.h;
`--lint` fails on a bare numeric literal in csrc/*.c outside the allowed
exemptions and the grandfathered-file allowlist."""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
TOOL = REPO / "scripts" / "specfactory" / "alg_constants.py"
ALGORITHMS_MD = REPO / "docs" / "bible" / "algorithms.md"
ALLOWLIST = REPO / "docs" / "northstar" / "spec_factory" / "constants_allowlist.txt"

sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
import alg_constants as ac  # noqa: E402


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True,
    )


# --------------------------------------------------------------------- --emit


def test_emit_never_edits_algorithms_md(tmp_path):
    before = ALGORITHMS_MD.read_bytes()
    proc = _run("--emit", str(tmp_path / "om_constants.h"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = ALGORITHMS_MD.read_bytes()
    assert before == after


def test_emit_writes_header_guard_and_generated_marker(tmp_path):
    out = tmp_path / "om_constants.h"
    proc = _run("--emit", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = out.read_text()
    assert "#ifndef OM_CONSTANTS_H" in text
    assert "#define OM_CONSTANTS_H" in text
    assert text.rstrip().endswith("#endif /* OM_CONSTANTS_H */")
    assert "GENERATED FILE" in text


def test_emit_is_idempotent(tmp_path):
    out1 = tmp_path / "a.h"
    out2 = tmp_path / "b.h"
    p1 = _run("--emit", str(out1))
    p2 = _run("--emit", str(out2))
    assert p1.returncode == 0 and p2.returncode == 0
    assert out1.read_text() == out2.read_text()


def test_emit_known_scalars(tmp_path):
    out = tmp_path / "om_constants.h"
    _run("--emit", str(out))
    text = out.read_text()
    assert "#define OM_ECONOMY_FLOOR 8.0" in text
    assert "#define OM_MILITARY_DECAY_RATE 0.006" in text
    assert "#define OM_TELEGRAPH_PREP_TICKS 3" in text
    assert "#define OM_COLONIZE_COST 20.0" in text


def test_emit_ranges_as_lo_hi(tmp_path):
    out = tmp_path / "om_constants.h"
    _run("--emit", str(out))
    text = out.read_text()
    assert "#define OM_HOME_POPULATION_RANGE_LO 55" in text
    assert "#define OM_HOME_POPULATION_RANGE_HI 75" in text
    assert "#define OM_WORLD_REGION_COUNT_RANGE_LO 60" in text
    assert "#define OM_WORLD_REGION_COUNT_RANGE_HI 110" in text


def test_emit_keyed_paren_range_table(tmp_path):
    """ALG-70: `CANVAS_SIZE_RANGES (small (8000, 12000), medium (12000,
    20000), large (20000, 28000))` -- the task's own worked example."""
    out = tmp_path / "om_constants.h"
    _run("--emit", str(out))
    text = out.read_text()
    assert "#define OM_CANVAS_SIZE_RANGES_SMALL_LO 8000" in text
    assert "#define OM_CANVAS_SIZE_RANGES_SMALL_HI 12000" in text
    assert "#define OM_CANVAS_SIZE_RANGES_MEDIUM_LO 12000" in text
    assert "#define OM_CANVAS_SIZE_RANGES_LARGE_HI 28000" in text


def test_emit_keyed_colon_table(tmp_path):
    out = tmp_path / "om_constants.h"
    _run("--emit", str(out))
    text = out.read_text()
    assert "#define OM_REINFORCE_MIL_CAP_HOME 100" in text
    assert "#define OM_REINFORCE_MIL_CAP_FRONTIER 60" in text
    assert "#define OM_ARCHETYPE_TELEGRAPH_PREFERENCE_CONQUEROR 0.7" in text
    assert "#define OM_ARCHETYPE_TELEGRAPH_PREFERENCE_DEFAULT 0.5" in text


def test_emit_keyed_colon_table_with_labels():
    """ALG-14: `ARCHETYPE_DECISION_WEIGHTS (attack, expand, defend):
    conqueror 1.2/1.0/0.4, ...` -- labels name the triple's components."""
    consts, _, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_ARCHETYPE_DECISION_WEIGHTS_CONQUEROR_ATTACK"].value == "1.2"
    assert consts["OM_ARCHETYPE_DECISION_WEIGHTS_CONQUEROR_EXPAND"].value == "1.0"
    assert consts["OM_ARCHETYPE_DECISION_WEIGHTS_CONQUEROR_DEFEND"].value == "0.4"


def test_emit_markdown_table():
    """ALG-26's full archetype x axis table."""
    consts, _, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_ARCHETYPE_TECH_MULTIPLIERS_CONQUEROR_ATTACK"].value == "0.16"
    assert consts["OM_ARCHETYPE_TECH_MULTIPLIERS_FORTIFIER_DEFENSE"].value == "0.09"
    assert consts["OM_ARCHETYPE_TECH_MULTIPLIERS_BREAKAWAY_ECONOMY"].value == "0.06"


def test_emit_markdown_table_skips_non_numeric_columns():
    """ALG-11's table mixes numeric weight columns with yes/no and prose
    columns; only the numeric ones are emitted, never guessed."""
    consts, unparsed, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_ARCHETYPE_ATTRACT_WEIGHTS_CONQUEROR_WEAKNESS"].value == "0.40"
    assert consts["OM_ARCHETYPE_ATTRACT_WEIGHTS_CONQUEROR_VALUE"].value == "0.25"
    assert consts["OM_ARCHETYPE_ATTRACT_WEIGHTS_CONQUEROR_POSITION"].value == "0.35"
    assert not any("TENSION_PRIMARY" in k or "CAN_COLONIZE" in k for k in consts)


def test_emit_brace_matrix():
    """ALG-60's damage category matrix: Strike/Line/Siege x Strike/Line/Siege."""
    consts, _, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_CATEGORY_MULTIPLIER_STRIKE_STRIKE"].value == "1.0"
    assert consts["OM_CATEGORY_MULTIPLIER_STRIKE_LINE"].value == "0.75"
    assert consts["OM_CATEGORY_MULTIPLIER_SIEGE_STRIKE"].value == "0.20"
    assert consts["OM_CATEGORY_MULTIPLIER_SIEGE_SIEGE"].value == "1.0"


def test_emit_bracket_list_of_pairs():
    """ALG-57: `PARITY_BREAKPOINTS = [(0, 0.80), (0.3, 0.85), ...]`."""
    consts, _, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_PARITY_BREAKPOINTS_N"].value == "5"
    assert consts["OM_PARITY_BREAKPOINTS_0_X"].value == "0"
    assert consts["OM_PARITY_BREAKPOINTS_0_Y"].value == "0.80"
    assert consts["OM_PARITY_BREAKPOINTS_4_Y"].value == "1.00"


def test_emit_formula_then_labels_convention():
    """ALG-07: "..., threshold `40.0`, rate `0.008`." names the two
    identifiers used just before it, in order."""
    consts, _, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_TENSION_STRESS_THRESHOLD"].value == "40.0"
    assert consts["OM_TENSION_STRESS_RATE"].value == "0.008"


def test_emit_formula_then_slash_weights():
    """ALG-09/10: "..., weights `0.40 / 0.35 / 0.25`." zipped positionally
    onto the formula's three identifiers."""
    consts, _, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_W_STAB_MILITARY"].value == "0.40"
    assert consts["OM_W_STAB_TENSION"].value == "0.35"
    assert consts["OM_W_STAB_POPULATION"].value == "0.25"


def test_emit_formula_then_range_label():
    """ALG-20: "..., range `(0.7, 1.3)`." on STOCHASTIC_RANGE."""
    consts, _, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_STOCHASTIC_RANGE_LO"].value == "0.7"
    assert consts["OM_STOCHASTIC_RANGE_HI"].value == "1.3"


def test_emit_compound_assignment_resolved_positionally():
    """ALG-07: "thresh = ECONOMY_FLOOR + SUBSISTENCE_CRISIS_RANGE = 8.0 +
    3.0" -- two identifiers, two values, same operator, matched by
    position, not by guessing which number is whose."""
    consts, _, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert consts["OM_SUBSISTENCE_CRISIS_RANGE"].value == "3.0"
    assert consts["OM_ECONOMY_FLOOR"].value == "8.0"


def test_emit_no_conflicts_in_real_doc():
    _, _, conflicts = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert conflicts == []


def test_emit_grouped_by_alg_id_with_comment(tmp_path):
    out = tmp_path / "om_constants.h"
    _run("--emit", str(out))
    lines = out.read_text().splitlines()
    idx = next(i for i, l in enumerate(lines) if "OM_ECONOMY_FLOOR " in l)
    comment_lines_above = [l for l in lines[:idx] if l.startswith("/* ALG-")]
    assert comment_lines_above, "every constant is preceded by an ALG-id comment somewhere above it"


def test_emit_deterministic_order(tmp_path):
    out = tmp_path / "om_constants.h"
    _run("--emit", str(out))
    defines = [l for l in out.read_text().splitlines() if l.startswith("#define OM_")]
    # within each ALG comment group, defines are alphabetical by output name
    groups = out.read_text().split("/* ALG-")[1:]
    for g in groups:
        body = g.split("*/", 1)[1]
        names = [l.split()[1] for l in body.splitlines() if l.startswith("#define ")]
        assert names == sorted(names)
    assert defines  # sanity: something was emitted


def test_ambiguous_compound_not_guessed():
    """ALG-59: `REFUSAL_TENSION_PENALTY_PCT = 8 / 100` -- a division
    compound, not a single number; never guessed as 8 nor as 0.08."""
    consts, unparsed, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert "OM_REFUSAL_TENSION_PENALTY_PCT" not in consts
    assert "REFUSAL_TENSION_PENALTY_PCT" in unparsed


def test_unparsed_reports_boolean_feature_flags():
    """ENABLE_* flags are booleans with no numeric value anywhere in the
    doc; they must be reported, never silently dropped nor guessed."""
    _, unparsed, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert "ENABLE_OSCILLATION" in unparsed


def test_unparsed_never_includes_a_resolved_table_umbrella_name():
    """A keyed table's own umbrella identifier (e.g.
    ARCHETYPE_TELEGRAPH_PREFERENCE) must not appear in the unparsed report
    once its keyed entries are resolved."""
    consts, unparsed, _ = ac.parse_algorithms_md(ALGORITHMS_MD.read_text())
    assert any(k.startswith("OM_ARCHETYPE_TELEGRAPH_PREFERENCE_") for k in consts)
    assert "ARCHETYPE_TELEGRAPH_PREFERENCE" not in unparsed


def test_positive_control_scratch_module_ambiguous_literal_is_unparsed(tmp_path):
    """A made-up formula-plus-bare-literal shape the parser has no pattern
    for must be reported, never guessed a value."""
    scratch = tmp_path / "scratch_algorithms.md"
    scratch.write_text(
        "# scratch\n\n**ALG-01 Made up.** `x = SCRATCH_WEIRD_CONSTANT` "
        "encoded some other way entirely, not a number at all.\n"
    )
    consts, unparsed, _ = ac.parse_algorithms_md(scratch.read_text())
    assert "OM_SCRATCH_WEIRD_CONSTANT" not in consts
    assert "SCRATCH_WEIRD_CONSTANT" in unparsed


# --------------------------------------------------------------------- --lint


def test_lint_positive_control_bare_literal_fails(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "newmodule.c").write_text("double f(double x) { return x * 0.33; }\n")
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "0.33" in proc.stdout
    assert "newmodule.c" in proc.stdout
    assert "CONSTANTS LINT FAILED" in proc.stdout


def test_lint_negative_control_real_csrc_passes():
    proc = _run("--lint", str(REPO / "csrc"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "CONSTANTS LINT OK" in proc.stdout


@pytest.mark.parametrize("literal", ["0", "1", "-1", "2", "0.0", "1.0", "-1.0", "2.0"])
def test_lint_always_exempt_values_never_flagged(tmp_path, literal):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "newmodule.c").write_text(f"double f(double x) {{ return x * {literal}; }}\n")
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_lint_array_size_in_declaration_exempt(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "newmodule.c").write_text(
        "void f(void) {\n"
        "    double vals[6] = {0};\n"
        "    (void)vals;\n"
        "}\n"
    )
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_lint_array_index_is_not_exempt(tmp_path):
    """Only a *declaration's* array size is exempt; indexing with a magic
    number is still a bare literal."""
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "newmodule.c").write_text(
        "void f(double *vals) {\n"
        "    double x = vals[3];\n"
        "    (void)x;\n"
        "}\n"
    )
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "`3`" in proc.stdout


def test_lint_define_line_exempt(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "newmodule.c").write_text("#define OM_NEWMODULE_MAGIC 42\n")
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_lint_sizeof_argument_exempt(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "newmodule.c").write_text(
        "#include <stddef.h>\n"
        "size_t f(void) { return sizeof(double); }\n"
    )
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_lint_comment_mentioning_a_number_not_flagged(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "newmodule.c").write_text(
        "/* the constant used to be 0.33, now it lives in om_constants.h */\n"
        "// see also 0.5 in the old code\n"
        "double f(double x) { return x; }\n"
    )
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_lint_string_literal_with_digits_not_flagged(tmp_path):
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "newmodule.c").write_text(
        '#include <stdio.h>\n'
        'void f(void) { printf("version 0.33\\n"); }\n'
    )
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_lint_new_module_is_not_grandfathered(tmp_path):
    """A brand-new module gets none of the grandfathered files' slack --
    every bare literal in it fails, even ones a grandfathered file could
    carry via the allowlist."""
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "brandnew.c").write_text("double f(double x) { return x * 8.0; }\n")
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "8.0" in proc.stdout


def test_lint_grandfathered_file_still_fails_on_a_literal_outside_the_allowlist(tmp_path):
    """sim.c is grandfathered by exact file:line:col:token; a literal at a
    location the allowlist does not name still fails -- grandfathering is
    not a blanket exemption for the whole file."""
    csrc = tmp_path / "csrc"
    csrc.mkdir()
    (csrc / "sim.c").write_text("double f(double x) { return x * 0.99; }\n")
    proc = _run("--lint", str(csrc))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "0.99" in proc.stdout


def test_allowlist_file_exists_and_is_nonempty():
    assert ALLOWLIST.exists()
    lines = [l for l in ALLOWLIST.read_text().splitlines() if l.strip()]
    assert len(lines) > 0
    for line in lines:
        path, lineno, col, token = line.split(":", 3)
        assert path.startswith("csrc/")
        assert path.rsplit("/", 1)[-1] in ac.GRANDFATHERED_FILES
        int(lineno)
        int(col)
        assert token


def test_lint_missing_dir_exits_2(tmp_path):
    proc = _run("--lint", str(tmp_path / "does_not_exist"))
    assert proc.returncode == 2, proc.stdout + proc.stderr
