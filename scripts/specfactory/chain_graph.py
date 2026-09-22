#!/usr/bin/env python3
"""Emits the JSON dependency DAG Agora's scheduler reads (audit 2026-09-21,
item 17): a card graph derived from the ouroboros-side tools
(`chain_sim.build_dag`, `tick_closure`) instead of a hand-listed order, with
a contract Agora can consume without ever importing an ouroboros-specific
module itself.

Usage:
    scripts/specfactory/chain_graph.py --queue <agora queue dir> --project <path>
        [--orchestrators om_world_step ...] [--out graph.json]

`--orchestrators` names the tick-step entry function(s) whose call order
inside its own source defines the hook-closure edges (PX-08's
`tick_closure` mechanism) -- default `om_world_step`, or read from
`[chain_graph] orchestrators = [...]` in a `specfactory.toml` at the
project root when neither is given; an empty list (a profile that names
none) skips hook-closure edges entirely and falls back to direct
acceptance-symbol ownership only. Reuses `chain_sim.build_dag` verbatim
when the orchestrator set is exactly `{"om_world_step"}` (this project's
only real case, and the one `build_dag`/`tick_closure` were written
against); any other orchestrator set uses a direct-symbol-only DAG with no
hook-closure expansion, noted in a code comment rather than silently
pretending to the same fidelity.

Output shape (this file is the contract; do not change it after the first
commit without a DECISIONS.md row per CLAUDE.md's stale-doc discipline):
    {
      "generated_at": ISO-8601 UTC,
      "project": "<project path>",
      "nodes": [{"card", "kind", "file", "symbols", "epic", "story"}, ...],
      "edges": [{"from", "to", "symbol"}, ...],
      "errors": [{"kind": "cycle"|"double_owner"|"missing_file"|"abi_gap",
                  "cards": [...], "symbol": <str or null>}, ...],
      "notes": [{"kind": "sequential_owner", "cards": [...], "symbol": <str>}, ...]
    }

`notes` is a shape addition (R17, Tenth round resolutions, design lane
2026-09-21 night, candidate (a)): two or more cards claiming one symbol are
`double_owner` (an error) only when reachability over the edge graph does
not order them; when it does (an already-working "sequential extension of
one function across several already-ordered cards" pattern, e.g. E-05's
`om_faction_candidates` across 203a1/203a2/203b1/203c), they move to
`notes` as `sequential_owner` instead -- not an error, and does not affect
the exit code.

Exit 0 when `errors` is empty, else 1 (`notes` never affects this).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain_sim  # noqa: E402
import tick_closure  # noqa: E402
from card_lint import (  # noqa: E402
    _iter_live_and_held_cards,
    _split_list,
    card_id_of,
    collect_acceptance_symbols,
    epic_of_card,
    lint,
)

is_gate = chain_sim.is_gate
from green_check import parse_card  # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 fallback: no toml default, CLI-only
    tomllib = None

DEFAULT_ORCHESTRATORS = ["om_world_step"]


def load_orchestrators_from_toml(project: Path) -> list[str] | None:
    toml_path = project / "specfactory.toml"
    if not tomllib or not toml_path.is_file():
        return None
    data = tomllib.loads(toml_path.read_text())
    section = data.get("chain_graph", {})
    if "orchestrators" in section:
        return list(section["orchestrators"])
    return None


def resolve_orchestrators(cli_value: list[str] | None, project: Path) -> list[str]:
    if cli_value is not None:
        return cli_value
    from_toml = load_orchestrators_from_toml(project)
    if from_toml is not None:
        return from_toml
    return list(DEFAULT_ORCHESTRATORS)


def load_all_cards(queue: Path) -> tuple[list[str], dict[str, dict]]:
    """Every card still actually in play: live `queue/*.md` plus
    `queue/parked/*.hold`. Excludes `.retired`/`.superseded`/`.legacy`/
    `.satisfied-by-*`/`.harness-bug`/`.blocked` -- a superseded card (e.g.
    `202a-e05-faction-identity`, split into 202a1..202a4) still claims its
    old symbols in its own frontmatter, so including it manufactures
    `double_owner` errors against its own live replacements that were
    never real (same reasoning as card_lint.py's `--fuel` runway count)."""
    ids: list[str] = []
    cards: dict[str, dict] = {}
    for p in _iter_live_and_held_cards(queue):
        try:
            card = parse_card(p)
        except Exception:
            continue
        cid = card_id_of(p)
        ids.append(cid)
        cards[cid] = card
    return ids, cards


def find_cycle(nodes: list[str], edges: list[tuple[str, str]]) -> list[str] | None:
    """One cycle (list of card ids, first repeated at the end) if the edge
    set (from -> to, "from" must build before "to") is not a DAG, else
    None. Plain DFS cycle detection."""
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for f, t in edges:
        if f in adj:
            adj[f].append(t)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    path: list[str] = []

    def dfs(n: str) -> list[str] | None:
        color[n] = GRAY
        path.append(n)
        for m in adj.get(n, []):
            if color.get(m) == GRAY:
                i = path.index(m)
                return path[i:] + [m]
            if color.get(m, WHITE) == WHITE:
                found = dfs(m)
                if found:
                    return found
        path.pop()
        color[n] = BLACK
        return None

    for n in nodes:
        if color[n] == WHITE:
            found = dfs(n)
            if found:
                return found
    return None


def compute_descendants(nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, set[str]]:
    """Every node reachable from each node, over the same (from -> to) edge
    set find_cycle uses. Plain DFS per node (the graphs here are small --
    low hundreds of nodes/edges -- so no need for a fancier closure)."""
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for f, t in edges:
        if f in adj:
            adj[f].append(t)
    descendants: dict[str, set[str]] = {}
    for n in nodes:
        seen: set[str] = set()
        stack = list(adj.get(n, []))
        while stack:
            m = stack.pop()
            if m in seen:
                continue
            seen.add(m)
            stack.extend(adj.get(m, []))
        descendants[n] = seen
    return descendants


def order_claimants(claimants: list[str], descendants: dict[str, set[str]]) -> list[str] | None:
    """Upstream-first order of `claimants` if reachability makes every pair
    comparable (one is a descendant of the other); None if any pair is
    unordered -- that pair (and so the whole claimant set) is a real
    `double_owner` conflict, not a sequential extension."""
    for i, a in enumerate(claimants):
        for b in claimants[i + 1:]:
            a_before_b = b in descendants.get(a, ())
            b_before_a = a in descendants.get(b, ())
            if not (a_before_b or b_before_a):
                return None
    return sorted(claimants, key=lambda c: len(descendants.get(c, ())), reverse=True)


def build_direct_symbol_dag(card_ids: list[str], cards: dict[str, dict], project: Path) -> dict:
    """Fallback DAG for an orchestrator set other than {"om_world_step"}:
    direct acceptance-symbol ownership only, no tick-hook closure (that
    expansion is specific to this project's om_world_step convention;
    generalizing it is future work, not silently approximated here)."""
    owner: dict[str, str] = {}
    claimants: dict[str, list[str]] = {}
    for cid in card_ids:
        for sym in _split_list(cards[cid].get("snippet_symbol", "")):
            claimants.setdefault(sym, []).append(cid)
            owner.setdefault(sym, cid)
    duplicate_owners = {s: c for s, c in claimants.items() if len(c) > 1}

    edges: dict[tuple[str, str], set[str]] = {}
    for cid in card_ids:
        card = cards[cid]
        if is_gate(card):
            continue
        direct, _bad = collect_acceptance_symbols(card, project)
        for sym in direct:
            src = owner.get(sym)
            if not src or src == cid:
                continue
            edges.setdefault((src, cid), set()).add(sym)

    edge_list = [{"from": f, "to": t, "via": sorted(v)} for (f, t), v in sorted(edges.items())]
    return {"nodes": list(card_ids), "edges": edge_list, "duplicate_owners": duplicate_owners}


def node_record(cid: str, card: dict) -> dict:
    return {
        "card": cid,
        "kind": "gate" if is_gate(card) else "build",
        "file": card.get("snippet_file", ""),
        "symbols": _split_list(card.get("snippet_symbol", "")),
        "epic": epic_of_card(card),
        "story": chain_sim.story_number_of(card),
    }


def build_graph(queue: Path, project: Path, orchestrators: list[str]) -> dict:
    card_ids, cards = load_all_cards(queue)
    csrc_dir = project / "csrc"
    csrc_texts = {p.name: p.read_text() for p in csrc_dir.glob("*.c")} if csrc_dir.is_dir() else {}

    if set(orchestrators) == {"om_world_step"}:
        dag = chain_sim.build_dag(card_ids, cards, project, csrc_texts)
    elif not orchestrators:
        dag = build_direct_symbol_dag(card_ids, cards, project)
    else:
        # Any other named orchestrator: same direct-symbol fallback, since
        # tick_closure.hooks_in_order/expand_closure are only proven against
        # om_world_step's own call convention in csrc/sim.c.
        dag = build_direct_symbol_dag(card_ids, cards, project)

    nodes = [node_record(cid, cards[cid]) for cid in card_ids]

    edges: list[dict] = []
    for e in dag["edges"]:
        for sym in e.get("via", []):
            edges.append({"from": e["from"], "to": e["to"], "symbol": sym})

    edge_pairs = [(e["from"], e["to"]) for e in dag["edges"]]

    errors: list[dict] = []
    notes: list[dict] = []
    for sym, owners in dag.get("duplicate_owners", {}).items():
        # Order claimants of `sym` using every edge EXCEPT one justified only
        # by `sym` itself: two cards sharing one still-stub symbol always
        # produce a same-symbol edge between them the moment either card's
        # own acceptance also reaches it (an artifact of the duplicate
        # claim, not evidence the claimants are sequenced) -- that alone
        # must never manufacture an order. An edge justified by `sym` AND
        # something else still counts (the something else is real
        # evidence); only a pure `via: [sym]` edge is dropped.
        other_edges = [
            (e["from"], e["to"]) for e in dag["edges"]
            if any(v != sym for v in e.get("via", []))
        ]
        descendants_excl_sym = compute_descendants(card_ids, other_edges)
        order = order_claimants(sorted(owners), descendants_excl_sym)
        if order is not None:
            notes.append({"kind": "sequential_owner", "cards": order, "symbol": sym})
        else:
            errors.append({"kind": "double_owner", "cards": sorted(owners), "symbol": sym})

    cycle = find_cycle(card_ids, edge_pairs)
    if cycle:
        errors.append({"kind": "cycle", "cards": cycle, "symbol": None})

    # lint() needs the card's own path, not a synthetic one; resolve each
    # card's real path under the given queue directory.
    errors_by_card: dict[str, set[str]] = {}
    for cid in card_ids:
        card_path = _find_card_path(queue, cid)
        if card_path is None:
            continue
        findings, lint_errors = lint(card_path, project, queue)
        if lint_errors:
            continue
        codes = {f["code"] for f in findings if f["level"] == "FAIL"}
        errors_by_card[cid] = codes

    for cid, codes in errors_by_card.items():
        if "MISSING_SNIPPET_FILE" in codes:
            errors.append({"kind": "missing_file", "cards": [cid], "symbol": None})
        if "ABI_GAP" in codes:
            errors.append({"kind": "abi_gap", "cards": [cid], "symbol": None})

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": str(project),
        "nodes": nodes,
        "edges": edges,
        "errors": errors,
        "notes": notes,
    }


def _find_card_path(queue: Path, card_id: str) -> Path | None:
    p = queue / f"{card_id}.md"
    if p.exists():
        return p
    parked = queue / "parked"
    if parked.is_dir():
        matches = sorted(parked.glob(f"{card_id}.md.*"))
        order = {"hold": 0, "retired": 1, "superseded": 2, "parked": 3, "legacy": 4}
        matches.sort(key=lambda x: order.get(x.suffix.lstrip("."), 9))
        if matches:
            return matches[0]
    return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--orchestrators", nargs="*", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    queue = Path(args.queue).expanduser()
    project = Path(args.project).expanduser()
    orchestrators = resolve_orchestrators(args.orchestrators, project)

    graph = build_graph(queue, project, orchestrators)
    text = json.dumps(graph, indent=2)

    if args.out:
        Path(args.out).write_text(text + "\n")
    else:
        print(text)

    return 1 if graph["errors"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
