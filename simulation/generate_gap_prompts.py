#!/usr/bin/env python3
import json
import math
import os
import re
from collections import Counter

BATCH_DIR = "batch_output"
PROMPT_DIR = "prompts"

FACTION_IDS = [
    "player", "conqueror", "fortifier", "opportunist",
    "faction_05", "faction_06", "faction_07",
    "faction_08", "faction_09", "faction_10",
]

ARCHETYPE_FACTIONS = ["player", "conqueror", "fortifier", "opportunist"]

NAME_TARGETS = {"people": 500, "places": 200, "units": 200, "factions": 100}
BATCH_SIZE = 75
BATCH_SIZE_FACTIONS = 55
OVERSHOOT = 1.10

from library_builder import (
    _build_naming_system_prompt, _build_naming_user_message,
    ORIGINAL_ARCHETYPE_SUBSETS,
)


def strip_markdown_fences(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_file(filepath):
    with open(filepath) as f:
        raw = f.read()
    if not raw.strip():
        return None
    cleaned = strip_markdown_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def is_eponym(name):
    parts = name.strip().split()
    return len(parts) == 2 and parts[0] == parts[1]


def find_overused_components(names, max_reuse=5):
    firsts = Counter()
    lasts = Counter()
    for n in names:
        parts = n.strip().split()
        if parts:
            firsts[parts[0]] += 1
        if len(parts) >= 2:
            lasts[parts[-1]] += 1
    return (
        {k for k, v in firsts.items() if v > max_reuse},
        {k for k, v in lasts.items() if v > max_reuse},
    )


def filter_names(names):
    seen = set()
    kept = []
    overused_first, overused_last = find_overused_components(names)
    first_usage = Counter()
    last_usage = Counter()

    for name in names:
        name = name.strip()
        if not name:
            continue
        lower = name.lower()
        if lower in seen:
            continue
        seen.add(lower)
        if is_eponym(name):
            continue
        parts = name.split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) >= 2 else ""
        if first in overused_first and first_usage[first] >= 3:
            continue
        if last and last in overused_last and last_usage[last] >= 3:
            continue
        first_usage[first] += 1
        if last:
            last_usage[last] += 1
        kept.append(name)
    return kept


def load_existing_names():
    pools = {}
    files = sorted(f for f in os.listdir(BATCH_DIR) if f.endswith(".txt"))

    for f in files:
        is_naming = any(f"{fid}_" in f for fid in FACTION_IDS)
        if not is_naming or "_b" in f:
            continue
        filepath = os.path.join(BATCH_DIR, f)
        if os.path.getsize(filepath) == 0:
            continue
        data = parse_file(filepath)
        if data is None:
            continue
        names = data.get("names", [])
        if not names:
            continue

        stem = f.replace(".txt", "")
        tokens = stem.split("_")[1:]
        category = tokens[-1]
        faction_id = "_".join(tokens[:-1])

        if faction_id not in ARCHETYPE_FACTIONS:
            continue

        kept = filter_names(names)
        pools[(faction_id, category)] = kept
    return pools


def main():
    existing = load_existing_names()
    system_prompt = _build_naming_system_prompt()

    # Clean old gap-fill prompts
    for f in os.listdir(PROMPT_DIR):
        if f.endswith(".txt") and "_b" in f:
            os.remove(os.path.join(PROMPT_DIR, f))

    prompt_num = 20  # start after chronicle prompts
    total_prompts = 0
    divider = "\u2500" * 56

    for fid in ARCHETYPE_FACTIONS:
        subset = ORIGINAL_ARCHETYPE_SUBSETS[fid]
        for cat in ["people", "places", "units", "factions"]:
            target = int(NAME_TARGETS[cat] * OVERSHOOT)
            salvaged = existing.get((fid, cat), [])
            gap = max(0, target - len(salvaged))

            if gap == 0:
                print(f"  {fid}/{cat}: COMPLETE ({len(salvaged)} salvaged >= {target} target)")
                continue

            batch_size = BATCH_SIZE_FACTIONS if cat == "factions" else BATCH_SIZE
            num_batches = math.ceil(gap / batch_size)

            for b in range(num_batches):
                prompt_num += 1
                batch_count = min(batch_size, gap - b * batch_size)
                user_msg = _build_naming_user_message(
                    fid, cat, subset, batch_count,
                    batch_num=b + 1, total_batches=num_batches,
                    existing_names=salvaged,
                )

                filename = f"{prompt_num:02d}_{fid}_{cat}_b{b+1}.txt"
                filepath = os.path.join(PROMPT_DIR, filename)

                with open(filepath, "w") as f:
                    f.write(f"=== PROMPT {prompt_num:02d} "
                            f"— Faction: {fid}, Category: {cat}, "
                            f"Batch {b+1}/{num_batches} "
                            f"(gap-fill: {len(salvaged)} salvaged, need {gap} more) ===\n")
                    f.write(f"Copy everything below the line into Claude (claude.ai).\n")
                    f.write(f"Save Claude's complete response to: "
                            f"batch_output/{filename}\n")
                    f.write(f"{divider}\n\n")
                    f.write(f"[SYSTEM PROMPT]\n\n{system_prompt}\n\n")
                    f.write(f"[USER MESSAGE]\n\n{user_msg}\n")

                # Create empty shell file
                batch_path = os.path.join(BATCH_DIR, filename)
                if not os.path.exists(batch_path):
                    open(batch_path, "w").close()

                print(f"  [{prompt_num:02d}] {filepath}")
                total_prompts += 1

    print(f"\nGenerated {total_prompts} gap-fill prompt files (#{21}-#{prompt_num})")
    print(f"Chronicle prompts (01-20) unchanged.")


if __name__ == "__main__":
    main()
