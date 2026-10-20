# Rule pins: R-005-12@a41d16, R-027-06@114581, R-055-01@15c0d9, R-055-02@c048d6, R-057-01@538237, R-057-02@8127b9, R-057-03@c9addd, R-057-04@943db2, R-061-01@4ce2c8, R-061-02@5f1239, R-061-03@8aa36f, R-061-04@b20c60, R-064-04@4638fc, R-065-01@5b085b, R-065-02@64cb68, R-065-03@ad852a, R-065-04@3d7ae5, R-065-05@3dd1e8, R-066-01@dc0b4a, R-066-02@55ece5, R-066-05@2ac99f, R-068-01@e63ace, R-068-04@85572a, R-068-06@8fbc8f, R-068-07@66b1c6, R-068-08@ea4e6c, R-070-01@6a9fcc, R-075-02@dbbd64, R-075-06@05a87b, R-075-07@ca6ea3, R-076-01@b0472a, R-076-03@37a3e4, R-077-05@d29340, R-079-01@7bf432, R-079-04@f543d9, R-096-06@b0f492, R-120-02@518a21, R-162-01@c6348a, R-162-02@5db7aa, R-162-03@b40132, R-163-01@b165a4, R-163-03@cdcd1b
"""VG-U-PIPE-TESTS (visible-game spec, Lane U, "U-PIPE-TESTS"): characterization tests for the mechanisms that already
run in play and show in a pipe frame, plus the pipe paths no test sent before. Fenced: builders never edit this file.

CHARACTERIZATION: every test here is green on origin/main. It asserts what the code does today, as a named expectation
with the source it came from; it adds no threshold. Each test's docstring pastes its positive control: the one-line
scratch break the writer made locally in the worktree (never committed, reverted with `git show HEAD:<file> > <file>`),
the rebuild, and the assertion line that went red.

The pin line above the docstring is written by `scripts/specfactory/rule_pins_tests.py --write-line` (HARNESS-C1b).

Mechanisms covered (evidence audit: docs/northstar/plans/drift_audits/2026-10-20-pipe-gaps.md, "Reachable and observable"):
  chronicle    significance scoring (R-066-01, R-066-02, R-066-05, R-070-01), 5-to-10 selection with category quotas
               (R-065-01, R-065-03, R-065-05), entry text assembly (R-068-01, R-068-04, R-068-06, R-068-07, R-068-08)
  generational commander stay-or-rotate (R-057-02), commander death (R-061-02, R-061-03, R-061-04), chapter phase
               machine (R-055-01, R-055-02)
  mission      eliminate-force (R-075-06), hold-zone (R-075-02), mission end and objective centre (R-075-07, R-076-01,
               R-076-03), briefing text (R-079-01)
  events       chain tags (R-027-06)
  support      per-unit move order from the enemy macro (R-120-02)
  save state   macro and fog field helpers through save and load (R-064-04)
  pipe paths   command ping (R-162-01, R-005-12), net_submit verb 5 emission (R-163-01, R-163-03), net_submit verb 6 ping
               (R-162-01), command hold (R-096-06)

FINDINGS (mechanisms the spec lists that do not show in a frame the way it says; no test was written for the part
that does not show, the evidence is in the writer's report):
  FINDING-admin-chain      no Admin template (ids 21 to 25) ever appears in delta events[] although revolts[] lists
                           triggered rolls: friction.c queues template 101 (OM_EVT_ADMIN_SEPARATIST) and events.c drops
                           any template id at or above n_templates ("unknown template: drop defensively"). The chain-tag
                           half of the mechanism (R-027-06) is tested below.
  FINDING-obstacles        map.obstacles[] is [] in every mission frame (om_map_add_obstacle has no caller outside
                           tests), so the sampling loop at pipe_tactical.c:408 never has a row to show.
  FINDING-emission         net_submit verb 5 is not observed to apply: OM_TP_EMIT_SIGHT_MULT and OM_TP_EMIT_SEEN_MULT default to
                           1.0 (tactical_move.c, OM_PP_ROWS), so the widened sight of R-163-01 is not visible in visible[];
                           only the accepted submit and the command log (net_log_dump) show it. R-163-01 calls the doubling
                           provisional "held as runtime settings"; the defaults hold 1.0, not the doubling.
  FINDING-save-fog-str     fog_sw_u8/fog_sr_u8 are called only for strings (era name and flags), and om_set_era_name and
                           om_set_era_flag have no caller in play, so on the fog side those branches see no byte; the fog round
                           trip proves the f64, i32, u32 and u64 helpers of its family. The macro side is different: the bus
                           runner (enemy_macro.c om_macro_update_bus_runner) creates "objective_N_contested" and
                           "force_N_routed" flags in play, so msv_str/msr_str and msv_u8/msr_u8 run on non-empty names once
                           the player holds the objective node; the macro round trip below drives that state.
  FINDING-pipe-hold-verb   `command` `hold` always answers error (no om_command_hold symbol, R-096-06 rejects a hold order);
                           U0 retires it, see test_command_hold_always_answers_error_today.
  FINDING-eliminate-start  no mission_start reaches an eliminate_force archetype (4 or 9) without a long refuse-and-jump
                           chain (seed 8 needs 25 of them): the pool draws are gated on breakaway factions and revolt
                           context. The eliminate test uses that chain.
"""
import importlib.util
import json
import math
import re
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
QUIT = {"type": "cmd", "name": "quit"}

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


def cmd(name, **kw):
    return {"type": "cmd", "name": name, **kw}


def set_seed(seed, **kw):
    return cmd("set_seed", seed=seed, n_regions=80, features=FEATURES, **kw)


def run(cmds, timeout=400):
    """Send the commands then quit; return every frame after hello."""
    script = b""
    for c in cmds + [QUIT]:
        body = json.dumps(c).encode()
        script += len(body).to_bytes(4, "big") + body
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=timeout)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]


def of_type(frames, kind):
    return [f for f in frames if f.get("type") == kind]


def last_tactical(frames):
    return of_type(frames, "tactical")[-1]


def start(**kw):
    return cmd("mission_start", faction=0, **kw)


BEGIN = cmd("mission_begin")
FULL = cmd("tactical_step", n=0, full=True)


def tstep(n, full=False):
    return cmd("tactical_step", n=n, full=full) if full else cmd("tactical_step", n=n)


# Numbers in this file that are neither rules nor thresholds, with where each comes from.
FLOAT_EPS = 1e-9  # a sum replayed in Python in the C order (scoring) or a ratio of HP sums (eliminate): double rounding only
FLOAT_EPS_TIGHT = 1e-12  # exact ratios of integers (hold zone: elapsed / 12000; debrief achieved): double rounding only
COVERAGE_FLOOR = 10  # a count of observed cases so a branch is not vacuous (dumped: 30 to 200 occur); a floor, not a rule value
MIN_ROOT_EVENTS = 100  # coverage floor for event roots in 400 steps (dumped: 656 and 840 on seeds 2 and 1)
DELTA_SCALE, DELTA_CAP = 50.0, 3.0  # R-066-01: base = T + min(D / 50, 3.0)
LINEAGE_MULT = 1.0 + 0.8  # R-066-02: the multiplier starts at 1.0, a lineage member in the region adds 0.8
DEDUP_OVERLAP = 0.40  # R-068-07: "40 percent or more of their content words"
PING_RADIUS = 500.0  # R-162-01: "radius 500"
ELIMINATE_STEPS = 800  # dumped on seed 8: 300 steps leave the progress at its clamp of 0, 800 give 0.014
CLASH_STEPS_BEFORE_LOSS = 5700  # test_pipe_assign_commander.py (TD A150): the first player loss lands at about tick 5765
CLASH_STEPS_AFTER = 300  # steps past the first loss so the lowest-hp unit has died (dumped: it died by 6000)
COOLDOWN_WAIT_STEPS = 450  # past OM_PULSE_COOLDOWN_TICKS = 400 (csrc/om_constants.h:563, R-162-02 "20 s")
HOLD_WINDOW, HOLD_WINDOWS = 50, 100  # dumped on seed 5: the enemy reaches the zone at tick 3230, so 5000 steps hold 35 held windows


# ---------------------------------------------------------------------------------------------------------------------
# chronicle: scoring, selection, assembly
# ---------------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def jump_chronicle(seed, ticks):
    """The chronicle frame of a `jump` of `ticks` on a fresh seed-`seed` world (the opening jump has already run)."""
    frames = run([set_seed(seed), cmd("jump", ticks=ticks)])
    chron = of_type(frames, "chronicle")
    assert len(chron) == 1, [f["type"] for f in frames]
    return chron[0]


def source(path):
    return (ROOT / path).read_text()


def gen_event_tiers():
    """(tier by template id, default tier, ownership-change tier) as csrc/generational.c writes them for the jump."""
    text = source("csrc/generational.c")
    table = re.search(r"GEN_LAUNCH_EVENT_TIER\[\] = \{(.*?)\};", text, re.S).group(1)
    tiers = [int(v) for v in re.findall(r"\d+", table)]
    default = int(re.search(r"#define GEN_DEFAULT_EVENT_TIER (\d+)", text).group(1))
    owner_change = int(re.search(r"#define GEN_OWNERSHIP_CHANGE_TIER (\d+)", text).group(1))
    return tiers, default, owner_change


def test_chronicle_significance_scoring():
    """R-066-01: base = T + min(D/50, 3.0). R-066-02: the multiplier starts at 1.0 and a lineage member in the region
    adds 0.8 (the mission-region, character and chain terms need context the jump does not pass:
    csrc/chronicle.c chron_score_event, so they add nothing). R-066-05: the score is never below the tier.
    R-070-01: an event in a lineage region gets the +0.8 and nothing else.

    What shows: a regional entry's `significance` in the chronicle frame is the cluster's peak score. It equals the
    best, over the events the same seeded world fires inside the jump (replayed with `step`, delta events[] carry
    template and the four field deltas), of tier + min(D/50, 3.0), or the ownership-change tier for a region that
    changed hands, times 1.8 in a lineage region (a lineage entry names it) and 1.0 elsewhere. Sources of the tier per
    template id: GEN_LAUNCH_EVENT_TIER, GEN_DEFAULT_EVENT_TIER, GEN_OWNERSHIP_CHANGE_TIER in csrc/generational.c.

    Positive control (scratch break, reverted): csrc/chronicle.c:1571 `return (double)tier + boost;` changed to
    `return (double)tier;` then `make libouroboros.so pipe/ouroboros_pipe`. Red:
    `assert e["significance"] == pytest.approx(want, abs=1e-9)` in test_chronicle_significance_scoring,
    seed 1 region 76 (CONTROL-SCORING-RESULT)."""
    tiers, default_tier, owner_tier = gen_event_tiers()
    saw_lineage_term = saw_plain = 0
    for seed in (1, 2, 3):
        chron = jump_chronicle(seed, 100)
        steps = run([set_seed(seed), cmd("step", n=100)])
        peak = {}
        for f in of_type(steps, "delta"):
            for ev in f["events"]:
                tier = tiers[ev["template"]] if ev["template"] < len(tiers) else default_tier
                score = tier + min(sum(abs(d) for d in ev["delta"]) / DELTA_SCALE, DELTA_CAP)
                peak[ev["region"]] = max(peak.get(ev["region"], 0.0), score)
        owners = chron["ownership"]["snapshots"]
        for r, (before, after) in enumerate(zip(owners[0], owners[-1])):
            if before != after:
                peak[r] = max(peak.get(r, 0.0), float(owner_tier))
        lineage_regions = {r for e in chron["entries"] if e["cluster_type"] == 1 for r in e["refs"]["regions"]}
        regional = [e for e in chron["entries"] if e["cluster_type"] == 3]
        assert regional, f"seed {seed}: no regional entry"
        for e in regional:
            r = e["refs"]["regions"][0]
            assert r in peak, f"seed {seed}: regional entry for region {r} but the replay fired nothing there"
            in_lineage = r in lineage_regions
            want = peak[r] * (LINEAGE_MULT if in_lineage else 1.0)
            assert e["significance"] == pytest.approx(want, abs=FLOAT_EPS), (seed, r, in_lineage, peak[r], e["significance"])
            assert e["significance"] >= 1.0, e  # R-066-05: never below the lowest tier
            saw_lineage_term += in_lineage
            saw_plain += not in_lineage
    assert saw_lineage_term >= 1 and saw_plain >= 1  # both branches of R-066-02 were exercised


SELECT_RUNS = [(s, t) for s in (1, 2, 3, 4) for t in (50, 100, 300)]


def test_chronicle_selection_quotas():
    """R-065-01: at most 10 entries, at least 5 whenever the cap allows. R-065-03/R-065-04: the player's lineage has an
    entry (or a lineage_quiet one) ahead of the rest. R-065-05: the remaining clusters are taken in descending peak
    score, skipping any category that already has 2 entries (csrc/chronicle.c OM_CHRON_CATEGORY_CAP, chron_run_selection).

    What shows: chronicle `entries[]` count, order, `cluster_type` (0 consequence, 1 lineage, 2 chain, 3 regional),
    `category` and `significance`, over 12 jumps (seeds 1 to 4, 50, 100 and 300 ticks).

    Positive control (scratch break, reverted): csrc/chronicle.c:53 `#define OM_CHRON_CATEGORY_CAP 2` changed to 3,
    rebuild. Red: `assert n <= 2, ...` in test_chronicle_selection_quotas (CONTROL-QUOTA-RESULT)."""
    for seed, ticks in SELECT_RUNS:
        entries = jump_chronicle(seed, ticks)["entries"]
        where = f"seed {seed} ticks {ticks}"
        assert 5 <= len(entries) <= 10, (where, len(entries))
        types = [e["cluster_type"] for e in entries]
        assert any(t == 1 for t in types), where
        last_head = max(i for i, t in enumerate(types) if t in (0, 1))
        first_tail = min(i for i, t in enumerate(types) if t in (2, 3))
        assert last_head < first_tail, (where, types)
        tail = [e for e in entries if e["cluster_type"] in (2, 3)]
        counts = {}
        for e in tail:
            counts[e["category"]] = counts.get(e["category"], 0) + 1
        for category, n in counts.items():
            assert n <= 2, (where, category, n)
        sig = [e["significance"] for e in tail]
        assert sig == sorted(sig, reverse=True), (where, sig)


def test_chronicle_entry_text_assembly():
    """R-068-01: the expanded form is the base form plus the closing. R-068-04: the first mention of a region in the
    scroll reads "<region>, held by <faction>", later mentions are bare, an unowned region gets no qualifier. R-068-06:
    a significant word that repeats is replaced by its curated synonym when one exists (the map is CHRON_SYNONYMS in
    csrc/chronicle.c). R-068-07: of two entries sharing 40 percent or more of their content words the later is dropped
    and the first survives (the stop words and the 0.40 are CHRON_STOP_WORDS and OM_CHRON_DEDUP_OVERLAP_THRESHOLD in
    csrc/chronicle.c; a dropped entry keeps its cluster and shows text ""). R-068-08: same seed, same text.

    What shows: chronicle `entries[].text`, `expanded_text`, `mentions[]` (code point offsets), `refs`, `fragment_ids`.
    The 12 jumps of SELECT_RUNS are read; the held-by rule is checked on the entry's own region (`refs.regions[0]`).

    Positive controls (scratch breaks, each reverted and rebuilt):
      held-by   csrc/chronicle.c:1531 `snprintf(out, cap, "%s, held by %s", name, ...)` changed to `"%s, ruled by %s"`. Red:
                `assert after.startswith(", held by") == (first and owned)` (CONTROL-HELDBY-RESULT).
      synonym   csrc/chronicle.c:1082 `replacement = chron_synonym_of(clean, cn);` (in chron_dedup_echo_words) changed to
                `replacement = NULL;`. Red: `assert max(counts.values(), default=0) <= 1` (CONTROL-SYNONYM-RESULT).
      dedup     csrc/chronicle.c:57 `#define OM_CHRON_DEDUP_OVERLAP_THRESHOLD 0.40` changed to 0.0 (the test holds the literal
                0.40 of R-068-07, not the define). Red: `assert len(kept) >= 5` (CONTROL-DEDUP-RESULT).
      dedup-use csrc/chronicle.c:1885 `>= OM_CHRON_DEDUP_OVERLAP_THRESHOLD)` changed to `>= 1.01)` (nothing is dropped). Red:
                `assert len(words & earlier) / small < DEDUP_OVERLAP` or `assert empties >= 1` (CONTROL-DEDUP-USE-RESULT)."""
    text = source("csrc/chronicle.c")
    stop = set(re.findall(r'"([a-z]+)"', re.search(r"CHRON_STOP_WORDS\[\] = \{(.*?)\};", text, re.S).group(1)))
    synonyms = dict(re.findall(r'\{"([a-z]+)", "([a-z]+)"\}', re.search(r"CHRON_SYNONYMS\[\] = \{(.*?)\};", text, re.S).group(1)))
    assert stop and synonyms

    def content_words(s):
        return {w for w in (x.lower() for x in re.findall(r"[A-Za-z]+", s)) if len(w) > 3 and w not in stop}

    saw_first = saw_later = empties = 0
    for seed, ticks in SELECT_RUNS:
        entries = jump_chronicle(seed, ticks)["entries"]
        where = f"seed {seed} ticks {ticks}"
        seen_regions, kept = set(), []
        for e in entries:
            body, expanded = e["text"], e["expanded_text"]
            region = e["refs"]["regions"][0] if e["refs"]["regions"] else None
            first = region is not None and region not in seen_regions
            if region is not None:
                seen_regions.add(region)
            if not body:
                empties += 1
                continue
            assert expanded.startswith(body) and len(expanded) > len(body), (where, e["id"])  # R-068-01
            own = [m for m in e["mentions"] if m["kind"] == "region" and m["id"] == region]
            if own:
                m = own[0]
                after = body[m["start"] + m["len"]:m["start"] + m["len"] + len(", held by")]
                owned = bool(e["refs"]["factions"])
                assert after.startswith(", held by") == (first and owned), (where, e["id"], after, first, owned)
                saw_first += first and owned
                saw_later += not first
            for t in (body, expanded):
                counts = {}
                for w in (x.lower() for x in re.findall(r"[A-Za-z]+", t)):
                    if len(w) > 3 and w in synonyms:
                        counts[w] = counts.get(w, 0) + 1
                assert max(counts.values(), default=0) <= 1, (where, e["id"], counts)  # R-068-06
            words = content_words(body)
            for earlier in kept:
                small = min(len(words), len(earlier))
                if small:
                    assert len(words & earlier) / small < DEDUP_OVERLAP, (where, e["id"])  # R-068-07
            kept.append(words)
        # R-068-07 keeps the first and drops only on overlap: the scroll keeps the R-065-01 floor of 5 entries with text
        assert len(kept) >= 5, (where, len(kept))
    assert saw_first >= COVERAGE_FLOOR and saw_later >= COVERAGE_FLOOR  # both branches of R-068-04 were exercised
    assert empties >= 1  # R-068-07 / unresolved fragments: dumped, 10 of the 120 entries show text "" (the dedup drops some)
    again = run([set_seed(1), cmd("jump", ticks=100)])
    assert [e["text"] for e in of_type(again, "chronicle")[0]["entries"]] == [
        e["text"] for e in jump_chronicle(1, 100)["entries"]
    ]  # R-068-08


# ---------------------------------------------------------------------------------------------------------------------
# generational: commander stay-or-rotate, commander death, chapter phase machine
# ---------------------------------------------------------------------------------------------------------------------

def refuse_cycle_commanders(seed, cycles):
    """(commander, lineage, chapter) of the snapshot after each post-mission jump: mission_start, mission_refuse, jump 50
    repeated `cycles` times from a fresh seed-`seed` world. Entry 0 is the world after the opening jump."""
    cmds = [set_seed(seed), cmd("snapshot")]
    for _ in range(cycles):
        cmds += [start(), cmd("mission_refuse"), cmd("jump", ticks=50)]
    frames = run(cmds)
    out = [(frames[0]["commander"], frames[0]["lineage"], frames[0]["chapter"])]
    for i, f in enumerate(frames):
        if f["type"] == "chronicle":
            s = frames[i + 1]
            assert s["type"] == "snapshot", s["type"]
            out.append((s["commander"], s["lineage"], s["chapter"]))
    assert len(out) == cycles + 1
    return out


def test_commander_stays_then_rotates():
    """R-057-02: a lineage with fewer than 2 chapters played stays, so the first post-mission jump keeps the lineage and
    advances the chapter. R-057-01: rotation is forced when the lineage has no living member within 2 hops of the mission
    region (csrc/generational.c om_character_selector_run_for_lineage, `forced`). R-057-03 and R-057-04 are pinned
    here only because they describe the roll that the rotation path shares; NO TEST REACHES THEM: the normal roll does not fire
    in the traces below (replacing `if (draw < p_rotate) {` by `if (0) {` leaves them unchanged).

    What shows: snapshot `commander`, `lineage` and `chapter` after each of four refuse-and-jump cycles. Seeds 2, 3, 4,
    6, 7 and 8 keep the same lineage through the first post-mission jump (chapter 2). Seed 1 keeps it for three jumps and
    rotates at the fourth: new commander, new lineage, chapter 5 (an observed trace of this seed and this command stream,
    named so; the rotation is the forced one, from the world the seeded stream built).

    Positive controls (scratch breaks, each reverted and rebuilt):
      stay     csrc/generational.c:1325 `int forced = (living_total == 0)` changed to `int forced = 1 || (living_total == 0)`
               (every selection rotates). Red: `assert after_first[1] == before[1]` (CONTROL-STAY-RESULT).
      rotate   csrc/generational.c:1326 `|| !gen_find_living_member_within_hops(...)` changed to
               `|| 0 && !gen_find_living_member_within_hops(...)`. Red: `assert rotated[1] != seed1[0][1]`
               (CONTROL-ROTATE-RESULT)."""
    for seed in (2, 3, 4, 6, 7, 8):
        before, after_first = refuse_cycle_commanders(seed, 1)
        assert after_first[1] == before[1], (seed, before, after_first)  # R-057-02: the lineage stays
        assert after_first[2] == before[2] + 1, (seed, before, after_first)  # the chapter advances once
    seed1 = refuse_cycle_commanders(1, 4)
    assert [t[1] for t in seed1[:4]] == [seed1[0][1]] * 4, seed1
    rotated = seed1[4]
    assert rotated[1] != seed1[0][1], seed1  # the fourth post-mission jump rotated to another lineage
    assert rotated[0] != seed1[0][0] and rotated[2] == 5, seed1


def _load_harness():
    spec = importlib.util.spec_from_file_location("long_harness_u", ROOT / "tests/long/harness.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=None)
def killed_commander_run():
    """One interactive session (tests/long/harness.py Pipe) on seed 1's chapter-1 Assault (dumped: 330 player units against
    350): every player unit attack-moves onto the enemy centroid, CLASH_STEPS_BEFORE_LOSS steps run (no player unit has died
    yet), the player unit with the lowest hp is assigned commander (`assign_commander` acks in play, R-077-05), then
    CLASH_STEPS_AFTER more steps, `mission_end` and the post-mission `jump` 50. Returns the debrief, the snapshot after
    mission_end, the chronicle frame, the snapshot after the jump and the commander unit's id."""
    harness = _load_harness()
    pipe = harness.Pipe()
    try:
        pipe.cmd("set_seed", seed=1, n_regions=80, features=FEATURES)
        pipe.cmd("step", n=10)
        pipe.cmd("mission_start", faction=0)
        while pipe.read_more()["type"] != "mission":
            pass
        pipe.send("mission_begin")
        units = pipe.send("tactical_step", n=0, full=True)["units"]
        player = [u["id"] for u in units if u["faction"] == 0]
        enemy = [u for u in units if u["faction"] != 0]
        ex, ey = sum(u["x"] for u in enemy) / len(enemy), sum(u["y"] for u in enemy) / len(enemy)
        assert pipe.send("command", verb="attack_move", units=player, x=ex, y=ey)["type"] == "ack"
        mid = pipe.send("tactical_step", n=CLASH_STEPS_BEFORE_LOSS, full=True)
        assert mid["mission_over"] is False, "fixture drifted: the mission ended before the clash"
        commander = min((u for u in mid["units"] if u["faction"] == 0), key=lambda u: u["hp"])["id"]
        assert pipe.send("assign_commander", unit_id=commander)["type"] == "ack"
        after = pipe.send("tactical_step", n=CLASH_STEPS_AFTER, full=True)
        assert commander not in {u["id"] for u in after["units"]}, "fixture drifted: the lowest-hp unit survived the clash"
        debrief = pipe.send("mission_end")
        ended = pipe.read_more()
        chron = pipe.send("jump", ticks=50)
        jumped = pipe.read_more()
        return {"debrief": debrief, "ended": ended, "chron": chron, "jumped": jumped}
    finally:
        pipe.close()


def test_commander_death_ends_the_chapter_and_seats_a_successor():
    """R-061-01/R-061-02: a commander who died in the mission is replaced by a living member of the same lineage and the
    chapter counter continues. R-061-03 is the rotation when none exists (not reached here). R-061-04: the chronicle
    frames the death. The chapter end reason 1 is `GEN_CHAPTER_END_COMMANDER_DEATH` (docs/architecture.md, chronicle
    `jump.chapter_end_reason`).

    What shows: debrief `commander_fate` 0 (killed) after the clash (the commander is the lowest-hp player unit at step 5700); the snapshot after `mission_end` and the one after
    the jump: `commander` changes, `lineage` stays, `chapter` 1 to 2; the chronicle frame's `jump.chapter_end_reason` is
    1 and its entries open with a consequence cluster (cluster_type 0, outcome category 1 = failure for band 0, R-065-02).
    Slow: one 6000-step clash in one session, about 17 s.

    Positive control (scratch break, reverted and rebuilt): csrc/generational.c:1296 `d.commander_fate == 0` changed to
    `d.commander_fate == 9`. Red: `assert jumped["commander"] != ended["commander"]` (CONTROL-DEATH-RESULT)."""
    run_frames = killed_commander_run()
    debrief, ended, jumped, chron = run_frames["debrief"], run_frames["ended"], run_frames["jumped"], run_frames["chron"]
    assert (debrief["type"], debrief["commander_fate"]) == ("debrief", 0), debrief  # premise: the assigned commander unit died
    assert chron["jump"]["chapter_end_reason"] == 1, chron["jump"]
    assert jumped["commander"] != ended["commander"], (ended["commander"], jumped["commander"])
    assert jumped["lineage"] == ended["lineage"], (ended["lineage"], jumped["lineage"])  # R-061-02: same lineage
    assert (ended["chapter"], jumped["chapter"]) == (1, 2)
    first = chron["entries"][0]
    assert first["cluster_type"] == 0 and first["category"] == 1, first  # R-061-04: framed, outcome category 1 = failure


def phase_run(extra, path):
    """Save at each point of `extra` (a list of (label, command list)), then list_saves; returns {label: slot dict}."""
    cmds = [set_seed(5)]
    for label, group in extra:
        cmds += group + [cmd("save", path=str(path / f"{label}.omsave"))]
    cmds.append(cmd("list_saves", dir=str(path)))
    saves = of_type(run(cmds), "saves")[0]
    return {Path(s["path"]).stem: s for s in saves["slots"]}


def test_chapter_phase_machine():
    """R-055-01: the chapter runs briefing, recon, mission, outcome, jump, selection, next briefing. R-055-02: while the
    mission runs no strategic tick runs. The pipe drives phases with om_chapter_set_phase (csrc/pipe/om_pipe.c, the
    OM_PIPE_CHAPTER_PHASE_* mirrors: 0 briefing, 2 mission) and the save sidecar records om_chapter_current_phase.

    What shows: the save sidecar `phase` read through list_saves: 0 after the opening jump, 2 after mission_start (recon
    lives inside the mission phase: `command` answers "not begun" until mission_begin) and after mission_begin, 0 after
    mission_end, 0 after a jump, 0 after a refused mission; `chapter` 1 then 2 after the post-mission jump; `step` and
    `run_to` are refused with "mission running" while phase 2 holds and run again after the mission ends.

    Positive control (scratch break, reverted and rebuilt): csrc/pipe/om_pipe.c:1360
    `om_chapter_set_phase(W, OM_PIPE_CHAPTER_PHASE_MISSION);` changed to `..._PHASE_BRIEFING);`, `make pipe/ouroboros_pipe`.
    Red: `assert [phases[k] for k in order] == [0, 2, 2, 0, 0, 0]` (CONTROL-PHASE-RESULT)."""
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)
        order = ["a_start", "b_recon", "c_mission", "d_ended", "e_jumped", "f_refused"]
        slots = phase_run([
            ("a_start", []),
            ("b_recon", [start()]),
            ("c_mission", [BEGIN, tstep(3)]),
            ("d_ended", [cmd("mission_end")]),
            ("e_jumped", [cmd("jump", ticks=50)]),
            ("f_refused", [start(), cmd("mission_refuse")]),
        ], path)
        phases = {k: slots[k]["phase"] for k in order}
        assert [phases[k] for k in order] == [0, 2, 2, 0, 0, 0], phases
        assert [slots[k]["chapter"] for k in order] == [1, 1, 1, 1, 2, 2], slots
    frames = run([set_seed(5), start(), cmd("step", n=1), cmd("run_to", tick=30), BEGIN, cmd("mission_end"), cmd("step", n=1)])
    refused = [f for f in frames if f["type"] == "error"]
    assert [(f["name"], f["reason"]) for f in refused] == [("step", "mission running"), ("run_to", "mission running")], frames
    assert of_type(frames, "delta"), "the strategic step did not run after the mission ended"


# ---------------------------------------------------------------------------------------------------------------------
# mission: eliminate-force, hold-zone, end and objective centre, briefing
# ---------------------------------------------------------------------------------------------------------------------

def eliminate_setup():
    """Seed 8: 25 refuse-and-jump cycles later the 26th mission_start draws archetype 4 (Suppression, kind eliminate_force)."""
    cmds = [set_seed(8)]
    for _ in range(25):
        cmds += [start(), cmd("mission_refuse"), cmd("jump", ticks=20)]
    return cmds + [start()]


def hp_by_faction(units):
    out = {}
    for u in units:
        out[u["faction"]] = out.get(u["faction"], 0.0) + u["hp"]
    return out


def test_eliminate_force_objective_tracks_enemy_hp():
    """R-075-06: eliminate_force completion = enemy HP destroyed / initial enemy HP (csrc/mission.c
    om_mission_eval_eliminate, called from om_mission_tactical_tick). R-075-07: the mission is not over while it is
    incomplete.

    What shows: the mission frame's objective kind 4 (eliminate_force) for archetype 4 (premise, FINDING-eliminate-start),
    then every player unit attack-moves onto the enemy centroid, 800 tactical steps run, and the tactical frame's
    `objectives[0].progress` equals 1 - (enemy HP now) / (enemy HP in the frame at mission_begin), summed over the units[]
    of the enemy faction, to 1e-9 (the progress is clamped at 0 before the enemy loses HP: it was 0 at 300 steps).

    Positive control (scratch break, reverted and rebuilt): csrc/mission.c:1569
    `double c = (o->eliminate_initial_hp > 0.0) ? hp_destroyed / o->eliminate_initial_hp : 0.0;` changed to divide by
    `(2.0 * o->eliminate_initial_hp)`. Red: `assert progress == pytest.approx(want, abs=1e-9)` (CONTROL-ELIMINATE-RESULT)."""
    probe = run(eliminate_setup() + [BEGIN, FULL])
    mission = of_type(probe, "mission")[-1]
    assert (mission["archetype"], mission["objectives"][0]["kind"]) == (4, 4), mission  # premise
    units = last_tactical(probe)["units"]
    player = [u["id"] for u in units if u["faction"] == 0]
    enemy = [u for u in units if u["faction"] != 0]
    ex, ey = sum(u["x"] for u in enemy) / len(enemy), sum(u["y"] for u in enemy) / len(enemy)
    enemy_faction = enemy[0]["faction"]
    hp0 = hp_by_faction(units)[enemy_faction]
    frames = run(eliminate_setup() + [BEGIN, cmd("command", verb="attack_move", units=player, x=ex, y=ey), tstep(ELIMINATE_STEPS), FULL])
    final = last_tactical(frames)
    progress = final["objectives"][0]["progress"]
    want = 1.0 - hp_by_faction(final["units"])[enemy_faction] / hp0
    assert progress > 0.0 and final["mission_over"] is False, final["objectives"]
    assert progress == pytest.approx(want, abs=FLOAT_EPS), (progress, want)


def source_constant(path, name):
    return int(re.search(rf"#define {name} (\d+)", source(path)).group(1))


def test_hold_zone_objective_advances_only_while_no_enemy_is_inside():
    """R-075-02: the hold timer advances only while no enemy unit is inside the zone radius; required = 12,000 base ticks;
    completion = elapsed / required (csrc/mission.c OM_MISSION_HOLD_ZONE_REQUIRED_TICKS, om_mission_eval_hold_zone).

    What shows: seed 5's first mission is archetype 0 (Defensive Stand, objective kind 0 hold_zone, radius 400, node 0). 100
    full tactical frames, 50 steps apart: in every 50-step window with no enemy unit within the objective radius of the node
    at either end, `objectives[0].progress` grows by exactly 50/12000; in every window with an enemy inside at both ends it
    does not grow. Both kinds of window occur (the enemy reaches the zone at tick 3230).

    Positive control (scratch break, reverted and rebuilt): csrc/mission.c:1591
    `if (enemies_inside == 0) o->hold_elapsed_ticks += om_tactical_tick_period(w);` changed to `if (1) ...`. Red:
    `assert progress[k] == pytest.approx(progress[k - 1], abs=1e-12)` (CONTROL-HOLD-RESULT)."""
    required = source_constant("csrc/mission.c", "OM_MISSION_HOLD_ZONE_REQUIRED_TICKS")
    window, windows = HOLD_WINDOW, HOLD_WINDOWS
    frames = run([set_seed(5), start(), BEGIN] + [tstep(window, True)] * windows)
    mission = of_type(frames, "mission")[0]
    assert (mission["archetype"], mission["objectives"][0]["kind"], mission["objectives"][0]["radius"]) == (0, 0, 400), mission
    ticks = of_type(frames, "tactical")[1:]
    assert len(ticks) == windows
    node = next(n for n in ticks[0]["map"]["nodes"] if n["i"] == mission["objectives"][0]["node"])
    radius = mission["objectives"][0]["radius"]

    def inside(frame):
        return any(u["faction"] != 0 and math.hypot(u["x"] - node["x"], u["y"] - node["y"]) <= radius for u in frame["units"])

    progress = [0.0] + [f["objectives"][0]["progress"] for f in ticks]
    states = [False] + [inside(f) for f in ticks]
    grew = held = 0
    for k in range(1, windows + 1):
        if not states[k - 1] and not states[k]:
            assert progress[k] == pytest.approx(progress[k - 1] + window / required, abs=FLOAT_EPS_TIGHT), (k, progress[k - 1:k + 1])
            grew += 1
        elif states[k - 1] and states[k]:
            assert progress[k] == pytest.approx(progress[k - 1], abs=FLOAT_EPS_TIGHT), (k, progress[k - 1:k + 1])
            held += 1
    assert grew >= COVERAGE_FLOOR and held >= COVERAGE_FLOOR, (grew, held)


def test_mission_ends_at_the_time_limit_and_the_objective_centre_is_on_the_map():
    """R-075-07: the mission ends on the first of objective complete, time limit reached, player force eliminated. R-076-01:
    the limit is the mission frame's `deadline_ticks`. R-076-03: once over, the objective values are final.

    What shows: seed 5's first mission (deadline_ticks 38190, hold_zone, the enemy sits in the zone so it never completes):
    the tactical frame is `mission_over` false, `band` -1 at step deadline - 1, then `mission_over` true with a band
    0..4 at step deadline, and `objectives[0].progress` and `band` do not change over three more steps; `mission_end` then
    answers a debrief with the same band and `achieved` equal to that progress. Objective centre: for seeds 5, 1 and 3 the
    full frame's map node numbered by `objectives[0].node` (kind 0) has a `cover` disc of radius `objectives[0].radius` at
    the same x and y.

    Positive controls (scratch breaks, each reverted and rebuilt):
      limit   csrc/mission.c:1197 `if (st->term_tick >= st->term_time_limit) return 1;` changed to `>`. Red:
              `assert (over_at_limit["mission_over"], over_at_limit["band"] in range(5)) == (True, True)`
              (CONTROL-LIMIT-RESULT).
      centre  csrc/mission.c:2747 `om_map_add_cover(w, ox, oy, OM_MISSION_OBJECTIVE_COVER_RADIUS, ...` changed to `ox + 100.0`.
              Red: `assert (disc["x"], disc["y"]) == (node["x"], node["y"])` (CONTROL-CENTRE-RESULT)."""
    probe = run([set_seed(5), start()])
    deadline = of_type(probe, "mission")[0]["deadline_ticks"]
    frames = run([set_seed(5), start(), BEGIN, tstep(deadline - 1), tstep(1), tstep(1), tstep(1), tstep(1), cmd("mission_end")])
    ticks = of_type(frames, "tactical")[1:]
    before, over_at_limit, *after = ticks
    assert (before["mission_over"], before["band"]) == (False, -1), before
    assert (over_at_limit["mission_over"], over_at_limit["band"] in range(5)) == (True, True), over_at_limit
    for later in after:
        assert later["mission_over"] is True and later["band"] == over_at_limit["band"], later  # R-076-03
        assert later["objectives"][0]["progress"] == over_at_limit["objectives"][0]["progress"]
    debrief = of_type(frames, "debrief")[0]
    assert debrief["band"] == over_at_limit["band"]
    assert debrief["achieved"] == pytest.approx(over_at_limit["objectives"][0]["progress"], abs=FLOAT_EPS_TIGHT)
    for seed in (5, 1, 3):
        fs = run([set_seed(seed), start(), BEGIN])
        obj = of_type(fs, "mission")[0]["objectives"][0]
        m = last_tactical(fs)["map"]
        node = next(n for n in m["nodes"] if n["i"] == obj["node"])
        assert node["kind"] == 0, node
        disc = next(c for c in m["cover"] if c["r"] == obj["radius"])
        assert (disc["x"], disc["y"]) == (node["x"], node["y"]), (seed, node, disc)


def test_briefing_text_has_situation_objective_and_assets():
    """R-079-01: the briefing has exactly Situation, Objective and Assets, in that order, each from authored fragments;
    Assets states parity in prose and names shortfall types. R-079-04: no raw field numbers in the text.
    (csrc/mission.c om_mission_assemble_briefing; the names are om_mission_archetype_name and
    om_mission_objective_kind_name.)

    What shows: the mission frame's `briefing` for seed 5 (Defensive Stand, hold the zone), seed 1 (Assault, destroy the
    designated targets), seed 3 (Rear Guard / Evacuation, escort the force to extraction) and the eliminate fixture
    (Suppression, eliminate the enemy force, whose assets read "no shortfall reported"): keys situation, objective, assets in
    that order, the archetype name in the situation, the objective name for the objective kind, "forces committed at
    parity" in the assets, a "Shortfall:" clause exactly when the assets do not read "no shortfall", no fractional number
    in any of the three.

    Positive control (scratch break, reverted and rebuilt): csrc/mission.c:1053 `"Objective: %s."` changed to `"Goal: %s."`.
    Red: `assert b["objective"] == f"Objective: {objective_names[kind]}."` (CONTROL-BRIEFING-RESULT)."""
    names = re.search(r"names\[OM_MISSION_N_ARCHETYPES\] = \{(.*?)\};", source("csrc/mission.c"), re.S).group(1)
    archetype_names = re.findall(r'"([^"]+)"', names)
    objective_names = {0: "hold the zone", 1: "destroy the designated targets", 2: "escort the force to extraction",
                       4: "eliminate the enemy force"}
    assert len(archetype_names) == 10
    runs = {5: [set_seed(5), start()], 1: [set_seed(1), start()], 3: [set_seed(3), start()], "elim": eliminate_setup()}
    seen_shortfall = seen_none = 0
    for label, cmds in runs.items():
        m = of_type(run(cmds), "mission")[-1]
        b, kind = m["briefing"], m["objectives"][0]["kind"]
        assert list(b) == ["situation", "objective", "assets"], (label, list(b))
        assert b["situation"] == f"Situation: {archetype_names[m['archetype']]} conditions have developed on the frontier.", b
        assert b["objective"] == f"Objective: {objective_names[kind]}.", b
        assert b["assets"].startswith("Assets: forces committed at parity"), b
        has_shortfall = "Shortfall:" in b["assets"]
        assert has_shortfall == ("no shortfall reported" not in b["assets"]), b
        seen_shortfall += has_shortfall
        seen_none += not has_shortfall
        assert not any(re.search(r"\d+\.\d", t) for t in b.values()), b  # R-079-04: no fractional field value
    assert seen_shortfall >= 1 and seen_none >= 1  # both Assets branches were exercised


# ---------------------------------------------------------------------------------------------------------------------
# events chain tags, enemy macro move order, save-state field helpers
# ---------------------------------------------------------------------------------------------------------------------

def test_event_chain_tags_follow_their_root():
    """R-027-06: any spawned event carries the chain tag of its root event, and the tag is unique per chain start and
    sequential (csrc/events.c: every trigger-fired event takes `++s->chain_counter`; om_event_queue_external takes
    counter + 1). The admin-revolt half of this mechanism does not show (FINDING-admin-chain, module docstring): no
    Admin template ever fires, so only the tag rule is pinned.

    What shows: delta events[] over 400 steps of seeds 1 and 2 (new_campaign false, so tick 1 is the first step): events
    with source 0 (trigger) or 2 (external), the roots, carry the tags 1, 2, 3 ... with no gap and no repeat in firing
    order, and every event with source 1 (spawned) carries a tag a root already holds.

    Positive control (scratch break, reverted and rebuilt): csrc/events.c:908 `int32_t tag = ++s->chain_counter;` changed to
    `int32_t tag = s->chain_counter + 1;`. Red: `assert tags == list(range(1, len(tags) + 1))` (CONTROL-CHAIN-RESULT)."""
    for seed in (1, 2):
        frames = run([set_seed(seed, new_campaign=False), cmd("step", n=400)])
        events = [e for f in of_type(frames, "delta") for e in f["events"]]
        roots = [e for e in events if e["source"] != 1]
        spawned = [e for e in events if e["source"] == 1]
        tags = [e["chain"] for e in roots]
        assert len(tags) > MIN_ROOT_EVENTS and spawned, (seed, len(tags), len(spawned))
        assert tags == list(range(1, len(tags) + 1)), (seed, tags[:12])
        assert {e["chain"] for e in spawned} <= set(tags), seed


def test_enemy_macro_move_order_shows_in_the_tactical_frame():
    """R-120-02: the enemy macro layer issues group orders (csrc/enemy_macro.c om_macro_issue_group_orders, per-unit rows
    through om_command_attack_move and, on a rout, om_unit_order_move); the first evaluation is the 40-tick interval
    OM_SCRIPT_EVAL_INTERVAL_TICKS, and an advancing force heads for the objective centre.

    What shows (seed 5, no player command at all): after 40 tactical steps no unit has moved; after 41 every enemy unit has
    moved and ends nearer to the objective node than it began, and no player unit moved; the delta frame of step 41
    (`units_changed`) lists exactly the enemy units.

    Positive control (scratch break, reverted and rebuilt): csrc/enemy_macro.c:504 in the OM_MACRO_ADVANCE branch,
    `om_command_attack_move(w, force_ids, n_force, dest_x, dest_y);` changed to `(void)0;`. Red:
    `assert moved == set(enemy)` (CONTROL-MACRO-MOVE-RESULT).

    Scope: this drives the ADVANCE branch only (enemy_macro.c:504, om_command_attack_move). The RETREAT branch, the only caller
    of om_unit_order_move (enemy_macro.c:525, B1-U1), is not driven: no scenario here routs an enemy force."""
    base = [set_seed(5), start(), BEGIN]
    f0 = last_tactical(run(base + [FULL]))
    pos0 = {u["id"]: (u["x"], u["y"]) for u in f0["units"]}
    faction = {u["id"]: u["faction"] for u in f0["units"]}
    enemy = [i for i, f in faction.items() if f != 0]
    node = next(n for n in f0["map"]["nodes"] if n["kind"] == 0)

    def moved_ids(steps):
        f = last_tactical(run(base + [tstep(steps, True)]))
        return f, {u["id"] for u in f["units"] if (u["x"], u["y"]) != pos0[u["id"]]}

    _, none_moved = moved_ids(40)
    assert none_moved == set()
    f41, moved = moved_ids(41)
    assert moved == set(enemy), (len(moved), len(enemy))
    for u in f41["units"]:
        if u["faction"] != 0:
            before = math.hypot(pos0[u["id"]][0] - node["x"], pos0[u["id"]][1] - node["y"])
            assert math.hypot(u["x"] - node["x"], u["y"] - node["y"]) < before, u
    delta = last_tactical(run(base + [tstep(40), tstep(1)]))
    assert delta["full"] is False and {u["id"] for u in delta["units_changed"]} == set(enemy)


def checksum_sections(frames):
    return [f["sections"] for f in of_type(frames, "net_ack") if f.get("name") == "net_checksum"]


def save_round_trip(prefix, steps_after, saved_bytes=None):
    """prefix commands, net_checksum, save; then (A) steps_after steps without a load vs (B) a load then the same steps.
    Returns (sections at save, sections right after the load, frame A, frame B, sections after A's steps). When
    `saved_bytes` is a list, the bytes of the .omsave written by the save are appended to it."""
    with tempfile.TemporaryDirectory() as d:
        slot = str(Path(d) / "mid.omsave")
        pre = prefix + [cmd("net_checksum"), cmd("save", path=slot)]
        a = run(pre + [tstep(steps_after, True), cmd("net_checksum")])
        b = run(pre + [cmd("load", path=slot), cmd("net_checksum"), tstep(steps_after, True)])
        if saved_bytes is not None:
            saved_bytes.append(Path(slot).read_bytes())
    at_save = checksum_sections(a)[0]
    return at_save, checksum_sections(b)[1], last_tactical(a), last_tactical(b), checksum_sections(a)[1]


MACRO_SECTION, FOG_SECTION = 7, 6  # tests/net/driver.py SECTIONS order: regions, factions, rng, units, movement, mission, fog, macro, support_map


# Seed 5, all 32 player units ordered to the objective node (8000, 8000): by 3000 steps the bus runner has set the flags
# "objective_N_contested" (csrc/enemy_macro.c om_macro_update_bus_runner, snprintf at :748 and :797) and the saved bytes hold
# those names; 4000 steps leaves a margin. Coverage floor, not a rule value.
MACRO_BUS_STEPS = 4000


def test_macro_state_survives_a_save_and_load():
    """R-064-04: a save and load leaves the next time jump or step as if never saved (determinism includes every saved
    section). The enemy macro writes and reads its force table and its bus flags through msv_* / msr_* (csrc/enemy_macro.c
    macro_state_put and its reader). The bus runner sets "objective_N_contested" flags in play, so msv_str/msr_str and
    msv_u8/msr_u8 run on non-empty names in this state (premise asserted below on the saved bytes); the fog side has no such
    string (FINDING-save-fog-str).

    What shows: seed 5, the player force ordered to node (8000, 8000), MACRO_BUS_STEPS tactical steps, net_checksum, save
    (the .omsave holds b"objective_" and b"_contested"); then 100 steps with no load (A) against load then 100 steps (B): the
    `macro` section hash of net_checksum right after the load equals the one at save and differs from the one 100 steps on (the
    state is live), and the 100-step full tactical frames of A and B are equal key for key.

    Positive controls (scratch breaks, each reverted and rebuilt; the earlier 300-step prefix left msr_u8 broken and the test
    green, which is why the prefix changed):
      u8     csrc/enemy_macro.c:1346 `msr_u8` `(uint32_t)msr_uint(sr, sizeof(uint8_t))` XORed with 1u. Red:
             `assert after_load[MACRO_SECTION] == at_save[MACRO_SECTION]` (CONTROL-MACRO-U8-RESULT).
      str    csrc/enemy_macro.c:1363 in msr_str `dst[i] = (char)msr_u8(sr);` changed to
             `dst[i] = (char)msr_u8(sr) ^ (char)(i == 0);` (the first name byte flips; a break that skips the read desyncs the
             reader, the load fails and the in-process world is left as it was, so it stays green). Red: the same line
             (CONTROL-MACRO-STR-RESULT).
      f64    csrc/enemy_macro.c:1354 in msr_f64 `return v;` changed to `return 0.0;`. Red: the same line
             (CONTROL-MACRO-F64-RESULT)."""
    mine = seed5_player_ids()
    prefix = [set_seed(5), start(), BEGIN, cmd("command", verb="move", units=mine, x=8000.0, y=8000.0), tstep(MACRO_BUS_STEPS)]
    saved = []
    at_save, after_load, frame_a, frame_b, later = save_round_trip(prefix, 100, saved)
    assert b"objective_" in saved[0] and b"_contested" in saved[0]  # premise: a bus flag name is in the saved state
    assert at_save[MACRO_SECTION] != later[MACRO_SECTION]  # the section is live state, not a constant
    assert after_load[MACRO_SECTION] == at_save[MACRO_SECTION]
    assert frame_b == frame_a


def pick_ping_pair(frame_full):
    """(caster id, enemy id, x, y, layer, distance): the player unit and enemy unit nearest each other in `frame_full`."""
    mine = [u for u in frame_full["units"] if u["faction"] == 0]
    foes = [u for u in frame_full["units"] if u["faction"] != 0]
    d, a, b = min((math.hypot(m["x"] - e["x"], m["y"] - e["y"]), m, e) for m in mine for e in foes)
    return a["id"], b["id"], b["x"], b["y"], b["layer"], d


APPROACH_STEPS = 3000  # seed 5: all 32 player units moved to (8000, 12000) for 3000 steps close on the enemy to ~1087 wu
PING_REACH = 2000.0  # csrc/tactical_move.c OM_PP_PING_REACH_DEFAULT; the player unit sight is 800 (units[].sight)


def approach_cmds(mine):
    return [set_seed(5), start(), BEGIN, cmd("command", verb="move", units=mine, x=8000.0, y=12000.0), tstep(APPROACH_STEPS)]


def seed5_player_ids():
    return [u["id"] for u in last_tactical(run([set_seed(5), start(), BEGIN]))["units"] if u["faction"] == 0]


def test_fog_state_survives_a_save_and_load():
    """R-064-04 (as the macro test) for the fog state: fog_sw_* / fog_sr_* (csrc/fog.c fog_state_put and its reader) write
    the ping reveals (position, radius, caught bits, expiry), the cast cooldown table and the unit tracks. FINDING-save-fog-str
    applies: only the f64, i32, u32 and u64 helpers see data.

    What shows: seed 5 as the ping test (one enemy 1087 wu from a player unit, outside its sight), a ping revealing it, 10 more
    steps, net_checksum, save; then 20 steps with no load (A) against load then 20 steps (B): the `fog` section hash right after
    the load equals the one at save and differs from the one of a world with no reveal, the live reveal still shows the enemy
    in `visible[0]` after the load (the enemy is outside every passive sight at that tick), and the 20-step full frames of A and
    B are equal key for key.

    Positive control (scratch break, reverted and rebuilt): csrc/fog.c:1189 in fog_sr_f64 (defined at :1185), `return v;`
    changed to `return 0.0;`. Red: `assert after_load[FOG_SECTION] == at_save[FOG_SECTION]` (CONTROL-FOG-SAVE-RESULT)."""
    mine = seed5_player_ids()
    caster, target, x, y, layer, distance = pick_ping_pair(last_tactical(run(approach_cmds(mine) + [FULL])))
    assert 800.0 < distance <= PING_REACH, distance  # premise: outside passive sight, inside ping reach
    ping = cmd("command", verb="ping", units=[caster], layer=layer, x=x, y=y)
    prefix = approach_cmds(mine) + [ping, tstep(10)]
    at_save, after_load, frame_a, frame_b, _ = save_round_trip(prefix, 20)
    no_reveal = checksum_sections(run(approach_cmds(mine) + [tstep(10), cmd("net_checksum")]))[0]
    assert at_save[FOG_SECTION] != no_reveal[FOG_SECTION]  # the reveal is in the section
    assert after_load[FOG_SECTION] == at_save[FOG_SECTION]
    assert target in frame_b["visible"]["0"] and frame_b["visible"] == frame_a["visible"]
    assert frame_b == frame_a


# ---------------------------------------------------------------------------------------------------------------------
# pipe paths no test sent before: command ping, net_submit verbs 5 and 6, command hold
# ---------------------------------------------------------------------------------------------------------------------

def enemy_ids(frame):
    return {u["id"] for u in frame["units"] if u["faction"] != 0}


def test_command_ping_reveals_the_enemy_it_is_cast_at():
    """R-162-01: in a space era, selected units, a layer and a place: every enemy unit on that layer around that place becomes
    visible and stays visible for a short time wherever it moves, within a reach of 2,000 (radius 500, reveal 5 s).
    R-162-02: the ping costs no resource and the casting unit has a cooldown. R-162-03: the pinged player is told nothing
    and the alert is off, so no frame carries it: only the revealed ids in `visible[0]` are observed.
    R-005-12: a ground era has no ping.

    What shows (seed 5, the 3000-step approach of the fog test): before the ping `visible[0]` holds no enemy id; after
    `command ping` (answered `ack`) the pinged enemy is in `visible[0]` after 0 and after 50 more steps, and the enemies
    newly visible at the cast are exactly those on that layer within 500 wu (R-162-01) of the pinged place at the cast (here the
    target alone: the next nearest enemy is 1145 wu away, so the check pins that nothing beyond the radius is revealed); a second ping of the same unit at once answers `error`
    `command failed` (cooldown), and one 450 steps later, at where the enemy then is, is acknowledged; a ping from a ground-era
    mission answers `command failed`; a ping beyond reach answers `command failed`; no tactical frame carries a key naming alerts.

    Positive control (scratch break, reverted and rebuilt): csrc/pipe/om_pipe.c:1600
    `om_command_ping(W, unit_ids[0], (uint32_t)layer, x, y) != 0;` changed to `0;` (the ack stays, nothing is cast), then
    `make pipe/ouroboros_pipe`. Red: `assert target in now["visible"]["0"] and target in later["visible"]["0"]` (CONTROL-PING-RESULT).
    Radius control: csrc/fog.c:959 `r->radius = om_tactical_get_param(w, OM_TP_PING_RADIUS);` changed to `3.0 *` that. Red:
    `assert newly == around and target in around` (CONTROL-PING-RADIUS-RESULT)."""
    mine = seed5_player_ids()
    base = approach_cmds(mine)
    before = last_tactical(run(base + [FULL]))
    caster, target, x, y, layer, distance = pick_ping_pair(before)
    assert 800.0 < distance <= PING_REACH, distance  # premise
    assert not (set(before["visible"]["0"]) & enemy_ids(before)), "premise: no enemy is passively visible"
    ping = cmd("command", verb="ping", units=[caster], layer=layer, x=x, y=y)
    frames = run(base + [ping, FULL, tstep(50, True)])
    ack = [f for f in frames if f.get("name") == "command"]
    assert ack and ack[-1]["type"] == "ack", ack
    now, later = of_type(frames, "tactical")[-2:]
    assert target in now["visible"]["0"] and target in later["visible"]["0"]  # revealed, and still revealed 50 steps on
    # R-162-01: every enemy on that layer within the radius of the place at the cast is revealed, and nothing else is: the
    # `before` frame and `now` are the same tick, so the cast-time positions are the `before` ones
    around = {u["id"] for u in before["units"]
              if u["faction"] != 0 and u["layer"] == layer and math.hypot(u["x"] - x, u["y"] - y) <= PING_RADIUS}
    newly = (set(now["visible"]["0"]) - set(before["visible"]["0"])) & enemy_ids(now)
    assert newly == around and target in around, (newly, around)
    assert not any("alert" in k for f in of_type(frames, "tactical") for k in f)  # R-162-03
    twice = run(base + [ping, ping])
    answers = [f for f in twice if f.get("name") == "command"][1:]  # the first answer is the approach's move order
    assert [a["type"] for a in answers] == ["ack", "error"], answers  # R-162-02: the caster is on cooldown
    assert answers[1]["reason"] == "command failed"
    # past the cooldown (OM_PULSE_COOLDOWN_TICKS, 400 steps) the same unit pings again, at where the enemy then is
    mid = last_tactical(run(base + [ping, tstep(COOLDOWN_WAIT_STEPS, True)]))
    enemy_now = next(u for u in mid["units"] if u["id"] == target)
    later_ping = cmd("command", verb="ping", units=[caster], layer=enemy_now["layer"], x=enemy_now["x"], y=enemy_now["y"])
    recast = run(base + [ping, tstep(COOLDOWN_WAIT_STEPS), later_ping])
    assert [f["type"] for f in recast if f.get("name") == "command"][1:] == ["ack", "ack"], recast[-3:]
    far = run(base + [cmd("command", verb="ping", units=[caster], layer=layer, x=x, y=y + 5000.0)])
    assert [f.get("reason") for f in far if f.get("name") == "command"][-1] == "command failed"
    ground = run([set_seed(5), start(era_kind=1), BEGIN, cmd("command", verb="ping", units=[1], layer=0, x=7925.0, y=100.0)])
    assert [f.get("reason") for f in ground if f.get("name") == "command"] == ["command failed"]  # R-005-12
    assert [f["type"] for f in ground if f.get("name") == "command"] == ["error"]


# tests/net/driver.py is a plain module beside the net tests; load it the way test_pipe_net_verbs.py loads the harness
def _load_driver():
    sys.path.insert(0, str(ROOT / "tests/net"))
    sys.path.insert(0, str(ROOT / "tests/long"))
    spec = importlib.util.spec_from_file_location("net_driver_u", ROOT / "tests/net/driver.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# csrc/cmd_stream.c:17-29, the log layout `net_log_dump` writes
LOG_HEADER, OFF_TICK, OFF_SEQ, OFF_ARG, OFF_PEER, OFF_VERB, OFF_LAYER, OFF_NUNITS, OFF_IDS = 12, 0, 8, 12, 32, 33, 34, 35, 36


def log_entries(hex_text):
    data = bytes.fromhex(hex_text)
    assert data[:4] == b"OMCL", data[:4]
    count = int.from_bytes(data[8:12], "little")
    out, off = [], LOG_HEADER
    for _ in range(count):
        n = data[off + OFF_NUNITS]
        out.append({
            "tick": int.from_bytes(data[off + OFF_TICK:off + OFF_TICK + 8], "little"),
            "arg": int.from_bytes(data[off + OFF_ARG:off + OFF_ARG + 4], "little"),
            "verb": data[off + OFF_VERB], "layer": data[off + OFF_LAYER],
            "units": [int.from_bytes(data[off + OFF_IDS + 4 * i:off + OFF_IDS + 4 * i + 4], "little") for i in range(n)],
        })
        off += OFF_IDS + 4 * n
    return out


def net_command(tick, verb, units, arg=0, layer=0, x=0.0, y=0.0, seq=0):
    return dict(tick=tick, peer=0, seq=seq, verb=verb, arg=arg, layer=layer, x=x, y=y, units=units)


def test_net_submit_emission_verb_is_accepted_and_logged():
    """R-163-01 / R-163-03 (emit or stay silent, a toggle on a unit or group, no resource cost), verb contract
    csrc/ouroboros_sim.h om_net_verb OM_NET_VERB_SET_EMISSION = 5, arg 1 = OM_EMIT_ACTIVE, 0 = OM_EMIT_SILENT.

    THAT THE EMISSION WAS APPLIED IS NOT OBSERVABLE THROUGH THE PIPE TODAY (FINDING-emission): the per-unit flag lives in
    fog.c `st->emit[]`, which is neither saved nor hashed (fog.c:206, the fog section ignores it), and its only reader scales the
    cross-layer sight factor by OM_TP_EMIT_SIGHT_MULT and OM_TP_EMIT_SEEN_MULT, which default to 1.0, so no frame, checksum or
    `visible[]` changes. Replacing the apply call at cmd_stream.c:252 with `(void)0;` leaves this test green. Lane T D2 makes the
    effect visible; the visible assertion belongs to it.

    What this test pins: through tests/net/driver.py (start_mission, PipeBackend) `net_submit` verb 5 on three units for tick 2
    answers code 0, `net_step` runs past it, and `net_log_dump` holds that entry (verb 5, arg 1, tick 2, the three ids); the
    toggle back (arg 0, tick 4) is a second entry; the tactical frame's `economy` is the same before and after (no resource
    cost) and no unit lost hp.

    Positive control (scratch break, reverted and rebuilt): csrc/cmd_stream.c:35 `#define OM_CMD_VERB_LAST
    OM_NET_VERB_ASSIGN_COMMANDER` changed to `OM_NET_VERB_SET_LAYER` (verbs 5 and above are malformed), `make -B`. Red:
    `assert backend.submit(emit_on) == 0` (CONTROL-EMISSION-RESULT)."""
    driver = _load_driver()
    pipe = driver.Pipe()
    try:
        info = driver.start_mission(pipe, 5)
        backend = driver.PipeBackend(pipe)
        group = info["mine"][:3]
        pipe.cmd("tactical_step", n=0, full=True)
        before = pipe.read_more()
        emit_on, emit_off = net_command(2, 5, group, arg=1), net_command(4, 5, group, arg=0, seq=1)
        assert backend.submit(emit_on) == 0
        assert backend.step(3)["tick"] == 3
        assert backend.submit(emit_off) == 0
        assert backend.step(3)["tick"] == 6
        log = pipe.send("net_log_dump")
        assert log["type"] == "net_log", log
        entries = log_entries(log["hex"])
        assert [(e["tick"], e["verb"], e["arg"], e["units"]) for e in entries] == [(2, 5, 1, group), (4, 5, 0, group)], entries
        pipe.cmd("tactical_step", n=0, full=True)
        after = pipe.read_more()
        assert after["economy"] == before["economy"]
        hp = {u["id"]: u["hp"] for u in before["units"]}
        assert all(u["hp"] >= hp[u["id"]] for u in after["units"] if u["id"] in hp and u["faction"] == 0)
    finally:
        pipe.close()


def test_net_submit_ping_verb_reveals_the_enemy():
    """R-162-01 through the lockstep path: csrc/ouroboros_sim.h OM_NET_VERB_PING = 6, applied by csrc/cmd_stream.c apply_one
    to the first listed unit (`om_command_ping(w, ids[0], layer, x, y)`). Through tests/net/driver.py: the mission's player
    units move for 3000 net steps (verb 0), the nearest enemy sits outside passive sight, a verb 6 submit for the next tick
    answers code 0, the step runs it and `visible[0]` then holds that enemy; `net_log_dump` carries the entry with verb 6 and
    the layer. The alert (R-162-03) is off and no frame carries it.

    Positive control (scratch break, reverted and rebuilt): csrc/cmd_stream.c:253
    `case OM_NET_VERB_PING: om_command_ping(w, ids[0], c->layer, c->x, c->y); break;` changed to `case OM_NET_VERB_PING: break;`.
    Red: `assert target in after["visible"]["0"]` (CONTROL-NETPING-RESULT)."""
    driver = _load_driver()
    pipe = driver.Pipe()
    try:
        info = driver.start_mission(pipe, 5)
        backend = driver.PipeBackend(pipe)
        assert backend.submit(net_command(1, 0, info["mine"], x=8000.0, y=12000.0)) == 0
        assert backend.step(APPROACH_STEPS)["tick"] == APPROACH_STEPS
        pipe.cmd("tactical_step", n=0, full=True)
        before = pipe.read_more()
        caster, target, x, y, layer, distance = pick_ping_pair(before)
        assert 800.0 < distance <= PING_REACH, distance
        assert not (set(before["visible"]["0"]) & enemy_ids(before))
        assert backend.submit(net_command(APPROACH_STEPS + 1, 6, [caster], layer=layer, x=x, y=y, seq=1)) == 0
        assert backend.step(1)["tick"] == APPROACH_STEPS + 1
        pipe.cmd("tactical_step", n=0, full=True)
        after = pipe.read_more()
        assert target in after["visible"]["0"]
        assert not any("alert" in k for k in after)
        entries = log_entries(pipe.send("net_log_dump")["hex"])
        assert [(e["verb"], e["layer"], e["units"]) for e in entries[-1:]] == [(6, layer, [caster])], entries
    finally:
        pipe.close()


# U0 RETIRES THIS TEST (FINDING-pipe-hold-verb): the hold verb is removed from architecture.md and from the handler.
def test_command_hold_always_answers_error_today():
    """R-096-06: any command other than the supported verbs (patrol, hold, stop, follow) is rejected with a reason and no
    state changes. csrc/pipe/om_pipe.c handle_command's `hold` branch (no om_command_hold symbol exists) always answers
    `error` `hold not supported: no om_command_hold symbol`.

    U0 RETIRES THIS TEST (FINDING-pipe-hold-verb): the U0 piece removes the `hold` verb from docs/architecture.md and the
    handler branch as never built; after it the verb answers `unknown verb` and this test is deleted or rewritten with the
    ledger row of U0.

    What shows: in a begun mission, `command` `hold` for a real unit answers the error with that reason and the unit's
    position and the tick are unchanged after a step; before mission_begin it answers `not begun` (the recon guard fires
    first).

    Positive control (scratch break, reverted and rebuilt): csrc/pipe/om_pipe.c:1612 `write_error("command", "hold not
    supported: no om_command_hold symbol");` changed to `write_error("command", "held");`, `make pipe/ouroboros_pipe`. Red:
    `assert (answer["type"], answer["reason"]) == ("error", HOLD_REASON)` (CONTROL-HOLD-VERB-RESULT)."""
    HOLD_REASON = "hold not supported: no om_command_hold symbol"
    mine = seed5_player_ids()
    frames = run([set_seed(5), start(), BEGIN, FULL, cmd("command", verb="hold", units=mine[:1], x=1.0, y=1.0), FULL])
    answer = next(f for f in frames if f.get("name") == "command")
    assert (answer["type"], answer["reason"]) == ("error", HOLD_REASON), answer
    first, second = of_type(frames, "tactical")[-2:]
    assert {u["id"]: (u["x"], u["y"]) for u in first["units"]} == {u["id"]: (u["x"], u["y"]) for u in second["units"]}
    recon = run([set_seed(5), start(), cmd("command", verb="hold", units=mine[:1])])
    assert [(f["type"], f["reason"]) for f in recon if f.get("name") == "command"] == [("error", "not begun")]
