#!/usr/bin/env python3
"""Integration check inside the isolated Mac stack; creates then removes test data.

Run with: sh scripts/mac_server.sh compose exec -T api python scripts/mac_smoke.py
Traffic follows the actual gateway/BFF/ASGI/S3 routes, preserving public hosts.
TLS and the tunnel provider itself are checked separately by mac_server.sh.
"""
import base64
import hashlib
from http.cookies import SimpleCookie
import json
import os
import socket
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from apps.media.models import MediaAsset
from apps.media.storage import abort_multipart_upload, delete_object
from apps.users.models import User


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = build_opener(NoRedirect)
app_origin = settings.CSRF_TRUSTED_ORIGINS[0]
app_host = urlsplit(app_origin).netloc
media_host = urlsplit(settings.S3_PUBLIC_ENDPOINT).netloc
cookies = SimpleCookie()


def request(path, *, method="GET", data=None, headers=None, media=False, expected=200):
    host = media_host if media else app_host
    port = 8081 if media else 8080
    request_headers = {"Host": host, "Origin": app_origin}
    if not media and cookies:
        request_headers["Cookie"] = "; ".join(f"{k}={v.value}" for k, v in cookies.items())
    if isinstance(data, dict):
        request_headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    request_headers.update(headers or {})
    req = Request(f"http://gateway:{port}{path}", data=data, headers=request_headers, method=method)
    try:
        response = opener.open(req, timeout=20)
    except HTTPError as exc:
        response = exc
    with response:
        body = response.read()
        # Don't include a presigned URL or cookie in failure output.
        assert response.status == expected, (method, path.split("?")[0], response.status, body[:500])
        return response.headers, body


def api(path, data=None, expected=200):
    _, body = request(path, method="POST" if data is not None else "GET", data=data, expected=expected)
    return json.loads(body)


def websocket(ticket, origin, expected):
    key = base64.b64encode(os.urandom(16)).decode()
    with socket.create_connection(("gateway", 8080), timeout=10) as conn:
        conn.sendall((
            f"GET /ws/notifications/?ticket={ticket} HTTP/1.1\r\n"
            f"Host: {app_host}\r\nOrigin: {origin}\r\n"
            "Connection: Upgrade\r\nUpgrade: websocket\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode())
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = conn.recv(4096)
            assert chunk, "WebSocket closed before the handshake"
            response += chunk
            assert len(response) < 65536
        header = response.split(b"\r\n\r\n", 1)[0]
        assert int(header.split(b" ", 2)[1]) == expected, header
        if expected == 101:
            accept = base64.b64encode(hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
            ).digest())
            assert b"sec-websocket-accept: " + accept.lower() in header.lower()


def main():
    nickname = "mac_smoke_" + uuid.uuid4().hex[:12]
    password = uuid.uuid4().hex + "Az!42"
    try:
        headers, _ = request("/")
        assert "noindex" in headers["X-Robots-Tag"]
        assert "default-src" in headers["Content-Security-Policy"]
        api("/api/v1/ready/")
        request("/api/v1/live/", headers={"Host": "untrusted.example"}, expected=421)
        request("/api/v1/live/", headers={"X-Forwarded-Host": "untrusted.example"})
        headers, _ = request("/", headers={"X-Forwarded-Proto": "http"}, expected=308)
        assert headers["Location"] == app_origin + "/"
        request("/api/schema/", expected=404)
        request("/api/v1/observability/metrics/", expected=404)

        headers, _ = request("/api/auth/register", method="POST", data={
            "nickname": nickname, "email": nickname + "@example.test", "password": password,
            "first_name": "Mac", "last_name": "Smoke", "country": "RU", "nationality": "RU",
            "interface_language": "ru",
        }, expected=201)
        for cookie in headers.get_all("Set-Cookie", []):
            cookies.load(cookie)
        for name in ("night_iris_access", "night_iris_refresh"):
            assert cookies[name]["secure"] and cookies[name]["httponly"]
            assert cookies[name]["samesite"].lower() == "lax"
            assert not cookies[name]["domain"]  # host-only; never sent to media
        me = api("/api/forum/users/me/")
        assert me["nickname"] == nickname
        cookies.clear()
        request("/api/forum/users/me/", expected=401)
        headers, _ = request("/api/auth/login", method="POST", data={"nickname": nickname, "password": password})
        for cookie in headers.get_all("Set-Cookie", []):
            cookies.load(cookie)
        assert api("/api/forum/users/me/")["nickname"] == nickname

        ticket = api("/api/forum/messenger/ws-ticket/", {})["ticket"]
        websocket(ticket, app_origin, 101)
        ticket = api("/api/forum/messenger/ws-ticket/", {})["ticket"]
        websocket(ticket, "https://untrusted.example", 403)

        content = b"Night Iris Mac gateway upload round trip\n"
        asset = api("/api/forum/uploads/initiate/", {
            "original_name": "mac-smoke.txt", "content_type": "text/plain", "size_bytes": len(content),
        }, expected=201)
        upload_path = f"/api/forum/uploads/{asset['id']}"
        signed = api(upload_path + "/parts/sign/", {"part_numbers": [1]})["parts"][0]["url"]
        parsed = urlsplit(signed)
        assert parsed.scheme == "https" and parsed.netloc == media_host
        headers, _ = request(parsed.path, media=True, method="OPTIONS", headers={
            "Access-Control-Request-Method": "PUT", "Access-Control-Request-Headers": "content-type",
        })
        assert headers["Access-Control-Allow-Origin"] == app_origin
        headers, _ = request(parsed.path + "?" + parsed.query, media=True, method="PUT", data=content)
        assert headers["Access-Control-Allow-Origin"] == app_origin
        assert "etag" in headers["Access-Control-Expose-Headers"].lower()
        complete = api(upload_path + "/complete/", {"parts": [{"part_number": 1, "etag": headers["ETag"]}]})
        assert complete["status"] == "ready"
        download = urlsplit(complete["url"])
        assert download.scheme == "https" and download.netloc == media_host
        headers, result = request(download.path + "?" + download.query, media=True)
        assert result == content
        assert "no-store" in headers["Cache-Control"]
        assert headers["Content-Disposition"].startswith("attachment;")
        request(download.path, media=True, expected=403)  # no anonymous objects
        for path in ("/", "/minio/admin/v3/info", "/minio/health/live", "/forum-media/", "/other-bucket/uploads/x"):
            request(path, media=True, expected=404)
        request(download.path, media=True, method="DELETE", expected=404)
        request(download.path, media=True, headers={"Host": app_host}, expected=404)
        print("Mac gateway smoke passed: host checks, HTTPS redirect, secure auth, BFF, WebSocket origin, signed upload/download, CORS, private storage.")
    finally:
        for asset in MediaAsset.objects.filter(owner__nickname=nickname):
            if asset.upload_id:
                abort_multipart_upload(object_key=asset.object_key, upload_id=asset.upload_id)
            delete_object(object_key=asset.object_key)
        User.objects.filter(nickname=nickname).delete()


if __name__ == "__main__":
    main()
