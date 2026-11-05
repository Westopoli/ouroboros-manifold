"""PARKED numbers for tests/qa/test_unit_scale_readthrough.py (H-041). Westley owns every tolerance; nobody has given these.
Register row: none yet, the Architect raises one (suggested id Q-H041-footprint-tol). Not a test file; never edited by a builder.
"""

# DRAFT-footprint-tol: the unit's drawn ground footprint radius in the 3D view may differ from the file's radius by this share of the
# radius, in percent. Westley owns it; a change of his is this one constant.
# Reasoning for the proposal: the file holds three decimals (error at most 0.0005 x 15 = 0.0075 wu, under 0.2 % of the smallest radius 4.05),
# the footprint is a drawn body judged by eye (a player cannot tell 5 % on a 4 wu unit), and the sim collides at the file's exact radius,
# so a visible footprint within 5 % never shows an overlap or a gap the collisions do not.
DRAFT_FOOTPRINT_TOL = 5.0
