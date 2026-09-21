from fastapi import APIRouter

from app.services.bluesky import get_timeline


router = APIRouter(
    prefix="/api/bluesky",
    tags=["bluesky"],
)


@router.get("/posts")
async def get_posts():

    posts = await get_timeline(
        limit=10
    )

    return {
        "posts": posts
    }