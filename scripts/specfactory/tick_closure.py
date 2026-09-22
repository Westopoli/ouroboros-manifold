#!/usr/bin/env python3
"""PF-8 prototype for H1 (tick-stage closure).

`card_lint.py` collects the om_* symbols a card's acceptance tests reach by
walking the test's own AST (plus conftest helpers) for literal attribute
calls and `getattr(lib, "...")` calls. That misses every symbol a test only
reaches as a side effect of calling the step orchestrator `om_world_step`:
`csrc/sim.c::om_world_step` unconditionally calls `om_faction_step_budget`,
`om_step_telegraphs`, `om_step_decisions`, `om_step_reinforce`,
`om_step_resolve`, `om_step_friction`, and `om_step_admin_revolts` (when
their features are on) without any test ever naming them, so a stub among
them is invisible to card_lint's symbol set no matter which file it lives in
or who owns it.

This module does not change card_lint.py. It provides:

  hooks_in_order(sim_c_text)      -- the om_step_* hook calls in om_world_step,
                                      in tick order.
  expand_closure(symbols, hooks)  -- symbols, plus every hook, if any
                                      orchestrator (om_world_step) is in
                                      symbols.
  stub_hooks_needed(...)          -- narrows that expansion down to hooks
                                      that can actually affect the card's own
                                      acceptance assertions (by struct-field
                                      overlap with the reader symbols --
                                      om_tick_*/om_pending_* -- the test
                                      itself reads), and reports the ones not
                                      yet owned-and-done per a chain order.

Bare `expand_closure` over-approximates: `om_world_step` also runs hooks a
test's fixture never exercises (e.g. every E-05 isolation test still
"reaches" om_step_friction even when OM_FEAT_FRICTION is off for that test).
`stub_hooks_needed` is the piece that keeps that over-approximation from
false-positiving on cards that only read data an undone hook never touches --
see the real-data report for 203a1/203c/203e, which call om_world_step too
but only read back through om_faction_candidates, an unrelated field.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card_lint import (  # noqa: E402
    _split_list,
    card_id_of,
    collect_acceptance_symbols,
    find_function_span,
)
from green_check import parse_card  # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

_SPECFACTORY_TOML = Path(__file__).resolve().parents[2] / "docs/northstar/spec_factory/specfactory.toml"
_DEFAULT_ORCHESTRATORS = {"om_world_step"}


def _load_orchestrators() -> set[str]:
    """`[chain_graph] orchestrators` from docs/northstar/spec_factory/
    specfactory.toml (freeze/F2, decision 3's orchestrator set for tick-stage
    closure); falls back to the historical single-orchestrator constant when
    the file is absent, unreadable, or missing the table."""
    if not tomllib or not _SPECFACTORY_TOML.is_file():
        return set(_DEFAULT_ORCHESTRATORS)
    try:
        data = tomllib.loads(_SPECFACTORY_TOML.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return set(_DEFAULT_ORCHESTRATORS)
    orchestrators = data.get("chain_graph", {}).get("orchestrators")
    if not orchestrators:
        return set(_DEFAULT_ORCHESTRATORS)
    return set(orchestrators)


ORCHESTRATORS = _load_orchestrators()
HOOK_CALL_RE = re.compile(r"^\s*(om_[A-Za-z0-9_]+)\(w\);", re.M)
READER_RE = re.compile(r"^om_(?:tick|pending)_[A-Za-z0-9_]*$")

# Every per-tick record buffer in om_world is an array plus an `_n` count
# (w->attacks/w->attacks_n, w->reinforces/w->reinforces_n, ...), and only the
# hook that owns a buffer ever resets or increments its counter -- a hook
# that merely reads another buffer (om_step_telegraphs reads w->reinforces
# to fold an existing reinforcement into its defense math, om_step_resolve
# reads w->decisions to find attacks to resolve) never touches that
# counter. Matching on the counter, not any struct-field reference, is what
# keeps this from flagging every hook against every reader: the two both
# touch dozens of shared scalar fields (regions, faction_budget, rng_state)
# that have no bearing on whether a *reader*'s buffer is populated yet.
COUNTER_WRITE_RE = re.compile(r"w->(\w+_n)\s*(?:=(?!=)|\+\+)")
COUNTER_READ_RE = re.compile(r"w->(\w+_n)\b")


def hooks_in_order(sim_c_text: str) -> list[str]:
    """The om_step_*-style hook calls inside om_world_step's own body, in
    the order they run each tick. Regex over the function body (per PF-8's
    brief) rather than a full C parse."""
    span = find_function_span(sim_c_text, "om_world_step")
    if span is None:
        return []
    body = sim_c_text[span[0]:span[1]]
    return HOOK_CALL_RE.findall(body)


def expand_closure(symbols: set[str], hooks: list[str],
                    orchestrators: set[str] = ORCHESTRATORS) -> set[str]:
    """symbols ∪ hooks if any orchestrator is in symbols, else symbols
    unchanged. A test that never calls om_world_step (or another
    orchestrator) never runs these hooks, so it gets no closure at all."""
    if symbols & orchestrators:
        return set(symbols) | set(hooks)
    return set(symbols)


def _span_of(csrc_texts: dict[str, str], name: str) -> str | None:
    for text in csrc_texts.values():
        span = find_function_span(text, name)
        if span:
            return text[span[0]:span[1]]
    return None


def _counters_written(csrc_texts: dict[str, str], name: str) -> set[str]:
    body = _span_of(csrc_texts, name)
    return set(COUNTER_WRITE_RE.findall(body)) if body else set()


def _counters_read(csrc_texts: dict[str, str], name: str) -> set[str]:
    body = _span_of(csrc_texts, name)
    return set(COUNTER_READ_RE.findall(body)) if body else set()


def relevant_hooks(direct_symbols: set[str], hooks: list[str],
                    csrc_texts: dict[str, str]) -> set[str]:
    """Which of `hooks` can actually affect this card's own acceptance
    assertions: hooks that write the `_n` counter of a buffer a reader
    (om_tick_*/om_pending_*) the test directly reads copies out of. A hook
    the orchestrator runs but whose buffer the test never reads back is
    inert for this card no matter how undone it is (see 203a1/203c/203e in
    the real-data report: they call om_world_step too, but only ever read
    through om_faction_candidates -- not an om_tick_*/om_pending_* reader
    at all, so they get no closure here regardless of what's undone)."""
    readers = {s for s in direct_symbols if READER_RE.match(s)}
    if not readers:
        return set()
    used_counters: set[str] = set()
    for r in readers:
        used_counters |= _counters_read(csrc_texts, r)
    if not used_counters:
        return set()
    return {h for h in hooks if _counters_written(csrc_texts, h) & used_counters}


def build_owner_map(card_records: list[dict]) -> dict[str, str]:
    """symbol -> card_id, from each record's own snippet_symbol list.
    Unlike card_lint's find_owning_card, this ignores snippet_file --
    the 204a1/204a3 cut shared csrc/resolve.c across three cards, so a
    same-file check can never catch a same-file cross-card dependency."""
    owner: dict[str, str] = {}
    for rec in card_records:
        for sym in _split_list(rec.get("snippet_symbol", "")):
            owner.setdefault(sym, rec["card_id"])
    return owner


def stub_hooks_needed(card_path: Path, project: Path, csrc_texts: dict[str, str],
                       done_symbols: set[str], owner_map: dict[str, str]) -> list[dict]:
    """For one card: collect its acceptance-reached symbols (card_lint's own
    static collector, unmodified), closure-expand them through
    om_world_step, narrow to hooks relevant to what the card's test actually
    reads back, and report each such hook that is owned by a DIFFERENT card
    not yet in `done_symbols`. Returns a list of
    {"hook": symbol, "owner": card_id} findings, empty when clean."""
    card = parse_card(card_path)
    card_id = card_id_of(card_path)
    direct_symbols, _bad = collect_acceptance_symbols(card, project)
    sim_c_text = csrc_texts.get("sim.c", "")
    hooks = hooks_in_order(sim_c_text)
    expanded = expand_closure(direct_symbols, hooks)
    candidate_hooks = expanded & set(hooks)
    needed = relevant_hooks(direct_symbols, hooks, csrc_texts) & candidate_hooks

    findings = []
    for hook in sorted(needed):
        if hook in done_symbols:
            continue
        owner = owner_map.get(hook)
        if owner and owner != card_id:
            findings.append({"hook": hook, "owner": owner})
    return findings
