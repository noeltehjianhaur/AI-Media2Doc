import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from services.provider_usage import ProviderUsageService


class ProviderUsageServiceTests(unittest.TestCase):
    def test_refresh_isolates_provider_failures(self):
        service = ProviderUsageService(cache_seconds=0)
        available = {
            "status": "available",
            "source": "provider_reported",
            "metrics": [{"name": "credits_remaining", "value": 4, "unit": "USD"}],
        }

        with patch.object(service, "fetch_gemini", AsyncMock(return_value=available)), patch.object(
            service, "fetch_openrouter", AsyncMock(side_effect=RuntimeError("denied"))
        ), patch.object(service, "fetch_cloudflare", AsyncMock(return_value=available)):
            result = asyncio.run(service.refresh(force=True))

        self.assertEqual(result["gemini"]["status"], "available")
        self.assertEqual(result["openrouter"]["status"], "error")
        self.assertEqual(result["openrouter"]["error_code"], "provider_request_failed")
        self.assertEqual(result["cloudflare"]["status"], "available")


if __name__ == "__main__":
    unittest.main()