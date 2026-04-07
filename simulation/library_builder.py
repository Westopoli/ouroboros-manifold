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


def run_manual_naming(output_dir="prompts"):
    print("Naming pool generation not yet implemented (Step F).")


def run_api_chronicle():
    print("API mode not yet implemented.")


def run_api_review_chronicle():
    print("API-review mode not yet implemented.")


def main():
    parser = argparse.ArgumentParser(description="Library Builder — offline content generation")
    parser.add_argument("--mode", choices=["api", "manual", "api-review"],
                        required=True, help="Operating mode")
    parser.add_argument("--content", choices=["chronicle", "naming"],
                        required=True, help="Content type to generate")
    args = parser.parse_args()

    if args.content == "chronicle":
        if args.mode == "manual":
            run_manual_chronicle()
        elif args.mode == "api":
            run_api_chronicle()
        elif args.mode == "api-review":
            run_api_review_chronicle()
    elif args.content == "naming":
        if args.mode == "manual":
            run_manual_naming()
        else:
            print(f"Mode {args.mode} for naming not yet implemented.")


if __name__ == "__main__":
    main()
