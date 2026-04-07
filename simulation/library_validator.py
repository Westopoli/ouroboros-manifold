import re
import config

VALID_SLOTS = {
    "{character_name}", "{character_rank}", "{character_faction}",
    "{lineage_name}", "{faction_name}", "{region_name}", "{adjacent_region}",
    "{event_description}", "{chain_length}", "{duration_ticks}", "{duration_prose}",
    "{field_delta_summary}", "{stability_level}", "{capacity_level}", "{tension_level}",
    "{mission_outcome}", "{mission_archetype}", "{mission_region}",
    "{previous_event_reference}", "{lineage_history_note}",
}

WORD_LIMITS = {"opening": 30, "detail": 60, "closing": 50}

MECHANICAL_PATTERNS = [
    re.compile(r"\b\d+(\.\d+)?\s*%", re.IGNORECASE),
    re.compile(r"(stability|tension|economy|military|population)\s+(dropped|rose|fell|increased|decreased)\s+to\s+\d", re.IGNORECASE),
    re.compile(r"\bstat(s|istic)?\b", re.IGNORECASE),
    re.compile(r"\bhit\s*points?\b", re.IGNORECASE),
    re.compile(r"\bthe player'?s?\s+faction\b", re.IGNORECASE),
    re.compile(r"\bin a dramatic turn of events\b", re.IGNORECASE),
    re.compile(r"\bgame\s*play\b", re.IGNORECASE),
    re.compile(r"\bscore\b", re.IGNORECASE),
    re.compile(r"\blevel\s+\d", re.IGNORECASE),
]

_SLOT_RE = re.compile(r"\{[a-z_]+\}")


def _extract_slots(text):
    return set(_SLOT_RE.findall(text))


def _word_count(text):
    cleaned = _SLOT_RE.sub("SLOT", text)
    return len(cleaned.split())


def _levenshtein(a, b):
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


# ── Layer 1: Structural Validation ──────────────────────────────────────────

def validate_structural(fragments, category_required_slots=None):
    issues = []
    seen_ids = set()

    for frag in fragments:
        fid = frag.get("id", "MISSING_ID")
        text = frag.get("text", "")
        ftype = frag.get("type", "unknown")
        category = frag.get("category", "unknown")

        if fid in seen_ids:
            issues.append({"id": fid, "issue": "duplicate_id", "detail": f"ID {fid} already used"})
        seen_ids.add(fid)

        slots_in_text = _extract_slots(text)
        invalid = slots_in_text - VALID_SLOTS
        if invalid:
            issues.append({"id": fid, "issue": "invalid_slot",
                           "detail": f"Invalid slot(s): {', '.join(sorted(invalid))}"})

        wc = _word_count(text)
        limit = WORD_LIMITS.get(ftype, 60)
        if wc > limit:
            issues.append({"id": fid, "issue": "word_limit_exceeded",
                           "detail": f"{ftype} has {wc} words (limit {limit})"})

        for pat in MECHANICAL_PATTERNS:
            match = pat.search(text)
            if match:
                issues.append({"id": fid, "issue": "mechanical_language",
                               "detail": f"Matched: '{match.group()}'"})
                break

        if category_required_slots and category in category_required_slots:
            required = set(category_required_slots[category])
            missing = required - slots_in_text
            if missing:
                issues.append({"id": fid, "issue": "missing_required_slot",
                               "detail": f"Missing required slot(s): {', '.join(sorted(missing))}"})

    return issues


# ── Layer 2: Deduplication ──────────────────────────────────────────────────

def validate_dedup(fragments, threshold=None):
    if threshold is None:
        threshold = getattr(config, "FRAGMENT_DEDUP_THRESHOLD", 3)

    matches = []
    by_pool = {}
    for frag in fragments:
        key = (frag.get("category", ""), frag.get("type", ""))
        by_pool.setdefault(key, []).append(frag)

    for pool_key, pool in by_pool.items():
        for i in range(len(pool)):
            for j in range(i + 1, len(pool)):
                dist = _levenshtein(pool[i]["text"], pool[j]["text"])
                if dist < threshold:
                    matches.append({
                        "id_a": pool[i].get("id", "?"),
                        "id_b": pool[j].get("id", "?"),
                        "pool": f"{pool_key[0]}/{pool_key[1]}",
                        "distance": dist,
                    })

    openings_by_cat = {}
    for frag in fragments:
        if frag.get("type") == "opening":
            openings_by_cat.setdefault(frag.get("category", ""), []).append(frag)

    cats = list(openings_by_cat.keys())
    for ci in range(len(cats)):
        for cj in range(ci + 1, len(cats)):
            for fa in openings_by_cat[cats[ci]]:
                for fb in openings_by_cat[cats[cj]]:
                    dist = _levenshtein(fa["text"], fb["text"])
                    if dist < threshold:
                        matches.append({
                            "id_a": fa.get("id", "?"),
                            "id_b": fb.get("id", "?"),
                            "pool": f"cross-category opening ({cats[ci]} vs {cats[cj]})",
                            "distance": dist,
                        })

    loss_flag = getattr(config, "BUILDER_DEDUP_LOSS_FLAG", 0.30)
    thin_pools = []
    for pool_key, pool in by_pool.items():
        dupes_in_pool = sum(1 for m in matches if m["pool"] == f"{pool_key[0]}/{pool_key[1]}")
        if len(pool) > 0 and dupes_in_pool / len(pool) > loss_flag:
            thin_pools.append({
                "pool": f"{pool_key[0]}/{pool_key[1]}",
                "total": len(pool),
                "dupes": dupes_in_pool,
                "loss_pct": round(dupes_in_pool / len(pool) * 100, 1),
            })

    return {"matches": matches, "thin_pools": thin_pools}


# ── Layer 3: Tone/Coherence (placeholder — requires AI for full check) ──────

def validate_tone(fragments):
    issues = []
    for frag in fragments:
        text = frag.get("text", "").lower()
        if "in a dramatic turn" in text or "suddenly" in text.split()[0:1]:
            issues.append({"id": frag.get("id", "?"), "issue": "tone_flag",
                           "detail": "Possible tone violation (meta-commentary detected)"})
    return issues


# ── Full Pipeline ───────────────────────────────────────────────────────────

def validate_all(fragments, category_required_slots=None):
    structural = validate_structural(fragments, category_required_slots)
    dedup = validate_dedup(fragments)
    tone = validate_tone(fragments)
    return {
        "structural": structural,
        "dedup": dedup,
        "tone": tone,
        "summary": {
            "total_fragments": len(fragments),
            "structural_failures": len(structural),
            "dedup_matches": len(dedup["matches"]),
            "thin_pools": len(dedup["thin_pools"]),
            "tone_flags": len(tone),
        },
    }
