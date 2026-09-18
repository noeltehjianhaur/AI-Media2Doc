import time

from fastapi import APIRouter

from core.exceptions import BusinessException
from core.response import APIResponse, success_response
from services.provider_usage import provider_usage_service
from services.model_routing import public_capability_manifest

router = APIRouter(prefix="/provider-usage", tags=["Provider usage"])
_last_manual_refresh = 0.0
_manual_refresh_interval = 10


@router.get("", response_model=APIResponse)
async def get_provider_usage():
    data = await provider_usage_service.refresh(force=False)
    return success_response(data=data, message="Provider usage retrieved")


@router.post("/refresh", response_model=APIResponse)
async def refresh_provider_usage():
    global _last_manual_refresh
    now = time.monotonic()
    if now - _last_manual_refresh < _manual_refresh_interval:
        raise BusinessException("Provider usage refresh is rate-limited; retry shortly")
    _last_manual_refresh = now
    data = await provider_usage_service.refresh(force=True)
    return success_response(data=data, message="Provider usage refreshed")


@router.get("/models", response_model=APIResponse)
async def get_model_capabilities():
    return success_response(
        data=public_capability_manifest(),
        message="Configured model capabilities retrieved",
    )