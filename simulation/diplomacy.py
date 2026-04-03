import config


def _pair_key(a: str, b: str) -> tuple:
    return tuple(sorted([a, b]))


def init_stances(registry: dict) -> dict:
    stances = {}
    faction_ids = list(registry.keys())
    for i, fid_a in enumerate(faction_ids):
        for fid_b in faction_ids[i + 1:]:
            key = _pair_key(fid_a, fid_b)
            arch_a = registry[fid_a].archetype
            arch_b = registry[fid_b].archetype
            stance = _starting_stance(arch_a, arch_b)
            stances[key] = {
                "stance": stance,
                "non_aggression_ticks": 0,
                "cooperative_since_tick": None,
            }
    sync_to_factions(stances, registry)
    return stances


def _starting_stance(arch_a: str, arch_b: str) -> str:
    overrides = config.STARTING_STANCE_OVERRIDES
    pair = tuple(sorted([arch_a, arch_b]))
    if pair in overrides:
        return overrides[pair]
    if (arch_a, arch_b) in overrides:
        return overrides[(arch_a, arch_b)]
    if (arch_b, arch_a) in overrides:
        return overrides[(arch_b, arch_a)]
    return "neutral"


def get_stance(stances: dict, a: str, b: str) -> str:
    if a == b:
        return "cooperative"
    key = _pair_key(a, b)
    entry = stances.get(key)
    return entry["stance"] if entry else "hostile"


def is_hostile(stances: dict, a: str, b: str) -> bool:
    return get_stance(stances, a, b) == "hostile"


def is_cooperative(stances: dict, a: str, b: str) -> bool:
    return get_stance(stances, a, b) == "cooperative"


def is_neutral(stances: dict, a: str, b: str) -> bool:
    return get_stance(stances, a, b) == "neutral"


def set_stance(stances: dict, a: str, b: str, stance: str,
               tick: int | None = None) -> None:
    key = _pair_key(a, b)
    if key not in stances:
        stances[key] = {"stance": stance, "non_aggression_ticks": 0, "cooperative_since_tick": None}
    stances[key]["stance"] = stance
    stances[key]["non_aggression_ticks"] = 0
    if stance == "cooperative" and tick is not None:
        stances[key]["cooperative_since_tick"] = tick
    elif stance != "cooperative":
        stances[key]["cooperative_since_tick"] = None


def sync_to_factions(stances: dict, registry: dict) -> None:
    for (fid_a, fid_b), entry in stances.items():
        stance = entry["stance"]
        if fid_a in registry:
            registry[fid_a].diplomatic_stance[fid_b] = stance
        if fid_b in registry:
            registry[fid_b].diplomatic_stance[fid_a] = stance
