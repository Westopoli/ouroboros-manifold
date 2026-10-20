#!/usr/bin/env python3
# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md Lane H part 3
#       (the spec provenance lint, HARNESS-provenance; Rev 12b and Rev 12c batch 2 rulings)
# See also: scripts/specfactory/pre_gate.sh (runs this when PRE_GATE_SPEC is set, DRAFT-pregate-spec-env)
"""spec_provenance.py <spec.md>: print `<spec path>:<line>: (<n>) <text>` per finding.

Exit 1 on any finding, 0 on none, 2 on usage. Reasons: (1) untagged behaviour unit,
(2) a stand-in-for-a-source phrase, (3) [P ..] without file:line or an approval heading
without file:line, (4) [B R-id] absent from the epics, (5) [W Q-id] not closed in the
register (closed or reading), (6) [DRAFT-name] with no ledger or register row, (7) CLASH_PAIRS on one piece id, (8) a [B R-id] pin missing or stale (rule_pins.py),
(9) a quantified [W] quote with no [ASSERT file::test] that asserts its words, (10) a number after a [W] quote with no DRAFT- in its
sentence, (11) an R-id set aside with no [OPEN Q-x] on an open register row that names a waiting piece (HARNESS-C235).
Unit: a heading line, a list item with its continuation lines, or a blank-separated
paragraph, reported at its first line. A tag in the unit, or in the lead-in paragraph a
list item continues, covers it. Python standard library only.
"""
import hashlib
import re
import sys
from pathlib import Path

DRAFT_PIN_HEX = 6  # DRAFT-pin-hex, harness enforcement spec section 4
# DRAFT-quantifiers and DRAFT-set-aside-phrases, harness enforcement spec section 4 (HARNESS-C235)
DRAFT_QUANTIFIERS = ("at least", "at most", "never", "always", "every", "all", "only", "no more than", "any age",
                     "within", "exactly", "none")
DRAFT_SET_ASIDE_PHRASES = ("not in scope", "out of scope", "set aside", "not this piece", "deferred", "later",
                           "follow-up")

# See also: spec Lane H part 3 reason (7): extended as found. ('refuse','clear') are substrings
# of two units sharing a piece id; ('ring','never form rings') pairs a unit with the word ring
# against the epic text of a rule that another unit sharing the piece id cites as [B R-id].
CLASH_PAIRS = [("refuse", "clear"), ("ring", "never form rings")]

SCRIPT_REPO = Path(__file__).resolve().parent.parent.parent
CODE_SPAN = re.compile(r"`[^`]*`")
TAG_START = re.compile(r"\[W Q-|\[W \d{4}-\d\d-\d\d|\[B R-|\[P |\[DRAFT-|\[ASSERT |\[OPEN Q-")
BEHAVIOUR_WORDS = re.compile(r"\b(when|then|shows|sees|draws|refuses|accepts|default)\b", re.I)
NUMBER = re.compile(r"(?<![\w.\-/#])\d")
STAND_INS = ("liberty", "as the builder drafted", "architect default")
CITATION = re.compile(r"[A-Za-z_][\w./-]*:\d+")
APPROVAL = re.compile(r"\b(approved|approval)\b", re.I)
PIECE_ID = re.compile(r"(?<![\w-])(?:VG-[A-Za-z0-9-]+|[A-Z]\d{1,2}[a-z]?(?:-[a-z0-9]+)?|K-[a-z]\d?"
                      r"|HARNESS-[a-z-]+)(?![\w-])")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
RULE_ID = re.compile(r"R-\d+-\d+")
_PINNED = r"R-\d+-\d+(?:@[0-9a-f]{6})?"
B_TAG = re.compile(r"\[B ((?:" + _PINNED + r")(?:,\s*" + _PINNED + r")*)([^\]]*)\]")
_ID = r"(?:Q-[A-Za-z0-9-]+|\d{4}-\d\d-\d\d)"
# Group 1 first id or date, 2 further ids or dates, 3 a double-quoted quote, 4 an unquoted quote.
W_TAG = re.compile(r"\[W (" + _ID + r")((?:,\s*" + _ID + r")*)(?:\s*\([^)]*\))?:?\s*(?:\"(.*?)\"\]|([^\]]*)\])")
Q_ID = re.compile(r"Q-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
ASSERT_TAG = re.compile(r"\[ASSERT ([^\]]*)\]")
OPEN_TAG = re.compile(r"\[OPEN (Q-[A-Za-z0-9-]+)\]")
QUANTIFIER = re.compile(r"(?<!\w)(?:" + "|".join(q.replace(" ", r"\s+") for q in DRAFT_QUANTIFIERS) + r")(?!\w)", re.I)
SET_ASIDE = re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, DRAFT_SET_ASIDE_PHRASES)) + r")(?!\w)", re.I)
CLAUSE_SPLIT = re.compile(r"\.|;| and | so ", re.I)
DEF_ANY = re.compile(r"^(\s*)(?:(?:async\s+)?def|(?:static\s+)?func)\s+\w+\(")
# Spans of a number that reason (10) does not check: a citation, a date, an id, a name, a @pin, a rev or wave number.
NOT_A_NUMBER = re.compile(r"[A-Za-z_][\w./-]*:\d+|\d{4}-\d\d-\d\d|\b[RQSE]-[\w-]+|\b(?:TD|FU|REC|DRAFT)-[\w-]+"
                          r"|@\w+|\b(?:rev|wave)\s*\d+[a-z]?", re.I)
PIN_RE = re.compile(r"(R-\d+-\d+)(?:@([0-9a-f]{6}))?")
RULE_LINE = re.compile(r"^- (R-\d+-\d+)(?!\S)")


def rule_pin(rule_line):
    # See also: rule_pins.py (the pin tool); the pin is the sha256 of the line after "- R-id", whitespace normalised.
    return hashlib.sha256(" ".join(rule_line.split()[2:]).encode("utf-8")).hexdigest()[:DRAFT_PIN_HEX]


class Unit:
    def __init__(self, line, lines, heading=False, lead=()):
        self.line, self.text, self.heading = line, "\n".join(lines), heading
        self.plain = CODE_SPAN.sub(" ", self.text)
        self.tag_text = self.plain + "\n" + CODE_SPAN.sub(" ", "\n".join(lead))


def split_units(lines):
    units, cur, lead, in_fence = [], None, [], False

    def flush(keep_lead=False):
        nonlocal cur, lead
        if cur:
            units.append(Unit(cur[0], cur[1], lead=lead if cur[2] else ()))
            lead = cur[1] if keep_lead and not cur[2] else lead
        cur = None

    for no, raw in enumerate(lines, 1):
        if raw.lstrip().startswith("```"):
            flush(); lead = []; in_fence = not in_fence
        elif in_fence:
            continue
        elif not raw.strip():
            flush(); lead = []
        elif raw.startswith("#"):
            flush(); lead = []
            units.append(Unit(no, [raw], heading=True))
        elif LIST_ITEM.match(raw):
            flush(keep_lead=True); cur = [no, [raw], True]
        elif cur is not None:
            cur[1].append(raw)
        else:
            cur = [no, [raw], False]
    flush()
    return units


def reason1(units, ctx):
    for u in units:
        behaviour = NUMBER.search(u.plain) or BEHAVIOUR_WORDS.search(u.plain)
        if behaviour and not u.heading and not TAG_START.search(u.tag_text):
            yield u.line, 1, "behaviour unit without a provenance tag: " + u.text.splitlines()[0][:70]


def reason2(units, ctx):
    for u in units:
        low = u.text.lower()
        for p in STAND_INS:
            if re.search(r"\b" + re.escape(p) + r"\b", low):
                yield u.line, 2, f"words that stand in for a source: {p!r}"


def reason3(units, ctx):
    for u in units:
        for m in re.finditer(r"\[P ([^\]]*)\]", u.plain):
            if not CITATION.search(m.group(1)):
                yield u.line, 3, f"[P {m.group(1)}] has no file:line citation"
        if u.heading and APPROVAL.search(u.plain) and not CITATION.search(u.plain):
            yield u.line, 3, "heading claims approval with no file:line citation"


def reason4(units, ctx):
    for u in units:
        for m in B_TAG.finditer(u.plain):
            for rid in RULE_ID.findall(m.group(1)):
                if rid not in ctx["rules"]:
                    yield u.line, 4, f"[B {rid}] is not in docs/bible/epics"


def reason8(units, ctx):
    for u in units:
        for m in B_TAG.finditer(u.plain):
            for rid, pin in PIN_RE.findall(m.group(1)):
                if rid not in ctx["rule_lines"]:
                    continue
                now = rule_pin(ctx["rule_lines"][rid])
                if not pin:
                    yield u.line, 8, f"[B {rid}] has no pin"
                elif pin != now:
                    yield u.line, 8, f"[B {rid}@{pin}] pin is stale: the rule line is now {now}"


def reason5(units, ctx):
    for u in units:
        for m in W_TAG.finditer(u.text):
            for qid in Q_ID.findall(m.group(1) + m.group(2)):
                if qid in ctx["malformed"]:
                    yield u.line, 5, f"register row {qid} is malformed"
                elif not ctx["status"].get(qid, "").startswith(("closed", "reading")):
                    yield u.line, 5, f"[W {qid}] register row is not closed"


def norm(text):
    return " ".join(text.split()).lower()


def key_clause(quote):
    first = QUANTIFIER.search(quote)
    lo = 0
    for d in list(CLAUSE_SPLIT.finditer(quote)) + [None]:
        hi = d.start() if d else len(quote)
        if lo <= first.start() < hi:
            return " ".join(quote[lo:hi].split())
        lo = d.end() if d else lo
    return " ".join(quote.split())


def test_body(root, ref):
    path, sep, name = ref.rpartition("::")
    f = root / path
    if not sep or not f.is_file():
        return None
    kind = r"(?:static\s+)?func" if f.suffix == ".gd" else r"(?:async\s+)?def"
    lines = f.read_text(errors="replace").splitlines()
    head = re.compile(r"^(\s*)" + kind + r"\s+" + re.escape(name) + r"\(")
    start = next((i for i, ln in enumerate(lines) if head.match(ln)), None)
    if start is None:
        return None
    indent = len(head.match(lines[start]).group(1))
    body = []
    for ln in lines[start + 1:]:
        d = DEF_ANY.match(ln)
        if d and len(d.group(1)) <= indent:
            break
        body.append(ln)
    return body


def assertions(body):
    out, i = [], 0
    while i < len(body):
        chunk = body[i].strip()
        if chunk.startswith(("assert ", "_assert(", "assert_")):
            depth = chunk.count("(") - chunk.count(")")
            while (depth > 0 or chunk.endswith("\\")) and i + 1 < len(body):
                i += 1
                more = body[i].strip()
                chunk, depth = chunk + " " + more, depth + more.count("(") - more.count(")")
            out.append(norm(chunk))
        i += 1
    return out


def reason9(units, ctx):
    for u in units:
        refs = [m.group(1) for m in ASSERT_TAG.finditer(u.text)]
        bodies = {r: test_body(ctx["root"], r) for r in refs}
        for r, body in bodies.items():
            if body is None:
                yield u.line, 9, f"[ASSERT {r}] test not found"
        for m in W_TAG.finditer(u.text):
            quote = m.group(3) if m.group(3) is not None else (m.group(4) or "").strip()
            if m.group(3) is None and "[" in quote:
                yield u.line, 9, 'unquoted [W] text contains "[": put the quote in double quotes'
            if not QUANTIFIER.search(quote):
                continue
            clause = key_clause(quote)
            if not refs:
                yield u.line, 9, f"[W {m.group(1)}] quantified quote has no [ASSERT]"
            elif not any(norm(clause) in a for b in bodies.values() if b for a in assertions(b)):
                for r, body in bodies.items():
                    if body is not None:
                        yield u.line, 9, f"[ASSERT {r}] the test does not assert the quote's words: \"{clause}\""


def reason10(units, ctx):
    for u in units:
        tags = list(W_TAG.finditer(u.text))
        if not tags:
            continue
        skip = [m.span() for m in NOT_A_NUMBER.finditer(u.text)]
        starts = [0] + [m.end() for m in re.finditer(r"\. ", u.text)] + [len(u.text) + 1]
        for m in NUMBER.finditer(u.text):
            if m.start() < tags[-1].end() or any(a <= m.start() < b for a, b in skip):
                continue
            lo = max(s for s in starts if s <= m.start())
            hi = min(s for s in starts if s > m.start())
            if "DRAFT-" not in u.text[lo:hi]:
                yield u.line, 10, f"number {re.match(r'[0-9]+(?:[.][0-9]+)?', u.text[m.start():]).group()} after a quote with no DRAFT in its sentence"


def reason11(units, ctx):
    for u in units:
        ids = sorted(set(RULE_ID.findall(u.text)))
        if not ids or not SET_ASIDE.search(u.text):
            continue
        opens = OPEN_TAG.findall(u.text)
        for rid in ids if not opens else ():
            yield u.line, 11, f"{rid} set aside with no [OPEN Q-x]"
        for qid in opens:
            if not ctx["status"].get(qid, "").startswith("open"):
                yield u.line, 11, f"[OPEN {qid}] row is not open"
            elif not (PIECE_ID.search(ctx["answers"][qid]) or re.search(r"(?<![\w-])FU-[A-Za-z0-9-]+", ctx["answers"][qid])):
                yield u.line, 11, f"[OPEN {qid}] row names no piece that waits"


def reason6(units, ctx):
    for u in units:
        for m in re.finditer(r"\[(DRAFT-[A-Za-z0-9-]+)\]", u.plain):
            if not re.search(r"(?<![\w-])" + re.escape(m.group(1)) + r"(?![\w-])", ctx["rows"]):
                yield u.line, 6, f"[{m.group(1)}] has no ledger or register row"


def reason7(units, ctx):
    ids = [set(PIECE_ID.findall(u.text)) for u in units]
    low = [u.text.lower() for u in units]
    cited = [" ".join(ctx["rules"].get(r, "") for m in B_TAG.finditer(u.plain)
                      for r in RULE_ID.findall(m.group(1))).lower() for u in units]
    first, second = CLASH_PAIRS[0]
    word, rule_words = CLASH_PAIRS[1]
    for i in range(len(units)):
        for j in range(len(units)):
            shared = ids[i] & ids[j]
            if i == j or not shared:
                continue
            names = ",".join(sorted(shared))
            if i < j and first in low[i] and second in low[j]:
                yield max(units[i].line, units[j].line), 7, (
                    f"{names}: '{first}' at line {units[i].line} versus '{second}' at line {units[j].line}")
            if i < j and second in low[i] and first in low[j]:
                yield max(units[i].line, units[j].line), 7, (
                    f"{names}: '{first}' at line {units[j].line} versus '{second}' at line {units[i].line}")
            if re.search(r"\b" + word + r"s?\b", low[i]) and rule_words in cited[j]:
                yield units[i].line, 7, (f"{names}: '{word}' at line {units[i].line} versus "
                                         f"'{rule_words}' in the rule cited at line {units[j].line}")


REASONS = [reason1, reason2, reason3, reason4, reason5, reason6, reason7, reason8, reason9, reason10, reason11]


def find_root(spec):
    for d in spec.resolve().parents:
        if (d / "docs" / "bible" / "epics").is_dir():
            return d
    return SCRIPT_REPO


def load_context(root):
    rules, rule_lines, status, answers, malformed, rows = {}, {}, {}, {}, set(), ""
    for f in sorted((root / "docs" / "bible" / "epics").glob("*.md")):
        for line in f.read_text(errors="replace").splitlines():
            for rid in RULE_ID.findall(line):
                rules[rid] = rules.get(rid, "") + " " + line
            if (m := RULE_LINE.match(line)):
                rule_lines.setdefault(m.group(1), line)
    register = root / "docs" / "northstar" / "ambiguity_register.md"
    ledger = root / "docs" / "northstar" / "plans" / "push_ledger_2026-09-22.md"
    for f in (register, ledger):
        if not f.is_file():
            continue
        for line in f.read_text(errors="replace").splitlines():
            if not line.startswith("|"):
                continue
            rows += line + "\n"
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if f == register and cells[0].startswith("Q-"):
                if len(cells) != 6:
                    malformed.add(cells[0])
                else:
                    status[cells[0]], answers[cells[0]] = cells[4].lower(), cells[5]
    return {"rules": rules, "rule_lines": rule_lines, "status": status, "answers": answers, "malformed": malformed,
            "rows": rows, "root": root}


def main(argv):
    if len(argv) != 2 or not Path(argv[1]).is_file():
        print("usage: spec_provenance.py <spec.md>", file=sys.stderr)
        return 2
    spec = Path(argv[1])
    units = split_units(spec.read_text(errors="replace").splitlines())
    ctx = load_context(find_root(spec))
    findings = sorted({f for r in REASONS for f in r(units, ctx)})
    for line, n, text in findings:
        print(f"{argv[1]}:{line}: ({n}) {text}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
