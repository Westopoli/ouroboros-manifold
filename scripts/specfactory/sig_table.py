#!/usr/bin/env python3
"""Emits the freeze artifacts from docs/northstar/spec_factory/signatures.toml
(decision 1, docs/northstar/plans/briefs/2026-09-22-two-day-push.md, F1b):

  1. csrc/ouroboros_sim.h: one block per module between
     `/* ---- generated from signatures.toml: <module> ---- */` and
     `/* ---- end generated: <module> ---- */` holding a declaration for every
     [[symbols]] row of that module not already declared elsewhere in the
     header, preceded by a `structs` block with a typedef for every [[structs]]
     row not already typedef'd. Existing declarations are never touched.
  2. tests/csim/conftest.py: between `# ---- generated from signatures.toml ----`
     and `# ---- end generated ----`, struct mirrors (ctypes.Structure, fields
     in table order), `_bind_eNN(lib)` per epic (each symbol bound once, in the
     lowest epic that names it; rows with `kwargs` get a paramflags prototype
     so keyword calls work) and the `wrapper` adapters.
  3. csrc/<module>.c: a `/* STUB */` body for every row whose module it is and
     that no csrc/*.c defines. Existing files are extended before a trailing
     `/* ---- end generated stubs ---- */`; new files take csrc/collision.c's
     header shape.

A row whose C type cannot be mapped (an enum or struct the header and the
table both lack) is left out of all three and listed under `blocked`, never
guessed. A second --emit changes nothing.

Usage:
    scripts/specfactory/sig_table.py --emit [--project DIR] [--table PATH] [--json]
    scripts/specfactory/sig_table.py --check   (exit 1 when --emit would change a file)
    scripts/specfactory/sig_table.py --report  (the counts and blocked rows only)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import card_lint as cl  # noqa: E402  (find_function_span: the one C-definition scanner)

DEFAULT_PROJECT = Path(__file__).resolve().parents[2]
TABLE_REL = Path("docs/northstar/spec_factory/signatures.toml")
HEADER_REL = Path("csrc/ouroboros_sim.h")
INTERNAL_REL = Path("csrc/om_internal.h")
CONFTEST_REL = Path("tests/csim/conftest.py")

SCALAR_CTYPES = {
    "uint32_t": "ctypes.c_uint32",
    "int32_t": "ctypes.c_int32",
    "uint64_t": "ctypes.c_uint64",
    "int64_t": "ctypes.c_int64",
    "uint8_t": "ctypes.c_uint8",
    "int8_t": "ctypes.c_int8",
    "uint16_t": "ctypes.c_uint16",
    "int16_t": "ctypes.c_int16",
    "double": "ctypes.c_double",
    "float": "ctypes.c_float",
    "int": "ctypes.c_int",
}
RET_DEFAULT = {k: ("0.0" if k in ("double", "float") else "0") for k in SCALAR_CTYPES}

HEADER_BLOCK_RE = re.compile(
    r"/\* ---- generated from signatures\.toml: (?P<mod>[^ ]+) ---- \*/\n.*?"
    r"/\* ---- end generated: (?P=mod) ---- \*/\n\n",
    re.S,
)
CONFTEST_START = "# ---- generated from signatures.toml ----"
CONFTEST_END = "# ---- end generated ----"
STUB_START = "/* ---- generated stubs from signatures.toml ---- */"
STUB_END = "/* ---- end generated stubs ---- */"

WRAPPERS = {
    "ids_list_or_single": "_wrap_ids_list_or_single",
    "ids_list_optional_target": "_wrap_ids_list_optional_target",
    "optional_trailing_null": "_wrap_optional_trailing_null",
    "out_pair": "_wrap_out_pair",
}


# ---- names and types ----

def camel_to_snake(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def is_class_name(name: str) -> bool:
    return re.match(r"^O[Mm][A-Z]", name) is not None


def c_struct_name(name: str) -> str:
    return camel_to_snake(name) if is_class_name(name) else name


def snake_to_class(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def parse_ctype(ctype: str) -> tuple[str, bool, int]:
    """'const om_world*' -> ('om_world', const=True, pointer_depth=1)."""
    t = ctype.strip()
    depth = 0
    while t.endswith("*"):
        t = t[:-1].rstrip()
        depth += 1
    const = t.startswith("const ")
    if const:
        t = t[len("const "):].strip()
    return t, const, depth


def strip_c_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


class Types:
    """What the header already knows, plus what the table adds."""

    def __init__(self, header_text: str):
        stripped = strip_c_comments(header_text)
        self.declared = set(re.findall(r"\b(om_[a-z0-9_]+)\s*\(", stripped))
        self.enums = set(re.findall(r"typedef\s+enum\s*\{[^}]*\}\s*(om_[a-z0-9_]+)\s*;", stripped, re.S))
        self.structs = set(re.findall(r"typedef\s+struct\s+\w*\s*\{[^}]*\}\s*(om_[a-z0-9_]+)\s*;", stripped, re.S))
        self.structs |= set(re.findall(r"typedef\s+struct\s+om_\w+\s+(om_[a-z0-9_]+)\s*;", stripped))
        self.generated_structs: set[str] = set()

    def known_struct(self, base: str) -> bool:
        return base in self.structs or base in self.generated_structs

    def kind(self, base: str) -> str | None:
        if base in SCALAR_CTYPES:
            return "scalar"
        if base == "void":
            return "void"
        if base == "char":
            return "char"
        if base in self.enums:
            return "enum"
        if self.known_struct(base):
            return "struct"
        return None


def c_base(base: str) -> str:
    return c_struct_name(base) if is_class_name(base) else base


def render_c_type(ctype: str) -> str | None:
    base, const, depth = parse_ctype(ctype)
    base = c_base(base)
    text = ("const " if const else "") + base
    return text + ("*" * depth)


def render_c_param(ctype: str, name: str) -> str:
    base, const, depth = parse_ctype(ctype)
    base = c_base(base)
    text = ("const " if const else "") + base
    if depth:
        return f"{text} {'*' * depth}{name}"
    return f"{text} {name}"


def ctypes_for(ctype: str, types: Types) -> str | None:
    base, _const, depth = parse_ctype(ctype)
    base = c_base(base)
    kind = types.kind(base)
    if kind is None or depth > 1:
        return None
    if depth == 1:
        if base == "om_world":
            return "W"
        if kind == "scalar":
            return f"P({SCALAR_CTYPES[base]})"
        if kind == "char":
            return "ctypes.c_char_p"
        if kind == "void":
            return "V"
        if kind == "enum":
            return "P(ctypes.c_int)"
        return "V"
    if kind == "scalar":
        return SCALAR_CTYPES[base]
    if kind == "void":
        return "None"
    if kind == "enum":
        return "ctypes.c_int"
    return None


def ret_default(ctype: str, types: Types) -> str | None:
    base, _const, depth = parse_ctype(ctype)
    if depth == 1 and base == "char":
        # The empty string, not NULL: ctypes maps a NULL char* to None and the
        # tests' ctypes.string_at(None) then reads address 0, which kills the
        # whole pytest process (two E-09 tests did exactly that at the freeze).
        return '""'
    if depth:
        return "NULL"
    if base == "void":
        return None
    if types.kind(c_base(base)) == "enum":
        return "0"
    return RET_DEFAULT.get(base)


def field_types(ctype: str, types: Types) -> tuple[str, str] | None:
    """('char name[32]' style C fragment via (c_type, suffix), ctypes text) or None."""
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?$", ctype.strip())
    if not m:
        return None
    base, count = m.group(1), m.group(2)
    if base == "char":
        if not count:
            return None
        return ("char", f"[{count}]", f"ctypes.c_char * {count}")
    if base in SCALAR_CTYPES:
        py = SCALAR_CTYPES[base]
    else:
        cname = c_base(base)
        if not types.known_struct(cname):
            return None
        base = cname
        py = base if not is_class_name(m.group(1)) else m.group(1)
        py = STRUCT_PY_NAMES.get(base, py)
    if count:
        return (base, f"[{count}]", f"{py} * {count}")
    return (base, "", py)


STRUCT_PY_NAMES: dict[str, str] = {}


# ---- table ----

def load_table(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def epic_num(epic: str) -> int:
    return int(re.search(r"(\d+)", epic).group(1))


def resolve_structs(table: dict, types: Types) -> tuple[list[dict], list[dict]]:
    """Collapse the [[structs]] rows to one C struct per C name. Returns
    (structs, blocked): each struct is {c_name, py_name, aliases, fields:[(name, c_type, suffix, py_type)]}."""
    by_c: dict[str, dict] = {}
    blocked: list[dict] = []
    rows = table.get("structs", [])
    for row in rows:
        cname = c_struct_name(row["name"])
        entry = by_c.setdefault(cname, {"c_name": cname, "rows": [], "names": []})
        entry["rows"].append(row)
        entry["names"].append(row["name"])
    for cname, entry in by_c.items():
        first = [(f["name"], f["ctype"]) for f in entry["rows"][0]["fields"]]
        for row in entry["rows"][1:]:
            if [(f["name"], f["ctype"]) for f in row["fields"]] != first:
                blocked.append({"name": cname, "module": "structs",
                                "reason": f"rows {entry['names']} disagree on fields"})
                entry["conflict"] = True
                break
        class_names = [n for n in entry["names"] if is_class_name(n)]
        entry["py_name"] = class_names[0] if class_names else snake_to_class(cname)
        entry["aliases"] = [n for n in entry["names"] if n != entry["py_name"]]
        STRUCT_PY_NAMES[cname] = entry["py_name"]
    # dependency order: a struct that embeds another comes after it
    ordered: list[dict] = []
    pending = {c: e for c, e in by_c.items() if not e.get("conflict")}
    for cname in pending:
        types.generated_structs.add(cname)
    progress = True
    while pending and progress:
        progress = False
        for cname in sorted(pending):
            entry = pending[cname]
            fields = []
            ok = True
            deps_ready = True
            for f in entry["rows"][0]["fields"]:
                ft = field_types(f["ctype"], types)
                if ft is None:
                    ok = False
                    blocked.append({"name": cname, "module": "structs",
                                    "reason": f"field {f['name']} has unknown type {f['ctype']}"})
                    break
                base = ft[0]
                if base in pending and base != cname:
                    deps_ready = False
                    break
                fields.append((f["name"], ft[0], ft[1], ft[2]))
            if not ok:
                types.generated_structs.discard(cname)
                del pending[cname]
                progress = True
                break
            if not deps_ready:
                continue
            entry["fields"] = fields
            ordered.append(entry)
            del pending[cname]
            progress = True
    for cname in pending:
        types.generated_structs.discard(cname)
        blocked.append({"name": cname, "module": "structs", "reason": "circular field dependency"})
    return ordered, blocked


C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double",
    "else", "enum", "extern", "float", "for", "goto", "if", "inline", "int", "long",
    "register", "restrict", "return", "short", "signed", "sizeof", "static", "struct",
    "switch", "typedef", "union", "unsigned", "void", "volatile", "while",
}


def sanitize_param_names(row: dict) -> tuple[list[str], list[dict]]:
    """Positional-only parameter names are cosmetic (table header, D-F1), so a
    name C rejects -- a keyword, or a repeat inside one declaration -- becomes
    p<index>; the rename is reported so the table can be corrected. A kwargs
    row keeps its names exactly (a rename there would break keyword calls)."""
    seen: set[str] = set()
    names: list[str] = []
    renamed: list[dict] = []
    kwargs = set(row.get("kwargs") or [])
    for i, p in enumerate(row["params"]):
        name = p["name"]
        invalid = name in C_KEYWORDS or name in seen or not re.match(r"^[A-Za-z_]\w*$", name)
        if invalid and name not in kwargs:
            new = f"p{i}"
            renamed.append({"name": row["name"], "param": name, "renamed_to": new, "index": i})
            name = new
        seen.add(name)
        names.append(name)
    return names, renamed


def resolve_symbols(table: dict, types: Types) -> tuple[list[dict], list[dict], list[dict]]:
    ok: list[dict] = []
    blocked: list[dict] = []
    renamed_all: list[dict] = []
    for row in table.get("symbols", []):
        reason = None
        c_ret = render_c_type(row["restype"])
        py_ret = ctypes_for(row["restype"], types)
        if py_ret is None:
            reason = f"restype {row['restype']} has no C definition"
        names, renamed = sanitize_param_names(row)
        if len(set(names)) != len(names):
            reason = reason or f"kwargs row repeats a parameter name: {names}"
        params = []
        for p, name in zip(row["params"], names):
            py = ctypes_for(p["ctype"], types)
            if py is None:
                reason = reason or f"param {p['name']} has unmappable ctype {p['ctype']}"
                break
            params.append({"name": name, "ctype": p["ctype"], "py": py})
        if row["restype"] != "void" and ret_default(row["restype"], types) is None and reason is None:
            reason = f"restype {row['restype']} has no stub default"
        if reason:
            blocked.append({"name": row["name"], "module": row["module"], "reason": reason})
            continue
        renamed_all.extend(renamed)
        ok.append({
            "name": row["name"], "module": row["module"], "restype": row["restype"],
            "c_ret": c_ret, "py_ret": py_ret, "params": params,
            "ret_default": ret_default(row["restype"], types),
            "epics": sorted(row["epics"], key=epic_num),
            "kwargs": row.get("kwargs"), "wrapper": row.get("wrapper"),
        })
    return ok, blocked, renamed_all


# ---- header ----

def render_declaration(sym: dict) -> str:
    params = ", ".join(render_c_param(p["ctype"], p["name"]) for p in sym["params"]) or "void"
    return f"{render_c_param(sym['restype'], sym['name'])}({params});"


def render_struct_typedef(st: dict) -> str:
    lines = [f"typedef struct {st['c_name']} {{"]
    for name, ctype, suffix, _py in st["fields"]:
        lines.append(f"    {ctype} {name}{suffix};")
    lines.append(f"}} {st['c_name']};")
    return "\n".join(lines)


def header_block(module: str, body: str) -> str:
    return (f"/* ---- generated from signatures.toml: {module} ---- */\n"
            f"{body}\n"
            f"/* ---- end generated: {module} ---- */")


def strip_header_blocks(text: str) -> str:
    return HEADER_BLOCK_RE.sub("", text)


def render_header(base_text: str, structs: list[dict], symbols: list[dict], types: Types) -> tuple[str, int, int]:
    blocks: list[str] = []
    new_structs = [st for st in structs if st["c_name"] not in types.structs]
    if new_structs:
        blocks.append(header_block("structs", "\n\n".join(render_struct_typedef(st) for st in new_structs)))
    header_added = 0
    modules = sorted({s["module"] for s in symbols})
    for module in modules:
        decls = [render_declaration(s) for s in symbols
                 if s["module"] == module and s["name"] not in types.declared]
        if not decls:
            continue
        header_added += len(decls)
        blocks.append(header_block(module, "\n".join(decls)))
    if not blocks:
        return base_text, 0, 0
    region = "\n\n".join(blocks) + "\n\n"
    at = base_text.rindex("#ifdef __cplusplus")
    return base_text[:at] + region + base_text[at:], header_added, len(new_structs)


# ---- conftest ----

def existing_mirror_names(conftest_text: str) -> set[str]:
    return set(re.findall(r"^class (\w+)\(ctypes\.Structure\)", conftest_text, re.M))


def render_mirror(st: dict) -> str:
    lines = [f"class {st['py_name']}(ctypes.Structure):", "    _fields_ = ["]
    for name, _ctype, _suffix, py in st["fields"]:
        lines.append(f'        ("{name}", {py}),')
    lines.append("    ]")
    return "\n".join(lines)


def render_bind_line(sym: dict) -> str:
    args = "[" + ", ".join(p["py"] for p in sym["params"]) + "]"
    names = "(" + ", ".join(f'"{p["name"]}"' for p in sym["params"]) + ("," if len(sym["params"]) == 1 else "") + ")"
    kw = ", kw=True" if sym.get("kwargs") else ""
    return f'    _bind(lib, "{sym["name"]}", {args}, {sym["py_ret"]}, {names}{kw})'


def render_conftest_region(structs: list[dict], symbols: list[dict], existing_mirrors: set[str]) -> tuple[str, int]:
    out = [
        CONFTEST_START,
        "# Written by scripts/specfactory/sig_table.py --emit from",
        "# docs/northstar/spec_factory/signatures.toml; edit the table, not this region.",
        "# Struct pointers bind as c_void_p (V): the story tests carry their own",
        "# ctypes.Structure classes, so a typed POINTER() would reject them. The",
        "# mirrors below serve the wrappers and future tests; STRUCT_C_NAMES maps",
        "# each Python name to its C typedef.",
        "",
    ]
    for st in structs:
        if st["py_name"] not in existing_mirrors:
            out.append(render_mirror(st))
            out.append("")
            out.append("")
        for alias in st["aliases"]:
            out.append(f"{alias} = {st['py_name']}")
            out.append("")
            out.append("")
    out.append("STRUCT_C_NAMES = {")
    for st in structs:
        for py in [st["py_name"], *st["aliases"]]:
            out.append(f'    "{py}": "{st["c_name"]}",')
    out.append("}")
    out.append("")
    out.append("")

    by_epic: dict[str, list[dict]] = {}
    for sym in symbols:
        by_epic.setdefault(sym["epics"][0], []).append(sym)
    binders = []
    bindings = 0
    for epic in sorted(by_epic, key=epic_num):
        tag = f"e{epic_num(epic):02d}"
        binders.append(f"_bind_{tag}")
        out.append(f"def _bind_{tag}(lib):")
        out.append(f'    if getattr(lib, "_{tag}_bound", False):')
        out.append("        return")
        out.append("    P = ctypes.POINTER")
        out.append("    V = ctypes.c_void_p")
        out.append("    W = OMWorldP")
        for sym in sorted(by_epic[epic], key=lambda s: s["name"]):
            out.append(render_bind_line(sym))
            bindings += 1
            if sym.get("wrapper"):
                out.append(f'    {WRAPPERS[sym["wrapper"]]}(lib, "{sym["name"]}")')
        out.append(f"    lib._{tag}_bound = True")
        out.append("")
        out.append("")
    out.append(f"_GENERATED_BINDERS = ({', '.join(binders)}{',' if len(binders) == 1 else ''})")
    out.append(CONFTEST_END)
    return "\n".join(out), bindings


def render_conftest(text: str, structs: list[dict], symbols: list[dict]) -> tuple[str, int]:
    start = text.index(CONFTEST_START)
    end = text.index(CONFTEST_END) + len(CONFTEST_END)
    outside = text[:start] + text[end:]
    region, bindings = render_conftest_region(structs, symbols, existing_mirror_names(outside))
    return text[:start] + region + text[end:], bindings


# ---- skeletons ----

def extract_private_layout(om_internal_text: str) -> str:
    start_idx = om_internal_text.index("#define OM_MAX_NEIGHBORS")
    struct_kw = om_internal_text.index("struct om_world {")
    i = om_internal_text.index("{", struct_kw)
    depth, j = 0, i
    while j < len(om_internal_text):
        if om_internal_text[j] == "{":
            depth += 1
        elif om_internal_text[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    end_idx = om_internal_text.index(";", j) + 1
    return om_internal_text[start_idx:end_idx].rstrip("\n")


def render_stub(sym: dict) -> str:
    params = ", ".join(render_c_param(p["ctype"], p["name"]) for p in sym["params"]) or "void"
    lines = [f"{render_c_param(sym['restype'], sym['name'])}({params}) {{", "    /* STUB */"]
    voids = " ".join(f"(void){p['name']};" for p in sym["params"])
    if voids:
        lines.append(f"    {voids}")
    default = sym["ret_default"]
    if default is not None:
        lines.append(f"    return {default};")
    lines.append("}")
    return "\n".join(lines)


def render_new_module(module: str, epics: list[str], private_layout: str) -> str:
    epics_str = ", ".join(epics) or "unknown epic"
    lines = [
        f"/* csrc/{module} -- {epics_str} (signatures.toml module; the epic's own math",
        " * lands with its build card).",
        " * Skeleton generated by scripts/specfactory/sig_table.py so the fenced suite",
        " * fails red on assertions, not on a missing symbol, and so the build harness",
        " * has a file to read; every body below is a STUB the build card replaces. */",
        "/* PRIVATE LAYOUT, verbatim from csrc/om_internal.h (already included below).",
        " * Use exactly these member names; there are no others.",
    ]
    for line in private_layout.splitlines():
        safe_line = line.replace("*/", "* /").replace("/*", "/ *")
        lines.append(" * " + safe_line if safe_line else " *")
    lines.append(" */")
    lines += [
        '#include "ouroboros_sim.h"',
        '#include "om_internal.h"',
        "#include <stddef.h>",
        "#include <string.h>",
        "",
    ]
    return "\n".join(lines) + "\n"


def defined_anywhere(csrc_dir: Path, names: set[str]) -> set[str]:
    found: set[str] = set()
    for c_file in sorted(csrc_dir.glob("*.c")):
        text = c_file.read_text()
        for name in names:
            if name not in found and cl.find_function_span(text, name) is not None:
                found.add(name)
    return found


def render_skeletons(project: Path, symbols: list[dict], private_layout: str) -> dict[Path, str]:
    """path -> new content for every module file that changes or is created."""
    csrc_dir = project / "csrc"
    defined = defined_anywhere(csrc_dir, {s["name"] for s in symbols})
    outputs: dict[Path, str] = {}
    modules = sorted({s["module"] for s in symbols})
    for module in modules:
        path = csrc_dir / module
        stubs = [render_stub(s) for s in symbols if s["module"] == module and s["name"] not in defined]
        if path.is_file():
            if not stubs:
                continue
            text = path.read_text()
            body = "\n\n".join(stubs)
            if STUB_END in text:
                at = text.index(STUB_END)
                new = text[:at] + body + "\n" + text[at:]
            else:
                new = text.rstrip("\n") + f"\n\n{STUB_START}\n{body}\n{STUB_END}\n"
            outputs[path] = new
        else:
            epics = sorted({e for s in symbols if s["module"] == module for e in s["epics"]}, key=epic_num)
            body = "\n\n".join(stubs)
            outputs[path] = (render_new_module(module, epics, private_layout)
                             + f"{STUB_START}\n{body}\n{STUB_END}\n")
    return outputs


# ---- driver ----

def plan(project: Path, table_path: Path) -> dict:
    header_path = project / HEADER_REL
    conftest_path = project / CONFTEST_REL
    internal_path = project / INTERNAL_REL
    header_text = header_path.read_text()
    base_header = strip_header_blocks(header_text)
    types = Types(base_header)
    STRUCT_PY_NAMES.clear()
    table = load_table(table_path)
    structs, blocked_structs = resolve_structs(table, types)
    symbols, blocked_symbols, renamed = resolve_symbols(table, types)

    new_header, header_added, structs_added = render_header(base_header, structs, symbols, types)
    conftest_text = conftest_path.read_text()
    new_conftest, bindings_added = render_conftest(conftest_text, structs, symbols)
    private_layout = extract_private_layout(internal_path.read_text()) if internal_path.is_file() else ""
    skeletons = render_skeletons(project, symbols, private_layout)

    writes: dict[Path, str] = {}
    if new_header != header_text:
        writes[header_path] = new_header
    if new_conftest != conftest_text:
        writes[conftest_path] = new_conftest
    writes.update(skeletons)
    stubs_added = sum(v.count("/* STUB */") - (p.read_text().count("/* STUB */") if p.is_file() else 0)
                      for p, v in skeletons.items())
    return {
        "header_added": header_added,
        "bindings_added": bindings_added,
        "structs_added": structs_added,
        "stubs_added": stubs_added,
        "skeleton_files": sorted(str(p.relative_to(project)) for p in skeletons),
        "blocked": blocked_structs + blocked_symbols,
        "renamed": renamed,
        "writes": writes,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=str(DEFAULT_PROJECT))
    ap.add_argument("--table", help=f"defaults to <project>/{TABLE_REL}")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--report", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    project = Path(args.project).expanduser().resolve()
    table_path = Path(args.table).expanduser() if args.table else project / TABLE_REL
    if not (project / HEADER_REL).is_file() or not table_path.is_file():
        print(f"missing header or table under {project}", file=sys.stderr)
        return 2

    result = plan(project, table_path)
    writes = result.pop("writes")
    result["changed_files"] = sorted(str(p.relative_to(project)) for p in writes)

    if args.emit:
        for path, content in writes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    rc = 0
    if args.check and writes:
        rc = 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"header declarations: {result['header_added']}  struct typedefs: {result['structs_added']}  "
              f"bindings: {result['bindings_added']}  stubs: {result['stubs_added']}")
        print(f"skeleton files: {', '.join(result['skeleton_files']) or '(none)'}")
        verb = "wrote" if args.emit else ("stale" if args.check else "would write")
        print(f"{verb}: {', '.join(result['changed_files']) or '(nothing)'}")
        if result["renamed"]:
            print(f"RENAMED params ({len(result['renamed'])}; fix the table):")
            for r in result["renamed"]:
                print(f"  {r['name']}: param {r['index']} {r['param']!r} -> {r['renamed_to']}")
        if result["blocked"]:
            print(f"BLOCKED ({len(result['blocked'])}):")
            for b in result["blocked"]:
                print(f"  {b['module']}: {b['name']}: {b['reason']}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
