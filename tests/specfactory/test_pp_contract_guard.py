# spec: docs/northstar/plans/push/pp_contract.md section 6 "The guard call" (A170, row 18): om_command_guard.
# Contract test written before the call lands; red until the contract implementer adds the signatures.toml row,
# the header declaration and the conftest binding (`sig_table --emit`), which also appends the stub.
"""Static check of the om_command_guard landing (Addendum 62, A170; E-13 S-096, R-096-05).

Same method as test_pp_contract.py: the header, the table and the conftest are read as text. The helpers
are imported from that file (it is fenced; imported, not edited)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_pp_contract import (CONFTEST, CONFTEST_END, CONFTEST_START, DOC, HEADER, HEADER_BLOCK_RE,  # noqa: E402
                              REPO, conftest_bindings, count_declarations, rows_named, strip_c_comments,
                              table_symbols)

NAME = "om_command_guard"
MODULE = "tactical_move.c"
PARAMS = [("w", "om_world*"), ("unit_ids", "const uint32_t*"), ("n_units", "uint32_t")]


def test_control_stub_scan_sees_a_defined_function_and_ignores_a_comment():
    text = "/* int om_x(void) { */\nint om_y(int a) {\n    return 0;\n}\n"
    pat = rf"^[a-z_0-9 ]+\bom_y\s*\([^)]*\)\s*\{{"
    assert re.search(pat, strip_c_comments(text), re.M)
    assert not re.search(pat.replace("om_y", "om_x"), strip_c_comments(text), re.M)


def test_R_096_05_signatures_row_is_exact():
    rows = rows_named(table_symbols(), NAME)
    assert len(rows) == 1, f"{NAME}: expected exactly one signatures.toml row, found {len(rows)}"
    row = rows[0]
    assert row["module"] == MODULE
    assert row["restype"] == "int"
    assert [(p["name"], p["ctype"]) for p in row["params"]] == PARAMS


def test_R_096_05_header_declares_it_once_in_the_tactical_move_block():
    text = HEADER.read_text()
    assert count_declarations(text, NAME) == 1
    blocks = {m.group("mod"): m.group("body") for m in HEADER_BLOCK_RE.finditer(text)}
    assert MODULE in blocks and count_declarations(blocks[MODULE], NAME) == 1, \
        f"{NAME} must sit in the generated block of {MODULE}"


def test_R_096_05_conftest_binds_it_once_with_the_table_names():
    text = CONFTEST.read_text()
    assert CONFTEST_START in text, "conftest has no generated region"
    generated = text[text.index(CONFTEST_START):text.index(CONFTEST_END)]
    binds = conftest_bindings(generated)
    assert NAME in binds, f"{NAME} is not bound in the generated conftest region"
    assert binds[NAME]["count"] == 1
    assert binds[NAME]["params"] == [p for p, _ in PARAMS]
    assert conftest_bindings(text)[NAME]["count"] == 1, "not bound a second time outside the generated region"


def test_R_096_05_defined_in_tactical_move_c_and_nowhere_else():
    pat = rf"^[a-z_0-9 ]+\b{NAME}\s*\([^)]*\)\s*\{{"
    in_move = re.search(pat, strip_c_comments((REPO / "csrc" / "tactical_move.c").read_text()), re.M)
    assert in_move, f"{NAME} must be defined in csrc/tactical_move.c"
    for other in sorted((REPO / "csrc").glob("*.c")):
        if other.name == "tactical_move.c":
            continue
        assert not re.search(pat, strip_c_comments(other.read_text()), re.M), f"{NAME} is also defined in {other.name}"


def test_R_096_05_contract_document_names_the_call_and_its_returns():
    doc = DOC.read_text()
    assert "int om_command_guard(om_world *w, const uint32_t *unit_ids, uint32_t n_units)" in doc
    assert "R-096-05" in doc and "A170" in doc

