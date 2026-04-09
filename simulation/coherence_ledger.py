import config

RANKS = ("supreme_commander", "regional_commander", "garrison_officer", "lineage_member")


class CharacterRecord:
    __slots__ = ("id", "name", "faction_id", "region_id", "rank",
                 "born_tick", "death_tick", "lifespan_ticks", "lineage_id",
                 "status", "event_history", "parent_id", "children_ids",
                 "generation", "rival_of")

    def __init__(self, char_id, name, faction_id, region_id, rank,
                 born_tick, lifespan_ticks, lineage_id=None, parent_id=None,
                 generation=0):
        self.id = char_id
        self.name = name
        self.faction_id = faction_id
        self.region_id = region_id
        self.rank = rank
        self.born_tick = born_tick
        self.death_tick = None
        self.lifespan_ticks = lifespan_ticks
        self.lineage_id = lineage_id
        self.status = "active"
        self.event_history = []
        self.parent_id = parent_id
        self.children_ids = []
        self.generation = generation
        self.rival_of = []


class CoherenceLedger:
    def __init__(self, naming_system):
        self._naming = naming_system
        self._characters = {}   # {char_id: CharacterRecord}
        self._lineages = {}     # {lineage_id: {"root_id": str, "member_ids": [str]}}
        self._next_char_id = 0
        self._next_lineage_id = 0

    def _gen_char_id(self):
        self._next_char_id += 1
        return f"char_{self._next_char_id}"

    def _gen_lineage_id(self):
        self._next_lineage_id += 1
        return f"lineage_{self._next_lineage_id}"

    def create_character(self, faction_id, region_id, rank, tick, rng,
                         lineage_id=None, parent_id=None, generation=0) -> CharacterRecord | None:
        name = self._naming.get_name(faction_id, "people", current_tick=tick, rng=rng)
        if name is None:
            return None
        char_id = self._gen_char_id()
        lifespan = rng.randint(config.LIFESPAN_MIN, config.LIFESPAN_MAX)
        rec = CharacterRecord(
            char_id, name, faction_id, region_id, rank,
            born_tick=tick, lifespan_ticks=lifespan, lineage_id=lineage_id,
            parent_id=parent_id, generation=generation,
        )
        self._characters[char_id] = rec
        if parent_id and parent_id in self._characters:
            self._characters[parent_id].children_ids.append(char_id)
        if lineage_id and lineage_id in self._lineages:
            self._lineages[lineage_id]["member_ids"].append(char_id)
        return rec

    def kill_character(self, char_id, tick, world=None, rng=None):
        rec = self._characters.get(char_id)
        if rec is None or rec.status == "historical":
            return
        rec.status = "historical"
        rec.death_tick = tick
        self._naming.release_name(rec.name, tick)
        if world and rng and rec.rank in ("supreme_commander", "regional_commander"):
            self._succeed(rec, tick, world, rng)

    def _succeed(self, dead_rec, tick, world, rng):
        faction_regions = world.regions_by_faction(dead_rec.faction_id)
        if not faction_regions:
            return
        if dead_rec.rank == "supreme_commander":
            self.create_character(
                dead_rec.faction_id, faction_regions[0].id,
                "supreme_commander", tick, rng)
        elif dead_rec.rank == "regional_commander":
            region = world.regions.get(dead_rec.region_id)
            if region and region.faction_id == dead_rec.faction_id:
                self.create_character(
                    dead_rec.faction_id, dead_rec.region_id,
                    "regional_commander", tick, rng)

    def create_lineage(self, root_character_id) -> str:
        lineage_id = self._gen_lineage_id()
        self._lineages[lineage_id] = {
            "root_id": root_character_id,
            "member_ids": [root_character_id],
        }
        rec = self._characters.get(root_character_id)
        if rec:
            rec.lineage_id = lineage_id
        return lineage_id

    def assign_faction_leader(self, faction_id, region_id, tick, rng,
                              parent_faction_id=None) -> CharacterRecord | None:
        if parent_faction_id:
            self._naming.ensure_pool(faction_id, "people", parent_faction_id)
            self._naming.ensure_pool(faction_id, "places", parent_faction_id)
            self._naming.ensure_pool(faction_id, "factions", parent_faction_id)
        return self.create_character(faction_id, region_id, "supreme_commander", tick, rng)

    def get_faction_name(self, faction_id, tick, rng):
        return self._naming.get_name(faction_id, "factions", current_tick=tick, rng=rng)

    def derive_schism_subset(self, parent_faction_id, child_faction_id, rng):
        self._naming.derive_schism_subset(parent_faction_id, child_faction_id, rng)

    def assign_regional_commander(self, faction_id, region_id, tick, rng) -> CharacterRecord | None:
        return self.create_character(faction_id, region_id, "regional_commander", tick, rng)

    def attach_event(self, event_log_entry, region_id, tick):
        # Default tier 3 until significance tiers are added to templates (Step I)
        tier = event_log_entry.get("significance_tier", 3)
        if tier < config.CHARACTER_ATTACHMENT_TIER_THRESHOLD:
            return None
        chars = self.get_characters_in_region(region_id)
        if not chars:
            return None
        rank_priority = {r: i for i, r in enumerate(RANKS)}
        chars.sort(key=lambda c: rank_priority.get(c.rank, 99))
        best = chars[0]
        event_log_entry["character_id"] = best.id
        event_log_entry["character_name"] = best.name
        best.event_history.append(event_log_entry.get("template_id", "unknown"))
        return best

    def generate_lineage_members(self, lineage_id, jump_duration, world, tick, rng):
        lin = self._lineages.get(lineage_id)
        if lin is None:
            return []

        living_members = [self._characters[cid] for cid in lin["member_ids"]
                          if self._characters[cid].status == "active"]
        if not living_members:
            return []

        n_descendants = max(1, int(len(living_members) * config.LINEAGE_FERTILITY_RATE * jump_duration))
        new_members = []
        for _ in range(n_descendants):
            parent = rng.choice(living_members)
            if rng.random() < config.LINEAGE_SPREAD_PROBABILITY and world:
                neighbors = world.get_neighbors(parent.region_id)
                inhabited = [nid for nid in neighbors
                             if nid in world.regions and world.regions[nid].tier != "empty"]
                region_id = rng.choice(inhabited) if inhabited else parent.region_id
            else:
                region_id = parent.region_id

            child = self.create_character(
                parent.faction_id, region_id, "lineage_member", tick, rng,
                lineage_id=lineage_id, parent_id=parent.id,
                generation=parent.generation + 1,
            )
            if child:
                new_members.append(child)
        return new_members

    def process_natural_deaths(self, tick, rng, world=None):
        deaths = []
        for rec in list(self._characters.values()):
            if rec.status != "active":
                continue
            age = tick - rec.born_tick
            if age >= rec.lifespan_ticks:
                self.kill_character(rec.id, tick, world=world, rng=rng)
                deaths.append(rec)
        return deaths

    # ── Queries ──────────────────────────────────────────────────────────────

    def get_character_by_id(self, char_id) -> CharacterRecord | None:
        return self._characters.get(char_id)

    def get_characters_in_region(self, region_id) -> list[CharacterRecord]:
        return [c for c in self._characters.values()
                if c.region_id == region_id and c.status == "active"]

    def get_lineage_members(self, lineage_id) -> list[CharacterRecord]:
        lin = self._lineages.get(lineage_id)
        if not lin:
            return []
        return [self._characters[cid] for cid in lin["member_ids"]
                if cid in self._characters]

    def get_lineage_history(self, lineage_id) -> list[str]:
        members = self.get_lineage_members(lineage_id)
        regions = []
        seen = set()
        for m in members:
            if m.region_id not in seen:
                regions.append(m.region_id)
                seen.add(m.region_id)
        return regions

    def lineage_in_region(self, lineage_id, region_id) -> bool:
        lin = self._lineages.get(lineage_id)
        if not lin:
            return False
        return any(self._characters[cid].region_id == region_id
                   and self._characters[cid].status == "active"
                   for cid in lin["member_ids"]
                   if cid in self._characters)

    def get_faction_leader(self, faction_id) -> CharacterRecord | None:
        for c in self._characters.values():
            if (c.faction_id == faction_id and c.rank == "supreme_commander"
                    and c.status == "active"):
                return c
        return None

    def active_character_count(self) -> int:
        return sum(1 for c in self._characters.values() if c.status == "active")

    def historical_character_count(self) -> int:
        return sum(1 for c in self._characters.values() if c.status == "historical")

    def total_event_attachments(self) -> int:
        return sum(len(c.event_history) for c in self._characters.values())

    # ── Nemesis detection (Phase 3) ─────────────────────────────────────────

    def tag_rivals(self, region_id: str, commander_id: str,
                   commander_faction_id: str) -> list[CharacterRecord]:
        tagged = []
        for c in self._characters.values():
            if (c.region_id == region_id and c.status == "active"
                    and c.faction_id != commander_faction_id
                    and commander_id not in c.rival_of):
                c.rival_of.append(commander_id)
                tagged.append(c)
        return tagged

    def get_nemesis_candidates(self, commander_ids: list[str]) -> list[CharacterRecord]:
        if not commander_ids:
            return []
        cmd_set = set(commander_ids)
        rivals = []
        for c in self._characters.values():
            if cmd_set.intersection(c.rival_of):
                rivals.append(c)
        return rivals

    def _get_descendants(self, char_id: str) -> list[CharacterRecord]:
        descendants = []
        stack = [char_id]
        while stack:
            cid = stack.pop()
            rec = self._characters.get(cid)
            if rec is None:
                continue
            for child_id in rec.children_ids:
                child = self._characters.get(child_id)
                if child:
                    descendants.append(child)
                    stack.append(child_id)
        return descendants

    def get_nemesis_descendants_in_region(self, commander_ids: list[str],
                                          region_id: str, world,
                                          hop_range: int = 2) -> list[CharacterRecord]:
        nemeses = self.get_nemesis_candidates(commander_ids)
        if not nemeses:
            return []

        nearby_rids = {region_id}
        frontier = [region_id]
        for _ in range(hop_range):
            next_frontier = []
            for rid in frontier:
                for nid in world.get_neighbors(rid):
                    if nid not in nearby_rids:
                        nearby_rids.add(nid)
                        next_frontier.append(nid)
            frontier = next_frontier

        candidates = []
        seen = set()
        for nem in nemeses:
            for desc in self._get_descendants(nem.id):
                if (desc.status == "active" and desc.region_id in nearby_rids
                        and desc.id not in seen):
                    seen.add(desc.id)
                    candidates.append(desc)
            # The nemesis character itself is also a candidate if alive and nearby
            if (nem.status == "active" and nem.region_id in nearby_rids
                    and nem.id not in seen):
                seen.add(nem.id)
                candidates.append(nem)
        return candidates

    # ── Inheritance detection (Phase 7B) ───────────────────────────────────

    def check_inheritance_connection(self, lineage_ids, region_id) -> dict | None:
        # PHASE 7B PENDING (Stage 5.5): The mission generator calls this after
        # selecting a (region, archetype) pair to check if a previous lineage
        # commander operated in this region. If so, it sets inheritance_flag on
        # MissionSetup.metadata. See: docs/random/bible_spec_reconciliation_plan.md Phase 7B.
        for lid in lineage_ids:
            members = self.get_lineage_members(lid)
            for m in members:
                if m.region_id == region_id and m.rank in ("supreme_commander", "regional_commander"):
                    return {
                        "lineage_id": lid,
                        "ancestor_id": m.id,
                        "ancestor_name": m.name,
                        "ancestor_rank": m.rank,
                    }
        return None
