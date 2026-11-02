"""Parked values for tests/specfactory/test_gate_channels.py: interfaces H-059 leaves open.

Each is None until the Architect rules the question below (Q-H059-4 is ruled, see its value); a test that needs one fails with the question named.
Nobody guessed these (docs/method/test_writer.md: a value nobody gave goes in a *_park_* file).

Q-H059-4 (test t4d): land_push.sh "fails closed when the lock is not won inside its timeout", but the story names
neither the timeout nor how a caller sets it. Candidates:
  (a) an environment variable, e.g. LAND_PUSH_LOCK_TIMEOUT_S (seconds)
  (b) a flag, e.g. `land_push.sh --lock-timeout S <worktree> <id>`
  (c) a fixed value in the script (then the test must wait it out; needs the value and Westley's tolerance)
Set LAND_PUSH_TIMEOUT_ENV to the variable name for (a).
"""
LAND_PUSH_TIMEOUT_ENV = "LAND_PUSH_LOCK_TIMEOUT_S"  # ruled: docs/stories/H-059.md:30 item 2 (default 600 s; a test seam)
