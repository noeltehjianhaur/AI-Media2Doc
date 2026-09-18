# -*- coding: UTF-8 -*-

from fastapi import APIRouter
from openai import APIError, OpenAI
import time

import env
from core.response import success_response, APIResponse
from models import ChatRequest, TranslationRequest
from services.model_routing import get_model_candidates, is_retryable_error, model_request_slot
from core.exceptions import ExternalServiceException

router = APIRouter(prefix="/llm", tags=["LLM"])


def create_completion(messages, timeout, max_tokens=None):
    """Try configured providers in order: Gemini, then OpenRouter."""
    providers = [
        (item["name"], item["base_url"], item["api_key"], item["model"])
        for item in get_model_candidates("text")
    ]

    last_error = None
    for provider_name, base_url, api_key, model_id in providers:
        for attempt in range(2):
            try:
                request_options = {
                    "model": model_id,
                    "messages": messages,
                    "timeout": timeout,
                }
                if max_tokens is not None:
                    request_options["max_tokens"] = max_tokens

                with model_request_slot:
                    return OpenAI(base_url=base_url, api_key=api_key).chat.completions.create(
                        **request_options
                    )
            except Exception as error:
                last_error = error
                if is_retryable_error(error) and attempt == 0:
                    time.sleep(5)
                    continue
                break

    raise ExternalServiceException("LLM", f"All configured text models failed: {last_error}")


def completion_data(response):
    usage = response.usage.model_dump(exclude_none=True) if response.usage else None
    return {
        "choices": [choice.model_dump() for choice in response.choices],
        "model": response.model,
        "usage": usage,
    }


@router.post("/completions", response_model=APIResponse)
async def default_chat(request: ChatRequest):
    """默认聊天接口"""
    messages = [
        {"role": message.role, "content": message.content}
        for message in request.messages
    ]

    response = create_completion(messages, timeout=120)
    return success_response(
        data=completion_data(response),
        message="Chat completed successfully",
    )


@router.post("/markdown-generation", response_model=APIResponse)
async def generate_markdown_text(request: ChatRequest):
    """生成 Markdown 文本"""
    messages = [
        {"role": message.role, "content": message.content}
        for message in request.messages
    ]

    if request.target_language:
        messages.append(
            {
                "role": "system",
                "content": (
                    f"Write the entire response in {request.target_language}. "
                    "Keep the same Markdown structure, headings, timestamps and "
                    "screenshot markers."
                ),
            }
        )

    response = create_completion(
        messages,
        timeout=request.timeout,
        max_tokens=request.max_tokens,
    )

    return success_response(
        data=completion_data(response),
        message="Chat completed successfully",
    )


@router.post("/translation", response_model=APIResponse)
async def translate_text(request: TranslationRequest):
    """将转写文本翻译为目标语言"""
    messages = [
        {
            "role": "system",
            "content": (
                f"Translate the user's transcript into {request.target_language}. "
                "Preserve line breaks and ordering. Return only the translated text "
                "without commentary."
            ),
        },
        {"role": "user", "content": request.text},
    ]

    response = create_completion(
        messages,
        timeout=request.timeout,
        max_tokens=request.max_tokens,
    )

    return success_response(
        data={
            "text": response.choices[0].message.content or "",
            "model": response.model,
            "usage": response.usage.model_dump(exclude_none=True) if response.usage else None,
        },
        message="Translation completed successfully",
    )
