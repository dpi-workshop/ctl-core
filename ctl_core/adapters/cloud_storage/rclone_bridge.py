"""Optional rclone bridge for copying CTL packages.

This adapter does not bundle rclone and does not manage credentials. It calls an
external rclone executable selected by the user, `CTL_RCLONE_BIN`, or `PATH`.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ...cli import validate_package


ADAPTER_ID = "cloud_storage.rclone"
ADAPTER_VERSION = "0.1"
DEFAULT_TIMEOUT_SECONDS = 300


def find_rclone(explicit_path: str | None = None) -> str | None:
    """Return the rclone executable path if available."""

    if explicit_path:
        expanded = Path(explicit_path).expanduser()
        if expanded.exists():
            return str(expanded.resolve())
        if shutil.which(explicit_path):
            return str(explicit_path)
        return None

    candidates = [
        os.environ.get("CTL_RCLONE_BIN"),
        shutil.which("rclone"),
        shutil.which("rclone.exe"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        expanded = Path(candidate).expanduser()
        if expanded.exists():
            return str(expanded.resolve())
        if shutil.which(candidate):
            return str(candidate)
    return None


def validate_target(value: str) -> str:
    """Reject target strings that are unsafe to pass to a subprocess."""

    target = value.strip()
    if not target:
        raise ValueError("rclone target is required")
    if target.startswith("-"):
        raise ValueError("rclone target must not start with '-'")
    if re.search(r"[\r\n\x00]", target):
        raise ValueError("rclone target must not contain control characters")
    return target


def run_rclone(args: list[str], *, rclone_bin: str | None = None, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    executable = find_rclone(rclone_bin)
    if not executable:
        return {
            "adapter_id": ADAPTER_ID,
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": "rclone executable not found. Install rclone or set CTL_RCLONE_BIN.",
        }

    command = [executable, *args]
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    return {
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "available": True,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def status(*, rclone_bin: str | None = None) -> dict[str, Any]:
    result = run_rclone(["version"], rclone_bin=rclone_bin, timeout=30)
    result["operation"] = "status"
    result["installed"] = result.get("available", False) and result.get("returncode") == 0
    result["source_of_truth"] = "CTL package files; rclone is an optional copy/sync bridge."
    return result


def list_remotes(*, rclone_bin: str | None = None) -> dict[str, Any]:
    result = run_rclone(["listremotes"], rclone_bin=rclone_bin, timeout=30)
    remotes = []
    if result.get("returncode") == 0:
        remotes = [line.strip() for line in result.get("stdout", "").splitlines() if line.strip()]
    result["operation"] = "list_remotes"
    result["remotes"] = remotes
    return result


def copy_package(
    package: Path,
    target: str,
    *,
    rclone_bin: str | None = None,
    dry_run: bool = False,
    checksum: bool = True,
) -> dict[str, Any]:
    root = package.expanduser().resolve()
    errors = validate_package(root)
    if errors:
        raise ValueError("Cannot copy invalid CTL package: " + "; ".join(errors))
    destination = validate_target(target)

    args = ["copy", str(root), destination]
    if checksum:
        args.append("--checksum")
    if dry_run:
        args.append("--dry-run")

    result = run_rclone(args, rclone_bin=rclone_bin)
    result.update(
        {
            "operation": "copy_package",
            "package": str(root),
            "target": destination,
            "dry_run": dry_run,
            "checksum": checksum,
            "deletes_destination_files": False,
        }
    )
    return result


def sync_package(
    package: Path,
    target: str,
    *,
    rclone_bin: str | None = None,
    dry_run: bool = False,
    checksum: bool = True,
    confirm_delete_risk: bool = False,
) -> dict[str, Any]:
    if not dry_run and not confirm_delete_risk:
        raise ValueError("rclone sync can delete destination files; pass --confirm-delete-risk to run it.")

    root = package.expanduser().resolve()
    errors = validate_package(root)
    if errors:
        raise ValueError("Cannot sync invalid CTL package: " + "; ".join(errors))
    destination = validate_target(target)

    args = ["sync", str(root), destination]
    if checksum:
        args.append("--checksum")
    if dry_run:
        args.append("--dry-run")

    result = run_rclone(args, rclone_bin=rclone_bin)
    result.update(
        {
            "operation": "sync_package",
            "package": str(root),
            "target": destination,
            "dry_run": dry_run,
            "checksum": checksum,
            "deletes_destination_files": True,
        }
    )
    return result
