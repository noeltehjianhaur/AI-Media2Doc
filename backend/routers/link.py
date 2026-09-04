# -*- coding: UTF-8 -*-
import os
import tempfile
import uuid
from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, BackgroundTasks

from models import VideoLinkRequest
from core.exceptions import BusinessException, ExternalServiceException
from core.response import success_response, APIResponse
from config.log import get_logger
from routers.audio import create_transcription_record, run_transcription_task
from utils.s3 import upload_bytes

router = APIRouter(prefix="/link", tags=["Link"])
logger = get_logger(__name__)


def normalize_video_url(url: str) -> str:
    """Map Rednote's public domain to yt-dlp's XiaoHongShu extractor domain."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]
    if host in {"rednote.com", "www.rednote.com"} and parsed.path.startswith(
        "/discovery/item/"
    ):
        return urlunparse(
            parsed._replace(scheme="https", netloc="www.xiaohongshu.com")
        )
    return url


def download_audio(url: str) -> bytes:
    """Extract the audio track of a remote video link as MP3 bytes."""
    try:
        import yt_dlp
    except ImportError:
        raise ExternalServiceException(
            "Link download", "yt-dlp is not installed on the backend"
        )

    normalized_url = normalize_video_url(url)
    if normalized_url != url:
        logger.info("Normalized Rednote URL for XiaoHongShu extraction")

    with tempfile.TemporaryDirectory() as workdir:
        outtmpl = os.path.join(workdir, "audio.%(ext)s")
        options = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": True,
            "noplaylist": True,
            # YouTube's default web client frequently breaks (signature/SABR
            # changes); android/tv clients are more stable for audio-only pulls.
            "extractor_args": {
                "youtube": {"player_client": ["android", "tv", "web"]}
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }
            ],
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([normalized_url])
        except Exception as error:
            raise ExternalServiceException(
                "Link download",
                f"Unable to download media from this link: {error}",
            )

        mp3_path = os.path.join(workdir, "audio.mp3")
        if not os.path.exists(mp3_path):
            raise ExternalServiceException(
                "Link download", "No audio track could be extracted from this link"
            )

        with open(mp3_path, "rb") as handle:
            return handle.read()


@router.post("/transcription-tasks", response_model=APIResponse)
async def create_link_transcription_task(
    request: VideoLinkRequest, background_tasks: BackgroundTasks
):
    """通过视频链接创建转写任务

    RESTful路径: POST /api/v1/link/transcription-tasks
    """
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        raise BusinessException("Only http(s) links are supported")

    logger.info(f"Creating link transcription task for: {url}")

    try:
        audio_bytes = download_audio(url)
        filename = f"link-{uuid.uuid4()}.mp3"
        upload_bytes(filename, audio_bytes, "audio/mpeg")

        task_id = create_transcription_record(filename)
        background_tasks.add_task(run_transcription_task, task_id, filename)

        return success_response(
            data={"task_id": task_id, "filename": filename},
            message="Link transcription task created successfully",
        )
    except (BusinessException, ExternalServiceException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error when transcribing link {url}: {str(e)}")
        raise BusinessException(f"Failed to transcribe link: {str(e)}")
