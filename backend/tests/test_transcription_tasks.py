import unittest
from unittest.mock import patch

from models import ProcessingMode
from routers import audio


class TranscriptionTaskTests(unittest.TestCase):
    def setUp(self):
        audio.ASR_TASKS.clear()

    def test_task_record_preserves_mode_and_source_metadata(self):
        task_id = audio.create_transcription_record(
            "temporary/task/source.mp4",
            processing_mode=ProcessingMode.AUDIO_VIDEO,
            source_type="upload",
            original_name="Demo.mp4",
        )

        task = audio.ASR_TASKS[task_id]
        self.assertEqual(task["status"], "queued")
        self.assertEqual(task["processing_mode"], "audio_video")
        self.assertEqual(task["source_type"], "upload")
        self.assertEqual(task["original_name"], "Demo.mp4")

    @patch("routers.audio.delete_object")
    @patch("routers.audio.transcribe_audio")
    def test_completed_audio_task_deletes_temporary_source(self, transcribe, delete):
        transcribe.return_value = ("hello", {"provider": "gemini"})
        key = "temporary/task/source.mp3"
        task_id = audio.create_transcription_record(key)

        audio.run_transcription_task(task_id, key)

        self.assertEqual(audio.ASR_TASKS[task_id]["status"], "completed")
        self.assertEqual(audio.ASR_TASKS[task_id]["usage"]["provider"], "gemini")
        delete.assert_called_once_with(key)

    def test_failed_task_response_includes_the_provider_error(self):
        task_id = audio.create_transcription_record("temporary/task/source.mp3")
        audio.ASR_TASKS[task_id]["status"] = "failed"
        audio.ASR_TASKS[task_id]["error"] = "ASR: No spoken text was detected"

        response = __import__("asyncio").run(audio.get_transcription_task(task_id))

        self.assertEqual(response.data["error"], "ASR: No spoken text was detected")


if __name__ == "__main__":
    unittest.main()