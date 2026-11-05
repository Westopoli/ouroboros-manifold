# spec: docs/northstar/plans/push/pp_contract.md (piece PP-contract: one ABI bump, 3 to 4, every call of the
# movement-layers-and-search plan's appendix). Contract tests written before the contract lands; they are
# red until the builder lands the header, signatures.toml and conftest changes and runs `sig_table --emit`.
"""Static and one built-library check of the PP-contract landing.

Nothing here imports tests/csim/conftest.py (it builds the libraries on import); the header, the table
and the conftest are read as text, in the style of test_conftest_bindings.py. The one exception is
test_library_reports_abi_4, which builds libouroboros.so the way tests/csim/conftest.py does and asks it.

The contract document's enum table (docs/northstar/plans/push/pp_contract.md section 4) is the order the
header must follow. Every detector below has a positive control on synthetic input."""
import ast
import ctypes
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SIG_TABLE = REPO / "scripts" / "specfactory" / "sig_table.py"
HEADER = REPO / "csrc" / "ouroboros_sim.h"
CONFTEST = REPO / "tests" / "csim" / "conftest.py"
TABLE = REPO / "docs" / "northstar" / "spec_factory" / "signatures.toml"
DOC = REPO / "docs" / "northstar" / "plans" / "push" / "pp_contract.md"

EXPECTED_ABI = 10

# name -> (module, restype, [(param name, ctype), ...]); the contract document section 1 and 6 (17 calls).
W = "om_world*"
CW = "const om_world*"
NEW_CALLS = {
    "om_tactical_get_param": ("tactical_move.c", "double", [("w", CW), ("p", "om_tac_param")]),
    "om_tactical_set_param": ("tactical_move.c", "int", [("w", W), ("p", "om_tac_param"), ("value", "double")]),
    "om_map_set_canvas": ("tactical_mapgen.c", "int", [("w", W), ("width", "double"), ("height", "double")]),
    "om_map_block_rect": ("tactical_mapgen.c", "int", [
        ("w", W), ("x0", "double"), ("y0", "double"), ("x1", "double"), ("y1", "double"),
        ("layer_lo", "uint32_t"), ("layer_hi", "uint32_t")]),
    "om_command_set_layer": ("tactical_move.c", "int", [
        ("w", W), ("unit_ids", "const uint32_t*"), ("n_units", "uint32_t"), ("layer", "uint32_t")]),
    "om_unit_transition_progress": ("tactical_move.c", "double", [("w", CW), ("unit", "uint32_t")]),
    "om_unit_get_target_layer": ("tactical_move.c", "uint32_t", [("w", CW), ("unit", "uint32_t")]),
    "om_roster_set_reach": ("tactical_move.c", "int", [
        ("w", W), ("unit_type", "int"), ("layers_up", "uint32_t"), ("layers_down", "uint32_t")]),
    "om_unit_profile_reach": ("tactical_move.c", "int", [
        ("w", CW), ("unit_type", "int"), ("up", "uint32_t*"), ("down", "uint32_t*")]),
    "om_command_set_emission": ("fog.c", "int", [
        ("w", W), ("unit_ids", "const uint32_t*"), ("n_units", "uint32_t"), ("mode", "om_emission")]),
    "om_unit_get_emission": ("fog.c", "int", [("w", CW), ("unit", "uint32_t")]),
    "om_command_ping": ("fog.c", "int", [
        ("w", W), ("caster", "uint32_t"), ("layer", "uint32_t"), ("x", "double"), ("y", "double")]),
    "om_ping_alert_count": ("fog.c", "uint32_t", [("w", CW), ("faction", "int32_t")]),
    "om_ping_alert_get": ("fog.c", "int", [
        ("w", CW), ("faction", "int32_t"), ("index", "uint32_t"), ("out", "om_ping_alert*")]),
    # A133: three read-only getters, defined in tactical_move.c (never unit.c), stubs in the contract wave
    "om_unit_get_group_id": ("tactical_move.c", "uint32_t", [("w", CW), ("unit", "uint32_t")]),
    "om_unit_get_leash_anchor": ("tactical_move.c", "int", [
        ("w", CW), ("unit", "uint32_t"), ("x", "double*"), ("y", "double*")]),
    "om_unit_get_engaged": ("tactical_move.c", "int", [("w", CW), ("unit", "uint32_t")]),
}

HEADER_BLOCK_RE = re.compile(
    r"/\* ---- generated from signatures\.toml: (?P<mod>[^ ]+) ---- \*/\n(?P<body>.*?)"
    r"/\* ---- end generated: (?P=mod) ---- \*/\n",
    re.S,
)
CONFTEST_START = "# ---- generated from signatures.toml ----"
CONFTEST_END = "# ---- end generated ----"


# ---- readers (each has a positive control below) ----

def strip_c_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def count_declarations(header_text: str, name: str) -> int:
    """Occurrences of `name(` outside comments."""
    return len(re.findall(rf"\b{re.escape(name)}\s*\(", strip_c_comments(header_text)))


def parse_c_enum(header_text: str, enum_name: str):
    """Members of an anonymous-tag `typedef enum {...} enum_name;` as [(name, value)], else None.
    Values: explicit `= N`, else previous + 1, first 0."""
    m = re.search(r"typedef\s+enum\s*\{([^}]*)\}\s*" + re.escape(enum_name) + r"\s*;",
                  strip_c_comments(header_text), re.S)
    if not m:
        return None
    members, value = [], -1
    for item in m.group(1).split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            name, _, num = item.partition("=")
            value = int(num.strip(), 0)
            name = name.strip()
        else:
            name, value = item, value + 1
        members.append((name, value))
    return members


def parse_param_table(doc_text: str):
    """Rows of the section 4 table: [{'value', 'name', 'kind', 'default', 'lo', 'hi'}] in table order,
    including the OM_TP__COUNT sentinel row (default/lo/hi None)."""
    rows, inside = [], False
    for line in doc_text.splitlines():
        if line.startswith("| # | member |"):
            inside = True
            continue
        if not inside:
            continue
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0].startswith("---"):
            continue
        name = cells[1].strip("`")
        if name == "OM_TP__COUNT":
            rows.append({"value": int(cells[0]), "name": name, "kind": None,
                         "default": None, "lo": None, "hi": None})
        else:
            rows.append({"value": int(cells[0]), "name": name, "kind": cells[2],
                         "default": float(cells[3]), "lo": float(cells[4]), "hi": float(cells[5])})
    return rows


def conftest_bindings(conftest_text: str) -> dict:
    """symbol -> {'params': [names], 'count': n} from every _bind(lib, "name", ...) call."""
    out = {}
    for node in ast.walk(ast.parse(conftest_text)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_bind"):
            continue
        if len(node.args) < 5:
            continue
        entry = out.setdefault(node.args[1].value, {"params": [e.value for e in node.args[4].elts], "count": 0})
        entry["count"] += 1
    return out


def conftest_enum_class(conftest_text: str, class_name: str):
    """{attr: int} of a plain `class X:` holding integer constants, else None."""
    for node in ast.parse(conftest_text).body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {t.id: stmt.value.value for stmt in node.body if isinstance(stmt, ast.Assign)
                    and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, int)
                    for t in stmt.targets if isinstance(t, ast.Name)}
    return None


def table_symbols() -> dict:
    with open(TABLE, "rb") as f:
        data = tomllib.load(f)
    return data


def rows_named(data: dict, name: str) -> list:
    return [r for r in data["symbols"] if r["name"] == name]


# ---- positive controls for the readers ----

def test_control_count_declarations_sees_a_duplicate_and_ignores_comments():
    text = "/* om_x(old) */\nint om_x(int a);\nint om_x(double a);\nint om_y(int a);\n"
    assert count_declarations(text, "om_x") == 2
    assert count_declarations(text, "om_y") == 1
    assert count_declarations(text, "om_z") == 0


def test_control_parse_c_enum_reads_values_and_rejects_the_tagged_form():
    text = "typedef enum { OM_A = 0, OM_B, OM_C = 7, OM_D } om_thing;\n"
    assert parse_c_enum(text, "om_thing") == [("OM_A", 0), ("OM_B", 1), ("OM_C", 7), ("OM_D", 8)]
    tagged = "typedef enum om_thing { OM_A = 0 } om_thing;\n"
    assert parse_c_enum(tagged, "om_thing") is None, "sig_table only recognises the anonymous-tag typedef"


def test_control_parse_param_table_reads_rows_and_stops_at_the_end():
    doc = ("text\n| # | member | kind | default | lo | hi | default source | range basis |\n"
           "|---|---|---|---|---|---|---|---|\n"
           "| 0 | `OM_TP_A` | bool | 1 | 0 | 1 | s | r |\n"
           "| 1 | `OM_TP_B` | real | 2.5 | 0 | 10 | s | r |\n"
           "| 2 | `OM_TP__COUNT` | - | - | - | - | s | - |\n\nmore text | not a row |\n")
    rows = parse_param_table(doc)
    assert [r["name"] for r in rows] == ["OM_TP_A", "OM_TP_B", "OM_TP__COUNT"]
    assert rows[1]["default"] == 2.5 and rows[1]["hi"] == 10.0 and rows[0]["kind"] == "bool"


def test_control_conftest_readers_see_a_binding_and_an_enum_class():
    text = ('class OMX:\n    A = 0\n    B = 3\n\n'
            'def f(lib):\n    _bind(lib, "om_x", [W, ctypes.c_int], ctypes.c_int, ("w", "p"))\n')
    assert conftest_bindings(text) == {"om_x": {"params": ["w", "p"], "count": 1}}
    assert conftest_enum_class(text, "OMX") == {"A": 0, "B": 3}
    assert conftest_enum_class(text, "OMMissing") is None


# ---- the contract (red until it lands) ----

def test_R_020_header_abi_version_is_4():
    m = re.search(r"#define\s+OM_ABI_VERSION\s+(\d+)", HEADER.read_text())
    assert m and int(m.group(1)) == EXPECTED_ABI


def test_R_020_conftest_expects_abi_4():
    m = re.search(r"^EXPECTED_ABI_VERSION\s*=\s*(\d+)", CONFTEST.read_text(), re.M)
    assert m and int(m.group(1)) == EXPECTED_ABI


def test_R_020_table_meta_abi_version_is_4():
    assert table_symbols()["meta"]["abi_version"] == EXPECTED_ABI


def test_R_020_library_reports_abi_4():
    """om_abi_version() from a freshly built library agrees with the header."""
    res = subprocess.run(["make", "-s", "libouroboros.so"], cwd=str(REPO), capture_output=True, text=True,
                         timeout=300)
    assert res.returncode == 0, (res.stderr or res.stdout)[-2000:]
    lib = ctypes.CDLL(str(REPO / "libouroboros.so"))
    lib.om_abi_version.argtypes = []
    lib.om_abi_version.restype = ctypes.c_uint32
    assert lib.om_abi_version() == EXPECTED_ABI


@pytest.mark.parametrize("name", sorted(NEW_CALLS))
def test_every_new_call_has_one_exact_signatures_row(name):
    module, restype, params = NEW_CALLS[name]
    rows = rows_named(table_symbols(), name)
    assert len(rows) == 1, f"{name}: expected exactly one signatures.toml row, found {len(rows)}"
    row = rows[0]
    assert row["module"] == module
    assert row["restype"] == restype
    assert [(p["name"], p["ctype"]) for p in row["params"]] == params


def test_ping_alert_struct_row_and_typedef():
    data = table_symbols()
    rows = [s for s in data.get("structs", []) if s["name"] in ("OMPingAlert", "om_ping_alert")]
    assert len(rows) == 1, "one [[structs]] row for om_ping_alert"
    assert [(f["name"], f["ctype"]) for f in rows[0]["fields"]] == [
        ("tick", "uint64_t"), ("faction", "int32_t"), ("sector", "int32_t")]
    header = strip_c_comments(HEADER.read_text())
    assert re.search(r"typedef\s+struct\s+\w*\s*\{[^}]*\}\s*om_ping_alert\s*;", header, re.S)


def define_value(text: str, name: str):
    """Values of every `#define name value` outside comments, as numbers (ints stay ints)."""
    out = []
    for m in re.finditer(rf"^[ \t]*#define[ \t]+{re.escape(name)}[ \t]+([0-9.]+)[ \t]*$", strip_c_comments(text), re.M):
        out.append(float(m.group(1)) if "." in m.group(1) else int(m.group(1)))
    return out


def test_control_define_value_counts_a_duplicate_and_ignores_comments():
    text = "/* #define OM_X 1 */\n#define OM_X 5\n#define OM_X 6\n#define OM_Y 2.5\n#define OM_XX 9\n"
    assert define_value(text, "OM_X") == [5, 6]
    assert define_value(text, "OM_Y") == [2.5]
    assert define_value(text, "OM_Z") == []


def test_E01_A132_header_carries_the_layer_count_as_one_named_constant_5():
    """A132: engine layers 0 to 4; the count is one constant, defined once."""
    assert define_value(HEADER.read_text(), "OM_LAYER_COUNT") == [5]


def test_PP_header_carries_the_canvas_limit_as_one_named_constant_28000():
    """A133 Q-C3: the limit is OM_MAP_MAX_CANVAS, defined once, equal to the constants header's large range."""
    assert [float(v) for v in define_value(HEADER.read_text(), "OM_MAP_MAX_CANVAS")] == [28000.0]
    large = define_value((REPO / "csrc" / "om_constants.h").read_text(), "OM_CANVAS_SIZE_RANGES_LARGE_HI")
    assert [float(v) for v in large] == [28000.0]


def test_the_three_getters_are_defined_in_tactical_move_never_in_unit_c():
    """A133: the stubs go to tactical_move.c. Positive control: a getter defined in unit.c would be found."""
    getters = ("om_unit_get_group_id", "om_unit_get_leash_anchor", "om_unit_get_engaged")
    pat = lambda n: rf"^[a-z_0-9 ]+\b{n}\s*\([^)]*\)\s*\{{"
    assert re.search(pat("om_unit_get_group_id"), "uint32_t om_unit_get_group_id(const om_world *w, uint32_t unit) {\n", re.M)
    move = strip_c_comments((REPO / "csrc" / "tactical_move.c").read_text())
    unit = strip_c_comments((REPO / "csrc" / "unit.c").read_text())
    for n in getters:
        assert re.search(pat(n), move, re.M), f"{n} must be defined in tactical_move.c"
        assert not re.search(pat(n), unit, re.M), f"{n} must not be defined in unit.c"


def test_param_table_in_the_contract_document_is_well_formed():
    rows = parse_param_table(DOC.read_text())
    assert len(rows) == 68, "67 parameters and the OM_TP__COUNT sentinel"
    assert [r["value"] for r in rows] == list(range(68))
    assert rows[-1]["name"] == "OM_TP__COUNT"
    by_name = {r["name"]: r for r in rows}
    # the six switches the plan names, hardcoded here so a mis-transcribed table cannot hide
    for name, default in (("OM_TP_PURSUE_BY_STEERING", 1), ("OM_TP_ROUTE_AROUND_TERRAIN", 1),
                          ("OM_TP_LEASH_BEFORE_DAMAGE", 0), ("OM_TP_TARGET_POLICY", 0),
                          ("OM_TP_TARGET_BY_SIGHT", 1), ("OM_TP_ROUTE_ACROSS_LAYERS", 1)):
        assert by_name[name]["default"] == default, name
    assert [r["name"] for r in rows[:6]] == [
        "OM_TP_PURSUE_BY_STEERING", "OM_TP_ROUTE_AROUND_TERRAIN", "OM_TP_LEASH_BEFORE_DAMAGE",
        "OM_TP_TARGET_POLICY", "OM_TP_TARGET_BY_SIGHT", "OM_TP_ROUTE_ACROSS_LAYERS"]
    for r in rows[:-1]:
        assert r["lo"] <= r["default"] <= r["hi"], f"{r['name']}: default outside its own range"


def test_header_enum_om_tac_param_matches_the_document_in_names_and_order():
    expected = [(r["name"], r["value"]) for r in parse_param_table(DOC.read_text())]
    assert parse_c_enum(HEADER.read_text(), "om_tac_param") == expected


def test_header_enum_om_emission():
    assert parse_c_enum(HEADER.read_text(), "om_emission") == [("OM_EMIT_SILENT", 0), ("OM_EMIT_ACTIVE", 1)]


@pytest.mark.parametrize("name", sorted(NEW_CALLS))
def test_header_declares_each_new_call_once_in_its_module_block(name):
    text = HEADER.read_text()
    assert count_declarations(text, name) == 1
    module = NEW_CALLS[name][0]
    blocks = {m.group("mod"): m.group("body") for m in HEADER_BLOCK_RE.finditer(text)}
    assert module in blocks and count_declarations(blocks[module], name) == 1, \
        f"{name} must sit in the generated block of {module}"


@pytest.mark.parametrize("name", sorted(NEW_CALLS))
def test_conftest_binds_each_new_call_once_with_the_table_names(name):
    text = CONFTEST.read_text()
    generated = text[text.index(CONFTEST_START):text.index(CONFTEST_END)]
    binds = conftest_bindings(generated)
    assert name in binds, f"{name} is not bound in the generated conftest region"
    assert binds[name]["count"] == 1
    assert binds[name]["params"] == [p for p, _ in NEW_CALLS[name][2]]
    assert conftest_bindings(text)[name]["count"] == 1, "not bound a second time outside the generated region"


def test_conftest_enum_mirrors_match_the_header():
    text = CONFTEST.read_text()
    tac = conftest_enum_class(text, "OMTacParam")
    assert tac is not None, "tests/csim/conftest.py needs a hand-written OMTacParam mirror"
    expected = {n[len("OM_TP_"):]: v for n, v in parse_c_enum(HEADER.read_text(), "om_tac_param")}
    assert tac == expected
    assert conftest_enum_class(text, "OMEmission") == {"SILENT": 0, "ACTIVE": 1}
    assert "class OMPingAlert(ctypes.Structure)" in text


def test_sig_table_check_is_clean_once_the_rows_exist():
    """Precondition: the rows are in the table (so this is red today). Then `--check` exits 0: header
    blocks, bindings and the stubs in the module .c files are all already emitted."""
    data = table_symbols()
    missing = [n for n in NEW_CALLS if not rows_named(data, n)]
    assert not missing, f"rows missing from signatures.toml: {missing}"
    proc = subprocess.run([sys.executable, str(SIG_TABLE), "--check"], cwd=str(REPO), capture_output=True,
                          text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_om_map_add_cover_stays_one_symbol_and_height_is_still_a_double():
    """Plan conflict, contract document section 5: the existing adder is kept, no second call."""
    data = table_symbols()
    rows = rows_named(data, "om_map_add_cover")
    assert len(rows) == 1
    assert [(p["name"], p["ctype"]) for p in rows[0]["params"]] == [
        ("w", "om_world*"), ("x", "double"), ("y", "double"), ("radius", "double"), ("height", "double")]
    header = HEADER.read_text()
    assert count_declarations(header, "om_map_add_cover") == 1
    assert "height_layers" not in header
    assert "height_layers" not in TABLE.read_text()
