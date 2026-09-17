import ctypes, os

REPO = "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/e5a6ed2f-9b6f-4836-ba20-e13fc9129eef/scratchpad/drift_trace/repo"
lib = ctypes.CDLL(os.path.join(REPO, "libouroboros.so"))

V = ctypes.c_void_p
lib.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]; lib.om_world_new.restype = V
lib.om_world_set_feature.argtypes = [V, ctypes.c_int, ctypes.c_int]; lib.om_world_set_feature.restype = None
lib.om_world_feature.argtypes = [V, ctypes.c_int]; lib.om_world_feature.restype = ctypes.c_int
lib.om_region_set.argtypes = [V, ctypes.c_uint32, ctypes.c_int,
                               ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
                               ctypes.c_double, ctypes.c_double, ctypes.c_int32]
lib.om_region_set.restype = ctypes.c_int
lib.om_world_step.argtypes = [V]; lib.om_world_step.restype = ctypes.c_uint64
lib.om_region_field.argtypes = [V, ctypes.c_uint32, ctypes.c_int]; lib.om_region_field.restype = ctypes.c_double

OM_F_MILITARY, OM_F_ECONOMY, OM_F_TENSION, OM_F_POPULATION = 0, 1, 2, 3
FIELD_NAMES = {0: "military", 1: "economy", 2: "tension", 3: "population"}
OM_TIER_HOME = 2

w = lib.om_world_new(1, 42)
assert w

rc = lib.om_region_set(w, 0, OM_TIER_HOME, 50.0, 50.0, 50.0, 50.0, 0.4, 0.1, -1)
assert rc == 0, rc

# Default feature state right after om_world_new (before any set_feature call).
print("=== defaults straight from om_world_new (no set_feature calls yet) ===")
for name, val in [("EVENTS",0),("FACTIONS",1),("FRICTION",2),("ADMIN_REVOLTS",3),
                   ("DIPLOMACY",4),("TECHNOLOGY",5),("DRIFT",6),("LIFECYCLE",7)]:
    print(f"  OM_FEAT_{name} = {lib.om_world_feature(w, val)}")

# Now mimic isolate_agents(): turn EVENTS/DIPLOMACY/TECHNOLOGY/DRIFT/LIFECYCLE off,
# FACTIONS on, FRICTION/ADMIN off.
for val in (0, 4, 5, 6, 7):
    lib.om_world_set_feature(w, val, 0)
lib.om_world_set_feature(w, 1, 1)  # FACTIONS on
lib.om_world_set_feature(w, 2, 0)  # FRICTION off
lib.om_world_set_feature(w, 3, 0)  # ADMIN off

print()
print("=== after isolate_agents()-equivalent call (DRIFT explicitly OFF) ===")
before = {f: lib.om_region_field(w, 0, f) for f in FIELD_NAMES}
print("before step:", {FIELD_NAMES[k]: v for k, v in before.items()})
lib.om_world_step(w)
after = {f: lib.om_region_field(w, 0, f) for f in FIELD_NAMES}
print("after 1 step:", {FIELD_NAMES[k]: v for k, v in after.items()})
for f in FIELD_NAMES:
    changed = before[f] != after[f]
    print(f"  {FIELD_NAMES[f]}: changed={changed} delta={after[f]-before[f]!r}")

print()
print("DRIFT feature flag value at time of step:", lib.om_world_feature(w, 6))
