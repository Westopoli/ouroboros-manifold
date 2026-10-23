#!/usr/bin/env python3
"""owner_lint.py -- Wave 0 item 3 of the gap-fix plan
(~/.claude/plans/witty-cuddling-goblet.md): the single-owner gate lint.

CLAUDE.md's architecture rules say every file has one owner AT A TIME:
`docs/northstar/plans/push/pieces.toml` names it, and "two in-flight pieces
never own the same file." `pieces.py`'s own `check_owns_disjoint` already
finds every `owns`/`owns_glob` overlap with no `depends_on` ordering between
the two pieces -- but it also flags an ATTACHED piece's (already-landed)
footprint against a brand-new piece that happens to reuse the same path,
which is not a conflict two in-flight pieces can actually race on (the
attached piece is already on main; nothing about it can still change
concurrently with the new one). This module reuses `check_owns_disjoint`
completely unmodified (per the brief: "do not change its behaviour") and
adds exactly the missing filter on top: keep a finding only when BOTH
pieces in the overlapping pair are in flight.

In flight: `status` is not `"attached"` (a dict `{state = "attached", ...}`
or the bare string) and not `"done"`. Every other status value (today, just
the bare string `"pending"`) counts as in flight.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_PIECES = REPO / "docs" / "northstar" / "plans" / "push" / "pieces.toml"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pieces as pc  # noqa: E402


def piece_state(piece: dict) -> str:
    """The piece's status state as a bare string, whichever of the two
    pieces.toml shapes it is written in: a bare string (`"pending"`) or a
    table (`{state = "attached", attach_sha = "..."}`)."""
    status = piece.get("status")
    if isinstance(status, dict):
        return str(status.get("state", ""))
    if isinstance(status, str):
        return status
    return ""


def is_in_flight(piece: dict) -> bool:
    return piece_state(piece) not in ("attached", "done")


def in_flight_overlaps(pieces: list[dict]) -> list[tuple[str, str, str]]:
    """check_owns_disjoint's own findings, narrowed to pairs where both
    pieces are in flight. A finding's `pair` field is always `"{pid}/{qid}"`
    (check_owns_disjoint's own format); split on the FIRST '/' only would
    break if an id itself contained '/', but piece ids never do (card_id_of/
    pieces.py's own id convention is alnum plus '-')."""
    by_id = {p["id"]: p for p in pieces if p.get("id")}
    findings = []
    for level, pair, msg in pc.check_owns_disjoint(pieces):
        pid, _, qid = pair.partition("/")
        p, q = by_id.get(pid), by_id.get(qid)
        if p is None or q is None:
            # Not a pieces-overlap finding this lint understands the shape
            # of (defensive; check_owns_disjoint today only ever emits the
            # pid/qid pair shape) -- pass it through rather than silently
            # dropping a real finding.
            findings.append((level, pair, msg))
            continue
        if is_in_flight(p) and is_in_flight(q):
            findings.append((level, pair, msg))
    return findings


def skipped_record_files(pieces: list[dict]) -> list[str]:
    """Record files (pc.SHARED_RECORD_GLOBS) listed by two or more in-flight pieces:
    in_flight_overlaps skips them, main() names them once."""
    seen: dict[str, set[str]] = {}
    for p in pieces:
        if not is_in_flight(p):
            continue
        for pat in pc.own_patterns(p):
            if pc.is_shared_record(pat):
                seen.setdefault(pat, set()).add(p.get("id", ""))
    return sorted(pat for pat, ids in seen.items() if len(ids) > 1)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="owner_lint.py",
        description="Single-owner gate: no file may be owned by two in-flight pieces "
                     "(pieces.toml status not attached and not done).",
    )
    ap.add_argument("--pieces", default=str(DEFAULT_PIECES), help="path to pieces.toml")
    args = ap.parse_args(argv)

    pieces_list = pc.load_pieces(Path(args.pieces))
    findings = in_flight_overlaps(pieces_list)

    skipped = skipped_record_files(pieces_list)
    if skipped:
        print("record files (no owner): " + ", ".join(skipped))
    for level, pair, msg in findings:
        print(f"{level} {pair}: {msg}")

    if findings:
        print(f"OWNER LINT FAILED ({len(findings)} in-flight overlap(s))")
        return 1
    print(f"OWNER LINT OK ({len(pieces_list)} pieces checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
