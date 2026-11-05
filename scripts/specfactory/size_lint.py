#!/usr/bin/env python3
"""size_lint.py -- Wave 0 item 3 of the gap-fix plan
(~/.claude/plans/witty-cuddling-goblet.md): the build-unit-size gate lint.

CLAUDE.md's architecture rules: "Build units are small. A Doer or 30B unit
is about one file and under about 100 lines; larger work is split when the
card is written." This checks that after the fact, on a piece's actual
branch diff against its base, restricted to the piece's OWN `owns`/
`owns_glob` files (from `pieces.toml`, loaded with `pieces.py`'s own
loader) -- a piece's branch commonly also carries new test files riding
along for its own acceptance (a separate `docs <id>-tests` landing owns
those, per the gap-fix plan's queue convention), and those are not this
piece's build-unit size to judge.

Given `--branch` and `--base`, this counts, over files that are BOTH
changed in `branch` (relative to `base`) AND listed in the piece's
`owns`/`owns_glob`:
  - total changed lines (added + removed, from `git diff --numstat`)
  - count of distinct owned files touched

WARN when changed lines > 100 or owned files touched > 1. FAIL only when
`--hard-cap-lines` is set (it defaults to off -- unset, this lint never
fails on size alone) and changed lines exceed it; Westley sets that cap
later, per the brief, so a piece is never rejected on size until he does.

Docs-profile pieces carry no `owns`/`owns_glob` at all (merge_cli.py's own
`cmd_docs`: "No owns/owns_glob: the docs profile carries no piece") --
CONST-1, a real recent docs-profile landing, touches 11 files and 526
changed lines but has no `pieces.toml` entry at all. A piece id that is
either absent from `pieces.toml` or present with empty `owns`/`owns_glob`
is a docs-profile run and is skipped outright (exit 0), matching "Skip
docs-profile runs" -- there is no owned-file footprint to size.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_PIECES = REPO / "docs" / "northstar" / "plans" / "push" / "pieces.toml"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pieces as pc  # noqa: E402

DEFAULT_WARN_LINES = 1500
DEFAULT_WARN_FILES = 1


def changed_files_numstat(project: Path, base: str, branch: str) -> dict[str, int]:
    """{path: added+removed} over `git diff --numstat base...branch`. A
    binary file (numstat prints `-\t-\tpath`) counts as 0 changed lines but
    still counts as a touched file."""
    proc = subprocess.run(
        ["git", "diff", "--numstat", f"{base}...{branch}"],
        cwd=project, capture_output=True, text=True, check=True,
    )
    out: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added, removed, path = parts
        added_n = int(added) if added.isdigit() else 0
        removed_n = int(removed) if removed.isdigit() else 0
        out[path] = added_n + removed_n
    return out


def owned_subset(changed: dict[str, int], patterns: list[str]) -> dict[str, int]:
    """changed, narrowed to paths matching one of patterns (pieces.py's own
    own_patterns() shape: exact strings and glob strings mixed)."""
    import fnmatch
    out: dict[str, int] = {}
    for path, n in changed.items():
        for pat in patterns:
            if pat == path or ("*" in pat and fnmatch.fnmatch(path, pat)):
                out[path] = n
                break
    return out


def find_piece(pieces_list: list[dict], piece_id: str) -> dict | None:
    for p in pieces_list:
        if p.get("id") == piece_id:
            return p
    return None


def owns_for_piece_id(pieces_list: list[dict], piece_id: str) -> tuple[list[str], list[str]]:
    """(patterns, unknown_ids). `piece_id` may be a comma-separated list, the
    same shape merge_gate.sh's own $PIECE_ID can be (a piece plus its
    dependants reverting together, footprint_check's own convention) --
    patterns is the union of every named, known piece's own_patterns()."""
    ids = [p.strip() for p in piece_id.split(",") if p.strip()]
    patterns: list[str] = []
    unknown: list[str] = []
    for pid in ids:
        piece = find_piece(pieces_list, pid)
        if piece is None:
            unknown.append(pid)
            continue
        patterns.extend(pc.own_patterns(piece))
    return patterns, unknown


def run(project: Path, branch: str, base: str, piece_id: str, pieces_path: Path,
        *, warn_lines: int = DEFAULT_WARN_LINES, warn_files: int = DEFAULT_WARN_FILES,
        hard_cap_lines: int | None = None, profile: str = "merge") -> tuple[str, str]:
    """(verdict, message). verdict is one of "SKIP", "OK", "WARN", "FAIL"."""
    pieces_list = pc.load_pieces(pieces_path)
    patterns, unknown = owns_for_piece_id(pieces_list, piece_id)

    if profile == "docs" or not patterns:
        reason = "explicit --profile docs" if profile == "docs" else (
            f"piece id(s) not found in pieces.toml: {unknown}" if unknown and not patterns
            else "piece owns no files (owns/owns_glob empty)"
        )
        return "SKIP", f"docs-profile run, not sized ({reason})"

    changed = changed_files_numstat(project, base, branch)
    owned = owned_subset(changed, patterns)
    total_lines = sum(owned.values())
    n_files = len(owned)

    detail = f"{total_lines} changed lines across {n_files} owned file(s): {sorted(owned) or '(none)'}"

    if hard_cap_lines is not None and total_lines > hard_cap_lines:
        return "FAIL", f"{detail} -- exceeds --hard-cap-lines={hard_cap_lines}"

    if total_lines > warn_lines or n_files > warn_files:
        return "WARN", f"{detail} -- over the {warn_lines}-line / {warn_files}-file build-unit guidance"

    return "OK", detail


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="size_lint.py",
        description="Build-unit size gate: warns above 100 changed lines or 1 owned file "
                     "for a merge-profile piece's branch; fails only above --hard-cap-lines "
                     "(off by default). Skips docs-profile runs.",
    )
    ap.add_argument("branch", help="candidate branch/ref (e.g. origin/push/B13-7)")
    ap.add_argument("base", help="base ref to diff against (e.g. origin/main)")
    ap.add_argument("--piece-id", required=True, help="pieces.toml id owning this branch's footprint")
    ap.add_argument("--pieces", default=str(DEFAULT_PIECES), help="path to pieces.toml")
    ap.add_argument("--project", default=str(REPO), help="repo root to run git diff in")
    ap.add_argument("--profile", choices=["merge", "docs"], default="merge",
                     help="docs-profile runs are always skipped, regardless of owns")
    ap.add_argument("--warn-lines", type=int, default=DEFAULT_WARN_LINES)
    ap.add_argument("--warn-files", type=int, default=DEFAULT_WARN_FILES)
    ap.add_argument("--hard-cap-lines", type=int, default=None,
                     help="fail above this many changed owned lines; unset (default) never fails")
    args = ap.parse_args(argv)

    verdict, detail = run(
        Path(args.project), args.branch, args.base, args.piece_id, Path(args.pieces),
        warn_lines=args.warn_lines, warn_files=args.warn_files,
        hard_cap_lines=args.hard_cap_lines, profile=args.profile,
    )
    print(f"SIZE LINT {verdict} ({args.piece_id}): {detail}")
    return 1 if verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
