"""focus_fire v3 (A196/A197): headline cells, per-side target policy. Run from the repo root:
python docs/northstar/research/layer_dynamics/runs/2026-10-03_focus_fire_v3/run_v3.py
Side 0 is the cell's play (the skilled side in S2 skilled / counter); side 1 is the enemy of 8 to 24.
Policy pair (p0, p1): 0 spread (nearest, kept), 1 focus (most damaged, re-picked every cohort turn)."""
import dataclasses, sys, time
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))
from scripts.skilllab import batches, report, rows, scan
from scripts.skilllab.pool import FightPool

OUT = Path(__file__).resolve().parent
HEADLINE = ("identical", "reach", "S2_skilled", "S2_counter")
PAIRS = ((0, 0), (1, 0), (0, 1), (1, 1))
WORKERS = 8


def with_policy(build, pair):
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        setup = dataclasses.replace(setup, settings={**setup.settings, **batches.BASE_SETTINGS})
        return dataclasses.replace(setup, target_policy=pair)
    return wrapped


def main():
    t0 = time.time()
    cells = {c.label: c for c in batches._focus_fire().cells if c.label in HEADLINE}
    scans, fight_rows, lines, body = {}, [], [], []
    with FightPool(WORKERS) as pool:
        for label in HEADLINE:
            c = cells[label]
            for pair in PAIRS:
                sc = scan.scan(with_policy(c.build, pair), c.size, c.enemy_from, c.enemy_to, replicates=c.replicates,
                               map_fn=pool.map, refine_factor=batches.REFINE_FACTOR)
                scans[(label, pair)] = sc
                for cell in sc.cells:
                    for f in cell.fights:
                        fight_rows.append(rows.fight_row(f, cell=label, p0=pair[0], p1=pair[1], size=c.size,
                                                         enemy_heads=cell.enemy_heads, status=c.status))
                print(label, pair, sc.beats, sc.loses_to, "%.0fs" % (time.time() - t0), flush=True)
    rows.write_rows(fight_rows, OUT / "focus_fire_v3.csv")
    lines += ["# focus_fire v3 run", "", "Pass marks provisional (A174). Policy pair (side 0, side 1): 0 spread, 1 focus.", "",
              "| cell | pair | beats | loses to | margin at beats | margin at loses to | pair spread at edge | mean ticks | stalled | fights |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for (label, pair), sc in scans.items():
        fights = [f for c in sc.cells for f in c.fights]
        m = {c.enemy_heads: c.mean_margin for c in sc.cells}
        edge = next((c for c in sc.cells if c.enemy_heads == sc.beats), None)
        sp = "%.2f to %.2f" % scan.pair_spread(edge) if edge else ""
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %.0f | %d | %d |" % (
            label, pair, sc.beats, sc.loses_to, "%.3f" % m[sc.beats] if edge else "", "%.3f" % m[sc.loses_to] if edge else "",
            sp, sum(f.ticks for f in fights) / len(fights), sum(f.outcome in ("stalemate", "cap") for f in fights), len(fights)))
        body += ["<h2>%s, pair %s</h2>" % (escape(label), escape(str(pair))), report._scan_svg(sc), report._scan_table(sc)]
    lines += ["", "Runtime %.0f s, %d fights." % (time.time() - t0, len(fight_rows)), ""]
    (OUT / "focus_fire_v3_run.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "focus_fire_v3_page.html").write_text(report._html("focus_fire v3", body), encoding="utf-8")


if __name__ == "__main__":
    main()
