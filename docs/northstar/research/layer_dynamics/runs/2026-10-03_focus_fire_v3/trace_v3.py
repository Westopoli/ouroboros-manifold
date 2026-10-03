"""Who shoots whom: identical 16 v 16 (and reach), seed 0, trace on, policy pairs (0,0) and (1,0)."""
import dataclasses, sys, collections
from scripts.skilllab import batches, engine as E, fight as F

LABELS = sys.argv[1:] or ["identical"]
cells = {c.label: c for c in batches._focus_fire().cells if c.build}
eng = E.Engine()
for label in LABELS:
    for pair in ((0, 0), (1, 0), (0, 1), (1, 1)):
        for seed in (0, 1, 2):
            b = batches._with_settings(cells[label].build, {})
            s = b(16, False)
            s = dataclasses.replace(s, trace=True, target_policy=pair)
            r = F.fight(s, seed, False, eng)
            ids = sorted({t[1] for t in r.trace})
            # side by unit id: first half spawned first; derive from survivors? use heads order: ids 1..16 side 0 if not swapped
            side = {u: (0 if i < 16 else 1) for i, u in enumerate(ids)}
            bytick = collections.defaultdict(list)
            for t in r.trace:
                bytick[t[0]].append(t)
            ticks = sorted(bytick)
            alive_prev = {}
            first_kill = None
            kills = []
            switches = collections.Counter()
            last_tgt = {}
            dist = {0: [], 1: []}
            for tk in ticks:
                tgts = {0: set(), 1: set()}
                for (_, u, x, y, tg, fc, al) in bytick[tk]:
                    if al and tg:
                        tgts[side[u]].add(tg)
                    if u in alive_prev and alive_prev[u] and not al:
                        kills.append((tk, side[u]))
                    alive_prev[u] = al
                    if al:
                        if u in last_tgt and tg and last_tgt[u] and tg != last_tgt[u] and alive_prev.get(last_tgt[u], 0):
                            switches[side[u]] += 1
                        if tg: last_tgt[u] = tg
                for sd in (0, 1):
                    dist[sd].append((tk, len(tgts[sd])))
            fk = kills[0] if kills else None
            fc = r.first_contact_tick
            def mean_between(sd, a, b):
                v = [n for tk, n in dist[sd] if a <= tk < b]
                return sum(v) / len(v) if v else 0
            end = fk[0] if fk else r.ticks
            print(label, pair, "seed", seed, "contact", fc, "first kill", fk, "ticks", r.ticks, "margin %.2f" % r.margin,
                  "mean distinct targets contact..firstkill s0 %.1f s1 %.1f" % (mean_between(0, fc, end), mean_between(1, fc, end)),
                  "switches while target alive s0 %d s1 %d" % (switches[0], switches[1]),
                  "first4 kills", kills[:4])
