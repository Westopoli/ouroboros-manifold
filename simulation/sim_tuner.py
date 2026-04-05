#!/usr/bin/env python3
"""
sim_tuner.py — Simulation tuning harness for Ouroboros Manifold.

Run all scenarios:     python sim_tuner.py
Run one scenario:      python sim_tuner.py 01_solo_drift
Run multiple:          python sim_tuner.py 01_solo_drift 03_contested
List scenarios:        python sim_tuner.py --list

Each scenario produces PNGs in tuning_output/:
  - {scenario}_all.png         Full overlay (all factions × all fields)
  - {scenario}_{field}.png     Per-field comparison across factions (multi-faction only)

The scenario progression:
  01  Solo drift          — One faction, 3 regions, pure field interaction
  02  Solo with events    — Same but events enabled
  03  Contested border    — Two factions, hostile, border friction + combat
  04  Four-way            — Four factions, full agent loop
  05  Full stack          — Everything above plus technology
"""

import sys
import os
import importlib

# ── Ensure we're running from the script's directory ─────────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
import world as world_mod
import faction as faction_mod
import events as _events
import drift as _drift
import technology as _tech
import tick as _tick
import sim_graph

# ── Output directory ─────────────────────────────────────────────────────────
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tuning_output")
os.makedirs(OUT_DIR, exist_ok=True)


# ═════════════════════════════════════════════════════════════════════════════
#  SCENARIO DEFINITIONS
# ═════════════════════════════════════════════════════════════════════════════

SCENARIOS = {

    # ── 01: Pure drift — normal vs low economy, side by side ────────────────
    "01_solo_drift": {
        "template":     "s1_isolated",
        "ticks":        300,
        "seed":         1,
        "description":  "Pure drift — normal vs low economy start (no events/agents/tech)",
        "use_tick_engine": False,
        "features": {
            "events":          False,
            "factions":        False,
            "border_friction": False,
            "recruitment":     True,
            "adjacency_bonus": True,
            "oscillation":     True,
            "technology":      False,
            "diplomacy":       False,
        },
        "overrides": {},
        # Variants: each gets its own sub-run with these overrides applied on top.
        # All variants share the same base features/template/ticks/seed.
        # Results are rendered side-by-side on one PNG.
        "variants": [
            {
                "label": "Normal start",
                "overrides": {},  # uses default config ranges
            },
            {
                "label": "Low economy start",
                "overrides": {
                    "S1_HOME_ECONOMY_RANGE":     (15, 25),
                    "S1_FRONTIER_ECONOMY_RANGE":  (8, 15),
                },
            },
        ],
    },

    # ── 01b: Famine stress test — 4 seeds, same brutal start ────────────────
    "01b_famine_stress": {
        "template":     "s1_isolated",
        "ticks":        300,
        "seed":         1,   # overridden per variant
        "description":  "Famine stress — low eco/pop start, 4 seeds, can they recover?",
        "use_tick_engine": False,
        "features": {
            "events":          True,
            "factions":        False,
            "border_friction": False,
            "recruitment":     True,
            "adjacency_bonus": True,
            "oscillation":     True,
            "technology":      False,
            "diplomacy":       False,
        },
        "overrides": {
            "S1_HOME_ECONOMY_RANGE":      (12, 20),
            "S1_FRONTIER_ECONOMY_RANGE":  (8, 14),
            "S1_HOME_POPULATION_RANGE":   (30, 45),
            "S1_FRONTIER_POPULATION_RANGE": (15, 25),
            "S1_HOME_TENSION_RANGE":      (30, 45),
            "S1_FRONTIER_TENSION_RANGE":  (20, 35),
        },
        "variants": [
            {"label": "Run A", "overrides": {"_seed": "random"}},
            {"label": "Run B", "overrides": {"_seed": "random"}},
            {"label": "Run C", "overrides": {"_seed": "random"}},
            {"label": "Run D", "overrides": {"_seed": "random"}},
        ],
    },

    # ── 02: Solo with events enabled ────────────────────────────────────────
    "02_solo_events": {
        "template":     "s1_isolated",
        "ticks":        300,
        "seed":         1,
        "description":  "Solo + events — 1 faction, 3 regions, events fire but no agents",
        "use_tick_engine": False,
        "features": {
            "events":          True,
            "factions":        False,
            "border_friction": False,
            "recruitment":     True,
            "adjacency_bonus": True,
            "oscillation":     True,
            "technology":      False,
            "diplomacy":       False,
        },
        "overrides": {},
    },

    # ── 03: Two factions, hostile, with border friction + combat ─────────────
    "03_contested": {
        "template":     "contested_border",
        "ticks":        50,
        "seed":         1,
        "description":  "Contested border — 2 factions, hostile, agents + attacks, no tech",
        "use_tick_engine": True,
        "features": {
            "events":          True,
            "factions":        True,
            "border_friction": True,
            "recruitment":     True,
            "adjacency_bonus": True,
            "oscillation":     True,
            "technology":      False,
            "diplomacy":       False,
        },
        "overrides": {},
    },

    # ── 04: Four factions, full agent loop ───────────────────────────────────
    "04_four_way": {
        "template":     "four_way",
        "ticks":        500,
        "seed":         1,
        "description":  "Four-way — 4 factions, full agents + combat, no tech",
        "use_tick_engine": True,
        "features": {
            "events":          True,
            "factions":        True,
            "border_friction": True,
            "recruitment":     True,
            "adjacency_bonus": True,
            "oscillation":     True,
            "technology":      False,
            "diplomacy":       False,
        },
        "overrides": {},
    },

    # ── 05: Full stack — everything including technology ─────────────────────
    "05_full_stack": {
        "template":     "four_way",
        "ticks":        500,
        "seed":         1,
        "description":  "Full stack — 4 factions, all systems including tech",
        "use_tick_engine": True,
        "features": {
            "events":          True,
            "factions":        True,
            "border_friction": True,
            "recruitment":     True,
            "adjacency_bonus": True,
            "oscillation":     True,
            "technology":      True,
            "diplomacy":       False,
        },
        "overrides": {},
    },
    "06_diplomacy": {
        "template":     "four_way",
        "ticks":        500,
        "seed":         1,
        "description":  "Full stack + diplomacy — peace formation enabled",
        "use_tick_engine": True,
        "features": {
            "events":          True,
            "factions":        True,
            "border_friction": True,
            "recruitment":     True,
            "adjacency_bonus": True,
            "oscillation":     True,
            "technology":      True,
            "diplomacy":       True,
        },
        "overrides": {},
    },
}


# ═════════════════════════════════════════════════════════════════════════════
#  SIMULATION RUNNER
# ═════════════════════════════════════════════════════════════════════════════

def _apply_features(features: dict):
    """Set config flags from scenario features dict."""
    config.ENABLE_EVENTS          = features.get("events", False)
    config.ENABLE_FACTIONS        = features.get("factions", False)
    config.ENABLE_BORDER_FRICTION = features.get("border_friction", False)
    config.ENABLE_RECRUITMENT     = features.get("recruitment", True)
    config.ENABLE_ADJACENCY_BONUS = features.get("adjacency_bonus", True)
    config.ENABLE_OSCILLATION     = features.get("oscillation", True)
    config.ENABLE_EVENTS_STAGE2   = features.get("events", False)
    config.ENABLE_TECHNOLOGY      = features.get("technology", False)
    config.ENABLE_DIPLOMACY       = features.get("diplomacy", False)
    config.DIAGNOSTIC_PRINTS      = False


def _apply_overrides(overrides: dict):
    """Apply any config constant overrides from the scenario."""
    for key, val in overrides.items():
        setattr(config, key, val)


def run_scenario(name: str, scenario: dict, seed_override: int | None = None) -> dict:
    """
    Run a single scenario. Returns:
    {
        "ticks_list": [0, 1, 2, ...],
        "faction_data": {
            "faction_id": {
                "display_name": str,
                "archetype": str,
                "fields": {"military": [...], "economy": [...], ...},
            }
        },
        "region_counts": {"faction_id": int},   # final region counts
        "events_fired": int,
        "conquests": int,
    }
    """
    seed_used = seed_override if seed_override is not None else scenario["seed"]
    print(f"\n{'─'*60}")
    print(f"  Scenario: {name}")
    print(f"  {scenario['description']}")
    print(f"  Template: {scenario['template']}  |  Ticks: {scenario['ticks']}  |  Seed: {seed_used}")
    print(f"{'─'*60}")

    # Apply config
    _apply_features(scenario["features"])
    _apply_overrides(scenario.get("overrides", {}))

    # Generate world
    template = scenario["template"]
    seed = seed_used
    ticks = scenario["ticks"]
    w = world_mod.generate(template, seed=seed)

    # Generate factions
    try:
        factions = faction_mod.generate_starting_factions(template, rng=w.rng, world=w)
        registry = faction_mod.make_registry(*factions)
    except ValueError:
        # Template has no defined factions (e.g. s1_isolated)
        registry = {}
        # For s1_isolated, all regions belong to "player" — make a minimal faction
        faction_ids_in_world = {r.faction_id for r in w.regions.values() if r.faction_id}
        for fid in faction_ids_in_world:
            registry[fid] = faction_mod.Faction(
                fid, fid.title(), "player_civilization",
                budget=0.0, rng=w.rng,
            )

    # Event system setup
    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()

    # Determine which fields to track
    base_fields = ["military", "economy", "tension", "population"]
    track_tech = scenario["features"].get("technology", False)

    # Discover all faction IDs present in the world
    all_faction_ids = sorted({r.faction_id for r in w.regions.values() if r.faction_id})

    # Initialize data collection
    faction_data = {}
    for fid in all_faction_ids:
        fac = registry.get(fid)
        display = fac.name if fac else fid.title()
        archetype = fac.archetype if fac else "unknown"
        faction_data[fid] = {
            "display_name": f"{display} ({archetype})",
            "archetype": archetype,
            "fields": {f: [] for f in base_fields},
        }
        if track_tech:
            faction_data[fid]["fields"]["tech_level"] = []

    ticks_list = []
    total_events = 0
    total_conquests = 0
    event_log = []  # [{"tick": int, "name": str, "region_id": str}, ...]

    # ── Record initial state (tick 0) ────────────────────────────────────────
    def sample(tick_num):
        ticks_list.append(tick_num)
        for fid in list(faction_data.keys()):
            owned = [r for r in w.regions.values() if r.faction_id == fid]
            if not owned:
                # Faction lost all regions — fill with None/0
                for field in base_fields:
                    faction_data[fid]["fields"][field].append(0.0)
                if track_tech:
                    faction_data[fid]["fields"]["tech_level"].append(0.0)
                continue
            for field in base_fields:
                avg = sum(r.fields[field] for r in owned) / len(owned)
                faction_data[fid]["fields"][field].append(avg)
            if track_tech:
                fac = registry.get(fid)
                faction_data[fid]["fields"]["tech_level"].append(
                    fac.tech_level if fac and hasattr(fac, "tech_level") else 0.0
                )

        # Check for new factions (breakaways etc.)
        current_fids = {r.faction_id for r in w.regions.values() if r.faction_id}
        for fid in current_fids - set(faction_data.keys()):
            fac = registry.get(fid)
            display = fac.name if fac else fid.title()
            archetype = fac.archetype if fac else "breakaway"
            faction_data[fid] = {
                "display_name": f"{display} ({archetype})",
                "archetype": archetype,
                "fields": {f: [0.0] * len(ticks_list) for f in base_fields},
            }
            if track_tech:
                faction_data[fid]["fields"]["tech_level"] = [0.0] * len(ticks_list)
            # Back-fill with final sample
            owned = [r for r in w.regions.values() if r.faction_id == fid]
            if owned:
                for field in base_fields:
                    faction_data[fid]["fields"][field][-1] = sum(r.fields[field] for r in owned) / len(owned)
                if track_tech and fac:
                    faction_data[fid]["fields"]["tech_level"][-1] = fac.tech_level

    sample(0)

    # ── Main simulation loop ─────────────────────────────────────────────────
    if scenario.get("use_tick_engine", False):
        # Full tick engine — agents, attacks, conquests, the works
        pending_telegraphs = []
        for t in range(1, ticks + 1):
            log = _tick.run_tick(
                w, t,
                pending_queue=pending_queue,
                noise_offsets=noise_offsets,
                trigger_state=trigger_state,
                registry=registry if config.ENABLE_FACTIONS else None,
                pending_telegraphs=pending_telegraphs,
            )
            total_events += len(log.get("events", []))
            for evt in log.get("events", []):
                event_log.append({"tick": t, "name": evt.get("name", evt.get("template_id", "?")), "region_id": evt.get("region_id", "?")})
            total_conquests += len(log.get("conquests", []))
            for col in log.get("colonizations", []):
                event_log.append({"tick": t, "name": "Colonization", "region_id": col.get("region_id", "?")})
            sample(t)
    else:
        # Manual drift loop — no agent decisions, just drift + optional events
        for t in range(1, ticks + 1):
            # Events
            if config.ENABLE_EVENTS:
                fired = _events.resolve_pending(pending_queue, w, t, w.rng)
                total_events += len(fired)
                for evt in fired:
                    event_log.append({"tick": t, "name": evt.get("name", evt.get("template_id", "?")), "region_id": evt.get("region_id", "?")})
                for region in w.inhabited_regions():
                    triggered_ids = _events.evaluate_triggers(region, noise_offsets, trigger_state, tick=t, rng=w.rng)
                    for tid in triggered_ids:
                        chain_tag = f"{tid}_{region.id}_t{t}"
                        result = _events.fire_event(tid, region, t, chain_tag, w.rng)
                        total_events += 1
                        event_log.append({"tick": t, "name": result.get("name", tid), "region_id": region.id})
                        for spawn in result["spawns"]:
                            pending_queue.enqueue(spawn)

            # Budget accumulation (even without full agent loop)
            for fac in registry.values():
                fac.accumulate_budget(w)

            # Border friction
            if config.ENABLE_BORDER_FRICTION:
                for region in w.inhabited_regions():
                    if region.faction_id is None:
                        continue
                    for neighbor_id in w.get_neighbors(region.id):
                        neighbor = w.regions[neighbor_id]
                        if neighbor.faction_id is None or neighbor.faction_id == region.faction_id:
                            continue
                        our_fac = registry.get(region.faction_id)
                        their_fac = registry.get(neighbor.faction_id)
                        our_stance = our_fac.diplomatic_stance.get(neighbor.faction_id, "hostile") if our_fac else "hostile"
                        their_stance = their_fac.diplomatic_stance.get(region.faction_id, "hostile") if their_fac else "hostile"
                        if our_stance == "hostile" or their_stance == "hostile":
                            region.fields["tension"] = min(100.0, region.fields["tension"] + config.BORDER_FRICTION_TENSION)
                            region.fields["economy"] = max(config.ECONOMY_FLOOR, region.fields["economy"] - config.BORDER_FRICTION_ECONOMY)
                            region.recompute_composites()

            # Drift
            for region in w.inhabited_regions():
                modifier = {}
                if region.faction_id in registry:
                    modifier = registry[region.faction_id].modifiers
                adj_bonus = 0.0
                if config.ENABLE_ADJACENCY_BONUS:
                    for nr in w.allied_inhabited_neighbors(region.id):
                        adj_bonus += config.NEIGHBOR_ECONOMY_BONUS * (nr.fields["economy"] / 100.0)
                    if config.ENABLE_DIPLOMACY and region.faction_id:
                        for nid in w.get_neighbors(region.id):
                            nr = w.regions.get(nid)
                            if (nr and nr.tier != "empty" and nr.faction_id
                                    and nr.faction_id != region.faction_id):
                                our_stance = registry[region.faction_id].diplomatic_stance.get(nr.faction_id, "hostile")
                                if our_stance == "cooperative":
                                    adj_bonus += config.NEIGHBOR_ECONOMY_BONUS * (nr.fields["economy"] / 100.0)
                deltas = _drift.compute_drift_deltas(
                    region, tick=t,
                    faction_modifier=modifier,
                    adjacency_bonus=adj_bonus,
                )
                _drift.apply_drift_deltas(region, deltas)

            # Tech growth
            if config.ENABLE_TECHNOLOGY:
                for fac in registry.values():
                    _tech.grow_tech(fac, w)

            sample(t)

    # ── Final region counts ──────────────────────────────────────────────────
    region_counts = {}
    for fid in faction_data:
        region_counts[fid] = len([r for r in w.regions.values() if r.faction_id == fid])

    # ── Print summary ────────────────────────────────────────────────────────
    print(f"\n  Results (tick {ticks}):")
    print(f"  {'Faction':<30} {'Regions':>7} {'Mil':>6} {'Eco':>6} {'Ten':>6} {'Pop':>6}", end="")
    if track_tech:
        print(f" {'Tech':>6}", end="")
    print()
    print(f"  {'─'*30} {'─'*7} {'─'*6} {'─'*6} {'─'*6} {'─'*6}", end="")
    if track_tech:
        print(f" {'─'*6}", end="")
    print()

    for fid, fdata in faction_data.items():
        n = region_counts[fid]
        mil = fdata["fields"]["military"][-1] if fdata["fields"]["military"] else 0
        eco = fdata["fields"]["economy"][-1] if fdata["fields"]["economy"] else 0
        ten = fdata["fields"]["tension"][-1] if fdata["fields"]["tension"] else 0
        pop = fdata["fields"]["population"][-1] if fdata["fields"]["population"] else 0
        row = f"  {fdata['display_name']:<30} {n:>7} {mil:>6.1f} {eco:>6.1f} {ten:>6.1f} {pop:>6.1f}"
        if track_tech:
            tech = fdata["fields"]["tech_level"][-1] if fdata["fields"].get("tech_level") else 0
            row += f" {tech:>6.1f}"
        print(row)

    print(f"\n  Events fired: {total_events}  |  Conquests: {total_conquests}")
    if event_log:
        from collections import Counter
        counts = Counter(e["name"] for e in event_log)
        for name, count in counts.most_common():
            print(f"    {count:>3}× {name}")

    return {
        "ticks_list": ticks_list,
        "faction_data": faction_data,
        "region_counts": region_counts,
        "events_fired": total_events,
        "conquests": total_conquests,
        "event_log": event_log,
    }


# ═════════════════════════════════════════════════════════════════════════════
#  GRAPH GENERATION
# ═════════════════════════════════════════════════════════════════════════════

def generate_graphs(name: str, scenario: dict, result: dict):
    """Produce all PNGs for a single-run (non-variant) scenario."""
    ticks_list = result["ticks_list"]
    faction_data = result["faction_data"]
    region_counts = result["region_counts"]

    base_fields = ["military", "economy", "tension", "population"]
    track_tech = scenario["features"].get("technology", False)
    all_fields = base_fields + (["tech_level"] if track_tech else [])

    # Build extra info string
    features_on = [k for k, v in scenario["features"].items() if v]
    extra = f"seed={scenario['seed']}  ticks={scenario['ticks']}  features: {', '.join(features_on)}"
    extra += f"\nevents={result['events_fired']}  conquests={result['conquests']}"

    # 1. Full overlay graph
    overlay_path = os.path.join(OUT_DIR, f"{name}_all.png")
    sim_graph.make_scenario_graph(
        scenario_name=name,
        description=scenario["description"],
        ticks_list=ticks_list,
        faction_data=faction_data,
        fields=all_fields,
        output_path=overlay_path,
        region_counts=region_counts,
        extra_info=extra,
        event_log=result.get("event_log", []),
    )
    print(f"  Saved: {overlay_path}")

    # 2. Per-field comparison graphs (only for multi-faction scenarios)
    if len(faction_data) >= 2:
        for field in all_fields:
            field_path = os.path.join(OUT_DIR, f"{name}_{field}.png")
            sim_graph.make_field_comparison(
                scenario_name=name,
                ticks_list=ticks_list,
                faction_data=faction_data,
                field=field,
                output_path=field_path,
            )
            print(f"  Saved: {field_path}")


def generate_variant_graphs(name: str, scenario: dict, variant_results: list):
    """Produce side-by-side PNG for variant scenarios, plus individual overlays."""
    base_fields = ["military", "economy", "tension", "population"]
    track_tech = scenario["features"].get("technology", False)
    all_fields = base_fields + (["tech_level"] if track_tech else [])
    features_on = [k for k, v in scenario["features"].items() if v]

    # Build variant_results in the format sim_graph expects
    panel_data = []
    for vr in variant_results:
        result = vr["result"]
        variant_def = vr["variant"]
        resolved_seed = variant_def.get("_resolved_seed", scenario["seed"])
        # Filter out _seed from displayed overrides
        overrides_str = ", ".join(f"{k}={v}" for k, v in variant_def.get("overrides", {}).items() if k != "_seed")
        extra = f"seed={resolved_seed}  ticks={scenario['ticks']}"
        if overrides_str:
            extra += f"\n{overrides_str}"
        extra += f"\nevents={result['events_fired']}  conquests={result['conquests']}"
        # Append seed to label for clarity
        label = variant_def["label"]
        if variant_def.get("overrides", {}).get("_seed") == "random":
            label += f" (seed={resolved_seed})"
        panel_data.append({
            "label": label,
            "ticks_list": result["ticks_list"],
            "faction_data": result["faction_data"],
            "region_counts": result["region_counts"],
            "extra_info": extra,
            "event_log": result.get("event_log", []),
        })

    # Side-by-side graph
    sidebyside_path = os.path.join(OUT_DIR, f"{name}_compare.png")
    sim_graph.make_sidebyside_graph(
        scenario_name=f"{name}\n{scenario['description']}",
        variant_results=panel_data,
        fields=all_fields,
        output_path=sidebyside_path,
    )
    print(f"  Saved: {sidebyside_path}")


def _snapshot_config(keys: list) -> dict:
    """Save current config values for the given keys."""
    return {k: getattr(config, k) for k in keys if hasattr(config, k)}


def _restore_config(snapshot: dict):
    """Restore config values from a snapshot."""
    for k, v in snapshot.items():
        setattr(config, k, v)


# ═════════════════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    if "--list" in args:
        print("\nAvailable scenarios:")
        for name, sc in SCENARIOS.items():
            n_variants = len(sc.get("variants", []))
            suffix = f"  ({n_variants} variants)" if n_variants else ""
            print(f"  {name:<25} {sc['description']}{suffix}")
        return

    # Which scenarios to run
    if args:
        to_run = [(name, SCENARIOS[name]) for name in args if name in SCENARIOS]
        unknown = [a for a in args if a not in SCENARIOS and a != "--list"]
        if unknown:
            print(f"Unknown scenarios: {unknown}")
            print(f"Available: {list(SCENARIOS.keys())}")
            return
    else:
        to_run = list(SCENARIOS.items())

    print(f"\n{'═'*60}")
    print(f"  Simulation Tuner — Ouroboros Manifold")
    print(f"  Running {len(to_run)} scenario(s)")
    print(f"  Output: {OUT_DIR}")
    print(f"{'═'*60}")

    for name, scenario in to_run:
        variants = scenario.get("variants")

        if variants:
            # ── Variant mode: run each variant, then produce side-by-side ────
            # Collect all override keys across all variants so we can restore them
            all_override_keys = set()
            for v in variants:
                all_override_keys.update(v.get("overrides", {}).keys())
            all_override_keys.update(scenario.get("overrides", {}).keys())
            config_backup = _snapshot_config(list(all_override_keys))

            variant_results = []
            for v_idx, variant in enumerate(variants):
                # Restore clean config before each variant
                _restore_config(config_backup)
                # Apply scenario-level overrides first, then variant overrides on top
                _apply_overrides(scenario.get("overrides", {}))
                # Filter out special _seed key before applying to config
                v_overrides = {k: v for k, v in variant.get("overrides", {}).items() if k != "_seed"}
                _apply_overrides(v_overrides)

                # Extract per-variant seed override
                v_seed_raw = variant.get("overrides", {}).get("_seed", None)
                if v_seed_raw == "random":
                    import time
                    v_seed = int(time.time() * 1000) % 100000 + v_idx
                else:
                    v_seed = v_seed_raw

                print(f"\n  ▸ Variant {v_idx+1}/{len(variants)}: {variant['label']} (seed={v_seed})")
                override_desc = ", ".join(f"{k}={v}" for k, v in variant.get("overrides", {}).items() if k != "_seed")
                if override_desc:
                    print(f"    Overrides: {override_desc}")

                result = run_scenario(name, scenario, seed_override=v_seed)
                # Store resolved seed so graph label can show it
                variant_with_seed = dict(variant)
                variant_with_seed["_resolved_seed"] = v_seed
                variant_results.append({"variant": variant_with_seed, "result": result})

            # Restore config
            _restore_config(config_backup)

            # Generate side-by-side graph
            generate_variant_graphs(name, scenario, variant_results)
        else:
            # ── Standard single-run mode ─────────────────────────────────────
            result = run_scenario(name, scenario)
            generate_graphs(name, scenario, result)

    print(f"\n{'═'*60}")
    print(f"  Done. All PNGs in: {OUT_DIR}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
