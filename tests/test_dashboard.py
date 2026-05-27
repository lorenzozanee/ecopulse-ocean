"""Tests for Module C: FastAPI dashboard server."""

from fastapi.testclient import TestClient

from web.server import app

client = TestClient(app)


class TestAPI:
    def test_index_returns_html(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "<html" in resp.text.lower()

    def test_list_regions(self):
        resp = client.get("/api/regions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["regions"]) == 5
        assert data["regions"][0]["key"] == "scs"

    def test_get_report_valid_region(self):
        resp = client.get("/api/report/scs?llm_provider=mock")
        assert resp.status_code == 200
        data = resp.json()
        assert data["region"] == "scs"
        assert len(data["report"]["sections"]) == 4
        assert "stats" in data

    def test_get_report_invalid_region(self):
        resp = client.get("/api/report/xyz")
        assert resp.status_code == 200
        assert "error" in resp.json()

    def test_static_css(self):
        resp = client.get("/static/style.css")
        assert resp.status_code == 200
        assert "background" in resp.text

    def test_static_js(self):
        resp = client.get("/static/app3d.js")
        assert resp.status_code == 200
        assert "WebSocket" in resp.text
