"""Lifecycle failure tests; real container/proxy behavior is exercised in CI."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def mac_runner(tmp_path):
    root = tmp_path / "project with spaces"
    (root / "scripts").mkdir(parents=True)
    (root / "VERSION").write_text("1.0.0\n")
    shutil.copyfile(Path(__file__).parents[1] / "scripts/mac_server.sh", root / "scripts/mac_server.sh")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "calls.jsonl"
    docker = bindir / "docker"
    docker.write_text(f"#!{sys.executable}\n" + '''
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['FAKE_LOG'], 'a') as f:
    f.write(json.dumps(args) + '\\n')
if args and args[0] == 'compose' and '--env-file' in args:
    i = args.index('-f') + 2
    action = args[i:]
    if action[0] == 'build' and os.environ.get('FAIL_BUILD'):
        sys.exit(1)
    if action[0] == 'logs':
        if action[-1] == 'tunnel-media' and os.environ.get('FAIL_MEDIA'):
            print('Tunnel connection failed')
        else:
            name = 'demo-site' if action[-1] == 'tunnel-app' else 'demo-media'
            print('Your quick Tunnel: https://' + name + '.trycloudflare.com')
''')
    docker.chmod(0o755)
    for name, body in {"git": "echo 1234567890abcdef", "curl": "exit 0", "sleep": "exit 0"}.items():
        stub = bindir / name
        stub.write_text("#!/bin/sh\n" + body + "\n")
        stub.chmod(0o755)

    def run(*args, **extra):
        env = {**os.environ, "PATH": str(bindir) + os.pathsep + os.environ["PATH"], "FAKE_LOG": str(log), **extra}
        result = subprocess.run(["sh", str(root / "scripts/mac_server.sh"), *args],
                                env=env, capture_output=True, text=True, timeout=30)
        calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        return result, calls

    return root, run


def test_quick_tunnel_hosts_update_without_rotating_credentials(mac_runner):
    root, run = mac_runner
    assert run("init")[0].returncode == 0
    env_file = root / ".env.mac"
    before = dict(line.split("=", 1) for line in env_file.read_text().splitlines())
    result, _ = run("start")
    assert result.returncode == 0, result.stderr
    after = dict(line.split("=", 1) for line in env_file.read_text().splitlines())
    assert after.pop("APP_DOMAIN") == "demo-site.trycloudflare.com"
    assert after.pop("MEDIA_DOMAIN") == "demo-media.trycloudflare.com"
    before.pop("APP_DOMAIN")
    before.pop("MEDIA_DOMAIN")
    assert after == before
    assert env_file.stat().st_mode & 0o777 == 0o600
    assert "Site:  https://demo-site.trycloudflare.com" in result.stdout


def test_incomplete_tunnel_setup_disconnects_public_access(mac_runner):
    root, run = mac_runner
    assert run("init")[0].returncode == 0
    before = (root / ".env.mac").read_bytes()
    result, calls = run("start", FAIL_MEDIA="1")
    assert result.returncode != 0
    assert calls[-1][-4:] == ["stop", "tunnel-app", "tunnel-media", "gateway"]
    assert (root / ".env.mac").read_bytes() == before
    assert not any("down" in call for call in calls)
    assert "Night Iris server is ready." not in result.stdout


def test_failed_build_keeps_existing_server_running(mac_runner):
    _, run = mac_runner
    result, calls = run("start", FAIL_BUILD="1")
    assert result.returncode != 0
    assert not any("stop" in call or "down" in call for call in calls)


@pytest.mark.parametrize("app,media", [
    ("https://example.com", "files.example.com"),
    ("*.example.com", "files.example.com"),
    ("example.com", "example.com"),
    ("example.com/path", "files.example.com"),
])
def test_invalid_external_domains_do_not_touch_docker(mac_runner, app, media):
    root, run = mac_runner
    result, calls = run("start", "--domains", app, media)
    assert result.returncode != 0
    assert not calls
    assert not (root / ".env.mac").exists()
