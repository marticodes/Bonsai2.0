import os

from atproto import AsyncClient


client = AsyncClient()
_logged_in = False


async def login_to_bluesky():
    global _logged_in

    if _logged_in:
        return

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
    _logged_in = True


async def get_feed(
    feed_uri: str,
    limit: int = 30,
):
    await login_to_bluesky()

    response = await client.app.bsky.feed.get_feed(
        {
            "feed": feed_uri,
            "limit": limit,
        }
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