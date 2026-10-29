#!/usr/bin/env python3
"""F6 item 1 helpers for scripts/specfactory/merge_gate.sh: the two checks
that need more than a shell one-liner (the footprint fence and the
symbol-ownership lint). Kept as a separate, directly-testable module so
merge_gate.sh's own logic stays a thin sequence of calls; the tools this
reads (pieces.toml, signatures.toml, symbol_modules.toml) always come from
the repo running the gate (GATE_DIR's own ancestor), never from the
candidate worktree being gated -- a leaf cannot edit any of them.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
import struct
import uuid
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import suite_regression as sr  # noqa: E402
from red_check import is_placeholder_control  # noqa: E402
from pieces import SHARED_RECORD_GLOBS  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DEFAULT_PIECES = REPO / "docs/northstar/plans/push/pieces.toml"
DEFAULT_SIGNATURES = REPO / "docs/northstar/spec_factory/signatures.toml"
DEFAULT_PLACEHOLDERS = REPO / "docs/northstar/spec_factory/placeholder_controls.txt"
DEFAULT_SYMBOL_MODULES = REPO / "docs/northstar/spec_factory/symbol_modules.toml"

DEFAULT_IGNORES = (".swarm/**", ".claude/**", "logs/**",
    # manager-mode artefacts that ride along with a leaf commit: the adapter
    # test and the per-piece spec are M0-reviewed documents, never a footprint
    "tests/push/**", "docs/northstar/plans/push/specs/**",
    # manager-mode's per-clone config (manager mode, not the leaf) -- a leaf
    # commit sometimes sweeps this in from the shared worktree; never a piece's
    # own footprint. See also: B10-1 merge reject 2026-09-22, owns ['csrc/...']
    ".claude-swarm.toml",
    # the Westley shot page and its copies: written by every shot-carrying piece in turn,
    # shared by rule. See also: pieces.SHARED_RECORD_GLOBS, HARNESS-westley-folder
    *SHARED_RECORD_GLOBS,
)
# A C return type: any run of qualifier/type words (const, static, unsigned,
# a `_t` typedef, an om_-prefixed struct/enum name, ...) plus optional
# pointer stars, anchored at column 0 -- a call inside a body always has
# leading whitespace or a statement keyword (`return`, ...) that is not
# itself a type word, so neither can match here.
_TYPE_WORD = (
    r"(?:const|static|unsigned|signed|struct|volatile|extern|inline|"
    r"void|int|char|float|double|short|long|bool|"
    r"[A-Za-z_][A-Za-z0-9_]*_t|om_[A-Za-z0-9_]+)"
)
DEF_RE = re.compile(rf"^(?:{_TYPE_WORD}[ \t]+)+[ \t]*\**[ \t]*\bom_[a-z0-9_]+\s*\(")
SYMBOL_RE = re.compile(r"\b(om_[a-z0-9_]+)\s*\(")

# GDScript requires class_name at column 0 (or right after an annotation,
# which this line-anchored match does not need to handle -- annotations are
# their own line). Anchoring at ^ with re.MULTILINE means a `class_name`
# inside a comment (`# class_name Foo`) or a string literal embedded mid-line
# never matches, since neither starts its line at column 0 with the bare word.
CLASS_NAME_RE = re.compile(r"^class_name\s+(\w+)", re.MULTILINE)
# 2026-09-22 defect: a merge worktree under runs/merge/ in the integrator
# clone, or any ad hoc worktree (`.swarm`'s own or elsewhere), holds a full
# second copy of every .gd file -- walked without this filter, every class
# would double and the check would reject clean trees.
GD_CLASS_IGNORE_DIRS = {".godot", "build", ".swarm", "runs", "worktrees"}


def _gd_path_ignored(parts: tuple[str, ...]) -> bool:
    return any(p in GD_CLASS_IGNORE_DIRS for p in parts)


def gd_class_names_check(root: Path) -> tuple[bool, str]:
    """(ok, detail). Walks every *.gd file under `root` (skipping
    GD_CLASS_IGNORE_DIRS at any depth) and maps each `^class_name NAME`
    declaration to the file(s) that declare it. Godot's global class
    registry means two scripts both naming themselves e.g. GalaxyGen
    silently shadow each other -- a `--script` test run against a candidate
    worktree with no `.godot/` class cache does not catch this (2026-09-22:
    C2 passed the gate this way and was red on main), but any project that
    imports both scripts does. ok=False names every duplicate, one line
    each, `NAME: path1, path2`."""
    root = Path(root)
    declarations: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.gd")):
        rel = path.relative_to(root)
        if _gd_path_ignored(rel.parts):
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for m in CLASS_NAME_RE.finditer(text):
            declarations.setdefault(m.group(1), []).append(str(rel))

    dups = {name: paths for name, paths in sorted(declarations.items()) if len(paths) > 1}
    if dups:
        lines = [f"{name}: {', '.join(paths)}" for name, paths in dups.items()]
        return False, "\n".join(lines)
    return True, f"{len(declarations)} classes unique"


def sig_blocked_check(project: Path, table: Path) -> tuple[bool, str]:
    """(ok, detail). Runs `sig_table --report` and fails on any BLOCKED item;
    detail is the BLOCKED lines (the indented block under `BLOCKED (N):`)."""
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "sig_table.py"),
         "--project", str(project), "--table", str(table), "--report"],
        capture_output=True, text=True)
    lines: list[str] = []
    in_block = False
    for line in proc.stdout.splitlines():
        if line.startswith("BLOCKED"):
            in_block = True
        elif in_block and line.startswith(" "):
            lines.append(line.strip())
        else:
            in_block = False
    if lines:
        return False, "\n".join(lines)
    if proc.returncode != 0:
        return False, f"sig_table --report failed (rc={proc.returncode}): {proc.stderr.strip()}"
    return True, "no BLOCKED signatures"


def sig_check(project: Path, table: Path) -> tuple[bool, str]:
    """(ok, detail). Runs `sig_table --check`: fails when --emit would change a file;
    detail names the stale files."""
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "sig_table.py"),
         "--project", str(project), "--table", str(table), "--check"],
        capture_output=True, text=True)
    if proc.returncode == 0:
        return True, "signature artifacts emit-clean"
    for line in proc.stdout.splitlines():
        if line.startswith("stale:"):
            return False, f"sig_table --emit would change: {line[len('stale:'):].strip()}"
    return False, f"sig_table --check failed (rc={proc.returncode}): {(proc.stdout + proc.stderr).strip()}"


def _load_pieces(pieces_path: Path) -> dict[str, dict]:
    data = tomllib.loads(Path(pieces_path).read_text())
    return {p["id"]: p for p in data.get("piece", []) if p.get("id")}


_INCREMENT_RE = re.compile(r"^(.*)-\d+$")


def resolve_piece_id(piece_id: str, pieces: dict[str, dict]) -> str:
    """The push plan's straggler rule lets a leaf submit an increment as
    branch `push/<piece>-<n>` (e.g. `push/C2-1`, `push/B10-2`). Every gate
    step and lookup that reads pieces.toml by piece id resolves such an id to
    its base piece here: strip one trailing `-<digits>` when `piece_id` is
    not itself a piece and the stripped id is (`C2-1` -> `C2`, `B10-2` ->
    `B10`; `B15m` stays `B15m` since it has no trailing `-<digits>`; an id
    that is already a piece is returned as-is). Unresolvable ids (no base
    piece either) are returned unchanged so the caller's own unknown-id
    check still rejects them."""
    if piece_id in pieces:
        return piece_id
    m = _INCREMENT_RE.match(piece_id)
    if m and m.group(1) in pieces:
        return m.group(1)
    return piece_id


def _norm_gd_uid(path: str) -> str:
    """`X.gd.uid` counts as `X.gd` for the footprint fence (decision 8):
    Godot regenerates a script's `.uid` sidecar whenever it re-imports the
    script, so a diff that only touches `foo.gd.uid` (never `foo.gd` itself)
    would otherwise look like an out-of-scope file the piece doesn't own."""
    if path.endswith(".gd.uid"):
        return path[: -len(".uid")]
    return path


def _ignored(path: str, ignores: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in ignores)


def changed_files(candidate_dir: Path, base_ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=str(candidate_dir), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git diff --name-only {base_ref}...HEAD failed: {proc.stderr}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _matches_owns(path: str, owns: list[str], owns_glob: list[str]) -> bool:
    if path in owns:
        return True
    return any(fnmatch.fnmatch(path, pat) for pat in owns_glob)


def footprint_check(candidate_dir: Path, base_ref: str, piece_id: str, *,
                     pieces_path: Path = DEFAULT_PIECES,
                     ignores: tuple[str, ...] = DEFAULT_IGNORES) -> tuple[bool, str]:
    """(ok, detail). ok=True iff the normalized, ignore-filtered diff set
    equals the union of owns/owns_glob for `piece_id` exactly -- extra files
    the diff touched but no named piece owns, AND owned files with no diff
    at all, are both named in `detail` (a piece that owns a file but never
    changed it is not itself wrong, so this only WARNs about that half; an
    extra file is the real reject). `piece_id` may be a comma-separated list
    (merge_cli.py's `revert`: a piece plus its dependants revert together in
    one candidate, so the fence must check the union of everything named,
    not any one piece alone)."""
    pieces = _load_pieces(pieces_path)
    piece_ids = [p.strip() for p in piece_id.split(",") if p.strip()]
    resolved_ids = [resolve_piece_id(pid, pieces) for pid in piece_ids]
    unknown = [pid for pid, rid in zip(piece_ids, resolved_ids) if rid not in pieces]
    if unknown:
        return False, f"unknown piece id(s) {unknown} (not in {pieces_path})"

    label = ",".join(pid if pid == rid else f"{pid} -> {rid}"
                      for pid, rid in zip(piece_ids, resolved_ids))

    owns: list[str] = []
    owns_glob: list[str] = []
    for rid in resolved_ids:
        owns.extend(pieces[rid].get("owns", []) or [])
        owns_glob.extend(pieces[rid].get("owns_glob", []) or [])

    raw = changed_files(candidate_dir, base_ref)
    normalized = sorted({_norm_gd_uid(p) for p in raw if not _ignored(p, ignores)})

    extra = [p for p in normalized if not _matches_owns(p, owns, owns_glob)]
    missing = [p for p in owns if p not in normalized]

    if extra:
        return False, f"diff touches files outside {label}'s owns: {extra}"
    if missing:
        return True, f"OK (owned files with no diff yet, fine for a partial increment): {missing}"
    return True, "OK"


_COMMENT_RE = re.compile(r"/\*.*?\*/|//.*")


def _in_block_comment_lines(text: str) -> set[int]:
    """1-based numbers of lines that start inside a /* ... */ comment."""
    inside: set[int] = set()
    open_ = False
    for n, line in enumerate(text.splitlines(), 1):
        if open_:
            inside.add(n)
        rest = line
        while rest:
            i = rest.find("*/" if open_ else "/*")
            if i < 0:
                break
            open_ = not open_
            rest = rest[i + 2:]
    return inside


def _diff_added_definitions(candidate_dir: Path, base_ref: str) -> list[tuple[str, str]]:
    """[(file, symbol), ...] for every `+` line in `git diff base_ref...HEAD`
    matching DEF_RE (a top-level-looking C function definition whose name
    starts with om_) -- a line-level heuristic, not a real C parse, exactly
    as the spec names it ("parse + lines for `^[a-z_ ]+ om_[a-z0-9_]+\\(`
    definitions")."""
    proc = subprocess.run(
        ["git", "diff", "-U0", f"{base_ref}...HEAD"],
        cwd=str(candidate_dir), capture_output=True, text=True,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"git diff -U0 {base_ref}...HEAD failed: {proc.stderr}")

    found: list[tuple[str, str]] = []
    current_file = None
    in_comment: set[int] = set()
    lineno = 0
    for line in proc.stdout.splitlines():
        if line.startswith("+++ "):
            path = line[4:]
            current_file = None if path == "/dev/null" else path[2:] if path.startswith("b/") else path
            shown = subprocess.run(["git", "show", f"HEAD:{current_file}"], cwd=str(candidate_dir),
                                   capture_output=True, text=True) if current_file else None
            in_comment = _in_block_comment_lines(shown.stdout) if shown and shown.returncode == 0 else set()
            continue
        if line.startswith("@@"):
            lineno = int(re.search(r"\+(\d+)", line).group(1)) - 1
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        lineno += 1
        if lineno in in_comment:
            continue  # text inside a block comment is never a definition
        body = _COMMENT_RE.sub("", line[1:])
        if not DEF_RE.match(body) or body.rstrip().endswith(";"):
            continue  # a line ending in ';' is an extern/prototype, not a definition
        m = SYMBOL_RE.search(body)
        if m and current_file:
            found.append((current_file, m.group(1)))
    return found


def _symbol_module_map(signatures_path: Path, symbol_modules_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if Path(signatures_path).is_file():
        sig = tomllib.loads(Path(signatures_path).read_text())
        for s in sig.get("symbols", []):
            if s.get("name") and s.get("module"):
                mapping[s["name"]] = s["module"]
    if Path(symbol_modules_path).is_file():
        sm = tomllib.loads(Path(symbol_modules_path).read_text())
        mapping.update(sm.get("symbols", {}))
    return mapping


def symbol_ownership_check(candidate_dir: Path, base_ref: str, *,
                            signatures_path: Path = DEFAULT_SIGNATURES,
                            symbol_modules_path: Path = DEFAULT_SYMBOL_MODULES) -> tuple[bool, str]:
    """(ok, detail). Rejects a diff that defines a symbol in a file other
    than the module signatures.toml/symbol_modules.toml says owns it. A
    symbol absent from both tables is not scored either way (nothing to
    check it against) -- named as SKIP in `detail` so the caller can see it
    without it blocking the gate."""
    mapping = _symbol_module_map(signatures_path, symbol_modules_path)
    defs = _diff_added_definitions(candidate_dir, base_ref)

    violations = []
    skipped = []
    for file_path, symbol in defs:
        module = mapping.get(symbol)
        if module is None:
            skipped.append(symbol)
            continue
        file_name = Path(file_path).name
        if file_name != module:
            violations.append(f"{symbol} defined in {file_path}, owned by {module}")

    if violations:
        detail = "; ".join(violations)
        if skipped:
            detail += f" (no ownership row, not checked: {sorted(set(skipped))})"
        return False, detail
    if skipped:
        return True, f"OK (no ownership row, not checked: {sorted(set(skipped))})"
    return True, "OK" if defs else "OK (no om_* definitions in diff)"


def undertest_warn(candidate_dir: Path, base_ref: str, piece_id: str, *,
                    pieces_path: Path = DEFAULT_PIECES, cap: int = 10) -> list[str]:
    """WARN-only lines for the gate's undertest_check step (decision 8: "as
    WARN rows only. block only on lines a named rule owns" -- no rule-
    ownership table exists yet, so nothing here ever blocks). Runs
    undertest_check.mutate_diff over the FIRST added/changed om_* function
    the diff defines inside the piece's own module, against the piece's
    acceptance ids -- one function, capped mutants, to keep this bounded;
    shadow_fixture is not run here at all, since it needs a hand-authored
    perturbation (which literal to change, and the recomputed expected
    value) per test that cannot be derived generically from a diff alone.
    Any failure (build error, function not in this diff, timeout) is itself
    reported as a WARN, never raised -- this step can never reject."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import undertest_check as utc  # noqa: E402

    pieces = _load_pieces(pieces_path)
    resolved_id = resolve_piece_id(piece_id, pieces)
    piece = pieces.get(resolved_id)
    if piece is None:
        return [f"undertest_check skipped: unknown piece id {piece_id!r}"]
    acceptance = [a for a in (piece.get("acceptance") or []) if a.endswith(".py") or "::" in a]
    if not acceptance:
        return ["undertest_check skipped: no pytest acceptance ids on this piece"]

    owns = set(piece.get("owns", []) or [])
    try:
        defs = _diff_added_definitions(candidate_dir, base_ref)
    except RuntimeError as exc:
        return [f"undertest_check skipped: {exc}"]
    own_defs = [(f, s) for f, s in defs if f in owns]
    if not own_defs:
        return ["undertest_check skipped: no new/changed om_* definition in this piece's own owns"]

    file_path, symbol = own_defs[0]
    try:
        result = utc.mutate_diff(base_ref, "HEAD", file_path, symbol, acceptance,
                                  project=candidate_dir, cap=cap)
    except Exception as exc:  # noqa: BLE001 -- advisory only, never blocks the gate
        return [f"undertest_check skipped ({symbol}): {exc}"]

    if result["verdict"] == "UNDER_TESTED":
        lines = [f"undertest_check UNDER_TESTED {symbol} in {file_path}: "
                 f"{result['survived']}/{result['total_mutants']} mutants survived"]
        for s in result["survivors"][:5]:
            lines.append(f"  survivor: line {s['line']} {s['mutation']}: {s['text']!r}")
        return lines
    return [f"undertest_check OK {symbol} in {file_path}: "
            f"{result['killed']}/{result['total_mutants']} mutants killed"]


def acceptance_ids(piece_id: str, *, pieces_path: Path = DEFAULT_PIECES) -> tuple[list[str], list[str]]:
    """(pytest_ids, godot_ids) for a piece's acceptance list. A pytest id is
    anything pytest can collect directly (a `.py` path, a `::`-qualified node
    id, or one of the three bare directory names the gate already runs
    whole) -- the exact filter merge_gate.sh's step 7 used inline before this
    function existed. A `.gd` id is a Godot test script, run through
    scripts/run_godot_tests.sh instead: pytest cannot collect it, so before
    this split it was silently never run for a client piece (C2, C7) whose
    acceptance is entirely Godot tests (2026-09-22 defect)."""
    pieces = _load_pieces(pieces_path)
    piece = pieces.get(resolve_piece_id(piece_id, pieces))
    if piece is None:
        return [], []
    pytest_ids: list[str] = []
    godot_ids: list[str] = []
    for a in piece.get("acceptance") or []:
        if a.endswith(".gd"):
            godot_ids.append(a)
        elif a.endswith(".py") or "::" in a or a in ("tests/transport", "tests/qa/t1", "tests/csim"):
            pytest_ids.append(a)
    return pytest_ids, godot_ids


def piece_controls(piece_ids: list[str], pieces_path: Path, project: Path) -> list[Path]:
    """Controls of the pieces' epics: an acceptance path `.../test_E<NN>_...` selects
    tests/csim/controls/test_control_e<NN>_*.py in `project`. No E<NN> path, no controls."""
    pieces = _load_pieces(pieces_path)
    epics: set[str] = set()
    for pid in piece_ids:
        piece = pieces.get(resolve_piece_id(pid, pieces))
        for a in (piece or {}).get("acceptance") or []:
            m = re.search(r"test_E(\d+)_", a)
            if m:
                epics.add(m.group(1))
    found: set[Path] = set()
    for nn in epics:
        found.update((Path(project) / "tests/csim/controls").glob(f"test_control_e{nn}_*.py"))
    return sorted(found)


def control_liveness_check(project: Path, piece_ids: list[str], pieces_path: Path, placeholders_path: Path,
                           scratch_root: Path | None = None, python_exe: str | None = None) -> tuple[bool, str]:
    """control_liveness.py over the pieces' controls in the candidate, listed placeholders removed first.
    Rejects any DEAD; an ERROR control (cannot run at all) also rejects, since it proves nothing."""
    project = Path(project).resolve()
    listed: set[str] = set()
    if Path(placeholders_path).exists():
        listed = {ln.strip() for ln in Path(placeholders_path).read_text().splitlines()
                  if ln.strip() and not ln.strip().startswith("#")}
    controls = piece_controls(piece_ids, pieces_path, project)
    run = [c for c in controls if c.relative_to(project).as_posix() not in listed]
    skipped = len(controls) - len(run)
    if not run:
        return True, f"LIVE=0 DEAD=0 ERROR=0 placeholders_skipped={skipped}"
    scratch = Path(scratch_root) if scratch_root else Path(tempfile.mkdtemp(prefix="control_liveness."))
    proc = subprocess.run([python_exe or sys.executable, str(Path(__file__).with_name("control_liveness.py")),
                           "--project", str(project), "--scratch-root", str(scratch), "--json",
                           *(["--python", python_exe] if python_exe else []), *map(str, run)],
                          capture_output=True, text=True)
    try:
        report = json.loads(proc.stdout)
    except ValueError:
        return False, f"control_liveness.py produced no report: {(proc.stderr or proc.stdout)[:300]}"
    bad = [f"{v['verdict']} {v['control']}" for v in report["verdicts"] if v["verdict"] != "LIVE"]
    detail = (f"LIVE={report['live']} DEAD={report['dead']} ERROR={report['error']} "
              f"placeholders_skipped={skipped}" + (": " + "; ".join(bad) if bad else ""))
    return not bad, detail


def placeholder_controls_check(project: Path, placeholders_path: Path) -> tuple[bool, str]:
    """Count the candidate's placeholder controls against the list. Unlisted and stale entries reject."""
    project = Path(project).resolve()
    listed: set[str] = set()
    if Path(placeholders_path).exists():
        listed = {ln.strip() for ln in Path(placeholders_path).read_text().splitlines()
                  if ln.strip() and not ln.strip().startswith("#")}
    found = sorted(f.relative_to(project).as_posix()
                   for f in (project / "tests/csim/controls").rglob("test_*.py") if is_placeholder_control(f))
    unlisted = [p for p in found if p not in listed]
    stale = sorted(p for p in listed if p not in set(found))
    detail = f"placeholders: {len(found)} unlisted={len(unlisted)} stale={len(stale)}"
    bad = [f"UNLISTED {p}" for p in unlisted] + [f"STALE {p}" for p in stale]
    return not bad, detail + (": " + "; ".join(bad) if bad else "")


def is_increment(piece_id: str, pieces: dict[str, dict]) -> str | None:
    """The resolved base piece id iff `piece_id` is an increment of it (the
    push plan's straggler rule, `push/<piece>-<n>`) -- resolve_piece_id maps
    it to a DIFFERENT, known piece. Returns None for a full piece id (already
    in `pieces`) and for an unresolvable id (stripping `-<digits>` still
    isn't a known piece), so both keep the caller's REJECT path."""
    resolved = resolve_piece_id(piece_id, pieces)
    if resolved != piece_id and resolved in pieces:
        return resolved
    return None


def partition_pytest_ids(ids: list[str], failing_ids) -> tuple[list[str], list[str]]:
    """(green, red) subsets of `ids` (a piece's pytest acceptance ids: node
    ids, whole-file paths, or bare directory names) given the failing node
    ids from a pytest run of exactly those ids (sr.parse_pytest's third
    element). An id is red if it IS a failing id, or a failing id lives
    under it (`id::...` for a whole-file id, `id/...` for a directory id)."""
    failing = set(failing_ids)
    green: list[str] = []
    red: list[str] = []
    for i in ids:
        hit = i in failing or any(f.startswith(f"{i}::") or f.startswith(f"{i}/") for f in failing)
        (red if hit else green).append(i)
    return green, red


def partition_godot_ids(ids: list[str], log_text: str) -> tuple[list[str], list[str]]:
    """(green, red) subsets of `ids` (Godot test script paths) given
    run_godot_tests.sh's own combined stdout/stderr log, which prints
    exactly one `PASS: res://<path>` line per script that passed (no
    suffix -- `FAIL: res://<path> (exit N)` and the not-found line both
    fail the exact match). An id missing from the log entirely (e.g. a
    timeout cut the run short before it ran) counts red."""
    passed = {line[len("PASS: "):].strip() for line in log_text.splitlines()
              if line.startswith("PASS: res://")}
    green: list[str] = []
    red: list[str] = []
    for i in ids:
        res = i if i.startswith("res://") else f"res://{i.lstrip('./')}"
        (green if res in passed else red).append(i)
    return green, red


def acceptance_warn_detail(piece_id: str, resolved_id: str, green: list[str],
                            total_ids: list[str], red: list[str]) -> str:
    return (f"increment {piece_id} of {resolved_id}: {len(green)}/{len(total_ids)} "
            f"acceptance ids green; red: {red[:5]}")


def _normalize_worktree_paths(text: str, *roots: Path) -> str:
    for root in roots:
        text = text.replace(str(root), "<WORKTREE>")
    return text


SCALE_LIST_REL = "docs/northstar/plans/push/scale_gated_tests.txt"


def read_scale_list(root: Path) -> set[str]:
    path = Path(root) / SCALE_LIST_REL
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text().splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")}


def _harness_sha() -> str:
    """Content hash of suite_regression.py -- folded into every cache entry
    so a harness change (new comparison rule, new junit parsing) invalidates
    every baseline cached under the old behaviour, even though the main sha
    the file name is keyed on hasn't moved."""
    return hashlib.sha256(Path(__file__).with_name("suite_regression.py").read_bytes()).hexdigest()[:16]


def _baseline_cache_path(merge_root: Path, main_sha: str) -> Path:
    shared = os.environ.get("MERGE_GATE_BASELINE_CACHE")
    if shared:
        return Path(shared) / f"{main_sha}.json"
    return Path(merge_root) / "baseline_cache" / f"{main_sha}.json"


def _load_cached_baseline(cache_path: Path, harness_sha: str, suite_key: str) -> sr.RunResult | None:
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text())
    except (OSError, ValueError):
        return None
    if data.get("harness_sha") != harness_sha:
        return None
    entry = data.get("suites", {}).get(suite_key)
    if entry is None or "scale_gated" not in entry:
        return None
    return sr.RunResult(passed=entry["passed"], failed=entry["failed"],
                         failing_ids=tuple(entry["failing_ids"]), wall_s=0.0,
                         returncode=entry["returncode"], first_assertion=dict(entry["first_assertion"]),
                         skipped=entry["skipped"], xfailed=entry["xfailed"],
                         scale_gated=tuple(entry["scale_gated"]))


def _store_cached_baseline(cache_path: Path, harness_sha: str, main_sha: str,
                            suite_key: str, result: sr.RunResult) -> None:
    data = {"main_sha": main_sha, "harness_sha": harness_sha, "suites": {}}
    if cache_path.exists():
        try:
            existing = json.loads(cache_path.read_text())
            if existing.get("harness_sha") == harness_sha and existing.get("main_sha") == main_sha:
                data = existing
        except (OSError, ValueError):
            pass
    data.setdefault("suites", {})[suite_key] = {
        "passed": result.passed, "failed": result.failed,
        "failing_ids": list(result.failing_ids), "returncode": result.returncode,
        "first_assertion": dict(result.first_assertion),
        "skipped": result.skipped, "xfailed": result.xfailed,
        "scale_gated": list(result.scale_gated),
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(data))
    tmp_path.replace(cache_path)


def regression_check(candidate_dir: Path, base_ref: str, test_args: list[str], *,
                      python_exe: str = sr.DEFAULT_PYTHON, timeout: int = 600,
                      junit: bool = True, worktree_root: Path | None = None,
                      merge_root: Path | None = None,
                      before_build: list[str] | None = None) -> tuple[bool, str, sr.RegressionReport]:
    """(ok, detail, report). Runs `test_args` against `base_ref` (a throwaway
    `git worktree add --detach` sibling of `candidate_dir`, never the live
    checkout, removed before returning) and against `candidate_dir` itself
    (already checked out at the candidate's HEAD, already built by the
    gate's earlier `make` step), then compares with
    suite_regression.compare_runs. `test_args` must be all-tests/csim or
    all-tests/qa/t1 -- never mixed (the two directories' bare-named
    conftest.py files collide in one pytest invocation; the caller is
    responsible for the two separate calls this implies).

    `merge_root`, when given: the base-ref run is identical for every
    candidate gated against the same main commit, so before building and
    running it, look for `<merge_root>/baseline_cache/<main_sha>.json`
    (main_sha = base_ref resolved from candidate_dir, no worktree needed for
    that) with a matching harness_sha (_harness_sha, invalidates on a
    suite_regression.py change) and a `suites[test_args joined]` entry; if
    found, reuse it as `before` and skip the worktree build + pytest run
    entirely. Otherwise run as without caching and write the entry after.
    Prints one `baseline: cached <sha>` or `baseline: computed <sha>` line.
    Omitted, behaviour is unchanged (no cache read or write).

    `before_build`, when given: run as a subprocess in the base-ref worktree
    right before the pytest call, on a fresh (non-cached) baseline only.
    tests/csim and tests/qa/t1 self-build inside their own conftest.py
    (mirrors the proving-ground conftest -- see tests/csim/conftest.py's
    `_build_libs`), so both sides of the comparison are always apples to
    apples there. tests/transport has no such fixture: `pipe/ouroboros_pipe`
    is built once, by the gate script, only in `candidate_dir` -- the
    base-ref worktree never gets it, so every transport test there
    `skipif`s instead of running. A skip-before/fail-after pair reads as a
    brand new failure to compare_runs even when the candidate changed
    nothing transport-related and the same test would already fail against
    main's own build (2026-09-24 false rejects: B5-3, B9-1-2, both far
    outside tests/transport's owners, both rejected on the same two ids that
    pass clean against a freshly built main). A failed `before_build` is not
    raised -- the base-ref worktree just keeps skipping, same as before this
    parameter existed, so an unbuilt dependency (T1 not yet attached, no
    om_pipe.c on main yet) degrades to the old behaviour instead of crashing
    the gate."""
    suite_key = " ".join(test_args)
    if os.environ.get("MALLOC_PERTURB_"):
        # the gate perturbs the csim and transport stages; a perturbed baseline is not an unperturbed one.
        # See also: MALLOC_PERTURB_=255 on the csim and transport commands of merge_gate.sh
        suite_key += f" MALLOC_PERTURB_={os.environ['MALLOC_PERTURB_']}"
    main_sha = None
    cache_path = None
    harness_sha = None
    cached_before = None
    if merge_root is not None:
        rev = subprocess.run(["git", "rev-parse", "--verify", "-q", base_ref],
                              cwd=str(candidate_dir), capture_output=True, text=True)
        if rev.returncode == 0:
            main_sha = rev.stdout.strip()
            harness_sha = _harness_sha()
            cache_path = _baseline_cache_path(Path(merge_root), main_sha)
            cached_before = _load_cached_baseline(cache_path, harness_sha, suite_key)

    worktree_root = Path(worktree_root) if worktree_root else Path(tempfile.gettempdir())
    tmp = None
    if cached_before is not None:
        before = cached_before
        print(f"baseline: cached {main_sha}")
    else:
        tmp = worktree_root / f"merge_gate_before_{uuid.uuid4().hex[:10]}"
        add = subprocess.run(["git", "worktree", "add", "--detach", str(tmp), base_ref],
                              cwd=str(candidate_dir), capture_output=True, text=True)
        if add.returncode != 0:
            return False, f"could not create base-ref worktree at {base_ref}: {add.stderr[-800:]}", None
        if main_sha is None:
            rev2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(tmp),
                                   capture_output=True, text=True)
            main_sha = rev2.stdout.strip() if rev2.returncode == 0 else base_ref
        print(f"baseline: computed {main_sha}")
        if before_build:
            build = subprocess.run(before_build, cwd=str(tmp), capture_output=True, text=True, timeout=timeout)
            status = "ok" if build.returncode == 0 else f"failed (rc={build.returncode})"
            print(f"baseline before_build {' '.join(before_build)}: {status}")
    try:
        with tempfile.TemporaryDirectory(prefix="merge_gate_junit_") as jtmp:
            after_xml = Path(jtmp) / "after.xml" if junit else None
            if tmp is not None:
                before_xml = Path(jtmp) / "before.xml" if junit else None
                before = sr.run_pytest(tmp, python_exe, test_args, timeout, junit_path=before_xml)
                # See regression_check's cache comment above: normalize before
                # caching so a cached entry replayed from a since-removed `tmp`
                # already reads "<WORKTREE>", matching whatever this run's own
                # `after` normalizes its candidate_dir path down to.
                before.first_assertion = {k: _normalize_worktree_paths(v, tmp)
                                           for k, v in before.first_assertion.items()}
                if cache_path is not None:
                    _store_cached_baseline(cache_path, harness_sha, main_sha, suite_key, before)
            after = sr.run_pytest(candidate_dir, python_exe, test_args, timeout, junit_path=after_xml)
        # Every unbuilt-symbol failure (extremely common in this codebase --
        # most of E-06..E-17 is still STUB) raises a ctypes AttributeError
        # whose text embeds the .so's own absolute path
        # (".../libouroboros.so: undefined symbol: ..."). `tmp` and
        # `candidate_dir` are two different directories by construction, so
        # every such failure's first-assertion text differs between
        # before/after even when nothing about the failure itself changed --
        # found building the F6 rejection replays: a pure docs-only diff
        # came back REJECT "changed assertions" over exactly this. Normalize
        # both worktree roots to one placeholder before comparing. `before`
        # is already normalized above (freshly run) or already normalized in
        # the cache (a prior run); only `after` still needs it here.
        after.first_assertion = {k: _normalize_worktree_paths(v, Path(candidate_dir).resolve())
                                  for k, v in after.first_assertion.items()}
        report = sr.compare_runs(before, after)
        flaky: list[str] = []
        if report.new_failures:
            flaky = [t for t in report.new_failures
                     if flake_rerun(Path(candidate_dir), t, python_exe=python_exe, timeout=timeout)[0]]
            if flaky:
                report.new_failures = [t for t in report.new_failures if t not in flaky]
        # A red test whose first assertion line moves is a WARN, not a reject:
        # an attached piece legitimately changes how a still-unbuilt test fails
        # (B3 moved test_E16_S111's failing line by changing the checksum path).
        # Only new red ids and rising skip/xfail counts reject.
        unlisted = sorted(set(after.scale_gated) - read_scale_list(candidate_dir))
        accept = (not report.new_failures and report.skipped_increase <= 0
                  and report.xfailed_increase <= 0 and not unlisted)
        scale_part = f"scale-gated: {len(after.scale_gated)}" if after.scale_gated else ""
        if accept:
            detail = f"OK ({after.passed}p/{after.failed}f)"
            if scale_part:
                detail += f"; {scale_part}"
            if report.changed_assertions:
                detail += f" WARN changed assertions: {report.changed_assertions}"
            if flaky:
                detail += f" WARN flake (passed on re-run): {flaky}"
        else:
            parts = []
            if report.new_failures:
                parts.append(f"new failures: {report.new_failures}")
            if report.changed_assertions:
                parts.append(f"changed assertions (warn): {report.changed_assertions}")
            if report.skipped_increase > 0:
                parts.append(f"skipped +{report.skipped_increase}")
            if report.xfailed_increase > 0:
                parts.append(f"xfailed +{report.xfailed_increase}")
            if unlisted:
                parts.append(f"scale-gated tests missing from {SCALE_LIST_REL}: {unlisted}")
            if scale_part:
                parts.append(scale_part)
            detail = "; ".join(parts)
        return accept, detail, report
    finally:
        if tmp is not None:
            subprocess.run(["git", "worktree", "remove", "--force", str(tmp)],
                            cwd=str(candidate_dir), capture_output=True, text=True)


FLAKE_RERUNS = 2


def flake_rerun(candidate_dir: Path, test_id: str, *, python_exe: str = sr.DEFAULT_PYTHON,
                timeout: int = 600) -> tuple[bool, str]:
    """(passed, detail). Re-runs only `test_id`, at most FLAKE_RERUNS times, stopping
    at the first pass. See also: regression_check, which drops new failures that pass here."""
    for n in range(1, FLAKE_RERUNS + 1):
        try:
            r = subprocess.run([python_exe, "-m", "pytest", "-q", "-p", "no:cacheprovider", test_id],
                               cwd=str(candidate_dir), capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            continue
        if r.returncode == 0:
            return True, f"flake: {test_id} red in the stage, green on re-run {n}"
    return False, f"{test_id} red on {FLAKE_RERUNS} re-runs"


def _read_png_gray(path: Path) -> list[int]:
    """Luminance per pixel of an 8-bit non-interlaced grey/RGB/RGBA PNG (stdlib only)."""
    data = path.read_bytes()
    pos, idat, w = 8, b"", 0
    h = ctype = 0
    while pos < len(data):
        n = int.from_bytes(data[pos:pos + 4], "big")
        tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        if tag == b"IHDR":
            w, h, depth, ctype, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace or ctype not in (0, 2, 6):
                raise ValueError(f"unsupported PNG layout in {path}")
        elif tag == b"IDAT":
            idat += body
        pos += 12 + n
    bpp = {0: 1, 2: 3, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * bpp
    prev = bytearray(stride)
    pix: list[int] = []
    for y in range(h):
        ft = raw[y * (stride + 1)]
        row = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = row[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:
                row[i] = (row[i] + a) & 255
            elif ft == 2:
                row[i] = (row[i] + b) & 255
            elif ft == 3:
                row[i] = (row[i] + ((a + b) >> 1)) & 255
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                row[i] = (row[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = row
        for x in range(w):
            px = row[x * bpp:x * bpp + bpp]
            pix.append(px[0] if bpp == 1 else (px[0] * 299 + px[1] * 587 + px[2] * 114) // 1000)
    return pix


def frame_busyness(path: Path) -> float:
    """Fraction of pixels differing from the frame's most common luminance (0 = blank)."""
    pix = _read_png_gray(path)
    if not pix:
        return 0.0
    counts: dict[int, int] = {}
    for v in pix:
        counts[v] = counts.get(v, 0) + 1
    return 1.0 - max(counts.values()) / len(pix)


def look_check(cand_dir: Path, base_dir: Path) -> tuple[str, list[str]]:
    """('OK'|'WARN', lines). Same-named PNGs are the same play moment; a candidate frame
    blanker than main's is flagged. Warn-only until Westley's threshold lands (spec G1)."""
    flagged: list[str] = []
    compared = 0
    for cf in sorted(Path(cand_dir).glob("*.png")):
        bf = Path(base_dir) / cf.name
        if not bf.exists():
            continue
        compared += 1
        cb, bb = frame_busyness(cf), frame_busyness(bf)
        if cb < bb:
            flagged.append(f"{cf.name} busyness {cb:.4f} vs main {bb:.4f} frame {cf}")
    if flagged:
        return "WARN", flagged
    return "OK", [f"{compared} frames compared, none blanker than main"]


LAB_TRIGGERS = ("csrc/", "scripts/skilllab/")
LAB_TARGETS = ["tests/skilllab/integration", "tests/skilllab/ground"]


def regression_lab_check(candidate_dir: Path, base_ref: str, **kw) -> tuple[bool, str]:
    """(ok, detail). The lab's real-engine suites (tests/skilllab/integration and /ground)
    under regression_csim's pass rule (failing ids equal base's); skipped unless the diff
    touches csrc/ or scripts/skilllab/. See also: merge_gate.sh stage regression_lab."""
    if not any(f.startswith(LAB_TRIGGERS) for f in changed_files(candidate_dir, base_ref)):
        return True, "skipped: diff touches neither csrc/ nor scripts/skilllab/"
    ok, detail, _report = regression_check(candidate_dir, base_ref, LAB_TARGETS, **kw)
    return ok, detail


PLAYTHROUGH_TRIGGERS = ("csrc/", "autoload/", "scenes/", "project.godot", "tests/qa/desktop/")
DEFAULT_KNOWN_RED = Path(__file__).resolve().parent / "playthrough_known_red.txt"


def playthrough_trigger(files: list[str]) -> str:
    """The changed path that makes the playthrough stage run, or ''."""
    for f in files:
        if f.startswith("scenes/mockups/"):
            continue
        if f.startswith(PLAYTHROUGH_TRIGGERS):
            return f
    return ""

# HARNESS-gate-keep-red-evidence: a red playthrough or lane_plays stage keeps its pytest -rA output and the PNGs it
# wrote under <evidence root>/<UTC start>-<piece>/<stage>/ -- outside SCRATCH_ROOT, which dies with the gate run.
# Only main() asks for it (evidence_out); the checks called bare write nothing.
# See also: merge_gate.sh (strips the EVIDENCE line, prints `GATE evidence kept:`), drift_audit.md (weekly --prune-evidence)
EVIDENCE_AGE_DAYS = 7  # DRAFT-evidence-age
EVIDENCE_CAP_BYTES = 52_428_800  # DRAFT-evidence-cap, per stage subdirectory
EVIDENCE_ENV_LINE = "env: MALLOC_PERTURB_=255 on the csim and transport stages of merge_gate.sh"


def _evidence_root() -> Path:
    return Path(os.environ.get("MERGE_GATE_EVIDENCE_ROOT") or "~/Projects/om-push/gate-evidence").expanduser()


def _evidence_run_dir() -> Path:
    import time
    start = os.environ.get("MERGE_GATE_START_UTC") or time.strftime("%Y%m%d-%H%M", time.gmtime())
    pieces = [x for x in os.environ.get("MERGE_GATE_PIECE_ID", "").split(",") if x]
    return _evidence_root() / f"{start}-{pieces[0] if pieces else 'nopiece'}"


def _qa_pngs() -> dict[Path, int]:
    """qa/*.png under XDG_DATA_HOME, symlinks never followed, with their mtimes."""
    root = os.environ.get("XDG_DATA_HOME")
    found: dict[Path, int] = {}
    for d, _dirs, files in os.walk(root, followlinks=False) if root else []:
        if os.path.basename(d) != "qa":
            continue
        for n in files:
            f = Path(d) / n
            if n.endswith(".png") and not f.is_symlink():
                found[f] = f.stat().st_mtime_ns
    return found


def _text(out) -> str:
    return out.decode("utf-8", "replace") if isinstance(out, bytes) else (out or "")


def _keep_evidence(stage: str, pytest_out: str, pngs_before: dict[Path, int], new_ids: list[str],
                   evidence_out: list) -> None:
    """Write the stage's evidence and append the run directory to evidence_out."""
    run = _evidence_run_dir()
    sub = run / stage
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "pytest_rA.txt").write_text(pytest_out)
    for f, mtime in sorted(_qa_pngs().items(), key=lambda kv: (kv[1], str(kv[0]))):
        if pngs_before.get(f) == mtime:
            continue
        dest, n = sub / f.name, 2
        while dest.exists():
            dest, n = sub / f"{f.stem}-{n}{f.suffix}", n + 1
        shutil.copy2(f, dest)
    dropped = []
    files = sorted((q for q in sub.iterdir() if q.is_file()), key=lambda q: q.stat().st_mtime)
    total = sum(q.stat().st_size for q in files)
    for q in files:
        if total <= EVIDENCE_CAP_BYTES:
            break
        total -= q.stat().st_size
        q.unlink()
        dropped.append(q.name)
    pieces = [x for x in os.environ.get("MERGE_GATE_PIECE_ID", "").split(",") if x]
    with open(run / "REPORT.txt", "a") as rep:
        rep.write(f"stage: {stage}\n")
        if len(pieces) > 1:
            rep.write(f"also in this gate run: {','.join(pieces[1:])}\n")
        rep.write(f"new red ids: {','.join(new_ids) or 'none (timeout)'}\n")
        if not os.environ.get("XDG_DATA_HOME"):
            rep.write("XDG_DATA_HOME unset: no PNGs scanned\n")
        if dropped:
            rep.write(f"dropped over the {EVIDENCE_CAP_BYTES}-byte cap: {','.join(dropped)}\n")
        rep.write(EVIDENCE_ENV_LINE + "\n\n")
    evidence_out.append(str(run))


def prune_evidence() -> list[str]:
    """Delete run directories of the evidence root older than EVIDENCE_AGE_DAYS; never touches a file, a symlink
    or a directory not named <YYYYMMDD>-<HHMM>-*."""
    import time
    root = _evidence_root()
    pruned = []
    if not root.is_dir():
        return pruned
    cutoff = time.time() - EVIDENCE_AGE_DAYS * 86400
    for e in sorted(os.scandir(root), key=lambda e: e.name):
        if e.is_dir(follow_symlinks=False) and re.match(r"[0-9]{8}-[0-9]{4}-", e.name) \
                and e.stat(follow_symlinks=False).st_mtime < cutoff:
            shutil.rmtree(e.path)
            pruned.append(str(root / e.name))
    return pruned


def playthrough_check(candidate: Path, base_ref: str, *, python_exe: str, timeout: int,
                      known_red_path: Path = DEFAULT_KNOWN_RED, target: str = "tests/qa/desktop",
                      force: bool = False, setup: bool = True, evidence_out: list | None = None) -> tuple[bool, str]:
    """Run the desktop flow suite (not its lane plays directory) on the merged tree. ok=False on any red not in
    the known-red list, a suite that collects or runs nothing, or a timeout."""
    import time
    if not force:
        trigger = playthrough_trigger(changed_files(candidate, base_ref))
        if not trigger:
            return True, "skipped: diff touches none of csrc/ autoload/ scenes/ (non-mockup) project.godot tests/qa/desktop/"
    if not (candidate / target).exists():
        return False, f"playthrough suite missing: candidate has no {target}"
    t0 = time.monotonic()
    if setup:
        mk = subprocess.run(["make", "-s", "libouroboros.so", "pipe/ouroboros_pipe"], cwd=str(candidate),
                            capture_output=True, text=True, timeout=300)
        if mk.returncode != 0 or not (candidate / "libouroboros.so").exists() \
                or not (candidate / "pipe/ouroboros_pipe").exists():
            return False, "playthrough setup failed: build " + (mk.stderr or "")[-300:]
        # import exit code left unchecked: godot prints errors yet exits 0, so it is no reliable signal
        subprocess.run(["godot", "--headless", "--path", str(candidate), "--import"],
                       capture_output=True, timeout=300)
    pngs_before = _qa_pngs() if evidence_out is not None else {}
    try:
        # lane story plays run in the lane_plays stage (HARNESS-laneplays), not here
        proc = subprocess.run([python_exe, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rA", "--color=no",
                               "--ignore=" + target.rstrip("/") + "/plays", target],
                              cwd=str(candidate), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if evidence_out is not None:
            _keep_evidence("playthrough", _text(exc.stdout), pngs_before, [], evidence_out)
        return False, f"timed out after {timeout}s"
    secs = f"{time.monotonic() - t0:.0f}s"
    # See also: playthrough_known_red.txt (the <test id> :: <row id> form)
    known = {l.split(" :: ")[0].strip() for l in known_red_path.read_text().splitlines()
             if l.strip() and not l.startswith("#") and l.split(" :: ")[0].strip()} if known_red_path.exists() else set()
    passed, red = set(), set()
    for line in proc.stdout.splitlines():
        m = re.match(r"(PASSED|FAILED|ERROR) (\S+)", line)
        if m:
            (passed if m.group(1) == "PASSED" else red).add(m.group(2).split("::")[-1].split(" ")[0])
    if not passed and not red:
        return False, f"no tests ran in {secs}: {' '.join(proc.stdout.splitlines()[-3:])}"
    # a list entry names a test by prefix (a prefix of the test function name)
    is_known = lambda t: any(t.startswith(k) for k in known)  # noqa: E731
    bad = sorted(t for t in red if not is_known(t))
    green = sorted(t for t in passed if is_known(t))
    notes = f"{len(passed)} passed, wall {secs}"
    if green:
        notes += f"; now green, remove from list: {','.join(green)}"
    if bad:
        if evidence_out is not None:
            _keep_evidence("playthrough", proc.stdout, pngs_before, bad, evidence_out)
        return False, f"red outside known-red list: {','.join(bad)} ({notes})"
    return True, f"{notes}; known red: {','.join(sorted(red)) or 'none'}"


DEFAULT_LANE_KNOWN_RED = Path(__file__).resolve().parent / "lane_plays_known_red.txt"
DEFAULT_LANE_MAP = Path(__file__).resolve().parent / "lane_plays.toml"


def lane_plays_check(candidate: Path, base_ref: str, *, python_exe: str, timeout: int,
                     known_red_path: Path = DEFAULT_LANE_KNOWN_RED, lane_map_path: Path = DEFAULT_LANE_MAP,
                     plays_dir: str = "tests/qa/desktop/plays", changed: list[str] | None = None,
                     setup: bool = True, evidence_out: list | None = None) -> tuple[bool, str]:
    """Run each touched lane's play files alone (a lane is touched by its globs, its own play files, or the
    lane_plays.toml [shared] table); red outside the known-red list, or a listed
    play that now passes, rejects."""
    files = changed if changed is not None else changed_files(candidate, base_ref)
    cfg = tomllib.loads(lane_map_path.read_text())
    lanes, shared = cfg.get("lanes", {}), cfg.get("shared", {})
    all_lanes = sorted(l for l in lanes if (candidate / plays_dir / l).is_dir())
    touched = {l for l, globs in lanes.items() if any(fnmatch.fnmatch(f, g) for f in files for g in globs)}
    touched |= {l for l in lanes if any(f.startswith(f"{plays_dir}/{l}/") for f in files)}
    for g, who in shared.items():
        # autoload/net/** belongs to F's own glob only, not the shared autoload/** glob
        if any(fnmatch.fnmatch(f, g) and not (g == "autoload/**" and f.startswith("autoload/net/")) for f in files):
            touched |= set(all_lanes) if "*" in who else set(who)
    touched = sorted(touched)
    plays = [p for l in touched if (candidate / plays_dir / l).is_dir()
             for p in sorted((candidate / plays_dir / l).glob("*.py")) if p.name != "conftest.py"
             and re.search(r"^def test_", p.read_text(), re.M)]
    if not plays:
        return True, "skipped: no lane plays touched"
    prefix = ["xvfb-run", "-a"] if setup and shutil.which("xvfb-run") else []
    env = {**os.environ, "OM_QA_RENDERER": "vulkan"}
    passed, red = set(), set()
    pngs_before = _qa_pngs() if evidence_out is not None else {}
    red_out = ""  # the output of the red plays only, each under a `### play:` header
    for play in plays:
        rel = play.relative_to(candidate).as_posix()
        try:
            proc = subprocess.run([*prefix, python_exe, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rA",
                                   "--color=no", rel], cwd=str(candidate), env=env, capture_output=True,
                                  text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            if evidence_out is not None:
                _keep_evidence("lane_plays", red_out + f"### play: {rel}\n" + _text(exc.stdout), pngs_before, [],
                               evidence_out)
            return False, f"timed out after {timeout}s: {rel}"
        found = 0
        red_before = len(red)
        for line in proc.stdout.splitlines():
            m = re.match(r"(PASSED|FAILED|ERROR) (\S+)", line)
            if m:
                found += 1
                (passed if m.group(1) == "PASSED" else red).add(m.group(2))
        if not found:
            red.add(rel + "::<nothing ran>")
        if len(red) > red_before or not found:
            red_out += f"### play: {rel}\n{proc.stdout}\n"
    known = {l.split("#")[0].strip() for l in known_red_path.read_text().splitlines()
             if l.strip() and not l.startswith("#")} if known_red_path.exists() else set()
    bad = sorted(red - known)
    if bad:
        if evidence_out is not None:
            _keep_evidence("lane_plays", red_out, pngs_before, bad, evidence_out)
        return False, f"red outside known-red list: {','.join(bad)}"
    stale = sorted(passed & known)
    if stale:
        return False, f"stale known-red, remove from list: {','.join(stale)}"
    return True, f"{len(passed)} passed, {len(red)} known red"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    fp = sub.add_parser("footprint")
    fp.add_argument("candidate_dir")
    fp.add_argument("base_ref")
    fp.add_argument("piece_id")
    fp.add_argument("--pieces", default=str(DEFAULT_PIECES))

    sy = sub.add_parser("symbols")
    sy.add_argument("candidate_dir")
    sy.add_argument("base_ref")
    sy.add_argument("--signatures", default=str(DEFAULT_SIGNATURES))
    sy.add_argument("--symbol-modules", default=str(DEFAULT_SYMBOL_MODULES))

    gc = sub.add_parser("gd-class-names")
    gc.add_argument("root")

    sb = sub.add_parser("sig-blocked")
    sb.add_argument("--project", default=str(REPO))
    sb.add_argument("--table", default=str(DEFAULT_SIGNATURES))

    sc = sub.add_parser("sig-check")
    sc.add_argument("--project", default=str(REPO))
    sc.add_argument("--table", default=None)

    ai = sub.add_parser("acceptance-ids")
    ai.add_argument("piece_id")
    ai.add_argument("--pieces", default=str(DEFAULT_PIECES))

    pt = sub.add_parser("playthrough")
    pt.add_argument("candidate_dir")
    pt.add_argument("base_ref")
    pt.add_argument("--python", default=sys.executable)
    pt.add_argument("--timeout", type=int, default=900)
    pt.add_argument("--known-red", default=str(DEFAULT_KNOWN_RED))
    pt.add_argument("--target", default="tests/qa/desktop")
    pt.add_argument("--force", action="store_true")
    pt.add_argument("--no-setup", action="store_true")

    lp = sub.add_parser("lane_plays")
    lp.add_argument("candidate_dir")
    lp.add_argument("base_ref")
    lp.add_argument("--python", default=sys.executable)
    lp.add_argument("--timeout", type=int, default=900)
    lp.add_argument("--known-red", default=str(DEFAULT_LANE_KNOWN_RED))
    lp.add_argument("--lane-map", default=str(DEFAULT_LANE_MAP))

    sub.add_parser("prune-evidence")

    rl = sub.add_parser("regression-lab")
    rl.add_argument("candidate_dir")
    rl.add_argument("base_ref")
    rl.add_argument("--python", default=sr.DEFAULT_PYTHON)
    rl.add_argument("--timeout", type=int, default=600)
    rl.add_argument("--merge-root", default=None)

    lk = sub.add_parser("look")
    lk.add_argument("candidate_frames")
    lk.add_argument("base_frames")

    fr = sub.add_parser("flake-rerun")
    fr.add_argument("candidate_dir")
    fr.add_argument("test_id")
    fr.add_argument("--python", default=sr.DEFAULT_PYTHON)
    fr.add_argument("--timeout", type=int, default=600)

    ut = sub.add_parser("undertest")
    ut.add_argument("candidate_dir")
    ut.add_argument("base_ref")
    ut.add_argument("piece_id")
    ut.add_argument("--pieces", default=str(DEFAULT_PIECES))
    ut.add_argument("--cap", type=int, default=10)

    cl = sub.add_parser("control-liveness")
    cl.add_argument("project")
    cl.add_argument("piece_ids")
    cl.add_argument("--pieces", default=str(DEFAULT_PIECES))
    cl.add_argument("--placeholders", default=str(DEFAULT_PLACEHOLDERS))
    cl.add_argument("--scratch-root", default=None)
    cl.add_argument("--python", default=None)

    pc = sub.add_parser("placeholder-controls")
    pc.add_argument("project")
    pc.add_argument("--placeholders", default=str(DEFAULT_PLACEHOLDERS))

    av = sub.add_parser("acceptance-verdict")
    av.add_argument("piece_id")
    av.add_argument("--pieces", default=str(DEFAULT_PIECES))
    av.add_argument("--ids-file", required=True)
    av.add_argument("--pytest-log")
    av.add_argument("--godot-log")

    rg = sub.add_parser("regression")
    rg.add_argument("candidate_dir")
    rg.add_argument("base_ref")
    rg.add_argument("test_args", nargs="+")
    rg.add_argument("--python", default=sr.DEFAULT_PYTHON)
    rg.add_argument("--timeout", type=int, default=600)
    rg.add_argument("--no-junit", action="store_true")
    rg.add_argument("--merge-root", default=None)
    rg.add_argument("--before-build", default=None,
                     help="shell-split command run in the base-ref worktree before its pytest call "
                          "(fresh baselines only); see regression_check's before_build docstring")

    args = ap.parse_args(argv)

    if args.cmd == "footprint":
        ok, detail = footprint_check(Path(args.candidate_dir), args.base_ref, args.piece_id,
                                      pieces_path=Path(args.pieces))
    elif args.cmd == "control-liveness":
        ok, detail = control_liveness_check(Path(args.project), args.piece_ids.split(","), Path(args.pieces),
                                            Path(args.placeholders),
                                            scratch_root=Path(args.scratch_root) if args.scratch_root else None,
                                            python_exe=args.python)
    elif args.cmd == "placeholder-controls":
        ok, detail = placeholder_controls_check(Path(args.project), Path(args.placeholders))
    elif args.cmd == "acceptance-ids":
        pytest_ids, godot_ids = acceptance_ids(args.piece_id, pieces_path=Path(args.pieces))
        for i in pytest_ids:
            print(f"PY {i}")
        for i in godot_ids:
            print(f"GD {i}")
        return 0
    elif args.cmd == "symbols":
        ok, detail = symbol_ownership_check(Path(args.candidate_dir), args.base_ref,
                                             signatures_path=Path(args.signatures),
                                             symbol_modules_path=Path(args.symbol_modules))
    elif args.cmd == "gd-class-names":
        ok, detail = gd_class_names_check(Path(args.root))
    elif args.cmd == "sig-blocked":
        ok, detail = sig_blocked_check(Path(args.project), Path(args.table))
    elif args.cmd == "sig-check":
        project = Path(args.project)
        ok, detail = sig_check(project, Path(args.table) if args.table
                               else project / "docs/northstar/spec_factory/signatures.toml")
    elif args.cmd == "acceptance-verdict":
        pieces = _load_pieces(Path(args.pieces))
        resolved = is_increment(args.piece_id, pieces)
        if resolved is None:
            print("REJECT")
            return 1
        ids = [line.strip() for line in Path(args.ids_file).read_text().splitlines() if line.strip()]
        if args.pytest_log:
            _passed, _failed, failing = sr.parse_pytest(Path(args.pytest_log).read_text())
            green, red = partition_pytest_ids(ids, failing)
        else:
            green, red = partition_godot_ids(ids, Path(args.godot_log).read_text())
        print(f"WARN {acceptance_warn_detail(args.piece_id, resolved, green, ids, red)}")
        return 0
    elif args.cmd == "prune-evidence":
        for d in prune_evidence():
            print(f"pruned: {d}")
        return 0
    elif args.cmd == "playthrough":
        evidence: list[str] = []
        ok, detail = playthrough_check(Path(args.candidate_dir), args.base_ref, python_exe=args.python,
                                       timeout=args.timeout, known_red_path=Path(args.known_red),
                                       target=args.target, force=args.force, setup=not args.no_setup,
                                       evidence_out=evidence)
    elif args.cmd == "lane_plays":
        evidence = []
        ok, detail = lane_plays_check(Path(args.candidate_dir), args.base_ref, python_exe=args.python,
                                      timeout=args.timeout, known_red_path=Path(args.known_red),
                                      lane_map_path=Path(args.lane_map), evidence_out=evidence)
    elif args.cmd == "regression-lab":
        ok, detail = regression_lab_check(Path(args.candidate_dir), args.base_ref, python_exe=args.python,
                                          timeout=args.timeout,
                                          merge_root=Path(args.merge_root) if args.merge_root else None)
    elif args.cmd == "look":
        status, lines = look_check(Path(args.candidate_frames), Path(args.base_frames))
        print(f"{status} {lines[0]}")
        for line in lines[1:]:
            print(line)
        return 0
    elif args.cmd == "flake-rerun":
        passed, detail = flake_rerun(Path(args.candidate_dir), args.test_id, python_exe=args.python,
                                     timeout=args.timeout)
        print(f"{'WARN' if passed else 'REJECT'} {detail}")
        return 0 if passed else 1
    elif args.cmd == "undertest":
        lines = undertest_warn(Path(args.candidate_dir), args.base_ref, args.piece_id,
                                pieces_path=Path(args.pieces), cap=args.cap)
        for line in lines:
            print(f"WARN {line}")
        return 0
    else:
        ok, detail, _report = regression_check(Path(args.candidate_dir), args.base_ref, args.test_args,
                                                 python_exe=args.python, timeout=args.timeout,
                                                 junit=not args.no_junit,
                                                 merge_root=Path(args.merge_root) if args.merge_root else None,
                                                 before_build=shlex.split(args.before_build)
                                                 if args.before_build else None)
    print(f"{'OK' if ok else 'REJECT'} {detail}")
    if args.cmd in ("playthrough", "lane_plays") and evidence:
        print(f"EVIDENCE {evidence[0]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
