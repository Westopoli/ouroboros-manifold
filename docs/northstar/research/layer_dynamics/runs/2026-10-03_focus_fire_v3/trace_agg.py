"""Seeds 0-9, swap False: first enemy (side 1) loss tick, first side 0 loss tick, side 0 mean distinct targets per tick
from contact to the first enemy loss, and mean target switches while the old target lived, per side-0 unit, whole fight."""
import dataclasses, sys, collections
from scripts.skilllab import batches, engine as E, fight as F
cells = {c.label: c for c in batches._focus_fire().cells if c.build}
eng = E.Engine()
for label in sys.argv[1:]:
    for pair in ((0, 0), (1, 0)):
        fk1, fk0, dist, sw = [], [], [], []
        for seed in range(10):
            s = dataclasses.replace(batches._with_settings(cells[label].build, {})(16, False), trace=True, target_policy=pair)
            r = F.fight(s, seed, False, eng)
            ids = sorted({t[1] for t in r.trace}); side = {u: int(i >= 16) for i, u in enumerate(ids)}
            by = collections.defaultdict(list)
            for t in r.trace: by[t[0]].append(t)
            alive, loss = {}, {0: None, 1: None}
            per = []
            last, n_sw = {}, 0
            for tk in sorted(by):
                tg = set()
                for (_, u, x, y, t, f, al) in by[tk]:
                    if alive.get(u) and not al and loss[side[u]] is None: loss[side[u]] = tk
                    alive[u] = al
                    if al and side[u] == 0:
                        if t: tg.add(t)
                        if t and last.get(u) and t != last[u] and alive.get(last[u]): n_sw += 1
                        if t: last[u] = t
                per.append((tk, len(tg)))
            end = loss[1] or r.ticks
            v = [n for tk, n in per if r.first_contact_tick <= tk < end]
            fk1.append(loss[1]); fk0.append(loss[0]); dist.append(sum(v) / max(1, len(v))); sw.append(n_sw)
        m = lambda a: sum(a) / len(a)
        print(label, pair, "first enemy loss %.0f" % m([x for x in fk1 if x]), "first own loss %.0f" % m([x for x in fk0 if x]),
              "side0 distinct targets (contact..first enemy loss) %.2f" % m(dist), "side0 switches/fight %.0f" % m(sw), fk1)
