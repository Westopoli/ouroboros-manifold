"""The reserves case (README 6.3, Westley's note: an even exchange is not an even outcome when the totals
differ, because the side with more units in reserve outlasts the other). A fields `front` units that meet
B's 10 head-on (an even exchange), plus `reserve` units that arrive `gap` world units behind. Flat ground,
one layer, both sides nearest-target, both sides attack-move at each other, so the no-reserve baseline is an even fight."""
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.run import run
from layerlab.analysis import exchange

def build(front=10, reserve=10, gap=800, n_b=10, a_x=1300.0, b_x=3000.0, y=1000.0, base="scenarios/x0_mirror.toml"):
    s = scenario.load(base)
    g = [dict(side="A", type="raider", count=front, formation="line", x=a_x, y=y, facing=0.0, layer=3,
              order="attack_move", goal=[b_x, y])]
    if reserve:
        g.append(dict(side="A", type="raider", count=reserve, formation="line", x=a_x - gap, y=y, facing=0.0, layer=3,
                      order="attack_move", goal=[b_x, y]))
    g.append(dict(side="B", type="raider", count=n_b, formation="line", x=b_x, y=y, facing=180.0, layer=3,
                  order="attack_move", goal=[a_x, y]))
    s["groups"] = g
    return set_path(s, "rules.chase_when_idle", 1)

if __name__ == "__main__":
    for label, kw in (("10 v 10, no reserve", dict(reserve=0)), ("10 + 10 reserve v 10", dict()), ("10 + 20 reserve v 10", dict(reserve=20))):
        s = build(**kw); wins = 0; surv = []; evw = []
        for sd in range(40):
            r = run(s, seed=sd, trace=True); wins += r.winner == 1; surv.append(r.survivors[0])
        r = run(s, seed=0, trace=True); t = exchange(r, s, window=40)
        print(f"{label}: A wins {wins}/40, A survivors {sum(surv)/40:.1f}")
    print("\nseed 0, 10 + 10 reserve v 10, 40-tick windows (A total 20, B total 10):")
    r = run(build(), seed=0, trace=True); print(exchange(r, build(), window=40).text)
