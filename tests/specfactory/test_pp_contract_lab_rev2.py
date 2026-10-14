# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, "Contract / Engine" and the Pieces row E0
# (piece LAB-REV2-E0: the contract lands before any engine shard builds). Tests written before the contract
# lands; red until E0's builder lands the header, the table row, the stubs, the pins and the bumps.
"""Static and built-library checks of the LAB-REV2-E0 contract piece.

What E0 lands (spec, Contract / Engine):
  * one setting, OM_TP_FIRING_ARC_DEG (real, default 360, bounds 10 to 360), appended before OM_TP__COUNT,
    with its OM_PP_ROWS row, its pp_contract.md section 4 row and its line in the conftest OMTacParam mirror;
  * two stubbed symbols, om_roster_set_cone (module tactical_move.c) and om_combat_can_engage (module unit.c),
    declared with the spec's exact signatures, with signatures.toml rows; both answer -1 ("not built")
    until LAB-REV2-E2 writes the bodies;
  * an ABI bump and a save-format bump (the setting is hashed in the net section and written in the save
    slot).

ABI and save-format numbers are NEVER pre-claimed (Architect 2026-10-14): E0 takes the next free number of each
at its landing, after VG-CONTRACT-E7 (ABI 7 to 8, save 11 to 12), and a clerk writes the actual numbers then.
So no test here names the new ABI or save number. They assert CONSISTENCY: every pin of the ABI number agrees
with the header, and every pin of the save-format number agrees with om_internal.h, and both are strictly above
the values on main before E0. COUNT is fixed (66 to 67), so it is asserted as BASE + 1.

Nothing here imports tests/csim/conftest.py (it builds the libraries on import and pins the ABI); the header,
the table, the contract document and the conftest are read as text, in the style of test_pp_contract.py, and
the built-library checks bind the handful of symbols they need themselves.

Every detector below that reads text has a positive control on synthetic input; every refusal check has an
in-range set on the same parameter that must return 0 and read back."""
import ast
import ctypes
import math
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
HEADER = REPO / "csrc" / "ouroboros_sim.h"
INTERNAL = REPO / "csrc" / "om_internal.h"
PIPE_INTERNAL = REPO / "csrc" / "pipe" / "pipe_internal.h"
TACTICAL_MOVE = REPO / "csrc" / "tactical_move.c"
CONFTEST = REPO / "tests" / "csim" / "conftest.py"
TABLE = REPO / "docs" / "northstar" / "spec_factory" / "signatures.toml"
DOC = REPO / "docs" / "northstar" / "plans" / "push" / "pp_contract.md"
ARCH = REPO / "docs" / "architecture.md"
LOAD_GAME_GD = REPO / "scenes" / "load_game" / "load_game.gd"
LOAD_GAME_TEST_GD = REPO / "tests" / "test_load_game_wrong_version.gd"

# The values on main before E0 landed. The ABI and save numbers are not named after E0 (never pre-claimed): the
# clerk who lands VG-CONTRACT-E7 (ABI 8, save 12) raises BASE_ABI_BEFORE_E0 and BASE_SAVE_BEFORE_E0 to the numbers
# E7 took, in the same landing, so "strictly greater" keeps meaning "E0 bumped it". COUNT is E0's alone.
BASE_ABI_BEFORE_E0 = 7
BASE_SAVE_BEFORE_E0 = 11
BASE_COUNT_BEFORE_E0 = 66

ARC = "OM_TP_FIRING_ARC_DEG"
ARC_DEFAULT, ARC_LO, ARC_HI = 360.0, 10.0, 360.0

SET_CONE_SIG = "int om_roster_set_cone(om_world *w, int unit_type, double range, double half_angle_deg, double share);"
CAN_ENGAGE_SIG = "int om_combat_can_engage(const om_world *w, uint32_t attacker, uint32_t target);"
NEW_SYMBOLS = {
    "om_roster_set_cone": ("tactical_move.c", "int", [
        ("w", "om_world*"), ("unit_type", "int"), ("range", "double"), ("half_angle_deg", "double"),
        ("share", "double")]),
    "om_combat_can_engage": ("unit.c", "int", [
        ("w", "const om_world*"), ("attacker", "uint32_t"), ("target", "uint32_t")]),
}
NOT_BUILT = -1  # spec: the stubs return -1 ("not built") until LAB-REV2-E2


# ---- text readers (each has a positive control below) ----

def strip_c_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def count_declarations(header_text: str, name: str) -> int:
    return len(re.findall(rf"\b{re.escape(name)}\s*\(", strip_c_comments(header_text)))


def parse_c_enum(header_text: str, enum_name: str):
    """Members of an anonymous-tag `typedef enum {...} enum_name;` as [(name, value)], else None."""
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
    """Rows of the pp_contract.md section 4 table, in order, including the OM_TP__COUNT sentinel row."""
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


def conftest_enum_class(conftest_text: str, class_name: str):
    """{attr: int} of a plain `class X:` holding integer constants, else None."""
    for node in ast.parse(conftest_text).body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {t.id: stmt.value.value for stmt in node.body if isinstance(stmt, ast.Assign)
                    and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, int)
                    for t in stmt.targets if isinstance(t, ast.Name)}
    return None


def conftest_binding_params(conftest_text: str, symbol: str):
    """Parameter names of the `_bind(lib, "symbol", ...)` call, else None."""
    for node in ast.walk(ast.parse(conftest_text)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_bind"
                and len(node.args) >= 5 and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == symbol):
            return [e.value for e in node.args[4].elts]
    return None


def define_value(text: str, name: str):
    m = re.search(rf"^[ \t]*#define[ \t]+{re.escape(name)}[ \t]+(\d+)", text, re.M)
    return int(m.group(1)) if m else None


def last_table_row(c_text: str, table: str):
    """The last top-level brace entry of `static const ... table[...] = { ... };` (comments stripped), else None."""
    m = re.search(rf"\b{re.escape(table)}\s*\[[^\]]*\]\s*=\s*\{{", strip_c_comments(c_text))
    if not m:
        return None
    text, depth, start, last, i = strip_c_comments(c_text), 1, None, None, m.end()
    while i < len(text) and depth:
        ch = text[i]
        if ch == "{":
            depth += 1
            if depth == 2:
                start = i
        elif ch == "}":
            depth -= 1
            if depth == 1 and start is not None:
                last = text[start:i + 1]
        i += 1
    return squash(last) if last else None


def table_symbols() -> dict:
    with open(TABLE, "rb") as f:
        return tomllib.load(f)


def rows_named(data: dict, name: str) -> list:
    return [r for r in data["symbols"] if r["name"] == name]


def header_enum():
    members = parse_c_enum(HEADER.read_text(), "om_tac_param")
    assert members, "om_tac_param typedef not found in csrc/ouroboros_sim.h"
    return members


# ---- positive controls for the readers ----

def test_control_readers_see_enum_rows_defines_and_bindings():
    assert squash("a \n  b\t c") == "a b c"
    assert count_declarations("/* om_x(old) */\nint om_x(int a);\nint om_x(double a);\n", "om_x") == 2
    assert parse_c_enum("typedef enum { OM_A = 0, OM_B, OM_C } om_t;\n", "om_t") == [
        ("OM_A", 0), ("OM_B", 1), ("OM_C", 2)]
    doc = ("| # | member | kind | default | lo | hi | s | r |\n|---|---|---|---|---|---|---|---|\n"
           "| 0 | `OM_TP_A` | real | 360 | 10 | 360 | s | r |\n| 1 | `OM_TP__COUNT` | - | - | - | - | s | - |\n")
    rows = parse_param_table(doc)
    assert rows[0]["default"] == 360.0 and rows[0]["lo"] == 10.0 and rows[1]["name"] == "OM_TP__COUNT"
    assert conftest_enum_class("class X:\n    A = 0\n    _COUNT = 2\n", "X") == {"A": 0, "_COUNT": 2}
    assert conftest_binding_params('_bind(lib, "om_x", [W], ctypes.c_int, ("w", "p"))\n', "om_x") == ["w", "p"]
    assert conftest_binding_params('_bind(lib, "om_x", [W], ctypes.c_int, ("w", "p"))\n', "om_y") is None
    assert define_value("#define OM_FOO_VERSION 12 /* c */\n", "OM_FOO_VERSION") == 12
    assert define_value("#define OM_FOO_VERSION 12\n", "OM_BAR") is None
    c = "static const t TAB[3] = {\n  { A, 1 }, /* x */\n  OM_M(2),\n  { B,\n    3 },\n};\n"
    assert last_table_row(c, "TAB") == "{ B, 3 }"
    assert last_table_row(c, "NOPE") is None


# ---- the setting: enum member, table row, doc row, conftest mirror ----

def test_member_is_appended_last_before_the_count_and_count_moves_by_one():
    members = header_enum()
    names = [n for n, _ in members]
    assert ARC in names, f"{ARC} is not a member of om_tac_param in csrc/ouroboros_sim.h"
    assert names[-1] == "OM_TP__COUNT" and names[-2] == ARC, "the new member goes last, right before OM_TP__COUNT"
    values = dict(members)
    assert values[ARC] == BASE_COUNT_BEFORE_E0, "appended: no existing number moves"
    assert values["OM_TP__COUNT"] == BASE_COUNT_BEFORE_E0 + 1


def test_pp_rows_table_is_positional_sized_by_count_and_has_the_real_arc_row_last():
    text = TACTICAL_MOVE.read_text()
    assert re.search(r"om_pp_row\s+OM_PP_ROWS\s*\[\s*OM_TP__COUNT\s*\]", strip_c_comments(text)), \
        "OM_PP_ROWS must stay sized [OM_TP__COUNT]"
    last = last_table_row(text, "OM_PP_ROWS")
    assert last is not None, "OM_PP_ROWS initializer not found in csrc/tactical_move.c"
    # The row before the arc is the ground-flyer seen multiple (1.5, lo 1, hi OM_PP_MULT_HI). Without an arc row of
    # its own the last entry is that one and the arc reads 0 (spec: "without the row the arc defaults to 0").
    assert "OM_PP_FLYER_SEEN_DEFAULT" not in last, \
        f"the last OM_PP_ROWS entry is still the ground-flyer row, not the {ARC} row: {last}"
    assert "OM_PP_REAL" in last, f"the {ARC} row is a real: {last}"


def test_pp_contract_section_4_has_the_arc_row_then_count_67():
    rows = parse_param_table(DOC.read_text())
    by_name = {r["name"]: r for r in rows}
    assert ARC in by_name, f"{ARC} has no row in pp_contract.md section 4"
    row = by_name[ARC]
    assert row["value"] == BASE_COUNT_BEFORE_E0
    assert (row["kind"], row["default"], row["lo"], row["hi"]) == ("real", ARC_DEFAULT, ARC_LO, ARC_HI)
    assert rows[-1]["name"] == "OM_TP__COUNT" and rows[-1]["value"] == BASE_COUNT_BEFORE_E0 + 1
    assert [r["value"] for r in rows] == list(range(len(rows))), "section 4 numbers run 0..COUNT with no gap"


def test_pp_contract_section_4_names_and_order_equal_the_header_enum():
    assert [(r["name"], r["value"]) for r in parse_param_table(DOC.read_text())] == header_enum()


def test_conftest_mirror_matches_the_header_enum():
    mirror = conftest_enum_class(CONFTEST.read_text(), "OMTacParam")
    assert mirror is not None, "class OMTacParam not found in tests/csim/conftest.py"
    expected = {n[len("OM_TP_"):] if n != "OM_TP__COUNT" else "_COUNT": v for n, v in header_enum()}
    assert mirror == expected, (
        f"mirror differs from the header: missing {sorted(set(expected) - set(mirror))}, "
        f"extra {sorted(set(mirror) - set(expected))}, "
        f"moved {sorted(k for k in set(expected) & set(mirror) if expected[k] != mirror[k])}")
    assert mirror["FIRING_ARC_DEG"] == BASE_COUNT_BEFORE_E0 and mirror["_COUNT"] == BASE_COUNT_BEFORE_E0 + 1


# ---- the two stubbed symbols: header, signatures.toml, conftest bindings ----

@pytest.mark.parametrize("name,sig", [("om_roster_set_cone", SET_CONE_SIG), ("om_combat_can_engage", CAN_ENGAGE_SIG)])
def test_symbol_is_declared_once_in_the_header_with_the_spec_signature(name, sig):
    text = HEADER.read_text()
    assert count_declarations(text, name) == 1, f"{name}: expected exactly one declaration in csrc/ouroboros_sim.h"
    assert sig in squash(strip_c_comments(text)), f"{name}: header prototype differs from the spec: {sig}"


@pytest.mark.parametrize("name", sorted(NEW_SYMBOLS))
def test_symbol_has_one_exact_signatures_row_with_a_module(name):
    module, restype, params = NEW_SYMBOLS[name]
    rows = rows_named(table_symbols(), name)
    assert len(rows) == 1, f"{name}: expected exactly one signatures.toml row, found {len(rows)}"
    row = rows[0]
    assert row["module"] == module
    assert row["restype"] == restype
    assert [(p["name"], p["ctype"]) for p in row["params"]] == params


def test_signatures_meta_symbol_count_equals_the_number_of_rows():
    """The spec has E0 write 'the symbol count'. On main the meta is stale (767 against 796 rows: nothing reads
    it), so the count to write is the number of [[symbols]] rows after E0's two new rows, not 767 + 2."""
    data = table_symbols()
    names = [r["name"] for r in data["symbols"]]
    assert set(NEW_SYMBOLS) <= set(names), "the two new symbols must be among the counted rows"
    assert len(names) == len(set(names)), "a symbol is listed twice"
    assert data["meta"]["symbol_count"] == len(names), (
        f"[meta] symbol_count is {data['meta']['symbol_count']}, the table has {len(names)} [[symbols]] rows")


def test_signatures_meta_struct_count_equals_the_number_of_struct_rows():
    data = table_symbols()
    assert data["meta"]["struct_count"] == len(data.get("structs", []))


@pytest.mark.parametrize("name", sorted(NEW_SYMBOLS))
def test_conftest_binds_the_symbol_with_the_row_parameter_names(name):
    got = conftest_binding_params(CONFTEST.read_text(), name)
    assert got is not None, f"{name} is not bound in tests/csim/conftest.py (run sig_table --emit)"
    assert got == [p[0] for p in NEW_SYMBOLS[name][2]]


# ---- ABI and save-format consistency (never literals; see the module docstring) ----

def _abi_pins():
    """Every place that pins the ABI number: name -> int. Each must equal the header's."""
    pins = {}
    pins["csrc/ouroboros_sim.h OM_ABI_VERSION"] = define_value(HEADER.read_text(), "OM_ABI_VERSION")
    pins["signatures.toml [meta] abi_version"] = table_symbols()["meta"]["abi_version"]
    for label, path, pattern in [
        ("tests/csim/conftest.py EXPECTED_ABI_VERSION", CONFTEST, r"^EXPECTED_ABI_VERSION\s*=\s*(\d+)"),
        ("tests/specfactory/test_pp_contract.py EXPECTED_ABI", REPO / "tests/specfactory/test_pp_contract.py",
         r"^EXPECTED_ABI\s*=\s*(\d+)"),
        ("tests/csim/test_E02_S020_abi.py", REPO / "tests/csim/test_E02_S020_abi.py",
         r"om_abi_version\(\)\s*==\s*(\d+)"),
        ("tests/csim/test_VG_E_contract.py", REPO / "tests/csim/test_VG_E_contract.py",
         r"om_abi_version\(\)\s*==\s*(\d+)"),
        ("tests/csim/test_VG_E_ke5.py", REPO / "tests/csim/test_VG_E_ke5.py", r"om_abi_version\(\)\s*==\s*(\d+)"),
        ("docs/architecture.md hello frame", ARCH, r'"type":"hello","abi":(\d+)'),
        ("docs/architecture.md abi sentence", ARCH, r"`abi` is `om_abi_version\(\)` \((\d+) since"),
    ]:
        found = re.findall(pattern, path.read_text(), re.M)
        assert found, f"{label}: no ABI pin found by /{pattern}/ in {path.relative_to(REPO)}"
        for i, v in enumerate(found):
            pins[label if len(found) == 1 else f"{label} #{i + 1}"] = int(v)
    return pins


def test_every_abi_pin_equals_the_header_and_is_above_main_before_e0():
    pins = _abi_pins()
    header_abi = pins["csrc/ouroboros_sim.h OM_ABI_VERSION"]
    assert header_abi is not None
    assert header_abi > BASE_ABI_BEFORE_E0, (
        f"OM_ABI_VERSION is {header_abi}: E0 adds two symbols and a hashed setting, so it takes the next free number "
        f"above {BASE_ABI_BEFORE_E0}")
    bad = {k: v for k, v in pins.items() if v != header_abi}
    assert not bad, f"ABI pins that disagree with the header ({header_abi}): {bad}"


def test_transport_abi_pins_equal_the_header():
    """tests/transport pins the hello frame's abi. Not in the E0 owner row at the time of writing (see the report)."""
    header_abi = define_value(HEADER.read_text(), "OM_ABI_VERSION")
    found = {}
    for rel, pattern in [("tests/transport/test_pipe_shapes.py", r'\["abi"\]\s*==\s*(\d+)'),
                         ("tests/transport/test_pipe_vg_e.py", r'\["abi"\]\s*==\s*(\d+)')]:
        got = re.findall(pattern, (REPO / rel).read_text())
        assert got, f"{rel}: no abi pin found"
        found[rel] = {int(v) for v in got}
    assert all(v == {header_abi} for v in found.values()), f"header ABI {header_abi}, transport pins {found}"


def _save_pins():
    """Every place that pins the save-format number: name -> int. Each must equal om_internal.h's."""
    pins = {"csrc/om_internal.h OM_SAVE_FORMAT_VERSION": define_value(INTERNAL.read_text(), "OM_SAVE_FORMAT_VERSION"),
            "csrc/pipe/pipe_internal.h OM_PIPE_SAVE_FORMAT_VERSION":
                define_value(PIPE_INTERNAL.read_text(), "OM_PIPE_SAVE_FORMAT_VERSION")}
    gd = re.search(r"const\s+CURRENT_SAVE_VERSION\s*:=\s*(\d+)", LOAD_GAME_GD.read_text())
    assert gd, "scenes/load_game/load_game.gd: CURRENT_SAVE_VERSION not found"
    pins["scenes/load_game/load_game.gd CURRENT_SAVE_VERSION"] = int(gd.group(1))
    for label, rel, pattern in [
        ("tests/test_load_game_wrong_version.gd EXPECTED_VERSION", "tests/test_load_game_wrong_version.gd",
         r"const\s+EXPECTED_VERSION\s*:=\s*(\d+)"),
        ("tests/csim/test_E16_B5_save_version.py EXPECTED_VERSION", "tests/csim/test_E16_B5_save_version.py",
         r"^EXPECTED_VERSION\s*=\s*(\d+)"),
        ("tests/csim/test_E16_C2_save_version.py EXPECTED_VERSION", "tests/csim/test_E16_C2_save_version.py",
         r"^EXPECTED_VERSION\s*=\s*(\d+)"),
        ("tests/csim/test_E01_T3_contract.py version word", "tests/csim/test_E01_T3_contract.py",
         r'buf\[4:8\]\),\s*"little"\)\s*==\s*(\d+)'),
        ("tests/csim/test_VG_E_ke3.py version word", "tests/csim/test_VG_E_ke3.py",
         r'buf\[4:8\]\),\s*"little"\)\s*==\s*(\d+)'),
        ("tests/csim/test_VG_E_ke5.py version word", "tests/csim/test_VG_E_ke5.py",
         r'save\(klib, scene\(klib, kmake\)\), 4\)\[0\]\s*==\s*(\d+)'),
        ("tests/csim/test_VG_E_ke5.py sidecar", "tests/csim/test_VG_E_ke5.py",
         r'side\["format_version"\]\s*==\s*(\d+)'),
        ("docs/architecture.md visible-game heading", "docs/architecture.md",
         r"\(VG-K-e, ABI \d+, save format (\d+);"),
    ]:
        found = re.findall(pattern, (REPO / rel).read_text(), re.M)
        assert found, f"{label}: no save-format pin found by /{pattern}/ in {rel}"
        for i, v in enumerate(found):
            pins[label if len(found) == 1 else f"{label} #{i + 1}"] = int(v)
    return pins


def test_every_save_format_pin_equals_om_internal_and_is_above_main_before_e0():
    pins = _save_pins()
    declared = pins["csrc/om_internal.h OM_SAVE_FORMAT_VERSION"]
    assert declared is not None
    assert declared > BASE_SAVE_BEFORE_E0, (
        f"OM_SAVE_FORMAT_VERSION is {declared}: E0 writes one more setting into the movement slot, so it takes the "
        f"next free number above {BASE_SAVE_BEFORE_E0}")
    bad = {k: v for k, v in pins.items() if v != declared}
    assert not bad, f"save-format pins that disagree with om_internal.h ({declared}): {bad}"


# ---- built library ----

W = ctypes.c_void_p


@pytest.fixture(scope="module")
def lib():
    res = subprocess.run(["make", "-s", "libouroboros.so"], cwd=str(REPO), capture_output=True, text=True,
                         timeout=600)
    assert res.returncode == 0, (res.stderr or res.stdout)[-2000:]
    h = ctypes.CDLL(str(REPO / "libouroboros.so"))
    h.om_abi_version.argtypes, h.om_abi_version.restype = [], ctypes.c_uint32
    h.om_world_new.argtypes, h.om_world_new.restype = [ctypes.c_uint32, ctypes.c_uint64], W
    h.om_world_free.argtypes, h.om_world_free.restype = [W], None
    h.om_tactical_get_param.argtypes, h.om_tactical_get_param.restype = [W, ctypes.c_int], ctypes.c_double
    h.om_tactical_set_param.argtypes, h.om_tactical_set_param.restype = [W, ctypes.c_int, ctypes.c_double], ctypes.c_int
    h.om_roster_set_reach.argtypes, h.om_roster_set_reach.restype = \
        [W, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int
    h.om_unit_spawn.argtypes, h.om_unit_spawn.restype = \
        [W, ctypes.c_int, ctypes.c_int32, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_uint32
    h.om_unit_alive.argtypes, h.om_unit_alive.restype = [W, ctypes.c_uint32], ctypes.c_int
    P8 = ctypes.POINTER(ctypes.c_uint8)
    h.om_save_state_size.argtypes, h.om_save_state_size.restype = [W], ctypes.c_uint32
    h.om_save_state_write.argtypes, h.om_save_state_write.restype = [W, P8, ctypes.c_uint32], None
    h.om_load_state_read.argtypes, h.om_load_state_read.restype = [W, P8, ctypes.c_uint32], ctypes.c_int
    h.om_world_checksum_full.argtypes = [W, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint32]
    h.om_world_checksum_full.restype = ctypes.c_uint64
    h.om_checksum_section_count.argtypes, h.om_checksum_section_count.restype = [], ctypes.c_uint32
    h.om_checksum_section_name.argtypes, h.om_checksum_section_name.restype = [ctypes.c_uint32], ctypes.c_char_p
    return h


@pytest.fixture
def world(lib):
    made = []

    def make(seed=1):
        w = lib.om_world_new(1, seed)
        assert w, "om_world_new returned NULL"
        made.append(w)
        return w

    yield make
    for w in made:
        lib.om_world_free(w)


def arc_member():
    """The enum value of OM_TP_FIRING_ARC_DEG from the header; a plain failure (not a fixture error) when missing."""
    values = dict(header_enum())
    assert ARC in values, f"{ARC} is not a member of om_tac_param in csrc/ouroboros_sim.h"
    return values[ARC]


def _bound(lib, name, argtypes, restype):
    try:
        fn = getattr(lib, name)
    except AttributeError:
        pytest.fail(f"{name} is not exported by the built library")
    fn.argtypes, fn.restype = argtypes, restype
    return fn


def _save(lib, w):
    n = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    lib.om_save_state_write(w, buf, n)
    return buf, n


def _movement_section(lib, w):
    """The movement section of checksum_full (the 'net section hash' the setting is hashed into)."""
    names = [lib.om_checksum_section_name(i).decode() for i in range(lib.om_checksum_section_count())]
    assert "movement" in names, f"no movement section in {names}"
    sections = (ctypes.c_uint64 * 32)()
    whole = lib.om_world_checksum_full(w, sections, 32)
    return sections[names.index("movement")], whole


def test_control_leash_still_reads_200_and_the_existing_defaults_are_unchanged(lib, world):
    """Control, green on main: adding a row must not move any existing default. The documented defaults of
    every pre-existing member are read from section 4 and compared with the built library."""
    w = world()
    assert lib.om_tactical_get_param(w, 6) == 200.0, "OM_TP_ATTACK_MOVE_LEASH (member 6) no longer defaults to 200"
    rows = [r for r in parse_param_table(DOC.read_text()) if r["name"] not in ("OM_TP__COUNT", ARC)]
    assert len(rows) >= BASE_COUNT_BEFORE_E0
    for r in rows:
        assert lib.om_tactical_get_param(w, r["value"]) == pytest.approx(r["default"], abs=1e-12), r["name"]


def test_library_reports_the_header_abi(lib):
    assert lib.om_abi_version() == define_value(HEADER.read_text(), "OM_ABI_VERSION")


def test_arc_defaults_to_360(lib, world):
    """Red on main for a stated reason: the member does not exist, so the read answers -1 (or the fixture fails)."""
    arc = arc_member()
    assert lib.om_tactical_get_param(world(), arc) == ARC_DEFAULT


def test_arc_accepts_the_bounds_and_reads_back(lib, world):
    arc = arc_member()
    w = world()
    for v in (ARC_LO, 120.0, 90.5, ARC_HI):  # real: a fraction is fine
        assert lib.om_tactical_set_param(w, arc, v) == 0, v
        assert lib.om_tactical_get_param(w, arc) == v, v


@pytest.mark.parametrize("bad", [9.999, 0.0, -1.0, 360.001, 720.0, math.nan, math.inf])
def test_arc_refuses_a_value_outside_10_to_360_and_changes_nothing(lib, world, bad):
    arc = arc_member()
    w = world()
    assert lib.om_tactical_set_param(w, arc, 120.0) == 0, "control: an in-range set must be accepted"
    assert lib.om_tactical_get_param(w, arc) == 120.0
    assert lib.om_tactical_set_param(w, arc, bad) != 0, f"{bad} was accepted"
    assert lib.om_tactical_get_param(w, arc) == 120.0, f"a refused set of {bad} changed the value"


def test_arc_survives_save_and_load_and_the_resave_is_byte_identical(lib, world):
    """The setting sits in the movement save slot: set 120, save, load into a fresh world, read 120."""
    arc = arc_member()
    src = world(seed=3)
    assert lib.om_tactical_set_param(src, arc, 120.0) == 0
    buf, n = _save(lib, src)
    dst = world(seed=3)
    assert lib.om_tactical_get_param(dst, arc) == ARC_DEFAULT, "control: a fresh world reads 360 before the load"
    assert lib.om_load_state_read(dst, buf, n) == 0
    assert lib.om_tactical_get_param(dst, arc) == 120.0, "the arc was not saved (or not loaded)"
    again, n2 = _save(lib, dst)
    assert n2 == n and bytes(again) == bytes(buf), "save, load, save is not byte identical"


def test_saved_version_word_equals_the_declared_save_format(lib, world):
    buf, _ = _save(lib, world(seed=4))
    word = int.from_bytes(bytes(buf[4:8]), "little")
    assert word == define_value(INTERNAL.read_text(), "OM_SAVE_FORMAT_VERSION")
    assert word > BASE_SAVE_BEFORE_E0


def test_arc_is_in_the_net_hash_and_back_to_360_restores_it(lib, world):
    """Hashed into the movement section: 120 differs from 360, 360 again equals the first read, and a second world
    set to 120 agrees with the first (so the difference is the arc, not noise)."""
    arc = arc_member()
    w, w2 = world(seed=5), world(seed=5)
    assert lib.om_tactical_set_param(w, arc, ARC_DEFAULT) == 0   # touch the movement state at the default
    base_sec, base_whole = _movement_section(lib, w)
    assert lib.om_tactical_set_param(w, arc, 120.0) == 0
    sec120, whole120 = _movement_section(lib, w)
    assert sec120 != base_sec, "the movement section did not change with the arc"
    assert whole120 != base_whole, "the whole-world full checksum did not change with the arc"
    assert lib.om_tactical_set_param(w2, arc, 120.0) == 0
    assert _movement_section(lib, w2) == (sec120, whole120), "control: the same arc on the same seed must hash the same"
    assert lib.om_tactical_set_param(w, arc, ARC_DEFAULT) == 0
    assert _movement_section(lib, w) == (base_sec, base_whole)


# ---- the stubs: not built until LAB-REV2-E2 (E2 retires these two tests) ----

def test_set_cone_stub_returns_not_built(lib, world):
    """Red on main: the symbol is missing. Green on the E0 tree: the stub answers -1 for a call the real body (E2)
    would accept (type 0, range 100, half-angle 45, share 1). E2 replaces the stub and retires this test."""
    fn = _bound(lib, "om_roster_set_cone", [W, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double],
                ctypes.c_int)
    w = world()
    assert lib.om_roster_set_reach(w, 0, 1, 1) == 0, "control: the world accepts a roster call for type 0"
    assert fn(w, 0, 100.0, 45.0, 1.0) == NOT_BUILT


def test_can_engage_stub_returns_not_built(lib, world):
    """Two living enemies 100 apart: the real body (E2) answers 0, 1, 2, 3, 4 or 5 for them; the stub answers -1.
    E2 replaces the stub and retires this test."""
    fn = _bound(lib, "om_combat_can_engage", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int)
    w = world()
    a = lib.om_unit_spawn(w, 0, 0, 0.0, 0.0, 0)
    b = lib.om_unit_spawn(w, 0, 1, 100.0, 0.0, 0)
    assert a != 0 and b != 0 and a != b, "control: two units spawned"
    assert lib.om_unit_alive(w, a) and lib.om_unit_alive(w, b), "control: both alive"
    assert fn(w, a, b) == NOT_BUILT
    assert fn(w, 0xFFFFFFF0, b) == NOT_BUILT, "an unknown id is -1 in the stub as in the real body"
