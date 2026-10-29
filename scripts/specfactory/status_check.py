#!/usr/bin/env python3
"""status_check.py: method rev 2, guard 7. The status copies must agree.

Twelve checks, one `STATUS <check> OK|WARN|DRIFT <detail>` line each (a check may
print several DRIFT lines); exit 1 when any check is DRIFT, else 0 (WARN exits 0).

  lane_table  every sha in the programme lane table's "On main" cells is an
              ancestor of --base
  pieces      every attached piece's attach_sha in pieces.toml is an ancestor
              of --base; in_flight piece ids are listed
  seen        queue rows with Westley verdict "approved" equal stories.md rows
              whose Status is "Seen" or starts with "Seen"
  roadmap     ROADMAP "## 1. Now building" holds no lane status copy and its
              programme row names the programme file
  pins        rule_pins_tests.py check over the whole tree and rule_pins.py
              check over the specs named by every piece row's `spec` key;
              WARN until the row FU-HARNESS-findings is attached in
              pieces.toml, DRIFT after (HARNESS-C1b)
  register    a closed register row whose Answer says `until Westley`, `Westley to
              confirm`, `Westley answers`, `Architect default` or the word `default`,
              or a row of other than six cells; same WARN/DRIFT switch (HARNESS-C235)
  reviews     a top-level story_reviews/*.md row dated on or after
              DRAFT-review-fields-from whose reviewer-verdict cell lacks `legend=`,
              `unit=` or `band=`; same switch (HARNESS-C235)
  launch      a row with `script`, `args` or `launch` keys must carry a `launch`
              sha equal to sha256 of `git show <base>:<script>` (`-` only for
              PRE_LAUNCH_IDS), a script and args path in git at --base; always
              DRIFT, no switch (HARNESS-C4). `check pieces` also prints
              `unknown key <k> in <id>` for a key outside KNOWN_KEYS.
  findings    a FINDING- ledger row dated (git blame) on or after 2026-10-26 whose
              Event cell lacks `found-by=`, or a TD- row lacking `ruler=`; always
              DRIFT (HARNESS-mm-3, method rev 3 G17)
  metrics     WARN naming the ids with status FAIL in the latest
              method_rev3_2026-10-26/metrics/*.json, else OK (HARNESS-mm-3)
  method_pins every pin in method_rev3_2026-10-26/pins.toml with a non-empty
              `since` must appear verbatim in `git show <base>:<file>`; a pin with
              an empty `since` is skipped; always DRIFT (HARNESS-mm-3, A2)
  sweep       the last PASS or BASE row of sweeps.md is the anchor: WARN above
              DRAFT-slow-tier-batch first-parent `Land ` merges since its sha on
              origin/main or, with at least one such landing, its row older than
              DRAFT-slow-tier-hours, DRIFT above DRAFT-slow-tier-drift-mult times
              either; zero landings since the anchor is quiet at any age
              (DEC-sweep-quiet-2026-10-29); a REJECT row is never an
              anchor and never a DRIFT (HARNESS-gate-tiers, spec section 8 B3, F10)
  (`check pieces` also accepts the keys `story` and `contract`, A1.)

See also: docs/northstar/plans/2026-10-07-visible-game-programme.md Lane table
"""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
D_PROGRAMME = "docs/northstar/plans/2026-10-07-visible-game-programme.md"
D_PIECES = "docs/northstar/plans/push/pieces.toml"
D_STORIES = "docs/bible/stories.md"
D_REVIEWS = "docs/northstar/story_reviews"
D_ROADMAP = "docs/northstar/ROADMAP.md"
D_REGISTER = "docs/northstar/ambiguity_register.md"
D_LEDGER = "docs/northstar/plans/push_ledger_2026-09-22.md"
D_MM = "docs/northstar/plans/method_rev3_2026-10-26"
D_SWEEPS = "docs/northstar/plans/push/sweeps.md"
# Named drafts of docs/northstar/plans/2026-10-29-layered-gate-spec.md section 4; Westley's to change.
SLOW_TIER_BATCH, SLOW_TIER_HOURS, SLOW_TIER_DRIFT_MULT = 3, 2, 2  # DRAFT-slow-tier-batch, -hours, -drift-mult
SWEEP_TS_FMT = "%Y-%m-%d %H:%M"  # the date-time cell of a sweeps.md row, UTC
LEDGER_TOKENS_FROM = "2026-10-26"  # method rev 3 G17: found-by= and ruler= are required from this date
SWITCH_ROW = "FU-HARNESS-findings"

SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{7,40}(?![0-9a-fA-F])")
# Column 8 of the queue format in docs/northstar/story_reviews/README.md.
VERDICT_COL = 7
REVIEW_VERDICT_COL, REVIEW_DATE_COL = 6, 8
REVIEW_FIELDS_FROM = "2026-10-20"  # DRAFT-review-fields-from, harness enforcement spec section 4
REVIEW_FIELDS = ("legend", "unit", "band")
# The ten keys pieces.toml rows use plus the four HARNESS-C4 adds. See also: pieces.py, which rejects no unknown key.
KNOWN_KEYS = frozenset("id manager wave owns owns_glob acceptance depends_on status tests_pending size_estimate "
                       "script args launch spec story contract impact".split())
# Ids whose `launch = "-"` is exempt from the sha test (launched before launch_check.sh); REPIN fills it.
PRE_LAUNCH_IDS = ()
STAND_IN_ANSWER = re.compile(r"until Westley|Westley to confirm|Westley answers|Architect default|\bdefault\b", re.I)


def cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_rule_row(line):
    return bool(re.fullmatch(r"\|[\s:|-]+\|?", line.strip())) and "-" in line


def is_ancestor(repo, sha, base):
    r = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, base],
                       capture_output=True, text=True)
    return r.returncode == 0


def check_lane_table(repo, base, programme):
    lines = programme.read_text().splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("| Lane | On main |")), None)
    if start is None:
        return [("lane_table", False, "no table headed '| Lane | On main |'")]
    on_main = cells(lines[start]).index("On main")
    out, n = [], 0
    for ln in lines[start + 1:]:
        if not ln.strip().startswith("|"):
            break
        if is_rule_row(ln):
            continue
        row = cells(ln)
        if len(row) <= on_main:
            continue
        for sha in SHA_RE.findall(row[on_main]):
            n += 1
            if not is_ancestor(repo, sha, base):
                out.append(("lane_table", False, f"{row[0]} {sha} is not an ancestor of {base}"))
    return out or [("lane_table", True, f"{n} shas checked")]


def parse_pieces(path):
    pieces, cur = [], None
    for ln in path.read_text().splitlines():
        s = ln.strip()
        if s.startswith("#"):
            continue
        if s == "[[piece]]":
            cur = {"id": "", "state": "", "sha": "", "spec": "", "script": "", "args": "", "launch": None, "keys": []}
            pieces.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"([A-Za-z_][\w-]*)\s*=", s)
        if m:
            cur["keys"].append(m.group(1))
        m = re.match(r'id\s*=\s*"([^"]+)"', s)
        if m:
            cur["id"] = m.group(1)
        for key in ("spec", "script", "args", "launch"):
            m = re.match(key + r'\s*=\s*"([^"]*)"', s)
            if m:
                cur[key] = m.group(1)
        if re.match(r"status\s*=", s):
            # Bare string or inline table. See also: owner_lint.py:37-44
            m = re.match(r'status\s*=\s*"([^"]*)"', s) or re.search(r'state\s*=\s*"([^"]*)"', s)
            if m:
                cur["state"] = m.group(1)
            m = re.search(r'attach_sha\s*=\s*"([0-9a-fA-F]{7,})"', s)
            if m:
                cur["sha"] = m.group(1)
    return pieces


def check_pieces(repo, base, pieces_path):
    pieces = parse_pieces(pieces_path)
    out = []
    for p in pieces:
        out += [("pieces", False, f"unknown key {k} in {p['id']}") for k in p["keys"] if k not in KNOWN_KEYS]
        if p["state"] == "attached" and p["sha"] and not is_ancestor(repo, p["sha"], base):
            out.append(("pieces", False, f"{p['id']} {p['sha']} is not an ancestor of {base}"))
    if out:
        return out
    fly = [p["id"] for p in pieces if p["state"] == "in_flight"]
    return [("pieces", True, "in_flight: " + ", ".join(fly))]


def git_blob(repo, base, path):
    r = subprocess.run(["git", "-C", str(repo), "show", f"{base}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def check_launch(repo, base, pieces_path):
    """See also: launch_check.sh, which prints the sha a row's `launch` key records."""
    out, n = [], 0
    for p in parse_pieces(pieces_path):
        if not (p["script"] or p["args"] or p["launch"] is not None):
            continue
        n += 1
        if p["script"]:
            blob = git_blob(repo, base, p["script"])
            if blob is None:
                out.append(("launch", False, f"{p['id']} script {p['script']} is not in git at {base}"))
            if p["launch"] is None:
                out.append(("launch", False, f"{p['id']} has a script and no launch key"))
            elif p["launch"] == "-":
                if p["id"] not in PRE_LAUNCH_IDS:
                    out.append(("launch", False, f"{p['id']} launch is - and the id is not in PRE_LAUNCH_IDS"))
            elif blob is not None and hashlib.sha256(blob).hexdigest() != p["launch"]:
                out.append(("launch", False, f"{p['id']} launch differs from sha256 of {base}:{p['script']}"))
        if p["args"] not in ("", "-") and git_blob(repo, base, p["args"]) is None:
            out.append(("launch", False, f"{p['id']} args {p['args']} is not in git at {base}"))
    return out or [("launch", True, f"{n} rows checked")]


PINS_FINDING = re.compile(r"^PINS REJECT \S+ R-\d+-\d+ (stale|missing) ")


def check_pins(repo, pieces_path):
    """Whole-tree pins; WARN while the switch row is not attached, DRIFT after. See also: rule_pins_tests.py, rule_pins.py."""
    pieces = parse_pieces(pieces_path)
    specs = sorted({p["spec"] for p in pieces if p["spec"] and (repo / p["spec"]).is_file()})
    runs = [[sys.executable, str(HERE / "rule_pins_tests.py"), "check", str(repo)]]
    if specs:
        runs.append([sys.executable, str(HERE / "rule_pins.py"), "check", *specs])
    found = []
    for cmd in runs:
        found += subprocess.run(cmd, cwd=repo, capture_output=True, text=True).stdout.splitlines()
    kinds = [m.group(1) for m in map(PINS_FINDING.match, found) if m]
    if not kinds:
        return [("pins", True, "every pin is right")]
    detail = ", ".join(f"{kinds.count(k)} {k}" for k in ("stale", "missing") if k in kinds)
    return [("pins", switched(pieces), detail)]


def switched(pieces):
    """False (DRIFT) once FU-HARNESS-findings is attached, else "warn". See also: owner_lint.py:37-44."""
    return False if any(p["id"] == SWITCH_ROW and p["state"] == "attached" for p in pieces) else "warn"


def check_register(register, pieces_path):
    """See also: spec_provenance.py reason (5), which reads the same six-cell rows."""
    if not register.is_file():
        return [("register", True, f"no register file at {register.name}")]
    found, n = [], 0
    for ln in register.read_text().splitlines():
        row = cells(ln)
        if not ln.strip().startswith("|") or is_rule_row(ln) or not row[0].startswith("Q-"):
            continue
        n += 1
        if len(row) != 6:
            found.append(f"{row[0]} is malformed: {len(row)} cells, not 6")
        elif row[4].lower().startswith("closed") and (m := STAND_IN_ANSWER.search(row[5])):
            found.append(f"{row[0]} is closed with a stand-in answer: {m.group(0)}")
    flag = switched(parse_pieces(pieces_path))
    return [("register", flag, f) for f in found] or [("register", True, f"{n} rows checked")]


def check_reviews(reviews, pieces_path):
    found, n = [], 0
    for f in sorted(reviews.glob("*.md")):
        for ln in f.read_text().splitlines():
            row = cells(ln)
            if len(row) <= REVIEW_DATE_COL or not re.fullmatch(r"\d{4}-\d\d-\d\d", row[REVIEW_DATE_COL]):
                continue
            if row[REVIEW_DATE_COL] < REVIEW_FIELDS_FROM:
                continue
            n += 1
            lacking = [k for k in REVIEW_FIELDS if not re.search(r"(?<!\w)" + k + "=", row[REVIEW_VERDICT_COL])]
            if lacking:
                found.append(f"{f.name} {row[0]} verdict cell lacks " + ", ".join(k + "=" for k in lacking))
    flag = switched(parse_pieces(pieces_path))
    return [("reviews", flag, f) for f in found] or [("reviews", True, f"{n} rows checked")]


def check_seen(reviews, stories):
    approved = 0
    for f in sorted(reviews.glob("*.md")):
        for ln in f.read_text().splitlines():
            if not ln.strip().startswith("|") or is_rule_row(ln):
                continue
            row = cells(ln)
            if len(row) > VERDICT_COL and row[VERDICT_COL] == "approved":
                approved += 1
    seen = 0
    status_col = 3
    for ln in stories.read_text().splitlines():
        if not ln.strip().startswith("|") or is_rule_row(ln):
            continue
        row = cells(ln)
        if row and row[0] == "Story" and "Status" in row:
            status_col = row.index("Status")
            continue
        if len(row) > status_col and row[status_col].startswith("Seen"):
            seen += 1
    if approved != seen:
        return [("seen", False, f"{approved} approved vs {seen} Seen")]
    return [("seen", True, f"{approved} approved = {seen} Seen")]


def check_roadmap(roadmap, programme_rel):
    section, inside = [], False
    for ln in roadmap.read_text().splitlines():
        if ln.startswith("## "):
            if inside:
                break
            inside = ln.startswith("## 1. Now building")
            continue
        if inside:
            section.append(ln)
    if not inside and not section:
        return [("roadmap", False, "no section '## 1. Now building'")]
    out, found = [], False
    for ln in section:
        if not ln.lstrip().startswith("|"):
            continue
        if ln.startswith("| Visible game lane"):
            out.append(("roadmap", False, f"lane status copy: {ln.strip()[:100]}"))
        if "visible game programme" in ln.lower() and not found:
            found = True
            if programme_rel not in ln:
                out.append(("roadmap", False, f"programme row lacks {programme_rel}: {ln.strip()[:100]}"))
    if not found:
        out.append(("roadmap", False, "no row naming the visible game programme"))
    return out or [("roadmap", True, "no lane copies; programme row names its file")]


def blame_dates(repo, rel):
    """{1-based line: author date} of the working file; an uncommitted line counts as today."""
    r = subprocess.run(["git", "-C", str(repo), "blame", "--line-porcelain", "--", rel], capture_output=True, text=True)
    out, line = {}, 0
    for ln in r.stdout.splitlines():
        if re.match(r"[0-9a-f]{40} \d+ \d+", ln):
            line = int(ln.split()[2])
        elif ln.startswith("author-time "):
            out[line] = datetime.datetime.fromtimestamp(int(ln.split()[1]), datetime.timezone.utc).date().isoformat()
    return out


def check_findings(repo, ledger):
    """See also: the ledger token rules in docs/northstar/plans/method_rev3_2026-10-26/spec.md Design item 3."""
    if not ledger.is_file():
        return [("findings", True, f"no ledger file at {ledger.name}")]
    lines = ledger.read_text().splitlines()
    rows = [(i, c[1]) for i, ln in enumerate(lines, 1) if ln.startswith("|") and len(c := cells(ln)) > 1
            and re.match(r"(FINDING|TD)-", c[1])]
    dates = blame_dates(repo, ledger.relative_to(repo).as_posix()) if rows else {}
    today = datetime.date.today().isoformat()
    out = []
    for i, event in rows:
        if dates.get(i, today) < LEDGER_TOKENS_FROM:
            continue
        token = "found-by=" if event.startswith("FINDING-") else "ruler="
        if token not in event:
            out.append(("findings", False, f"{event.split()[0]} (ledger line {i}) lacks {token}"))
    return out or [("findings", True, f"{len(rows)} rows checked")]


def check_metrics(mm):
    files = sorted((mm / "metrics").glob("*.json"))
    if not files:
        return [("metrics", True, "no metrics file")]
    d = json.loads(files[-1].read_text())
    fails = [m["id"] for m in d.get("metrics", []) if m.get("status") == "FAIL"]
    return [("metrics", "warn", ", ".join(fails))] if fails else [("metrics", True, f"{files[-1].stem} has no FAIL")]


def check_method_pins(repo, base, mm):
    """See also: pins.toml (spec A2); rule_pins.py pins R-###-## test rules only."""
    path = mm / "pins.toml"
    if not path.is_file():
        return [("method_pins", True, "no pins.toml")]
    out, n = [], 0
    for pin in tomllib.loads(path.read_text()).get("pin", []):
        if not pin.get("since"):
            continue
        n += 1
        blob = git_blob(repo, base, pin["file"])
        if blob is None or pin["sentence"] not in blob.decode(errors="replace"):
            out.append(("method_pins", False, f"{pin.get('gap', '?')} sentence missing from {base}:{pin['file']}"))
    return out or [("method_pins", True, f"{n} dated pins checked")]


def check_sweep(repo, base, sweeps):
    """See also: tests/specfactory/test_gate_tiers.py group 4; row format in the layered gate spec section 8 B2.
    A landing is a first-parent merge commit on origin/main (else `base`) whose subject begins `Land `."""
    if not sweeps.is_file():
        return [("sweep", True, f"no {sweeps.name}")]
    anchor = None
    for ln in sweeps.read_text().splitlines():
        c = cells(ln) if ln.strip().startswith("|") else []
        if len(c) >= 3 and c[2] in ("PASS", "BASE"):
            anchor = c
    if anchor is None:
        return [("sweep", True, "no PASS or BASE row yet")]
    sha = anchor[1]
    tip = "origin/main" if subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", "origin/main"],
                                          capture_output=True).returncode == 0 else base
    if not is_ancestor(repo, sha, tip):
        return [("sweep", "warn", f"{anchor[2]} row sha {sha} is not an ancestor of {tip}")]
    log = subprocess.run(["git", "-C", str(repo), "log", "--first-parent", "--merges", "--format=%s", f"{sha}..{tip}"],
                         capture_output=True, text=True).stdout.splitlines()
    landings = sum(1 for subject in log if subject.startswith("Land "))
    if landings == 0:
        return [("sweep", True, f"0 landings since {sha}")]
    try:
        stamp = datetime.datetime.strptime(anchor[0], SWEEP_TS_FMT).replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return [("sweep", False, f"{anchor[2]} row at {sha} has an unreadable date-time {anchor[0]!r}")]
    hours = (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds() / 3600
    detail = f"{landings} landings and {hours:.1f} h since the {anchor[2]} row at {sha[:8]}"
    if landings > SLOW_TIER_BATCH * SLOW_TIER_DRIFT_MULT or hours > SLOW_TIER_HOURS * SLOW_TIER_DRIFT_MULT:
        return [("sweep", False, detail)]
    if landings > SLOW_TIER_BATCH or hours > SLOW_TIER_HOURS:
        return [("sweep", "warn", detail)]
    return [("sweep", True, detail)]


def main(argv):
    ap = argparse.ArgumentParser(prog="status_check.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--programme", default=D_PROGRAMME)
    ap.add_argument("--pieces", default=D_PIECES)
    ap.add_argument("--stories", default=D_STORIES)
    ap.add_argument("--reviews", default=D_REVIEWS)
    ap.add_argument("--roadmap", default=D_ROADMAP)
    ap.add_argument("--register", default=D_REGISTER)
    ap.add_argument("--ledger", default=D_LEDGER)
    ap.add_argument("--method-dir", default=D_MM)
    ap.add_argument("--sweeps", default=D_SWEEPS)
    a = ap.parse_args(argv)
    repo = Path(a.repo)

    def at(p):
        p = Path(p)
        return p if p.is_absolute() else repo / p

    results = []
    results += check_lane_table(repo, a.base, at(a.programme))
    results += check_pieces(repo, a.base, at(a.pieces))
    results += check_seen(at(a.reviews), at(a.stories))
    results += check_roadmap(at(a.roadmap), a.programme)
    results += check_pins(repo, at(a.pieces))
    results += check_register(at(a.register), at(a.pieces))
    results += check_reviews(at(a.reviews), at(a.pieces))
    results += check_launch(repo, a.base, at(a.pieces))
    results += check_findings(repo, at(a.ledger))
    results += check_metrics(at(a.method_dir))
    results += check_method_pins(repo, a.base, at(a.method_dir))
    results += check_sweep(repo, a.base, at(a.sweeps))
    for name, ok, detail in results:
        print(f"STATUS {name} {'WARN' if ok == 'warn' else 'OK' if ok else 'DRIFT'} {detail}")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
