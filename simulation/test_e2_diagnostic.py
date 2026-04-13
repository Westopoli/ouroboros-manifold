"""
E2 Diagnostic — isolates why a conquest fails to transfer ownership.

Three hypotheses:
  A) Non-conquest ownership change overwrites the transfer
     (breakaway formation, latent-loyalty reversion, zombie absorption)
  B) conqueror_absorbed exemption missed — absorb happens wrong tick
  C) Collision edge case — conquest logged but different faction won

Run:
  python3 test_e2_diagnostic.py
"""
import sys
sys.path.insert(0, ".")

from sim_tuner import SCENARIOS
from sim_validator import run_recorded_scenario

SCENARIO = "14_mission_calm"
SEED     = int(sys.argv[1]) if len(sys.argv) > 1 else 3

# ─── Run ──────────────────────────────────────────────────────────────────────

print(f"\n{'═'*68}")
print(f"  E2 DIAGNOSTIC — {SCENARIO}  seed={SEED}")
print(f"{'═'*68}\n")

scenario = SCENARIOS[SCENARIO]
tlog     = run_recorded_scenario(SCENARIO, scenario, seed_override=SEED)
snaps    = tlog.snapshots

# ─── Helper ───────────────────────────────────────────────────────────────────

def owner_at(rid, idx):
    if idx < 0 or idx >= len(snaps):
        return "—"
    rd = snaps[idx].regions.get(rid)
    return rd["faction_id"] if rd else "—"

def events_for(idx, rid):
    """Return events fired at snapshot index idx that mention region rid."""
    if idx < 0 or idx >= len(snaps):
        return []
    return [e for e in snaps[idx].events_fired
            if e.get("region_id") == rid or e.get("region") == rid]

def is_breakaway_event(evt):
    tid = evt.get("template_id", "")
    return "breakaway" in tid or "revolt" in tid or "reversion" in tid

# ─── Section 1: Collect ALL E2 failures ───────────────────────────────────────

failures = []
for i, snap in enumerate(snaps):
    for conquest in snap.conquests:
        rid     = conquest.get("region_id")
        new_fid = conquest.get("new_faction_id")
        if not rid or not new_fid:
            continue
        ni = i + 1
        if ni >= len(snaps):
            continue
        actual = owner_at(rid, ni)
        if actual == new_fid:
            continue

        # Evaluate exemptions
        same_tick     = sum(1 for c in snap.conquests if c.get("region_id") == rid)
        next_reconq   = any(c.get("region_id") == rid for c in snaps[ni].conquests)
        conq_absorbed = new_fid not in snaps[ni].factions

        if same_tick > 1 or next_reconq or conq_absorbed:
            continue

        failures.append({
            "snap_idx":     i,
            "tick":         snap.tick,
            "region_id":    rid,
            "old_fid":      conquest.get("old_faction_id", "—"),
            "new_fid":      new_fid,
            "actual_t1":    actual,
            "same_tick_n":  same_tick,
            "next_reconq":  next_reconq,
            "conq_absorbed":conq_absorbed,
        })

total_conquests = sum(len(s.conquests) for s in snaps)
print(f"Total conquests: {total_conquests}  |  E2 failures (unexempted): {len(failures)}")

# ─── Section 2: Per-failure triage ────────────────────────────────────────────

print(f"\n{'─'*68}")
print("  PER-FAILURE TRIAGE")
print(f"{'─'*68}")

for idx_f, f in enumerate(failures):
    i       = f["snap_idx"]
    tick    = f["tick"]
    rid     = f["region_id"]
    new_fid = f["new_fid"]
    actual  = f["actual_t1"]
    old_fid = f["old_fid"]

    print(f"\n  [{idx_f+1}] tick={tick}  region={rid}")
    print(f"      Conquest:  {old_fid}  →  {new_fid}")
    print(f"      Actual T+1 owner: {actual}")

    # Classify the actual owner
    if actual and "breakaway" in actual:
        note = "← BREAKAWAY FACTION"
    elif actual == old_fid:
        note = "← REVERTED to pre-conquest owner"
    elif actual and "player" in actual.lower():
        note = "← player faction"
    else:
        note = ""
    if note:
        print(f"      {note}")

    # Exemption audit
    print(f"\n      Exemption audit:")
    print(f"        same_tick_reconquest : {f['same_tick_n']} conquest(s) of this region at tick {tick}"
          f"  (need >1 to skip)  {'→ NOT exempt' if f['same_tick_n'] <= 1 else '→ SKIPPED'}")
    print(f"        next_tick_reconquest : {f['next_reconq']}  {'→ NOT exempt' if not f['next_reconq'] else '→ SKIPPED'}")
    print(f"        conqueror_absorbed   : {f['conq_absorbed']}  {'→ NOT exempt' if not f['conq_absorbed'] else '→ SKIPPED'}")

    # Ownership chain
    o_prev = owner_at(rid, i - 1)
    o_at   = owner_at(rid, i)
    o_next = owner_at(rid, i + 1)
    o_n2   = owner_at(rid, i + 2)
    print(f"\n      Ownership chain:")
    print(f"        tick {tick-1:>5} (T-1): {o_prev}")
    print(f"        tick {tick:>5} (T)  : {o_at}  ← conquest recorded")
    print(f"        tick {tick+1:>5} (T+1): {o_next}  ← E2 checks here")
    print(f"        tick {tick+2:>5} (T+2): {o_n2}")

    # Events at T and T+1
    evts_t  = events_for(i,   rid)
    evts_t1 = events_for(i+1, rid)

    def fmt_evt(e):
        tid = e.get("template_id", e.get("type", "?"))
        marker = " ★" if is_breakaway_event(e) else ""
        return f"{tid}{marker}"

    if evts_t:
        print(f"\n      Events at T (tick {tick}):")
        for e in evts_t:
            print(f"        · {fmt_evt(e)}")
    if evts_t1:
        print(f"      Events at T+1 (tick {tick+1}):")
        for e in evts_t1:
            print(f"        · {fmt_evt(e)}")
    if not evts_t and not evts_t1:
        print(f"\n      No events found for this region at T or T+1.")

    # Hypothesis verdict
    breakaway_at_t1 = any(is_breakaway_event(e) for e in evts_t1)
    breakaway_at_t  = any(is_breakaway_event(e) for e in evts_t)
    is_reversion    = (actual == old_fid)
    is_new_breakaway= actual and "breakaway" in actual

    if breakaway_at_t1 or breakaway_at_t:
        verdict = "HYPOTHESIS A — non-conquest event changed ownership"
    elif is_reversion:
        verdict = "HYPOTHESIS A — latent-loyalty reversion (no event record)"
    elif is_new_breakaway and not breakaway_at_t1:
        verdict = "HYPOTHESIS A — ownership became a breakaway (cause unclear, no event found)"
    else:
        verdict = "UNKNOWN — no matching hypothesis"

    print(f"\n      → {verdict}")

# ─── Section 3: Non-conquest ownership changes ────────────────────────────────

print(f"\n{'─'*68}")
print("  NON-CONQUEST OWNERSHIP CHANGES  (ownership shifted without a conquest record)")
print(f"{'─'*68}")

non_conquest_changes = []

for i in range(1, len(snaps)):
    prev = snaps[i - 1]
    curr = snaps[i]
    conquered_rids = {c.get("region_id") for c in curr.conquests}
    colonized_rids = {a.get("target_region") for a in curr.faction_actions
                      if a.get("action") == "colonize" and a.get("outcome_band") == "success"}

    for rid, rdata in curr.regions.items():
        new_fid  = rdata.get("faction_id")
        prev_rdata = prev.regions.get(rid)
        if not prev_rdata:
            continue
        old_fid  = prev_rdata.get("faction_id")
        if old_fid == new_fid:
            continue
        if rid in conquered_rids or rid in colonized_rids:
            continue

        region_evts = events_for(i, rid)
        evt_types   = [e.get("template_id", e.get("type", "?")) for e in region_evts]
        has_revolt  = any(is_breakaway_event(e) for e in region_evts)

        non_conquest_changes.append({
            "tick":       curr.tick,
            "region_id":  rid,
            "old_fid":    old_fid,
            "new_fid":    new_fid,
            "evt_types":  evt_types,
            "has_revolt": has_revolt,
        })

if non_conquest_changes:
    revolt_count  = sum(1 for c in non_conquest_changes if c["has_revolt"])
    zombie_count  = sum(1 for c in non_conquest_changes
                        if not c["has_revolt"] and c["new_fid"] and "breakaway" not in c["new_fid"])
    breakaway_count = sum(1 for c in non_conquest_changes
                          if not c["has_revolt"] and c["new_fid"] and "breakaway" in c["new_fid"])
    print(f"  Total: {len(non_conquest_changes)} changes"
          f"  (with revolt event: {revolt_count}"
          f"  | new breakaway owner: {breakaway_count}"
          f"  | other: {zombie_count})")

    print(f"\n  {'Tick':<8} {'Region':<25} {'Old Owner':<28} {'New Owner':<28} {'Events'}")
    print(f"  {'─'*8} {'─'*25} {'─'*28} {'─'*28} {'─'*30}")
    for c in non_conquest_changes:
        evt_str = ", ".join(c["evt_types"][:3]) if c["evt_types"] else "(none)"
        star    = " ★" if c["has_revolt"] else ""
        print(f"  {c['tick']:<8} {c['region_id']:<25} {str(c['old_fid']):<28} "
              f"{str(c['new_fid']):<28} {evt_str}{star}")
else:
    print("  None found — all ownership changes have a conquest or colonization record.")

# ─── Section 4: Summary ───────────────────────────────────────────────────────

print(f"\n{'─'*68}")
print("  SUMMARY")
print(f"{'─'*68}")
print(f"  Total conquests              : {total_conquests}")
print(f"  E2 failures (unexempted)     : {len(failures)}")

if failures:
    hyp_a = sum(1 for f2 in failures
                if (any(is_breakaway_event(e)
                        for e in events_for(f2['snap_idx'],   f2['region_id']))
                    or any(is_breakaway_event(e)
                           for e in events_for(f2['snap_idx']+1, f2['region_id']))
                    or f2['actual_t1'] == f2['old_fid']
                    or (f2['actual_t1'] and "breakaway" in f2['actual_t1'])))
    hyp_unk = len(failures) - hyp_a
    print(f"  Hypothesis A (non-conquest)  : {hyp_a}")
    print(f"  Unknown                      : {hyp_unk}")

print(f"\n{'═'*68}\n")
