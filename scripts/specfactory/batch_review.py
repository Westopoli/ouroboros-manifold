#!/usr/bin/env python3
"""Batch reviews billed to the Console credits: epic drift audits and story-shot reviews (Message Batches API).

Batch calls cost half of list price. Dry run is the default: requests.jsonl and index.json are written to --out,
the request count and an estimated cost are printed, nothing is sent. --submit sends the batch (needs the key
file, see sdk_engineer.read_key) and writes batch_id.txt. fetch never polls: it says "in_progress" until it ends.

  batch_review.py audit-epics   --out DIR [--samples N] [--model M] [--max-tokens N] [--root R] [--dry-run | --submit]
  batch_review.py story-reviews --out DIR [--model M] [--max-tokens N] [--root R] [--dry-run | --submit]
  batch_review.py fetch BATCH_ID --out DIR   # results.jsonl + digest.md (use the --out the batch was built in)
  batch_review.py digest --out DIR           # rebuild digest.md from DIR/results.jsonl, offline

audit-epics: one request per docs/bible/epics/E-*.md: the epic text plus the rows of
docs/northstar/plans/push_ledger_2026-09-22.md that name one of the epic's own rule ids (lines "- R-###-##");
the model returns a table of drift between the rules and those rulings. --samples N repeats each epic with a
different system nonce. story-reviews: one request per shot, the newest run per file stem under
docs/northstar/story_reviews/shots/: PNG (scaled to 1280 wide if wider) + its state json (<stem>.state.json,
<stem>.json or <stem>.qa_state.json) + the story's words (docs/bible/stories.md) + the epic's rule lines for it;
the model answers yes / no / unclear in the one-line form of the review-queue rows. Shots with no story id
(file name or lane row) or no state json are listed as skipped. The estimate: input at chars/4 plus 2,700 per
image (dense JSON tokenises worse than prose, so read it as a floor), output at max_tokens for every request (a
ceiling). Needs the anthropic package only for --submit and fetch.
See also: sdk_engineer.py (read_key), README_credits.md, docs/northstar/story_reviews/README.md (queue form).
"""
import argparse
import base64
import hashlib
import io
import json
import re
import struct
import sys
from datetime import date
from pathlib import Path

from sdk_engineer import read_key

ROOT = Path(__file__).resolve().parents[2]
RATES = {"claude-sonnet-5-5": (1.0, 5.0), "claude-fable-5-1": (5.0, 25.0)}  # USD per MTok in/out, batch prices (the Architect's; the pricing page agrees)
DEFAULT_MODEL = "claude-sonnet-5-5"
IMAGE_TOKENS, IMAGE_WIDTH, MAX_STATE_CHARS = 2700, 1280, 400_000
MAX_REQUESTS, MAX_BYTES = 100_000, 256 * 1024 * 1024
MAX_TOKENS = {"audit-epics": 8000, "story-reviews": 1500}
LEDGER = "docs/northstar/plans/push_ledger_2026-09-22.md"
SHOTS = "docs/northstar/story_reviews/shots"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

AUDIT_SYSTEM = (
    "You audit one epic of a game design bible against the rulings recorded in a project ledger. Work only from the "
    "text given; quote ids and words exactly; never invent a rule or a ruling. Drift is: a ruling changed, narrowed, "
    "extended, reversed or retired a rule while the epic still states the old thing; or the epic states something a "
    "ledger row contradicts. Ledger rows that only report a test, build or gate and give the rule no new meaning "
    "are not rulings; leave them out.")
REVIEW_SYSTEM = (
    "You review one player-facing screenshot of a game against the story it is meant to prove. You get the story in "
    "the player's words, the epic's rules for it, the screenshot, and the game's own state dump from the same frame. "
    "Judge only what the picture and the state show; behavior that needs motion or time is unclear unless the state "
    "records its result. Reply with exactly one line, no markdown, no line break, no pipe character: 'yes. <evidence>' "
    "when the story is visibly delivered, 'no. <evidence>' when the shot contradicts it or its required elements are "
    "absent, 'unclear. <evidence>' when this frame cannot decide it. Evidence: what you see (resolution, the elements "
    "and where they sit), the qa_state fields and values that confirm or refute it, the rule ids (R-###-##) satisfied "
    "or violated, and what a single frame cannot show.")
RULE_ID = re.compile(r"(?m)^\s*[-*]\s*(R-\d{3}-\d{2})\b")
STORY_ROW = re.compile(r"\|\s*(S-\d{3})\s*\|\s*(E-\d+)\s*\|\s*(.*?)\s*\|")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def request(cid: str, model: str, max_tokens: int, system: str, content) -> dict:
    return {"custom_id": cid, "params": {"model": model, "max_tokens": max_tokens, "system": system,
                                         "messages": [{"role": "user", "content": content}]}}


def est_tokens(params: dict) -> int:
    chars, images = len(params.get("system", "")), 0
    for m in params["messages"]:
        for b in ([{"type": "text", "text": m["content"]}] if isinstance(m["content"], str) else m["content"]):
            images += b["type"] == "image"
            chars += len(b.get("text", ""))
    return chars // 4 + IMAGE_TOKENS * images


def audit_requests(root: Path, model: str, samples: int, max_tokens: int):
    ledger = root / LEDGER
    rows = [(n, l) for n, l in enumerate(read(ledger).splitlines(), 1) if l.startswith("|")] if ledger.is_file() else []
    reqs, items = [], {}
    for f in sorted((root / "docs/bible/epics").glob("E-*.md")):
        eid = re.match(r"E-\d+", f.name)
        if not eid:
            continue
        text, eid = read(f), eid.group(0)
        ids = sorted(set(RULE_ID.findall(text)))
        pat = re.compile(r"(?<![A-Za-z0-9])(?:%s)(?!\d)" % "|".join(map(re.escape, ids))) if ids else None
        hit = [f"L{n}: {l}" for n, l in rows if pat and pat.search(l)]
        user = (f"EPIC FILE {f.name}\n\n<epic>\n{text}\n</epic>\n\n"
                f"LEDGER ROWS naming this epic's rule ids ({len(hit)} rows of {LEDGER}; Ln is the ledger line):\n\n"
                "<ledger>\n" + ("\n".join(hit) or "(none)") + "\n</ledger>\n\n"
                "Task: find the drift between the epic's rules and these rulings. Output one markdown table of drift "
                "only, nothing before it, columns: | Rule id | Epic text (quote) | Ruling (quote, ledger line) | "
                "Kind (stale / contradiction / unreflected) | Suggested edit to the epic |. If there is none, output "
                "the single line 'No drift found.' End with the line 'Ledger rows read: N.'")
        for k in range(1, samples + 1):
            cid = f"audit-{eid}-s{k}"
            nonce = hashlib.sha1(f"{eid}:{k}".encode()).hexdigest()[:8]
            reqs.append(request(cid, model, max_tokens, f"{AUDIT_SYSTEM}\nSample {k} of {samples}, nonce {nonce}.", user))
            items[cid] = {"epic": eid, "file": f.name, "sample": k, "rows": len(hit), "note": f"{f.name} rows={len(hit)}"}
    return reqs, items, []


def story_catalog(root: Path) -> dict:
    f, cat = root / "docs/bible/stories.md", {}
    for l in (read(f).splitlines() if f.is_file() else []):
        m = STORY_ROW.match(l)
        if m:
            cat[m.group(1)] = (m.group(2), m.group(3))
    return cat


def story_rules(root: Path, sid: str, epic: str) -> str:
    f = next(iter(sorted((root / "docs/bible/epics").glob(f"{epic}-*.md"))), None)
    out, on = [], False
    for l in (read(f).splitlines() if f else []):
        if l.startswith("### "):
            if on:
                break
            on = re.match(rf"###\s+{sid}\b", l) is not None
        if on and (l.startswith("### ") or l.startswith("As a") or re.match(r"-\s*R-\d{3}-\d{2}\b", l)):
            out.append(l)
    return "\n".join(out)


def lane_rows(root: Path) -> list:
    rows = []
    for f in sorted((root / "docs/northstar/story_reviews").glob("*.md")):
        for l in (read(f).splitlines() if f.name != "README.md" else []):
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            m = re.match(r"S-\d{3}", c[0]) if l.startswith("|") and len(c) > 3 else None
            if m:
                rows.append({"story": m.group(0), "lane": c[1], "png": c[3]})
    return rows


def run_key(name: str) -> tuple:
    m = re.search(r"(\d{8})[-T](\d{4})", name)  # both run-id schemes: 20261013-0103-<sha> and run-20261020T072108Z
    return (m.group(1) + m.group(2) if m else "0", name)


def story_id(stem: str) -> str | None:
    m = re.search(r"(?<![A-Za-z0-9])[Ss]-?(\d{3})(?!\d)", stem)
    return f"S-{m.group(1)}" if m else None


def png_block(png: Path):
    data = png.read_bytes()
    orig = sent = struct.unpack(">II", data[16:24])
    if orig[0] > IMAGE_WIDTH:
        try:
            from PIL import Image
        except ImportError:
            sys.exit("Pillow is needed to scale screenshots wider than 1280 px: pip install pillow")
        im = Image.open(io.BytesIO(data))
        im = im.convert("RGBA" if "A" in im.mode else "RGB")
        sent = (IMAGE_WIDTH, round(orig[1] * IMAGE_WIDTH / orig[0]))
        buf = io.BytesIO()
        im.resize(sent, Image.Resampling.LANCZOS).save(buf, "PNG", optimize=True)
        data = buf.getvalue()
    block = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(data).decode()}}
    return block, orig, sent


def story_requests(root: Path, model: str, max_tokens: int):
    cat, lanes = story_catalog(root), lane_rows(root)
    by_png, by_story = {r["png"]: r for r in lanes}, {r["story"]: r for r in lanes}
    newest = {}
    for run in sorted((p for p in (root / SHOTS).glob("*") if p.is_dir()), key=lambda p: run_key(p.name)):
        for png in run.glob("*.png"):
            newest[png.stem] = png  # the newest run wins per file stem
    reqs, items, skipped = [], {}, []
    for stem, png in sorted(newest.items()):
        rel = png.relative_to(root).as_posix()
        sid = story_id(stem) or by_png.get(rel, {}).get("story")
        state = next((s for s in (png.with_name(stem + e) for e in (".state.json", ".json", ".qa_state.json")) if s.is_file()), None)
        try:
            state_text = json.dumps(json.loads(read(state)), separators=(",", ":")) if state else None
        except ValueError:
            state_text = ""
        why = ("no story id in the file name or a lane row" if not sid else "story not in docs/bible/stories.md" if sid not in cat
               else "no state json beside it" if not state else "state json does not parse" if not state_text
               else "not a PNG" if not png.read_bytes().startswith(PNG_MAGIC) else None)
        if why:
            skipped.append([rel, why])
            continue
        epic, words = cat[sid]
        block, orig, sent = png_block(png)
        if len(state_text) > MAX_STATE_CHARS:
            state_text = state_text[:MAX_STATE_CHARS] + f"...[state truncated at {MAX_STATE_CHARS} of {len(state_text)} chars]"
        scaled = f", sent scaled to {sent[0]}x{sent[1]}" if sent != orig else ""
        text = (f"STORY {sid}, in the commander's words:\n{words}\n\nTHE EPIC'S RULES FOR THIS STORY:\n{story_rules(root, sid, epic) or '(none found)'}"
                f"\n\nSCREENSHOT {rel}: original {orig[0]}x{orig[1]}{scaled} (the image above).\n\n"
                f"QA STATE from the same frame (the game's own dump, compact JSON):\n{state_text}\n\n"
                "Does this frame show the story? Answer in the one-line form: yes. / no. / unclear. then the evidence.")
        cid = f"story-{sid}-{hashlib.sha1(rel.encode()).hexdigest()[:8]}"
        reqs.append(request(cid, model, max_tokens, REVIEW_SYSTEM, [block, {"type": "text", "text": text}]))
        items[cid] = {"story": sid, "lane": by_story.get(sid, {}).get("lane", "?"), "run": png.parent.name, "png": rel,
                      "state": state.relative_to(root).as_posix(), "note": rel}
    return reqs, items, skipped


def client():
    try:
        import anthropic
    except ImportError:
        sys.exit("the anthropic package is not installed here; run with /home/westopoli/Projects/om-push/venv-sdk/bin/python")
    return anthropic.Anthropic(api_key=read_key())


def emit(a: argparse.Namespace, reqs: list, items: dict, skipped: list) -> int:
    a.out.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in reqs)
    (a.out / "requests.jsonl").write_text(body)
    (a.out / "index.json").write_text(json.dumps({"kind": a.cmd, "model": a.model, "items": items, "skipped": skipped}, indent=1, sort_keys=True) + "\n")
    tin, tout, (ri, ro) = sum(est_tokens(r["params"]) for r in reqs), len(reqs) * a.max_tokens, RATES[a.model]
    for r in reqs:
        print(f"  {r['custom_id']:34s} ~{est_tokens(r['params']) / 1000:6.1f}k tok  {items[r['custom_id']]['note']}")
    for rel, why in skipped:
        print(f"  skipped {rel}: {why}")
    print(f"{a.cmd}: {len(reqs)} requests, model {a.model}, max_tokens {a.max_tokens}, {len(body) / 1e6:.1f} MB, {len(skipped)} skipped\n"
          f"estimate (batch rates ${ri:g}/${ro:g} per MTok): input ~{tin:,} tok = ${tin * ri / 1e6:.2f}, output at most {tout:,} tok = "
          f"${tout * ro / 1e6:.2f}, total ~${(tin * ri + tout * ro) / 1e6:.2f}\nwrote {a.out / 'requests.jsonl'} and index.json")
    if not reqs or len(reqs) > MAX_REQUESTS or len(body.encode()) > MAX_BYTES:
        print("refusing: no requests, or over the API limit of 100,000 requests / 256 MB per batch", file=sys.stderr)
        return 1
    if not a.submit:
        print("dry run: nothing sent (add --submit to send)")
        return 0
    batch = client().messages.batches.create(requests=reqs)
    (a.out / "batch_id.txt").write_text(batch.id + "\n")
    print(f"submitted {batch.id}; later: batch_review.py fetch {batch.id} --out {a.out}")
    return 0


def verdict(text: str) -> str:
    t = " ".join(text.replace("|", "/").split())
    return re.sub(r"^(Yes|No|Unclear)", lambda m: m.group(1).lower(), t) if re.match(r"(yes|no|unclear)\b", t, re.I) \
        else f"unclear. (reviewer left the one-line form) {t}"


def digest(out: Path) -> Path:
    if not (out / "results.jsonl").is_file():
        sys.exit(f"{out / 'results.jsonl'} not found: run fetch first")
    idx = json.loads(read(out / "index.json")) if (out / "index.json").is_file() else {"kind": "", "model": None, "items": {}, "skipped": []}
    res = [json.loads(l) for l in read(out / "results.jsonl").splitlines() if l.strip()]
    ok = sorted((r for r in res if r["result"]["type"] == "succeeded"), key=lambda r: r["custom_id"])
    bad = [r for r in res if r["result"]["type"] != "succeeded"]
    tin = sum(r["result"]["message"]["usage"]["input_tokens"] for r in ok)
    tout = sum(r["result"]["message"]["usage"]["output_tokens"] for r in ok)
    model = idx["model"] or (ok[0]["result"]["message"]["model"] if ok else DEFAULT_MODEL)
    ri, ro = RATES.get(model) or next((v for k, v in RATES.items() if model.startswith(k)), RATES[DEFAULT_MODEL])
    text = lambda r: "".join(b.get("text", "") for b in r["result"]["message"]["content"] if b["type"] == "text")
    out_lines = [f"# {idx['kind'] or 'batch'} digest", "",
                 f"{len(ok)} succeeded, {len(bad)} not; tokens in {tin:,}, out {tout:,}; cost at batch rates ${(tin * ri + tout * ro) / 1e6:.2f} ({model})", ""]
    if idx["kind"] == "story-reviews":
        out_lines += ["Rows for docs/northstar/story_reviews/<lane>.md (lane ? = no earlier row names the story):", "",
                      "| story | lane | run id | screenshot path | qa_state file | reviewer | reviewer verdict (yes/no/unclear + evidence) "
                      "| Westley verdict (pending/approved/rejected) | date |",
                      "|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(ok, key=lambda r: (idx["items"].get(r["custom_id"], {}).get("story", ""), r["custom_id"])):
            i = idx["items"].get(r["custom_id"], {})
            out_lines.append(f"| {i.get('story', r['custom_id'])} | {i.get('lane', '?')} | {i.get('run', '')} | {i.get('png', '')} | {i.get('state', '')} "
                             f"| batch {model} | {verdict(text(r))} | pending | {date.today()} |")
    else:
        for r in ok:
            i = idx["items"].get(r["custom_id"], {})
            out_lines += [f"## {i.get('epic', r['custom_id'])}, sample {i.get('sample', '?')} ({i.get('rows', '?')} ledger rows)", "", text(r).strip(), ""]
    out_lines += ["", "## Not reviewed", ""] if bad or idx["skipped"] else []
    out_lines += [f"- {r['custom_id']}: {r['result']['type']} {json.dumps(r['result'].get('error', ''))[:300]}" for r in bad]
    out_lines += [f"- skipped at build, {rel}: {why}" for rel, why in idx["skipped"]]
    (out / "digest.md").write_text("\n".join(out_lines) + "\n")
    return out / "digest.md"


def fetch(batch_id: str, out: Path) -> int:
    c = client()
    b = c.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        print(f"{batch_id} is {b.processing_status}: {b.request_counts.model_dump()}; run fetch again later (most batches end within an hour)")
        return 1
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.jsonl").write_text("".join(r.model_dump_json() + "\n" for r in c.messages.batches.results(batch_id)))
    print(f"wrote {out / 'results.jsonl'} and {digest(out)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out", required=True, type=Path)
    for name in ("audit-epics", "story-reviews"):
        s = sub.add_parser(name, parents=[common])
        s.add_argument("--root", type=Path, default=ROOT, help="repo root holding docs/ (default: this checkout)")
        s.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(RATES))
        s.add_argument("--max-tokens", type=int, default=MAX_TOKENS[name])
        mode = s.add_mutually_exclusive_group()
        mode.add_argument("--dry-run", action="store_true", help="the default: write the files, print the estimate, send nothing")
        mode.add_argument("--submit", action="store_true", help="send the batch (needs the key file)")
    sub.choices["audit-epics"].add_argument("--samples", type=int, default=1)
    sub.add_parser("fetch", parents=[common]).add_argument("batch_id")
    sub.add_parser("digest", parents=[common])
    a = p.parse_args(argv)
    if getattr(a, "submit", False):
        read_key()  # fail before the build, not after it, when the key file is wrong
    if a.cmd == "fetch":
        return fetch(a.batch_id, a.out)
    if a.cmd == "digest":
        print(f"wrote {digest(a.out)}")
        return 0
    if a.cmd == "audit-epics":
        return emit(a, *audit_requests(a.root, a.model, max(a.samples, 1), a.max_tokens))
    return emit(a, *story_requests(a.root, a.model, a.max_tokens))


if __name__ == "__main__":
    sys.exit(main())
