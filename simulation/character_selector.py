import config
from mission_contracts import CommanderSelection

# PHASE 6A PENDING (Stage 5.5): This module does NOT need changes for cross-faction
# rotation. The mission generator is responsible for selecting the mission region
# (which may belong to any faction when cross_faction=True at hard cap). This module
# receives that region_id and selects a character from it — faction falls out naturally.
# See: generational.rotate_lineage() and docs/random/bible_spec_reconciliation_plan.md Phase 6.


def run_selection(gen_state, ledger, world, region_id, rng, tick,
                  current_lineage_id=None, region_field_delta=0.0):
    """
    Full rotation decision + commander selection. Priority cascade:
      1. Forced rotation (bloodline extinct / KIA with no successor)
      2. Minimum stay (chapter_counter < SELECTOR_MIN_CHAPTERS)
      3. Hard cap (chapter_counter >= SELECTOR_HARD_CAP)
      4. Delta-based probability + crisis veto
    Returns CommanderSelection.
    """
    chapter = gen_state.current_chapter
    chapter_number = gen_state.chapter_count
    char_id = chapter.get("character_id")
    rec = ledger.get_character_by_id(char_id) if char_id else None
    lineage_id = current_lineage_id or (rec.lineage_id if rec else None)

    # ── Step 1: Forced rotation ──────────────────────────────────────────────
    forced_rotate = False
    if lineage_id:
        members = ledger.get_lineage_members(lineage_id)
        living = [m for m in members if m.status == "active"]
        if not living:
            forced_rotate = True
    if not forced_rotate and rec and rec.status != "active":
        # Commander dead — check for successor near mission region
        successor = _find_lineage_successor_near(ledger, world, lineage_id, region_id)
        if not successor:
            forced_rotate = True
        else:
            # Successor found via deterministic bloodline lookup — no pool roll
            return CommanderSelection(
                character_id=successor.id,
                character_name=successor.name,
                lineage_id=lineage_id,
                faction_id=successor.faction_id,
                region_id=successor.region_id,
                chapter_number=chapter_number,
                pool_used=None,
                pool_rolled=None,
                rotation_reason="commander_death",
                rotation_mechanism="bloodline_succession",
            )

    if forced_rotate:
        return _do_rotate(gen_state, ledger, world, region_id, rng, tick,
                          chapter_number, reason="forced")

    # ── Step 2: Minimum stay ─────────────────────────────────────────────────
    chapters_in_lineage = ledger.get_chapter_count(lineage_id) if lineage_id else 0
    if chapters_in_lineage < config.SELECTOR_MIN_CHAPTERS:
        return _stay(rec, lineage_id, region_id, ledger, world, chapter_number)

    # ── Step 3: Hard cap ────────────────────────────────────────────────────
    if chapters_in_lineage >= config.SELECTOR_HARD_CAP:
        return _do_rotate(gen_state, ledger, world, region_id, rng, tick,
                          chapter_number, reason="hard_cap")

    # ── Step 4: Delta-based probability + crisis veto ────────────────────────
    t = min(1.0, region_field_delta / config.SELECTOR_DELTA_SAFE)
    rotation_prob = (config.SELECTOR_MAX_ROTATION_PROB +
                     t * (config.SELECTOR_MIN_ROTATION_PROB - config.SELECTOR_MAX_ROTATION_PROB))
    if rng.random() < rotation_prob:
        # Crisis veto: don't rotate if home region is in crisis
        home_region = _lineage_home_region(ledger, world, lineage_id)
        if home_region:
            stab = home_region.composites.get("stability", 100 - home_region.fields.get("tension", 0))
            if stab < config.SELECTOR_CRISIS_THRESHOLD:
                return _stay(rec, lineage_id, region_id, ledger, world, chapter_number)
        return _do_rotate(gen_state, ledger, world, region_id, rng, tick,
                          chapter_number, reason="normal")

    return _stay(rec, lineage_id, region_id, ledger, world, chapter_number)


def _stay(rec, lineage_id, region_id, ledger, world, chapter_number):
    # Find best available commander from current lineage near mission region
    if lineage_id:
        nearby = _nearby_region_ids(world, region_id, config.SELECTOR_PROXIMITY_HOPS)
        members = ledger.get_lineage_members(lineage_id)
        local = [m for m in members if m.status == "active" and m.region_id in nearby]
        if local:
            best = local[0]
            return CommanderSelection(
                character_id=best.id,
                character_name=best.name,
                lineage_id=lineage_id,
                faction_id=best.faction_id,
                region_id=best.region_id,
                chapter_number=chapter_number,
                pool_used=None,
                pool_rolled=None,
                rotation_reason=None,
                rotation_mechanism=None,
            )
    if rec and rec.status == "active":
        return CommanderSelection(
            character_id=rec.id,
            character_name=rec.name,
            lineage_id=lineage_id,
            faction_id=rec.faction_id,
            region_id=rec.region_id,
            chapter_number=chapter_number,
            pool_used=None,
            pool_rolled=None,
            rotation_reason=None,
            rotation_mechanism=None,
        )
    return None


def _do_rotate(gen_state, ledger, world, region_id, rng, tick,
               chapter_number, reason):
    raw = select_commander(gen_state, ledger, world, region_id, rng)
    if not raw:
        return None
    char = ledger.get_character_by_id(raw["character_id"])
    return CommanderSelection(
        character_id=raw["character_id"],
        character_name=char.name if char else raw["character_id"],
        lineage_id=raw["lineage_id"],
        faction_id=raw["faction_id"],
        region_id=raw["region_id"],
        chapter_number=chapter_number + 1,
        pool_used=raw["pool_used"],
        pool_rolled=raw["pool_rolled"],
        rotation_reason=reason,
        rotation_mechanism="pool_roll",
    )


def _find_lineage_successor_near(ledger, world, lineage_id, region_id):
    if not lineage_id:
        return None
    members = ledger.get_lineage_members(lineage_id)
    living = [m for m in members if m.status == "active" and m.rank != "supreme_commander"]
    if not living:
        return None
    nearby = _nearby_region_ids(world, region_id, config.SELECTOR_PROXIMITY_HOPS)
    local = [m for m in living if m.region_id in nearby]
    return local[0] if local else living[0]


def _lineage_home_region(ledger, world, lineage_id):
    if not lineage_id:
        return None
    history = ledger.get_lineage_history(lineage_id)
    if not history:
        return None
    return world.regions.get(history[0])


def select_commander(gen_state, coherence_ledger, world, region_id, rng):
    pool_weights = {
        "previous_descendant": config.SELECTOR_POOL_PREVIOUS_WEIGHT,
        "nemesis_descendant":  config.SELECTOR_POOL_NEMESIS_WEIGHT,
        "unrelated":           config.SELECTOR_POOL_UNRELATED_WEIGHT,
    }
    pools = list(pool_weights.keys())
    weights = [pool_weights[p] for p in pools]

    roll = rng.random()
    cumulative = 0.0
    selected_pool = pools[-1]
    for pool, weight in zip(pools, weights):
        cumulative += weight
        if roll < cumulative:
            selected_pool = pool
            break

    # Build ordered fallthrough: selected pool first, then others in priority order
    priority_order = ["previous_descendant", "nemesis_descendant", "unrelated"]
    search_order = [selected_pool] + [p for p in priority_order if p != selected_pool]

    previous_lineage_ids = _get_previous_lineage_ids(gen_state, coherence_ledger)
    commander_ids = _get_previous_commander_ids(gen_state, coherence_ledger)

    for pool in search_order:
        if pool == "previous_descendant":
            candidate = _select_from_previous(
                previous_lineage_ids, gen_state, coherence_ledger,
                world, region_id, rng)
            if candidate:
                return {
                    "character_id": candidate.id,
                    "lineage_id": candidate.lineage_id,
                    "faction_id": candidate.faction_id,
                    "region_id": candidate.region_id,
                    "pool_used": "previous_descendant",
                    "pool_rolled": selected_pool,
                }

        elif pool == "nemesis_descendant":
            candidate = _select_from_nemesis(
                commander_ids, coherence_ledger, world, region_id, rng)
            if candidate:
                return {
                    "character_id": candidate.id,
                    "lineage_id": candidate.lineage_id,
                    "faction_id": candidate.faction_id,
                    "region_id": candidate.region_id,
                    "pool_used": "nemesis_descendant",
                    "pool_rolled": selected_pool,
                }

        elif pool == "unrelated":
            candidate = coherence_ledger.create_character(
                world.regions[region_id].faction_id, region_id,
                "lineage_member", 0, rng)
            if candidate:
                lineage_id = coherence_ledger.create_lineage(candidate.id)
                return {
                    "character_id": candidate.id,
                    "lineage_id": lineage_id,
                    "faction_id": candidate.faction_id,
                    "region_id": candidate.region_id,
                    "pool_used": "unrelated",
                    "pool_rolled": selected_pool,
                }

    return None


def _get_previous_lineage_ids(gen_state, coherence_ledger):
    lineage_ids = set()
    for chapter in gen_state.chapters:
        char_id = chapter.get("character_id")
        if char_id:
            rec = coherence_ledger.get_character_by_id(char_id)
            if rec and rec.lineage_id:
                lineage_ids.add(rec.lineage_id)
    return list(lineage_ids)


def _get_previous_commander_ids(gen_state, coherence_ledger):
    ids = []
    for chapter in gen_state.chapters:
        char_id = chapter.get("character_id")
        if char_id and coherence_ledger.get_character_by_id(char_id):
            ids.append(char_id)
    return ids


def _nearby_region_ids(world, region_id, hop_range):
    nearby = {region_id}
    frontier = [region_id]
    for _ in range(hop_range):
        next_frontier = []
        for rid in frontier:
            for nid in world.get_neighbors(rid):
                if nid not in nearby:
                    nearby.add(nid)
                    next_frontier.append(nid)
        frontier = next_frontier
    return nearby


def _select_from_previous(lineage_ids, gen_state, coherence_ledger,
                          world, region_id, rng):
    if not lineage_ids:
        return None

    hop_range = config.SELECTOR_PROXIMITY_HOPS
    nearby = _nearby_region_ids(world, region_id, hop_range)
    current_chapter_num = gen_state.chapter_count

    scored_candidates = []
    for lid in lineage_ids:
        members = coherence_ledger.get_lineage_members(lid)
        nearby_living = [m for m in members
                         if m.status == "active" and m.region_id in nearby]
        if not nearby_living:
            continue

        # Find the most recent chapter this lineage was played
        last_chapter = 0
        for i, ch in enumerate(gen_state.chapters):
            ch_char = coherence_ledger.get_character_by_id(ch.get("character_id"))
            if ch_char and ch_char.lineage_id == lid:
                last_chapter = i + 1

        chapters_ago = current_chapter_num - last_chapter

        # Recency penalty: don't immediately return to a lineage just left
        if chapters_ago < config.SELECTOR_RECENCY_PENALTY_WINDOW:
            continue

        # Score: gap bonus peaks at SELECTOR_GAP_BONUS_PEAK chapters ago
        # + bonus for more living descendants nearby
        gap_score = min(chapters_ago, config.SELECTOR_GAP_BONUS_PEAK) / config.SELECTOR_GAP_BONUS_PEAK
        density_score = min(len(nearby_living), 5) / 5.0
        score = gap_score * 0.6 + density_score * 0.4

        for member in nearby_living:
            scored_candidates.append((member, score))

    if not scored_candidates:
        return None

    # Weighted random draw
    total = sum(s for _, s in scored_candidates)
    if total <= 0:
        return rng.choice([c for c, _ in scored_candidates])

    roll = rng.random() * total
    cumulative = 0.0
    for candidate, score in scored_candidates:
        cumulative += score
        if roll < cumulative:
            return candidate
    return scored_candidates[-1][0]


def _select_from_nemesis(commander_ids, coherence_ledger, world, region_id, rng):
    if not commander_ids:
        return None

    candidates = coherence_ledger.get_nemesis_descendants_in_region(
        commander_ids, region_id, world, hop_range=config.SELECTOR_PROXIMITY_HOPS)

    if not candidates:
        return None

    return rng.choice(candidates)
