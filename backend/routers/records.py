from fastapi import APIRouter

from core.response import APIResponse, success_response
from models import OutputRecordRequest, PublishOutputRequest
from routers.llm import create_completion
from services.github_output import publish_bundle
from services.output_records import build_output_bundle

router = APIRouter(prefix="/records", tags=["Output records"])


def _generate_title(request: OutputRecordRequest) -> str:
    if request.title:
        return request.title
    prompt = (
        "Return only a concise 6-12 word title for this transcript. "
        "Do not use quotes or punctuation.\n\n"
        f"{str(request.transcript)[:8000]}"
    )
    try:
        response = create_completion([{"role": "user", "content": prompt}], timeout=60, max_tokens=40)
        title = (response.choices[0].message.content or "").strip().strip('"')
        if title:
            return title
    except Exception:
        pass
    words = request.generated_content.replace("#", " ").split()
    return " ".join(words[:10]) or "Untitled Record"


@router.post("", response_model=APIResponse)
async def create_output_record(request: OutputRecordRequest):
    title = _generate_title(request)
    bundle = build_output_bundle(
        title=title,
        processing_mode=request.processing_mode,
        transcript=request.transcript,
        generated_content=request.generated_content,
        metadata=request.metadata,
        visual_analysis=request.visual_analysis,
        screenshots=request.screenshots,
    )
    publication = None
    if request.publish:
        try:
            publication = {
                "status": "published",
                **publish_bundle(bundle["files"], f"Add transcript record: {title}"),
            }
        except Exception:
            publication = {
                "status": "failed",
                "error_code": "github_publication_failed",
            }
    return success_response(
        data={
            "title": bundle["title"],
            "output_path": bundle["output_path"],
            "files": bundle["files"],
            "manifest": bundle["manifest"],
            "publication": publication,
        },
        message="Output record created",
    )


@router.post("/publish", response_model=APIResponse)
async def retry_output_publication(request: PublishOutputRequest):
    publication = publish_bundle(request.files, f"Add transcript record: {request.title}")
    return success_response(
        data={"status": "published", **publication},
        message="Output record published",
    )