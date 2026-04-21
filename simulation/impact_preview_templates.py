import config

FIELD_TEMPLATES = {
    "military": {
        ("up", "large"):    "Your victory significantly bolstered the region's military capabilities.",
        ("up", "moderate"): "Your defense stabilized the region's military position.",
        ("up", "small"):    "The region's military recovered slightly.",
        ("down", "large"):  "The region's military was devastated by the engagement.",
        ("down", "moderate"): "Military strength in the region took a notable hit.",
        ("down", "small"):  "Minor military losses were sustained.",
        ("stable", "none"): None,
    },
    "tension": {
        ("up", "large"):    "Regional tensions surged — the population is on edge.",
        ("up", "moderate"): "Tensions rose noticeably in the aftermath.",
        ("up", "small"):    "A slight uptick in regional tension.",
        ("down", "large"):  "The decisive outcome crushed regional unrest.",
        ("down", "moderate"): "Tensions in the region eased.",
        ("down", "small"):  "A marginal calming effect on the region.",
        ("stable", "none"): None,
    },
    "economy": {
        ("up", "large"):    "The region's economy surged — trade routes restored, infrastructure intact.",
        ("up", "moderate"): "Economic recovery gained momentum in the region.",
        ("up", "small"):    "A small economic uptick followed the engagement.",
        ("down", "large"):  "The region's economy was gutted — infrastructure destroyed, trade collapsed.",
        ("down", "moderate"): "Significant economic disruption followed the fighting.",
        ("down", "small"):  "Minor economic disruption from the engagement.",
        ("stable", "none"): None,
    },
    "population": {
        ("up", "large"):    "Refugees returned — the population stabilized.",
        ("up", "moderate"): "Population began recovering as conditions improved.",
        ("up", "small"):    "A slight population recovery.",
        ("down", "large"):  "Massive civilian displacement — the region is emptying out.",
        ("down", "moderate"): "Population declined as civilians fled the fighting.",
        ("down", "small"):  "Some population displacement occurred.",
        ("stable", "none"): None,
    },
}

FORWARD_LOOK_TEMPLATES = {
    ("military", "up", "tension_down"):
        "The eased tensions may discourage further aggression along this border.",
    ("military", "up", "tension_up"):
        "But rising tensions suggest this reprieve won't last.",
    ("military", "up", "economy_down"):
        "But the economic disruption could attract opportunists if the region doesn't recover quickly.",
    ("military", "up", "economy_up"):
        "Combined with economic recovery, this region is in a strong position going forward.",
    ("military", "down", "tension_up"):
        "The weakened garrison and rising unrest could invite further attacks — or internal fractures.",
    ("military", "down", "tension_down"):
        "At least the population isn't restless — but the garrison needs time to rebuild.",
    ("military", "down", "economy_down"):
        "Military and economic damage together make this region vulnerable to the next crisis.",
    ("economy", "down", "military_stable"):
        "The economic damage may compound over time if the region's trade routes aren't restored.",
    ("economy", "down", "tension_up"):
        "Economic hardship and rising tension are a dangerous combination.",
    ("economy", "up", "tension_down"):
        "Economic growth and calming tensions — this region should stabilize on its own.",
    ("tension", "up", "military_down"):
        "Rising tension with a weakened garrison — exactly the conditions that spawn revolts.",
    ("tension", "up", "military_up"):
        "Military strength may keep the lid on, but the underlying pressure is building.",
    ("tension", "down", "economy_down"):
        "The calm may not hold if economic conditions continue to deteriorate.",
    ("tension", "down", "military_up"):
        "A strong garrison and low tension — this border is secure for now.",
    ("population", "down", "economy_down"):
        "Population flight combined with economic collapse could take generations to reverse.",
    ("population", "down", "tension_up"):
        "Displaced populations fuel grievances — expect instability.",
    ("economy", "up", "military_up"):
        "A strengthened position on all fronts. This region may become a staging ground.",
    ("tension", "down", "economy_up"):
        "Stability and prosperity — the best outcome a commander can hope for.",
    ("military", "down", "population_down"):
        "Losses on every front. This region will need significant investment to recover.",
}

MAGNITUDE_THRESHOLDS = {
    "large": 8.0,
    "moderate": 3.0,
}


def _classify_delta(raw_delta):
    abs_d = abs(raw_delta)
    if abs_d < 0.01:
        return "stable", "none"
    direction = "up" if raw_delta > 0 else "down"
    if abs_d >= MAGNITUDE_THRESHOLDS["large"]:
        magnitude = "large"
    elif abs_d >= MAGNITUDE_THRESHOLDS["moderate"]:
        magnitude = "moderate"
    else:
        magnitude = "small"
    return direction, magnitude


def _build_field_deltas(raw_deltas):
    result = {}
    for field_name, raw in raw_deltas.items():
        direction, magnitude = _classify_delta(raw)
        templates = FIELD_TEMPLATES.get(field_name, {})
        prose = templates.get((direction, magnitude))
        result[field_name] = {
            "raw": round(raw, 2),
            "direction": direction,
            "magnitude": magnitude,
            "prose": prose or "",
        }
    return result


def _find_forward_look(field_deltas):
    ranked = sorted(
        [(f, d) for f, d in field_deltas.items() if d["magnitude"] != "none"],
        key=lambda x: abs(x[1]["raw"]),
        reverse=True,
    )
    if not ranked:
        return None

    dominant_field, dominant_data = ranked[0]
    dominant_dir = dominant_data["direction"]

    for secondary_field, secondary_data in field_deltas.items():
        if secondary_field == dominant_field:
            continue
        sec_dir = secondary_data["direction"]
        if secondary_data["magnitude"] == "none":
            sec_key = f"{secondary_field}_stable"
        else:
            sec_key = f"{secondary_field}_{sec_dir}"

        key = (dominant_field, dominant_dir, sec_key)
        if key in FORWARD_LOOK_TEMPLATES:
            return FORWARD_LOOK_TEMPLATES[key]

    return None


def build_impact_preview(raw_deltas):
    field_deltas = _build_field_deltas(raw_deltas)

    sentences = []
    ranked = sorted(
        [(f, d) for f, d in field_deltas.items() if d["prose"]],
        key=lambda x: abs(x[1]["raw"]),
        reverse=True,
    )
    for field_name, data in ranked[:2]:
        sentences.append(data["prose"])

    forward = _find_forward_look(field_deltas)
    if forward and len(sentences) < config.IMPACT_PREVIEW_MAX_SENTENCES:
        sentences.append(forward)

    return field_deltas, " ".join(sentences) if sentences else "No significant regional impact."
