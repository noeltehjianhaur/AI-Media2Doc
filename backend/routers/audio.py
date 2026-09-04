# -*- coding: UTF-8 -*-
from fastapi import APIRouter, BackgroundTasks
import base64
import time
import uuid
import requests
from openai import OpenAI

from constants import AsrTaskStatus
from models import FileNameRequest
from core.exceptions import BusinessException, ExternalServiceException
from core.response import success_response, APIResponse
from config.log import get_logger
import env
from utils.s3 import generate_download_url

router = APIRouter(prefix="/audio", tags=["Audio"])
logger = get_logger(__name__)
ASR_TASKS = {}

# Language auto-detection is delegated to the model; the transcript keeps the spoken language.
TRANSCRIPTION_PROMPT = (
    "Transcribe this audio accurately. Return only the spoken text."
)


def get_asr_providers():
    """Ordered ASR providers: Gemini first, OpenRouter as fallback."""
    providers = []
    if all([env.GEMINI_BASE_URL, env.GEMINI_API_KEY, env.GEMINI_MODEL_ID]):
        providers.append(
            (
                "Google Gemini",
                env.GEMINI_BASE_URL,
                env.GEMINI_API_KEY,
                env.GEMINI_MODEL_ID,
            )
        )
    if all(
        [
            env.OPENROUTER_BASE_URL,
            env.OPENROUTER_API_KEY,
            env.OPENROUTER_ASR_MODEL_ID,
        ]
    ):
        providers.append(
            (
                "OpenRouter",
                env.OPENROUTER_BASE_URL,
                env.OPENROUTER_API_KEY,
                env.OPENROUTER_ASR_MODEL_ID,
            )
        )
    return providers


def transcribe_audio(filename):
    """Download the uploaded MP3 from object storage and transcribe it via the LLM providers."""
    providers = get_asr_providers()
    if not providers:
        raise ExternalServiceException(
            "ASR",
            "Configure GEMINI_API_KEY/GEMINI_MODEL_ID or OPENROUTER_API_KEY/OPENROUTER_MODEL_ID",
        )

    download_url = generate_download_url(filename)
    audio_response = requests.get(download_url, timeout=120)
    audio_response.raise_for_status()
    audio_data = base64.b64encode(audio_response.content).decode("ascii")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": TRANSCRIPTION_PROMPT},
                {
                    "type": "input_audio",
                    "input_audio": {"data": audio_data, "format": "mp3"},
                },
            ],
        }
    ]

    last_error = None
    for provider_name, base_url, api_key, model_id in providers:
        for attempt in range(3):
            try:
                response = OpenAI(
                    base_url=base_url,
                    api_key=api_key,
                    max_retries=0,
                ).chat.completions.create(
                    model=model_id, messages=messages, timeout=90
                )
                text = (response.choices[0].message.content or "").strip()
                if not text:
                    raise ExternalServiceException(
                        "ASR",
                        "No spoken text was detected in the extracted audio",
                    )
                return text
            except Exception as error:
                last_error = error
                is_transient = "503" in str(error) or "UNAVAILABLE" in str(error)
                if not is_transient or attempt == 2:
                    logger.warning(f"{provider_name} transcription failed: {error}")
                    break

                retry_delay = 10 * (attempt + 1)
                logger.warning(
                    f"{provider_name} is temporarily unavailable; retrying in "
                    f"{retry_delay} seconds (attempt {attempt + 2}/3)"
                )
                time.sleep(retry_delay)

    raise ExternalServiceException("ASR", f"All providers failed: {last_error}")


def create_transcription_record(filename):
    task_id = f"asr-{uuid.uuid4()}"
    ASR_TASKS[task_id] = {
        "status": AsrTaskStatus.RUNNING.value,
        "text": None,
        "error": None,
    }
    return task_id


def run_transcription_task(task_id, filename):
    """Run provider calls after task creation so the client can poll safely."""
    try:
        ASR_TASKS[task_id]["text"] = transcribe_audio(filename)
        ASR_TASKS[task_id]["status"] = AsrTaskStatus.FINISHED.value
        logger.info(f"Transcription task {task_id} completed successfully")
    except Exception as error:
        logger.error(f"Transcription task {task_id} failed: {error}")
        ASR_TASKS[task_id]["status"] = AsrTaskStatus.FAILED.value
        ASR_TASKS[task_id]["error"] = str(error)


@router.post("/transcription-tasks", response_model=APIResponse)
async def create_transcription_task(
    request: FileNameRequest, background_tasks: BackgroundTasks
):
    """创建音频转写任务

    RESTful路径: POST /api/v1/audio/transcription-tasks
    """
    logger.info(f"Creating transcription task for file: {request.filename}")

    try:
        task_id = create_transcription_record(request.filename)
        background_tasks.add_task(run_transcription_task, task_id, request.filename)

        logger.info(f"Transcription task created successfully with ID: {task_id}")

        return success_response(
            data={"task_id": task_id}, message="Transcription task created successfully"
        )

    except ExternalServiceException:
        raise
    except requests.RequestException as e:
        logger.error(f"Request failed when creating transcription task: {str(e)}")
        raise ExternalServiceException("ASR", f"Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error when creating transcription task: {str(e)}")
        raise BusinessException(f"Failed to create transcription task: {str(e)}")


@router.get("/transcription-tasks/{task_id}", response_model=APIResponse)
async def get_transcription_task(task_id: str):
    """获取音频转写任务状态

    RESTful路径: GET /api/v1/audio/transcription-tasks/{task_id}
    """
    logger.info(f"Querying transcription task status: {task_id}")

    try:
        if task_id not in ASR_TASKS:
            logger.error(f"Transcription task {task_id} not found")
            return success_response(
                data={"status": AsrTaskStatus.FAILED.value, "result": None},
                message="Transcription task not found",
            )

        task = ASR_TASKS[task_id]
        if task["status"] == AsrTaskStatus.RUNNING.value:
            return success_response(
                data={"status": AsrTaskStatus.RUNNING.value, "result": None},
                message="Transcription in progress",
            )

        if task["status"] == AsrTaskStatus.FAILED.value:
            return success_response(
                data={"status": AsrTaskStatus.FAILED.value, "result": None},
                message=task["error"] or "Transcription failed",
            )

        return success_response(
            data={
                "status": AsrTaskStatus.FINISHED.value,
                "result": [
                    {"start_time": 0, "end_time": 0, "text": task["text"]}
                ],
            },
            message="Transcription completed",
        )

    except Exception as e:
        logger.error(
            f"Unexpected error when querying transcription task {task_id}: {str(e)}"
        )
        raise BusinessException(f"Failed to query transcription task: {str(e)}")
