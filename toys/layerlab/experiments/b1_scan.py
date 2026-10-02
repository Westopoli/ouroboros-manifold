"""Design chat (b1): one skill, one map, one size, whole heads, read in soldiers.
Usage: python3 experiments/b1_scan.py <unit> <skills: - or S2 or S1+S2> <size> <enemy from> <enemy to> [seeds=10] [family=flat]"""
import sys, dataclasses
sys.path.insert(0, ".")
from layerlab.skill import plays
from layerlab.skill.fight import run_fights
from layerlab.skill.situation import sample_situations

def pick(family, unit):
    sit = [s for s in sample_situations(14, 1) if s.family == family][0]
    return dataclasses.replace(sit, mix={unit: 1.0})

def make_build(sit, skills, size, mine="line", theirs="line"):
    """Like plays.build_scenario, but each side may use its own naive ladder (line, blob, hold)."""
    import copy
    from layerlab import scenario
    from layerlab.skill import situation
    from layerlab.skill.cost import counts_for_heads
    base = situation.base_scenario(sit)
    sc = counts_for_heads(sit.mix, size, base)
    arc = plays._fit_arc(sit, base, sc, skills, mine)[0] if "S2" in skills else plays._ARC
    def build(ratio, swap):
        nc = counts_for_heads(sit.mix, int(ratio * size + 0.5), base)
        scn = copy.deepcopy(base)
        a = plays._compose(sit, base, 0, sc, skills, mine, (sit.mix, nc), sum(sc.values()) > sum(nc.values()), arc)
        b = plays._compose(sit, base, 1, nc, frozenset(), theirs, (sit.mix, sc), sum(nc.values()) > sum(sc.values()), layer=sit.layer)
        if swap:
            a = [dict(g, side="B") for g in a]; b = [dict(g, side="A") for g in b]
        g = a + b
        scn["groups"] = [x for x in g if x["side"] == "A"] + [x for x in g if x["side"] == "B"]
        scenario.to_c(scn)
        return scn
    return build

def scan(sit, skills, size, heads, seeds, processes=8, mine="line", theirs="line"):
    build = make_build(sit, skills, size, mine, theirs)
    jobs, slots = [], []
    for n in heads:
        for swap in (False, True):
            scn = build(n / size, swap)
            for seed in range(seeds):
                jobs.append((scn, seed)); slots.append((n, swap))
    rows = {}
    for (n, swap), fr in zip(slots, run_fights(jobs, processes=processes)):
        sk = int(swap)
        m = -fr.margin if swap else fr.margin
        dur = max(fr.ticks - max(fr.first_contact_tick, 0), 1)
        rows.setdefault(n, []).append((m, fr.firing_ticks[sk] / dur, fr.firing_ticks[1 - sk] / dur, fr.outcome, dur))
    return rows

def report(title, size, rows, win=0.05):
    print(f"\n{title}")
    print(f"  {'enemy':>5} | {'won':>7} | {'margin':>7} | avg firing after contact: ours | theirs | {'secs':>5} | stalemates")
    beat = None
    for n in sorted(rows):
        r = rows[n]; k = len(r)
        won = sum(1 for x in r if x[0] > win)
        mm = sum(x[0] for x in r) / k
        print(f"  {n:>5} | {won:>3}/{k:<3} | {mm:>+7.2f} | {sum(x[1] for x in r)/k:>30.1f} | {sum(x[2] for x in r)/k:>6.1f} | {sum(x[4] for x in r)/k/20:>5.0f} | {sum(1 for x in r if x[3]=='stalemate')}")
        if won * 2 > k:
            beat = n
    lose = min((n for n in rows if n > (beat or 0) and sum(1 for x in rows[n] if x[0] > win) * 2 <= len(rows[n])), default=None)
    print(f"  => {size} units beat {beat} and lose to {lose}" if beat else f"  => {size} units beat nothing in this range")
    return beat

if __name__ == "__main__":
    unit, sk, size, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    seeds = int(sys.argv[6]) if len(sys.argv) > 6 else 10
    family = sys.argv[7] if len(sys.argv) > 7 else "flat"
    mine = sys.argv[8] if len(sys.argv) > 8 else "line"
    theirs = sys.argv[9] if len(sys.argv) > 9 else "line"
    skills = frozenset() if sk == "-" else frozenset(sk.split("+"))
    sit = pick(family, unit)
    report(f"{unit}, {family}, {size} units. Ours: {mine if not skills else '+'.join(sorted(skills))}. Theirs: {theirs}", size, scan(sit, skills, size, range(lo, hi + 1), seeds, mine=mine, theirs=theirs))
