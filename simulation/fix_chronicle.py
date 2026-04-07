#!/usr/bin/env python3
import json
import re

with open("batch_output/20_consequence_mixed.txt") as f:
    raw = f.read().strip()
raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
raw = re.sub(r"\n?```\s*$", "", raw)
data = json.loads(raw)

print("=== Fragments missing {mission_outcome} ===\n")
for ftype in ("details", "closings"):
    for frag in data[ftype]:
        if "{mission_outcome}" not in frag["text"]:
            print(f"  {frag['id']} ({ftype}):")
            print(f"    {frag['text']}\n")

print("=== Patching — inserting {mission_outcome} ===\n")

patches = {
    "CM_D_001": "What had been intended as {mission_outcome} instead became something harder to name — not failure, not triumph, but the kind of result that reshaped {mission_region} without satisfying anyone.",
    "CM_D_003": "The {character_name} campaign yielded {mission_outcome}, though the word 'yielded' perhaps overstated the certainty of it — the consequences would take a generation to fully understand.",
    "CM_D_007": "In {mission_region}, what the commanders called {mission_outcome} looked rather different to those who lived through it, the {lineage_name} household among them.",
    "CM_C_002": "Whether {mission_outcome} had been worth the cost was a question the {lineage_name} family would debate for generations.",
    "CM_C_003": "The ledger of {mission_outcome} balanced only if one squinted — and the {lineage_name} name was written on both sides.",
    "CM_C_005": "History would record {mission_outcome}, though history, as always, would leave out the parts that mattered most to those who lived it.",
}

patched = 0
for ftype in ("details", "closings"):
    for frag in data[ftype]:
        if frag["id"] in patches:
            old = frag["text"]
            frag["text"] = patches[frag["id"]]
            frag["word_count"] = len(frag["text"].replace("{", "").replace("}", "").split())
            if "{mission_outcome}" not in frag.get("slots_used", []):
                frag.setdefault("slots_used", []).append("{mission_outcome}")
            print(f"  {frag['id']}: PATCHED")
            patched += 1

with open("batch_output/20_consequence_mixed.txt", "w") as f:
    json.dump(data, f, indent=2)

print(f"\n  Patched {patched} fragments. File saved.")

# Verify
with open("batch_output/20_consequence_mixed.txt") as f:
    verify = json.loads(f.read())
missing = 0
for ftype in ("details", "closings"):
    for frag in verify[ftype]:
        if "{mission_outcome}" not in frag["text"]:
            missing += 1
print(f"  Remaining missing: {missing}")
