import unittest

from pydantic import ValidationError

from models import FileNameRequest, ProcessingMode, VideoLinkRequest


class ProcessingModeContractTests(unittest.TestCase):
    def test_existing_requests_default_to_audio(self):
        self.assertEqual(FileNameRequest(filename="sample.mp3").processing_mode, ProcessingMode.AUDIO)
        self.assertEqual(VideoLinkRequest(url="https://example.com/video").processing_mode, ProcessingMode.AUDIO)

    def test_audio_video_mode_is_accepted(self):
        request = FileNameRequest(filename="sample.mp4", processing_mode="audio_video")

        self.assertEqual(request.processing_mode, ProcessingMode.AUDIO_VIDEO)

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValidationError):
            FileNameRequest(filename="sample.mp4", processing_mode="frames_only")


if __name__ == "__main__":
    unittest.main()