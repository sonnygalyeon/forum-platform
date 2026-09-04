from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/check_openapi_compat.py"


def run_check(tmp_path, baseline, current):
    baseline_path = tmp_path / "baseline.yml"
    current_path = tmp_path / "current.yml"
    baseline_path.write_text(yaml.safe_dump(baseline), encoding="utf-8")
    current_path.write_text(yaml.safe_dump(current), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(baseline_path), str(current_path)],
        text=True,
        capture_output=True,
        check=False,
    )


def contract(properties):
    return {
        "openapi": "3.1.0",
        "paths": {
            "/api/v1/example/": {
                "get": {"responses": {"200": {"description": "ok"}}}
            }
        },
        "components": {
            "schemas": {
                "Example": {
                    "type": "object",
                    "properties": properties,
                    "required": ["id"],
                }
            }
        },
    }


def test_openapi_compatibility_allows_additive_changes(tmp_path):
    baseline = contract({"id": {"type": "string"}})
    current = contract(
        {
            "id": {"type": "string"},
            "display_name": {"type": "string"},
        }
    )
    current["paths"]["/api/v1/new/"] = {
        "get": {"responses": {"200": {"description": "ok"}}}
    }

    result = run_check(tmp_path, baseline, current)

    assert result.returncode == 0, result.stderr


def test_openapi_compatibility_rejects_removed_property(tmp_path):
    baseline = contract(
        {"id": {"type": "string"}, "display_name": {"type": "string"}}
    )
    current = contract({"id": {"type": "string"}})

    result = run_check(tmp_path, baseline, current)

    assert result.returncode == 1
    assert "property 'display_name' was removed" in result.stderr
