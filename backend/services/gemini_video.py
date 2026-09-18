import json
import mimetypes
import os
import tempfile
import time
from typing import Any, Dict, Optional, Tuple

import requests

import env
from core.exceptions import ExternalServiceException
from services.model_routing import get_model_candidates, is_retryable_error, model_request_slot
from utils.s3 import generate_download_url


VISUAL_TRANSCRIPT_PROMPT = """
Analyze the complete video, including speech and visible content. Return JSON only:
{
  "detected_language": "language code",
  "summary": "short factual summary",
  "segments": [{
    "start_seconds": 0,
    "end_seconds": 0,
    "spoken_text": "",
    "on_screen_text": "",
    "visual_actions": [""],
    "important": false
  }],
  "flowchart": [{"source": "", "target": "", "label": ""}]
}
Use timestamps from the video. Never emit HTML or JavaScript. Include only observed facts.
""".strip()


def _strip_code_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_visual_response(value: str) -> Dict[str, Any]:
    """Validate and normalize model JSON into the application's safe data shape."""
    try:
        raw = json.loads(_strip_code_fence(value))
    except (TypeError, json.JSONDecodeError) as error:
        raise ExternalServiceException("Gemini video", "Invalid structured response") from error

    segments = []
    for item in raw.get("segments", []):
        if not isinstance(item, dict):
            continue
        start = max(float(item.get("start_seconds", 0) or 0), 0)
        end = max(float(item.get("end_seconds", start) or start), start)
        segments.append(
            {
                "start_time": int(start * 1000),
                "end_time": int(end * 1000),
                "text": str(item.get("spoken_text", "")).strip(),
                "on_screen_text": str(item.get("on_screen_text", "")).strip(),
                "visual_actions": [
                    str(action) for action in item.get("visual_actions", []) if action
                ],
                "important": bool(item.get("important", False)),
            }
        )

    flowchart = []
    for edge in raw.get("flowchart", []):
        if isinstance(edge, dict) and edge.get("source") and edge.get("target"):
            flowchart.append(
                {
                    "source": str(edge["source"]),
                    "target": str(edge["target"]),
                    "label": str(edge.get("label", "")),
                }
            )
    return {
        "detected_language": str(raw.get("detected_language", "unknown")),
        "summary": str(raw.get("summary", "")).strip(),
        "segments": segments,
        "flowchart": flowchart,
    }


def _usage_metadata(response) -> Dict[str, Any]:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump(exclude_none=True)
    return {
        key: value
        for key, value in vars(usage).items()
        if not key.startswith("_") and value is not None
    }


def analyze_video(
    filename: Optional[str] = None, source_url: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Analyze an uploaded video or supported public URL with the native Gemini API."""
    candidates = get_model_candidates("video")
    if not candidates:
        raise ExternalServiceException("Gemini video", "Gemini credentials are not configured")

    try:
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise ExternalServiceException("Gemini video", "google-genai is not installed") from error

    client = genai.Client(api_key=env.GEMINI_API_KEY)
    uploaded_file = None
    temporary_path = None
    try:
        if source_url:
            media_part = types.Part(
                file_data=types.FileData(file_uri=source_url, mime_type="video/mp4")
            )
        elif filename:
            suffix = os.path.splitext(filename)[1] or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
                temporary_path = handle.name
                downloaded = 0
                maximum = env.MAX_VIDEO_SIZE_MB * 1024 * 1024
                with requests.get(generate_download_url(filename), timeout=180, stream=True) as response:
                    response.raise_for_status()
                    content_length = int(response.headers.get("content-length", 0) or 0)
                    if content_length > maximum:
                        raise ExternalServiceException(
                            "Gemini video", f"Video exceeds the {env.MAX_VIDEO_SIZE_MB} MB limit"
                        )
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        downloaded += len(chunk)
                        if downloaded > maximum:
                            raise ExternalServiceException(
                                "Gemini video", f"Video exceeds the {env.MAX_VIDEO_SIZE_MB} MB limit"
                            )
                        handle.write(chunk)
            uploaded_file = client.files.upload(
                file=temporary_path,
                config={"mime_type": mimetypes.guess_type(filename)[0] or "video/mp4"},
            )
            deadline = time.monotonic() + 180
            while getattr(uploaded_file, "state", None) and str(uploaded_file.state).endswith("PROCESSING"):
                if time.monotonic() >= deadline:
                    raise ExternalServiceException("Gemini video", "Video processing timed out")
                time.sleep(2)
                uploaded_file = client.files.get(name=uploaded_file.name)
            if str(getattr(uploaded_file, "state", "")).endswith("FAILED"):
                raise ExternalServiceException("Gemini video", "Gemini rejected the video file")
            media_part = uploaded_file
        else:
            raise ExternalServiceException("Gemini video", "No video source was provided")

        last_error = None
        for candidate in candidates:
            for attempt in range(2):
                try:
                    with model_request_slot:
                        response = client.models.generate_content(
                            model=candidate["model"],
                            contents=[media_part, VISUAL_TRANSCRIPT_PROMPT],
                            config=types.GenerateContentConfig(response_mime_type="application/json"),
                        )
                    result = parse_visual_response(response.text or "")
                    usage = {
                        "provider": "gemini",
                        "model": candidate["model"],
                        **_usage_metadata(response),
                    }
                    return result, usage
                except Exception as error:
                    last_error = error
                    if not is_retryable_error(error) or attempt == 1:
                        break
                    time.sleep(5 * (attempt + 1))
        raise ExternalServiceException("Gemini video", f"All configured video models failed: {last_error}")
    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)