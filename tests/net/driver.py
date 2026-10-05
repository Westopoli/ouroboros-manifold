"""Lockstep proof driver: N sim pipes joined by a seeded fake network.

Spec: docs/northstar/plans/2026-10-05-lockstep-backend-spec.md ("harness" and
"pipe" lane rows). Pipe verbs used: net_reset, net_submit (one flat command per
frame), net_step (one net_ack with tick, and checksum + sections on multiples of
10 or when asked), net_checksum. Those verbs land with the pipe lane; until the
pipe answers net_reset with a net_ack every test here is skipped (net_available).

Lockstep rule: input delay DELAY ticks (a command issued after stepping s ticks is
stamped s+DELAY); a peer's packet for tick t carries its commands for ticks
t-4..t; tick t is stepped only when every live peer's packet for t (or a later
packet that covers it) is in. Stall and drop are counted in driver rounds, one
round being one chance for each peer to step one tick (20 and 1200 by default).
A blocked peer, and every peer each STALL rounds, re-sends the recent packets it
holds from all origins (relay), so loss and a dead peer's last packets converge.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "long"))
from harness import FEATURES, N_REGIONS, PIPE, Pipe  # noqa: E402

DELAY = 3
REPEAT = 5
STALL = 20
DROP = 1200
CHECK_EVERY = 10
REISSUE = 400
MAX_UNITS = 70  # per command: OM_CMD_MAX_UNITS in csrc/cmd_stream.c (spec: at most 70 unit ids)
VERB_ATTACK_MOVE = 1  # enum in csrc/ouroboros_sim.h (spec, base item 1)
SECTIONS = ["regions", "factions", "rng", "units", "movement", "mission", "fog", "macro", "support_map"]

_probe = {}


def net_available():
    """True when the pipe answers net_reset with a net_ack. Probed once per session."""
    if "v" not in _probe:
        ok = False
        if PIPE.exists():
            pp = None
            try:
                pp = Pipe()
                pp.cmd("set_seed", seed=3, n_regions=N_REGIONS, features=FEATURES)
                pp.cmd("snapshot")
                pp.read_more()
                ok = pp.send("net_reset").get("type") == "net_ack"
            except Exception:  # noqa: BLE001 - any failure means "not there yet"
                ok = False
            finally:
                if pp is not None:
                    pp.close()
        _probe["v"] = ok
    return _probe["v"]


# ---------------------------------------------------------------- fake network
class FakeNet:
    """Seeded in-process network: per-packet delay (ticks), loss, reordering."""

    def __init__(self, seed, delay=(1, 2), loss=0.0, reorder=0.0, reorder_extra=3):
        self.rng = random.Random(seed)
        self.delay, self.loss, self.reorder, self.extra = delay, loss, reorder, reorder_extra
        self.q = []  # (deliver_at, order, dst, packet)
        self.n = 0

    def send(self, now, dst, packet):
        if self.rng.random() < self.loss:
            return
        at = now + self.rng.randint(*self.delay)
        if self.rng.random() < self.reorder:
            at += self.rng.randint(1, self.extra)
        self.q.append((at, self.n, dst, packet))
        self.n += 1

    def poll(self, now, dst):
        due = sorted(e for e in self.q if e[2] == dst and e[0] <= now)
        self.q = [e for e in self.q if not (e[2] == dst and e[0] <= now)]
        return [e[3] for e in due]


# ---------------------------------------------------------------- backends
class PipeBackend:
    """One sim process driven through the net verbs."""

    def __init__(self, pipe):
        self.pipe = pipe

    def submit(self, c):
        r = self.pipe.send("net_submit", tick=c["tick"], peer=c["peer"], seq=c["seq"], verb=c["verb"],
                           arg=c["arg"], layer=c["layer"], x=c["x"], y=c["y"], units=c["units"])
        assert r.get("type") == "net_ack", r
        return r.get("code", 0)

    def step(self, n=1, checksum=False):
        kw = {"checksum": True} if checksum else {}
        r = self.pipe.send("net_step", n=n, **kw)
        assert r.get("type") == "net_ack", r
        return r

    def close(self):
        self.pipe.close()


class Cluster:
    def __init__(self, backends, script, seed=1, net=None, delay=DELAY, stall=STALL, drop=DROP,
                 drop_peer=None, drop_at=None, withhold=None):
        """script(peer, n_peers, s) -> list of command dicts issued after s ticks.
        drop_peer stops stepping and sending once it has stepped drop_at ticks.
        withhold=(receiver, src, seq): that receiver never submits that command."""
        self.b, self.n, self.script = backends, len(backends), script
        self.net = net or FakeNet(seed)
        self.delay, self.stall, self.drop = delay, stall, drop
        self.drop_peer, self.drop_at, self.withhold = drop_peer, drop_at, withhold
        self.tick = [0] * self.n
        self.seq = [0] * self.n
        self.known = [[{t: [] for t in range(1, delay)} for _ in range(self.n)] for _ in range(self.n)]
        self.held = [[{} for _ in range(self.n)] for _ in range(self.n)]  # [me][src] tick -> packet
        self.dropped = [set() for _ in range(self.n)]
        self.blocked = [0] * self.n
        self.submitted = [set() for _ in range(self.n)]
        self.trace = [dict() for _ in range(self.n)]  # tick -> (checksum, sections)
        self.drop_log = []  # (peer, dropped_peer, tick, round)
        self.rounds = 0
        for p in range(self.n):
            self._produce(p)

    def _dead(self, p):
        return p == self.drop_peer and self.tick[p] >= self.drop_at

    def _produce(self, p):
        s, t = self.tick[p], self.tick[p] + self.delay
        cmds = []
        for c in self.script(p, self.n, s):
            cmds.append(dict(c, tick=t, peer=p, seq=self.seq[p]))
            self.seq[p] += 1
        hist = self.held[p][p]
        pk_cmds = {t: cmds}
        for k in range(t - REPEAT + 1, t):
            if k in hist:
                pk_cmds[k] = hist[k]["cmds"][k]
        pk = {"src": p, "tick": t, "cmds": pk_cmds}
        self._learn(p, pk)
        self._broadcast(p, pk)

    def _learn(self, me, pk):
        src = pk["src"]
        self.held[me][src][pk["tick"]] = pk
        for k in [k for k in self.held[me][src] if k < pk["tick"] - REPEAT]:
            del self.held[me][src][k]
        kn = self.known[me][src]
        for k in range(pk["tick"] - REPEAT + 1, pk["tick"] + 1):
            if k >= 1 and k not in kn:
                kn[k] = list(pk["cmds"].get(k, []))

    def _broadcast(self, p, pk):
        for q in range(self.n):
            if q != p:
                self.net.send(self.rounds, q, pk)

    def _relay(self, p):
        for src in range(self.n):
            for pk in list(self.held[p][src].values()):
                self._broadcast(p, pk)

    def _ready(self, p, t):
        return all(t in self.known[p][s] for s in range(self.n) if s not in self.dropped[p])

    def _step(self, p, want_check):
        t = self.tick[p] + 1
        be = self.b[p]
        for s in range(self.n):
            for c in self.known[p][s].get(t, []):
                key = (c["peer"], c["seq"])
                if key in self.submitted[p]:
                    continue
                self.submitted[p].add(key)
                if self.withhold == (p, c["peer"], c["seq"]):
                    continue
                code = be.submit(c)
                assert code == 0, "net_submit refused %r: code %r" % (c, code)
        ack = be.step(1, checksum=want_check or t % CHECK_EVERY == 0)
        assert ack["tick"] == t, ack
        if "checksum" in ack:
            self.trace[p][t] = (ack["checksum"], ack.get("sections"))
        self.tick[p] = t
        self.blocked[p] = 0
        if not self._dead(p):
            self._produce(p)

    def run(self, ticks, max_rounds=None):
        max_rounds = max_rounds or (ticks * 8 + 4 * self.drop + 1000)
        while any(self.tick[p] < ticks and not self._dead(p) for p in range(self.n)):
            self.rounds += 1
            assert self.rounds <= max_rounds, "no progress: ticks %r" % self.tick
            for p in range(self.n):
                if self._dead(p):
                    continue
                for pk in self.net.poll(self.rounds, p):
                    self._learn(p, pk)
                if self.tick[p] >= ticks:
                    pass
                elif self._ready(p, self.tick[p] + 1):
                    self._step(p, False)
                else:
                    self.blocked[p] += 1
                    if self.blocked[p] % self.stall == 0:
                        self._relay(p)
                    if self.blocked[p] >= self.drop:
                        t = self.tick[p] + 1
                        for s in range(self.n):
                            if s not in self.dropped[p] and t not in self.known[p][s]:
                                self.dropped[p].add(s)
                                self.drop_log.append((p, s, t, self.rounds))
                        self.blocked[p] = 0
                if self.rounds % self.stall == 0:
                    self._relay(p)
        return self

    def first_mismatch(self, peers=None):
        """(tick, [differing section names], {peer: checksum}) of the first checked tick
        at which the compared peers disagree, or None."""
        peers = peers if peers is not None else [p for p in range(self.n) if not self._dead(p)]
        ticks = sorted(set.intersection(*[set(self.trace[p]) for p in peers]))
        for t in ticks:
            sums = {p: self.trace[p][t][0] for p in peers}
            if len(set(sums.values())) > 1:
                secs = [self.trace[p][t][1] for p in peers]
                diff = []
                if all(s is not None for s in secs):
                    diff = [SECTIONS[i] if i < len(SECTIONS) else str(i)
                            for i in range(len(secs[0])) if len({s[i] for s in secs}) > 1]
                return t, diff, sums
        return None


# ---------------------------------------------------------------- real mission
def start_mission(pipe, seed):
    """Same start as tests/long/test_mission_plays_to_its_end.py; ends with net_reset.
    Returns the tactical frame plus the facts the script needs."""
    pipe.cmd("set_seed", seed=seed, n_regions=N_REGIONS, features=FEATURES)
    pipe.cmd("snapshot")
    snap = pipe.read_more()
    pf = snap.get("player_faction", 0)
    m = pipe.send("mission_start", faction=pf)
    assert m["type"] == "mission", m
    t = pipe.send("mission_begin")
    assert t["type"] == "tactical", t
    r = pipe.send("net_reset")
    assert r.get("type") == "net_ack", r
    nodes = {n["i"]: n for n in t["map"]["nodes"]}
    obj = next((o["node"] for o in m["objectives"] if o["primary"]), -1)
    mine = sorted(u["id"] for u in t["units"] if u["faction"] == pf)
    foe = [u for u in t["units"] if u["faction"] != pf]
    if obj in nodes:
        target = (nodes[obj]["x"], nodes[obj]["y"])
    else:
        target = (sum(u["x"] for u in foe) / len(foe), sum(u["y"] for u in foe) / len(foe))
    return {"deadline": m["deadline_ticks"], "mine": mine, "target": target, "frame": t}


def make_script(mine, target):
    """Peer p of n attack-moves its share (every n-th unit id) to target at s = 0 and every REISSUE ticks."""
    def script(p, n, s):
        if s % REISSUE:
            return []
        ids = mine[p::n]
        return [{"verb": VERB_ATTACK_MOVE, "arg": 0, "layer": 0, "x": target[0], "y": target[1],
                 "units": ids[i:i + MAX_UNITS]} for i in range(0, len(ids), MAX_UNITS)]
    return script


def run_ticks(deadline):
    import os
    return int(os.environ.get("OM_NET_TICKS", deadline))


def open_cluster(n_peers, seed=3, net=None, **kw):
    """Start n real pipes on the same mission; returns (cluster, ticks_to_run, pipes)."""
    pipes, info = [], None
    for _ in range(n_peers):
        pp = Pipe()
        pipes.append(pp)
        info = start_mission(pp, seed)
    cl = Cluster([PipeBackend(pp) for pp in pipes], make_script(info["mine"], info["target"]),
                 seed=seed, net=net, **kw)
    return cl, run_ticks(info["deadline"]), pipes, info
