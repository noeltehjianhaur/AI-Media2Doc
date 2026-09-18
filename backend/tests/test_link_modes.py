import unittest
from unittest.mock import patch

from models import ProcessingMode
from routers import audio, link


class LinkModeTests(unittest.TestCase):
    def setUp(self):
        audio.ASR_TASKS.clear()

    def test_youtube_video_mode_uses_direct_url(self):
        url = "https://www.youtube.com/watch?v=abc123"
        task_id = audio.create_transcription_record(
            "",
            processing_mode=ProcessingMode.AUDIO_VIDEO,
            source_type="link",
            source_url=url,
        )

        with patch("routers.link.download_media") as download, patch(
            "routers.link.run_transcription_task"
        ) as run:
            link.run_link_transcription_task(task_id, url)

        download.assert_not_called()
        run.assert_called_once_with(task_id, None)

    def test_audio_mode_requests_mp3(self):
        with patch("routers.link._download_with_ytdlp", return_value=b"audio") as download:
            data, extension, content_type = link.download_media(
                "https://example.com/video", ProcessingMode.AUDIO
            )

        self.assertEqual(data, b"audio")
        self.assertEqual((extension, content_type), ("mp3", "audio/mpeg"))
        self.assertEqual(download.call_args.args[1], ProcessingMode.AUDIO)


if __name__ == "__main__":
    unittest.main()