import unittest
from unittest.mock import Mock, patch

from services.github_output import publish_bundle


class GitHubOutputTests(unittest.TestCase):
    @patch("services.github_output.env.GITHUB_OUTPUT_ENABLED", True)
    @patch("services.github_output.env.GITHUB_OUTPUT_TOKEN", "secret-token")
    @patch("services.github_output.env.GITHUB_OUTPUT_REPOSITORY", "owner/output")
    @patch("services.github_output.env.GITHUB_OUTPUT_BRANCH", "main")
    @patch("services.github_output.requests.request")
    def test_bundle_is_published_with_one_commit_and_ref_update(self, request):
        payloads = iter(
            [
                {"object": {"sha": "parent"}},
                {"tree": {"sha": "base-tree"}},
                {"sha": "blob-a"},
                {"sha": "blob-b"},
                {"sha": "new-tree"},
                {"sha": "new-commit"},
                {"object": {"sha": "new-commit"}},
            ]
        )

        def response(*_args, **_kwargs):
            result = Mock()
            result.json.return_value = next(payloads)
            return result

        request.side_effect = response
        result = publish_bundle(
            {
                "record.md": "hello",
                "images/frame.jpg": {"content": "aGVsbG8=", "encoding": "base64"},
            },
            "Add record",
        )

        self.assertEqual(result["commit_sha"], "new-commit")
        patch_calls = [call for call in request.call_args_list if call.args[0] == "PATCH"]
        self.assertEqual(len(patch_calls), 1)
        self.assertNotIn("secret-token", str(result))


if __name__ == "__main__":
    unittest.main()