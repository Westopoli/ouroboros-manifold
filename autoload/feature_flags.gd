extends Node

# Stage 11g kill-switch flags — defaults OFF until each checkpoint proves out.
# Mirrors simulation/config.py ENABLE_* constants for the sim side.
# Toggle these to revert to pre-stage-11g behavior cleanly.

var ENABLE_FACTION_PALETTE: bool = true
var ENABLE_INSPECTION_PANELS: bool = true
var ENABLE_INSPECTION_PAUSE: bool = true
var ENABLE_CHRONICLE_MENTIONS: bool = true
var ENABLE_OWNERSHIP_HISTORY: bool = false
var ENABLE_DEBUG_OVERLAY: bool = false
