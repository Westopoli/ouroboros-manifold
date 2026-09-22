#!/usr/bin/env python3
"""Generates STUB skeletons for csrc/*.c modules that the Agora queue's cards
name in `snippet_file` but that do not exist on disk yet, so `card_lint.py`
has a file to check instead of failing MISSING_SNIPPET_FILE outright.

Never guesses a function signature. A candidate `om_*` symbol gets a STUB
body in a module only when all four hold:
  1. some card's `snippet_file` names this module and its `snippet_symbol`
     names the function (`--project`'s queue: every `queue/*.md` and every
     `queue/parked/*.md.hold`);
  2. some test in that card's own epic (by `tests/csim/test_E<NN>_*.py`)
     actually calls the symbol, directly or through a `tests/csim/conftest.py`
     or test-module helper chain (the same static walk `card_lint.py` uses);
  3. `tests/csim/conftest.py` declares an explicit ctypes `argtypes`/`restype`
     mirror for it (a direct `<handle>.<name>.argtypes = [...]` assignment,
     or the repo's `for name, st in ((...), ...): fn = getattr(...)` loop
     idiom) that this tool can translate to a C signature with confidence;
  4. no other csrc/*.c file already defines the symbol (never duplicate a
     definition -- that is a compile error, not a stub).

Anything that fails (2)-(4) is reported, not fabricated: --report lists, per
module, what was generated and every symbol refused and why.

Usage:
    scripts/specfactory/skeleton_gen.py [--project P] [--queue Q]
                                        [--modules csrc/a.c,csrc/b.c]
                                        [--report] [--json]

With no --modules, every csrc/*.c path named by some card's snippet_file
that does not yet exist under --project is treated as a target module.
--report prints the per-module listing and writes nothing. Exit code 0 on
success, 2 on a usage error (bad --project/--queue).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from green_check import parse_card  # noqa: E402  (reuse the frontmatter parser)
import card_lint as cl  # noqa: E402  (reuse the symbol-collection + C-scan machinery)

DEFAULT_PROJECT = cl.DEFAULT_PROJECT
DEFAULT_QUEUE = cl.DEFAULT_QUEUE

CTYPES_SCALAR = {
    "ctypes.c_uint32": "uint32_t",
    "ctypes.c_int32": "int32_t",
    "ctypes.c_uint64": "uint64_t",
    "ctypes.c_int64": "int64_t",
    "ctypes.c_double": "double",
    "ctypes.c_int": "int",
    "ctypes.c_char_p": "const char *",
}
WORLD_TOKENS = {"V", "OMWorldP", "ctypes.c_void_p"}
RET_DEFAULT = {
    "int": "0", "uint32_t": "0", "int32_t": "0",
    "uint64_t": "0", "int64_t": "0", "double": "0.0",
}


# ---- card / queue discovery ----

def iter_target_cards(queue: Path):
    """Exactly `queue/*.md` plus `queue/parked/*.md.hold` -- the live and
    still-waiting cards; every other parked suffix (.retired/.superseded/
    .legacy/.satisfied-by-*/.harness-bug/.blocked/...) is already resolved
    one way or another and is not a source of truth for what a module owns."""
    if not queue.is_dir():
        return
    for p in sorted(queue.glob("*.md")):
        yield p
    parked = queue / "parked"
    if parked.is_dir():
        for p in sorted(parked.glob("*.md.hold")):
            yield p


def load_cards(queue: Path) -> list[tuple[Path, dict]]:
    cards = []
    for p in iter_target_cards(queue):
        try:
            card = parse_card(p)
        except Exception:
            continue
        cards.append((p, card))
    return cards


def discover_modules(cards: list[tuple[Path, dict]], project: Path) -> list[str]:
    """Every `csrc/*.c` path named by some card's snippet_file that either
    does not exist yet or is still a pure skeleton this tool wrote -- the
    generic form of "the twelve missing modules" so this tool is not a
    hardcoded list. A module that has grown a real (non-stub) body is left
    alone by auto-discovery entirely; pass it to --modules explicitly to
    force the overwrite check to run (and refuse) anyway."""
    found: set[str] = set()
    for _path, card in cards:
        for f in cl._split_list(card.get("snippet_file", "")):
            if f.startswith("csrc/") and is_pure_skeleton(project / f):
                found.add(f)
    return sorted(found)


def global_symbol_to_files(cards: list[tuple[Path, dict]]) -> dict[str, dict[str, list[str]]]:
    """symbol -> {snippet_file -> [card ids]}, over every card in the queue
    (not just the target modules) -- the source of truth for "which module
    does a card assign this symbol to" and for spotting a symbol two cards
    disagree about."""
    out: dict[str, dict[str, list[str]]] = {}
    for path, card in cards:
        files = cl._split_list(card.get("snippet_file", ""))
        symbols = cl._split_list(card.get("snippet_symbol", ""))
        if not files or not symbols:
            continue
        cid = cl.card_id_of(path)
        for sym in symbols:
            for f in files:
                out.setdefault(sym, {}).setdefault(f, []).append(cid)
    return out


def module_epics(cards_for_module: list[tuple[Path, dict]]) -> list[str]:
    epics = set()
    for _path, card in cards_for_module:
        e = cl.epic_of_card(card)
        if e:
            epics.add(e)
    return sorted(epics)


def test_files_for_epic(tests_dir: Path, epic: str) -> list[Path]:
    m = re.match(r"E-(\d+)", epic)
    if not m:
        return []
    num = int(m.group(1))
    return sorted(tests_dir.glob(f"test_E{num:02d}_*.py"))


# ---- static symbol collection per test file (reuses card_lint's walk) ----

def symbols_called_by_file(test_path: Path, tests_dir: Path,
                            conftest_cache: dict, module_cache: dict) -> set[str]:
    if test_path not in module_cache:
        module_cache[test_path] = cl.helper_defs_of(test_path)
    module_defs = module_cache[test_path]
    conftest_helpers = cl.conftest_chain_helpers(test_path.parent, tests_dir, conftest_cache)
    helper_defs = {**conftest_helpers, **module_defs}
    tree = ast.parse(test_path.read_text(), filename=str(test_path))
    return cl._collect_from_node(tree, {}, helper_defs, frozenset())


# ---- conftest.py ctypes mirror extraction ----

_DIRECT_ARGTYPES_RE = re.compile(r"\b\w+\.(om_[A-Za-z0-9_]+)\.argtypes\s*=\s*(\[.*?\])", re.S)
_DIRECT_RESTYPE_RE = re.compile(r"\b\w+\.(om_[A-Za-z0-9_]+)\.restype\s*=\s*([^\n;]+)")
_LOOP_RE = re.compile(
    r"for\s+name,\s*st\s+in\s+\((.*?)\):\s*\n"
    r"\s*fn\s*=\s*getattr\([A-Za-z_]\w*,\s*name\)\s*\n"
    r"\s*fn\.argtypes\s*=\s*(\[.*?\])\s*\n"
    r"\s*fn\.restype\s*=\s*([^\n]+)",
    re.S,
)
_LOOP_TUPLE_RE = re.compile(r'\(\s*"(om_[A-Za-z0-9_]+)"\s*,\s*(\w+)\s*\)')


def extract_mirrors(conftest_text: str) -> dict[str, dict[str, str]]:
    """symbol -> {"argtypes": "<raw ctypes list text>", "restype": "<raw ctypes text>"},
    for every symbol conftest.py declares an explicit mirror for -- either a
    direct `<handle>.<name>.argtypes = [...]` / `.restype = ...` pair, or the
    `for name, st in ((...), ...): fn = getattr(...); fn.argtypes = ...`
    loop idiom this repo's E-05/E-04 blocks use for tick-log readers."""
    mirrors: dict[str, dict[str, str]] = {}
    for m in _DIRECT_ARGTYPES_RE.finditer(conftest_text):
        mirrors.setdefault(m.group(1), {})["argtypes"] = m.group(2)
    for m in _DIRECT_RESTYPE_RE.finditer(conftest_text):
        mirrors.setdefault(m.group(1), {})["restype"] = m.group(2).strip()
    for lm in _LOOP_RE.finditer(conftest_text):
        tuple_text, argtypes_tpl, restype_tpl = lm.group(1), lm.group(2), lm.group(3)
        for tm in _LOOP_TUPLE_RE.finditer(tuple_text):
            sym, struct = tm.group(1), tm.group(2)
            mirrors.setdefault(sym, {})["argtypes"] = re.sub(r"\bst\b", struct, argtypes_tpl)
            mirrors.setdefault(sym, {})["restype"] = re.sub(r"\bst\b", struct, restype_tpl).strip()
    return {k: v for k, v in mirrors.items() if "argtypes" in v and "restype" in v}


# ---- ctypes -> C signature translation ----

def _camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _split_top_level(text: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return [p.strip() for p in parts]


def _ctype_token_to_c(token: str) -> str | None:
    token = token.strip()
    if token in WORLD_TOKENS:
        return "om_world *"
    if token in CTYPES_SCALAR:
        return CTYPES_SCALAR[token]
    m = re.match(r"^(?:P|ctypes\.POINTER)\((.+)\)$", token, re.S)
    if m:
        inner = m.group(1).strip()
        if inner in CTYPES_SCALAR:
            return CTYPES_SCALAR[inner] + " *"
        if re.match(r"^[A-Z]\w*$", inner):
            return _camel_to_snake(inner) + " *"
        return None
    return None


def convert_signature(name: str, mirror: dict[str, str]) -> dict | None:
    """mirror -> {"name", "params": [(c_type, c_name), ...], "ret_type", "ret_default"},
    or None if any argtype/restype token is not one this tool recognizes with
    confidence (refused, not guessed)."""
    m = re.match(r"^\[(.*)\]$", mirror["argtypes"].strip(), re.S)
    if not m:
        return None
    items = _split_top_level(m.group(1)) if m.group(1).strip() else []
    params = []
    for i, tok in enumerate(items):
        c_type = _ctype_token_to_c(tok)
        if c_type is None:
            return None
        pname = "w" if i == 0 and c_type == "om_world *" else f"a{i}"
        params.append((c_type, pname))

    restype_raw = mirror["restype"].strip()
    if restype_raw == "None":
        ret_type, ret_default = "void", None
    else:
        ret_type = _ctype_token_to_c(restype_raw)
        if ret_type is None:
            return None
        ret_default = RET_DEFAULT.get(ret_type)
        if ret_default is None and ret_type.endswith("*"):
            ret_default = "NULL"
        if ret_default is None:
            return None

    return {"name": name, "params": params, "ret_type": ret_type, "ret_default": ret_default}


def _render_param(c_type: str, c_name: str) -> str:
    return f"{c_type}{c_name}" if c_type.endswith("*") else f"{c_type} {c_name}"


def render_declaration(fn: dict) -> str:
    params_str = ", ".join(_render_param(t, n) for t, n in fn["params"]) or "void"
    return f"{_render_param(fn['ret_type'], fn['name'])}({params_str});"


def render_stub(fn: dict) -> str:
    params_str = ", ".join(_render_param(t, n) for t, n in fn["params"]) or "void"
    lines = [f"{_render_param(fn['ret_type'], fn['name'])}({params_str}) {{", "    /* STUB */"]
    voids = " ".join(f"(void){n};" for _, n in fn["params"])
    if voids:
        lines.append(f"    {voids}")
    if fn["ret_type"] != "void":
        lines.append(f"    return {fn['ret_default']};")
    lines.append("}")
    return "\n".join(lines)


# ---- symbols already defined in some other csrc/*.c file ----

def symbols_defined_elsewhere(csrc_dir: Path, symbols: set[str], own_file: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not csrc_dir.is_dir():
        return out
    own_name = Path(own_file).name
    for c_file in sorted(csrc_dir.glob("*.c")):
        if c_file.name == own_name:
            continue
        text = c_file.read_text()
        for sym in symbols:
            if sym in out:
                continue
            if cl.find_function_span(text, sym) is not None:
                out[sym] = f"csrc/{c_file.name}"
    return out


# ---- om_internal.h PRIVATE LAYOUT block extraction ----

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


# ---- per-module analysis ----

def analyze_module(module_file: str, cards_for_module: list[tuple[Path, dict]],
                    sym_to_files: dict[str, dict[str, list[str]]], tests_dir: Path,
                    mirrors: dict[str, dict[str, str]], csrc_dir: Path,
                    conftest_cache: dict, module_cache: dict) -> dict:
    owned = {sym: files[module_file] for sym, files in sym_to_files.items() if module_file in files}
    epics = module_epics(cards_for_module)

    test_files: list[Path] = []
    for e in epics:
        test_files += test_files_for_epic(tests_dir, e)
    test_files = sorted(set(test_files))

    called: set[str] = set()
    for tf in test_files:
        called |= symbols_called_by_file(tf, tests_dir, conftest_cache, module_cache)

    global_carded = set(sym_to_files.keys())
    no_card = sorted(called - global_carded)
    not_test_called = sorted(set(owned) - called)
    qualifying = sorted(set(owned) & called)

    elsewhere = symbols_defined_elsewhere(csrc_dir, set(qualifying), module_file)
    conflicts = {sym: files for sym, files in sym_to_files.items()
                 if module_file in files and len(files) > 1}

    generated: list[dict] = []
    refused_no_mirror: list[str] = []
    refused_elsewhere: list[tuple[str, str]] = []
    for sym in qualifying:
        if sym in conflicts:
            # two different cards assign this symbol to two different files --
            # generating it in either would risk a duplicate definition the
            # moment the other file is also filled in. Refused everywhere;
            # see the CONFLICT line in --report.
            continue
        if sym in elsewhere:
            refused_elsewhere.append((sym, elsewhere[sym]))
            continue
        mirror = mirrors.get(sym)
        c_sig = convert_signature(sym, mirror) if mirror else None
        if c_sig is None:
            refused_no_mirror.append(sym)
            continue
        generated.append(c_sig)

    return {
        "module_file": module_file,
        "epics": epics,
        "cards": sorted({cl.card_id_of(p) for p, _ in cards_for_module}),
        "owned_symbols": sorted(owned),
        "generated": generated,
        "refused_no_mirror": refused_no_mirror,
        "refused_already_elsewhere": refused_elsewhere,
        "no_card": no_card,
        "not_test_called": not_test_called,
        "conflicts": conflicts,
    }


# ---- rendering csrc/<module>.c ----

def render_module_c(analysis: dict, private_layout: str) -> str:
    epics_str = ", ".join(analysis["epics"]) or "unknown epic"
    cards_str = ", ".join(analysis["cards"]) or "none"
    lines = [
        f"/* {analysis['module_file']} -- {epics_str} skeleton (cards: {cards_str}).",
        " * Generated by scripts/specfactory/skeleton_gen.py so the fenced suite fails red",
        " * on assertions, not on a missing symbol, and so the build harness has a file to",
        " * read; every body below is a STUB the build card replaces. */",
        "/* PRIVATE LAYOUT, verbatim from csrc/om_internal.h (already included below).",
        " * Use exactly these member names; there are no others.",
    ]
    for line in private_layout.splitlines():
        # om_internal.h's struct bodies carry their own nested /* ... */ notes
        # (ALG-11, the E-05 state comment); a literal "*/" inside them would
        # close THIS wrapping comment early and corrupt every line after it
        # into stray C tokens, and a literal "/*" trips -Wcomment even though
        # it is harmless. Break both tokens, not the words.
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
    if not analysis["generated"]:
        lines += [
            "/* No function bodies generated: every om_* symbol a card assigned to this",
            " * module was refused (no card-and-test-verified candidate qualified this run).",
            " * See `scripts/specfactory/skeleton_gen.py --report` for the reasons. */",
        ]
    else:
        for i, fn in enumerate(analysis["generated"]):
            if i:
                lines.append("")
            lines.append(render_stub(fn))
    return "\n".join(lines).rstrip("\n") + "\n"


def is_pure_skeleton(path: Path) -> bool:
    if not path.is_file():
        return True
    text = path.read_text()
    for name in cl.all_defined_symbols(text):
        span = cl.find_function_span(text, name)
        if span is None:
            continue
        if not cl.is_stub_body(text[span[0]:span[1]]):
            return False
    return True


# ---- header block insertion ----

def _header_block(module_file: str, epics: list[str], fns: list[dict]) -> str:
    epics_str = ", ".join(epics) or "unknown epic"
    start = f"/* ---- {module_file} skeleton (auto-generated by scripts/specfactory/skeleton_gen.py; {epics_str}) ---- */"
    end = f"/* ---- end {module_file} skeleton ---- */"
    decls = "\n".join(render_declaration(fn) for fn in fns)
    return f"{start}\n{decls}\n{end}"


def append_header_blocks(header_text: str, blocks: dict[str, str]) -> str:
    text = header_text
    for module_file, block in blocks.items():
        block_lines = block.splitlines()
        start_marker, end_marker = block_lines[0], block_lines[-1]
        pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
        if pattern.search(text):
            text = pattern.sub(block, text)
        else:
            insert_at = text.rindex("#ifdef __cplusplus")
            text = text[:insert_at] + block + "\n\n" + text[insert_at:]
    return text


# ---- report rendering ----

def print_report(analyses: list[dict]) -> None:
    for a in analyses:
        print(f"== {a['module_file']} ({', '.join(a['epics']) or 'unknown epic'}) ==")
        print(f"  cards: {', '.join(a['cards']) or '(none)'}")
        gen_names = [fn["name"] for fn in a["generated"]]
        print(f"  generated ({len(gen_names)}): {', '.join(gen_names) or '(none)'}")
        print(f"  refused - no mirror ({len(a['refused_no_mirror'])}): "
              f"{', '.join(a['refused_no_mirror']) or '(none)'}")
        elsewhere_str = ", ".join(f"{s} (in {f})" for s, f in a["refused_already_elsewhere"])
        print(f"  refused - already defined elsewhere ({len(a['refused_already_elsewhere'])}): "
              f"{elsewhere_str or '(none)'}")
        print(f"  card names, no test calls ({len(a['not_test_called'])}): "
              f"{', '.join(a['not_test_called']) or '(none)'}")
        print(f"  no card (tests call, no card assigns) ({len(a['no_card'])}): "
              f"{', '.join(a['no_card']) or '(none)'}")
        if a["conflicts"]:
            print(f"  CONFLICT (symbol claimed by more than one file):")
            for sym, files in sorted(a["conflicts"].items()):
                print(f"    {sym}: {files}")
        print()


# ---- main ----

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=str(DEFAULT_PROJECT))
    ap.add_argument("--queue", default=str(DEFAULT_QUEUE))
    ap.add_argument("--modules", help="comma-separated csrc/*.c paths; default auto-discovers")
    ap.add_argument("--report", action="store_true", help="print the listing only, write nothing")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    project = Path(args.project).expanduser()
    queue = Path(args.queue).expanduser()
    if not project.is_dir():
        print(f"project is not a directory: {project}", file=sys.stderr)
        return 2

    csrc_dir = project / "csrc"
    header_path = csrc_dir / "ouroboros_sim.h"
    internal_path = csrc_dir / "om_internal.h"
    tests_dir = project / "tests" / "csim"
    conftest_path = tests_dir / "conftest.py"

    cards = load_cards(queue)
    modules = ([m.strip() for m in args.modules.split(",") if m.strip()]
               if args.modules else discover_modules(cards, project))

    sym_to_files = global_symbol_to_files(cards)
    mirrors = extract_mirrors(conftest_path.read_text()) if conftest_path.is_file() else {}
    private_layout = extract_private_layout(internal_path.read_text()) if internal_path.is_file() else ""

    conftest_cache: dict = {}
    module_cache: dict = {}

    analyses = []
    for module_file in modules:
        cards_for_module = [(p, c) for p, c in cards
                             if module_file in cl._split_list(c.get("snippet_file", ""))]
        analyses.append(analyze_module(
            module_file, cards_for_module, sym_to_files, tests_dir, mirrors, csrc_dir,
            conftest_cache, module_cache,
        ))

    if args.json:
        print(json.dumps([{
            **a,
            "generated": [fn["name"] for fn in a["generated"]],
        } for a in analyses], indent=2))
    else:
        print_report(analyses)

    if args.report:
        return 0

    refused_overwrite = []
    header_blocks: dict[str, str] = {}
    for a in analyses:
        target = project / a["module_file"]
        if not is_pure_skeleton(target):
            refused_overwrite.append(a["module_file"])
            continue
        content = render_module_c(a, private_layout)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_text() != content:
            target.write_text(content)
        if a["generated"]:
            header_blocks[a["module_file"]] = _header_block(a["module_file"], a["epics"], a["generated"])

    if header_blocks and header_path.is_file():
        new_header = append_header_blocks(header_path.read_text(), header_blocks)
        if new_header != header_path.read_text():
            header_path.write_text(new_header)

    if refused_overwrite:
        print("REFUSED TO OVERWRITE (not a pure skeleton):", file=sys.stderr)
        for m in refused_overwrite:
            print(f"  {m}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
