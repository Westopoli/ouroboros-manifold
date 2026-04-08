#!/usr/bin/env python3
import json
import os
import re
import sys

BATCH_DIR = "batch_output"
LIBRARY_DIR = "library"

FACTION_IDS = [
    "player", "conqueror", "fortifier", "opportunist",
    "faction_05", "faction_06", "faction_07",
    "faction_08", "faction_09", "faction_10",
]


def strip_markdown_fences(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_response(filepath):
    with open(filepath) as f:
        raw = f.read()
    if not raw.strip():
        return None
    cleaned = strip_markdown_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"  ERROR parsing {filepath}: {e}")
        print(f"  First 200 chars: {cleaned[:200]}")
        return None


def _is_naming_file(filename):
    return any(f"{fid}_" in filename for fid in FACTION_IDS)


def _parse_naming_filename(filename):
    stem = filename.replace(".txt", "")
    stem = re.sub(r"_b\d+$", "", stem)
    tokens = stem.split("_")
    tokens = tokens[1:]
    category = tokens[-1]
    faction_id = "_".join(tokens[:-1])
    return faction_id, category


def _is_eponym(name):
    parts = name.strip().split()
    return len(parts) == 2 and parts[0] == parts[1]


def _filter_quality(batch_names, original_names, max_component_reuse=10):
    from collections import Counter
    first_count = Counter()
    last_count = Counter()
    kept = []

    for n in batch_names:
        if _is_eponym(n):
            continue
        parts = n.strip().split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) >= 2 else ""
        if first_count[first] >= max_component_reuse:
            continue
        if last and last_count[last] >= max_component_reuse:
            continue
        first_count[first] += 1
        if last:
            last_count[last] += 1
        kept.append(n)

    for n in original_names:
        if _is_eponym(n):
            continue
        parts = n.strip().split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) >= 2 else ""
        if first_count[first] >= max_component_reuse:
            continue
        if last and last_count[last] >= max_component_reuse:
            continue
        first_count[first] += 1
        if last:
            last_count[last] += 1
        kept.append(n)

    return kept


def ingest_chronicle():
    os.makedirs(os.path.join(LIBRARY_DIR, "chronicle"), exist_ok=True)
    all_fragments = []
    errors = 0

    for i in range(1, 21):
        pattern = f"{i:02d}_"
        matches = [f for f in os.listdir(BATCH_DIR)
                   if f.startswith(pattern) and not _is_naming_file(f)]
        if not matches:
            print(f"  MISSING: chronicle prompt {i:02d}")
            errors += 1
            continue

        filepath = os.path.join(BATCH_DIR, matches[0])
        data = parse_response(filepath)
        if data is None:
            errors += 1
            continue

        category = re.sub(r"_b\d+$", "", matches[0].replace(f"{i:02d}_", "").replace(".txt", ""))
        count = 0
        type_map = {"openings": "opening", "details": "detail", "closings": "closing"}
        for ftype in ("openings", "details", "closings"):
            for frag in data.get(ftype, []):
                frag["type"] = type_map[ftype]
                frag["category"] = category
                all_fragments.append(frag)
                count += 1

        print(f"  [{i:02d}] {category}: {count} fragments")

    outpath = os.path.join(LIBRARY_DIR, "chronicle", "fragments.json")
    with open(outpath, "w") as f:
        json.dump(all_fragments, f, indent=2)
    print(f"\n  Wrote {len(all_fragments)} fragments to {outpath}")
    if errors:
        print(f"  {errors} file(s) had errors or were missing")
    return all_fragments


def ingest_naming():
    os.makedirs(os.path.join(LIBRARY_DIR, "naming"), exist_ok=True)
    batch_names = {}   # (faction_id, category) -> [names from _b files]
    original_names = {} # (faction_id, category) -> [names from non-_b files]
    errors = 0

    all_files = sorted(f for f in os.listdir(BATCH_DIR) if f.endswith(".txt") and _is_naming_file(f))
    for f in all_files:
        filepath = os.path.join(BATCH_DIR, f)
        data = parse_response(filepath)
        if data is None:
            if os.path.getsize(filepath) > 0:
                errors += 1
            continue

        names = data.get("names", [])
        faction_id, category = _parse_naming_filename(f)
        key = (faction_id, category)
        is_batch = "_b" in f

        target = batch_names if is_batch else original_names
        target.setdefault(key, [])
        target[key].extend(names)

        batch_label = ""
        batch_match = re.search(r"_b(\d+)\.txt$", f)
        if batch_match:
            batch_label = f" (batch {batch_match.group(1)})"
        print(f"  {faction_id}/{category}{batch_label}: {len(names)} names")

    all_keys = set(batch_names.keys()) | set(original_names.keys())
    all_names = {}

    for key in sorted(all_keys):
        fid, cat = key
        b_names = list(dict.fromkeys(batch_names.get(key, [])))
        o_names = list(dict.fromkeys(original_names.get(key, [])))

        b_set = set(n.lower() for n in b_names)
        o_names = [n for n in o_names if n.lower() not in b_set]

        total_before = len(b_names) + len(o_names)
        merged = _filter_quality(b_names, o_names)
        removed = total_before - len(merged)

        all_names.setdefault(fid, {})
        all_names[fid][cat] = merged

        parts = []
        if b_names:
            parts.append(f"{len(b_names)} batch")
        if o_names:
            parts.append(f"{len(o_names)} original")
        source = " + ".join(parts)
        filter_note = f", quality filter removed {removed}" if removed else ""
        print(f"  {fid}/{cat}: {source} → {len(merged)} kept{filter_note}")

    outpath = os.path.join(LIBRARY_DIR, "naming", "names.json")
    with open(outpath, "w") as f:
        json.dump(all_names, f, indent=2)

    print(f"\n  Wrote names for {len(all_names)} factions to {outpath}")
    for fid in sorted(all_names):
        cats = ", ".join(f"{c}={len(ns)}" for c, ns in sorted(all_names[fid].items()))
        print(f"    {fid}: {cats}")
    if errors:
        print(f"  {errors} file(s) had errors")
    return all_names


def main():
    if not os.path.exists(BATCH_DIR):
        print(f"No {BATCH_DIR}/ directory found. Run the library builder first.")
        sys.exit(1)

    files = os.listdir(BATCH_DIR)
    txt_files = [f for f in files if f.endswith(".txt")]
    if not txt_files:
        print(f"No .txt files in {BATCH_DIR}/. Paste Claude's responses there first.")
        sys.exit(1)

    non_empty = [f for f in txt_files if os.path.getsize(os.path.join(BATCH_DIR, f)) > 0]
    print(f"Found {len(non_empty)} non-empty response files in {BATCH_DIR}/\n")

    has_chronicle = any(not _is_naming_file(f) for f in non_empty)
    has_naming = any(_is_naming_file(f) for f in non_empty)

    if has_chronicle:
        print("=== Ingesting Chronicle Fragments ===")
        ingest_chronicle()
        print()

    if has_naming:
        print("=== Ingesting Naming Pools ===")
        ingest_naming()
        print()

    print("=== Done ===")
    print(f"Library files written to {LIBRARY_DIR}/")


if __name__ == "__main__":
    main()
