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
        for ftype in ("openings", "details", "closings"):
            for frag in data.get(ftype, []):
                frag["type"] = ftype.rstrip("s")
                if ftype == "closings":
                    frag["type"] = "closing"
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
    all_names = {}
    errors = 0

    for f in sorted(os.listdir(BATCH_DIR)):
        if not f.endswith(".txt") or not _is_naming_file(f):
            continue

        filepath = os.path.join(BATCH_DIR, f)
        data = parse_response(filepath)
        if data is None:
            if os.path.getsize(filepath) > 0:
                errors += 1
            continue

        names = data.get("names", [])
        faction_id, category = _parse_naming_filename(f)

        all_names.setdefault(faction_id, {})
        if category in all_names[faction_id]:
            all_names[faction_id][category].extend(names)
        else:
            all_names[faction_id][category] = list(names)

        batch_label = ""
        batch_match = re.search(r"_b(\d+)\.txt$", f)
        if batch_match:
            batch_label = f" (batch {batch_match.group(1)})"
        print(f"  {faction_id}/{category}{batch_label}: {len(names)} names")

    for fid in all_names:
        for cat in all_names[fid]:
            before = len(all_names[fid][cat])
            all_names[fid][cat] = list(dict.fromkeys(all_names[fid][cat]))
            after = len(all_names[fid][cat])
            if before != after:
                print(f"  {fid}/{cat}: deduped {before} → {after}")

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
