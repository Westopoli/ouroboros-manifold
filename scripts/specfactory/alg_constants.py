#!/usr/bin/env python3
"""Two mechanical jobs for the C rewrite's constants (F3, two-day push):

`--emit PATH`: parses every numeric constant out of docs/bible/algorithms.md's
ALG-NN paragraphs (scalars `IDENT = 8.0`, ranges `IDENT = (55, 75)`, keyed
tables `IDENT[key]: key1 v1, key2 v2`, and the doc's "formula, then trailing
labelled values" convention, e.g. "..., rate `0.5`") and writes them as
`#define OM_<IDENT> <value>` to PATH, grouped by ALG id. Never edits
algorithms.md; only reads it.

`--lint DIR`: fails on any bare numeric literal in DIR/*.c other than 0, 1,
-1, 2, an array size in a declaration, a #define line, or a sizeof(...)
argument -- so a tuned constant lands in algorithms.md and this header, not
scattered through the C. csrc/{sim,region,faction,agent,resolve}.c predate
this lint; their current literals are grandfathered by exact
file:line:col:token in docs/northstar/spec_factory/constants_allowlist.txt
(regenerate with --gen-allowlist after a deliberate change to one of them).

Both commands are deterministic and idempotent: same input, same output,
every time.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ALGORITHMS_MD = REPO / "docs" / "bible" / "algorithms.md"
ALLOWLIST_PATH = REPO / "docs" / "northstar" / "spec_factory" / "constants_allowlist.txt"
GRANDFATHERED_FILES = {"sim.c", "region.c", "faction.c", "agent.c", "resolve.c"}
ALWAYS_EXEMPT_VALUES = {0.0, 1.0, -1.0, 2.0}

# --------------------------------------------------------------------- ALG parsing

ALG_HEADER_RE = re.compile(r"\*\*(ALG-\d+[a-z]?)\s+([^*.]+)\.?\*\*")
NUM = r"-?\d+(?:\.\d+)?"


def alg_sort_key(alg_id: str) -> tuple[int, str]:
    m = re.match(r"ALG-(\d+)([a-z]?)", alg_id)
    return (int(m.group(1)), m.group(2))


class Const:
    __slots__ = ("name", "value", "alg_id", "alg_title")

    def __init__(self, name: str, value: str, alg_id: str, alg_title: str):
        self.name = name
        self.value = value
        self.alg_id = alg_id
        self.alg_title = alg_title


def split_alg_blocks(text: str) -> list[tuple[str, str, str]]:
    """[(alg_id, alg_title, block_text)] -- block_text runs from one
    `**ALG-NN ...**` marker to the next (or EOF), so untitled paragraphs
    that follow an ALG marker (e.g. "**Apply.**" after ALG-08) are treated
    as part of that ALG's block. Text before the first marker (the tick
    sequence, the preamble) is out of scope -- the task is ALG paragraphs
    only, and every constant used in the preamble is restated inside its
    owning ALG paragraph."""
    matches = list(ALG_HEADER_RE.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((m.group(1), m.group(2).strip(), text[start:end]))
    return blocks


def is_number_str(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def fmt_value(raw: str) -> str:
    """Doubles keep a decimal point at full precision; integers stay integers."""
    raw = raw.strip()
    if "." in raw:
        return raw if raw not in ("-0.0",) else "0.0"
    return raw


def strip_backticks(s: str) -> str:
    return s.replace("`", "")


def snake_upper(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s.strip()).strip("_").upper()


def looks_ambiguous_after(text: str, end: int) -> bool:
    """True if the number just matched (ending at `end`) is immediately
    followed by an arithmetic operator and then another bare number, e.g.
    "= 8.0 + 3.0" -- a compound expression, not one constant's value.
    Handled separately by the compound-assignment pattern; never guessed
    here."""
    rest = text[end:end + 12]
    return bool(re.match(r"\s*[+\-*/·×]\s*-?\d", rest))


# --- Pattern 0: compound "IDENT_A + IDENT_B = v1 + v2" (positional, same operator) ---
COMPOUND_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]*)\s*\+\s*([A-Z][A-Z0-9_]*)\s*=\s*(" + NUM + r")\s*\+\s*(" + NUM + r")\b"
)

# --- Pattern A: scalar "IDENT = NUMBER" ---
SCALAR_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*(" + NUM + r")(?!\s*[.,]?\d)")

# --- Pattern B: range "IDENT = (NUM, NUM)" ---
RANGE_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*\(\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\)"
)

# --- Pattern C: keyed paren-list without a colon: IDENT (k1 (a,b), k2 (c,d), ...) ---
KEYED_PAREN_LIST_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]{2,})\s*\(\s*((?:[a-z][a-z_]*\s*\(\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\)\s*,?\s*){2,})\)"
)
KEYED_PAREN_ITEM_RE = re.compile(r"([a-z][a-z_]*)\s*\(\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\)")

# --- Pattern D: keyed colon-list: IDENT[key] or IDENT (labels): key1 v1, key2 v2, ... ---
KEYED_COLON_HEAD_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]{2,})(?:\[[a-z_]+\](?:\[[a-z_]+\])?)?"
    r"(?:\s*\(([a-z][a-z, ]*[a-z])\))?\s*:\s*"
)
KEYED_ITEM_RE = re.compile(
    r"([a-z][a-z_]*)\s+(\(\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\)|" + NUM + r"(?:\s*/\s*" + NUM + r"){0,3})"
)
SENTENCE_END_RE = re.compile(r"[.;](?!\d)")

# --- Pattern E: bracketed list of pairs: IDENT = [(a, b), (c, d), ...] ---
BRACKET_PAIRS_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*\[\s*((?:\(\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\)\s*,?\s*)+)\]"
)
PAIR_ITEM_RE = re.compile(r"\(\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\)")

# --- Pattern F: formula backtick-span, then trailing labelled value(s) ---
# F1: one or more ", label `v`" clauses, matched to identifiers by substring.
# F2: a single ", label `v1 / v2 / ... / vN`" clause, matched positionally.
# A label's value may also be a range `(a, b)` (e.g. "range `(0.7, 1.3)`").
LABEL_VALUE = r"(?:\(\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\)|" + NUM + r"(?:\s*/\s*" + NUM + r")*)"
FORMULA_THEN_LABELS_RE = re.compile(
    r"`([^`]+)`((?:\s*,\s*[a-zA-Z][a-zA-Z \-]*`" + LABEL_VALUE + r"`)+)"
)
LABEL_ITEM_RE = re.compile(r",\s*([a-zA-Z][a-zA-Z \-]*?)\s*`(" + LABEL_VALUE + r")`")

# --- Pattern G: formula backtick-span, then a bare `= NUMBER` backtick span
# naming the value of the formula's one still-unresolved identifier, e.g.
# "`capacity = p' . ECO_POP_RATIO`, `= 0.85`." ---
FORMULA_THEN_BARE_EQ_RE = re.compile(r"`([^`]+)`\s*,\s*`=\s*(" + NUM + r")`")


def parse_scalars_and_compounds(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for m in COMPOUND_RE.finditer(block):
        out.append((m.group(1), fmt_value(m.group(3))))
        out.append((m.group(2), fmt_value(m.group(4))))
        used_spans.append(m.span())
    for m in SCALAR_RE.finditer(block):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        if looks_ambiguous_after(block, m.end()):
            continue
        out.append((m.group(1), fmt_value(m.group(2))))
        used_spans.append(m.span())
    return out


def parse_ranges(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for m in RANGE_RE.finditer(block):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        name = m.group(1)
        out.append((f"{name}_LO", fmt_value(m.group(2))))
        out.append((f"{name}_HI", fmt_value(m.group(3))))
        used_spans.append(m.span())
    return out


def parse_keyed_paren_lists(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for m in KEYED_PAREN_LIST_RE.finditer(block):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        name = m.group(1)
        for item in KEYED_PAREN_ITEM_RE.finditer(m.group(2)):
            key = snake_upper(item.group(1))
            out.append((f"{name}_{key}_LO", fmt_value(item.group(2))))
            out.append((f"{name}_{key}_HI", fmt_value(item.group(3))))
        used_spans.append(m.span())
    return out


TABLE_HEAD_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})(?:\[[a-z_]+\](?:\[[a-z_]+\])?)?[^:\n|]{0,60}:\s*")


def parse_markdown_tables(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """IDENT[key], or IDENT with a short run-up of prose (labels or a
    "for x, y, z" lead-in), then a colon and a markdown pipe table -- row
    key is the table's first column, e.g.
    OM_ARCHETYPE_TECH_MULTIPLIERS_CONQUEROR_ATTACK. A column is emitted
    only if every data row's cell in it is a bare number (ALG-11's
    tension-primary/can-colonize/recent-damage-boost columns are not, and
    are silently left out -- reported unparsed instead of guessed)."""
    out = []
    for head in TABLE_HEAD_RE.finditer(block):
        name = head.group(1)
        rest = block[head.end():]
        if not rest.lstrip().startswith("|"):
            continue
        table_start = head.end() + (len(rest) - len(rest.lstrip()))
        blank_idx = block.find("\n\n", table_start)
        table_end = blank_idx if blank_idx != -1 else len(block)
        rows = [ln for ln in block[table_start:table_end].splitlines() if ln.strip().startswith("|")]
        if len(rows) < 3:
            continue
        header = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        data_rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows[2:]]
        col_numeric = [
            all(is_number_str(row[ci]) for row in data_rows if ci < len(row))
            for ci in range(len(header))
        ]
        found = False
        for row in data_rows:
            row_key = snake_upper(row[0])
            for ci in range(1, len(header)):
                if ci < len(row) and col_numeric[ci]:
                    out.append((f"{name}_{row_key}_{snake_upper(header[ci])}", fmt_value(row[ci])))
                    found = True
        if found:
            used_spans.append((table_start, table_end))
    return out


def parse_keyed_colon_lists(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for head in KEYED_COLON_HEAD_RE.finditer(block):
        name = head.group(1)
        if block[head.end():].lstrip().startswith("|"):
            continue  # a markdown table -- parse_markdown_tables' job
        labels = [w.strip() for w in head.group(2).split(",")] if head.group(2) else None
        end_m = SENTENCE_END_RE.search(block, head.end())
        region_end = end_m.start() if end_m else len(block)
        region = block[head.end():region_end]
        items = list(KEYED_ITEM_RE.finditer(region))
        if not items:
            continue
        for item in items:
            used_spans.append((head.end() + item.start(), head.end() + item.end()))
            key = snake_upper(item.group(1))
            val = item.group(2)
            if val.startswith("("):
                lo, hi = [v.strip() for v in val.strip("()").split(",")]
                out.append((f"{name}_{key}_LO", fmt_value(lo)))
                out.append((f"{name}_{key}_HI", fmt_value(hi)))
            elif "/" in val:
                parts = [v.strip() for v in val.split("/")]
                if labels and len(labels) == len(parts):
                    for label, v in zip(labels, parts):
                        out.append((f"{name}_{key}_{snake_upper(label)}", fmt_value(v)))
                else:
                    for i, v in enumerate(parts):
                        out.append((f"{name}_{key}_{i}", fmt_value(v)))
            else:
                out.append((f"{name}_{key}", fmt_value(val)))
    return out


BRACE_ROW_IDENT_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\[[a-z_]+\]\[[a-z_]+\]")
BRACE_ROW_RE = re.compile(r"([A-Za-z][A-Za-z]*)\s*\{([^{}]+)\}")
BRACE_ITEM_RE = re.compile(r"([A-Za-z][A-Za-z]*)\s+(" + NUM + r")")


def parse_brace_matrix(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """`IDENT[a][b]` ... "Matrix: Row1 {Col1 v, Col2 v}; Row2 {Col1 v, ...}"
    (ALG-60's damage category matrix) -- one row/col-keyed constant per
    cell."""
    out = []
    for head in BRACE_ROW_IDENT_RE.finditer(block):
        name = head.group(1)
        matrix_idx = block.find("Matrix:", head.end())
        if matrix_idx == -1 or matrix_idx - head.end() > 200:
            continue
        # Rows are chained directly (`Row1 {...}; Row2 {...}; Row3 {...}`),
        # so consume consecutive "; Row {...}" groups rather than bounding
        # by a sentence end -- the rows themselves are ';'-separated.
        pos = matrix_idx + len("Matrix:")
        found = False
        while True:
            gap = re.match(r"\s*;?\s*", block[pos:])
            row_m = BRACE_ROW_RE.match(block, pos + gap.end())
            if not row_m:
                break
            row_key = snake_upper(row_m.group(1))
            for item_m in BRACE_ITEM_RE.finditer(row_m.group(2)):
                col_key = snake_upper(item_m.group(1))
                out.append((f"{name}_{row_key}_{col_key}", fmt_value(item_m.group(2))))
                found = True
            pos = row_m.end()
        if found:
            used_spans.append((matrix_idx, pos))
    return out


def parse_bracket_pairs(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for m in BRACKET_PAIRS_RE.finditer(block):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        name = m.group(1)
        pairs = PAIR_ITEM_RE.findall(m.group(2))
        out.append((f"{name}_N", str(len(pairs))))
        for i, (x, y) in enumerate(pairs):
            out.append((f"{name}_{i}_X", fmt_value(x)))
            out.append((f"{name}_{i}_Y", fmt_value(y)))
        used_spans.append(m.span())
    return out


def parse_formula_then_labels(raw_block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """Operates on the ORIGINAL (backtick-preserved) block text, since the
    formula/label split relies on backtick-span boundaries."""
    out = []
    for m in FORMULA_THEN_LABELS_RE.finditer(raw_block):
        formula = m.group(1)
        idents = re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", formula)
        if not idents:
            continue
        items = LABEL_ITEM_RE.findall(m.group(2))
        for label, val in items:
            label_key = snake_upper(label)
            if val.startswith("("):
                lo, hi = [v.strip() for v in val.strip("()").split(",")]
                candidates = sorted(set(i for i in idents if _label_matches(label_key, i)))
                if len(candidates) == 1:
                    out.append((f"{candidates[0]}_LO", fmt_value(lo)))
                    out.append((f"{candidates[0]}_HI", fmt_value(hi)))
                continue
            if "/" in val:
                parts = [v.strip() for v in val.split("/")]
                if len(parts) == len(idents):
                    for ident, v in zip(idents, parts):
                        out.append((ident, fmt_value(v)))
                continue
            candidates = sorted(set(i for i in idents if _label_matches(label_key, i)))
            if len(candidates) == 1:
                out.append((candidates[0], fmt_value(val)))
        used_spans.append(m.span())
    return out


def _label_matches(label_key: str, ident: str) -> bool:
    """True if `label_key` (already SNAKE_UPPER, possibly multi-word, e.g.
    "MAX_HOPS") occupies one or more whole underscore-delimited components
    of `ident`, e.g. "BASE" matches "BASE_BETRAYAL_RATE" and "FLOOR"
    matches "COLLISION_ECONOMY_FLOOR", but "BASE" does not match
    "DATABASE_X"."""
    return f"_{label_key}_" in f"_{ident}_" or ident == label_key


def parse_formula_then_bare_eq(raw_block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """"`formula`, `= NUMBER`." -- the value belongs to the formula's one
    identifier that has no other resolution in this same clause."""
    out = []
    for m in FORMULA_THEN_BARE_EQ_RE.finditer(raw_block):
        formula = m.group(1)
        idents = sorted(set(re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", formula)))
        if len(idents) == 1:
            out.append((idents[0], fmt_value(m.group(2))))
            used_spans.append(m.span())
    return out


def parse_algorithms_md(text: str) -> tuple[dict[str, Const], list[str], list[str]]:
    blocks = split_alg_blocks(text)
    resolved: dict[str, Const] = {}
    conflicts: list[str] = []
    all_idents_seen: set[str] = set()

    for alg_id, alg_title, raw_block in blocks:
        used_spans: list[tuple[int, int]] = []
        pairs = parse_formula_then_labels(raw_block, used_spans)
        pairs += parse_formula_then_bare_eq(raw_block, used_spans)
        block = strip_backticks(raw_block)
        used_spans = []  # spans above were in raw_block coords; stripping backticks shifts offsets, so re-derive on `block`.
        pairs += parse_bracket_pairs(block, used_spans)
        pairs += parse_brace_matrix(block, used_spans)
        pairs += parse_markdown_tables(block, used_spans)
        pairs += parse_keyed_paren_lists(block, used_spans)
        pairs += parse_keyed_colon_lists(block, used_spans)
        pairs += parse_ranges(block, used_spans)
        pairs += parse_scalars_and_compounds(block, used_spans)

        for name, val in pairs:
            out_name = f"OM_{name}"
            if out_name in resolved:
                if resolved[out_name].value != val:
                    conflicts.append(
                        f"{out_name}: {resolved[out_name].value} ({resolved[out_name].alg_id}) "
                        f"vs {val} ({alg_id})"
                    )
                continue
            resolved[out_name] = Const(out_name, val, alg_id, alg_title)

        all_idents_seen.update(re.findall(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]*[A-Z0-9]\b", block))

    resolved_bare = {c.name[3:] for c in resolved.values()}
    unparsed = sorted(
        ident for ident in all_idents_seen
        if ident not in resolved_bare
        and not any(rb.startswith(ident + "_") for rb in resolved_bare)
    )
    return resolved, unparsed, conflicts


def emit_header(consts: dict[str, Const]) -> str:
    ordered = sorted(consts.values(), key=lambda c: (alg_sort_key(c.alg_id), c.name))
    lines = [
        "/* GENERATED FILE -- do not edit by hand.",
        " * scripts/specfactory/alg_constants.py --emit csrc/om_constants.h",
        " * Source: docs/bible/algorithms.md (ALG-01..75). */",
        "#ifndef OM_CONSTANTS_H",
        "#define OM_CONSTANTS_H",
        "",
    ]
    current_alg = None
    for c in ordered:
        if c.alg_id != current_alg:
            lines.append(f"/* {c.alg_id} {c.alg_title} */")
            current_alg = c.alg_id
        lines.append(f"#define {c.name} {c.value}")
    lines.append("")
    lines.append("#endif /* OM_CONSTANTS_H */")
    lines.append("")
    return "\n".join(lines)


def cmd_emit(out_path: Path) -> int:
    text = ALGORITHMS_MD.read_text()
    consts, unparsed, conflicts = parse_algorithms_md(text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(emit_header(consts))
    print(f"emitted {len(consts)} constants to {out_path}")
    if conflicts:
        print(f"CONFLICTS ({len(conflicts)}):")
        for line in conflicts:
            print(f"  {line}")
    if unparsed:
        print(f"UNPARSED ({len(unparsed)}) -- referenced but no value mechanically extracted:")
        for name in unparsed:
            print(f"  {name}")
    return 0


# --------------------------------------------------------------------- csrc lint

DECL_PREFIX_RE = re.compile(
    r"(?:^|[;{}])\s*(?:static\s+|const\s+|volatile\s+)*[A-Za-z_]\w*\s*\**\s*[A-Za-z_]\w*\s*$"
)
DEFINE_LINE_RE = re.compile(r"^\s*#\s*define\b")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_RE = re.compile(r'"(?:[^"\\\n]|\\.)*"')
CHAR_RE = re.compile(r"'(?:[^'\\\n]|\\.)*'")
SIZEOF_RE = re.compile(r"sizeof\s*\([^()]*\)")
TOKEN_RE = re.compile(
    r"(?<![\w.])(-)?\b(\d+\.\d+(?:[eE][+-]?\d+)?[fFlL]?|\d+(?:[uUlL]*)|0[xX][0-9a-fA-F]+[uUlL]*)"
)


def _blank(m: re.Match) -> str:
    return "".join(c if c == "\n" else " " for c in m.group(0))


def strip_noise(text: str) -> str:
    text = BLOCK_COMMENT_RE.sub(_blank, text)
    text = LINE_COMMENT_RE.sub(_blank, text)
    text = STRING_RE.sub(_blank, text)
    text = CHAR_RE.sub(_blank, text)
    text = SIZEOF_RE.sub(_blank, text)
    return text


def literal_value(token: str, negative: bool) -> float:
    core = token.rstrip("uUlLfF")
    if core.lower().startswith("0x"):
        v = float(int(core, 16))
    else:
        v = float(core)
    return -v if negative else v


def find_declaration_bracket_spans(line: str) -> list[tuple[int, int]]:
    """[(start, end)] character ranges of every `[...]` on `line` that sits
    directly after a `type name` prefix -- i.e. an array size in a
    declaration, not an indexing expression."""
    spans = []
    for bm in re.finditer(r"\[([^\[\]]*)\]", line):
        prefix = line[:bm.start()]
        if DECL_PREFIX_RE.search(prefix):
            spans.append(bm.span())
        else:
            # a later dimension of the same declaration, e.g. `x[8][16]`
            trail = line[:bm.start()]
            if trail and trail[-1] == "]":
                spans.append(bm.span())
    return spans


def find_violations(text: str) -> list[tuple[int, int, str]]:
    """[(line 1-based, col 1-based, token)] for every bare numeric literal
    in `text` that is not 0, 1, -1, 2, inside a declaration's array-size
    brackets, on a #define line, or inside sizeof(...)."""
    clean = strip_noise(text)
    violations = []
    for lineno, line in enumerate(clean.splitlines(), start=1):
        if DEFINE_LINE_RE.match(line):
            continue
        decl_spans = find_declaration_bracket_spans(line)
        for m in TOKEN_RE.finditer(line):
            start = m.start(1) if m.group(1) else m.start(2)
            token = line[start:m.end(2)]
            val = literal_value(m.group(2), bool(m.group(1)))
            if val in ALWAYS_EXEMPT_VALUES:
                continue
            if any(s <= start < e for s, e in decl_spans):
                continue
            violations.append((lineno, start + 1, token))
    return violations


def load_allowlist() -> set[tuple[str, int, int, str]]:
    if not ALLOWLIST_PATH.exists():
        return set()
    entries = set()
    for line in ALLOWLIST_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path, lineno, col, token = line.split(":", 3)
        entries.add((path, int(lineno), int(col), token))
    return entries


def cmd_lint(csrc_dir: Path) -> int:
    if not csrc_dir.is_dir():
        print(f"csrc dir not found: {csrc_dir}", file=sys.stderr)
        return 2
    allowlist = load_allowlist()
    messages = []
    for c_file in sorted(csrc_dir.glob("*.c")):
        text = c_file.read_text()
        abs_file = c_file.resolve()
        rel = str(abs_file.relative_to(REPO)) if abs_file.is_relative_to(REPO) else c_file.name
        grandfathered = c_file.name in GRANDFATHERED_FILES
        for lineno, col, token in find_violations(text):
            if grandfathered and (rel, lineno, col, token) in allowlist:
                continue
            messages.append(f"FAIL {rel}:{lineno} bare literal `{token}`")
    for m in messages:
        print(m)
    if messages:
        print(f"CONSTANTS LINT FAILED ({len(messages)})")
        return 1
    print("CONSTANTS LINT OK")
    return 0


def cmd_gen_allowlist(csrc_dir: Path) -> int:
    entries = []
    for c_file in sorted(csrc_dir.glob("*.c")):
        if c_file.name not in GRANDFATHERED_FILES:
            continue
        rel = str(c_file.resolve().relative_to(REPO))
        for lineno, col, token in find_violations(c_file.read_text()):
            entries.append(f"{rel}:{lineno}:{col}:{token}")
    ALLOWLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALLOWLIST_PATH.write_text("\n".join(entries) + "\n")
    print(f"wrote {len(entries)} entries to {ALLOWLIST_PATH}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", metavar="PATH", help="write the generated header to PATH")
    g.add_argument("--lint", metavar="CSRC_DIR", help="lint CSRC_DIR/*.c for bare numeric literals")
    g.add_argument("--gen-allowlist", metavar="CSRC_DIR",
                    help="regenerate the grandfathered-literal allowlist from CSRC_DIR/*.c")
    args = ap.parse_args(argv)

    if args.emit:
        return cmd_emit(Path(args.emit))
    if args.lint:
        return cmd_lint(Path(args.lint))
    return cmd_gen_allowlist(Path(args.gen_allowlist))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
