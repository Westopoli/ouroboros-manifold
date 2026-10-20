#!/usr/bin/env python3
# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md Lane H part 3
#       (the spec provenance lint, HARNESS-provenance; Rev 12b and Rev 12c batch 2 rulings)
# See also: scripts/specfactory/pre_gate.sh (runs this when PRE_GATE_SPEC is set, DRAFT-pregate-spec-env)
"""spec_provenance.py <spec.md>: print `<spec path>:<line>: (<n>) <text>` per finding.

Exit 1 on any finding, 0 on none, 2 on usage. Reasons: (1) untagged behaviour unit,
(2) a stand-in-for-a-source phrase, (3) [P ..] without file:line or an approval heading
without file:line, (4) [B R-id] absent from the epics, (5) [W Q-id] not closed in the
register, (6) [DRAFT-name] with no ledger or register row, (7) CLASH_PAIRS on one piece id, (8) a [B R-id] pin missing or stale (rule_pins.py).
Unit: a heading line, a list item with its continuation lines, or a blank-separated
paragraph, reported at its first line. A tag in the unit, or in the lead-in paragraph a
list item continues, covers it. Python standard library only.
"""
import hashlib
import re
import sys
from pathlib import Path

DRAFT_PIN_HEX = 6  # DRAFT-pin-hex, harness enforcement spec section 4

# See also: spec Lane H part 3 reason (7): extended as found. ('refuse','clear') are substrings
# of two units sharing a piece id; ('ring','never form rings') pairs a unit with the word ring
# against the epic text of a rule that another unit sharing the piece id cites as [B R-id].
CLASH_PAIRS = [("refuse", "clear"), ("ring", "never form rings")]

SCRIPT_REPO = Path(__file__).resolve().parent.parent.parent
CODE_SPAN = re.compile(r"`[^`]*`")
TAG_START = re.compile(r"\[W Q-|\[W \d{4}-\d\d-\d\d|\[B R-|\[P |\[DRAFT-")
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
        for m in re.finditer(r"\[W (Q-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)", u.plain):
            if not ctx["closed"].get(m.group(1)):
                yield u.line, 5, f"[W {m.group(1)}] register row is not closed"


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


REASONS = [reason1, reason2, reason3, reason4, reason5, reason6, reason7, reason8]


def find_root(spec):
    for d in spec.resolve().parents:
        if (d / "docs" / "bible" / "epics").is_dir():
            return d
    return SCRIPT_REPO


def load_context(root):
    rules, rule_lines, closed, rows = {}, {}, {}, ""
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
            if f == register and len(cells) > 4 and cells[0].startswith("Q-"):
                closed[cells[0]] = cells[4].lower().startswith("closed")
    return {"rules": rules, "rule_lines": rule_lines, "closed": closed, "rows": rows}


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
