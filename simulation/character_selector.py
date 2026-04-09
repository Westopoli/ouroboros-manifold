import config


def select_commander(gen_state, coherence_ledger, world, region_id, rng):
    pool_weights = config.LINEAGE_POOL_WEIGHTS
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

    hop_range = config.NEMESIS_HOP_RANGE
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
        if chapters_ago <= config.LINEAGE_RECENCY_PENALTY_CHAPTERS:
            continue

        # Score: prefer moderate gap (not too recent, not too distant)
        # + bonus for more living descendants nearby
        gap_score = min(chapters_ago, 6) / 6.0
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
        commander_ids, region_id, world, hop_range=config.NEMESIS_HOP_RANGE)

    if not candidates:
        return None

    return rng.choice(candidates)
