from fastapi import APIRouter

from app.services.bluesky import get_feed


router = APIRouter(
    prefix="/api/bluesky",
    tags=["bluesky"],
)


@router.get("/posts")
async def get_posts():

    feed_uri = (
        "at://did:plc:z72i7hdynmk6r22z27h6tvur/"
        "app.bsky.feed.generator/hot-classic"
    )

    posts = await get_feed(
        feed_uri=feed_uri,
        limit=20,
    )

    return {
        "posts": posts
    }