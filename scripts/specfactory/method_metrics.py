#!/usr/bin/env python3
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" and "The gaps" (HARNESS-mm-1a)
"""Method metrics, git and ledger half: M01, M02, M04, M05, M09, M10, M11, M12, M19, M20, M23, M24.

One function per metric: f(ctx) -> (status, value, threshold, numbers); status PASS|FAIL|DRAFT|NA. Rendered as
`METRIC <id> PASS|FAIL|DRAFT|NA <value> vs <op><threshold> <gap> (<numbers>) <week>`; the CLI exits 1 on any FAIL.
Everything is read from origin/main through git on --repo, never from a live checkout.

# See also: scripts/specfactory/method_metrics_runs.py (runs and transcript metrics) and
# scripts/specfactory/method_metrics_cli.py (the entry point: M16-M18, --write, --last, --weeks). Both import
# Context, judge, na, fmt, METRICS and render from here; this file's __main__ hands over to the CLI.
"""
import argparse
import csv
import datetime as dt
import os
import re
import statistics
import subprocess
import sys
import tomllib
from pathlib import Path

LEDGER_REL = "docs/northstar/plans/push_ledger_2026-09-22.md"
PIECES_REL = "docs/northstar/plans/push/pieces.toml"
README_REL = "docs/northstar/story_reviews/westley/README.md"
STORIES_REL = "docs/bible/stories.md"
CLIENT_PATHS = ("csrc/", "autoload/", "scenes/")
LAB_PATHS = ("scripts/skilllab/",)
GAME_EXT = (".c", ".h", ".gd", ".tscn", ".py")
TEST_EXT = (".py", ".gd", ".c", ".h")
TEST_CODE_EXT = TEST_EXT + (".sh", ".tscn", ".md", ".uid")
RETRO_REL = "docs/northstar/plans/retro_"
SLUG = "-home-westopoli-Projects-ouroboros-manifold"
DETAIL_CAP = 400
METHOD_PATHS = ("CLAUDE.md", "docs/northstar/README.md", "docs/northstar/PLAN.md",
                "docs/northstar/plans/workflows_2026-10-07/")
# M11c does not count these: lab data (research/*/data/), shots, and the harness records (pieces, gate csv, stored weeks)
M11C_SKIP = re.compile(r"^docs/northstar/(research/[^/]+/data/|story_reviews/|plans/push/|plans/method_rev3_2026-10-26/metrics/)")
PIECE_STATES = ("attached", "queued", "superseded", "landed", "pending")
FINDINGS_FROM = "2026-10-26"


def week_bounds(week):
    """'2026-W44' -> (monday 00:00 UTC epoch, next monday epoch)."""
    y, w = week.split("-W")
    mon = dt.datetime.combine(dt.date.fromisocalendar(int(y), int(w), 1), dt.time(), tzinfo=dt.timezone.utc)
    return int(mon.timestamp()), int((mon + dt.timedelta(days=7)).timestamp())


def date_epoch(s):
    return int(dt.datetime.fromisoformat(s[:10]).replace(tzinfo=dt.timezone.utc).timestamp())


def fmt(v):
    if isinstance(v, float):
        s = f"{v:.2f}".rstrip("0")
        return s + "0" if s.endswith(".") else s
    return str(v)


def under(path, prefixes):
    return path.startswith(tuple(prefixes))


def is_fixture(p):
    return "/fixtures/" in p


def week_range(spec):
    """'2026-W40..2026-W42' -> ['2026-W40', '2026-W41', '2026-W42']."""
    a, b = spec.split("..")
    day = dt.date.fromisocalendar(int(a[:4]), int(a.split("W")[1]), 1)
    end = dt.date.fromisocalendar(int(b[:4]), int(b.split("W")[1]), 1)
    out = []
    while day <= end:
        out.append("%d-W%02d" % day.isocalendar()[:2])
        day += dt.timedelta(days=7)
    return out


class Context:
    """Paths, week, phase, thresholds and cached git reads shared by every metric."""

    def __init__(self, a):
        self.week, self.repo = a.week, Path(a.repo)
        self.t0, self.t1 = week_bounds(a.week)
        self.th = tomllib.loads(Path(a.thresholds).read_text()) if a.thresholds and Path(a.thresholds).is_file() else {}
        self.phase = a.phase or self.th.get("phase", "lab")
        self.ledger_rel = self.rel(a.ledger, LEDGER_REL)
        self.pieces_rel = self.rel(a.pieces, PIECES_REL)
        self.gate_runs, self.sdk_runs = a.gate_runs, a.sdk_runs
        self.transcripts, self.wt = a.transcripts, a.wt
        self.project, self.verbose = a.project, a.verbose
        self.prices = self.th.get("prices", {})
        self.decisive = {}
        self._c = {}

    def rel(self, p, default):
        if not p:
            return default
        try:
            return os.path.relpath(Path(p).resolve(), self.repo.resolve())
        except ValueError:
            return default

    def git(self, *args, check=True):
        r = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True)
        if check and r.returncode:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout

    def cached(self, key, fn):
        if key not in self._c:
            self._c[key] = fn()
        return self._c[key]

    # ---- thresholds
    def thr(self, mid):
        return self.th.get(mid)

    @property
    def product_paths(self):  # the phase's product columns (spec A4)
        return CLIENT_PATHS + (LAB_PATHS if self.phase == "lab" else ())

    # ---- git
    def commits(self):
        """Non-merge commits since 16 days before the week: [{sha, at, paths: [(add, del, path)]}]."""
        def load():
            out = self.git("log", "origin/main", "--no-merges", "--no-renames", "--numstat",
                           f"--since=@{self.t0 - 16 * 86400}", "--format=@%H %at")
            res = []
            for ln in out.splitlines():
                if ln.startswith("@"):
                    sha, at = ln[1:].split()
                    res.append({"sha": sha, "at": int(at), "paths": []})
                elif ln.strip() and res:
                    a, d, p = ln.split("\t", 2)
                    res[-1]["paths"].append((int(a) if a.isdigit() else 0, int(d) if d.isdigit() else 0, p))
            return res
        return self.cached("commits", load)

    def week_commits(self):
        return [c for c in self.commits() if self.t0 <= c["at"] < self.t1]

    def added_files(self, pathspec=None):
        """[(sha, at, path)] for files added (status A) on origin/main in the trailing 30 days."""
        def load():
            args = ["log", "origin/main", "--no-renames", "--diff-filter=A", "--name-only",
                    f"--since=@{self.t0 - 30 * 86400}", "--format=@%H %at"]
            out = self.git(*args)
            res, cur = [], None
            for ln in out.splitlines():
                if ln.startswith("@"):
                    cur = ln[1:].split()
                elif ln.strip() and cur:
                    res.append((cur[0], int(cur[1]), ln))
            return res
        return self.cached("added", load)

    def week_added(self):
        return [x for x in self.added_files() if self.t0 <= x[1] < self.t1]

    def first_parent(self):
        """[(sha, at, parents, paths)] first-parent commits in the week (merges diffed against parent 1)."""
        def load():
            out = self.git("log", "origin/main", "--first-parent", "--diff-merges=first-parent", "--no-renames",
                           "--name-only", f"--since=@{self.t0 - 86400}", "--format=@%H %at %P")
            res = []
            for ln in out.splitlines():
                if ln.startswith("@"):
                    f = ln[1:].split()
                    res.append((f[0], int(f[1]), f[2:], []))
                elif ln.strip() and res:
                    res[-1][3].append(ln)
            return [c for c in res if self.t0 <= c[1] < self.t1]
        return self.cached("fp", load)

    def is_on_main(self, sha):
        r = subprocess.run(["git", "-C", str(self.repo), "merge-base", "--is-ancestor", sha, "origin/main"],
                           capture_output=True)
        return r.returncode == 0

    def show(self, rel):
        r = subprocess.run(["git", "-C", str(self.repo), "show", f"origin/main:{rel}"], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None

    def blame_rows(self, rel):
        """[(author epoch, line text)] for a file on origin/main; [] when the file is not there."""
        def load():
            r = subprocess.run(["git", "-C", str(self.repo), "blame", "--line-porcelain", "origin/main", "--", rel],
                               capture_output=True, text=True)
            res, at = [], 0
            for ln in r.stdout.splitlines():
                if ln.startswith("author-time "):
                    at = int(ln.split()[1])
                elif ln.startswith("\t"):
                    res.append((at, ln[1:]))
            return res
        return self.cached(("blame", rel), load)

    def ledger_rows(self, in_week=True):
        """[(epoch, event cell, full line)] of table rows, optionally only those added in the week."""
        out = []
        for at, ln in self.blame_rows(self.ledger_rel):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not ln.lstrip().startswith("|") or len(cells) < 2 or set(cells[0]) <= set("-: "):
                continue
            if in_week and not self.t0 <= at < self.t1:
                continue
            out.append((at, cells[1], ln))
        return out

    # ---- gate rows
    def all_gate_rows(self):
        """Every well-formed row of gate_runs.csv (header from merge_gate.sh); a row with more or fewer fields than
        the header is skipped with a note on stderr (a multi-piece label written unquoted shifts every column)."""
        def load():
            if not self.gate_runs or not Path(self.gate_runs).is_file():
                return []
            with open(self.gate_runs, newline="") as f:
                rows = list(csv.DictReader(f))
            ok = [r for r in rows if None not in r and None not in r.values()]
            if len(ok) < len(rows):
                print(f"method_metrics: skipped {len(rows) - len(ok)} malformed rows of {self.gate_runs}", file=sys.stderr)
            return ok
        return self.cached("gate_all", load)

    def gate_rows(self, days=7):
        """Rows dated in the week (days=7) or in the `days` days up to its end."""
        def in_window(r):
            try:
                return self.t1 - days * 86400 <= date_epoch(r["date"]) < self.t1
            except ValueError:
                return False
        return self.cached(("gate", days), lambda: [r for r in self.all_gate_rows() if in_window(r)])

    def pieces(self):
        txt = self.show(self.pieces_rel)
        return tomllib.loads(txt).get("piece", []) if txt else []

    def has_ledger(self):
        return self.show(self.ledger_rel) is not None

    def retro_folders(self):
        """{folder: epoch of its first added file} over the whole history, for retro_* folders under plans/."""
        def load():
            out = self.git("log", "origin/main", "--no-renames", "--diff-filter=A", "--name-only", "--format=@%at",
                           "--", "docs/northstar/plans/")
            first, at = {}, 0
            for ln in out.splitlines():
                if ln.startswith("@"):
                    at = int(ln[1:])
                elif ln.startswith(RETRO_REL):
                    f = "/".join(ln.split("/")[:4])
                    first[f] = min(first.get(f, at), at)
            return first
        return self.cached("retro", load)

    def recent_retro_folders(self):
        """Retro folders first created in the 14 days up to the week's end (the current window)."""
        return {f for f, at in self.retro_folders().items() if self.t1 - 14 * 86400 <= at < self.t1}

    def in_recent_retro(self, path):
        return any(path.startswith(f + "/") for f in self.recent_retro_folders())

    def lab_sum(self, r):
        """Product lines of a gate row in this phase: product_lines, plus lab_lines in the lab phase."""
        return int(r["product_lines"]) + (int(r["lab_lines"]) if self.phase == "lab" else 0)


def judge(ctx, mid, value, numbers, rows=()):
    """The compare step: PASS/FAIL against the toml value, DRAFT instead of PASS while `approved` is empty."""
    t = ctx.thr(mid)
    if not t:
        return "NA", value, ("", "no threshold"), numbers
    op, tv = t.get("direction", "<="), t["value"]
    ok = value <= tv if op == "<=" else value >= tv
    status = "PASS" if ok else "FAIL"
    if status == "PASS" and not t.get("approved"):
        status = "DRAFT"
    if status == "FAIL":
        ctx.decisive[mid] = list(rows)
    return status, value, (op, tv), numbers


def na(ctx, mid, numbers):
    t = ctx.thr(mid) or {}
    return "NA", "NA", (t.get("direction", ""), t.get("value", "")), numbers


def phase_ok(ctx, mid):
    p = (ctx.thr(mid) or {}).get("phase", "both")
    return p == "both" or p == ctx.phase


def pct(n, d):
    return 100.0 * n / d if d else 0.0


# ======================================================================= metrics
def m01(ctx):  # G01 test-code lines over game-code lines
    tests = game = 0
    for c in ctx.week_commits():
        for a, _, p in c["paths"]:
            base = os.path.basename(p)
            if p.startswith("tests/") and not is_fixture(p) and p.endswith(TEST_EXT) and "golden" not in base:
                tests += a
            elif under(p, ctx.product_paths) and p.endswith(GAME_EXT):
                game += a
    n = f"tests +{tests}, game +{game}"
    if game < (ctx.thr("M01") or {}).get("min_game_lines", 200):
        return na(ctx, "M01", n + " (game under the minimum)")
    return judge(ctx, "M01", round(tests / game, 2), n)


def _landings(ctx):
    return [r for r in ctx.gate_rows() if r["rc"] == "0" and ctx.is_on_main(r["candidate_sha"])]


def m02(ctx):  # G02 test-defect rows over landings
    td = [e for _, e, _ in ctx.ledger_rows() if e.startswith("TD-")]
    land = len(_landings(ctx))
    rows = [f"{e.split()[0]} {next((x for x in e.split() if x.startswith('ruler=')), 'ruler=?')}" for e in td]
    n = f"{len(td)} TD rows, {land} landings"
    if not land:
        return na(ctx, "M02", n)
    return judge(ctx, "M02", round(len(td) / land, 2), n, rows)


def m02b(ctx):
    td = [e for _, e, _ in ctx.ledger_rows() if e.startswith("TD-")]
    return judge(ctx, "M02b", len(td), f"{len(td)} TD rows", [e.split()[0] for e in td])


def m04(ctx):  # G03 docs-only commits over product commits
    docs = prod = 0
    for c in ctx.week_commits():
        ps = [p for _, _, p in c["paths"]]
        if any(under(p, ctx.product_paths) for p in ps):
            prod += 1
        elif ps and all(p.startswith("docs/") for p in ps):
            docs += 1
    n = f"{docs} docs-only commits, {prod} product commits"
    if not prod:
        return na(ctx, "M04", n + " (no product commit)")
    return judge(ctx, "M04", round(docs / prod, 2), n)


def m05(ctx):  # G03 ledger rows over landings
    rows = ctx.ledger_rows()
    land = len(_landings(ctx))
    n = f"{len(rows)} ledger rows, {land} landings"
    if not land:
        return na(ctx, "M05", n)
    return judge(ctx, "M05", round(len(rows) / land, 2), n, [e for _, e, _ in rows])


def m05b(ctx):
    d = [e.split()[0] for _, e, _ in ctx.ledger_rows() if e.startswith("DRAFT-")]
    return judge(ctx, "M05b", len(d), f"{len(d)} DRAFT rows", d)


def _gate_line(r):
    return f"{r['date']} {r['label']} rc={r['rc']} queue_s={r['queue_s']} stage_s={r['stage_s']} {r['reject_causes']}"


def m09(ctx):  # G06 suite timeouts in gate rows
    bad = [r for r in ctx.gate_rows() if "suite-timeout" in r["reject_causes"]]
    return judge(ctx, "M09", len(bad), f"{len(bad)} of {len(ctx.gate_rows())} gate rows", [_gate_line(r) for r in bad])


def m09b(ctx):
    ok = [r for r in ctx.gate_rows() if r["rc"] == "0"]
    if not ok:
        return na(ctx, "M09b", "no rc-0 gate row")
    med = statistics.median(float(r["stage_s"]) for r in ok)
    return judge(ctx, "M09b", med, f"median stage_s of {len(ok)} rc-0 rows", [_gate_line(r) for r in ok])


def m09c(ctx):
    rows = ctx.gate_rows()
    if not rows:
        return na(ctx, "M09c", "no gate row")
    worst = max(rows, key=lambda r: float(r["queue_s"]))
    return judge(ctx, "M09c", float(worst["queue_s"]), f"max queue_s of {len(rows)} rows", [_gate_line(worst)])


def m10(ctx):  # G07 a floor on landing size
    rows = [r for r in ctx.gate_rows() if r["rc"] == "0" and ctx.lab_sum(r) > 0]
    need = (ctx.thr("M10") or {}).get("min_rows", 3)
    n = f"{len(rows)} rc-0 rows with product lines"
    if len(rows) < need:
        return na(ctx, "M10", n + f", under {need}")
    return judge(ctx, "M10", statistics.median(ctx.lab_sum(r) for r in rows), n + f", lines {[ctx.lab_sum(r) for r in rows]}",
                 [_gate_line(r) for r in rows])


def m10b(ctx):
    big = [r for r in ctx.gate_rows() if r["rc"] == "0" and ctx.lab_sum(r) > 1000]
    return judge(ctx, "M10b", len(big), f"{len(big)} landings over 1000 product lines",
                 [f"{r['label']} lines={ctx.lab_sum(r)}" for r in big])


def m11(ctx):  # G08 northstar md lines over product lines
    if any(ctx.in_recent_retro(p) for _, _, p in ctx.week_added()):
        return na(ctx, "M11", "a file is added to a current retro folder this week")
    md = prod = 0
    for c in ctx.week_commits():
        for a, _, p in c["paths"]:
            if p.startswith("docs/northstar/") and p.endswith(".md"):
                md += a
            elif under(p, ctx.product_paths):
                prod += a
    n = f"md +{md}, product +{prod}"
    if not prod:
        return na(ctx, "M11", n)
    return judge(ctx, "M11", round(md / prod, 2), n)


def m11b(ctx):
    txt = ctx.show("CLAUDE.md")
    if txt is None:
        return na(ctx, "M11b", "no CLAUDE.md on origin/main")
    return judge(ctx, "M11b", len(txt.splitlines()), "CLAUDE.md lines")


def m11b_bytes(ctx):  # G08 wrapping keeps the line count flat while prose grows, so the bytes are bounded too
    txt = ctx.show("CLAUDE.md")
    if txt is None:
        return na(ctx, "M11b-bytes", "no CLAUDE.md on origin/main")
    return judge(ctx, "M11b-bytes", len(txt.encode()), "CLAUDE.md bytes")


def m11c(ctx):
    bad = [p for _, _, p in ctx.week_added() if p.startswith("docs/northstar/") and not p.endswith(".md")
           and not M11C_SKIP.match(p)]
    return judge(ctx, "M11c", len(bad), f"{len(bad)} non-md files outside data/, story_reviews/ and the records", bad)


def _beta_list(ctx):
    out = ctx.git("ls-tree", "-r", "--name-only", "origin/main", "docs/northstar/plans/").splitlines()
    cands = sorted(p for p in out if p.startswith("docs/northstar/plans/beta_") and p.endswith("/stories.md"))
    return (cands[-1], ctx.show(cands[-1])) if cands else (None, None)


def _list_stories(txt):
    return [ln.split("|")[1].strip() for ln in txt.splitlines() if ln.lstrip().startswith("| S-")]


def m12a(ctx):  # G09 the beta list exists, at most 25 rows, approved
    if not phase_ok(ctx, "M12a"):
        return na(ctx, "M12a", "beta only")
    path, txt = _beta_list(ctx)
    if txt is None:
        t = ctx.thr("M12a") or {}
        ctx.decisive["M12a"] = ["no docs/northstar/plans/beta_*/stories.md"]
        return "FAIL", 0, (t.get("direction", ""), t.get("value", "")), "no beta list on origin/main"
    rows = len(_list_stories(txt))
    approved = any(ln.startswith("Approved: Westley") for ln in txt.splitlines())
    r = judge(ctx, "M12a", rows, f"{rows} rows, approval line {'present' if approved else 'missing'} ({path})",
              [f"{path}: {rows} rows"])
    if r[0] in ("PASS", "DRAFT") and not approved:
        ctx.decisive["M12a"] = [f"{path}: no 'Approved: Westley' line"]
        return "FAIL", *r[1:]
    return r


def m12b(ctx):  # G09 landed product pieces whose story is on the list
    if not phase_ok(ctx, "M12b"):
        return na(ctx, "M12b", "beta only")
    _, txt = _beta_list(ctx)
    listed = set(_list_stories(txt)) if txt else set()
    landed = {l.strip() for r in ctx.gate_rows() if r["rc"] == "0" for l in r["label"].split(",")}
    prod = [p for p in ctx.pieces() if p["id"] in landed and any(under(o, CLIENT_PATHS) for o in p.get("owns", []))]
    if not prod:
        return na(ctx, "M12b", "no landed product piece")
    on = [p for p in prod if p.get("story") in listed]
    return judge(ctx, "M12b", round(pct(len(on), len(prod)), 1), f"{len(on)} of {len(prod)} landed product pieces on the list",
                 [f"{p['id']} story={p.get('story', '-')}" for p in prod if p not in on])


def m12c(ctx):  # G09 stories moved to Seen in the week
    if not phase_ok(ctx, "M12c"):
        return na(ctx, "M12c", "beta only")
    seen = []
    for at, ln in ctx.blame_rows(STORIES_REL):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.lstrip().startswith("| S-") and len(cells) > 3 and cells[3] == "Seen" and ctx.t0 <= at < ctx.t1:
            seen.append(cells[0])
    return judge(ctx, "M12c", len(seen), f"{len(seen)} stories moved to Seen", seen)


def m19a(ctx):  # G17 findings and test-defects without their token
    t0, t1 = date_epoch(FINDINGS_FROM), ctx.t1
    bad = []
    for at, e, _ in ctx.ledger_rows(in_week=False):
        if t0 <= at < t1 and ((e.startswith("FINDING-") and "found-by=" not in e)
                              or (e.startswith("TD-") and "ruler=" not in e)):
            bad.append(e.split()[0])
    return judge(ctx, "M19a", len(bad), f"{len(bad)} rows without found-by=/ruler=", bad)


def m19b(ctx):
    bad = [p["id"] for p in ctx.pieces()
           if not (isinstance(p.get("status"), dict) and p["status"].get("state") in PIECE_STATES)]
    return judge(ctx, "M19b", len(bad), f"{len(bad)} pieces with a non-standard status", bad)


def m19c(ctx):  # G17 product commits on main with no gate row
    keys = [r["candidate_sha"] for r in ctx.all_gate_rows() if r.get("candidate_sha")]
    prod = [c for c in ctx.first_parent() if any(under(p, ctx.product_paths) for p in c[3])]
    missing = [c[0] for c in prod
               if not any(c[0].startswith(k) or k.startswith(c[0]) or k in c[2][1:] for k in keys if len(k) >= 7)]
    n = f"{len(missing)} of {len(prod)} product commits ({fmt(pct(len(missing), len(prod)))}%) have no gate row"
    return judge(ctx, "M19c", len(missing), n, [m[:12] for m in missing])


def m20(ctx):  # G18 landings off the phase's lane
    if not phase_ok(ctx, "M20"):
        return na(ctx, "M20", "lab phase only")
    rows = [r for r in ctx.gate_rows() if r["rc"] == "0" and ctx.lab_sum(r) > 0]
    off = [r for r in rows if int(r["lab_lines"]) == 0 and int(r["product_lines"]) > 0]
    if not rows:
        return na(ctx, "M20", "no rc-0 gate row")
    return judge(ctx, "M20", round(pct(len(off), len(rows)), 1), f"{len(off)} client-only of {len(rows)} rc-0 landings",
                 [_gate_line(r) for r in off])


def m23(ctx):  # G22 goldens and data counted as tests
    bad = [p for _, _, p in ctx.week_added()
           if p.startswith("tests/") and not is_fixture(p)
           and (not p.endswith(TEST_CODE_EXT) or "golden" in os.path.basename(p))]
    return judge(ctx, "M23", len(bad), f"{len(bad)} golden/data files outside a fixtures/ directory", bad)


def _is_method(p):
    return p in METHOD_PATHS or p.startswith(METHOD_PATHS[3]) or p.endswith("dispatcher.md")


def m24a(ctx):  # G23 method text edited with no retro in the commit
    retro_adds = {sha for sha, _, p in ctx.added_files() if ctx.in_recent_retro(p)}
    bad = [c for c in ctx.week_commits() if any(_is_method(p) for _, _, p in c["paths"]) and c["sha"] not in retro_adds]
    return judge(ctx, "M24a", len(bad), f"{len(bad)} method-text commits that add no file to a current retro folder",
                 [c["sha"][:12] for c in bad])


def m24b(ctx):  # G23 retro folders created in the trailing 14 days
    recent = sorted(ctx.recent_retro_folders())
    return judge(ctx, "M24b", len(recent), f"{len(recent)} retro folders in 14 days", recent)


METRICS = {"M01": m01, "M02": m02, "M02b": m02b, "M04": m04, "M05": m05, "M05b": m05b, "M09": m09, "M09b": m09b,
           "M09c": m09c, "M10": m10, "M10b": m10b, "M11": m11, "M11b": m11b, "M11b-bytes": m11b_bytes, "M11c": m11c, "M12a": m12a,
           "M12b": m12b, "M12c": m12c, "M19a": m19a, "M19b": m19b, "M19c": m19c, "M20": m20, "M23": m23,
           "M24a": m24a, "M24b": m24b}


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def fields(ctx, mid, res):
    """(value, threshold) as printed: a percent unit gets a % suffix on both."""
    _, value, (op, tv), _ = res
    pc = "%" if (ctx.thr(mid) or {}).get("unit") == "%" else ""
    return fmt(value) + (pc if num(value) else ""), f"{op}{fmt(tv)}" + (pc if num(tv) else "")


def cap(ctx, text):
    return text if ctx.verbose or len(text) <= DETAIL_CAP else text[:DETAIL_CAP - 3] + "..."


def render(ctx, mid, res):
    value, thr = fields(ctx, mid, res)
    gap = (ctx.thr(mid) or {}).get("gap", "")
    return f"METRIC {mid} {res[0]} {value} vs {thr} {gap} ({cap(ctx, str(res[3]))}) {ctx.week}"


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--week", default=None)
    p.add_argument("--weeks", default=None, help="A..B: print the back-test table (values only, nothing judged)")
    p.add_argument("--phase", choices=("lab", "beta"))
    p.add_argument("--project", default=SLUG, help="transcript folder under --transcripts that is counted")
    p.add_argument("--verbose", action="store_true", help="print the full detail list under each line")
    for k, d in (("repo", "."), ("ledger", None), ("pieces", None), ("gate-runs", os.path.expanduser("~/Projects/om-push/gate_runs.csv")),
                 ("sdk-runs", os.path.expanduser("~/Projects/om-push/runs/sdk_runs.csv")),
                 ("transcripts", os.path.expanduser("~/.claude/projects")),
                 ("wt", os.path.expanduser("~/Projects/om-push/wt")),
                 ("thresholds", str(Path(__file__).with_name("method_thresholds.toml")))):
        p.add_argument("--" + k, default=d)
    return p


if __name__ == "__main__":
    import method_metrics_cli
    sys.exit(method_metrics_cli.main())
