import asyncio
import unittest
from unittest.mock import patch

from routers.secrets import get_environment_variables


class SecretsEndpointTests(unittest.TestCase):
    def test_provider_credentials_are_masked(self):
        credentials = {
            "OPENROUTER_MANAGEMENT_KEY": "openrouter-secret-value",
            "CLOUDFLARE_ANALYTICS_TOKEN": "cloudflare-secret-value",
            "GOOGLE_CLOUD_ACCESS_TOKEN": "google-secret-value",
            "GITHUB_OUTPUT_TOKEN": "github-secret-value",
        }
        patches = [patch(f"routers.secrets.env.{name}", value) for name, value in credentials.items()]
        for active_patch in patches:
            active_patch.start()
        try:
            response = asyncio.run(get_environment_variables())
        finally:
            for active_patch in reversed(patches):
                active_patch.stop()

        for name, secret in credentials.items():
            self.assertNotEqual(response.data[name], secret)
            self.assertIn("*", response.data[name])


if __name__ == "__main__":
    unittest.main()