import json
import tomllib
from pathlib import Path

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.django_db
@override_settings(APP_VERSION="1.0.0", BUILD_SHA="abc123")
def test_version_endpoint_exposes_release_provenance():
    response = APIClient().get("/api/v1/version/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "night-iris",
        "version": "1.0.0",
        "build": "abc123",
    }


def test_runtime_package_versions_match_version_file():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    with (ROOT / "pyproject.toml").open("rb") as handle:
        backend_version = tomllib.load(handle)["project"]["version"]
    frontend_version = json.loads(
        (ROOT / "frontend/package.json").read_text(encoding="utf-8")
    )["version"]

    assert version == backend_version == frontend_version
