from fastapi import APIRouter
from pydantic import BaseModel

from app.services.bluesky import get_feed
from app.services.curator import score_post
from app.services.specification import FeedSpecification


router = APIRouter(
    prefix="/api/feed",
    tags=["feed"],
)


DEFAULT_FEED_URI = (
    "at://did:plc:z72i7hdynmk6r22z27h6tvur/"
    "app.bsky.feed.generator/hot-classic"
)


class FeedRequest(BaseModel):
    specification: FeedSpecification
    feed_uri: str = DEFAULT_FEED_URI
    limit: int = 30


@router.post("/generate")
async def generate_feed(request: FeedRequest):

    posts = await get_feed(
        feed_uri=request.feed_uri,
        limit=request.limit,
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