import unittest
from unittest.mock import patch

from services.model_routing import get_model_candidates, is_retryable_error


class ModelRoutingTests(unittest.TestCase):
    @patch("services.model_routing.env.GEMINI_VIDEO_MODELS", ["video-a", "video-b"])
    @patch("services.model_routing.env.GEMINI_API_KEY", "key")
    def test_video_candidates_are_limited_to_configured_gemini_allowlist(self):
        candidates = get_model_candidates("video")

        self.assertEqual([candidate["model"] for candidate in candidates], ["video-a", "video-b"])
        self.assertTrue(all(candidate["provider"] == "gemini" for candidate in candidates))

    def test_only_capacity_errors_are_retryable(self):
        self.assertTrue(is_retryable_error(RuntimeError("429 RESOURCE_EXHAUSTED")))
        self.assertTrue(is_retryable_error(RuntimeError("503 UNAVAILABLE")))
        self.assertFalse(is_retryable_error(RuntimeError("401 invalid API key")))


if __name__ == "__main__":
    unittest.main()