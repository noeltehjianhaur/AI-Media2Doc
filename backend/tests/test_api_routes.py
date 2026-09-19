import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app import app


class ApiRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_route(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "healthy")

    @patch("routers.provider_usage.provider_usage_service.refresh", new_callable=AsyncMock)
    def test_provider_usage_route(self, refresh):
        refresh.return_value = {
            name: {
                "status": "not_configured",
                "source": "provider_reported",
                "retrieved_at": "2026-09-16T00:00:00+00:00",
                "reporting_period": None,
                "metrics": [],
                "dashboard_url": None,
                "stale": False,
            }
            for name in ("gemini", "openrouter", "cloudflare")
        }
        response = self.client.get("/api/v1/provider-usage")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()["data"]), {"gemini", "openrouter", "cloudflare"})

    @patch("routers.provider_usage.provider_usage_service.refresh", new_callable=AsyncMock)
    def test_repeated_manual_refresh_returns_cached_data(self, refresh):
        refresh.return_value = {"gemini": {"status": "not_configured"}}
        response = self.client.post("/api/v1/provider-usage/refresh")
        repeated_response = self.client.post("/api/v1/provider-usage/refresh")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(repeated_response.status_code, 200)
        self.assertEqual(repeated_response.json()["data"]["gemini"]["status"], "not_configured")

    def test_model_capabilities_route(self):
        response = self.client.get("/api/v1/provider-usage/models")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()["data"]), {"audio", "video", "text"})

    def test_audio_record_route(self):
        response = self.client.post(
            "/api/v1/records",
            json={
                "processing_mode": "audio",
                "transcript": "hello",
                "generated_content": "# Summary",
                "metadata": {"source_type": "upload", "original_name": "demo.mp3"},
                "title": "Demo Transcript",
                "publish": False,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["output_path"].endswith(".md"))

    @patch("routers.records.publish_bundle")
    def test_existing_bundle_can_retry_publication(self, publish):
        publish.return_value = {"commit_sha": "abc123", "repository_url": "https://github.com/owner/output"}
        response = self.client.post(
            "/api/v1/records/publish",
            json={"title": "Demo", "files": {"record.md": "hello"}},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["commit_sha"], "abc123")


if __name__ == "__main__":
    unittest.main()