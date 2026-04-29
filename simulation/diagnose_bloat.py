#!/usr/bin/env python3
"""Diagnostic script: why can a faction hold 30+ regions in a 50-region world?

Runs a 500-tick simulation and tracks:
  1. Territory count per faction per tick
  2. Admin revolts initiated vs completed (breakaway created)
  3. What happens to each breakaway (absorbed back to parent? conquered? survived?)
  4. Budget trajectory of the dominant faction
  5. Zombie absorptions — who absorbs whom
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import random
import config
import world as world_mod
import faction as faction_mod
import events as _events
import tick as _tick

config.DIAGNOSTIC_PRINTS = False

TICKS = 2000
SEEDS = [42, 7, 13, 99, 123, 256, 314, 555, 777, 1000, 2025, 3141, 6789, 8888, 9999]

print("=" * 70)
print("EMPIRE BLOAT DIAGNOSTIC — MULTI-SEED SCAN")
print("=" * 70)

worst_seed = None
worst_peak = 0
worst_fid = None

for SEED in SEEDS:
    _events.reset_chain_counter()
    w = world_mod.generate_random(seed=SEED)
    factions = faction_mod.generate_starting_factions(rng=w.rng, world=w)
    registry = faction_mod.make_registry(*factions)

    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    pending_queue = _events.PendingQueue()
    trigger_state = {}
    pending_telegraphs = []

    peak_territory = {}
    breakaway_fates = {}
    breakaway_parent = {}
    admin_revolt_initiated = 0
    zombie_absorptions = []
    territory_timeline = {}  # {fid: [count_at_t25, count_at_t50, ...]}

    for t in range(1, TICKS + 1):
        log = _tick.run_tick(
            w, t, ledger=None,
            pending_queue=pending_queue, noise_offsets=noise_offsets,
            trigger_state=trigger_state, registry=registry,
            pending_telegraphs=pending_telegraphs,
        )

        for fid in list(registry.keys()):
            owned = len(w.regions_by_faction(fid))
            if fid not in peak_territory or owned > peak_territory[fid]:
                peak_territory[fid] = owned

        for ar in log.get("admin_revolts", []):
            admin_revolt_initiated += 1

        for rev in log.get("revolts", []):
            if rev["type"] == "revolt":
                breakaway_parent[rev["new_faction"]] = rev["original_faction"]
                breakaway_fates[rev["new_faction"]] = "alive"

        for ab in log.get("factions_absorbed", []):
            zombie_absorptions.append(ab)
            dead_fid = ab["faction"]
            absorber = ab.get("absorbed_by")
            if dead_fid in breakaway_parent:
                parent = breakaway_parent[dead_fid]
                if absorber == parent:
                    breakaway_fates[dead_fid] = "absorbed_by_parent"
                elif absorber is not None:
                    breakaway_fates[dead_fid] = "absorbed_by_other"
                else:
                    breakaway_fates[dead_fid] = "dissolved"

        # Record territory at intervals for the 4 starting factions
        if t % 25 == 0:
            for fid in ["player", "conqueror", "fortifier", "opportunist"]:
                territory_timeline.setdefault(fid, []).append(len(w.regions_by_faction(fid)))

    # Summary for this seed
    top_peak_fid = max(peak_territory, key=peak_territory.get)
    top_peak = peak_territory[top_peak_fid]
    n_regions = len(w.regions)

    fate_counts = {}
    for fate in breakaway_fates.values():
        fate_counts[fate] = fate_counts.get(fate, 0) + 1
    absorbed_back = fate_counts.get("absorbed_by_parent", 0)
    total_breakaways = len(breakaway_fates)
    back_pct = (100 * absorbed_back / total_breakaways) if total_breakaways > 0 else 0

    print(f"\nseed={SEED:>4}  regions={n_regions}  peak={top_peak:>2} by {top_peak_fid:<20}"
          f"  admin_revolts={admin_revolt_initiated:>3}"
          f"  breakaways={total_breakaways:>3}  absorbed_back={absorbed_back} ({back_pct:.0f}%)")

    # Show timeline of the peak faction
    timeline = territory_timeline.get(top_peak_fid, [])
    if not timeline and top_peak_fid.startswith("breakaway_"):
        # For breakaways, just show peak
        pass
    else:
        ticks_labels = list(range(25, TICKS + 1, 25))
        bars = "  timeline: " + " ".join(f"{c:>2}" for c in timeline)
        print(bars)

    if top_peak > worst_peak:
        worst_peak = top_peak
        worst_seed = SEED
        worst_fid = top_peak_fid

print(f"\n{'=' * 70}")
print(f"WORST CASE: seed={worst_seed}, peak={worst_peak} regions by {worst_fid}")
print(f"{'=' * 70}")

# ── Over-10 duration analysis across ALL seeds ──
print(f"\n{'=' * 70}")
print("OVER-10 DURATION ANALYSIS")
print(f"{'=' * 70}")

for SEED in SEEDS:
    _events.reset_chain_counter()
    w = world_mod.generate_random(seed=SEED)
    factions = faction_mod.generate_starting_factions(rng=w.rng, world=w)
    registry = faction_mod.make_registry(*factions)

    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    pending_queue = _events.PendingQueue()
    trigger_state = {}
    pending_telegraphs = []

    over10_stretches = {}
    current_stretch = {}

    for t in range(1, TICKS + 1):
        log = _tick.run_tick(
            w, t, ledger=None,
            pending_queue=pending_queue, noise_offsets=noise_offsets,
            trigger_state=trigger_state, registry=registry,
            pending_telegraphs=pending_telegraphs,
        )

        for fid in list(registry.keys()):
            count = len(w.regions_by_faction(fid))
            if count > 10:
                if fid not in current_stretch:
                    current_stretch[fid] = (t, count)
                else:
                    start, peak = current_stretch[fid]
                    current_stretch[fid] = (start, max(peak, count))
            else:
                if fid in current_stretch:
                    start, peak = current_stretch[fid]
                    over10_stretches.setdefault(fid, []).append((start, t - 1, peak))
                    del current_stretch[fid]

    for fid, (start, peak) in current_stretch.items():
        over10_stretches.setdefault(fid, []).append((start, TICKS, peak))

    all_stretches = []
    for fid, stretches in over10_stretches.items():
        for s_start, s_end, s_peak in stretches:
            duration = s_end - s_start + 1
            all_stretches.append((SEED, fid, s_start, s_end, duration, s_peak))

    if all_stretches:
        all_stretches.sort(key=lambda x: -x[4])
        print(f"\nseed={SEED}  ({len(w.regions)} regions)")
        for _, fid, s_start, s_end, dur, peak in all_stretches[:8]:
            archetype = registry[fid].archetype if fid in registry else "dead"
            print(f"  {fid:<35} t={s_start:>4}-{s_end:>4}  duration={dur:>4} ticks  peak={peak:>2}  ({archetype})")
    else:
        print(f"\nseed={SEED}  ({len(w.regions)} regions)  — no faction ever exceeded 10")
