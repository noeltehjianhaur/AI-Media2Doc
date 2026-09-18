# -*- coding: UTF-8 -*-
import os
import glob
import tempfile
from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, BackgroundTasks

from models import ProcessingMode, VideoLinkRequest
from core.exceptions import BusinessException, ExternalServiceException
from core.response import success_response, APIResponse
from config.log import get_logger
import env
from routers.audio import ASR_TASKS, create_transcription_record, run_transcription_task
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


def is_youtube_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().split(":")[0]
    return host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def _download_with_ytdlp(url: str, processing_mode: ProcessingMode) -> bytes:
    """Download audio or merged video bytes with yt-dlp."""
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
        stem = "audio" if processing_mode == ProcessingMode.AUDIO else "video"
        outtmpl = os.path.join(workdir, f"{stem}.%(ext)s")
        options = {
            "format": "bestaudio/best"
            if processing_mode == ProcessingMode.AUDIO
            else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
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
            ] if processing_mode == ProcessingMode.AUDIO else [],
            "merge_output_format": "mp4",
            "max_filesize": env.MAX_VIDEO_SIZE_MB * 1024 * 1024,
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([normalized_url])
        except Exception as error:
            raise ExternalServiceException(
                "Link download",
                f"Unable to download media from this link: {error}",
            )

        candidates = glob.glob(os.path.join(workdir, f"{stem}.*"))
        media_path = next((path for path in candidates if not path.endswith((".part", ".ytdl"))), None)
        if not media_path:
            raise ExternalServiceException(
                "Link download", "No compatible media could be extracted from this link"
            )

        with open(media_path, "rb") as handle:
            return handle.read()


def download_media(url: str, processing_mode: ProcessingMode):
    data = _download_with_ytdlp(url, processing_mode)
    if processing_mode == ProcessingMode.AUDIO:
        return data, "mp3", "audio/mpeg"
    return data, "mp4", "video/mp4"


def run_link_transcription_task(task_id: str, url: str):
    """Acquire remote media in the background, then use the shared transcription worker."""
    task = ASR_TASKS[task_id]
    try:
        mode = ProcessingMode(task["processing_mode"])
        if mode == ProcessingMode.AUDIO_VIDEO and is_youtube_url(url):
            run_transcription_task(task_id, None)
            return

        media, extension, content_type = download_media(url, mode)
        filename = f"temporary/{task_id}/source.{extension}"
        upload_bytes(filename, media, content_type)
        task["filename"] = filename
        run_transcription_task(task_id, filename)
    except Exception as error:
        logger.error(f"Link transcription task {task_id} failed: {error}")
        task["status"] = "failed"
        task["error"] = str(error)


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
        task_id = create_transcription_record(
            "",
            processing_mode=request.processing_mode,
            source_type="link",
            original_name=url,
            source_url=url,
            keep_source_media=request.keep_source_media,
        )
        background_tasks.add_task(run_link_transcription_task, task_id, url)

        return success_response(
            data={"task_id": task_id, "filename": None},
            message="Link transcription task created successfully",
        )
    except (BusinessException, ExternalServiceException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error when transcribing link {url}: {str(e)}")
        raise BusinessException(f"Failed to transcribe link: {str(e)}")
