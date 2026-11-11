#!/usr/bin/env python3
"""rule_table.py [<repo>] [<outdir>]: mechanical table of every bible rule and every test that names it.
Reads only; standard library only. Defaults: repo ~/Projects/om-wt/engine-rules, outdir = this script's folder.
Writes rule_table.csv and rule_table_summary.md (v2; the v1 outputs are kept as *_v1.*). No judgment: every column is a text or AST match.

Definitions
- rule: a line `- R-###-##  text` in docs/bible/epics/E-*.md; invariant: a top-level `- ` bullet under `## Invariants`
  (id `E-## Invariant N`, N from 1).
- test function: `def test_*` (.py, found by ast, also methods; nested defs are part of their outer test) or
  `func test_*` / `func _test_*` (.gd, lines from the func to the next column-0 code line). Span includes decorators
  and docstring.
- ids: `R-042-01` and `R_042_01` both match (case-sensitive, not followed by a digit), normalised to the dash form.
- quotes_rule (function-level rows only): the function span contains the first 40 characters of the rule's text, whitespace-normalised.
- level "function": the id appears inside a test function's span. level "file": the id appears in the file outside
  every test function span (module docstring, comments, `Rule pins:` line, helpers, constants).
- assert_in_loop: an `assert` statement (or call named assert*, `_assert`, `_check`, `_expect`) nested in a for/while.
- sight_off_*: text `OM_TP_TARGET_BY_SIGHT` or `sight off` / `sight_off` (case-insensitive); `_fn` in the function,
  `_file` anywhere in the file.
- lab_*: text `scripts.skilllab`, `skilllab`, `invariants` (the lab engine or the invariants checker).
- skip_*: text `skip` or `xfail`.
- known_red: the file is listed in a known-red list (names joined by `+`). A list entry that names `file::function`
  marks only that function (file-level rows show `list*`); a bare file entry marks every function; playthrough list
  entries match function names by prefix.
"""
import ast
import csv
import re
import sys
from pathlib import Path

REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Projects/om-wt/engine-rules"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent

# Reused from scripts/specfactory/rule_pins_tests.py (RULE_TOKEN, PINS_LINE, PIN_TOKEN).
# v2: also the underscore form R_042_01 (test function names), word-bounded, case-sensitive; ids are normalised to the dash form.
RULE_TOKEN = re.compile(r"(?<![A-Za-z0-9])R[-_]\d{3}[-_]\d{2}(?!\d)")
PINS_LINE = re.compile(r"Rule pins:\s*(.*)")
PIN_TOKEN = re.compile(r"(R-\d+-\d+)@([0-9a-f]{6}|\?)")

RULE_LINE = re.compile(r"^- (R-\d{3}-\d{2})\s+(.*)$")
STORY_LINE = re.compile(r"^###\s+(S-\d+)\s*(.*)$")
INV_REF = re.compile(r"E-(\d\d)\s+Invariant\s+(\d+)")
SIGHT_OFF = re.compile(r"OM_TP_TARGET_BY_SIGHT|sight[ _]off", re.I)
LAB = re.compile(r"scripts\.skilllab|skilllab|invariants", re.I)
SKIP = re.compile(r"skip|xfail")
GD_ASSERT = re.compile(r"\b(assert\w*|_assert\w*|_check\w*|_expect\w*)\s*\(|^\s*assert\b")
GD_FUNC = re.compile(r"^func\s+(_?test_\w*)")


# ---------- bible ----------
def find_rules(text):
    """Rule ids in text, dash and underscore forms, normalised to the dash form."""
    return {t.replace("_", "-") for t in RULE_TOKEN.findall(text)}


def norm(text):
    return " ".join(text.split())


def read_epics():
    rules, invs = [], []
    for f in sorted((REPO / "docs/bible/epics").glob("E-*.md")):
        epic = re.match(r"E-\d\d", f.name).group(0)
        story, in_inv, n = "", False, 0
        lines = f.read_text(errors="replace").splitlines()
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("## "):
                in_inv = ln.strip() == "## Invariants"
            m = STORY_LINE.match(ln)
            if m:
                story = m.group(1)
            m = RULE_LINE.match(ln)
            if m:
                rules.append(dict(id=m.group(1), epic=epic, file=f.name, line=i + 1, story=story,
                                  text=m.group(2)[:160], full=m.group(2), kind="rule"))
            elif in_inv and ln.startswith("- "):
                n += 1
                text, j = ln[2:], i + 1
                while j < len(lines) and lines[j].startswith((" ", "\t")) and lines[j].strip():
                    text += " " + lines[j].strip()
                    j += 1
                invs.append(dict(id=f"{epic} Invariant {n}", epic=epic, file=f.name, line=i + 1, story="",
                                 text=text[:160], full=text, kind="invariant"))
            i += 1
    return rules, invs


# ---------- known-red lists ----------
def known_red():
    files, prefixes = {}, []
    sf = REPO / "scripts/specfactory"

    def lines(p):
        if not p.is_file():
            return []
        return [x.rstrip("\n") for x in p.read_text(errors="replace").splitlines() if x.strip() and not x.lstrip().startswith("#")]

    def add(entry, name):
        path, _, fn = entry.partition("::")
        files.setdefault(path.strip(), {}).setdefault(name, set()).add(fn.strip())  # "" = the whole file

    for ln in lines(sf / "gd_tests_known_red.txt"):
        e = ln.split(" :: ")[0].strip()
        add(e[len("res://"):] if e.startswith("res://") else e, "gd_tests_known_red")
    for ln in lines(sf / "lane_plays_known_red.txt"):
        add(ln.split("#")[0].strip(), "lane_plays_known_red")
    for ln in lines(sf / "playthrough_known_red.txt"):
        prefixes.append(ln.split(" :: ")[0].strip())
    for ln in lines(REPO / "docs/northstar/spec_factory/placeholder_controls.txt"):
        add(ln.strip(), "placeholder_controls")
    return files, prefixes


# ---------- test files ----------
def py_functions(text):
    """[(name, first line, last line, assert_in_loop)] 1-based; ast, with an indentation fallback."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return indent_functions(text, re.compile(r"^(\s*)(?:async\s+)?def\s+(test_\w*)"), False)
    out = []

    def visit(node):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if ch.name.startswith("test_"):
                    first = min([ch.lineno] + [d.lineno for d in ch.decorator_list])
                    out.append((ch.name, first, ch.end_lineno, loop_assert(ch)))
            else:
                visit(ch)  # module level, classes, if/try blocks

    visit(tree)
    return out


def loop_assert(fn):
    for loop in ast.walk(fn):
        if isinstance(loop, (ast.For, ast.While, ast.AsyncFor)):
            for n in ast.walk(loop):
                if isinstance(n, ast.Assert):
                    return True
                if isinstance(n, ast.Call):
                    f = n.func
                    nm = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                    if nm.startswith(("assert", "_assert", "_check", "_expect")):
                        return True
    return False


def indent_functions(text, head, gd):
    """Fallback and .gd: a function runs from its head line to the line before the next code line at an indent <= its own."""
    lines = text.splitlines()
    out = []
    for i, ln in enumerate(lines):
        m = head.match(ln)
        if not m:
            continue
        name = m.group(1) if gd else m.group(2)
        ind = 0 if gd else len(m.group(1))
        j = i + 1
        while j < len(lines):
            s = lines[j]
            if s.strip() and not s.lstrip().startswith("#") and len(s) - len(s.lstrip()) <= ind and not s.lstrip().startswith(")"):
                break
            j += 1
        end = j
        while end > i + 1 and not lines[end - 1].strip():
            end -= 1
        out.append((name, i + 1, end, loop_assert_text(lines[i:end])))
    return out


def loop_assert_text(body):
    loop_ind = None
    for ln in body:
        if not ln.strip():
            continue
        ind = len(ln) - len(ln.lstrip())
        if loop_ind is not None and ind <= loop_ind:
            loop_ind = None
        if loop_ind is not None and GD_ASSERT.search(ln):
            return True
        if loop_ind is None and re.match(r"\s*(for|while)\b", ln):
            loop_ind = ind
    return False


def gd_functions(text):
    return indent_functions(text, GD_FUNC, True)


def scan_tests(red_files, red_prefixes):
    """Returns (funcs, filelevel): funcs {rule id or inv id: [row dict]}, filelevel {id: [row dict]}, plus unknown-id bookkeeping."""
    func_rows, file_rows = {}, {}
    nfiles = nfuncs = 0
    for f in sorted(p for s in ("*.py", "*.gd") for p in (REPO / "tests").rglob(s)):
        rel = f.relative_to(REPO).as_posix()
        text = f.read_text(errors="replace")
        lines = text.splitlines()
        fns = py_functions(text) if f.suffix == ".py" else gd_functions(text)
        nfiles += 1
        nfuncs += len(fns)
        in_fn = set()
        for _, a, b, _ in fns:
            in_fn.update(range(a, b + 1))
        file_text = "\n".join(l for k, l in enumerate(lines, 1) if k not in in_fn)
        file_flags = dict(sight_off_file=bool(SIGHT_OFF.search(text)), lab_file=bool(LAB.search(text)),
                          skip_file=bool(SKIP.search(file_text)), controls=rel.startswith("tests/csim/controls/"))
        red_entries = red_files.get(rel, {})
        red_file = {n + ("*" if "" not in fs else "") for n, fs in red_entries.items()}  # * = only named functions of the file
        for name, a, b, loop in fns:
            body = "\n".join(lines[a - 1:b])
            row = dict(test_file=rel, test_func=name, test_line=a, assert_in_loop=loop,
                       sight_off_fn=bool(SIGHT_OFF.search(body)), lab_fn=bool(LAB.search(body)),
                       skip_fn=bool(SKIP.search(body)), **file_flags)
            r = {n for n, fs in red_entries.items() if "" in fs or name in fs}
            if any(name.startswith(p) for p in red_prefixes):
                r.add("playthrough_known_red")
            row["known_red"] = "+".join(sorted(r))
            row["body_norm"] = norm(body)
            for ident in find_rules(body) | {f"E-{m[0]} Invariant {m[1]}" for m in INV_REF.findall(body)}:
                func_rows.setdefault(ident, []).append(row)
        ids = find_rules(file_text) | {f"E-{m[0]} Invariant {m[1]}" for m in INV_REF.findall(file_text)}
        for ident in ids:
            file_rows.setdefault(ident, []).append(dict(
                test_file=rel, test_func="", test_line="", assert_in_loop="", sight_off_fn="", lab_fn="", skip_fn="",
                known_red="+".join(sorted(red_file)), **file_flags))
    return func_rows, file_rows, nfiles, nfuncs


# ---------- invariants checker ----------
def checker_rules():
    p = REPO / "scripts/skilllab/invariants.py"
    text = p.read_text(errors="replace")
    m = re.search(r"^RULES\s*=\s*\(([^)]*)\)", text, re.M)
    checked = find_rules(m.group(1)) if m else set()
    return checked, find_rules(text) - checked


# ---------- main ----------
def quotes(r, x, level):
    """quotes_rule: function-level pairs only; true when the function span contains the first 40 chars of the rule text (whitespace-normalised)."""
    if level != "function":
        return ""
    head = norm(r["full"])[:40]
    return "true" if head and head in x["body_norm"] else "false"


def yn(v):
    return "" if v == "" else ("yes" if v else "no")


def main():
    rules, invs = read_epics()
    red_files, red_prefixes = known_red()
    func_rows, file_rows, nfiles, nfuncs = scan_tests(red_files, red_prefixes)
    checked, mentioned = checker_rules()
    cols = ["id", "kind", "epic", "epic_file", "line", "story", "text", "level", "test_file", "test_func", "test_line",
            "assert_in_loop", "sight_off_fn", "sight_off_file", "lab_engine_fn", "lab_engine_file", "controls_dir",
            "known_red", "skip_xfail_fn", "skip_xfail_file", "checker", "quotes_rule"]
    status = {}
    with open(OUT / "rule_table.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cols)
        for r in rules + invs:
            chk = "checks" if r["id"] in checked else ("mentions" if r["id"] in mentioned else "")
            rows = [("function", x) for x in sorted(func_rows.get(r["id"], []), key=lambda x: (x["test_file"], x["test_line"]))]
            rows += [("file", x) for x in sorted(file_rows.get(r["id"], []), key=lambda x: x["test_file"])]
            status[r["id"]] = "function" if func_rows.get(r["id"]) else ("file" if file_rows.get(r["id"]) else "none")
            if not rows:
                rows = [("none", {})]
            for level, x in rows:
                w.writerow([r["id"], r["kind"], r["epic"], r["file"], r["line"], r["story"], r["text"], level,
                            x.get("test_file", ""), x.get("test_func", ""), x.get("test_line", ""),
                            yn(x.get("assert_in_loop", "")), yn(x.get("sight_off_fn", "")), yn(x.get("sight_off_file", "")),
                            yn(x.get("lab_fn", "")), yn(x.get("lab_file", "")), yn(x.get("controls", "")) if x else "",
                            x.get("known_red", ""), yn(x.get("skip_fn", "")), yn(x.get("skip_file", "")), chk, quotes(r, x, level)])
    # summary
    known = {r["id"] for r in rules}
    unknown = sorted((set(func_rows) | set(file_rows)) - known - {i["id"] for i in invs})
    epics = sorted({r["epic"] for r in rules})
    out = ["v2: underscore ids matched (v1 missed them)", "", "# Rule table summary", "",
           f"Source: `{REPO}` at `{__import__('subprocess').run(['git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()}`. "
           f"Generated by `rule_table.py`; {nfiles} test files (.py, .gd) with {nfuncs} test functions. "
           "Definitions are in the script's docstring: `function` = id inside a test function's span; `file only` = id in a test file "
           "outside every test function (docstring, comment, `Rule pins:`, helper) and in no test function anywhere; `none` = in no test file.", "",
           "| Epic | Rules | Named by a test function | File level only | Named by nothing | Checker checks | Checker mentions only | Invariants | Invariants named |",
           "|---|---|---|---|---|---|---|---|---|"]
    tot = [0] * 8
    for e in epics:
        er = [r for r in rules if r["epic"] == e]
        ei = [i for i in invs if i["epic"] == e]
        c = lambda s: sum(status[r["id"]] == s for r in er)
        vals = [len(er), c("function"), c("file"), c("none"), sum(r["id"] in checked for r in er),
                sum(r["id"] in mentioned for r in er), len(ei), sum(status[i["id"]] != "none" for i in ei)]
        tot = [a + b for a, b in zip(tot, vals)]
        out.append(f"| {e} | " + " | ".join(map(str, vals[:4] + vals[4:])) + " |")
    out.append("| **Total** | " + " | ".join(f"**{v}**" for v in tot) + " |")
    out += ["", f"Checker `scripts/skilllab/invariants.py` RULES tuple (checks): {', '.join(sorted(checked))}. "
            f"Other rule ids it names in text only (mentions): {', '.join(sorted(mentioned)) or 'none'}.", ""]
    out += [f"Rule ids named by tests but not in the bible epics ({len(unknown)}): {', '.join(unknown) or 'none'}.", ""]
    # flags overview
    fn_total = sum(len(v) for v in func_rows.values())
    out += ["## Flag counts over (rule, test function) pairs", ""]
    allf = [x for v in func_rows.values() for x in v]
    for k, label in [("assert_in_loop", "assert inside for/while"), ("sight_off_fn", "mentions sight off (function)"),
                     ("sight_off_file", "mentions sight off (file)"), ("lab_fn", "lab engine / invariants (function)"),
                     ("lab_file", "lab engine / invariants (file)"), ("controls", "under tests/csim/controls/"),
                     ("skip_fn", "skip/xfail text (function)")]:
        out.append(f"- {label}: {sum(bool(x[k]) for x in allf)} of {fn_total}")
    out.append(f"- file in a known-red or placeholder list: {sum(bool(x['known_red']) for x in allf)} of {fn_total}")
    (OUT / "rule_table_summary.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
