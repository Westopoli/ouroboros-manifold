# spec: docs/northstar/proving_ground/PX-19-prefetch-resident-model.md
"""PX-19 measurement tool: is there CPU-side prep work a prefetching dispatcher
could do while the GPU builds the previous card, and how much of the observed
outcome-to-next-attempt gap would that prep, plus a resident (never-unloaded)
model, actually close?

Three independent measurements, each a subcommand:

  gaps   -- parse ~/Projects/agora/runs/cron.log for the wall-clock gap between
            one dispatch->build/burn tick and the next. cron.log carries only
            [HH:MM:SS] (no date), so gaps are computed pairwise with a same-day
            rollover assumption (any negative delta is treated as crossing one
            midnight); see PX-19 write-up for why this is safe for adjacent-line
            gaps even though the log spans many days.

  loads  -- scan a directory tree for resp_*.json / state.json files carrying
            an Ollama `load_duration` field (nanoseconds) and report the
            distinct values found (deduped by content hash: the only files
            found under ~/Projects/agora/runs turned out to be 672 copies of
            6 distinct files, all static evidence checked into this repo's
            docs/northstar/research/harness_defects_2026-09-17/evidence/tokens/,
            not live per-card telemetry -- see write-up).

  prep   -- given a real parked card (queue/parked/*.md.hold) and a scratch
            git worktree, time each CPU-only step build.py performs before its
            first model call: `git worktree add`, `make -s libouroboros.so`,
            the baseline pytest of the card's first acceptance command,
            card_lint.py, card_slice.py --write, and prompt assembly (a plain
            char-count/4 estimate -- build.py's own OllamaReply
            (~/Projects/agora/scripts/cascade_types.py:982-990) has no
            pre-call token counter at all, only post-call prompt_eval_count
            from Ollama's reply, so there is nothing in build.py to "reuse";
            this is a labelled approximation, not a reproduction of a real
            counter).

No network calls, no Ollama, no agy, no writes under ~/Projects/agora.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

DISPATCH_RE = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\] dispatch -> (build|burn)\b")

# An outcome line (DONE/INCOMPLETE/SPEC-INVALID/UNSATISFIABLE) that names its own run
# directory carries a true YYYYMMDD -- cron.log's own [HH:MM:SS] lines never do. Used
# as a dating anchor so a multi-day idle stretch between two build/burn ticks (real,
# and common: the log covers probe days with no continuous dispatcher) is not silently
# folded into a same-day rollover.
ANCHOR_RE = re.compile(r"report at .*-(\d{8})-\d{4}(?:-\d+)?/report\.md")


def parse_dispatch_ticks(cron_log_text: str) -> list[tuple[int, dt.datetime]]:
    """Every `dispatch -> build` / `dispatch -> burn` line, as (line_no, datetime), in
    file order. These are the CPU-slot ticks that start a queue-task attempt --
    verified against the brief's own two worked examples (DONE at 21:50:30 -> next
    dispatch->build at 21:51:33 = 63s; DONE at 14:40:31 -> 14:42:42 = 131s, then
    14:42:42 -> 14:43:44 = 62s -- all three reproduced from the live log by this
    parser during PX-19).

    Dating: cron.log has no date on any line. Absolute dates come from the run
    directory name embedded in the outcome line each build/burn tick produces
    (ANCHOR_RE); a tick without its own anchor (crash before any report line) falls
    back to same-day rollover from the previous tick, and self-corrects at the next
    anchored tick. A tick's own gap gets the wrong duration only in the (unobserved
    here) case of a run of *consecutive* un-anchored ticks spanning a real midnight --
    see the PX-19 write-up for how many ticks this affects."""
    lines = cron_log_text.splitlines()
    anchors: dict[int, str] = {}
    for i, line in enumerate(lines, start=1):
        m = ANCHOR_RE.search(line)
        if m:
            anchors[i] = m.group(1)
    anchor_items = sorted(anchors.items())

    raw = []
    for i, line in enumerate(lines, start=1):
        m = DISPATCH_RE.match(line)
        if m:
            raw.append((i, int(m.group(1)), int(m.group(2)), int(m.group(3))))

    ticks: list[tuple[int, dt.datetime]] = []
    current_dt: dt.datetime | None = None
    ai = 0
    for idx, (line_no, h, mnt, s) in enumerate(raw):
        sec = h * 3600 + mnt * 60 + s
        next_line_no = raw[idx + 1][0] if idx + 1 < len(raw) else None
        while ai < len(anchor_items) and anchor_items[ai][0] < line_no:
            ai += 1
        anchor_date = None
        if ai < len(anchor_items) and (next_line_no is None or anchor_items[ai][0] < next_line_no):
            anchor_date = anchor_items[ai][1]

        if anchor_date is not None:
            y, mo, da = int(anchor_date[:4]), int(anchor_date[4:6]), int(anchor_date[6:8])
            current_dt = dt.datetime(y, mo, da) + dt.timedelta(seconds=sec)
        elif current_dt is None:
            current_dt = dt.datetime(2020, 1, 1) + dt.timedelta(seconds=sec)
        else:
            candidate = dt.datetime(current_dt.year, current_dt.month, current_dt.day) + dt.timedelta(seconds=sec)
            if candidate < current_dt:
                candidate += dt.timedelta(days=1)
            current_dt = candidate
        ticks.append((line_no, current_dt))
    return ticks


def gap_stats(ticks: list[tuple[int, dt.datetime]]) -> dict:
    """Consecutive-tick gaps in seconds, using the dated timestamps from
    parse_dispatch_ticks (anchor-corrected, so a real multi-day idle stretch reports
    as a multi-day gap instead of wrapping to a small number)."""
    gaps = []
    pairs = []
    for (ln_a, t_a), (ln_b, t_b) in zip(ticks, ticks[1:]):
        delta = (t_b - t_a).total_seconds()
        gaps.append(delta)
        pairs.append((ln_a, ln_b, delta))
    if not gaps:
        return {"count": 0, "median": None, "p90": None, "max": None, "over_300s": 0, "pairs": []}
    sorted_gaps = sorted(gaps)
    p90_idx = min(len(sorted_gaps) - 1, int(round(0.9 * (len(sorted_gaps) - 1))))
    return {
        "count": len(gaps),
        "median": statistics.median(gaps),
        "p90": sorted_gaps[p90_idx],
        "max": max(gaps),
        "over_300s": sum(1 for g in gaps if g > 300),
        "pairs": pairs,
    }


def cmd_gaps(args: argparse.Namespace) -> int:
    text = Path(args.cron_log).read_text(errors="replace")
    ticks = parse_dispatch_ticks(text)
    stats = gap_stats(ticks)
    out = {
        "cron_log": str(args.cron_log),
        "dispatch_tick_count": len(ticks),
        "gap_count": stats["count"],
        "median_s": stats["median"],
        "p90_s": stats["p90"],
        "max_s": stats["max"],
        "over_300s_count": stats["over_300s"],
    }
    if args.show_max and stats["pairs"]:
        worst = sorted(stats["pairs"], key=lambda p: p[2], reverse=True)[: args.show_max]
        out["worst_pairs"] = [{"from_line": a, "to_line": b, "gap_s": g} for a, b, g in worst]
    print(json.dumps(out, indent=2))
    return 0


# --- loads ----------------------------------------------------------------------------

def find_load_durations(root: Path) -> list[dict]:
    """resp_*.json / state.json files under root carrying a top-level `load_duration`
    (nanoseconds), deduped by sha256 of file content -- a single evidence file
    checked into the repo shows up once per worktree snapshot it happens to be
    inside, which is not the same as one measurement per card."""
    seen_hashes: dict[str, dict] = {}
    for pattern in ("resp_*.json", "state.json"):
        for p in root.rglob(pattern):
            try:
                raw = p.read_bytes()
            except OSError:
                continue
            digest = hashlib.sha256(raw).hexdigest()
            if digest in seen_hashes:
                seen_hashes[digest]["paths"].append(str(p))
                continue
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(data, dict) or "load_duration" not in data:
                continue
            seen_hashes[digest] = {
                "sha256": digest,
                "load_duration_ns": data["load_duration"],
                "load_duration_s": data["load_duration"] / 1e9,
                "model": data.get("model"),
                "prompt_eval_count": data.get("prompt_eval_count"),
                "paths": [str(p)],
                "occurrences": 1,
            }
    for v in seen_hashes.values():
        v["occurrences"] = len(v["paths"])
    return sorted(seen_hashes.values(), key=lambda v: v["load_duration_ns"])


def cmd_loads(args: argparse.Namespace) -> int:
    root = Path(args.root)
    found = find_load_durations(root)
    total_occurrences = sum(v["occurrences"] for v in found)
    values_s = [v["load_duration_s"] for v in found]
    trimmed = []
    for v in found:
        v2 = dict(v)
        v2["example_paths"] = v2.pop("paths")[: args.max_paths]
        trimmed.append(v2)
    out = {
        "root": str(root),
        "distinct_files_with_load_duration": len(found),
        "total_occurrences_on_disk": total_occurrences,
        "median_s": statistics.median(values_s) if values_s else None,
        "min_s": min(values_s) if values_s else None,
        "max_s": max(values_s) if values_s else None,
        "values": trimmed,
    }
    print(json.dumps(out, indent=2))
    return 0


# --- prep -------------------------------------------------------------------------------

CARD_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
BRIEF_SECTION_RE = re.compile(r"^## Brief for DeepSeek[ \t]*\n(.*?)(?=^## |\Z)", re.S | re.M)
HEADER_SLICE_RE = re.compile(r"^## Header slice[ \t]*\n(.*?)(?=^## |\Z)", re.S | re.M)


def parse_card(card_path: Path) -> tuple[dict, str]:
    import yaml

    m = CARD_FRONTMATTER_RE.match(card_path.read_text())
    if not m:
        raise ValueError(f"{card_path}: no --- frontmatter block")
    spec = yaml.safe_load(m.group(1)) or {}
    return spec, m.group(2)


def assemble_worker_prompt(spec: dict, body: str, worktree: Path) -> str:
    """Reproduces the string build.py's `_worker_user_c` assembles for the FIRST
    candidate of a C card whose brief lives inline (`## Brief for DeepSeek`, no
    driver call -- ~/Projects/agora/scripts/build.py:833), no previous attempt, no
    advisor hint. Logic mirrored from build.py:316-332 (_worker_user_c),
    build.py:786-794 (header_text/symbols selection), build.py:811-817
    (extra_context_files), optimize.py:94-96 (brief_section). Not imported from
    build.py directly, to avoid pulling in agy_client/deepseek_client/network-capable
    module-level code for a pure string-assembly measurement."""
    names = [s.strip() for s in str(spec["snippet_symbol"]).split(",") if s.strip()]
    instruction = (BRIEF_SECTION_RE.search(body).group(1).strip()
                   if BRIEF_SECTION_RE.search(body) else "")
    skeleton_text = (worktree / spec["snippet_file"]).read_text()

    slice_m = HEADER_SLICE_RE.search(body)
    if slice_m and slice_m.group(1).strip():
        header_text = slice_m.group(1).strip()
    else:
        hp = spec.get("header_file")
        header_text = (worktree / hp).read_text() if hp and (worktree / hp).exists() else ""

    extra_context = ""
    for rel in (r.strip() for r in str(spec.get("extra_context_files") or "").split(",") if r.strip()):
        p = worktree / rel
        if p.exists():
            extra_context += f"# {rel}\n```c\n{p.read_text()}```\n\n"

    parts = [
        f"SCOPE (declared in the header, use only these): {', '.join(names)}",
        f"INSTRUCTION:\n{instruction}",
        f"HEADER (read-only, do not change):\n```c\n{header_text}```",
    ]
    if extra_context:
        parts.append("EXTRA CONTEXT (read-only; private layout and helpers not in the header -- "
                     "use these member and type names exactly, do not invent them):\n" + extra_context)
    parts.append(f"WHOLE FILE (rewrite only the stubbed function(s) {', '.join(names)}):\n```c\n{skeleton_text}```")
    parts.append(f"OUTPUT: exactly one ```snippet block containing the rewritten function(s) {', '.join(names)}; no other text.")
    return "\n\n".join(parts)


def estimate_tokens(text: str) -> int:
    """chars/4 heuristic. build.py has no pre-call tokenizer to reuse (see module
    docstring); this is a labelled approximation only."""
    return len(text) // 4


def timed(fn):
    t0 = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - t0


def cmd_prep(args: argparse.Namespace) -> int:
    card_path = Path(args.card)
    spec, body = parse_card(card_path)
    repo = Path(args.repo).expanduser().resolve()
    worktree = Path(args.worktree).expanduser()
    steps = {}

    def run(cmd, cwd=None, timeout=600):
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)

    if worktree.exists():
        print(f"refusing to reuse existing worktree path: {worktree}", file=sys.stderr)
        return 2

    r, dt = timed(lambda: run(["git", "worktree", "add", "--detach", str(worktree), args.commit], cwd=repo))
    steps["git_worktree_add"] = {"seconds": dt, "returncode": r.returncode}
    if r.returncode != 0:
        print(r.stdout + r.stderr, file=sys.stderr)
        return 2

    try:
        r, dt = timed(lambda: run(["make", "-s", "libouroboros.so"], cwd=worktree))
        steps["make_libouroboros"] = {"seconds": dt, "returncode": r.returncode}

        first_check = spec["acceptance"][0].split()
        r, dt = timed(lambda: run(first_check, cwd=worktree, timeout=300))
        steps["baseline_pytest"] = {"seconds": dt, "returncode": r.returncode,
                                     "argv": first_check}

        scratch_card = worktree.parent / f"_cardcopy_{card_path.name}"
        scratch_card.write_text(card_path.read_text())

        lint_script = repo / "scripts" / "specfactory" / "card_lint.py"
        if lint_script.exists():
            r, dt = timed(lambda: run(
                [sys.executable, str(lint_script), str(scratch_card), "--project", str(worktree), "--json"]))
            steps["card_lint"] = {"seconds": dt, "returncode": r.returncode}
        else:
            steps["card_lint"] = {"seconds": 0.0, "returncode": None, "note": "card_lint.py not found"}

        slice_script = repo / "scripts" / "specfactory" / "card_slice.py"
        if slice_script.exists():
            r, dt = timed(lambda: run(
                [sys.executable, str(slice_script), str(scratch_card), "--project", str(worktree), "--write"]))
            steps["card_slice_write"] = {"seconds": dt, "returncode": r.returncode}
        else:
            steps["card_slice_write"] = {"seconds": 0.0, "returncode": None, "note": "card_slice.py not found"}

        def assemble():
            return assemble_worker_prompt(spec, body, worktree)

        prompt, dt = timed(assemble)
        steps["prompt_assembly"] = {"seconds": dt, "returncode": 0,
                                     "prompt_chars": len(prompt),
                                     "estimated_tokens": estimate_tokens(prompt)}
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo,
                        capture_output=True, text=True)
        subprocess.run(["git", "worktree", "prune"], cwd=repo, capture_output=True, text=True)

    total = sum(s["seconds"] for s in steps.values())
    out = {"card": str(card_path), "repo": str(repo), "steps": steps, "total_prep_seconds": total}
    print(json.dumps(out, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_gaps = sub.add_parser("gaps", help="cron.log dispatch-tick gap distribution")
    p_gaps.add_argument("cron_log")
    p_gaps.add_argument("--show-max", type=int, default=0)
    p_gaps.set_defaults(func=cmd_gaps)

    p_loads = sub.add_parser("loads", help="load_duration values under a directory tree")
    p_loads.add_argument("root")
    p_loads.add_argument("--max-paths", type=int, default=3,
                          help="example paths to print per distinct file (occurrences count is always exact)")
    p_loads.set_defaults(func=cmd_loads)

    p_prep = sub.add_parser("prep", help="time CPU prep steps for one card in a scratch worktree")
    p_prep.add_argument("card")
    p_prep.add_argument("--repo", required=True)
    p_prep.add_argument("--worktree", required=True)
    p_prep.add_argument("--commit", default="HEAD")
    p_prep.set_defaults(func=cmd_prep)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
