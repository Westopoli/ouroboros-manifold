#!/usr/bin/env python3
"""scripts/library/emit_chronicle_fragments.py
Parse csrc/chronicle.c CHRON_FRAGMENTS[] and placeholder name tables,
emit library/chronicle/fragments.json.

Usage:
    python scripts/library/emit_chronicle_fragments.py [output_path]

Fails loudly if zero fragments are parsed or if the count differs from
the CHRON_N_FRAGMENTS define in the C source.
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
_DEFAULT_OUT = os.path.join(_REPO, "library", "chronicle", "fragments.json")
_C_SOURCE = os.path.join(_REPO, "csrc", "chronicle.c")


def _read_source() -> str:
    with open(_C_SOURCE, encoding="utf-8") as f:
        return f.read()


def _n_define(src: str, name: str) -> int:
    m = re.search(r"#define\s+" + re.escape(name) + r"\s+(\d+)", src)
    if not m:
        raise SystemExit(f"ERROR: {name} not found in C source")
    return int(m.group(1))


def _parse_fragments(src: str) -> list:
    """Extract each element from CHRON_FRAGMENTS[] as a dict."""
    start_m = re.search(r"CHRON_FRAGMENTS\[\]\s*=\s*\{", src)
    if not start_m:
        raise SystemExit("ERROR: CHRON_FRAGMENTS[] not found in C source")
    start = start_m.end()
    end_m = re.search(r"/\* end constants-table \*/", src[start:])
    if end_m:
        end = start + end_m.start()
    else:
        em = re.search(r"^};", src[start:], re.MULTILINE)
        if not em:
            raise SystemExit("ERROR: could not find end of CHRON_FRAGMENTS[]")
        end = start + em.start()
    body = src[start:end]

    # Each entry: { "id_string", "text (may have {slots})", category, type, word_count }
    pattern = re.compile(
        r'\{\s*"([^"]+)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}'
    )
    fragments = []
    for i, m in enumerate(pattern.finditer(body)):
        c_id, text, category, ftype, _wc = m.groups()
        fragments.append({
            "id": i,
            "c_id": c_id,
            "category": int(category),
            "type": int(ftype),
            "text": text,
        })
    return fragments


def _parse_string_array(src: str, array_name: str) -> list:
    """Extract all string literals from a static const char* array."""
    m = re.search(
        r"\b" + re.escape(array_name) + r"\[\]\s*=\s*\{([^}]+)\}",
        src,
        re.DOTALL,
    )
    if not m:
        raise SystemExit(f"ERROR: {array_name} not found in C source")
    return re.findall(r'"([^"]*)"', m.group(1))


def main(out_path: str) -> None:
    src = _read_source()

    fragments = _parse_fragments(src)
    if not fragments:
        raise SystemExit("ERROR: parsed zero fragments from CHRON_FRAGMENTS[]")

    n_expected = _n_define(src, "CHRON_N_FRAGMENTS")
    if len(fragments) != n_expected:
        raise SystemExit(
            f"ERROR: parsed {len(fragments)} fragments but "
            f"CHRON_N_FRAGMENTS={n_expected} in C source"
        )

    region_names = _parse_string_array(src, "CHRON_REGION_NAMES")
    faction_names = _parse_string_array(src, "CHRON_FACTION_NAMES")
    lineage_surnames = _parse_string_array(src, "CHRON_LINEAGE_SURNAMES")

    data = {
        "fragments": fragments,
        "name_tables": {
            "region_names": region_names,
            "faction_names": faction_names,
            "lineage_surnames": lineage_surnames,
        },
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Emitted {len(fragments)} fragments to {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_OUT
    main(out)
