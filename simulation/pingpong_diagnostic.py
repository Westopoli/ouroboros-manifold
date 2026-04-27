"""
pingpong_diagnostic.py — Targeted diagnostic for ping-pong, zombie, and entrenchment issues
Run from simulation/:  python3 pingpong_diagnostic.py
"""

import sys, os, collections

import config
import sim_validator as sv
import world as world_mod
import faction as faction_mod
import events as _events
import diplomacy as _diplomacy
import tick as _tick

TICKS = 500
SEED = 1


def run_trajectory():
    scenario = {
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
    return sv.run_recorded_scenario("pingpong_diag", scenario, seed_override=SEED)


def find_worst_pingpong(tlog, min_tick=100):
    prev_owners = {}
    changes = collections.defaultdict(list)
    for snap in tlog.snapshots:
        for rid, rdata in snap.regions.items():
            fid = rdata["faction_id"]
            old = prev_owners.get(rid)
            if old != fid and snap.tick > 0:
                changes[rid].append((snap.tick, old, fid))
            prev_owners[rid] = fid
    post100 = {rid: [c for c in clist if c[0] >= min_tick] for rid, clist in changes.items()}
    worst_rid = max(post100, key=lambda r: len(post100[r]))
    return worst_rid, post100[worst_rid], changes


def pick_zombies(tlog, min_ticks=300):
    agent_decisions = collections.defaultdict(lambda: collections.Counter())
    faction_first_seen = {}
    for snap in tlog.snapshots:
        for fid in snap.factions:
            if fid not in faction_first_seen:
                faction_first_seen[fid] = snap.tick
        for a in snap.faction_actions:
            agent_decisions[a.get("faction_id")][a.get("action", "accumulate")] += 1

    zombies = []
    for fid, counts in agent_decisions.items():
        if "breakaway_" not in fid:
            continue
        total = sum(counts.values())
        if total < min_ticks:
            continue
        acc_pct = counts.get("accumulate", 0) / total
        if acc_pct >= 0.995:
            zombies.append((fid, total, faction_first_seen.get(fid, 0)))
    zombies.sort(key=lambda x: -x[1])
    return zombies[:3]


def run_instrumented(target_rid, zombie_fids):
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

    w = world_mod.generate_random(seed=SEED)
    factions = faction_mod.generate_starting_factions(rng=w.rng, world=w)
    registry = faction_mod.make_registry(*factions)
    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()
    stances = _diplomacy.init_stances(registry)
    pending_telegraphs = []

    attack_logs = []
    zombie_budgets = collections.defaultdict(list)
    entrenchment_logs = []
    prev_owner = None

    zombie_sample_offsets = [0, 50, 100, 200]

    for t in range(1, TICKS + 1):
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
                "held_since_tick": r.held_since_tick,
            }

        # ── Test 3: Entrenchment tracking ─────────────────────────────────
        current_owner = w.regions[target_rid].faction_id
        if current_owner != prev_owner and t > 1:
            region = w.regions[target_rid]
            held_since = region.held_since_tick
            if prev_owner is not None:
                entrenchment_logs.append({
                    "tick": t,
                    "old_owner": prev_owner,
                    "new_owner": current_owner,
                    "held_since_tick": held_since,
                })
        prev_owner = current_owner

        # ── Test 2: Zombie budget tracking ────────────────────────────────
        for zfid in zombie_fids:
            if zfid in registry:
                parts = zfid.split("_")
                spawn_tick = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                for offset in zombie_sample_offsets:
                    if t == spawn_tick + offset:
                        owned = w.regions_by_faction(zfid)
                        owned_rid = owned[0].id if owned else None
                        neighbors = []
                        if owned_rid:
                            for nid in w.get_neighbors(owned_rid):
                                nb = w.regions.get(nid)
                                neighbors.append({
                                    "rid": nid,
                                    "faction_id": nb.faction_id if nb else None,
                                    "in_registry": (nb.faction_id in registry) if nb and nb.faction_id else False,
                                })
                        zombie_budgets[zfid].append({
                            "tick": t,
                            "offset": offset,
                            "budget": round(registry[zfid].budget, 2),
                            "owned_region": owned_rid,
                            "n_regions": len(owned),
                            "neighbors": neighbors,
                        })

        # ── Test 1: Attack decision context ───────────────────────────────
        if t >= 100 and len(attack_logs) < 10:
            for fac in list(registry.values()):
                owned = [rid for rid, rd in snapshot.items() if rd["faction_id"] == fac.id]
                if not owned:
                    continue
                intent = fac.decide(snapshot, w.adjacency, registry, w.rng, t, debug=True)
                if intent["action"] == "attack" and intent["target_region"] == target_rid:
                    target_fields = snapshot[target_rid]["fields"]

                    all_candidates = _compute_all_candidates(
                        fac, owned, snapshot, w.adjacency, registry
                    )

                    attack_logs.append({
                        "tick": t,
                        "faction_id": fac.id,
                        "archetype": fac.archetype,
                        "budget": round(fac.budget, 2),
                        "target_mil": round(target_fields["military"], 2),
                        "target_eco": round(target_fields["economy"], 2),
                        "target_ten": round(target_fields["tension"], 2),
                        "target_pop": round(target_fields["population"], 2),
                        "expected_net": intent.get("expected_outcome"),
                        "diag": intent.get("diag", {}),
                        "all_candidates": all_candidates,
                    })
                    if len(attack_logs) >= 10:
                        break

    return attack_logs, dict(zombie_budgets), entrenchment_logs


def _compute_all_candidates(fac, owned_rids, snapshot, adjacency, registry):
    we = config.ATTRACT_ECONOMY_SUBWEIGHT
    wp = config.ATTRACT_POPULATION_SUBWEIGHT
    aweights = config.ARCHETYPE_ATTRACT_WEIGHTS.get(fac.archetype, config.DEFAULT_ATTRACT_WEIGHTS)
    ten_pri = aweights.get("tension_primary", False)

    seen = set()
    candidates = {}
    for rid in owned_rids:
        for nid in adjacency.get(rid, []):
            if nid in seen or nid not in snapshot:
                continue
            seen.add(nid)
            nd = snapshot[nid]
            nf = nd["faction_id"]
            if nf == fac.id or nf is None:
                continue

            nfields = nd["fields"]
            factor_1 = (nfields["tension"] / 100.0) if ten_pri else (1.0 - nfields["military"] / 100.0)

            current_value = (nfields["economy"] * we + nfields["population"] * wp) / 100.0

            nb_of_target = adjacency.get(nid, [])
            non_owned = [n for n in nb_of_target
                         if snapshot.get(n, {}).get("faction_id") != fac.id]
            nb_scores = []
            for nb_id in non_owned:
                nb_data = snapshot.get(nb_id)
                if not nb_data:
                    continue
                if nb_data["faction_id"] is None:
                    nb_scores.append(config.EXPANSION_POTENTIAL)
                else:
                    nbf = nb_data["fields"]
                    nb_scores.append((nbf["economy"] * we + nbf["population"] * wp) / 100.0)
            strategic_position = sum(nb_scores) / len(nb_scores) if nb_scores else 0.0

            attractiveness = (aweights["weakness"] * factor_1
                              + aweights["value"] * current_value
                              + aweights["position"] * strategic_position)

            potential_commit = fac.budget * config.ATTACK_COMMIT_FRACTION
            expected_net = (potential_commit * config.ATTACK_EFFICIENCY
                            - nfields["military"] * config.RESISTANCE_FACTOR)

            our_stance = fac.diplomatic_stance.get(nf, "neutral")
            their_fac = registry.get(nf)
            their_stance = their_fac.diplomatic_stance.get(fac.id, "neutral") if their_fac else "neutral"
            hostile = our_stance == "hostile" or their_stance == "hostile"

            candidates[nid] = {
                "faction_id": nf,
                "mil": round(nfields["military"], 1),
                "eco": round(nfields["economy"], 1),
                "pop": round(nfields["population"], 1),
                "weakness": round(factor_1, 3),
                "current_value": round(current_value, 3),
                "strategic_pos": round(strategic_position, 3),
                "attractiveness": round(attractiveness, 3),
                "expected_net": round(expected_net, 2),
                "hostile": hostile,
                "passes_min_value": current_value >= config.MIN_ATTACK_VALUE,
            }

    return candidates


def print_test1(attack_logs, target_rid):
    print("\n" + "=" * 100)
    print(f"  TEST 1: WHY DO FACTIONS ATTACK {target_rid}?")
    print("=" * 100)

    if not attack_logs:
        print("  No attacks on target region found after tick 100.")
        return

    for i, log in enumerate(attack_logs):
        cv = (log["target_eco"] * 0.60 + log["target_pop"] * 0.40) / 100.0
        weakness = 1.0 - log["target_mil"] / 100.0
        print(f"\n  ── Attack #{i+1} (tick {log['tick']}) ──────────────────────────────")
        print(f"  Attacker: {log['faction_id']} ({log['archetype']})")
        print(f"  Budget: {log['budget']}")
        print(f"  Target fields: mil={log['target_mil']}, eco={log['target_eco']}, "
              f"ten={log['target_ten']}, pop={log['target_pop']}")
        print(f"  current_value = ({log['target_eco']}×0.6 + {log['target_pop']}×0.4) / 100 = {cv:.3f}")
        print(f"  weakness = 1 - {log['target_mil']}/100 = {weakness:.3f}")
        print(f"  expected_net = {log['expected_net']}")

        diag = log["diag"]
        print(f"  Diag: #atk_candidates={diag.get('n_attack_candidates', '?')}, "
              f"#viable={diag.get('n_viable_attacks', '?')}, "
              f"eff_confidence={diag.get('effective_confidence', '?')}")

        cands = log["all_candidates"]
        hostile_viable = {rid: c for rid, c in cands.items()
                          if c["hostile"] and c["passes_min_value"]}
        print(f"\n  All hostile attack candidates ({len(hostile_viable)} total):")
        print(f"    {'Region':<25} {'Owner':<30} {'Mil':>5} {'Eco':>5} {'Pop':>5} "
              f"{'Value':>6} {'Weak':>6} {'Attract':>8} {'ExpNet':>8}")
        print(f"    {'-'*25} {'-'*30} {'-'*5} {'-'*5} {'-'*5} "
              f"{'-'*6} {'-'*6} {'-'*8} {'-'*8}")

        sorted_cands = sorted(hostile_viable.items(), key=lambda x: -x[1]["attractiveness"])
        for rid, c in sorted_cands:
            marker = " ◄◄◄" if rid == target_rid else ""
            owner_short = (c["faction_id"] or "None")[:30]
            print(f"    {rid:<25} {owner_short:<30} {c['mil']:>5.1f} {c['eco']:>5.1f} {c['pop']:>5.1f} "
                  f"{c['current_value']:>6.3f} {c['weakness']:>6.3f} {c['attractiveness']:>8.3f} "
                  f"{c['expected_net']:>8.2f}{marker}")

        if not hostile_viable:
            print("    (none)")


def print_test2(zombie_budgets, zombie_fids, tlog):
    print("\n" + "=" * 100)
    print("  TEST 2: WHY DO ZOMBIES PERSIST?")
    print("=" * 100)

    if not zombie_fids:
        print("  No zombies found with 300+ ticks.")
        return

    for zfid, total_ticks, spawn_tick in zombie_fids:
        print(f"\n  ── Zombie: {zfid} ──────────────────────────────")
        print(f"  Spawn tick: {spawn_tick}, Survived: {total_ticks} ticks, 100% accumulate")

        samples = zombie_budgets.get(zfid, [])
        if samples:
            print(f"\n  Budget trajectory:")
            print(f"    {'Tick':>5} {'Offset':>7} {'Budget':>8} {'Region':<25} {'#Rgns':>5}")
            print(f"    {'-'*5} {'-'*7} {'-'*8} {'-'*25} {'-'*5}")
            for s in samples:
                print(f"    {s['tick']:>5} {'+'+str(s['offset']):>7} {s['budget']:>8.2f} "
                      f"{s['owned_region'] or 'None':<25} {s['n_regions']:>5}")

            last_sample = samples[-1] if samples else None
            if last_sample and last_sample["neighbors"]:
                print(f"\n  Neighbors of {last_sample['owned_region']} at tick {last_sample['tick']}:")
                print(f"    {'Region':<25} {'Owner':<35} {'In Registry':>12}")
                print(f"    {'-'*25} {'-'*35} {'-'*12}")
                for nb in last_sample["neighbors"]:
                    owner = nb["faction_id"] or "None (unowned)"
                    in_reg = "Yes" if nb["in_registry"] else "No"
                    print(f"    {nb['rid']:<25} {str(owner)[:35]:<35} {in_reg:>12}")

                has_absorber = any(nb["in_registry"] for nb in last_sample["neighbors"])
                budget_ok = last_sample["budget"] < config.COLONIZE_COST

                print(f"\n  Cleanup diagnosis:")
                print(f"    Owns 1 region:     Yes")
                print(f"    Age > {config.ZOMBIE_CLEANUP_TICKS} ticks:     Yes ({total_ticks} ticks)")
                print(f"    Budget < {config.COLONIZE_COST}:    {'Yes' if budget_ok else 'NO'} ({last_sample['budget']})")
                print(f"    Adjacent absorber:  {'Yes' if has_absorber else 'NO'}")
                if not has_absorber:
                    print(f"    >>> BLOCKED: No adjacent faction in registry to absorb into")
                elif not budget_ok:
                    print(f"    >>> BLOCKED: Budget too high ({last_sample['budget']} >= {config.COLONIZE_COST})")
        else:
            print("  (No budget samples captured — faction may not have existed at sample ticks)")


def print_test3(entrenchment_logs, target_rid):
    print("\n" + "=" * 100)
    print(f"  TEST 3: ENTRENCHMENT ON {target_rid}")
    print("=" * 100)

    post100 = [e for e in entrenchment_logs if e["tick"] >= 100]
    if not post100:
        print("  No ownership changes on target region after tick 100.")
        return

    print(f"\n  {'Tick':>5} {'Old Owner':<35} {'New Owner':<35} {'HeldSince':>9} "
          f"{'PrevHeld':>9} {'Entrench':>8}")
    print(f"  {'-'*5} {'-'*35} {'-'*35} {'-'*9} {'-'*9} {'-'*8}")

    prev_held_since = None
    for i, e in enumerate(post100[:10]):
        held_since = e["held_since_tick"]
        if prev_held_since is not None:
            prev_ticks_held = e["tick"] - prev_held_since
            ent = config.ENTRENCHMENT_BASE + (config.ENTRENCHMENT_MAX - config.ENTRENCHMENT_BASE) * min(1.0, prev_ticks_held / config.ENTRENCHMENT_RAMP_TICKS)
        else:
            prev_ticks_held = None
            ent = None

        old_short = (e["old_owner"] or "None")[:35]
        new_short = (e["new_owner"] or "None")[:35]
        held_str = str(held_since) if held_since is not None else "None"
        prev_str = str(prev_ticks_held) if prev_ticks_held is not None else "?"
        ent_str = f"{ent:.3f}" if ent is not None else "?"

        print(f"  {e['tick']:>5} {old_short:<35} {new_short:<35} {held_str:>9} "
              f"{prev_str:>9} {ent_str:>8}")

        prev_held_since = held_since

    if len(post100) > 10:
        print(f"  ... and {len(post100) - 10} more changes")

    ticks_held_values = []
    prev_hs = None
    for e in post100:
        if prev_hs is not None:
            ticks_held_values.append(e["tick"] - prev_hs)
        prev_hs = e["held_since_tick"]

    if ticks_held_values:
        avg = sum(ticks_held_values) / len(ticks_held_values)
        mn = min(ticks_held_values)
        mx = max(ticks_held_values)
        avg_ent = config.ENTRENCHMENT_BASE + (config.ENTRENCHMENT_MAX - config.ENTRENCHMENT_BASE) * min(1.0, avg / config.ENTRENCHMENT_RAMP_TICKS)
        print(f"\n  Summary ({len(ticks_held_values)} tenure periods):")
        print(f"    Mean tenure: {avg:.1f} ticks → entrenchment {avg_ent:.3f}")
        print(f"    Min tenure:  {mn} ticks → entrenchment "
              f"{config.ENTRENCHMENT_BASE + (config.ENTRENCHMENT_MAX - config.ENTRENCHMENT_BASE) * min(1.0, mn / config.ENTRENCHMENT_RAMP_TICKS):.3f}")
        print(f"    Max tenure:  {mx} ticks → entrenchment "
              f"{config.ENTRENCHMENT_BASE + (config.ENTRENCHMENT_MAX - config.ENTRENCHMENT_BASE) * min(1.0, mx / config.ENTRENCHMENT_RAMP_TICKS):.3f}")
        print(f"    ENTRENCHMENT_RAMP_TICKS = {config.ENTRENCHMENT_RAMP_TICKS}")
        print(f"    For reference: 100 ticks → {config.ENTRENCHMENT_MAX:.1f}x defense multiplier")


if __name__ == "__main__":
    print("Ping-Pong Diagnostic — Ouroboros Manifold")
    print("=" * 50)

    print("\nPass 1: Running trajectory (run_recorded_scenario)...")
    tlog = run_trajectory()

    target_rid, target_changes, all_changes = find_worst_pingpong(tlog)
    print(f"Worst ping-pong region: {target_rid} ({len(target_changes)} changes after tick 100)")

    zombie_picks = pick_zombies(tlog)
    print(f"Selected zombies: {[z[0] for z in zombie_picks]}")

    zombie_fids_list = [z[0] for z in zombie_picks]

    print(f"\nPass 2: Running instrumented sim (500 ticks, capturing decisions)...")
    attack_logs, zombie_budgets, entrenchment_logs = run_instrumented(target_rid, zombie_fids_list)
    print(f"Captured {len(attack_logs)} attack decisions on {target_rid}")
    print(f"Captured {sum(len(v) for v in zombie_budgets.values())} zombie budget samples")
    print(f"Captured {len(entrenchment_logs)} ownership changes on {target_rid}")

    print_test1(attack_logs, target_rid)
    print_test2(zombie_budgets, zombie_picks, tlog)
    print_test3(entrenchment_logs, target_rid)
