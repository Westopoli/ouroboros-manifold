#!/usr/bin/env python3
import os, json, re

BATCH_DIR = "batch_output"
FACTION_IDS = ["player", "conqueror", "fortifier", "opportunist",
               "faction_05", "faction_06", "faction_07",
               "faction_08", "faction_09", "faction_10"]

def _is_naming_file(filename):
    return any(f"{fid}_" in filename for fid in FACTION_IDS)

for f in sorted(os.listdir(BATCH_DIR)):
    if "player_places" in f or "player_units" in f:
        is_naming = _is_naming_file(f)
        filepath = os.path.join(BATCH_DIR, f)
        size = os.path.getsize(filepath)
        raw = open(filepath).read().strip()
        raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)
        try:
            data = json.loads(raw)
            names = data.get("names", [])
            print(f"{f}: naming={is_naming} size={size} names={len(names)}")
        except Exception as e:
            print(f"{f}: naming={is_naming} size={size} PARSE ERROR: {e}")
            print(f"  First 100 chars: {raw[:100]}")
