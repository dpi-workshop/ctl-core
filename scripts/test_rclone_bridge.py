"""Smoke test the optional rclone bridge without requiring rclone."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ctl_core.adapters.cloud_storage.rclone_bridge import run_rclone, status, validate_target


def main() -> None:
    missing = str(ROOT / "tools" / "missing-rclone-for-test.exe")
    result = status(rclone_bin=missing)
    if result["available"]:
        raise SystemExit("Explicit missing rclone path should not fall back to another executable")
    if result["installed"]:
        raise SystemExit("Missing rclone should not report installed")

    run_result = run_rclone(["version"], rclone_bin=missing)
    if run_result["returncode"] is not None:
        raise SystemExit("Missing rclone should not run a subprocess")

    if validate_target("remote:path/to/package") != "remote:path/to/package":
        raise SystemExit("Valid rclone target was rejected")

    for target in ["", "-bad", "remote:path\nbad", "remote:path\x00bad"]:
        try:
            validate_target(target)
        except ValueError:
            continue
        raise SystemExit(f"Unsafe rclone target was accepted: {target!r}")

    print("rclone bridge smoke test passed.")


if __name__ == "__main__":
    main()
