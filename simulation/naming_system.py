import json
import os
import config


class NamingSystem:
    def __init__(self):
        self._pools = {}        # {(faction_id, category): [name, ...]}
        self._in_use = {}       # {name: faction_id}
        self._cooldowns = {}    # {name: expiry_tick}
        self._subsets = {}      # {faction_id: {linguistic_roots, phoneme_patterns, cultural_flavor_tags}}
        self._schism_parents = {}  # {child_faction_id: parent_faction_id}

    def load_pool(self, faction_id: str, category: str, names: list[str]):
        self._pools[(faction_id, category)] = list(names)

    def load_pools_from_json(self, directory: str):
        for fname in os.listdir(directory):
            if not fname.endswith(".json") or fname == "variable_subsets.json" or fname == "validation_report.json":
                continue
            parts = fname.replace(".json", "").split("_", 1)
            if len(parts) < 2:
                continue
            path = os.path.join(directory, fname)
            with open(path) as f:
                data = json.load(f)
            fid = data.get("faction_id", parts[0])
            cat = data.get("category", parts[1])
            self._pools[(fid, cat)] = list(data.get("names", []))

    def set_variable_subset(self, faction_id: str, subset: dict):
        self._subsets[faction_id] = dict(subset)

    def get_variable_subset(self, faction_id: str) -> dict | None:
        return self._subsets.get(faction_id)

    def ensure_pool(self, faction_id: str, category: str, parent_faction_id: str | None = None):
        key = (faction_id, category)
        if key in self._pools:
            return
        if parent_faction_id:
            parent_pool = self._pools.get((parent_faction_id, category), [])
            if parent_pool:
                self._pools[key] = list(parent_pool)
                return
        self._pools[key] = [f"{faction_id}_name_{i}" for i in range(50)]

    def get_name(self, faction_id: str, category: str, current_tick: int = 0, rng=None) -> str | None:
        key = (faction_id, category)
        pool = self._pools.get(key)
        if not pool:
            self.ensure_pool(faction_id, category)
            pool = self._pools.get(key)
        if not pool:
            return None

        available = [n for n in pool if self._is_available(n, current_tick)]
        if not available:
            return None

        if rng is not None:
            name = rng.choice(available)
        else:
            name = available[0]

        self._in_use[name] = faction_id
        return name

    def release_name(self, name: str, death_tick: int, cooldown_ticks=None):
        self._in_use.pop(name, None)
        self._cooldowns[name] = death_tick + (cooldown_ticks or config.NAME_REUSE_COOLDOWN_TICKS)

    def is_available(self, name: str, current_tick: int = 0) -> bool:
        return self._is_available(name, current_tick)

    def _is_available(self, name: str, current_tick: int) -> bool:
        if name in self._in_use:
            return False
        if name in self._cooldowns:
            return current_tick >= self._cooldowns[name]
        return True

    def derive_schism_subset(self, parent_faction_id: str, child_faction_id: str, rng):
        self._schism_parents[child_faction_id] = parent_faction_id
        parent = self._subsets.get(parent_faction_id)
        if not parent:
            ancestor = parent_faction_id
            visited = {ancestor}
            while ancestor in self._schism_parents:
                ancestor = self._schism_parents[ancestor]
                if ancestor in visited:
                    break
                visited.add(ancestor)
                parent = self._subsets.get(ancestor)
                if parent:
                    break
        if not parent:
            return
        child_subset = {k: list(v) for k, v in parent.items()}
        categories = list(child_subset.keys())
        cat = rng.choice(categories)
        values = child_subset[cat]
        if not values:
            self._subsets[child_faction_id] = child_subset
            return
        idx = rng.randrange(len(values))
        all_values = _ALL_VALUES.get(cat, [])
        alternatives = [v for v in all_values if v not in values]
        if alternatives:
            values[idx] = rng.choice(alternatives)
        self._subsets[child_faction_id] = child_subset

    def pool_size(self, faction_id: str, category: str) -> int:
        return len(self._pools.get((faction_id, category), []))

    def available_count(self, faction_id: str, category: str, current_tick: int = 0) -> int:
        pool = self._pools.get((faction_id, category), [])
        return sum(1 for n in pool if self._is_available(n, current_tick))


_ALL_VALUES = {
    "linguistic_roots": [
        "Semitic triconsonantal", "Polynesian open syllables", "Germanic compound",
        "Sino-monosyllabic", "Tolkien-esque", "ancient Greek", "Sumerian",
        "invented liquid-heavy", "invented guttural-aspirated", "Sanskrit-derived",
        "Bantu agglutinative", "Gaelic consonant-cluster", "Persian flowing",
        "Nahuatl compound", "Japanese mora-based", "Slavic palatalized",
        "Khmer sesquisyllabic", "Quechua suffixing", "Yoruba tonal",
        "Finnish agglutinative", "Georgian consonant-clustered", "Maori CV-open",
        "Tibetan aspirated", "Basque ergative", "Swahili noun-class",
    ],
    "phoneme_patterns": [
        "patronymic", "place-derived", "title-prefix", "two-part compound",
        "single name only", "three-syllable cadence", "consonant-final",
        "vowel-final", "reduplicative", "honorific-suffix", "clan-prefix",
        "syllable-initial stress", "alternating long-short", "nasal-onset",
        "glottal-stop midword",
    ],
    "cultural_flavor_tags": [
        "martial", "pastoral", "mercantile", "priestly", "frontier/rough",
        "imperial/formal", "scholarly", "nomadic", "maritime", "aristocratic",
        "revolutionary", "ancient/archaic", "subterranean", "riverine",
        "artisan/guild", "oracular", "exilic/diaspora", "volcanic/forge",
    ],
}
