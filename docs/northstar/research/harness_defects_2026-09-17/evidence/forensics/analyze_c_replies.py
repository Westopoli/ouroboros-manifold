#!/usr/bin/env python3
"""Read-only forensics over agora runs/ for C cards, 2xx range. Writes CSV + prints tables.
Does NOT import scripts/build.py or scripts/splice.py (avoid any accidental execution
path); parsing logic below is a hand-written reimplementation of the same regexes for
inspection purposes only.
"""
from __future__ import annotations
import csv, json, re, subprocess, sys
from pathlib import Path
from collections import defaultdict, Counter

AGORA = Path("/home/westopoli/Projects/agora")
QUEUE = AGORA / "queue"
RUNS = AGORA / "runs"
OUT_CSV = Path(__file__).parent / "c_replies.csv"

TS_RE = re.compile(r"^(?P<card>.+?)-(?:manual-(?P<mdate>\d{8})|(?P<date>\d{8})-(?P<time>\d{4}))(?:-(?P<dup>\d+))?$")

FENCE_LINE_RE = re.compile(r"^\s*```(\S*)")
SNIPPET_FENCE_RE = re.compile(r"```snippet[ \t]*\n(.*?)```", re.S)

FUNC_DEF_RE = re.compile(
    r"(?m)^(?!\s*(?:if|for|while|switch|do|else|return|typedef|struct|union|enum|case|default|"
    r"sizeof|goto|break|continue)\b)"
    r"[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{"
)


def c_def_present(block: str, name: str) -> bool:
    pat = re.compile(r"\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{")
    return bool(pat.search(block))


def fenced_blocks_paired(reply: str) -> list[str]:
    """Reimplementation of build.py::_fenced_blocks: pairs consecutive ``` lines,
    an unterminated trailing opener is dropped (not returned)."""
    blocks, cur = [], None
    for line in reply.splitlines(keepends=True):
        if FENCE_LINE_RE.match(line):
            if cur is None:
                cur = []
            else:
                blocks.append("".join(cur))
                cur = None
            continue
        if cur is not None:
            cur.append(line)
    return blocks


def parse_card_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    import yaml
    try:
        d = yaml.safe_load(m.group(1))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def strip_card_suffix(name: str) -> str:
    for suf in (".md.hold", ".md.legacy", ".md.parked", ".md"):
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


def build_card_registry() -> dict:
    """card_base_id -> list of (path, meta-dict) across queue/, queue/parked/, etc."""
    reg = defaultdict(list)
    for p in QUEUE.rglob("*"):
        if not p.is_file():
            continue
        if not re.search(r"\.md(\.(hold|legacy|parked))?$", p.name):
            continue
        base = strip_card_suffix(p.name)
        try:
            text = p.read_text(errors="replace")
        except Exception:
            continue
        meta = parse_card_frontmatter(text)
        reg[base].append((p, meta))
    return reg


def pick_card_meta(reg: dict, card_id: str):
    """Best-effort match of a run-dir card_id (which may carry a spurious literal
    '.md' from a driver bug) to a queue card's frontmatter."""
    candidates = [card_id, strip_card_suffix(card_id + ".md"), card_id.replace(".md", "")]
    for cid in candidates:
        if cid in reg:
            entries = reg[cid]
            for p, meta in entries:
                if meta.get("snippet_file", "").endswith(".c"):
                    return p, meta
            return entries[0]
    return None, {}


def split_run_dirname(name: str):
    m = TS_RE.match(name)
    if not m:
        return None
    return m.group("card")


def card_numeric_prefix(card_id: str):
    m = re.match(r"^(\d+)", card_id)
    return int(m.group(1)) if m else None


def git_show(worktree: Path, sha: str, relpath: str) -> bytes | None:
    if not sha or not worktree.is_dir():
        return None
    r = subprocess.run(["git", "-C", str(worktree), "show", f"{sha}:{relpath}"],
                        capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout


def detect_header_from_skeleton(skeleton_text: str) -> str | None:
    m = re.search(r'^\s*#include\s+"([^"]+)"', skeleton_text, re.M)
    if not m:
        return None
    return f"csrc/{m.group(1)}" if "/" not in m.group(1) else m.group(1)


def classify_snippet_format(reply: str, target_names: list[str]) -> str:
    raw_openers = len(re.findall(r"```snippet\b", reply))
    strict_matches = SNIPPET_FENCE_RE.findall(reply)
    if len(strict_matches) >= 2:
        return f"two-or-more-snippet-blocks({len(strict_matches)})"
    if raw_openers >= 1 and len(strict_matches) == 0:
        detail = "snippet-opener-unclosed(truncated)"
    elif raw_openers == 0:
        detail = "no-snippet-fence"
    else:
        detail = "snippet-fence-other"
    blocks = fenced_blocks_paired(reply)
    if not blocks:
        return detail + "; fallback:no-closed-fenced-blocks"
    defining = [b for b in blocks if all(c_def_present(b, n) for n in target_names)]
    if len(defining) == 0:
        return detail + f"; fallback:{len(blocks)}-blocks-none-define-target"
    if len(defining) == 1:
        return detail + "; fallback:would-have-parsed(reconstruction-mismatch)"
    return detail + f"; fallback:{len(defining)}-blocks-define-target"


def extract_block_for_measurement(reply: str, target_names: list[str]):
    strict = SNIPPET_FENCE_RE.findall(reply)
    if len(strict) == 1:
        return strict[0], "snippet-strict"
    blocks = fenced_blocks_paired(reply)
    defining = [b for b in blocks if target_names and all(c_def_present(b, n) for n in target_names)]
    if len(defining) == 1:
        return defining[0], "fallback-unique-target"
    if blocks:
        return blocks[0], "first-fenced-any"
    return "", "raw-reply-no-fence"


def main():
    reg = build_card_registry()
    rows = []
    run_roots = [RUNS] + sorted([d for d in RUNS.glob("_archive_*") if d.is_dir()])
    seen_run_dirs = set()

    for root in run_roots:
        archive_name = "" if root == RUNS else root.name
        for rd in sorted(root.iterdir()):
            if root != RUNS and not rd.is_dir():
                continue
            if root == RUNS and (not rd.is_dir() or rd.name.startswith("_archive_")):
                continue
            card_id = split_run_dirname(rd.name)
            if card_id is None:
                continue
            num = card_numeric_prefix(card_id)
            if num is None or not (200 <= num <= 299):
                continue
            cand_file = rd / "candidates.jsonl"
            if not cand_file.exists():
                continue
            run_key = (archive_name, rd.name)
            if run_key in seen_run_dirs:
                continue
            seen_run_dirs.add(run_key)

            card_path, card_meta = pick_card_meta(reg, card_id)
            snippet_file = card_meta.get("snippet_file")
            snippet_symbol = card_meta.get("snippet_symbol", "")
            header_file_meta = card_meta.get("header_file")
            expected_lines_card = card_meta.get("expected_lines")

            brief = {}
            bpath = rd / "brief.json"
            if bpath.exists():
                try:
                    brief = json.loads(bpath.read_text())
                except Exception:
                    pass

            state = {}
            spath = rd / "state.json"
            if spath.exists():
                try:
                    state = json.loads(spath.read_text())
                except Exception:
                    pass
            base_sha = state.get("base_sha")

            worktree = rd / "worktree"
            instruction_text = brief.get("instruction", "")
            is_c_card = bool(snippet_file and snippet_file.endswith(".c"))
            fallback_used = False
            if not is_c_card:
                # Fallback for cards retired from queue/ before this survey (e.g. the
                # pre-split 201/202/203/204a/... multi-symbol cards): recover snippet_file
                # from the brief's own instruction text ("In csrc/X.c ...") rather than
                # guessing a fixed filename.
                m = re.search(r"\bcsrc/(\w+\.c)\b", instruction_text)
                if m:
                    snippet_file = f"csrc/{m.group(1)}"
                    is_c_card = True
                    fallback_used = True
                else:
                    r1 = rd / "reply-1.md"
                    if r1.exists():
                        txt = r1.read_text(errors="replace")
                        if "#include" in txt and ("om_world" in txt or "uint32_t" in txt):
                            is_c_card = True
                            fallback_used = True
                            # last resort: whichever csrc/*.c in the worktree defines the
                            # first om_* identifier the instruction names.
                            ids = re.findall(r"\bom_[a-z0-9_]+\b", instruction_text)
                            if worktree.is_dir() and ids:
                                for cf in sorted((worktree / "csrc").glob("*.c")):
                                    body = cf.read_text(errors="replace")
                                    if re.search(r"\b" + re.escape(ids[0]) + r"\s*\(", body):
                                        snippet_file = f"csrc/{cf.name}"
                                        break
                            snippet_file = snippet_file or "csrc/faction.c"
            if not is_c_card:
                continue

            target_names = [s.strip() for s in str(snippet_symbol).split(",") if s.strip()]
            if fallback_used and worktree.is_dir() and snippet_file:
                fp = worktree / snippet_file
                if fp.exists():
                    file_text = fp.read_text(errors="replace")
                    mentioned = set(re.findall(r"\bom_[a-z0-9_]+\b", instruction_text))
                    defined_in_file = {m.group(1) for m in FUNC_DEF_RE.finditer(file_text)}
                    overlap = sorted(mentioned & defined_in_file)
                    if overlap:
                        target_names = overlap

            skeleton_bytes = None
            header_bytes = None
            skeleton_source = "missing"
            n_funcs_skeleton = None
            if worktree.is_dir() and snippet_file:
                sk = git_show(worktree, base_sha, snippet_file) if base_sha else None
                if sk is not None:
                    skeleton_source = "base_sha"
                else:
                    fp = worktree / snippet_file
                    if fp.exists():
                        sk = fp.read_bytes()
                        skeleton_source = "worktree-fallback"
                if sk is not None:
                    skeleton_bytes = len(sk)
                    sk_text = sk.decode(errors="replace")
                    n_funcs_skeleton = len(FUNC_DEF_RE.findall(sk_text))
                    hf = header_file_meta or detect_header_from_skeleton(sk_text)
                    if hf:
                        hb = git_show(worktree, base_sha, hf) if base_sha else None
                        if hb is None:
                            fp2 = worktree / hf
                            if fp2.exists():
                                hb = fp2.read_bytes()
                        if hb is not None:
                            header_bytes = len(hb)
                    if not target_names:
                        # fallback: sniff which function in skeleton is a STUB
                        stub_m = re.search(r"(\w[\w\s\*]*?\b(\w+)\s*\([^;{}]*\)\s*\{\s*/\*\s*STUB\s*\*/)", sk_text)
                        if stub_m:
                            target_names = [stub_m.group(2)]

            is_done = (rd / "DONE").exists()

            for line in cand_file.read_text(errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    c = json.loads(line)
                except Exception:
                    continue
                n = c.get("n")
                reply_path = rd / f"reply-{n}.md"
                reply_text = reply_path.read_text(errors="replace") if reply_path.exists() else ""
                reply_bytes = len(reply_text.encode("utf-8", errors="replace"))

                fence_marker_lines = [ln for ln in reply_text.splitlines() if FENCE_LINE_RE.match(ln)]
                n_fence_markers = len(fence_marker_lines)
                first_fence_label_raw = FENCE_LINE_RE.match(fence_marker_lines[0]).group(1) if fence_marker_lines else ""
                if not fence_marker_lines:
                    first_fence_bucket = "none"
                elif first_fence_label_raw == "snippet":
                    first_fence_bucket = "snippet"
                elif first_fence_label_raw == "c":
                    first_fence_bucket = "c"
                else:
                    first_fence_bucket = "other"
                n_blocks_paired = len(fenced_blocks_paired(reply_text))
                last_fence_closed = (n_fence_markers > 0 and n_fence_markers % 2 == 0)

                stripped = reply_text.rstrip()
                # descriptive only (per spec): does the reply end on a closing fence or a
                # complete sentence/statement, vs. cut off mid-word/mid-statement.
                looks_complete = bool(stripped) and (stripped.endswith("```") or stripped[-1] in ".!?;:}`)]\"'")
                ends_mid_token = not looks_complete
                last60 = stripped[-60:].replace("\n", "\\n")

                block, block_source = extract_block_for_measurement(reply_text, target_names)
                n_funcs_reply = len(FUNC_DEF_RE.findall(block)) if block else 0
                target_defined = bool(target_names) and all(c_def_present(block, tn) for tn in target_names) if block else False

                # classification gate: an actually truncated reply is one whose LAST fence
                # never closes (odd marker count) -- trailing chatter after a closed fence
                # is harmless noise the parser already ignores, so it must not gate here.
                truncated = (n_fence_markers > 0 and not last_fence_closed)
                classification = "OTHER"
                ratio = None
                if n_funcs_skeleton:
                    ratio = n_funcs_reply / n_funcs_skeleton
                if truncated:
                    classification = "TRUNCATED"
                elif ratio is not None and ratio >= 0.9:
                    classification = "WHOLE-FILE"
                elif target_defined and ratio is not None and ratio < 0.5 and n_funcs_reply >= 1:
                    classification = "PARTIAL"
                elif n_funcs_reply == 0 and not fence_marker_lines:
                    classification = "OTHER"

                reason = c.get("reason")
                snippet_fmt_detail = ""
                if reason == "snippet-format":
                    snippet_fmt_detail = classify_snippet_format(reply_text, target_names)

                rows.append(dict(
                    archive=archive_name, run_dir=rd.name, card_id=card_id,
                    card_path=str(card_path) if card_path else "",
                    n=n, rung=c.get("rung"), model=c.get("model"), think=c.get("think"),
                    reason=reason or "", passed=c.get("passed"), failed=c.get("failed"),
                    wall_s=c.get("wall_s"), body_lines_jsonl=c.get("body_lines"),
                    reply_bytes=reply_bytes,
                    first_fence_label_raw=first_fence_label_raw, first_fence_bucket=first_fence_bucket,
                    n_fence_markers=n_fence_markers, n_blocks_paired=n_blocks_paired,
                    last_fence_closed=last_fence_closed, ends_mid_token=ends_mid_token,
                    last60=last60, block_source=block_source,
                    n_funcs_reply=n_funcs_reply, n_funcs_skeleton=n_funcs_skeleton,
                    func_ratio=round(ratio, 3) if ratio is not None else "",
                    target_symbol=";".join(target_names), target_defined=target_defined,
                    classification=classification, snippet_fmt_detail=snippet_fmt_detail,
                    skeleton_bytes=skeleton_bytes, header_bytes=header_bytes,
                    skeleton_source=skeleton_source, diff_sha=c.get("diff_sha"),
                    is_done_run=is_done, brief_source=brief.get("source", ""),
                    brief_expected_lines=brief.get("expected_lines", ""),
                ))

    if not rows:
        print("NO ROWS FOUND. Check card_id regex / queue paths.", file=sys.stderr)
        return

    fieldnames = list(rows[0].keys())
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"WROTE {len(rows)} rows -> {OUT_CSV}")

    # ---------------- A: model x think x classification x reason ----------------
    print("\n=== A: model|think x classification x reason (counts) ===")
    a_counter = Counter()
    for r in rows:
        a_counter[(r["model"], r["think"], r["classification"], r["reason"] or "PASS")] += 1
    for k in sorted(a_counter):
        print(k, a_counter[k])

    # ---------------- B: per-card summary ----------------
    print("\n=== B: per-card runs/attempts/passes ===")
    by_card = defaultdict(lambda: {"runs": set(), "attempts": 0, "passes": 0, "pass_who": [],
                                    "skel_bytes": set(), "hdr_bytes": set()})
    for r in rows:
        d = by_card[r["card_id"]]
        d["runs"].add((r["archive"], r["run_dir"]))
        d["attempts"] += 1
        if r["reason"] == "" and r["passed"]:
            d["passes"] += 1
            d["pass_who"].append(f"{r['run_dir']}#n{r['n']}:{r['model']}/{r['think']}")
        if r["skeleton_bytes"]:
            d["skel_bytes"].add(r["skeleton_bytes"])
        if r["header_bytes"]:
            d["hdr_bytes"].add(r["header_bytes"])

    def card_sort_key(cid):
        m = re.match(r"^(\d+)([a-z]*\d*)", cid)
        return (int(m.group(1)), m.group(2)) if m else (9999, cid)

    for cid in sorted(by_card, key=card_sort_key):
        d = by_card[cid]
        print(f"{cid}: runs={len(d['runs'])} attempts={d['attempts']} passes={d['passes']} "
              f"skel_bytes={sorted(d['skel_bytes'])} hdr_bytes={sorted(d['hdr_bytes'])} "
              f"pass_who={d['pass_who']}")

    # ---------------- C: reason==tests & classification==PARTIAL ----------------
    print("\n=== C: reason=tests & classification=PARTIAL ===")
    c_rows = [r for r in rows if r["reason"] == "tests" and r["classification"] == "PARTIAL"]
    print(f"count = {len(c_rows)}")
    for r in c_rows[:2]:
        rp = RUNS / r["archive"] / r["run_dir"] if r["archive"] else RUNS / r["run_dir"]
        reply_path = rp / f"reply-{r['n']}.md"
        text = reply_path.read_text(errors="replace") if reply_path.exists() else ""
        first15 = "\n".join(text.splitlines()[:15])
        print(f"--- card={r['card_id']} run={r['run_dir']} n={r['n']} ---")
        print(first15)
        print()

    # ---------------- D: reason==snippet-format breakdown ----------------
    print("\n=== D: reason=snippet-format detail breakdown ===")
    d_rows = [r for r in rows if r["reason"] == "snippet-format"]
    d_counter = Counter(r["snippet_fmt_detail"] for r in d_rows)
    for k, v in d_counter.most_common():
        print(v, k)
    print(f"\ntotal snippet-format rows = {len(d_rows)}")
    picked, seen_details = [], set()
    for r in d_rows:
        key = r["snippet_fmt_detail"].split(";")[0]
        if key not in seen_details:
            seen_details.add(key)
            picked.append(r)
        if len(picked) == 3:
            break
    for r in picked:
        rp = RUNS / r["archive"] / r["run_dir"] if r["archive"] else RUNS / r["run_dir"]
        reply_path = rp / f"reply-{r['n']}.md"
        text = reply_path.read_text(errors="replace") if reply_path.exists() else ""
        print(f"--- card={r['card_id']} run={r['run_dir']} n={r['n']} detail={r['snippet_fmt_detail']} ---")
        print(repr(text.rstrip()[-100:]))

    # ---------------- E: brief.json across 202b2 runs ----------------
    print("\n=== E: 202b2 brief.json survey ===")
    seen_briefs = set()
    mess_count = 0
    for root in run_roots:
        archive_name = "" if root == RUNS else root.name
        for rd in sorted(root.iterdir()):
            if not rd.is_dir():
                continue
            cid = split_run_dirname(rd.name)
            if cid is None or not cid.startswith("202b2"):
                continue
            bpath = rd / "brief.json"
            if not bpath.exists():
                continue
            key = (archive_name, rd.name)
            if key in seen_briefs:
                continue
            seen_briefs.add(key)
            try:
                b = json.loads(bpath.read_text())
            except Exception:
                continue
            instr = b.get("instruction", "")
            has_a = "from 0 to OM_MAX_FACTIONS - 1" in instr
            has_b = "all other functions" in instr
            print(f"{archive_name or '(live)'}/{rd.name}: expected_lines={b.get('expected_lines')} "
                  f"source={b.get('source')} has_from0toMAX={has_a} has_all_other_functions={has_b}")
            cf = rd / "candidates.jsonl"
            if cf.exists():
                for line in cf.read_text(errors="replace").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        c = json.loads(line)
                    except Exception:
                        continue
                    reason = (c.get("reason") or "")
                    if "mess" in reason or "too-long" in reason or reason == "syntax":
                        mess_count += 1
    print(f"\nmess()-heuristic rejects across ALL rows (reason in {{too-long,syntax}}) = "
          f"{sum(1 for r in rows if r['reason'] in ('too-long', 'syntax'))}")
    print(f"(202b2-scoped count from second pass) = {mess_count}")

    # ---------------- F: wall_s outliers ----------------
    print("\n=== F: top 10 wall_s outliers ===")
    for r in sorted(rows, key=lambda r: (r["wall_s"] or 0), reverse=True)[:10]:
        print(f"wall_s={r['wall_s']} model={r['model']} think={r['think']} reply_bytes={r['reply_bytes']} "
              f"card={r['card_id']} run={r['run_dir']} n={r['n']} reason={r['reason']}")


if __name__ == "__main__":
    main()
