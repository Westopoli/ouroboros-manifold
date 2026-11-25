"""LI5 part 1, the comparison table and the artifact page of the lab isolation (docs/northstar/plans/lab-isolation-2026-11-24/spec.md sections 5 and 6; interface:
docs/reports/2026-11-24-li5-interface.md). Reads LI4-FW rows (`isolation_fw.comparison_rows`), arm M summaries and arm V rows as plain data (the shapes of LI3's interface, no import of its
module), and the clip pipeline's `facts.json` files; writes one `index.html` (the A-003 theme form), the ledger row `artifacts-row.md`, and the copied clips. Nothing is judged: a flag is a signal,
a value that was not measured says so and is never 0. No clock, no path, no hash order reaches an output byte. Tests: tests/skilllab/integration/test_isolation_page_*.py."""
import html as _html
import importlib
import json
import re
import shutil
from datetime import date
from pathlib import Path

from scripts.skilllab.arena import isolation_fw as fw

BANNER_KINDS = ("decision", "ask")
VERSIONS = ("then", "now", "fix")
VARIANTS = ("layout", "control")
MAX_CLIP_SET = 4
NOT_PUBLISHED = "not published yet"
NOT_RECORDED = "not recorded"
NONE_YET = "none yet"
FACTS_KEYS = ("version", "first_tick", "last_frame_tick", "engine_sha")


class PageError(ValueError):
    """Bad input; raised before anything is written."""


# ---------------------------------------------------------------- the DRAFT list

def draft_label(name):
    """`DRAFT_OPENING_WINDOW_40` -> `DRAFT-opening-window-40`."""
    if not name.startswith("DRAFT_"):
        raise ValueError("a DRAFT constant starts DRAFT_, not %r" % name)
    return "DRAFT-" + name[len("DRAFT_"):].lower().replace("_", "-")


def collect_drafts():
    """Every module-level DRAFT_* of the isolation modules, name as in the module (arms is read when it is importable; the page never reads its data through it)."""
    out = {}
    for mod in ("isolation_measures", "isolation_fw", "isolation_arms"):
        try:
            m = importlib.import_module("scripts.skilllab.arena." + mod)
        except ImportError:
            continue
        out.update({k: getattr(m, k) for k in dir(m) if k.startswith("DRAFT_")})
    return out


# ---------------------------------------------------------------- reading inputs

def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        raise PageError("%s: %s" % (path, err))


def _read_jsonl(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, ValueError) as err:
        raise PageError("%s: %s" % (path, err))
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except ValueError as err:
            raise PageError("%s:%d: not JSON: %s" % (path, n, err))
        if not isinstance(value, dict):
            raise PageError("%s:%d: not a JSON object" % (path, n))
        out.append(value)
    return out


def read_inputs(*, rows=(), m=(), v=(), repo=None):
    """`rows`: LI4-FW rows files (JSONL); `m`: JSON files of M summaries; `v`: JSONL files of V rows. A file that cannot be read, or a line that is not JSON, is a PageError naming it."""
    all_rows = [r for f in rows for r in _read_jsonl(f)]
    try:
        comparison = fw.comparison_rows(all_rows, repo)
    except (KeyError, IndexError, TypeError, ValueError, OSError) as err:
        raise PageError("the rows files %s do not give a comparison: %s: %s" % ([str(f) for f in rows], type(err).__name__, err))
    summaries = []
    for f in m:
        data = _read_json(f)
        if not isinstance(data, list):
            raise PageError("%s: not a JSON list of M summaries" % f)
        summaries += data
    return {"comparison": comparison, "m_summaries": summaries, "v_rows": [r for f in v for r in _read_jsonl(f)]}


# ---------------------------------------------------------------- text of values

def _e(x):
    return _html.escape(str(x), quote=True)


def _is_nm(value):
    return isinstance(value, str) and value.startswith(fw.NOT_MEASURED)


def not_measured_text(version, value):
    """`not measured: <reason>` -> `not measured at <version> (<reason>)`; `not measured at ...` and any other value stay as they are."""
    if _is_nm(value) and value.startswith("not measured: "):
        return "not measured at %s (%s)" % (version, value[len("not measured: "):])
    return value


def _show(version, value):
    if isinstance(value, str):
        return not_measured_text(version, value)
    if value is None:
        return "none"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return "%g" % value
    if isinstance(value, dict):
        return ", ".join("%s %s" % (k, _show(version, x)) for k, x in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return ", ".join(_show(version, x) for x in value)
    return str(value)


def _score(version, value):
    return "%d:%d" % tuple(value) if isinstance(value, (list, tuple)) else _show(version, value)


def _result_text(c):
    """`A 21:0 t3394 (A 2, B 1)`: the headline cell's winner, survivors and last tick, then the winner counts over the seeds."""
    if c == fw.NOT_RUN:
        return c
    if _is_nm(c["winner"]):
        return not_measured_text(c["version"], c["winner"])
    counts = ", ".join("%s %d" % (_show(c["version"], k), n) for k, n in sorted(c["winner_counts"].items()))
    return "%s %s t%d (%s)" % (c["winner"], _score(c["version"], c["survivors"]), c["last_tick"], counts)


def _standing(c):
    if c == fw.NOT_RUN:
        return c
    if _is_nm(c["winner"]):
        return not_measured_text(c["version"], c["winner"])
    a, b = c["survivors"]
    if c["winner"] in ("A", "B"):
        return "side %s won with %d standing" % (c["winner"], a if c["winner"] == "A" else b)
    return "%s, A %d and B %d standing" % (c["winner"], a, b)


def _flags_html(names):
    return " ".join('<span class="flag" data-flag="%s">signal: %s</span>' % (_e(n), _e(n)) for n in names) or "none"


def _td(col, inner):
    return '<td data-col="%s">%s</td>' % (col, inner)


def _table(name, cols, body):
    head = "".join('<th data-col="%s">%s</th>' % (c, c.replace("_", " ")) for c in cols)
    return '<div class="tablewrap"><table data-table="%s"><thead><tr>%s</tr></thead><tbody>\n%s</tbody></table></div>' % (name, head, "\n".join(body) + "\n")


def _section(name, title, inner, note=""):
    small = '<p class="small">%s</p>' % _e(note) if note else ""
    return '<section data-section="%s" class="card"><h2>%s</h2>%s\n%s</section>' % (name, _e(title), small, inner)


# ---------------------------------------------------------------- comparison and sentences

def _ruling_text(r):
    ru = r["ruling"]
    return '"%s" %s; %s; predict_rate %g; stage 3 approval %s: "%s"' % (ru["words"], ru["date"], ru["per_picture"], r["predict_rate"], ru["stage_approval"]["date"], ru["stage_approval"]["words"])


def _change_text(r):
    verdict = r["same_or_changed"]
    if verdict == fw.NOT_RUN:
        return verdict
    if _is_nm(verdict):
        version = next((v for v in ("then", "now") if r[v] != fw.NOT_RUN and _is_nm(r[v]["winner"])), "now")
        return not_measured_text(version, verdict)
    n = r["seeds_flipped"]
    head = "same" if verdict == "same" else "changed, %d seed%s flipped" % (n, "" if n == 1 else "s")
    return "%s (DRAFT-same-or-changed-rule: %s)" % (head, r["rule"])


def _sentences(comparison):
    ps = []
    for r in comparison:
        parts = ["%s, %s" % (v, _standing(r[v])) for v in VERSIONS if r[v] != fw.NOT_RUN]
        ps.append('<p data-sentence="%s">%s: %s.</p>' % (r["layout"], r["layout"], _e("; ".join(parts) or fw.NOT_RUN)))
    return _section("sentences", "In soldiers", "\n".join(ps) or "<p>No comparison rows were given.</p>")


def _comparison(comparison, clip_sets):
    if not comparison:
        return _section("comparison", "Comparison", "<p>No comparison rows were given.</p>")
    has_fix = any(r["fix"] != fw.NOT_RUN for r in comparison)
    versions = ("then", "now", "fix") if has_fix else ("then", "now")
    cols = ["layout", "ruling", *versions, "change", "first_arm"]
    body = []
    for r in comparison:
        layout, links = _e(r["layout"]), ""
        if r["same_or_changed"] == "changed":
            links = "".join(' <a data-clipset="%s" href="#%s">clip %s</a>' % (_e(s["id"]), _e(s["id"]), _e(s["id"])) for s in clip_sets if s["row"] == r["layout"])
        cells = [_td("layout", layout + links), _td("ruling", _e(_ruling_text(r)))] + [_td(v, _e(_result_text(r[v]))) for v in versions]
        body.append('<tr data-layout="%s">%s</tr>' % (layout, "".join(cells + [_td("change", _e(_change_text(r))), _td("first_arm", _e(r["first_differing_arm"]))])))
        if r["same_or_changed"] == "changed":
            twin = [_td("layout", "control twin"), "<td></td>"] + [_td(v, _e(_result_text(r["control"][v]))) for v in versions] + ["<td></td>", "<td></td>"]
            body.append('<tr data-layout="%s" data-variant="control">%s</tr>' % (r["layout"], "".join(twin)))
    return _section("comparison", "Comparison, then against now", _table("comparison", cols, body),
                    "His ruling beside each result; a result is the winner at the headline seed with the winner counts over the seeds. Same or changed is a count, never better or worse.")


# ---------------------------------------------------------------- arms W and F

def _firing_html(version, uf):
    if not isinstance(uf, dict):
        return _e(_show(version, uf))
    frames = uf["by_frame"]
    if not frames:
        return "no frames"
    t0, t1 = frames[0][0], frames[-1][0]
    top = max(1, max(max(f[1], f[2]) for f in frames))

    def points(i):
        return " ".join("%.1f,%.1f" % (2 + 236 * ((f[0] - t0) / (t1 - t0) if t1 > t0 else 0), 58 - 56 * f[i] / top) for f in frames)
    lines = "".join('<polyline class="line-%s" data-side="%s" aria-label="side %s units firing" fill="none" points="%s"></polyline>' % (s.lower(), s, s, points(i)) for s, i in (("A", 1), ("B", 2)))
    legend = "units firing, side A (blue line) peak %d, side B (red line) peak %d, tick %d to %d" % (max(f[1] for f in frames), max(f[2] for f in frames), t0, t1)
    return '<svg viewBox="0 0 240 60" role="img" data-lines="units_firing"><title>units firing per frame, side A and side B</title>%s</svg><div class="small">%s</div>' % (lines, legend)


def _arm_entries(comparison, arm):
    out = []
    for r in comparison:
        for v in VERSIONS:
            if arm == "W":
                pair = (("layout", r[v]), ("control", r["control"][v]))
            else:
                pair = tuple((variant, r["f"][v][variant]) for variant in VARIANTS) if r["f"][v] != fw.NOT_RUN else ()
            out += [(r["layout"], variant, v, c) for variant, c in pair if c != fw.NOT_RUN]
    return out


def _arm_table(arm, entries):
    cols = ["layout", "variant", "version", "winner", "survivors", "last_tick", "end", "invalid", "agreement", "units_firing", "flags"]
    body = []
    for layout, variant, v, c in entries:
        sh = lambda x: _e(_show(c["version"], x))
        invalid = c["invalid"]
        names = (["defect"] if c["defect"] is True else []) + (["invalid"] if isinstance(invalid, list) and invalid else [])
        cells = [layout, variant, v, sh(c["winner"]), _e(_score(c["version"], c["survivors"])), sh(c["last_tick"]), sh(c["end"]),
                 _e(", ".join(invalid) or "none") if isinstance(invalid, list) else sh(invalid), sh(c["predictions"]["agreement"]),
                 _firing_html(c["version"], c["units_firing"]), _flags_html(names)]
        body.append('<tr data-layout="%s" data-variant="%s" data-version="%s">%s</tr>' % (layout, variant, v, "".join(_td(k, x) for k, x in zip(cols, cells))))
    return _table("arm-" + arm, cols, body)


# ---------------------------------------------------------------- arms M and V

def _m_block(s):
    v = s["version"]
    after = {f["after"]: f["direction"] for f in s["flips"]}
    body = []
    for p in s["points"]:
        flip = after.get(p["enemy_heads"])
        won = "defect" if p["defect"] else "won" if p["won"] else "lost"
        cells = [p["enemy_heads"], won, flip or "none", _show(v, p["mean_margin"]), _show(v, p["orders_ended_short"])]
        body.append('<tr data-enemy="%d"%s>%s</tr>' % (p["enemy_heads"], ' data-flip="true"' if flip else "", "".join(_td(k, _e(x)) for k, x in zip(("enemy", "won", "flip", "mean_margin", "orders_ended_short"), cells))))
    stops = [r["stopping"] for r in s["rows"] if isinstance(r.get("stopping"), dict)]
    counts = [st["orders_ended_short"] for st in stops]
    said = "; ".join(sorted({c for c in counts if not isinstance(c, int)})) or str(sum(counts))
    units = [u for st in stops for u in st["units"]]
    li = "".join('<li data-unit-id="%s">unit %s, tick %s, at x %g, y %g</li>' % (_e(u["id"]), _e(u["id"]), _e(u["tick"]), u["x"], u["y"]) for u in units)
    flags = sorted({f for r in s["rows"] for f in r.get("flags", [])})
    head = "%s, own %d, movement %s; beats %s, loses to %s (the points below); part word %s" % (v, s["own"], s["movement"], _show(v, s["beats"]), _show(v, s["loses_to"]), s["part_word"])
    badge = ' <span class="badge blocks">blocks</span>' if s["blocks"] is True else ""
    return ('<div class="mblock" data-version="%s"%s><h3>%s%s</h3><p>%s</p>%s<p class="mono">orders ended short: %s</p>%s</div>'
            % (_e(v), ' data-multi-flip="true"' if s["multi_flip"] else "", _e(head), badge, _flags_html(flags),
               _table("arm-M", ("enemy", "won", "flip", "mean_margin", "orders_ended_short"), body), _e(said), "<ul>%s</ul>" % li if li else ""))


def _v_table(rows):
    cols = ["layout", "kind", "version", "part_word", "sensor", "notice", "first_seen", "standoff_count", "first_shot_tick", "twin", "flags"]
    body = []
    for r in rows:
        v, vis = r["version"], r["vision"]
        get = lambda k: vis[k] if isinstance(vis, dict) else vis
        twin = r["twin"]
        twin = "sight %s: %s %s t%d %s" % (twin["sight"], twin["result"]["winner"], _score(v, twin["result"]["survivors"]), twin["result"]["last_tick"], twin["result"]["end"]) if isinstance(twin, dict) else twin
        cells = [r["layout"], r["kind"], v, r["part_word"], get("sensor"), get("notice"), get("first_seen"), get("standoff_count"), get("first_shot_tick"), twin]
        body.append('<tr data-layout="%s" data-kind="%s" data-version="%s">%s%s</tr>' % (_e(r["layout"]), _e(r["kind"]), _e(v), "".join(_td(k, _e(_show(v, x))) for k, x in zip(cols, cells)), _td("flags", _flags_html(r["flags"]))))
    return _table("arm-V", cols, body)


# ---------------------------------------------------------------- drafts, shas

def _drafts(drafts):
    li = "".join('<li data-draft="%s"><code>%s</code>: %s</li>' % (draft_label(k), draft_label(k), _e(_show("", drafts[k]))) for k in sorted(drafts))
    return _section("drafts", "DRAFT list", "<ul>%s</ul>" % li, "These numbers are drafts; every threshold and tolerance is Westley's to set.")


def _lab_shas(inputs):
    found = {}

    def add(c):
        if isinstance(c, dict) and c.get("lab_sha"):
            found.setdefault(c["version"], set()).add(c["lab_sha"])
    for arm in ("W", "F"):
        for _, _, _, c in _arm_entries(inputs["comparison"], arm):
            add(c)
    for x in inputs["m_summaries"] + inputs["v_rows"]:
        add(x)
    return found


def _version_order(shas):
    return [x for x in VERSIONS if x in shas] + sorted(set(shas) - set(VERSIONS))


def _shas(shas, clip_sets):
    labs = "".join('<li data-version="%s">%s: %s</li>' % (_e(v), _e(v), " ".join("<code>%s</code>" % s for s in sorted(shas[v]))) for v in _version_order(shas))
    clips = "".join('<li data-clip="%s">clip %s: engine <code>%s</code></li>' % (_e(c["name"]), _e(c["name"]), _e(c["engine"])) for s in clip_sets for c in s["clips"])
    return _section("shas", "Lab and engine shas", "<ul>%s</ul>%s" % (labs, "<ul>%s</ul>" % clips if clips else ""), "Lab and engine are one tree; each clip names the engine it was rendered with.")


# ---------------------------------------------------------------- clips

def _need(doc, path, *keys):
    node = doc
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            raise PageError("%s: no key %s" % (path, ".".join(keys)))
        node = node[k]
    return node


def load_clips(manifest):
    """The clip sets of a manifest with every file checked: [{id, layout, seed, row, why, clips: [{name, poster, version, first, last, engine, sha256, video_src, poster_src}]}]."""
    path = Path(manifest)
    sets, seen, dest = [], set(), {}
    for entry in _need(_read_json(path), path, "sets"):
        sid = _need(entry, path, "id")
        if sid in seen:
            raise PageError("%s: clip set %s twice" % (path, sid))
        seen.add(sid)
        paths = _need(entry, path, "facts")
        if not 1 <= len(paths) <= MAX_CLIP_SET:
            raise PageError("%s: clip set %s has %d clips, one to %d are placed" % (path, sid, len(paths), MAX_CLIP_SET))
        clips = []
        for rel in paths:
            fpath = path.parent / rel
            doc = _read_json(fpath)
            c = {"version": _need(doc, fpath, "version"), "first": _need(doc, fpath, "first_tick"), "last": _need(doc, fpath, "last_frame_tick"), "engine": _need(doc, fpath, "engine_sha"),
                 "name": _need(doc, fpath, "video", "file"), "sha256": _need(doc, fpath, "video", "sha256"), "poster": _need(doc, fpath, "poster", "file")}
            c["video_src"], c["poster_src"] = fpath.parent / c["name"], fpath.parent / c["poster"]
            for src in (c["video_src"], c["poster_src"]):
                if not src.is_file():
                    raise PageError("%s: the file %s does not exist" % (fpath, src))
                if dest.setdefault(src.name, src) != src:
                    raise PageError("%s: two clips are both named %s" % (path, src.name))
            clips.append(c)
        sets.append({"id": sid, "layout": _need(entry, path, "layout"), "seed": _need(entry, path, "seed"), "row": _need(entry, path, "row"), "why": _need(entry, path, "why"), "clips": clips})
    return sets


TRANSPORT = """<div class="transport">
<div class="group"><button data-play aria-label="Play or pause">Play</button></div>
<input type="range" data-scrub min="0" max="1000" value="0" aria-label="Scrub all clips">
<span class="readout">tick <span data-tk>%d</span></span>
<div class="group"><span class="label">Speed</span><button data-rate="0.25">0.25x</button><button data-rate="0.5">0.5x</button><button data-rate="1" aria-pressed="true">1x</button><button data-rate="2">2x</button></div>
<div class="group"><span class="label">Step</span><button data-step="-1">&#9664; 2 ticks</button><button data-step="1">2 ticks &#9654;</button></div>
</div>"""


def _clips(clip_sets):
    out = []
    for s in clip_sets:
        figs = []
        for c in s["clips"]:
            cap = ('<figcaption><b>%s</b> <span>%s, seed %s</span> <span>tick %s to %s</span> <span>row %s</span> <span class="small">%s</span></figcaption>'
                   % (_e(c["version"]), _e(s["layout"]), _e(s["seed"]), _e(c["first"]), _e(c["last"]), _e(s["row"]), _e(s["why"])))
            single = len(s["clips"]) == 1
            figs.append('<figure><video %spreload="metadata" playsinline %sposter="clips/%s" src="clips/%s"></video>%s</figure>' % ("controls " if single else "", "" if single else "muted ", _e(c["poster"]), _e(c["name"]), cap))
        if len(figs) == 1:
            inner = figs[0]
        else:
            first, last = min(c["first"] for c in s["clips"]), max(c["last"] for c in s["clips"])
            inner = '<div class="bench grid" data-bench="true" data-first="%s" data-last="%s">%s</div>\n%s' % (first, last, "\n".join(figs), TRANSPORT % first)
        out.append('<section id="%s" class="card"><h3>%s</h3>\n%s</section>' % (_e(s["id"]), _e(s["id"]), inner))
    return '<section data-section="clips" class="card"><h2>Clips</h2>\n%s</section>' % "\n".join(out)


# ---------------------------------------------------------------- the page

CSS = """/* Layout: the decision banner first, the comparison table, then the arm tables, the DRAFT list, the shas and the clips. */
:root {
  --bg: #f3f5f6; --panel: #ffffff; --fg: #1b2329; --muted: #5b6871; --line: #d5dde2;
  --accent: #0f7c86; --blue: #2459c9; --red: #c23a2b; --warn: #a15c00; --warn-bg: #fff3e0;
  --sans: "IBM Plex Sans", system-ui, -apple-system, Segoe UI, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #12181c; --panel: #1a2227; --fg: #e4eaee; --muted: #93a2ab; --line: #2c373e;
  --accent: #3fb8c2; --blue: #7ea2f2; --red: #f08070; --warn: #f0b060; --warn-bg: #2b2215; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #12181c; --panel: #1a2227; --fg: #e4eaee; --muted: #93a2ab; --line: #2c373e;
  --accent: #3fb8c2; --blue: #7ea2f2; --red: #f08070; --warn: #f0b060; --warn-bg: #2b2215; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font-family: var(--sans); font-size: 15px; line-height: 1.55;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 28px 48px; }
.wrap { max-width: 1280px; margin: 0 auto; display: grid; gap: 26px; }
h1 { font-size: 26px; font-weight: 600; margin: 0; text-wrap: balance; }
h2 { font-size: 19px; font-weight: 600; margin: 0; text-wrap: balance; }
h3 { font-size: 15px; font-weight: 600; margin: 0; }
.eyebrow { font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
code, .mono { font-family: var(--mono); font-size: 13px; overflow-wrap: anywhere; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px; display: grid; gap: 10px; min-width: 0; }
.card p { margin: 0; max-width: 84ch; }
.decide { border-left: 4px solid var(--warn); }
.small { font-size: 13px; color: var(--muted); }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
@media (max-width: 760px) { .grid { grid-template-columns: minmax(0, 1fr); } }
figure { margin: 0; display: grid; gap: 6px; min-width: 0; }
figcaption { display: flex; flex-wrap: wrap; gap: 4px 10px; align-items: baseline; font-size: 14px; }
video { width: 100%; max-width: 100%; aspect-ratio: 16 / 9; background: #000; border-radius: 6px; display: block; }
svg { display: block; width: 100%; max-width: 240px; height: auto; }
polyline { stroke-width: 1.5; }
.line-a { stroke: var(--blue); } .line-b { stroke: var(--red); }
.flag { display: inline-block; font: 500 12px var(--mono); padding: 1px 8px; border-radius: 99px; border: 1px solid var(--warn); color: var(--warn); }
.badge { display: inline-block; font: 600 12px var(--mono); padding: 1px 8px; border-radius: 4px; background: var(--red); color: var(--panel); }
.mblock { display: grid; gap: 8px; min-width: 0; }
.transport { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center; }
.transport .group { display: flex; gap: 4px; align-items: center; flex-wrap: wrap; }
.transport .label { font-size: 12px; color: var(--muted); margin-right: 2px; }
button { font: 500 13px var(--sans); color: var(--fg); background: var(--bg); border: 1px solid var(--line); border-radius: 5px; padding: 5px 10px; cursor: pointer; }
button:hover { border-color: var(--accent); }
button:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
button[aria-pressed="true"] { background: var(--accent); color: var(--panel); border-color: var(--accent); }
input[type="range"] { flex: 1 1 260px; min-width: 160px; accent-color: var(--accent); }
.readout { font-family: var(--mono); font-size: 14px; font-variant-numeric: tabular-nums; padding: 4px 10px; border-radius: 5px; background: var(--bg); border: 1px solid var(--line); }
.tablewrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 14px; font-variant-numeric: tabular-nums; }
th, td { text-align: left; vertical-align: top; padding: 6px 10px; border-bottom: 1px solid var(--line); }
td[data-col="ruling"] { min-width: 280px; }
th { color: var(--muted); font-weight: 500; font-size: 12.5px; white-space: nowrap; }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto; } }"""

# The clip transport is the A-003 one (FPS and TPF are the clip pipeline's 20 frames a second and one frame per 2 ticks), without its moment buttons.
SCRIPT = """(function () {
  const FPS = 20, TPF = 2;
  document.querySelectorAll("[data-bench]").forEach(function (bench) {
    const sec = bench.parentElement;
    const vids = Array.from(bench.querySelectorAll("video"));
    const tr = sec.querySelector(".transport");
    const first = Number(bench.dataset.first);
    const scrub = tr.querySelector("[data-scrub]"), tk = tr.querySelector("[data-tk]"), playBtn = tr.querySelector("[data-play]");
    let rate = 1, playing = false, seeking = false;
    const dur = function () { return Math.max.apply(null, vids.map(function (v) { return v.duration || 0; })); };
    const toTick = function (t) { return first + Math.round(t * FPS) * TPF; };
    const seek = function (t) { vids.forEach(function (v) { v.currentTime = Math.min(Math.max(0, t), v.duration || t); }); };
    const show = function () {
      const t = vids[0].currentTime; tk.textContent = toTick(t).toLocaleString("en-US");
      const d = dur(); if (d && !seeking) scrub.value = String(Math.round(t / d * 1000));
    };
    const setPlay = function (on) {
      playing = on; playBtn.textContent = on ? "Pause" : "Play";
      vids.forEach(function (v) { v.playbackRate = rate; if (on) { v.play().catch(function () {}); } else { v.pause(); } });
    };
    playBtn.addEventListener("click", function () { setPlay(!playing); });
    vids[0].addEventListener("timeupdate", show);
    vids.forEach(function (v) { v.addEventListener("ended", function () { v.pause(); }); });
    vids[0].addEventListener("ended", function () { if (vids.every(function (v) { return v.ended || v.paused; })) setPlay(false); });
    scrub.addEventListener("input", function () { seeking = true; setPlay(false); seek(Number(scrub.value) / 1000 * dur()); show(); });
    scrub.addEventListener("change", function () { seeking = false; });
    tr.querySelectorAll("[data-rate]").forEach(function (b) {
      b.addEventListener("click", function () {
        rate = Number(b.dataset.rate); vids.forEach(function (v) { v.playbackRate = rate; });
        tr.querySelectorAll("[data-rate]").forEach(function (o) { o.setAttribute("aria-pressed", String(o === b)); });
      });
    });
    tr.querySelectorAll("[data-step]").forEach(function (b) {
      b.addEventListener("click", function () { setPlay(false); seek(vids[0].currentTime + Number(b.dataset.step) / FPS); });
    });
  });
})();"""


def _check_ledger(ledger):
    for key in ("id", "date", "title"):
        if not isinstance(ledger.get(key), str) or not ledger[key].strip():
            raise PageError("the ledger needs %s" % key)
    try:
        if not re.fullmatch(r"\d{4}-\d\d-\d\d", ledger["date"]):
            raise ValueError
        date.fromisoformat(ledger["date"])
    except ValueError:
        raise PageError("the ledger date is YYYY-MM-DD, not %r" % ledger["date"])


def _cell(text):
    return str(text).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _ledger_row(ledger, arms, comparison, shas, clip_sets):
    code = ["%s %s" % (v, sha) for v in _version_order(shas) for sha in sorted(shas[v])]
    code += ["clip %s video sha256 %s" % (c["name"], c["sha256"]) for s in clip_sets for c in s["clips"]]
    code.append("artifacts/%s/page.html" % ledger["id"])
    n = len(clip_sets)
    shows = "layouts %s; arms %s; %d clip set%s" % (", ".join(r["layout"] for r in comparison), ", ".join(arms), n, "" if n == 1 else "s")
    cells = [ledger["id"], ledger.get("url") or NOT_PUBLISHED, ledger["date"], ledger["title"], shows, ledger.get("why") or NOT_RECORDED, "; ".join(code), NONE_YET, NONE_YET, "current"]
    return "| " + " | ".join(_cell(c) for c in cells) + " |\n"


def build_page(out_dir, *, banner, banner_kind="decision", inputs, clips=None, drafts=None, ledger):
    """Writes `index.html`, `artifacts-row.md` and, with a clips manifest, the media under `clips/` into `out_dir`; everything is checked first, so a PageError leaves nothing written."""
    if banner_kind not in BANNER_KINDS:
        raise PageError("the banner kind is one of %s, not %r" % (", ".join(BANNER_KINDS), banner_kind))
    _check_ledger(ledger)
    clip_sets = load_clips(clips) if clips else []
    comparison, m_summaries, v_rows = inputs["comparison"], inputs.get("m_summaries", []), inputs.get("v_rows", [])
    shas = _lab_shas({"comparison": comparison, "m_summaries": m_summaries, "v_rows": v_rows})
    w, f = _arm_entries(comparison, "W"), _arm_entries(comparison, "F")
    present = {"M": m_summaries, "V": v_rows, "W": w, "F": f}
    arms = [a for a in fw.ARM_ORDER if present.get(a)]
    sections = [_sentences(comparison), _comparison(comparison, clip_sets)]
    if m_summaries:
        sections.append(_section("arm-M", "Arm M, the break-even map", "\n".join(_m_block(s) for s in m_summaries), "Every point is a row; a flip is marked on the point after it. A flag is a signal, not a verdict."))
    if v_rows:
        sections.append(_section("arm-V", "Arm V, vision", _v_table(v_rows), "A flag is a signal, not a verdict."))
    if w:
        sections.append(_section("arm-W", "Arm W, the whole", _arm_table("W", w), "The layout as authored and its control twin. A flag is a signal, not a verdict."))
    if f:
        sections.append(_section("arm-F", "Arm F, one factor", _arm_table("F", f), "Every unit Vanguard at Vanguard's range, and its control twin. A flag is a signal, not a verdict."))
    sections += [_drafts(collect_drafts() if drafts is None else drafts), _shas(shas, clip_sets)]
    if clip_sets:
        sections.append(_clips(clip_sets))
    eyebrow, kind = ("Decision waiting for you", "decision") if banner_kind == "decision" else ("A question for you", "ask")
    top = '<section data-section="banner" data-banner="%s" class="card decide"><div class="eyebrow">%s</div><p>%s</p></section>' % (kind, eyebrow, _e(banner))
    head = '<header><div class="eyebrow">Ouroboros Manifold &middot; lab isolation &middot; %s</div><h1>%s</h1></header>' % (_e(ledger["date"]), _e(ledger["title"]))
    page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<meta name=\"claude:viewport-fit-sides\" content=\"cover\">\n<title>%s</title>\n"
            "<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap\">\n"
            "<style>\n%s\n</style>\n</head>\n<body>\n<div class=\"wrap\">\n%s\n%s\n%s\n</div>\n%s</body>\n</html>\n"
            % (_e(ledger["title"]), CSS, top, head, "\n".join(sections), "<script>\n%s\n</script>\n" % SCRIPT if clip_sets else ""))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if clip_sets:
        (out / "clips").mkdir(exist_ok=True)
        for s in clip_sets:
            for c in s["clips"]:
                shutil.copyfile(c["video_src"], out / "clips" / c["name"])
                shutil.copyfile(c["poster_src"], out / "clips" / c["poster"])
    (out / "index.html").write_bytes(page.encode("ascii", "xmlcharrefreplace"))
    (out / "artifacts-row.md").write_bytes(_ledger_row(ledger, arms, comparison, shas, clip_sets).encode("utf-8"))
    return {"index": out / "index.html", "row": out / "artifacts-row.md"}


# ---------------------------------------------------------------- the command line

def main(argv=None):
    import argparse
    import sys
    ap = argparse.ArgumentParser(prog="isolation_page", description="Write the lab isolation artifact page and its ledger row.")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--banner", required=True)
    ap.add_argument("--banner-kind", choices=BANNER_KINDS, default="decision")
    ap.add_argument("--rows", nargs="+", default=[], type=Path, help="LI4-FW rows files (JSONL)")
    ap.add_argument("--m", nargs="+", default=[], type=Path, help="files of M summaries (JSON lists)")
    ap.add_argument("--v", nargs="+", default=[], type=Path, help="files of V rows (JSONL)")
    ap.add_argument("--clips", type=Path, help="the clips manifest")
    ap.add_argument("--id", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--why")
    ap.add_argument("--url")
    ap.add_argument("--repo", type=Path)
    a = ap.parse_args(argv)
    try:
        inputs = read_inputs(rows=a.rows, m=a.m, v=a.v, repo=a.repo)
        build_page(a.out, banner=a.banner, banner_kind=a.banner_kind, inputs=inputs, clips=a.clips, ledger={"id": a.id, "date": a.date, "title": a.title, "why": a.why, "url": a.url})
    except PageError as err:
        print("isolation_page: %s" % err, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
