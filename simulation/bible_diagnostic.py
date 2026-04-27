"""
bible_diagnostic.py — Bible-vs-Simulation Sanity Check
=======================================================
Run from simulation/:  python3 bible_diagnostic.py

Adapted to Ouroboros project layout. Uses sim_validator.run_recorded_scenario()
for data collection, then produces the 13-section diagnostic report.
"""

import sys, os, math, collections, json

import config
import sim_validator as sv
import world as world_mod
import faction as faction_mod
import events as _events
import diplomacy as _diplomacy
import tick as _tick

TICKS = 500
SEED = 1

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


class DiagnosticCollector:
    """Hooks into each tick and records everything we need."""

    def __init__(self):
        self.faction_region_counts = []
        self.faction_budgets = []
        self.region_snapshots = []
        self.conquests = []
        self.colonizations = []
        self.tension_revolts = []
        self.admin_revolts = []
        self.attacks = []
        self.faction_births = []
        self.faction_deaths = []
        self.agent_decisions = []
        self.early_scoring = []
        self.border_friction_applied = []
        self.breakaway_spawns = []


def populate_from_trajectory(tlog):
    c = DiagnosticCollector()
    known_factions = set()

    for snap in tlog.snapshots:
        rsnap = {}
        for rid, rdata in snap.regions.items():
            rsnap[rid] = {
                'mil': rdata["fields"].get("military", 0),
                'eco': rdata["fields"].get("economy", 0),
                'ten': rdata["fields"].get("tension", 0),
                'pop': rdata["fields"].get("population", 0),
                'faction': rdata["faction_id"],
                'tier': rdata.get("tier", "unknown"),
            }
        c.region_snapshots.append(rsnap)

        frc = {}
        fbudget = {}
        for fid, fdata in snap.factions.items():
            frc[fid] = fdata["owned_region_count"]
            fbudget[fid] = fdata["budget"]
        c.faction_region_counts.append(frc)
        c.faction_budgets.append(fbudget)

        new_fids = set(snap.factions.keys()) - known_factions
        for nfid in new_fids:
            if known_factions:
                fdata = snap.factions[nfid]
                parent = None
                if "breakaway_" in nfid:
                    for rev in snap.events_fired:
                        if rev.get("creates_faction") and rev.get("region_id") in nfid:
                            parent = "event_chain"
                            break
                c.faction_births.append((snap.tick, nfid, fdata["archetype"], parent))
            known_factions.add(nfid)

        for a in snap.faction_actions:
            action_type = a.get("action")
            fid = a.get("faction_id")

            c.agent_decisions.append((snap.tick, fid, action_type, None))

            if action_type == "attack":
                outcome = a.get("outcome_band", "unknown")
                net = a.get("expected_outcome")
                committed = a.get("budget_committed", 0)
                target = a.get("target_region", "?")
                c.attacks.append((snap.tick, fid, target, outcome, net, committed))

            elif action_type == "colonize":
                target = a.get("target_region", "?")
                c.colonizations.append((snap.tick, fid, target))

        for con in snap.conquests:
            c.conquests.append((
                snap.tick,
                con.get("new_faction_id", "?"),
                con.get("old_faction_id", "?"),
                con.get("region_id", "?"),
            ))

        for evt in snap.events_fired:
            tid = evt.get("template_id", "")
            rid = evt.get("region_id", "?")
            if tid == "evt_revolt_entrenched":
                owner = snap.regions.get(rid, {}).get("faction_id", "?")
                c.tension_revolts.append((snap.tick, owner, rid))
            elif tid == "evt_admin_separatist":
                owner = snap.regions.get(rid, {}).get("faction_id", "?")
                c.admin_revolts.append((snap.tick, owner, rid))

            if evt.get("creates_faction"):
                region_data = snap.regions.get(rid)
                if region_data:
                    f = region_data["fields"]
                    c.breakaway_spawns.append((
                        snap.tick, rid,
                        f.get("military", 0), f.get("economy", 0),
                        f.get("tension", 0), f.get("population", 0),
                    ))

    prev_alive = set()
    for t, frc in enumerate(c.faction_region_counts):
        alive = {fid for fid, count in frc.items() if count > 0}
        died = prev_alive - alive
        for fid in died:
            c.faction_deaths.append((t, fid))
        prev_alive = alive

    return c


def collect_early_scoring(n_ticks=50, seed=SEED):
    """Run a short sim with debug=True on faction.decide() to capture scoring."""
    config.ENABLE_EVENTS = True
    config.ENABLE_FACTIONS = True
    config.ENABLE_BORDER_FRICTION = True
    config.ENABLE_RECRUITMENT = True
    config.ENABLE_ADJACENCY_BONUS = True
    config.ENABLE_OSCILLATION = True
    config.ENABLE_TECHNOLOGY = True
    config.ENABLE_DIPLOMACY = True
    config.ENABLE_ADMIN_REVOLTS = True
    config.DIAGNOSTIC_PRINTS = False

    w = world_mod.generate_random(seed=seed)
    factions = faction_mod.generate_starting_factions(rng=w.rng, world=w)
    registry = faction_mod.make_registry(*factions)
    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()
    stances = _diplomacy.init_stances(registry)
    pending_telegraphs = []

    scoring_log = []

    for t in range(1, n_ticks + 1):
        _tick.run_tick(
            w, t,
            pending_queue=pending_queue,
            noise_offsets=noise_offsets,
            trigger_state=trigger_state,
            registry=registry,
            stances=stances,
            pending_telegraphs=pending_telegraphs,
        )

        snapshot = {}
        for rid, r in w.regions.items():
            snapshot[rid] = {
                "faction_id": r.faction_id,
                "fields": dict(r.fields),
                "tier": r.tier,
            }

        for fac in list(registry.values()):
            owned = [rid for rid, rd in snapshot.items() if rd["faction_id"] == fac.id]
            if not owned:
                continue
            intent = fac.decide(snapshot, w.adjacency, registry, w.rng, t, debug=True)
            diag = intent.get("diag", {})

            best_col = diag.get("best_colonize")
            best_atk = diag.get("best_attack_any")
            weighted = diag.get("weighted_scores", {})

            col_score = weighted.get("colonize")
            atk_score = weighted.get("attack")

            scoring_log.append({
                "tick": t,
                "faction_id": fac.id,
                "archetype": fac.archetype,
                "budget": round(fac.budget, 2),
                "n_attack_candidates": diag.get("n_attack_candidates", 0),
                "n_colonize_candidates": diag.get("n_colonize_candidates", 0),
                "n_viable_attacks": diag.get("n_viable_attacks", 0),
                "potential_commit": diag.get("potential_commit", 0),
                "attack_confidence": diag.get("attack_confidence", 0),
                "effective_confidence": diag.get("effective_confidence", 0),
                "best_attack_rid": best_atk["rid"] if best_atk else None,
                "best_attack_attract": best_atk["attractiveness"] if best_atk else None,
                "best_attack_mil": best_atk["military"] if best_atk else None,
                "best_attack_net": best_atk["expected_net"] if best_atk else None,
                "best_attack_viable": best_atk["viable"] if best_atk else None,
                "best_colonize_rid": best_col["rid"] if best_col else None,
                "best_colonize_attract": best_col["attractiveness"] if best_col else None,
                "col_score_weighted": col_score,
                "atk_score_weighted": atk_score,
                "action_chosen": intent["action"],
                "dweights_attack": config.ARCHETYPE_DECISION_WEIGHTS.get(fac.archetype, {}).get("attack", 0),
                "dweights_expand": config.ARCHETYPE_DECISION_WEIGHTS.get(fac.archetype, {}).get("expand", 0),
            })

    return scoring_log


# ── REPORT GENERATION ───────────────────────────────────────────────────

def print_report(collector, ticks_run, config_module, scoring_log=None):
    c = collector
    print("\n" + "=" * 80)
    print("  BIBLE DIAGNOSTIC REPORT")
    print(f"  {ticks_run} ticks, seed {SEED}")
    print("=" * 80)

    # ── SECTION 1: Config Dump (the tuning knobs) ──────────────────────
    print("\n── 1. KEY CONFIG VALUES ──────────────────────────────────────")
    config_keys = [
        'BUDGET_GROWTH_RATE', 'REGION_MAINTENANCE_COST', 'ATTACK_COMMIT_FRACTION',
        'ATTACK_EFFICIENCY', 'RESISTANCE_FACTOR', 'BREAKTHROUGH_THRESHOLD',
        'CONQUEST_THRESHOLD', 'GARRISON_FRACTION', 'SURPRISE_EFFICIENCY',
        'COLONIZE_COST', 'COLONY_START_MILITARY', 'COLONY_START_ECONOMY',
        'COLONY_START_TENSION', 'COLONY_START_POPULATION',
        'REINFORCE_EFFICIENCY', 'REINFORCE_MAX_FRACTION',
        'MILITARY_DECAY_RATE', 'RECRUITMENT_RATE', 'RECRUITMENT_BASELINE',
        'RECRUITMENT_THRESHOLD', 'RECRUITMENT_CEILING',
        'ECONOMY_BASE_GROWTH', 'TENSION_ECONOMY_RATE', 'TENSION_NATURAL_DECAY_RATE',
        'TENSION_ECONOMY_MIDPOINT', 'POPULATION_GROWTH_RATE',
        'POPULATION_SUBSISTENCE', 'ECONOMY_FLOOR',
        'BORDER_FRICTION_TENSION', 'BORDER_FRICTION_ECONOMY',
        'ECON_OSCILLATION_AMPLITUDE', 'ECON_OSCILLATION_PERIOD',
        'ADMIN_REVOLT_BASE_RATE', 'ADMIN_REVOLT_SCALING_RATE',
        'ADMIN_REVOLT_INFLECTION_POINT',
        'REVOLT_BASE_PROBABILITY', 'REVOLT_TENSION_EXPONENT',
        'BASE_TECH_RATE', 'TECH_CONVERGENCE_RATE',
        'ENTRENCHMENT_BASE', 'ENTRENCHMENT_MAX', 'ENTRENCHMENT_RAMP_TICKS',
        'HOME_MILITARY_CAP', 'FRONTIER_MILITARY_CAP',
        'ATTACK_CONFIDENCE_RANGE',
        'ARCHETYPE_DECISION_WEIGHTS',
        'MIN_ACTION_THRESHOLD',
        'ATTACK_NORM_RANGE', 'COLONIZE_NORM_RANGE',
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
    if len(c.region_snapshots) > 100:
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
    for check_tick in [0, min(100, ticks_run - 1)]:
        if check_tick < len(c.region_snapshots):
            snap = c.region_snapshots[check_tick]
            regions_with_hostile = 0
            max_hostile = 0
            for rid, r in snap.items():
                if r['faction'] is not None:
                    regions_with_hostile += 1
            print(f"  (Need adjacency data to compute hostile border counts at tick {check_tick})")

    # ── SECTION 8: Attack Outcome Distribution ─────────────────────────
    print("\n── 8. ATTACK OUTCOME DISTRIBUTION ──────────────────────────")
    if c.attacks:
        outcomes = collections.Counter(a[3] for a in c.attacks)
        total = len(c.attacks)
        for outcome, count in sorted(outcomes.items()):
            print(f"  {outcome}: {count} ({count/total:.1%})")

        net_forces = [a[4] for a in c.attacks if a[4] is not None]
        if net_forces:
            print(f"\n  Net force stats: mean={safe_mean(net_forces):.2f}, "
                  f"median={safe_median(net_forces):.2f}, "
                  f"min={min(net_forces):.2f}, max={max(net_forces):.2f}")

        commits = [a[5] for a in c.attacks if a[5] is not None]
        if commits:
            print(f"  Committed budget: mean={safe_mean(commits):.2f}, "
                  f"median={safe_median(commits):.2f}, "
                  f"min={min(commits):.2f}, max={max(commits):.2f}")
    else:
        print("  No attacks recorded.")

    # ── SECTION 9: Colonization Scoring (WHY isn't colonization happening?) ─
    print("\n── 9. COLONIZE vs ATTACK SCORING (first 50 ticks) ──────────")
    if scoring_log:
        print(f"  {'Tick':>4} {'Faction':<15} {'Arch':<12} {'Budget':>7} {'#Col':>4} {'#Atk':>4} {'#Viab':>5} "
              f"{'ColScore':>8} {'AtkScore':>8} {'ColRID':<15} {'AtkRID':<15} {'AtkMil':>6} {'AtkNet':>7} {'Conf':>6} {'Winner':<10}")
        print(f"  {'-'*4} {'-'*15} {'-'*12} {'-'*7} {'-'*4} {'-'*4} {'-'*5} "
              f"{'-'*8} {'-'*8} {'-'*15} {'-'*15} {'-'*6} {'-'*7} {'-'*6} {'-'*10}")
        for entry in scoring_log:
            col_s = f"{entry['col_score_weighted']:.4f}" if entry['col_score_weighted'] is not None else "   None"
            atk_s = f"{entry['atk_score_weighted']:.4f}" if entry['atk_score_weighted'] is not None else "   None"
            col_rid = str(entry['best_colonize_rid'] or '')[:15]
            atk_rid = str(entry['best_attack_rid'] or '')[:15]
            atk_mil = f"{entry['best_attack_mil']:.1f}" if entry['best_attack_mil'] is not None else "  None"
            atk_net = f"{entry['best_attack_net']:.2f}" if entry['best_attack_net'] is not None else "  None"
            conf = f"{entry['effective_confidence']:.2f}"
            winner = entry['action_chosen'].upper()
            print(f"  {entry['tick']:>4} {entry['faction_id']:<15} {entry['archetype']:<12} {entry['budget']:>7.1f} "
                  f"{entry['n_colonize_candidates']:>4} {entry['n_attack_candidates']:>4} {entry['n_viable_attacks']:>5} "
                  f"{col_s:>8} {atk_s:>8} {col_rid:<15} {atk_rid:<15} {atk_mil:>6} {atk_net:>7} {conf:>6} {winner:<10}")
    else:
        print("  (No scoring data collected — see instrumentation notes below)")

    # ── SECTION 10: Breakaway Viability ────────────────────────────────
    print("\n── 10. BREAKAWAY SPAWN FIELD VALUES ─────────────────────────")
    if c.breakaway_spawns:
        print(f"  {'Tick':>5} {'Region':<25} {'Mil':>6} {'Eco':>6} {'Ten':>6} {'Pop':>6}")
        print(f"  {'-----':>5} {'-'*25} {'------':>6} {'------':>6} {'------':>6} {'------':>6}")
        for tick, rid, mil, eco, ten, pop in c.breakaway_spawns[:15]:
            print(f"  {tick:>5} {str(rid):<25} {mil:>6.1f} {eco:>6.1f} {ten:>6.1f} {pop:>6.1f}")
        if len(c.breakaway_spawns) > 15:
            print(f"  ... and {len(c.breakaway_spawns) - 15} more")

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

    col_count = len(c.colonizations)
    atk_count = len(c.attacks)
    if col_count == 0:
        checks.append(("FAIL", "Zero colonizations — expansion phase missing entirely"))
    elif col_count < 5:
        checks.append(("WARN", f"Only {col_count} colonizations vs {atk_count} attacks — expansion phase very weak"))
    else:
        checks.append(("OK", f"{col_count} colonizations vs {atk_count} attacks"))

    orig_survive_100 = 0
    orig_factions_set = set()
    if c.faction_region_counts:
        orig_factions_set = set(c.faction_region_counts[0].keys())
    for fid in orig_factions_set:
        if len(c.faction_region_counts) > 100:
            if c.faction_region_counts[100].get(fid, 0) > 0:
                orig_survive_100 += 1
    if orig_survive_100 < len(orig_factions_set) * 0.5:
        checks.append(("WARN", f"Only {orig_survive_100}/{len(orig_factions_set)} original factions alive at tick 100"))
    else:
        checks.append(("OK", f"{orig_survive_100}/{len(orig_factions_set)} original factions alive at tick 100"))

    if c.region_snapshots:
        final = c.region_snapshots[-1]
        high_tension = sum(1 for r in final.values() if r['faction'] and r['ten'] > 90)
        total_inhabited = sum(1 for r in final.values() if r['faction'])
        if high_tension > total_inhabited * 0.5:
            checks.append(("WARN", f"{high_tension}/{total_inhabited} regions above tension 90 at final tick"))
        else:
            checks.append(("OK", f"{high_tension}/{total_inhabited} regions above tension 90"))

    for t, snap in enumerate(c.faction_region_counts):
        total_regions = sum(snap.values())
        for fid, count in snap.items():
            if count == total_regions and total_regions > 1:
                persists = True
                for t2 in range(t, min(t + 200, len(c.faction_region_counts))):
                    s2 = c.faction_region_counts[t2]
                    if len([f for f, c2 in s2.items() if c2 > 0]) > 1:
                        persists = False
                        break
                if persists:
                    checks.append(("FAIL", f"J5 VIOLATION: {fid} held all {total_regions} regions for 200+ ticks starting tick {t}"))
                break

    if c.faction_region_counts:
        final_factions = sum(1 for f, count in c.faction_region_counts[-1].items() if count > 0)
        if final_factions < 2:
            checks.append(("FAIL", f"Only {final_factions} faction(s) alive at end"))
        else:
            checks.append(("OK", f"{final_factions} factions alive at end"))

    admin_chain_starts = len(c.admin_revolts)
    admin_breakaways = len([b for b in c.faction_births if b[3] is not None])
    if admin_chain_starts > 0:
        completion = admin_breakaways / admin_chain_starts if admin_chain_starts > 0 else 0
        if completion < 0.9:
            checks.append(("WARN", f"Admin revolt completion rate: {completion:.0%} ({admin_breakaways}/{admin_chain_starts})"))
        else:
            checks.append(("OK", f"Admin revolt completion: {admin_breakaways}/{admin_chain_starts}"))

    for status, msg in checks:
        icon = {"OK": "✓", "WARN": "⚠", "FAIL": "✗"}[status]
        print(f"  {icon} [{status}] {msg}")

    # ── SECTION 13: Instrumentation Gaps ───────────────────────────────
    print("\n── 13. INSTRUMENTATION NOTES ────────────────────────────────")
    print("""
  Data sources:
    - Sections 1-8, 10-12: populated from sim_validator.TrajectoryLog
      (run_recorded_scenario with use_tick_engine=True)
    - Section 9: populated from separate 50-tick run with faction.decide(debug=True)
    - Section 7 border friction: adjacency data not threaded through to report
      (would need world.adjacency access at report time)

  Known gaps:
    - Border friction hostile-neighbor counts (section 7) — only per-tick rates shown
    - Breakaway spawn data (section 10) captures region fields at snapshot time,
      which is AFTER resource steal; pre-steal values not available from trajectory
    """)


if __name__ == "__main__":
    print("Bible Diagnostic — Ouroboros Manifold")
    print("=" * 40)

    scenario = {
        "ticks":        TICKS,
        "seed":         SEED,
        "use_tick_engine": True,
        "features": {
            "events": True, "factions": True, "border_friction": True,
            "recruitment": True, "adjacency_bonus": True, "oscillation": True,
            "technology": True, "diplomacy": True, "admin_revolts": True,
        },
        "overrides": {},
    }

    print(f"\nRunning {TICKS}-tick scenario (seed {SEED}) via sim_validator...")
    tlog = sv.run_recorded_scenario("bible_diagnostic", scenario, seed_override=SEED)
    print("Populating collector from trajectory log...")
    collector = populate_from_trajectory(tlog)

    print("Collecting early scoring data (first 50 ticks, debug=True)...")
    scoring_log = collect_early_scoring(n_ticks=50, seed=SEED)

    print_report(collector, TICKS, config, scoring_log=scoring_log)
