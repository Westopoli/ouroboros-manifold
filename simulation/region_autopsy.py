"""
region_autopsy.py — Targeted diagnostic for hotspot regions
Run from simulation/:  python3 region_autopsy.py
"""

import sys, os, collections

import config
import sim_validator as sv

TICKS = 500
SEED = 1

HOTSPOT_REGIONS = [
    "region_p_f0", "region_c_f0", "region_f_f0", "region_o_f0",
    "region_e01", "region_e06", "region_e11", "region_e16",
    "region_e29", "region_e30",
]

EMPTY_REGION_MARKERS = {"region_e"}


def is_empty_origin(rid):
    return any(m in rid for m in EMPTY_REGION_MARKERS)


def run():
    scenario = {
        "name": "autopsy_full_stack",
        "ticks": TICKS,
        "seed": SEED,
        "use_tick_engine": True,
        "features": {
            "events": True, "factions": True, "border_friction": True,
            "recruitment": True, "adjacency_bonus": True, "oscillation": True,
            "technology": True, "diplomacy": True, "admin_revolts": True,
        },
        "overrides": {},
    }
    tlog = sv.run_recorded_scenario("autopsy_full_stack", scenario, seed_override=SEED)

    ownership_changes = collections.defaultdict(list)
    region_snapshots = collections.defaultdict(list)
    breakaway_origins = []
    agent_decisions = collections.defaultdict(lambda: collections.Counter())
    known_factions = set()

    prev_owners = {}

    for snap in tlog.snapshots:
        tick = snap.tick

        for rid, rdata in snap.regions.items():
            fid = rdata["faction_id"]
            f = rdata["fields"]
            ten = f.get("tension", 0)
            eco = f.get("economy", 0)
            mil = f.get("military", 0)
            pop = f.get("population", 0)

            if rid in HOTSPOT_REGIONS or is_empty_origin(rid):
                region_snapshots[rid].append((tick, ten, eco, mil, pop))

            old_fid = prev_owners.get(rid)
            if old_fid != fid and tick > 0:
                cause = "unknown"
                for con in snap.conquests:
                    if con.get("region_id") == rid:
                        cause = "conquest"
                        break
                if cause == "unknown":
                    for evt in snap.events_fired:
                        if evt.get("region_id") == rid:
                            tid = evt.get("template_id", "")
                            if evt.get("creates_faction"):
                                cause = "revolt/breakaway"
                            elif "coloniz" in tid.lower() or (old_fid is None and fid is not None):
                                cause = "colonization"
                            break
                if cause == "unknown" and old_fid is None and fid is not None:
                    cause = "colonization"
                ownership_changes[rid].append((tick, old_fid, fid, cause))

            prev_owners[rid] = fid

        new_fids = set(snap.factions.keys()) - known_factions
        for nfid in new_fids:
            if known_factions and "breakaway_" in nfid:
                parts = nfid.split("_", 2)
                spawn_region = "_".join(parts[2:]) if len(parts) > 2 else "?"
                spawn_region = "region_" + spawn_region if not spawn_region.startswith("region_") else spawn_region
                breakaway_origins.append((tick, nfid, spawn_region, is_empty_origin(spawn_region)))
            known_factions.add(nfid)

        for a in snap.faction_actions:
            fid = a.get("faction_id")
            action = a.get("action", "accumulate")
            agent_decisions[fid][action] += 1

    print_report(ownership_changes, region_snapshots, breakaway_origins, agent_decisions, TICKS, tlog)


def print_report(ownership_changes, region_snapshots, breakaway_origins, agent_decisions, tick_count, tlog):
    print("\n" + "=" * 80)
    print("  REGION AUTOPSY REPORT")
    print("  " + f"{tick_count} ticks, seed {SEED}")
    print("=" * 80)

    # ── SECTION A ─────────────────────────────────────────────────────────
    print("\n── A. OWNERSHIP CHANGES PER REGION ─────────────────────────")
    print(f"  {'Region':<25} {'Changes':>8} {'Rate/100t':>10} {'MinGap':>7} {'MaxGap':>7} {'MeanGap':>8}")
    print(f"  {'-'*25} {'-'*8:>8} {'-'*10:>10} {'-'*7:>7} {'-'*7:>7} {'-'*8:>8}")

    all_regions_with_changes = sorted(ownership_changes.keys())
    for rid in all_regions_with_changes:
        changes = ownership_changes[rid]
        n = len(changes)
        rate = n / tick_count * 100
        if n >= 2:
            gaps = [changes[i+1][0] - changes[i][0] for i in range(n-1)]
            min_gap = min(gaps)
            max_gap = max(gaps)
            mean_gap = sum(gaps) / len(gaps)
        else:
            min_gap = max_gap = mean_gap = 0
        print(f"  {rid:<25} {n:>8} {rate:>10.1f} {min_gap:>7} {max_gap:>7} {mean_gap:>8.1f}")

    # ── SECTION B ─────────────────────────────────────────────────────────
    print("\n── B. OWNERSHIP TIMELINE (worst 3 regions by churn) ────────")
    worst = sorted(all_regions_with_changes, key=lambda r: len(ownership_changes[r]), reverse=True)[:3]

    for rid in worst:
        changes = ownership_changes[rid]
        print(f"\n  {rid} ({len(changes)} changes):")
        print(f"    {'Tick':>5} {'Old Faction':<30} {'New Faction':<30} {'Cause':<15}")
        print(f"    {'-----':>5} {'-'*30} {'-'*30} {'-'*15}")
        for tick, old_f, new_f, cause in changes[:30]:
            old_short = (old_f or 'None')[:30]
            new_short = (new_f or 'None')[:30]
            print(f"    {tick:>5} {old_short:<30} {new_short:<30} {cause:<15}")
        if len(changes) > 30:
            print(f"    ... and {len(changes) - 30} more changes")

    # ── SECTION C ─────────────────────────────────────────────────────────
    print("\n── C. TENSION TRAJECTORY (sampled every 25 ticks) ─────────")
    for target in ["region_p_f0", "region_c_f0", "region_e29", "region_e30"]:
        if target not in region_snapshots:
            continue
        snaps = region_snapshots[target]
        sample_ticks = set(range(0, tick_count + 1, 25))
        print(f"\n  {target}:")
        print(f"  {'Tick':>5} {'Tension':>8} {'Economy':>8} {'Military':>8} {'Pop':>8}")
        print(f"  {'-----':>5} {'--------':>8} {'--------':>8} {'--------':>8} {'--------':>8}")
        for s in snaps:
            if s[0] in sample_ticks:
                print(f"  {s[0]:>5} {s[1]:>8.1f} {s[2]:>8.1f} {s[3]:>8.1f} {s[4]:>8.1f}")

    # ── SECTION D ─────────────────────────────────────────────────────────
    print("\n── D. BREAKAWAY SPAWN ORIGINS ──────────────────────────────")
    from_empty = [b for b in breakaway_origins if b[3]]
    from_real = [b for b in breakaway_origins if not b[3]]
    total = len(breakaway_origins)
    print(f"  Total breakaways: {total}")
    print(f"  From former-empty regions: {len(from_empty)} ({len(from_empty)/max(1,total):.0%})")
    print(f"  From original faction territory: {len(from_real)} ({len(from_real)/max(1,total):.0%})")

    if from_empty:
        print(f"\n  Former-empty region breakdown:")
        empty_counts = collections.Counter(b[2] for b in from_empty)
        for rid, count in empty_counts.most_common():
            print(f"    {rid}: {count} breakaways")

    if from_real:
        print(f"\n  Original territory breakdown:")
        real_counts = collections.Counter(b[2] for b in from_real)
        for rid, count in real_counts.most_common():
            print(f"    {rid}: {count} breakaways")

    # ── SECTION E ─────────────────────────────────────────────────────────
    print("\n── E. ZOMBIE FACTION ANALYSIS ──────────────────────────────")
    print("  (Breakaway factions surviving 100+ ticks with 100% accumulate)")
    zombies = []
    for fid, counts in sorted(agent_decisions.items()):
        if "breakaway_" not in fid:
            continue
        total_acts = sum(counts.values())
        if total_acts < 100:
            continue
        acc_pct = counts.get("accumulate", 0) / total_acts * 100
        if acc_pct >= 99.5:
            zombies.append((fid, total_acts, acc_pct))
    print(f"  Total zombie breakaways: {len(zombies)}")
    for fid, total_acts, acc_pct in zombies:
        print(f"    {fid}: {total_acts} ticks, {acc_pct:.0f}% accumulate")

    # ── SECTION F ─────────────────────────────────────────────────────────
    print("\n── F. BORDER FRICTION CODE PATH ────────────────────────────")
    print("  CONFIRMED: tick.py calls _apply_border_friction() (line 269)")
    print("  This is the INLINE version — FLAT friction per hostile neighbor.")
    print("  border_friction.py run_border_friction() is NOT called.")
    print()
    print("  Active formula (tick.py _apply_border_friction):")
    print("    tension += BORDER_FRICTION_TENSION  (flat, per hostile neighbor)")
    print("    economy -= BORDER_FRICTION_ECONOMY  (flat, per hostile neighbor)")
    print(f"    Current values: tension +{config.BORDER_FRICTION_TENSION}, economy -{config.BORDER_FRICTION_ECONOMY}")
    print()
    print("  UNUSED formula (border_friction.py):")
    print("    tension += BORDER_FRICTION_TENSION * (neighbor_military / 100)")
    print("    economy -= BORDER_FRICTION_ECONOMY * (neighbor_military / 100)")
    print("    (Scales by neighbor military — weak neighbors cause less friction)")
    print()
    print("  Default diplomatic stance: 'neutral' (changed from 'hostile' via Fix D)")
    print("    border_friction.py also defaults to 'neutral' — now consistent.")


if __name__ == "__main__":
    print("Region Autopsy — Ouroboros Manifold")
    print("=" * 40)
    run()
