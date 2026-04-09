import config
import character_selector


class GenerationalState:
    def __init__(self, player_faction_id, start_tick=0):
        self.player_faction_id = player_faction_id
        self.chapters = []
        self.current_chapter_index = 0
        self._start_chapter(player_faction_id, start_tick)

    def _start_chapter(self, faction_id, tick):
        chapter = {
            "chapter_number": len(self.chapters) + 1,
            "faction_id":     faction_id,
            "character_id":   f"character_ch{len(self.chapters) + 1}",
            "start_tick":     tick,
            "end_tick":       None,
            "end_reason":     None,
        }
        self.chapters.append(chapter)
        self.current_chapter_index = len(self.chapters) - 1
        self.player_faction_id = faction_id
        return chapter

    @property
    def current_chapter(self):
        return self.chapters[self.current_chapter_index]

    @property
    def chapter_count(self):
        return len(self.chapters)


def check_player_collapse(state, world, registry):
    if state.player_faction_id not in registry:
        return True
    owned = world.regions_by_faction(state.player_faction_id)
    return len(owned) == 0


def reassign_player(state, world, registry, rng, tick):
    state.current_chapter["end_tick"] = tick
    state.current_chapter["end_reason"] = "faction_collapsed"

    surviving = []
    for fid in registry:
        if fid == state.player_faction_id:
            continue
        count = len(world.regions_by_faction(fid))
        if count > 0:
            surviving.append((fid, count))

    if not surviving:
        return {"type": "game_over", "tick": tick, "reason": "no_surviving_factions"}

    surviving.sort(key=lambda x: -x[1])
    max_count = surviving[0][1]
    candidates = [fid for fid, count in surviving if count == max_count]
    new_faction_id = rng.choice(candidates)

    old_faction = state.player_faction_id
    chapter = state._start_chapter(new_faction_id, tick)

    return {
        "type":            "reassignment",
        "tick":            tick,
        "old_faction":     old_faction,
        "new_faction":     new_faction_id,
        "chapter_number":  chapter["chapter_number"],
        "character_id":    chapter["character_id"],
    }


def should_rotate(state, world, registry, tick):
    chapter = state.current_chapter
    chapters_in_lineage = state.chapter_count

    if chapters_in_lineage >= config.LINEAGE_HARD_CAP:
        return "hard_cap"

    if chapters_in_lineage < config.LINEAGE_MIN_CHAPTERS:
        return False

    fid = state.player_faction_id
    owned = world.regions_by_faction(fid)
    if not owned:
        return False

    avg_tension = sum(r.fields["tension"] for r in owned) / len(owned)
    stability = 100.0 - avg_tension
    if stability < config.CRISIS_VETO_STABILITY:
        return False

    chapter_duration = tick - chapter["start_tick"]
    if chapter_duration < 50:
        return False

    avg_economy = sum(r.fields["economy"] for r in owned) / len(owned)
    avg_military = sum(r.fields["military"] for r in owned) / len(owned)
    regional_delta = abs(avg_economy - 50.0) + abs(avg_military - 50.0)

    if regional_delta < config.LINEAGE_DELTA_LOW:
        return "normal"
    if regional_delta > config.LINEAGE_DELTA_HIGH:
        return False

    t = (regional_delta - config.LINEAGE_DELTA_LOW) / (config.LINEAGE_DELTA_HIGH - config.LINEAGE_DELTA_LOW)
    rotation_prob = 1.0 - t
    if world.rng.random() < rotation_prob * 0.1:
        return "normal"
    return False


def rotate_lineage(state, ledger, world, region_id, rng, tick, reason="rotation"):
    # PHASE 6A PENDING (Stage 5.5): When reason == "hard_cap", the mission generator
    # should run with cross_faction=True BEFORE this function is called, so that
    # region_id already points to the winning mission region (which may belong to any
    # faction). The character selector then picks from that region as normal, and the
    # faction reassignment below handles the cross-faction switch.
    # See: docs/random/bible_spec_reconciliation_plan.md, Phase 6A (line ~303).
    # Currently region_id is always in the player's faction — cross-faction mission
    # selection is deferred until mission_generator.py exists.

    state.current_chapter["end_tick"] = tick
    state.current_chapter["end_reason"] = reason

    result = character_selector.select_commander(state, ledger, world, region_id, rng)
    if not result:
        return {"type": "rotation_failed", "reason": "no_candidates_anywhere"}

    old_faction = state.player_faction_id
    new_faction = result["faction_id"]

    new_chapter = state._start_chapter(new_faction, tick)
    new_chapter["character_id"] = result["character_id"]

    rotation_result = {
        "type": "rotation",
        "reason": reason,
        "tick": tick,
        "old_faction": old_faction,
        "new_faction": new_faction,
        "new_character_id": result["character_id"],
        "new_lineage_id": result["lineage_id"],
        "pool_used": result["pool_used"],
        "pool_rolled": result["pool_rolled"],
        "chapter_number": new_chapter["chapter_number"],
        "cross_faction": old_faction != new_faction,
    }

    return rotation_result


def handle_commander_death(state, ledger, world, region_id, rng, tick):
    chapter = state.current_chapter
    char_id = chapter.get("character_id")
    if not char_id:
        return {"type": "no_op", "reason": "no_character_in_chapter"}

    rec = ledger.get_character_by_id(char_id)
    if not rec:
        return {"type": "no_op", "reason": "character_not_found"}

    if rec.status == "active":
        return {"type": "no_op", "reason": "commander_alive"}

    lineage_id = rec.lineage_id
    chapters_in_lineage = _count_lineage_chapters(state, ledger, lineage_id)
    below_minimum = chapters_in_lineage < config.LINEAGE_MIN_CHAPTERS

    successor = _find_lineage_successor(ledger, world, lineage_id, region_id,
                                        global_search=below_minimum)
    if successor:
        successor.rank = "supreme_commander"
        chapter["character_id"] = successor.id
        return {
            "type": "succession",
            "successor_id": successor.id,
            "successor_name": successor.name,
            "lineage_id": lineage_id,
            "dead_commander_id": char_id,
            "dead_commander_name": rec.name,
            "search_scope": "global" if below_minimum else "nearby",
        }

    # No successor found — force rotation
    rot = rotate_lineage(state, ledger, world, region_id, rng, tick, reason="commander_death")
    if rot["type"] == "rotation":
        rot["death_reason"] = "bloodline_extinct" if below_minimum else "no_nearby_heir"
    return rot


def _count_lineage_chapters(state, ledger, lineage_id):
    count = 0
    for ch in state.chapters:
        ch_char = ledger.get_character_by_id(ch.get("character_id"))
        if ch_char and ch_char.lineage_id == lineage_id:
            count += 1
    return count


def _find_lineage_successor(ledger, world, lineage_id, region_id, global_search=False):
    if not lineage_id:
        return None
    members = ledger.get_lineage_members(lineage_id)
    living = [m for m in members if m.status == "active"
              and m.rank != "supreme_commander"]
    if not living:
        return None

    # (a) Living members in the mission region
    local = [m for m in living if m.region_id == region_id]
    if local:
        return local[0]

    # (b) Living members in adjacent regions
    adjacent_rids = set(world.get_neighbors(region_id))
    adjacent = [m for m in living if m.region_id in adjacent_rids]
    if adjacent:
        return adjacent[0]

    # (c) Global search — only if below minimum chapter count
    if global_search and living:
        return living[0]

    return None
