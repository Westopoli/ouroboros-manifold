"""Budget gate for every factory runner that calls a model.

Westley's rule (2026-09-14): test authoring burned Antigravity's Gemini
five-hour window in about twenty minutes across two chats. Before any batch
that calls a model, the person running the factory must say which budget it
spends, after checking the current state of both:

  * gemini  — agy on the Gemini quota group (`agy` then `/credits`; short bursts only)
  * claude  — Claude Code Sonnet sub-agents on the Claude Max subscription

Runners refuse to start until FACTORY_BUDGET is set to one of those. A chat
should ask Westley for his current Claude usage before choosing.
"""
from __future__ import annotations

import os
import sys

CHOICES = ("gemini", "claude")


def require_budget() -> str:
    choice = os.environ.get("FACTORY_BUDGET", "").strip().lower()
    if choice in CHOICES:
        return choice
    sys.stderr.write(
        "BUDGET CHECK: set FACTORY_BUDGET=gemini or FACTORY_BUDGET=claude before running this.\n"
        "Ask Westley for his current Claude usage first. Gemini's five-hour window drains in\n"
        "minutes under parallel fills (2026-09-14); check `agy` -> /credits before choosing it.\n"
        "With claude, prefer Claude Code Sonnet sub-agents over agy.\n")
    sys.exit(3)
