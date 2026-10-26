from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.generator import Format, Platform, generate_post

router = APIRouter(prefix="/api/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    platform: Platform
    format: Format
    topic: str = Field(min_length=1)
    tone: str = Field(min_length=1)
    context: str = Field(min_length=1)
    values: str = Field(min_length=1)
    constraints: str = ""


class DownloadPayload(BaseModel):
    filename: str
    mime: str
    base64: str


class GenerateResponse(BaseModel):
    platform: Platform
    format: Format
    username: str
    display_name: str
    age: int | None = None
    caption: str
    media_mime: str | None = None
    media_base64: str | None = None
    download: DownloadPayload


@router.post("", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    try:
        result = await generate_post(
            platform=req.platform,
            fmt=req.format,
            topic=req.topic.strip(),
            tone=req.tone.strip(),
            context=req.context.strip(),
            values=req.values.strip(),
            constraints=req.constraints.strip(),
        )
        return GenerateResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface API failures cleanly
        raise HTTPException(
            status_code=502,
            detail=f"Generation failed: {exc}",
        ) from exc
