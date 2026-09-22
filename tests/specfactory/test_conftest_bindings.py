# spec: docs/northstar/plans/briefs/2026-09-22-two-day-push.md decision 1 and the F1b row
"""The freeze's own control over the generated bindings in tests/csim/conftest.py
and the generated declarations in csrc/ouroboros_sim.h:

  - every lib.om_*(...) call site in tests/csim that passes keyword arguments
    names only parameters its binding declares, and that binding carries a
    paramflags prototype (kw=True), so no keyword is dropped by raw ctypes;
  - regenerating from the committed table reproduces the committed header and
    conftest byte for byte, and the pre-existing E-03/E-04/E-05 declarations and
    the three hand-written binders are untouched by generation;
  - every [[symbols]] row the generator can map has exactly one declaration in
    the header and exactly one binding in conftest;
  - every generated struct mirror lists its fields in the header's order (a
    swapped pair is caught, proven by a positive control).

Nothing here imports tests/csim/conftest.py (it builds the libraries on import);
everything is read statically."""
import ast
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SIG_TABLE = REPO / "scripts" / "specfactory" / "sig_table.py"
HEADER = REPO / "csrc" / "ouroboros_sim.h"
CONFTEST = REPO / "tests" / "csim" / "conftest.py"
TABLE = REPO / "docs" / "northstar" / "spec_factory" / "signatures.toml"
TESTS_DIR = REPO / "tests" / "csim"

HANDLE_NAMES = {"lib", "dbg", "handle"}
CONFTEST_START = "# ---- generated from signatures.toml ----"
CONFTEST_END = "# ---- end generated ----"
HEADER_BLOCK_RE = re.compile(
    r"/\* ---- generated from signatures\.toml: (?P<mod>[^ ]+) ---- \*/\n.*?"
    r"/\* ---- end generated: (?P=mod) ---- \*/\n\n",
    re.S,
)
LEGACY_BINDERS = ("_bind_e03", "_bind_e04", "_bind_e05")


def _generated_region(conftest_text: str) -> str:
    return conftest_text[conftest_text.index(CONFTEST_START):conftest_text.index(CONFTEST_END)]


def _bindings(conftest_text: str) -> dict[str, dict]:
    """symbol -> {"params": [...], "kw": bool, "count": n} from every _bind(lib, "name", ...) call."""
    out: dict[str, dict] = {}
    for node in ast.walk(ast.parse(conftest_text)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_bind"):
            continue
        name = node.args[1].value
        params = [elt.value for elt in node.args[4].elts]
        kw = any(k.arg == "kw" and getattr(k.value, "value", False) is True for k in node.keywords)
        entry = out.setdefault(name, {"params": params, "kw": kw, "count": 0})
        entry["count"] += 1
    return out


def _keyword_call_sites() -> list[tuple[str, int, str, list[str]]]:
    sites = []
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            if not (isinstance(node.func.value, ast.Name) and node.func.value.id in HANDLE_NAMES):
                continue
            if not node.func.attr.startswith("om_") or not node.keywords:
                continue
            sites.append((str(path.relative_to(REPO)), node.lineno, node.func.attr, [k.arg for k in node.keywords]))
    return sites


def _report() -> dict:
    proc = subprocess.run([sys.executable, str(SIG_TABLE), "--report", "--json"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def _header_struct_fields(header_text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"typedef struct (om_\w+) \{\n(.*?)\n\} \1;", header_text, re.S):
        fields = []
        for line in m.group(2).splitlines():
            fm = re.match(r"\s*[\w ]+?\s\**(\w+)(?:\[\d+\])?;", line)
            if fm:
                fields.append(fm.group(1))
        out[m.group(1)] = fields
    return out


def _mirror_fields(conftest_text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for node in ast.parse(conftest_text).body:
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and any(getattr(t, "id", "") == "_fields_" for t in stmt.targets):
                out[node.name] = [elt.elts[0].value for elt in stmt.value.elts]
    return out


def _struct_c_names(conftest_text: str) -> dict[str, str]:
    for node in ast.parse(conftest_text).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "STRUCT_C_NAMES" for t in node.targets):
            return {k.value: v.value for k, v in zip(node.value.keys, node.value.values)}
    return {}


def _mirror_order_mismatches(header_text: str, conftest_text: str) -> list[str]:
    header_fields = _header_struct_fields(header_text)
    mirror_fields = _mirror_fields(conftest_text)
    mismatches = []
    for py_name, c_name in _struct_c_names(conftest_text).items():
        if py_name not in mirror_fields:
            continue
        if header_fields.get(c_name) != mirror_fields[py_name]:
            mismatches.append(f"{py_name} ({c_name}): header {header_fields.get(c_name)} vs mirror {mirror_fields[py_name]}")
    return mismatches


def test_every_keyword_call_site_names_a_bound_parameter():
    bindings = _bindings(CONFTEST.read_text())
    problems = []
    sites = _keyword_call_sites()
    assert sites, "the walk found no keyword call sites; the detector itself is broken"
    for path, line, name, kwargs in sites:
        binding = bindings.get(name)
        if binding is None:
            problems.append(f"{path}:{line} {name}({', '.join(kwargs)}): no generated binding")
            continue
        if not binding["kw"]:
            problems.append(f"{path}:{line} {name}: binding has no paramflags prototype (kw=True), keywords would be dropped")
        unknown = [k for k in kwargs if k not in binding["params"]]
        if unknown:
            problems.append(f"{path}:{line} {name}: keyword(s) {unknown} not in binding params {binding['params']}")
    assert not problems, "\n".join(problems)


def test_every_mappable_table_row_has_one_declaration_and_one_binding():
    report = _report()
    blocked = {b["name"] for b in report["blocked"]}
    table = tomllib.load(TABLE.open("rb"))
    header = re.sub(r"/\*.*?\*/", "", HEADER.read_text(), flags=re.S)
    bindings = _bindings(CONFTEST.read_text())
    problems = []
    for row in table["symbols"]:
        name = row["name"]
        if name in blocked or row.get("internal"):
            continue
        decls = len(re.findall(r"\b" + re.escape(name) + r"\s*\(", header))
        if decls != 1:
            problems.append(f"{name}: {decls} declarations in the header")
        count = bindings.get(name, {}).get("count", 0)
        if count != 1:
            problems.append(f"{name}: {count} bindings in conftest")
    assert not problems, "\n".join(problems)
    assert len(blocked) <= 2, f"blocked rows grew: {sorted(blocked)}"


def test_regeneration_reproduces_committed_files_and_leaves_legacy_blocks_untouched(tmp_path):
    project = tmp_path / "proj"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "docs" / "northstar" / "spec_factory").mkdir(parents=True)
    for c_file in (REPO / "csrc").glob("*.c"):
        shutil.copy(c_file, project / "csrc" / c_file.name)
    shutil.copy(REPO / "csrc" / "om_internal.h", project / "csrc" / "om_internal.h")
    shutil.copy(TABLE, project / "docs" / "northstar" / "spec_factory" / "signatures.toml")

    committed_header = HEADER.read_text()
    committed_conftest = CONFTEST.read_text()
    stripped_header = HEADER_BLOCK_RE.sub("", committed_header)
    assert stripped_header != committed_header, "the committed header carries no generated block"
    start = committed_conftest.index(CONFTEST_START) + len(CONFTEST_START)
    end = committed_conftest.index(CONFTEST_END)
    stripped_conftest = committed_conftest[:start] + "\n" + committed_conftest[end:]
    (project / "csrc" / "ouroboros_sim.h").write_text(stripped_header)
    (project / "tests" / "csim" / "conftest.py").write_text(stripped_conftest)

    proc = subprocess.run([sys.executable, str(SIG_TABLE), "--project", str(project), "--emit"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after_header = (project / "csrc" / "ouroboros_sim.h").read_text()
    after_conftest = (project / "tests" / "csim" / "conftest.py").read_text()
    assert after_header == committed_header
    assert after_conftest == committed_conftest
    assert HEADER_BLOCK_RE.sub("", after_header) == stripped_header, "text outside the generated blocks changed"

    def legacy_sources(text):
        tree = ast.parse(text)
        return {node.name: ast.get_source_segment(text, node)
                for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in LEGACY_BINDERS}

    before_binders = legacy_sources(stripped_conftest)
    after_binders = legacy_sources(after_conftest)
    assert set(before_binders) == set(LEGACY_BINDERS)
    assert before_binders == after_binders

    legacy_decl_re = re.compile(r"^[^\n/]*\b(om_[a-z0-9_]+)\s*\([^;]*;", re.M)
    before_decls = {m.group(1): m.group(0) for m in legacy_decl_re.finditer(stripped_header)}
    after_decls = {m.group(1): m.group(0) for m in legacy_decl_re.finditer(HEADER_BLOCK_RE.sub("", after_header))}
    assert before_decls == after_decls
    assert len(before_decls) >= 84


def test_struct_mirrors_follow_header_field_order_with_positive_control():
    header = HEADER.read_text()
    conftest = CONFTEST.read_text()
    mismatches = _mirror_order_mismatches(header, conftest)
    assert not mismatches, "\n".join(mismatches)
    checked = [n for n in _struct_c_names(conftest) if n in _mirror_fields(conftest)]
    assert len(checked) >= 23

    swapped = header.replace(
        "typedef struct om_absorption_record {\n    uint64_t tick;\n    int32_t absorbed_faction;",
        "typedef struct om_absorption_record {\n    int32_t absorbed_faction;\n    uint64_t tick;",
    )
    assert swapped != header, "positive control could not plant the swap"
    assert any("om_absorption_record" in m for m in _mirror_order_mismatches(swapped, conftest)), \
        "a swapped field pair in the header went unnoticed"
