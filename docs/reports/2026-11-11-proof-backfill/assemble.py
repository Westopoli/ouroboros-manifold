#!/usr/bin/env python3
"""assemble.py [--repo <engine-rules worktree>] [--table <rule_table.csv>]: merge the 26 backfill files E-##.md into
all.csv, totals.md and conflicts.md, validated against the bible epics. Reads text only; standard library only.
Writes (beside this script): all.csv, totals.md, conflicts.md, assemble_report.md (validation detail).

Input file shape: a table `| id | proof | kind | candidate | fails | evidence |` (evidence may contain `|`),
a `## Conflicts` section of `- ` bullets, a `## Totals` line (ignored; recomputed here and compared).

Normalisation 1 (qualification 1, strict): a proven row whose test has quotes_rule == false for (rule, test function)
in rule_table.csv becomes MISSING, candidate = that test, fails = 1. Not applied to kind `client` rows or `.gd` tests
(listed as "client form, unresolved"), and not to proven rows whose (rule, test) pair is absent from the table or
file-level there (listed as "not in table").
"""
import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DEFAULT_REPO = Path.home() / "Projects/om-wt/engine-rules"

RULE_RE = re.compile(r"^- (R-\d{3}-\d{2})(?!\d)")
INV_ID = re.compile(r"E-?\s*(\d+)\s*Invariant\s*(\d+)", re.I)
INV_SHORT = re.compile(r"^Invariant\s*(\d+)$", re.I)
RULE_ID = re.compile(r"R-\d{3}-\d{2}")
CAND_FILE = re.compile(r"[\w./\-]+\.(?:py|gd)(?:::\w+)?")
BARE_NAME = re.compile(r"(?<![:\w])((?:_?test_\w+))")
PROOF_WORDS = {"missing": "MISSING", "missing?": "MISSING?", "unbuilt": "unbuilt"}


def epic_of_file(name):
    return "E-" + re.match(r"E-(\d+)", name).group(1)


# ---------- bible ----------
def read_bible(repo):
    """{epic: {"file", "ids": [ids in file order], "dups": [ids appearing twice]}}"""
    out = {}
    for f in sorted((repo / "docs/bible/epics").glob("E-*.md")):
        epic = epic_of_file(f.name)
        ids, in_inv, n = [], False, 0
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                in_inv = line.strip() == "## Invariants"
                continue
            if (m := RULE_RE.match(line)):
                ids.append(m.group(1))
            elif in_inv and re.match(r"^[-*+] ", line):
                n += 1
                ids.append(f"{epic} Invariant {n}")
        dups = sorted(i for i, c in Counter(ids).items() if c > 1)
        out[epic] = {"file": f.name, "ids": ids, "dups": dups}
    return out


# ---------- rule table ----------
def read_table(path):
    pairs = {}      # (id, file, func) -> quotes_rule string
    for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
        if r["test_file"] and r["test_func"]:
            pairs[(r["id"], r["test_file"], r["test_func"])] = r["quotes_rule"]
    return pairs


# ---------- input files ----------
def norm_id(raw, epic):
    s = raw.strip().strip("`*").strip()
    s = re.sub(r"\s+", " ", s)
    if (m := INV_ID.fullmatch(s)):
        return f"E-{int(m.group(1)):02d} Invariant {int(m.group(2))}"
    if (m := INV_SHORT.fullmatch(s)):
        return f"{epic} Invariant {int(m.group(1))}"
    if (m := re.fullmatch(r"R[-_](\d{3})[-_](\d{2})", s)):
        return f"R-{m.group(1)}-{m.group(2)}"
    return s


def norm_proof(raw):
    s = raw.strip().strip("`").strip()
    return PROOF_WORDS.get(s.lower(), s)


def parse_input(path, notes):
    """rows, conflicts, declared totals line for one input file"""
    epic = epic_of_file(path.name)
    rows, conflicts, totals, section = [], [], "", None
    cur = None
    for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## "):
            section = line[3:].strip()
            cur = None
            continue
        if section == "Conflicts":
            if re.match(r"^[-*] ", line):
                cur = [line[2:].strip()]
                conflicts.append(cur)
            elif line.strip() and cur is not None:
                cur.append(line.strip())
            elif line.strip():
                notes.append(f"{path.name}:{ln} conflicts text outside a bullet: {line.strip()[:80]}")
            continue
        if section == "Totals":
            if line.strip():
                totals += line.strip() + " "
            continue
        if not line.startswith("|"):
            continue
        inner = line.strip()
        inner = inner[1:-1] if inner.endswith("|") else inner[1:]
        cells = [c.strip() for c in inner.split("|", 5)]
        if len(cells) < 6:
            notes.append(f"{path.name}:{ln} row with {len(cells)} cells: {line[:80]}")
            cells += [""] * (6 - len(cells))
        if cells[0].lower() == "id" or set(cells[0]) <= set("-: "):
            continue
        rid = norm_id(cells[0], epic)
        if rid != cells[0].strip():
            notes.append(f"{path.name}:{ln} id normalised {cells[0].strip()!r} -> {rid!r}")
        rows.append({"epic": epic, "id": rid, "proof": norm_proof(cells[1]), "kind": cells[2].strip().lower(),
                     "candidate": cells[3].strip().strip("`"),
                     "fails": re.sub(r"\s+", "", cells[4]), "evidence": cells[5].strip(), "src": f"{path.name}:{ln}"})
    return rows, [" ".join(c) for c in conflicts], totals.strip()


# ---------- repo existence ----------
_text_cache = {}


def file_text(repo, rel):
    if rel not in _text_cache:
        p = repo / rel
        _text_cache[rel] = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else None
    return _text_cache[rel]


_index = {}   # {"names": {func: [files]}, "bases": {basename: [files]}}


def build_index(repo):
    names, bases = defaultdict(list), defaultdict(list)
    for f in sorted((repo / "tests").rglob("*")):
        if f.suffix in (".py", ".gd") and f.is_file():
            rel = f.relative_to(repo).as_posix()
            bases[f.name].append(rel)
            for m in re.finditer(r"^\s*(?:async\s+)?(?:def|func)\s+(\w+)", f.read_text(encoding="utf-8", errors="replace"), re.M):
                names[m.group(1)].append(rel)
    _index["names"], _index["bases"] = names, bases


def resolve_file(rel):
    """A path given without a directory is resolved to the one tests/ file with that name, else left alone."""
    if "/" not in rel and len(_index["bases"].get(rel, [])) == 1:
        return _index["bases"][rel][0]
    return rel


def check_ref(repo, ref):
    """ref 'file::name' or 'file' or a bare test name; returns '' when ok, else a short fault text."""
    rel, sep, name = ref.partition("::")
    if not sep and not re.search(r"\.(py|gd)$", rel):       # bare test name, file not given
        return "" if _index["names"].get(rel) else f"bare test name defined nowhere in tests/: {rel}"
    t = file_text(repo, rel)
    if t is None:
        return f"file missing: {rel}"
    if name and not re.search(r"(?:def|func)\s+%s\b" % re.escape(name), t):
        return f"name not a def/func in file: {ref}" + (" (substring only)" if name in t else " (absent)")
    return ""


def candidate_refs(cand):
    """All file[::name] refs and bare test names in a candidate cell."""
    return [m.group(0) for m in re.finditer(r"[\w./\-]+\.(?:py|gd)(?:::\w+)?|(?<![:\w/.])_?test_\w+", cand)]


def resolve_candidate(cand, notes, where):
    def sub(m):
        tok = m.group(0)
        rel, sep, name = tok.partition("::")
        full = resolve_file(rel)
        if full != rel:
            notes.append(f"{where} file given without directory, resolved {rel} -> {full}")
        return full + sep + name
    return re.sub(r"[\w./\-]+\.(?:py|gd)(?:::\w+)?", sub, cand)


def fail_set(fails):
    s = {x for x in fails.split(",") if x}
    if "all" in s:
        s = (s - {"all"}) | {"1", "2", "3", "4", "5", "6"}
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--table", default=str(BASE / "bill/rule_table.csv"))
    a = ap.parse_args()
    repo = Path(a.repo)
    bible = read_bible(repo)
    table = read_table(a.table)
    build_index(repo)
    notes = []

    # ---- parse inputs
    rows_by_epic, conflicts_by_epic, declared = defaultdict(list), defaultdict(list), {}
    for f in sorted(HERE.glob("E-*.md")):
        rows, conf, tot = parse_input(f, notes)
        epic = epic_of_file(f.name)
        rows_by_epic[epic] += rows
        conflicts_by_epic[epic] += conf
        declared[f.name] = tot

    # ---- validate ids
    all_rows, val = [], {}
    id_home = {i: e for e, b in bible.items() for i in b["ids"]}
    for epic in sorted(bible):
        b, rows = bible[epic], rows_by_epic.get(epic, [])
        have = Counter(r["id"] for r in rows)
        want = set(b["ids"])
        missing = [i for i in b["ids"] if have[i] == 0]
        dup = sorted(i for i, c in have.items() if c > 1)
        unknown = sorted(i for i in have if i not in want)
        elsewhere = {i: id_home[i] for i in unknown if i in id_home}
        n_inv = sum(1 for i in b["ids"] if "Invariant" in i)
        val[epic] = {"rules": len(b["ids"]) - n_inv, "inv": n_inv, "rows": len(rows), "missing": missing, "dup": dup,
                     "unknown": unknown, "elsewhere": elsewhere, "epic_dups": b["dups"]}
        seen = set()
        for r in rows:
            if r["id"] in want and r["id"] not in seen:
                seen.add(r["id"])
                all_rows.append(r)
    order = {i: n for e in sorted(bible) for n, i in enumerate(bible[e]["ids"])}
    all_rows.sort(key=lambda r: (r["epic"], order[r["id"]]))
    for r in all_rows:
        r["candidate"] = resolve_candidate(r["candidate"], notes, f"{r['src']} {r['id']} candidate")
        if "::" in r["proof"]:
            r["proof"] = resolve_candidate(r["proof"], notes, f"{r['src']} {r['id']} proof")

    # ---- validate references in the repo
    ref_faults = []
    for r in all_rows:
        refs = []
        if "::" in r["proof"] or re.search(r"\.(py|gd)\b", r["proof"]):
            refs.append(("proof", r["proof"]))
        refs += [("candidate", c) for c in candidate_refs(r["candidate"])]
        for what, ref in refs:
            if (msg := check_ref(repo, ref)):
                ref_faults.append((r["epic"], r["id"], what, msg))
        if r["proof"] not in ("MISSING", "MISSING?", "unbuilt") and "::" not in r["proof"]:
            ref_faults.append((r["epic"], r["id"], "proof", f"proof is neither MISSING/MISSING?/unbuilt nor file::name: {r['proof'][:80]}"))
        if r["proof"] not in ("MISSING", "MISSING?", "unbuilt") and r["kind"] not in ("scenario", "whole-run", "client"):
            ref_faults.append((r["epic"], r["id"], "kind", f"proven row with kind {r['kind']!r}"))

    for r in all_rows:
        r["proof0"] = r["proof"]
    # ---- normalise qualification 1
    dropped, client_unres, not_in_table = [], [], []
    for r in all_rows:
        if r["proof"] in ("MISSING", "MISSING?", "unbuilt"):
            continue
        rel, _, name = r["proof"].partition("::")
        q = table.get((r["id"], rel, name))
        if r["kind"] == "client" or rel.endswith(".gd"):
            client_unres.append((r["epic"], r["id"], r["proof"], r["kind"], "absent from table" if q is None else f"quotes_rule={q or 'blank (file level)'}"))
            continue
        if q is None or q == "":
            not_in_table.append((r["epic"], r["id"], r["proof"], "pair absent from table" if q is None else "file level in table"))
            continue
        if q == "false":
            dropped.append((r["epic"], r["id"], r["proof"]))
            r["candidate"], r["fails"] = r["proof"], "1"
            r["evidence"] = "[quals-1 normalisation: rule_table quotes_rule=false for this test] " + r["evidence"]
            r["proof"], r["kind"] = "MISSING", ""

    # ---- diagnostic: MISSING rows with a candidate that the table says does not quote the rule, fails lacks 1
    diag_q1 = []
    for r in all_rows:
        if r["proof"] == "MISSING" and r["candidate"] and "1" not in fail_set(r["fails"]):
            refs = [c for c in candidate_refs(r["candidate"]) if "::" in c]
            if refs:
                rel, _, name = refs[0].partition("::")
                q = table.get((r["id"], rel, name))
                if q == "false":
                    diag_q1.append(r)

    # ---- write all.csv
    with open(HERE / "all.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["epic", "id", "proof", "kind", "candidate", "fails", "evidence"])
        for r in all_rows:
            w.writerow([r[k] for k in ("epic", "id", "proof", "kind", "candidate", "fails", "evidence")])

    # ---- totals
    def count(rows):
        c = Counter(r["proof"] if r["proof"] in ("MISSING", "MISSING?", "unbuilt") else "proven" for r in rows)
        return [len(rows), c["proven"], c["MISSING"], c["MISSING?"], c["unbuilt"]]

    def bucket(rows):
        miss = [r for r in rows if r["proof"] == "MISSING"]
        b = Counter()
        part = Counter()
        for r in miss:
            if not r["candidate"]:
                b["no candidate"] += 1
                part["no candidate"] += 1
                continue
            s = fail_set(r["fails"])
            if not s:
                b["candidate but no fails recorded"] += 1
                part["candidate but no fails recorded"] += 1
                continue
            five = s & {"5", "5?"}
            if s == {"5?"}:
                b["only 5?"] += 1
            if s and s <= {"5", "5?"}:
                b["only 5 or 5?"] += 1
            if s == {"1"}:
                b["only 1"] += 1
            if "1" in s and five and s <= {"1", "5", "5?"}:
                b["only 1 and 5/5?"] += 1
            if "3" in s:
                b["involves 3"] += 1
            if "4" in s:
                b["involves 4"] += 1
            # disjoint partition, first match wins
            if "3" in s or "4" in s:
                part["involves 3 or 4"] += 1
            elif s == {"5?"}:
                part["only 5?"] += 1
            elif s == {"5"}:
                part["only 5"] += 1
            elif s == {"5", "5?"}:
                part["only 5 and 5?"] += 1
            elif s == {"1"}:
                part["only 1"] += 1
            elif "1" in s and five and s <= {"1", "5", "5?"}:
                part["only 1 and 5/5?"] += 1
            else:
                part["other (no 3, no 4)"] += 1
        return len(miss), b, part

    lines = ["# Backfill totals (assemble.py)", "",
             "Counted after the qualification-1 normalisation; `proven` = a test is the proof line. Rows = rules + Invariant bullets.", "",
             "| epic | rules | invariants | rows | proven | MISSING | MISSING? | unbuilt |", "|---|---|---|---|---|---|---|---|"]
    tot = [0] * 5
    for epic in sorted(bible):
        rs = [r for r in all_rows if r["epic"] == epic]
        c = count(rs)
        tot = [x + y for x, y in zip(tot, c)]
        lines.append(f"| {epic} | {val[epic]['rules']} | {val[epic]['inv']} | " + " | ".join(map(str, c)) + " |")
    nr, ni = sum(v["rules"] for v in val.values()), sum(v["inv"] for v in val.values())
    lines.append(f"| **all** | {nr} | {ni} | " + " | ".join(f"**{x}**" for x in tot) + " |")
    lines += ["", f"Overall: rows {tot[0]}, proven {tot[1]}, MISSING {tot[2]}, MISSING? {tot[3]}, unbuilt {tot[4]}.",
              f"Before normalisation 1: proven {tot[1] + len(dropped)}, MISSING {tot[2] - len(dropped)} ({len(dropped)} proven rows dropped to MISSING)."]
    n_miss, b, part = bucket(all_rows)
    lines += ["", "## MISSING rows by failing set", "",
              f"Population: the {n_miss} rows whose proof is `MISSING` (not `MISSING?`; `MISSING?` rows are counted apart below). "
              "A `fails` cell is read as a set of qualification numbers; `5?` is kept apart from `5`; the word `all` is read as {1,2,3,4,5,6}. "
              "Rows with an empty candidate cell go to `no candidate at all` and to no other bucket (their fails cell, if any, is not read). "
              "The first block below uses the buckets as named in the brief and they overlap on purpose (`only 5?` is inside `only 5 or 5?`; "
              "a row failing 3 and 4 is in both involves lines).", "",
              "| bucket | rows |", "|---|---|"]
    for k in ("only 5?", "only 5 or 5?", "only 1", "only 1 and 5/5?", "involves 3", "involves 4", "no candidate"):
        lines.append(f"| {k.replace('no candidate', 'no candidate at all')} | {b[k]} |")
    lines.append(f"| candidate present but no fails recorded | {b['candidate but no fails recorded']} |")
    lines += ["", "Disjoint partition of the same rows (first match wins, in this order), sums to the population:", "",
              "| bucket | rows |", "|---|---|"]
    keys = ["no candidate", "candidate but no fails recorded", "involves 3 or 4", "only 5?", "only 5", "only 5 and 5?", "only 1",
            "only 1 and 5/5?", "other (no 3, no 4)"]
    for k in keys:
        lines.append(f"| {k.replace('no candidate', 'no candidate at all')} | {part[k]} |")
    lines.append(f"| sum | {sum(part[k] for k in keys)} (population {n_miss}) |")
    both34 = sum(1 for r in all_rows if r["proof"] == "MISSING" and r["candidate"] and {"3", "4"} <= fail_set(r["fails"]))
    lines += ["", f"Rows involving both 3 and 4: {both34}.",
              f"`MISSING?` rows: {tot[3]}; of them with a candidate: {sum(1 for r in all_rows if r['proof'] == 'MISSING?' and r['candidate'])}.",
              "", "## Sensitivity: does the candidate quote the rule?", "",
              f"{len(diag_q1)} MISSING rows have a candidate `file::name` that the rule table (quotes_rule) says does NOT quote the rule, "
              "yet their fails cell omits `1`. These are not changed; they would also fail qualification 1. By bucket of the fails cell as written: " +
              ", ".join(f"{k} {v}" for k, v in sorted(Counter(
                  "only 5?" if fail_set(r['fails']) == {"5?"} else
                  "only 5 or 5?" if fail_set(r['fails']) <= {"5", "5?"} and fail_set(r['fails']) else
                  "has 3 or 4" if fail_set(r['fails']) & {"3", "4"} else "other" for r in diag_q1).items())) + ".",
              f"Of them {sum(1 for r in diag_q1 if candidate_refs(r['candidate'])[0].partition('::')[0].endswith('.gd'))} name a .gd test (client form; the table's quotes_rule is a text match on the first 40 characters of the rule, which a .gd header paraphrase can miss)."
              " (Detail: assemble_report.md.)"]
    (HERE / "totals.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- conflicts.md
    cl = ["# Conflicts collected from the backfill files", "",
          "Text kept as written; numbering C-<epic>-<n> follows the order in the input file(s) (E-16 and E-17: part a, then part b).", ""]
    ctotal = 0
    for epic in sorted(conflicts_by_epic):
        if not conflicts_by_epic[epic]:
            continue
        cl += [f"## {epic}", ""]
        for n, c in enumerate(conflicts_by_epic[epic], 1):
            cl.append(f"- C-{epic}-{n}: {c}")
            ctotal += 1
        cl.append("")
    cl.append(f"Total: {ctotal} conflicts.")
    (HERE / "conflicts.md").write_text("\n".join(cl) + "\n", encoding="utf-8")

    # ---- report
    rp = ["# assemble.py validation report", "", "## ids per epic (bible vs rows)", "",
          "| epic | rules | invariants | rows parsed | missing | duplicate | unknown |", "|---|---|---|---|---|---|---|"]
    for epic in sorted(val):
        v = val[epic]
        rp.append(f"| {epic} | {v['rules']} | {v['inv']} | {v['rows']} | {len(v['missing'])} | {len(v['dup'])} | {len(v['unknown'])} |")
    for epic in sorted(val):
        v = val[epic]
        for k in ("missing", "dup", "unknown", "epic_dups"):
            if v[k]:
                rp.append(f"- {epic} {k}: {', '.join(v[k])}")
        if v["elsewhere"]:
            rp.append(f"- {epic} unknown ids that are in another epic: {v['elsewhere']}")
    rp += ["", "## header totals declared in the inputs vs recomputed (from parsed rows, before normalisation 1)", ""]
    byfile = defaultdict(list)
    for rws in rows_by_epic.values():
        for r in rws:
            byfile[r["src"].split(":")[0]].append(r)
            r.setdefault("proof0", r["proof"])
    for fname, tl in sorted(declared.items()):
        rs = byfile[fname]
        c = Counter(r["proof0"] if r["proof0"] in ("MISSING", "MISSING?", "unbuilt") else "proven" for r in rs)
        got = f"proven {c['proven']}, MISSING {c['MISSING']}, MISSING? {c['MISSING?']}, unbuilt {c['unbuilt']}"
        rp.append(f"- {fname}: declared `{tl}`; recomputed `{got}`" + ("" if re.sub(r'\W+', ' ', tl).strip() == re.sub(r'\W+', ' ', got).strip() else "  <-- DIFFERENT"))
    rp += ["", f"## repo reference faults ({len(ref_faults)})", ""] + [f"- {e} {i} {w}: {m}" for e, i, w, m in ref_faults]
    rp += ["", f"## normalised on qualification 1 ({len(dropped)} proven rows dropped to MISSING)", ""] + [f"- {e} {i}: {p}" for e, i, p in dropped]
    rp += ["", f"## client form, unresolved ({len(client_unres)}: kind client or a .gd test; not normalised)", ""] + [f"- {e} {i}: {p} [{k}] {q}" for e, i, p, k, q in client_unres]
    rp += ["", f"## proven rows not decidable from the table ({len(not_in_table)})", ""] + [f"- {e} {i}: {p} ({q})" for e, i, p, q in not_in_table]
    rp += ["", f"## MISSING rows whose candidate the table says does not quote the rule, fails cell without 1 ({len(diag_q1)})", ""] + [f"- {r['epic']} {r['id']}: {r['candidate'][:100]} fails {r['fails']}" for r in diag_q1]
    rp += ["", f"## parse notes ({len(notes)})", ""] + [f"- {n}" for n in notes]
    (HERE / "assemble_report.md").write_text("\n".join(rp) + "\n", encoding="utf-8")

    print(f"rows {tot[0]} proven {tot[1]} MISSING {tot[2]} MISSING? {tot[3]} unbuilt {tot[4]}")
    print(f"dropped on q1 {len(dropped)}, client-form unresolved {len(client_unres)}, not-in-table {len(not_in_table)}, ref faults {len(ref_faults)}, conflicts {ctotal}")
    bad = [e for e, v in val.items() if v["missing"] or v["dup"] or v["unknown"]]
    print("epics with id faults:", bad or "none")


if __name__ == "__main__":
    sys.exit(main())
