import unittest
from unittest.mock import Mock, patch

from utils.s3 import configure_temporary_lifecycle, delete_object


class S3CleanupTests(unittest.TestCase):
    @patch("utils.s3.env.STORAGE_BUCKET", "test-bucket")
    @patch("utils.s3.get_s3_client")
    def test_delete_object_uses_configured_bucket(self, get_client):
        client = Mock()
        get_client.return_value = client

        delete_object("temporary/task/source.mp4")

        client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="temporary/task/source.mp4"
        )

    @patch("utils.s3.env.STORAGE_BUCKET", "test-bucket")
    @patch("utils.s3.get_s3_client")
    def test_temporary_lifecycle_preserves_existing_rules(self, get_client):
        client = Mock()
        client.get_bucket_lifecycle_configuration.return_value = {
            "Rules": [{"ID": "keep-existing", "Status": "Enabled", "Filter": {"Prefix": "archive/"}}]
        }
        get_client.return_value = client

        configure_temporary_lifecycle()

        rules = client.put_bucket_lifecycle_configuration.call_args.kwargs["LifecycleConfiguration"]["Rules"]
        self.assertEqual(rules[0]["ID"], "keep-existing")
        self.assertEqual(rules[-1]["Expiration"]["Days"], 1)
        self.assertEqual(rules[-1]["Filter"]["Prefix"], "temporary/")


if __name__ == "__main__":
    unittest.main()