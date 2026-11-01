"""H-040 stage page: one static page of arena fights for Westley's eyes (spec: docs/stories/H-040.md, Part 4).

python3 -m scripts.skilllab.arena.page --dir <out dir> --out <html>

One row per `<stem>.fight.json` in the directory: id, pair, predict and predict_why (from the layout at `layout_path`, resolved
against the current directory), winner, survivors, ticks, agree in green or red, a verdict cell, then the frame strip
(`<stem>/frame-<i>.png`, 240 px high) and the fall map (the last frame larger). A file that fails `snapshot.read` is listed as
`INVALID <stem>` and the page still builds. Shape and words follow scripts/skilllab/catalogue/review.py build.
"""
import argparse
import html
import sys
import tomllib
from pathlib import Path

from scripts.skilllab.arena.snapshot import read

STRIP_HEIGHT = 240     # story: frame strip 240 px high
FALL_HEIGHT = 480      # DRAFT-fall-map-height: "the last frame larger"; Westley rules

STYLE = ("<style>.agree{background:#bfe8bf}.disagree{background:#f0b8b8}"
         ".strip figure{display:inline-block;margin:2px;text-align:center}</style>")


def _layout(path):
    """The layout TOML at `path` (against the current directory), or an empty table when it cannot be read."""
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _figure(src, tick, alive, height):
    return ('<figure><img src="%s" height="%d"><figcaption>tick %d A %d B %d</figcaption></figure>'
            % (html.escape(src), height, tick, alive[0], alive[1]))


def _row(path):
    stem = path.name[:-len(".fight.json")]
    try:
        doc = read(path)
    except ValueError as err:
        return '<tr><td colspan="4"><b>INVALID %s</b><br>%s</td></tr>' % (html.escape(stem), html.escape(str(err)))
    layout = _layout(doc["layout_path"])
    res = doc["result"]
    frames = doc["frames"]
    count = lambda side: sum(1 for u in frames[0]["units"] if u["side"] == side)
    cls = "agree" if res["agree"] else "disagree"
    strip = "".join(_figure("%s/frame-%d.png" % (stem, i), f["tick"], f["alive"], STRIP_HEIGHT) for i, f in enumerate(frames))
    last = len(frames) - 1
    fall = _figure("%s/frame-%d.png" % (stem, last), frames[last]["tick"], frames[last]["alive"], FALL_HEIGHT)
    return ('<tr><td><b>%(id)s</b><br>seed %(seed)d<br>pair: %(pair)s</td>'
            '<td>predict: %(predict)s<br>%(why)s</td>'
            '<td>winner: %(winner)s<br>survivors: %(surv)s<br>ticks: %(ticks)d%(capped)s</td>'
            '<td class="%(cls)s">%(cls)s</td></tr>\n'
            '<tr><td colspan="4">verdict: %(verdict)s<br>%(feedback)s</td></tr>\n'
            '<tr><td colspan="4" class="strip">%(strip)s</td></tr>\n'
            '<tr><td colspan="4">fall map<br>%(fall)s</td></tr>'
            % {"id": html.escape(doc["layout_id"]), "seed": doc["seed"], "pair": "%d:%d" % (count("A"), count("B")),
               "predict": html.escape(res["predict"]), "why": html.escape(layout.get("predict_why", "")),
               "winner": html.escape(res["winner"]), "surv": "%d:%d" % tuple(res["survivors"]), "ticks": res["ticks"],
               "capped": " (capped)" if res["capped"] else "", "cls": cls,
               "verdict": html.escape(layout.get("verdict") or "-"), "feedback": html.escape(layout.get("feedback", "")),
               "strip": strip, "fall": fall})


def build(d, out):
    rows = [_row(p) for p in sorted(Path(d).glob("*.fight.json"))]
    page = ('<!doctype html><meta charset="utf-8"><title>Arena stage review</title>%s<body><h1>Arena stage review</h1>'
            "<p>Side A blue, side B red. Answer in verdicts.md: | id | verdict | feedback | with verdict A, B, draw or deny.</p>"
            '<table border="1" cellpadding="6">%s</table></body>\n' % (STYLE, "\n".join(rows)))
    Path(out).write_text(page)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return build(args.dir, args.out)


if __name__ == "__main__":
    sys.exit(main())
