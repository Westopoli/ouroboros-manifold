"""H-040 stage page: one static page of arena fights for Westley's eyes (spec: docs/stories/H-040.md, Part 4).

python3 -m scripts.skilllab.arena.page --dir <out dir> --out <html>

One row per `<stem>.fight.json` in the directory: id, pair, predict and predict_why (from the layout at `layout_path`, resolved
against the current directory), winner, survivors, ticks, agree in green or red, a verdict cell, then the frame strip
(`<stem>/frame-<i>.png`, 240 px high) and the fall map (the last frame larger). A file that fails `snapshot.read` is listed as
`INVALID <stem>` and the page still builds. Shape and words follow scripts/skilllab/catalogue/review.py build.

H-053 (DRAFT-stage2-page): a layout with a `<id>.rate.json` in the directory is shown as one block per layout, after a head and a summary table
(`_layout_block`); its fight files are not also listed as stage 1 rows. Rates, stall and none seeds, firing_capable and the median seed are the rate
file's, never recomputed; the per-role survivors are means over the seeds' last frames. One strip per layout, the median seed's; the seed numbers are
plain text (H-053 Replay readability, no per-seed strip pages).

H-063 (stage 3): `--control-dir <dir>` adds, under a fight's strip (an unrated row's, a rated layout's median seed), the control strip: the same fight with the layout's
`features` emptied, `<id>-control-s<n>.fight.json` in that directory with its frames in `<id>-control-s<n>/frame-<i>.png` (run.py `--control-dir` writes the fight).
A fight without a control file shows no second strip. `--stage N` names the stage in the header (4, 3 and 2 have words, any other is `Stage N`). `--sentences <md>`
is a table `| id | What to expect | Approve means | Deny means |` whose row for a layout id replaces the layout's `what_to_expect`, `approve_means`, `deny_means`.
Every fight, rated or not, shows the three sentences and `blocked unit-frames: n` (n = sum of len(frame["blocked"]); a rated block counts its median seed's fight).
"""
import argparse
import datetime
import html
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from scripts.skilllab.arena.snapshot import read

STRIP_HEIGHT = 240     # story: frame strip 240 px high
STAGE2_THUMB_PX = 480  # DRAFT-stage2-thumb-px: a stage 2 strip image is at least this tall (stage 1 stays STRIP_HEIGHT); Westley rules
FALL_HEIGHT = 480      # DRAFT-fall-map-height: "the last frame larger"; Westley rules

STYLE = ("<style>.agree{background:#bfe8bf}.disagree{background:#f0b8b8}.none{background:#cccccc}td.stall,span.stall{background:#f5d76e}.shot img{outline:4px solid #e6c200}"
         ".stall td{background:#f5d76e}"   # DRAFT-stall-colour: flagged amber; Westley rules
         ".strip figure{display:inline-block;margin:2px;text-align:center}</style>")


def _layout(path):
    """The layout TOML at `path` (against the current directory), or an empty table when it cannot be read."""
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


WORDS = (("What to expect", "what_to_expect"), ("Approve means", "approve_means"), ("Deny means", "deny_means"))
STAGE_WORDS = {4: "Stage 4, sight", 3: "Stage 3, the ground pushes back", 2: "Stage 2, roles and ranges"}


def _sentences(path):
    """{layout id: {key: text}} from the markdown table at `path` (`| id | What to expect | Approve means | Deny means |`); empty without a path."""
    rows = {}
    for line in Path(path).read_text().splitlines() if path else []:
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(cells) == 4 and cells[0] not in ("id", "") and not set(cells[0]) <= set("-: "):
            rows[cells[0]] = dict(zip((k for _, k in WORDS), cells[1:]))
    return rows


def _words(layout, row):
    """The three sentences: the sentences row's, else the layout's own, else `-`."""
    return "".join("<p><b>%s:</b> %s</p>" % (label, html.escape(row.get(key) or layout.get(key, "-"))) for label, key in WORDS)


def _blocked(doc):
    """`blocked unit-frames: n`, n the sum over the fight's frames of len(frame["blocked"]) (0 for a fight with no `blocked` key)."""
    return "<p>blocked unit-frames: %d</p>" % sum(len(f.get("blocked", [])) for f in doc["frames"])


def _first_seen(doc):
    """`first seen A <tick|never>  B <tick|never>` from result.first_seen (H-088 stage 4); `first seen A -  B -` when the fight has no such key."""
    fs = doc["result"].get("first_seen")
    cell = lambda side: "-" if fs is None else "never" if fs.get(side) is None else str(fs[side])
    return "<p>first seen A %s  B %s</p>" % (cell("A"), cell("B"))


def _invalid(doc):
    """F0: `INVALID: <rule> tick <N> unit <U>`, the first violation of a fight whose run broke a rule of scripts/skilllab/invariants.py; empty for a clean fight."""
    if not doc.get("invalid"):
        return ""
    v = doc["violations"][0] if doc.get("violations") else {"rule": "?", "tick": 0, "unit": 0}
    return "INVALID: %s tick %d unit %d" % (v["rule"], v["tick"], v["unit"])


def _figure(src, tick, alive, height):
    return ('<figure><img src="%s" height="%d"><figcaption>tick %d A %d B %d</figcaption></figure>'
            % (html.escape(src), height, tick, alive[0], alive[1]))


def _row(path, control_dir=None, sentences=None):
    stem = path.name[:-len(".fight.json")]
    try:
        doc = read(path)
    except ValueError as err:
        return '<tr><td colspan="4"><b>INVALID %s</b><br>%s</td></tr>' % (html.escape(stem), html.escape(str(err)))
    layout = _layout(doc["layout_path"])
    res = doc["result"]
    frames = doc["frames"]
    count = lambda side: sum(1 for u in frames[0]["units"] if u["side"] == side)
    bad = _invalid(doc)
    cls = "none" if bad else "agree" if res["agree"] else "disagree"   # F0: an invalid fight is not ranked: no agree or disagree
    verdict_cell = "invalid, not ranked" if bad else cls
    strip = "".join(_figure("%s/frame-%d.png" % (stem, i), f["tick"], f["alive"], STRIP_HEIGHT) for i, f in enumerate(frames))
    last = len(frames) - 1
    fall = _figure("%s/frame-%d.png" % (stem, last), frames[last]["tick"], frames[last]["alive"], FALL_HEIGHT)
    stall = bool(res.get("stall"))
    return ('<tr%(rowcls)s><td><b>%(id)s</b><br>seed %(seed)d<br>pair: %(pair)s%(bad)s</td>'
            '<td>predict: %(predict)s<br>%(why)s</td>'
            '<td>winner: %(winner)s<br>survivors: %(surv)s<br>ticks: %(ticks)d%(capped)s<br>end: %(end)s (%(schema)s)%(flag)s</td>'
            '<td class="%(cls)s">%(cell)s</td></tr>\n'
            '<tr><td colspan="4">verdict: %(verdict)s<br>%(feedback)s</td></tr>\n'
            '<tr><td colspan="4" class="strip">%(strip)s</td></tr>\n'
            '<tr><td colspan="4">fall map<br>%(fall)s</td></tr>\n'
            '<tr><td colspan="4">%(words)s%(blocked)s</td></tr>%(control)s'
            % {"id": html.escape(doc["layout_id"]), "seed": doc["seed"], "pair": "%d:%d" % (count("A"), count("B")),
               "predict": html.escape(res["predict"]), "why": html.escape(layout.get("predict_why", "")),
               "winner": html.escape(res["winner"]), "surv": "%d:%d" % tuple(res["survivors"]), "ticks": res["ticks"],
               "capped": " (capped)" if res["capped"] else "", "cls": cls, "cell": verdict_cell, "bad": "<br><b>%s</b>" % html.escape(bad) if bad else "",
               "rowcls": ' class="stall"' if stall else "", "end": html.escape(res.get("end", "-")),
               "schema": html.escape(doc["schema"]), "flag": "<br><b>stall: bring to Westley</b>" if stall else "",
               "verdict": html.escape(layout.get("verdict") or "-"), "feedback": html.escape(layout.get("feedback", "")),
               "strip": strip, "fall": fall, "words": _words(layout, (sentences or {}).get(doc["layout_id"], {})), "blocked": _blocked(doc) + _first_seen(doc),
               "control": _control_row(control_dir, doc["layout_id"], doc["seed"], doc.get("sight"))})


def _first_shot(frames):
    """Index of the first frame in which some unit's hp is lower than in the frame before; -1 when none (the replay's marker frame)."""
    for i in range(1, len(frames)):
        before = {u["id"]: u["hp"] for u in frames[i - 1]["units"]}
        if any(u["hp"] < before.get(u["id"], u["hp"]) for u in frames[i]["units"]):
            return i
    return -1


def _roles(doc, side):
    """'16 Vanguard + 8 Bombard' for the side's units on frame 0."""
    count = {}
    for u in doc["frames"][0]["units"]:
        if u["side"] == side:
            count[u["role"]] = count.get(u["role"], 0) + 1
    return " + ".join("%d %s" % (n, r) for r, n in sorted(count.items())) or "-"


def _strip(stem, frames, src_dir="", marker=-1):
    """The frame figures of one fight; the figure of frame `marker` (the first shot) is outlined."""
    out = []
    for i, f in enumerate(frames):
        fig = _figure("%s%sframe-%d.png" % (src_dir, "/" if src_dir else "", i), f["tick"], f["alive"], STAGE2_THUMB_PX)
        out.append('<span class="shot">%s</span>' % fig if i == marker else fig)
    return "".join(out)


def _survivors(docs):
    """Rows (role, A mean survivors, B mean survivors, A start, B start): the last frame's living units by role and side, mean over the seeds, one decimal."""
    roles = sorted({u["role"] for d in docs for u in d["frames"][0]["units"]})
    rows = []
    for r in roles:
        cells = []
        for side in "AB":
            cells.append(sum(1 for d in docs for u in d["frames"][-1]["units"] if u["alive"] and u["side"] == side and u["role"] == r) / len(docs))
        start = [sum(1 for u in docs[0]["frames"][0]["units"] if u["side"] == side and u["role"] == r) for side in "AB"]
        rows.append((r, cells[0], cells[1], start[0], start[1]))
    return rows


def _engine_sha():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=20, check=True).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _layout_entry(d, rate_path):
    """(rate dict, the seeds' valid fight docs by seed, the layout table, INVALID messages) for one rated layout."""
    rate = json.loads(rate_path.read_text())
    docs, bad = {}, []
    for s in rate["seeds"]:
        stem = "%s-s%d" % (rate["layout_id"], s)
        try:
            docs[s] = read(Path(d) / (stem + ".fight.json"))
        except (ValueError, OSError) as err:
            bad.append("INVALID %s: %s" % (stem, err))
    median = docs.get(rate["median_seed"]) or next(iter(docs.values()), None)
    return rate, docs, _layout(median["layout_path"]) if median else {}, bad


def _summary_cells(rate, docs, layout):
    """The summary row of one layout as a list of (text, css class)."""
    first = next(iter(docs.values()), None)
    stalls = "%d (%s)" % (rate["stalls"], " ".join(str(s) for s in rate["stall_seeds"]) or "-")
    fc = rate["firing_capable"]
    return [(rate["layout_id"], ""), (layout.get("situation", "-"), ""), (_roles(first, "A") if first else "-", ""), (_roles(first, "B") if first else "-", ""),
            ("%.2f" % rate["predict_rate"], ""), ("%.2f" % rate["rate_a"], ""), _agree_cell(rate, docs),
            (stalls, "stall" if rate["stalls"] else ""), (" ".join(str(s) for s in rate["none_seeds"]) or "-", "none" if rate["none_seeds"] else ""),
            ("%s / %s" % (fc["A"], fc["B"]), ""), (str(rate["median_seed"]), "")]


def _agree_cell(rate, docs=None):
    """The winner-guess verdict; an exact-mirror draw (`agree` null) is flagged, not scored (H-053 Scoring); a layout with an invalid seed is not ranked (F0)."""
    if any(d.get("invalid") for d in (docs or {}).values()):
        return ("invalid, not ranked", "none")
    if rate["agree"] is None:
        return ("mirror: not scored (check the winner for an engine asymmetry)", "")
    word = "agree" if rate["agree"] else "disagree"
    return (word, word)


def _gap_sentence(rate):
    """`heuristic target <p>, measured <m>, gap <n> pts (not scored)`, grey up to the band and amber above it (information, no verdict)."""
    gap = rate.get("band_gap", abs(rate["rate_a"] - rate["predict_rate"]) * 100)
    colour = "gray" if gap <= rate.get("band", 0.10) * 100 else "darkorange"
    return '<p style="color:%s">heuristic target %.2f, measured %.2f, gap %d pts (not scored)</p>' % (colour, rate["predict_rate"], rate["rate_a"], round(gap))


SUMMARY_HEAD = ("id", "situation", "A roles", "B roles", "predicted rate A", "measured rate A", "agree", "stalls (seeds)", "none seeds",
                "firing_capable A / B", "median seed")


def _row_html(cells, tag="td"):
    return "<tr>%s</tr>" % "".join('<%s%s>%s</%s>' % (tag, ' class="%s"' % c if c else "", html.escape(x), tag) for x, c in cells)


def _control_strip(control_dir, layout_id, seed, main_sight=None):
    """The control strip of one seed, with its label (H-088: a sight off control of a sight on fight reads the sight caption, any other the ground one); empty when no control fight file is there or it does not validate."""
    stem = "%s-control-s%d" % (layout_id, seed)
    try:
        doc = read(Path(control_dir) / (stem + ".fight.json"))
    except (ValueError, OSError):
        return ""
    caption = ("control: the same fight with everyone seeing everyone (sight off)" if main_sight == "on" and doc.get("sight") == "off"
               else "control: the same fight without the ground (features emptied)")
    return '<p>%s</p><div class="strip">%s</div>' % (caption, _strip(stem, doc["frames"], stem))


def _control_row(control_dir, layout_id, seed, main_sight=None):
    """The control strip of an unrated fight as a table row; empty when there is none."""
    strip = _control_strip(control_dir, layout_id, seed, main_sight) if control_dir else ""
    return '\n<tr><td colspan="4">%s</td></tr>' % strip if strip else ""


def _layout_block(d, out_dir, rate, docs, layout, bad, control_dir=None, sentences=None):
    """One layout's block (title line, the three sentences, survivors, median seed strip, control strip, seed line)."""
    cells = _summary_cells(rate, docs, layout)
    median = docs.get(rate["median_seed"])
    seeds = []
    for s in rate["seeds"]:
        cls = "stall" if s in rate["stall_seeds"] else "none" if s in rate["none_seeds"] else ""
        seeds.append('<span%s>%d</span>' % (' class="%s"' % cls if cls else "", s))
    survivors = "".join("<tr><td>%s</td><td>%.1f</td><td>%.1f</td><td>%d</td><td>%d</td></tr>" % (html.escape(r), a, b, sa, sb)
                        for r, a, b, sa, sb in _survivors(list(docs.values()))) if docs else ""
    stem = "%s-s%d" % (rate["layout_id"], rate["median_seed"])
    strip = _strip(stem, median["frames"], stem, _first_shot(median["frames"])) if median else ""
    words = _words(layout, (sentences or {}).get(rate["layout_id"], {})) + (_blocked(median) + _first_seen(median) if median else "")
    return ('<h2>%s</h2><table border="1" cellpadding="6">%s%s</table>%s%s<table border="1" cellpadding="4"><tr><th>role</th><th>A mean survivors</th>'
            '<th>B mean survivors</th><th>A start</th><th>B start</th></tr>%s</table><p>median seed %d strip (first shot outlined)</p>'
            '<div class="strip">%s</div>%s<p>seeds: %s</p>%s'
            % (html.escape(rate["layout_id"]), _row_html([(h, "") for h in SUMMARY_HEAD], "th"), _row_html(cells), _gap_sentence(rate), words, survivors, rate["median_seed"], strip,
               _control_strip(control_dir, rate["layout_id"], rate["median_seed"], median.get("sight") if median else None) if control_dir else "", " ".join(seeds), "".join("<p><b>%s</b></p>" % html.escape(m) for m in bad + ["seed %d %s" % (s, _invalid(d)) for s, d in sorted(docs.items()) if d.get("invalid")])))


def build(d, out, control_dir=None, stage=None, sentences=None):
    sentences = _sentences(sentences)
    rate_files = sorted(Path(d).glob("*.rate.json"))
    rated = set()
    entries = []
    for rp in rate_files:
        entry = _layout_entry(d, rp)
        entries.append(entry)
        rated |= {"%s-s%d.fight.json" % (entry[0]["layout_id"], s) for s in entry[0]["seeds"]}
    rows = [_row(p, control_dir, sentences) for p in sorted(Path(d).glob("*.fight.json")) if p.name not in rated]
    head = summary = blocks = ""
    if entries or stage is not None:
        head = ("<h2>%s</h2><p>facing not simulated, abilities off<br>engine %s, %s</p>"
                % (STAGE_WORDS.get(stage, "Stage %s" % stage) if stage is not None else "Arena stage", html.escape(_engine_sha()), datetime.date.today().isoformat()))
    if entries:
        summary = ('<table border="1" cellpadding="6">%s%s</table>' % (_row_html([(h, "") for h in SUMMARY_HEAD], "th"),
                   "".join(_row_html(_summary_cells(r, dd, lay)) for r, dd, lay, _ in sorted(entries, key=lambda e: e[0]["layout_id"]))))
        blocks = "".join(_layout_block(d, Path(out).parent, r, dd, lay, bad, control_dir, sentences) for r, dd, lay, bad in sorted(entries, key=lambda e: e[0]["layout_id"]))
    page = ('<!doctype html><meta charset="utf-8"><title>Arena stage review</title>%s<body><h1>Arena stage review</h1>'
            "%s%s%s<p>Side A blue, side B red. Answer in verdicts.md: | id | verdict | feedback | with verdict A, B, draw or deny.</p>"
            '<table border="1" cellpadding="6">%s</table></body>\n' % (STYLE, head, summary, blocks, "\n".join(rows)))
    Path(out).write_text(page)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--control-dir", help="directory of <id>-control-s<n>.fight.json control fights, shown as a second strip (H-063)")
    ap.add_argument("--stage", type=int, help="the stage number named in the header (4: sight, 3: the ground pushes back, 2: roles and ranges)")
    ap.add_argument("--sentences", help="markdown table | id | What to expect | Approve means | Deny means | overriding the layouts' own sentences")
    args = ap.parse_args(argv)
    return build(args.dir, args.out, args.control_dir, args.stage, args.sentences)


if __name__ == "__main__":
    sys.exit(main())
