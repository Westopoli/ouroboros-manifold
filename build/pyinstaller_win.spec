# PyInstaller spec for the Ouroboros Manifold sim bundle (Windows).
# Stage 13 Checkpoint A, B5-A. One-dir mode: produces sim/ouroboros_sim.exe + sim/_internal/.
# Mirror of build/pyinstaller_spec.spec (Mac). PyInstaller adds the .exe suffix on Windows
# automatically — do not hardcode it on `name`.
#
# Invoke from build_zip.py via:
#   pyinstaller --noconfirm build/pyinstaller_win.spec
# Or directly:
#   pyinstaller --noconfirm --workpath build/_pyi_work --distpath build/_pyi_dist build/pyinstaller_win.spec

# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent  # build/ -> project root  # noqa: F821
SIM_DIR = PROJECT_ROOT / "simulation"
ENTRY_SCRIPT = str(SIM_DIR / "pipe_transport.py")

hidden_imports = [
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
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
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
