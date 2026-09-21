#!/usr/bin/env python3
"""PX-16 prototype: graph-scheduler simulation for the Agora release chain.

Tests the "Pipelining (the drive-thru rule)" claim in
docs/northstar/PLAN.md: if RELEASE_CHAIN were a dependency graph with
escalate-and-continue instead of a serial list, most of the idle time
measured on 2026-09-18/19 (research/factory/A9-throughput-timeline.md)
disappears.

Two independent pieces, both real-data driven, neither one guessed:

  1. Dependency graph (`build_dag`). A card's acceptance tests reach a set
     of om_* symbols (card_lint's own static collector, plus tick_closure's
     tick-stage hook expansion, both reused unmodified). Card B depends on
     card A when a symbol B reaches is one A's own `snippet_symbol` claims
     and that symbol is *presently a stub* in the real csrc/ (i.e. nothing
     before A has implemented it yet -- a symbol already real, whoever
     "owns" it on paper, is not a live dependency). Gate cards (`kind:
     gate`) instead depend on every non-gate card in the same slice whose
     test naming shares their story number.

  2. Replay (`simulate`). A card's real run history in the window (one
     `Cycle` per Agora run directory: wall minutes from candidates.jsonl,
     terminal outcome from the run directory's own marker file) is fed to a
     single-GPU-slot discrete-event scheduler under four policies (S0-S3,
     see the module docstring on `simulate`).

The real-repo I/O (RELEASE_CHAIN, queue/*.md, csrc/*.c, agora/runs/*) lives
in the CLI functions at the bottom and is exercised by hand against the two
real repos to produce PX-16's numbers -- same convention as PX-08's
tick_closure.py: the pytest suite proves the mechanism on synthetic
fixtures, not the live repos' current state.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from green_check import parse_card  # noqa: E402
from card_lint import (  # noqa: E402
    _split_list,
    collect_acceptance_symbols,
    find_function_span,
    is_stub_body,
)
import tick_closure  # noqa: E402

AGORA = Path("/home/westopoli/Projects/agora")
QUEUE = AGORA / "queue"
PARKED = QUEUE / "parked"
RUNS = AGORA / "runs"

TERMINAL_OUTCOMES = {"UNSATISFIABLE", "SPEC-INVALID", "GATE-FAILED"}
MAX_TASK_RUNS = 10  # agora/scripts/next.py::MAX_TASK_RUNS


# ------------------------------------------------------------------
# 1. Dependency graph
# ------------------------------------------------------------------

def is_gate(card: dict) -> bool:
    return card.get("kind") == "gate"


def story_number_of(card: dict) -> str | None:
    """S-number a card belongs to: from the gate's own "story S-0NN gate"
    goal text, or from a regular card's `test_E0#_S0NN_...py` test_file."""
    if is_gate(card):
        m = re.search(r"S-(\d{3})", card.get("goal", "") or "")
    else:
        m = re.search(r"S(\d{3})", card.get("test_file", "") or "")
    return m.group(1) if m else None


def build_owner_map(card_ids: list[str], cards: dict[str, dict]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """symbol -> first-claiming card id in `card_ids` order (the tiebreak is
    only used when two cards genuinely claim the same symbol, e.g.
    205a/205b both extending `om_tick_collisions` in the same file -- that
    pairing is real and is reported back in `duplicate_owners`, not hidden
    by the tiebreak)."""
    owner: dict[str, str] = {}
    claimants: dict[str, list[str]] = {}
    for cid in card_ids:
        card = cards.get(cid)
        if not card:
            continue
        for sym in _split_list(card.get("snippet_symbol", "")):
            claimants.setdefault(sym, []).append(cid)
            owner.setdefault(sym, cid)
    duplicates = {s: c for s, c in claimants.items() if len(c) > 1}
    return owner, duplicates


def find_symbol_stub(csrc_texts: dict[str, str], symbol: str) -> bool:
    """True if `symbol` is presently defined as a STUB body somewhere in
    `csrc_texts`. False both when it is real code and when it is not
    defined anywhere (an undefined symbol is card_lint's ABI_GAP, not this
    module's problem)."""
    for text in csrc_texts.values():
        span = find_function_span(text, symbol)
        if span:
            return is_stub_body(text[span[0]:span[1]])
    return False


def card_symbol_closure(card: dict, project: Path, csrc_texts: dict[str, str], hooks: list[str]) -> set[str]:
    """Symbols a card's acceptance reaches directly, plus the tick-stage
    hooks its own om_tick_*/om_pending_* readers depend on (PX-08's
    stub_hooks_needed mechanism, reused rather than re-derived)."""
    direct, _bad = collect_acceptance_symbols(card, project)
    expanded = tick_closure.expand_closure(direct, hooks)
    candidate_hooks = expanded & set(hooks)
    needed = tick_closure.relevant_hooks(direct, hooks, csrc_texts) & candidate_hooks
    return direct | needed


def build_dag(card_ids: list[str], cards: dict[str, dict], project: Path,
              csrc_texts: dict[str, str], exclude_from_gates: frozenset = frozenset()) -> dict:
    """DAG over `card_ids`. `card_ids`' own order is used only to break ties
    when two cards claim the same symbol -- it is never treated as an
    implied dependency itself (that's exactly the "not list order" the
    experiment is about). `exclude_from_gates` keeps a card (a
    since-retired one kept around only so its own real run history can be
    replayed, e.g. 204b1/207 -- see chain_sim.py's REPLAY_PHANTOMS) from
    being counted as a gate's story dependency: RELEASE_CHAIN's own gate
    cards never actually waited on a retired card, since retiring it is
    exactly what unblocked the gate in reality."""
    owner, dup_owners = build_owner_map(card_ids, cards)
    hooks = tick_closure.hooks_in_order(csrc_texts.get("sim.c", ""))

    story_cards: dict[str, list[str]] = {}
    for cid in card_ids:
        if cid in exclude_from_gates:
            continue
        card = cards.get(cid)
        if card is None or is_gate(card):
            continue
        sn = story_number_of(card)
        if sn:
            story_cards.setdefault(sn, []).append(cid)

    edges: dict[tuple[str, str], set[str]] = {}
    for cid in card_ids:
        card = cards.get(cid)
        if card is None:
            continue
        if is_gate(card):
            sn = story_number_of(card)
            for dep in story_cards.get(sn, []):
                if dep != cid:
                    edges.setdefault((dep, cid), set()).add(f"gate:S-{sn}")
            continue
        for sym in card_symbol_closure(card, project, csrc_texts, hooks):
            src = owner.get(sym)
            if not src or src == cid or src not in card_ids:
                continue
            if not find_symbol_stub(csrc_texts, sym):
                continue  # already real code -- not a live dependency
            edges.setdefault((src, cid), set()).add(sym)

    edge_list = [{"from": f, "to": t, "via": sorted(v)} for (f, t), v in sorted(edges.items())]
    return {"nodes": list(card_ids), "edges": edge_list, "duplicate_owners": dup_owners}


def edge_stats(dag: dict) -> dict:
    n = len(dag["nodes"])
    return {
        "nodes": n,
        "real_edges": len(dag["edges"]),
        "serial_implied_edges": max(n - 1, 0),
    }


def edge_pairs(dag: dict) -> list[tuple[str, str]]:
    return [(e["from"], e["to"]) for e in dag["edges"]]


# ------------------------------------------------------------------
# Plateau diagnosis (PX-08 H2, K=3)
# ------------------------------------------------------------------

def plateau_cutoff(candidates: list[dict], k: int = 3) -> tuple[int, float]:
    """(n_consumed, wall_s_consumed) scanning `candidates` in order (each
    {"failing": iterable of ids, "wall_s": float}). The first run of `k`
    consecutive candidates sharing the same *non-empty* failing set ends
    the scan there -- PX-08's plateau diagnosis. No such run: every
    candidate is consumed (n_consumed == len(candidates))."""
    total = 0.0
    run_val: frozenset | None = None
    run_len = 0
    for i, c in enumerate(candidates):
        total += c["wall_s"]
        failing = frozenset(c["failing"])
        if failing and failing == run_val:
            run_len += 1
        else:
            run_val = failing
            run_len = 1 if failing else 0
        if failing and run_len >= k:
            return i + 1, total
    return len(candidates), total


# ------------------------------------------------------------------
# 2. Replay
# ------------------------------------------------------------------

@dataclass
class Cycle:
    """One real Agora run directory (one dispatcher cycle): one or more
    worker candidates against a single card, ending in a single terminal
    outcome. `gap_to_next_min` is the real wall-clock minutes between this
    cycle ending and the *next real cycle for this same task* starting --
    used as the "fix landed" timestamp when this cycle ends terminal or
    caps out (see `simulate`); None if there is no later real cycle for
    this task in the window."""
    dur_min: float
    outcome: str
    candidates: list[dict] | None = None
    gap_to_next_min: float | None = None


def simulate(nodes: list[str], edges: list[tuple[str, str]],
             cycles_by_task: dict[str, list[Cycle]], priority_of,
             targets: list[str], *, done_at_start=(), use_plateau: bool = False,
             fix_delay_min: float | None = None, cap: int = MAX_TASK_RUNS,
             plateau_k: int = 3, retire_on_block: frozenset = frozenset()) -> dict:
    """Single-GPU-slot discrete-event replay.

    S0 (serial-as-it-ran) is NOT this function -- it is the literal
    historical timeline, reproduced by replaying `cycles_by_task` in real
    chronological order regardless of readiness (see `s0_timeline`).

    S1/S2/S3 all go through here:
      S1: use_plateau=False, fix_delay_min=None (real fix timestamp)
      S2: use_plateau=True,  fix_delay_min=None
      S3: use_plateau=True,  fix_delay_min=<15|30|60>

    Escalate-and-continue: whenever the GPU is idle, it runs the
    highest-priority node (`priority_of`, lower sorts first) that is READY
    -- deps DONE, not itself DONE, not currently blocked, and has a real
    historical cycle left to replay. A node's cycle outcome:
      DONE                          -> node DONE, dependents may unblock
      UNSATISFIABLE/SPEC-INVALID/
      GATE-FAILED, or the node has
      now run `cap` cycles with no
      DONE                          -> node BLOCKED. If in `retire_on_block`
                                        (the historically-retired 204b1/207
                                        phantoms, which nothing here depends
                                        on) it is dropped for good. Else it
                                        re-enters the ready pool after
                                        `fix_delay_min` minutes (S3) or the
                                        real `gap_to_next_min` (S1/S2) --
                                        or never, if there is no later real
                                        cycle in the window.
      INCOMPLETE, under cap         -> stays ready; the scheduler retries
                                        the SAME node's next real cycle
                                        immediately if it is still the
                                        highest-priority ready node (this is
                                        today's real behaviour too: a
                                        non-terminal retry needs no human).

    `use_plateau` shortens (never lengthens) a cycle's own duration via
    `plateau_cutoff` on its `candidates`; a plateau that cuts off before the
    cycle's real last (passing) candidate turns a real DONE into a modelled
    INCOMPLETE for that cycle -- the false-stop risk PX-08 already found at
    every K, inherited here rather than re-derived.
    """
    status = {n: ("DONE" if n in done_at_start else "PENDING") for n in nodes}
    cursor = {n: 0 for n in nodes}
    run_count = {n: 0 for n in nodes}
    blocked_until: dict[str, float | None] = {n: None for n in nodes}
    retired: set[str] = set()
    time = 0.0
    building = 0.0
    idle = 0.0
    events: list[tuple] = []

    def deps_done(n: str) -> bool:
        return all(status[f] == "DONE" for (f, t) in edges if t == n)

    def is_ready(n: str, t: float) -> bool:
        if n in retired or status[n] == "DONE":
            return False
        if blocked_until[n] is not None and t < blocked_until[n]:
            return False
        if cursor[n] >= len(cycles_by_task.get(n, [])):
            return False
        return deps_done(n)

    guard = 0
    while not all(status[tgt] == "DONE" for tgt in targets):
        guard += 1
        if guard > 200_000:
            raise RuntimeError("simulate: exceeded iteration guard -- likely a stuck loop")
        ready_now = [n for n in nodes if is_ready(n, time)]
        if not ready_now:
            future = [
                blocked_until[n] for n in nodes
                if n not in retired and status[n] != "DONE"
                and blocked_until[n] not in (None, float("inf"))
                and blocked_until[n] > time
                and cursor[n] < len(cycles_by_task.get(n, []))
            ]
            if not future:
                break  # nothing left can ever become ready in this window
            nxt = min(future)
            events.append(("IDLE", time, nxt))
            idle += nxt - time
            time = nxt
            continue

        node = min(ready_now, key=priority_of)
        cyc = cycles_by_task[node][cursor[node]]
        cursor[node] += 1
        run_count[node] += 1
        dur = cyc.dur_min
        outcome = cyc.outcome
        truncated = False
        if use_plateau and cyc.candidates:
            idx, wall_s = plateau_cutoff(cyc.candidates, k=plateau_k)
            if idx < len(cyc.candidates):
                dur = wall_s / 60.0
                truncated = True
                if outcome == "DONE":
                    outcome = "INCOMPLETE"

        start = time
        time += dur
        building += dur
        events.append(("BUILD", node, start, time, outcome, truncated))

        if outcome == "DONE":
            status[node] = "DONE"
            run_count[node] = 0
        elif outcome in TERMINAL_OUTCOMES or run_count[node] >= cap:
            if node in retire_on_block:
                retired.add(node)
            elif fix_delay_min is not None:
                blocked_until[node] = time + fix_delay_min
            elif cyc.gap_to_next_min is not None:
                blocked_until[node] = time + cyc.gap_to_next_min
            else:
                blocked_until[node] = float("inf")
            run_count[node] = 0
        # else: INCOMPLETE, under cap -- stays ready, retried on a later pass

    return {
        "finish_min": time,
        "building_min": building,
        "idle_min": idle,
        "all_done": all(status[tgt] == "DONE" for tgt in targets),
        "events": events,
    }


def s0_timeline(rows: list[tuple[str, dt.datetime, float, str]]) -> dict:
    """S0 validation: replay real (task, start_ts, dur_min, outcome) rows in
    literal chronological order (no readiness logic at all -- this is what
    the serial list actually did). building = sum(dur_min); idle = sum of
    the gaps between one row ending and the next starting."""
    rows = sorted(rows, key=lambda r: r[1])
    if not rows:
        return {"finish_min": 0.0, "building_min": 0.0, "idle_min": 0.0}
    window_start = rows[0][1]
    building = sum(r[2] for r in rows)
    idle = 0.0
    cursor_end = rows[0][1]
    for _task, start_ts, dur_min, _outcome in rows:
        gap = (start_ts - cursor_end).total_seconds() / 60.0
        if gap > 0:
            idle += gap
        cursor_end = start_ts + dt.timedelta(minutes=dur_min)
    finish_min = (cursor_end - window_start).total_seconds() / 60.0
    return {"finish_min": finish_min, "building_min": building, "idle_min": idle}


# ------------------------------------------------------------------
# Real-repo I/O (exercised by the CLI below; not part of the pytest suite,
# same convention as PX-08's tick_closure.py real-data report)
# ------------------------------------------------------------------

def load_release_chain() -> tuple[str, ...]:
    agora_scripts = str(AGORA / "scripts")
    if agora_scripts not in sys.path:
        sys.path.insert(0, agora_scripts)
    spec = importlib.util.spec_from_file_location("_agora_next", AGORA / "scripts" / "next.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.RELEASE_CHAIN


def chain_slice(chain: tuple[str, ...], start: str, end: str) -> list[str]:
    return list(chain[chain.index(start): chain.index(end) + 1])


def resolve_card_path(card_id: str) -> Path | None:
    p = QUEUE / f"{card_id}.md"
    if p.exists():
        return p
    order = {"hold": 0, "retired": 1, "superseded": 2, "parked": 3, "legacy": 4}
    cands = sorted(PARKED.glob(f"{card_id}.md.*"), key=lambda x: order.get(x.suffix.lstrip("."), 9))
    return cands[0] if cands else None


def load_cards(card_ids: list[str]) -> dict[str, dict]:
    out = {}
    for cid in card_ids:
        p = resolve_card_path(cid)
        if p is not None:
            out[cid] = parse_card(p)
    return out


RUN_DIR_RE = re.compile(
    r"^(?:_archived-[a-z]+-)?(?P<task>.+?)(?:\.md)?-(?P<date>\d{8})-(?P<time>\d{4})(?:-\d+)?$"
)


def parse_run_dir(name: str) -> tuple[str, dt.datetime] | None:
    m = RUN_DIR_RE.match(name)
    if not m:
        return None
    try:
        ts = dt.datetime.strptime(m["date"] + m["time"], "%Y%m%d%H%M")
    except ValueError:
        return None
    return m["task"], ts


def load_run_outcome(run_dir: Path) -> str | None:
    if (run_dir / "DONE").exists():
        return "DONE"
    for marker in ("UNSATISFIABLE.md", "SPEC-INVALID.md", "GATE-FAILED.md"):
        if (run_dir / marker).exists():
            return marker[:-3]
    if (run_dir / "INCOMPLETE.md").exists():
        return "INCOMPLETE"
    return None  # dispatcher-cleared/in-progress noise -- excluded


def load_run_candidates(run_dir: Path) -> list[dict]:
    path = run_dir / "candidates.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        out.append({
            "failing": frozenset(row.get("failing_ids") or []),
            "wall_s": float(row.get("wall_s") or 0.0),
        })
    return out


def load_metrics_rows(agora_root: Path, tasks: set[str], window_start: dt.datetime,
                       window_end: dt.datetime) -> list[dict]:
    """One row per real dispatcher build cycle, from agora/runs/metrics.jsonl
    (per-cycle wall_minutes -- the whole cycle: worktree, baseline, every
    candidate, gate check -- not just candidates.jsonl's own per-candidate
    wall_s, which excludes that overhead and undercounts real BUILDING time
    by roughly half against A9's own headline number). `metrics.jsonl`'s
    `ts` is the cycle's END time; `start_ts` is derived from it."""
    path = agora_root / "runs" / "metrics.jsonl"
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("kind") != "build" or row.get("task") not in tasks:
            continue
        outcome = row.get("outcome")
        if outcome == "HARNESS-ERROR":
            continue  # dead input, never reached the card -- excluded, same as next.py's cap accounting
        try:
            end_ts = dt.datetime.fromisoformat(row["ts"])
        except (KeyError, ValueError):
            continue
        if not (window_start <= end_ts <= window_end):
            continue
        dur_min = float(row.get("wall_minutes") or 0.0)
        start_ts = end_ts - dt.timedelta(minutes=dur_min)
        rows.append({"task": row["task"], "start_ts": start_ts, "dur_min": dur_min,
                     "outcome": outcome or "INCOMPLETE"})
    return rows


def index_run_dirs(runs_dir: Path, tasks: set[str]) -> dict[str, list[tuple[dt.datetime, Path]]]:
    idx: dict[str, list[tuple[dt.datetime, Path]]] = {}
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir():
            continue
        parsed = parse_run_dir(d.name)
        if not parsed:
            continue
        task, ts = parsed
        if task in tasks:
            idx.setdefault(task, []).append((ts, d))
    return idx


def attach_candidates(rows: list[dict], run_index: dict[str, list[tuple[dt.datetime, Path]]],
                       tolerance_s: float = 300.0) -> None:
    """Matches each metrics.jsonl cycle row to the real run directory whose
    own start timestamp is closest to that row's derived start_ts (both are
    the same cycle, logged twice, so the match is normally exact to the
    minute); attaches its candidates.jsonl for plateau_cutoff. A row with no
    match inside `tolerance_s` gets `candidates=[]` (plateau shortening is
    simply unavailable for it, never fabricated)."""
    for r in rows:
        best, best_delta = None, None
        for ts, d in run_index.get(r["task"], []):
            delta = abs((ts - r["start_ts"]).total_seconds())
            if delta <= tolerance_s and (best_delta is None or delta < best_delta):
                best, best_delta = d, delta
        r["candidates"] = load_run_candidates(best) if best is not None else []


def load_raw_rows(agora_root: Path, tasks: set[str], window_start: dt.datetime,
                   window_end: dt.datetime) -> list[dict]:
    rows = load_metrics_rows(agora_root, tasks, window_start, window_end)
    attach_candidates(rows, index_run_dirs(agora_root / "runs", tasks))
    return rows


def rows_to_cycles(rows: list[dict]) -> dict[str, list[Cycle]]:
    by_task: dict[str, list[dict]] = {}
    for r in rows:
        by_task.setdefault(r["task"], []).append(r)
    cycles: dict[str, list[Cycle]] = {}
    for task, task_rows in by_task.items():
        task_rows.sort(key=lambda r: r["start_ts"])
        seq = []
        for i, r in enumerate(task_rows):
            if i + 1 < len(task_rows):
                end = r["start_ts"] + dt.timedelta(minutes=r["dur_min"])
                gap = max((task_rows[i + 1]["start_ts"] - end).total_seconds() / 60.0, 0.0)
            else:
                gap = None
            seq.append(Cycle(dur_min=r["dur_min"], outcome=r["outcome"],
                              candidates=r["candidates"], gap_to_next_min=gap))
        cycles[task] = seq
    return cycles


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

E05_SLICE_START = "203e-e05-telegraph-declare-draw-queue"
E04_SLICE_END = "210-e04-fault-injection"

# The replay's node set: exactly the cards with real run history inside the
# A9 window (research/factory/A9-throughput-timeline.md, 2026-09-18 13:01:04
# -> 2026-09-19 23:20:00). Every other card in the requested 203e..210 slice
# (205a onward) was never attempted in this window under the real serial
# chain, so there is no real run history to replay for it -- it is covered
# by part 1 (the DAG) but out of scope for part 2 (the replay), stated here
# rather than guessed. 204b1/207 are real, in-window, GPU-time-consuming
# cards that were later hand-retired from RELEASE_CHAIN; they are kept as
# "phantom" nodes (real cycles, but nothing in the replayed slice depends on
# them and they gate nothing) so S0 can validate against the measured
# baseline at all.
REPLAY_DONE_AT_START = ("203e-e05-telegraph-declare-draw-queue", "208+e05-spawn-fault-branches")
REPLAY_TARGETS = (
    "204a2-e05-reactive-reinforcement", "204a1-e05-telegraph-maturation",
    "204a3-e05-core-attack", "204z1-e05-s037-gate", "204z2-e05-s036-gate",
    "204b3-e05-damage-history", "204z-e05-s034-gate", "204b2-e05-unrest-colonize",
    "204z3-e05-s038-gate",
)
REPLAY_PHANTOMS = ("204b1-e05-conquest-garrison", "207-e05-step-order-fault")
WINDOW_START = dt.datetime(2026, 9, 18, 13, 1, 4)
WINDOW_END = dt.datetime(2026, 9, 19, 23, 20, 0)


# The last commit before the A9 measurement window (208+e05-spawn-fault-
# branches landed 2026-09-18 13:00:01 -0400, one minute before the window's
# own 13:01:04 start). build_dag needs each symbol's STUB-ness as it stood
# when these cards were actually queued and run, not today's -- most of the
# 204* cards in this slice have since landed on main, which would make their
# own snippet_symbol read as "already real" and silently erase the very
# edges (204a1->204a3, 204a1/204a3->204b2, ...) this experiment exists to
# find.
PRE_WINDOW_REV = "e024dde671b5591ca8074be1675c3d8da29908b0"


def csrc_texts_at_revision(project: Path, rev: str) -> dict[str, str]:
    ls = subprocess.run(["git", "-C", str(project), "ls-tree", "-r", "--name-only", rev, "--", "csrc"],
                         capture_output=True, text=True, check=True)
    texts: dict[str, str] = {}
    for path in ls.stdout.splitlines():
        if not path.endswith(".c"):
            continue
        show = subprocess.run(["git", "-C", str(project), "show", f"{rev}:{path}"],
                               capture_output=True, text=True, check=True)
        texts[Path(path).name] = show.stdout
    return texts


def _project_for(cards: dict[str, dict]) -> Path:
    for card in cards.values():
        if card.get("project"):
            return Path(card["project"])
    raise RuntimeError("no card carries a project: field")


def cmd_dag(argv: list[str]) -> int:
    chain = load_release_chain()
    slice_ids = chain_slice(chain, E05_SLICE_START, E04_SLICE_END)
    cards = load_cards(slice_ids)
    project = _project_for(cards)
    csrc_texts = csrc_texts_at_revision(project, PRE_WINDOW_REV)
    dag = build_dag(slice_ids, cards, project, csrc_texts)
    out = {"dag": dag, "stats": edge_stats(dag)}
    print(json.dumps(out, indent=2, default=list))
    return 0


def cmd_replay(argv: list[str]) -> int:
    nodes = list(REPLAY_DONE_AT_START) + list(REPLAY_TARGETS) + list(REPLAY_PHANTOMS)
    cards = load_cards(nodes)
    project = _project_for(cards)
    csrc_texts = csrc_texts_at_revision(project, PRE_WINDOW_REV)
    dag = build_dag(nodes, cards, project, csrc_texts, exclude_from_gates=frozenset(REPLAY_PHANTOMS))
    edges = edge_pairs(dag)

    tasks = set(nodes)
    rows = load_raw_rows(AGORA, tasks, WINDOW_START, WINDOW_END)
    cycles = rows_to_cycles(rows)

    priority_index = {n: i for i, n in enumerate(nodes)}

    def priority_of(n):
        return priority_index.get(n, len(nodes))

    report = {"dag_edges": dag["edges"], "duplicate_owners": dag["duplicate_owners"],
              "n_cycles_by_task": {t: len(c) for t, c in cycles.items()}}

    report["S0"] = s0_timeline([(r["task"], r["start_ts"], r["dur_min"], r["outcome"]) for r in rows])
    common = dict(nodes=nodes, edges=edges, cycles_by_task=cycles, priority_of=priority_of,
                  targets=list(REPLAY_TARGETS), done_at_start=set(REPLAY_DONE_AT_START),
                  retire_on_block=frozenset(REPLAY_PHANTOMS))
    report["S1"] = simulate(**common, use_plateau=False, fix_delay_min=None)
    report["S2"] = simulate(**common, use_plateau=True, fix_delay_min=None)
    for delay in (15, 30, 60):
        report[f"S3_{delay}"] = simulate(**common, use_plateau=True, fix_delay_min=float(delay))

    def summarize(r):
        return {k: r[k] for k in ("finish_min", "building_min", "idle_min", "all_done") if k in r}

    printable = {k: (summarize(v) if isinstance(v, dict) and "finish_min" in v else v)
                 for k, v in report.items()}
    print(json.dumps(printable, indent=2, default=list))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dag")
    sub.add_parser("replay")
    args, rest = ap.parse_known_args(argv)
    if args.cmd == "dag":
        return cmd_dag(rest)
    return cmd_replay(rest)


if __name__ == "__main__":
    raise SystemExit(main())
