import os

# Run the builder
os.system("python3 library_builder.py --mode manual --content chronicle")

# Count prompt files
prompt_dir = "prompts"
prompt_files = sorted(f for f in os.listdir(prompt_dir) if f.endswith(".txt"))
print(f"\n=== Checkpoint D: Library Builder (Chronicle Fragments) ===")
print(f"  Prompt files generated: {len(prompt_files)}")
for f in prompt_files:
    print(f"    {f}")

# Read and analyze prompt 01
first_path = os.path.join(prompt_dir, prompt_files[0])
with open(first_path) as f:
    content = f.read()

print(f"\n=== First prompt analysis ({prompt_files[0]}) ===")

# Category name
for line in content.split("\n"):
    if line.startswith("Category:"):
        print(f"  {line.strip()}")
    if line.startswith("Required slots"):
        print(f"  {line.strip()}")
    if line.startswith("Emotional register"):
        print(f"  {line.strip()}")

# Check for all 8 rules
for i in range(1, 9):
    marker = f"Rule {i}"
    if marker in content:
        print(f"  {marker}: PRESENT")
    else:
        print(f"  {marker}: MISSING")

# Check for slot vocabulary
if "{character_name}" in content and "{region_name}" in content:
    print(f"  Slot vocabulary: PRESENT")
else:
    print(f"  Slot vocabulary: MISSING")

# Check for JSON output format
if "JSON" in content:
    print(f"  JSON output format: PRESENT")
else:
    print(f"  JSON output format: MISSING")

# Check fragment counts
if "6 openings" in content and "8 details" in content and "5 closings" in content:
    print(f"  Fragment counts (6/8/5): PRESENT")
else:
    print(f"  Fragment counts (6/8/5): MISSING")

print(f"\n=== Done ===")
