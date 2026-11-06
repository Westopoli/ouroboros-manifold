import sys
import os
import math
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _entry_id(index):
    return f"ce_{index:04d}"


def _generate_region_positions(region_ids, seed=0):
    """Generate stable 3D positions for regions, spread through a sphere.
    Uses a seeded RNG so positions are consistent for the entire campaign."""
    rng = random.Random(seed)
    positions = {}
    radius = 30.0
    for rid in sorted(region_ids):
        # Spherical coordinates with jitter for natural feel
        theta = rng.uniform(0, 2.0 * math.pi)
        phi = math.acos(rng.uniform(-1.0, 1.0))
        r = radius * (0.3 + 0.7 * rng.random())  # vary distance from center
        x = round(r * math.sin(phi) * math.cos(theta), 2)
        y = round(r * math.sin(phi) * math.sin(theta), 2)
        z = round(r * math.cos(phi), 2)
        positions[rid] = (x, y, z)
    return positions


def _tick_in_range(tick, tick_range_start, tick_range_end):
    return tick_range_start <= tick <= tick_range_end


def _conquest_tick_for_region(region_id, conquests):
    for c in conquests:
        if c["region_id"] == region_id:
            return c["tick"]
    return None


def select_keyframes(time_jump_result: dict, start_ownership: dict | None = None) -> list[dict]:
    scroll_entries = time_jump_result.get("scroll_entries", [])
    territory_changes = time_jump_result.get("territory_changes", [])
    conquests = time_jump_result.get("conquests", [])

    keyframes = []
    for i, entry in enumerate(scroll_entries):
        keyframes.append({
            "entry_id": _entry_id(i),
            "tick": entry.tick_range[1],
            "tick_range_start": entry.tick_range[0],
            "tick_range_end": entry.tick_range[1],
            "chronicle_entry_id": _entry_id(i),
            "ownership_changes": [],
            "military_events": [],
        })

    for tc in territory_changes:
        conquest_tick = _conquest_tick_for_region(tc["region_id"], conquests)

        absorbed = False
        if conquest_tick is not None:
            for kf in keyframes:
                if _tick_in_range(conquest_tick, kf["tick_range_start"], kf["tick_range_end"]):
                    kf["ownership_changes"].append({
                        "region_id": tc["region_id"],
                        "old_faction_id": tc["old_faction"],
                        "new_faction_id": tc["new_faction"],
                    })
                    absorbed = True
                    break

        if not absorbed:
            tick = conquest_tick if conquest_tick is not None else time_jump_result.get("end_tick", 0)
            keyframes.append({
                "entry_id": "",
                "tick": tick,
                "tick_range_start": tick,
                "tick_range_end": tick,
                "chronicle_entry_id": None,
                "ownership_changes": [{
                    "region_id": tc["region_id"],
                    "old_faction_id": tc["old_faction"],
                    "new_faction_id": tc["new_faction"],
                }],
                "military_events": [],
            })

    for conquest in conquests:
        ctick = conquest["tick"]
        target = None
        target_dist = None
        for kf in keyframes:
            if _tick_in_range(ctick, kf["tick_range_start"], kf["tick_range_end"]):
                target = kf
                break
        if target is None:
            for kf in keyframes:
                dist = abs(kf["tick"] - ctick)
                if target_dist is None or dist < target_dist:
                    target = kf
                    target_dist = dist
        if target is not None:
            target["military_events"].append({
                "kind": "conquest",
                "attacker_region_id": conquest.get("region_id", ""),
                "defender_region_id": conquest.get("region_id", ""),
            })

    keyframes.sort(key=lambda kf: kf["tick"])

    if len(keyframes) > config.KEYFRAME_MAX_PER_TIME_JUMP:
        # Keep highest-significance: prefer keyframes with chronicle entries, then by event count
        def significance(kf):
            has_chronicle = 0 if kf["chronicle_entry_id"] is None else 1
            events = len(kf["ownership_changes"]) + len(kf["military_events"])
            return (has_chronicle, events)
        keyframes.sort(key=significance, reverse=True)
        keyframes = keyframes[:config.KEYFRAME_MAX_PER_TIME_JUMP]
        keyframes.sort(key=lambda kf: kf["tick"])

    if start_ownership:
        sorted_conquests = sorted(conquests, key=lambda c: c["tick"])
        all_region_ids = sorted(start_ownership.keys())

        region_positions = _generate_region_positions(all_region_ids, seed=42)

        region_populations = time_jump_result.get("region_populations", {})
        max_pop = max(region_populations.values()) if region_populations else 1.0
        max_pop = max(max_pop, 1.0)

        adjacency = time_jump_result.get("adjacency", {})
        edge_types = time_jump_result.get("edge_types", {})

        for kf in keyframes:
            kf_tick = kf["tick"]
            current_ownership = dict(start_ownership)
            for c in sorted_conquests:
                if c["tick"] <= kf_tick:
                    current_ownership[c["region_id"]] = c.get("new_faction_id", c.get("new_faction", ""))
                else:
                    break
            snapshot = []
            for rid in all_region_ids:
                faction_id = current_ownership.get(rid)
                x, y, z = region_positions[rid]
                pop = region_populations.get(rid, 0.0)
                sig = 0.15 + 0.85 * (pop / max_pop)
                snapshot.append({
                    "region_id": rid,
                    "owner_faction_id": faction_id if faction_id else "",
                    "significance": round(sig, 3),
                    "x": x,
                    "y": y,
                    "z": z,
                })
            kf["regions_snapshot"] = snapshot

            seen_edges = set()
            connections = []
            for rid in all_region_ids:
                for nid in adjacency.get(rid, []):
                    edge_key = (min(rid, nid), max(rid, nid))
                    if edge_key in seen_edges:
                        continue
                    seen_edges.add(edge_key)
                    a, b = edge_key
                    etype = edge_types.get((a, b), edge_types.get((b, a), "both"))
                    color_fid = current_ownership.get(a, "")
                    connections.append({
                        "from_id": a,
                        "to_id": b,
                        "edge_type": etype,
                        "color_faction_id": color_fid,
                    })
            kf["connections_snapshot"] = connections

    for i, kf in enumerate(keyframes):
        old_id = kf["entry_id"]
        new_id = _entry_id(i)
        if kf["chronicle_entry_id"] == old_id:
            kf["chronicle_entry_id"] = new_id
        kf["entry_id"] = new_id

    # Stage 11g — additive, gated extensions. Flags off → no changes to payload.
    # See docs/legacy/stage_specs/stage_11g_world_view_inspection_spec.md
    if getattr(config, "ENABLE_INSPECTION_PANELS", False):
        region_metadata = time_jump_result.get("region_metadata", {})
        if region_metadata:
            for kf in keyframes:
                snap_list = kf.get("regions_snapshot")
                if not snap_list:
                    continue
                for snap in snap_list:
                    meta = region_metadata.get(snap["region_id"])
                    if not meta:
                        continue
                    for k in ("name", "tier", "military", "economy", "tension", "population", "stability", "capacity"):
                        if k in meta:
                            snap[k] = meta[k]

    if getattr(config, "ENABLE_FACTION_PALETTE", False):
        faction_metadata = time_jump_result.get("faction_metadata", {})
        if faction_metadata:
            factions_array = []
            for fid in sorted(faction_metadata.keys()):
                meta = faction_metadata[fid]
                factions_array.append({
                    "id": fid,
                    "name": meta.get("name", fid),
                    "archetype": meta.get("archetype", ""),
                    "tech_tier": meta.get("tech_tier", 0),
                })
            for kf in keyframes:
                kf["factions"] = factions_array

    return keyframes
