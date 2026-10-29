#!/usr/bin/env python3
"""coverage_report.py <out_dir> <repo>: HARNESS-coverage. Turns the gcov JSON that coverage_run.sh left in
<out_dir>/A (csim run) and <out_dir>/B (pipe run) into functions.csv and summary.json in <out_dir>.

Release and debug builds in one directory are summed per (file, function) and per (file, line). `reachable` comes
from reach_lint's call graph (the tick, the time jump and the pipe dispatch handlers as roots); a function defined
after `__attribute__((weak))` is a weak_stub and leaves the zero counts and the line totals.
See also: coverage_run.sh, status_check.py check_coverage.
"""
import csv
import datetime
import functools
import gzip
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import reach_lint

COLS = ["file", "function", "lines", "exec_A", "exec_B", "reachable", "weak_stub"]


def read_dir(d):
    """({(file, function): execution_count}, {(file, line): (function, count)}) summed over every *.gcov.json.gz."""
    execs, lines = defaultdict(int), {}
    for gz in sorted(d.glob("*.gcov.json.gz")):
        with gzip.open(gz, "rt") as fh:
            data = json.load(fh)
        for f in data["files"]:
            for fn in f["functions"]:
                execs[(f["file"], fn["name"])] += fn["execution_count"]
            for ln in f["lines"]:
                key = (f["file"], ln["line_number"])
                lines[key] = (ln.get("function_name", ""), lines.get(key, ("", 0))[1] + ln["count"])
    return execs, lines


@functools.lru_cache(maxsize=None)
def source_text(path):
    return path.read_text(errors="replace") if path.is_file() else ""


def is_weak(repo, file, name):
    return bool(re.search(r"__attribute__\(\(weak\)\)[\w\s\*]*?\b" + re.escape(name) + r"\s*\(",
                          source_text(repo / file)))


def main(argv):
    out, repo = Path(argv[0]), Path(argv[1])
    (ea, la), (eb, lb) = read_dir(out / "A"), read_dir(out / "B")
    csrc = repo / "csrc"
    graph = reach_lint.build_callgraph(csrc)
    pipe_c = csrc / "pipe" / "om_pipe.c"
    names = reach_lint.dispatch_call_names(pipe_c.read_text()) if pipe_c.is_file() else set()
    reach = reach_lint.reachable_from(graph, reach_lint.resolve_roots(graph, names, "csrc/pipe/om_pipe.c"))

    owner = {k: v[0] for k, v in {**lb, **la}.items()}  # (file, line) -> function name
    nlines = defaultdict(int)
    for (f, _), fn in owner.items():
        nlines[(f, fn)] += 1
    rows = []
    for f, fn in sorted(set(ea) | set(eb)):
        rows.append({"file": f, "function": fn, "lines": nlines[(f, fn)], "exec_A": ea.get((f, fn), 0),
                     "exec_B": eb.get((f, fn), 0), "reachable": fn in reach or f"{f}:{fn}" in reach,
                     "weak_stub": is_weak(repo, f, fn)})
    with open(out / "functions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    weak = {(r["file"], r["function"]) for r in rows if r["weak_stub"]}
    keys = [k for k, fn in owner.items() if (k[0], fn) not in weak]

    def pct(lines):
        return round(100 * sum(1 for k in keys if lines.get(k, ("", 0))[1] > 0) / len(keys), 1) if keys else 0.0

    live = [r for r in rows if r["reachable"] and not r["weak_stub"]]
    summary = {
        "sha": subprocess.run(["git", "-C", str(repo), "rev-parse", "--short=12", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip(),
        "date": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        "zero_a_reachable": sum(1 for r in live if r["exec_A"] == 0),
        "zero_b_reachable": sum(1 for r in live if r["exec_B"] == 0),
        "lines_pct_a": pct(la), "lines_pct_b": pct(lb),
        "exit_a": int((out / "exit_a").read_text()), "exit_b": int((out / "exit_b").read_text()),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
