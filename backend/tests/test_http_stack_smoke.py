"""Smoke test of the pinned HTTP stack: python-multipart under FastAPI/Starlette, and aiohttp's client.

backend/requirements.txt pins fastapi==0.104.1 (which forces starlette<0.28) and moves python-multipart and aiohttp
independently, via security patches. Nothing else exercises "form + file upload through Starlette's form parser" or an
aiohttp round trip without a network, so this guards the combination the CI installs.
"""

import io

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.testclient import TestClient


def _app() -> FastAPI:
    app = FastAPI()

    @app.post("/upload")
    async def upload(name: str = Form(...), attachment: UploadFile = File(...)):
        return {"name": name, "size": len(await attachment.read()), "content_type": attachment.content_type}

    @app.post("/login")
    async def login(username: str = Form(...), password: str = Form(...)):
        return {"username": username, "has_password": bool(password)}

    return app


def test_multipart_file_upload_and_text_field():
    r = TestClient(_app()).post(
        "/upload", data={"name": "ana"}, files={"attachment": ("a.txt", io.BytesIO(b"hello"), "text/plain")}
    )
    assert r.status_code == 200
    assert r.json() == {"name": "ana", "size": 5, "content_type": "text/plain"}


def test_urlencoded_form():
    r = TestClient(_app()).post("/login", data={"username": "ana", "password": "x"})
    assert r.status_code == 200 and r.json() == {"username": "ana", "has_password": True}


def test_missing_form_field_is_a_422_not_a_crash():
    assert TestClient(_app()).post("/login", data={"username": "ana"}).status_code == 422


@pytest.mark.asyncio
async def test_aiohttp_client_round_trip_with_timeout_and_session():
    async def hello(request: web.Request) -> web.Response:
        return web.json_response({"q": request.query.get("q"), "ua": request.headers.get("User-Agent")})

    async def echo(request: web.Request) -> web.Response:
        return web.json_response(await request.json())

    app = web.Application()
    app.add_routes([web.get("/hello", hello), web.post("/echo", echo)])
    async with TestServer(app) as server:
        base = f"http://{server.host}:{server.port}"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), headers={"User-Agent": "t"}) as s:
            async with s.get(f"{base}/hello", params={"q": "1"}) as resp:
                assert resp.status == 200 and await resp.json() == {"q": "1", "ua": "t"}
            async with s.post(f"{base}/echo", json={"a": [1, 2]}) as resp:
                assert resp.status == 200 and await resp.json() == {"a": [1, 2]}
