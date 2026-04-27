import json
import os
import random
import re
from dataclasses import dataclass, field

from events import TEMPLATES as _EVENT_TEMPLATES

LIBRARY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library")


@dataclass
class ScrollEntry:
    base_text: str
    expanded_text: str
    cluster_type: str
    category: str
    fragment_ids: list = field(default_factory=list)
    resolved_slots: dict = field(default_factory=dict)
    source_events: list = field(default_factory=list)
    region_id: str = ""
    tick_range: tuple = (0, 0)


_fragment_cache = None


def _load_fragments():
    global _fragment_cache
    if _fragment_cache is not None:
        return _fragment_cache
    path = os.path.join(LIBRARY_DIR, "chronicle", "fragments.json")
    with open(path) as f:
        _fragment_cache = json.load(f)
    return _fragment_cache


def _get_pool(category, frag_type):
    fragments = _load_fragments()
    return [f for f in fragments
            if f["category"] == category and f["type"] == frag_type]


def _slots_in_text(text):
    return set(re.findall(r"\{[a-z_]+\}", text))


def _can_resolve(fragment, available_slots):
    needed = _slots_in_text(fragment["text"])
    return needed.issubset(available_slots)


def _resolve_slots(text, slot_values):
    for slot, value in slot_values.items():
        text = text.replace(slot, value)
    return text


def _fix_post_period_caps(text):
    return re.sub(r'(\. )([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)


_STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "its", "their", "was", "were", "had", "has",
    "that", "this", "which", "what", "as", "is", "it", "be", "been", "not",
    "no", "all", "each", "every", "into", "over", "than", "then", "when",
    "after", "before", "while", "until", "across", "beyond",
})

_ECHO_SYNONYMS = {
    "instability": ["unease", "disorder", "turbulence"],
    "unrest": ["discontent", "agitation", "dissent"],
    "tensions": ["frictions", "pressures", "strains"],
    "tension": ["friction", "pressure", "strain"],
    "collapsed": ["crumbled", "fell apart", "gave way"],
    "collapse": ["breakdown", "disintegration", "failure"],
    "deteriorated": ["worsened", "declined", "degraded"],
    "expanded": ["grew", "increased", "advanced"],
    "eroded": ["weakened", "diminished", "waned"],
    "mounted": ["grew", "intensified", "built"],
    "spread": ["widened", "extended", "advanced"],
    "surged": ["swelled", "climbed", "rose sharply"],
    "strengthened": ["solidified", "fortified", "recovered"],
    "contracted": ["shrank", "diminished", "receded"],
    "military": ["martial", "armed", "garrison"],
    "commerce": ["trade", "the markets", "economic activity"],
}


def _deduplicate_echo_words(text, rng):
    words = text.split()
    seen = {}
    result = []
    for i, word in enumerate(words):
        clean = re.sub(r'[.,;:!?]$', '', word).lower()
        if clean in _STOP_WORDS or len(clean) <= 3:
            result.append(word)
            continue
        if clean in seen:
            alts = _ECHO_SYNONYMS.get(clean, [])
            if alts:
                replacement = rng.choice(alts)
                suffix = word[len(clean):] if len(word) > len(clean) else ""
                if word[0].isupper():
                    replacement = replacement[0].upper() + replacement[1:]
                result.append(replacement + suffix)
            else:
                result.append(word)
        else:
            seen[clean] = i
            result.append(word)
    return " ".join(result)


def _duration_prose(tick_range):
    ticks = tick_range[1] - tick_range[0]
    if ticks <= 5:
        return "in a matter of days"
    if ticks <= 15:
        return "over the following weeks"
    if ticks <= 30:
        return "over the following months"
    if ticks <= 60:
        return "over the span of a year"
    return "across the years that followed"


def _field_delta_summary(events, faction_name=None):
    net = {}
    for e in events:
        for f, d in e.get("field_deltas", {}).items():
            net[f] = net.get(f, 0) + d
    if not net:
        return "little changed"

    eco = net.get("economy", 0)
    mil = net.get("military", 0)
    tension = net.get("tension", 0)
    pop = net.get("population", 0)

    # Optional possessive prefix: "the Dominion's garrison" vs "the garrison"
    poss = f"{faction_name}'s " if faction_name else ""
    the_poss = f"{faction_name}'s " if faction_name else "the "

    seed = abs(hash(tuple(sorted(net.items()))))

    if mil < -3 and tension > 3:
        phrases = [
            f"{the_poss}garrison collapsed and unrest spread in its wake",
            f"{the_poss}military order deteriorated sharply while civil tensions climbed",
            f"armed authority eroded and public fear surged to fill the vacuum",
        ]
    elif mil > 3 and tension <= 0:
        phrases = [
            f"{the_poss}military consolidated its position and confidence returned",
            f"{the_poss}garrison strengthened and public anxieties began to ease",
            f"martial order was restored and a measure of stability followed",
        ]
    elif eco > 3 and pop > 0:
        phrases = [
            f"{poss}commerce expanded and the population grew with it",
            f"trade swelled and drew settlers to the region in growing numbers",
            f"prosperity took hold and compounded with each passing season",
        ]
    elif eco < -3 and pop < 0:
        phrases = [
            f"{poss}commerce contracted and families began leaving the region",
            f"the economy deteriorated until it could no longer sustain {the_poss}population",
            f"hardship set in and thinned both the markets and the populace",
        ]
    elif tension < -2:
        phrases = [
            "the tensions that had gripped the region gradually eased",
            "civil order was slowly restored after months of unease",
            "a fragile calm settled over what had been volatile ground",
        ]
    elif tension > 5:
        phrases = [
            f"civil unrest mounted beyond what {the_poss}authorities could contain",
            "tensions escalated dangerously across all quarters",
            "discontent spread until it saturated every level of public life",
        ]
    elif abs(eco) <= 2 and abs(mil) <= 2 and abs(tension) <= 2:
        phrases = [
            "conditions remained largely unchanged",
            f"{the_poss}garrison held steady, the markets neither grew nor shrank, and civil order persisted",
            "military strength, commerce, and public order all held within familiar bounds",
        ]
    else:
        parts = []
        if mil > 2:
            parts.append(f"{poss}military strength grew")
        elif mil < -2:
            parts.append(f"{poss}military strength eroded")
        if eco > 2:
            parts.append(f"{poss}commerce expanded")
        elif eco < -2:
            parts.append(f"{poss}commerce contracted")
        if tension > 2:
            parts.append("civil tensions rose")
        elif tension < -2:
            parts.append("civil tensions eased")
        if pop > 2:
            parts.append("the population swelled")
        elif pop < -2:
            parts.append("the population thinned")
        if not parts:
            parts = ["conditions shifted in ways that resisted easy summary"]
        phrases = [" while ".join(parts) if len(parts) == 2
                   else ", ".join(parts[:-1]) + ", and " + parts[-1] if len(parts) > 2
                   else parts[0]]

    return phrases[seed % len(phrases)]


def _stability_prose(region, world):
    if region is None:
        return "uncertain"
    stab = region.composites.get("stability", 50)
    if stab >= 70:
        return "firmly stable"
    if stab >= 50:
        return "reasonably stable"
    if stab >= 30:
        return "uneasy"
    return "dangerously unstable"


def _capacity_prose(region):
    if region is None:
        return "modest"
    cap = region.composites.get("capacity", 50)
    if cap >= 70:
        return "thriving"
    if cap >= 50:
        return "adequate"
    if cap >= 30:
        return "strained"
    return "depleted"


def _tension_prose(region):
    if region is None:
        return "simmering"
    t = region.fields.get("tension", 30)
    if t >= 60:
        return "volatile"
    if t >= 40:
        return "tense"
    if t >= 20:
        return "restless"
    return "calm"


def build_slot_values(cluster, ledger, player_lineage_id, world,
                      mission_info=None, registry=None):
    slots = {}
    events = cluster.events
    region = world.regions.get(cluster.region_id) if world else None

    slots["{region_name}"] = cluster.region_id
    if region:
        slots["{region_name}"] = region.name

    slots["{duration_prose}"] = _duration_prose(cluster.tick_range)
    faction_name = None
    if region and region.faction_id:
        if registry and region.faction_id in registry:
            faction_name = registry[region.faction_id].name
    slots["{field_delta_summary}"] = _field_delta_summary(events, faction_name)

    if region:
        slots["{stability_level}"] = _stability_prose(region, world)
        slots["{capacity_level}"] = _capacity_prose(region)
        slots["{tension_level}"] = _tension_prose(region)

    if world and cluster.region_id:
        neighbors = world.get_neighbors(cluster.region_id) if hasattr(world, "get_neighbors") else []
        if neighbors:
            adj = neighbors[0]
            adj_region = world.regions.get(adj)
            slots["{adjacent_region}"] = adj_region.name if adj_region else adj

    chain_lengths = [e.get("chain_length", 0) for e in events if e.get("chain_length", 0) > 0]
    if chain_lengths:
        slots["{chain_length}"] = str(max(chain_lengths))

    ticks = cluster.tick_range[1] - cluster.tick_range[0]
    slots["{duration_ticks}"] = str(ticks)

    char_id = None
    for e in events:
        if e.get("character_id"):
            char_id = e["character_id"]
            break
    if char_id and ledger:
        char = ledger.get_character_by_id(char_id)
        if char:
            slots["{character_name}"] = char.name
            slots["{character_rank}"] = char.rank
            slots["{character_faction}"] = char.faction_id
            if registry and char.faction_id in registry:
                slots["{character_faction}"] = registry[char.faction_id].name

    if ledger and player_lineage_id:
        members = ledger.get_lineage_members(player_lineage_id)
        if members:
            root = members[0]
            last_name = root.name.split()[-1] if root.name and " " in root.name else root.name
            slots["{lineage_name}"] = last_name

    if region and region.faction_id:
        if registry and region.faction_id in registry:
            slots["{faction_name}"] = registry[region.faction_id].name
        else:
            slots["{faction_name}"] = region.faction_id

    event_descriptions = []
    for e in events:
        tid = e.get("template_id", "")
        tmpl = _EVENT_TEMPLATES.get(tid, {})
        prose = tmpl.get("chronicle_prose", "")
        if not prose:
            prose = e.get("name", e.get("template_id", "an event")).lower()
        event_descriptions.append(prose)
    if event_descriptions:
        slots["{event_description}"] = event_descriptions[0]

    if mission_info:
        slots["{mission_outcome}"] = mission_info.get("outcome", "the outcome of the mission")
        slots["{mission_archetype}"] = mission_info.get("archetype", "the commander")
        mr = mission_info.get("region", cluster.region_id)
        if world and mr in world.regions:
            slots["{mission_region}"] = world.regions[mr].name
        else:
            slots["{mission_region}"] = mr

    if ledger and player_lineage_id:
        history = ledger.get_lineage_history(player_lineage_id)
        if len(history) > 1:
            slots["{lineage_history_note}"] = f"a family with roots in {history[0]}"
        elif history:
            slots["{lineage_history_note}"] = f"long established in {history[0]}"

    slots["{previous_event_reference}"] = "what had come before"

    return slots


ECHO_WORD_THRESHOLD = 6

ANAPHORIC_FORMS = {
    "{mission_outcome}": ["the outcome", "what had transpired", "the result"],
    "{field_delta_summary}": ["what followed", "the aftermath", "what ensued"],
}


def _long_slots(fragment, slot_values):
    slots = _slots_in_text(fragment["text"])
    return {s for s in slots
            if s in slot_values and len(slot_values[s].split()) >= ECHO_WORD_THRESHOLD}


def _make_anaphoric(slot_values, echoed_slots, rng):
    reduced = dict(slot_values)
    for slot in echoed_slots:
        forms = ANAPHORIC_FORMS.get(slot, ["this", "what occurred", "the event"])
        reduced[slot] = rng.choice(forms)
    return reduced


def assemble_entry(cluster, slot_values, rng):
    available = set(slot_values.keys())

    openings = _get_pool(cluster.category, "opening")
    details = _get_pool(cluster.category, "detail")
    closings = _get_pool(cluster.category, "closing")

    resolvable_openings = [f for f in openings if _can_resolve(f, available)]
    resolvable_details = [f for f in details if _can_resolve(f, available)]
    resolvable_closings = [f for f in closings if _can_resolve(f, available)]

    if not resolvable_openings or not resolvable_details:
        resolvable_openings = resolvable_openings or openings
        resolvable_details = resolvable_details or details

    opening = rng.choice(resolvable_openings) if resolvable_openings else None
    detail = rng.choice(resolvable_details) if resolvable_details else None
    closing = rng.choice(resolvable_closings) if resolvable_closings else None

    if not opening or not detail:
        return None

    # Detect long-slot echo between adjacent fragments and substitute anaphoric forms
    opening_long = _long_slots(opening, slot_values)
    detail_long = _long_slots(detail, slot_values)
    opening_detail_echo = opening_long & detail_long

    detail_slots = slot_values
    if opening_detail_echo:
        detail_slots = _make_anaphoric(slot_values, opening_detail_echo, rng)

    closing_slots = detail_slots
    if closing:
        closing_long = _long_slots(closing, detail_slots)
        detail_closing_echo = detail_long & closing_long
        if detail_closing_echo:
            closing_slots = _make_anaphoric(detail_slots, detail_closing_echo, rng)

    fragment_ids = [opening["id"], detail["id"]]
    if closing:
        fragment_ids.append(closing["id"])

    opening_resolved = _resolve_slots(opening["text"], slot_values)
    detail_resolved = _resolve_slots(detail["text"], detail_slots)

    base_text = opening_resolved + " " + detail_resolved

    if closing:
        closing_resolved = _resolve_slots(closing["text"], closing_slots)
        expanded_text = base_text + " " + closing_resolved
    else:
        expanded_text = base_text

    base_text = _deduplicate_echo_words(base_text, rng)
    expanded_text = _deduplicate_echo_words(expanded_text, rng)
    base_text = _fix_post_period_caps(base_text)
    expanded_text = _fix_post_period_caps(expanded_text)
    if base_text:
        base_text = base_text[0].upper() + base_text[1:]
    if expanded_text:
        expanded_text = expanded_text[0].upper() + expanded_text[1:]

    source_events = [e.get("template_id", "") for e in cluster.events]

    return ScrollEntry(
        base_text=base_text,
        expanded_text=expanded_text,
        cluster_type=cluster.cluster_type,
        category=cluster.category,
        fragment_ids=fragment_ids,
        resolved_slots=slot_values,
        source_events=source_events,
        region_id=cluster.region_id,
        tick_range=cluster.tick_range,
    )


def _enrich_first_mention(region_id, slots, world, registry, seen_regions):
    if region_id in seen_regions or not world:
        return
    seen_regions.add(region_id)
    region = world.regions.get(region_id)
    if not region:
        return
    name = slots.get("{region_name}", region_id)
    qualifier = ""
    if region.faction_id and registry and region.faction_id in registry:
        qualifier = f", held by {registry[region.faction_id].name}"
    elif region.faction_id:
        qualifier = f", held by {region.faction_id}"
    if qualifier:
        slots["{region_name}"] = name + qualifier


def assemble_scroll(clusters, ledger, player_lineage_id, world,
                    mission_info=None, seed=None, registry=None):
    rng = random.Random(seed)
    entries = []
    warnings = []
    seen_regions = set()

    for cluster in clusters:
        slot_values = build_slot_values(cluster, ledger, player_lineage_id,
                                        world, mission_info, registry=registry)
        _enrich_first_mention(cluster.region_id, slot_values, world, registry, seen_regions)
        entry = assemble_entry(cluster, slot_values, rng)
        if entry is None:
            warnings.append(f"Could not assemble entry for {cluster.category} "
                            f"in {cluster.region_id}")
            continue

        base_wc = len(entry.base_text.split())
        expanded_wc = len(entry.expanded_text.split())
        if base_wc >= 90:
            warnings.append(f"{cluster.category}: base_text {base_wc} words (limit 90)")
        if expanded_wc >= 140:
            warnings.append(f"{cluster.category}: expanded_text {expanded_wc} words (limit 140)")

        entries.append(entry)

    entries = _dedup_cross_entry(entries)
    return entries, warnings


_OVERLAP_THRESHOLD = 0.40

def _content_words(text):
    return {w for w in re.sub(r'[.,;:!?]', '', text.lower()).split()
            if w not in _STOP_WORDS and len(w) > 3}


def _dedup_cross_entry(entries):
    if len(entries) <= 1:
        return entries
    keep = [entries[0]]
    for entry in entries[1:]:
        words = _content_words(entry.base_text)
        if not words:
            keep.append(entry)
            continue
        duplicate = False
        for kept in keep:
            kept_words = _content_words(kept.base_text)
            if not kept_words:
                continue
            overlap = len(words & kept_words) / min(len(words), len(kept_words))
            if overlap >= _OVERLAP_THRESHOLD:
                duplicate = True
                break
        if not duplicate:
            keep.append(entry)
    return keep
