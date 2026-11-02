"""PARKED numbers for tests/qa/test_unit_scale_readthrough.py (H-041). Westley owns every tolerance; nobody has given these.
Register row: none yet, the Architect raises one (suggested id Q-H041-footprint-tol). Not a test file; never edited by a builder.
"""

# DRAFT-footprint-tol: the unit's ground footprint radius in the game may differ from the file's radius by this share of the radius.
# Reasoning for the proposal: the file holds three decimals (error at most 0.0005 x 15 = 0.0075 wu, under 0.2 % of the smallest radius 4.05),
# the footprint is a drawn model measured by eye (a player cannot tell 5 % on a 4 wu unit), and the sim collides at the file's exact
# radius, so a visible footprint within 5 % never shows an overlap or a gap the collisions do not. Westley may tighten or widen it.
FOOTPRINT_TOL_PCT = 5.0

# The H-023 scene's meaning of the number (Architect ruling 2026-11-02, rule 2): drawn radius = visual_scale x BASE_RADIUS wu, where
# BASE_RADIUS is scenes/proto/unit_scale/unit_scale_model.gd's 15 (OM_UNIT_COLLISION_RADIUS). It is a restatement of that scene's
# constant, parked so a change to it is Westley's.
H023_BASE_RADIUS_WU = 15.0
