#!/usr/bin/env python3
"""status_check.py: method rev 2, guard 7. The status copies must agree.

Four checks, one `STATUS <check> OK|DRIFT <detail>` line each (a check may
print several DRIFT lines); exit 1 when any check is DRIFT, else 0.

  lane_table  every sha in the programme lane table's "On main" cells is an
              ancestor of --base
  pieces      every attached piece's attach_sha in pieces.toml is an ancestor
              of --base; in_flight piece ids are listed
  seen        queue rows with Westley verdict "approved" equal stories.md rows
              whose Status is "Seen" or starts with "Seen"
  roadmap     ROADMAP "## 1. Now building" holds no lane status copy and its
              programme row names the programme file

See also: docs/northstar/plans/2026-10-07-visible-game-programme.md Lane table
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D_PROGRAMME = "docs/northstar/plans/2026-10-07-visible-game-programme.md"
D_PIECES = "docs/northstar/plans/push/pieces.toml"
D_STORIES = "docs/bible/stories.md"
D_REVIEWS = "docs/northstar/story_reviews"
D_ROADMAP = "docs/northstar/ROADMAP.md"

SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{7,40}(?![0-9a-fA-F])")
# Column 8 of the queue format in docs/northstar/story_reviews/README.md.
VERDICT_COL = 7


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
            cur = {"id": "", "state": "", "sha": ""}
            pieces.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r'id\s*=\s*"([^"]+)"', s)
        if m:
            cur["id"] = m.group(1)
        if re.match(r"status\s*=", s):
            m = re.search(r'state\s*=\s*"([^"]*)"', s)
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
        if p["state"] == "attached" and p["sha"] and not is_ancestor(repo, p["sha"], base):
            out.append(("pieces", False, f"{p['id']} {p['sha']} is not an ancestor of {base}"))
    if out:
        return out
    fly = [p["id"] for p in pieces if p["state"] == "in_flight"]
    return [("pieces", True, "in_flight: " + ", ".join(fly))]


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


def main(argv):
    ap = argparse.ArgumentParser(prog="status_check.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--programme", default=D_PROGRAMME)
    ap.add_argument("--pieces", default=D_PIECES)
    ap.add_argument("--stories", default=D_STORIES)
    ap.add_argument("--reviews", default=D_REVIEWS)
    ap.add_argument("--roadmap", default=D_ROADMAP)
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
    for name, ok, detail in results:
        print(f"STATUS {name} {'OK' if ok else 'DRIFT'} {detail}")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
