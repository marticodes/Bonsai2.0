import os

from openai import AsyncOpenAI
from pydantic import BaseModel


client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


class FeedSpecification(BaseModel):
    overarching_point: str

    best_types_of_post: list[str]

    desirable_and_decent: list[str]

    acceptable: list[str]

    better_than_nothing: list[str]

    avoid: list[str]

    penalize_for: list[str]


async def generate_feed_specification(
    conversation: list[dict[str, str]],
) -> FeedSpecification:

    system_prompt = """
Take this conversation and faithfully synthesize a concise
description in the form below.

In synthesizing:

- Respect and reflect the user's different degrees of
  preference: essential, preferred, and mildly preferred.
- Do not invent preferences that the user did not express.
- Align descriptions with real posts one can find on Bluesky.
- Describe classes or characteristics of posts, not individual
  hypothetical posts.
- Focus on the TEXT content of posts.
- Do not include author identity, follower counts, engagement
  metrics, images, or feed-balancing rules.
- Keep the specification concise and useful for a later
  post-scoring system.

The resulting specification should have these sections:

OVERARCHING POINT AND THEME

Describe at a high level what the feed is about and what its
purpose is.

BEST TYPES OF POST (0.8-1.0)

Posts that satisfy the user's essential requirements and
strongest preferences.

DESIRABLE AND DECENT (0.5-0.7)

Posts that meet the essential requirements but miss some
other preferences.

ACCEPTABLE (0.3-0.5)

Posts that do not meet all essential requirements but still
provide some value.

BETTER THAN NOTHING (0.1-0.2)

Posts that have some positive characteristics and contain
nothing that the user explicitly wants excluded.

MAKE SURE TO AVOID (rate 0)

Types of posts that should receive a score of zero.

PENALIZE POSTS FOR

Characteristics that should reduce a post's score, even if
the post is otherwise relevant.

Important distinction:

- "avoid" means the post should be rated 0.
- "penalize_for" means the characteristic lowers the score
  but does not necessarily make the post completely
  unacceptable.
- The scoring categories should reflect the strength of the
  user's preferences.
- Do not turn every preference into an exclusion.
- If the user has no preference about something, do not
  create a preference for it.

Return only the structured specification.
"""

    response = await client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *conversation,
        ],
        response_format=FeedSpecification,
    )

    specification = response.choices[0].message.parsed

    print("\n" + "=" * 60)
    print("GENERATED FEED SPECIFICATION")
    print("=" * 60)
    print(specification.model_dump_json(indent=2))
    print("=" * 60 + "\n")

    return specification