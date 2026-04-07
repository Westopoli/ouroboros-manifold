# Input:  World, optional PendingQueue + noise_offsets (required when ENABLE_EVENTS=True)
#         registry: {faction_id: Faction} when ENABLE_FACTIONS=True
#         antagonist: Antagonist when ENABLE_FACTIONS=False (backward compat)
# Output: mutates world in place each tick; returns tick log dict
#
# 7-step tick resolution sequence (Stage 0 revision):
#   1. Resolve pending events
#   2. Evaluate fresh threshold triggers
#   3. Run all faction agents  (was: single antagonist)
#   4. Apply border friction   (new)
#   5. Apply passive drift     (military now includes recruitment term)
#   6. Recompute composites    (happens inside apply_drift_deltas)
#   7. Log everything

import config
import drift as _drift
import events as _events
import intent_resolver as _intent_resolver
import technology as _technology
import diplomacy as _diplomacy
import admin_revolt as _admin_revolt

_SHORT_NAMES = {
    "player": "pl", "conqueror": "conq", "fortifier": "fort", "opportunist": "opp",
}

def _short(fid):
    for key, val in _SHORT_NAMES.items():
        if key in fid:
            return val
    return fid[:8]


def run_tick(world, tick_num: int, ledger=None,
             pending_queue=None, noise_offsets=None, trigger_state=None,
             registry=None, antagonist=None, stances=None,
             pending_telegraphs=None,
             coherence_ledger=None) -> dict:
    log = {
        "tick":            tick_num,
        "events":          [],
        "faction_actions": [],
        "antagonist":      None,
        "border_friction": {},
        "diplomatic_events": [],
        "betrayals":       [],
        "tech_growth":     {},
        "drift":           {},
        "revolts":         [],
        "admin_revolts":   [],
        "conquests":       [],
        "colonizations":   [],
        "collisions":      [],
        "factions_absorbed": [],
        "event_attachments": [],
    }

    rng = world.rng

    # ── Steps 1–2: Event system ──────────────────────────────────────────────
    if config.ENABLE_EVENTS:
        # Step 1: resolve pending events
        fired = _events.resolve_pending(pending_queue, world, tick_num, rng)
        log["events"].extend(fired)

        # Step 2: evaluate fresh threshold triggers
        for region in world.inhabited_regions():
            triggered_ids = _events.evaluate_triggers(region, noise_offsets, trigger_state, tick=tick_num, rng=rng)
            for tid in triggered_ids:
                chain_tag = f"{tid}_{region.id}_t{tick_num}"
                result    = _events.fire_event(tid, region, tick_num, chain_tag, rng)
                spawn_dicts = result["spawns"]
                for spawn in spawn_dicts:
                    pending_queue.enqueue(spawn)
                result["spawns"] = [
                    f"{s['template_id']}@tick_{s['due_tick']}" for s in spawn_dicts
                ]
                log["events"].append(result)

        # L4: handle revolt faction creation from any fired event
        if registry is not None:
            for evt in log["events"]:
                if evt.get("creates_faction"):
                    revolt_log = _handle_revolt_faction_creation(
                        evt, world, registry, rng, tick_num
                    )
                    if revolt_log:
                        log["revolts"].append(revolt_log)
                        if ledger is not None:
                            ledger.log_revolt(tick_num, revolt_log)
                        if coherence_ledger is not None and revolt_log.get("new_faction"):
                            new_fid = revolt_log["new_faction"]
                            rid = revolt_log["region"]
                            coherence_ledger.assign_faction_leader(new_fid, rid, tick_num, rng)

    # ── Step 3: Faction agents — two-phase telegraph/surprise resolution ─────
    if pending_telegraphs is None:
        pending_telegraphs = []

    if registry is not None and config.ENABLE_FACTIONS:
        # 3a: Snapshot (before any mutations this tick)
        snapshot = _build_snapshot(world)
        # 3b: Accumulate budget
        for faction in list(registry.values()):
            faction.accumulate_budget(world)

        # 3c: Resolve pending telegraphed attacks from previous tick(s)
        due_now = [t for t in pending_telegraphs if t["due_tick"] <= tick_num]
        for t in due_now:
            pending_telegraphs.remove(t)
        if due_now:
            fresh_snap = _build_snapshot(world)
            due_intents = [t["intent"] for t in due_now]
            resolved_due = _intent_resolver.resolve(due_intents, fresh_snap, registry, rng, tick=tick_num)
            for action in resolved_due:
                log["faction_actions"].append(action)
                _apply_resolved_action(world, registry, action, pending_queue, ledger, tick_num)
                if action.get("conquest"):
                    log["conquests"].append(action["conquest"])
                if action.get("colonization"):
                    log["colonizations"].append(action["colonization"])
                if action.get("significance") == "collision" and action.get("outcome_band") == "collision":
                    log["collisions"].append(action["log"])

        # 3d: Normal faction decisions (attack/colonize/accumulate)
        intents = []
        for faction in list(registry.values()):
            intent = faction.decide(snapshot, world.adjacency, registry, rng, tick_num)
            intents.append(intent)

        # Split intents: surprise attacks resolve now, telegraphed go to pending
        immediate_intents = []
        new_telegraphs = []
        for intent in intents:
            if intent["action"] == "attack" and intent.get("attack_mode") == "telegraph":
                target_rid = intent["target_region"]
                target_faction = snapshot[target_rid]["faction_id"] if target_rid in snapshot else None
                new_telegraphs.append({
                    "faction_id":       intent["faction_id"],
                    "target_region":    target_rid,
                    "target_faction":   target_faction,
                    "budget_committed": intent["budget_committed"],
                    "due_tick":         tick_num + config.TELEGRAPH_PREP_TICKS,
                    "source_region":    intent.get("source_region"),
                    "intent":           intent,
                })
            else:
                immediate_intents.append(intent)

        # 3e: Reactive reinforce phase — defenders respond to new telegraphs
        if new_telegraphs:
            for faction in list(registry.values()):
                reactive = faction.decide_reactive(new_telegraphs, snapshot, rng)
                if reactive is not None:
                    immediate_intents.append(reactive)
            pending_telegraphs.extend(new_telegraphs)

        # 3f: Resolve immediate intents (surprise attacks, colonize, accumulate, reactive reinforce)
        resolved = _intent_resolver.resolve(immediate_intents, snapshot, registry, rng, tick=tick_num)
        for action in resolved:
            log["faction_actions"].append(action)
            _apply_resolved_action(world, registry, action, pending_queue, ledger, tick_num)
            if action.get("conquest"):
                log["conquests"].append(action["conquest"])
            if action.get("colonization"):
                log["colonizations"].append(action["colonization"])
            if action.get("significance") == "collision" and action.get("outcome_band") == "collision":
                log["collisions"].append(action["log"])

        if config.DIAGNOSTIC_PRINTS:
            # ── DIAGNOSTIC — windowed snapshots + all significant events ─────
            in_window   = tick_num <= 5 or (248 <= tick_num <= 252) or tick_num >= 496
            is_round    = tick_num in (5, 252, 500)

            all_intents = intents  # includes both immediate and telegraphed
            sig_factions = [
                faction.id for faction in registry.values()
                if next((i for i in all_intents if i["faction_id"] == faction.id), {}).get("action")
                   in ("attack", "colonize")
            ]
            any_significant = (bool(sig_factions) or bool(log.get("conquests"))
                               or bool(log.get("revolts")) or bool(due_now))

            if in_window or any_significant or is_round:
                print(f"\n── t={tick_num} ──")

                # Show due telegraphed attacks that resolved this tick
                for t in due_now:
                    fid = t["faction_id"]
                    tgt = t["target_region"].replace("region_", "")
                    print(f"  t={tick_num:>4} {_short(fid):<5}  TELEGRAPH LANDS  → {tgt}")

                for faction in list(registry.values()):
                    mi = next((i for i in all_intents if i["faction_id"] == faction.id), None)
                    mr = next((a for a in resolved if a["faction_id"] == faction.id), None)
                    if not mi:
                        continue
                    if not in_window and faction.id not in sig_factions:
                        continue

                    act = mi["action"]
                    tgt_rid = mi.get("target_region")
                    tgt = tgt_rid.replace("region_", "") if tgt_rid else "—"

                    suffix = ""
                    if act == "attack":
                        mode = mi.get("attack_mode", "surprise")
                        if mode == "telegraph":
                            suffix = f" [TELEGRAPH → t={tick_num + config.TELEGRAPH_PREP_TICKS}]"
                        else:
                            band = mr.get("outcome_band", "") if mr else ""
                            suffix = f" [surprise] <<< {band}"
                            if mr and mr.get("conquest"):
                                suffix += " CONQUEST!"
                            tgt_mil = snapshot[tgt_rid]["fields"]["military"] if tgt_rid and tgt_rid in snapshot else None
                            if tgt_mil is not None:
                                suffix += f"  def_mil={tgt_mil:.1f}"
                    elif act == "colonize":
                        suffix = " <<<"

                    budget_before = faction.budget + (mr['budget_spent'] if mr else 0)
                    spent = mr['budget_spent'] if mr else 0
                    print(
                        f"  t={tick_num:>4} {_short(faction.id):<5}"
                        f"  b={budget_before:>6.1f}"
                        f"  {act:<10}"
                        f"  spent={spent:>5.1f}"
                        f"  rem={faction.budget:>6.1f}"
                        f"  {tgt}{suffix}"
                    )

                if is_round:
                    ownership = {}
                    for rid, r in world.regions.items():
                        fid = r.faction_id or "—"
                        ownership.setdefault(fid, []).append(rid.replace("region_", ""))
                    for fid, rids in sorted(ownership.items()):
                        print(f"    {_short(fid):<5} [{len(rids)}]: {', '.join(sorted(rids))}")

    elif config.ENABLE_ANTAGONIST and antagonist is not None:
        # Backward-compat path for Groups A–E tests
        ant_log = antagonist.act(world.inhabited_regions())
        log["antagonist"] = ant_log
        if ledger is not None:
            ledger.log_antagonist(
                tick_num, ant_log["budget"],
                ant_log["allocation"], ant_log["applied"]
            )

    # ── Step 3.5: Betrayal checks on cooperative pairs ─────────────────────
    if config.ENABLE_DIPLOMACY and registry is not None and stances is not None:
        betrayals = _diplomacy.check_betrayals(stances, registry, world, rng, tick_num)
        log["betrayals"] = betrayals
        for b in betrayals:
            if b["attack_target_region"]:
                intent = {
                    "faction_id": b["betrayer"],
                    "action": "attack",
                    "target_region": b["attack_target_region"],
                    "budget_committed": registry[b["betrayer"]].budget,
                    "is_betrayal": True,
                }
                snap = _build_snapshot(world)
                resolved = _intent_resolver.resolve(
                    [intent], snap, registry, rng, tick=tick_num
                )
                for action in resolved:
                    action["is_betrayal"] = True
                    log["faction_actions"].append(action)
                    _apply_resolved_action(world, registry, action, pending_queue, ledger, tick_num)
                    if action.get("conquest"):
                        log["conquests"].append(action["conquest"])

    # ── Step 4: Border friction ──────────────────────────────────────────────
    if config.ENABLE_BORDER_FRICTION and registry is not None:
        friction_log = _apply_border_friction(world, registry)
        log["border_friction"] = friction_log

    # ── Step 4.1: Admin revolt checks ───────────────────────────────────────
    if config.ENABLE_ADMIN_REVOLTS and registry is not None:
        admin_log = _admin_revolt.check_admin_revolts(
            world, registry, pending_queue, rng, tick_num
        )
        log["admin_revolts"] = admin_log

    # ── Step 4.25: Diplomacy — timers + peace formation ─────────────────────
    if config.ENABLE_DIPLOMACY and registry is not None and stances is not None:
        _diplomacy.update_timers(stances, registry, world, log)
        diplo_events = _diplomacy.check_peace_formation(
            stances, registry, world, rng, tick_num, log
        )
        log["diplomatic_events"] = diplo_events

    # ── Step 4.5: Technology growth + convergence ─────────────────────────────
    if config.ENABLE_TECHNOLOGY and registry is not None:
        for faction in registry.values():
            entry = _technology.grow_tech(faction, world)
            if entry is not None:
                log["tech_growth"][faction.id] = entry
        if config.ENABLE_DIPLOMACY and stances is not None:
            for faction in registry.values():
                conv = _technology.apply_convergence(faction, registry, stances)
                if conv is not None:
                    log["tech_growth"].setdefault(faction.id, {})["convergence"] = conv

    # ── Step 5: Passive drift (with optional faction modifiers + adjacency) ──
    for region in world.inhabited_regions():
        modifier = {}
        if registry is not None and region.faction_id in registry:
            modifier = registry[region.faction_id].modifiers
        adj_bonus = 0.0
        if config.ENABLE_ADJACENCY_BONUS:
            for nr in world.allied_inhabited_neighbors(region.id):
                adj_bonus += config.NEIGHBOR_ECONOMY_BONUS * (nr.fields["economy"] / 100.0)
            # Cooperative-faction neighbors also contribute adjacency bonus
            if config.ENABLE_DIPLOMACY and registry and region.faction_id and region.faction_id in registry:
                for nid in world.get_neighbors(region.id):
                    nr = world.regions.get(nid)
                    if (nr and nr.tier != "empty" and nr.faction_id
                            and nr.faction_id != region.faction_id):
                        our_stance = registry[region.faction_id].diplomatic_stance.get(nr.faction_id, "hostile")
                        if our_stance == "cooperative":
                            adj_bonus += config.NEIGHBOR_ECONOMY_BONUS * (nr.fields["economy"] / 100.0)
        deltas = _drift.compute_drift_deltas(
            region, tick=tick_num,
            faction_modifier=modifier,
            adjacency_bonus=adj_bonus,
        )
        _drift.apply_drift_deltas(region, deltas)
        log["drift"][region.id] = deltas

    # ── Step 6: Zombie faction cleanup ─────────────────────────────────────
    if registry is not None:
        log["factions_absorbed"] = _cleanup_zombie_factions(world, registry, tick_num)

    # ── Step 6.5: Coherence ledger — character attachment + leader cleanup ──
    if coherence_ledger is not None:
        for absorbed in log["factions_absorbed"]:
            leader = coherence_ledger.get_faction_leader(absorbed["faction"])
            if leader:
                coherence_ledger.kill_character(leader.id, tick_num)
        for evt in log["events"]:
            attached = coherence_ledger.attach_event(evt, evt["region_id"], tick_num)
            if attached:
                log["event_attachments"].append({
                    "character_id": attached.id,
                    "character_name": attached.name,
                    "rank": attached.rank,
                    "event_template": evt.get("template_id"),
                    "region_id": evt["region_id"],
                })

    # ── Step 7: Log ──────────────────────────────────────────────────────────
    if ledger is not None:
        for evt in log["events"]:
            ledger.log_event(
                tick_num, evt["region_id"], evt["template_id"],
                evt["name"], evt["field_deltas"],
                evt["chain_tag"], evt["spawns"]
            )
        ledger.log_snapshot(tick_num, world)

    return log


def run_ticks(world, n: int, ledger=None,
              pending_queue=None, noise_offsets=None, trigger_state=None,
              registry=None, antagonist=None, stances=None) -> list:
    pending_telegraphs = []
    logs = []
    for t in range(n):
        log = run_tick(world, t + 1, ledger, pending_queue, noise_offsets, trigger_state,
                       registry, antagonist, stances,
                       pending_telegraphs=pending_telegraphs)
        logs.append(log)
    return logs


# ── F3: Snapshot builder ─────────────────────────────────────────────────────

def _build_snapshot(world) -> dict:
    return {
        rid: {
            "fields":     dict(r.fields),
            "faction_id": r.faction_id,
            "tier":       r.tier,
            "held_since_tick": r.held_since_tick,
            "previous_faction_id": r.previous_faction_id,
        }
        for rid, r in world.regions.items()
    }


# ── F3: Apply a single resolved action to live world state ───────────────────

def _apply_resolved_action(world, registry, action, pending_queue, ledger, tick_num):
    fid     = action["faction_id"]
    faction = registry.get(fid)

    if faction and action["budget_spent"] > 0:
        faction.budget = max(0.0, faction.budget - action["budget_spent"])

    if action.get("colonization"):
        col    = action["colonization"]
        region = world.regions[col["region_id"]]
        region.faction_id = col["faction_id"]
        region.tier       = "frontier"

    if action.get("conquest"):
        con    = action["conquest"]
        region = world.regions[con["region_id"]]
        region.previous_faction_id = con["old_faction_id"]
        region.faction_id = con["new_faction_id"]

    bypass_floor = action.get("log", {}).get("bypass_floor", False)
    for rid, deltas in action["deltas"].items():
        region = world.regions.get(rid)
        if region is None:
            continue
        for field, delta in deltas.items():
            old_val = region.fields.get(field, 0.0)
            new_val = old_val + delta
            if field == "economy":
                floor = 0.0 if bypass_floor else config.ECONOMY_FLOOR
                new_val = max(floor, min(100.0, new_val))
            else:
                new_val = max(0.0, min(100.0, new_val))
            region.fields[field] = new_val
        region.recompute_composites()

    # Apply garrison military after battle damage is resolved
    if action.get("conquest") and action["conquest"].get("garrison"):
        con_region = world.regions[action["conquest"]["region_id"]]
        garrison = action["conquest"]["garrison"]
        con_region.fields["military"] = min(100.0, con_region.fields["military"] + garrison)
        con_region.held_since_tick = tick_num
        if con_region.fields["population"] < config.COLONY_START_POPULATION:
            con_region.fields["population"] = config.COLONY_START_POPULATION
        if con_region.fields["economy"] < config.COLONY_START_ECONOMY:
            con_region.fields["economy"] = config.COLONY_START_ECONOMY
        con_region.recompute_composites()

    if action.get("colonization"):
        col_region = world.regions[action["colonization"]["region_id"]]
        col_region.held_since_tick = tick_num

    if pending_queue is not None:
        for spawn in action.get("chain_spawns", []):
            pending_queue.enqueue(spawn)


# ── J2: Border friction helper ────────────────────────────────────────────────

def _apply_border_friction(world, registry: dict) -> dict:
    friction_log = {}
    for region in world.inhabited_regions():
        if region.faction_id is None:
            continue
        total_ten = 0.0
        total_eco = 0.0
        for neighbor_id in world.get_neighbors(region.id):
            neighbor = world.regions[neighbor_id]
            if neighbor.faction_id is None or neighbor.faction_id == region.faction_id:
                continue
            our_faction  = registry.get(region.faction_id)
            their_faction = registry.get(neighbor.faction_id)
            our_stance   = our_faction.diplomatic_stance.get(neighbor.faction_id, "neutral") if our_faction else "neutral"
            their_stance = their_faction.diplomatic_stance.get(region.faction_id, "neutral") if their_faction else "neutral"
            if our_stance == "hostile" or their_stance == "hostile":
                total_ten += config.BORDER_FRICTION_TENSION
                total_eco += config.BORDER_FRICTION_ECONOMY
        if total_ten > 0.0 or total_eco > 0.0:
            region.fields["tension"] = min(100.0, region.fields["tension"] + total_ten)
            region.fields["economy"] = max(config.ECONOMY_FLOOR, region.fields["economy"] - total_eco)
            region.recompute_composites()
            friction_log[region.id] = {
                "tension": round(total_ten, 3),
                "economy": round(-total_eco, 3),
            }
    return friction_log


# ── L4: Revolt faction creation helper ───────────────────────────────────────

def _handle_revolt_faction_creation(evt: dict, world, registry: dict,
                                     rng, tick: int) -> dict | None:
    from faction import Faction

    region = world.regions.get(evt["region_id"])
    if region is None or region.faction_id is None:
        return None

    is_admin = evt.get("admin_revolt", False)

    if is_admin:
        source_fid = evt.get("source_faction_id")
        if source_fid and region.faction_id != source_fid:
            return None
        # Prune if ownership changed mid-chain (lost and re-conquered)
        chain_start = evt.get("chain_start_tick")
        if (chain_start is not None
                and region.held_since_tick is not None
                and region.held_since_tick > chain_start):
            return None
        success_rate = 1.0
    else:
        # Tension revolts: roll for breakaway formation
        lo, hi = config.REVOLT_SUCCESS_RANGE
        success_rate = rng.uniform(lo, hi)
        if rng.random() > success_rate:
            return None
        if region.fields["population"] < config.REVOLT_BREAKAWAY_POP_FLOOR:
            return None

    original_faction = region.faction_id

    # Steal resources from the region (applies to both reversion and breakaway)
    mil_stolen = region.fields["military"] * config.REVOLT_MILITARY_STEAL
    eco_stolen = region.fields["economy"]  * config.REVOLT_ECONOMY_STEAL
    region.fields["military"] = max(0.0, region.fields["military"] - mil_stolen)
    region.fields["economy"]  = max(0.0, region.fields["economy"]  - eco_stolen)
    region.recompute_composites()

    # Latent loyalty: recently conquered regions may revert to previous faction
    restore_previous = False
    if (region.previous_faction_id is not None
            and region.previous_faction_id != region.faction_id
            and region.held_since_tick is not None
            and (tick - region.held_since_tick) <= config.LATENT_LOYALTY_TICKS
            and rng.random() < config.LATENT_LOYALTY_REVERT_CHANCE):
        if region.previous_faction_id in registry:
            restore_previous = True

    if restore_previous:
        restored_fid = region.previous_faction_id
        region.faction_id = restored_fid
        region.previous_faction_id = None
        region.held_since_tick = tick

        region.fields["tension"] = min(region.fields["tension"], config.REVOLT_BREAKAWAY_TENSION_CAP)
        region.fields["population"] = max(region.fields["population"], config.REVOLT_BREAKAWAY_POP_FLOOR)
        region.fields["economy"] = max(region.fields["economy"], config.REVOLT_BREAKAWAY_ECO_FLOOR)
        region.recompute_composites()

        return {
            "type":             "reversion",
            "tick":             tick,
            "region":           region.id,
            "original_faction": original_faction,
            "restored_faction": restored_fid,
            "success_rate":     round(success_rate, 3),
            "military_stolen":  round(mil_stolen, 2),
            "economy_stolen":   round(eco_stolen, 2),
        }

    # Standard breakaway creation
    new_id   = f"breakaway_{tick}_{region.id}"
    new_name = f"Breakaway of {region.name}"

    region.previous_faction_id = original_faction
    region.faction_id = new_id

    region.fields["tension"] = min(region.fields["tension"], config.REVOLT_BREAKAWAY_TENSION_CAP)
    region.fields["population"] = max(region.fields["population"], config.REVOLT_BREAKAWAY_POP_FLOOR)
    region.fields["economy"] = max(region.fields["economy"], config.REVOLT_BREAKAWAY_ECO_FLOOR)
    region.recompute_composites()

    if evt.get("admin_revolt"):
        pool = ["conqueror", "fortifier", "warlord", "opportunist", "schism"]
        archetype = rng.choice(pool)
    else:
        archetype = "breakaway"

    new_faction = Faction(
        new_id, new_name, archetype,
        budget=0.0,
        diplomatic_stance={fid: "hostile" for fid in registry},
    )
    for fac in registry.values():
        fac.diplomatic_stance[new_id] = "hostile"

    registry[new_id] = new_faction
    if original_faction in registry:
        new_faction.tech_level = registry[original_faction].tech_level

    return {
        "type":             "revolt",
        "tick":             tick,
        "region":           region.id,
        "original_faction": original_faction,
        "new_faction":      new_id,
        "success_rate":     round(success_rate, 3),
        "military_stolen":  round(mil_stolen, 2),
        "economy_stolen":   round(eco_stolen, 2),
    }


def _cleanup_zombie_factions(world, registry, tick):
    absorbed = []
    to_remove = []

    # Pass 1: Remove ghost factions (0 regions for 5+ ticks)
    for fid, fac in list(registry.items()):
        if not fid.startswith("breakaway_"):
            continue
        owned = world.regions_by_faction(fid)
        if len(owned) == 0:
            parts = fid.split("_")
            spawn_tick = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            if (tick - spawn_tick) >= 5:
                to_remove.append(fid)
                absorbed.append({
                    "tick": tick, "faction": fid, "region": None,
                    "absorbed_by": None,
                })

    # Pass 2: Absorb single-region zombies
    for fid, fac in list(registry.items()):
        if not fid.startswith("breakaway_") or fid in to_remove:
            continue
        owned = world.regions_by_faction(fid)
        if len(owned) != 1:
            continue
        parts = fid.split("_")
        spawn_tick = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        if (tick - spawn_tick) < config.ZOMBIE_CLEANUP_TICKS:
            continue
        if fac.budget >= config.COLONIZE_COST:
            continue
        region = owned[0]
        best_absorber = None
        best_strength = 0
        for nid in world.get_neighbors(region.id):
            nb = world.regions.get(nid)
            if nb and nb.faction_id and nb.faction_id != fid and nb.faction_id in registry:
                strength = len(world.regions_by_faction(nb.faction_id))
                if strength > best_strength:
                    best_strength = strength
                    best_absorber = nb.faction_id
        if best_absorber is None:
            continue
        region.previous_faction_id = fid
        region.faction_id = best_absorber
        region.held_since_tick = tick
        to_remove.append(fid)
        absorbed.append({
            "tick": tick, "faction": fid, "region": region.id,
            "absorbed_by": best_absorber,
        })
    for fid in to_remove:
        for fac in registry.values():
            fac.diplomatic_stance.pop(fid, None)
        del registry[fid]
        for region in world.regions.values():
            if region.faction_id == fid:
                region.faction_id = None
                region.held_since_tick = None
    return absorbed
