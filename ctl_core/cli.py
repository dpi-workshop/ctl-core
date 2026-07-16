"""Small CTL-Core command line helpers.

The CLI reads CTL packages that already exist on disk. It does not own the data
and it does not require a database.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import __version__


REQUIRED_FILES = [
    "manifest.json",
    "search.json",
    "assets/tables/ctl-records.json",
    "manifests/provenance.json",
    "okf/index.md",
]

REQUIRED_DIRS = [
    "assets",
    "assets/original",
    "assets/tables",
    "documents",
    "manifests",
    "okf",
]


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}") from exc


def package_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def is_safe_relative_path(value: str) -> bool:
    if not value:
        return True
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return True
    candidate = Path(value)
    return not candidate.is_absolute() and ".." not in candidate.parts


def validate_package(root: Path) -> list[str]:
    errors: list[str] = []

    if not root.exists():
        return [f"Package path does not exist: {root}"]
    if not root.is_dir():
        return [f"Package path is not a directory: {root}"]

    for folder in REQUIRED_DIRS:
        if not (root / folder).is_dir():
            errors.append(f"Missing required directory: {folder}")

    for filename in REQUIRED_FILES:
        if not (root / filename).is_file():
            errors.append(f"Missing required file: {filename}")

    manifest: dict[str, Any] = {}
    records: list[dict[str, Any]] = []
    search_rows: list[dict[str, Any]] = []

    for filename in ["manifest.json", "search.json", "assets/tables/ctl-records.json", "manifests/provenance.json"]:
        target = root / filename
        if target.exists():
            try:
                data = read_json(target)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if filename == "manifest.json" and isinstance(data, dict):
                manifest = data
            elif filename == "search.json" and isinstance(data, list):
                search_rows = data
            elif filename == "assets/tables/ctl-records.json" and isinstance(data, list):
                records = data
            elif filename == "search.json":
                errors.append("search.json must contain a JSON array")
            elif filename == "assets/tables/ctl-records.json":
                errors.append("assets/tables/ctl-records.json must contain a JSON array")

    if manifest:
        for key in ["ctl_schema_version", "source_id", "record_count"]:
            if key not in manifest:
                errors.append(f"manifest.json is missing key: {key}")

    record_ids: list[str] = []
    for index, record in enumerate(records, start=1):
        record_id = str(record.get("id", "")).strip()
        record_type = str(record.get("type", "")).strip()
        if not record_id:
            errors.append(f"Record {index} is missing id")
        if not record_type:
            errors.append(f"Record {index} is missing type")
        if record_id:
            record_ids.append(record_id)
        for path_key in ["asset_path", "source_path", "asset", "source"]:
            value = record.get(path_key)
            if isinstance(value, str) and not is_safe_relative_path(value):
                errors.append(f"Record {record_id or index} has unsafe {path_key}: {value}")

    duplicates = [record_id for record_id, count in Counter(record_ids).items() if count > 1]
    for record_id in sorted(duplicates):
        errors.append(f"Duplicate record id: {record_id}")

    search_ids = {str(row.get("id", "")) for row in search_rows if isinstance(row, dict)}
    missing_from_search = sorted(set(record_ids) - search_ids)
    if missing_from_search:
        preview = ", ".join(missing_from_search[:5])
        suffix = "..." if len(missing_from_search) > 5 else ""
        errors.append(f"Records missing from search.json: {preview}{suffix}")

    return errors


def load_package(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest = read_json(root / "manifest.json")
    search_rows = read_json(root / "search.json")
    records = read_json(root / "assets/tables/ctl-records.json")
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must contain a JSON object")
    if not isinstance(search_rows, list):
        raise ValueError("search.json must contain a JSON array")
    if not isinstance(records, list):
        raise ValueError("assets/tables/ctl-records.json must contain a JSON array")
    return manifest, search_rows, records


def cmd_inspect(args: argparse.Namespace) -> int:
    root = package_path(args.package)
    manifest, _search_rows, records = load_package(root)
    type_counts = Counter(str(record.get("type", "unknown")) for record in records)
    documents = sorted((root / "documents").glob("*.html")) if (root / "documents").exists() else []
    okf_cards = sorted((root / "okf").rglob("*.md")) if (root / "okf").exists() else []

    print(f"CTL package: {root}")
    print(f"Source ID: {manifest.get('source_id', 'unknown')}")
    print(f"Schema: {manifest.get('ctl_schema_version', 'unknown')}")
    print(f"Records: {len(records)}")
    print(f"Documents: {len(documents)}")
    print(f"OKF cards: {len(okf_cards)}")
    if type_counts:
        print("Record types:")
        for record_type, count in sorted(type_counts.items()):
            print(f"  {record_type}: {count}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = package_path(args.package)
    errors = validate_package(root)
    if errors:
        print("CTL package validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CTL package is valid.")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = package_path(args.package)
    query = args.query.casefold()
    _manifest, search_rows, _records = load_package(root)
    matches: list[dict[str, Any]] = []
    for row in search_rows:
        if not isinstance(row, dict):
            continue
        haystack = " ".join(str(row.get(key, "")) for key in ["id", "type", "text", "source"]).casefold()
        if query in haystack:
            matches.append(row)

    for row in matches[: args.limit]:
        text = str(row.get("text", "")).replace("\n", " ")
        if len(text) > 160:
            text = text[:157] + "..."
        print(f"{row.get('id', 'unknown')} [{row.get('type', 'unknown')}] {text}")

    if not matches:
        print("No matches.")
        return 1 if args.strict else 0
    if len(matches) > args.limit:
        print(f"... {len(matches) - args.limit} more matches")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ctl-core", description="Inspect, validate, and search CTL packages.")
    parser.add_argument("--version", action="version", version=f"CTL-Core {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Show a CTL package summary.")
    inspect_parser.add_argument("package", help="Path to a CTL package folder.")
    inspect_parser.set_defaults(func=cmd_inspect)

    validate_parser = subparsers.add_parser("validate", help="Validate a CTL package folder.")
    validate_parser.add_argument("package", help="Path to a CTL package folder.")
    validate_parser.set_defaults(func=cmd_validate)

    search_parser = subparsers.add_parser("search", help="Search a CTL package search.json file.")
    search_parser.add_argument("package", help="Path to a CTL package folder.")
    search_parser.add_argument("query", help="Case-insensitive text query.")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum result rows to print.")
    search_parser.add_argument("--strict", action="store_true", help="Exit with code 1 when no matches are found.")
    search_parser.set_defaults(func=cmd_search)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
