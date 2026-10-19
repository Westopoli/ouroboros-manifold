"""Chronicle twin sweep (sim lane 2026-10-12, "Method notes"; ported from the scratch run.py and analyze.py).

Per seed: a campaign of N chapters over scripts.simviewer.pipe_session.PipeSession. Each chapter ends a
mission (rotating end / complete / refuse), saves, steps 50 ticks collecting deltas, loads the save and
jumps 50 ticks (the twin). The step and jump snapshots must carry the same checksum; the chronicle the
jump writes is then analysed against the deltas the step run showed.

Usage: python3 scripts/simviewer/probes/chronicle_twin.py --seeds 1-5 --chapters 5 --out DIR
Writes DIR/camp_<seed>.json, DIR/chronicle_summary.json, DIR/chronicle_summary.md.
"""
import argparse
import collections
import itertools
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.simviewer.pipe_session import DEFAULT_FEATURES, PipeError, PipeSession  # noqa: E402

TIER = [4, 4, 3, 4, 3, 5, 3, 2, 4, 3, 4, 3, 2, 3, 3, 3, 2, 4, 3, 2, 2, 5, 5, 5, 5, 6]
BANDOUT = {0: 1, 1: 2, 2: 2, 3: 0, 4: 0, 5: 1}
MODES = ["end", "complete", "refuse", "end", "complete"]
STOP = set("the a an and of in to was were that this with for from by as at on it its is are be had has have "
           "which their they them but not or who whom into than then there these those what when while over "
           "under after before during again".split())
TWIN_TICKS = 50


def parse_seeds(text):
    if "-" in text:
        a, b = text.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in text.split(",")]


# ---------------------------------------------------------------- run

def _slim(snap):
    """The parts of a snapshot the analysis reads."""
    return {"tick": snap.get("tick"), "checksum": snap.get("checksum"),
            "regions": [{"owner": r["owner"]} for r in snap["regions"]],
            "edges": [{"a": e["a"], "b": e["b"]} for e in snap.get("edges", [])]}


def campaign(seed, chapters, workdir):
    s = PipeSession()
    rec = {"seed": seed, "chapters": []}
    try:
        s.send("set_seed", seed=seed, n_regions=0, features=DEFAULT_FEATURES)
        snap = s.send("snapshot")[0]
        for ch in range(chapters):
            c = {"chapter": ch + 1}
            mode = MODES[ch % len(MODES)]
            try:
                m = s.send("mission_start", faction=snap.get("player_faction", 0))[0]
            except PipeError as e:
                m = None
                mode = "nomission"
                c["mission_error"] = e.frame
            c["mission"] = m
            if mode == "nomission":
                deb = None
                snap = s.send("snapshot")[0]
            elif mode == "refuse":
                deb, snap = s.send("mission_refuse")
            else:
                s.send("mission_begin")
                if mode == "complete":
                    s.send("objective_complete", objective=0, completion=1.0)
                deb, snap = s.send("mission_end")
            c["mode"] = mode
            c["debrief"] = deb
            c["pre_snapshot"] = _slim(snap)
            path = str(Path(workdir) / ("save_%d_%d.bin" % (seed, ch)))
            s.send("save", path=path)
            frames = s.send("step", n=TWIN_TICKS)
            c["deltas"] = [f for f in frames if f["type"] == "delta"]
            step_snap = s.send("snapshot")[0]
            c["step_snapshot"] = _slim(step_snap)
            s.send("load", path=path)
            chron, post = s.send("jump", ticks=TWIN_TICKS)
            c["chronicle"] = chron
            c["post_snapshot"] = _slim(post)
            c["twin_match"] = step_snap.get("checksum") == post.get("checksum")
            snap = post
            rec["chapters"].append(c)
    finally:
        s.close()
    return rec


# ---------------------------------------------------------------- analysis

def _sig(t, d):
    return (TIER[t] if t < len(TIER) else 2) + min(sum(abs(x) for x in d) / 50, 3.0)


def _words(t):
    return {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in STOP}


def _sents(t):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]


def analyze(recs):
    R = collections.Counter()
    ex = collections.defaultdict(list)
    tot = collections.Counter()

    def flag(k, loc, msg=""):
        R[k] += 1
        if len(ex[k]) < 4:
            ex[k].append([loc, msg])

    for rec in recs:
        sd = rec["seed"]
        seen_sent = {}
        seen_frag = collections.Counter()
        for c in rec["chapters"]:
            ch = c["chapter"]
            loc = "seed%d ch%d" % (sd, ch)
            tot["chapters"] += 1
            if not c.get("twin_match", True):
                flag("twin_checksum_mismatch", loc)
            ents = c["chronicle"]["entries"]
            tot["entries"] += len(ents)
            evs = [e for d in c["deltas"] for e in d["events"]]
            tot["events"] += len(evs)
            tot["attacks"] += sum(len(d["attacks"]) for d in c["deltas"])
            tot["revolts"] += sum(len(d["revolts"]) for d in c["deltas"])
            tot["collisions"] += sum(len(d["collisions"]) for d in c["deltas"])
            post = c["post_snapshot"]["regions"]
            own0 = [r["owner"] for r in c["pre_snapshot"]["regions"]]
            own1 = [r["owner"] for r in post]
            changed = {i for i in range(len(own0)) if own0[i] != own1[i]}
            adj = collections.defaultdict(set)
            for e in c["pre_snapshot"]["edges"]:
                adj[e["a"]].add(e["b"])
                adj[e["b"]].add(e["a"])
            mission = c["mission"]
            mreg = mission["region"] if mission else None
            band = c["debrief"]["band"] if c["debrief"] else None
            by_reg = collections.defaultdict(list)
            for e in evs:
                by_reg[e["region"]].append(e)
            chain_cnt = collections.Counter(e["chain"] for e in evs if e["chain"] > 0)

            def score(e):
                m = 1.0 + (0.5 if e["region"] == mreg else 0) + 0.1 * min(chain_cnt.get(e["chain"], 1), 5) * (
                    1 if e["chain"] > 0 and chain_cnt[e["chain"]] > 1 else 0)
                return _sig(e["template"], e["delta"]) * m

            peak = {r: max(score(e) for e in es) for r, es in by_reg.items()}
            for r in changed:
                peak[r] = max(peak.get(r, 0), 4 * (1.0 + (0.5 if r == mreg else 0)))
            n_blank = sum(1 for e in ents if not e["text"].strip())
            tot["blank_entries"] += n_blank
            if n_blank:
                flag("blank_text", loc, "%d blank of %d (ids %s)" % (n_blank, len(ents), [e["id"] for e in ents if not e["text"].strip()]))
            if len(ents) > 10:
                flag("over10", loc)
            if len(ents) - n_blank < 5:
                flag("under5_readable", loc, "%d readable, %d total" % (len(ents) - n_blank, len(ents)))
            cons = [e for e in ents if e["cluster_type"] == 0]
            real_cons = [e for e in cons if e["category"] < 3]
            if mission is not None:
                if not ents or ents[0]["cluster_type"] != 0 or ents[0]["category"] > 2:
                    flag("R065-02_first_not_consequence", loc)
                elif band is not None and ents[0]["category"] != BANDOUT[band]:
                    flag("R065-02_wrong_outcome", loc, "band %s -> cat %s" % (band, ents[0]["category"]))
                if len(real_cons) != 1:
                    flag("R065-02_consequence_count", loc, str(len(real_cons)))
                if ents and not ents[0]["text"].strip():
                    flag("R065-02_consequence_blank", loc)
            elif cons:
                flag("R065-02_consequence_without_mission", loc)
            rip = [e for e in cons if e["category"] == 3]
            tot["ripple_entries"] += len(rip)
            if len(rip) > 2:
                flag("R065-05_ripple_exceeds_cap2", loc, "%d ripple entries" % len(rip))
            for e in rip:
                rr = e["refs"]["regions"][0]
                if mreg is None or rr not in adj[mreg]:
                    flag("ripple_not_adjacent", loc, str(rr))
                if rr not in by_reg:
                    flag("ripple_no_event", loc, str(rr))
            lin = [e for e in ents if e["cluster_type"] == 1]
            if not lin:
                flag("family_entry_missing", loc)
            elif not any(e["text"].strip() for e in lin):
                flag("family_entry_blank", loc)
            if len(lin) > 2:
                flag("lineage_gt2", loc, str(len(lin)))
            covered = set()
            for e in ents:
                regs = e["refs"]["regions"]
                covered.update(regs)
                ct = e["cluster_type"]
                tot["ct%d" % ct] += 1
                if ct == 2:
                    ok = any(x["chain"] > 0 and x["region"] in regs and e["start_tick"] - 1 <= x["tick"] <= e["end_tick"] + 1 for x in evs)
                    if not ok:
                        flag("chain_entry_no_chain_event", loc, "id%d cat%d regs%s" % (e["id"], e["category"], regs))
                if ct == 3:
                    r = regs[0]
                    has_ev = r in by_reg
                    chg = r in changed
                    if not has_ev and not chg:
                        flag("regional_entry_no_event_padding", loc, "id%d region %d cat%d sig%s" % (e["id"], r, e["category"], e["significance"]))
                    if e["category"] == 20 and not chg:
                        flag("faction_shift_without_owner_change", loc, "id%d region %d" % (e["id"], r))
                    if chg and e["category"] != 20:
                        flag("owner_change_not_faction_shift", loc, "id%d region %d cat%d" % (e["id"], r, e["category"]))
                    if has_ev or chg:
                        lb = peak.get(r, 0)
                        if e["significance"] + 1e-6 < lb:
                            flag("significance_below_recomputed_lowerbound", loc, "id%d sig %.2f vs %.2f" % (e["id"], e["significance"], lb))
            cc = collections.Counter((e["cluster_type"], e["category"]) for e in ents if e["cluster_type"] in (2, 3))
            for k, v in cc.items():
                if v > 2:
                    flag("R065-05_category_cap_exceeded", loc, "%s x%d" % (k, v))
            others = [e for e in ents if e["cluster_type"] in (2, 3)]
            cutoff = min([e["significance"] for e in others if e["significance"] > 0] or [0])
            full = len(ents) >= 10
            capcats = collections.Counter(e["category"] for e in others)
            for r, p in peak.items():
                if r in covered:
                    continue
                cat = 20 if r in changed else 23
                if p >= cutoff and cutoff > 0:
                    why = "budget_full" if full else ("category_capped" if capcats[cat] >= 2 else "UNEXPLAINED")
                    tot["uncovered_above_cutoff_" + why] += 1
                    if why == "UNEXPLAINED":
                        flag("event_region_above_cutoff_no_entry", loc, "region %d score %.2f cutoff %.2f" % (r, p, cutoff))
            t5 = [x for x in evs if TIER[x["template"]] >= 5]
            tot["tier5plus_events"] += len(t5)
            tot["tier5plus_events_total_uncovered"] += sum(1 for x in t5 if x["region"] not in covered)
            conq = [(d["tick"], a) for d in c["deltas"] for a in d["attacks"] if a["conquest"]]
            tot["conquests"] += len(conq)
            for _, a in conq:
                tr = a["target"]
                if tr not in changed:
                    tot["conquest_net_reverted"] += 1
                elif tr not in covered:
                    tot["conquest_owner_change_no_entry"] += 1
            for r in changed:
                tot["ownership_changes"] += 1
                if r not in covered:
                    tot["ownership_change_no_entry"] += 1
                    fl = "budget_full" if full else ("category_capped" if capcats[20] >= 2 else "UNEXPLAINED")
                    tot["own_change_no_entry_" + fl] += 1
                    if fl == "UNEXPLAINED":
                        flag("ownership_change_no_entry", loc, "region %d" % r)
            for d in c["deltas"]:
                for rv in d["revolts"]:
                    tot["revolt_rolls"] += 1
                    if rv["region"] not in covered:
                        tot["revolt_region_no_entry"] += 1
            for x in evs:
                if x["creates_faction"]:
                    tot["creates_faction_events"] += 1
                    if x["region"] not in covered:
                        tot["creates_faction_no_entry"] += 1
            for e in ents:
                for key in ("text", "expanded_text"):
                    if re.search(r"\d", e[key]):
                        flag("digit_in_text", loc, e[key][:60])
                if len(e["text"].split()) >= 90:
                    flag("base_over_90_words", loc, "id%d" % e["id"])
            nb = [e for e in ents if e["text"].strip()]
            for a, b in itertools.combinations(nb, 2):
                wa, wb = _words(a["text"]), _words(b["text"])
                if wa and wb and len(wa & wb) / min(len(wa), len(wb)) >= 0.4:
                    flag("R068-07_overlap_ge40pct_survived", loc, "ids %d,%d %.2f" % (a["id"], b["id"], len(wa & wb) / min(len(wa), len(wb))))
            for e in ents:
                for key in ("text", "expanded_text"):
                    for s_ in _sents(e[key]):
                        if len(s_.split()) < 4:
                            continue
                        nm = (sd, s_)
                        if nm in seen_sent and seen_sent[nm] != (ch, e["id"]):
                            flag("R071_sentence_repeat", loc, "'%s' first at %s" % (s_[:70], seen_sent[nm]))
                            tot["sentence_repeat_instances"] += 1
                            if seen_sent[nm][0] == ch:
                                tot["sentence_repeat_same_scroll"] += 1
                        else:
                            seen_sent.setdefault(nm, (ch, e["id"]))
                for fid in e["fragment_ids"]:
                    if fid >= 0:
                        seen_frag[fid] += 1
        tot["fragment_ids_reused_in_campaign"] += sum(1 for v in seen_frag.values() if v > 1)
        tot["fragment_ids_used"] += len(seen_frag)

    # the named groups the lane notes talk about
    groups = {
        "family_entries": {"entries_cluster_lineage": tot["ct1"], "missing": R["family_entry_missing"], "blank": R["family_entry_blank"]},
        "chain_entries": {"entries_cluster_chain": tot["ct2"], "no_chain_event": R["chain_entry_no_chain_event"]},
        "blank_shells": {"blank_entries": tot["blank_entries"], "scrolls_with_blank": R["blank_text"]},
        "ripple_over_cap": {"ripple_entries": tot["ripple_entries"], "scrolls_over_cap": R["R065-05_ripple_exceeds_cap2"]},
        "repeats": {"sentence_repeat_instances": tot["sentence_repeat_instances"], "same_scroll": tot["sentence_repeat_same_scroll"],
                    "fragment_ids_reused": tot["fragment_ids_reused_in_campaign"], "fragment_ids_used": tot["fragment_ids_used"]},
        "significance_threshold_explanations": {
            "uncovered_budget_full": tot["uncovered_above_cutoff_budget_full"],
            "uncovered_category_capped": tot["uncovered_above_cutoff_category_capped"],
            "uncovered_UNEXPLAINED": tot["uncovered_above_cutoff_UNEXPLAINED"],
            "owner_change_no_entry_budget_full": tot["own_change_no_entry_budget_full"],
            "owner_change_no_entry_category_capped": tot["own_change_no_entry_category_capped"],
            "owner_change_no_entry_UNEXPLAINED": tot["own_change_no_entry_UNEXPLAINED"],
            "significance_below_recomputed_lowerbound": R["significance_below_recomputed_lowerbound"]},
    }
    return {"totals": dict(tot), "mismatch_classes": dict(sorted(R.items())),
            "examples": {k: v for k, v in sorted(ex.items())}, "groups": groups}


def write_md(summary, path):
    lines = ["# Chronicle twin summary", "", "Seeds: %s, chapters per seed: %d" % (summary["seeds"], summary["chapters"]), "",
             "## Counts", "", "| item | count |", "|---|---|"]
    lines += ["| %s | %s |" % kv for kv in sorted(summary["totals"].items())]
    lines += ["", "## Mismatch classes", "", "| class | count | first example |", "|---|---|---|"]
    for k, v in summary["mismatch_classes"].items():
        e = summary["examples"].get(k, [[]])[0]
        lines.append("| %s | %d | %s |" % (k, v, " : ".join(str(x) for x in e).replace("|", "/")))
    if not summary["mismatch_classes"]:
        lines.append("| (none) | 0 | |")
    lines += ["", "## Groups", "", "| group | item | count |", "|---|---|---|"]
    for g, d in summary["groups"].items():
        lines += ["| %s | %s | %s |" % (g, k, v) for k, v in d.items()]
    Path(path).write_text("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", default="1-5")
    ap.add_argument("--chapters", type=int, default=5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    seeds = parse_seeds(a.seeds)
    recs = []
    with tempfile.TemporaryDirectory(prefix="chrtwin_") as work:
        for sd in seeds:
            rec = campaign(sd, a.chapters, work)
            (out / ("camp_%d.json" % sd)).write_text(json.dumps(rec))
            recs.append(rec)
            print("seed %d done" % sd, file=sys.stderr)
    summary = analyze(recs)
    summary["seeds"] = a.seeds
    summary["chapters"] = a.chapters
    (out / "chronicle_summary.json").write_text(json.dumps(summary, indent=1))
    write_md(summary, out / "chronicle_summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
