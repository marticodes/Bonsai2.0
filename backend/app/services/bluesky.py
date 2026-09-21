import os

from atproto import AsyncClient


client = AsyncClient()


async def login_to_bluesky():
    handle = os.getenv("BLUESKY_HANDLE")
    app_password = os.getenv("BLUESKY_APP_PASSWORD")

    if not handle or not app_password:
        raise ValueError(
            "BLUESKY_HANDLE and BLUESKY_APP_PASSWORD "
            "must be set in .env"
        )

    await client.login(
        handle,
        app_password,
    )


async def get_timeline(limit: int = 10):
    await login_to_bluesky()

    response = await client.get_timeline(
        algorithm="reverse-chronological",
        limit=limit,
    )

    posts = []

    for feed_view in response.feed:
        post = feed_view.post

        posts.append(
            {
                "uri": post.uri,
                "cid": post.cid,
                "text": post.record.text,
                "author": post.author.handle,
                "display_name": post.author.display_name,
            }
        )

    return posts