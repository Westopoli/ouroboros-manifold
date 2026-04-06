import config


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
        return True

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
        return True
    if regional_delta > config.LINEAGE_DELTA_HIGH:
        return False

    t = (regional_delta - config.LINEAGE_DELTA_LOW) / (config.LINEAGE_DELTA_HIGH - config.LINEAGE_DELTA_LOW)
    rotation_prob = 1.0 - t
    return world.rng.random() < rotation_prob * 0.1
