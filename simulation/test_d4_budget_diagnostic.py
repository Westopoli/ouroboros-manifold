#!/usr/bin/env python3
"""
D4 Budget Hoarding Diagnostic

Runs the 07_full_game_50 scenario and traces the opportunist's budget over time,
along with all the variables that feed into its spending decisions:
  - Budget accumulation (net economy income per tick)
  - Attack candidates (hostile neighbors, their military, viability)
  - Colonization candidates
  - Budget pressure effect on confidence
  - Chosen action each tick and why

Prints a tick-by-tick table for the hoarding window, plus summary stats.
"""
import os, sys, random
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
import world as world_mod
import faction as faction_mod
import events as _events
import diplomacy as _diplomacy
import tick as _tick
from sim_validator import _apply_features, _snapshot_config
from sim_tuner import SCENARIOS


def run():
    scenario = SCENARIOS["07_full_game_50"]
    seed = scenario["seed"]
    _apply_features(scenario["features"])
    for key, val in scenario.get("overrides", {}).items():
        setattr(config, key, val)

    w = world_mod.generate_random(seed=seed)
    factions = faction_mod.generate_starting_factions(rng=w.rng, world=w)
    registry = faction_mod.make_registry(*factions)
    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()
    stances = _diplomacy.init_stances(registry)
    pending_telegraphs = []

    # D4 thresholds (from invariant)
    min_confidence = 8.0
    commit_fraction = config.ATTACK_COMMIT_FRACTION
    cheapest_attack = min_confidence * commit_fraction
    hoard_threshold = cheapest_attack * 5.0

    # Track per-tick data for ALL factions
    history = {fid: [] for fid in registry}

    ticks = scenario["ticks"]
    for t in range(1, ticks + 1):
        # Capture pre-tick state
        pre_budgets = {fid: fac.budget for fid, fac in registry.items()}
        pre_regions = {fid: len(w.regions_by_faction(fid)) for fid in registry}
        pre_stances = {}
        for fid, fac in registry.items():
            core_others = [ofid for ofid in registry
                           if ofid != fid and not ofid.startswith("breakaway_")]
            pre_stances[fid] = {ofid: fac.diplomatic_stance.get(ofid, "neutral")
                                for ofid in core_others}

        # Run diagnostic decisions on a cloned RNG (doesn't affect main RNG)
        diag_rng = random.Random()
        diag_rng.setstate(w.rng.getstate())
        snapshot = {
            rid: {
                "fields": dict(r.fields),
                "faction_id": r.faction_id,
                "tier": r.tier,
                "held_since_tick": r.held_since_tick,
                "previous_faction_id": r.previous_faction_id,
            }
            for rid, r in w.regions.items()
        }
        border_adj = {rid: w.get_neighbors(rid, edge_type="border") for rid in w.adjacency}
        diag_intents = {}
        for fid, fac in list(registry.items()):
            diag_intents[fid] = fac.decide(snapshot, border_adj, registry, diag_rng, t, debug=True)

        tick_log = _tick.run_tick(
            w, t,
            pending_queue=pending_queue,
            noise_offsets=noise_offsets,
            trigger_state=trigger_state,
            registry=registry if config.ENABLE_FACTIONS else None,
            stances=stances if config.ENABLE_DIPLOMACY else None,
            pending_telegraphs=pending_telegraphs,
        )

        # Record per-faction tick data
        for fid in list(history.keys()):
            if fid not in registry:
                history[fid].append(None)
                continue

            fac = registry[fid]
            intent = diag_intents.get(fid, {})
            diag = intent.get("diag", {})
            action_taken = next(
                (a for a in tick_log.get("faction_actions", []) if a["faction_id"] == fid),
                None
            )

            # Net economy income
            owned = [r for r in w.regions.values() if r.faction_id == fid and r.fields]
            net_eco = sum(r.fields["economy"] - config.REGION_MAINTENANCE_COST for r in owned)
            budget_delta = net_eco * fac.budget_growth_rate

            history[fid].append({
                "tick": t,
                "budget": round(fac.budget, 2),
                "budget_before": round(pre_budgets.get(fid, 0), 2),
                "budget_delta": round(budget_delta, 3),
                "regions": pre_regions.get(fid, 0),
                "action": intent.get("action", "?"),
                "action_actual": action_taken["action"] if action_taken else "—",
                "target": intent.get("target_region", "").replace("region_", "") if intent.get("target_region") else "—",
                "n_attack_cands": diag.get("n_attack_candidates", 0),
                "n_viable": diag.get("n_viable_attacks", 0),
                "n_colonize_cands": diag.get("n_colonize_candidates", 0),
                "attack_confidence": round(fac.attack_confidence, 2),
                "effective_confidence": diag.get("effective_confidence", None),
                "potential_commit": diag.get("potential_commit", None),
                "best_attack": diag.get("best_attack_any"),
                "scores": diag.get("weighted_scores", {}),
                "stances": pre_stances.get(fid, {}),
                "conquests": [c for c in tick_log.get("conquests", [])
                              if c.get("new_faction_id") == fid or c.get("old_faction_id") == fid],
                "was_betrayed": any(b["victim"] == fid for b in tick_log.get("betrayals", [])),
                "did_betray": any(b["betrayer"] == fid for b in tick_log.get("betrayals", [])),
            })

    # ── Print results ────────────────────────────────────────────────────────
    print(f"{'='*100}")
    print(f"  D4 Budget Hoarding Diagnostic — 07_full_game_50 (seed={seed}, {ticks} ticks)")
    print(f"  Hoard threshold: {hoard_threshold:.1f} (5x cheapest attack @ confidence 8.0)")
    print(f"{'='*100}")

    # Find the hoarding faction and window
    for fid in history:
        entries = history[fid]
        run = 0
        hoard_start = None
        hoard_end = None
        for i, e in enumerate(entries):
            if e is None:
                run = 0
                continue
            if e["budget"] > hoard_threshold:
                if run == 0:
                    hoard_start = i
                run += 1
                if run >= 50:
                    hoard_end = i
            else:
                run = 0

        if hoard_end is None:
            continue

        print(f"\n  HOARDING DETECTED: {fid}")
        print(f"  Window: tick {entries[hoard_start]['tick']} → tick {entries[hoard_end]['tick']} ({hoard_end - hoard_start + 1} ticks)")
        print(f"  Attack confidence (base): {entries[hoard_start]['attack_confidence']}")

        # Print context window: 20 ticks before hoarding starts through end
        ctx_start = max(0, hoard_start - 20)
        ctx_end = min(len(entries) - 1, hoard_end + 10)

        print(f"\n  {'Tick':>5} {'Budget':>8} {'Δ':>7} {'Rgn':>3} {'Action':>10} {'Target':>12} "
              f"{'AtkCand':>7} {'Viable':>6} {'ColCand':>7} {'Conf':>5} {'EffConf':>7} "
              f"{'Commit':>7} {'AtkScr':>7} {'ColScr':>7} {'Notes'}")
        print(f"  {'─'*5} {'─'*8} {'─'*7} {'─'*3} {'─'*10} {'─'*12} "
              f"{'─'*7} {'─'*6} {'─'*7} {'─'*5} {'─'*7} "
              f"{'─'*7} {'─'*7} {'─'*7} {'─'*30}")

        for i in range(ctx_start, ctx_end + 1):
            e = entries[i]
            if e is None:
                print(f"  {i:>5}  (eliminated)")
                continue

            notes = []
            if e["conquests"]:
                for c in e["conquests"]:
                    if c.get("new_faction_id") == fid:
                        notes.append(f"WON {c['region_id'].replace('region_', '')}")
                    else:
                        notes.append(f"LOST {c['region_id'].replace('region_', '')}")
            if e["was_betrayed"]:
                notes.append("BETRAYED!")
            if e["did_betray"]:
                notes.append("betrayed other")
            if i == hoard_start:
                notes.append("<<< HOARD START")
            if i == hoard_end:
                notes.append("<<< HOARD END (50 ticks)")

            atk_score = e["scores"].get("attack")
            col_score = e["scores"].get("colonize")
            eff_conf = e["effective_confidence"]
            commit = e["potential_commit"]
            best_atk = e["best_attack"]
            best_mil = f" (mil={best_atk['military']:.0f})" if best_atk and best_atk.get("military") else ""

            print(f"  {e['tick']:>5} {e['budget']:>8.1f} {e['budget_delta']:>+7.2f} {e['regions']:>3} "
                  f"{e['action']:>10} {e['target']:>12}{best_mil:<8} "
                  f"{e['n_attack_cands']:>7} {e['n_viable']:>6} {e['n_colonize_cands']:>7} "
                  f"{e['attack_confidence']:>5.1f} {eff_conf:>7.2f} " if eff_conf is not None else
                  f"  {e['tick']:>5} {e['budget']:>8.1f} {e['budget_delta']:>+7.2f} {e['regions']:>3} "
                  f"{e['action']:>10} {e['target']:>12}{'':8} "
                  f"{e['n_attack_cands']:>7} {e['n_viable']:>6} {e['n_colonize_cands']:>7} "
                  f"{e['attack_confidence']:>5.1f} {'—':>7} ",
                  end="")
            print(f"{commit:>7.1f} " if commit is not None else f"{'—':>7} ", end="")
            print(f"{atk_score:>7.3f} " if atk_score is not None else f"{'—':>7} ", end="")
            print(f"{col_score:>7.3f} " if col_score is not None else f"{'—':>7} ", end="")
            print(" ".join(notes))

        # Stance summary during hoarding window
        print(f"\n  Diplomatic stances during hoarding:")
        sample = entries[hoard_start]
        if sample:
            for ofid, stance in sample["stances"].items():
                print(f"    → {ofid}: {stance}")

        # Best attack target details during hoarding
        print(f"\n  Best attack target details (sampled every 10 ticks in window):")
        for i in range(hoard_start, hoard_end + 1, 10):
            e = entries[i]
            if e is None:
                continue
            ba = e["best_attack"]
            if ba:
                print(f"    t={e['tick']:>4}: target={ba['rid']}  mil={ba['military']}  "
                      f"net={ba['expected_net']}  viable={ba['viable']}  "
                      f"commit={e['potential_commit']:.1f}  eff_conf={e['effective_confidence']:.2f}")
            else:
                print(f"    t={e['tick']:>4}: no attack candidates")

    # ── Summary for all factions ──────────────────────────────────────────────
    print(f"\n{'─'*100}")
    print(f"  FACTION BUDGET SUMMARY (max budget, avg budget, ticks above hoard threshold)")
    print(f"{'─'*100}")
    for fid in sorted(history.keys()):
        entries = [e for e in history[fid] if e is not None]
        if not entries:
            print(f"  {fid:<20} eliminated before any data")
            continue
        budgets = [e["budget"] for e in entries]
        above = sum(1 for b in budgets if b > hoard_threshold)
        max_b = max(budgets)
        avg_b = sum(budgets) / len(budgets)
        final_regions = entries[-1]["regions"] if entries else 0
        print(f"  {fid:<20} max={max_b:>7.1f}  avg={avg_b:>7.1f}  "
              f"ticks_above_threshold={above:>4}  final_regions={final_regions}")

    print(f"\n{'='*100}")
    print(f"  Config values governing D4:")
    print(f"    BUDGET_GROWTH_RATE          = {config.BUDGET_GROWTH_RATE}")
    print(f"    REGION_MAINTENANCE_COST     = {config.REGION_MAINTENANCE_COST}")
    print(f"    ATTACK_COMMIT_FRACTION      = {config.ATTACK_COMMIT_FRACTION}")
    print(f"    BUDGET_PRESSURE_THRESHOLD   = {config.BUDGET_PRESSURE_THRESHOLD}")
    print(f"    ATTACK_CONFIDENCE_RANGE     = {config.ATTACK_CONFIDENCE_RANGE}")
    print(f"    COLONIZE_COST               = {config.COLONIZE_COST}")
    print(f"    RESISTANCE_FACTOR           = {config.RESISTANCE_FACTOR}")
    print(f"    ATTACK_EFFICIENCY           = {config.ATTACK_EFFICIENCY}")
    print(f"    MIN_ACTION_THRESHOLD        = {config.MIN_ACTION_THRESHOLD}")
    print(f"    MIN_ATTACK_VALUE            = {config.MIN_ATTACK_VALUE}")
    print(f"    SURPRISE_EFFICIENCY_MULT    = {config.SURPRISE_EFFICIENCY_MULT}")
    print(f"    ENTRENCHMENT_BASE           = {config.ENTRENCHMENT_BASE}")
    print(f"    ENTRENCHMENT_MAX            = {config.ENTRENCHMENT_MAX}")
    print(f"    ENTRENCHMENT_RAMP_TICKS     = {config.ENTRENCHMENT_RAMP_TICKS}")
    print(f"{'='*100}")


if __name__ == "__main__":
    run()
