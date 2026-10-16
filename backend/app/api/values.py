from fastapi import APIRouter
from pydantic import BaseModel

from app.services.bluesky import get_feed
from app.services.value_classifier import classify_post, classify_posts


router = APIRouter(
    prefix="/api/values",
    tags=["values"],
)


DEFAULT_FEED_URI = (
    "at://did:plc:z72i7hdynmk6r22z27h6tvur/"
    "app.bsky.feed.generator/hot-classic"
)


class ValuesFeedRequest(BaseModel):
    feed_uri: str = DEFAULT_FEED_URI
    limit: int = 20


class ClassifyRequest(BaseModel):
    text: str


@router.post("/feed")
async def values_feed(request: ValuesFeedRequest):
    """
    Bluesky posts → value classifier → 19-d vectors.
    Reuses the existing Bluesky fetch service.
    """
    posts = await get_feed(
        feed_uri=request.feed_uri,
        limit=request.limit,
    )

    vectors = await classify_posts(
        [post["text"] for post in posts]
    )

    enriched = []
    for post, values in zip(posts, vectors):
        enriched.append(
            {
                **post,
                "values": values,
            }
        )

    return {
        "posts": enriched
    }


@router.post("/classify")
async def classify_one(request: ClassifyRequest):
    """Classify a single post text (useful for re-scoring / debugging)."""
    values = await classify_post(request.text)
    return {
        "values": values
    }
