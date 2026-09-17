import sys, json
sys.path.insert(0, '/home/westopoli/Projects/agora/scripts')
import build

D = "/home/westopoli/Projects/agora/runs/_archive_202b2_pre_gemini_switch/202b2-e05-faction-budget-20260917-1236/worktree"

skeleton_text = open(f"{D}/csrc/faction.c").read()
header_text = open(f"{D}/csrc/ouroboros_sim.h").read()
extra_context_raw = open(f"{D}/csrc/om_internal.h").read()
extra_context = f"# csrc/om_internal.h\n```c\n{extra_context_raw}```\n\n"

symbols = build.c_symbols(header_text)
names = ["om_faction_step_budget"]

brief = json.load(open("/home/westopoli/Projects/agora/runs/_archive_202b2_pre_gemini_switch/202b2-e05-faction-budget-20260917-1236/brief.json"))
instruction = brief["instruction"]

worker_system = open("/home/westopoli/Projects/agora/prompts/worker-build-c.md").read()

user = build._worker_user_c(names, instruction, skeleton_text, header_text, symbols, None, None, extra_context)

with open(f"{sys.argv[1]}/system.txt", "w") as f: f.write(worker_system)
with open(f"{sys.argv[1]}/user.txt", "w") as f: f.write(user)

# component breakdown
scope_line = f"SCOPE (declared in the header, use only these): {', '.join(symbols)}"
instr_block = f"INSTRUCTION:\n{instruction}"
header_block = f"HEADER (read-only, do not change):\n```c\n{header_text}```"
extra_block = "EXTRA CONTEXT (read-only; private layout and helpers not in the header — use these member and type names exactly, do not invent them):\n" + extra_context
whole_block = f"WHOLE FILE (rewrite it; define {', '.join(names)}):\n```c\n{skeleton_text}```"
output_line = f"OUTPUT: exactly one ```snippet block containing the COMPLETE .c file with the #include line and every function {', '.join(names)}; no other text."

report = {
    "system_chars": len(worker_system),
    "scope_line_chars": len(scope_line),
    "instruction_block_chars": len(instr_block),
    "header_block_chars": len(header_block),
    "header_text_chars_alone": len(header_text),
    "extra_context_block_chars": len(extra_block),
    "extra_context_text_chars_alone": len(extra_context_raw),
    "whole_file_block_chars": len(whole_block),
    "skeleton_text_chars_alone": len(skeleton_text),
    "output_line_chars": len(output_line),
    "user_total_chars": len(user),
    "system_plus_user_chars": len(worker_system) + len(user),
    "n_symbols": len(symbols),
    "symbols": symbols,
}
print(json.dumps(report, indent=2))
