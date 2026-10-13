"""Sim-lane scout B: verify the SOURCE of the chronicle (ROADMAP 2b step 1, part 2).

A jump is one pipe verb and streams no deltas, so each jump is replayed in a second
pipe process: `save` just before the jump, then a fresh process loads the save and
`step`s the same number of ticks (the jump's om_world_step loop is the same loop), and
the deltas it streams are the independent record of what happened. The replay is
accepted only if its ownership timeline equals the chronicle frame's `ownership`
snapshots; otherwise the jump is reported REPLAY and skipped by every other check.

Run (from the worktree root):
  .venv python -m scripts.simlane.chronicle_source --seeds 1-10 --out OUTDIR
Tooling only, never in the game loop. Reads the sim, changes nothing in it.
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.simviewer.pipe_session import PipeSession, PipeError  # noqa: E402

FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
N_REGIONS = 80  # 60 fails generation (below the feasible minimum, viewer spec pre-flight 8)
STRIDE = 2  # OM_OWNERSHIP_TIMELINE_STRIDE

# csrc/events.c TID_* order (names) and csrc/generational.c GEN_LAUNCH_EVENT_TIER
TEMPLATES = [
    "Garrison Collapse", "Border Incursion", "Emergency Levy", "Regional Revolt", "Revolt Crushed",
    "Revolt Entrenched", "Trade Boom", "Prosperity Unrest", "Population Crisis", "Resistance Movement",
    "Conquest Unrest", "Labor Shortage", "Immigration Wave", "Infrastructure Decay", "Military Buildup",
    "War Weariness", "Cultural Renaissance", "Famine", "Famine Relief", "Diplomatic Incident",
    "Harvest Surplus", "Admin Separatist", "Admin Political Crisis", "Admin Popular Support",
    "Admin Military Defection", "Admin Breakaway",
]
TIERS = [4, 4, 3, 4, 3, 5, 3, 2, 4, 3, 4, 3, 2, 3, 3, 3, 2, 4, 3, 2, 2, 5, 5, 5, 5, 6]
CREATES_FACTION_TEMPLATES = {"Admin Separatist", "Admin Breakaway"}  # informational only

# om_mission_band: 0 total_failure 1 partial_failure 2 partial_success 3 strong_success
# 4 total_success 5 refusal.  R-065-02 (Westley 2026-10-01) -> consequence category
BAND_TO_OUTCOME = {0: 1, 1: 2, 2: 2, 3: 0, 4: 0, 5: 1}  # 0 success 1 failure 2 mixed
OUTCOME_NAME = {0: "success", 1: "failure", 2: "mixed", 3: "ripple"}
CAT_NAME = {0: "lineage_succession", 1: "lineage_military_action", 2: "lineage_thrived",
            3: "lineage_suffered", 4: "lineage_quiet", 10: "chain_revolt_spawned",
            11: "chain_expansion", 12: "chain_cascade", 13: "chain_conflict_victory",
            14: "chain_conflict_defeat", 15: "chain_conflict_stalemate",
            16: "chain_crisis_resolved_well", 17: "chain_crisis_resolved_badly",
            20: "regional_faction_shift", 21: "regional_growth", 22: "regional_decline",
            23: "regional_stable"}
CTYPE = {0: "consequence", 1: "lineage", 2: "chain", 3: "regional"}


def tmpl(i):
    return TEMPLATES[i] if 0 <= i < len(TEMPLATES) else "?%d" % i


def tier(i):
    return TIERS[i] if 0 <= i < len(TIERS) else 2


def event_base(ev):
    dsum = sum(abs(x) for x in ev["delta"])
    return tier(ev["template"]) + min(dsum / 50.0, 3.0)


# ---------------------------------------------------------------- driving
def seed_session(seed, new_campaign=True):
    s = PipeSession()
    kw = dict(seed=seed, n_regions=N_REGIONS, features=FEATURES)
    if not new_campaign:
        kw["new_campaign"] = False
    s.send("set_seed", **kw)
    return s


def replay(seed, savepath, n):
    """Fresh process: load the pre-jump save, step n ticks, return (baseline snapshot, deltas)."""
    s = seed_session(seed, new_campaign=False)
    try:
        base = s.send("load", path=str(savepath))[0]
        frames = s.send("step", n=n)
        return base, [f for f in frames if f["type"] == "delta"]
    finally:
        s.close()


def do_mission(s, how, log):
    """how: ('end', completion) or ('refuse',). Returns dict(band, region, archetype) or None."""
    try:
        m = s.send("mission_start", faction=0, era_kind=0)[0]
    except PipeError as e:
        log.append(("mission_start error", e.frame))
        return None
    info = dict(region=m["region"], archetype=m["archetype"], quiet_world=m.get("quiet_world"),
                how=how[0])
    try:
        if how[0] == "refuse":
            d = s.send("mission_refuse")[0]
        else:
            s.send("objective_complete", objective=0, completion=how[1])
            d = s.send("mission_end")[0]
    except PipeError as e:
        log.append(("mission verb error", e.frame))
        return None
    info["band"] = d["band"]
    info["requested_completion"] = how[1] if how[0] == "end" else None
    return info


def run_jump(s, seed, label, n, mission, workdir, log):
    snap0 = s.send("snapshot")[0]
    savepath = Path(workdir) / ("seed%d_%s.omsave" % (seed, label))
    s.send("save", path=str(savepath))
    chron, snap1 = s.send("jump", ticks=n)
    base, deltas = replay(seed, savepath, n)
    return dict(seed=seed, label=label, n=n, mission=mission, pre=snap0, post=snap1,
                chron=chron, base=base, deltas=deltas)


def run_seed(seed, workdir, with_cycles):
    log = []
    s = seed_session(seed)
    jumps = []
    step_deltas = []
    try:
        # ticks run with `step` (the brief's collected delta stream), kept for totals
        step_deltas += [f for f in s.send("step", n=30) if f["type"] == "delta"]
        jumps.append(run_jump(s, seed, "j1_nomission", 50, None, workdir, log))
        m1 = do_mission(s, ("end", 1.0), log)
        jumps.append(run_jump(s, seed, "j2_after_m1", 50, m1, workdir, log))
        jumps.append(run_jump(s, seed, "j3_nomission", 20, None, workdir, log))
        m2 = do_mission(s, ("end", 0.4), log)
        jumps.append(run_jump(s, seed, "j4_after_m2", 100, m2, workdir, log))
        m3 = do_mission(s, ("refuse",), log)
        jumps.append(run_jump(s, seed, "j5_after_refuse", 50, m3, workdir, log))
        step_deltas += [f for f in s.send("step", n=15) if f["type"] == "delta"]
        jumps.append(run_jump(s, seed, "j6_nomission", 50, None, workdir, log))
        for k, comp in enumerate([0.0, 0.2, 0.6, 0.85]):  # reach the other bands of R-065-02
            mk = do_mission(s, ("end", comp), log)
            jumps.append(run_jump(s, seed, "j%d_after_m_c%02d" % (7 + k, int(comp * 100)), 20, mk, workdir, log))
        for c in range(with_cycles):  # long campaign: chapter / lineage / entry-count observation
            mi = do_mission(s, ("end", 1.0), log)
            if mi is None:
                break
            jumps.append(run_jump(s, seed, "c%02d" % (c + 1), 50, mi, workdir, log))
    finally:
        s.close()
    return dict(seed=seed, jumps=jumps, step_deltas=step_deltas, log=log)


# ---------------------------------------------------------------- oracle
class Rec:
    pass


def build_oracle(j):
    """Independent record of the jump from the replayed deltas."""
    ch = j["chron"]
    frm, to = ch["jump"]["from_tick"], ch["jump"]["to_tick"]
    owner = {r["i"]: r["owner"] for r in j["base"]["regions"]}
    start_owner = dict(owner)
    own_by_tick = {frm: dict(owner)}
    events, attacks, collisions, revolts = [], [], [], []
    owner_changes = []  # (tick, region, old, new)
    for d in j["deltas"]:
        t = d["tick"]
        for r in d["regions"]:
            if owner.get(r["i"]) != r["owner"]:
                owner_changes.append((t, r["i"], owner.get(r["i"]), r["owner"]))
                owner[r["i"]] = r["owner"]
        own_by_tick[t] = dict(owner)
        for e in d["events"]:
            events.append(e)
        for a in d["attacks"]:
            attacks.append(dict(a, tick=t))
        for c in d["collisions"]:
            collisions.append(dict(c, tick=t))
        for rv in d["revolts"]:
            revolts.append(dict(rv, tick=t))
    o = Rec()
    o.frm, o.to = frm, to
    o.start_owner, o.end_owner = start_owner, dict(owner)
    o.own_by_tick = own_by_tick
    o.events, o.attacks, o.collisions, o.revolts = events, attacks, collisions, revolts
    o.owner_changes = owner_changes
    return o


def replay_ok(j, o):
    snaps = j["chron"].get("ownership", {}).get("snapshots", [])
    if not snaps:
        return False, "no ownership timeline"
    for k, row in enumerate(snaps):
        t = o.frm + STRIDE * k
        mine = o.own_by_tick.get(t)
        if mine is None:
            return False, "tick %d not replayed" % t
        theirs = {i: v for i, v in enumerate(row)}
        if mine != theirs:
            diff = [i for i in theirs if theirs[i] != mine.get(i)]
            return False, "ownership differs at tick %d regions %s" % (t, diff[:5])
    return True, ""


# ---------------------------------------------------------------- checks
class Findings:
    def __init__(self):
        self.rows = []          # every mismatch occurrence
        self.counts = Counter()  # passes and totals

    def bad(self, code, seed, label, tick, msg, **kw):
        self.rows.append(dict(code=code, seed=seed, jump=label, tick=tick, msg=msg, **kw))

    def ok(self, key, n=1):
        self.counts[key] += n


def chains_of(o):
    ch = defaultdict(list)
    for e in o.events:
        if e["chain"] > 0:
            ch[e["chain"]].append(e)
    return ch


def rule_chain_category(evs):
    names = [tmpl(e["template"]).lower() for e in evs]
    mil = sum(e["delta"][0] for e in evs)
    eco = sum(e["delta"][1] for e in evs)
    ten = sum(e["delta"][2] for e in evs)
    if any("revolt" in n for n in names):
        return 10
    if any("expansion" in n or "coloniz" in n for n in names):
        return 11
    if len(evs) >= 4:
        return 12
    if mil > 2 and ten < 3:
        return 13
    if mil < -2 and ten > 3:
        return 14
    if abs(mil) <= 2 and ten > 2:
        return 15
    if eco > 0 and ten <= 0:
        return 16
    return 17


def code_chain_category(evs):
    """csrc/chronicle.c chron_categorize_chain_cluster as called from generational.c: the
    template of the chain's FIRST event, strstr case-sensitive on the Title Case name."""
    name = tmpl(evs[0]["template"])
    mil = sum(e["delta"][0] for e in evs)
    eco = sum(e["delta"][1] for e in evs)
    ten = sum(e["delta"][2] for e in evs)
    if "revolt" in name:
        return 10
    if "expansion" in name or "coloniz" in name:
        return 11
    if len(evs) >= 4:
        return 12
    if mil > 2 and ten < 3:
        return 13
    if mil < -2 and ten > 3:
        return 14
    if abs(mil) <= 2 and ten > 2:
        return 15
    if eco > 0 and ten <= 0:
        return 16
    return 17


def m_present(j):
    return j["mission"] is not None


def check_jump(j, F, stats):
    seed, label = j["seed"], j["label"]
    ch = j["chron"]
    entries = ch["entries"]
    frm, to = ch["jump"]["from_tick"], ch["jump"]["to_tick"]
    o = build_oracle(j)
    ok, why = replay_ok(j, o)
    stats["jumps"] += 1
    stats["entries"] += len(entries)
    stats["events"] += len(o.events)
    stats["attacks"] += len(o.attacks)
    stats["collisions"] += len(o.collisions)
    stats["revolts"] += len(o.revolts)
    stats["owner_changes"] += len(o.owner_changes)
    stats["conquests"] += sum(1 for a in o.attacks if a.get("conquest"))
    if not ok:
        F.bad("REPLAY", seed, label, frm, "replay does not reproduce the jump: " + why)
        return
    F.ok("replay_ok")
    n = len(entries)
    types = Counter(e["cluster_type"] for e in entries)
    for e in entries:
        stats["by_type_%s" % CTYPE[e["cluster_type"]]] += 1
        stats["by_cat_%s" % (CAT_NAME.get(e["category"]) if e["cluster_type"] != 0
                             else "consequence_" + OUTCOME_NAME[e["category"]])] += 1
    region_of = lambda e: e["refs"]["regions"][0]

    # R-055-06: the chapter number advances once per jump that follows a mission, never otherwise
    adv = j["post"]["chapter"] - j["pre"]["chapter"]
    if adv != (1 if m_present(j) else 0):
        F.bad("CHAPTER_ADVANCE", seed, label, frm, "chapter %d -> %d after a jump %s a mission" %
              (j["pre"]["chapter"], j["post"]["chapter"], "following" if m_present(j) else "with no"))
    else:
        F.ok("chapter_advance_ok")
    # R-065-01 count
    if n > 10:
        F.bad("COUNT_GT10", seed, label, frm, "%d entries (max 10)" % n, n=n)
    else:
        F.ok("count_le_10")
    if n < 5:
        F.bad("COUNT_LT5", seed, label, frm, "%d entries (min 5 unless the cap forbids)" % n, n=n)
    else:
        F.ok("count_ge_5")

    # R-065-05 category cap among the non-consequence non-lineage entries
    cc = Counter(e["category"] for e in entries if e["cluster_type"] in (2, 3))
    over = {c: k for c, k in cc.items() if k > 2}
    if over:
        F.bad("CAT_CAP", seed, label, frm, "category count over 2: %s" % over)
    else:
        F.ok("cat_cap_ok")

    # lineage presence / count (R-065-03/04, Q-070-01 b)
    nl = types[1]
    stats["lineage_entries_hist_%d" % nl] += 1
    if nl == 0:
        F.bad("NO_LINEAGE", seed, label, frm, "no lineage entry (R-065-03/04 require one)")
    else:
        F.ok("lineage_present")
    if nl > 2:
        F.bad("LINEAGE_GT2", seed, label, frm, "%d lineage entries (Q-070-01 b caps at 2)" % nl, n=nl)

    # consequence (R-065-02)
    cons = [e for e in entries if e["cluster_type"] == 0 and e["category"] < 3]
    ripples = [e for e in entries if e["cluster_type"] == 0 and e["category"] == 3]
    m = j["mission"]
    if m is None:
        if cons or ripples:
            F.bad("CONS_NO_MISSION", seed, label, frm, "consequence entries with no mission since the last jump")
        else:
            F.ok("no_cons_when_no_mission")
    else:
        exp = BAND_TO_OUTCOME[m["band"]]
        stats["mission_band_%d" % m["band"]] += 1
        if len(cons) != 1:
            F.bad("CONS_COUNT", seed, label, frm, "%d consequence entries after a mission (expected 1)" % len(cons))
        else:
            c = cons[0]
            if c["category"] != exp:
                F.bad("CONS_MAP", seed, label, frm,
                      "band %d (%s) expected consequence_%s, entry is consequence_%s" %
                      (m["band"], "refusal" if m["band"] == 5 else "played", OUTCOME_NAME[exp],
                       OUTCOME_NAME[c["category"]]), band=m["band"], how=m["how"])
            else:
                F.ok("cons_map_ok_band%d" % m["band"])
            if region_of(c) != m["region"]:
                F.bad("CONS_REGION", seed, label, frm, "consequence region %d, mission region %d" %
                      (region_of(c), m["region"]))
            else:
                F.ok("cons_region_ok")
            if cons[0] is not entries[0]:
                F.bad("CONS_ORDER", seed, label, frm, "consequence entry is not entry 1 (id %d)" % c["id"])
            else:
                F.ok("cons_first")
        # ripple: adjacent to the mission region with a fired event
        adj = set()
        for e in j["pre"]["edges"]:
            if e["a"] == m["region"]:
                adj.add(e["b"])
            if e["b"] == m["region"]:
                adj.add(e["a"])
        ev_regions = {e["region"] for e in o.events}
        exp_ripple = adj & ev_regions
        got = {region_of(r) for r in ripples}
        if got != exp_ripple:
            F.bad("RIPPLE_SET", seed, label, frm, "ripple regions %s, adjacent regions with an event %s" %
                  (sorted(got), sorted(exp_ripple)))
        else:
            F.ok("ripple_set_ok")
        stats["ripple_entries"] += len(ripples)
        # events flagged as mission consequences: the sim sends no flag
        for r in ripples:
            if not any(ev["region"] == region_of(r) for ev in o.events):
                F.bad("RIPPLE_NO_EVENT", seed, label, frm, "ripple entry region %d has no event" % region_of(r))

    # per-entry checks
    ev_by_region = defaultdict(list)
    for e in o.events:
        ev_by_region[e["region"]].append(e)
    changed = {c[1] for c in o.owner_changes if o.start_owner[c[1]] != o.end_owner[c[1]]}
    revolt_regions = {r["region"] for r in o.revolts}
    chains = chains_of(o)
    mission_region = m["region"] if m else None

    reg_by_region = defaultdict(list)
    for e in entries:
        if e["cluster_type"] == 3:
            reg_by_region[region_of(e)].append(e)
    for r, es in reg_by_region.items():
        if len(es) > 1:
            F.bad("REGION_DUP", seed, label, frm,
                  "region %d has %d regional entries (%s); R-067-05 says one regional cluster per region" %
                  (r, len(es), ",".join(CAT_NAME[x["category"]] for x in es)))
        else:
            F.ok("region_single")

    chain_entries = [e for e in entries if e["cluster_type"] == 2]
    code_cats = sorted(code_chain_category(v) for v in chains.values())
    rule_cats = sorted(rule_chain_category(v) for v in chains.values())
    stats["chains_in_window"] += len(chains)
    stats["chain_events"] += sum(len(v) for v in chains.values())
    stats["chains_with_revolt_template"] += sum(
        1 for v in chains.values() if any("revolt" in tmpl(e["template"]).lower() for e in v))
    if len(chains) > 32:
        F.bad("CHAIN_CAP32", seed, label, frm, "%d chains, generational.c keeps 32" % len(chains))
    for e in chain_entries:
        evs = None
        # a chain entry is anchored on the region of the chain's first event
        cands = [v for v in chains.values() if v[0]["region"] == region_of(e)]
        if not cands:
            F.bad("CHAIN_NO_SOURCE", seed, label, frm,
                  "chain entry (cat %s, region %d) has no chain whose first event is in that region" %
                  (CAT_NAME.get(e["category"]), region_of(e)))
            continue
        F.ok("chain_has_source")
        rc = {rule_chain_category(v) for v in cands}
        cc_ = {code_chain_category(v) for v in cands}
        if e["category"] in rc:
            F.ok("chain_cat_matches_rule")
        else:
            F.bad("CHAIN_CAT_RULE", seed, label, frm,
                  "chain entry region %d category %s; R-067-04 on that region's chain(s) gives %s" %
                  (region_of(e), CAT_NAME.get(e["category"]), sorted(CAT_NAME[x] for x in rc)))
        if e["category"] not in cc_:
            F.bad("CHAIN_CAT_CODE_ORACLE", seed, label, frm,
                  "oracle model of chronicle.c disagrees (model bug?) region %d" % region_of(e))
    # rule says each chain tag is a chain cluster; entries absent
    stats["chain_entries_out"] += len(chain_entries)
    # chains whose rule category is revolt_spawned: does any entry carry cat 10?
    n_rule_revolt = sum(1 for c in rule_cats if c == 10)
    n_entry_revolt = sum(1 for e in chain_entries if e["category"] == 10)
    stats["rule_cat10_chains"] += n_rule_revolt
    stats["entry_cat10"] += n_entry_revolt
    for e in chain_entries:
        stats["chain_entry_cat_%s" % CAT_NAME.get(e["category"])] += 1
    stats["chain_cats_code_model"] += 0

    window_full = lambda e: e["start_tick"] == frm and e["end_tick"] == to
    for e in entries:
        t = e["cluster_type"]
        r = region_of(e)
        # tick range vs source
        src = ev_by_region.get(r, [])
        if t == 3 and src:
            lo, hi = min(x["tick"] for x in src), max(x["tick"] for x in src)
            if not (e["start_tick"] <= lo and hi <= e["end_tick"]):
                F.bad("TICK_CONTRADICT", seed, label, lo,
                      "regional entry %d range %d-%d excludes its events %d-%d" %
                      (e["id"], e["start_tick"], e["end_tick"], lo, hi))
            elif window_full(e) and (hi - lo) < (to - frm):
                stats["range_whole_window_but_events_narrower"] += 1
        if t == 2:
            cands = [v for v in chains.values() if v[0]["region"] == r]
            if cands:
                lo = min(x["tick"] for v in cands for x in v)
                hi = max(x["tick"] for v in cands for x in v)
                if window_full(e) and (hi - lo) < (to - frm):
                    stats["range_whole_window_but_events_narrower"] += 1
        stats["entries_with_full_window_range"] += 1 if window_full(e) else 0
        if e["start_tick"] < frm or e["end_tick"] > to:
            F.bad("TICK_OUTSIDE_JUMP", seed, label, frm, "entry %d range %d-%d outside jump %d-%d" %
                  (e["id"], e["start_tick"], e["end_tick"], frm, to))
        # no event behind it
        if t == 3:
            backed = bool(src) or r in changed or r in revolt_regions
            if not backed:
                F.bad("NO_EVENT_BEHIND", seed, label, frm,
                      "regional entry %d (%s, region %d) has no event, ownership change or revolt in %d-%d" %
                      (e["id"], CAT_NAME[e["category"]], r, frm, to),
                      significance=e["significance"], category=CAT_NAME[e["category"]])
            else:
                F.ok("regional_backed")
            # category vs R-067-05
            has_shift = (r in changed) or (r in revolt_regions) or any(
                tmpl(x["template"]) in CREATES_FACTION_TEMPLATES or x.get("creates_faction") for x in src)
            net_all = sum(x["delta"][1] + x["delta"][3] for x in src)
            net_nochain = sum(x["delta"][1] + x["delta"][3] for x in src if x["chain"] <= 0)
            if has_shift:
                rc = 20
            else:
                nn = net_nochain
                rc = 21 if nn > 3 else 22 if nn < -3 else 23
            if e["category"] != rc and not (e["category"] == 23 and rc in (21, 22)):
                # the stable twin of a growth/decline region is reported under REGION_DUP; flag others
                F.bad("REGIONAL_CAT", seed, label, frm,
                      "regional entry %d region %d is %s, R-067-05 gives %s (net eco+pop %.1f, no-chain %.1f, "
                      "changed=%s revolt=%s)" % (e["id"], r, CAT_NAME[e["category"]], CAT_NAME[rc],
                                                  net_all, net_nochain, r in changed, r in revolt_regions))
            elif e["category"] == 23 and rc in (21, 22):
                F.bad("REGIONAL_STABLE_TWIN", seed, label, frm,
                      "region %d carries a regional_stable entry although R-067-05 gives %s" %
                      (r, CAT_NAME[rc]))
            else:
                F.ok("regional_cat_ok")
            # significance (R-066-01/02/05): code uses base * (1 + .8 lineage) only
            if src or r in changed:
                cand = [event_base(x) for x in src] + ([4.0] if r in changed else [])
                base = max(cand)
                sig = e["significance"]
                # events are scored mid-jump, the ownership-change term after the descendants are
                # generated, so each source may carry its own lineage factor (oracle limit)
                ok_lin = any(abs(sig - b * k) < 1e-6 for b in cand for k in (1.0, 1.8))
                # R-066-02 full context (mission region .5, chain>1 .1*min(L,5)), character unknown
                rule_mult_min = 1.0 + (0.5 if r == mission_region else 0.0)
                best = 0.0
                for x in src:
                    cl = 0
                    if x["chain"] > 0:
                        cl = len(chains.get(x["chain"], []))
                    mult = 1.0 + (0.5 if r == mission_region else 0.0) + (0.1 * min(cl, 5) if cl > 1 else 0.0)
                    best = max(best, event_base(x) * mult)
                if r in changed:
                    best = max(best, 4.0 * rule_mult_min)
                if not ok_lin:
                    F.bad("SIG_FORMULA", seed, label, frm,
                          "regional entry %d region %d significance %.3f; max event base %.3f x {1.0,1.8} "
                          "does not give it" % (e["id"], r, sig, base))
                else:
                    F.ok("sig_matches_base_x_lineage")
                if best > sig * 1.8 - 1e-9 and best > max(base, base * 1.8) + 1e-6:
                    # R-066-02 terms the sim never applies (mission region / chain length) would raise it
                    stats["sig_below_rule_context"] += 1
                    F.bad("SIG_CONTEXT_MISSING", seed, label, frm,
                          "region %d reported %.3f; R-066-02 mission-region/chain terms alone give >= %.3f" %
                          (r, sig, best))
                elif best > base * 1.8 + 1e-6:
                    stats["sig_below_rule_context"] += 1
        if t in (0, 1, 2) and e["significance"] == 0.0:
            stats["zero_significance_%s" % CTYPE[t]] += 1


    # ranking audit (R-065-05): rebuild the regional candidates the way generational.c feeds them
    # (one stable-or-shift cluster per active region, plus a growth/decline twin when the owner did not
    # change) and check the selection against the entries the frame actually carries. Lineage factor
    # unknown over the pipe, so the missed candidate's score is the lower bound (base, factor 1.0).
    sel = [e for e in entries if e["cluster_type"] in (2, 3)]
    sel_by_cat = Counter(e["category"] for e in sel)
    cand = []
    for r, evs in ev_by_region.items():
        base_r = max(event_base(x) for x in evs)
        if r in changed:
            base_r = max(base_r, 4.0)
        cand.append((r, 20 if r in changed else 23, base_r))
        net = sum(x["delta"][1] + x["delta"][3] for x in evs)
        if r not in changed and (net > 3.0 or net < -3.0):
            cand.append((r, 21 if net > 3.0 else 22, base_r))
    for r in changed - set(ev_by_region):
        cand.append((r, 20, 4.0))
    for r, cat_, lo_score in cand:
        if any(region_of(e) == r and e["category"] == cat_ for e in sel if e["cluster_type"] == 3):
            F.ok("rank_candidate_selected")
            continue
        worse = [e for e in sel if e["significance"] < lo_score - 1e-6
                 and (sel_by_cat[cat_] < 2 or e["category"] == cat_)]
        if worse:
            w_ = min(worse, key=lambda e: e["significance"])
            F.bad("RANK_VIOLATION", seed, label, frm,
                  "candidate region %d cat %s score>=%.2f not selected (cat count %d, budget %d) while entry %d "
                  "(%s region %d, significance %.2f) was" % (r, CAT_NAME[cat_], lo_score, sel_by_cat[cat_], n,
                                                              w_["id"], CAT_NAME[w_["category"]], region_of(w_),
                                                              w_["significance"]))
        else:
            F.ok("rank_skip_justified")

    # tier-5+ events and conquests with no entry (permitted only if the budget/cap forced it)
    entry_regions = {region_of(e) for e in entries}
    n_ent = len(entries)
    for tk, r in sorted({(e["tick"], e["region"]) for e in o.events if tier(e["template"]) >= 5}):
        if r not in entry_regions:
            F.bad("T5_NO_ENTRY", seed, label, tk,
                  "tier>=5 event (%s) in region %d has no entry (entries: %d)" %
                  ([tmpl(e["template"]) for e in o.events if e["region"] == r and e["tick"] == tk][0], r, n_ent),
                  budget_full=(n_ent >= 10))
        else:
            F.ok("t5_event_has_entry")
    for r in sorted(changed):
        if r not in entry_regions:
            F.bad("OWNERCHANGE_NO_ENTRY", seed, label, frm,
                  "region %d changed owner (%s -> %s) with no entry (entries: %d)" %
                  (r, o.start_owner[r], o.end_owner[r], n_ent), budget_full=(n_ent >= 10))
        else:
            F.ok("owner_change_has_entry")
    flips = {c[1] for c in o.owner_changes} - changed
    for r in sorted(flips):
        F.bad("OWNER_FLIPPED_BACK", seed, label, frm,
              "region %d changed owner mid-jump and was back to %s by the end: no ownership-change cluster" %
              (r, o.end_owner[r]))
    cq = {a["target"] for a in o.attacks if a.get("conquest")}
    for r in sorted(cq - entry_regions):
        F.bad("CONQUEST_NO_ENTRY", seed, label, frm, "conquest of region %d has no entry (entries: %d)" %
              (r, n_ent), budget_full=(n_ent >= 10))
    for r in sorted(revolt_regions - entry_regions):
        F.bad("REVOLT_NO_ENTRY", seed, label, frm, "revolt in region %d has no entry (entries: %d)" %
              (r, n_ent), budget_full=(n_ent >= 10))
    stats["event_regions"] += len(ev_by_region)
    stats["event_regions_with_entry"] += sum(1 for r in ev_by_region if r in entry_regions)

    # text invariants
    for e in entries:
        txt = e["text"]
        if not txt:
            stats["ghost_%s" % (CAT_NAME.get(e["category"]) if e["cluster_type"] != 0 else "consequence_" + OUTCOME_NAME[e["category"]])] += 1
            F.bad("EMPTY_TEXT", seed, label, frm, "entry %d (%s/%s region %d) has empty text, fragments %s" %
                  (e["id"], CTYPE[e["cluster_type"]],
                   CAT_NAME.get(e["category"]) if e["cluster_type"] != 0 else "consequence_" + OUTCOME_NAME[e["category"]],
                   region_of(e), e["fragment_ids"]), ctype=e["cluster_type"], cat=e["category"])
        else:
            F.ok("text_nonempty")
        if any(ch_.isdigit() for ch_ in txt + e["expanded_text"]):
            F.bad("DIGIT_IN_TEXT", seed, label, frm, "entry %d text contains a digit: %r" % (e["id"], txt[:80]))
        if txt and e["fragment_ids"] == [-1, -1, -1] and not (e["cluster_type"] == 0 and e["category"] == 3):
            F.bad("TEXT_NO_FRAGMENT", seed, label, frm,
                  "entry %d has text but fragment_ids [-1,-1,-1] (type %s cat %s)" %
                  (e["id"], CTYPE[e["cluster_type"]], e["category"]))
    n_text = sum(1 for e in entries if e["text"])
    if n_text < 5:
        F.bad("VISIBLE_LT5", seed, label, frm, "%d of %d entries have text (R-065-01 minimum 5)" % (n_text, n), n=n_text)
    stats["entries_with_text"] += n_text

    # refs
    for e in entries:
        r = region_of(e)
        own = o.end_owner.get(r, -2)
        got = e["refs"]["factions"]
        if (got and got[0] != own) or (not got and own >= 0):
            F.bad("REF_FACTION", seed, label, frm, "entry %d region %d faction ref %s, owner at jump end %s" %
                  (e["id"], r, got, own))
        else:
            F.ok("faction_ref_is_end_owner")
        if e["cluster_type"] == 3 and r in changed and got and got[0] == o.start_owner[r]:
            F.bad("REF_STALE_OWNER", seed, label, frm, "entry %d region %d names the old owner" % (e["id"], r))

    # keyframes (R-069-05)
    kf = ch.get("keyframes", [])
    real_changes = sorted({(c[0], c[1]) for c in o.owner_changes})
    missing = [(t_, r_) for t_, r_ in real_changes if t_ not in kf]
    for t_, r_ in missing:
        F.bad("KEYFRAME_OWNER_CHANGE", seed, label, t_,
              "ownership change of region %d at tick %d has no keyframe" % (r_, t_))
    stats["owner_changes_total"] += len(real_changes)
    stats["owner_changes_keyframed"] += len(real_changes) - len(missing)
    for e in entries:
        if not any(e["start_tick"] <= k <= e["end_tick"] for k in kf):
            F.bad("KEYFRAME_ENTRY", seed, label, frm, "entry %d range %d-%d contains no keyframe (keyframes %s)" %
                  (e["id"], e["start_tick"], e["end_tick"], kf[:6]))
            break
    else:
        F.ok("entry_keyframes_ok")


# ---------------------------------------------------------------- report helpers
def summarise(F):
    by = defaultdict(list)
    for r in F.rows:
        by[r["code"]].append(r)
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1-10")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cycles", type=int, default=0, help="extra mission+jump cycles per seed (chapter observation)")
    a = ap.parse_args()
    lo, _, hi = a.seeds.partition("-")
    seeds = list(range(int(lo), int(hi or lo) + 1))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    F = Findings()
    stats = Counter()
    per_seed = {}
    cycles_all = {}
    for sd in seeds:
        r = run_seed(sd, out, a.cycles)
        st = Counter()
        sub = Findings()
        for j in r["jumps"]:
            check_jump(j, sub, st)
        F.rows += sub.rows
        F.counts.update(sub.counts)
        stats.update(st)
        per_seed[sd] = dict(
            jumps=len(r["jumps"]), entries=st["entries"], events=st["events"],
            attacks=st["attacks"], collisions=st["collisions"], revolts=st["revolts"],
            step_ticks=len(r["step_deltas"]), log=r["log"], findings=Counter(x["code"] for x in sub.rows))
        per_seed[sd]["findings"] = dict(per_seed[sd]["findings"])
        cycles_all[sd] = [dict(label=j["label"], chapter_before=j["pre"]["chapter"], chapter_after=j["post"]["chapter"],
                               commander_before=j["pre"]["commander"], commander_after=j["post"]["commander"],
                               lineage_before=j["pre"]["lineage"], lineage_after=j["post"]["lineage"],
                               player_faction_before=j["pre"]["player_faction"],
                               player_faction_after=j["post"]["player_faction"],
                               end_reason=j["chron"]["jump"]["chapter_end_reason"],
                               band=(j["mission"] or {}).get("band"), n_entries=len(j["chron"]["entries"]),
                               n_lineage_entries=sum(1 for e in j["chron"]["entries"] if e["cluster_type"] == 1))
                          for j in r["jumps"] if j["label"].startswith("c")]
        with open(out / ("seed%d_jumps.json" % sd), "w") as f:
            json.dump([dict(label=j["label"], mission=j["mission"], pre_tick=j["pre"]["tick"],
                            chron=j["chron"], events=[e for d in j["deltas"] for e in d["events"]])
                       for j in r["jumps"]], f)
        print("seed", sd, dict(per_seed[sd]["findings"]), "entries", st["entries"], "events", st["events"], flush=True)
    result = dict(per_seed=per_seed, stats=dict(stats), counts=dict(F.counts), rows=F.rows, cycles=cycles_all)
    with open(out / "result.json", "w") as f:
        json.dump(result, f, indent=1, default=str)
    by = summarise(F)
    print("TOTAL", {k: len(v) for k, v in sorted(by.items())})
    print("STATS", dict(stats))
    print("PASS", dict(F.counts))


if __name__ == "__main__":
    main()
