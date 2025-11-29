"""Smoke tests for the user endpoints."""

import json

from app.main import app
from app.services.user_service import _data_file
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_module():
    path = _data_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{"id": "1", "name": "Tester", "email": "test@example.com"}]), encoding="utf-8")


def test_read_users():
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Tester"


def test_read_user_detail():
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
