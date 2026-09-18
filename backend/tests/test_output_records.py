import unittest

from services.output_records import build_output_bundle, sanitize_title


class OutputRecordTests(unittest.TestCase):
    def test_title_is_sanitized_and_bounded(self):
        stem = sanitize_title("Building: HTML Artifacts / with Local Agents!!!")

        self.assertEqual(stem, "building-html-artifacts-with-local-agents")
        self.assertLessEqual(len(stem), 90)

    def test_uploaded_audio_record_omits_source_url(self):
        bundle = build_output_bundle(
            title="Demo Record",
            processing_mode="audio",
            transcript="Hello",
            generated_content="# Summary\nDone",
            metadata={"original_name": "demo.mp3", "source_type": "upload"},
        )

        content = next(iter(bundle["files"].values()))
        self.assertNotIn("Source URL", content)
        self.assertIn("Original file: demo.mp3", content)

    def test_link_record_includes_source_url_and_html_is_escaped(self):
        bundle = build_output_bundle(
            title="Visual Demo",
            processing_mode="audio_video",
            transcript="Hello",
            generated_content="<script>alert(1)</script>",
            metadata={"source_type": "link", "source_url": "https://example.com/video"},
            visual_analysis={"segments": [], "flowchart": []},
        )

        html = bundle["files"][bundle["output_path"]]
        self.assertIn("Source URL", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_visual_record_packages_selected_screenshots(self):
        bundle = build_output_bundle(
            title="Visual Demo",
            processing_mode="audio_video",
            transcript="Hello",
            generated_content="Summary",
            metadata={"source_type": "upload", "original_name": "demo.mp4"},
            visual_analysis={"segments": [], "flowchart": []},
            screenshots=[{"timestamp": 12, "data_url": "data:image/jpeg;base64,aGVsbG8="}],
        )

        image_path = next(path for path in bundle["files"] if "/images/" in path)
        self.assertTrue(image_path.endswith("frame-001.jpg"))
        self.assertIn("images/frame-001.jpg", bundle["files"][bundle["output_path"]])
        self.assertEqual(bundle["files"][image_path]["encoding"], "base64")


if __name__ == "__main__":
    unittest.main()