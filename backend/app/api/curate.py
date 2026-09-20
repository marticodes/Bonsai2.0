from fastapi import APIRouter
from pydantic import BaseModel

from app.services.curator import score_post
from app.services.specification import FeedSpecification


router = APIRouter(
    prefix="/api/curate",
    tags=["curation"],
)


class ScoreRequest(BaseModel):
    post: str
    specification: FeedSpecification


class ScoreResponse(BaseModel):
    score: float
    reason: str


@router.post(
    "/score",
    response_model=ScoreResponse,
)
async def score_post_endpoint(
    request: ScoreRequest,
):

    result = await score_post(
        post=request.post,
        specification=request.specification,
    )

    return result

