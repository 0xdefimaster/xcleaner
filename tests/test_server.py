import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import server  # noqa: E402

client = TestClient(server.app)


def test_index_is_served():
    assert client.get("/").status_code == 200


def test_start_rejects_foreign_origin():
    r = client.post("/start", data={"username": "abc"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_start_validates_input():
    r = client.post("/start", data={"username": "bad name!", "browser_path": sys.executable})
    assert r.status_code == 400


def test_start_accepts_valid_config():
    r = client.post("/start", data={"username": "abc", "browser_path": sys.executable, "dry_run": "true"})
    assert r.status_code == 200 and "job_id" in r.json()


def test_no_cors_headers():
    r = client.get("/", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers
