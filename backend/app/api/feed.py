from fastapi import APIRouter
from pydantic import BaseModel

from app.services.bluesky import get_timeline
from app.services.curator import score_post
from app.services.specification import FeedSpecification


router = APIRouter(
    prefix="/api/feed",
    tags=["feed"],
)


class FeedRequest(BaseModel):
    specification: FeedSpecification
    limit: int = 10


@router.post("/generate")
async def generate_feed(request: FeedRequest):

    posts = await get_timeline(
        limit=request.limit
    )

    scored_posts = []

    for post in posts:

        result = await score_post(
            post=post["text"],
            specification=request.specification,
        )

        scored_posts.append(
            {
                **post,
                "score": result["score"],
                "reason": result["reason"],
            }
        )

    scored_posts.sort(
        key=lambda post: post["score"],
        reverse=True,
    )

    return {
        "posts": scored_posts
    }