#!/usr/bin/env python3
"""Fail when Night Iris release metadata drifts between runtime packages."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        fail("VERSION is empty")

    with (ROOT / "pyproject.toml").open("rb") as handle:
        backend_version = tomllib.load(handle)["project"]["version"]

    frontend = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    frontend_lock = json.loads(
        (ROOT / "frontend/package-lock.json").read_text(encoding="utf-8")
    )
    frontend_version = frontend["version"]
    frontend_lock_version = frontend_lock["version"]
    frontend_lock_root_version = frontend_lock["packages"][""]["version"]

    versions = {
        "VERSION": version,
        "pyproject.toml": backend_version,
        "frontend/package.json": frontend_version,
        "frontend/package-lock.json": frontend_lock_version,
        "frontend/package-lock.json root package": frontend_lock_root_version,
    }
    mismatched = {name: value for name, value in versions.items() if value != version}
    if mismatched:
        details = ", ".join(f"{name}={value!r}" for name, value in mismatched.items())
        fail(f"release version drift: canonical={version!r}; {details}")

    settings_text = (ROOT / "config/settings.py").read_text(encoding="utf-8")
    if '"VERSION": APP_VERSION' not in settings_text:
        fail("OpenAPI version is not derived from APP_VERSION")
    if 'f"night-iris@{APP_VERSION}"' not in settings_text:
        fail("Sentry fallback release is not derived from APP_VERSION")

    print(f"Release metadata consistent: {version}")


if __name__ == "__main__":
    main()
