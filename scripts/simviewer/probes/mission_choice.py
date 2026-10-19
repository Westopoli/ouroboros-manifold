"""Mission-choice sweep (sim lane 2026-10-12, finding_mission_choice.md "Method"; rewritten from the scratch script).

Drives pipe/ouroboros_pipe_dbg through scripts.simviewer.pipe_session.PipeSession (set_seed, snapshot,
mission_start, objective_complete, mission_end with retention, jump 50; outcome bands rotated through
viewer.pick_to_inputs) and a shadow world over libouroboros_dbg.so that replays the same calls, because the
pipe does not expose the candidate pool. The shadow's state checksum must equal the pipe snapshot's before
every mission_start; a desync stops that seed and is logged.

Usage: python3 scripts/simviewer/probes/mission_choice.py --seeds 1-10 --missions 10 --out DIR
Writes DIR/rows.json (one row per candidate per mission), DIR/mission_summary.json and .md.
"""
import argparse
import collections
import ctypes as C
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
from scripts.simviewer.pipe_session import DEFAULT_FEATURES, JUMP_TICKS, PipeError, PipeSession  # noqa: E402
try:
    from scripts.simviewer.viewer import pick_to_inputs  # noqa: E402
except ImportError:  # the system python3 has no pygame; pick_to_inputs is pure, so stub the module for the import only
    from unittest import mock
    sys.modules["pygame"] = mock.MagicMock()
    from scripts.simviewer.viewer import pick_to_inputs  # noqa: E402

L = C.CDLL(str(ROOT / "libouroboros_dbg.so"))
vp, u32, i32, u64, dbl = C.c_void_p, C.c_uint32, C.c_int32, C.c_uint64, C.c_double
def sig(n, res, *args):
    f = getattr(L, n); f.restype = res; f.argtypes = list(args); return f
class Cand(C.Structure):
    _fields_ = [("region", u32), ("arch", u32), ("urgency", dbl), ("relevance", dbl), ("preference", dbl), ("score", dbl)]
class Tele(C.Structure):
    _fields_ = [("declared_tick", u64), ("attacker", i32), ("target", u32), ("source", u32), ("pad", u32), ("commit", dbl)]
class Rep(C.Structure):
    _fields_ = [("start_tick", u64), ("end_tick", u64)] + [(n, u32) for n in "jump_ticks terr births deaths conq colon revolts chron snaps".split()]
world_new = sig("om_world_new", vp, u32, u64); world_free = sig("om_world_free", None, vp)
set_feat = sig("om_world_set_feature", None, vp, C.c_int, C.c_int); gen = sig("om_world_generate", None, vp)
gen_ok = sig("om_world_generated", C.c_int, vp)
ev_load = sig("om_events_load_launch", None, vp); lib_load = sig("om_mission_load_launch_library", None, vp)
camp = sig("om_campaign_start", None, vp, u32); cksum = sig("om_world_get_state_checksum", u64, vp)
nreg = sig("om_region_count", u32, vp); owner = sig("om_region_owner", i32, vp, u32)
prev_owner = sig("om_region_previous_owner", i32, vp, u32)
field = sig("om_region_field", dbl, vp, u32, C.c_int); comp = sig("om_region_composite", dbl, vp, u32, C.c_int)
neigh = sig("om_region_neighbors", u32, vp, u32, C.POINTER(u32), u32)
stance = sig("om_faction_stance", C.c_int, vp, i32, i32); pf = sig("om_player_faction", i32, vp)
ptele = sig("om_pending_telegraphs", u32, vp, C.POINTER(Tele), u32)
ncand = sig("om_mission_candidates", u32, vp, C.POINTER(Cand), u32)
chosen_a = sig("om_mission_generator_chosen_archetype", i32, vp); chosen_r = sig("om_mission_generator_chosen_region", u32, vp)
refresh = sig("om_mission_refresh_context", None, vp, i32); mstart = sig("om_mission_start", u32, vp, i32)
jump = sig("om_time_jump_run", C.c_int, vp, u32, C.POINTER(Rep))
fb_region = sig("om_mission_fallback_region", u32, vp); fb_enemy = sig("om_mission_fallback_enemy", i32, vp, u32)
setup_fb = sig("om_mission_setup_fallback", None, vp, u32, i32); setup = sig("om_mission_setup", None, vp, u32, u32, C.c_int)
dep = sig("om_mission_get_deployed_force_count", u32, vp); epow = sig("om_mission_get_enemy_power", dbl, vp)
narch = sig("om_mission_archetype_count", u32, vp); setviable = sig("om_mission_set_candidate_viable", None, vp, u32, C.c_int)
sel_cand = sig("om_mission_select_candidate", u32, vp); build_obj = sig("om_mission_build_objectives", None, vp, u32)
set_comp = sig("om_mission_set_objective_completion", None, vp, u32, dbl); mend = sig("om_mission_end", None, vp)
nobj = sig("om_mission_objective_count", u32, vp)
ucount = sig("om_unit_count", u32, vp); ualive = sig("om_unit_alive", C.c_int, vp, u32); ufac = sig("om_unit_get_faction", i32, vp, u32)
utype = sig("om_unit_get_unit_type", i32, vp, u32); maxhp = sig("om_unit_profile_max_hp", dbl, vp, C.c_int); sethp = sig("om_unit_set_hp", None, vp, u32, dbl)
nlin = sig("om_lineage_count", u32, vp); linid = sig("om_lineage_id_at", u32, vp, u32)
linhist = sig("om_lineage_history_region", i32, vp, u32, u32); linmem = sig("om_lineage_member_in_region", C.c_int, vp, u32, u32)
camp_lin = sig("om_campaign_lineage", u32, vp); camp_cmd = sig("om_campaign_commander", u32, vp)
ARCH = ["defensive_stand","siege_breaking","reconquest","assault","suppression","multi_front_defense","interception","evacuation","containment","counterinsurgency"]
# om_mission_archetype ids per csrc/mission.c: read below from the pipe frame; names are listed in the sim's order.

def world_for(seed, n_regions=80):
    w = world_new(n_regions, seed)
    for f in DEFAULT_FEATURES: set_feat(w, f, 1)
    gen(w); ev_load(w); assert gen_ok(w); lib_load(w); camp(w, 1); return w

def shadow_mission_start(w, faction):
    mstart(w, faction)
    for r in range(nreg(w)): refresh(w, r)
    drawn = chosen_a(w)
    retry = 0
    while drawn < 0 and retry < 5:
        rep = Rep(); jump(w, 20, C.byref(rep))
        for r in range(nreg(w)): refresh(w, r)
        drawn = chosen_a(w); retry += 1
    region = arch = 0; have = 0; quiet = 0; gen_choice = (chosen_r(w), drawn) if drawn >= 0 else None; replaced = None
    if drawn < 0:
        region = fb_region(w); e = fb_enemy(w, region)
        if e >= 0: have = 1; quiet = 1; fbe = e
    elif drawn >= 0:
        region = chosen_r(w); arch = drawn; have = 1
    if not have:
        for a in range(narch(w)): setviable(w, a, 1)
        arch = sel_cand(w); p = pf(w)
        for i in range(nreg(w)):
            if owner(w, i) == p: region = i; have = 1; break
    if have:
        if quiet: setup_fb(w, region, fbe)
        else: setup(w, region, arch, 0)
        if dep(w) == 0 or epow(w) <= 0.0: have = 0; replaced = (dep(w), epow(w))
    if not have:
        p = pf(w)
        for a in range(narch(w)):
            if have: break
            for i in range(nreg(w)):
                if owner(w, i) != p: continue
                setup(w, i, a, 0)
                if dep(w) > 0 and epow(w) > 0.0: region, arch, have = i, a, 1; break
    if not have: return None
    build_obj(w, arch)
    return region, arch, quiet, retry, gen_choice, replaced

def get_pool(w):
    n = ncand(w, None, 100000); buf = (Cand * max(n, 1))(); ncand(w, buf, n)
    return [(c.region, c.arch, c.urgency, c.relevance, c.preference, c.score) for c in buf[:n]]

def recompute(w, region, arch, player):
    """Independent recomputation in Python of R-072-02/03/04/05 from the live world (same frame)."""
    mil, eco = field(w, region, 0), field(w, region, 1); stab = comp(w, region, 0)
    deficit = ((100 - mil) + (100 - eco) + (100 - stab)) / 300.0
    own = owner(w, region); nb = (u32 * 32)(); n = min(neigh(w, region, nb, 32), 32)
    maxm = 0.0; lost = 0
    for i in range(n):
        o = owner(w, nb[i])
        if o >= 0 and o != own and stance(w, own, o) == 0: maxm = max(maxm, field(w, nb[i], 0))
        if o >= 0 and o != player and prev_owner(w, nb[i]) == player: lost += 1
    tl = (Tele * 256)(); nt = min(ptele(w, tl, 256), 256)
    att = [t.commit for t in tl[:nt] if t.target == region]
    c = lambda x: max(0.0, min(1.0, x))
    border = c(maxm / 70.0); ap = c(0.5 * len(att) + sum(att) / 600.0); tloss = c(0.5 * lost)
    conflict = c(border + 0.5 * ap + 0.3 * tloss); chain = 0.0
    urg = c(0.4 * deficit + 0.4 * conflict + 0.2 * chain)
    # relevance (lineage = last lineage created; hops = BFS from its history[0])
    lin = 0.0; hops = 5; nl = nlin(w)
    if nl:
        lid = linid(w, nl - 1); inh = False; i = 0
        while linhist(w, lid, i) >= 0:
            if linhist(w, lid, i) == region: inh = True; break
            i += 1
        lin = 1.0 if linmem(w, lid, region) else (0.5 if inh else 0.0)
        home = linhist(w, lid, 0)
        if home >= 0:
            dist = {home: 0}; q = [home]
            while q:
                cur = q.pop(0)
                if cur == region: hops = dist[cur]; break
                if dist[cur] >= 5: continue
                nb2 = (u32 * 32)(); k = min(neigh(w, cur, nb2, 32), 32)
                for j in range(k):
                    if nb2[j] not in dist: dist[nb2[j]] = dist[cur] + 1; q.append(nb2[j])
    rel = c(0.4 * lin + 0.3 * (1 - min(hops, 5) / 5.0) + 0.3 * 0.0)
    pref = 0.5
    return dict(urg=urg, rel=rel, pref=pref, deficit=deficit, conflict=conflict, chain=chain, lin=lin, hops=hops,
                score=0.5 * urg + 0.3 * rel + 0.2 * pref, att=len(att), lost=lost, border=maxm, mil=mil, eco=eco, stab=stab)


def parse_seeds(text):
    if "-" in text:
        a, b = text.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in text.split(",")]


def arch_name(a):
    return ARCH[a] if 0 <= a < len(ARCH) else "arch%d" % a


def campaign(seed, n_missions, rows_out, log):
    """One seed. Appends candidate rows to rows_out and one record per mission to log."""
    sess = PipeSession()
    w = world_for(seed)
    out = dict(seed=seed, missions=0, ended=None)
    try:
        sess.send("set_seed", seed=seed, n_regions=80, features=DEFAULT_FEATURES)
        snap = sess.send("snapshot")[0]
        for m in range(n_missions):
            if snap["checksum"] != cksum(w):
                log.append(dict(kind="shadow_desync", seed=seed, mission=m, tick=snap["tick"]))
                out["ended"] = "shadow_desync"
                return out
            player = pf(w)
            pool = get_pool(w)
            tick = snap["tick"]
            recs = [(r, a, u, rl, p, s, recompute(w, r, a, player)) for r, a, u, rl, p, s in pool]
            try:
                fr = sess.send("mission_start", faction=0, era_kind=0)[0]
            except PipeError as e:
                out["ended"] = "mission_start error %s" % e.frame
                return out
            sh = shadow_mission_start(w, 0)
            pr, pa = fr["region"], fr["archetype"]
            if sh is None or (sh[0], sh[1]) != (pr, pa):
                log.append(dict(kind="shadow_mismatch", seed=seed, mission=m, tick=tick, pipe=[pr, pa], shadow=sh))
            drawn = sh[4] if sh else None
            order = sorted(range(len(recs)), key=lambda i: (-recs[i][5], i))
            rank = {i: k for k, i in enumerate(order)}
            for i, (r, a, u, rl, p, s, rc) in enumerate(recs):
                rows_out.append(dict(seed=seed, mission=m, tick=tick, region=r, archetype=a, archetype_name=arch_name(a),
                                     urgency=u, relevance=rl, preference=p, score=s, rank=rank[i],
                                     drawn=bool(drawn and (r, a) == tuple(drawn)), played=(r, a) == (pr, pa),
                                     recomputed=dict(urgency=rc["urg"], relevance=rc["rel"], preference=rc["pref"], score=rc["score"])))
            log.append(dict(kind="mission", seed=seed, mission=m, tick=tick, played=[pr, pa], drawn=list(drawn) if drawn else None,
                            quiet=fr["quiet_world"], pool_n=len(recs), retries=sh[3] if sh else None, replaced=sh[5] if sh else None))
            band = m % 5
            comp_, ret = pick_to_inputs(pa, band)
            for o in range(max(1, len(fr["objectives"]))):
                sess.send("objective_complete", objective=o, completion=comp_)
                set_comp(w, o, comp_)
            deb = sess.send("mission_end", retention=ret)
            for i in range(1, ucount(w) + 1):
                if ualive(w, i) and ufac(w, i) == pf(w):
                    sethp(w, i, ret * maxhp(w, utype(w, i)))
            mend(w)
            log[-1]["band_asked"] = band
            log[-1]["band_got"] = deb[0]["band"]
            out["missions"] += 1
            try:
                sess.send("jump", ticks=JUMP_TICKS)
            except PipeError as e:
                out["ended"] = "jump error %s" % e.frame
                return out
            rep = Rep()
            jump(w, JUMP_TICKS, C.byref(rep))
            snap = sess.send("snapshot")[0]
        return out
    finally:
        sess.close()
        world_free(w)


def summarise(outs, rows, log, seeds, missions):
    ms = [r for r in log if r["kind"] == "mission"]
    tol = 1e-9
    tot = collections.Counter()
    rank_hist = collections.Counter()
    swapped = []
    seen, played = set(), set()
    first_zero_rows = first_rows = first_zero_pools = 0
    max_urg = 0.0
    by_mission = collections.defaultdict(list)
    for r in rows:
        by_mission[(r["seed"], r["mission"])].append(r)
        seen.add(r["archetype"])
        max_urg = max(max_urg, r["urgency"])
        rc = r["recomputed"]
        for k in ("urgency", "relevance", "preference", "score"):
            if abs(rc[k] - r[k]) > tol:
                tot["recompute_mismatch_" + k] += 1
    for m in ms:
        pool = by_mission.get((m["seed"], m["mission"]), [])
        played.add(m["played"][1])
        d = [r for r in pool if r["drawn"]]
        if m["drawn"] is not None:
            tot["draws_checked"] += 1
            if d:
                tot["draw_in_pool"] += 1
                rk = d[0]["rank"]
                if rk < 5:
                    tot["draw_in_top5"] += 1
                rank_hist[rk] += 1
                if rk == 0:
                    tot["argmax"] += 1
        if m["drawn"] is not None and m["drawn"] != m["played"]:
            swapped.append(dict(seed=m["seed"], tick=m["tick"], mission=m["mission"], drawn=m["drawn"], played=m["played"], replaced=m["replaced"]))
        if m["mission"] == 0 and pool:
            first_rows += len(pool)
            z = sum(1 for r in pool if r["relevance"] == 0.0)
            first_zero_rows += z
            first_zero_pools += 1 if z == len(pool) else 0
        if m["quiet"]:
            tot["quiet_world"] += 1
        if m["retries"]:
            tot["retries"] += 1
        if m.get("band_asked") != m.get("band_got"):
            tot["band_asked_ne_got"] += 1
    shadow_bad = [r for r in log if r["kind"] != "mission"]
    return dict(
        seeds=seeds, missions_requested=missions, missions_run=len(ms), candidate_rows=len(rows),
        draws_checked=tot["draws_checked"], draws_in_pool=tot["draw_in_pool"], draws_in_top5=tot["draw_in_top5"],
        argmax_count=tot["argmax"], argmax_rate=(tot["argmax"] / tot["draws_checked"]) if tot["draws_checked"] else None,
        rank_histogram={str(k): rank_hist[k] for k in sorted(rank_hist)},
        swapped_count=len(swapped), swapped=swapped,
        first_mission_rows=first_rows, first_mission_relevance_zero_rows=first_zero_rows,
        first_mission_pools_all_zero=first_zero_pools,
        archetypes_seen=sorted(arch_name(a) for a in seen), archetypes_played=sorted(arch_name(a) for a in played),
        max_urgency=max_urg, quiet_world=tot["quiet_world"], retries=tot["retries"],
        band_asked_ne_got=tot["band_asked_ne_got"],
        recompute_mismatches={k: v for k, v in tot.items() if k.startswith("recompute_mismatch_")},
        shadow_problems=shadow_bad, campaigns=outs)


def write_md(s, path):
    L = ["# Mission choice summary", "", "Seeds %s, %d missions each requested." % (s["seeds"], s["missions_requested"]), "",
         "| item | value |", "|---|---|"]
    for k in ("missions_run", "candidate_rows", "draws_checked", "draws_in_pool", "draws_in_top5", "argmax_count", "argmax_rate",
              "swapped_count", "first_mission_rows", "first_mission_relevance_zero_rows", "first_mission_pools_all_zero",
              "max_urgency", "quiet_world", "retries", "band_asked_ne_got"):
        L.append("| %s | %s |" % (k, s[k]))
    L += ["| archetypes_seen | %s |" % ", ".join(s["archetypes_seen"]), "| archetypes_played | %s |" % ", ".join(s["archetypes_played"]),
          "| recompute_mismatches | %s |" % s["recompute_mismatches"], "| shadow_problems | %d |" % len(s["shadow_problems"]),
          "", "## Rank of the draw", "", "| rank | draws |", "|---|---|"]
    L += ["| %s | %s |" % kv for kv in s["rank_histogram"].items()]
    L += ["", "## Swapped (drawn pick replaced at mission_start)", "", "| seed | tick | drawn (region, archetype) | played | pipe-side counts (units, power) |", "|---|---|---|---|---|"]
    L += ["| %d | %d | %s | %s | %s |" % (x["seed"], x["tick"], x["drawn"], x["played"], x["replaced"]) for x in s["swapped"]]
    Path(path).write_text("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", default="1-10")
    ap.add_argument("--missions", type=int, default=10)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, log, outs = [], [], []
    for sd in parse_seeds(a.seeds):
        outs.append(campaign(sd, a.missions, rows, log))
        print(outs[-1], file=sys.stderr)
    (out / "rows.json").write_text(json.dumps(rows))
    s = summarise(outs, rows, log, a.seeds, a.missions)
    (out / "mission_summary.json").write_text(json.dumps(s, indent=1))
    write_md(s, out / "mission_summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
