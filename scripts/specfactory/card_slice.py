#!/usr/bin/env python3
"""Mechanically generates an Agora card's `## Header slice` -- the verbatim
excerpt of csrc/ouroboros_sim.h a worker needs to see -- instead of a human
hand-copying declarations out of the header.

Collects every om_*/OM_* identifier the card could plausibly need (the
acceptance tests' symbols, the card's own snippet_symbol list, every om_*/OM_*
token in the "## Brief for DeepSeek" prose, and every identifier used inside
the current bodies of the snippet_symbol functions), then pulls from the
header, verbatim: #define lines, whole typedef struct/enum blocks that define
or mention one of those identifiers, matching function prototypes, and the
banner comment glued directly above each. Prototype parameter types get one
extra level of closure (e.g. selecting om_faction_candidates pulls in
om_world and om_candidate even though "om_world" never appears as a token
anywhere else).

Usage:
    scripts/specfactory/card_slice.py <card_file> [--project <path>] [--write]

Prints the slice under a `## Header slice` heading. With --write, splices it
into the card file (replacing an existing `## Header slice` section, or
appending one after `## Brief for DeepSeek`).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from green_check import parse_card  # noqa: E402
from card_lint import (  # noqa: E402
    collect_acceptance_symbols, find_function_span, _split_list,
)

SOFT_LINE_BUDGET = 150

IDENT_RE = re.compile(r"\b(?:om_[A-Za-z0-9_]*|OM_[A-Za-z0-9_]*)\b")
COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
BANNER_RE = re.compile(r"/\*[ \t]*-{3,}.*?\*/", re.S)
DEFINE_RE = re.compile(r"^[ \t]*#define[ \t]+([A-Za-z_]\w*)\b[^\n]*$", re.M)
OPAQUE_TYPEDEF_RE = re.compile(r"^typedef\s+struct\s+(\w+)\s+(\w+)\s*;\s*$", re.M)
TYPEDEF_START_RE = re.compile(r"typedef\s+(?:struct|enum)\b[^{;]*\{")
PROTO_RE = re.compile(
    r"^[ \t]*(?!#|typedef\b|/\*|\*)[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*;"
    r"[ \t]*(?:/\*.*?\*/)?[ \t]*$",
    re.M,
)
BRIEF_HEADING_RE = re.compile(r"^## Brief for DeepSeek\s*$", re.M)
HEADER_SLICE_HEADING_RE = re.compile(r"^## Header slice\s*$", re.M)
NEXT_HEADING_RE = re.compile(r"^## ", re.M)


# ---- identifier collection ----

def section_text(card_text: str, heading_re: re.Pattern) -> str:
    m = heading_re.search(card_text)
    if not m:
        return ""
    start = m.end()
    next_m = NEXT_HEADING_RE.search(card_text, start)
    end = next_m.start() if next_m else len(card_text)
    return card_text[start:end]


def collect_identifiers(card: dict, card_text: str, project: Path) -> set[str]:
    ids: set[str] = set()

    symbols, _bad = collect_acceptance_symbols(card, project)
    ids |= symbols

    ids |= set(_split_list(card.get("snippet_symbol", "")))

    brief = section_text(card_text, BRIEF_HEADING_RE)
    ids |= set(IDENT_RE.findall(brief))

    snippet_file = card.get("snippet_file", "")
    if snippet_file:
        snippet_path = project / snippet_file
        if snippet_path.is_file():
            snippet_text = snippet_path.read_text()
            for name in _split_list(card.get("snippet_symbol", "")):
                span = find_function_span(snippet_text, name)
                if span:
                    ids |= set(IDENT_RE.findall(snippet_text[span[0]:span[1]]))

    return ids


# ---- header parsing ----

def _find_typedef_blocks(text: str) -> list[dict]:
    blocks = []
    for m in TYPEDEF_START_RE.finditer(text):
        brace_start = m.end() - 1
        depth = 0
        i = brace_start
        end_brace = None
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end_brace = i
                    break
            i += 1
        if end_brace is None:
            continue
        tail_m = re.match(r"\s*([A-Za-z_]\w*)\s*;", text[end_brace + 1:])
        if not tail_m:
            continue
        end = end_brace + 1 + tail_m.end()
        blocks.append({"start": m.start(), "end": end, "name": tail_m.group(1)})
    return blocks


def _in_span(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(s <= pos < e for s, e in spans)


def parse_header_items(header_text: str) -> tuple[list[dict], list[tuple[int, int]]]:
    comment_spans = [(m.start(), m.end()) for m in COMMENT_RE.finditer(header_text)]
    banners = [(m.start(), m.end()) for m in BANNER_RE.finditer(header_text)]

    items: list[dict] = []

    for m in DEFINE_RE.finditer(header_text):
        if _in_span(m.start(), comment_spans):
            continue
        items.append({"start": m.start(), "end": m.end(), "names": {m.group(1)}, "kind": "define"})

    for m in OPAQUE_TYPEDEF_RE.finditer(header_text):
        items.append({
            "start": m.start(), "end": m.end(),
            "names": {m.group(1), m.group(2)}, "kind": "type", "own_name": m.group(2),
        })

    for blk in _find_typedef_blocks(header_text):
        body = header_text[blk["start"]:blk["end"]]
        names = {blk["name"]} | set(IDENT_RE.findall(body))
        items.append({"start": blk["start"], "end": blk["end"], "names": names,
                      "kind": "type", "own_name": blk["name"]})

    for m in PROTO_RE.finditer(header_text):
        if _in_span(m.start(), comment_spans):
            continue
        items.append({"start": m.start(), "end": m.end(), "names": {m.group(1)}, "kind": "proto",
                      "own_name": m.group(1), "text": m.group(0)})

    items.sort(key=lambda it: it["start"])
    return items, banners


def select_items(items: list[dict], ids: set[str]) -> list[dict]:
    selected = [it for it in items if it["names"] & ids]

    type_by_name: dict[str, dict] = {}
    for it in items:
        if it["kind"] == "type":
            type_by_name[it["own_name"]] = it

    selected_ids = {id(it) for it in selected}
    for it in list(selected):
        if it["kind"] != "proto":
            continue
        for tok in set(re.findall(r"\b[A-Za-z_]\w*\b", it["text"])):
            cand = type_by_name.get(tok)
            if cand and id(cand) not in selected_ids:
                selected.append(cand)
                selected_ids.add(id(cand))

    selected.sort(key=lambda it: it["start"])
    return selected


def attach_banner(item: dict, banners: list[tuple[int, int]], header_text: str) -> str | None:
    for bs, be in banners:
        if be <= item["start"] and header_text[be:item["start"]].strip() == "":
            return header_text[bs:be]
    return None


def build_slice(header_text: str, ids: set[str]) -> str:
    items, banners = parse_header_items(header_text)
    selected = select_items(items, ids)

    pieces = []
    for it in selected:
        banner = attach_banner(it, banners, header_text)
        text = header_text[it["start"]:it["end"]]
        pieces.append(f"{banner}\n{text}" if banner else text)

    slice_text = "\n\n".join(p.rstrip("\n") for p in pieces)
    return slice_text + ("\n" if slice_text else "")


def verify_verbatim(slice_text: str, header_text: str) -> list[str]:
    header_lines = {line.strip() for line in header_text.splitlines()}
    bad = []
    for line in slice_text.splitlines():
        stripped = line.strip()
        if stripped and stripped not in header_lines:
            bad.append(line)
    return bad


# ---- card splicing ----

def render_section(slice_text: str) -> str:
    return "## Header slice\n\n```c\n" + slice_text.rstrip("\n") + "\n```\n"


def splice_into_card(card_text: str, section: str) -> str:
    m = HEADER_SLICE_HEADING_RE.search(card_text)
    if m:
        start = m.start()
        next_m = NEXT_HEADING_RE.search(card_text, m.end())
        end = next_m.start() if next_m else len(card_text)
        return card_text[:start] + section + ("\n" if not section.endswith("\n\n") else "") + card_text[end:]

    m = BRIEF_HEADING_RE.search(card_text)
    if m:
        next_m = NEXT_HEADING_RE.search(card_text, m.end())
        insert_at = next_m.start() if next_m else len(card_text)
        prefix = card_text[:insert_at]
        if not prefix.endswith("\n\n"):
            prefix = prefix.rstrip("\n") + "\n\n"
        return prefix + section + "\n" + card_text[insert_at:]

    return card_text.rstrip("\n") + "\n\n" + section


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("card_file")
    ap.add_argument("--project", help="defaults to the card's project: field")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    card_path = Path(args.card_file)
    if not card_path.is_file():
        print(f"card not found: {card_path}", file=sys.stderr)
        return 2

    card_text = card_path.read_text()
    try:
        card = parse_card(card_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    project = Path(args.project).expanduser() if args.project else Path(card.get("project", "")).expanduser()
    if not project.is_dir():
        print(f"project is not a directory: {project}", file=sys.stderr)
        return 2

    header_file = card.get("header_file") or "csrc/ouroboros_sim.h"
    header_path = project / header_file
    if not header_path.is_file():
        print(f"header_file not found: {header_path}", file=sys.stderr)
        return 2
    header_text = header_path.read_text()

    ids = collect_identifiers(card, card_text, project)
    slice_text = build_slice(header_text, ids)

    bad = verify_verbatim(slice_text, header_text)
    if bad:
        print("INTERNAL CHECK FAILED: non-verbatim line(s) in generated slice:", file=sys.stderr)
        for line in bad:
            print(f"  {line}", file=sys.stderr)
        return 2

    n_lines = slice_text.count("\n") + (1 if slice_text and not slice_text.endswith("\n") else 0)
    if n_lines > SOFT_LINE_BUDGET:
        print(f"warning: header slice is {n_lines} lines (soft budget {SOFT_LINE_BUDGET})", file=sys.stderr)

    section = render_section(slice_text)

    if args.write:
        new_card_text = splice_into_card(card_text, section)
        card_path.write_text(new_card_text)
    else:
        print(section)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
