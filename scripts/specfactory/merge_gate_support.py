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
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import suite_regression as sr  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DEFAULT_PIECES = REPO / "docs/northstar/plans/push/pieces.toml"
DEFAULT_SIGNATURES = REPO / "docs/northstar/spec_factory/signatures.toml"
DEFAULT_SYMBOL_MODULES = REPO / "docs/northstar/spec_factory/symbol_modules.toml"

DEFAULT_IGNORES = (".swarm/**", ".claude/**", "logs/**",
    # manager-mode artefacts that ride along with a leaf commit: the adapter
    # test and the per-piece spec are M0-reviewed documents, never a footprint
    "tests/push/**", "docs/northstar/plans/push/specs/**",
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


def _load_pieces(pieces_path: Path) -> dict[str, dict]:
    data = tomllib.loads(Path(pieces_path).read_text())
    return {p["id"]: p for p in data.get("piece", []) if p.get("id")}


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
        ["git", "diff", "--name-only", f"{base_ref}..HEAD"],
        cwd=str(candidate_dir), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git diff --name-only {base_ref}..HEAD failed: {proc.stderr}")
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
    unknown = [pid for pid in piece_ids if pid not in pieces]
    if unknown:
        return False, f"unknown piece id(s) {unknown} (not in {pieces_path})"

    owns: list[str] = []
    owns_glob: list[str] = []
    for pid in piece_ids:
        owns.extend(pieces[pid].get("owns", []) or [])
        owns_glob.extend(pieces[pid].get("owns_glob", []) or [])

    raw = changed_files(candidate_dir, base_ref)
    normalized = sorted({_norm_gd_uid(p) for p in raw if not _ignored(p, ignores)})

    extra = [p for p in normalized if not _matches_owns(p, owns, owns_glob)]
    missing = [p for p in owns if p not in normalized]

    if extra:
        return False, f"diff touches files outside {piece_id}'s owns: {extra}"
    if missing:
        return True, f"OK (owned files with no diff yet, fine for a partial increment): {missing}"
    return True, "OK"


def _diff_added_definitions(candidate_dir: Path, base_ref: str) -> list[tuple[str, str]]:
    """[(file, symbol), ...] for every `+` line in `git diff base_ref..HEAD`
    matching DEF_RE (a top-level-looking C function definition whose name
    starts with om_) -- a line-level heuristic, not a real C parse, exactly
    as the spec names it ("parse + lines for `^[a-z_ ]+ om_[a-z0-9_]+\\(`
    definitions")."""
    proc = subprocess.run(
        ["git", "diff", "-U0", f"{base_ref}..HEAD"],
        cwd=str(candidate_dir), capture_output=True, text=True,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"git diff -U0 {base_ref}..HEAD failed: {proc.stderr}")

    found: list[tuple[str, str]] = []
    current_file = None
    for line in proc.stdout.splitlines():
        if line.startswith("+++ "):
            path = line[4:]
            current_file = None if path == "/dev/null" else path[2:] if path.startswith("b/") else path
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:]
        if not DEF_RE.match(body):
            continue
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
    piece = pieces.get(piece_id)
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


def _normalize_worktree_paths(text: str, *roots: Path) -> str:
    for root in roots:
        text = text.replace(str(root), "<WORKTREE>")
    return text


def regression_check(candidate_dir: Path, base_ref: str, test_args: list[str], *,
                      python_exe: str = sr.DEFAULT_PYTHON, timeout: int = 600,
                      junit: bool = True, worktree_root: Path | None = None) -> tuple[bool, str, sr.RegressionReport]:
    """(ok, detail, report). Runs `test_args` against `base_ref` (a throwaway
    `git worktree add --detach` sibling of `candidate_dir`, never the live
    checkout, removed before returning) and against `candidate_dir` itself
    (already checked out at the candidate's HEAD, already built by the
    gate's earlier `make` step), then compares with
    suite_regression.compare_runs. `test_args` must be all-tests/csim or
    all-tests/qa/t1 -- never mixed (the two directories' bare-named
    conftest.py files collide in one pytest invocation; the caller is
    responsible for the two separate calls this implies)."""
    worktree_root = Path(worktree_root) if worktree_root else Path(tempfile.gettempdir())
    tmp = worktree_root / f"merge_gate_before_{uuid.uuid4().hex[:10]}"
    add = subprocess.run(["git", "worktree", "add", "--detach", str(tmp), base_ref],
                          cwd=str(candidate_dir), capture_output=True, text=True)
    if add.returncode != 0:
        return False, f"could not create base-ref worktree at {base_ref}: {add.stderr[-800:]}", None
    try:
        with tempfile.TemporaryDirectory(prefix="merge_gate_junit_") as jtmp:
            before_xml = Path(jtmp) / "before.xml" if junit else None
            after_xml = Path(jtmp) / "after.xml" if junit else None
            before = sr.run_pytest(tmp, python_exe, test_args, timeout, junit_path=before_xml)
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
        # both worktree roots to one placeholder before comparing.
        before.first_assertion = {k: _normalize_worktree_paths(v, tmp, candidate_dir)
                                   for k, v in before.first_assertion.items()}
        after.first_assertion = {k: _normalize_worktree_paths(v, tmp, candidate_dir)
                                  for k, v in after.first_assertion.items()}
        report = sr.compare_runs(before, after)
        # A red test whose first assertion line moves is a WARN, not a reject:
        # an attached piece legitimately changes how a still-unbuilt test fails
        # (B3 moved test_E16_S111's failing line by changing the checksum path).
        # Only new red ids and rising skip/xfail counts reject.
        accept = not report.new_failures and report.skipped_increase <= 0 and report.xfailed_increase <= 0
        if accept:
            detail = f"OK ({after.passed}p/{after.failed}f)"
            if report.changed_assertions:
                detail += f" WARN changed assertions: {report.changed_assertions}"
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
            detail = "; ".join(parts)
        return accept, detail, report
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(tmp)],
                        cwd=str(candidate_dir), capture_output=True, text=True)


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

    ut = sub.add_parser("undertest")
    ut.add_argument("candidate_dir")
    ut.add_argument("base_ref")
    ut.add_argument("piece_id")
    ut.add_argument("--pieces", default=str(DEFAULT_PIECES))
    ut.add_argument("--cap", type=int, default=10)

    rg = sub.add_parser("regression")
    rg.add_argument("candidate_dir")
    rg.add_argument("base_ref")
    rg.add_argument("test_args", nargs="+")
    rg.add_argument("--python", default=sr.DEFAULT_PYTHON)
    rg.add_argument("--timeout", type=int, default=600)
    rg.add_argument("--no-junit", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "footprint":
        ok, detail = footprint_check(Path(args.candidate_dir), args.base_ref, args.piece_id,
                                      pieces_path=Path(args.pieces))
    elif args.cmd == "symbols":
        ok, detail = symbol_ownership_check(Path(args.candidate_dir), args.base_ref,
                                             signatures_path=Path(args.signatures),
                                             symbol_modules_path=Path(args.symbol_modules))
    elif args.cmd == "undertest":
        lines = undertest_warn(Path(args.candidate_dir), args.base_ref, args.piece_id,
                                pieces_path=Path(args.pieces), cap=args.cap)
        for line in lines:
            print(f"WARN {line}")
        return 0
    else:
        ok, detail, _report = regression_check(Path(args.candidate_dir), args.base_ref, args.test_args,
                                                 python_exe=args.python, timeout=args.timeout,
                                                 junit=not args.no_junit)
    print(f"{'OK' if ok else 'REJECT'} {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
