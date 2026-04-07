from library_validator import validate_all

test_fragments = [
    # ── Category A: lineage_thrived (5 fragments) ──
    {
        "id": "LT_O_001", "type": "opening", "category": "lineage_thrived",
        "text": "In the years that followed, the {lineage_name} family found new footing in {region_name}.",
    },
    {
        "id": "LT_D_001", "type": "detail", "category": "lineage_thrived",
        "text": "The {lineage_name} household prospered as trade routes shifted in their favor, drawing wealth and influence to their holdings.",
    },
    # DELIBERATE ERROR: invalid slot {mood_rating}
    {
        "id": "LT_D_002", "type": "detail", "category": "lineage_thrived",
        "text": "Their standing improved markedly, the {lineage_name} name spoken with a {mood_rating} that surprised even their allies.",
    },
    {
        "id": "LT_C_001", "type": "closing", "category": "lineage_thrived",
        "text": "What the {lineage_name} built in those years would outlast the generation that built it.",
    },
    # DELIBERATE ERROR: mechanical language
    {
        "id": "LT_C_002", "type": "closing", "category": "lineage_thrived",
        "text": "Stability dropped to 23 across the {lineage_name} holdings, though few noticed at first.",
    },

    # ── Category B: chain_conflict_victory (5 fragments) ──
    {
        "id": "CCV_O_001", "type": "opening", "category": "chain_conflict_victory",
        "text": "The campaign for {region_name} ended as swiftly as it had begun.",
    },
    # DELIBERATE ERROR: word limit exceeded (opening > 30 words)
    {
        "id": "CCV_O_002", "type": "opening", "category": "chain_conflict_victory",
        "text": "After long months of siege and counter-siege across the disputed territories surrounding {region_name}, "
                "the defenders finally broke and the gates were thrown open to the advancing columns of the victorious army.",
    },
    {
        "id": "CCV_D_001", "type": "detail", "category": "chain_conflict_victory",
        "text": "The {faction_name} forces swept through {region_name}, establishing control before the defenders could regroup.",
    },
    # DELIBERATE ERROR: near-duplicate of CCV_D_001 (edit distance < 3)
    {
        "id": "CCV_D_002", "type": "detail", "category": "chain_conflict_victory",
        "text": "The {faction_name} forces swept through {region_name}, establishing control before the defenders could re-group.",
    },
    {
        "id": "CCV_C_001", "type": "closing", "category": "chain_conflict_victory",
        "text": "The new border held, though the cost of holding it would be measured in generations, not campaigns.",
    },

    # ── Category C: regional_decline (5 fragments) ──
    {
        "id": "RD_O_001", "type": "opening", "category": "regional_decline",
        "text": "The slow erosion of {region_name} began without fanfare.",
    },
    {
        "id": "RD_D_001", "type": "detail", "category": "regional_decline",
        "text": "Fields lay fallow and the young departed for more promising lands, leaving {region_name} to age in silence.",
    },
    {
        "id": "RD_D_002", "type": "detail", "category": "regional_decline",
        "text": "What had once been a {stability_level} province now showed cracks in every institution.",
    },
    {
        "id": "RD_C_001", "type": "closing", "category": "regional_decline",
        "text": "No single event marked {region_name}'s decline — it was the accumulation of a hundred small surrenders.",
    },
    {
        "id": "RD_C_002", "type": "closing", "category": "regional_decline",
        "text": "The land endured, as it always had, though fewer remained to tend it.",
    },
]

required_slots = {
    "lineage_thrived": {"{lineage_name}"},
    "chain_conflict_victory": {"{region_name}"},
    "regional_decline": {"{region_name}"},
}

report = validate_all(test_fragments, category_required_slots=required_slots)

print("=== Checkpoint E: Library Validator ===")
print(f"  Total fragments: {report['summary']['total_fragments']}")

print(f"\n=== Layer 1: Structural ({report['summary']['structural_failures']} issues) ===")
for issue in report["structural"]:
    print(f"  [{issue['id']}] {issue['issue']}: {issue['detail']}")

print(f"\n=== Layer 2: Dedup ({report['summary']['dedup_matches']} matches) ===")
for match in report["dedup"]["matches"]:
    print(f"  {match['id_a']} <-> {match['id_b']} "
          f"(pool={match['pool']}, distance={match['distance']})")
for tp in report["dedup"]["thin_pools"]:
    print(f"  THIN POOL: {tp['pool']} — {tp['dupes']}/{tp['total']} "
          f"({tp['loss_pct']}% loss)")

print(f"\n=== Layer 3: Tone ({report['summary']['tone_flags']} flags) ===")
for flag in report["tone"]:
    print(f"  [{flag['id']}] {flag['issue']}: {flag['detail']}")

print("\n=== Error Detection Summary ===")
errors_expected = {
    "invalid_slot ({mood_rating})": any(
        i["issue"] == "invalid_slot" and "mood_rating" in i["detail"]
        for i in report["structural"]),
    "word_limit (CCV_O_002)": any(
        i["issue"] == "word_limit_exceeded" and i["id"] == "CCV_O_002"
        for i in report["structural"]),
    "mechanical_language (stability dropped to 23)": any(
        i["issue"] == "mechanical_language" and i["id"] == "LT_C_002"
        for i in report["structural"]),
    "near-duplicate (CCV_D_001/CCV_D_002)": any(
        (m["id_a"] == "CCV_D_001" and m["id_b"] == "CCV_D_002") or
        (m["id_a"] == "CCV_D_002" and m["id_b"] == "CCV_D_001")
        for m in report["dedup"]["matches"]),
}
all_caught = True
for desc, caught in errors_expected.items():
    status = "CAUGHT" if caught else "MISSED"
    if not caught:
        all_caught = False
    print(f"  {desc}: {status}")

print(f"\n  All deliberate errors caught: {'YES' if all_caught else 'NO'}")
