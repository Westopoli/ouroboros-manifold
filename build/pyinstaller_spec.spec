# PyInstaller spec for the Ouroboros Manifold sim bundle.
# Stage 13 Checkpoint A. One-dir mode: produces sim/ouroboros_sim.exe + sim/_internal/.
#
# Iterate hidden_imports during Checkpoint A — start the bundle, run it with
# --root <test>, watch stderr for ImportError, append the missing module here,
# rebuild. 2-3 rounds is normal.
#
# Invoke from build_zip.py via:
#   pyinstaller --noconfirm build/pyinstaller_spec.py
# Or directly:
#   pyinstaller --noconfirm --workpath build/_pyi_work --distpath build/_pyi_dist build/pyinstaller_spec.py

# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent  # build/ -> project root  # noqa: F821
SIM_DIR = PROJECT_ROOT / "simulation"
ENTRY_SCRIPT = str(SIM_DIR / "pipe_transport.py")

# Modules PyInstaller's static analysis is unlikely to discover.
# Add anything imported via __import__, importlib, or string-keyed dispatch.
hidden_imports = [
    # Sim engine modules dispatched dynamically (extend during Checkpoint A).
    "config",
    "tactical_engine",
    "tactical_map",
    "command",
    "command_ingest",
    "damage",
    "movement",
    "facing",
    "ability",
    "fog_of_war",
    "objectives",
    "reinforcement",
    "spine_drift",
    "snapshot_serializer",
    "naming_system",
    "mission_generator",
    "mission_briefing",
    "mission_contracts",
    "force_allocator",
    "force_composition",
    "outcome_resolver",
    "behavior_runner",
    "script_loader",
    "trigger_bus",
    "fairness_evaluator",
    "archetype_filters",
    "layout_library",
    "layout_instantiator",
    "map_generator",
    "map_gen_contracts",
    "gradient_placer",
    "sim_flavoring",
    "chronicle_distiller",
    "chronicle_assembler",
    "coherence_ledger",
    "lifecycle",
    "generational",
    "character_selector",
    "save_writer",
    "save_loader",
    "onboarding_store",
    "bug_report_bundler",
    "debrief_data",
    "power_rating",
    "unit",
    "world",
    "faction",
    "events",
    "time_jump",
    "world_view",
    "world_view.time_jump_emitter",
]

# Data files bundled inside _internal/. Each entry is (source, dest_in_bundle).
# Library JSON, layout JSON, scripts JSON, prompt templates.
datas = [
    (str(SIM_DIR / "library"), "library"),
    (str(SIM_DIR / "layout_library"), "layout_library"),
    (str(SIM_DIR / "scripts"), "scripts"),
    (str(SIM_DIR / "prompts"), "prompts"),
]


a = Analysis(  # noqa: F821
    [ENTRY_SCRIPT],
    pathex=[str(SIM_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ouroboros_sim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # I3 — no visible console window when Godot spawns the sim
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ouroboros_sim",
)
