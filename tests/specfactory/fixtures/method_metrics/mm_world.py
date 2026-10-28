# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" (fixtures for tests/specfactory/test_method_metrics.py)
"""Synthetic worlds for the method metrics tests: a git repo (author dates inside ISO week 2026-W44, Mon
2026-10-26 to Sun 2026-11-01), a ledger, pieces.toml, gate_runs.csv, sdk_runs.csv, transcripts, a wt/ tree and a
thresholds toml. `build_world(tmp, **opts)` returns the CLI argument list. The defaults are the KNOWN-GOOD week
(every metric PASS or NA); each test passes the one option that makes its metric the known-bad (positive control).

Interfaces the fixtures fix (the spec leaves them open; the tests writer's report lists them):
- gate_runs.csv columns: date,label,branch,base_sha,candidate_sha,queue_s,stage_s,rc,reject_stages,reject_causes,
  product_lines,test_lines,docs_lines,lab_lines (header line first; audit finding 1: the header the real
  docs/northstar/plans/push/gate_runs.csv carries, which the script must read). `label` is the piece id (a comma
  list is quoted by csv.writer, as merge_gate.sh must write it, finding 2).
  product_lines = csrc/ autoload/ scenes/ ; lab_lines = scripts/skilllab/ ; test_lines = tests/ ; docs_lines = docs/.
- sdk_runs.csv columns: date,label,piece,role,model,turns,cost,outcome (header first). cost in dollars.
- thresholds toml: top-level `phase`, `lanes`; one table per metric id (sub-ids too) with id, gap, draft, value,
  direction, unit, approved, baseline, window, phase. Percent thresholds are written as numbers like 25 (unit "%").
- ledger rows are `| time | event | detail |`; the event cell holds the id and the found-by= / ruler= tokens.
- the week of a ledger/README/stories row is the author date of the commit that added it (git blame).
"""
import csv
import json
import os
import subprocess
from pathlib import Path

WEEK = "2026-W44"
D = {"mon": "2026-10-26", "tue": "2026-10-27", "wed": "2026-10-28", "thu": "2026-10-29", "fri": "2026-10-30",
     "sun": "2026-11-01"}
LEDGER_REL = "docs/northstar/plans/push_ledger_2026-09-22.md"
PIECES_REL = "docs/northstar/plans/push/pieces.toml"
README_REL = "docs/northstar/story_reviews/westley/README.md"
DECISIONS_REL = "docs/northstar/story_reviews/westley/decisions.md"
STORIES_REL = "docs/bible/stories.md"
METRICS_DIR = "docs/northstar/plans/method_rev3_2026-10-26/metrics"
GATE_COLS = ["date", "label", "branch", "base_sha", "candidate_sha", "queue_s", "stage_s", "rc", "reject_stages",
             "reject_causes", "product_lines", "test_lines", "docs_lines", "lab_lines"]
SDK_COLS = ["date", "label", "piece", "role", "model", "turns", "cost", "outcome"]
SLUG = "-home-westopoli-Projects-ouroboros-manifold"  # default --project (finding 5): this repo's transcript folder
VERDICTS_REL = "docs/northstar/story_reviews/westley/verdicts_2026-10.md"
SONNET = "claude-sonnet-5-5"
FABLE = "claude-fable-5-1"

# id -> (direction, value, unit, phase). The spec's DRAFT numbers (spec.md "The gaps").
TH = {
    "M01": ("<=", 1.5, "ratio", "both"), "M01b": ("<=", 0, "runs", "both"),
    "M02": ("<=", 1.0, "ratio", "both"), "M02b": ("<=", 10, "rows", "both"), "M03": ("<=", 2, "rows", "both"),
    "M04": ("<=", 2.0, "ratio", "both"), "M05": ("<=", 3, "ratio", "both"), "M05b": ("<=", 2, "rows", "both"),
    "M06": ("<=", 25, "%", "both"), "M06b": ("<=", 0, "runs", "both"),
    "M07": ("<=", 5, "%", "both"), "M07b": ("<=", 0, "runs", "both"),
    "M08": ("<=", 0, "calls", "both"), "M08b": ("<=", 0, "turns", "both"),
    "M09": ("<=", 0, "rows", "both"), "M09b": ("<=", 3600, "s", "both"), "M09c": ("<=", 3600, "s", "both"),
    "M10": (">=", 40, "lines", "both"), "M10b": ("<=", 0, "rows", "both"),
    "M11": ("<=", 2.0, "ratio", "both"), "M11b": ("<=", 120, "lines", "both"), "M11c": ("<=", 0, "files", "both"),
    "M11b-bytes": ("<=", 18000, "bytes", "both"),
    "M12a": ("<=", 25, "rows", "beta"), "M12b": (">=", 80, "%", "beta"), "M12c": (">=", 1, "stories", "beta"),
    "M13": ("<=", 2, "runs", "both"), "M13b": ("<=", 1.0, "ratio", "both"),
    "M14": ("<=", 4, "runs", "both"), "M14b": ("<=", 0, "roles", "both"),
    "M15": ("<=", 20, "%", "both"), "M16": (">=", 2, "pieces", "both"),
    "M18a": ("<=", 12, "dirs", "both"), "M18b": ("<=", 20, "dirs", "both"), "M18c": ("<=", 120, "GB", "both"),
    "M18d": ("<=", 10, "branches", "both"),
    "M19a": ("<=", 0, "rows", "both"), "M19b": ("<=", 0, "rows", "both"), "M19c": ("<=", 0, "commits", "both"),
    "M20": ("<=", 20, "%", "lab"), "M21a": ("<=", 1, "rows", "both"), "M21b": ("<=", 2, "lines", "both"),
    "M22": ("<=", 2, "sessions", "both"), "M23": ("<=", 0, "files", "both"),
    "M24a": ("<=", 3, "commits", "both"), "M24b": ("<=", 1, "folders", "both"),
}
# extra tuning numbers the spec gives in prose (min sample sizes); written into the matching table
# M15 max_unknown: the share of runs with no RESULT line above which M15 FAILs (finding 21; a key the tests fix)
EXTRA = {"M01": {"min_game_lines": 200}, "M10": {"min_rows": 3}, "M15": {"max_unknown": 20}}


def sh(cwd, *args, env=None, check=True):
    e = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
    e.update(env or {})
    return subprocess.run(list(args), cwd=cwd, env=e, check=check, capture_output=True, text=True).stdout.strip()


def git(repo, *args, date=None):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"{date}T12:00:00+0000"
    return sh(repo, "git", *args, env=env)


class Repo:
    """A linear-history repo whose main is also refs/remotes/origin/main; commit() returns the sha."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.mkdir(parents=True)
        git(self.path, "init", "-q", "-b", "main")
        self.n = 0

    def commit(self, files, date, msg=None):
        """files: {path: int lines | str text | ("append", str)}; int n writes n lines `x<k>`."""
        for rel, body in files.items():
            p = self.path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(body, int):
                p.write_text("".join(f"x{i}\n" for i in range(body)))
            elif isinstance(body, tuple):
                with open(p, "a") as f:
                    f.write(body[1])
            else:
                p.write_text(body)
            git(self.path, "add", rel)
        self.n += 1
        git(self.path, "commit", "-q", "-m", msg or f"c{self.n}", date=date)
        sha = git(self.path, "rev-parse", "HEAD")
        git(self.path, "update-ref", "refs/remotes/origin/main", sha)
        return sha


def lines(n, prefix="line"):
    return "".join(f"{prefix} {i}\n" for i in range(n))


def thresholds_toml(approved="2026-10-26", override=None, drop=(), lanes=("VG-X",), prices=None):
    """override: {id: {key: value}}; drop: ids left out (unapproved test uses approved='').
    prices: {model id prefix: {input, cache_read, cache_write, output}} dollars per million tokens, written as
    `[prices."<model>"]` tables (finding 8; the shape the tests fix, the builder reads it)."""
    out = [f'phase = "lab"', "lanes = [" + ", ".join(f'"{x}"' for x in lanes) + "]", ""]
    for mid, (op, val, unit, phase) in TH.items():
        if mid in drop:
            continue
        row = {"id": mid, "gap": "G00", "draft": f"DRAFT-mm-{mid}", "value": val, "direction": op, "unit": unit,
               "approved": approved, "baseline": 0, "window": "week", "phase": phase}
        row.update(EXTRA.get(mid, {}))
        row.update((override or {}).get(mid, {}))
        out.append(f"[{mid}]")
        for k, v in row.items():
            out.append(f"{k} = {json.dumps(v)}")
        out.append("")
    for model, row in (prices or {}).items():
        out.append(f'[prices."{model}"]')
        out += [f"{k} = {json.dumps(v)}" for k, v in row.items()]
        out.append("")
    return "\n".join(out)


def pieces_toml(rows):
    out = []
    for r in rows:
        out += ["[[piece]]", f'id = "{r["id"]}"', "owns = [" + ", ".join(json.dumps(o) for o in r["owns"]) + "]",
                "acceptance = []", "depends_on = []"]
        st = r.get("status", "landed")
        out.append(f'status = "{st[1]}"' if isinstance(st, tuple) else f'status = {{ state = "{st}" }}')
        if r.get("contract"):
            out.append("contract = true")
        if r.get("story"):
            out.append(f'story = "{r["story"]}"')
        out.append("")
    return "\n".join(out)


LEDGER_HEAD = "# Push ledger\n\n| Time | Event | Detail |\n|---|---|---|\n"
OLD_LEDGER = ("| day1 | FINDING-old-untagged | before 2026-10-26: needs no found-by |\n"
              "| day1 | TD-old-untagged | before 2026-10-26: needs no ruler |\n")
GOOD_LEDGER_WEEK = [
    "| day40 | FINDING-good-1 found-by=test | a finding with its token |",
    "| day40 | TD-good-1 ruler=clerk | a test-defect ruled by the clerk |",
    "| day40 | TD-good-2 ruler=sonnet | a test-defect ruled by Sonnet |",
    "| day40 | DRAFT-good-1 | one named draft |",
]
# the README's Picture table as Westley's 2026-10-26 form has it (finding 32): every row is a picture awaiting him
README_HEAD = ("# Shots waiting on Westley\n\n| Picture | Story | What it shows | What to look for | Approve means / reject means |\n"
               "|---|---|---|---|---|\n")
README_TAIL = ("\n## Pages waiting on you\n\n| Page | What it asks |\n|---|---|\n| `page.md` | a question |\n")
GOOD_VERDICTS = ("# Verdicts\n\n| Picture | Verdict |\n|---|---|\n"
                 "| `VG-X-a` look piece | Approved: \"yes\" (Westley, 2026-10-22) |\n"
                 "| `VG-X-b` look piece | Approved: \"yes\" (Westley, 2026-10-22) |\n")


def default_pieces(n):
    rows = [{"id": f"P{i}", "owns": [f"csrc/sim_{i}.c", f"tests/csim/test_{i}.py"], "story": f"S-00{i + 1}"}
            for i in range(n)]
    rows += [{"id": "PS", "owns": ["scenes/x/x.tscn"], "status": "queued"},
             {"id": "VG-X-a", "owns": ["scenes/x/a.gd"], "status": "attached"},
             {"id": "VG-X-b", "owns": ["scenes/x/b.gd"], "status": "attached"}]
    return rows


def default_sdk(n):
    rows = []
    for i in range(n):
        for role, cost in (("spec", 1.0), ("tests", 1.0), ("build", 2.0), ("land", 1.0)):
            rows.append((D["wed"], f"P{i} {role}", f"P{i}", role, SONNET, 10, cost, "success"))
    return rows


def write_csv(path, cols, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def build_world(tmp, *, phase="lab", prod_commits=4, prod_lines=100, test_lines=100, docs_commits=4,
                docs_lines=50, claude_lines=100, extra_commits=(), old_branches=2, ledger_week=None,
                ledger_old=True, ledger=True, readme_open=3, readme_rows=(), verdicts_text=GOOD_VERDICTS,
                claude_text=None, base_files=None,
                pieces=None, gate_rows="auto", sdk_rows="auto", transcripts="auto", wt_active=3, wt_done=2,
                wt_extra_mb=0, stories_seen_in_week=1, beta_list=None, thresholds=None, decisions_text=""):
    """Returns dict(args=[...], repo=Path, shas=[...], files=...). Every option's default is the good week."""
    tmp = Path(tmp)
    r = Repo(tmp / "repo")
    base = r.commit({"CLAUDE.md": claude_text if claude_text is not None else lines(claude_lines), "README.md": "r\n",
                     **({LEDGER_REL: LEDGER_HEAD + (OLD_LEDGER if ledger_old else "")} if ledger else {}),
                     **(base_files or {}),
                     STORIES_REL: "# Stories\n\n| Story | Epic | Words | Status | Depth |\n|---|---|---|---|---|\n"
                                  "| S-001 | E-01 | \"a\" | Spec'd | x |\n| S-002 | E-01 | \"b\" | Spec'd | x |\n"
                                  "| S-003 | E-01 | \"c\" | Spec'd | x |\n"
                                  "| S-004 | E-01 | \"d\" | Spec'd | x |\n| S-005 | E-01 | \"e\" | Spec'd | x |\n",
                     DECISIONS_REL: "# Decisions\n" + decisions_text}, "2026-10-01")
    open_rows = "".join(f"| `open-{i}.png` | S-00{i} | what it shows | look | yes / no |\n" for i in range(readme_open))
    r.commit({README_REL: README_HEAD + open_rows + "".join(x + "\n" for x in readme_rows) + README_TAIL,
              **({VERDICTS_REL: verdicts_text} if verdicts_text else {})}, "2026-10-20")
    side = None
    if old_branches:  # unmerged push/* branches whose commit is old (committer date 2026-09-01)
        git(r.path, "checkout", "-q", "-b", "side")
        side = git(r.path, "commit", "-q", "--allow-empty", "-m", "stale", date="2026-09-01") or git(r.path, "rev-parse", "HEAD")
        side = git(r.path, "rev-parse", "HEAD")
        git(r.path, "checkout", "-q", "main")
        git(r.path, "branch", "-q", "-D", "side")
        for i in range(old_branches):
            git(r.path, "update-ref", f"refs/remotes/origin/push/stale-{i}", side)
    prev, shas = base, []
    for i in range(prod_commits):
        files = {f"csrc/sim_{i}.c": prod_lines, f"tests/csim/test_{i}.py": test_lines}
        sha = r.commit(files, D["tue"], f"P{i}")
        shas.append((i, prev, sha))
        prev = sha
    for i in range(docs_commits):
        prev = r.commit({f"docs/northstar/plans/notes_{i}.md": docs_lines}, D["thu"], f"docs {i}")
    for files, date in extra_commits:
        prev = r.commit(files, date)
    week_rows = list(GOOD_LEDGER_WEEK if ledger_week is None else ledger_week)
    if week_rows and ledger:
        r.commit({LEDGER_REL: ("append", "".join(x + "\n" for x in week_rows))}, D["fri"], "ledger")
    if stories_seen_in_week:
        r.commit({STORIES_REL: ("append", "".join(f"| S-9{k} | E-09 | \"w\" | Seen | x |\n" for k in range(stories_seen_in_week)))},
                 D["fri"], "seen")
    if beta_list is not None:
        r.commit({"docs/northstar/plans/beta_2026-11-01/stories.md": beta_list}, D["mon"], "beta list")
    prows = default_pieces(prod_commits) if pieces is None else pieces
    pp = r.path / PIECES_REL
    r.commit({PIECES_REL: pieces_toml(prows) if not isinstance(prows, str) else prows}, D["fri"], "pieces")
    # gate_runs
    if gate_rows == "auto":
        gate_rows = [(D["tue"], f"P{i}", f"push/p{i}", b, c, 600, 1800, 0, "", "", prod_lines, test_lines, 0, 20)
                     for i, b, c in shas]
    gp = tmp / "gate_runs.csv"
    write_csv(gp, GATE_COLS, gate_rows)
    sp = tmp / "sdk_runs.csv"
    write_csv(sp, SDK_COLS, default_sdk(prod_commits) if sdk_rows == "auto" else sdk_rows)
    # transcripts (<slug dir>/<session>.jsonl and <session>/subagents/agent-*.jsonl|.meta.json)
    td = tmp / "transcripts"
    td.mkdir()
    if transcripts == "auto":
        transcripts = default_transcripts()
    write_transcripts(td, transcripts)
    # wt tree
    wt = tmp / "wt"
    wt.mkdir()
    for i in range(wt_active):
        (wt / f"a{i}").mkdir()
        (wt / f"a{i}" / ".wt-state").write_text(f"active {D['wed']} chat purpose words\n")
    for i in range(wt_done):
        (wt / f"d{i}").mkdir()
        (wt / f"d{i}" / ".wt-state").write_text(f"finished {D['mon']} chat purpose words\n")
        (wt / f"d{i}" / ".wt-done").write_text(f"{D['mon']} push/d{i} {base}\n")
    if wt_extra_mb:
        (wt / "a0" / "big.bin").write_bytes(b"\0" * (wt_extra_mb * 1024 * 1024))
    tp = tmp / "thresholds.toml"
    tp.write_text(thresholds if thresholds is not None else thresholds_toml())
    args = ["--week", WEEK, "--phase", phase, "--repo", str(r.path), "--ledger", str(r.path / LEDGER_REL),
            "--pieces", str(pp), "--gate-runs", str(gp), "--sdk-runs", str(sp), "--transcripts", str(td),
            "--wt", str(wt), "--thresholds", str(tp)]
    return {"args": args, "repo": r.path, "shas": shas, "tmp": tmp, "transcripts": td, "wt": wt}


# ---------------------------------------------------------------- transcripts
def entry(model, ts, tools=(), ctx=60000, sidechain=False, text="ok"):
    content = [{"type": "tool_use", "id": f"t{i}", "name": n, "input": inp} for i, (n, inp) in enumerate(tools)]
    if not content:
        content = [{"type": "text", "text": text}]
    return {"type": "assistant", "isSidechain": sidechain, "cwd": str(Path.home() / "Projects/om-push/wt/x"),
            "timestamp": ts, "message": {"model": model, "usage": {"input_tokens": 1000,
            "cache_read_input_tokens": ctx - 1500, "cache_creation_input_tokens": 500, "output_tokens": 200},
            "content": content}}


def clean(model, ts, ctx=60000):
    return entry(model, ts, ctx=ctx, tools=[
        ("Bash", {"command": "git show origin/main:CLAUDE.md"}),
        ("Agent", {"subagent_type": "engineer", "model": "sonnet", "prompt": "x"})])


def ts(hour, minute):
    return f"{D['wed']}T{hour:02d}:{minute:02d}:00.000Z"


def default_transcripts():
    """Two top-level sessions in one hour (an Architect on Fable, a Dispatcher on Sonnet), all clean, plus a
    sub-agent transcript on Fable in the same hour that must NOT count as a coordinator session (M22)."""
    return {
        "sess-arch.jsonl": [clean(FABLE, ts(10, m)) for m in range(5)],
        "sess-disp.jsonl": [clean(SONNET, ts(10, m)) for m in range(5)],
        "sess-disp/subagents/agent-sub1.jsonl": [entry(FABLE, ts(10, 3), sidechain=True, text="RESULT success")],
        "sess-disp/subagents/agent-sub1.meta.json": {"agentType": "engineer", "description": "P0 build"},
    }


def write_transcripts(td, spec):
    """Keys are written under <td>/<SLUG>/ (the default --project folder, finding 5); a key starting with `!` is
    written relative to the transcripts root, to put a session in another project's folder."""
    for rel, body in spec.items():
        p = Path(td) / (rel[1:] if rel.startswith("!") else f"{SLUG}/{rel}")
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, dict):
            p.write_text(json.dumps(body))
        else:
            p.write_text("\n".join(json.dumps(e) for e in body) + "\n")
