from dataclasses import dataclass, field
import config
from events import TEMPLATES


@dataclass
class Cluster:
    cluster_type: str           # "consequence", "lineage", "chain", "regional"
    category: str               # one of the 20 CATEGORIES names
    events: list = field(default_factory=list)
    region_id: str = ""
    peak_score: float = 0.0
    chain_tag: str = ""
    tick_range: tuple = (0, 0)


def score_event(event, ledger, player_lineage_id, last_mission_region):
    tmpl = TEMPLATES.get(event.get("template_id", ""), {})
    base = tmpl.get("significance_tier", 2)

    deltas = event.get("field_deltas", {})
    delta_mag = sum(abs(d) for d in deltas.values())
    delta_boost = min(delta_mag / config.SIGNIFICANCE_DELTA_SCALE,
                      config.SIGNIFICANCE_DELTA_CAP)

    context = 1.0
    if event.get("region_id") == last_mission_region:
        context += config.SIGNIFICANCE_MISSION_REGION_BONUS
    if event.get("character_id") is not None:
        context += config.SIGNIFICANCE_CHARACTER_BONUS
    chain_len = event.get("chain_length", 0)
    if chain_len > 1:
        context += config.SIGNIFICANCE_CHAIN_LENGTH_BONUS * min(chain_len, config.CHAIN_LENGTH_CAP)
    if ledger and player_lineage_id and ledger.lineage_in_region(player_lineage_id, event.get("region_id", "")):
        context += config.SIGNIFICANCE_LINEAGE_REGION_BONUS

    return (base + delta_boost) * context


def _tick_range(events):
    ticks = [e.get("tick", 0) for e in events]
    if not ticks:
        return (0, 0)
    return (min(ticks), max(ticks))


def _primary_region(events):
    from collections import Counter
    regions = [e.get("region_id", "") for e in events if e.get("region_id")]
    if not regions:
        return ""
    return Counter(regions).most_common(1)[0][0]


def _classify_lineage_cluster(events):
    net = {}
    for e in events:
        for field_name, delta in e.get("field_deltas", {}).items():
            net[field_name] = net.get(field_name, 0) + delta

    has_military = any("military" in e.get("template_id", "") or "revolt" in e.get("template_id", "")
                       for e in events)
    has_succession = any("succession" in e.get("template_id", "") or "death" in e.get("template_id", "")
                         for e in events)

    if has_succession:
        return "lineage_succession"
    if has_military:
        return "lineage_military_action"

    eco = net.get("economy", 0)
    mil = net.get("military", 0)
    tension = net.get("tension", 0)

    if eco > 2 or mil > 2:
        return "lineage_thrived"
    if eco < -3 or tension > 5:
        return "lineage_suffered"
    return "lineage_quiet"


def _classify_chain_cluster(events, chain_tag):
    net = {}
    for e in events:
        for field_name, delta in e.get("field_deltas", {}).items():
            net[field_name] = net.get(field_name, 0) + delta

    templates = [e.get("template_id", "") for e in events]
    has_revolt = any("revolt" in t for t in templates)
    has_expansion = any("expansion" in t or "coloniz" in t for t in templates)

    if has_revolt:
        return "chain_revolt_spawned"
    if has_expansion:
        return "chain_expansion"

    eco = net.get("economy", 0)
    mil = net.get("military", 0)
    tension = net.get("tension", 0)

    if len(events) >= 4:
        return "chain_cascade"

    if mil > 2 and tension < 3:
        return "chain_conflict_victory"
    if mil < -2 and tension > 3:
        return "chain_conflict_defeat"
    if abs(mil) <= 2 and tension > 2:
        return "chain_conflict_stalemate"

    if eco > 0 and tension <= 0:
        return "chain_crisis_resolved_well"
    return "chain_crisis_resolved_badly"


def _classify_regional_cluster(events):
    net = {}
    for e in events:
        for field_name, delta in e.get("field_deltas", {}).items():
            net[field_name] = net.get(field_name, 0) + delta

    has_faction_shift = any("conquest" in e.get("template_id", "") or
                            "revolt" in e.get("template_id", "") or
                            e.get("creates_faction", False)
                            for e in events)
    if has_faction_shift:
        return "regional_faction_shift"

    eco = net.get("economy", 0)
    pop = net.get("population", 0)
    total = eco + pop

    if total > 3:
        return "regional_growth"
    if total < -3:
        return "regional_decline"
    return "regional_stable"


def distill(event_log, ledger, player_lineage_id, last_mission_region,
            last_mission_outcome=None, world=None):
    scored = []
    for evt in event_log:
        score = score_event(evt, ledger, player_lineage_id, last_mission_region)
        scored.append((evt, score))

    remaining = list(scored)
    clusters = []

    # Pass 2 step 1: consequence cluster
    consequence_events = [(e, s) for e, s in remaining if e.get("mission_consequence")]
    if consequence_events:
        evts = [e for e, s in consequence_events]
        remaining = [(e, s) for e, s in remaining if not e.get("mission_consequence")]

        if last_mission_outcome == "success":
            cat = "consequence_success"
        elif last_mission_outcome == "failure":
            cat = "consequence_failure"
        else:
            cat = "consequence_mixed"

        clusters.append(Cluster(
            cluster_type="consequence",
            category=cat,
            events=evts,
            region_id=_primary_region(evts),
            peak_score=max(s for _, s in consequence_events),
            tick_range=_tick_range(evts),
        ))

    # Pass 2 step 2: lineage clusters
    lineage_events = []
    non_lineage = []
    for e, s in remaining:
        is_lineage = False
        if ledger and player_lineage_id:
            if ledger.lineage_in_region(player_lineage_id, e.get("region_id", "")):
                is_lineage = True
            if e.get("character_id"):
                char = ledger.get_character_by_id(e["character_id"])
                if char and char.lineage_id == player_lineage_id:
                    is_lineage = True
        if e.get("region_id") == last_mission_region:
            is_lineage = True
        if is_lineage:
            lineage_events.append((e, s))
        else:
            non_lineage.append((e, s))

    if lineage_events:
        by_region = {}
        for e, s in lineage_events:
            rid = e.get("region_id", "unknown")
            by_region.setdefault(rid, []).append((e, s))

        for rid, group in by_region.items():
            evts = [e for e, s in group]
            cat = _classify_lineage_cluster(evts)
            clusters.append(Cluster(
                cluster_type="lineage",
                category=cat,
                events=evts,
                region_id=rid,
                peak_score=max(s for _, s in group),
                tick_range=_tick_range(evts),
            ))
    elif ledger and player_lineage_id:
        # K2 guarantee: always emit at least one lineage cluster
        primary_region = None
        members = ledger.get_lineage_members(player_lineage_id)
        active = [m for m in members if m.status == "active" and m.region_id]
        if active:
            primary_region = active[0].region_id
        if not primary_region:
            history = [h for h in ledger.get_lineage_history(player_lineage_id) if h]
            if history:
                primary_region = history[-1]
        if not primary_region and last_mission_region:
            primary_region = last_mission_region
        if not primary_region and world:
            for rid, r in world.regions.items():
                if r.faction_id and r.tier != "empty":
                    primary_region = rid
                    break
        tick_lo = event_log[0].get("tick", 0) if event_log else 0
        tick_hi = event_log[-1].get("tick", 0) if event_log else 0
        clusters.append(Cluster(
            cluster_type="lineage",
            category="lineage_quiet",
            events=[],
            region_id=primary_region,
            peak_score=0.0,
            tick_range=(tick_lo, tick_hi),
        ))

    remaining = non_lineage

    # Pass 2 step 3: chain clusters
    by_chain = {}
    unchained = []
    for e, s in remaining:
        tag = e.get("chain_tag", "")
        if tag:
            by_chain.setdefault(tag, []).append((e, s))
        else:
            unchained.append((e, s))

    raw_chain_clusters = []
    for tag, group in by_chain.items():
        evts = [e for e, s in group]
        cat = _classify_chain_cluster(evts, tag)
        raw_chain_clusters.append(Cluster(
            cluster_type="chain",
            category=cat,
            events=evts,
            region_id=_primary_region(evts),
            peak_score=max(s for _, s in group),
            chain_tag=tag,
            tick_range=_tick_range(evts),
        ))

    # Merge chain clusters that share both region and category
    merged_chain = {}
    for c in raw_chain_clusters:
        key = (c.region_id, c.category)
        if key in merged_chain:
            existing = merged_chain[key]
            existing.events.extend(c.events)
            existing.peak_score = max(existing.peak_score, c.peak_score)
            existing.tick_range = _tick_range(existing.events)
        else:
            merged_chain[key] = c
    clusters.extend(merged_chain.values())

    # Pass 2 step 4: regional summary clusters
    by_region = {}
    for e, s in unchained:
        rid = e.get("region_id", "unknown")
        by_region.setdefault(rid, []).append((e, s))

    for rid, group in by_region.items():
        evts = [e for e, s in group]
        cat = _classify_regional_cluster(evts)
        clusters.append(Cluster(
            cluster_type="regional",
            category=cat,
            events=evts,
            region_id=rid,
            peak_score=max(s for _, s in group),
            tick_range=_tick_range(evts),
        ))

    # Pass 2 step 5: rank and select
    consequence = [c for c in clusters if c.cluster_type == "consequence"]
    lineage = [c for c in clusters if c.cluster_type == "lineage"]
    other = [c for c in clusters if c.cluster_type not in ("consequence", "lineage")]
    other.sort(key=lambda c: c.peak_score, reverse=True)

    selected = consequence + lineage

    from collections import Counter
    cat_counts = Counter(c.category for c in selected)

    for c in other:
        if len(selected) >= config.CHRONICLE_MAX_ENTRIES:
            break
        if cat_counts[c.category] >= 2:
            continue
        selected.append(c)
        cat_counts[c.category] += 1

    # Pad to minimum if needed: promote remaining regionals or split
    if len(selected) < config.CHRONICLE_MIN_ENTRIES and other:
        for c in other:
            if c not in selected and cat_counts[c.category] < 2:
                selected.append(c)
                cat_counts[c.category] += 1
            if len(selected) >= config.CHRONICLE_MIN_ENTRIES:
                break

    # If still below minimum, synthesize quiet regional entries from world state
    if len(selected) < config.CHRONICLE_MIN_ENTRIES and world:
        for rid in list(world.regions.keys()):
            if len(selected) >= config.CHRONICLE_MIN_ENTRIES:
                break
            if cat_counts["regional_stable"] >= 2:
                break
            already_covered = {c.region_id for c in selected}
            if rid in already_covered:
                continue
            region = world.regions[rid]
            if region.tier == "empty":
                continue
            synth = Cluster(
                cluster_type="regional",
                category="regional_stable",
                events=[],
                region_id=rid,
                peak_score=0.0,
                tick_range=(0, 0),
            )
            clusters.append(synth)
            selected.append(synth)
            cat_counts["regional_stable"] += 1

    return selected[:config.CHRONICLE_MAX_ENTRIES]
