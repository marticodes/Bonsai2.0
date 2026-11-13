from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.services.generator import Format, Platform, generate_post

router = APIRouter(prefix="/api/generate", tags=["generate"])

_MAX_IMAGES = 4
_MAX_IMAGE_CHARS = 8_000_000


class GenerateRequest(BaseModel):
    platform: Platform
    format: Format
    topic: str = ""
    tone: str = ""
    context: str = ""
    values: str = ""
    constraints: str = ""
    reference_images: list[str] = Field(default_factory=list, max_length=_MAX_IMAGES)

    @model_validator(mode="after")
    def require_brief_or_screenshots(self):
        filled = all(
            field.strip()
            for field in (self.topic, self.tone, self.context, self.values)
        )
        if not filled and not self.reference_images:
            raise ValueError(
                "Add a screenshot, or fill in topic, tone, context, and values."
            )
        for image in self.reference_images:
            if not image.startswith("data:image/"):
                raise ValueError("Screenshots must be image files.")
            if len(image) > _MAX_IMAGE_CHARS:
                raise ValueError("A screenshot is too large. Try a smaller image.")
        return self


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
            reference_images=req.reference_images,
        )
        return GenerateResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface API failures cleanly
        raise HTTPException(
            status_code=502,
            detail=f"Generation failed: {exc}",
        ) from exc
