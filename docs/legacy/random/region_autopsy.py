# region_autopsy.py — Targeted diagnostic for hotspot regions
# ============================================================
#
# Paste to Claude Code with this prompt:
#
#   Read region_autopsy.py. Adapt it to our project's imports and run it.
#   It needs to run a 500-tick simulation (seed 1, same as bible_diagnostic)
#   and collect per-tick data for specific regions. The output should be
#   pasted back to Westley — do not summarize.
#
# This script answers three questions:
#   1. How often do hotspot regions change hands? (conquest churn)
#   2. What are the tension sources on a flatlined region? (tension breakdown)
#   3. How many breakaways spawn from former-empty regions vs real territory?

# ── ADAPT THESE IMPORTS ────────────────────────────────────────────────
# Claude Code: replace with actual project imports, same as bible_diagnostic.py
# import config, world gen, tick runner, etc.

TICKS = 500
SEED = 1

# ── DATA TO COLLECT ────────────────────────────────────────────────────
#
# For each tick, for each region, record:
#   - faction_id (who owns it)
#   - tension, economy, military, population
#
# Additionally, for hotspot regions (region_e1, region_c_f0, region_e0,
# region_f_f0, region_p_f0, region_pe0), record:
#   - Every ownership change (tick, old_faction, new_faction, cause)
#   - Time between consecutive ownership changes
#
# For ALL breakaway spawns:
#   - What region they spawned from
#   - Whether that region was originally empty (name contains "_e0" or "_e1"
#     or "ce0" or "fe0" or "oe0" or "pe0") vs original faction territory

# ── REPORT FORMAT ──────────────────────────────────────────────────────

def print_report(ownership_changes, region_snapshots, breakaway_origins, tick_count):
    """
    ownership_changes: {region_id: [(tick, old_faction, new_faction, cause), ...]}
    region_snapshots:  {region_id: [(tick, tension, economy, military, pop), ...]}
    breakaway_origins: [(tick, breakaway_id, region_id, region_was_empty)]
    """

    print("\n" + "=" * 80)
    print("  REGION AUTOPSY REPORT")
    print("=" * 80)

    # ── SECTION A: Ownership change frequency per region ───────────────
    print("\n── A. OWNERSHIP CHANGES PER REGION ─────────────────────────")
    print(f"  {'Region':<25} {'Changes':>8} {'Rate/100t':>10} {'MinGap':>7} {'MaxGap':>7} {'MeanGap':>8} {'MedianGap':>10}")
    print(f"  {'-'*25} {'--------':>8} {'----------':>10} {'-------':>7} {'-------':>7} {'--------':>8} {'----------':>10}")

    for rid in sorted(ownership_changes.keys()):
        changes = ownership_changes[rid]
        n = len(changes)
        rate = n / tick_count * 100

        if n >= 2:
            gaps = [changes[i+1][0] - changes[i][0] for i in range(n-1)]
            min_gap = min(gaps)
            max_gap = max(gaps)
            mean_gap = sum(gaps) / len(gaps)
            sorted_gaps = sorted(gaps)
            median_gap = sorted_gaps[len(sorted_gaps)//2]
        else:
            min_gap = max_gap = mean_gap = median_gap = 0

        print(f"  {rid:<25} {n:>8} {rate:>10.1f} {min_gap:>7} {max_gap:>7} {mean_gap:>8.1f} {median_gap:>10}")

    # ── SECTION B: Ownership timeline for worst hotspots ───────────────
    print("\n── B. OWNERSHIP TIMELINE (worst 3 regions by churn) ────────")
    worst = sorted(ownership_changes.keys(), key=lambda r: len(ownership_changes[r]), reverse=True)[:3]

    for rid in worst:
        changes = ownership_changes[rid]
        print(f"\n  {rid} ({len(changes)} changes):")
        print(f"    {'Tick':>5} {'Old Faction':<30} {'New Faction':<30} {'Cause':<15}")
        print(f"    {'-----':>5} {'-'*30} {'-'*30} {'-'*15}")
        for tick, old_f, new_f, cause in changes[:30]:  # cap at 30 to avoid flooding
            old_short = (old_f or 'None')[:30]
            new_short = (new_f or 'None')[:30]
            print(f"    {tick:>5} {old_short:<30} {new_short:<30} {cause:<15}")
        if len(changes) > 30:
            print(f"    ... and {len(changes) - 30} more changes")

    # ── SECTION C: Tension trajectory for flatlined regions ────────────
    print("\n── C. TENSION TRAJECTORY (region_e1 — worst offender) ──────")
    # Show tension at sampled ticks
    target = "region_e1"
    if target in region_snapshots:
        snaps = region_snapshots[target]
        sample_ticks = list(range(0, tick_count, 25))  # every 25 ticks
        print(f"  {'Tick':>5} {'Tension':>8} {'Economy':>8} {'Military':>8} {'Pop':>8}")
        print(f"  {'-----':>5} {'--------':>8} {'--------':>8} {'--------':>8} {'--------':>8}")
        for s in snaps:
            if s[0] in sample_ticks:
                print(f"  {s[0]:>5} {s[1]:>8.1f} {s[2]:>8.1f} {s[3]:>8.1f} {s[4]:>8.1f}")

    # ── SECTION D: Breakaway origins — empty vs real territory ─────────
    print("\n── D. BREAKAWAY SPAWN ORIGINS ──────────────────────────────")
    from_empty = [b for b in breakaway_origins if b[3]]
    from_real = [b for b in breakaway_origins if not b[3]]
    print(f"  Total breakaways: {len(breakaway_origins)}")
    print(f"  From former-empty regions: {len(from_empty)} ({len(from_empty)/max(1,len(breakaway_origins)):.0%})")
    print(f"  From original faction territory: {len(from_real)} ({len(from_real)/max(1,len(breakaway_origins)):.0%})")

    if from_empty:
        print(f"\n  Former-empty region breakdown:")
        from collections import Counter
        empty_counts = Counter(b[2] for b in from_empty)
        for rid, count in empty_counts.most_common():
            print(f"    {rid}: {count} breakaways")

    # ── SECTION E: Zombie faction analysis ─────────────────────────────
    print("\n── E. ZOMBIE FACTION ANALYSIS ──────────────────────────────")
    print("  (Factions that existed 100+ ticks but never attacked)")
    # This needs to be populated from agent decision data
    print("  (Populate from Section 11 of bible_diagnostic — count breakaways")
    print("   with 100% accumulate that survived > 100 ticks)")

    # ── SECTION F: Which border friction implementation is active? ─────
    print("\n── F. BORDER FRICTION CODE PATH ────────────────────────────")
    print("  There are TWO border friction implementations in the codebase:")
    print("  1. tick.py _apply_border_friction() — FLAT per hostile neighbor")
    print("  2. border_friction.py run_border_friction() — SCALES by neighbor military")
    print()
    print("  Which one is being called during the tick loop?")
    print("  Search tick.py for which function is called in the friction step.")
    print("  If border_friction.py is active, friction on a region next to")
    print("  a neighbor with military=80 is 4x stronger than next to military=20.")
    print("  This would explain why some regions have extreme tension while")
    print("  others with the same number of hostile neighbors are fine.")


# ── IMPLEMENTATION NOTES FOR CLAUDE CODE ──────────────────────────────
#
# To populate ownership_changes:
#   - Each tick, for each region, compare current faction_id to previous tick
#   - If changed, record (tick, old_faction, new_faction, cause)
#   - "cause" should be: "conquest", "colonization", "revolt", "admin_revolt",
#     or "reversion" — check the tick log for which event caused the change
#
# To populate region_snapshots:
#   - Each tick, for target regions, record (tick, tension, economy, military, pop)
#
# To populate breakaway_origins:
#   - When a new faction appears in the registry, record which region it spawned from
#   - Mark whether that region's ID contains an "empty region" marker
#     (the template names empty regions with patterns like "region_e0", "region_e1",
#     "region_ce0", "region_fe0", "region_oe0", "region_pe0")
#
# CRITICAL: Section F asks you to verify which border friction code path
# is actually executing. Read the tick loop and confirm. If border_friction.py
# is the active path, that's a significant finding — it means friction is
# military-weighted, not flat, which the config values don't reflect.

if __name__ == "__main__":
    print("Region Autopsy — adapt imports and run via Claude Code")
    print("See implementation notes at bottom of file")
