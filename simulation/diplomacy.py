import config


def _pair_key(a: str, b: str) -> tuple:
    return tuple(sorted([a, b]))


def init_stances(registry: dict) -> dict:
    stances = {}
    faction_ids = list(registry.keys())
    for i, fid_a in enumerate(faction_ids):
        for fid_b in faction_ids[i + 1:]:
            key = _pair_key(fid_a, fid_b)
            arch_a = registry[fid_a].archetype
            arch_b = registry[fid_b].archetype
            stance = _starting_stance(arch_a, arch_b)
            stances[key] = {
                "stance": stance,
                "non_aggression_ticks": 0,
                "cooperative_since_tick": None,
            }
    sync_to_factions(stances, registry)
    return stances


def _starting_stance(arch_a: str, arch_b: str) -> str:
    overrides = config.STARTING_STANCE_OVERRIDES
    pair = tuple(sorted([arch_a, arch_b]))
    if pair in overrides:
        return overrides[pair]
    if (arch_a, arch_b) in overrides:
        return overrides[(arch_a, arch_b)]
    if (arch_b, arch_a) in overrides:
        return overrides[(arch_b, arch_a)]
    return "neutral"


def get_stance(stances: dict, a: str, b: str) -> str:
    if a == b:
        return "cooperative"
    key = _pair_key(a, b)
    entry = stances.get(key)
    return entry["stance"] if entry else "hostile"


def is_hostile(stances: dict, a: str, b: str) -> bool:
    return get_stance(stances, a, b) == "hostile"


def is_cooperative(stances: dict, a: str, b: str) -> bool:
    return get_stance(stances, a, b) == "cooperative"


def is_neutral(stances: dict, a: str, b: str) -> bool:
    return get_stance(stances, a, b) == "neutral"


def set_stance(stances: dict, a: str, b: str, stance: str,
               tick: int | None = None) -> None:
    key = _pair_key(a, b)
    if key not in stances:
        stances[key] = {"stance": stance, "non_aggression_ticks": 0, "cooperative_since_tick": None}
    stances[key]["stance"] = stance
    stances[key]["non_aggression_ticks"] = 0
    if stance == "cooperative" and tick is not None:
        stances[key]["cooperative_since_tick"] = tick
    elif stance != "cooperative":
        stances[key]["cooperative_since_tick"] = None


def sync_to_factions(stances: dict, registry: dict) -> None:
    for (fid_a, fid_b), entry in stances.items():
        stance = entry["stance"]
        if fid_a in registry:
            registry[fid_a].diplomatic_stance[fid_b] = stance
        if fid_b in registry:
            registry[fid_b].diplomatic_stance[fid_a] = stance


def _factions_share_border(fid_a: str, fid_b: str, world) -> bool:
    for region in world.regions.values():
        if region.faction_id != fid_a:
            continue
        for nid in world.get_neighbors(region.id, edge_type="border"):
            nr = world.regions.get(nid)
            if nr and nr.faction_id == fid_b:
                return True
    return False


def _avg_border_stability(fid: str, partner_fid: str, world) -> float:
    stabilities = []
    for region in world.regions.values():
        if region.faction_id != fid:
            continue
        borders_partner = any(
            world.regions[nid].faction_id == partner_fid
            for nid in world.get_neighbors(region.id, edge_type="border")
            if nid in world.regions
        )
        if borders_partner:
            stabilities.append(region.composites.get("stability", 0.0))
    return sum(stabilities) / len(stabilities) if stabilities else 0.0


def _border_military(fid: str, partner_fid: str, world) -> float:
    total_mil = 0.0
    count = 0
    for region in world.regions.values():
        if region.faction_id != fid:
            continue
        borders_partner = any(
            world.regions[nid].faction_id == partner_fid
            for nid in world.get_neighbors(region.id, edge_type="border")
            if nid in world.regions
        )
        if borders_partner:
            total_mil += region.fields.get("military", 0.0)
            count += 1
    return total_mil / count if count else 0.0


def _avg_tension(fid: str, world) -> float:
    owned = [r for r in world.regions.values() if r.faction_id == fid]
    if not owned:
        return 0.0
    return sum(r.fields.get("tension", 0.0) for r in owned) / len(owned)


def _weakest_border_region(victim_fid: str, betrayer_fid: str, world) -> str | None:
    best_rid = None
    best_mil = float("inf")
    for region in world.regions.values():
        if region.faction_id != victim_fid:
            continue
        borders_betrayer = any(
            world.regions[nid].faction_id == betrayer_fid
            for nid in world.get_neighbors(region.id, edge_type="border")
            if nid in world.regions
        )
        if borders_betrayer and region.fields.get("military", 0.0) < best_mil:
            best_mil = region.fields.get("military", 0.0)
            best_rid = region.id
    return best_rid


def _avg_economy(fid: str, world) -> float:
    owned = [r for r in world.regions.values() if r.faction_id == fid and r.fields]
    if not owned:
        return 0.0
    return sum(r.fields["economy"] for r in owned) / len(owned)


def _attack_involving(fid_a: str, fid_b: str, tick_log: dict) -> bool:
    for action in tick_log.get("faction_actions", []):
        if action.get("action") != "attack":
            continue
        attacker = action.get("faction_id")
        target_rid = action.get("target_region")
        if not target_rid:
            continue
        defender = action.get("log", {}).get("defender_faction")
        if defender is None:
            for conquest in tick_log.get("conquests", []):
                if conquest.get("region_id") == target_rid:
                    if conquest.get("old_faction_id") in (fid_a, fid_b) and attacker in (fid_a, fid_b):
                        return True
            continue
        if (attacker == fid_a and defender == fid_b) or (attacker == fid_b and defender == fid_a):
            return True
    return False


def update_timers(stances: dict, registry: dict, world, tick_log: dict) -> None:
    for key, entry in stances.items():
        if entry["stance"] != "neutral":
            continue
        fid_a, fid_b = key
        if fid_a not in registry or fid_b not in registry:
            continue
        if not _factions_share_border(fid_a, fid_b, world):
            continue
        if _attack_involving(fid_a, fid_b, tick_log):
            entry["non_aggression_ticks"] = 0
        else:
            entry["non_aggression_ticks"] += 1


def check_peace_formation(stances: dict, registry: dict, world, rng, tick: int,
                          tick_log: dict) -> list:
    events = []
    for key, entry in list(stances.items()):
        if entry["stance"] != "neutral":
            continue
        if entry["non_aggression_ticks"] < config.PEACE_FORMATION_THRESHOLD:
            continue
        fid_a, fid_b = key
        if fid_a not in registry or fid_b not in registry:
            continue

        eco_a = _avg_economy(fid_a, world)
        eco_b = _avg_economy(fid_b, world)
        eco_compatibility = 1.0 - abs(eco_a - eco_b) / 100.0

        stab_a = _avg_border_stability(fid_a, fid_b, world)
        stab_b = _avg_border_stability(fid_b, fid_a, world)
        stability_factor = min(stab_a, stab_b) / 100.0

        if min(stab_a, stab_b) < config.PEACE_STABILITY_THRESHOLD:
            entry["non_aggression_ticks"] = 0
            continue

        disp_a = config.ARCHETYPE_PEACE_DISPOSITION.get(registry[fid_a].archetype, 1.0)
        disp_b = config.ARCHETYPE_PEACE_DISPOSITION.get(registry[fid_b].archetype, 1.0)

        success_prob = (config.PEACE_BASE_PROBABILITY
                        * eco_compatibility
                        * stability_factor
                        * disp_a * disp_b)
        success_prob = min(1.0, max(0.0, success_prob))

        roll = rng.random()
        success = roll < success_prob

        event = {
            "event_type": "diplomatic_overture",
            "tick": tick,
            "factions": [fid_a, fid_b],
            "result": "success" if success else "failed",
            "non_aggression_duration": entry["non_aggression_ticks"],
            "avg_border_stability": round(min(stab_a, stab_b), 1),
            "eco_compatibility": round(eco_compatibility, 3),
            "success_probability": round(success_prob, 4),
            "roll": round(roll, 4),
        }
        events.append(event)

        if success:
            set_stance(stances, fid_a, fid_b, "cooperative", tick=tick)
            sync_to_factions(stances, registry)
            # 2E: Cooperative peace upgrades shared edges to "both" (enables trade)
            world.update_faction_pair_edges(fid_a, fid_b, "both")
        else:
            entry["non_aggression_ticks"] = 0

    return events


def check_betrayals(stances: dict, registry: dict, world, rng,
                    tick: int) -> list:
    events = []
    for key, entry in list(stances.items()):
        if entry["stance"] != "cooperative":
            continue
        fid_a, fid_b = key
        if fid_a not in registry or fid_b not in registry:
            continue

        for betrayer_id, victim_id in [(fid_a, fid_b), (fid_b, fid_a)]:
            arch = registry[betrayer_id].archetype
            base = config.BASE_BETRAYAL_RATE
            arch_weight = config.ARCHETYPE_BETRAYAL_WEIGHT.get(arch, 1.0)

            own_mil = _border_military(betrayer_id, victim_id, world)
            partner_mil = _border_military(victim_id, betrayer_id, world)
            opportunity = max(1.0, own_mil / partner_mil) if partner_mil > 0 else config.BETRAYAL_OPPORTUNITY_CAP
            opportunity = min(opportunity, config.BETRAYAL_OPPORTUNITY_CAP)

            own_tension = _avg_tension(betrayer_id, world)
            pressure = max(1.0, own_tension / 50.0)

            prob = base * arch_weight * opportunity * pressure
            prob = min(1.0, max(0.0, prob))

            roll = rng.random()
            if roll >= prob:
                continue

            target_rid = _weakest_border_region(victim_id, betrayer_id, world)
            coop_since = entry.get("cooperative_since_tick")
            coop_duration = (tick - coop_since) if coop_since is not None else 0

            set_stance(stances, betrayer_id, victim_id, "hostile", tick=tick)
            sync_to_factions(stances, registry)
            # 2E: Betrayal downgrades shared edges to "border" (severs trade)
            world.update_faction_pair_edges(betrayer_id, victim_id, "border")

            events.append({
                "event_type": "betrayal",
                "tick": tick,
                "betrayer": betrayer_id,
                "victim": victim_id,
                "betrayal_probability": round(prob, 6),
                "opportunity_modifier": round(opportunity, 3),
                "pressure_modifier": round(pressure, 3),
                "archetype_weight": arch_weight,
                "attack_target_region": target_rid,
                "cooperative_duration_ticks": coop_duration,
            })
            break  # only one betrayal per pair per tick

    return events
