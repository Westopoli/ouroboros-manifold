# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md sections 5 and 6, piece LI5 part 1 (the comparison table and the artifact page generator)
"""Helpers shared by test_isolation_page_*.py. Interface: docs/reports/2026-11-24-li5-interface.md. The module under test is imported lazily so a missing module fails each test (red), not the
collection. Three things live here: a small DOM over `html.parser` plus the page checkers (each one is shown green on the standing page A-003 and red on a planted bad snippet in
test_isolation_page_controls.py), synthetic inputs built to the shapes of the LI1, LI3 and LI4-FW interfaces, and the real-run fixture.

Premises dumped 2026-11-24 on this branch (li4 base, scratch engine-rules-baseline/li5/): `isolation_fw.comparison_rows` accepts the synthetic LI4 rows below (a positive control runs it on them, no
fight needed); a short real run `run_arms(["then", "now"], layouts=("L-0039",), arms=("W",), seeds=(10,))` is 4 fights: then layout cap 8:8 t12000, then twin A 3:0 t2606, now layout A 2:0 t3081,
now twin B 0:5 t2352 (isolation_fw_real.FACTS); the then fights have no per-unit `fired` (units firing `not measured: ...` in the cell, `not measured at then` in the row) and no rule checker
(`invalid` is `not measured at then`); the A-003 page (copy in data/a003_page.html) has no `<html>` or `<body>` tag and one inline `<script>`."""
import hashlib
import importlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import isolation_fixtures as fx
from isolation_fw_real import FACTS, WORDS, STAGE_WORDS, STAGE_DATE  # noqa: F401  (re-exported for the tests)

ROOT = fx.ROOT
A003 = Path(__file__).parent / "data" / "a003_page.html"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
THEME_TOKENS = ("--bg", "--panel", "--fg", "--muted", "--line", "--accent", "--blue", "--red", "--warn", "--warn-bg")
SCRIPT_HOSTS = ("cdnjs.cloudflare.com", "cdn.jsdelivr.net")
FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
SHA = {"then": "4fa618ce78349fcc077ce552753131e737ae2cea", "now": "893a5af7fc54de5bb238a5fabb528e2ddf70ed91"}
LEDGER = {"id": "A-005", "date": "2026-11-24", "title": "Lab isolation, stage 3", "why": 'He asked: "go back to stage 3 and do some movement/vision only isolation testing" | verbatim'}
BANNER = 'Decide: is "L-0084 changed" a result you accept? <b>&</b> not markup'
ARM_KEYS = ("M", "V", "R", "F", "P", "W")


def page():
    return importlib.import_module("scripts.skilllab.arena.isolation_page")


def fw():
    return importlib.import_module("scripts.skilllab.arena.isolation_fw")


# ---------------------------------------------------------------- a small DOM

class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []

    def cls(self):
        return (self.attrs.get("class") or "").split()

    def walk(self):
        yield self
        for k in self.kids:
            if isinstance(k, Node):
                yield from k.walk()

    def text(self):
        """Visible text: no style or script content, whitespace folded."""
        if self.tag in ("style", "script"):
            return ""
        return re.sub(r"\s+", " ", " ".join(k.text() if isinstance(k, Node) else k for k in self.kids)).strip()

    def find(self, tag=None, **attrs):
        out = []
        for n in self.walk():
            if tag and n.tag != tag:
                continue
            if all((n.attrs.get(k.replace("_", "-")) == v) if v is not True else (k.replace("_", "-") in n.attrs) for k, v in attrs.items()):
                out.append(n)
        return out

    def one(self, tag=None, **attrs):
        (n,) = self.find(tag, **attrs)
        return n

    def inside(self, tag=None, cls=None):
        n = self.parent
        while n is not None:
            if (tag is None or n.tag == tag) and (cls is None or cls in n.cls()):
                return True
            n = n.parent
        return False


class Malformed(ValueError):
    pass


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root
        self.order = []

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.cur.tag != tag:
            raise Malformed("</%s> closes <%s>" % (tag, self.cur.tag))
        self.cur = self.cur.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(html):
    """The page as a Node tree; Malformed for an end tag that closes the wrong tag or a tag left open."""
    b = _Builder()
    b.feed(html)
    b.close()
    if b.cur is not b.root:
        raise Malformed("<%s> never closed" % b.cur.tag)
    return b.root


def css_of(root):
    return "\n".join("".join(k for k in n.kids if isinstance(k, str)) for n in root.find("style"))


def rule_body(css, selector_re):
    """The text between the braces of the first rule whose selector matches `selector_re`; None when none."""
    m = re.search(selector_re + r"\s*\{", css)
    if not m:
        return None
    depth, i = 1, m.end()
    while depth and i < len(css):
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        i += 1
    return css[m.end():i - 1]


def tokens_in(body):
    return set(re.findall(r"(--[a-z-]+)\s*:", body or ""))


# ---------------------------------------------------------------- the page checkers (each returns a list of problems)

def problems_theme(css):
    out = []
    light = rule_body(css, r"(?<![\w\]\)-]):root(?![\w:\[-])")
    if light is None or not set(THEME_TOKENS) <= tokens_in(light):
        out.append("`:root` lacks tokens %s" % sorted(set(THEME_TOKENS) - tokens_in(light)))
    media = re.search(r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{\s*:root:not\(\[data-theme=\"light\"\]\)\s*\{", css)
    auto = rule_body(css, r':root:not\(\[data-theme="light"\]\)')
    forced = rule_body(css, r':root\[data-theme="dark"\]')
    if not media or auto is None:
        out.append('no `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {`')
    if forced is None:
        out.append('no `:root[data-theme="dark"]`')
    for name, body in (("auto dark", auto), ("forced dark", forced)):
        if body is not None and not set(THEME_TOKENS) <= tokens_in(body):
            out.append("%s block lacks %s" % (name, sorted(set(THEME_TOKENS) - tokens_in(body))))
    return out


def problems_body_background(css):
    body = rule_body(css, r"(?:^|[}\s,])body")
    return [] if body and re.search(r"background(-color)?\s*:\s*var\(--[a-z-]+\)", body) else ["no `body { background: var(--...) }`"]


def problems_no_hero(css):
    return ["`%s` in the css" % m for m in re.findall(r"100[dsl]?vh", css)]


def problems_hosts(html):
    """Every http(s) URL is from Google Fonts or a pinned script host; every `<script src>` is cdnjs or jsdelivr with a version in the path."""
    out = []
    for url in re.findall(r"""(?:https?:)?//[^\s"'<>)]+""", re.sub(r"<script>.*?</script>", "", html, flags=re.S)):
        host = re.sub(r"^(?:https?:)?//", "", url).split("/")[0]
        if host not in FONT_HOSTS + SCRIPT_HOSTS:
            out.append("host %s" % host)
    for n in parse(html).find("script"):
        src = n.attrs.get("src")
        if src is None:
            continue
        host = re.sub(r"^(?:https?:)?//", "", src).split("/")[0]
        pinned = re.search(r"/ajax/libs/[^/]+/\d+\.\d+\.\d+/", src) if host == "cdnjs.cloudflare.com" else re.search(r"/npm/[^/@]+@\d+\.\d+\.\d+", src)
        if host not in SCRIPT_HOSTS or not pinned:
            out.append("script src %s" % src)
    for n in parse(html).find("link", rel="stylesheet"):
        if re.sub(r"^(?:https?:)?//", "", n.attrs.get("href", "")).split("/")[0] not in FONT_HOSTS:
            out.append("stylesheet %s" % n.attrs.get("href"))
    return out


def problems_media(root, out_dir=None):
    """Every video and poster is a relative path (and the file exists in `out_dir` when given); every video has a poster."""
    out = []
    for v in root.find("video"):
        for attr in ("src", "poster"):
            val = v.attrs.get(attr)
            if not val:
                out.append("video without %s" % attr)
            elif re.match(r"^([a-z]+:|/|\.\./|~)", val):
                out.append("%s not relative: %s" % (attr, val))
            elif out_dir is not None and not (Path(out_dir) / val).is_file():
                out.append("%s missing in the output: %s" % (attr, val))
    return out


def problems_mobile(root, css):
    """No horizontal page scroll: tables sit in a scrolling wrap, the grid collapses under a width query, video and svg cannot exceed the column."""
    out = []
    if not re.search(r"\.tablewrap\s*\{[^}]*overflow-x\s*:\s*auto", css):
        out.append("no .tablewrap with overflow-x: auto")
    out += ["table outside .tablewrap" for t in root.find("table") if not t.inside(cls="tablewrap")]
    if not re.search(r"@media\s*\(max-width:\s*\d+px\)", css):
        out.append("no max-width media query")
    if not re.search(r"video\s*\{[^}]*max-width\s*:\s*100%", css):
        out.append("video can exceed the column")
    out += ["svg without viewBox" for s in root.find("svg") if "viewBox" not in s.attrs and "viewbox" not in s.attrs]
    out += ["svg with a fixed width" for s in root.find("svg") if re.fullmatch(r"\d+(px)?", s.attrs.get("width", ""))]
    return out


def all_problems(html, out_dir=None):
    root = parse(html)
    css = css_of(root)
    return (problems_theme(css) + problems_body_background(css) + problems_no_hero(css) + problems_hosts(html) + problems_media(root, out_dir) + problems_mobile(root, css))


# ---------------------------------------------------------------- synthetic rows (LI4-FW shape; `fw.comparison_rows` accepts them)

NM_FIRED = "not measured: the fight file has no per-unit fired flag"


def firing(frames):
    """LI2 units_firing over `frames` [[tick, A, B], ...]."""
    return {"by_frame": frames, "first_contact": frames[0][0], "window_ticks": 40, "window": [1.0, 1.0], "whole": [2.0, 2.0],
            "peak": [max(f[1] for f in frames), max(f[2] for f in frames)]}


def row(version, layout, variant, seed, winner, surv, ticks, end="wipe", arm="W", frames=((100, 3, 2), (200, 9, 4), (300, 5, 1)), invalid=None, error=None):
    """One LI4-FW row (LI1 keys, variant, invalid, measures)."""
    then = version == "then"
    if error:
        return {"version": version, "lab_sha": SHA[version], "arm": arm, "layout": layout, "seed": seed, "result": None, "margin": None, "units_firing": None, "fight_path": None,
                "fight_sha256": None, "error": {"stage": error[0], "message": error[1]}, "variant": variant, "invalid": None, "measures": None}
    defect = winner in ("draw", "cap")
    uf = NM_FIRED if then else firing([list(f) for f in frames])
    return {"version": version, "lab_sha": SHA[version], "arm": arm, "layout": layout, "seed": seed,
            "result": {"winner": winner, "survivors": list(surv), "last_tick": ticks, "end": end}, "margin": surv[0] - surv[1],
            "units_firing": "not measured at then" if then else {"by_frame": [list(f) for f in frames], "peak": [9, 4]},
            "fight_path": "/scratch/%s/%s-%s-%d.fight.json" % (version, layout, variant, seed), "fight_sha256": "ab" * 32, "error": None, "variant": variant,
            "invalid": ("not measured at then" if then else [] if invalid is None else invalid),
            "measures": {"result": {"winner": winner, "end": end, "survivors": list(surv), "last_tick": ticks, "defect": defect}, "units_firing": uf,
                         "predictions": {"count": NM_FIRED if then else "A", "type": NM_FIRED if then else "A", "agreement": NM_FIRED if then else "count and type agree"}}}


def write_rows(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    return path


SEEDS = (10, 1)


def synthetic_rows(plant=None):
    """W rows of L-0055 (same at both versions) and L-0084 (changed: then B 0:6 t2268, now A 18:0 t2097), then and now, layout and twin, two seeds. `plant` overrides (version, layout, variant)
    -> dict of row kwargs, so one test changes one value and nothing else."""
    spec = {("then", "L-0055", "layout"): ("A", (21, 0), 3394), ("now", "L-0055", "layout"): ("A", (19, 0), 1963), ("then", "L-0055", "control"): ("A", (23, 0), 2196),
            ("now", "L-0055", "control"): ("A", (19, 0), 2188), ("then", "L-0084", "layout"): ("B", (0, 6), 2268), ("now", "L-0084", "layout"): ("A", (18, 0), 2097),
            ("then", "L-0084", "control"): ("draw", (40, 56), 820), ("now", "L-0084", "control"): ("B", (0, 27), 1361)}
    plant = plant or {}
    out = []
    for version in ("then", "now"):
        for layout in ("L-0055", "L-0084"):
            for variant in ("layout", "control"):
                for seed in SEEDS:
                    w, s, t = spec[version, layout, variant]
                    kw = {"end": "silence" if w == "draw" else "wipe"}
                    kw.update(plant.get((version, layout, variant), {}))
                    out.append(row(version, layout, variant, seed, kw.pop("winner", w), kw.pop("surv", s), kw.pop("ticks", t), **kw))
    return out


def synthetic_f_rows(plant=None):
    """Arm F rows (neutral Vanguard roles) of L-0084, then and now, layout and twin, seed 10: the same winners at both versions, so the whole is the only arm that differs. `plant` as above."""
    spec = {("then", "layout"): ("B", (0, 4), 2000), ("now", "layout"): ("B", (0, 5), 1900), ("then", "control"): ("B", (0, 9), 1500), ("now", "control"): ("B", (0, 8), 1400)}
    plant = plant or {}
    out = []
    for version in ("then", "now"):
        for variant in ("layout", "control"):
            w, s, t = spec[version, variant]
            kw = dict(plant.get((version, "L-0084", variant), {}))
            out.append(row(version, "L-0084", variant, 10, kw.pop("winner", w), kw.pop("surv", s), kw.pop("ticks", t), arm="F", **kw))
    return out


# ---------------------------------------------------------------- synthetic arm inputs (LI3 shapes)

def m_summary(version="now", points=((16, True, 0), (17, False, 0)), blocks=False, units=(), part_word="pass"):
    """An M summary of the shape of isolation_arms.scan_m: `points` (enemy_heads, won, orders_ended_short); `units` the stopping-check offenders [(id, tick, x, y)]."""
    pts = [{"own_heads": 16, "enemy_heads": e, "won": w, "defect": False, "outcomes": ["side0" if w else "side1"] * 2, "mean_margin": 3.5 if w else -2.0, "fights": 2, "layouts": ["L-9001"],
            "orders_ended_short": o, "idle_behind": 4, "idle_front": 1, "max_overlap_pairs": 0, "first_contact_ticks": [120, 120]} for e, w, o in points]
    flips = [{"before": a["enemy_heads"], "after": b["enemy_heads"], "direction": "win_to_loss" if a["won"] else "loss_to_win"} for a, b in zip(pts, pts[1:]) if a["won"] != b["won"]]
    stop = {"orders_ended_short": len(units), "units": [{"id": i, "side": "A", "x": x, "y": y, "tick": t, "since": t - 200} for i, t, x, y in units], "died_short": [], "blocks": bool(units)}
    rows = [{"own": 16, "enemy": pts[-1]["enemy_heads"], "swap": False, "stopping": stop, "blocks": bool(units), "flags": ["orders_ended_short"] if units else []}]
    return {"arm": "M", "version": version, "lab_sha": SHA[version], "own": 16, "heads": [p["enemy_heads"] for p in pts], "seeds": [10], "movement": "walk", "spread_ticks": [0, 100], "points": pts,
            "beats": max([p["enemy_heads"] for p in pts if p["won"]], default=None), "loses_to": min([p["enemy_heads"] for p in pts if not p["won"]], default=None), "ceiling_hit": False,
            "multi_flip": len(flips) > 1, "flips": flips, "part_word": part_word, "blocks": bool(units), "mirror": next((p for p in pts if p["enemy_heads"] == 16), None), "rows": rows}


def v_row(version="now", kind="flat", layout="L-9002", standoff=2, first_shot=140, flags=(), sensor=None, expected=None, part_word="no stated direction"):
    nm = "not measured at %s" % version
    return {"version": version, "lab_sha": SHA[version], "arm": "V", "layout": layout, "seed": 10, "result": {"winner": "A", "survivors": [5, 0], "last_tick": 900, "end": "wipe"}, "margin": 5,
            "units_firing": nm if version == "then" else {"by_frame": [[100, 1, 0]], "peak": [1, 0]}, "fight_path": "/scratch/v.fight.json", "fight_sha256": "cd" * 32, "error": None,
            "kind": kind, "heads": 8, "holder": "A", "sight": "on", "expected_winner": expected, "part_word": part_word, "measures": None,
            "vision": {"sensor": sensor or ({"Vanguard": 700} if version == "now" else nm), "notice": {"Vanguard": 330.0} if version == "now" else nm, "first_seen": {"A": 80, "B": 82} if version == "now" else nm,
                       "holder": {"side": "A", "stepped": False, "fired": True, "returned": False}, "standoff_count": standoff, "first_shot_tick": first_shot},
            "twin": nm if version == "then" else {"sight": "off", "result": {"winner": "A", "survivors": [5, 0], "last_tick": 880, "end": "wipe"}, "fight_path": "/scratch/t.json", "fight_sha256": "ef" * 32, "invalid": []},
            "flags": sorted(flags), "blocks": False}


# ---------------------------------------------------------------- clips (the clip pipeline's facts files, fake media)

def facts(name, version, layout="L-0084", seed=10, first=0, last=2098, engine=None):
    """A facts.json of the shape of docs/reports/2026-11-24-clip-pipeline-interface.md (the keys the page reads, the rest as the interface lists them)."""
    return {"name": name, "version": version, "kind": "layout", "layout_id": layout, "seed": seed, "snapshot_every_ticks": 2, "winner": "A", "survivors_A_B": [18, 0], "last_tick": last,
            "end_kind": "wipe", "capped": False, "frames": (last - first) // 2 + 1, "first_tick": first, "last_frame_tick": last, "label": {"first": "%s  tick %d" % (version, first), "last": "%s  tick %d" % (version, last)},
            "camera_box": [0, 0, 4000, 4000], "position_box": [0, 0, 4000, 4000],
            "video": {"file": name + ".mp4", "codec": "h264", "pix_fmt": "yuv420p", "fps": 20, "width": 1600, "height": 900, "frames": 50, "duration_s": 2.5, "size_bytes": 20, "max_bytes": 9000000,
                      "crf": 24, "faststart": True, "sha256": hashlib.sha256(name.encode()).hexdigest()}, "poster": {"file": name + "-poster.jpg", "sha256": "11" * 32},
            "fight": {"file": name + ".fight.json", "sha256": "22" * 32, "size_bytes": 1}, "record_command": "<record>", "render_command": "<render>", "encode_command": "<encode>",
            "tree": "/scratch/tree", "engine_sha": engine or SHA.get(version, "0" * 40), "chunk_frames": 500, "times": {"generated_at": "x", "record_s": 1, "render_s": 1, "encode_s": 1}}


def clip_dir(root, sets):
    """Write fake clips and a manifest under `root`; `sets` is [(set id, layout, why, [version, ...])]. Returns the manifest path. The mp4 and jpg are fake bytes: the page copies, it never decodes."""
    root = Path(root)
    (root / "src").mkdir(parents=True, exist_ok=True)
    manifest = {"sets": []}
    for sid, layout, why, versions in sets:
        paths = []
        for v in versions:
            name = "%s-%s" % (sid, v)
            f = facts(name, v, layout=layout)
            (root / "src" / (name + ".mp4")).write_bytes(b"FAKE-MP4:" + name.encode())
            (root / "src" / (name + "-poster.jpg")).write_bytes(b"FAKE-JPG:" + name.encode())
            (root / "src" / (name + ".facts.json")).write_text(json.dumps(f, sort_keys=True))
            paths.append("src/%s.facts.json" % name)
        manifest["sets"].append({"id": sid, "layout": layout, "seed": 10, "row": layout, "why": why, "facts": paths})
    (root / "clips.json").write_text(json.dumps(manifest, sort_keys=True))
    return root / "clips.json"


# ---------------------------------------------------------------- building a page from synthetic inputs

def build(tmp, rows=None, m=(), v=(), clips=None, out="out", banner=BANNER, kind="decision", ledger=None, drafts=None):
    """read_inputs + build_page into tmp/out; returns (out dir, result dict of build_page)."""
    mod = page()
    tmp = Path(tmp)
    rows_files = [write_rows(rows, tmp / "in" / "rows.jsonl")] if rows else []
    m_files = []
    if m:
        (tmp / "in").mkdir(parents=True, exist_ok=True)
        (tmp / "in" / "m.json").write_text(json.dumps(list(m), sort_keys=True))
        m_files = [tmp / "in" / "m.json"]
    v_files = [write_rows(list(v), tmp / "in" / "v.jsonl")] if v else []
    inputs = mod.read_inputs(rows=rows_files, m=m_files, v=v_files, repo=ROOT)
    res = mod.build_page(tmp / out, banner=banner, banner_kind=kind, inputs=inputs, clips=clips, drafts=drafts, ledger=ledger or LEDGER)
    return tmp / out, res


def table_cells(root, table):
    """{(row key...): {col: text}} of `table[data-table=<table>]`: rows with data-layout, keyed (layout, kind-or-variant, version) as the row attributes give them."""
    t = root.one("table", data_table=table)
    out = {}
    for tr in t.find("tr"):
        cells = {td.attrs["data-col"]: td.text() for td in tr.find("td") if "data-col" in td.attrs}
        if cells:
            out[(tr.attrs.get("data-layout"), tr.attrs.get("data-variant") or tr.attrs.get("data-kind"), tr.attrs.get("data-version"))] = cells
    return out


def page_root(out_dir):
    return parse((Path(out_dir) / "index.html").read_text())
