import json
import os

from openai import AsyncOpenAI

from app.services.specification import FeedSpecification


client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


async def score_post(
    post: str,
    specification: FeedSpecification,
) -> dict:

    system_prompt = """
You are a post-ranking system for a personalized Bluesky feed.

Your job is to score ONE individual text post according to a
user's Feed Specification.

The score must be between 0 and 1.

Interpret the specification as follows:

- 0.8–1.0:
  Best types of posts. Strongly matches the user's preferences.

- 0.5–0.7:
  Desirable and decent. Meets important requirements but misses
  some preferences.

- 0.3–0.5:
  Acceptable. Provides some value but does not satisfy all
  important requirements.

- 0.1–0.2:
  Better than nothing. Has some positive characteristics and
  nothing explicitly excluded.

- 0:
  The post contains something the user explicitly wants to avoid.

Important rules:

1. Judge only the TEXT of the post.
2. Do not consider the author.
3. Do not consider popularity or engagement.
4. Do not invent user preferences.
5. An "avoid" characteristic should result in a score of 0.
6. "Penalize for" characteristics should lower the score but
   do not necessarily make the score 0.
7. Give a short explanation for the score.

Return JSON with exactly these fields:

{
  "score": number,
  "reason": "short explanation"
}
"""

    user_prompt = f"""
FEED SPECIFICATION:

{specification.model_dump_json(indent=2)}

POST:

{post}
"""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        response_format={
            "type": "json_object"
        },
    )

    result = response.choices[0].message.content

    return json.loads(result)