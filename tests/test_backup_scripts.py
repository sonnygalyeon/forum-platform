import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def backup_project(tmp_path):
    root = Path(__file__).resolve().parents[1]
    shutil.copytree(root / "scripts", tmp_path / "scripts")
    # No real Docker, database, network or production credentials in these tests.
    (tmp_path / ".env.prod").write_text("POSTGRES_USER=forum\nPOSTGRES_DB=forum\nS3_BUCKET=test-media\n")
    (tmp_path / "scripts/prod_smoke.sh").write_text("#!/bin/sh\nexit 0\n")
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    docker = binary_dir / "docker"
    docker.write_text(f"#!{sys.executable}\n" + '''
import json
import os
from pathlib import Path
import subprocess
import sys

args = sys.argv[1:]
with Path("docker-calls.jsonl").open("a") as handle:
    handle.write(json.dumps(args) + "\\n")
if "pg_dump" in args:
    sys.stdout.write("fake PostgreSQL dump")
elif "pg_restore" in args or "psql" in args:
    sys.stdin.read()
elif "storage-tool" in args:
    assert args[args.index("--user") + 1] == f"{os.getuid()}:{os.getgid()}"
    command, source = args[args.index("storage-tool") + 1:][:2]
    source = Path("backups/object-storage") / Path(source).relative_to("/backup")
    if command == "backup":
        source.mkdir()
        (source / "manifest.json").write_text(json.dumps({
            "format": 1, "bucket": "test-media", "object_count": 0, "objects": [],
        }))
    else:
        # Execute the real offline validator for both verification and the
        # simulated remote restore. Record ordering without contacting S3.
        env = {**os.environ, "S3_BUCKET": "test-media"}
        result = subprocess.run([sys.executable, "scripts/object_storage_transfer.py", "verify", str(source)], env=env)
        sys.exit(result.returncode)
''')
    docker.chmod(0o755)
    env = {**os.environ, "PATH": f"{binary_dir}:{os.environ['PATH']}", "BACKUP_SET_ID": "test-snapshot"}

    def run(script, *args, **extra):
        return subprocess.run(["sh", f"scripts/{script}", *args], cwd=tmp_path,
                              env={**env, **extra}, capture_output=True, text=True)

    return tmp_path, run


def test_full_backup_and_restore_use_matching_storage_paths(backup_project):
    root, run = backup_project
    backup = run("backup_all.sh")
    assert backup.returncode == 0, backup.stdout + backup.stderr
    manifest = (root / "backups/manifests/test-snapshot.env").read_text()
    assert "BACKUP_FORMAT=2" in manifest
    assert "OBJECT_STORAGE_DIR=backups/object-storage/forum-media-test-snapshot" in manifest
    assert "OBJECT_STORAGE_SHA256=backups/manifests/test-snapshot.object-storage.sha256" in manifest
    (root / "docker-calls.jsonl").write_text("")
    restored = run("restore_all.sh", "test-snapshot", RESTORE_CONFIRM="YES")
    assert restored.returncode == 0, restored.stdout + restored.stderr
    calls = [json.loads(line) for line in (root / "docker-calls.jsonl").read_text().splitlines()]
    verify = next(i for i, call in enumerate(calls) if "storage-tool" in call and "verify" in call)
    pg_write = next(i for i, call in enumerate(calls) if "psql" in call)
    storage_write = next(i for i, call in enumerate(calls) if "storage-tool" in call and "restore" in call)
    assert verify < pg_write < storage_write
    assert "/backup/forum-media-test-snapshot" in calls[storage_write]


def test_restore_rejects_incomplete_storage_before_database_changes(backup_project):
    root, run = backup_project
    assert run("backup_all.sh").returncode == 0
    manifest_path = root / "backups/object-storage/forum-media-test-snapshot/manifest.json"
    manifest_path.write_text('{"format": 1, "bucket": "test-media", "object_count": 0}')
    # Make the outer checksum valid: structural validation must still refuse it.
    result = subprocess.run(["sha256sum", str(manifest_path.relative_to(root))], cwd=root,
                            check=True, capture_output=True, text=True)
    (root / "backups/manifests/test-snapshot.object-storage.sha256").write_text(result.stdout)
    (root / "docker-calls.jsonl").write_text("")
    restored = run("restore_all.sh", "test-snapshot", RESTORE_CONFIRM="YES")
    assert restored.returncode != 0
    assert "invalid object list/count" in restored.stderr
    calls = [json.loads(line) for line in (root / "docker-calls.jsonl").read_text().splitlines()]
    assert not any("psql" in call or "stop" in call or "restore" in call for call in calls)


def test_legacy_backup_is_rejected_before_any_docker_action(backup_project):
    root, run = backup_project
    (root / "backups/manifests").mkdir(parents=True)
    (root / "backups/manifests/legacy.env").write_text("MINIO_DIR=backups/minio/old\n")
    restored = run("restore_all.sh", "legacy", RESTORE_CONFIRM="YES")
    assert restored.returncode != 0
    assert "legacy backup format" in restored.stderr
    assert not (root / "docker-calls.jsonl").exists()
