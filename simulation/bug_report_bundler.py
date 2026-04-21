import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path("logs/reports")


def bundle_report(
    sim_state: dict | None = None,
    tactical_snapshots: list[dict] | None = None,
    command_log: list[dict] | None = None,
    mission_metrics: dict | None = None,
    onboarding: dict | None = None,
    crash_log_path: Path | None = None,
    screenshot_path: Path | None = None,
    metadata_overrides: dict | None = None,
    output_dir: Path | None = None,
) -> Path:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"bug_report_{stamp}.zip"
    dest = (output_dir or OUTPUT_DIR) / filename
    dest.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "schema_version": 1,
        "game_version": "0.12.0",
        "timestamp": now.isoformat(),
        "buffer_snapshots_count": len(tactical_snapshots) if tactical_snapshots else 0,
        "command_log_entries": len(command_log) if command_log else 0,
        "note": "Paste this file into Discord for Westley.",
    }
    if metadata_overrides:
        metadata.update(metadata_overrides)

    with zipfile.ZipFile(str(dest), "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))

        if sim_state is not None:
            zf.writestr("sim_state.json", json.dumps(sim_state, indent=2))

        if tactical_snapshots:
            for snap in tactical_snapshots:
                tick = snap.get("tick", 0)
                zf.writestr(
                    f"tactical_snapshots/snapshot_tick_{tick}.json",
                    json.dumps(snap, indent=2),
                )

        if command_log:
            zf.writestr("command_log.json", json.dumps(command_log, indent=2))

        if mission_metrics is not None:
            zf.writestr("mission_metrics.json", json.dumps(mission_metrics, indent=2))

        if onboarding is not None:
            zf.writestr("onboarding.json", json.dumps(onboarding, indent=2))

        if crash_log_path and crash_log_path.exists():
            zf.write(str(crash_log_path), "crash_log.txt")

        if screenshot_path and screenshot_path.exists():
            zf.write(str(screenshot_path), "screenshot.png")

    return dest


def read_report(zip_path: Path) -> dict:
    contents = {}
    with zipfile.ZipFile(str(zip_path), "r") as zf:
        for name in zf.namelist():
            if name.endswith(".json"):
                contents[name] = json.loads(zf.read(name))
            else:
                contents[name] = zf.read(name)
    return contents
