from collections import defaultdict, deque


class OwnershipHistory:
    def __init__(self, max_jumps: int = 5) -> None:
        self._max_jumps = max_jumps
        self._owner_chain: dict[str, list[str]] = {}
        self._current_owner: dict[str, str] = {}
        self._region_count_history: dict[str, deque] = {}
        self._known_factions: set[str] = set()
        self._current_counts: dict[str, int] = {}

    def observe_keyframe(self, keyframe: dict) -> None:
        snap = keyframe.get("regions_snapshot", [])
        for r in snap:
            rid = r["region_id"]
            new_owner = r.get("owner_faction_id", "") or ""
            chain = self._owner_chain.setdefault(rid, [])
            if not chain or chain[-1] != new_owner:
                chain.append(new_owner)
            self._current_owner[rid] = new_owner
            if new_owner:
                self._known_factions.add(new_owner)

    def end_jump(self) -> None:
        counts: dict[str, int] = defaultdict(int)
        for owner in self._current_owner.values():
            if owner:
                counts[owner] += 1
        for fid in self._known_factions:
            hist = self._region_count_history.setdefault(
                fid, deque(maxlen=self._max_jumps)
            )
            hist.append(counts.get(fid, 0))
        self._current_counts = dict(counts)

    def owner_chain(self, region_id: str) -> list[str]:
        return list(self._owner_chain.get(region_id, []))

    def current_owner(self, region_id: str) -> str:
        return self._current_owner.get(region_id, "")

    def previous_owners(self, region_id: str) -> list[str]:
        chain = self._owner_chain.get(region_id, [])
        if not chain:
            return []
        return list(chain[:-1])

    def region_count_history(self, faction_id: str) -> list[int]:
        hist = self._region_count_history.get(faction_id)
        return list(hist) if hist is not None else []

    def region_count_delta(self, faction_id: str) -> int:
        hist = self._region_count_history.get(faction_id)
        if hist is None or len(hist) < 2:
            return 0
        return hist[-1] - hist[-2]

    def status(self, faction_id: str) -> str:
        cur = self._current_counts.get(faction_id, 0)
        if cur == 0:
            return "Defeated"
        delta = self.region_count_delta(faction_id)
        if delta > 0:
            return "Rising"
        if delta < 0:
            return "Waning"
        return "Stable"
