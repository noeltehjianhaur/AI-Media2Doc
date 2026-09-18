import threading
from typing import Any, Dict, List

import env


model_request_slot = threading.BoundedSemaphore(max(env.MAX_CONCURRENT_MODEL_REQUESTS, 1))


def get_model_candidates(role: str) -> List[Dict[str, Any]]:
    candidates = []
    if role == "video":
        if env.GEMINI_API_KEY:
            candidates.extend(
                {"provider": "gemini", "name": "Google Gemini", "model": model, "role": role}
                for model in env.GEMINI_VIDEO_MODELS
            )
        return candidates

    gemini_models = env.GEMINI_ASR_MODELS if role == "audio" else env.GEMINI_TEXT_MODELS
    if env.GEMINI_API_KEY and env.GEMINI_BASE_URL:
        candidates.extend(
            {
                "provider": "gemini",
                "name": "Google Gemini",
                "base_url": env.GEMINI_BASE_URL,
                "api_key": env.GEMINI_API_KEY,
                "model": model,
                "role": role,
            }
            for model in gemini_models
        )

    openrouter_models = env.OPENROUTER_ASR_MODELS if role == "audio" else env.OPENROUTER_TEXT_MODELS
    if env.OPENROUTER_API_KEY and env.OPENROUTER_BASE_URL:
        candidates.extend(
            {
                "provider": "openrouter",
                "name": "OpenRouter",
                "base_url": env.OPENROUTER_BASE_URL,
                "api_key": env.OPENROUTER_API_KEY,
                "model": model,
                "role": role,
            }
            for model in openrouter_models
        )
    return candidates


def is_retryable_error(error: Exception) -> bool:
    message = str(error).upper()
    return any(marker in message for marker in ("429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"))


def public_capability_manifest() -> Dict[str, Any]:
    return {
        role: [
            {"provider": item["provider"], "model": item["model"], "role": role}
            for item in get_model_candidates(role)
        ]
        for role in ("audio", "video", "text")
    }