#!/usr/bin/env python3
"""F6 item 4 (two-day push): validates docs/northstar/plans/push/pieces.toml,
the per-piece attach unit `merge_gate.sh`/`merge_cli.py` read from.

Three checks:
  unique ids       -- no two [[piece]] blocks share an id.
  owns disjoint     -- no two pieces' `owns`/`owns_glob` overlap unless one is
                       in the other's transitive `depends_on` chain (a piece
                       and its wave-3 `b` follow-up intentionally share a
                       file, sequenced by depends_on so they never run
                       concurrently -- that is not a conflict).
  acceptance collects -- every pytest-style acceptance id collects
                       (`pytest --collect-only`); a `.gd` entry is checked for
                       file existence only, since Godot tests run through
                       scripts/run_godot_tests.sh, not pytest collection.
                       `tests_pending = true` on a piece downgrades a missing
                       acceptance path from FAIL to WARN, for a piece whose
                       tests are named in the plan but not written yet.

tests/csim and tests/qa/t1 each carry their own bare-named conftest.py, and
running both directories in one pytest invocation fails collection for every
tests/csim file (ImportError: the wrong conftest module answers first) --
this is a fenced, load-bearing fact of the harness (two-day-push plan,
"Facts that shaped the method"), not a bug this tool works around
by guessing; entries are grouped by root and collected in separate
invocations, one per root, never mixed.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_PIECES = REPO / "docs/northstar/plans/push/pieces.toml"
DEFAULT_PYTHON = "/home/westopoli/Projects/agora/.venv/bin/python"
ROOTS = ("tests/csim", "tests/qa/t1", "tests/qa/desktop", "tests/transport", "tests/specfactory")
# Record folders every shot-carrying piece writes into (the Westley shot page and its
# copies, docs/northstar/story_reviews/westley/README.md): shared by rule, so a piece
# may list them in owns without an owns-overlap finding, and the footprint fence ignores
# them (merge_gate_support.DEFAULT_IGNORES). Record files every landing appends rows to
# (ledger, register, decisions, decision-pack batch, lane review pages) have no owner either.
# See also: HARNESS-westley-folder, HARNESS-record-files.
SHARED_RECORD_GLOBS = (
    "docs/northstar/story_reviews/westley/*",
    "docs/northstar/plans/push_ledger_2026-09-22.md",
    "docs/northstar/ambiguity_register.md",
    "docs/northstar/story_reviews/westley/decisions.md",
    "docs/northstar/plans/decision_pack_2026-10-18/batch.md",
    "docs/northstar/story_reviews/*.md",
)


def load_pieces(path: Path) -> list[dict]:
    data = tomllib.loads(Path(path).read_text())
    return list(data.get("piece", []))


def own_patterns(piece: dict) -> list[str]:
    return list(piece.get("owns", []) or []) + list(piece.get("owns_glob", []) or [])


def _glob_prefix(pattern: str) -> str:
    idx = pattern.find("*")
    return pattern if idx == -1 else pattern[:idx]


def is_shared_record(pattern: str) -> bool:
    return any(fnmatch.fnmatch(pattern, g) for g in SHARED_RECORD_GLOBS)


def patterns_overlap(a: str, b: str) -> bool:
    if is_shared_record(a) and is_shared_record(b):
        return False
    if a == b:
        return True
    a_glob, b_glob = "*" in a, "*" in b
    if not a_glob and not b_glob:
        return False
    if a_glob and not b_glob:
        return fnmatch.fnmatch(b, a)
    if b_glob and not a_glob:
        return fnmatch.fnmatch(a, b)
    pa, pb = _glob_prefix(a), _glob_prefix(b)
    return pa.startswith(pb) or pb.startswith(pa)


def transitive_depends(by_id: dict[str, dict], piece_id: str) -> set[str]:
    seen: set[str] = set()
    stack = list(by_id.get(piece_id, {}).get("depends_on", []) or [])
    while stack:
        dep = stack.pop()
        if dep in seen:
            continue
        seen.add(dep)
        if dep in by_id:
            stack.extend(by_id[dep].get("depends_on", []) or [])
    return seen


def check_unique_ids(pieces: list[dict]) -> list[tuple[str, str, str]]:
    findings = []
    seen: set[str] = set()
    for p in pieces:
        pid = p.get("id")
        if not pid:
            findings.append(("FAIL", "?", "a [[piece]] block has no id"))
            continue
        if pid in seen:
            findings.append(("FAIL", pid, f"duplicate piece id {pid!r}"))
        seen.add(pid)
    return findings


def check_owns_disjoint(pieces: list[dict]) -> list[tuple[str, str, str]]:
    findings = []
    by_id = {p["id"]: p for p in pieces if p.get("id")}
    ids = list(by_id)
    for i, pid in enumerate(ids):
        for qid in ids[i + 1:]:
            p, q = by_id[pid], by_id[qid]
            for pa in own_patterns(p):
                for pb in own_patterns(q):
                    if not patterns_overlap(pa, pb):
                        continue
                    chain_p = transitive_depends(by_id, pid)
                    chain_q = transitive_depends(by_id, qid)
                    if qid in chain_p or pid in chain_q:
                        continue
                    findings.append((
                        "FAIL", f"{pid}/{qid}",
                        f"owns overlap with no depends_on ordering between them: "
                        f"{pid} owns {pa!r}, {qid} owns {pb!r}",
                    ))
    return findings


def check_depends_acyclic(pieces: list[dict]) -> list[tuple[str, str, str]]:
    """FAIL for each cycle among the depends_on edges of the rows present,
    named `A -> B -> ... -> A`. Ids that are not rows present are ignored.
    # See also: check_owns_disjoint, which skips an overlap on a transitive
    # chain and so needs this pass to keep that chain acyclic."""
    findings = []
    by_id = {p["id"]: p for p in pieces if p.get("id")}
    done: set[str] = set()

    def walk(pid: str, path: list[str]) -> None:
        if pid in path:
            cycle = path[path.index(pid):] + [pid]
            findings.append(("FAIL", pid, "depends_on cycle: " + " -> ".join(cycle)))
            return
        if pid in done:
            return
        for dep in by_id[pid].get("depends_on", []) or []:
            if dep in by_id:
                walk(dep, path + [pid])
        done.add(pid)

    for pid in by_id:
        walk(pid, [])
    return findings


def _root_of(entry: str) -> str | None:
    for r in ROOTS:
        if entry == r or entry.startswith(r + "/"):
            return r
    return None


def _real_collect(python_exe: str, project: Path, node_ids: list[str], timeout: int) -> tuple[int, str]:
    proc = subprocess.run(
        [python_exe, "-m", "pytest", "--collect-only", "-q", *node_ids],
        cwd=str(project), capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout + proc.stderr


_ERROR_FILE_RE = re.compile(r"^ERROR (?:collecting )?(\S+?)(?:::.*)?\s*$", re.M)


def check_acceptance(pieces: list[dict], project: Path, *, python_exe: str = DEFAULT_PYTHON,
                      timeout: int = 300, collector=None) -> list[tuple[str, str, str]]:
    """`tests_pending = true` on a piece means its acceptance is not
    expected to be green yet in EITHER of two ways: the file may not exist
    at all, or (the more common case once the design lane authors a fenced
    test ahead of the piece's own build) the file exists but fails to
    COLLECT because it imports the piece's own not-yet-built module (e.g.
    tests/qa/t1/test_rts_detectors.py's own `from scripts.qa.rts_detectors
    import ...  # expected red: module does not exist yet`) -- both are
    WARN, never FAIL, for such a piece; a collection failure on a piece
    WITHOUT tests_pending set is a real defect (FAIL)."""
    collector = collector or (lambda node_ids, root: _real_collect(python_exe, project, node_ids, timeout))
    findings: list[tuple[str, str, str]] = []
    by_root: dict[str, list[tuple[str, str]]] = {}
    pending_by_pid: dict[str, bool] = {}

    for p in pieces:
        pid = p.get("id", "?")
        pending = bool(p.get("tests_pending"))
        pending_by_pid[pid] = pending
        for entry in p.get("acceptance", []) or []:
            if entry.endswith(".gd"):
                if not (project / entry).is_file():
                    level = "WARN" if pending else "FAIL"
                    findings.append((level, pid, f"acceptance godot script missing: {entry}"))
                continue
            root = _root_of(entry)
            if root is None:
                findings.append(("WARN", pid, f"acceptance entry is not under a known pytest root, not collected: {entry}"))
                continue
            file_part = entry.split("::", 1)[0]
            if not (project / file_part).exists():
                level = "WARN" if pending else "FAIL"
                findings.append((level, pid, f"acceptance path does not exist: {entry}"))
                continue
            by_root.setdefault(root, []).append((pid, entry))

    for root, entries in sorted(by_root.items()):
        node_ids = sorted({e for _, e in entries})
        rc, output = collector(node_ids, root)
        if rc in (0, 5):
            continue
        bad_files = set(_ERROR_FILE_RE.findall(output))
        for pid, entry in entries:
            file_part = entry.split("::", 1)[0]
            if not bad_files or file_part in bad_files or any(file_part in b or b in file_part for b in bad_files):
                level = "WARN" if pending_by_pid.get(pid) else "FAIL"
                findings.append((level, pid, f"acceptance id did not collect ({root} batch rc={rc}): {entry}"))

    return findings


def run_check(pieces_path: Path, project: Path, *, python_exe: str = DEFAULT_PYTHON,
              timeout: int = 300, collector=None) -> tuple[list[tuple[str, str, str]], int]:
    pieces = load_pieces(pieces_path)
    findings = []
    findings += check_unique_ids(pieces)
    findings += check_owns_disjoint(pieces)
    findings += check_depends_acyclic(pieces)
    findings += check_acceptance(pieces, project, python_exe=python_exe, timeout=timeout, collector=collector)
    fail_count = sum(1 for f in findings if f[0] == "FAIL")
    return findings, len(pieces)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pieces", default=str(DEFAULT_PIECES))
    ap.add_argument("--project", default=str(REPO))
    ap.add_argument("--python", default=DEFAULT_PYTHON)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--check", action="store_true", help="run all validations (the only mode; kept as a flag for the caller's clarity)")
    args = ap.parse_args(argv)

    findings, n_pieces = run_check(Path(args.pieces), Path(args.project),
                                    python_exe=args.python, timeout=args.timeout)
    for level, pid, msg in findings:
        print(f"{level} {pid}: {msg}")
    fail_count = sum(1 for f in findings if f[0] == "FAIL")
    if fail_count:
        print(f"PIECES CHECK FAILED ({fail_count})")
        return 1
    print(f"PIECES CHECK OK ({n_pieces} pieces)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
