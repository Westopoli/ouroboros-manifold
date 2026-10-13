#!/usr/bin/env python3
"""Sim lane scout A: verify mission CHOICE against E-10 S-072..S-074 (ALG-54/55).

FINDINGS ONLY tooling (docs/northstar/plans/2026-10-12-sim-lane-context.md, ROADMAP 2b step 1).

Two sides run the same campaign in lockstep:
  * the debug pipe (scripts/simviewer/pipe_session.py), which is what the client talks to; its
    `mission` frame and `snapshot` frames are the ground truth;
  * a ctypes replica of the pipe handlers (csrc/pipe/om_pipe.c handle_set_seed, handle_mission_start,
    handle_objective_complete, handle_mission_end, handle_jump) on libouroboros_dbg.so, used only to
    read what the pipe cannot show: the candidate pool, previous owners, held_since, lineage rows.
    The replica is validated per mission (tick, checksum, region, archetype must equal the pipe's).

Independent recomputation is in Python from the pipe snapshot (fields, composites, edges, stances,
telegraphs) plus the replica's raw lineage / previous-owner reads. Two models:
  V_C  membership = the C pool, arithmetic per ALG-55 with the C's own inputs (times_run 0, last lineage);
       verifies urgency / relevance / preference / score / top-5.
  V_R  membership and inputs as the rule text reads them (R-072-01..05, R-073-01) with what the world
       can supply; verifies the choice against the RULE, not against the implementation.

Usage: mission_choice.py [--seeds 1-10] [--n-regions 80] [--missions 6] [--out DIR]
"""
import argparse
import ctypes
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.simviewer.pipe_session import PipeSession, DEFAULT_FEATURES, JUMP_TICKS  # noqa: E402

ARCH_NAMES = ["Defensive Stand", "Siege Breaking", "Reconquest", "Assault", "Suppression",
              "Multi-Front Defense", "Interception", "Evacuation", "Containment", "Counterinsurgency"]
DS, SIEGE, RECON, ASSAULT, SUPPR, MULTI, INTERC, EVAC, CONTAIN, COIN = range(10)
STANCE_HOSTILE = 0
ARCH_BREAKAWAY = 6
ARCH_CONQUEROR, ARCH_OPPORTUNIST, ARCH_WARLORD = 1, 3, 4
CAND_ATTACK = 0
PHASE_BRIEFING, PHASE_MISSION = 0, 2
MAX_POOL = 512

# ---- named constants copied from docs/bible/algorithms.md ALG-55 and E-10 R-072/R-073 -------------
W_URG = (0.4, 0.4, 0.2)          # field, conflict, chain
W_REL = (0.4, 0.3, 0.3)          # lineage, proximity, archetype fit
W_SCORE = (0.5, 0.3, 0.2)        # urgency, relevance, preference
MAX_HOPS = 5
FIT_THRESHOLD = 3
TOP_N = 5
DEFAULT_PREF = 0.5
RARE_PREF = 0.1
HOSTILE_MIL = 50.0               # R-073-01 Siege "hostile neighbor above military 50"
SIEGE_OWN = 40.0                 # R-073-01 Siege "own military <= 40 or economy <= 40"
# R-073-01 Evacuation says "collapsed" with no number; the C's draft numbers are used for V_R.
EVAC_M, EVAC_E, EVAC_S = 15.0, 20.0, 15.0
WINDOW = JUMP_TICKS              # "this window" = the jump just run


def clamp01(v):
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


# ---------------------------------------------------------------------------------------------
# ctypes replica
# ---------------------------------------------------------------------------------------------
class Cand(ctypes.Structure):
    _fields_ = [("region_idx", ctypes.c_uint32), ("archetype", ctypes.c_uint32),
                ("urgency", ctypes.c_double), ("relevance", ctypes.c_double),
                ("preference", ctypes.c_double), ("score", ctypes.c_double)]


class AttCand(ctypes.Structure):
    _fields_ = [("region_idx", ctypes.c_uint32), ("kind", ctypes.c_uint32),
                ("weakness", ctypes.c_double), ("value", ctypes.c_double),
                ("position", ctypes.c_double), ("attractiveness", ctypes.c_double),
                ("entrenchment", ctypes.c_double), ("net", ctypes.c_double),
                ("viable", ctypes.c_uint32), ("_pad", ctypes.c_uint32)]


class JumpReport(ctypes.Structure):
    _fields_ = [("start_tick", ctypes.c_uint64), ("end_tick", ctypes.c_uint64),
                ("jump_ticks", ctypes.c_uint32), ("n_territory_changes", ctypes.c_uint32),
                ("n_faction_births", ctypes.c_uint32), ("n_faction_deaths", ctypes.c_uint32),
                ("n_conquests", ctypes.c_uint32), ("n_colonizations", ctypes.c_uint32),
                ("n_revolts", ctypes.c_uint32), ("n_chronicle_entries", ctypes.c_uint32),
                ("n_snapshots", ctypes.c_uint32)]


class Sim:
    """Replica of the pipe's campaign flow on libouroboros_dbg.so (same lib the dbg pipe links)."""

    def __init__(self):
        L = self.L = ctypes.CDLL(str(ROOT / "libouroboros_dbg.so"))
        W, u32, i32, u64, d, i = (ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32,
                                  ctypes.c_uint64, ctypes.c_double, ctypes.c_int)

        def b(name, args, res):
            f = getattr(L, name)
            f.argtypes = args
            f.restype = res
            return f
        self.world_new = b("om_world_new", [u32, u64], W)
        self.world_free = b("om_world_free", [W], None)
        self.set_feature = b("om_world_set_feature", [W, i, i], None)
        self.generate = b("om_world_generate", [W], None)
        self.generated = b("om_world_generated", [W], i)
        self.events_load_launch = b("om_events_load_launch", [W], None)
        self.load_library = b("om_mission_load_launch_library", [W], None)
        self.campaign_start = b("om_campaign_start", [W, u32], None)
        self.strategic_tick = b("om_world_strategic_tick", [W], u64)
        self.checksum = b("om_world_get_state_checksum", [W], u64)
        self.n_regions = b("om_region_count", [W], u32)
        self.owner = b("om_region_owner", [W, u32], i32)
        self.prev_owner = b("om_region_previous_owner", [W, u32], i32)
        self.held_since = b("om_region_held_since", [W, u32], ctypes.c_int64)
        self.player = b("om_player_faction", [W], i32)
        self.neighbors = b("om_region_neighbors", [W, u32, ctypes.POINTER(u32), u32], u32)
        self.lineage_count = b("om_lineage_count", [W], u32)
        self.lineage_id_at = b("om_lineage_id_at", [W, u32], u32)
        self.lineage_hist = b("om_lineage_history_region", [W, u32, u32], i32)
        self.lineage_member = b("om_lineage_member_in_region", [W, u32, u32], i)
        self.campaign_lineage = b("om_campaign_lineage", [W], u32)
        self.refresh = b("om_mission_refresh_context", [W, i32], None)
        self.cands = b("om_mission_candidates", [W, ctypes.POINTER(Cand), u32], u32)
        self.chosen_arch = b("om_mission_generator_chosen_archetype", [W], i32)
        self.chosen_region = b("om_mission_generator_chosen_region", [W], u32)
        self.fb_region = b("om_mission_fallback_region", [W], u32)
        self.fb_enemy = b("om_mission_fallback_enemy", [W, u32], i32)
        self.jump_run = b("om_time_jump_run", [W, u32, ctypes.POINTER(JumpReport)], i)
        self.set_era = b("om_set_era_kind", [W, i], i)
        self.setup = b("om_mission_setup", [W, u32, u32, i], None)
        self.setup_fb = b("om_mission_setup_fallback", [W, u32, i32], None)
        self.force_count = b("om_mission_get_deployed_force_count", [W], u32)
        self.enemy_power = b("om_mission_get_enemy_power", [W], d)
        self.build_obj = b("om_mission_build_objectives", [W, u32], None)
        self.set_phase = b("om_chapter_set_phase", [W, i], None)
        self.obj_count = b("om_mission_objective_count", [W], u32)
        self.set_obj = b("om_mission_set_objective_completion", [W, u32, d], None)
        self.mission_end = b("om_mission_end", [W], None)
        self.fac_cand = b("om_faction_candidates", [W, i32, ctypes.POINTER(AttCand), u32], u32)
        self.w = None
        self.tick = 0

    def set_seed(self, seed, n_regions, features):
        if self.w:
            self.world_free(self.w)
        self.w = self.world_new(n_regions, seed)
        for f in features:
            self.set_feature(self.w, f, 1)
        self.generate(self.w)
        self.events_load_launch(self.w)
        if not self.generated(self.w):
            raise RuntimeError("replica generation failed")
        self.load_library(self.w)
        self.campaign_start(self.w, 1)

    def refresh_all(self):
        for r in range(self.n_regions(self.w)):
            self.refresh(self.w, r)

    def jump(self, ticks):
        rep = JumpReport()
        rc = self.jump_run(self.w, ticks, ctypes.byref(rep))
        return rc, rep

    def pool(self):
        buf = (Cand * MAX_POOL)()
        n = self.cands(self.w, buf, MAX_POOL)
        return [(c.region_idx, c.archetype, c.urgency, c.relevance, c.preference, c.score) for c in buf[:n]]

    def mission_start(self):
        """Mirror of handle_mission_start (era_kind 0, no movement kinds). Returns a mission dict."""
        w = self.w
        self.refresh_all()
        drawn = self.chosen_arch(w)
        retries = 0
        while drawn < 0 and retries < 5:
            rep = JumpReport()
            if self.jump_run(w, 20, ctypes.byref(rep)) != 0:
                break
            retries += 1
            self.refresh_all()
            drawn = self.chosen_arch(w)
        region = arch = 0
        fb_enemy = -1
        quiet = False
        path = "pool"
        if drawn < 0:
            region = self.fb_region(w)
            fb_enemy = self.fb_enemy(w, region)
            if fb_enemy >= 0:
                quiet = True
                path = "quiet_world"
            else:
                path = "unsupported-no-fallback-enemy"
        else:
            region = self.chosen_region(w)
            arch = drawn
        self.set_era(w, 0)
        if quiet:
            self.setup_fb(w, region, fb_enemy)
        else:
            self.setup(w, region, arch, 0)
        scan_used = False
        drawn_pair = (region, arch)
        first_force, first_power = self.force_count(w), self.enemy_power(w)
        if self.force_count(w) == 0 or self.enemy_power(w) <= 0.0:
            scan_used = True
            # handle_mission_start scans every archetype x player region for a mission that fields units
            player = self.player(w)
            found = False
            for a in range(10):
                for i in range(self.n_regions(w)):
                    if self.owner(w, i) != player:
                        continue
                    self.setup(w, i, a, 0)
                    if self.force_count(w) > 0 and self.enemy_power(w) > 0.0:
                        region, arch, found = i, a, True
                        break
                if found:
                    break
            quiet = False
        self.build_obj(w, arch)
        self.set_phase(w, PHASE_MISSION)
        return {"region": region, "archetype": arch, "quiet_world": quiet, "retries": retries,
                "fb_enemy": fb_enemy, "scan_used": scan_used, "path": path, "drawn": drawn_pair,
                "drawn_force": first_force, "drawn_enemy_power": first_power}

    def mission_finish(self):
        for k in range(self.obj_count(self.w)):
            self.set_obj(self.w, k, 1.0)
        self.mission_end(self.w)
        self.set_phase(self.w, PHASE_BRIEFING)

    def raw_inputs(self):
        """Raw reads the pipe does not expose."""
        w = self.w
        n = self.n_regions(w)
        nb = []
        for r in range(n):
            buf = (ctypes.c_uint32 * 32)()
            k = self.neighbors(w, r, buf, 32)
            nb.append(sorted(buf[:min(k, 32)]))
        lin = {"count": self.lineage_count(w), "campaign": self.campaign_lineage(w), "rows": {}}
        for idx in range(lin["count"]):
            lid = self.lineage_id_at(w, idx)
            hist, j = [], 0
            while True:
                h = self.lineage_hist(w, lid, j)
                if h < 0:
                    break
                hist.append(h)
                j += 1
            lin["rows"][lid] = {"history": hist,
                                "members": [r for r in range(n) if self.lineage_member(w, lid, r)]}
        lin["last"] = self.lineage_id_at(w, lin["count"] - 1) if lin["count"] else None
        attack = []
        buf = (AttCand * 512)()
        k = self.fac_cand(w, self.player(w), buf, 512)
        for c in buf[:k]:
            if c.kind == CAND_ATTACK:
                attack.append((c.region_idx, c.viable))
        return {"neighbors": nb,
                "prev_owner": [self.prev_owner(w, r) for r in range(n)],
                "held_since": [self.held_since(w, r) for r in range(n)],
                "lineage": lin, "attack_cands": attack}


# ---------------------------------------------------------------------------------------------
# independent Python model (from the pipe snapshot)
# ---------------------------------------------------------------------------------------------
class World:
    def __init__(self, snap, raw):
        self.tick = snap["tick"]
        self.player = snap["player_faction"]
        self.reg = snap["regions"]
        self.n = len(self.reg)
        self.fac = {f["id"]: f for f in snap["factions"]}
        self.adj = [set() for _ in range(self.n)]
        for e in snap["edges"]:
            self.adj[e["a"]].add(e["b"])
            self.adj[e["b"]].add(e["a"])
        self.tg = snap["telegraphs"]
        self.raw = raw
        self.snap_lineage = snap["lineage"]

    def owner(self, r):
        return self.reg[r]["owner"]

    def hostile(self, a, b):
        # snapshot stance rows omit the faction itself (csrc/pipe/om_pipe.c write_snapshot, k == f skipped)
        return self.fac[a]["stance"][b if b < a else b - 1] == STANCE_HOSTILE

    def border_threat(self, r):
        o = self.owner(r)
        if o < 0:
            return 0.0
        m = 0.0
        for nb in self.adj[r]:
            no = self.owner(nb)
            if no < 0 or no == o or not self.hostile(o, no):
                continue
            m = max(m, self.reg[nb]["military"])
        return m

    def attacks_on(self, r):
        t = [x for x in self.tg if x["target"] == r]
        return len(t), sum(x["commit"] for x in t), len({x["attacker"] for x in t})

    def adjacent_lost(self, r):
        n = 0
        for nb in self.adj[r]:
            o = self.owner(nb)
            if o >= 0 and o != self.player and self.raw["prev_owner"][nb] == self.player:
                n += 1
        return n

    def distinct_threat_sources(self, r):
        """simulation/mission_generator.py trigger_multi_front_defense: attacker factions union the owners of
        hostile neighbours above military 50."""
        src = {x["attacker"] for x in self.tg if x["target"] == r}
        o = self.owner(r)
        for nb in self.adj[r]:
            no = self.owner(nb)
            if no >= 0 and no != o and self.hostile(o, no) and self.reg[nb]["military"] > HOSTILE_MIL:
                src.add(no)
        return src

    def hops_from(self, home):
        dist = {home: 0}
        q = deque([home])
        while q:
            c = q.popleft()
            if dist[c] >= MAX_HOPS:
                continue
            for nb in sorted(self.adj[c]):
                if nb not in dist:
                    dist[nb] = dist[c] + 1
                    q.append(nb)
        return dist

    def urgency(self, r, revolt_events=0):
        g = self.reg[r]
        deficit = ((100 - g["military"]) + (100 - g["economy"]) + (100 - g["stability"])) / 300.0
        n_att, budget, _ = self.attacks_on(r)
        conflict = clamp01(min(1.0, self.border_threat(r) / 70.0)
                           + 0.5 * min(1.0, 0.5 * n_att + budget / 600.0)
                           + 0.3 * min(1.0, 0.5 * self.adjacent_lost(r)))
        chain = min(1.0, 0.3 * revolt_events)
        return clamp01(W_URG[0] * deficit + W_URG[1] * conflict + W_URG[2] * chain)

    def relevance(self, r, lid, times_run):
        row = self.raw["lineage"]["rows"].get(lid) if lid is not None else None
        lineage = 0.0
        hops = MAX_HOPS
        if row is not None:
            if r in row["members"]:
                lineage = 1.0
            elif r in row["history"]:
                lineage = 0.5
            if row["history"]:
                d = self.hops_from(row["history"][0])
                hops = d.get(r, MAX_HOPS)
        prox = 1.0 - min(hops, MAX_HOPS) / MAX_HOPS
        fit = min(1.0, times_run / FIT_THRESHOLD)
        return clamp01(W_REL[0] * lineage + W_REL[1] * prox + W_REL[2] * fit)


def score(u, rel, pref):
    return W_SCORE[0] * u + W_SCORE[1] * rel + W_SCORE[2] * pref


def top5(cands):
    """cands: list of (region, arch, score) -> top-N by score, ties to earlier input order."""
    order = sorted(range(len(cands)), key=lambda i: (-cands[i][2], i))
    return [cands[i] for i in order[:TOP_N]]


def rule_triggers(W):
    """V_R pool: R-073-01 triggers read as written, with the inputs the world can supply.
    Returns (pool {(r,a): note}, unevaluable archetype set)."""
    pool = {}
    p = W.player
    cand_regions = [r for r in range(W.n) if W.owner(r) >= 0 and
                    (W.owner(r) == p or any(W.owner(nb) == p for nb in W.adj[r]))]
    atk_targets = {r for r, _ in W.raw["attack_cands"]}
    for r in cand_regions:
        o = W.owner(r)
        g = W.reg[r]
        n_att, _, n_att_fac = W.attacks_on(r)
        bt = W.border_threat(r)
        held_age = W.tick - W.raw["held_since"][r] if W.raw["held_since"][r] >= 0 else None
        if o == p:
            if n_att > 0:
                pool[(r, DS)] = "telegraph"
            if bt > HOSTILE_MIL and (g["military"] <= SIEGE_OWN or g["economy"] <= SIEGE_OWN):
                pool[(r, SIEGE)] = "hostile>50 own<=40 (held-long-enough unverifiable)"
            if n_att_fac >= 2:
                pool[(r, MULTI)] = ">=2 attacker factions in pending telegraphs"
            if n_att > 0:
                pool[(r, INTERC)] = "telegraph in transit"
            if g["military"] < EVAC_M and g["economy"] < EVAC_E and g["stability"] < EVAC_S:
                pool[(r, EVAC)] = "all three collapsed (draft numbers)"
        else:
            if W.raw["prev_owner"][r] == p and held_age is not None and held_age <= WINDOW:
                pool[(r, RECON)] = "lost within the last %d ticks" % WINDOW
            if r in atk_targets and W.hostile(p, o):
                pool[(r, ASSAULT)] = "scored attack target of player faction, hostile"
            if (W.fac[o]["archetype"] == ARCH_BREAKAWAY and held_age is not None and held_age <= WINDOW
                    and any(W.owner(nb) == p for nb in W.adj[r])):
                pool[(r, SUPPR)] = "breakaway-held, taken within window"
    # Containment (>=2 colonizations this window) and Counterinsurgency (active revolt chain) need
    # event logs the world does not keep: unevaluable, never in V_R.
    return pool, {CONTAIN, COIN}


def analyse(W, c_pool, c_pick, quiet, hist):
    """c_pool: [(r,a,u,rel,pref,score)] from the C; c_pick: (region, arch); hist: archetype -> times run
    by the current lineage in this campaign (the V_R fit input)."""
    out = {"checks": []}
    raw_lin = W.raw["lineage"]
    last = raw_lin["last"]
    cur = raw_lin["campaign"]
    out["lineage_last"] = last
    out["lineage_campaign"] = cur
    out["lineage_snapshot"] = W.snap_lineage
    # ---- V_C: arithmetic of the C pool
    vc = []
    max_du = max_dr = max_ds = 0.0
    for (r, a, u, rel, pref, sc) in c_pool:
        pu = W.urgency(r)
        pr = W.relevance(r, last, 0)
        ps = score(pu, pr, DEFAULT_PREF)
        max_du = max(max_du, abs(pu - u))
        max_dr = max(max_dr, abs(pr - rel))
        max_ds = max(max_ds, abs(ps - sc), abs(pref - DEFAULT_PREF))
        vc.append((r, a, ps))
    out["vc"] = {"n": len(c_pool), "max_du": max_du, "max_dr": max_dr, "max_ds": max_ds,
                 "top5": top5(vc), "chosen_in_top5": any((r, a) == c_pick for r, a, _ in top5(vc)) if vc else None}
    # ---- V_R: rule-literal
    rp, unev = rule_triggers(W)
    vr = []
    for (r, a), note in sorted(rp.items()):
        pu = W.urgency(r)
        pr = W.relevance(r, cur, hist.get(a, 0))
        vr.append((r, a, score(pu, pr, DEFAULT_PREF)))
    out["vr_pool"] = vr
    out["vr_top5"] = top5(vr)
    out["vr_chosen_in_top5"] = (any((r, a) == c_pick for r, a, _ in out["vr_top5"])) if vr else None
    out["vr_chosen_in_pool"] = any((r, a) == c_pick for r, a, _ in vr)
    out["c_only"] = sorted({(r, a) for r, a, *_ in c_pool} - {(r, a) for r, a, _ in vr})
    out["rule_only"] = sorted({(r, a) for r, a, _ in vr} - {(r, a) for r, a, *_ in c_pool})
    # chosen pair figures under both models
    r, a = c_pick
    out["chosen_C"] = next(((u, rel, sc) for (rr, aa, u, rel, pf, sc) in c_pool if (rr, aa) == c_pick), None)
    out["chosen_R"] = (W.urgency(r), W.relevance(r, cur, hist.get(a, 0)),
                       score(W.urgency(r), W.relevance(r, cur, hist.get(a, 0)), DEFAULT_PREF))
    # ---- the C's own stored scores: R-072-05 selection (top-N pool, one weighted draw)
    st = sorted(range(len(c_pool)), key=lambda i: (-c_pool[i][5], i))
    top = [c_pool[i] for i in st[:TOP_N]]
    tot = sum(c[5] for c in top)
    pos = next((k for k, c in enumerate(top) if (c[0], c[1]) == c_pick), None)
    out["c_stored"] = {"rank_in_top5": None if pos is None else pos + 1,
                       "p_drawn": None if pos is None or tot <= 0 else top[pos][5] / tot,
                       "p_rank1": None if tot <= 0 else top[0][5] / tot,
                       "n_pool": len(c_pool)}
    out["c_pool_by_arch"] = {a: sum(1 for c in c_pool if c[1] == a) for a in range(10)}
    out["vr_pool_by_arch"] = {a: sum(1 for (_, aa, _) in vr if aa == a) for a in range(10)}
    out["n_telegraphs"] = len(W.tg)
    out["ds_pool_no_attack"] = sum(1 for c in c_pool if c[1] == DS and W.attacks_on(c[0])[0] == 0)
    out["ds_pool"] = sum(1 for c in c_pool if c[1] == DS)
    out["stale_relevance_regions"] = sorted({c[0] for c in c_pool
                                             if abs(c[3] - W.relevance(c[0], last, 0)) > 1e-9})
    out["c_only_by_arch"] = {a: sum(1 for (_, aa) in out["c_only"] if aa == a) for a in range(10)}
    out["rule_only_by_arch"] = {a: sum(1 for (_, aa) in out["rule_only"] if aa == a) for a in range(10)}
    # per-trigger evidence used by the findings ledger (docs/.../findings/mission_choice.md)
    pl = W.player
    mf = [c for c in c_pool if c[1] == MULTI]
    out["mf_c_pool"] = len(mf)
    out["mf_lt2_distinct_sources"] = sum(1 for c in mf if len(W.distinct_threat_sources(c[0])) < 2)
    sg = [c for c in c_pool if c[1] == SIEGE]
    out["siege_c_pool"] = len(sg)
    out["siege_held_lt_200"] = sum(1 for c in sg if W.raw["held_since"][c[0]] < 0 or W.tick - W.raw["held_since"][c[0]] < 200)
    out["legacy_interception_regions"] = sorted(
        r for r in range(W.n) if W.owner(r) == pl and any(
            x["target"] == r and not any(W.owner(nb) == x["attacker"] for nb in W.adj[r]) for x in W.tg))
    out["attacked_player_regions"] = sorted({x["target"] for x in W.tg if W.owner(x["target"]) == pl})
    out["telegraph_age_max"] = max((W.tick - x["declared_tick"] for x in W.tg), default=None)
    out["contain_c_pool"] = sum(1 for c in c_pool if c[1] == CONTAIN)
    out["pool_region_outside_r07201"] = [(c[0], c[1]) for c in c_pool if not (
        W.owner(c[0]) >= 0 and (W.owner(c[0]) == pl or any(W.owner(nb) == pl for nb in W.adj[c[0]])))]
    out["top5_set_stored"] = sorted((c[0], c[1]) for c in top)
    out["top5_set_fresh"] = sorted((r, a) for r, a, _ in top5(vc))
    return out


def fallback_check(W, region, enemy):
    """R-072-07/08 re-derivation from the snapshot."""
    p = W.player
    best = None
    for r in range(W.n):
        if W.owner(r) == p:
            s = W.reg[r]["stability"]
            if best is None or s < best[0] - 1e-12:
                best = (s, r)
    exp_region = best[1] if best else None
    # BFS hops from the region over all edges
    dist = {region: 0}
    q = deque([region])
    while q:
        c = q.popleft()
        for nb in W.adj[c]:
            if nb not in dist:
                dist[nb] = dist[c] + 1
                q.append(nb)
    cand = {}
    for r in range(W.n):
        o = W.owner(r)
        if o < 0 or o == p:
            continue
        c = cand.setdefault(o, [10 ** 9, 0.0])
        c[1] += W.reg[r]["military"]
        if r in dist:
            c[0] = min(c[0], dist[r])
    exp_enemy = None
    for f in sorted(cand):
        h, m = cand[f]
        if exp_enemy is None or h < cand[exp_enemy][0] or (h == cand[exp_enemy][0] and m > cand[exp_enemy][1] + 1e-9):
            exp_enemy = f
    return exp_region, exp_enemy


# ---------------------------------------------------------------------------------------------
# campaign driver
# ---------------------------------------------------------------------------------------------
def run_campaign(seed, n_regions, n_missions, features):
    rows = []
    pipe = PipeSession()
    sim = Sim()
    notes = []
    try:
        pipe.send("set_seed", seed=seed, n_regions=n_regions, features=features)
        try:
            pipe.send("snapshot")
        except Exception as e:  # generation failed
            return rows, ["set_seed failed: %s" % (e,)]
        sim.set_seed(seed, n_regions, features)
        lineage_runs = {}   # (lineage id, archetype) -> count of earlier missions
        last_jump = None    # the opening jump runs inside om_campaign_start and returns no report
        for k in range(n_missions):
            mframe = pipe.send("mission_start", faction=0, era_kind=0)[0]
            smission = sim.mission_start()
            snap = pipe.send("snapshot")[0]
            sync = {
                "tick": snap["tick"] == sim.strategic_tick(sim.w),
                "checksum": snap["checksum"] == sim.checksum(sim.w),
                "region": mframe["region"] == smission["region"],
                "archetype": mframe["archetype"] == smission["archetype"],
                "quiet": mframe["quiet_world"] == smission["quiet_world"],
            }
            raw = sim.raw_inputs()
            W = World(snap, raw)
            c_pool = sim.pool()
            pick = tuple(smission["drawn"])      # what the generator drew (before the pipe's zero-force scan)
            cur = raw["lineage"]["campaign"]
            hist = {a: lineage_runs.get((cur, a), 0) for a in range(10)}
            res = analyse(W, c_pool, pick, mframe["quiet_world"], hist)
            final = (mframe["region"], mframe["archetype"])
            res["final_in_vr_pool"] = final in {(r, a) for r, a, _ in res["vr_pool"]}
            res["final_in_vr_top5"] = final in {(r, a) for r, a, _ in res["vr_top5"]}
            res["final_in_c_pool"] = final in {(c[0], c[1]) for c in c_pool}
            fb = None
            if mframe["quiet_world"]:
                fb = fallback_check(W, mframe["region"], smission["fb_enemy"])
                fb = {"expected_region": fb[0], "expected_enemy": fb[1],
                      "region_ok": fb[0] == mframe["region"], "enemy_ok": fb[1] == smission["fb_enemy"]}
            rows.append({"seed": seed, "k": k + 1, "tick": snap["tick"], "region": mframe["region"],
                         "archetype": mframe["archetype"], "quiet_world": mframe["quiet_world"],
                         "objectives": [(o["kind"], o["primary"]) for o in mframe["objectives"]],
                         "retries": smission["retries"], "scan_used": smission["scan_used"],
                         "prev_jump": last_jump,
                         "drawn": list(smission["drawn"]), "drawn_force": smission["drawn_force"],
                         "drawn_enemy_power": smission["drawn_enemy_power"],
                         "sync": sync, "analysis": res, "fallback": fb,
                         "pool_size": len(c_pool), "owner": W.owner(mframe["region"]),
                         "player": W.player, "mframe_force": sum(mframe["force"]["types"])})
            lineage_runs[(cur, mframe["archetype"])] = lineage_runs.get((cur, mframe["archetype"]), 0) + 1
            # play it out as the brief says
            for o in mframe["objectives"]:
                pipe.send("objective_complete", objective=o["i"], completion=1.0)
            pipe.send("mission_end")
            sim.mission_finish()
            pipe.send("jump", ticks=JUMP_TICKS)
            rc, rep = sim.jump(JUMP_TICKS)
            last_jump = {"n_conquests": rep.n_conquests, "n_colonizations": rep.n_colonizations,
                         "n_revolts": rep.n_revolts, "n_faction_births": rep.n_faction_births,
                         "n_faction_deaths": rep.n_faction_deaths, "n_territory_changes": rep.n_territory_changes}
            if rc != 0:
                notes.append("replica jump rc=%d after mission %d" % (rc, k + 1))
    finally:
        pipe.close()
    return rows, notes


def parse_range(s):
    a, _, b = s.partition("-")
    return list(range(int(a), int(b or a) + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1-10")
    ap.add_argument("--n-regions", type=int, default=80)
    ap.add_argument("--missions", type=int, default=6)
    ap.add_argument("--out", default=str(ROOT / "docs/northstar/plans/sim_lane_2026-10-12/findings"))
    a = ap.parse_args()
    all_rows, all_notes = [], {}
    for seed in parse_range(a.seeds):
        rows, notes = run_campaign(seed, a.n_regions, a.missions, DEFAULT_FEATURES)
        all_rows += rows
        if notes:
            all_notes[seed] = notes
        print("seed %d: %d missions %s" % (seed, len(rows), notes), file=sys.stderr)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "mission_choice_raw.json").write_text(json.dumps({"rows": all_rows, "notes": all_notes}, indent=1,
                                                             default=lambda o: list(o) if isinstance(o, (set, tuple)) else str(o)))
    print("wrote %s (%d missions)" % (out / "mission_choice_raw.json", len(all_rows)))


if __name__ == "__main__":
    main()
