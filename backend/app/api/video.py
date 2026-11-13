import os
import tempfile

from pydantic import BaseModel, Field

from app.services.screenshot_analyzer import analyze_screenshot
from app.services.screenshot_cluster import cluster_screenshots
from app.services.theme_classifier import classify_themes, load_classification

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.video_processor import extract_frames

router = APIRouter(prefix="/api/video", tags=["Video"])

MAX_VIDEO_SIZE = 1000 * 1024 * 1024  # 100 MB


@router.post("/extract-frames")
async def upload_video(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided",
        )

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format",
        )

    temp_path = None

    try:
        # Save the upload temporarily, with a size limit.
        size = 0

        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                size += len(chunk)

                if size > MAX_VIDEO_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Video exceeds the 1000 MB limit",
                    )

                temp_file.write(chunk)

        if size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded video is empty",
            )

        result = extract_frames(
            video_path=temp_path,
            interval_seconds=5,
        )

        # One skipped 5s frame can still belong to the same post.
        # A larger jump starts a new cluster even when the text is similar.
        max_gap_seconds = float(result["interval_seconds"]) * 2 + 2

        try:
            result["clusters"] = cluster_screenshots(
                result["frames"],
                max_gap_seconds=max_gap_seconds,
            )
        except Exception as error:
            print(f"Screenshot clustering failed: {error}")
            result["clusters"] = []
            result["clustering_error"] = (
                "Screenshots were extracted, but OCR clustering failed: "
                f"{error}"
            )

        return result

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Video processing failed",
        ) from error

    finally:
        await file.close()

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

class ThemeScreenshot(BaseModel):
    ocr_text: str = ""
    normalized_text: str = ""


class ThemePost(BaseModel):
    cluster_id: int
    ocr_text: str = ""
    normalized_text: str = ""
    screenshots: list[ThemeScreenshot] = Field(default_factory=list)


class ThemeClassificationRequest(BaseModel):
    posts: list[ThemePost] = Field(min_length=1, max_length=500)


@router.post("/classify-themes")
def classify_post_themes(request: ThemeClassificationRequest):
    """Classify each unique OCR-clustered post. Does not read screenshots."""
    try:
        return classify_themes(
            [post.model_dump() for post in request.posts]
        )
    except Exception as error:
        print(f"Theme classification failed: {error}")
        raise HTTPException(
            status_code=500,
            detail="Theme classification failed. Check the backend terminal.",
        ) from error


@router.get("/themes")
def get_stored_themes():
    return load_classification()


class ScreenshotAnalysisRequest(BaseModel):
    image: str = Field(min_length=1, max_length=15_000_000)


@router.post("/analyze-screenshot")
def analyze_uploaded_screenshot(
    request: ScreenshotAnalysisRequest,
):
    try:
        analysis = analyze_screenshot(request.image)

        return {
            "analysis": analysis,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        # Log the actual exception in the backend terminal.
        print(f"Screenshot analysis failed: {error}")

        raise HTTPException(
            status_code=500,
            detail="Screenshot analysis failed. Check the backend terminal.",
        ) from error