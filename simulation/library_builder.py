#!/usr/bin/env python3
import argparse
import json
import os

CATEGORIES = [
    {
        "name": "lineage_thrived",
        "register": "warm, measured, historically appreciative",
        "required_slots": ["{lineage_name}"],
        "optional_slots": ["{character_name}", "{region_name}", "{duration_prose}", "{stability_level}"],
        "cluster_type": "lineage",
    },
    {
        "name": "lineage_suffered",
        "register": "somber, restrained grief, weight of loss",
        "required_slots": ["{lineage_name}"],
        "optional_slots": ["{character_name}", "{region_name}", "{field_delta_summary}", "{duration_prose}"],
        "cluster_type": "lineage",
    },
    {
        "name": "lineage_quiet",
        "register": "reflective, peaceful, 'life went on' as a meaningful beat",
        "required_slots": ["{lineage_name}"],
        "optional_slots": ["{region_name}", "{duration_prose}", "{stability_level}"],
        "cluster_type": "lineage",
    },
    {
        "name": "lineage_military_action",
        "register": "tense, martial, duty-focused",
        "required_slots": ["{lineage_name}"],
        "optional_slots": ["{character_name}", "{character_rank}", "{region_name}", "{faction_name}", "{field_delta_summary}"],
        "cluster_type": "lineage",
    },
    {
        "name": "lineage_succession",
        "register": "transitional, generational weight, continuity",
        "required_slots": ["{lineage_name}"],
        "optional_slots": ["{character_name}", "{region_name}", "{duration_prose}"],
        "cluster_type": "lineage",
    },
    {
        "name": "chain_crisis_resolved_well",
        "register": "cautious relief, hard-won stability",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{character_name}", "{event_description}", "{chain_length}", "{duration_prose}", "{stability_level}", "{field_delta_summary}"],
        "cluster_type": "chain",
    },
    {
        "name": "chain_crisis_resolved_badly",
        "register": "grim, consequence-heavy, permanent loss",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{character_name}", "{event_description}", "{chain_length}", "{duration_prose}", "{stability_level}", "{field_delta_summary}"],
        "cluster_type": "chain",
    },
    {
        "name": "chain_conflict_victory",
        "register": "decisive, martial, territorial shift",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{character_name}", "{faction_name}", "{adjacent_region}", "{field_delta_summary}", "{duration_prose}"],
        "cluster_type": "chain",
    },
    {
        "name": "chain_conflict_stalemate",
        "register": "exhausted, grinding, unresolved tension",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{character_name}", "{faction_name}", "{tension_level}", "{duration_prose}", "{field_delta_summary}"],
        "cluster_type": "chain",
    },
    {
        "name": "chain_conflict_defeat",
        "register": "somber, measured, historical weight",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{character_name}", "{faction_name}", "{field_delta_summary}", "{duration_prose}"],
        "cluster_type": "chain",
    },
    {
        "name": "chain_revolt_spawned",
        "register": "fractured, ideological, internal rupture",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{character_name}", "{faction_name}", "{event_description}", "{tension_level}", "{field_delta_summary}"],
        "cluster_type": "chain",
    },
    {
        "name": "chain_expansion",
        "register": "pioneering, forward-looking, cautious optimism",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{faction_name}", "{adjacent_region}", "{capacity_level}", "{duration_prose}", "{field_delta_summary}"],
        "cluster_type": "chain",
    },
    {
        "name": "chain_cascade",
        "register": "ominous, overwhelming, 'too many things at once'",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{event_description}", "{chain_length}", "{tension_level}", "{field_delta_summary}", "{duration_prose}"],
        "cluster_type": "chain",
    },
    {
        "name": "regional_decline",
        "register": "erosion, slow decay, quiet deterioration",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{field_delta_summary}", "{stability_level}", "{capacity_level}", "{duration_prose}"],
        "cluster_type": "regional",
    },
    {
        "name": "regional_growth",
        "register": "steady, constructive, quiet progress",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{field_delta_summary}", "{stability_level}", "{capacity_level}", "{duration_prose}"],
        "cluster_type": "regional",
    },
    {
        "name": "regional_stable",
        "register": "neutral, brief, background",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{stability_level}", "{duration_prose}"],
        "cluster_type": "regional",
    },
    {
        "name": "regional_faction_shift",
        "register": "political, realignment, new order",
        "required_slots": ["{region_name}"],
        "optional_slots": ["{faction_name}", "{character_name}", "{field_delta_summary}", "{duration_prose}"],
        "cluster_type": "regional",
    },
    {
        "name": "consequence_success",
        "register": "earned, direct cause-and-effect, the player's mark",
        "required_slots": ["{mission_outcome}"],
        "optional_slots": ["{character_name}", "{mission_region}", "{mission_archetype}", "{lineage_name}", "{field_delta_summary}", "{duration_prose}"],
        "cluster_type": "consequence",
    },
    {
        "name": "consequence_failure",
        "register": "weight of failure, consequences faced honestly",
        "required_slots": ["{mission_outcome}"],
        "optional_slots": ["{character_name}", "{mission_region}", "{mission_archetype}", "{lineage_name}", "{field_delta_summary}", "{duration_prose}"],
        "cluster_type": "consequence",
    },
    {
        "name": "consequence_mixed",
        "register": "bittersweet, complicated, no clean answers",
        "required_slots": ["{mission_outcome}"],
        "optional_slots": ["{character_name}", "{mission_region}", "{mission_archetype}", "{lineage_name}", "{field_delta_summary}", "{duration_prose}"],
        "cluster_type": "consequence",
    },
]

SLOT_VOCABULARY = """Variable Slot Vocabulary — every slot resolves to a string at assembly time.

Identity slots (from coherence ledger):
  {character_name} — a named character involved in the cluster's events
  {character_rank} — their rank (supreme_commander, regional_commander, garrison_officer, lineage_member)
  {character_faction} — faction name of the character
  {lineage_name} — the player's current lineage family name
  {faction_name} — a faction involved in the cluster
  {region_name} — the region where the cluster's events occurred
  {adjacent_region} — a neighboring region referenced by the events

Event slots (from cluster event data):
  {event_description} — a short label for the root/primary event in the cluster
  {chain_length} — how many events are in this causal chain
  {duration_ticks} — how many ticks the chain spanned
  {duration_prose} — duration mapped to a human-readable time phrase ("over three decades," "in a matter of years")

State slots (from simulation snapshot):
  {field_delta_summary} — prose summary of field changes ("military strength collapsed," "the economy slowly recovered")
  {stability_level} — qualitative label (critical, low, moderate, high)
  {capacity_level} — qualitative label for capacity
  {tension_level} — qualitative label for factional tension

Consequence-specific slots (only in consequence categories):
  {mission_outcome} — the outcome band as a prose phrase ("a decisive victory," "a pyrrhic success")
  {mission_archetype} — the mission type that was completed
  {mission_region} — where the mission took place

Relational slots:
  {previous_event_reference} — a short callback to an earlier chain
  {lineage_history_note} — a callback to the lineage's earlier involvement"""

FRAGMENT_RULES = """Fragment Generation Rules — all 8 rules must be followed.

Rule 1 — Tone lock. Every fragment must match the category's emotional register specified below.

Rule 2 — Slot discipline. Fragments may only use slots from the defined vocabulary. No invented slots, no inline data.

Rule 3 — Slot optionality. Not every fragment uses every slot. Mark which slots each fragment uses. The assembler filters fragments based on available data.

Rule 4 — No cross-fragment assumptions. An opening cannot assume which detail follows it. A closing cannot reference something only mentioned in a specific opening. Each fragment is self-contained within its type. Shared context comes only through variable slots.

Rule 5 — Prose quality floor. Fragments read like excerpts from a real historical text. No game-speak ("the player's faction"), no mechanical language ("stability dropped to 23"), no meta-commentary ("in a dramatic turn of events"). State slots resolve to qualitative prose ("precarious," "fragile"), never raw numbers.

Rule 6 — Length hard limits. Opening: max 30 words. Detail: max 60 words. Closing: max 50 words.

Rule 7 — Temporal language conventions. Openings own time-anchoring language ("In the decades that followed," "A generation later"). Details and closings continue from the opening's temporal frame without re-anchoring.

Rule 8 — Category-specific required slots. Every fragment in a category must use all slots listed as required for that category."""

FRAGMENT_STRUCTURE = """Fragment Structure:

Opening — sets tone and temporal context. One sentence, max 30 words. Anchors when and where. Used in both base and expanded form.

Detail — the specific events, drawn from cluster data. One to two sentences, max 60 words. The substance of the entry. Used in both base and expanded form.

Closing — implication, forward look, or emotional beat. One to two sentences, max 50 words. Used only in expanded form. Adds the "so what."

Base form = opening + detail (under 90 words).
Expanded form = opening + detail + closing (under 140 words).

Fragment Compatibility Rule: Any opening in a category can combine with any detail in that category and any closing in that category. The category boundary is the compatibility guarantee. Each fragment assumes nothing about its paired fragments except shared category and emotional register."""


def _build_system_prompt():
    return f"""You are a historical chronicle fragment writer for a civilization simulation game. You write prose fragments that read like excerpts from a real history — never like game text.

{FRAGMENT_RULES}

{FRAGMENT_STRUCTURE}

{SLOT_VOCABULARY}

Output Format:
Return a JSON object with three arrays: "openings", "details", and "closings". Each fragment is an object with:
- "id": a unique ID in the format "XX_T_NNN" where XX is the category abbreviation, T is O/D/C for opening/detail/closing, and NNN is a zero-padded number
- "text": the fragment prose with variable slots in curly braces
- "slots_used": array of slot names used in the text. Example: "slots_used": ["{{lineage_name}}", "{{region_name}}"]
- "word_count": integer word count of the text (counting slot placeholders as one word each)

Example fragments (from a hypothetical "example_category" — do NOT copy these, they illustrate format only):

{{"openings": [
  {{
    "id": "EC_O_001",
    "text": "In the decades following the upheaval at {{region_name}}, the {{lineage_name}} household found its standing quietly transformed.",
    "slots_used": ["{{region_name}}", "{{lineage_name}}"],
    "word_count": 16
  }}
],
"details": [
  {{
    "id": "EC_D_001",
    "text": "The {{lineage_name}} name carried weight in the merchant halls now, and with that weight came new debts, new rivals, and the particular kind of ambition that only prosperity breeds.",
    "slots_used": ["{{lineage_name}}"],
    "word_count": 30
  }}
],
"closings": []}}

Generate exactly 6 openings, 8 details, and 5 closings (19 fragments total)."""


def _build_user_message(category):
    name = category["name"]
    register = category["register"]
    required = ", ".join(category["required_slots"])
    optional = ", ".join(category["optional_slots"])

    abbrev = "".join(word[0].upper() for word in name.split("_"))

    return f"""Category: {name}
Emotional register: {register}
Required slots (every fragment must use): {required}
Optional slots (use for variety): {optional}
ID prefix: {abbrev}

Generate 6 openings (max 30 words each), 8 details (max 60 words each), and 5 closings (max 50 words each) for this category.

Every fragment must:
- Match the emotional register: {register}
- Use all required slots: {required}
- Use only slots from the defined vocabulary
- Read like a real historical text, not game output

Return as JSON with keys "openings", "details", "closings"."""


def _category_abbrev(name):
    return "".join(word[0].upper() for word in name.split("_"))


def run_manual_chronicle(output_dir="prompts"):
    os.makedirs(output_dir, exist_ok=True)
    system_prompt = _build_system_prompt()

    for i, cat in enumerate(CATEGORIES):
        num = i + 1
        filename = f"{num:02d}_{cat['name']}.txt"
        filepath = os.path.join(output_dir, filename)

        user_msg = _build_user_message(cat)
        divider = "\u2500" * 56

        with open(filepath, "w") as f:
            f.write(f"=== PROMPT {num:02d} of {len(CATEGORIES)} "
                    f"— Category: {cat['name']} ===\n")
            f.write(f"Copy everything below the line into Claude (claude.ai).\n")
            f.write(f"Save Claude's complete response to: "
                    f"batch_output/{num:02d}_{cat['name']}.txt\n")
            f.write(f"{divider}\n\n")
            f.write(f"[SYSTEM PROMPT]\n\n{system_prompt}\n\n")
            f.write(f"[USER MESSAGE]\n\n{user_msg}\n")

        print(f"  [{num:02d}/{len(CATEGORIES)}] {filepath}")

    print(f"\nGenerated {len(CATEGORIES)} prompt files in {output_dir}/")
    os.makedirs("batch_output", exist_ok=True)
    print(f"Created batch_output/ directory for responses.")


NAME_CATEGORIES = ["people", "places", "units", "factions"]
NAME_TARGETS = {"people": 500, "places": 200, "units": 200, "factions": 100}

FACTION_IDS = [
    "player", "conqueror", "fortifier", "opportunist",
    "faction_05", "faction_06", "faction_07", "faction_08",
    "faction_09", "faction_10",
]

from naming_system import _ALL_VALUES
import config
import random


def _generate_variable_subsets(seed=42, locked_factions=None):
    rng = random.Random(seed)
    subsets = {}
    used_roots = set()

    if locked_factions:
        for fid, sub in locked_factions.items():
            subsets[fid] = sub
            used_roots.update(sub["linguistic_roots"])

    for fid in FACTION_IDS:
        if fid in subsets:
            continue

        if fid == "player":
            n_roots, n_patterns, n_tags = config.PLAYER_FACTION_SUBSET_WIDTH
        else:
            n_roots, n_patterns, n_tags = config.DEFAULT_FACTION_SUBSET_WIDTH

        available_roots = [r for r in _ALL_VALUES["linguistic_roots"] if r not in used_roots]
        if len(available_roots) < n_roots:
            available_roots = list(_ALL_VALUES["linguistic_roots"])
        roots = rng.sample(available_roots, min(n_roots, len(available_roots)))
        used_roots.update(roots)

        patterns = rng.sample(_ALL_VALUES["phoneme_patterns"],
                              min(n_patterns, len(_ALL_VALUES["phoneme_patterns"])))
        tags = rng.sample(_ALL_VALUES["cultural_flavor_tags"],
                          min(n_tags, len(_ALL_VALUES["cultural_flavor_tags"])))

        subsets[fid] = {
            "linguistic_roots": roots,
            "phoneme_patterns": patterns,
            "cultural_flavor_tags": tags,
        }
    return subsets


def _build_naming_system_prompt():
    return """You are a name generator for a civilization simulation game. You generate names that feel culturally coherent within a faction and distinct across factions.

Rules:
1. Names must feel like they belong to the same culture — consistent phonetic patterns, syllable structures, and aesthetic.
2. Draw freely from real human history and linguistic traditions. Names inspired by or adapted from historical cultures are encouraged. The only restriction: no names from Isaac Asimov's Foundation series.
3. Names should work across any time period — avoid era-specific modifiers (no "cyber-", no "Sir").
4. People names: first + last name (two parts). Place names: evocative single or compound names. Unit names: military-flavored compound names. Faction names: organization or polity names.
5. Vary syllable count (2-4 syllables), name structure, and phonetic shape across the batch. Not every name should follow the same template.

CRITICAL — Do NOT:
- Generate names by combining roots and suffixes systematically (e.g. Aath, Baath, Caath, Daath...)
- Enumerate through the alphabet
- Reuse the same first-name or last-name component more than 3 times in a batch
- Produce names that are just permutations of the same phoneme set
Each name should feel individually crafted, as if pulled from a real historical record.

Output Format:
Return a JSON object with a single key "names" containing an array of name strings.
Example: {"names": ["Kaelith Vorn", "Suranna Deshkov", "Toryn Ashemark"]}"""


BATCH_SIZE = 75
BATCH_SIZE_FACTIONS = 55

def _build_naming_user_message(faction_id, category, subset, count, batch_num=1, total_batches=1, existing_names=None):
    roots = ", ".join(subset["linguistic_roots"])
    patterns = ", ".join(subset["phoneme_patterns"])
    tags = ", ".join(subset["cultural_flavor_tags"])

    msg = f"""Faction: {faction_id}
Name category: {category}
Generate: {count} names (batch {batch_num} of {total_batches})

This faction's cultural profile:
- Linguistic roots: {roots}
- Phoneme patterns: {patterns}
- Cultural flavor tags: {tags}

Every name should reflect this faction's cultural profile. Names should feel like they come from a real civilization's historical records — varied, organic, individually crafted."""

    if existing_names:
        sample = existing_names[:30]
        msg += f"\n\nPreviously generated names for this faction (avoid duplicates and stay consistent with the established style): {', '.join(sample)}"
        if len(existing_names) > 30:
            msg += f" ... and {len(existing_names) - 30} more"

    msg += f'\n\nReturn as JSON: {{"names": [...]}}'
    return msg


ARCHETYPE_FACTIONS = ["player", "conqueror", "fortifier", "opportunist"]

ORIGINAL_ARCHETYPE_SUBSETS = {
    "player": {
        "linguistic_roots": ["Sino-monosyllabic", "Semitic triconsonantal", "Gaelic consonant-cluster"],
        "phoneme_patterns": ["single name only", "two-part compound", "honorific-suffix", "title-prefix"],
        "cultural_flavor_tags": ["ancient/archaic", "pastoral", "maritime", "revolutionary"],
    },
    "conqueror": {
        "linguistic_roots": ["Nahuatl compound", "Semitic triconsonantal"],
        "phoneme_patterns": ["patronymic", "place-derived", "two-part compound"],
        "cultural_flavor_tags": ["priestly", "maritime", "aristocratic"],
    },
    "fortifier": {
        "linguistic_roots": ["Semitic triconsonantal", "invented guttural-aspirated"],
        "phoneme_patterns": ["two-part compound", "reduplicative", "consonant-final"],
        "cultural_flavor_tags": ["priestly", "nomadic", "aristocratic"],
    },
    "opportunist": {
        "linguistic_roots": ["invented guttural-aspirated", "Persian flowing"],
        "phoneme_patterns": ["patronymic", "title-prefix", "consonant-final"],
        "cultural_flavor_tags": ["imperial/formal", "frontier/rough", "mercantile"],
    },
}

def run_manual_naming(output_dir="prompts", start_num=21, locked_factions=None):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("batch_output", exist_ok=True)

    subsets = _generate_variable_subsets(locked_factions=locked_factions)
    subsets_path = os.path.join(output_dir, "variable_subsets.json")
    with open(subsets_path, "w") as f:
        json.dump(subsets, f, indent=2)
    print(f"  Variable subsets written to {subsets_path}")

    system_prompt = _build_naming_system_prompt()
    prompt_num = start_num - 1

    import math
    for fid in ARCHETYPE_FACTIONS:
        subset = subsets[fid]
        for cat in NAME_CATEGORIES:
            target = NAME_TARGETS[cat]
            overshoot = int(target * config.BUILDER_NAME_OVERSHOOT)
            batch_size = BATCH_SIZE_FACTIONS if cat == "factions" else BATCH_SIZE
            num_batches = math.ceil(overshoot / batch_size)

            for b in range(num_batches):
                prompt_num += 1
                batch_count = min(batch_size, overshoot - b * batch_size)
                user_msg = _build_naming_user_message(
                    fid, cat, subset, batch_count,
                    batch_num=b + 1, total_batches=num_batches,
                )

                if num_batches == 1:
                    filename = f"{prompt_num:02d}_{fid}_{cat}.txt"
                else:
                    filename = f"{prompt_num:02d}_{fid}_{cat}_b{b+1}.txt"
                filepath = os.path.join(output_dir, filename)
                divider = "\u2500" * 56

                with open(filepath, "w") as f:
                    f.write(f"=== PROMPT {prompt_num:02d} "
                            f"— Faction: {fid}, Category: {cat}, "
                            f"Batch {b+1}/{num_batches} ===\n")
                    f.write(f"Copy everything below the line into Claude (claude.ai).\n")
                    f.write(f"Save Claude's complete response to: "
                            f"batch_output/{filename}\n")
                    f.write(f"{divider}\n\n")
                    f.write(f"[SYSTEM PROMPT]\n\n{system_prompt}\n\n")
                    f.write(f"[USER MESSAGE]\n\n{user_msg}\n")

                print(f"  [{prompt_num:02d}] {filepath}")

    total = prompt_num - start_num + 1
    print(f"\nGenerated {total} naming prompt files in {output_dir}/")
    print(f"Variable subsets: {subsets_path}")


def run_api_chronicle():
    print("API mode not yet implemented.")


def run_api_review_chronicle():
    print("API-review mode not yet implemented.")


def main():
    parser = argparse.ArgumentParser(description="Library Builder — offline content generation")
    parser.add_argument("--mode", choices=["api", "manual", "api-review"],
                        required=True, help="Operating mode")
    parser.add_argument("--content", choices=["chronicle", "naming", "all"],
                        required=True, help="Content type to generate")
    args = parser.parse_args()

    if args.content in ("chronicle", "all"):
        if args.mode == "manual":
            run_manual_chronicle()
        elif args.mode == "api":
            run_api_chronicle()
        elif args.mode == "api-review":
            run_api_review_chronicle()

    if args.content in ("naming", "all"):
        if args.mode == "manual":
            start = 21 if args.content == "all" else 1
            run_manual_naming(start_num=start, locked_factions=ORIGINAL_ARCHETYPE_SUBSETS)
        else:
            print(f"Mode {args.mode} for naming not yet implemented.")


if __name__ == "__main__":
    main()
