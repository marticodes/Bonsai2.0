"""
Schwartz Basic Human Values classifier.

Isolated module so the scoring model can be swapped later without
touching the Bluesky fetch layer or the /values API/UI.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from openai import AsyncOpenAI


# Canonical 19 Schwartz refined values (labels used everywhere downstream).
SCHWARTZ_VALUES: list[str] = [
    "Self-Direction–Thought",
    "Self-Direction–Action",
    "Stimulation",
    "Hedonism",
    "Achievement",
    "Power–Dominance",
    "Power–Resources",
    "Face",
    "Security–Personal",
    "Security–Societal",
    "Tradition",
    "Conformity–Rules",
    "Conformity–Interpersonal",
    "Humility",
    "Benevolence–Dependability",
    "Benevolence–Caring",
    "Universalism–Concern",
    "Universalism–Nature",
    "Universalism–Tolerance",
]


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Lazy client so this module can be imported / swapped without side effects."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def empty_value_vector() -> dict[str, float]:
    return {name: 0.0 for name in SCHWARTZ_VALUES}


def normalize_value_vector(raw: dict[str, Any] | None) -> dict[str, float]:
    """Ensure every response has all 19 keys with floats in [0, 1]."""
    vector = empty_value_vector()

    if not raw:
        return vector

    for name in SCHWARTZ_VALUES:
        value = raw.get(name)
        if value is None:
            continue
        try:
            score = float(value)
        except (TypeError, ValueError):
            continue
        vector[name] = max(0.0, min(1.0, score))

    return vector


async def classify_post(text: str) -> dict[str, float]:
    """
    Classify a single post into a 19-dimensional Schwartz value vector.

    Returns a dict mapping each of the 19 value names to a score in [0, 1].
    Replace this function's internals to swap models later.
    """
    if not text or not text.strip():
        return empty_value_vector()

    value_list = "\n".join(
        f"{i}. {name}" for i, name in enumerate(SCHWARTZ_VALUES, start=1)
    )

    system_prompt = f"""
You classify short social-media posts against the Schwartz theory of
basic human values (19 refined values).

Score how strongly the post expresses, endorses, or appeals to EACH
value. Judge only the text. Do not invent author intent beyond what
the text supports.

Score meanings:
- 0.0: absent / irrelevant
- 0.1–0.3: weak or indirect cue
- 0.4–0.6: clear presence
- 0.7–0.9: strong presence
- 1.0: dominant theme of the post

Most posts should have low scores on many values. Prefer sparse
vectors over spreading medium scores everywhere.

You MUST return JSON with exactly these 19 keys (spelling and
punctuation must match exactly), each a number from 0 to 1:

{value_list}

Return ONLY a JSON object with those 19 keys. No extra fields.
"""

    user_prompt = f"""POST:
{text}
"""

    response = await _get_client().chat.completions.create(
        model="gpt-4o-mini",
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
        temperature=0,
    )

    content = response.choices[0].message.content or "{}"
    parsed = json.loads(content)
    return normalize_value_vector(parsed)


async def classify_posts(texts: list[str]) -> list[dict[str, float]]:
    """Classify many posts. Override later for batch models."""
    return list(
        await asyncio.gather(
            *(classify_post(text) for text in texts)
        )
    )
