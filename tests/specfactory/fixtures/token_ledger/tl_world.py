# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md Amendment A10, A14 (fixtures for tests/specfactory/test_token_ledger.py)
"""Synthetic transcripts and thresholds for the token ledger and metrics M25 to M29 (HARNESS-mm-12).
Reuses the builders of fixtures/method_metrics/mm_world.py (entry, write_transcripts, build_world).

Interfaces the fixtures fix (the spec leaves them open; the tests writer's report lists them):
- token_ledger.py flags: --day YYYY-MM-DD | --week YYYY-Www, --plan CSV (columns date,piece,role,estimate_m),
  --transcripts ROOT, --project SLUG (default the repo's folder), --thresholds TOML (week mode reads the allotment).
- A run is a sub-agent transcript `<session>/subagents/agent-*.jsonl` with `.meta.json` {"description": "<piece> <role>"};
  its day is the date of its entries' timestamps; a top-level session counts as `coordinator` per entry day.
- Tokens of one entry = input + cache_read + cache_creation + output (cache reads at face value), reported in millions.
- Thresholds toml: tables M25..M29 (id, gap, draft, value, direction, unit, approved, baseline, window, phase) and
  `[estimates.<task type>]` with median_m, ceiling_m, calls_cap. M25 value is the worst ratio over the week's landed
  pieces of (their runs' tokens in M) / (sum of the ceiling_m of the roles run on them), limit 1.0, a role maps to the
  estimates table of the same name. M26 value is the week allotment in M (1500) with day_m 300, dispatcher_m 60,
  pieces_m 180, reserve_m 60 as extra keys. M27 value is a ratio, M28 messages per session-day, M29 extra tests runs.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "method_metrics"))
import mm_world as W  # noqa: E402

APPROVED = "Westley 2026-10-28"  # fixtures isolate the compare from DRAFT; the real toml's DRAFT state has its own case
PRICES = {
    "claude-fable-5-1": {"input": 10.0, "cache_read": 0.25, "cache_write": 12.5, "output": 50.0},
    "claude-sonnet-5-5": {"input": 2.0, "cache_read": 0.1, "cache_write": 2.5, "output": 10.0},
}
ESTIMATES = {"tests": (3.8, 16, 60), "build": (1.2, 6.3, 40), "land": (1.6, 5.5, 40), "records": (0.2, 1.2, 15),
             "audit": (4.7, 13.8, 60), "research": (1.4, 6.4, 30), "drift": (10.9, 15, 70)}
NEW = {"M25": (1.0, "ratio"), "M26": (1500, "M"), "M27": (0.1, "ratio"), "M28": (4, "messages"), "M29": (1, "runs")}


def thresholds(approved=APPROVED, prices=None):
    out = [W.thresholds_toml(prices=prices)]
    for mid, (val, unit) in NEW.items():
        out += [f"[{mid}]", f'id = "{mid}"', 'gap = "G24"', f'draft = "DRAFT-mm-{mid}"', f"value = {val}", 'direction = "<="',
                f'unit = "{unit}"', f"approved = {json.dumps(approved)}", "baseline = 0", 'window = "week"', 'phase = "both"']
        if mid == "M26":
            out += ["day_m = 300", "dispatcher_m = 60", "pieces_m = 180", "reserve_m = 60"]
        out.append("")
    for task, (med, ceil, cap) in ESTIMATES.items():
        out += [f"[estimates.{task}]", f"median_m = {med}", f"ceiling_m = {ceil}", f"calls_cap = {cap}", ""]
    return "\n".join(out)


def tok(model, stamp, m=0.0, *, usage=None, tools=(), sidechain=False, text="ok"):
    """An assistant entry holding `m` million tokens (5% input, 90% cache read, 4% cache write, 1% output), or the
    explicit `usage` dict."""
    e = W.entry(model, stamp, tools=tools, sidechain=sidechain, text=text)
    t = int(round(m * 1e6))
    e["message"]["usage"] = usage or {"input_tokens": t * 5 // 100, "cache_read_input_tokens": t * 90 // 100,
                                      "cache_creation_input_tokens": t * 4 // 100,
                                      "output_tokens": t - t * 5 // 100 - t * 90 // 100 - t * 4 // 100}
    return e


def at(day, hour=10, minute=0):
    return f"{day}T{hour:02d}:{minute:02d}:00.000Z"


def run_files(session, n, desc, entries):
    """Transcript files of one sub-agent run `desc` ("P0 tests") under top-level `session`."""
    base = f"{session}/subagents/agent-{n}"
    return {base + ".jsonl": entries, base + ".meta.json": {"agentType": "engineer", "description": desc}}


def event(kind, stamp):
    """A user entry the harness injects: a finished background task or a message from another session."""
    if kind == "task":
        return {"type": "user", "isSidechain": False, "timestamp": stamp, "userType": "external",
                "origin": {"kind": "task-notification", "producer": "session-task", "runId": "r1"},
                "message": {"role": "user", "content": "<task-notification>\n<task-id>b1</task-id>\n</task-notification>"}}
    return {"type": "user", "isSidechain": False, "timestamp": stamp, "userType": "external",
            "origin": {"kind": "peer", "from": "uds:/run/x.sock", "name": "other-chat"},
            "message": {"role": "user", "content": "Another Claude session sent a message:\n<cross-session-message from=\"uds:/run/x.sock\">hi</cross-session-message>"}}


def dispatcher_episodes(text_only, total=10, model=W.SONNET, day=W.D["wed"]):
    """A top-level session that spawns (one Agent call), then `total` events each followed by one assistant turn,
    the first `text_only` of them text-only and the rest a Bash call."""
    es = [W.clean(model, at(day, 9, 0))]
    for i in range(total):
        kind = "task" if i % 2 == 0 else "peer"
        es.append(event(kind, at(day, 10, 2 * i)))
        if i < text_only:
            es.append(W.entry(model, at(day, 10, 2 * i + 1), text="status: all quiet"))
        else:
            es.append(W.entry(model, at(day, 10, 2 * i + 1), tools=[("Bash", {"command": "ls"})]))
    return es
