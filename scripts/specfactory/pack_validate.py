#!/usr/bin/env python3
"""Validates an era pack directory (docs/bible/epics/E-20-multi-era-and-
monetization.md R-146-01, R-146-03; docs/northstar/plans/briefs/
2026-09-21-px-batch-b-spec-content-boundary.md PX-10).

Checks manifest.json (assets/eras/<era>/manifest.json shape) for: every
required top-level key present (including era_spatial_scale, era_tone, era_order; test_only is an optional bool) (R-146-03: a missing one fails, named); every
referenced scene path exists on disk relative to the pack; no unit id
contains the era's own era_id (R-145-01, "no identifier names an era",
applied to content); and era_display_name plus any naming_pools entry
contains no word from banned_words.txt. A top-level key not in
REQUIRED_KEYS (e.g. a future "weather" class) is optional and its absence is
never a finding (R-146-03's "a missing optional asset uses the placeholder").

Usage:
    scripts/specfactory/pack_validate.py <pack_dir> [--banned-words FILE] [--json]
    scripts/specfactory/pack_validate.py --mechanical <pack_dir>
    scripts/specfactory/pack_validate.py --diff-mechanical <pack_dir> <reference_dir>

Exit code 0 if the pack has no FAIL-level finding. Exit code 1 with every
failing entry named otherwise. Exit code 2 on a usage error (missing pack
directory). --diff-mechanical exits 0 if the two packs' mechanical (non-art,
non-name) keys are identical, 1 with the diff otherwise -- the fenced content
diff a `kind: content` card's acceptance runs (R-146-02: identical mechanics
across eras).
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

REQUIRED_KEYS = (
    "era_id", "era_display_name", "era_accent_color",
    "era_spatial_scale", "era_tone", "era_order",
    "units", "structures", "environment", "materials", "faction_colors",
)

DEFAULT_BANNED_WORDS_FILE = Path(__file__).resolve().parents[2] / "docs/northstar/spec_factory/banned_words.txt"


class Finding(dict):
    def __init__(self, level: str, code: str, message: str):
        super().__init__(level=level, code=code, message=message)


def load_banned_words(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    words: set[str] = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        words.add(line.lower())
    return words


def _banned_hits(text: str, banned: set[str]) -> list[str]:
    lowered = text.lower()
    return [w for w in sorted(banned) if re.search(rf"\b{re.escape(w)}\b", lowered)]


def _iter_scene_paths(entry) -> list[str]:
    if not isinstance(entry, dict):
        return []
    scenes = []
    if isinstance(entry.get("scene"), str):
        scenes.append(entry["scene"])
    tiers = entry.get("tiers")
    if isinstance(tiers, dict):
        for tier in tiers.values():
            if isinstance(tier, dict) and isinstance(tier.get("scene"), str):
                scenes.append(tier["scene"])
    return scenes


def validate_pack(pack_dir: Path, banned_words_path: Path = DEFAULT_BANNED_WORDS_FILE) -> list[Finding]:
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        return [Finding("FAIL", "MISSING_MANIFEST", f"no manifest.json in {pack_dir}")]
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        return [Finding("FAIL", "BAD_MANIFEST_JSON", f"manifest.json does not parse: {exc}")]

    findings: list[Finding] = []

    for key in REQUIRED_KEYS:
        if key not in manifest:
            findings.append(Finding("FAIL", "MISSING_REQUIRED_KEY", f"manifest.json is missing required key: {key}"))

    for key in ("era_spatial_scale", "era_tone"):
        value = manifest.get(key)
        if key in manifest and not (isinstance(value, str) and value.strip()):
            findings.append(Finding("FAIL", "BAD_ERA_IDENTITY", f"{key} must be non-empty text"))
    order = manifest.get("era_order")
    if "era_order" in manifest and (not isinstance(order, int) or isinstance(order, bool)):
        findings.append(Finding("FAIL", "BAD_ERA_IDENTITY", "era_order must be an int"))
    if "test_only" in manifest and not isinstance(manifest["test_only"], bool):
        findings.append(Finding("FAIL", "BAD_ERA_IDENTITY", "test_only must be a bool when present"))

    era_id = manifest.get("era_id")
    units = manifest.get("units")
    if isinstance(era_id, str) and era_id and isinstance(units, dict):
        for unit_id in units:
            if era_id.lower() in unit_id.lower():
                findings.append(Finding(
                    "FAIL", "ERA_ID_IN_UNIT_ID",
                    f"unit id {unit_id!r} contains the era id {era_id!r}",
                ))

    for class_name in ("units", "structures", "environment"):
        entries = manifest.get(class_name)
        if not isinstance(entries, dict):
            continue
        for entry_id, entry in entries.items():
            for scene in _iter_scene_paths(entry):
                if not (pack_dir / scene).is_file():
                    findings.append(Finding(
                        "FAIL", "MISSING_SCENE",
                        f"{class_name}.{entry_id}: scene not found: {scene}",
                    ))

    banned = load_banned_words(banned_words_path)
    if banned:
        display_name = manifest.get("era_display_name")
        if isinstance(display_name, str):
            for word in _banned_hits(display_name, banned):
                findings.append(Finding(
                    "FAIL", "BANNED_WORD",
                    f"era_display_name contains banned word {word!r}: {display_name!r}",
                ))
        naming_pools = manifest.get("naming_pools")
        if isinstance(naming_pools, dict):
            for pool_name, names in naming_pools.items():
                if not isinstance(names, list):
                    continue
                for name in names:
                    if not isinstance(name, str):
                        continue
                    for word in _banned_hits(name, banned):
                        findings.append(Finding(
                            "FAIL", "BANNED_WORD",
                            f"naming_pools.{pool_name} entry {name!r} contains banned word {word!r}",
                        ))

    return findings


# ---- mechanical-keys content diff (R-146-02: identical across eras except
# art, names, and prose) -- the fence a `kind: content` card's acceptance
# runs alongside pack_validate.py itself, so the worker cannot touch either
# the validator or drift the gameplay-relevant shape of the pack it builds.

def mechanical_keys(manifest: dict) -> dict:
    units = manifest.get("units") if isinstance(manifest.get("units"), dict) else {}
    structures = manifest.get("structures") if isinstance(manifest.get("structures"), dict) else {}
    environment = manifest.get("environment") if isinstance(manifest.get("environment"), dict) else {}
    materials = manifest.get("materials") if isinstance(manifest.get("materials"), dict) else {}
    faction_colors = manifest.get("faction_colors") if isinstance(manifest.get("faction_colors"), dict) else {}
    return {
        "unit_ids": sorted(units.keys()),
        "unit_categories": {k: v.get("category") for k, v in units.items() if isinstance(v, dict)},
        "unit_squad_counts": {k: v.get("squad_count") for k, v in units.items() if isinstance(v, dict)},
        "unit_tier_counts": {k: len(v.get("tiers") or {}) for k, v in units.items() if isinstance(v, dict)},
        "structure_ids": sorted(structures.keys()),
        "structure_tier_counts": {k: len(v.get("tiers") or {}) for k, v in structures.items() if isinstance(v, dict)},
        "environment_ids": sorted(environment.keys()),
        "material_tier_treatments": {k: v.get("faction_color_treatment") for k, v in materials.items() if isinstance(v, dict)},
        "faction_color_count": len(faction_colors),
    }


def diff_mechanical(pack_dir: Path, reference_dir: Path) -> tuple[bool, str]:
    a = mechanical_keys(json.loads((pack_dir / "manifest.json").read_text()))
    b = mechanical_keys(json.loads((reference_dir / "manifest.json").read_text()))
    a_text = json.dumps(a, indent=2, sort_keys=True).splitlines(keepends=True)
    b_text = json.dumps(b, indent=2, sort_keys=True).splitlines(keepends=True)
    diff_lines = list(difflib.unified_diff(b_text, a_text, fromfile=str(reference_dir), tofile=str(pack_dir)))
    return not diff_lines, "".join(diff_lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pack_dir", nargs="?")
    ap.add_argument("--banned-words", default=str(DEFAULT_BANNED_WORDS_FILE))
    ap.add_argument("--mechanical", metavar="PACK_DIR", help="print the pack's mechanical-keys JSON and exit")
    ap.add_argument("--diff-mechanical", nargs=2, metavar=("PACK_DIR", "REFERENCE_DIR"),
                     help="exit 0 if the two packs' mechanical keys are identical, 1 with the diff otherwise")
    ap.add_argument("--json", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2

    if args.mechanical is not None:
        manifest = json.loads((Path(args.mechanical) / "manifest.json").read_text())
        print(json.dumps(mechanical_keys(manifest), indent=2, sort_keys=True))
        return 0

    if args.diff_mechanical is not None:
        pack_dir, reference_dir = (Path(p) for p in args.diff_mechanical)
        identical, diff_text = diff_mechanical(pack_dir, reference_dir)
        if identical:
            print("MECHANICAL DIFF OK: identical")
            return 0
        print(diff_text)
        print("MECHANICAL DIFF FAILED: mechanical keys differ")
        return 1

    if not args.pack_dir:
        print("pack_dir is required unless --mechanical or --diff-mechanical is given", file=sys.stderr)
        return 2

    pack_dir = Path(args.pack_dir)
    if not pack_dir.is_dir():
        print(f"pack directory not found: {pack_dir}", file=sys.stderr)
        return 2

    findings = validate_pack(pack_dir, Path(args.banned_words).expanduser())
    fail_count = sum(1 for f in findings if f["level"] == "FAIL")

    if args.json:
        print(json.dumps({
            "pack": str(pack_dir),
            "findings": findings,
            "ok": fail_count == 0,
            "fail_count": fail_count,
        }, indent=2))
    else:
        for f in findings:
            print(f"PACK {f['level']} {f['code']} {f['message']}")
        print("PACK OK" if fail_count == 0 else f"PACK FAILED ({fail_count})")

    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
