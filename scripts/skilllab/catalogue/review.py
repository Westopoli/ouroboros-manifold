"""H-025 review queue: build one static page of layouts, apply Westley's verdict table, list the denied.

python3 scripts/skilllab/catalogue/review.py build --dir <catalogue> --out <catalogue>/review.html
python3 scripts/skilllab/catalogue/review.py apply --dir <catalogue> --verdicts <verdicts.md>
python3 scripts/skilllab/catalogue/review.py denied --dir <catalogue>
"""
import argparse
import html
import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.skilllab.catalogue.produce import write_layout  # noqa: E402

VERDICTS = ("A", "B", "draw", "deny")


def _layouts(d):
    out = []
    for p in sorted(Path(d).glob("L-*.toml")):
        with open(p, "rb") as f:
            out.append(tomllib.load(f))
    return out


def _pair(layout):
    return "%d:%d" % (layout["side_a"]["headcount"], layout["side_b"]["headcount"])


def build(d, out):
    cards = []
    for l in _layouts(d):
        cards.append(
            '<tr><td><img src="%(id)s.png" alt="%(id)s" width="640"></td><td><b>%(id)s</b><br>situation: %(situation)s<br>pair: %(pair)s<br>'
            'landscape: %(landscape)s<br>predict: %(predict)s<br>%(why)s</td><td>verdict: %(verdict)s<br>%(feedback)s</td></tr>'
            % {"id": l["id"], "situation": html.escape(l["situation"]), "pair": _pair(l), "landscape": html.escape(l["landscape"]),
               "predict": html.escape(l["predict"]), "why": html.escape(l["predict_why"]), "verdict": html.escape(l["verdict"] or "-"),
               "feedback": html.escape(l["feedback"])})
    page = ('<!doctype html><meta charset="utf-8"><title>Layout review</title><body><h1>Layout review</h1>'
            "<p>Side A blue, side B red. Answer in verdicts.md: | id | verdict | feedback | with verdict A, B, draw or deny.</p>"
            '<table border="1" cellpadding="6">%s</table></body>\n' % "\n".join(cards))
    Path(out).write_text(page)
    return 0


def _rows(verdicts):
    rows = []
    for line in Path(verdicts).read_text().splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        s = s[1:-1] if s.endswith("|") else s[1:]
        cells = [c.strip() for c in s.split("|")]
        if len(cells) >= 2 and re.fullmatch(r"L-\d{4}", cells[0]):
            rows.append((cells[0], cells[1], " | ".join(cells[2:])))
    return rows


def apply(d, verdicts):
    by_id = {l["id"]: l for l in _layouts(d)}
    rows = _rows(verdicts)
    bad = [r for r in rows if r[0] not in by_id or r[1] not in VERDICTS]
    if bad:
        print("bad verdict rows (unknown id or verdict not in %s): %s" % (list(VERDICTS), bad), file=sys.stderr)
        return 1
    for lid, verdict, feedback in rows:
        layout = by_id[lid]
        layout["verdict"], layout["feedback"] = verdict, feedback
        write_layout(layout, d)
        print("APPLIED %s %s" % (lid, verdict))
    return 0


def denied(d):
    for l in _layouts(d):
        if l["verdict"] == "deny":
            print("%s %s %s %s" % (l["id"], l["situation"], _pair(l), l["feedback"]))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--dir", required=True)
    b.add_argument("--out", required=True)
    a = sub.add_parser("apply")
    a.add_argument("--dir", required=True)
    a.add_argument("--verdicts", required=True)
    n = sub.add_parser("denied")
    n.add_argument("--dir", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "build":
        return build(args.dir, args.out)
    if args.cmd == "apply":
        return apply(args.dir, args.verdicts)
    return denied(args.dir)


if __name__ == "__main__":
    sys.exit(main())
