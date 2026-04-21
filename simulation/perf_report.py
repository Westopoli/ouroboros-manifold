# Correlates logs/sim_perf.jsonl + logs/client_perf.jsonl, writes a
# human-readable markdown report to logs/perf_report.md.
#
# Usage:
#   python3 simulation/perf_report.py
#
# Claude reads the report and classifies which hitching hypothesis
# (A=snapshot stomp, B=loose resync threshold, C=Godot-side interp mismatch)
# the snap-back pattern matches. See plan H.4 and stage_8_5_spec.md.

import json
import os
import statistics
import sys
from collections import Counter, defaultdict

SIM_LOG = "logs/sim_perf.jsonl"
CLIENT_LOG = "logs/client_perf.jsonl"
OUT_PATH = "logs/perf_report.md"


def read_jsonl(path):
    header = None
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("type") == "header":
                header = d
            else:
                rows.append(d)
    return header, rows


def pct(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]


def fmt_ms(x):
    return f"{x:.2f}ms"


def main():
    if not os.path.exists(SIM_LOG) or not os.path.exists(CLIENT_LOG):
        print(f"Missing input. Expected {SIM_LOG} and {CLIENT_LOG}.", file=sys.stderr)
        print("Run: python3 simulation/run_debug_server.py  (then)  python3 simulation/perf_probe_client.py", file=sys.stderr)
        sys.exit(1)

    sim_header, sim_rows = read_jsonl(SIM_LOG)
    client_header, client_rows = read_jsonl(CLIENT_LOG)

    # ── Server-side stats ───────────────────────────────────────────────────
    step_ms = [r["step_ms"] for r in sim_rows if r.get("step_ms", 0) > 0]
    ser_ms = [r["ser_ms"] for r in sim_rows]
    snapshot_rows = [r for r in sim_rows if r.get("msg") == "snapshot"]
    delta_rows = [r for r in sim_rows if r.get("msg") == "delta"]
    snapshot_bytes = [r["bytes"] for r in snapshot_rows]
    delta_bytes = [r["bytes"] for r in delta_rows]
    delta_updated = [r.get("units_updated", 0) for r in delta_rows]

    # ── Client-side stats ───────────────────────────────────────────────────
    msg_rows = [r for r in client_rows if "msg" in r and "event" not in r]
    snap_events = [r for r in client_rows if r.get("event") == "snap"]

    snaps_by_tick = defaultdict(list)
    for e in snap_events:
        snaps_by_tick[e["tick"]].append(e)

    by_cause = Counter(e["cause"] for e in snap_events)
    msg_type_by_tick = {m["tick"]: m["msg"] for m in msg_rows}

    # Top ticks by total snap events
    tick_totals = [(t, len(evts)) for t, evts in snaps_by_tick.items()]
    tick_totals.sort(key=lambda x: -x[1])

    # Separate stats by cause
    stomp = [e for e in snap_events if e["cause"] == "snapshot_stomp"]
    delta_snap = [e for e in snap_events if e["cause"] == "delta_update"]
    stomp_magnitudes = [e["snap_wu"] for e in stomp]
    delta_snap_magnitudes = [e["snap_wu"] for e in delta_snap]
    backward_count = sum(1 for e in delta_snap if e.get("backward"))

    # ── Hypothesis classification ───────────────────────────────────────────
    snapshot_ticks = {r["tick"] for r in snapshot_rows}
    stomp_ticks = {e["tick"] for e in stomp}
    aligned_with_snapshot = stomp_ticks & snapshot_ticks
    verdict_parts = []
    if stomp:
        if stomp_ticks.issubset(snapshot_ticks):
            verdict_parts.append(
                f"HYPOTHESIS A CONFIRMED. All {len(stomp)} snapshot_stomp events fall on "
                f"full-snapshot ticks {sorted(snapshot_ticks)}. The 5-second user-visible hitch "
                f"is full snapshots overriding client DR state with authoritative positions "
                f"that lag the client's extrapolation."
            )
        else:
            verdict_parts.append(
                f"HYPOTHESIS A partial: {len(aligned_with_snapshot)}/{len(stomp_ticks)} stomp "
                f"ticks align with snapshot ticks. Investigate outliers."
            )
    if delta_snap:
        if backward_count / len(delta_snap) > 0.3:
            verdict_parts.append(
                f"HYPOTHESIS B signal: {backward_count}/{len(delta_snap)} delta snap events "
                f"are backward moves — resync threshold may be too loose."
            )
        else:
            verdict_parts.append(
                f"Delta-update snaps are mostly forward corrections ({len(delta_snap) - backward_count}"
                f"/{len(delta_snap)} forward), consistent with DR velocity error on course changes. "
                f"Not indicative of Hypothesis B."
            )

    # ── Tick-rate check ─────────────────────────────────────────────────────
    if sim_rows:
        first_t = sim_rows[0].get("t_mono", 0.0)
        last_t = sim_rows[-1].get("t_mono", 0.0)
        last_tick = sim_rows[-1].get("tick", 0)
        achieved_hz = (last_tick - sim_rows[0].get("tick", 0)) / (last_t - first_t) if last_t > first_t else 0.0
    else:
        achieved_hz = 0.0

    # ── Write report ────────────────────────────────────────────────────────
    out = []
    out.append("# Stage 8.5 Perf Report")
    out.append("")
    out.append(f"Generated from `{SIM_LOG}` + `{CLIENT_LOG}`.")
    out.append("")
    out.append(f"- sim_perf rows: {len(sim_rows)}  ({len(snapshot_rows)} snapshot, {len(delta_rows)} delta)")
    out.append(f"- client messages received: {len(msg_rows)}")
    out.append(f"- snap events detected: {len(snap_events)}")
    out.append(f"- achieved tick rate: {achieved_hz:.2f} Hz")
    out.append("")
    out.append("## Server step time")
    out.append("")
    if step_ms:
        out.append(f"- count: {len(step_ms)}")
        out.append(f"- p50: {fmt_ms(pct(step_ms, 50))}")
        out.append(f"- p95: {fmt_ms(pct(step_ms, 95))}")
        out.append(f"- p99: {fmt_ms(pct(step_ms, 99))}")
        out.append(f"- max: {fmt_ms(max(step_ms))}")
        out.append(f"- mean: {fmt_ms(statistics.mean(step_ms))}")
    else:
        out.append("(no samples)")
    out.append("")
    out.append("## Serialization time")
    out.append("")
    if ser_ms:
        out.append(f"- snapshot ser p95: {fmt_ms(pct([r['ser_ms'] for r in snapshot_rows], 95))}  max: {fmt_ms(max((r['ser_ms'] for r in snapshot_rows), default=0.0))}")
        out.append(f"- delta ser p95:    {fmt_ms(pct([r['ser_ms'] for r in delta_rows], 95))}  max: {fmt_ms(max((r['ser_ms'] for r in delta_rows), default=0.0))}")
    out.append("")
    out.append("## Payload sizes")
    out.append("")
    if snapshot_bytes:
        out.append(f"- snapshot bytes: mean {int(statistics.mean(snapshot_bytes)):,}  p95 {int(pct(snapshot_bytes, 95)):,}  max {max(snapshot_bytes):,}")
    if delta_bytes:
        out.append(f"- delta bytes:    mean {int(statistics.mean(delta_bytes)):,}  p95 {int(pct(delta_bytes, 95)):,}  max {max(delta_bytes):,}")
    if delta_updated:
        out.append(f"- delta units_updated: mean {statistics.mean(delta_updated):.1f}  p95 {pct(delta_updated, 95)}  max {max(delta_updated)}")
    out.append("")
    out.append("## Snap events (client-side DR vs authoritative)")
    out.append("")
    out.append(f"- total: {len(snap_events)}")
    out.append(f"- by cause: {dict(by_cause)}")
    if stomp_magnitudes:
        out.append(f"- snapshot_stomp magnitude (wu): mean {statistics.mean(stomp_magnitudes):.2f}  p95 {pct(stomp_magnitudes, 95):.2f}  max {max(stomp_magnitudes):.2f}")
    if delta_snap_magnitudes:
        out.append(f"- delta_update magnitude (wu):   mean {statistics.mean(delta_snap_magnitudes):.2f}  p95 {pct(delta_snap_magnitudes, 95):.2f}  max {max(delta_snap_magnitudes):.2f}")
        out.append(f"- delta_update backward fraction: {backward_count}/{len(delta_snap)} ({100.0*backward_count/len(delta_snap):.1f}%)")
    out.append("")
    out.append("### Top snap-event ticks")
    out.append("")
    out.append("| tick | msg type | snap events | % of 400 units |")
    out.append("|------|----------|-------------|----------------|")
    for tick, n in tick_totals[:12]:
        mtype = msg_type_by_tick.get(tick, "?")
        out.append(f"| {tick} | {mtype} | {n} | {100.0*n/400.0:.0f}% |")
    out.append("")
    out.append("### Snapshot ticks vs stomp-event alignment")
    out.append("")
    out.append(f"- full-snapshot ticks in log: {sorted(snapshot_ticks)}")
    out.append(f"- ticks with stomp events:    {sorted(stomp_ticks)}")
    aligned = stomp_ticks & snapshot_ticks
    out.append(f"- aligned: {sorted(aligned)}  ({len(aligned)}/{len(stomp_ticks)} stomp ticks match a snapshot tick)")
    out.append("")
    out.append("## Hypothesis verdict")
    out.append("")
    for p in verdict_parts:
        out.append(f"- {p}")
    out.append("")
    out.append("## Hypothesis reminders")
    out.append("")
    out.append("- **A (snapshot stomp):** snap-backs cluster on SNAPSHOT_INTERVAL boundaries, magnitude ≈ velocity × elapsed_since_last_resync.")
    out.append("- **B (loose resync threshold):** snap-backs spread across ticks, disproportionately backward, tied to direction changes.")
    out.append("- **C (Godot-side interp mismatch):** this probe uses exact Python dt; few snap-backs here means the protocol is clean and the bug is in Godot's display_positions interpolation, not the protocol.")

    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"Wrote {OUT_PATH}  ({len(out)} lines)")


if __name__ == "__main__":
    main()
