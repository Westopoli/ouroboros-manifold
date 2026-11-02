"""Parked values for tests/specfactory/test_gate_channels.py: interfaces H-059 leaves open.

Each is None until the Architect rules the question below; a test that needs one fails with the question named.
Nobody guessed these (docs/method/test_writer.md: a value nobody gave goes in a *_park_* file).

Q-H059-1 (test 5): how does status_check.py learn which channel lock the clerk took? Candidates:
  (a) an argument: `status_check.py --repo R --story H-xyz --lock gate-lab.lock`
  (b) an argument on the channel word: `status_check.py --repo R --story H-xyz --took-channel lab`
  (c) it reads the lock name out of the clerk's gate command line (a log or a file path passed in).
Set TAKEN_LOCK_ARGV to a function (story_id, lock_name) -> list of extra argv for status_check.py.
"""
TAKEN_LOCK_ARGV = None
