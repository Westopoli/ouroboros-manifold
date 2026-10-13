#!/usr/bin/env python3
"""reach_lint.py -- Wave 0 item 3 of the gap-fix plan
(~/.claude/plans/witty-cuddling-goblet.md): the reachability gate lint.

Problem this closes: `card_lint.py`/`pieces.py` prove a story's acceptance
tests are green, but a test reaches a `csrc/ouroboros_sim.h` symbol directly
through ctypes (`lib.om_x(...)`), so a symbol can be fully tested while no
code path in the real, running game ever calls it (the exact shape of the
`om_mission_eval_commander_fate` gap the gap-fix plan exists to close: it is
defined, it has a passing unit test, and nothing in `om_mission_end` calls
it, so a mission's commander dying never changes the debrief).

What this checks: for every public function declared in
`csrc/ouroboros_sim.h` that some test under `tests/` calls, is it reachable
in the running game -- reachable by a STATIC call graph from
`om_world_step`, `om_tactical_step`, the time-jump entry point
(`om_time_jump_run`), or one of the handlers `csrc/pipe/om_pipe.c`'s
`main()` dispatch loop calls for an incoming pipe command? If not, and the
symbol is not in `reach_allowlist.toml`, it is a finding: tested, but
unwired.

Method (deterministic; never depends on the working tree's current,
possibly mid-edit state):

  1. `git archive <ref> -- csrc tests` into a scratch directory. A pristine
     copy of the C sources AND the test suite at that exact commit -- the
     caller's on-disk checkout (dirty, mid-rebase, whatever) never enters
     the analysis. Same ref in, same report out, always.
  2. Compile every `csrc/*.c` file and `csrc/pipe/om_pipe.c` as its own
     translation unit with `gcc -std=c11 -O0 -fcallgraph-info -DOM_DEBUG_INJECT
     -Icsrc -c`, one `.ci` VCG-format file per unit. `-O0`: the flattest,
     least-transformed compile available, so a call site the source clearly
     has is never dropped by inlining or dead-code elimination before the
     graph is written (the shipped build uses `-O2`; that is a fine
     compiled artifact but a worse call-graph source -- cross-file calls,
     which is everything that matters here, are never inlined either way
     since nothing here uses `-flto`). `-DOM_DEBUG_INJECT`: the superset
     build the debug library (`libouroboros_dbg.so`) and the debug pipe use,
     so `om_debug_inject` and the `#ifdef`-gated pipe handlers
     (`handle_place_structure`, `handle_inject`) are present in the graph
     too, rather than silently absent.
  3. Parse every `.ci` file's `node:`/`edge:` records into one directed
     graph, keyed by GCC's own node title: a function with external
     linkage (every `om_*` public symbol, and `main`) is titled by its bare
     name; a `static` function (every `handle_*` pipe dispatcher, and every
     other file-local helper) is titled `<path-as-compiled>:<name>`. Since
     every symbol this lint cares about on the header side is, by
     construction, externally linked (ctypes needs that), a bare-name graph
     lookup for a header symbol can never collide with a same-named static
     helper in some other file -- GCC never emits a bare title for a static
     symbol.
  4. Roots: `{om_world_step, om_tactical_step, om_time_jump_run}`, plus
     every function name found textually inside `om_pipe.c`'s own `main()`
     dispatch loop (the `for (;;) { ... }` body) as a call target --
     `handle_step`, `handle_jump`, `write_snapshot`, ... -- resolved to
     their compiled (possibly path-prefixed) node title. This is read off
     the dispatch loop's source text, not hardcoded, so a new pipe command
     is picked up the next time this runs without editing this file.
  5. BFS from the roots over the parsed graph gives the reachable set.
  6. Header symbols: every `name(params);` prototype in
     `csrc/ouroboros_sim.h` (comments stripped first with a `/* */` and
     `//` regex). The header has no function-pointer typedefs and no
     macro-functions today (verified by inspection), so a plain
     `identifier(...);` scan is unambiguous -- no need for a real C parse.
  7. Tested symbols: every `om_[A-Za-z0-9_]+` identifier immediately
     preceded by `.` (a `lib.om_x(...)` ctypes call) or named as a string
     literal inside `getattr(...)`, scanned across every `.py` file under
     `tests/` -- test files AND their `conftest.py` fixture builders, since
     a fixture that calls a header symbol on a test's behalf still means
     the test reaches it, by this lint's own definition of "calls".
  8. Report every tested symbol that (a) is a real header prototype, (b) is
     not in the reachable set, and (c) is not in `reach_allowlist.toml`,
     together with one test file that calls it.

This is deliberately feature-flag-insensitive: the graph is static, so
`om_world_step`'s `OM_FEAT_TACTICAL` branch (`csrc/sim.c` ~206, 230, 547)
still statically calls `om_tactical_step` whether or not that flag is ever
set on the live pipe path. That produces no false negative here (nothing
downstream of `om_tactical_step` is missed because of it); the branch is
allowlisted anyway, per the gap-fix plan's Wave 0 item 3, purely as a note
that the live path for tactical stepping is the pipe's own dedicated
handler, not this branch -- not because this tool needs the exemption to
get a clean answer.

Known limitation: a static call graph built this way sees a direct call
site (`foo();`) but not an indirect one through a function pointer
(`w->write_fn(...)` where `write_fn` was assigned `some_writer` elsewhere --
GCC's own `.ci` output represents that call as `__indirect_call`, dropping
the edge to `some_writer` entirely). `csrc/save.c`'s per-slot shadow-save
hooks are exactly this shape. Checked by hand for the two slots that are
actually wired today (events, generational): neither hook function calls
any `om_*` header symbol, so this gap does not currently produce a false
"unreachable" verdict for anything this lint checks -- worth re-checking
whenever a new save slot's hooks are wired (`csrc/save.c`'s ten-slot
comment names them), since a hook that starts calling a public accessor
would not get credit for the reachability that pointer-indirected call
still genuinely provides.

Baseline (regression) mode. Run bare (no `--base-ref`), this lint is
absolute: on origin/main today it reports 480 tested-but-unreachable
symbols, because most of E-06..E-17 is real, tested, but not yet wired into
any live path (`merge_cli.py`'s own words) -- wiring this into a merge gate
unconditionally would reject every candidate against that pre-existing
480-symbol baseline forever. `--base-ref <ref>` switches to regression
mode, mirroring `suite_regression.py`'s `compare_runs`: compute the
unreachable-symbol SET at `--base-ref` and at `--ref` (the candidate)
independently -- each is just another `git archive` of a ref, so this needs
no worktree, unlike `suite_regression.py`'s diff-apply approach -- and
report only `set(after) - set(before)`: a symbol already unreachable on the
base is a pre-existing finding no candidate is responsible for fixing; a
symbol the candidate newly tests that comes up unreachable is caught for
free by the same set difference (it is in `after`, never in `before`). The
bare, absolute mode (no `--base-ref`) is unchanged and still available for
a full read of where the codebase stands.

Read exemption. A getter/predicate a human or the client calls to display
state (`om_unit_get_hp`, `om_region_count`, `om_world_is_terminal`,
`om_unit_has_active_buff`) is naturally exercised by tests and by the
client without the SIMULATION's own tick/jump/pipe code ever needing to
call it back -- flagging it as "unreachable" is noise, not a finding; the
real defect class this lint exists for is behaviour a rule says happens in
play (a fate eval, a state transition, an apply/resolve/setup step) that
nothing ever drives. The obvious rule -- "first parameter is `const
om_world *` (or no world parameter at all), and the return type is not
void, is a read accessor" -- was tried first and rejected: checked against
`om_mission_eval_commander_fate(double hp, double max_hp)` (declared
`ouroboros_sim.h:1541`), which takes NO `om_world *` parameter at all and
returns `int32_t`, so that rule would have exempted the exact symbol this
lint's own acceptance bar (Wave 0 item 4) requires it to keep reporting.
The rule actually used, per the fallback the gap-fix plan specifies: a pure
NAME-pattern exemption, no signature involved -- `om_*_get_*`, `*_count`,
`*_is_*`, `*_has_*`. `om_mission_eval_commander_fate` matches none of these
and stays a finding. `--include-reads` turns the exemption off and shows
every tested-but-unreachable symbol, reads included, same as before this
mode existed.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

REPO = Path(__file__).resolve().parents[2]
DEFAULT_ALLOWLIST = Path(__file__).resolve().parent / "reach_allowlist.toml"
DEFAULT_HEADER = "csrc/ouroboros_sim.h"
DEFAULT_PIPE_FILE = "csrc/pipe/om_pipe.c"
EXTRA_ROOTS = ("om_world_step", "om_tactical_step", "om_time_jump_run")

NODE_RE = re.compile(r'^node:\s*\{\s*title:\s*"([^"]*)"', re.M)
EDGE_RE = re.compile(r'^edge:\s*\{\s*sourcename:\s*"([^"]*)"\s*targetname:\s*"([^"]*)"', re.M)

# Header prototype scan: comments stripped, then `name(params);` with no
# intervening `{`/`}` -- every declaration in ouroboros_sim.h ends in `;`
# with no body; DOTALL so a multi-line parameter list (om_region_set, ...)
# still matches as one prototype.
COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
PROTO_RE = re.compile(r"\b(om_[A-Za-z0-9_]+)\s*\(([^;{}]*)\)\s*;", re.S)

# Tested symbols: `lib.om_x(` / `dbg.om_x(` style ctypes attribute calls, and
# `getattr(lib, "om_x")` style dynamic lookups.
CALL_ATTR_RE = re.compile(r"\.\s*(om_[A-Za-z0-9_]+)\s*\(")
GETATTR_RE = re.compile(r"""getattr\(\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*["'](om_[A-Za-z0-9_]+)["']""")

CALL_IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")

# Read-accessor exemption (see module docstring "Read exemption" section for
# why this is a pure name pattern and not the signature-based rule tried
# first): om_*_get_*, *_count, *_is_*, *_has_*.
READ_NAME_RE = re.compile(r"_get_|_count$|_is_|_has_")


def is_read_accessor(name: str) -> bool:
    return bool(READ_NAME_RE.search(name))


def _strip_comments(text: str) -> str:
    return LINE_COMMENT_RE.sub("", COMMENT_RE.sub(" ", text))


def header_public_symbols(header_text: str) -> set[str]:
    return {m.group(1) for m in PROTO_RE.finditer(_strip_comments(header_text))}


def find_function_span(text: str, name: str) -> tuple[int, int] | None:
    """(start, end) char offsets of the brace-matched body of a top-level
    definition of `name`. Duplicated (not imported) from card_lint.py: this
    module must stand alone against any git ref's source text, including
    refs where card_lint.py's own signature has since changed."""
    pattern = re.compile(
        r"^[ \t]*(?:static\s+|inline\s+)*[A-Za-z_][\w\s\*]*?\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{",
        re.M,
    )
    m = pattern.search(text)
    if not m:
        return None
    depth = 0
    i = m.end() - 1
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return m.start(), i + 1
        i += 1
    return m.start(), len(text)


def dispatch_call_names(pipe_c_text: str) -> set[str]:
    """Every identifier called from inside om_pipe.c's main() dispatch loop
    (the `for (;;) { ... }` body) -- handle_step, write_snapshot, ... Found
    textually so a newly added pipe command is picked up without editing
    this file."""
    span = find_function_span(pipe_c_text, "main")
    if span is None:
        return set()
    body = pipe_c_text[span[0]:span[1]]
    loop_start = body.find("for (;;)")
    if loop_start == -1:
        loop_start = 0
    loop_body = body[loop_start:]
    names = set(CALL_IDENT_RE.findall(loop_body))
    # C keywords that parse like calls (`if (`, `while (`, `sizeof(...)`) are
    # never real graph nodes, so leaving them in is harmless -- they simply
    # fail to resolve to any node title and are dropped in resolve_roots.
    # Excluded anyway, for a cleaner root list in --help output/debugging.
    keywords = {"if", "while", "for", "switch", "sizeof", "return"}
    return names - keywords


def build_callgraph(csrc_dir: Path) -> dict[str, set[str]]:
    """{node_title: {callee_node_title, ...}} over every csrc/*.c file and
    csrc/pipe/om_pipe.c, compiled as independent translation units with
    gcc -fcallgraph-info. Raises RuntimeError on a compile failure (a
    harness fault, not a lint finding)."""
    graph: dict[str, set[str]] = {}
    sources = sorted(csrc_dir.glob("*.c"))
    # Every csrc/pipe/*.c: om_pipe.c's handlers were split into pipe_*.c.
    sources.extend(sorted((csrc_dir / "pipe").glob("*.c")))

    with tempfile.TemporaryDirectory(prefix="reach_lint_cc_") as scratch:
        scratch_path = Path(scratch)
        for src in sources:
            # Both the source path AND the -I path are passed RELATIVE to
            # cwd=csrc_dir.parent (never absolute): GCC's callgraph-info
            # titles a static (file-local) function `<path-as-given>:<name>`,
            # so an absolute path would bake this run's own tempdir name into
            # every static node title, making two runs of the same ref
            # produce different, non-comparable graphs -- exactly the
            # working-tree-independence this tool promises to avoid.
            rel = src.relative_to(csrc_dir.parent)
            obj = scratch_path / (rel.as_posix().replace("/", "_") + ".o")
            proc = subprocess.run(
                ["gcc", "-std=c11", "-O0", "-fcallgraph-info", "-DOM_DEBUG_INJECT",
                 "-Icsrc", "-c", str(rel), "-o", str(obj)],
                cwd=csrc_dir.parent, capture_output=True, text=True,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"gcc -fcallgraph-info failed on {rel}: {proc.stderr[-2000:]}")
            ci_path = obj.with_suffix(".ci")
            if not ci_path.is_file():
                # A TU with no functions at all emits no .ci; nothing to add.
                continue
            ci_text = ci_path.read_text()
            for title in NODE_RE.findall(ci_text):
                graph.setdefault(title, set())
            for source_name, target_name in EDGE_RE.findall(ci_text):
                graph.setdefault(source_name, set()).add(target_name)
    return graph


def resolve_roots(graph: dict[str, set[str]], pipe_dispatch_names: set[str],
                   pipe_rel: str) -> set[str]:
    """Root node titles: the three fixed extern roots, plus every dispatch
    call name resolved against the graph -- preferring the om_pipe.c-scoped
    static title (`<pipe_rel>:name`), falling back to a bare extern title
    (a dispatch call that happens to be extern, e.g. a future command that
    calls an om_* accessor directly instead of through a `handle_*` static)."""
    roots: set[str] = set()
    for name in EXTRA_ROOTS:
        if name in graph:
            roots.add(name)
    for name in pipe_dispatch_names:
        static_title = f"{pipe_rel}:{name}"
        if static_title in graph:
            roots.add(static_title)
        elif name in graph:
            roots.add(name)
    return roots


def reachable_from(graph: dict[str, set[str]], roots: set[str]) -> set[str]:
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph.get(node, ()))
    return seen


def tested_symbols(tests_dir: Path) -> dict[str, list[str]]:
    """{symbol: [test file path relative to tests_dir's parent, ...]} for
    every om_* ctypes call literally present in any .py file under
    tests_dir (test files and their conftest.py fixture builders alike)."""
    found: dict[str, list[str]] = {}
    for py_file in sorted(tests_dir.rglob("*.py")):
        text = py_file.read_text(errors="replace")
        symbols = set(CALL_ATTR_RE.findall(text)) | set(GETATTR_RE.findall(text))
        if not symbols:
            continue
        rel = py_file.relative_to(tests_dir.parent)
        for sym in symbols:
            found.setdefault(sym, []).append(str(rel))
    return found


def load_allowlist(path: Path) -> dict[str, str]:
    """{symbol: reason}. Missing file -> empty allowlist (no exemptions)."""
    if not path.is_file():
        return {}
    if tomllib is None:
        raise RuntimeError("tomllib unavailable (Python < 3.11) and reach_allowlist.toml is present")
    data = tomllib.loads(path.read_text())
    out: dict[str, str] = {}
    for entry in data.get("allow", []):
        sym = entry.get("symbol")
        if sym:
            out[sym] = entry.get("reason", "")
    return out


def _archive_path(project: Path, ref: str, path: str, dest: Path) -> bool:
    """git archive <ref> -- <path>, extracted into dest. Returns False (not
    an error) when <path> has no tracked file at ref -- `git archive` itself
    exits nonzero for a pathspec matching nothing, which is a legitimate
    shape for `tests` on some throwaway fixture ref, not a harness fault."""
    proc = subprocess.run(
        ["git", "archive", ref, "--", path],
        cwd=project, capture_output=True,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode(errors="replace")
        if "did not match any files" in stderr:
            return False
        raise RuntimeError(f"git archive {ref} -- {path} failed: {stderr[-2000:]}")
    tar = subprocess.run(["tar", "-x", "-C", str(dest)], input=proc.stdout, capture_output=True)
    if tar.returncode != 0:
        raise RuntimeError(f"tar extract of {ref} -- {path} archive failed: {tar.stderr.decode(errors='replace')[-2000:]}")
    return True


def archive_ref(project: Path, ref: str, dest: Path) -> None:
    """csrc/ and tests/ from `ref`, extracted into dest as two independent
    `git archive` calls (never one combined pathspec: git archive fails its
    ENTIRE invocation, csrc included, if any one pathspec in the same call
    matches nothing -- a real risk for `tests` alone on a throwaway fixture
    ref). Never touches or depends on the working tree's own current file
    contents; csrc/ missing is a real harness error (nothing to analyze),
    tests/ missing is not (an empty tested-symbols set, not a crash)."""
    dest.mkdir(parents=True, exist_ok=True)
    if not _archive_path(project, ref, "csrc", dest):
        raise RuntimeError(f"{ref} has no tracked files under csrc/")
    _archive_path(project, ref, "tests", dest)


def compute_unreachable(project: Path, ref: str, allowlist_path: Path, *,
                         include_reads: bool = False) -> tuple[dict[str, str], int]:
    """({symbol: one calling test file}, n_tested_public_symbols) for every
    tested public header symbol that is not reachable, not allowlisted, and
    (unless include_reads) not a read accessor by name. The two callers
    (`run`, the absolute/bare mode; `regression`, the base-vs-candidate
    mode) both just need this one ref's own unreachable set."""
    with tempfile.TemporaryDirectory(prefix="reach_lint_src_") as scratch:
        scratch_path = Path(scratch)
        archive_ref(project, ref, scratch_path)
        csrc_dir = scratch_path / "csrc"
        tests_dir = scratch_path / "tests"
        if not csrc_dir.is_dir():
            raise RuntimeError(f"{ref} has no csrc/ directory")
        header_path = csrc_dir / "ouroboros_sim.h"
        if not header_path.is_file():
            # A harness fault (nothing to check), not a lint finding -- a
            # fixture/scratch repo with a csrc/ but no public header (e.g.
            # merge_gate.sh's own minimal test fixtures, which carry only a
            # stub .c file) has no public API surface for this lint to
            # reason about at all.
            raise RuntimeError(f"{ref}'s csrc/ has no ouroboros_sim.h")

        header_text = header_path.read_text()
        public_symbols = header_public_symbols(header_text)

        pipe_c = csrc_dir / "pipe" / "om_pipe.c"
        pipe_dispatch_names = dispatch_call_names(pipe_c.read_text()) if pipe_c.is_file() else set()

        graph = build_callgraph(csrc_dir)
        roots = resolve_roots(graph, pipe_dispatch_names, "csrc/pipe/om_pipe.c")
        reachable = reachable_from(graph, roots)

        tested = tested_symbols(tests_dir) if tests_dir.is_dir() else {}
        allowlist = load_allowlist(allowlist_path)

        tested_public = {s: files for s, files in tested.items() if s in public_symbols}

        unreachable: dict[str, str] = {}
        for sym in sorted(tested_public):
            if sym in reachable:
                continue
            if sym in allowlist:
                continue
            if not include_reads and is_read_accessor(sym):
                continue
            unreachable[sym] = tested_public[sym][0]
        return unreachable, len(tested_public)


def run(project: Path, ref: str, allowlist_path: Path, *,
        include_reads: bool = False) -> tuple[list[dict], int]:
    """Absolute/bare mode: every finding at `ref` on its own. Returns
    (findings, n_tested_public_symbols). Each finding is {"symbol": str,
    "test_file": str}."""
    unreachable, n_tested = compute_unreachable(project, ref, allowlist_path, include_reads=include_reads)
    findings = [{"symbol": s, "test_file": unreachable[s]} for s in sorted(unreachable)]
    return findings, n_tested


def regression(project: Path, base_ref: str, candidate_ref: str, allowlist_path: Path, *,
               include_reads: bool = False) -> tuple[list[dict], dict[str, str], dict[str, str]]:
    """(new_findings, before_map, after_map). Mirrors suite_regression.py's
    compare_runs: new_findings = after's unreachable set MINUS before's. A
    symbol already unreachable on `base_ref` is a pre-existing finding this
    candidate did not create (not counted); a symbol the candidate newly
    tests that comes up unreachable is never in `before` at all, so the set
    difference reports it for free -- both cases the brief asks for
    ("unreachable in the candidate but reachable in the base, or new and
    unreachable") collapse to the one set operation."""
    before, _ = compute_unreachable(project, base_ref, allowlist_path, include_reads=include_reads)
    after, _ = compute_unreachable(project, candidate_ref, allowlist_path, include_reads=include_reads)
    new_syms = sorted(set(after) - set(before))
    findings = [{"symbol": s, "test_file": after[s]} for s in new_syms]
    return findings, before, after


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="reach_lint.py",
        description="Reachability gate: every tested public sim symbol must be reachable "
                     "from om_world_step, om_tactical_step, the time-jump entry, or a pipe "
                     "handler, or be in reach_allowlist.toml. Bare, this is an absolute "
                     "report (everything tested-but-unreachable at --ref); with --base-ref, "
                     "it is a regression gate (only what's newly unreachable versus the base).",
    )
    ap.add_argument("--ref", default="HEAD", help="git ref to analyze (default: HEAD)")
    ap.add_argument("--base-ref", default=None,
                     help="if given, report only symbols unreachable at --ref that were "
                          "reachable (or untested) at this base ref -- a regression gate, "
                          "mirroring suite_regression.py's before/after comparison. Omit "
                          "for the full absolute list at --ref alone.")
    ap.add_argument("--project", default=str(REPO), help="repo root (default: this checkout)")
    ap.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST),
                     help="path to reach_allowlist.toml")
    ap.add_argument("--include-reads", action="store_true",
                     help="do not exempt om_*_get_*/*_count/*_is_*/*_has_* read-accessor "
                          "names; show the full unreachable set, reads included")
    args = ap.parse_args(argv)

    try:
        if args.base_ref:
            findings, before, after = regression(
                Path(args.project), args.base_ref, args.ref, Path(args.allowlist),
                include_reads=args.include_reads,
            )
        else:
            findings, n_tested = run(Path(args.project), args.ref, Path(args.allowlist),
                                      include_reads=args.include_reads)
    except RuntimeError as exc:
        print(f"reach_lint.py: HARNESS ERROR: {exc}", file=sys.stderr)
        return 2

    if args.base_ref:
        if not findings:
            print(f"REACH LINT OK (regression: {len(after)} unreachable at {args.ref}, "
                  f"{len(before)} at base {args.base_ref}, none new)")
            return 0
        for f in findings:
            print(f"NEW UNREACHABLE {f['symbol']}: tested by {f['test_file']}, unreachable at "
                  f"{args.ref}, reachable or untested at base {args.base_ref}")
        print(f"REACH LINT FAILED (regression: {len(findings)} newly unreachable; "
              f"{len(after)} total at {args.ref} vs {len(before)} at base {args.base_ref})")
        return 1

    if not findings:
        print(f"REACH LINT OK ({n_tested} tested public symbols, all reachable, allowlisted, "
              f"or read accessors)")
        return 0

    for f in findings:
        print(f"UNREACHABLE {f['symbol']}: tested by {f['test_file']}, not reachable from any root, not allowlisted")
    print(f"REACH LINT FAILED ({len(findings)} unreachable of {n_tested} tested public symbols)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
