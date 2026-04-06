"""
bible_diagnostic.py — Bible-vs-Simulation Sanity Check
=======================================================
Run from the project root:  python3 bible_diagnostic.py

This script runs the simulation and collects every metric needed to evaluate
whether the sim produces the experience described in the game bible.
It prints a full report at the end. No modifications to sim code required.

If imports fail, update the import block below to match your project layout.
"""

import sys, os, math, collections, json

# ── IMPORT BLOCK — update these if your layout differs ──────────────────
# Try common layouts. Claude Code: adjust if needed.
try:
    import config
    from tick import run_tick  # or whatever your tick entry point is
    from world_gen import generate_world  # or template loader
    from faction import Faction
except ImportError as e:
    print(f"Import failed: {e}")
    print("Please adjust the import block at the top of bible_diagnostic.py")
    print("I need access to: config, tick loop, world generation, faction model")
    sys.exit(1)

# ── CONFIGURATION ───────────────────────────────────────────────────────
TICKS = 500
SEED = 1
SCENARIO = "05_full_stack"  # adjust to whichever scenario you want to diagnose

# ── HELPERS ─────────────────────────────────────────────────────────────

def safe_mean(vals):
    return sum(vals) / len(vals) if vals else 0.0

def safe_median(vals):
    if not vals:
        return 0.0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2

# ── DATA COLLECTORS ─────────────────────────────────────────────────────

class DiagnosticCollector:
    """Hooks into each tick and records everything we need."""

    def __init__(self):
        # Per-tick snapshots
        self.faction_region_counts = []     # [{faction_id: count}, ...]
        self.faction_budgets = []           # [{faction_id: budget}, ...]
        self.region_snapshots = []          # [{region_id: {mil, eco, ten, pop}}, ...]

        # Event counters
        self.conquests = []                 # [(tick, attacker_id, defender_id, region_id)]
        self.colonizations = []             # [(tick, faction_id, region_id)]
        self.tension_revolts = []           # [(tick, faction_id, region_id)]
        self.admin_revolts = []             # [(tick, faction_id, region_id)]
        self.attacks = []                   # [(tick, attacker_id, target_region, outcome, net_force, committed)]
        self.faction_births = []            # [(tick, faction_id, archetype, parent_id_or_None)]
        self.faction_deaths = []            # [(tick, faction_id)]

        # Agent decision tracking
        self.agent_decisions = []           # [(tick, faction_id, decision_type, details)]

        # Colonization vs attack scoring (first 100 ticks)
        self.early_scoring = []             # [(tick, faction_id, best_colonize_score, best_attack_score)]

        # Border friction tracking
        self.border_friction_applied = []   # [(tick, region_id, hostile_neighbor_count)]

        # Breakaway viability
        self.breakaway_spawns = []          # [(tick, faction_id, mil, eco, ten, pop)]

    def snapshot_tick(self, tick, world, factions, event_log_this_tick=None):
        """Call this AFTER each tick resolves. Adapt parameter names to your sim."""
        # Region snapshots
        rsnap = {}
        for r in world.regions:  # adapt to your region iteration
            rsnap[r.id] = {
                'mil': r.military,
                'eco': r.economy,
                'ten': r.tension,  # or r.factional_tension
                'pop': r.population,
                'faction': r.faction_id,
                'tier': getattr(r, 'tier', 'unknown'),
            }
        self.region_snapshots.append(rsnap)

        # Faction snapshots
        frc = {}
        fbudget = {}
        for f in factions:
            regions_owned = [r for r in world.regions if r.faction_id == f.id]
            frc[f.id] = len(regions_owned)
            fbudget[f.id] = f.budget
        self.faction_region_counts.append(frc)
        self.faction_budgets.append(fbudget)

    def record_conquest(self, tick, attacker_id, defender_id, region_id):
        self.conquests.append((tick, attacker_id, defender_id, region_id))

    def record_colonization(self, tick, faction_id, region_id):
        self.colonizations.append((tick, faction_id, region_id))

    def record_attack(self, tick, attacker_id, target_region, outcome, net_force, committed):
        self.attacks.append((tick, attacker_id, target_region, outcome, net_force, committed))

    def record_revolt(self, tick, faction_id, region_id, revolt_type="tension"):
        if revolt_type == "admin":
            self.admin_revolts.append((tick, faction_id, region_id))
        else:
            self.tension_revolts.append((tick, faction_id, region_id))

    def record_faction_birth(self, tick, faction_id, archetype, parent_id=None):
        self.faction_births.append((tick, faction_id, archetype, parent_id))

    def record_faction_death(self, tick, faction_id):
        self.faction_deaths.append((tick, faction_id))

    def record_agent_decision(self, tick, faction_id, decision, details=None):
        self.agent_decisions.append((tick, faction_id, decision, details))

    def record_breakaway_spawn(self, tick, faction_id, mil, eco, ten, pop):
        self.breakaway_spawns.append((tick, faction_id, mil, eco, ten, pop))


# ── REPORT GENERATION ───────────────────────────────────────────────────

def print_report(collector, ticks_run, config_module):
    c = collector
    print("\n" + "=" * 80)
    print("  BIBLE DIAGNOSTIC REPORT")
    print(f"  {ticks_run} ticks, seed {SEED}")
    print("=" * 80)

    # ── SECTION 1: Config Dump (the tuning knobs) ──────────────────────
    print("\n── 1. KEY CONFIG VALUES ──────────────────────────────────────")
    config_keys = [
        # Budget & attack
        'BUDGET_GROWTH_RATE', 'REGION_MAINTENANCE_COST', 'COMMIT_FRACTION',
        'ATTACK_EFFICIENCY', 'RESISTANCE_FACTOR', 'BREAKTHROUGH_THRESHOLD',
        'CONQUEST_THRESHOLD', 'GARRISON_FRACTION', 'SURPRISE_EFFICIENCY',
        # Colonization
        'COLONIZE_COST', 'COLONY_START_MILITARY', 'COLONY_START_ECONOMY',
        'COLONY_START_TENSION', 'COLONY_START_POPULATION',
        # Reinforcement
        'REINFORCE_EFFICIENCY', 'REINFORCE_MAX_FRACTION',
        # Drift rates
        'MILITARY_DECAY_RATE', 'RECRUITMENT_RATE', 'RECRUITMENT_BASELINE',
        'RECRUITMENT_THRESHOLD', 'RECRUITMENT_CEILING',
        'BASE_ECON_GROWTH', 'TENSION_ECONOMY_RATE', 'TENSION_DECAY_RATE',
        'TENSION_ECONOMY_MIDPOINT', 'POPULATION_GROWTH_RATE',
        'SUBSISTENCE_THRESHOLD', 'ECONOMY_FLOOR',
        # Border friction
        'BORDER_FRICTION_TENSION', 'BORDER_FRICTION_ECONOMY',
        # Oscillation
        'ECON_OSCILLATION_AMPLITUDE', 'ECON_OSCILLATION_PERIOD',
        # Admin revolts
        'ADMIN_REVOLT_BASE_RATE', 'ADMIN_REVOLT_SCALING_RATE',
        'ADMIN_REVOLT_INFLECTION_POINT',
        # Revolt
        'REVOLT_BASE_PROBABILITY', 'REVOLT_TENSION_EXPONENT',
        # Tech
        'TECH_GROWTH_RATE', 'TECH_CONVERGENCE_RATE',
        # Entrenchment
        'ENTRENCHMENT_BASE', 'ENTRENCHMENT_MAX', 'ENTRENCHMENT_RAMP_TICKS',
        # Capacity caps
        'HOME_MILITARY_CAP', 'FRONTIER_MILITARY_CAP',
        # Archetype weights (if accessible)
        'ARCHETYPE_CONFIGS',
    ]
    for key in config_keys:
        val = getattr(config_module, key, '(not found)')
        if isinstance(val, dict):
            print(f"  {key}:")
            for k, v in val.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key} = {val}")

    # ── SECTION 2: Starting World ──────────────────────────────────────
    print("\n── 2. STARTING WORLD (tick 0 snapshot) ───────────────────────")
    if c.region_snapshots:
        t0 = c.region_snapshots[0]
        empty_count = sum(1 for r in t0.values() if r['faction'] is None)
        inhabited = {rid: r for rid, r in t0.items() if r['faction'] is not None}
        print(f"  Total regions: {len(t0)}")
        print(f"  Empty regions at start: {empty_count}")
        print(f"  Inhabited regions at start: {len(inhabited)}")
        print(f"  Empty fraction: {empty_count / len(t0):.1%}")
        print()

        # Per-faction starting state
        factions_t0 = collections.defaultdict(list)
        for rid, r in t0.items():
            if r['faction']:
                factions_t0[r['faction']].append(r)

        print(f"  {'Faction':<25} {'Rgns':>4} {'Mil':>6} {'Eco':>6} {'Ten':>6} {'Pop':>6} {'Tier':<10}")
        print(f"  {'-'*25} {'----':>4} {'------':>6} {'------':>6} {'------':>6} {'------':>6} {'----------':<10}")
        for fid, regions in sorted(factions_t0.items()):
            mil = safe_mean([r['mil'] for r in regions])
            eco = safe_mean([r['eco'] for r in regions])
            ten = safe_mean([r['ten'] for r in regions])
            pop = safe_mean([r['pop'] for r in regions])
            tiers = ', '.join(set(str(r['tier']) for r in regions))
            print(f"  {fid:<25} {len(regions):>4} {mil:>6.1f} {eco:>6.1f} {ten:>6.1f} {pop:>6.1f} {tiers:<10}")

    # ── SECTION 3: Event Timeline ──────────────────────────────────────
    print("\n── 3. EVENT TIMELINE ─────────────────────────────────────────")

    # First events of each type
    if c.colonizations:
        print(f"  First colonization: tick {c.colonizations[0][0]} by {c.colonizations[0][1]}")
    else:
        print(f"  First colonization: NEVER (0 colonizations in {ticks_run} ticks)")

    if c.attacks:
        print(f"  First attack: tick {c.attacks[0][0]} by {c.attacks[0][1]}")
    else:
        print(f"  First attack: NEVER")

    if c.conquests:
        print(f"  First conquest: tick {c.conquests[0][0]} by {c.conquests[0][1]}")
    else:
        print(f"  First conquest: NEVER")

    if c.tension_revolts:
        print(f"  First tension revolt: tick {c.tension_revolts[0][0]}")
    if c.admin_revolts:
        print(f"  First admin revolt: tick {c.admin_revolts[0][0]}")

    # Colonization vs attack ratio over time windows
    print()
    windows = [(0, 50), (0, 100), (0, 200), (200, 500)]
    print(f"  {'Window':<12} {'Coloniz':>8} {'Attacks':>8} {'Conquests':>10} {'T-Revolts':>10} {'A-Revolts':>10} {'Col:Atk':>8}")
    print(f"  {'-'*12} {'--------':>8} {'--------':>8} {'----------':>10} {'----------':>10} {'----------':>10} {'--------':>8}")
    for t0, t1 in windows:
        cols = len([x for x in c.colonizations if t0 <= x[0] < t1])
        atks = len([x for x in c.attacks if t0 <= x[0] < t1])
        cons = len([x for x in c.conquests if t0 <= x[0] < t1])
        trev = len([x for x in c.tension_revolts if t0 <= x[0] < t1])
        arev = len([x for x in c.admin_revolts if t0 <= x[0] < t1])
        ratio = f"{cols}:{atks}" if atks > 0 else f"{cols}:0"
        print(f"  {f'{t0}-{t1}':<12} {cols:>8} {atks:>8} {cons:>10} {trev:>10} {arev:>10} {ratio:>8}")

    # ── SECTION 4: Faction Lifespans ───────────────────────────────────
    print("\n── 4. FACTION LIFESPANS ──────────────────────────────────────")

    # Track when each faction first and last had regions
    all_faction_ids = set()
    for snap in c.faction_region_counts:
        all_faction_ids.update(snap.keys())

    print(f"  {'Faction':<30} {'Born':>5} {'Died':>5} {'Peak':>5} {'PeakTk':>7} {'Lifespan':>9}")
    print(f"  {'-'*30} {'-----':>5} {'-----':>5} {'-----':>5} {'-------':>7} {'---------':>9}")
    for fid in sorted(all_faction_ids):
        first_tick = None
        last_tick = None
        peak = 0
        peak_tick = 0
        for t, snap in enumerate(c.faction_region_counts):
            count = snap.get(fid, 0)
            if count > 0:
                if first_tick is None:
                    first_tick = t
                last_tick = t
                if count > peak:
                    peak = count
                    peak_tick = t
        born = first_tick if first_tick is not None else '?'
        died_tick = last_tick + 1 if last_tick is not None and last_tick < ticks_run - 1 else 'alive'
        lifespan = (last_tick - first_tick + 1) if first_tick is not None else 0
        print(f"  {str(fid):<30} {str(born):>5} {str(died_tick):>5} {peak:>5} {peak_tick:>7} {lifespan:>9}")

    # ── SECTION 5: Budget Trajectory ───────────────────────────────────
    print("\n── 5. BUDGET TRAJECTORY (original factions) ──────────────────")
    # Show budget at key ticks for original factions
    orig_factions = set()
    if c.faction_region_counts:
        orig_factions = set(c.faction_region_counts[0].keys())

    sample_ticks = [0, 10, 25, 50, 100, 200, 300, 500]
    sample_ticks = [t for t in sample_ticks if t < ticks_run]

    header = f"  {'Faction':<20}" + "".join(f"{'t='+str(t):>8}" for t in sample_ticks)
    print(header)
    print(f"  {'-'*20}" + "--------" * len(sample_ticks))
    for fid in sorted(orig_factions, key=str):
        row = f"  {str(fid):<20}"
        for t in sample_ticks:
            if t < len(c.faction_budgets):
                val = c.faction_budgets[t].get(fid, None)
                row += f"{val:>8.1f}" if val is not None else f"{'dead':>8}"
            else:
                row += f"{'?':>8}"
        print(row)

    # ── SECTION 6: Tension Equilibrium Analysis ────────────────────────
    print("\n── 6. TENSION ANALYSIS ──────────────────────────────────────")
    # For each region that survives 100+ ticks, compute tension stats
    if len(c.region_snapshots) > 100:
        # Get regions that exist in last snapshot
        final_snap = c.region_snapshots[-1]
        for rid in sorted(final_snap.keys()):
            tensions = []
            for t in range(max(0, len(c.region_snapshots) - 200), len(c.region_snapshots)):
                snap = c.region_snapshots[t]
                if rid in snap and snap[rid]['faction'] is not None:
                    tensions.append(snap[rid]['ten'])
            if len(tensions) > 50:
                print(f"  Region {rid} (last 200 ticks): "
                      f"mean={safe_mean(tensions):.1f}, "
                      f"min={min(tensions):.1f}, max={max(tensions):.1f}, "
                      f"range={max(tensions)-min(tensions):.1f}")

    # ── SECTION 7: Border Friction Impact ──────────────────────────────
    print("\n── 7. BORDER FRICTION IMPACT ────────────────────────────────")
    bf_tension = getattr(config_module, 'BORDER_FRICTION_TENSION', '?')
    bf_economy = getattr(config_module, 'BORDER_FRICTION_ECONOMY', '?')
    print(f"  Per-hostile-neighbor per-tick: tension +{bf_tension}, economy -{bf_economy}")
    # Count hostile borders at tick 0 and tick 100
    for check_tick in [0, min(100, ticks_run - 1)]:
        if check_tick < len(c.region_snapshots):
            snap = c.region_snapshots[check_tick]
            regions_with_hostile = 0
            max_hostile = 0
            for rid, r in snap.items():
                if r['faction'] is not None:
                    # We'd need adjacency info — print what we can
                    regions_with_hostile += 1  # placeholder
            print(f"  (Need adjacency data to compute hostile border counts at tick {check_tick})")

    # ── SECTION 8: Attack Outcome Distribution ─────────────────────────
    print("\n── 8. ATTACK OUTCOME DISTRIBUTION ──────────────────────────")
    if c.attacks:
        outcomes = collections.Counter(a[3] for a in c.attacks)
        total = len(c.attacks)
        for outcome, count in sorted(outcomes.items()):
            print(f"  {outcome}: {count} ({count/total:.1%})")

        # Net force distribution
        net_forces = [a[4] for a in c.attacks if a[4] is not None]
        if net_forces:
            print(f"\n  Net force stats: mean={safe_mean(net_forces):.2f}, "
                  f"median={safe_median(net_forces):.2f}, "
                  f"min={min(net_forces):.2f}, max={max(net_forces):.2f}")

        # Committed budget distribution
        commits = [a[5] for a in c.attacks if a[5] is not None]
        if commits:
            print(f"  Committed budget: mean={safe_mean(commits):.2f}, "
                  f"median={safe_median(commits):.2f}, "
                  f"min={min(commits):.2f}, max={max(commits):.2f}")
    else:
        print("  No attacks recorded.")

    # ── SECTION 9: Colonization Scoring (WHY isn't colonization happening?) ─
    print("\n── 9. COLONIZE vs ATTACK SCORING (first 50 ticks) ──────────")
    if c.early_scoring:
        for tick, fid, col_score, atk_score in c.early_scoring[:20]:
            winner = "COLONIZE" if col_score > atk_score else "ATTACK"
            print(f"  t={tick:>3} {str(fid):<15} col={col_score:>6.3f} atk={atk_score:>6.3f} → {winner}")
    else:
        print("  (No scoring data collected — see instrumentation notes below)")

    # ── SECTION 10: Breakaway Viability ────────────────────────────────
    print("\n── 10. BREAKAWAY SPAWN FIELD VALUES ─────────────────────────")
    if c.breakaway_spawns:
        print(f"  {'Tick':>5} {'Faction':<25} {'Mil':>6} {'Eco':>6} {'Ten':>6} {'Pop':>6}")
        print(f"  {'-----':>5} {'-'*25} {'------':>6} {'------':>6} {'------':>6} {'------':>6}")
        for tick, fid, mil, eco, ten, pop in c.breakaway_spawns[:15]:
            print(f"  {tick:>5} {str(fid):<25} {mil:>6.1f} {eco:>6.1f} {ten:>6.1f} {pop:>6.1f}")
        if len(c.breakaway_spawns) > 15:
            print(f"  ... and {len(c.breakaway_spawns) - 15} more")

        # Compare breakaway averages to original faction averages at same ticks
        ba_eco = safe_mean([s[3] for s in c.breakaway_spawns])
        ba_mil = safe_mean([s[2] for s in c.breakaway_spawns])
        print(f"\n  Breakaway spawn averages: mil={ba_mil:.1f}, eco={ba_eco:.1f}")
    else:
        print("  (No breakaway spawn data collected)")

    # ── SECTION 11: Agent Decision Distribution ────────────────────────
    print("\n── 11. AGENT DECISION DISTRIBUTION ─────────────────────────")
    if c.agent_decisions:
        by_faction = collections.defaultdict(lambda: collections.Counter())
        for tick, fid, decision, details in c.agent_decisions:
            by_faction[fid][decision] += 1

        for fid in sorted(by_faction.keys(), key=str):
            counts = by_faction[fid]
            total = sum(counts.values())
            parts = ", ".join(f"{k}={v} ({v/total:.0%})" for k, v in sorted(counts.items()))
            print(f"  {str(fid):<25}: {parts}")
    else:
        print("  (No agent decision data collected — see instrumentation notes)")

    # ── SECTION 12: Bible Compliance Checklist ─────────────────────────
    print("\n── 12. BIBLE COMPLIANCE CHECKLIST ──────────────────────────")
    checks = []

    # Check: Colonization exists
    col_count = len(c.colonizations)
    atk_count = len(c.attacks)
    if col_count == 0:
        checks.append(("FAIL", "Zero colonizations — expansion phase missing entirely"))
    elif col_count < 5:
        checks.append(("WARN", f"Only {col_count} colonizations vs {atk_count} attacks — expansion phase very weak"))
    else:
        checks.append(("OK", f"{col_count} colonizations vs {atk_count} attacks"))

    # Check: Original factions survive past tick 100
    orig_survive_100 = 0
    for fid in orig_factions:
        if len(c.faction_region_counts) > 100:
            if c.faction_region_counts[100].get(fid, 0) > 0:
                orig_survive_100 += 1
    if orig_survive_100 < len(orig_factions) * 0.5:
        checks.append(("WARN", f"Only {orig_survive_100}/{len(orig_factions)} original factions alive at tick 100"))
    else:
        checks.append(("OK", f"{orig_survive_100}/{len(orig_factions)} original factions alive at tick 100"))

    # Check: Tension not permanently maxed
    if c.region_snapshots:
        final = c.region_snapshots[-1]
        high_tension = sum(1 for r in final.values() if r['faction'] and r['ten'] > 90)
        total_inhabited = sum(1 for r in final.values() if r['faction'])
        if high_tension > total_inhabited * 0.5:
            checks.append(("WARN", f"{high_tension}/{total_inhabited} regions above tension 90 at final tick"))
        else:
            checks.append(("OK", f"{high_tension}/{total_inhabited} regions above tension 90"))

    # Check: Admin revolts firing for large factions (J1)
    # Check: No total dominance sustained (J5)
    for t, snap in enumerate(c.faction_region_counts):
        total_regions = sum(snap.values())
        for fid, count in snap.items():
            if count == total_regions and total_regions > 1:
                # Check if dominance persists 200 ticks
                persists = True
                for t2 in range(t, min(t + 200, len(c.faction_region_counts))):
                    s2 = c.faction_region_counts[t2]
                    if len([f for f, c2 in s2.items() if c2 > 0]) > 1:
                        persists = False
                        break
                if persists:
                    checks.append(("FAIL", f"J5 VIOLATION: {fid} held all {total_regions} regions for 200+ ticks starting tick {t}"))
                break

    # Check: Multiple factions alive at end (J10 variant)
    if c.faction_region_counts:
        final_factions = sum(1 for f, count in c.faction_region_counts[-1].items() if count > 0)
        if final_factions < 2:
            checks.append(("FAIL", f"Only {final_factions} faction(s) alive at end"))
        else:
            checks.append(("OK", f"{final_factions} factions alive at end"))

    # Check: Admin revolts completing (J3)
    admin_chain_starts = len(c.admin_revolts)
    admin_breakaways = len([b for b in c.faction_births if b[3] is not None])  # has parent = breakaway
    if admin_chain_starts > 0:
        completion = admin_breakaways / admin_chain_starts if admin_chain_starts > 0 else 0
        if completion < 0.9:
            checks.append(("WARN", f"Admin revolt completion rate: {completion:.0%} ({admin_breakaways}/{admin_chain_starts})"))
        else:
            checks.append(("OK", f"Admin revolt completion: {admin_breakaways}/{admin_chain_starts}"))

    # Print checklist
    for status, msg in checks:
        icon = {"OK": "✓", "WARN": "⚠", "FAIL": "✗"}[status]
        print(f"  {icon} [{status}] {msg}")

    # ── SECTION 13: Instrumentation Gaps ───────────────────────────────
    print("\n── 13. INSTRUMENTATION NOTES ────────────────────────────────")
    print("""
  This script needs hooks in your tick loop to collect data. If sections
  above show "(No data collected)", add these calls:

  In tick.py (or wherever attacks resolve):
    collector.record_attack(tick, attacker.id, target_region.id, outcome, net_force, committed_budget)

  In tick.py (where conquests fire):
    collector.record_conquest(tick, attacker.id, defender.id, region.id)

  In tick.py (where colonizations fire):
    collector.record_colonization(tick, faction.id, region.id)

  In tick.py (where agent makes its decision):
    collector.record_agent_decision(tick, faction.id, decision_type, {details})

  In faction.py (agent scoring, first 50 ticks only):
    collector.record_early_scoring(tick, faction.id, best_colonize_score, best_attack_score)

  In faction.py (breakaway creation):
    collector.record_breakaway_spawn(tick, new_faction.id, region.military, region.economy, ...)

  In tick.py (revolt events):
    collector.record_revolt(tick, faction.id, region.id, "tension" or "admin")

  In faction.py (faction dies):
    collector.record_faction_death(tick, faction.id)

  In faction.py (faction born):
    collector.record_faction_birth(tick, faction.id, archetype, parent_id)

  ALTERNATIVE: If you already have an event_log that stores all this,
  adapt the report functions to read from event_log instead.
  """)


# ── MAIN — OPTION A: Use sim_tuner / existing test infrastructure ──────

def run_via_existing_infra():
    """
    If you have sim_tuner.py or a similar runner, this adapts to it.
    Claude Code: try this first. If it doesn't work, use Option B.
    """
    try:
        from sim_tuner import run_scenario
        print("Found sim_tuner.run_scenario — running scenario...")
        # You'll need to adapt this to however run_scenario works
        # and hook the collector in
        result = run_scenario(SCENARIO)
        print("Scenario completed. Adapt collector hooks to extract data.")
        return result
    except ImportError:
        return None


# ── MAIN — OPTION B: Minimal standalone runner ─────────────────────────

def run_standalone():
    """
    Direct tick loop. Adapt to your actual sim API.
    """
    import random
    random.seed(SEED)

    # Generate world — adapt to your actual function signature
    world = generate_world(template="full_stack")  # or whatever template name

    # Get initial factions
    factions = world.factions  # adapt

    collector = DiagnosticCollector()

    for tick in range(TICKS):
        # Snapshot before events
        # Run one tick — adapt to your tick function signature
        run_tick(tick, world, factions)

        # Snapshot after tick
        collector.snapshot_tick(tick, world, factions)

        # You'll need to hook event recording into your tick loop
        # See instrumentation notes in the report

    print_report(collector, TICKS, config)


# ── ENTRY POINT ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Bible Diagnostic — Ouroboros Manifold")
    print("=" * 40)
    print()
    print("This script needs to be adapted to your project's import structure.")
    print("Claude Code: read the import block and the run_standalone() function,")
    print("then adapt them to match the actual file/function names in the project.")
    print()
    print("Once adapted, it will produce a 13-section diagnostic report covering:")
    print("  1. Key config values (all tuning knobs)")
    print("  2. Starting world (empty regions, faction placement)")
    print("  3. Event timeline (first colonize/attack/conquest/revolt + time windows)")
    print("  4. Faction lifespans (born, died, peak territory)")
    print("  5. Budget trajectory (budget at sampled ticks)")
    print("  6. Tension equilibrium (per-region tension stats)")
    print("  7. Border friction impact")
    print("  8. Attack outcome distribution (breakthrough/contested/repelled)")
    print("  9. Colonize vs attack scoring (why factions choose attack over expand)")
    print("  10. Breakaway spawn field values (are viability buffs too generous?)")
    print("  11. Agent decision distribution (accumulate/attack/colonize ratios)")
    print("  12. Bible compliance checklist")
    print("  13. Instrumentation gaps")
    print()

    # Try existing infrastructure first
    result = run_via_existing_infra()
    if result is None:
        print("sim_tuner not found — trying standalone runner...")
        try:
            run_standalone()
        except Exception as e:
            print(f"\nStandalone runner failed: {e}")
            print("Claude Code: adapt the imports and runner to your project layout,")
            print("then re-run. The report template and collector are ready to go.")
