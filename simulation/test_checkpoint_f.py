import os
import json
import shutil

# Clean prompts dir to avoid mixing with chronicle prompts
if os.path.exists("prompts"):
    shutil.rmtree("prompts")

os.system("python3 library_builder.py --mode manual --content naming")

# Check variable_subsets.json
subsets_path = "prompts/variable_subsets.json"
with open(subsets_path) as f:
    subsets = json.load(f)

print("\n=== Checkpoint F: Naming Pool Generation ===")
print(f"\n=== Variable Subsets ({len(subsets)} factions) ===")
header = f"  {'Faction':<16}{'Roots':<8}{'Patterns':<10}{'Tags':<8}"
print(header)
print("  " + "-" * (len(header) - 2))
for fid, sub in subsets.items():
    nr = len(sub["linguistic_roots"])
    np = len(sub["phoneme_patterns"])
    nt = len(sub["cultural_flavor_tags"])
    wider = " (wider)" if fid == "player" else ""
    print(f"  {fid:<16}{nr:<8}{np:<10}{nt:<8}{wider}")

# Verify player has wider subset
player = subsets["player"]
other = subsets["conqueror"]
assert len(player["linguistic_roots"]) > len(other["linguistic_roots"]), \
    "Player should have more roots than non-player"
print(f"\n  Player has wider subset than others: YES")

# Count prompt files (excluding variable_subsets.json)
prompt_files = sorted(f for f in os.listdir("prompts")
                      if f.endswith(".txt"))
print(f"\n=== Prompt files: {len(prompt_files)} ===")
for f in prompt_files[:5]:
    print(f"    {f}")
if len(prompt_files) > 5:
    print(f"    ... and {len(prompt_files) - 5} more")

assert len(prompt_files) == 40, f"Expected 40 prompt files, got {len(prompt_files)}"
print(f"  40 prompt files: YES")

# Analyze one prompt
sample_path = os.path.join("prompts", prompt_files[0])
with open(sample_path) as f:
    content = f.read()

print(f"\n=== Sample prompt: {prompt_files[0]} ===")
for line in content.split("\n"):
    line = line.strip()
    if line.startswith("Faction:"):
        print(f"  {line}")
    if line.startswith("Name category:"):
        print(f"  {line}")
    if line.startswith("Generate:"):
        print(f"  {line}")
    if line.startswith("- Linguistic roots:"):
        print(f"  {line}")
    if line.startswith("- Phoneme patterns:"):
        print(f"  {line}")
    if line.startswith("- Cultural flavor tags:"):
        print(f"  {line}")

# Verify overshoot
if "overshoot" in content.lower() or "550" in content:
    print(f"  10% overshoot mentioned: YES")
else:
    print(f"  10% overshoot mentioned: checking count...")
    for line in content.split("\n"):
        if "Generate:" in line:
            print(f"    {line.strip()}")

print("\n=== Done ===")
